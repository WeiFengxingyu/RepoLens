from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Protocol, TypeVar
from urllib import error, request
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import CodeChunk

DEFAULT_COLLECTION_NAME = "repolens_code_chunks"
DEFAULT_EMBEDDING_BATCH_SIZE = 32
DEFAULT_UPSERT_BATCH_SIZE = 64
T = TypeVar("T")


class QdrantStoreError(RuntimeError):
    pass


class QdrantHttpError(QdrantStoreError):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class QdrantTransport(Protocol):
    def request_json(
        self,
        method: str,
        url: str,
        payload: dict[str, object] | None,
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        pass


class EmbeddingAdapter(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


@dataclass(frozen=True)
class QdrantConfig:
    url: str
    collection_name: str = DEFAULT_COLLECTION_NAME


@dataclass(frozen=True)
class QdrantPoint:
    id: str
    vector: list[float]
    payload: dict[str, str | int]


@dataclass(frozen=True)
class VectorIndexResult:
    repository_id: str
    collection_name: str
    chunk_count: int
    vector_count: int
    dimension: int | None


@dataclass(frozen=True)
class VectorSearchFilters:
    language: str | None = None
    file_path_prefix: str | None = None
    symbol_type: str | None = None


@dataclass(frozen=True)
class VectorSearchResult:
    chunk_id: str
    score: float
    vector_score: float
    metadata: dict[str, object]
    source: str = "vector"


class UrllibQdrantTransport:
    def request_json(
        self,
        method: str,
        url: str,
        payload: dict[str, object] | None,
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, object]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request_headers = {"Content-Type": "application/json", **headers}
        req = request.Request(url, data=body, headers=request_headers, method=method)
        try:
            with request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
                if not response_body:
                    return {}
                return json.loads(response_body)
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise QdrantHttpError(exc.code, f"Qdrant request failed with {exc.code}: {message}") from exc
        except error.URLError as exc:
            raise QdrantStoreError(f"Qdrant request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise QdrantStoreError("Qdrant response is not valid JSON.") from exc


class QdrantVectorStore:
    def __init__(
        self,
        config: QdrantConfig,
        *,
        transport: QdrantTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.config = config
        self.transport = transport or UrllibQdrantTransport()
        self.timeout = timeout

    def ensure_collection(self, dimension: int) -> None:
        if dimension <= 0:
            raise QdrantStoreError("Qdrant vector dimension must be positive.")

        try:
            response = self.transport.request_json(
                "GET",
                _collection_url(self.config),
                None,
                {},
                self.timeout,
            )
        except QdrantHttpError as exc:
            if exc.status_code != 404:
                raise
            self._create_collection(dimension)
            return

        existing_dimension = _extract_vector_size(response)
        if existing_dimension is not None and existing_dimension != dimension:
            raise QdrantStoreError(
                f"Qdrant collection dimension mismatch: expected {dimension}, "
                f"existing {existing_dimension}."
            )

    def upsert_points(self, points: Sequence[QdrantPoint]) -> int:
        if not points:
            return 0

        self.transport.request_json(
            "PUT",
            _points_url(self.config),
            {
                "points": [
                    {"id": point.id, "vector": point.vector, "payload": point.payload}
                    for point in points
                ]
            },
            {},
            self.timeout,
        )
        return len(points)

    def search(
        self,
        query_vector: list[float],
        repository_id: str,
        *,
        top_k: int = 10,
        filters: VectorSearchFilters | None = None,
    ) -> list[VectorSearchResult]:
        if top_k <= 0:
            return []
        if not query_vector:
            raise QdrantStoreError("Qdrant search vector must not be empty.")

        response = self.transport.request_json(
            "POST",
            _search_url(self.config),
            {
                "vector": query_vector,
                "limit": top_k,
                "with_payload": True,
                "with_vector": False,
                "filter": _build_qdrant_filter(repository_id, filters),
            },
            {},
            self.timeout,
        )
        return _parse_search_response(response)

    def _create_collection(self, dimension: int) -> None:
        self.transport.request_json(
            "PUT",
            _collection_url(self.config),
            {"vectors": {"size": dimension, "distance": "Cosine"}},
            {},
            self.timeout,
        )


def qdrant_config_from_settings(settings: Settings) -> QdrantConfig:
    return QdrantConfig(url=settings.qdrant_url.rstrip("/"))


def index_repository_chunks(
    db: Session,
    repository_id: str,
    *,
    embedding_adapter: EmbeddingAdapter,
    vector_store: QdrantVectorStore,
    embedding_batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    upsert_batch_size: int = DEFAULT_UPSERT_BATCH_SIZE,
) -> VectorIndexResult:
    chunks = db.scalars(
        select(CodeChunk)
        .where(CodeChunk.repository_id == repository_id)
        .order_by(CodeChunk.file_path, CodeChunk.start_line, CodeChunk.id)
    ).all()
    if not chunks:
        return VectorIndexResult(
            repository_id=repository_id,
            collection_name=vector_store.config.collection_name,
            chunk_count=0,
            vector_count=0,
            dimension=None,
        )

    if embedding_batch_size <= 0 or upsert_batch_size <= 0:
        raise QdrantStoreError("Embedding and upsert batch sizes must be positive.")

    dimension: int | None = None
    vector_count = 0
    pending_points: list[QdrantPoint] = []

    for chunk_batch in _batched(chunks, embedding_batch_size):
        texts = [build_embedding_input(chunk) for chunk in chunk_batch]
        embeddings = embedding_adapter.embed_texts(texts)
        if len(embeddings) != len(chunk_batch):
            raise QdrantStoreError("Embedding count does not match chunk count.")

        for chunk, embedding in zip(chunk_batch, embeddings, strict=True):
            if dimension is None:
                dimension = len(embedding)
                vector_store.ensure_collection(dimension)
            elif len(embedding) != dimension:
                raise QdrantStoreError(
                    f"Embedding dimension mismatch: expected {dimension}, got {len(embedding)}."
                )

            pending_points.append(qdrant_point_from_chunk(chunk, embedding))
            if len(pending_points) >= upsert_batch_size:
                vector_count += vector_store.upsert_points(pending_points)
                pending_points = []

    if pending_points:
        vector_count += vector_store.upsert_points(pending_points)

    return VectorIndexResult(
        repository_id=repository_id,
        collection_name=vector_store.config.collection_name,
        chunk_count=len(chunks),
        vector_count=vector_count,
        dimension=dimension,
    )


def search_repository_chunks(
    repository_id: str,
    query: str,
    *,
    embedding_adapter: EmbeddingAdapter,
    vector_store: QdrantVectorStore,
    top_k: int = 10,
    filters: VectorSearchFilters | None = None,
) -> list[VectorSearchResult]:
    normalized_query = query.strip()
    if not normalized_query or top_k <= 0:
        return []
    query_embeddings = embedding_adapter.embed_texts([normalized_query])
    if len(query_embeddings) != 1:
        raise QdrantStoreError("Embedding count does not match query count.")
    query_vector = query_embeddings[0]
    return vector_store.search(query_vector, repository_id, top_k=top_k, filters=filters)


def build_embedding_input(chunk: CodeChunk) -> str:
    return "\n".join(
        [
            f"path: {chunk.file_path}",
            f"language: {chunk.language}",
            f"symbol: {chunk.symbol_name}",
            f"type: {chunk.symbol_type}",
            "content:",
            chunk.content,
        ]
    )


def qdrant_point_from_chunk(chunk: CodeChunk, vector: list[float]) -> QdrantPoint:
    return QdrantPoint(
        id=qdrant_point_id(chunk.repository_id, chunk.id),
        vector=vector,
        payload={
            "chunk_id": chunk.id,
            "repository_id": chunk.repository_id,
            "file_path": chunk.file_path,
            "symbol_name": chunk.symbol_name,
            "symbol_type": chunk.symbol_type,
            "language": chunk.language,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content_hash": chunk.content_hash,
            "point_hash": qdrant_point_hash(chunk.repository_id, chunk.id),
        },
    )


def qdrant_point_id(repository_id: str, chunk_id: str) -> str:
    return str(uuid.UUID(hex=qdrant_point_hash(repository_id, chunk_id)[:32]))


def qdrant_point_hash(repository_id: str, chunk_id: str) -> str:
    return hashlib.sha256(f"{repository_id}:{chunk_id}".encode("utf-8")).hexdigest()


def _collection_url(config: QdrantConfig) -> str:
    return f"{config.url.rstrip('/')}/collections/{config.collection_name}"


def _points_url(config: QdrantConfig) -> str:
    return f"{_collection_url(config)}/points?wait=true"


def _search_url(config: QdrantConfig) -> str:
    return f"{_collection_url(config)}/points/search"


def _build_qdrant_filter(
    repository_id: str,
    filters: VectorSearchFilters | None,
) -> dict[str, object]:
    must: list[dict[str, object]] = [
        {"key": "repository_id", "match": {"value": repository_id}}
    ]
    if filters is None:
        return {"must": must}
    if filters.language:
        must.append({"key": "language", "match": {"value": filters.language}})
    if filters.symbol_type:
        must.append({"key": "symbol_type", "match": {"value": filters.symbol_type}})
    if filters.file_path_prefix:
        must.append({"key": "file_path", "match": {"text": filters.file_path_prefix}})
    return {"must": must}


def _parse_search_response(response: dict[str, object]) -> list[VectorSearchResult]:
    result = response.get("result")
    if not isinstance(result, list):
        raise QdrantStoreError("Qdrant search response missing result list.")

    search_results: list[VectorSearchResult] = []
    for item in result:
        if not isinstance(item, dict):
            raise QdrantStoreError("Qdrant search result item is not an object.")
        payload = item.get("payload")
        if not isinstance(payload, dict):
            raise QdrantStoreError("Qdrant search result missing payload.")
        chunk_id = payload.get("chunk_id")
        if not isinstance(chunk_id, str):
            raise QdrantStoreError("Qdrant search result missing chunk_id.")
        score = item.get("score")
        if not isinstance(score, (int, float)):
            raise QdrantStoreError("Qdrant search result missing numeric score.")
        search_results.append(
            VectorSearchResult(
                chunk_id=chunk_id,
                score=float(score),
                vector_score=float(score),
                metadata=dict(payload),
            )
        )
    return search_results


def _extract_vector_size(response: dict[str, object]) -> int | None:
    result = response.get("result")
    if not isinstance(result, dict):
        return None
    config = result.get("config")
    if not isinstance(config, dict):
        return None
    params = config.get("params")
    if not isinstance(params, dict):
        return None
    vectors = params.get("vectors")
    if not isinstance(vectors, dict):
        return None
    size = vectors.get("size")
    return int(size) if isinstance(size, int) else None


def _batched(items: Sequence[T], batch_size: int) -> list[Sequence[T]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]
