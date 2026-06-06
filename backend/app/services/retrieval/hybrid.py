from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import CodeChunk
from app.services.graph import expand_graph_neighbors, load_code_graph
from app.services.indexing import (
    EmbeddingDisabledError,
    EmbeddingRequestError,
    OpenAICompatibleEmbeddingAdapter,
    QdrantStoreError,
    QdrantVectorStore,
    build_bm25_index,
    embedding_config_from_settings,
    qdrant_config_from_settings,
    search_repository_chunks,
)
from app.services.retrieval.candidates import merge_candidates
from app.services.retrieval.context import ContextPackage, build_context_package
from app.services.retrieval.evidence import Evidence, build_evidences
from app.services.retrieval.rerank import rerank_candidates


@dataclass(frozen=True)
class RetrievalDebug:
    bm25_count: int
    vector_count: int
    graph_count: int
    merged_count: int
    evidence_count: int
    vector_disabled_reason: str | None
    context_truncated: bool


@dataclass(frozen=True)
class RetrievalResult:
    repository_id: str
    query: str
    evidences: list[Evidence]
    context: ContextPackage
    debug: RetrievalDebug


def retrieve_repository(
    db: Session,
    repository_id: str,
    query: str,
    settings: Settings,
    *,
    top_k: int = 10,
    use_bm25: bool = True,
    use_vector: bool = True,
    use_graph: bool = True,
) -> RetrievalResult:
    chunks = db.scalars(
        select(CodeChunk)
        .where(CodeChunk.repository_id == repository_id)
        .order_by(CodeChunk.file_path, CodeChunk.start_line, CodeChunk.id)
    ).all()
    if not chunks:
        context = build_context_package([])
        return RetrievalResult(
            repository_id=repository_id,
            query=query,
            evidences=[],
            context=context,
            debug=RetrievalDebug(
                bm25_count=0,
                vector_count=0,
                graph_count=0,
                merged_count=0,
                evidence_count=0,
                vector_disabled_reason=None,
                context_truncated=context.truncated,
            ),
        )

    bm25_candidates = build_bm25_index(chunks).search(query, top_k=top_k) if use_bm25 else []
    vector_candidates = []
    vector_disabled_reason = None
    if use_vector:
        embedding_adapter = OpenAICompatibleEmbeddingAdapter(embedding_config_from_settings(settings))
        vector_store = QdrantVectorStore(qdrant_config_from_settings(settings))
        try:
            vector_candidates = search_repository_chunks(
                repository_id,
                query,
                embedding_adapter=embedding_adapter,
                vector_store=vector_store,
                top_k=top_k,
            )
        except (EmbeddingDisabledError, EmbeddingRequestError, QdrantStoreError) as exc:
            vector_disabled_reason = str(exc)

    graph_candidates = []
    if use_graph:
        seed_chunk_ids = [candidate.chunk_id for candidate in [*bm25_candidates, *vector_candidates]]
        if seed_chunk_ids:
            graph_candidates = expand_graph_neighbors(
                load_code_graph(db, repository_id),
                seed_chunk_ids,
                top_k=top_k,
            )

    merged_candidates = merge_candidates(
        bm25_candidates=bm25_candidates,
        vector_candidates=vector_candidates,
        graph_candidates=graph_candidates,
    )
    ranked_candidates = rerank_candidates(merged_candidates, query, top_k=top_k)
    evidences = build_evidences(db, repository_id, ranked_candidates)
    context = build_context_package(evidences)

    return RetrievalResult(
        repository_id=repository_id,
        query=query,
        evidences=evidences,
        context=context,
        debug=RetrievalDebug(
            bm25_count=len(bm25_candidates),
            vector_count=len(vector_candidates),
            graph_count=len(graph_candidates),
            merged_count=len(merged_candidates),
            evidence_count=len(evidences),
            vector_disabled_reason=vector_disabled_reason,
            context_truncated=context.truncated,
        ),
    )
