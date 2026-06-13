import json
from datetime import datetime

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    AgentTrace,
    AgentTraceStatus,
    Repository,
    RepositorySourceType,
    RepositoryStatus,
    Task,
    TaskStatus,
    TaskType,
    ToolCall,
    ToolCallStatus,
    ToolPermissionDecision,
)


def test_phase4_tool_calls_table_is_created() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    tables = set(inspect(engine).get_table_names())

    assert "tool_calls" in tables


def test_tool_call_round_trip_with_task_trace_and_repository() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    input_payload = {"query": "repository import", "top_k": 8}
    output_payload = {"evidence_count": 2}

    with Session(engine) as session:
        repository = Repository(
            name="demo",
            source_type=RepositorySourceType.LOCAL.value,
            local_path="F:/Desktop/demo",
            status=RepositoryStatus.READY.value,
        )
        session.add(repository)
        session.flush()

        task = Task(
            repository_id=repository.id,
            task_type=TaskType.REVIEW.value,
            status=TaskStatus.RUNNING.value,
            input_payload=json.dumps({"diff_text": "diff --git a/app.py b/app.py"}),
        )
        session.add(task)
        session.flush()

        trace = AgentTrace(
            task_id=task.id,
            step_name="ToolRunner",
            step_order=1,
            status=AgentTraceStatus.COMPLETED.value,
            input_summary="run code_search",
            output_summary="tool completed",
        )
        session.add(trace)
        session.flush()

        tool_call = ToolCall(
            task_id=task.id,
            trace_id=trace.id,
            repository_id=repository.id,
            tool_name="code_search",
            status=ToolCallStatus.COMPLETED.value,
            permission_decision=ToolPermissionDecision.ALLOW.value,
            input_summary="query=repository import, top_k=8",
            output_summary="evidence_count=2",
            input_payload=json.dumps(input_payload),
            output_payload=json.dumps(output_payload),
            latency_ms=12,
            completed_at=datetime.utcnow(),
        )
        session.add(tool_call)
        session.commit()

        stored = session.get(ToolCall, tool_call.id)

        assert stored is not None
        assert stored.task.task_type == TaskType.REVIEW.value
        assert stored.trace.step_name == "ToolRunner"
        assert stored.repository.name == "demo"
        assert json.loads(stored.input_payload or "{}") == input_payload
        assert json.loads(stored.output_payload or "{}") == output_payload
        assert stored.permission_decision == ToolPermissionDecision.ALLOW.value
        assert stored.latency_ms == 12


def test_task_delete_cascades_tool_calls() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        repository = Repository(
            name="demo",
            source_type=RepositorySourceType.LOCAL.value,
            local_path="F:/Desktop/demo",
            status=RepositoryStatus.READY.value,
        )
        task = Task(
            repository=repository,
            task_type=TaskType.REVIEW.value,
            status=TaskStatus.COMPLETED.value,
            input_payload=json.dumps({"diff_text": "diff"}),
        )
        tool_call = ToolCall(
            task=task,
            repository=repository,
            tool_name="read_file_slice",
            status=ToolCallStatus.DENIED.value,
            permission_decision=ToolPermissionDecision.DENY.value,
            input_summary="file_path=../.env",
            output_summary="denied",
            error_message="Path traversal is not allowed.",
        )
        session.add(repository)
        session.flush()
        tool_call_id = tool_call.id
        session.delete(task)
        session.commit()

        assert session.scalar(select(ToolCall).where(ToolCall.id == tool_call_id)) is None
