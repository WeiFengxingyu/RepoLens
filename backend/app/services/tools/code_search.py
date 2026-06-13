from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.retrieval import Evidence, retrieve_repository

CODE_SEARCH_MAX_TOP_K = 50


class CodeSearchError(ValueError):
    """Raised when code_search input is outside the Phase 4 tool contract."""


@dataclass(frozen=True)
class CodeSearchEvidence:
    evidence_id: str
    chunk_id: str
    repository_id: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    language: str
    source: str
    sources: list[str]
    score: float
    bm25_score: float
    vector_score: float
    graph_score: float
    snippet: str
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "chunk_id": self.chunk_id,
            "repository_id": self.repository_id,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "language": self.language,
            "source": self.source,
            "sources": self.sources,
            "score": self.score,
            "bm25_score": self.bm25_score,
            "vector_score": self.vector_score,
            "graph_score": self.graph_score,
            "snippet": self.snippet,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CodeSearchDebug:
    bm25_count: int
    vector_count: int
    graph_count: int
    merged_count: int
    evidence_count: int
    vector_disabled_reason: str | None
    context_truncated: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "bm25_count": self.bm25_count,
            "vector_count": self.vector_count,
            "graph_count": self.graph_count,
            "merged_count": self.merged_count,
            "evidence_count": self.evidence_count,
            "vector_disabled_reason": self.vector_disabled_reason,
            "context_truncated": self.context_truncated,
        }


@dataclass(frozen=True)
class CodeSearchResult:
    repository_id: str
    query: str
    evidences: list[CodeSearchEvidence]
    debug: CodeSearchDebug
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "repository_id": self.repository_id,
            "query": self.query,
            "evidences": [evidence.to_dict() for evidence in self.evidences],
            "debug": self.debug.to_dict(),
            "warnings": self.warnings,
        }


def code_search(
    db: Session,
    repository_id: str,
    query: str,
    settings: Settings,
    *,
    top_k: int = 8,
    use_bm25: bool = True,
    use_vector: bool = True,
    use_graph: bool = True,
) -> CodeSearchResult:
    normalized_query = " ".join(query.strip().split())
    if not normalized_query:
        raise CodeSearchError("query is required.")
    if top_k < 1 or top_k > CODE_SEARCH_MAX_TOP_K:
        raise CodeSearchError(f"top_k must be between 1 and {CODE_SEARCH_MAX_TOP_K}.")
    if not any([use_bm25, use_vector, use_graph]):
        raise CodeSearchError("At least one retrieval source must be enabled.")

    retrieval_result = retrieve_repository(
        db,
        repository_id,
        normalized_query,
        settings,
        top_k=top_k,
        use_bm25=use_bm25,
        use_vector=use_vector,
        use_graph=use_graph,
    )
    warnings = []
    if retrieval_result.debug.vector_disabled_reason:
        warnings.append(
            f"Vector retrieval disabled: {retrieval_result.debug.vector_disabled_reason}"
        )

    return CodeSearchResult(
        repository_id=retrieval_result.repository_id,
        query=retrieval_result.query,
        evidences=[_evidence_to_tool_evidence(evidence) for evidence in retrieval_result.evidences],
        debug=CodeSearchDebug(
            bm25_count=retrieval_result.debug.bm25_count,
            vector_count=retrieval_result.debug.vector_count,
            graph_count=retrieval_result.debug.graph_count,
            merged_count=retrieval_result.debug.merged_count,
            evidence_count=retrieval_result.debug.evidence_count,
            vector_disabled_reason=retrieval_result.debug.vector_disabled_reason,
            context_truncated=retrieval_result.debug.context_truncated,
        ),
        warnings=warnings,
    )


def _evidence_to_tool_evidence(evidence: Evidence) -> CodeSearchEvidence:
    return CodeSearchEvidence(
        evidence_id=evidence.evidence_id,
        chunk_id=evidence.chunk_id,
        repository_id=evidence.repository_id,
        file_path=evidence.file_path,
        start_line=evidence.start_line,
        end_line=evidence.end_line,
        symbol_name=evidence.symbol_name,
        symbol_type=evidence.symbol_type,
        language=evidence.language,
        source=evidence.source,
        sources=evidence.sources,
        score=evidence.score,
        bm25_score=evidence.bm25_score,
        vector_score=evidence.vector_score,
        graph_score=evidence.graph_score,
        snippet=evidence.snippet,
        metadata=evidence.metadata,
    )
