import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
RUNBOOK = REPO_ROOT / "docs" / "phase10-demo-runbook.md"
RELEASE_PACKAGE = REPO_ROOT / "docs" / "phase10-v1-release-package.md"
DOCS_INDEX = REPO_ROOT / "docs" / "README.md"
INTERVIEW_INDEX = REPO_ROOT / "docs" / "interview" / "README.md"
REAL_CASE_DOC = REPO_ROOT / "docs" / "interview" / "v1-real-pr-mr-case-studies.md"
SCORECARD = REPO_ROOT / "docs" / "interview" / "v1-evaluation-scorecard.md"
INTERVIEW_GUIDE = REPO_ROOT / "docs" / "interview" / "v1-interview-deep-dive-guide.md"
REAL_CASE_JSON = REPO_ROOT / "evals" / "change_requests" / "real_pr_mr_case_studies.json"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed_demo.ps1"


def test_v1_real_pr_mr_case_studies_cover_mainstream_platforms() -> None:
    cases = json.loads(REAL_CASE_JSON.read_text(encoding="utf-8"))

    assert len(cases) >= 5
    assert {case["platform"] for case in cases} >= {
        "github",
        "gitee",
        "gitlab",
        "self_hosted_gitlab",
    }
    assert all(case["url"].startswith("https://") for case in cases)
    assert all(case["demo_status"] for case in cases)
    assert any("/pull/" in case["url"] for case in cases if case["platform"] == "github")
    assert any("/pulls/" in case["url"] for case in cases if case["platform"] == "gitee")
    assert all(
        "/-/merge_requests/" in case["url"]
        for case in cases
        if case["platform"] in {"gitlab", "self_hosted_gitlab"}
    )


def test_v1_real_pr_mr_case_doc_states_live_smoke_boundaries() -> None:
    content = REAL_CASE_DOC.read_text(encoding="utf-8")

    for term in [
        "GitHub",
        "Gitee",
        "GitLab.com",
        "self-hosted GitLab",
        "live smoke",
        "default demo remains offline",
        "must not comment",
        "diff-size limits",
    ]:
        assert term in content


def test_v1_evaluation_scorecard_contains_ablation_and_metric_map() -> None:
    content = SCORECARD.read_text(encoding="utf-8")

    for term in [
        "vector_only",
        "bm25_vector",
        "bm25_vector_graph",
        "Hit@5",
        "MRR",
        "0.892",
        "unsupported_claim_rate",
        "dissent_usefulness",
        "permission_denial_correctness",
    ]:
        assert term in content


def test_demo_seed_script_calls_real_local_apis() -> None:
    content = SEED_SCRIPT.read_text(encoding="utf-8")

    for term in [
        "/health",
        "/api/repositories",
        "/api/mcp",
        "/api/v1-benchmarks",
        "evals/demo_repos/python_service",
        "evals/demo_repos/ts_webapp",
        ".repolens/demo-seed-summary.json",
    ]:
        assert term in content
    assert "Invoke-RestMethod" in content
    assert "Set-Content" in content


def test_v1_interview_deep_dive_guide_covers_architecture_and_talk_tracks() -> None:
    content = INTERVIEW_GUIDE.read_text(encoding="utf-8")

    for term in [
        "【给你理解】",
        "【面试可说】",
        "Repository Ingestion",
        "Hybrid Retrieval",
        "GraphRAG",
        "Change Request Provider",
        "MCP endpoint",
        "Multi-Agent Review",
        "Evaluation 和 Benchmark",
        "backend/app/services/retrieval/hybrid.py",
        "backend/app/services/change_request/providers.py",
        "backend/app/services/mcp/registry.py",
        "backend/app/services/multi_agent/service.py",
    ]:
        assert term in content


def test_v1_hardening_assets_are_linked_from_release_docs() -> None:
    readme = README.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    release_package = RELEASE_PACKAGE.read_text(encoding="utf-8")
    docs_index = DOCS_INDEX.read_text(encoding="utf-8")
    interview_index = INTERVIEW_INDEX.read_text(encoding="utf-8")

    for content in [readme, runbook, release_package, docs_index, interview_index]:
        assert "docs/interview/v1-real-pr-mr-case-studies.md" in content
        assert "docs/interview/v1-evaluation-scorecard.md" in content
        assert "docs/interview/v1-interview-deep-dive-guide.md" in content
    for content in [readme, runbook, release_package, docs_index]:
        assert "scripts/seed_demo.ps1" in content
