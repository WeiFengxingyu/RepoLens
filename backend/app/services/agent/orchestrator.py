import json
from time import perf_counter
from typing import Callable

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AgentTrace, AgentTraceStatus
from app.services.agent.chat import OpenAICompatibleChatAdapter
from app.services.agent.qa_agents import (
    plan_question,
    retrieve_for_plan,
    review_answer,
    verify_draft,
    write_report,
)
from app.services.agent.state import (
    AgentToolCall,
    QAAgentState,
    QAPlan,
    RetrievalOptions,
)
from app.services.retrieval import build_context_package
from app.services.retrieval.evidence import Evidence


def run_qa_orchestrator(
    db: Session,
    task_id: str,
    repository_id: str,
    question: str,
    settings: Settings,
    *,
    options: RetrievalOptions,
    chat_adapter: OpenAICompatibleChatAdapter | None = None,
) -> QAAgentState:
    graph = _build_graph()
    initial_state: QAAgentState = {
        "task_id": task_id,
        "repository_id": repository_id,
        "question": question,
        "settings": settings,
        "db": db,
        "chat_adapter": chat_adapter,
        "options": options,
        "retrieval_attempts": 0,
        "evidences": [],
        "context_text": "",
        "context_truncated": False,
        "warnings": [],
        "step_order": 0,
    }
    return graph.invoke(initial_state)


def _build_graph():
    graph = StateGraph(QAAgentState)
    graph.add_node("planner", _node_with_trace("Planner", _planner_node))
    graph.add_node("retriever", _node_with_trace("Retriever", _retriever_node))
    graph.add_node("answer_reviewer", _node_with_trace("AnswerReviewer", _answer_reviewer_node))
    graph.add_node("verifier", _node_with_trace("Verifier", _verifier_node))
    graph.add_node("report_writer", _node_with_trace("ReportWriter", _report_writer_node))
    graph.set_entry_point("planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "answer_reviewer")
    graph.add_edge("answer_reviewer", "verifier")
    graph.add_conditional_edges(
        "verifier",
        _route_after_verifier,
        {"retrieve_again": "retriever", "write_report": "report_writer"},
    )
    graph.add_edge("report_writer", END)
    return graph.compile()


def _node_with_trace(step_name: str, node: Callable[[QAAgentState], QAAgentState]):
    def wrapped(state: QAAgentState) -> QAAgentState:
        started_at = perf_counter()
        try:
            next_state = node(state)
        except Exception as exc:
            _record_trace(
                state,
                step_name=step_name,
                status=AgentTraceStatus.FAILED.value,
                latency_ms=_elapsed_ms(started_at),
                error_message=str(exc),
            )
            raise

        _record_trace(
            next_state,
            step_name=step_name,
            status=AgentTraceStatus.COMPLETED.value,
            latency_ms=_elapsed_ms(started_at),
        )
        return next_state

    return wrapped


def _planner_node(state: QAAgentState) -> QAAgentState:
    plan = plan_question(state["question"])
    return {**state, "plan": plan}


def _retriever_node(state: QAAgentState) -> QAAgentState:
    retrieval_attempts = int(state.get("retrieval_attempts", 0)) + 1
    plan = state["plan"]
    if state.get("second_retrieval_query"):
        plan = QAPlan(
            question_type=plan.question_type,
            retrieval_queries=[str(state["second_retrieval_query"])],
            answer_style=plan.answer_style,
            use_graph=plan.use_graph,
        )

    result = retrieve_for_plan(
        state["db"],
        state["repository_id"],
        plan,
        state["settings"],
        options=state["options"],
    )
    evidences = _deduplicate_evidences([*state.get("evidences", []), *result.evidences])
    context = build_context_package(evidences, max_evidence_count=12, max_chars=12000)
    warnings = _deduplicate_strings([*state.get("warnings", []), *result.warnings])
    tool_calls = [*state.get("last_tool_calls", []), *result.tool_calls]
    return {
        **state,
        "retrieval_attempts": retrieval_attempts,
        "evidences": evidences,
        "context_text": context.context_text,
        "context_truncated": context.truncated,
        "warnings": warnings,
        "last_tool_calls": tool_calls,
        "second_retrieval_query": None,
    }


def _answer_reviewer_node(state: QAAgentState) -> QAAgentState:
    draft = review_answer(
        state["question"],
        state.get("evidences", []),
        state.get("context_text", ""),
        chat_adapter=state.get("chat_adapter"),
    )
    return {**state, "draft": draft}


def _verifier_node(state: QAAgentState) -> QAAgentState:
    verification = verify_draft(
        state["draft"],
        state.get("evidences", []),
        question=state["question"],
        retrieval_attempts=int(state.get("retrieval_attempts", 1)),
    )
    return {
        **state,
        "verification": verification,
        "second_retrieval_query": verification.second_retrieval_query,
    }


def _report_writer_node(state: QAAgentState) -> QAAgentState:
    final_answer = write_report(
        state["draft"],
        state["verification"],
        state.get("evidences", []),
        warnings=state.get("warnings", []),
        retrieval_attempts=int(state.get("retrieval_attempts", 1)),
    )
    return {**state, "final_answer": final_answer}


def _route_after_verifier(state: QAAgentState) -> str:
    verification = state["verification"]
    return "retrieve_again" if verification.needs_second_retrieval else "write_report"


def _record_trace(
    state: QAAgentState,
    *,
    step_name: str,
    status: str,
    latency_ms: int,
    error_message: str | None = None,
) -> None:
    db = state.get("db")
    task_id = state.get("task_id")
    if not isinstance(db, Session) or not isinstance(task_id, str):
        return

    state["step_order"] = int(state.get("step_order", 0)) + 1
    trace = AgentTrace(
        task_id=task_id,
        step_name=step_name,
        step_order=int(state["step_order"]),
        status=status,
        input_summary=_input_summary(step_name, state),
        output_summary=_output_summary(step_name, state) if status == AgentTraceStatus.COMPLETED.value else None,
        evidence_ids=json.dumps([evidence.evidence_id for evidence in state.get("evidences", [])]),
        tool_calls=json.dumps(_tool_calls_for_trace(step_name, state), ensure_ascii=False),
        token_usage=json.dumps(_token_usage_for_trace(step_name, state), ensure_ascii=False),
        latency_ms=latency_ms,
        error_message=error_message,
    )
    db.add(trace)
    db.commit()


def _input_summary(step_name: str, state: QAAgentState) -> str:
    if step_name == "Retriever":
        return f"attempt={state.get('retrieval_attempts', 0)}, question={state.get('question', '')}"
    return f"question={state.get('question', '')}"


def _output_summary(step_name: str, state: QAAgentState) -> str:
    if step_name == "Planner":
        plan = state.get("plan")
        return (
            f"question_type={plan.question_type}, queries={len(plan.retrieval_queries)}"
            if isinstance(plan, QAPlan)
            else "no plan"
        )
    if step_name == "Retriever":
        return (
            f"attempts={state.get('retrieval_attempts', 0)}, "
            f"evidence_count={len(state.get('evidences', []))}"
        )
    if step_name == "AnswerReviewer":
        draft = state.get("draft")
        return f"chat_mode={draft.chat_mode}, claims={len(draft.claims)}" if draft else "no draft"
    if step_name == "Verifier":
        verification = state.get("verification")
        if verification is None:
            return "no verification"
        return (
            f"supported={verification.supported}, missing={len(verification.missing_claims)}, "
            f"needs_second_retrieval={verification.needs_second_retrieval}"
        )
    if step_name == "ReportWriter":
        final_answer = state.get("final_answer")
        return (
            f"citations={len(final_answer.citations)}, confidence={final_answer.confidence}"
            if final_answer
            else "no final answer"
        )
    return "completed"


def _tool_calls_for_trace(step_name: str, state: QAAgentState) -> list[dict[str, object]]:
    if step_name != "Retriever":
        return []
    return [_tool_call_to_dict(tool_call) for tool_call in state.get("last_tool_calls", [])]


def _token_usage_for_trace(step_name: str, state: QAAgentState) -> dict[str, object]:
    if step_name != "AnswerReviewer":
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": "rules"}
    draft = state.get("draft")
    return dict(draft.token_usage) if draft else {}


def _tool_call_to_dict(tool_call: AgentToolCall) -> dict[str, object]:
    return {
        "tool_name": tool_call.tool_name,
        "input_summary": tool_call.input_summary,
        "output_summary": tool_call.output_summary,
        "permission_decision": tool_call.permission_decision,
        "latency_ms": tool_call.latency_ms,
        "success": tool_call.success,
        "error": tool_call.error,
    }


def _deduplicate_evidences(evidences: list[Evidence]) -> list[Evidence]:
    best_by_chunk_id: dict[str, Evidence] = {}
    for evidence in evidences:
        current = best_by_chunk_id.get(evidence.chunk_id)
        if current is None or evidence.score > current.score:
            best_by_chunk_id[evidence.chunk_id] = evidence
    return sorted(
        best_by_chunk_id.values(),
        key=lambda evidence: (-evidence.score, evidence.file_path, evidence.start_line, evidence.chunk_id),
    )


def _deduplicate_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _elapsed_ms(started_at: float) -> int:
    return max(int((perf_counter() - started_at) * 1000), 0)
