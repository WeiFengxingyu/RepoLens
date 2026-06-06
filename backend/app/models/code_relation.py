from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RelationType(StrEnum):
    CONTAINS = "contains"
    IMPORTS = "imports"
    CALLS = "calls"
    DEFINED_IN = "defined_in"


class CodeRelation(Base):
    __tablename__ = "code_relations"
    __table_args__ = (
        Index("ix_code_relations_repository_type", "repository_id", "relation_type"),
        Index("ix_code_relations_source", "repository_id", "source_file", "source_symbol"),
        Index("ix_code_relations_target", "repository_id", "target_symbol"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_symbol: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_symbol: Mapped[str | None] = mapped_column(String(512), nullable=True)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_file: Mapped[str] = mapped_column(Text, nullable=False)
    target_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    repository: Mapped["Repository"] = relationship(back_populates="relations")


from app.models.repository import Repository  # noqa: E402

