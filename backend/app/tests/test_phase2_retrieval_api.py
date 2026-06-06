from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import CodeChunk, CodeRelation, RelationType, Repository, RepositoryStatus, SymbolType


def test_retrieval_api_returns_evidences_and_debug_counts(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_retrieval_fixture(db)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/retrieve",
        json={"query": "main helper", "top_k": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_id"] == repository_id
    assert body["query"] == "main helper"
    assert body["debug"]["bm25_count"] >= 1
    assert body["debug"]["vector_count"] == 0
    assert body["debug"]["graph_count"] >= 1
    assert "REPOLENS_EMBEDDING_BASE_URL" in body["debug"]["vector_disabled_reason"]
    assert body["debug"]["evidence_count"] == len(body["evidences"])
    assert body["evidences"]
    first_evidence = body["evidences"][0]
    assert first_evidence["repository_id"] == repository_id
    assert first_evidence["file_path"] == "app.py"
    assert first_evidence["start_line"] >= 1
    assert first_evidence["score"] >= 0
    assert first_evidence["snippet"]


def test_retrieval_api_rejects_repository_before_ready() -> None:
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
            local_path="demo",
            status=RepositoryStatus.PARSING.value,
        )
        db.add(repository)
        db.commit()
        repository_id = repository.id

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/retrieve",
        json={"query": "main", "top_k": 5},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository must be ready before retrieval."


def _insert_retrieval_fixture(db: Session) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=RepositoryStatus.READY.value,
        chunk_count=2,
        relation_count=1,
    )
    db.add(repository)
    db.flush()
    main_chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="main",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=1,
        end_line=2,
        content_hash="hash-main",
        content="def main():\n    return helper()\n",
    )
    helper_chunk = CodeChunk(
        repository_id=repository.id,
        file_path="app.py",
        language="python",
        symbol_name="helper",
        symbol_type=SymbolType.FUNCTION.value,
        start_line=4,
        end_line=5,
        content_hash="hash-helper",
        content="def helper():\n    return 2\n",
    )
    db.add_all([main_chunk, helper_chunk])
    db.flush()
    db.add(
        CodeRelation(
            repository_id=repository.id,
            source_id=main_chunk.id,
            target_id=helper_chunk.id,
            source_symbol="main",
            target_symbol="helper",
            relation_type=RelationType.CALLS.value,
            source_file="app.py",
            target_file="app.py",
        )
    )
    db.commit()
    return repository.id


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
