from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.core.config import get_settings
from app.models import (
    CodeChunk,
    CodeRelation,
    RelationType,
    Repository,
    RepositoryStatus,
    SymbolType,
    Task,
    TaskStatus,
    TaskType,
)


def test_qa_api_answers_question_with_citations_and_traces(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository(db, RepositoryStatus.READY.value, with_chunks=True)

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db(TestingSessionLocal)
    client = TestClient(app)

    response = client.post(
        f"/api/repositories/{repository_id}/questions",
        json={"question": "Where is repository import implemented?", "top_k": 8},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["repository_id"] == repository_id
    assert body["status"] == TaskStatus.COMPLETED.value
    assert body["question"] == "Where is repository import implemented?"
    assert body["answer"]
    assert body["citations"]
    assert body["confidence"] > 0
    assert {trace["step_name"] for trace in body["traces"]} >= {
        "Planner",
        "Retriever",
        "AnswerReviewer",
        "Verifier",
        "ReportWriter",
    }

    task_id = body["task_id"]
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task_id"] == task_id

    with TestingSessionLocal() as db:
        stored_task = db.scalar(select(Task).where(Task.id == task_id))

    assert stored_task is not None
    assert stored_task.task_type == TaskType.QA.value
    assert stored_task.status == TaskStatus.COMPLETED.value
    assert "Where is repository import implemented?" in stored_task.input_payload
    assert stored_task.output_payload is not None


def test_qa_api_uses_second_retrieval_when_evidence_is_missing(monkeypatch) -> None:
    _clear_embedding_env(monkeypatch)
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
        f"/api/repositories/{repository_id}/questions",
        json={"question": "Where is repository import implemented?", "top_k": 8},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == TaskStatus.COMPLETED.value
    assert body["citations"] == []
    assert body["confidence"] == 0.2
    assert [trace["step_name"] for trace in body["traces"]].count("Retriever") == 2


def test_qa_api_rejects_repository_before_ready() -> None:
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
        f"/api/repositories/{repository_id}/questions",
        json={"question": "Where is repository import implemented?"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository must be ready before QA."


def test_qa_api_returns_not_found_for_missing_task() -> None:
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

    response = client.get("/api/tasks/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def _insert_repository(db: Session, status: str, *, with_chunks: bool = False) -> str:
    repository = Repository(
        name="demo",
        source_type="local",
        local_path="demo",
        status=status,
        chunk_count=2 if with_chunks else 0,
        relation_count=1 if with_chunks else 0,
    )
    db.add(repository)
    db.flush()
    if with_chunks:
        main_chunk = CodeChunk(
            repository_id=repository.id,
            file_path="backend/app/services/repository/service.py",
            language="python",
            symbol_name="RepositoryService.import_repository",
            symbol_type=SymbolType.METHOD.value,
            start_line=10,
            end_line=20,
            content_hash="hash-main",
            content="def import_repository(self, request):\n    return self._save_repository(request)\n",
        )
        helper_chunk = CodeChunk(
            repository_id=repository.id,
            file_path="backend/app/api/repositories.py",
            language="python",
            symbol_name="import_repository",
            symbol_type=SymbolType.FUNCTION.value,
            start_line=20,
            end_line=30,
            content_hash="hash-api",
            content="def import_repository(request, db):\n    return service.import_repository(request)\n",
        )
        db.add_all([main_chunk, helper_chunk])
        db.flush()
        db.add(
            CodeRelation(
                repository_id=repository.id,
                source_id=helper_chunk.id,
                target_id=main_chunk.id,
                source_symbol="import_repository",
                target_symbol="RepositoryService.import_repository",
                relation_type=RelationType.CALLS.value,
                source_file="backend/app/api/repositories.py",
                target_file="backend/app/services/repository/service.py",
            )
        )
    db.commit()
    return repository.id


def _clear_embedding_env(monkeypatch) -> None:
    monkeypatch.delenv("REPOLENS_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_DIMENSION", raising=False)
    monkeypatch.delenv("REPOLENS_CHAT_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_CHAT_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_CHAT_MODEL", raising=False)
    get_settings.cache_clear()


def _override_get_db(TestingSessionLocal):
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    return override_get_db
