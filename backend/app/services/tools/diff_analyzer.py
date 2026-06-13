from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Final


DIFF_MAX_CHARS: Final = 200_000
HUNK_MAX_LINES: Final = 2_000

CHANGE_TYPE_ADDED: Final = "added"
CHANGE_TYPE_DELETED: Final = "deleted"
CHANGE_TYPE_MODIFIED: Final = "modified"
CHANGE_TYPE_RENAMED: Final = "renamed"

_HUNK_RE: Final = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@(?P<section>.*)$"
)


class DiffAnalyzerError(ValueError):
    """Raised when a diff cannot be analyzed within Phase 4 limits."""


@dataclass(frozen=True)
class DiffLine:
    line: int
    content: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "content": self.content,
        }


@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    section_header: str | None = None
    added_lines: list[DiffLine] = field(default_factory=list)
    removed_lines: list[DiffLine] = field(default_factory=list)
    context_line_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "old_start": self.old_start,
            "old_count": self.old_count,
            "new_start": self.new_start,
            "new_count": self.new_count,
            "section_header": self.section_header,
            "added_lines": [line.to_dict() for line in self.added_lines],
            "removed_lines": [line.to_dict() for line in self.removed_lines],
            "context_line_count": self.context_line_count,
        }


@dataclass
class DiffFile:
    old_path: str | None
    new_path: str | None
    change_type: str = CHANGE_TYPE_MODIFIED
    hunks: list[DiffHunk] = field(default_factory=list)
    binary: bool = False

    @property
    def added_line_count(self) -> int:
        return sum(len(hunk.added_lines) for hunk in self.hunks)

    @property
    def removed_line_count(self) -> int:
        return sum(len(hunk.removed_lines) for hunk in self.hunks)

    def to_dict(self) -> dict[str, object]:
        return {
            "old_path": self.old_path,
            "new_path": self.new_path,
            "change_type": self.change_type,
            "binary": self.binary,
            "hunks": [hunk.to_dict() for hunk in self.hunks],
            "added_line_count": self.added_line_count,
            "removed_line_count": self.removed_line_count,
        }


@dataclass(frozen=True)
class DiffAnalysis:
    files: list[DiffFile]

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def added_line_count(self) -> int:
        return sum(file.added_line_count for file in self.files)

    @property
    def removed_line_count(self) -> int:
        return sum(file.removed_line_count for file in self.files)

    def to_dict(self) -> dict[str, object]:
        return {
            "files": [file.to_dict() for file in self.files],
            "file_count": self.file_count,
            "added_line_count": self.added_line_count,
            "removed_line_count": self.removed_line_count,
        }


def analyze_diff(diff_text: str) -> DiffAnalysis:
    if not diff_text.strip():
        raise DiffAnalyzerError("Diff text is empty.")
    if len(diff_text) > DIFF_MAX_CHARS:
        raise DiffAnalyzerError(f"Diff text exceeds {DIFF_MAX_CHARS} characters.")

    files: list[DiffFile] = []
    current_file: DiffFile | None = None
    current_hunk: DiffHunk | None = None
    old_line = 0
    new_line = 0
    hunk_line_count = 0

    for raw_line in diff_text.splitlines():
        hunk_match = _HUNK_RE.match(raw_line)

        if raw_line.startswith("diff --git "):
            current_file = _file_from_git_header(raw_line)
            files.append(current_file)
            current_hunk = None
            continue

        if hunk_match:
            if current_file is None:
                current_file = DiffFile(old_path=None, new_path=None)
                files.append(current_file)
            current_hunk = _hunk_from_match(hunk_match)
            current_file.hunks.append(current_hunk)
            old_line = current_hunk.old_start
            new_line = current_hunk.new_start
            hunk_line_count = 0
            continue

        if current_hunk is not None and _is_hunk_body_line(raw_line):
            old_line, new_line, hunk_line_count = _append_hunk_line(
                raw_line=raw_line,
                hunk=current_hunk,
                old_line=old_line,
                new_line=new_line,
                hunk_line_count=hunk_line_count,
            )
            continue

        if raw_line.startswith("--- "):
            if current_file is None:
                current_file = DiffFile(old_path=None, new_path=None)
                files.append(current_file)
            current_file.old_path = _parse_file_marker_path(raw_line[4:])
            _refresh_change_type(current_file)
            continue

        if raw_line.startswith("+++ "):
            if current_file is None:
                current_file = DiffFile(old_path=None, new_path=None)
                files.append(current_file)
            current_file.new_path = _parse_file_marker_path(raw_line[4:])
            _refresh_change_type(current_file)
            continue

        if current_file is None:
            continue

        _apply_file_metadata(raw_line, current_file)

    if not files:
        raise DiffAnalyzerError("Diff format is not supported.")

    for file in files:
        _refresh_change_type(file)

    return DiffAnalysis(files=files)


def _file_from_git_header(line: str) -> DiffFile:
    parts = line.removeprefix("diff --git ").split()
    old_path = _parse_file_marker_path(parts[0]) if parts else None
    new_path = _parse_file_marker_path(parts[1]) if len(parts) > 1 else old_path
    return DiffFile(old_path=old_path, new_path=new_path)


def _hunk_from_match(match: re.Match[str]) -> DiffHunk:
    old_count = match.group("old_count")
    new_count = match.group("new_count")
    section = match.group("section").strip()
    return DiffHunk(
        old_start=int(match.group("old_start")),
        old_count=int(old_count) if old_count is not None else 1,
        new_start=int(match.group("new_start")),
        new_count=int(new_count) if new_count is not None else 1,
        section_header=section or None,
    )


def _append_hunk_line(
    *,
    raw_line: str,
    hunk: DiffHunk,
    old_line: int,
    new_line: int,
    hunk_line_count: int,
) -> tuple[int, int, int]:
    if raw_line.startswith("\\"):
        return old_line, new_line, hunk_line_count

    hunk_line_count += 1
    if hunk_line_count > HUNK_MAX_LINES:
        raise DiffAnalyzerError(f"Diff hunk exceeds {HUNK_MAX_LINES} lines.")

    marker = raw_line[:1]
    content = raw_line[1:]
    if marker == "+":
        hunk.added_lines.append(DiffLine(line=new_line, content=content))
        return old_line, new_line + 1, hunk_line_count
    if marker == "-":
        hunk.removed_lines.append(DiffLine(line=old_line, content=content))
        return old_line + 1, new_line, hunk_line_count

    hunk.context_line_count += 1
    return old_line + 1, new_line + 1, hunk_line_count


def _is_hunk_body_line(line: str) -> bool:
    return line.startswith(("+", "-", " ", "\\"))


def _apply_file_metadata(line: str, file: DiffFile) -> None:
    if line.startswith("new file mode "):
        file.change_type = CHANGE_TYPE_ADDED
        return
    if line.startswith("deleted file mode "):
        file.change_type = CHANGE_TYPE_DELETED
        return
    if line.startswith("rename from "):
        file.old_path = _parse_file_marker_path(line.removeprefix("rename from "))
        file.change_type = CHANGE_TYPE_RENAMED
        return
    if line.startswith("rename to "):
        file.new_path = _parse_file_marker_path(line.removeprefix("rename to "))
        file.change_type = CHANGE_TYPE_RENAMED
        return
    if line.startswith("Binary files ") or line == "GIT binary patch":
        file.binary = True


def _refresh_change_type(file: DiffFile) -> None:
    if file.change_type == CHANGE_TYPE_RENAMED:
        return
    if file.old_path is None and file.new_path is not None:
        file.change_type = CHANGE_TYPE_ADDED
        return
    if file.new_path is None and file.old_path is not None:
        file.change_type = CHANGE_TYPE_DELETED
        return
    if file.change_type not in {CHANGE_TYPE_ADDED, CHANGE_TYPE_DELETED}:
        file.change_type = CHANGE_TYPE_MODIFIED


def _parse_file_marker_path(value: str) -> str | None:
    path = value.strip().split("\t", 1)[0].strip()
    if path == "/dev/null":
        return None
    if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
        path = path[1:-1]
    if path.startswith(("a/", "b/")):
        path = path[2:]
    return path or None
