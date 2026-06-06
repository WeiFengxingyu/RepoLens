from dataclasses import dataclass, field
from typing import Final

from app.services.indexing import tokenize
from app.services.retrieval.candidates import RetrievalCandidate

RERANK_WEIGHTS: Final = {
    "vector": 0.35,
    "bm25": 0.30,
    "graph": 0.20,
    "file": 0.10,
    "diff": 0.05,
}


@dataclass(frozen=True)
class RankedRetrievalCandidate:
    chunk_id: str
    sources: list[str]
    final_score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0
    graph_score: float = 0.0
    file_relevance_score: float = 0.0
    diff_relevance_score: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


def rerank_candidates(
    candidates: list[RetrievalCandidate],
    query: str,
    *,
    top_k: int | None = None,
) -> list[RankedRetrievalCandidate]:
    if not candidates or top_k == 0:
        return []

    max_bm25_score = _max_score(candidate.bm25_score for candidate in candidates)
    max_vector_score = _max_score(candidate.vector_score for candidate in candidates)
    max_graph_score = _max_score(candidate.graph_score for candidate in candidates)

    ranked = [
        _rank_candidate(
            candidate,
            query,
            max_bm25_score=max_bm25_score,
            max_vector_score=max_vector_score,
            max_graph_score=max_graph_score,
        )
        for candidate in candidates
    ]
    ranked = sorted(ranked, key=lambda candidate: (-candidate.final_score, candidate.chunk_id))
    return ranked if top_k is None else ranked[:top_k]


def _rank_candidate(
    candidate: RetrievalCandidate,
    query: str,
    *,
    max_bm25_score: float,
    max_vector_score: float,
    max_graph_score: float,
) -> RankedRetrievalCandidate:
    bm25_score = _normalize(candidate.bm25_score, max_bm25_score)
    vector_score = _normalize(candidate.vector_score, max_vector_score)
    graph_score = _normalize(candidate.graph_score, max_graph_score)
    file_relevance_score = _file_relevance_score(query, candidate.metadata)
    diff_relevance_score = candidate.diff_relevance_score
    final_score = (
        RERANK_WEIGHTS["vector"] * vector_score
        + RERANK_WEIGHTS["bm25"] * bm25_score
        + RERANK_WEIGHTS["graph"] * graph_score
        + RERANK_WEIGHTS["file"] * file_relevance_score
        + RERANK_WEIGHTS["diff"] * diff_relevance_score
    )
    metadata = dict(candidate.metadata)
    metadata["raw_scores"] = {
        "bm25": candidate.bm25_score,
        "vector": candidate.vector_score,
        "graph": candidate.graph_score,
        "file": candidate.file_relevance_score,
        "diff": candidate.diff_relevance_score,
    }
    return RankedRetrievalCandidate(
        chunk_id=candidate.chunk_id,
        sources=candidate.sources,
        final_score=final_score,
        bm25_score=bm25_score,
        vector_score=vector_score,
        graph_score=graph_score,
        file_relevance_score=file_relevance_score,
        diff_relevance_score=diff_relevance_score,
        metadata=metadata,
    )


def _file_relevance_score(query: str, metadata: dict[str, object]) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0

    file_path = metadata.get("file_path")
    if isinstance(file_path, str) and query_tokens.intersection(tokenize(file_path)):
        return 1.0

    symbol_name = metadata.get("symbol_name")
    if isinstance(symbol_name, str) and query_tokens.intersection(tokenize(symbol_name)):
        return 0.8

    return 0.0


def _max_score(scores) -> float:
    return max([score for score in scores if score > 0.0], default=0.0)


def _normalize(score: float, max_score: float) -> float:
    if score <= 0.0 or max_score <= 0.0:
        return 0.0
    return score / max_score
