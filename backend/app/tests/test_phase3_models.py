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
)


def test_phase3_tables_are_created() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    tables = set(inspect(engine).get_table_names())

    assert {"tasks", "agent_traces"}.issubset(tables)


def test_task_and_agent_trace_round_trip() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    question_payload = {
        "question": "Where is repository import implemented?",
        "top_k": 8,
        "use_bm25": True,
        "use_vector": True,
        "use_graph": True,
    }
    output_payload = {
        "answer": "Repository import starts in the repository API. [1]",
        "citations": [{"evidence_id": "ev_1", "file_path": "backend/app/api/repositories.py"}],
        "confidence": 0.8,
    }
    token_usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

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
            task_type=TaskType.QA.value,
            status=TaskStatus.COMPLETED.value,
            input_payload=json.dumps(question_payload),
            output_payload=json.dumps(output_payload),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        session.add(task)
        session.flush()

        trace = AgentTrace(
            task_id=task.id,
            step_name="Planner",
            step_order=1,
            status=AgentTraceStatus.COMPLETED.value,
            input_summary="question=Where is repository import implemented?",
            output_summary="question_type=feature_location",
            evidence_ids=json.dumps(["ev_1"]),
            tool_calls=json.dumps([]),
            token_usage=json.dumps(token_usage),
            latency_ms=3,
            completed_at=datetime.utcnow(),
        )
        session.add(trace)
        session.commit()

        stored_task = session.get(Task, task.id)

        assert stored_task is not None
        assert stored_task.repository.name == "demo"
        assert json.loads(stored_task.input_payload) == question_payload
        assert json.loads(stored_task.output_payload or "{}") == output_payload
        assert stored_task.traces[0].step_name == "Planner"
        assert json.loads(stored_task.traces[0].token_usage) == token_usage


def test_repository_delete_cascades_phase3_tasks_and_traces() -> None:
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
            task_type=TaskType.QA.value,
            status=TaskStatus.COMPLETED.value,
            input_payload=json.dumps({"question": "main"}),
        )
        trace = AgentTrace(
            task=task,
            step_name="Planner",
            step_order=1,
            status=AgentTraceStatus.COMPLETED.value,
            input_summary="question=main",
            output_summary="question_type=function_explanation",
        )
        session.add(repository)
        session.flush()
        task_id = task.id
        trace_id = trace.id
        session.delete(repository)
        session.commit()

        assert session.scalar(select(Task).where(Task.id == task_id)) is None
        assert session.scalar(select(AgentTrace).where(AgentTrace.id == trace_id)) is None
