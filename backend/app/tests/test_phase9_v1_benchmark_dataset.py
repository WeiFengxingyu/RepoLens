import json
from pathlib import Path

import pytest

from app.services.v1_benchmark import (
    V1BenchmarkDatasetError,
    load_v1_benchmark_dataset,
    parse_v1_benchmark_sample,
)


DATASET_PATH = Path(__file__).resolve().parents[3] / "evals" / "datasets" / "v1_pr_mr_benchmark.jsonl"


def test_v1_benchmark_dataset_fixture_has_required_phase9_coverage() -> None:
    dataset = load_v1_benchmark_dataset(DATASET_PATH)

    assert dataset.sample_count >= 20
    assert {"github", "gitee", "gitlab", "self_hosted_gitlab", "synthetic"}.issubset(
        {sample.platform for sample in dataset.samples}
    )
    assert {sample.repository_key for sample in dataset.samples} == {"python_demo", "ts_demo"}
    assert all(sample.expected_risks for sample in dataset.samples)
    assert all(sample.expected_files for sample in dataset.samples)
    assert any(not call.expect_success for sample in dataset.samples for call in sample.mcp_tool_calls)
    assert any(
        call.expect_permission_decision == "disabled"
        for sample in dataset.samples
        for call in sample.mcp_tool_calls
    )


def test_parse_v1_benchmark_sample_normalizes_expected_risk_and_mcp_call() -> None:
    sample = parse_v1_benchmark_sample(
        {
            "id": "case-1",
            "repository_key": "python_demo",
            "platform": "github",
            "change_type": "pull_request",
            "url": "https://github.com/example/repo/pull/1",
            "title": "Token guard",
            "diff_text": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py",
            "expected_risks": [
                {
                    "title_keywords": ["Token", "Auth"],
                    "severity": "medium",
                    "file_path": "app.py",
                }
            ],
            "expected_files": ["app.py"],
            "expected_labels": ["security", "security"],
            "mcp_tool_calls": [
                {
                    "tool_name": "code.search",
                    "arguments": {"repository_id": "{repository_id}", "query": "token"},
                    "expect_success": True,
                    "expect_permission_decision": "allow",
                }
            ],
        }
    )

    assert sample.expected_risks[0].title_keywords == ["token", "auth"]
    assert sample.expected_labels == ["security"]
    assert sample.mcp_tool_calls[0].arguments["repository_id"] == "{repository_id}"


def test_load_v1_benchmark_dataset_rejects_small_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "small.jsonl"
    dataset_path.write_text(json.dumps(_sample("case-1")), encoding="utf-8")

    with pytest.raises(V1BenchmarkDatasetError, match="at least 20 samples"):
        load_v1_benchmark_dataset(dataset_path)


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"platform": "bitbucket"}, "platform must be one of"),
        ({"change_type": "issue"}, "change_type must be one of"),
        ({"expected_files": ["../secret.py"]}, "paths cannot contain traversal"),
        ({"expected_risks": []}, "expected_risks must contain"),
        (
            {
                "mcp_tool_calls": [
                    {
                        "tool_name": "code.search",
                        "arguments": {},
                        "expect_success": True,
                        "expect_permission_decision": "maybe",
                    }
                ]
            },
            "expect_permission_decision",
        ),
    ],
)
def test_parse_v1_benchmark_sample_rejects_invalid_payload(
    patch: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(V1BenchmarkDatasetError, match=message):
        parse_v1_benchmark_sample({**_sample("case-invalid"), **patch})


def _sample(sample_id: str) -> dict[str, object]:
    return {
        "id": sample_id,
        "repository_key": "python_demo",
        "platform": "github",
        "change_type": "pull_request",
        "url": "https://github.com/example/repo/pull/1",
        "title": "Token guard",
        "diff_text": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py",
        "expected_risks": [
            {
                "title_keywords": ["token"],
                "severity": "medium",
                "file_path": "app.py",
            }
        ],
        "expected_files": ["app.py"],
    }
