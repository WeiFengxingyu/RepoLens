from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.qa import AgentTraceResponse
from app.services.tools import DIFF_MAX_CHARS


class ReviewCreateRequest(BaseModel):
    diff_text: str = Field(min_length=1, max_length=DIFF_MAX_CHARS)
    top_k: int = Field(default=8, ge=1, le=50)
    use_bm25: bool = True
    use_vector: bool = True
    use_graph: bool = True
    run_static_check: bool = False


class ReviewToolCallResponse(BaseModel):
    id: str
    tool_name: str
    status: str
    permission_decision: str
    input_summary: str
    output_summary: str | None
    latency_ms: int | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ReviewTaskResponse(BaseModel):
    task_id: str
    repository_id: str
    status: str
    summary: str | None
    risk_level: str | None
    risks: list[dict[str, object]]
    impacted_symbols: list[str]
    suggested_tests: list[dict[str, object]]
    citations: list[dict[str, object]]
    markdown: str | None
    tool_calls: list[ReviewToolCallResponse]
    traces: list[AgentTraceResponse]
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
