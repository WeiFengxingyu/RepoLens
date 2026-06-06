from dataclasses import dataclass, field
from typing import Final

from app.services.graph import GraphExpansionCandidate
from app.services.indexing import BM25SearchResult, VectorSearchResult

SOURCE_ORDER: Final = ["bm25", "vector", "graph_expand"]


@dataclass(frozen=True)
class RetrievalCandidate:
    chunk_id: str
    sources: list[str]
    bm25_score: float = 0.0
    vector_score: float = 0.0
    graph_score: float = 0.0
    file_relevance_score: float = 0.0
    diff_relevance_score: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class _CandidateAccumulator:
    chunk_id: str
    sources: set[str] = field(default_factory=set)
    bm25_score: float = 0.0
    vector_score: float = 0.0
    graph_score: float = 0.0
    file_relevance_score: float = 0.0
    diff_relevance_score: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


def merge_candidates(
    *,
    bm25_candidates: list[BM25SearchResult] | None = None,
    vector_candidates: list[VectorSearchResult] | None = None,
    graph_candidates: list[GraphExpansionCandidate] | None = None,
) -> list[RetrievalCandidate]:
    merged: dict[str, _CandidateAccumulator] = {}

    for candidate in bm25_candidates or []:
        accumulator = _get_accumulator(merged, candidate.chunk_id)
        accumulator.sources.add("bm25")
        accumulator.bm25_score = max(accumulator.bm25_score, candidate.score)
        _merge_matched_terms(accumulator.metadata, candidate.matched_terms)

    for candidate in vector_candidates or []:
        accumulator = _get_accumulator(merged, candidate.chunk_id)
        accumulator.sources.add("vector")
        if candidate.vector_score >= accumulator.vector_score:
            accumulator.vector_score = candidate.vector_score
            accumulator.metadata.update(candidate.metadata)

    for candidate in graph_candidates or []:
        accumulator = _get_accumulator(merged, candidate.chunk_id)
        accumulator.sources.add("graph_expand")
        if candidate.graph_score >= accumulator.graph_score:
            accumulator.graph_score = candidate.graph_score
            accumulator.metadata.update(candidate.metadata)
            accumulator.metadata["graph_distance"] = candidate.graph_distance
            accumulator.metadata["seed_chunk_id"] = candidate.seed_chunk_id
            accumulator.metadata["relation_type"] = candidate.relation_type

    return sorted(
        [_to_retrieval_candidate(accumulator) for accumulator in merged.values()],
        key=lambda candidate: (-_max_source_score(candidate), candidate.chunk_id),
    )


def _get_accumulator(
    merged: dict[str, _CandidateAccumulator],
    chunk_id: str,
) -> _CandidateAccumulator:
    accumulator = merged.get(chunk_id)
    if accumulator is None:
        accumulator = _CandidateAccumulator(chunk_id=chunk_id)
        merged[chunk_id] = accumulator
    return accumulator


def _merge_matched_terms(metadata: dict[str, object], matched_terms: list[str]) -> None:
    current = metadata.get("bm25_matched_terms", [])
    if not isinstance(current, list):
        current = []
    terms = sorted({str(term) for term in [*current, *matched_terms]})
    metadata["bm25_matched_terms"] = terms


def _to_retrieval_candidate(accumulator: _CandidateAccumulator) -> RetrievalCandidate:
    return RetrievalCandidate(
        chunk_id=accumulator.chunk_id,
        sources=[source for source in SOURCE_ORDER if source in accumulator.sources],
        bm25_score=accumulator.bm25_score,
        vector_score=accumulator.vector_score,
        graph_score=accumulator.graph_score,
        file_relevance_score=accumulator.file_relevance_score,
        diff_relevance_score=accumulator.diff_relevance_score,
        metadata=dict(accumulator.metadata),
    )


def _max_source_score(candidate: RetrievalCandidate) -> float:
    return max(candidate.bm25_score, candidate.vector_score, candidate.graph_score)
