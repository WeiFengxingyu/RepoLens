from typing import Any

from pydantic import BaseModel, Field


class MCPJsonRpcRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


class MCPJsonRpcResponse(BaseModel):
    jsonrpc: str
    id: str | int | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class MCPToolInfo(BaseModel):
    name: str
    description: str
    input_schema: dict[str, object]
    permission_policy: str
    enabled: bool


class MCPToolCallAuditResponse(BaseModel):
    id: str
    task_id: str
    repository_id: str
    tool_name: str
    status: str
    permission_decision: str
    permission_policy: str | None
    client_name: str | None
    client_session_id: str | None
    input_hash: str | None
    output_hash: str | None
    input_summary: str
    output_summary: str | None
    latency_ms: int | None
    error_message: str | None
    created_at: str
    completed_at: str | None
