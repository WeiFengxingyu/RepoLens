from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict

from app.services.retrieval.evidence import Evidence


class QAQuestionType(StrEnum):
    ARCHITECTURE = "architecture"
    FEATURE_LOCATION = "feature_location"
    FUNCTION_EXPLANATION = "function_explanation"
    CALL_RELATION = "call_relation"
    IMPACT_SCOPE = "impact_scope"


@dataclass(frozen=True)
class QAPlan:
    question_type: str
    retrieval_queries: list[str]
    answer_style: str
    use_graph: bool


@dataclass(frozen=True)
class RetrievalOptions:
    top_k: int = 8
    use_bm25: bool = True
    use_vector: bool = True
    use_graph: bool = True


@dataclass(frozen=True)
class AgentToolCall:
    tool_name: str
    input_summary: str
    output_summary: str
    permission_decision: str
    latency_ms: int
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class RetrievalAgentResult:
    evidences: list[Evidence]
    context_text: str
    context_truncated: bool
    warnings: list[str]
    tool_calls: list[AgentToolCall]
    debug_counts: dict[str, int]


@dataclass(frozen=True)
class DraftClaim:
    text: str
    evidence_ids: list[str]


@dataclass(frozen=True)
class DraftAnswer:
    draft_answer: str
    claims: list[DraftClaim]
    used_evidence_ids: list[str]
    warnings: list[str]
    token_usage: dict[str, int | str]
    chat_mode: str


@dataclass(frozen=True)
class VerificationResult:
    supported: bool
    missing_claims: list[str]
    needs_second_retrieval: bool
    second_retrieval_query: str | None
    checked_claim_count: int
    valid_evidence_ids: list[str]


@dataclass(frozen=True)
class QACitation:
    evidence_id: str
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    language: str
    score: float
    sources: list[str]
    snippet: str


@dataclass(frozen=True)
class QAAnswer:
    answer: str
    citations: list[QACitation]
    confidence: float
    warnings: list[str]
    verification: dict[str, object]


class QAAgentState(TypedDict, total=False):
    task_id: str
    repository_id: str
    question: str
    options: RetrievalOptions
    settings: object
    db: object
    chat_adapter: object
    plan: QAPlan
    retrieval_attempts: int
    second_retrieval_query: str | None
    evidences: list[Evidence]
    context_text: str
    context_truncated: bool
    draft: DraftAnswer
    verification: VerificationResult
    final_answer: QAAnswer
    warnings: list[str]
    step_order: int
