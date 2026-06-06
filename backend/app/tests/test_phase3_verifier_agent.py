from app.services.agent import DraftAnswer, DraftClaim, verify_draft
from app.services.retrieval.evidence import Evidence


def test_verifier_accepts_claims_with_available_evidence() -> None:
    evidence = _evidence("ev_1")
    draft = DraftAnswer(
        draft_answer="Repository import is handled by service. [1]",
        claims=[DraftClaim(text="Repository import is handled by service.", evidence_ids=["ev_1"])],
        used_evidence_ids=["ev_1"],
        warnings=[],
        token_usage={"total_tokens": 0, "model": "test"},
        chat_mode="disabled_fallback",
    )

    result = verify_draft(
        draft,
        [evidence],
        question="Where is repository import implemented?",
        retrieval_attempts=1,
    )

    assert result.supported is True
    assert result.missing_claims == []
    assert result.needs_second_retrieval is False
    assert result.valid_evidence_ids == ["ev_1"]


def test_verifier_requests_second_retrieval_for_missing_evidence() -> None:
    draft = DraftAnswer(
        draft_answer="Repository import uses an async queue.",
        claims=[DraftClaim(text="Repository import uses an async queue.", evidence_ids=[])],
        used_evidence_ids=[],
        warnings=[],
        token_usage={"total_tokens": 0, "model": "test"},
        chat_mode="disabled_fallback",
    )

    result = verify_draft(
        draft,
        [_evidence("ev_1")],
        question="Where is repository import implemented?",
        retrieval_attempts=1,
    )

    assert result.supported is False
    assert result.needs_second_retrieval is True
    assert "async queue" in result.second_retrieval_query


def test_verifier_does_not_request_third_retrieval() -> None:
    draft = DraftAnswer(
        draft_answer="Repository import uses an async queue.",
        claims=[DraftClaim(text="Repository import uses an async queue.", evidence_ids=["missing"])],
        used_evidence_ids=["missing"],
        warnings=[],
        token_usage={"total_tokens": 0, "model": "test"},
        chat_mode="chat",
    )

    result = verify_draft(
        draft,
        [_evidence("ev_1")],
        question="Where is repository import implemented?",
        retrieval_attempts=2,
    )

    assert result.supported is False
    assert result.needs_second_retrieval is False
    assert result.second_retrieval_query is None


def test_verifier_rejects_draft_without_claims() -> None:
    draft = DraftAnswer(
        draft_answer="No evidence.",
        claims=[],
        used_evidence_ids=[],
        warnings=[],
        token_usage={"total_tokens": 0, "model": "test"},
        chat_mode="no_evidence",
    )

    result = verify_draft(
        draft,
        [],
        question="Where is repository import implemented?",
        retrieval_attempts=1,
    )

    assert result.supported is False
    assert result.needs_second_retrieval is True
    assert result.missing_claims == ["Draft contains no verifiable claims."]


def _evidence(evidence_id: str) -> Evidence:
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
        score=0.8,
        bm25_score=0.8,
        vector_score=0,
        graph_score=0,
        snippet="def import_repository(): ...",
    )
