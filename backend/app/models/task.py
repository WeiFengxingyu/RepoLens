from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaskType(StrEnum):
    QA = "qa"
    REVIEW = "review"
    EVALUATION = "evaluation"
    MCP_TOOL = "mcp_tool"
    MULTI_AGENT_REVIEW = "multi_agent_review"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_repository_status", "repository_id", "status"),
        Index("ix_tasks_type_created", "task_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TaskStatus.PENDING.value,
        index=True,
    )
    input_payload: Mapped[str] = mapped_column("input", Text, nullable=False)
    output_payload: Mapped[str | None] = mapped_column("output", Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    repository: Mapped["Repository"] = relationship(back_populates="tasks")
    traces: Mapped[list["AgentTrace"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    change_requests: Mapped[list["ChangeRequest"]] = relationship(back_populates="task")
    agent_sessions: Mapped[list["AgentSession"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )


from app.models.agent_trace import AgentTrace  # noqa: E402
from app.models.agent_session import AgentSession  # noqa: E402
from app.models.change_request import ChangeRequest  # noqa: E402
from app.models.repository import Repository  # noqa: E402
from app.models.tool_call import ToolCall  # noqa: E402
