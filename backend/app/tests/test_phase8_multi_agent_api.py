from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import (
    AgentAssignment,
    AgentMessage,
    AgentSession,
    CodeChunk,
    Repository,
    RepositoryStatus,
    SymbolType,
    Task,
    TaskType,
)


def test_multi_agent_review_api_creates_session_assignments_messages_and_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    client, TestingSessionLocal, repository_id = _create_ready_client(monkeypatch, tmp_path)

    response = client.post(
        f"/api/repositories/{repository_id}/multi-agent-reviews",
        json={
            "diff_text": _security_diff(),
            "top_k": 5,
            "use_bm25": True,
            "use_vector": False,
            "use_graph": True,
            "round_limit": 2,
            "assignment_limit": 8,
            "token_budget": 8000,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["repository_id"] == repository_id
    assert body["status"] == "completed"
    assert body["session"]["mode"] == "multi_agent_review"
    assert body["session"]["round_limit"] == 2
    assert body["session"]["assignment_limit"] == 8
    assert {item["role"] for item in body["assignments"]} == {
        "coordinator",
        "risk_reviewer",
        "security_reviewer",
        "test_strategist",
        "arbiter",
        "report_writer",
    }
    assert {message["sender"] for message in body["messages"]}.issuperset(
        {"coordinator", "risk_reviewer", "security_reviewer", "arbiter", "report_writer"}
    )
    assert body["arbiter_decision"]["accepted"] >= 1
    assert body["comparison"]["assignment_count"] == 6
    assert body["comparison"]["message_count"] == 6
    assert body["comparison"]["variant"] == "multi_agent_review"
    assert body["comparison"]["token_estimate"] <= body["session"]["token_budget"]
    assert max(item["round_index"] for item in body["assignments"]) <= body["session"]["round_limit"]
    assert body["markdown"].startswith("## Summary")

    task_id = body["task_id"]
    session_id = body["session"]["id"]
    assert client.get(f"/api/multi-agent-reviews/{task_id}").status_code == 200
    assert client.get(f"/api/agent-sessions/{session_id}").json()["task_id"] == task_id

    with TestingSessionLocal() as db:
        task = db.get(Task, task_id)
        sessions = db.scalars(select(AgentSession)).all()
        assignments = db.scalars(select(AgentAssignment)).all()
        messages = db.scalars(select(AgentMessage)).all()

    assert task is not None
    assert task.task_type == TaskType.MULTI_AGENT_REVIEW.value
    assert len(sessions) == 1
    assert len(assignments) == 6
    assert len(messages) == 6


def test_multi_agent_review_preserves_dissent_for_unindexed_security_claim(
    monkeypatch,
    tmp_path: Path,
) -> None:
    client, _TestingSessionLocal, repository_id = _create_ready_client(monkeypatch, tmp_path)

    response = client.post(
        f"/api/repositories/{repository_id}/multi-agent-reviews",
        json={
            "diff_text": _unindexed_security_diff(),
            "top_k": 5,
            "use_bm25": True,
            "use_vector": False,
            "use_graph": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["dissent"]
    assert body["arbiter_decision"]["dissent_count"] >= 1
    assert any(item["type"] == "security_evidence_gap" for item in body["dissent"])
    assert any(message["requires_arbitration"] for message in body["messages"])


def test_multi_agent_review_records_comparison_against_single_main_review(
    monkeypatch,
    tmp_path: Path,
) -> None:
    client, _TestingSessionLocal, repository_id = _create_ready_client(monkeypatch, tmp_path)

    single_response = client.post(
        f"/api/repositories/{repository_id}/reviews",
        json={
            "diff_text": _security_diff(),
            "top_k": 5,
            "use_bm25": True,
            "use_vector": False,
            "use_graph": True,
        },
    )
    multi_response = client.post(
        f"/api/repositories/{repository_id}/multi-agent-reviews",
        json={
            "diff_text": _security_diff(),
            "top_k": 5,
            "use_bm25": True,
            "use_vector": False,
            "use_graph": True,
        },
    )

    assert single_response.status_code == 201
    assert multi_response.status_code == 201
    single_body = single_response.json()
    multi_body = multi_response.json()
    assert single_body["status"] == "completed"
    assert multi_body["status"] == "completed"
    assert single_body["task_id"] != multi_body["task_id"]
    assert single_body["traces"]
    assert multi_body["messages"]
    assert multi_body["comparison"]["baseline"] == "single_main_review"
    assert multi_body["comparison"]["variant"] == "multi_agent_review"
    assert multi_body["comparison"]["assignment_count"] == len(multi_body["assignments"])
    assert multi_body["session"]["final_report"]["source_agents"]


def test_multi_agent_review_api_rejects_not_ready_and_missing_records(tmp_path: Path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    with TestingSessionLocal() as db:
        repository = Repository(
            name="demo",
            source_type="local",
            local_path=str(repository_root),
            status=RepositoryStatus.PARSING.value,
        )
        db.add(repository)
        db.commit()
        repository_id = repository.id

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/multi-agent-reviews",
        json={"diff_text": _security_diff()},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository must be ready before Multi-Agent Review."
    assert client.get("/api/multi-agent-reviews/missing").status_code == 404
    assert client.get("/api/agent-sessions/missing").status_code == 404


def _insert_ready_repository(db: Session, repository_root: Path) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path=str(repository_root),
        status=RepositoryStatus.READY.value,
        file_count=1,
        parsed_file_count=1,
        chunk_count=1,
        relation_count=0,
    )
    db.add(repository)
    db.flush()
    db.add(
        CodeChunk(
            repository_id=repository.id,
            file_path="app.py",
            language="python",
            symbol_name="login",
            symbol_type=SymbolType.FUNCTION.value,
            start_line=1,
            end_line=2,
            content_hash="hash-login",
            content="def login(token):\n    return token\n",
        )
    )
    db.commit()
    return repository.id


def _security_diff() -> str:
    return """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def login(token):
-    return token
+    return token + secret
"""


def _unindexed_security_diff() -> str:
    return """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,2 @@
 def issue_token(token):
-    return token
+    return token + secret
"""


def _create_ready_client(monkeypatch, tmp_path: Path):
    _clear_embedding_env(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "app.py").write_text(
        "def login(token):\n    return token\n",
        encoding="utf-8",
    )

    with TestingSessionLocal() as db:
        repository_id = _insert_ready_repository(db, repository_root)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    return TestClient(app), TestingSessionLocal, repository_id


def _override_get_db(TestingSessionLocal):
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


def _clear_embedding_env(monkeypatch) -> None:
    monkeypatch.delenv("REPOLENS_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_DIMENSION", raising=False)
    get_settings.cache_clear()
