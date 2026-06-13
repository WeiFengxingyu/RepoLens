from dataclasses import dataclass

import pytest

from app.services.evaluation import (
    EvaluationEvidenceRef,
    EvaluationMetricsError,
    EvaluationSample,
    EvaluationSampleMetric,
    EvaluationSampleType,
    compute_aggregate_metrics,
    compute_sample_metrics,
    estimate_token_count,
)


@dataclass(frozen=True)
class FakeEvaluationResult:
    sample_id: str
    strategy: str
    query: str
    latency_ms: int
    error_message: str | None
    evidences: list[EvaluationEvidenceRef]


def test_compute_sample_metrics_calculates_hit_mrr_coverage_and_estimated_tokens() -> None:
    metric = compute_sample_metrics(
        _sample(
            expected_files=["app.py", "services/helper.py"],
            expected_symbols=["helper"],
        ),
        _result(
            evidences=[
                _evidence("ev-1", "unrelated.py", "noise"),
                _evidence("ev-2", "services/helper.py", "helper"),
            ],
            latency_ms=123,
            query="Where is helper?",
        ),
        token_character_count=17,
    )

    assert metric.hit_at_5 is True
    assert metric.mrr == 0.5
    assert metric.citation_coverage == 0.5
    assert metric.latency_ms == 123
    assert metric.token_count == 5
    assert metric.token_estimated is True
    assert metric.matched_files == ["services/helper.py"]
    assert metric.matched_symbols == ["helper"]
    assert metric.to_dict()["hit_at_5"] is True


def test_compute_sample_metrics_requires_symbol_hit_when_expected_symbols_exist() -> None:
    metric = compute_sample_metrics(
        _sample(expected_files=["app.py"], expected_symbols=["target_symbol"]),
        _result(evidences=[_evidence("ev-1", "app.py", "other_symbol")]),
    )

    assert metric.hit_at_5 is False
    assert metric.mrr == 1.0
    assert metric.citation_coverage == 1.0
    assert metric.matched_files == ["app.py"]
    assert metric.matched_symbols == []


def test_compute_sample_metrics_handles_additional_review_citation_files() -> None:
    metric = compute_sample_metrics(
        _sample(expected_files=["app.py", "risk.py"], expected_symbols=[]),
        _result(evidences=[_evidence("ev-1", "app.py", "main")]),
        additional_citation_files=["risk.py"],
        token_count=42,
    )

    assert metric.hit_at_5 is True
    assert metric.citation_coverage == 1.0
    assert metric.token_count == 42
    assert metric.token_estimated is False
    assert metric.matched_files == ["app.py", "risk.py"]


def test_compute_sample_metrics_sets_zero_scores_for_failed_result() -> None:
    metric = compute_sample_metrics(
        _sample(expected_files=["app.py"], expected_symbols=[]),
        _result(
            evidences=[_evidence("ev-1", "app.py", "main")],
            error_message="retrieval failed",
        ),
    )

    assert metric.failed is True
    assert metric.hit_at_5 is False
    assert metric.mrr == 0.0
    assert metric.citation_coverage == 0.0
    assert metric.error_message == "retrieval failed"


def test_compute_sample_metrics_limits_hit_to_top_five_but_keeps_mrr_consistent() -> None:
    evidences = [
        _evidence(f"ev-{index}", f"noise-{index}.py", f"noise_{index}")
        for index in range(1, 6)
    ]
    evidences.append(_evidence("ev-6", "target.py", "target"))

    metric = compute_sample_metrics(
        _sample(expected_files=["target.py"], expected_symbols=[]),
        _result(evidences=evidences),
    )

    assert metric.hit_at_5 is False
    assert metric.mrr == 0.0
    assert metric.citation_coverage == 0.0


def test_compute_aggregate_metrics_calculates_strategy_summary() -> None:
    metrics = [
        EvaluationSampleMetric(
            sample_id="s1",
            sample_type="location",
            repository_key="python_demo",
            strategy="bm25_vector_graph",
            hit_at_5=True,
            mrr=1.0,
            citation_coverage=1.0,
            latency_ms=100,
            token_count=10,
            token_estimated=True,
        ),
        EvaluationSampleMetric(
            sample_id="s2",
            sample_type="architecture",
            repository_key="python_demo",
            strategy="bm25_vector_graph",
            hit_at_5=False,
            mrr=0.5,
            citation_coverage=0.5,
            latency_ms=300,
            token_count=30,
            token_estimated=False,
        ),
        EvaluationSampleMetric(
            sample_id="s3",
            sample_type="review",
            repository_key="python_demo",
            strategy="bm25_vector_graph",
            hit_at_5=False,
            mrr=0.0,
            citation_coverage=0.0,
            latency_ms=900,
            token_count=50,
            token_estimated=True,
            error_message="failed",
        ),
    ]

    aggregate = compute_aggregate_metrics(metrics)

    assert aggregate.strategy == "bm25_vector_graph"
    assert aggregate.sample_count == 3
    assert aggregate.hit_at_5 == 0.3333
    assert aggregate.mrr == 0.5
    assert aggregate.citation_coverage == 0.5
    assert aggregate.avg_latency_ms == 433.3333
    assert aggregate.p50_latency_ms == 300
    assert aggregate.p95_latency_ms == 900
    assert aggregate.avg_token_count == 30.0
    assert aggregate.token_estimated is True
    assert aggregate.token_estimated_count == 2
    assert aggregate.error_count == 1
    assert aggregate.to_dict()["error_count"] == 1


def test_compute_aggregate_metrics_rejects_empty_or_mixed_strategy_metrics() -> None:
    with pytest.raises(EvaluationMetricsError):
        compute_aggregate_metrics([])

    with pytest.raises(EvaluationMetricsError):
        compute_aggregate_metrics(
            [
                EvaluationSampleMetric(
                    sample_id="s1",
                    sample_type="location",
                    repository_key="python_demo",
                    strategy="vector_only",
                    hit_at_5=True,
                    mrr=1.0,
                    citation_coverage=1.0,
                    latency_ms=1,
                    token_count=1,
                    token_estimated=True,
                ),
                EvaluationSampleMetric(
                    sample_id="s2",
                    sample_type="location",
                    repository_key="python_demo",
                    strategy="bm25_vector",
                    hit_at_5=True,
                    mrr=1.0,
                    citation_coverage=1.0,
                    latency_ms=1,
                    token_count=1,
                    token_estimated=True,
                ),
            ]
        )


def test_estimate_token_count_uses_four_character_bucket() -> None:
    assert estimate_token_count(0) == 0
    assert estimate_token_count(1) == 1
    assert estimate_token_count(4) == 1
    assert estimate_token_count(5) == 2
    assert estimate_token_count(-10) == 0


def _sample(
    *,
    expected_files: list[str],
    expected_symbols: list[str],
) -> EvaluationSample:
    return EvaluationSample(
        id="sample-1",
        type=EvaluationSampleType.LOCATION,
        repository_key="python_demo",
        question="Where is the target?",
        expected_files=expected_files,
        expected_symbols=expected_symbols,
    )


def _result(
    *,
    evidences: list[EvaluationEvidenceRef],
    latency_ms: int = 10,
    query: str = "query",
    error_message: str | None = None,
) -> FakeEvaluationResult:
    return FakeEvaluationResult(
        sample_id="sample-1",
        strategy="bm25_vector_graph",
        query=query,
        latency_ms=latency_ms,
        error_message=error_message,
        evidences=evidences,
    )


def _evidence(evidence_id: str, file_path: str, symbol_name: str) -> EvaluationEvidenceRef:
    return EvaluationEvidenceRef(
        evidence_id=evidence_id,
        chunk_id=f"chunk-{evidence_id}",
        file_path=file_path,
        start_line=1,
        end_line=2,
        symbol_name=symbol_name,
        score=0.8,
        sources=["bm25"],
    )
