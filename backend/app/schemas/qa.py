from datetime import datetime

from pydantic import BaseModel, Field


class QACreateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=8, ge=1, le=20)
    use_bm25: bool = True
    use_vector: bool = True
    use_graph: bool = True


class QACitationResponse(BaseModel):
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


class AgentTraceResponse(BaseModel):
    id: str
    step_name: str
    step_order: int
    status: str
    input_summary: str
    output_summary: str | None
    evidence_ids: list[str]
    tool_calls: list[dict[str, object]]
    token_usage: dict[str, object]
    latency_ms: int | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class QATaskResponse(BaseModel):
    task_id: str
    repository_id: str
    status: str
    question: str
    answer: str | None
    citations: list[QACitationResponse]
    confidence: float | None
    warnings: list[str]
    error_message: str | None
    traces: list[AgentTraceResponse]
    created_at: datetime
    completed_at: datetime | None
