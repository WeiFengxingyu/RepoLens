from app.services.review import DraftReviewRisk, ReviewRiskLocation, suggest_review_tests
from app.services.tools import analyze_diff


def test_test_suggestion_agent_generates_unit_test_for_impacted_symbol() -> None:
    risk = _risk(
        title="Changed helper",
        severity="medium",
        file_path="app.py",
        impacted_symbols=["helper"],
    )

    result = suggest_review_tests(
        verified_risks=[risk],
        impacted_symbols=["helper"],
        diff_analysis=_diff_analysis("app.py"),
    )

    assert len(result.suggested_tests) == 1
    suggestion = result.suggested_tests[0]
    assert suggestion.target == "helper"
    assert suggestion.test_type == "unit"
    assert suggestion.related_risk_titles == ["Changed helper"]
    assert "changed helper" in suggestion.reason.lower()
    assert result.to_dict()["suggested_tests"][0]["target"] == "helper"


def test_test_suggestion_agent_uses_integration_for_high_or_api_risk() -> None:
    high_risk = _risk(
        title="API validation risk",
        severity="high",
        file_path="backend/app/api/reviews.py",
        impacted_symbols=["create_review"],
    )

    result = suggest_review_tests(
        verified_risks=[high_risk],
        impacted_symbols=["create_review"],
        diff_analysis=_diff_analysis("backend/app/api/reviews.py"),
    )

    assert result.suggested_tests[0].test_type == "integration"
    assert result.suggested_tests[0].target == "create_review"


def test_test_suggestion_agent_deduplicates_by_target_and_type() -> None:
    risks = [
        _risk("Risk one", "medium", "app.py", ["helper"]),
        _risk("Risk two", "medium", "app.py", ["helper"]),
    ]

    result = suggest_review_tests(
        verified_risks=risks,
        impacted_symbols=["helper"],
        diff_analysis=_diff_analysis("app.py"),
    )

    assert len(result.suggested_tests) == 1
    assert result.suggested_tests[0].related_risk_titles == ["Risk one", "Risk two"]


def test_test_suggestion_agent_handles_empty_or_limited_input() -> None:
    empty = suggest_review_tests(verified_risks=[])
    limited = suggest_review_tests(
        verified_risks=[_risk("Risk", "low", "app.py", [])],
        max_tests=0,
    )

    assert empty.suggested_tests == []
    assert "No verified risks" in empty.warnings[0]
    assert limited.suggested_tests == []
    assert limited.warnings == ["max_tests <= 0"]


def _risk(
    title: str = "Changed helper",
    severity: str = "medium",
    file_path: str = "app.py",
    impacted_symbols: list[str] | None = None,
) -> DraftReviewRisk:
    return DraftReviewRisk(
        title=title,
        severity=severity,
        location=ReviewRiskLocation(file_path=file_path, start_line=1, end_line=2),
        reason="Changed helper behavior.",
        evidence_ids=[],
        impacted_symbols=impacted_symbols or [],
        suggestion="Add tests.",
        diff_refs=[{"file_path": file_path, "line": 1}],
    )


def _diff_analysis(file_path: str):
    return analyze_diff(
        f"""diff --git a/{file_path} b/{file_path}
--- a/{file_path}
+++ b/{file_path}
@@ -1,1 +1,1 @@
-old()
+new()
"""
    )
