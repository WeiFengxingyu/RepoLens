from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.services.tools import DIFF_MAX_CHARS


class MultiAgentReviewCreateRequest(BaseModel):
    diff_text: str = Field(min_length=1, max_length=DIFF_MAX_CHARS)
    top_k: int = Field(default=8, ge=1, le=50)
    use_bm25: bool = True
    use_vector: bool = True
    use_graph: bool = True
    run_static_check: bool = False
    round_limit: int = Field(default=2, ge=2, le=3)
    assignment_limit: int = Field(default=8, ge=6, le=12)
    token_budget: int = Field(default=8000, ge=1000, le=50000)


class AgentSessionResponse(BaseModel):
    id: str
    task_id: str
    repository_id: str
    status: str
    mode: str
    round_limit: int
    assignment_limit: int
    token_budget: int | None
    summary: str | None
    final_report: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class AgentAssignmentResponse(BaseModel):
    id: str
    session_id: str
    agent_name: str
    role: str
    status: str
    round_index: int
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None
    evidence_ids: list[str]
    dissent: dict[str, Any] | None
    confidence: int
    token_estimate: int
    latency_ms: int | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class AgentMessageResponse(BaseModel):
    id: str
    session_id: str
    assignment_id: str | None
    sender: str
    recipient: str
    message_type: str
    round_index: int
    content: str
    evidence_ids: list[str]
    claims: list[str]
    confidence: int
    requires_arbitration: bool
    created_at: datetime


class MultiAgentReviewResponse(BaseModel):
    task_id: str
    repository_id: str
    status: str
    session: AgentSessionResponse
    assignments: list[AgentAssignmentResponse]
    messages: list[AgentMessageResponse]
    summary: str | None
    risk_level: str | None
    risks: list[dict[str, Any]]
    suggested_tests: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    markdown: str | None
    arbiter_decision: dict[str, Any]
    dissent: list[dict[str, Any]]
    comparison: dict[str, Any]
    warnings: list[str]
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
