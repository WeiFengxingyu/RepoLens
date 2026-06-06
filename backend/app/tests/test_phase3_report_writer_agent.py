from app.services.agent import DraftAnswer, DraftClaim, VerificationResult, write_report
from app.services.retrieval.evidence import Evidence


def test_report_writer_outputs_citations_and_confidence() -> None:
    evidence = _evidence("ev_1", score=0.8)
    draft = DraftAnswer(
        draft_answer="Repository import is handled by RepositoryService. [1]",
        claims=[DraftClaim(text="RepositoryService handles import.", evidence_ids=["ev_1"])],
        used_evidence_ids=["ev_1"],
        warnings=["Chat adapter is not configured."],
        token_usage={"total_tokens": 0, "model": "disabled_fallback"},
        chat_mode="disabled_fallback",
    )
    verification = VerificationResult(
        supported=True,
        missing_claims=[],
        needs_second_retrieval=False,
        second_retrieval_query=None,
        checked_claim_count=1,
        valid_evidence_ids=["ev_1"],
    )

    answer = write_report(draft, verification, [evidence], warnings=[])

    assert answer.answer.startswith("Repository import")
    assert answer.citations[0].evidence_id == "ev_1"
    assert answer.confidence == 0.65
    assert "Chat adapter is not configured." in answer.warnings


def test_report_writer_lowers_confidence_for_unsupported_answer() -> None:
    draft = DraftAnswer(
        draft_answer="Repository import uses a queue.",
        claims=[DraftClaim(text="Repository import uses a queue.", evidence_ids=[])],
        used_evidence_ids=[],
        warnings=[],
        token_usage={"total_tokens": 0, "model": "test"},
        chat_mode="chat",
    )
    verification = VerificationResult(
        supported=False,
        missing_claims=["Repository import uses a queue."],
        needs_second_retrieval=False,
        second_retrieval_query=None,
        checked_claim_count=1,
        valid_evidence_ids=[],
    )

    answer = write_report(draft, verification, [], warnings=[])

    assert answer.citations == []
    assert answer.confidence == 0.2
    assert "could not be fully supported" in answer.answer
    assert "No citations were available for the final answer." in answer.warnings


def _evidence(evidence_id: str, *, score: float) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        chunk_id="chunk_1",
        repository_id="repo_1",
        file_path="backend/app/services/repository/service.py",
        start_line=10,
        end_line=20,
        symbol_name="RepositoryService.import_repository",
        symbol_type="function",
        language="python",
        source="bm25",
        sources=["bm25"],
        score=score,
        bm25_score=score,
        vector_score=0,
        graph_score=0,
        snippet="def import_repository(): ...",
    )
