import json
from typing import Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentTrace, Repository, RepositoryStatus, Task, TaskStatus, TaskType
from app.schemas.qa import (
    AgentTraceResponse,
    QACitationResponse,
    QACreateRequest,
    QATaskResponse,
)
from app.core.config import Settings
from app.services.agent import (
    OpenAICompatibleChatAdapter,
    RetrievalOptions,
    chat_config_from_settings,
    run_qa_orchestrator,
)


class QAService:
    def __init__(self, db: Session):
        self.db = db

    def get_repository(self, repository_id: str) -> Repository | None:
        return self.db.get(Repository, repository_id)

    def create_question_task(
        self,
        repository: Repository,
        request: QACreateRequest,
    ) -> Task:
        payload = {
            "question": request.question.strip(),
            "top_k": request.top_k,
            "use_bm25": request.use_bm25,
            "use_vector": request.use_vector,
            "use_graph": request.use_graph,
        }
        task = Task(
            repository_id=repository.id,
            task_type=TaskType.QA.value,
            status=TaskStatus.PENDING.value,
            input_payload=json.dumps(payload, ensure_ascii=False),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def run_question_task(
        self,
        task: Task,
        request: QACreateRequest,
        settings: Settings,
    ) -> Task:
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        self.db.commit()
        chat_adapter = OpenAICompatibleChatAdapter(chat_config_from_settings(settings))
        try:
            final_state = run_qa_orchestrator(
                self.db,
                task.id,
                task.repository_id,
                request.question.strip(),
                settings,
                options=RetrievalOptions(
                    top_k=request.top_k,
                    use_bm25=request.use_bm25,
                    use_vector=request.use_vector,
                    use_graph=request.use_graph,
                ),
                chat_adapter=chat_adapter,
            )
        except Exception as exc:
            task.status = TaskStatus.FAILED.value
            task.error_message = str(exc)
            task.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
            return task

        task.status = TaskStatus.COMPLETED.value
        task.output_payload = json.dumps(_qa_answer_to_output(final_state["final_answer"]), ensure_ascii=False)
        task.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self.db.get(Task, task_id)

    def build_task_response(self, task: Task) -> QATaskResponse:
        input_payload = _load_json_object(task.input_payload)
        output_payload = _load_json_object(task.output_payload or "{}")
        traces = self.db.scalars(
            select(AgentTrace)
            .where(AgentTrace.task_id == task.id)
            .order_by(AgentTrace.step_order, AgentTrace.created_at, AgentTrace.id)
        ).all()

        return QATaskResponse(
            task_id=task.id,
            repository_id=task.repository_id,
            status=task.status,
            question=str(input_payload.get("question", "")),
            answer=_optional_str(output_payload.get("answer")),
            citations=[
                _build_citation_response(citation)
                for citation in _load_json_list(output_payload.get("citations"))
            ],
            confidence=_optional_float(output_payload.get("confidence")),
            warnings=[str(warning) for warning in _load_json_list(output_payload.get("warnings"))],
            error_message=task.error_message,
            traces=[_build_trace_response(trace) for trace in traces],
            created_at=task.created_at,
            completed_at=task.completed_at,
        )

    def ensure_repository_ready(self, repository: Repository) -> None:
        if repository.status != RepositoryStatus.READY.value:
            raise RepositoryNotReadyError("Repository must be ready before QA.")


class RepositoryNotReadyError(ValueError):
    pass


def _build_citation_response(value: Any) -> QACitationResponse:
    citation = value if isinstance(value, dict) else {}
    return QACitationResponse(
        evidence_id=str(citation.get("evidence_id", "")),
        chunk_id=str(citation.get("chunk_id", "")),
        file_path=str(citation.get("file_path", "")),
        start_line=int(citation.get("start_line", 0)),
        end_line=int(citation.get("end_line", 0)),
        symbol_name=str(citation.get("symbol_name", "")),
        symbol_type=str(citation.get("symbol_type", "")),
        language=str(citation.get("language", "")),
        score=float(citation.get("score", 0)),
        sources=[str(source) for source in _load_json_list(citation.get("sources"))],
        snippet=str(citation.get("snippet", "")),
    )


def _build_trace_response(trace: AgentTrace) -> AgentTraceResponse:
    return AgentTraceResponse(
        id=trace.id,
        step_name=trace.step_name,
        step_order=trace.step_order,
        status=trace.status,
        input_summary=trace.input_summary,
        output_summary=trace.output_summary,
        evidence_ids=[str(evidence_id) for evidence_id in _load_json_list(trace.evidence_ids)],
        tool_calls=[
            tool_call if isinstance(tool_call, dict) else {"value": tool_call}
            for tool_call in _load_json_list(trace.tool_calls)
        ],
        token_usage=_load_json_object(trace.token_usage),
        latency_ms=trace.latency_ms,
        error_message=trace.error_message,
        created_at=trace.created_at,
        completed_at=trace.completed_at,
    )


def _load_json_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _qa_answer_to_output(answer) -> dict[str, object]:
    return {
        "answer": answer.answer,
        "citations": [
            {
                "evidence_id": citation.evidence_id,
                "chunk_id": citation.chunk_id,
                "file_path": citation.file_path,
                "start_line": citation.start_line,
                "end_line": citation.end_line,
                "symbol_name": citation.symbol_name,
                "symbol_type": citation.symbol_type,
                "language": citation.language,
                "score": citation.score,
                "sources": citation.sources,
                "snippet": citation.snippet,
            }
            for citation in answer.citations
        ],
        "confidence": answer.confidence,
        "warnings": answer.warnings,
        "verification": answer.verification,
    }
