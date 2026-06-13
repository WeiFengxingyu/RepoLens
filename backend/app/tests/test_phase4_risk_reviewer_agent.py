from dataclasses import dataclass

from app.services.agent import ChatMessage, ChatResult
from app.services.review import (
    DiffSymbolMappingResult,
    DiffSymbolMatch,
    UnmatchedDiffLine,
    review_risks,
)
from app.services.tools import analyze_diff


@dataclass(frozen=True)
class FakeEvidence:
    evidence_id: str
    file_path: str


def test_risk_reviewer_fallback_drafts_risks_from_mapped_symbols() -> None:
    diff_analysis = _analysis_for_symbol_change()
    mapping = _mapping_with_symbol_match()

    result = review_risks(
        diff_analysis=diff_analysis,
        mapping=mapping,
        evidences=[FakeEvidence(evidence_id="ev_app", file_path="app.py")],
    )

    assert result.mode == "fallback"
    assert len(result.risks) == 1
    risk = result.risks[0]
    assert risk.title == "Review changes around helper"
    assert risk.severity == "medium"
    assert risk.location.file_path == "app.py"
    assert risk.evidence_ids == ["ev_app"]
    assert risk.impacted_symbols == ["helper"]
    assert risk.diff_refs
    assert result.impacted_symbols == ["helper"]
    assert result.to_dict()["risks"][0]["title"] == "Review changes around helper"


def test_risk_reviewer_fallback_drafts_file_risk_for_unmatched_lines() -> None:
    diff_analysis = analyze_diff(
        """diff --git a/missing.py b/missing.py
--- a/missing.py
+++ b/missing.py
@@ -1,1 +1,1 @@
-old()
+new()
"""
    )
    mapping = DiffSymbolMappingResult(repository_id="repo", matches=[], unmatched_lines=[])
    mapping = DiffSymbolMappingResult(
        repository_id="repo",
        matches=[],
        unmatched_lines=[
            UnmatchedDiffLine(
                file_path="missing.py",
                change_type="modified",
                line_type="added",
                line=1,
                hunk_index=1,
                reason="no_chunk_for_changed_line",
            )
        ],
    )

    result = review_risks(diff_analysis=diff_analysis, mapping=mapping)

    assert len(result.risks) == 1
    assert result.risks[0].title == "Review changes in missing.py"
    assert result.risks[0].impacted_symbols == []
    assert result.risks[0].diff_refs


def test_risk_reviewer_uses_chat_adapter_when_it_returns_risks() -> None:
    adapter = FakeRiskChatAdapter(
        {
            "risks": [
                {
                    "title": "Path validation regression",
                    "severity": "high",
                    "location": {"file_path": "app.py", "start_line": 4, "end_line": 6},
                    "reason": "Changed branch may reject valid paths.",
                    "evidence_ids": ["ev_1"],
                    "impacted_symbols": ["helper"],
                    "suggestion": "Add path tests.",
                }
            ],
            "impacted_symbols": ["helper"],
        }
    )

    result = review_risks(
        diff_analysis=_analysis_for_symbol_change(),
        mapping=_mapping_with_symbol_match(),
        chat_adapter=adapter,
    )

    assert result.mode == "chat"
    assert result.risks[0].severity == "high"
    assert result.risks[0].evidence_ids == ["ev_1"]
    assert adapter.messages[0].role == "system"


def test_risk_reviewer_respects_max_risks() -> None:
    diff_analysis = _analysis_for_symbol_change()
    mapping = DiffSymbolMappingResult(
        repository_id="repo",
        matches=[
            *_mapping_with_symbol_match().matches,
            DiffSymbolMatch(
                repository_id="repo",
                file_path="other.py",
                change_type="modified",
                line_type="added",
                line=2,
                hunk_index=1,
                chunk_id="chunk-other",
                symbol_name="other",
                symbol_type="function",
                start_line=1,
                end_line=3,
            ),
        ],
    )

    result = review_risks(diff_analysis=diff_analysis, mapping=mapping, max_risks=1)

    assert len(result.risks) == 1


def _analysis_for_symbol_change():
    return analyze_diff(
        """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -4,2 +4,2 @@
-return old()
+return new()
"""
    )


def _mapping_with_symbol_match() -> DiffSymbolMappingResult:
    return DiffSymbolMappingResult(
        repository_id="repo",
        matches=[
            DiffSymbolMatch(
                repository_id="repo",
                file_path="app.py",
                change_type="modified",
                line_type="removed",
                line=4,
                hunk_index=1,
                chunk_id="chunk-helper",
                symbol_name="helper",
                symbol_type="function",
                start_line=4,
                end_line=8,
            ),
            DiffSymbolMatch(
                repository_id="repo",
                file_path="app.py",
                change_type="modified",
                line_type="added",
                line=4,
                hunk_index=1,
                chunk_id="chunk-helper",
                symbol_name="helper",
                symbol_type="function",
                start_line=4,
                end_line=8,
            ),
        ],
    )


class FakeRiskChatAdapter:
    def __init__(self, parsed_json):
        self.parsed_json = parsed_json
        self.messages: list[ChatMessage] = []

    def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: str,
    ) -> ChatResult:
        self.messages = messages
        self.response_schema = response_schema
        return ChatResult(
            parsed_json=self.parsed_json,
            content="{}",
            prompt_tokens=1,
            completion_tokens=1,
            total_tokens=2,
            model="fake",
        )
