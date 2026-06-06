from app.services.agent import ChatMessage, ChatResult, review_answer
from app.services.agent.chat import ChatDisabledError
from app.services.retrieval.evidence import Evidence


def test_answer_reviewer_builds_extractive_fallback_draft() -> None:
    evidence = _evidence("ev_1", "chunk_1", "RepositoryService.import_repository")

    draft = review_answer(
        "Where is repository import implemented?",
        [evidence],
        "context",
        chat_adapter=None,
    )

    assert draft.chat_mode == "disabled_fallback"
    assert draft.claims[0].evidence_ids == ["ev_1"]
    assert draft.used_evidence_ids == ["ev_1"]
    assert "RepositoryService.import_repository" in draft.draft_answer
    assert draft.token_usage["total_tokens"] == 0
    assert draft.warnings


def test_answer_reviewer_uses_chat_adapter_json() -> None:
    evidence = _evidence("ev_1", "chunk_1", "RepositoryService.import_repository")
    chat_adapter = FakeAnswerReviewerChatAdapter(
        ChatResult(
            content="{}",
            parsed_json={
                "draft_answer": "Repository import is handled by RepositoryService. [1]",
                "claims": [{"text": "RepositoryService handles import.", "evidence_ids": ["ev_1"]}],
                "used_evidence_ids": ["ev_1"],
            },
            model="demo-chat",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )
    )

    draft = review_answer(
        "Where is repository import implemented?",
        [evidence],
        "context",
        chat_adapter=chat_adapter,
    )

    assert chat_adapter.messages[0].role == "system"
    assert draft.chat_mode == "chat"
    assert draft.draft_answer.startswith("Repository import")
    assert draft.claims[0].evidence_ids == ["ev_1"]
    assert draft.token_usage["model"] == "demo-chat"


def test_answer_reviewer_falls_back_when_chat_is_disabled() -> None:
    evidence = _evidence("ev_1", "chunk_1", "RepositoryService.import_repository")

    draft = review_answer(
        "Where is repository import implemented?",
        [evidence],
        "context",
        chat_adapter=DisabledChatAdapter(),
    )

    assert draft.chat_mode == "disabled_fallback"
    assert "Missing chat configuration" in draft.warnings[0]


def test_answer_reviewer_returns_missing_evidence_draft() -> None:
    draft = review_answer("Where is repository import implemented?", [], "", chat_adapter=None)

    assert draft.chat_mode == "no_evidence"
    assert draft.claims == []
    assert draft.used_evidence_ids == []
    assert "not find enough code evidence" in draft.draft_answer


def _evidence(evidence_id: str, chunk_id: str, symbol_name: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        chunk_id=chunk_id,
        repository_id="repo_1",
        file_path="backend/app/services/repository/service.py",
        start_line=10,
        end_line=20,
        symbol_name=symbol_name,
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


class FakeAnswerReviewerChatAdapter:
    def __init__(self, result: ChatResult):
        self.result = result
        self.messages: list[ChatMessage] = []

    def complete_json(self, messages: list[ChatMessage], *, response_schema: str) -> ChatResult:
        self.messages = messages
        self.response_schema = response_schema
        return self.result


class DisabledChatAdapter:
    def complete_json(self, messages: list[ChatMessage], *, response_schema: str) -> ChatResult:
        raise ChatDisabledError("Missing chat configuration: REPOLENS_CHAT_BASE_URL")
