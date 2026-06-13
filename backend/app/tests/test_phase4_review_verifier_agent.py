from dataclasses import dataclass

from app.services.review import DraftReviewRisk, ReviewRiskLocation, verify_review_risks
from app.services.tools import analyze_diff


@dataclass(frozen=True)
class FakeEvidence:
    evidence_id: str
    file_path: str


def test_review_verifier_keeps_risk_with_valid_evidence() -> None:
    risk = _risk(evidence_ids=["ev_valid", "ev_missing"], severity="high", diff_refs=[])

    result = verify_review_risks(
        risks=[risk],
        diff_analysis=_diff_analysis(),
        evidences=[FakeEvidence(evidence_id="ev_valid", file_path="app.py")],
    )

    assert len(result.verified_risks) == 1
    assert result.verified_risks[0].evidence_ids == ["ev_valid"]
    assert result.verified_risks[0].severity == "high"
    assert result.missing_risks == []
    assert result.risk_level == "high"


def test_review_verifier_keeps_and_downgrades_diff_supported_high_risk() -> None:
    risk = _risk(evidence_ids=[], severity="high", diff_refs=[_diff_ref()])

    result = verify_review_risks(
        risks=[risk],
        diff_analysis=_diff_analysis(),
        evidences=[],
    )

    assert len(result.verified_risks) == 1
    assert result.verified_risks[0].severity == "medium"
    assert "downgraded" in result.warnings[0]
    assert result.risk_level == "medium"


def test_review_verifier_removes_unsupported_risk() -> None:
    risk = _risk(evidence_ids=["missing"], severity="medium", diff_refs=[])

    result = verify_review_risks(
        risks=[risk],
        diff_analysis=_diff_analysis(),
        evidences=[],
    )

    assert result.verified_risks == []
    assert result.missing_risks == [risk]
    assert result.risk_level == "none"


def test_review_verifier_rejects_risk_location_outside_diff_and_evidence() -> None:
    risk = DraftReviewRisk(
        title="Outside file",
        severity="low",
        location=ReviewRiskLocation(file_path="outside.py", start_line=1, end_line=1),
        reason="outside",
        evidence_ids=[],
        impacted_symbols=[],
        suggestion="check",
        diff_refs=[{"file_path": "app.py", "line": 1}],
    )

    result = verify_review_risks(
        risks=[risk],
        diff_analysis=_diff_analysis(),
        evidences=[],
    )

    assert result.verified_risks == []
    assert result.missing_risks == [risk]


def _risk(
    *,
    evidence_ids: list[str],
    severity: str,
    diff_refs: list[dict[str, object]],
) -> DraftReviewRisk:
    return DraftReviewRisk(
        title="Changed helper",
        severity=severity,
        location=ReviewRiskLocation(file_path="app.py", start_line=1, end_line=1),
        reason="changed helper",
        evidence_ids=evidence_ids,
        impacted_symbols=["helper"],
        suggestion="add tests",
        diff_refs=diff_refs,
    )


def _diff_ref() -> dict[str, object]:
    return {
        "file_path": "app.py",
        "line": 1,
        "line_type": "added",
        "hunk_index": 1,
        "change_type": "modified",
    }


def _diff_analysis():
    return analyze_diff(
        """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,1 +1,1 @@
-old()
+new()
"""
    )
