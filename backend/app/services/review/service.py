import json
from collections.abc import Callable
from datetime import datetime
from time import perf_counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import (
    AgentTrace,
    AgentTraceStatus,
    Repository,
    RepositoryStatus,
    Task,
    TaskStatus,
    TaskType,
    ToolCall,
    ToolCallStatus,
    ToolPermissionDecision,
)
from app.schemas.review import ReviewCreateRequest, ReviewTaskResponse, ReviewToolCallResponse
from app.services.qa.service import _build_trace_response
from app.services.review.agents import (
    review_risks,
    suggest_review_tests,
    verify_review_risks,
    write_review_report,
)
from app.services.review.diff_mapper import map_diff_to_symbols, write_changed_by_relations
from app.services.tools import (
    StaticCheckResult,
    analyze_diff,
    code_search,
    get_symbol_context,
    run_safe_static_check,
)


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_repository(self, repository_id: str) -> Repository | None:
        return self.db.get(Repository, repository_id)

    def ensure_repository_ready(self, repository: Repository) -> None:
        if repository.status != RepositoryStatus.READY.value:
            raise ReviewRepositoryNotReadyError("Repository must be ready before Review.")

    def create_review_task(self, repository: Repository, request: ReviewCreateRequest) -> Task:
        diff_text = request.diff_text.strip()
        if not diff_text:
            raise ReviewValidationError("Diff text is required.")

        payload = {
            "diff_text": diff_text,
            "top_k": request.top_k,
            "use_bm25": request.use_bm25,
            "use_vector": request.use_vector,
            "use_graph": request.use_graph,
            "run_static_check": request.run_static_check,
        }
        task = Task(
            repository_id=repository.id,
            task_type=TaskType.REVIEW.value,
            status=TaskStatus.PENDING.value,
            input_payload=json.dumps(payload, ensure_ascii=False),
            output_payload=json.dumps(_empty_review_output(), ensure_ascii=False),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def run_review_task(
        self,
        task: Task,
        request: ReviewCreateRequest,
        settings: Settings,
    ) -> Task:
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        self.db.commit()

        tool_summaries: list[dict[str, object]] = []
        trace_order = 1

        try:
            diff_analysis, analyze_call = self._run_logged_tool(
                task=task,
                tool_name="analyze_diff",
                input_summary=f"Analyze diff with {len(request.diff_text)} characters.",
                input_payload={"diff_text_chars": len(request.diff_text)},
                call=lambda: analyze_diff(request.diff_text.strip()),
                output_summary=lambda result: (
                    f"{result.file_count} file(s), "
                    f"+{result.added_line_count}/-{result.removed_line_count} line(s)."
                ),
                output_payload=lambda result: result.to_dict(),
            )
            tool_summaries.append(_tool_call_summary(analyze_call))
            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="ReviewPlanner",
                input_summary="Received PR diff and selected Phase 4 review tools.",
                output_summary="Diff parsed and ready for symbol mapping.",
                tool_calls=tool_summaries[-1:],
            )
            trace_order += 1

            mapping = map_diff_to_symbols(self.db, task.repository_id, diff_analysis)
            relations = write_changed_by_relations(self.db, task.repository_id, task.id, mapping)
            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="DiffSymbolMapper",
                input_summary="Map changed diff lines to indexed code chunks.",
                output_summary=(
                    f"{mapping.match_count} symbol match(es), "
                    f"{mapping.unmatched_count} unmatched line(s), "
                    f"{len(relations)} changed_by relation(s)."
                ),
            )
            trace_order += 1

            query = _review_search_query(diff_analysis, mapping)
            search_result, search_call = self._run_logged_tool(
                task=task,
                tool_name="code_search",
                input_summary=f"Search context for: {query[:160]}",
                input_payload={
                    "query": query,
                    "top_k": request.top_k,
                    "use_bm25": request.use_bm25,
                    "use_vector": request.use_vector,
                    "use_graph": request.use_graph,
                },
                call=lambda: code_search(
                    self.db,
                    task.repository_id,
                    query,
                    settings,
                    top_k=request.top_k,
                    use_bm25=request.use_bm25,
                    use_vector=request.use_vector,
                    use_graph=request.use_graph,
                ),
                output_summary=lambda result: (
                    f"{len(result.evidences)} evidence item(s); "
                    f"{len(result.warnings)} warning(s)."
                ),
                output_payload=lambda result: result.to_dict(),
            )
            tool_summaries.append(_tool_call_summary(search_call))

            for match in _unique_symbol_context_targets(mapping)[:3]:
                try:
                    symbol_context, symbol_call = self._run_logged_tool(
                        task=task,
                        tool_name="get_symbol_context",
                        input_summary=(
                            f"Load graph neighborhood for {match.symbol_name} "
                            f"in {match.file_path}."
                        ),
                        input_payload={
                            "symbol_name": match.symbol_name,
                            "file_path": match.file_path,
                            "max_neighbors": 8,
                        },
                        call=lambda match=match: get_symbol_context(
                            self.db,
                            task.repository_id,
                            match.symbol_name,
                            file_path=match.file_path,
                            max_neighbors=8,
                        ),
                        output_summary=lambda result: (
                            f"{len(result.neighbors)} neighbor(s); "
                            f"{len(result.warnings)} warning(s)."
                        ),
                        output_payload=lambda result: result.to_dict(),
                    )
                    _ = symbol_context
                    tool_summaries.append(_tool_call_summary(symbol_call))
                except Exception:
                    tool_summaries.append(
                        _tool_call_summary(
                            self.db.scalars(
                                select(ToolCall)
                                .where(ToolCall.task_id == task.id)
                                .order_by(ToolCall.created_at.desc(), ToolCall.id.desc())
                            ).first()
                        )
                    )

            static_result: StaticCheckResult | None = None
            if request.run_static_check:
                static_result, static_call = self._run_logged_tool(
                    task=task,
                    tool_name="run_safe_static_check",
                    input_summary="Run configured Phase 4 static check placeholder.",
                    input_payload={
                        "checker": "python_ast_parse",
                        "file_paths": _changed_files(diff_analysis),
                    },
                    call=lambda: run_safe_static_check(
                        checker="python_ast_parse",
                        file_paths=_changed_files(diff_analysis),
                        settings=settings,
                    ),
                    output_summary=lambda result: result.output_summary,
                    output_payload=lambda result: result.to_dict(),
                    status_from_result=lambda result: _tool_status_from_static_check(result),
                    permission_from_result=lambda result: result.permission_decision,
                )
                tool_summaries.append(_tool_call_summary(static_call))

            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="RetrievalAgent",
                input_summary="Collect evidence and graph context for changed code.",
                output_summary=(
                    f"{len(search_result.evidences)} evidence item(s), "
                    f"{len(tool_summaries)} tool call(s) recorded."
                ),
                evidence_ids=[evidence.evidence_id for evidence in search_result.evidences],
                tool_calls=tool_summaries,
            )
            trace_order += 1

            risk_result = review_risks(
                diff_analysis=diff_analysis,
                mapping=mapping,
                evidences=search_result.evidences,
            )
            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="RiskReviewer",
                input_summary="Draft risks from diff, mapped symbols, and evidence.",
                output_summary=(
                    f"{len(risk_result.risks)} risk(s), "
                    f"{len(risk_result.impacted_symbols)} impacted symbol(s)."
                ),
                evidence_ids=[evidence.evidence_id for evidence in search_result.evidences],
            )
            trace_order += 1

            verifier_result = verify_review_risks(
                risks=risk_result.risks,
                diff_analysis=diff_analysis,
                evidences=search_result.evidences,
            )
            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="ReviewVerifier",
                input_summary="Verify drafted risks against diff and evidence.",
                output_summary=(
                    f"{len(verifier_result.verified_risks)} verified risk(s), "
                    f"{len(verifier_result.missing_risks)} unsupported risk(s)."
                ),
                evidence_ids=[evidence.evidence_id for evidence in search_result.evidences],
            )
            trace_order += 1

            test_result = suggest_review_tests(
                verified_risks=verifier_result.verified_risks,
                impacted_symbols=risk_result.impacted_symbols,
                diff_analysis=diff_analysis,
            )
            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="TestSuggestionAgent",
                input_summary="Suggest focused tests for verified risks.",
                output_summary=f"{len(test_result.suggested_tests)} suggested test(s).",
            )
            trace_order += 1

            warnings = [
                *search_result.warnings,
                *risk_result.warnings,
                *verifier_result.warnings,
                *test_result.warnings,
            ]
            if static_result is not None:
                warnings.extend(static_result.warnings)

            report = write_review_report(
                verified_risks=verifier_result.verified_risks,
                suggested_tests=test_result.suggested_tests,
                evidences=search_result.evidences,
                warnings=_deduplicate_strings(warnings),
                risk_level=verifier_result.risk_level,
            )
            self._add_trace(
                task=task,
                step_order=trace_order,
                step_name="ReviewReportWriter",
                input_summary="Write final structured review report.",
                output_summary=report.summary,
                evidence_ids=[citation["evidence_id"] for citation in report.citations],
            )

            task.status = TaskStatus.COMPLETED.value
            task.output_payload = json.dumps(report.to_dict(), ensure_ascii=False)
            task.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
            return task
        except Exception as exc:
            task.status = TaskStatus.FAILED.value
            task.error_message = str(exc)
            task.completed_at = datetime.utcnow()
            task.output_payload = json.dumps(_empty_review_output(), ensure_ascii=False)
            self.db.commit()
            self.db.refresh(task)
            return task

    def get_task(self, task_id: str) -> Task | None:
        return self.db.get(Task, task_id)

    def build_task_response(self, task: Task) -> ReviewTaskResponse:
        output_payload = _load_json_object(task.output_payload or "{}")
        traces = self.db.scalars(
            select(AgentTrace)
            .where(AgentTrace.task_id == task.id)
            .order_by(AgentTrace.step_order, AgentTrace.created_at, AgentTrace.id)
        ).all()
        tool_calls = self.db.scalars(
            select(ToolCall)
            .where(ToolCall.task_id == task.id)
            .order_by(ToolCall.created_at, ToolCall.id)
        ).all()

        return ReviewTaskResponse(
            task_id=task.id,
            repository_id=task.repository_id,
            status=task.status,
            summary=_optional_str(output_payload.get("summary")),
            risk_level=_optional_str(output_payload.get("risk_level")),
            risks=_load_dict_list(output_payload.get("risks")),
            impacted_symbols=_load_str_list(output_payload.get("impacted_symbols")),
            suggested_tests=_load_dict_list(output_payload.get("suggested_tests")),
            citations=_load_dict_list(output_payload.get("citations")),
            markdown=_optional_str(output_payload.get("markdown")),
            tool_calls=[_build_tool_call_response(tool_call) for tool_call in tool_calls],
            traces=[_build_trace_response(trace) for trace in traces],
            error_message=task.error_message,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )

    def _run_logged_tool(
        self,
        *,
        task: Task,
        tool_name: str,
        input_summary: str,
        input_payload: dict[str, object],
        call: Callable[[], Any],
        output_summary: Callable[[Any], str],
        output_payload: Callable[[Any], dict[str, object]],
        status_from_result: Callable[[Any], str] | None = None,
        permission_from_result: Callable[[Any], str] | None = None,
    ) -> tuple[Any, ToolCall]:
        tool_call = ToolCall(
            task_id=task.id,
            repository_id=task.repository_id,
            tool_name=tool_name,
            status=ToolCallStatus.RUNNING.value,
            permission_decision=ToolPermissionDecision.ALLOW.value,
            input_summary=input_summary,
            input_payload=json.dumps(input_payload, ensure_ascii=False),
        )
        self.db.add(tool_call)
        self.db.flush()

        started = perf_counter()
        try:
            result = call()
        except Exception as exc:
            tool_call.status = ToolCallStatus.FAILED.value
            tool_call.error_message = str(exc)
            tool_call.latency_ms = _elapsed_ms(started)
            tool_call.completed_at = datetime.utcnow()
            self.db.flush()
            raise

        tool_call.status = (
            status_from_result(result) if status_from_result else ToolCallStatus.COMPLETED.value
        )
        tool_call.permission_decision = (
            permission_from_result(result)
            if permission_from_result
            else ToolPermissionDecision.ALLOW.value
        )
        tool_call.output_summary = output_summary(result)
        tool_call.output_payload = json.dumps(output_payload(result), ensure_ascii=False)
        tool_call.latency_ms = _elapsed_ms(started)
        tool_call.completed_at = datetime.utcnow()
        self.db.flush()
        return result, tool_call

    def _add_trace(
        self,
        *,
        task: Task,
        step_order: int,
        step_name: str,
        input_summary: str,
        output_summary: str,
        evidence_ids: list[str] | None = None,
        tool_calls: list[dict[str, object]] | None = None,
    ) -> AgentTrace:
        trace = AgentTrace(
            task_id=task.id,
            step_name=step_name,
            step_order=step_order,
            status=AgentTraceStatus.COMPLETED.value,
            input_summary=input_summary,
            output_summary=output_summary,
            evidence_ids=json.dumps(evidence_ids or [], ensure_ascii=False),
            tool_calls=json.dumps(tool_calls or [], ensure_ascii=False),
            token_usage=json.dumps({}, ensure_ascii=False),
            latency_ms=0,
            completed_at=datetime.utcnow(),
        )
        self.db.add(trace)
        self.db.flush()
        return trace


class ReviewRepositoryNotReadyError(ValueError):
    pass


class ReviewValidationError(ValueError):
    pass


def _empty_review_output() -> dict[str, object]:
    return {
        "summary": None,
        "risk_level": None,
        "risks": [],
        "impacted_symbols": [],
        "suggested_tests": [],
        "citations": [],
        "markdown": None,
    }


def _build_tool_call_response(tool_call: ToolCall) -> ReviewToolCallResponse:
    return ReviewToolCallResponse(
        id=tool_call.id,
        tool_name=tool_call.tool_name,
        status=tool_call.status,
        permission_decision=tool_call.permission_decision,
        input_summary=tool_call.input_summary,
        output_summary=tool_call.output_summary,
        latency_ms=tool_call.latency_ms,
        error_message=tool_call.error_message,
        created_at=tool_call.created_at,
        completed_at=tool_call.completed_at,
    )


def _load_json_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_dict_list(value: Any) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _load_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _review_search_query(diff_analysis, mapping) -> str:
    symbols = _deduplicate_strings([match.symbol_name for match in mapping.matches])
    files = _changed_files(diff_analysis)
    query_parts = [*symbols[:8], *files[:8]]
    if query_parts:
        return " ".join(query_parts)
    return "review changed code"


def _changed_files(diff_analysis) -> list[str]:
    return _deduplicate_strings(
        [
            file_path
            for diff_file in diff_analysis.files
            for file_path in [diff_file.new_path or diff_file.old_path]
            if file_path
        ]
    )


def _unique_symbol_context_targets(mapping):
    targets = []
    seen: set[tuple[str, str]] = set()
    for match in mapping.matches:
        key = (match.symbol_name, match.file_path)
        if key in seen:
            continue
        seen.add(key)
        targets.append(match)
    return targets


def _tool_call_summary(tool_call: ToolCall | None) -> dict[str, object]:
    if tool_call is None:
        return {}
    return {
        "id": tool_call.id,
        "tool_name": tool_call.tool_name,
        "status": tool_call.status,
        "permission_decision": tool_call.permission_decision,
        "latency_ms": tool_call.latency_ms,
        "input_summary": tool_call.input_summary,
        "output_summary": tool_call.output_summary,
        "error_message": tool_call.error_message,
    }


def _tool_status_from_static_check(result: StaticCheckResult) -> str:
    if result.status == "disabled":
        return ToolCallStatus.DISABLED.value
    if result.status == "denied":
        return ToolCallStatus.DENIED.value
    return ToolCallStatus.COMPLETED.value


def _elapsed_ms(started: float) -> int:
    return max(int((perf_counter() - started) * 1000), 0)


def _deduplicate_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated
