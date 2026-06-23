from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.mcp import (
    MCPJsonRpcRequest,
    MCPJsonRpcResponse,
    MCPToolCallAuditResponse,
    MCPToolInfo,
)
from app.services.mcp import MCPService

router = APIRouter(tags=["mcp"])


@router.post("/api/mcp", response_model=MCPJsonRpcResponse)
def mcp_json_rpc(
    request: MCPJsonRpcRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    response = MCPService(db, settings).handle_json_rpc(request.model_dump())
    return MCPJsonRpcResponse(**response)


@router.get("/api/mcp/tools", response_model=list[MCPToolInfo])
def list_mcp_tools(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return MCPService(db, settings).list_tools()


@router.get("/api/mcp/tool-calls", response_model=list[MCPToolCallAuditResponse])
def list_mcp_tool_calls(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return MCPService(db, settings).list_tool_calls(limit=limit)
