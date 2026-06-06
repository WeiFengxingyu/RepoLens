from collections.abc import Generator
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import CodeChunk, Repository, RepositoryStatus, SymbolType
from app.services.indexing import (
    QdrantConfig,
    QdrantHttpError,
    QdrantStoreError,
    QdrantVectorStore,
    VectorSearchFilters,
    index_repository_chunks,
    qdrant_point_id,
    search_repository_chunks,
)


@dataclass
class FakeEmbeddingAdapter:
    batches: list[list[str]] = field(default_factory=list)
    calls: int = 0

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.batches.append(texts)
        embeddings = []
        for _text in texts:
            self.calls += 1
            embeddings.append([float(self.calls), float(self.calls) + 0.1, float(self.calls) + 0.2])
        return embeddings


@dataclass
class FakeQdrantTransport:
    collection_exists: bool = False
    vector_size: int = 3
    search_response: dict[str, object] = field(default_factory=lambda: {"result": []})
    requests: list[dict[str, object]] = field(default_factory=list)

    def request_json(
        self,
        method: str,
        url: str,
        payload: dict[str, object] | None,
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        self.requests.append(
            {
                "method": method,
                "url": url,
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if method == "GET":
            if not self.collection_exists:
                raise QdrantHttpError(404, "not found")
            return {"result": {"config": {"params": {"vectors": {"size": self.vector_size}}}}}
        if method == "POST":
            return self.search_response
        return {"result": True}


class EmptyEmbeddingAdapter:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return []


def test_qdrant_point_id_uses_stable_sha256() -> None:
    point_id = qdrant_point_id("repo-1", "chunk-1")
    expected_hash = hashlib.sha256("repo-1:chunk-1".encode("utf-8")).hexdigest()

    assert point_id == str(uuid.UUID(hex=expected_hash[:32]))


def test_index_repository_chunks_creates_collection_and_upserts_points() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    embedding_adapter = FakeEmbeddingAdapter()
    qdrant_transport = FakeQdrantTransport()
    vector_store = QdrantVectorStore(
        QdrantConfig(url="http://qdrant.local"),
        transport=qdrant_transport,
        timeout=1.5,
    )

    with TestingSessionLocal() as db:
        repository_id = _insert_repository_with_chunks(db)

        result = index_repository_chunks(
            db,
            repository_id,
            embedding_adapter=embedding_adapter,
            vector_store=vector_store,
            embedding_batch_size=1,
            upsert_batch_size=1,
        )

    assert result.repository_id == repository_id
    assert result.collection_name == "repolens_code_chunks"
    assert result.chunk_count == 2
    assert result.vector_count == 2
    assert result.dimension == 3
    assert len(embedding_adapter.batches) == 2

    methods = [request["method"] for request in qdrant_transport.requests]
    assert methods == ["GET", "PUT", "PUT", "PUT"]
    assert qdrant_transport.requests[1]["payload"] == {
        "vectors": {"size": 3, "distance": "Cosine"}
    }

    first_upsert = qdrant_transport.requests[2]["payload"]
    assert isinstance(first_upsert, dict)
    points = first_upsert["points"]
    assert isinstance(points, list)
    assert points[0]["vector"] == [1.0, 1.1, 1.2]
    assert points[0]["payload"]["repository_id"] == repository_id
    assert points[0]["payload"]["file_path"] == "app.py"
    assert points[0]["payload"]["symbol_name"] == "main"
    assert "point_hash" in points[0]["payload"]


def test_index_repository_chunks_returns_empty_result_without_qdrant_call() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    qdrant_transport = FakeQdrantTransport()
    vector_store = QdrantVectorStore(QdrantConfig(url="http://qdrant.local"), transport=qdrant_transport)

    with TestingSessionLocal() as db:
        result = index_repository_chunks(
            db,
            "missing-repository",
            embedding_adapter=FakeEmbeddingAdapter(),
            vector_store=vector_store,
        )

    assert result.chunk_count == 0
    assert result.vector_count == 0
    assert result.dimension is None
    assert qdrant_transport.requests == []


def test_qdrant_store_rejects_collection_dimension_mismatch() -> None:
    vector_store = QdrantVectorStore(
        QdrantConfig(url="http://qdrant.local"),
        transport=FakeQdrantTransport(collection_exists=True, vector_size=3),
    )

    with pytest.raises(QdrantStoreError):
        vector_store.ensure_collection(4)


def test_search_repository_chunks_posts_vector_search_with_repository_filter() -> None:
    qdrant_transport = FakeQdrantTransport(
        search_response={
            "result": [
                {
                    "id": "point-1",
                    "score": 0.91,
                    "payload": {
                        "chunk_id": "chunk-1",
                        "repository_id": "repo-1",
                        "file_path": "app.py",
                        "symbol_name": "main",
                        "symbol_type": "function",
                        "language": "python",
                    },
                }
            ]
        }
    )
    vector_store = QdrantVectorStore(
        QdrantConfig(url="http://qdrant.local"),
        transport=qdrant_transport,
    )

    results = search_repository_chunks(
        "repo-1",
        "main flow",
        embedding_adapter=FakeEmbeddingAdapter(),
        vector_store=vector_store,
        top_k=5,
        filters=VectorSearchFilters(
            language="python",
            file_path_prefix="app",
            symbol_type="function",
        ),
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].source == "vector"
    assert results[0].score == 0.91
    assert results[0].vector_score == 0.91
    assert results[0].metadata["file_path"] == "app.py"

    assert len(qdrant_transport.requests) == 1
    request = qdrant_transport.requests[0]
    assert request["method"] == "POST"
    assert request["url"] == "http://qdrant.local/collections/repolens_code_chunks/points/search"
    payload = request["payload"]
    assert isinstance(payload, dict)
    assert payload["vector"] == [1.0, 1.1, 1.2]
    assert payload["limit"] == 5
    assert payload["with_payload"] is True
    assert payload["with_vector"] is False
    assert payload["filter"] == {
        "must": [
            {"key": "repository_id", "match": {"value": "repo-1"}},
            {"key": "language", "match": {"value": "python"}},
            {"key": "symbol_type", "match": {"value": "function"}},
            {"key": "file_path", "match": {"text": "app"}},
        ]
    }


def test_search_repository_chunks_skips_blank_query_and_non_positive_top_k() -> None:
    qdrant_transport = FakeQdrantTransport()
    vector_store = QdrantVectorStore(
        QdrantConfig(url="http://qdrant.local"),
        transport=qdrant_transport,
    )

    assert (
        search_repository_chunks(
            "repo-1",
            "  ",
            embedding_adapter=FakeEmbeddingAdapter(),
            vector_store=vector_store,
        )
        == []
    )
    assert (
        search_repository_chunks(
            "repo-1",
            "main flow",
            embedding_adapter=FakeEmbeddingAdapter(),
            vector_store=vector_store,
            top_k=0,
        )
        == []
    )
    assert qdrant_transport.requests == []


def test_qdrant_search_requires_chunk_id_payload() -> None:
    vector_store = QdrantVectorStore(
        QdrantConfig(url="http://qdrant.local"),
        transport=FakeQdrantTransport(search_response={"result": [{"score": 0.5, "payload": {}}]}),
    )

    with pytest.raises(QdrantStoreError):
        vector_store.search([0.1, 0.2, 0.3], "repo-1")


def test_search_repository_chunks_validates_query_embedding_count() -> None:
    vector_store = QdrantVectorStore(
        QdrantConfig(url="http://qdrant.local"),
        transport=FakeQdrantTransport(),
    )

    with pytest.raises(QdrantStoreError):
        search_repository_chunks(
            "repo-1",
            "main flow",
            embedding_adapter=EmptyEmbeddingAdapter(),
            vector_store=vector_store,
        )


def test_vector_index_api_reports_disabled_embedding_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("REPOLENS_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("REPOLENS_EMBEDDING_DIMENSION", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        repository_id = _insert_repository_with_chunks(db, tmp_path)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(f"/api/repositories/{repository_id}/indexes/vector")

    assert response.status_code == 400
    assert "REPOLENS_EMBEDDING_BASE_URL" in response.json()["detail"]
    get_settings.cache_clear()


def _insert_repository_with_chunks(db: Session, tmp_path: Path | None = None) -> str:
    local_path = str(tmp_path or Path("demo").resolve())
    repository = Repository(
        name="demo",
        source_type="local",
        local_path=local_path,
        status=RepositoryStatus.READY.value,
        chunk_count=2,
    )
    db.add(repository)
    db.flush()
    db.add_all(
        [
            CodeChunk(
                repository_id=repository.id,
                file_path="app.py",
                language="python",
                symbol_name="main",
                symbol_type=SymbolType.FUNCTION.value,
                start_line=1,
                end_line=2,
                content_hash="hash-main",
                content="def main():\n    return 1\n",
            ),
            CodeChunk(
                repository_id=repository.id,
                file_path="app.py",
                language="python",
                symbol_name="helper",
                symbol_type=SymbolType.FUNCTION.value,
                start_line=4,
                end_line=5,
                content_hash="hash-helper",
                content="def helper():\n    return 2\n",
            ),
        ]
    )
    db.commit()
    return repository.id
