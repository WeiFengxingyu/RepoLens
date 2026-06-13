from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RepositorySourceType(StrEnum):
    LOCAL = "local"
    GITHUB = "github"
    GITEE = "gitee"
    GITLAB = "gitlab"
    GENERIC_GIT = "generic_git"


class RepositoryStatus(StrEnum):
    PENDING = "pending"
    CLONING = "cloning"
    SCANNING = "scanning"
    PARSING = "parsing"
    CHUNKING = "chunking"
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language_summary: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parsed_file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RepositoryStatus.PENDING.value,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    chunks: Mapped[list["CodeChunk"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    relations: Mapped[list["CodeRelation"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )


from app.models.code_chunk import CodeChunk  # noqa: E402
from app.models.code_relation import CodeRelation  # noqa: E402
from app.models.task import Task  # noqa: E402
from app.models.tool_call import ToolCall  # noqa: E402
