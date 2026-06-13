from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.evaluation.dataset import EvaluationSample, EvaluationSampleType
from app.services.retrieval import RetrievalResult, retrieve_repository


VECTOR_ONLY_STRATEGY = "vector_only"
VECTOR_ONLY_TOP_K = 5
BM25_VECTOR_STRATEGY = "bm25_vector"
BM25_VECTOR_TOP_K = 5
BM25_VECTOR_GRAPH_STRATEGY = "bm25_vector_graph"
BM25_VECTOR_GRAPH_TOP_K = 5


@dataclass(frozen=True)
class EvaluationEvidenceRef:
    evidence_id: str
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    score: float
    sources: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "score": self.score,
            "sources": self.sources,
        }


@dataclass(frozen=True)
class VectorOnlyEvaluationResult:
    sample_id: str
    sample_type: str
    repository_key: str
    repository_id: str
    strategy: str
    query: str
    evidence_count: int
    vector_count: int
    latency_ms: int
    vector_disabled_reason: str | None = None
    error_message: str | None = None
    evidences: list[EvaluationEvidenceRef] = field(default_factory=list)

    @property
    def vector_unavailable(self) -> bool:
        return self.vector_disabled_reason is not None

    @property
    def failed(self) -> bool:
        return self.error_message is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "sample_type": self.sample_type,
            "repository_key": self.repository_key,
            "repository_id": self.repository_id,
            "strategy": self.strategy,
            "query": self.query,
            "evidence_count": self.evidence_count,
            "vector_count": self.vector_count,
            "latency_ms": self.latency_ms,
            "vector_disabled_reason": self.vector_disabled_reason,
            "error_message": self.error_message,
            "evidences": [evidence.to_dict() for evidence in self.evidences],
        }


@dataclass(frozen=True)
class BM25VectorEvaluationResult:
    sample_id: str
    sample_type: str
    repository_key: str
    repository_id: str
    strategy: str
    query: str
    evidence_count: int
    bm25_count: int
    vector_count: int
    latency_ms: int
    vector_disabled_reason: str | None = None
    error_message: str | None = None
    evidences: list[EvaluationEvidenceRef] = field(default_factory=list)

    @property
    def vector_unavailable(self) -> bool:
        return self.vector_disabled_reason is not None

    @property
    def failed(self) -> bool:
        return self.error_message is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "sample_type": self.sample_type,
            "repository_key": self.repository_key,
            "repository_id": self.repository_id,
            "strategy": self.strategy,
            "query": self.query,
            "evidence_count": self.evidence_count,
            "bm25_count": self.bm25_count,
            "vector_count": self.vector_count,
            "latency_ms": self.latency_ms,
            "vector_disabled_reason": self.vector_disabled_reason,
            "error_message": self.error_message,
            "evidences": [evidence.to_dict() for evidence in self.evidences],
        }


@dataclass(frozen=True)
class BM25VectorGraphEvaluationResult:
    sample_id: str
    sample_type: str
    repository_key: str
    repository_id: str
    strategy: str
    query: str
    evidence_count: int
    bm25_count: int
    vector_count: int
    graph_count: int
    latency_ms: int
    vector_disabled_reason: str | None = None
    error_message: str | None = None
    evidences: list[EvaluationEvidenceRef] = field(default_factory=list)

    @property
    def vector_unavailable(self) -> bool:
        return self.vector_disabled_reason is not None

    @property
    def failed(self) -> bool:
        return self.error_message is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "sample_type": self.sample_type,
            "repository_key": self.repository_key,
            "repository_id": self.repository_id,
            "strategy": self.strategy,
            "query": self.query,
            "evidence_count": self.evidence_count,
            "bm25_count": self.bm25_count,
            "vector_count": self.vector_count,
            "graph_count": self.graph_count,
            "latency_ms": self.latency_ms,
            "vector_disabled_reason": self.vector_disabled_reason,
            "error_message": self.error_message,
            "evidences": [evidence.to_dict() for evidence in self.evidences],
        }


def run_vector_only_sample(
    db: Session,
    sample: EvaluationSample,
    *,
    repository_id: str,
    settings: Settings,
    top_k: int = VECTOR_ONLY_TOP_K,
) -> VectorOnlyEvaluationResult:
    query = _query_for_sample(sample)
    started = perf_counter()
    try:
        retrieval_result = retrieve_repository(
            db,
            repository_id,
            query,
            settings,
            top_k=top_k,
            use_bm25=False,
            use_vector=True,
            use_graph=False,
        )
    except Exception as exc:
        return VectorOnlyEvaluationResult(
            sample_id=sample.id,
            sample_type=sample.type.value,
            repository_key=sample.repository_key,
            repository_id=repository_id,
            strategy=VECTOR_ONLY_STRATEGY,
            query=query,
            evidence_count=0,
            vector_count=0,
            latency_ms=_elapsed_ms(started),
            error_message=str(exc),
        )

    return _vector_result_from_retrieval(
        sample=sample,
        repository_id=repository_id,
        query=query,
        retrieval_result=retrieval_result,
        latency_ms=_elapsed_ms(started),
    )


def run_bm25_vector_sample(
    db: Session,
    sample: EvaluationSample,
    *,
    repository_id: str,
    settings: Settings,
    top_k: int = BM25_VECTOR_TOP_K,
) -> BM25VectorEvaluationResult:
    query = _query_for_sample(sample)
    started = perf_counter()
    try:
        retrieval_result = retrieve_repository(
            db,
            repository_id,
            query,
            settings,
            top_k=top_k,
            use_bm25=True,
            use_vector=True,
            use_graph=False,
        )
    except Exception as exc:
        return BM25VectorEvaluationResult(
            sample_id=sample.id,
            sample_type=sample.type.value,
            repository_key=sample.repository_key,
            repository_id=repository_id,
            strategy=BM25_VECTOR_STRATEGY,
            query=query,
            evidence_count=0,
            bm25_count=0,
            vector_count=0,
            latency_ms=_elapsed_ms(started),
            error_message=str(exc),
        )

    return _bm25_vector_result_from_retrieval(
        sample=sample,
        repository_id=repository_id,
        query=query,
        retrieval_result=retrieval_result,
        latency_ms=_elapsed_ms(started),
    )


def run_bm25_vector_graph_sample(
    db: Session,
    sample: EvaluationSample,
    *,
    repository_id: str,
    settings: Settings,
    top_k: int = BM25_VECTOR_GRAPH_TOP_K,
) -> BM25VectorGraphEvaluationResult:
    query = _query_for_sample(sample)
    started = perf_counter()
    try:
        retrieval_result = retrieve_repository(
            db,
            repository_id,
            query,
            settings,
            top_k=top_k,
            use_bm25=True,
            use_vector=True,
            use_graph=True,
        )
    except Exception as exc:
        return BM25VectorGraphEvaluationResult(
            sample_id=sample.id,
            sample_type=sample.type.value,
            repository_key=sample.repository_key,
            repository_id=repository_id,
            strategy=BM25_VECTOR_GRAPH_STRATEGY,
            query=query,
            evidence_count=0,
            bm25_count=0,
            vector_count=0,
            graph_count=0,
            latency_ms=_elapsed_ms(started),
            error_message=str(exc),
        )

    return _bm25_vector_graph_result_from_retrieval(
        sample=sample,
        repository_id=repository_id,
        query=query,
        retrieval_result=retrieval_result,
        latency_ms=_elapsed_ms(started),
    )


def _vector_result_from_retrieval(
    *,
    sample: EvaluationSample,
    repository_id: str,
    query: str,
    retrieval_result: RetrievalResult,
    latency_ms: int,
) -> VectorOnlyEvaluationResult:
    return VectorOnlyEvaluationResult(
        sample_id=sample.id,
        sample_type=sample.type.value,
        repository_key=sample.repository_key,
        repository_id=repository_id,
        strategy=VECTOR_ONLY_STRATEGY,
        query=query,
        evidence_count=len(retrieval_result.evidences),
        vector_count=retrieval_result.debug.vector_count,
        latency_ms=latency_ms,
        vector_disabled_reason=retrieval_result.debug.vector_disabled_reason,
        evidences=_evidence_refs(retrieval_result),
    )


def _bm25_vector_result_from_retrieval(
    *,
    sample: EvaluationSample,
    repository_id: str,
    query: str,
    retrieval_result: RetrievalResult,
    latency_ms: int,
) -> BM25VectorEvaluationResult:
    return BM25VectorEvaluationResult(
        sample_id=sample.id,
        sample_type=sample.type.value,
        repository_key=sample.repository_key,
        repository_id=repository_id,
        strategy=BM25_VECTOR_STRATEGY,
        query=query,
        evidence_count=len(retrieval_result.evidences),
        bm25_count=retrieval_result.debug.bm25_count,
        vector_count=retrieval_result.debug.vector_count,
        latency_ms=latency_ms,
        vector_disabled_reason=retrieval_result.debug.vector_disabled_reason,
        evidences=_evidence_refs(retrieval_result),
    )


def _bm25_vector_graph_result_from_retrieval(
    *,
    sample: EvaluationSample,
    repository_id: str,
    query: str,
    retrieval_result: RetrievalResult,
    latency_ms: int,
) -> BM25VectorGraphEvaluationResult:
    return BM25VectorGraphEvaluationResult(
        sample_id=sample.id,
        sample_type=sample.type.value,
        repository_key=sample.repository_key,
        repository_id=repository_id,
        strategy=BM25_VECTOR_GRAPH_STRATEGY,
        query=query,
        evidence_count=len(retrieval_result.evidences),
        bm25_count=retrieval_result.debug.bm25_count,
        vector_count=retrieval_result.debug.vector_count,
        graph_count=retrieval_result.debug.graph_count,
        latency_ms=latency_ms,
        vector_disabled_reason=retrieval_result.debug.vector_disabled_reason,
        evidences=_evidence_refs(retrieval_result),
    )


def _evidence_refs(retrieval_result: RetrievalResult) -> list[EvaluationEvidenceRef]:
    return [
        EvaluationEvidenceRef(
            evidence_id=evidence.evidence_id,
            chunk_id=evidence.chunk_id,
            file_path=evidence.file_path,
            start_line=evidence.start_line,
            end_line=evidence.end_line,
            symbol_name=evidence.symbol_name,
            score=evidence.score,
            sources=evidence.sources,
        )
        for evidence in retrieval_result.evidences
    ]


def _query_for_sample(sample: EvaluationSample) -> str:
    if sample.type == EvaluationSampleType.REVIEW and sample.review_diff:
        return " ".join(
            [
                sample.question,
                *sample.expected_files[:3],
                *sample.expected_symbols[:3],
            ]
        )
    return sample.question


def _elapsed_ms(started: float) -> int:
    return max(int((perf_counter() - started) * 1000), 0)
