from __future__ import annotations

import hashlib
import json
from datetime import datetime
from time import perf_counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Task, TaskStatus, TaskType, ToolCall, ToolCallStatus
from app.services.mcp.registry import (
    MCPPermissionDecision,
    MCPToolCallError,
    MCPToolContext,
    MCPToolRegistry,
    MCPToolResult,
    build_default_registry,
)

JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2025-06-18"


class MCPRequestError(ValueError):
    def __init__(self, message: str, *, code: int = -32602) -> None:
        super().__init__(message)
        self.code = code


class MCPService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        *,
        registry: MCPToolRegistry | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.registry = registry or build_default_registry()

    def handle_json_rpc(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_id = payload.get("id")
        try:
            if payload.get("jsonrpc") != JSONRPC_VERSION:
                raise MCPRequestError("jsonrpc must be 2.0.", code=-32600)
            method = _required_str(payload, "method")
            params = payload.get("params", {})
            if params is None:
                params = {}
            if not isinstance(params, dict):
                raise MCPRequestError("params must be an object.")
            result = self._dispatch(method, params)
            return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}
        except MCPRequestError as exc:
            return _error_response(request_id, exc.code, str(exc))
        except MCPToolCallError as exc:
            return _error_response(request_id, -32000, str(exc))
        except Exception as exc:
            return _error_response(request_id, -32603, str(exc))

    def list_tools(self) -> list[dict[str, object]]:
        return [tool.to_registry_dict() for tool in self.registry.list_tools()]

    def list_tool_calls(self, *, limit: int = 50) -> list[dict[str, object]]:
        capped_limit = max(1, min(limit, 200))
        tool_calls = self.db.scalars(
            select(ToolCall).order_by(ToolCall.created_at.desc(), ToolCall.id.desc()).limit(capped_limit)
        ).all()
        return [_tool_call_to_dict(tool_call) for tool_call in tool_calls]

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "repolens", "version": self.settings.app_version},
            }
        if method == "tools/list":
            return {"tools": [tool.to_mcp_tool() for tool in self.registry.list_tools()]}
        if method == "tools/call":
            return self._call_tool(params)
        raise MCPRequestError(f"Unsupported MCP method: {method}.", code=-32601)

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = _required_str(params, "name")
        arguments = params.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise MCPRequestError("tools/call arguments must be an object.")

        client_name = _optional_nested_str(params, "client", "name") or _optional_str(
            params.get("client_name")
        )
        client_session_id = _optional_str(params.get("session_id")) or _optional_str(
            params.get("client_session_id")
        )

        tool = self.registry.get(tool_name)
        decision, reason = self.registry.decide_permission(tool)
        context = MCPToolContext(
            db=self.db,
            settings=self.settings,
            client_name=client_name,
            client_session_id=client_session_id,
        )
        repository_id = _optional_str(arguments.get("repository_id"))

        if decision != MCPPermissionDecision.ALLOW.value:
            self._audit_call(
                tool_name=tool_name,
                repository_id=repository_id,
                arguments=arguments,
                result={"error": reason or decision},
                status=ToolCallStatus.DISABLED.value
                if decision == MCPPermissionDecision.DISABLED.value
                else ToolCallStatus.DENIED.value,
                permission_decision=decision,
                permission_policy=tool.permission_policy,
                client_name=client_name,
                client_session_id=client_session_id,
                latency_ms=0,
                error_message=reason,
            )
            return {
                "content": [{"type": "text", "text": reason or decision}],
                "isError": True,
                "structuredContent": {
                    "permission_decision": decision,
                    "reason": reason,
                },
            }

        started = perf_counter()
        try:
            result = tool.handler(context, arguments)
        except Exception as exc:
            latency_ms = _elapsed_ms(started)
            self._audit_call(
                tool_name=tool_name,
                repository_id=repository_id,
                arguments=arguments,
                result={"error": str(exc)},
                status=ToolCallStatus.FAILED.value,
                permission_decision=decision,
                permission_policy=tool.permission_policy,
                client_name=client_name,
                client_session_id=client_session_id,
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            raise MCPToolCallError(str(exc)) from exc

        latency_ms = _elapsed_ms(started)
        self._audit_call(
            tool_name=tool_name,
            repository_id=result.repository_id or repository_id,
            arguments=arguments,
            result=result.structured_content,
            status=ToolCallStatus.COMPLETED.value,
            permission_decision=decision,
            permission_policy=tool.permission_policy,
            client_name=client_name,
            client_session_id=client_session_id,
            latency_ms=latency_ms,
            error_message=None,
            output_summary=_output_summary(result),
        )
        return {
            "content": result.content,
            "structuredContent": result.structured_content,
            "isError": False,
        }

    def _audit_call(
        self,
        *,
        tool_name: str,
        repository_id: str | None,
        arguments: dict[str, Any],
        result: dict[str, Any],
        status: str,
        permission_decision: str,
        permission_policy: str,
        client_name: str | None,
        client_session_id: str | None,
        latency_ms: int,
        error_message: str | None,
        output_summary: str | None = None,
    ) -> None:
        if not repository_id:
            return
        task = Task(
            repository_id=repository_id,
            task_type=TaskType.MCP_TOOL.value,
            status=TaskStatus.COMPLETED.value
            if status == ToolCallStatus.COMPLETED.value
            else TaskStatus.FAILED.value,
            input_payload=json.dumps(
                {"tool_name": tool_name, "arguments": arguments},
                ensure_ascii=False,
                sort_keys=True,
            ),
            output_payload=json.dumps(result, ensure_ascii=False, sort_keys=True),
            error_message=error_message,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        self.db.add(task)
        self.db.flush()
        tool_call = ToolCall(
            task_id=task.id,
            repository_id=repository_id,
            tool_name=tool_name,
            status=status,
            permission_decision=permission_decision,
            permission_policy=permission_policy,
            client_name=client_name,
            client_session_id=client_session_id,
            input_hash=_hash_payload(arguments),
            output_hash=_hash_payload(result),
            input_summary=_input_summary(tool_name, arguments),
            output_summary=output_summary,
            input_payload=json.dumps(arguments, ensure_ascii=False, sort_keys=True),
            output_payload=json.dumps(result, ensure_ascii=False, sort_keys=True),
            latency_ms=latency_ms,
            error_message=error_message,
            completed_at=datetime.utcnow(),
        )
        self.db.add(tool_call)
        self.db.commit()


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MCPRequestError(f"{key} is required.")
    return value.strip()


def _optional_str(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_nested_str(payload: dict[str, Any], parent: str, child: str) -> str | None:
    value = payload.get(parent)
    if not isinstance(value, dict):
        return None
    return _optional_str(value.get(child))


def _error_response(request_id: object, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _input_summary(tool_name: str, arguments: dict[str, Any]) -> str:
    keys = ", ".join(sorted(arguments))
    return f"MCP {tool_name} call with argument keys: {keys or 'none'}."


def _output_summary(result: MCPToolResult) -> str:
    return f"MCP tool returned {len(result.structured_content)} structured field(s)."


def _elapsed_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)


def _tool_call_to_dict(tool_call: ToolCall) -> dict[str, object]:
    return {
        "id": tool_call.id,
        "task_id": tool_call.task_id,
        "repository_id": tool_call.repository_id,
        "tool_name": tool_call.tool_name,
        "status": tool_call.status,
        "permission_decision": tool_call.permission_decision,
        "permission_policy": tool_call.permission_policy,
        "client_name": tool_call.client_name,
        "client_session_id": tool_call.client_session_id,
        "input_hash": tool_call.input_hash,
        "output_hash": tool_call.output_hash,
        "input_summary": tool_call.input_summary,
        "output_summary": tool_call.output_summary,
        "latency_ms": tool_call.latency_ms,
        "error_message": tool_call.error_message,
        "created_at": tool_call.created_at.isoformat(),
        "completed_at": tool_call.completed_at.isoformat()
        if tool_call.completed_at
        else None,
    }
