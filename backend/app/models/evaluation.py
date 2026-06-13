from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvaluationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_runs_strategy_status", "strategy", "status"),
        Index("ix_evaluation_runs_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_path: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=EvaluationStatus.PENDING.value,
        index=True,
    )
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repository_map_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.sample_id, EvaluationResult.strategy",
    )


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        Index("ix_evaluation_results_run_strategy", "run_id", "strategy"),
        Index("ix_evaluation_results_sample", "sample_id", "strategy"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_type: Mapped[str] = mapped_column(String(32), nullable=False)
    repository_key: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    hit_at_5: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mrr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    citation_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    matched_files_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    matched_symbols_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    citations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[EvaluationRun] = relationship(back_populates="results")
