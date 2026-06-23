from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChangeRequestPlatform(StrEnum):
    GITHUB = "github"
    GITEE = "gitee"
    GITLAB = "gitlab"
    SELF_HOSTED_GITLAB = "self_hosted_gitlab"


class ChangeRequestType(StrEnum):
    PULL_REQUEST = "pull_request"
    MERGE_REQUEST = "merge_request"


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    __table_args__ = (
        Index(
            "ix_change_requests_repository_ref",
            "repository_id",
            "platform",
            "owner",
            "repo",
            "number",
        ),
        Index("ix_change_requests_task", "task_id"),
        Index("ix_change_requests_platform_created", "platform", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[str | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    change_type: Mapped[str] = mapped_column(String(32), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    repo: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    changed_file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    addition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_payload: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    repository: Mapped["Repository"] = relationship(back_populates="change_requests")
    task: Mapped["Task | None"] = relationship(back_populates="change_requests")


from app.models.repository import Repository  # noqa: E402
from app.models.task import Task  # noqa: E402
