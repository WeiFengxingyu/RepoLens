from collections.abc import Generator
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import AgentTrace, Repository, RepositoryStatus, Task, TaskStatus, TaskType, ToolCall


def test_review_api_creates_completed_review_report_and_gets_review_response() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/reviews",
        json={
            "diff_text": _sample_diff(),
            "top_k": 8,
            "use_bm25": True,
            "use_vector": False,
            "use_graph": True,
            "run_static_check": False,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["repository_id"] == repository_id
    assert body["status"] == TaskStatus.COMPLETED.value
    assert body["summary"] == "Found 1 verified review risk(s) across 0 impacted symbol(s)."
    assert body["risk_level"] == "low"
    assert body["risks"][0]["location"]["file_path"] == "app.py"
    assert [tool_call["tool_name"] for tool_call in body["tool_calls"]] == [
        "analyze_diff",
        "code_search",
    ]
    assert body["tool_calls"][0]["permission_decision"] == "allow"
    assert any(trace["step_name"] == "ReviewReportWriter" for trace in body["traces"])

    task_id = body["task_id"]
    get_response = client.get(f"/api/reviews/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task_id"] == task_id
    assert get_response.json()["markdown"].startswith("## Summary")

    with TestingSessionLocal() as db:
        stored_task = db.scalar(select(Task).where(Task.id == task_id))
        tool_calls = db.scalars(select(ToolCall).where(ToolCall.task_id == task_id)).all()
        traces = db.scalars(select(AgentTrace).where(AgentTrace.task_id == task_id)).all()

    assert stored_task is not None
    assert stored_task.task_type == TaskType.REVIEW.value
    assert stored_task.status == TaskStatus.COMPLETED.value
    assert json.loads(stored_task.input_payload)["diff_text"].startswith("diff --git")
    assert len(tool_calls) == 2
    assert len(traces) == 7


def test_review_api_rejects_repository_before_ready() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.PARSING.value)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/reviews",
        json={"diff_text": _sample_diff()},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository must be ready before Review."


def test_review_api_rejects_blank_diff_and_missing_review_task() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/reviews",
        json={"diff_text": "   "},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Diff text is required."

    missing_response = client.get("/api/reviews/missing")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Review task not found."


def _insert_repository(db: Session, status: str) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=status,
    )
    db.add(repository)
    db.commit()
    return repository.id


def _sample_diff() -> str:
    return """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,1 +1,1 @@
-old()
+new()
"""


def _override_get_db(TestingSessionLocal):
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db
