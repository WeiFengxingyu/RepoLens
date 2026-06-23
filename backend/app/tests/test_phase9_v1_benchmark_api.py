from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import CodeChunk, Repository, RepositoryStatus, SymbolType


def test_v1_benchmark_api_runs_review_multi_agent_and_mcp(tmp_path: Path, monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    dataset_path = _write_dataset(tmp_path)
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
        repository_id = _insert_repository(db, repository_root)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/v1-benchmarks",
        json={
            "name": "P9 smoke",
            "dataset_path": str(dataset_path),
            "repository_map": {"python_demo": repository_id},
            "include_review": True,
            "include_multi_agent": True,
            "include_mcp": True,
            "top_k": 5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["sample_count"] == 20
    assert body["metrics"]["review"]["sample_count"] == 20
    assert body["metrics"]["multi_agent"]["sample_count"] == 20
    assert body["metrics"]["mcp"]["tool_call_count"] == 40
    assert body["metrics"]["mcp"]["permission_denial_correctness"] == 1.0
    assert body["results"][0]["review"]["risk_hit"] is True
    assert body["results"][0]["multi_agent"]["arbiter_resolved"] is True
    assert body["results"][0]["mcp"]
    assert body["report_markdown"].startswith("# V1 Benchmark Report")


def test_v1_benchmark_api_rejects_missing_repository_map_key(tmp_path: Path) -> None:
    dataset_path = _write_dataset(tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/v1-benchmarks",
        json={"dataset_path": str(dataset_path), "repository_map": {}},
    )

    assert response.status_code == 422
    assert "repository_map missing keys" in response.json()["detail"]


def test_v1_benchmark_api_rejects_repository_before_ready(tmp_path: Path) -> None:
    dataset_path = _write_dataset(tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        repository = Repository(
            name="demo",
            source_type="local",
            local_path=str(tmp_path / "repo"),
            status=RepositoryStatus.PARSING.value,
        )
        db.add(repository)
        db.commit()
        repository_id = repository.id

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        "/api/v1-benchmarks",
        json={
            "dataset_path": str(dataset_path),
            "repository_map": {"python_demo": repository_id},
        },
    )

    assert response.status_code == 400
    assert "must be ready" in response.json()["detail"]


def _write_dataset(tmp_path: Path) -> Path:
    dataset_path = tmp_path / "v1.jsonl"
    lines = []
    for index in range(1, 21):
        lines.append(
            {
                "id": f"case-{index:03}",
                "repository_key": "python_demo",
                "platform": "github",
                "change_type": "pull_request",
                "url": f"https://github.com/example/repo/pull/{index}",
                "title": "Token security change",
                "diff_text": _diff_text(),
                "expected_risks": [
                    {
                        "title_keywords": ["login", "token"],
                        "severity": "medium",
                        "file_path": "app.py",
                    }
                ],
                "expected_files": ["app.py"],
                "expected_labels": ["security"] if index % 2 == 0 else [],
                "mcp_tool_calls": [
                    {
                        "tool_name": "code.search",
                        "arguments": {
                            "repository_id": "{repository_id}",
                            "query": "login token",
                            "top_k": 5,
                            "use_vector": False,
                        },
                        "expect_success": True,
                        "expect_permission_decision": "allow",
                    },
                    {
                        "tool_name": "run_safe_static_check",
                        "arguments": {
                            "repository_id": "{repository_id}",
                            "checker": "python_ast_parse",
                            "file_paths": ["app.py"],
                        },
                        "expect_success": False,
                        "expect_permission_decision": "disabled",
                    },
                ],
            }
        )
    dataset_path.write_text("\n".join(__import__("json").dumps(line) for line in lines), encoding="utf-8")
    return dataset_path


def _insert_repository(db: Session, repository_root: Path) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path=str(repository_root),
        status=RepositoryStatus.READY.value,
        file_count=1,
        parsed_file_count=1,
        chunk_count=1,
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


def _diff_text() -> str:
    return """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def login(token):
-    return token
+    return token + secret
"""


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
