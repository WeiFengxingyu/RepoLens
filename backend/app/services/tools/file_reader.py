from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Final


FILE_SLICE_MAX_LINES: Final = 120
FILE_SLICE_MAX_CHARS: Final = 12_000

SENSITIVE_FILE_PATTERNS: Final = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa",
    "secrets.*",
)
BLOCKED_PATH_PARTS: Final = frozenset(
    {
        ".git",
        ".next",
        ".repolens",
        ".venv",
        "node_modules",
    }
)


class FileSliceError(ValueError):
    """Raised when a file slice request violates Phase 4 tool boundaries."""


@dataclass(frozen=True)
class FileSliceResult:
    file_path: str
    start_line: int
    end_line: int
    content: str
    truncated: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "truncated": self.truncated,
        }


def read_file_slice(
    *,
    repository_root: str | Path,
    file_path: str,
    start_line: int,
    end_line: int,
) -> FileSliceResult:
    root = Path(repository_root).expanduser().resolve()
    if not root.exists():
        raise FileSliceError("Repository root does not exist.")
    if not root.is_dir():
        raise FileSliceError("Repository root is not a directory.")
    if start_line < 1:
        raise FileSliceError("start_line must be greater than or equal to 1.")
    if end_line < start_line:
        raise FileSliceError("end_line must be greater than or equal to start_line.")

    relative_path = _validate_relative_path(file_path)
    _validate_path_parts(relative_path.parts)

    candidate_raw = root.joinpath(relative_path)
    if _contains_symlink(candidate_raw, root, relative_path):
        raise FileSliceError("Symlink paths are not allowed.")

    candidate = candidate_raw.resolve()
    try:
        normalized_file_path = candidate.relative_to(root).as_posix()
    except ValueError as exc:
        raise FileSliceError("File path must stay inside the repository root.") from exc

    if not candidate.exists():
        raise FileSliceError("File does not exist.")
    if not candidate.is_file():
        raise FileSliceError("File path is not a regular file.")
    if _looks_binary(candidate):
        raise FileSliceError("Binary files are not allowed.")

    content = candidate.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    if start_line > len(lines):
        raise FileSliceError("start_line exceeds file length.")

    capped_end_line = min(end_line, start_line + FILE_SLICE_MAX_LINES - 1, len(lines))
    selected_lines = lines[start_line - 1 : capped_end_line]
    selected_content = "\n".join(selected_lines)

    truncated = capped_end_line < min(end_line, len(lines))
    if len(selected_content) > FILE_SLICE_MAX_CHARS:
        selected_content = selected_content[:FILE_SLICE_MAX_CHARS]
        truncated = True

    return FileSliceResult(
        file_path=normalized_file_path,
        start_line=start_line,
        end_line=capped_end_line,
        content=selected_content,
        truncated=truncated,
    )


def _validate_relative_path(file_path: str) -> Path:
    if not file_path.strip():
        raise FileSliceError("file_path is required.")

    normalized = file_path.replace("\\", "/")
    path = Path(normalized)
    if path.is_absolute():
        raise FileSliceError("Absolute file paths are not allowed.")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise FileSliceError("Path traversal is not allowed.")
    return path


def _validate_path_parts(parts: tuple[str, ...]) -> None:
    lowered_parts = [part.lower() for part in parts]
    if any(part in BLOCKED_PATH_PARTS for part in lowered_parts):
        raise FileSliceError("Blocked dependency or cache directory is not allowed.")

    file_name = lowered_parts[-1]
    if any(fnmatchcase(file_name, pattern.lower()) for pattern in SENSITIVE_FILE_PATTERNS):
        raise FileSliceError("Sensitive files are not allowed.")


def _looks_binary(path: Path) -> bool:
    try:
        with path.open("rb") as file:
            sample = file.read(4096)
    except OSError as exc:
        raise FileSliceError("File cannot be read.") from exc
    return b"\0" in sample


def _contains_symlink(path: Path, root: Path, relative_path: Path) -> bool:
    current = root
    for part in relative_path.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            return True
    return path.exists() and path.is_symlink()
