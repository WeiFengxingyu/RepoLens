import json

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    AgentAssignment,
    AgentAssignmentStatus,
    AgentMessage,
    AgentMessageType,
    AgentSession,
    AgentSessionStatus,
    Repository,
    RepositorySourceType,
    RepositoryStatus,
    Task,
    TaskStatus,
    TaskType,
)


def test_phase8_multi_agent_tables_are_created() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    tables = set(inspect(engine).get_table_names())

    assert "agent_sessions" in tables
    assert "agent_assignments" in tables
    assert "agent_messages" in tables


def test_multi_agent_session_assignment_message_round_trip() -> None:
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
            task_type=TaskType.MULTI_AGENT_REVIEW.value,
            status=TaskStatus.RUNNING.value,
            input_payload=json.dumps({"diff_text": "diff --git a/app.py b/app.py"}),
        )
        agent_session = AgentSession(
            task=task,
            repository=repository,
            status=AgentSessionStatus.RUNNING.value,
            mode="multi_agent_review",
            round_limit=2,
            assignment_limit=8,
            token_budget=8000,
        )
        assignment = AgentAssignment(
            session=agent_session,
            agent_name="RiskReviewerAgent",
            role="risk_reviewer",
            status=AgentAssignmentStatus.COMPLETED.value,
            round_index=1,
            input_payload=json.dumps({"focus": "functional risks"}),
            output_payload=json.dumps({"risk_count": 1}),
            evidence_ids=json.dumps(["ev-1"]),
            confidence=72,
            token_estimate=32,
            latency_ms=5,
        )
        message = AgentMessage(
            session=agent_session,
            assignment=assignment,
            sender="risk_reviewer",
            recipient="arbiter",
            message_type=AgentMessageType.ANALYSIS.value,
            round_index=1,
            content="Risk reviewer found one functional risk.",
            evidence_ids=json.dumps(["ev-1"]),
            claims=json.dumps(["Changed behavior needs regression coverage."]),
            confidence=72,
            requires_arbitration=True,
        )
        session.add(message)
        session.commit()

        stored_session = session.get(AgentSession, agent_session.id)

        assert stored_session is not None
        assert stored_session.task.task_type == TaskType.MULTI_AGENT_REVIEW.value
        assert stored_session.repository.name == "demo"
        assert stored_session.assignments[0].agent_name == "RiskReviewerAgent"
        assert stored_session.messages[0].sender == "risk_reviewer"
        assert json.loads(stored_session.assignments[0].evidence_ids) == ["ev-1"]
        assert json.loads(stored_session.messages[0].claims) == [
            "Changed behavior needs regression coverage."
        ]


def test_task_delete_cascades_multi_agent_records() -> None:
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
            task_type=TaskType.MULTI_AGENT_REVIEW.value,
            status=TaskStatus.COMPLETED.value,
            input_payload=json.dumps({"diff_text": "diff"}),
        )
        agent_session = AgentSession(
            task=task,
            repository=repository,
            status=AgentSessionStatus.COMPLETED.value,
            mode="multi_agent_review",
        )
        assignment = AgentAssignment(
            session=agent_session,
            agent_name="ArbiterAgent",
            role="arbiter",
            status=AgentAssignmentStatus.COMPLETED.value,
            input_payload="{}",
        )
        message = AgentMessage(
            session=agent_session,
            assignment=assignment,
            sender="arbiter",
            recipient="all",
            message_type=AgentMessageType.FINAL.value,
            content="Final decision.",
        )
        session.add(message)
        session.flush()
        agent_session_id = agent_session.id
        assignment_id = assignment.id
        message_id = message.id

        session.delete(task)
        session.commit()

        assert session.scalar(select(AgentSession).where(AgentSession.id == agent_session_id)) is None
        assert session.scalar(select(AgentAssignment).where(AgentAssignment.id == assignment_id)) is None
        assert session.scalar(select(AgentMessage).where(AgentMessage.id == message_id)) is None
