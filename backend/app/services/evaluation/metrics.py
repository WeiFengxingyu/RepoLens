from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Protocol, Sequence

from app.services.evaluation.dataset import EvaluationSample


DEFAULT_HIT_TOP_K = 5


class EvaluationMetricsError(ValueError):
    """Raised when Phase 5 evaluation metrics cannot be computed."""


class EvaluationResultLike(Protocol):
    sample_id: str
    strategy: str
    query: str
    latency_ms: int
    error_message: str | None
    evidences: Sequence[object]


@dataclass(frozen=True)
class EvaluationSampleMetric:
    sample_id: str
    sample_type: str
    repository_key: str
    strategy: str
    hit_at_5: bool
    mrr: float
    citation_coverage: float
    latency_ms: int
    token_count: int
    token_estimated: bool
    matched_files: list[str] = field(default_factory=list)
    matched_symbols: list[str] = field(default_factory=list)
    error_message: str | None = None

    @property
    def failed(self) -> bool:
        return self.error_message is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "sample_type": self.sample_type,
            "repository_key": self.repository_key,
            "strategy": self.strategy,
            "hit_at_5": self.hit_at_5,
            "mrr": self.mrr,
            "citation_coverage": self.citation_coverage,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "token_estimated": self.token_estimated,
            "matched_files": self.matched_files,
            "matched_symbols": self.matched_symbols,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class EvaluationAggregateMetrics:
    strategy: str
    sample_count: int
    hit_at_5: float
    mrr: float
    citation_coverage: float
    avg_latency_ms: float
    p50_latency_ms: int
    p95_latency_ms: int
    avg_token_count: float
    token_estimated: bool
    token_estimated_count: int
    error_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "sample_count": self.sample_count,
            "hit_at_5": self.hit_at_5,
            "mrr": self.mrr,
            "citation_coverage": self.citation_coverage,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "avg_token_count": self.avg_token_count,
            "token_estimated": self.token_estimated,
            "token_estimated_count": self.token_estimated_count,
            "error_count": self.error_count,
        }


def compute_sample_metrics(
    sample: EvaluationSample,
    result: EvaluationResultLike,
    *,
    top_k: int = DEFAULT_HIT_TOP_K,
    token_count: int | None = None,
    token_character_count: int | None = None,
    additional_citation_files: Sequence[str] | None = None,
) -> EvaluationSampleMetric:
    top_evidences = list(result.evidences[: max(top_k, 0)])
    evidence_files = [_normalize_path(_evidence_file_path(evidence)) for evidence in top_evidences]
    evidence_symbols = [_evidence_symbol_name(evidence) for evidence in top_evidences]

    expected_files = [_normalize_path(file_path) for file_path in sample.expected_files]
    expected_symbols = [symbol for symbol in sample.expected_symbols if symbol]
    matched_files = _matched_files(sample.expected_files, evidence_files, additional_citation_files)
    matched_symbols = [symbol for symbol in expected_symbols if symbol in set(evidence_symbols)]

    file_hit = bool(matched_files)
    symbol_hit = not expected_symbols or bool(matched_symbols)
    error_message = result.error_message
    hit_at_5 = bool(file_hit and symbol_hit and error_message is None)
    mrr = 0.0 if error_message is not None else _mrr(top_evidences, expected_files, expected_symbols)
    citation_coverage = (
        0.0
        if error_message is not None
        else _citation_coverage(sample.expected_files, evidence_files, additional_citation_files)
    )
    resolved_token_count, token_estimated = _resolve_token_count(
        result,
        token_count=token_count,
        token_character_count=token_character_count,
    )

    return EvaluationSampleMetric(
        sample_id=sample.id,
        sample_type=sample.type.value,
        repository_key=sample.repository_key,
        strategy=result.strategy,
        hit_at_5=hit_at_5,
        mrr=mrr,
        citation_coverage=citation_coverage,
        latency_ms=max(int(result.latency_ms), 0),
        token_count=resolved_token_count,
        token_estimated=token_estimated,
        matched_files=matched_files,
        matched_symbols=matched_symbols,
        error_message=error_message,
    )


def compute_aggregate_metrics(
    metrics: Sequence[EvaluationSampleMetric],
    *,
    strategy: str | None = None,
) -> EvaluationAggregateMetrics:
    if not metrics:
        raise EvaluationMetricsError("Cannot aggregate an empty metrics list.")

    resolved_strategy = strategy or metrics[0].strategy
    mismatched = [metric.strategy for metric in metrics if metric.strategy != resolved_strategy]
    if mismatched:
        raise EvaluationMetricsError("Cannot aggregate metrics from multiple strategies.")

    sample_count = len(metrics)
    latencies = [metric.latency_ms for metric in metrics]
    token_counts = [metric.token_count for metric in metrics]
    token_estimated_count = sum(1 for metric in metrics if metric.token_estimated)

    return EvaluationAggregateMetrics(
        strategy=resolved_strategy,
        sample_count=sample_count,
        hit_at_5=_round_ratio(sum(1 for metric in metrics if metric.hit_at_5), sample_count),
        mrr=_round_float(sum(metric.mrr for metric in metrics) / sample_count),
        citation_coverage=_round_float(
            sum(metric.citation_coverage for metric in metrics) / sample_count
        ),
        avg_latency_ms=_round_float(sum(latencies) / sample_count),
        p50_latency_ms=_nearest_rank_percentile(latencies, 0.50),
        p95_latency_ms=_nearest_rank_percentile(latencies, 0.95),
        avg_token_count=_round_float(sum(token_counts) / sample_count),
        token_estimated=token_estimated_count > 0,
        token_estimated_count=token_estimated_count,
        error_count=sum(1 for metric in metrics if metric.failed),
    )


def estimate_token_count(character_count: int) -> int:
    return max(ceil(max(character_count, 0) / 4), 0)


def _matched_files(
    expected_files: Sequence[str],
    evidence_files: Sequence[str],
    additional_citation_files: Sequence[str] | None,
) -> list[str]:
    cited_files = {
        *evidence_files,
        *[_normalize_path(file_path) for file_path in additional_citation_files or []],
    }
    return [file_path for file_path in expected_files if _normalize_path(file_path) in cited_files]


def _citation_coverage(
    expected_files: Sequence[str],
    evidence_files: Sequence[str],
    additional_citation_files: Sequence[str] | None,
) -> float:
    if not expected_files:
        return 0.0
    return _round_float(len(_matched_files(expected_files, evidence_files, additional_citation_files)) / len(expected_files))


def _mrr(
    evidences: Sequence[object],
    expected_files: Sequence[str],
    expected_symbols: Sequence[str],
) -> float:
    expected_file_set = set(expected_files)
    expected_symbol_set = set(expected_symbols)
    for rank, evidence in enumerate(evidences, start=1):
        file_matches = _normalize_path(_evidence_file_path(evidence)) in expected_file_set
        symbol_matches = (
            bool(expected_symbol_set)
            and _evidence_symbol_name(evidence) in expected_symbol_set
        )
        if file_matches or symbol_matches:
            return _round_float(1 / rank)
    return 0.0


def _resolve_token_count(
    result: EvaluationResultLike,
    *,
    token_count: int | None,
    token_character_count: int | None,
) -> tuple[int, bool]:
    if token_count is not None:
        return max(int(token_count), 0), False
    if token_character_count is not None:
        return estimate_token_count(token_character_count), True

    character_count = len(result.query)
    for evidence in result.evidences:
        character_count += len(_evidence_file_path(evidence))
        character_count += len(_evidence_symbol_name(evidence))
    return estimate_token_count(character_count), True


def _evidence_file_path(evidence: object) -> str:
    return str(getattr(evidence, "file_path", ""))


def _evidence_symbol_name(evidence: object) -> str:
    return str(getattr(evidence, "symbol_name", ""))


def _normalize_path(path_value: str) -> str:
    return path_value.replace("\\", "/").strip()


def _nearest_rank_percentile(values: Sequence[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(ceil(percentile * len(ordered)) - 1, 0)
    return int(ordered[min(rank, len(ordered) - 1)])


def _round_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _round_float(numerator / denominator)


def _round_float(value: float) -> float:
    return round(float(value), 4)
