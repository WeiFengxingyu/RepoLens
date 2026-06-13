from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ToolCallStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"
    DISABLED = "disabled"


class ToolPermissionDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    DISABLED = "disabled"


class ToolCall(Base):
    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("ix_tool_calls_task_order", "task_id", "created_at"),
        Index("ix_tool_calls_repository_tool", "repository_id", "tool_name"),
        Index("ix_tool_calls_permission", "permission_decision", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trace_id: Mapped[str | None] = mapped_column(
        ForeignKey("agent_traces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ToolCallStatus.RUNNING.value,
        index=True,
    )
    permission_decision: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ToolPermissionDecision.ALLOW.value,
        index=True,
    )
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="tool_calls")
    trace: Mapped["AgentTrace"] = relationship(back_populates="tool_call_records")
    repository: Mapped["Repository"] = relationship(back_populates="tool_calls")


from app.models.agent_trace import AgentTrace  # noqa: E402
from app.models.repository import Repository  # noqa: E402
from app.models.task import Task  # noqa: E402
