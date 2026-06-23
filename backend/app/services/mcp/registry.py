from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Repository, RepositoryStatus
from app.schemas.qa import QACreateRequest
from app.schemas.review import ReviewCreateRequest
from app.services.qa import QAService
from app.services.review import ReviewService
from app.services.tools import (
    analyze_diff,
    code_search,
    get_symbol_context,
    read_file_slice,
)


class MCPPermissionPolicy(StrEnum):
    READ_ONLY = "read_only"
    SAFE_CHECK = "safe_check"


class MCPPermissionDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM_REQUIRED = "confirm_required"
    DISABLED = "disabled"


class MCPToolCallError(ValueError):
    pass


@dataclass(frozen=True)
class MCPToolContext:
    db: Session
    settings: Settings
    client_name: str | None = None
    client_session_id: str | None = None


@dataclass(frozen=True)
class MCPToolResult:
    content: list[dict[str, object]]
    structured_content: dict[str, object]
    repository_id: str | None = None


MCPToolHandler = Callable[[MCPToolContext, dict[str, Any]], MCPToolResult]


@dataclass(frozen=True)
class MCPToolDefinition:
    name: str
    description: str
    input_schema: dict[str, object]
    permission_policy: str
    handler: MCPToolHandler
    enabled: bool = True

    def to_mcp_tool(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": {
                "permission_policy": self.permission_policy,
                "enabled": self.enabled,
            },
        }

    def to_registry_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "permission_policy": self.permission_policy,
            "enabled": self.enabled,
        }


class MCPToolRegistry:
    def __init__(self, tools: list[MCPToolDefinition]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def list_tools(self) -> list[MCPToolDefinition]:
        return [self._tools[name] for name in sorted(self._tools)]

    def get(self, name: str) -> MCPToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise MCPToolCallError(f"Unknown MCP tool: {name}.") from exc

    def decide_permission(self, tool: MCPToolDefinition) -> tuple[str, str | None]:
        if not tool.enabled:
            return MCPPermissionDecision.DISABLED.value, "Tool is disabled."
        if tool.permission_policy == MCPPermissionPolicy.READ_ONLY.value:
            return MCPPermissionDecision.ALLOW.value, None
        if tool.permission_policy == MCPPermissionPolicy.SAFE_CHECK.value:
            return MCPPermissionDecision.DISABLED.value, "Safe check tools are disabled by default."
        return MCPPermissionDecision.DENY.value, "Unsupported permission policy."


def build_default_registry() -> MCPToolRegistry:
    return MCPToolRegistry(
        [
            MCPToolDefinition(
                name="repository.list",
                description="List imported repositories.",
                input_schema=_object_schema({}),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_repository_list,
            ),
            MCPToolDefinition(
                name="repository.status",
                description="Get repository indexing status and counts.",
                input_schema=_object_schema({"repository_id": _string_schema()}),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_repository_status,
            ),
            MCPToolDefinition(
                name="code.search",
                description="Search indexed repository code with hybrid retrieval.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "query": _string_schema(),
                        "top_k": _integer_schema(default=8, minimum=1, maximum=50),
                        "use_bm25": _boolean_schema(default=True),
                        "use_vector": _boolean_schema(default=True),
                        "use_graph": _boolean_schema(default=True),
                    },
                    required=["repository_id", "query"],
                ),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_code_search,
            ),
            MCPToolDefinition(
                name="file.read_slice",
                description="Read a bounded safe slice from an indexed repository file.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "file_path": _string_schema(),
                        "start_line": _integer_schema(default=1, minimum=1),
                        "end_line": _integer_schema(default=80, minimum=1),
                    },
                    required=["repository_id", "file_path"],
                ),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_file_read_slice,
            ),
            MCPToolDefinition(
                name="symbol.context",
                description="Load graph neighborhood for a symbol.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "symbol_name": _string_schema(),
                        "file_path": {"type": ["string", "null"]},
                        "max_neighbors": _integer_schema(default=8, minimum=1, maximum=50),
                    },
                    required=["repository_id", "symbol_name"],
                ),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_symbol_context,
            ),
            MCPToolDefinition(
                name="diff.analyze",
                description="Analyze a unified diff without writing to any platform.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "diff_text": _string_schema(),
                    },
                    required=["repository_id", "diff_text"],
                ),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_diff_analyze,
            ),
            MCPToolDefinition(
                name="repository.ask",
                description="Ask an evidence-grounded repository question.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "question": _string_schema(),
                        "top_k": _integer_schema(default=8, minimum=1, maximum=20),
                        "use_bm25": _boolean_schema(default=True),
                        "use_vector": _boolean_schema(default=True),
                        "use_graph": _boolean_schema(default=True),
                    },
                    required=["repository_id", "question"],
                ),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_repository_ask,
            ),
            MCPToolDefinition(
                name="review.diff",
                description="Run the existing read-only Review pipeline on a diff.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "diff_text": _string_schema(),
                        "top_k": _integer_schema(default=8, minimum=1, maximum=50),
                        "use_bm25": _boolean_schema(default=True),
                        "use_vector": _boolean_schema(default=True),
                        "use_graph": _boolean_schema(default=True),
                        "run_static_check": _boolean_schema(default=False),
                    },
                    required=["repository_id", "diff_text"],
                ),
                permission_policy=MCPPermissionPolicy.READ_ONLY.value,
                handler=_review_diff,
            ),
            MCPToolDefinition(
                name="run_safe_static_check",
                description="Reserved safe-check placeholder; disabled by default.",
                input_schema=_object_schema(
                    {
                        "repository_id": _string_schema(),
                        "checker": _string_schema(),
                        "file_paths": {"type": "array", "items": _string_schema()},
                    },
                    required=["repository_id", "checker", "file_paths"],
                ),
                permission_policy=MCPPermissionPolicy.SAFE_CHECK.value,
                handler=lambda _context, _arguments: MCPToolResult(
                    content=[_text_content("run_safe_static_check is disabled.")],
                    structured_content={"status": "disabled"},
                    repository_id=_optional_str(_arguments.get("repository_id")),
                ),
                enabled=False,
            ),
        ]
    )


def _repository_list(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    _ensure_no_unknown(arguments, set())
    repositories = [
        {
            "id": repository.id,
            "name": repository.name,
            "source_type": repository.source_type,
            "status": repository.status,
            "file_count": repository.file_count,
            "chunk_count": repository.chunk_count,
            "relation_count": repository.relation_count,
            "updated_at": repository.updated_at.isoformat(),
        }
        for repository in context.db.query(Repository)
        .order_by(Repository.updated_at.desc())
        .all()
    ]
    return MCPToolResult(
        content=[_text_content(f"{len(repositories)} repositories.")],
        structured_content={"repositories": repositories},
    )


def _repository_status(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    repository = _ready_or_existing_repository(context, _required_str(arguments, "repository_id"))
    result = {
        "id": repository.id,
        "name": repository.name,
        "status": repository.status,
        "file_count": repository.file_count,
        "parsed_file_count": repository.parsed_file_count,
        "skipped_file_count": repository.skipped_file_count,
        "chunk_count": repository.chunk_count,
        "relation_count": repository.relation_count,
        "error_message": repository.error_message,
    }
    return MCPToolResult(
        content=[_text_content(f"Repository {repository.name} is {repository.status}.")],
        structured_content=result,
        repository_id=repository.id,
    )


def _code_search(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    repository = _ready_repository(context, _required_str(arguments, "repository_id"))
    result = code_search(
        context.db,
        repository.id,
        _required_str(arguments, "query"),
        context.settings,
        top_k=_int_arg(arguments, "top_k", 8),
        use_bm25=_bool_arg(arguments, "use_bm25", True),
        use_vector=_bool_arg(arguments, "use_vector", True),
        use_graph=_bool_arg(arguments, "use_graph", True),
    )
    payload = result.to_dict()
    return MCPToolResult(
        content=[_text_content(f"{len(result.evidences)} evidence item(s).")],
        structured_content=payload,
        repository_id=repository.id,
    )


def _file_read_slice(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    repository = _ready_repository(context, _required_str(arguments, "repository_id"))
    result = read_file_slice(
        repository_root=repository.local_path,
        file_path=_required_str(arguments, "file_path"),
        start_line=_int_arg(arguments, "start_line", 1),
        end_line=_int_arg(arguments, "end_line", 80),
    )
    return MCPToolResult(
        content=[_text_content(result.content)],
        structured_content=result.to_dict(),
        repository_id=repository.id,
    )


def _symbol_context(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    repository = _ready_repository(context, _required_str(arguments, "repository_id"))
    result = get_symbol_context(
        context.db,
        repository.id,
        _required_str(arguments, "symbol_name"),
        file_path=_optional_str(arguments.get("file_path")),
        max_neighbors=_int_arg(arguments, "max_neighbors", 8),
    )
    return MCPToolResult(
        content=[_text_content(f"{len(result.neighbors)} neighbor(s).")],
        structured_content=result.to_dict(),
        repository_id=repository.id,
    )


def _diff_analyze(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    repository = _ready_or_existing_repository(context, _required_str(arguments, "repository_id"))
    result = analyze_diff(_required_str(arguments, "diff_text"))
    return MCPToolResult(
        content=[
            _text_content(
                f"{result.file_count} file(s), +{result.added_line_count}/-{result.removed_line_count}."
            )
        ],
        structured_content=result.to_dict(),
        repository_id=repository.id,
    )


def _repository_ask(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    service = QAService(context.db)
    repository = _ready_repository(context, _required_str(arguments, "repository_id"))
    request = QACreateRequest(
        question=_required_str(arguments, "question"),
        top_k=_int_arg(arguments, "top_k", 8),
        use_bm25=_bool_arg(arguments, "use_bm25", True),
        use_vector=_bool_arg(arguments, "use_vector", True),
        use_graph=_bool_arg(arguments, "use_graph", True),
    )
    task = service.create_question_task(repository, request)
    task = service.run_question_task(task, request, context.settings)
    response = service.build_task_response(task)
    payload = response.model_dump(mode="json")
    return MCPToolResult(
        content=[_text_content(response.answer or response.error_message or response.status)],
        structured_content=payload,
        repository_id=repository.id,
    )


def _review_diff(context: MCPToolContext, arguments: dict[str, Any]) -> MCPToolResult:
    service = ReviewService(context.db)
    repository = _ready_repository(context, _required_str(arguments, "repository_id"))
    request = ReviewCreateRequest(
        diff_text=_required_str(arguments, "diff_text"),
        top_k=_int_arg(arguments, "top_k", 8),
        use_bm25=_bool_arg(arguments, "use_bm25", True),
        use_vector=_bool_arg(arguments, "use_vector", True),
        use_graph=_bool_arg(arguments, "use_graph", True),
        run_static_check=_bool_arg(arguments, "run_static_check", False),
    )
    task = service.create_review_task(repository, request)
    task = service.run_review_task(task, request, context.settings)
    response = service.build_task_response(task)
    payload = response.model_dump(mode="json")
    return MCPToolResult(
        content=[_text_content(response.summary or response.error_message or response.status)],
        structured_content=payload,
        repository_id=repository.id,
    )


def _ready_repository(context: MCPToolContext, repository_id: str):
    repository = _ready_or_existing_repository(context, repository_id)
    if repository.status != RepositoryStatus.READY.value:
        raise MCPToolCallError("Repository must be ready before MCP tool calls.")
    return repository


def _ready_or_existing_repository(context: MCPToolContext, repository_id: str):
    from app.models import Repository

    repository = context.db.get(Repository, repository_id)
    if repository is None:
        raise MCPToolCallError("Repository not found.")
    return repository


def _object_schema(
    properties: dict[str, object],
    *,
    required: list[str] | None = None,
) -> dict[str, object]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or list(properties.keys()),
        "additionalProperties": False,
    }


def _string_schema() -> dict[str, object]:
    return {"type": "string"}


def _integer_schema(
    *,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> dict[str, object]:
    schema: dict[str, object] = {"type": "integer"}
    if default is not None:
        schema["default"] = default
    if minimum is not None:
        schema["minimum"] = minimum
    if maximum is not None:
        schema["maximum"] = maximum
    return schema


def _boolean_schema(*, default: bool) -> dict[str, object]:
    return {"type": "boolean", "default": default}


def _text_content(text: str) -> dict[str, object]:
    return {"type": "text", "text": text}


def _required_str(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MCPToolCallError(f"{key} is required.")
    return value.strip()


def _optional_str(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _int_arg(arguments: dict[str, Any], key: str, default: int) -> int:
    value = arguments.get(key, default)
    if not isinstance(value, int):
        raise MCPToolCallError(f"{key} must be an integer.")
    return value


def _bool_arg(arguments: dict[str, Any], key: str, default: bool) -> bool:
    value = arguments.get(key, default)
    if not isinstance(value, bool):
        raise MCPToolCallError(f"{key} must be a boolean.")
    return value


def _ensure_no_unknown(arguments: dict[str, Any], allowed: set[str]) -> None:
    unknown = set(arguments) - allowed
    if unknown:
        raise MCPToolCallError(f"Unknown argument(s): {', '.join(sorted(unknown))}.")
