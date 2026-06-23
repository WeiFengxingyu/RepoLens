from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentSessionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentAssignmentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentMessageType(StrEnum):
    ASSIGNMENT = "assignment"
    ANALYSIS = "analysis"
    DISSENT = "dissent"
    ARBITRATION = "arbitration"
    FINAL = "final"


class AgentSession(Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (
        Index("ix_agent_sessions_repository_status", "repository_id", "status"),
        Index("ix_agent_sessions_task_mode", "task_id", "mode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AgentSessionStatus.PENDING.value,
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    round_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    assignment_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    token_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="agent_sessions")
    repository: Mapped["Repository"] = relationship(back_populates="agent_sessions")
    assignments: Mapped[list["AgentAssignment"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["AgentMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class AgentAssignment(Base):
    __tablename__ = "agent_assignments"
    __table_args__ = (
        Index("ix_agent_assignments_session_round", "session_id", "round_index"),
        Index("ix_agent_assignments_role_status", "role", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AgentAssignmentStatus.PENDING.value,
        index=True,
    )
    round_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    input_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    output_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    dissent: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped["AgentSession"] = relationship(back_populates="assignments")
    messages: Mapped[list["AgentMessage"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    __table_args__ = (
        Index("ix_agent_messages_session_round", "session_id", "round_index"),
        Index("ix_agent_messages_type_sender", "message_type", "sender"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id: Mapped[str | None] = mapped_column(
        ForeignKey("agent_assignments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sender: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(128), nullable=False, default="all")
    message_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    round_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    claims: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requires_arbitration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    session: Mapped["AgentSession"] = relationship(back_populates="messages")
    assignment: Mapped["AgentAssignment"] = relationship(back_populates="messages")


from app.models.repository import Repository  # noqa: E402
from app.models.task import Task  # noqa: E402
