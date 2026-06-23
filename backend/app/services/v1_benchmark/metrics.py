from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from statistics import mean
from typing import Any, Sequence

from app.services.v1_benchmark.dataset import V1BenchmarkMCPToolCall, V1BenchmarkSample


@dataclass(frozen=True)
class V1BenchmarkReviewSampleMetrics:
    risk_hit: bool
    citation_coverage: float
    unsupported_claim_rate: float
    latency_ms: int
    token_count: int
    matched_files: list[str] = field(default_factory=list)
    matched_risk_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "risk_hit": self.risk_hit,
            "citation_coverage": self.citation_coverage,
            "unsupported_claim_rate": self.unsupported_claim_rate,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "matched_files": self.matched_files,
            "matched_risk_keywords": self.matched_risk_keywords,
        }


@dataclass(frozen=True)
class V1BenchmarkReviewMetrics:
    sample_count: int
    risk_hit_rate: float
    citation_coverage: float
    unsupported_claim_rate: float
    avg_latency_ms: float
    avg_token_count: float
    error_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "risk_hit_rate": self.risk_hit_rate,
            "citation_coverage": self.citation_coverage,
            "unsupported_claim_rate": self.unsupported_claim_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_token_count": self.avg_token_count,
            "error_count": self.error_count,
        }


@dataclass(frozen=True)
class V1BenchmarkMultiAgentSampleMetrics:
    risk_hit: bool
    citation_coverage: float
    dissent_useful: bool
    arbiter_resolved: bool
    latency_ms: int
    token_count: int
    token_overhead_ratio: float
    dissent_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "risk_hit": self.risk_hit,
            "citation_coverage": self.citation_coverage,
            "dissent_useful": self.dissent_useful,
            "arbiter_resolved": self.arbiter_resolved,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "token_overhead_ratio": self.token_overhead_ratio,
            "dissent_count": self.dissent_count,
        }


@dataclass(frozen=True)
class V1BenchmarkMultiAgentMetrics:
    sample_count: int
    risk_hit_rate: float
    citation_coverage: float
    dissent_usefulness: float
    arbiter_resolution_rate: float
    token_overhead_ratio: float
    avg_latency_ms: float
    error_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "risk_hit_rate": self.risk_hit_rate,
            "citation_coverage": self.citation_coverage,
            "dissent_usefulness": self.dissent_usefulness,
            "arbiter_resolution_rate": self.arbiter_resolution_rate,
            "token_overhead_ratio": self.token_overhead_ratio,
            "avg_latency_ms": self.avg_latency_ms,
            "error_count": self.error_count,
        }


@dataclass(frozen=True)
class V1BenchmarkMCPSampleMetrics:
    tool_name: str
    success_correct: bool
    permission_correct: bool
    latency_ms: int
    actual_success: bool
    actual_permission_decision: str | None
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "tool_name": self.tool_name,
            "success_correct": self.success_correct,
            "permission_correct": self.permission_correct,
            "latency_ms": self.latency_ms,
            "actual_success": self.actual_success,
            "actual_permission_decision": self.actual_permission_decision,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class V1BenchmarkMCPMetrics:
    tool_call_count: int
    tool_success_rate: float
    permission_denial_correctness: float
    avg_latency_ms: float
    error_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "tool_call_count": self.tool_call_count,
            "tool_success_rate": self.tool_success_rate,
            "permission_denial_correctness": self.permission_denial_correctness,
            "avg_latency_ms": self.avg_latency_ms,
            "error_count": self.error_count,
        }


def compute_review_sample_metrics(
    sample: V1BenchmarkSample,
    review_payload: dict[str, Any],
    *,
    latency_ms: int,
    error_message: str | None = None,
) -> V1BenchmarkReviewSampleMetrics:
    risks = _dict_list(review_payload.get("risks"))
    citations = _dict_list(review_payload.get("citations"))
    matched_keywords = _matched_risk_keywords(sample, risks)
    matched_files = _matched_files(sample.expected_files, _citation_files(citations))
    unsupported_claim_rate = _unsupported_claim_rate(risks)
    token_count = estimate_token_count(_payload_character_count(review_payload))
    return V1BenchmarkReviewSampleMetrics(
        risk_hit=bool(matched_keywords) and error_message is None,
        citation_coverage=0.0
        if error_message
        else _coverage(sample.expected_files, _citation_files(citations)),
        unsupported_claim_rate=1.0 if error_message else unsupported_claim_rate,
        latency_ms=max(latency_ms, 0),
        token_count=token_count,
        matched_files=matched_files,
        matched_risk_keywords=matched_keywords,
    )


def aggregate_review_metrics(
    metrics: Sequence[V1BenchmarkReviewSampleMetrics],
    *,
    error_count: int = 0,
) -> V1BenchmarkReviewMetrics:
    if not metrics:
        return V1BenchmarkReviewMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0, error_count)
    return V1BenchmarkReviewMetrics(
        sample_count=len(metrics),
        risk_hit_rate=_ratio(sum(1 for metric in metrics if metric.risk_hit), len(metrics)),
        citation_coverage=_average([metric.citation_coverage for metric in metrics]),
        unsupported_claim_rate=_average([metric.unsupported_claim_rate for metric in metrics]),
        avg_latency_ms=_average([metric.latency_ms for metric in metrics]),
        avg_token_count=_average([metric.token_count for metric in metrics]),
        error_count=error_count,
    )


def compute_multi_agent_sample_metrics(
    sample: V1BenchmarkSample,
    multi_agent_payload: dict[str, Any],
    *,
    latency_ms: int,
    single_review_token_count: int,
    error_message: str | None = None,
) -> V1BenchmarkMultiAgentSampleMetrics:
    review_metrics = compute_review_sample_metrics(
        sample,
        multi_agent_payload,
        latency_ms=latency_ms,
        error_message=error_message,
    )
    comparison = _dict_value(multi_agent_payload.get("comparison"))
    arbiter_decision = _dict_value(multi_agent_payload.get("arbiter_decision"))
    dissent = _dict_list(multi_agent_payload.get("dissent"))
    token_count = int(comparison.get("token_estimate") or review_metrics.token_count)
    token_overhead_ratio = _round_float(
        token_count / max(single_review_token_count, 1)
    )
    return V1BenchmarkMultiAgentSampleMetrics(
        risk_hit=review_metrics.risk_hit,
        citation_coverage=review_metrics.citation_coverage,
        dissent_useful=_dissent_useful(sample, dissent),
        arbiter_resolved=_arbiter_resolved(arbiter_decision),
        latency_ms=max(latency_ms, 0),
        token_count=token_count,
        token_overhead_ratio=token_overhead_ratio,
        dissent_count=len(dissent),
    )


def aggregate_multi_agent_metrics(
    metrics: Sequence[V1BenchmarkMultiAgentSampleMetrics],
    *,
    error_count: int = 0,
) -> V1BenchmarkMultiAgentMetrics:
    if not metrics:
        return V1BenchmarkMultiAgentMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, error_count)
    return V1BenchmarkMultiAgentMetrics(
        sample_count=len(metrics),
        risk_hit_rate=_ratio(sum(1 for metric in metrics if metric.risk_hit), len(metrics)),
        citation_coverage=_average([metric.citation_coverage for metric in metrics]),
        dissent_usefulness=_ratio(sum(1 for metric in metrics if metric.dissent_useful), len(metrics)),
        arbiter_resolution_rate=_ratio(
            sum(1 for metric in metrics if metric.arbiter_resolved), len(metrics)
        ),
        token_overhead_ratio=_average([metric.token_overhead_ratio for metric in metrics]),
        avg_latency_ms=_average([metric.latency_ms for metric in metrics]),
        error_count=error_count,
    )


def compute_mcp_sample_metrics(
    expected_call: V1BenchmarkMCPToolCall,
    *,
    actual_success: bool,
    actual_permission_decision: str | None,
    latency_ms: int,
    error_message: str | None = None,
) -> V1BenchmarkMCPSampleMetrics:
    return V1BenchmarkMCPSampleMetrics(
        tool_name=expected_call.tool_name,
        success_correct=actual_success == expected_call.expect_success,
        permission_correct=actual_permission_decision == expected_call.expect_permission_decision,
        latency_ms=max(latency_ms, 0),
        actual_success=actual_success,
        actual_permission_decision=actual_permission_decision,
        error_message=error_message,
    )


def aggregate_mcp_metrics(metrics: Sequence[V1BenchmarkMCPSampleMetrics]) -> V1BenchmarkMCPMetrics:
    if not metrics:
        return V1BenchmarkMCPMetrics(0, 0.0, 0.0, 0.0, 0)
    return V1BenchmarkMCPMetrics(
        tool_call_count=len(metrics),
        tool_success_rate=_ratio(sum(1 for metric in metrics if metric.success_correct), len(metrics)),
        permission_denial_correctness=_ratio(
            sum(1 for metric in metrics if metric.permission_correct), len(metrics)
        ),
        avg_latency_ms=_average([metric.latency_ms for metric in metrics]),
        error_count=sum(1 for metric in metrics if metric.error_message),
    )


def estimate_token_count(character_count: int) -> int:
    return max(ceil(max(character_count, 0) / 4), 0)


def _matched_risk_keywords(sample: V1BenchmarkSample, risks: list[dict[str, Any]]) -> list[str]:
    matched: list[str] = []
    for expected_risk in sample.expected_risks:
        keyword_hit: list[str] = []
        file_hit = False
        for risk in risks:
            risk_text = " ".join(
                str(value)
                for value in [
                    risk.get("title"),
                    risk.get("reason"),
                    _dict_value(risk.get("location")).get("file_path"),
                ]
                if value is not None
            ).lower()
            if expected_risk.file_path.lower() not in risk_text:
                continue
            file_hit = True
            keyword_hit.extend(
                keyword for keyword in expected_risk.title_keywords if keyword in risk_text
            )
        if file_hit and keyword_hit:
            matched.extend(keyword_hit)
    return _deduplicate(matched)


def _matched_files(expected_files: Sequence[str], citation_files: Sequence[str]) -> list[str]:
    normalized_citations = {_normalize_path(file_path) for file_path in citation_files}
    return [
        file_path
        for file_path in expected_files
        if _normalize_path(file_path) in normalized_citations
    ]


def _coverage(expected_files: Sequence[str], citation_files: Sequence[str]) -> float:
    if not expected_files:
        return 0.0
    return _ratio(len(_matched_files(expected_files, citation_files)), len(expected_files))


def _citation_files(citations: list[dict[str, Any]]) -> list[str]:
    return [str(citation.get("file_path") or "") for citation in citations if citation.get("file_path")]


def _unsupported_claim_rate(risks: list[dict[str, Any]]) -> float:
    actionable = [
        risk
        for risk in risks
        if str(risk.get("severity") or "").lower() in {"medium", "high"}
    ]
    if not actionable:
        return 0.0
    unsupported = [
        risk for risk in actionable if not _string_list_value(risk.get("evidence_ids"))
    ]
    return _ratio(len(unsupported), len(actionable))


def _dissent_useful(sample: V1BenchmarkSample, dissent: list[dict[str, Any]]) -> bool:
    labels = {label.lower() for label in sample.expected_labels}
    if labels.intersection({"security", "permissions", "tenant", "auth"}):
        return bool(dissent)
    return True


def _arbiter_resolved(arbiter_decision: dict[str, Any]) -> bool:
    return (
        int(arbiter_decision.get("accepted") or 0)
        + int(arbiter_decision.get("rejected") or 0)
        + int(arbiter_decision.get("downgraded") or 0)
        + int(arbiter_decision.get("dissent_count") or 0)
    ) > 0


def _payload_character_count(payload: dict[str, Any]) -> int:
    return len(str(payload.get("summary") or "")) + len(str(payload.get("markdown") or "")) + len(
        str(payload.get("risks") or "")
    )


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list_value(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _normalize_path(path_value: str) -> str:
    return path_value.replace("\\", "/").strip()


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _round_float(numerator / denominator)


def _average(values: Sequence[int | float]) -> float:
    if not values:
        return 0.0
    return _round_float(mean(values))


def _round_float(value: float) -> float:
    return round(float(value), 4)


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated
