from dataclasses import dataclass

from app.services.review import (
    DraftReviewRisk,
    ReviewRiskLocation,
    SuggestedReviewTest,
    write_review_report,
)


@dataclass(frozen=True)
class FakeEvidence:
    evidence_id: str
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    score: float
    sources: list[str]
    snippet: str


def test_review_report_writer_outputs_structured_json_and_markdown() -> None:
    risk = DraftReviewRisk(
        title="Changed helper",
        severity="medium",
        location=ReviewRiskLocation(file_path="app.py", start_line=4, end_line=6),
        reason="Changed helper behavior.",
        evidence_ids=["ev_1"],
        impacted_symbols=["helper"],
        suggestion="Add helper tests.",
        diff_refs=[{"file_path": "app.py", "line": 4}],
    )
    test = SuggestedReviewTest(
        target="helper",
        reason="Cover helper behavior.",
        test_type="unit",
        related_risk_titles=["Changed helper"],
        file_path="app.py",
    )

    report = write_review_report(
        verified_risks=[risk],
        suggested_tests=[test],
        evidences=[
            FakeEvidence(
                evidence_id="ev_1",
                chunk_id="chunk-helper",
                file_path="app.py",
                start_line=4,
                end_line=6,
                symbol_name="helper",
                score=0.9,
                sources=["bm25"],
                snippet="def helper(): ...",
            )
        ],
        warnings=["static check disabled"],
    )

    assert report.summary == "Found 1 verified review risk(s) across 1 impacted symbol(s)."
    assert report.risk_level == "medium"
    assert report.risks[0]["title"] == "Changed helper"
    assert "diff_refs" not in report.risks[0]
    assert report.suggested_tests[0]["target"] == "helper"
    assert report.citations[0]["evidence_id"] == "ev_1"
    assert "## Summary" in report.markdown
    assert "## Risks" in report.markdown
    assert report.to_dict()["warnings"] == ["static check disabled"]


def test_review_report_writer_outputs_empty_report_for_no_verified_risks() -> None:
    report = write_review_report(
        verified_risks=[],
        suggested_tests=[],
        evidences=[],
    )

    assert report.summary == "No verified review risks were found."
    assert report.risk_level == "none"
    assert report.risks == []
    assert report.impacted_symbols == []
    assert "No verified risks." in report.markdown
    assert "No focused tests suggested." in report.markdown


def test_review_report_writer_only_includes_citations_used_by_risks() -> None:
    risk = DraftReviewRisk(
        title="Changed helper",
        severity="low",
        location=ReviewRiskLocation(file_path="app.py", start_line=1, end_line=1),
        reason="Changed helper.",
        evidence_ids=["ev_used"],
        impacted_symbols=["helper"],
        suggestion="Add tests.",
        diff_refs=[],
    )

    report = write_review_report(
        verified_risks=[risk],
        suggested_tests=[],
        evidences=[
            FakeEvidence("ev_used", "chunk-1", "app.py", 1, 1, "helper", 0.8, ["bm25"], "used"),
            FakeEvidence("ev_unused", "chunk-2", "app.py", 2, 2, "other", 0.7, ["bm25"], "unused"),
        ],
    )

    assert [citation["evidence_id"] for citation in report.citations] == ["ev_used"]
