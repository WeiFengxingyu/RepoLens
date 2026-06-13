from __future__ import annotations

from dataclasses import dataclass, field
import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CodeChunk, CodeRelation, RelationType, SymbolType
from app.services.tools import DiffAnalysis, DiffFile


class DiffMapperError(ValueError):
    """Raised when diff-to-symbol mapping input is invalid."""


@dataclass(frozen=True)
class DiffSymbolMatch:
    repository_id: str
    file_path: str
    change_type: str
    line_type: str
    line: int
    hunk_index: int
    chunk_id: str
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict[str, object]:
        return {
            "repository_id": self.repository_id,
            "file_path": self.file_path,
            "change_type": self.change_type,
            "line_type": self.line_type,
            "line": self.line,
            "hunk_index": self.hunk_index,
            "chunk_id": self.chunk_id,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass(frozen=True)
class UnmatchedDiffLine:
    file_path: str
    change_type: str
    line_type: str
    line: int
    hunk_index: int
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type,
            "line_type": self.line_type,
            "line": self.line,
            "hunk_index": self.hunk_index,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DiffSymbolMappingResult:
    repository_id: str
    matches: list[DiffSymbolMatch] = field(default_factory=list)
    unmatched_lines: list[UnmatchedDiffLine] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return len(self.matches)

    @property
    def unmatched_count(self) -> int:
        return len(self.unmatched_lines)

    def to_dict(self) -> dict[str, object]:
        return {
            "repository_id": self.repository_id,
            "matches": [match.to_dict() for match in self.matches],
            "unmatched_lines": [line.to_dict() for line in self.unmatched_lines],
            "match_count": self.match_count,
            "unmatched_count": self.unmatched_count,
        }


def map_diff_to_symbols(
    db: Session,
    repository_id: str,
    diff_analysis: DiffAnalysis,
) -> DiffSymbolMappingResult:
    chunks_by_file = _load_chunks_by_file(db, repository_id)
    matches: list[DiffSymbolMatch] = []
    unmatched_lines: list[UnmatchedDiffLine] = []

    for diff_file in diff_analysis.files:
        for hunk_index, hunk in enumerate(diff_file.hunks, start=1):
            changed_lines = [
                *[
                    ("added", _changed_file_path(diff_file, line_type="added"), line)
                    for line in hunk.added_lines
                ],
                *[
                    ("removed", _changed_file_path(diff_file, line_type="removed"), line)
                    for line in hunk.removed_lines
                ],
            ]
            for line_type, file_path, diff_line in changed_lines:
                if file_path is None:
                    continue
                chunk = _best_chunk_for_line(chunks_by_file.get(file_path, []), diff_line.line)
                if chunk is None:
                    unmatched_lines.append(
                        UnmatchedDiffLine(
                            file_path=file_path,
                            change_type=diff_file.change_type,
                            line_type=line_type,
                            line=diff_line.line,
                            hunk_index=hunk_index,
                            reason="no_chunk_for_changed_line",
                        )
                    )
                    continue
                matches.append(
                    DiffSymbolMatch(
                        repository_id=repository_id,
                        file_path=file_path,
                        change_type=diff_file.change_type,
                        line_type=line_type,
                        line=diff_line.line,
                        hunk_index=hunk_index,
                        chunk_id=chunk.id,
                        symbol_name=chunk.symbol_name,
                        symbol_type=chunk.symbol_type,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                    )
                )

    return DiffSymbolMappingResult(
        repository_id=repository_id,
        matches=matches,
        unmatched_lines=unmatched_lines,
    )


def write_changed_by_relations(
    db: Session,
    repository_id: str,
    task_id: str,
    mapping: DiffSymbolMappingResult,
) -> list[CodeRelation]:
    if not task_id.strip():
        raise DiffMapperError("task_id is required.")
    if mapping.repository_id != repository_id:
        raise DiffMapperError("mapping repository_id does not match repository_id.")

    db.execute(
        delete(CodeRelation).where(
            CodeRelation.repository_id == repository_id,
            CodeRelation.relation_type == RelationType.CHANGED_BY.value,
            CodeRelation.extra_metadata.like(f'%"task_id": "{task_id}"%'),
        )
    )

    relations = [
        CodeRelation(
            repository_id=repository_id,
            source_id=match.chunk_id,
            target_id=None,
            source_symbol=match.symbol_name,
            target_symbol="diff",
            relation_type=RelationType.CHANGED_BY.value,
            source_file=match.file_path,
            target_file=match.file_path,
            extra_metadata=json.dumps(
                {
                    "task_id": task_id,
                    "hunk_index": match.hunk_index,
                    "line": match.line,
                    "line_type": match.line_type,
                    "change_type": match.change_type,
                },
                sort_keys=True,
            ),
        )
        for match in mapping.matches
    ]
    db.add_all(relations)
    db.flush()
    return relations


def _load_chunks_by_file(db: Session, repository_id: str) -> dict[str, list[CodeChunk]]:
    chunks = db.scalars(
        select(CodeChunk)
        .where(CodeChunk.repository_id == repository_id)
        .order_by(CodeChunk.file_path, CodeChunk.start_line, CodeChunk.end_line, CodeChunk.id)
    ).all()
    chunks_by_file: dict[str, list[CodeChunk]] = {}
    for chunk in chunks:
        chunks_by_file.setdefault(chunk.file_path, []).append(chunk)
    return chunks_by_file


def _best_chunk_for_line(chunks: list[CodeChunk], line: int) -> CodeChunk | None:
    matched = [chunk for chunk in chunks if chunk.start_line <= line <= chunk.end_line]
    if not matched:
        file_level_chunks = [
            chunk for chunk in chunks if chunk.symbol_type == SymbolType.FILE.value
        ]
        return file_level_chunks[0] if file_level_chunks else None
    return sorted(
        matched,
        key=lambda chunk: (
            chunk.end_line - chunk.start_line,
            chunk.symbol_type == SymbolType.FILE.value,
            chunk.start_line,
            chunk.symbol_name,
        ),
    )[0]


def _changed_file_path(diff_file: DiffFile, *, line_type: str) -> str | None:
    if line_type == "removed":
        return diff_file.old_path or diff_file.new_path
    return diff_file.new_path or diff_file.old_path
