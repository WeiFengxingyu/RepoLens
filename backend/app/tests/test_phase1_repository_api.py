from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import CodeChunk, CodeRelation, RelationType


def test_repository_api_imports_local_repository(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (tmp_path / "ui.tsx").write_text("export function UI() {}\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post("/api/repositories", json={"source": str(tmp_path)})

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "local"
    assert body["status"] == "ready"
    assert body["local_path"] == str(tmp_path.resolve())
    assert body["file_count"] == 2
    assert body["parsed_file_count"] == 2
    assert body["skipped_file_count"] == 1
    assert body["chunk_count"] == 4
    assert body["relation_count"] == 4
    assert body["indexed_at"] is not None
    assert body["language_summary"] == {"python": 1, "typescript": 1}

    repository_id = body["id"]
    status_response = client.get(f"/api/repositories/{repository_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "ready"
    assert status_response.json()["progress"]["file_count"] == 2
    assert status_response.json()["progress"]["parsed_file_count"] == 2
    assert status_response.json()["progress"]["chunk_count"] == 4
    assert status_response.json()["progress"]["relation_count"] == 4

    list_response = client.get("/api/repositories")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    with TestingSessionLocal() as db:
        chunks = db.scalars(
            select(CodeChunk).where(CodeChunk.repository_id == repository_id)
        ).all()
        relations = db.scalars(
            select(CodeRelation).where(CodeRelation.repository_id == repository_id)
        ).all()

    assert {chunk.symbol_name for chunk in chunks} == {"app.py", "main", "ui.tsx", "UI"}
    assert {relation.relation_type for relation in relations} == {
        RelationType.CONTAINS.value,
        RelationType.DEFINED_IN.value,
    }
