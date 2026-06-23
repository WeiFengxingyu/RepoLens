from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
RUNBOOK = REPO_ROOT / "docs" / "phase10-demo-runbook.md"
RELEASE_PACKAGE = REPO_ROOT / "docs" / "phase10-v1-release-package.md"
DETAILED_DESIGN = REPO_ROOT / "docs" / "phase10-detailed-design.md"
SCREENSHOT_ROOT = REPO_ROOT / "docs" / "assets" / "screenshots"

REQUIRED_SCREENSHOTS = [
    "repository-status.png",
    "evidence-panel.png",
    "ask-trace-panel.png",
    "review-panel.png",
    "tool-calls-panel.png",
    "evaluation-panel.png",
    "change-request-review-panel.png",
    "mcp-tool-permissions-panel.png",
    "multi-agent-trace-panel.png",
    "v1-benchmark-panel.png",
]


def test_phase10_release_documents_exist_and_cover_tasks() -> None:
    for path in [DETAILED_DESIGN, RUNBOOK, RELEASE_PACKAGE]:
        assert path.is_file()

    detailed_design = DETAILED_DESIGN.read_text(encoding="utf-8")
    for task_id in [f"P10-{index:03d}" for index in range(1, 9)]:
        assert task_id in detailed_design


def test_phase10_readme_has_v1_release_packaging_sections() -> None:
    readme = README.read_text(encoding="utf-8")

    required_terms = [
        "Current scope: **P0+ complete path plus V1 complete path, Phase 1 to Phase 10**",
        "Phase 10",
        "V1 Demo Runbook",
        "V1 Release Package",
        "PR/MR Review Flow",
        "MCP Server Flow",
        "Multi-Agent Review Flow",
        "V1 Benchmark",
        "Resume Bullets",
        "Interview Talk Track",
    ]
    for term in required_terms:
        assert term in readme


def test_phase10_runbook_covers_all_v1_demo_paths() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")

    for heading in [
        "Demo Path A: PR/MR Review",
        "Demo Path B: MCP Client",
        "Demo Path C: Multi-Agent Trace",
        "Demo Path D: V1 Benchmark",
    ]:
        assert heading in runbook

    for path in [
        "evals/change_requests/phase6_demo_prs.json",
        "evals/datasets/v1_pr_mr_benchmark.jsonl",
        "docs/assets/screenshots/change-request-review-panel.png",
        "docs/assets/screenshots/mcp-tool-permissions-panel.png",
        "docs/assets/screenshots/multi-agent-trace-panel.png",
        "docs/assets/screenshots/v1-benchmark-panel.png",
    ]:
        assert path in runbook


def test_phase10_release_package_has_resume_and_interview_material() -> None:
    release_package = RELEASE_PACKAGE.read_text(encoding="utf-8")

    assert "Resume Bullets V2" in release_package
    assert "Interview Talk Track V2" in release_package
    assert "Release Checklist" in release_package
    for term in ["GitHub", "Gitee", "GitLab.com", "self-hosted GitLab", "MCP", "Arbiter"]:
        assert term in release_package


def test_phase10_screenshots_exist_and_are_pngs() -> None:
    missing = [name for name in REQUIRED_SCREENSHOTS if not (SCREENSHOT_ROOT / name).is_file()]
    assert missing == []

    for name in REQUIRED_SCREENSHOTS:
        path = SCREENSHOT_ROOT / name
        data = path.read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert path.stat().st_size > 10_000

