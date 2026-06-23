from app.services.v1_benchmark import (
    aggregate_mcp_metrics,
    aggregate_multi_agent_metrics,
    aggregate_review_metrics,
    compute_mcp_sample_metrics,
    compute_multi_agent_sample_metrics,
    compute_review_sample_metrics,
)
from app.services.v1_benchmark.dataset import V1BenchmarkMCPToolCall, parse_v1_benchmark_sample


def test_review_metrics_compute_risk_hit_citation_and_unsupported_claim_rate() -> None:
    sample = _sample()

    metrics = compute_review_sample_metrics(
        sample,
        {
            "risks": [
                {
                    "title": "Token security risk",
                    "severity": "medium",
                    "location": {"file_path": "app/auth/tokens.py"},
                    "reason": "token handling changed",
                    "evidence_ids": ["ev-1"],
                },
                {
                    "title": "Unsupported billing risk",
                    "severity": "high",
                    "location": {"file_path": "app/auth/tokens.py"},
                    "reason": "no evidence",
                    "evidence_ids": [],
                },
            ],
            "citations": [{"file_path": "app/auth/tokens.py"}],
            "markdown": "report",
        },
        latency_ms=25,
    )

    assert metrics.risk_hit is True
    assert metrics.citation_coverage == 1.0
    assert metrics.unsupported_claim_rate == 0.5
    assert metrics.matched_risk_keywords == ["token", "security"]
    aggregate = aggregate_review_metrics([metrics])
    assert aggregate.risk_hit_rate == 1.0
    assert aggregate.unsupported_claim_rate == 0.5


def test_multi_agent_metrics_track_dissent_arbiter_and_token_overhead() -> None:
    sample = _sample(labels=["security"])

    metrics = compute_multi_agent_sample_metrics(
        sample,
        {
            "risks": [
                {
                    "title": "Token security risk",
                    "severity": "medium",
                    "location": {"file_path": "app/auth/tokens.py"},
                    "reason": "token handling changed",
                    "evidence_ids": ["ev-1"],
                }
            ],
            "citations": [{"file_path": "app/auth/tokens.py"}],
            "comparison": {"token_estimate": 300},
            "dissent": [{"type": "security_evidence_gap"}],
            "arbiter_decision": {
                "accepted": 1,
                "rejected": 0,
                "downgraded": 0,
                "dissent_count": 1,
            },
        },
        latency_ms=40,
        single_review_token_count=100,
    )

    assert metrics.risk_hit is True
    assert metrics.dissent_useful is True
    assert metrics.arbiter_resolved is True
    assert metrics.token_overhead_ratio == 3.0
    aggregate = aggregate_multi_agent_metrics([metrics])
    assert aggregate.dissent_usefulness == 1.0
    assert aggregate.arbiter_resolution_rate == 1.0
    assert aggregate.token_overhead_ratio == 3.0


def test_multi_agent_dissent_usefulness_requires_dissent_for_security_labels() -> None:
    sample = _sample(labels=["permissions"])

    metrics = compute_multi_agent_sample_metrics(
        sample,
        {"risks": [], "citations": [], "comparison": {}, "dissent": [], "arbiter_decision": {}},
        latency_ms=1,
        single_review_token_count=10,
    )

    assert metrics.dissent_useful is False
    assert metrics.arbiter_resolved is False


def test_mcp_metrics_compare_expected_success_and_permission_decision() -> None:
    disabled_call = V1BenchmarkMCPToolCall(
        tool_name="run_safe_static_check",
        arguments={},
        expect_success=False,
        expect_permission_decision="disabled",
    )
    allowed_call = V1BenchmarkMCPToolCall(
        tool_name="code.search",
        arguments={},
        expect_success=True,
        expect_permission_decision="allow",
    )

    disabled_metrics = compute_mcp_sample_metrics(
        disabled_call,
        actual_success=False,
        actual_permission_decision="disabled",
        latency_ms=0,
        error_message="Tool is disabled.",
    )
    allowed_metrics = compute_mcp_sample_metrics(
        allowed_call,
        actual_success=True,
        actual_permission_decision="allow",
        latency_ms=10,
    )
    aggregate = aggregate_mcp_metrics([disabled_metrics, allowed_metrics])

    assert disabled_metrics.success_correct is True
    assert disabled_metrics.permission_correct is True
    assert aggregate.tool_success_rate == 1.0
    assert aggregate.permission_denial_correctness == 1.0
    assert aggregate.error_count == 1


def _sample(labels=None):
    return parse_v1_benchmark_sample(
        {
            "id": "sample-1",
            "repository_key": "python_demo",
            "platform": "github",
            "change_type": "pull_request",
            "url": "https://github.com/example/repo/pull/1",
            "title": "Token security",
            "diff_text": "diff --git a/app/auth/tokens.py b/app/auth/tokens.py",
            "expected_risks": [
                {
                    "title_keywords": ["token", "security"],
                    "severity": "medium",
                    "file_path": "app/auth/tokens.py",
                }
            ],
            "expected_files": ["app/auth/tokens.py"],
            "expected_labels": labels or [],
        }
    )
