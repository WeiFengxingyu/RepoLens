from dataclasses import dataclass, field
from fnmatch import fnmatchcase
import os
from pathlib import Path

from app.models import CodeLanguage


DEFAULT_IGNORED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
        "__pycache__",
        ".next",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "target",
        "vendor",
    }
)
DEFAULT_IGNORED_FILES = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.crt",
    "*.p12",
    "*.pfx",
    "*.log",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.pdf",
    "*.sqlite",
    "*.db",
)
DEFAULT_MAX_FILE_SIZE_BYTES = 1024 * 1024
SUPPORTED_LANGUAGES = {
    CodeLanguage.PYTHON.value,
    CodeLanguage.TYPESCRIPT.value,
    CodeLanguage.JAVASCRIPT.value,
}


class ScannerError(ValueError):
    pass


@dataclass(frozen=True)
class ScanRules:
    ignored_dirs: frozenset[str] = DEFAULT_IGNORED_DIRS
    ignored_files: tuple[str, ...] = DEFAULT_IGNORED_FILES
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES


@dataclass(frozen=True)
class ScannedFile:
    path: Path
    relative_path: str
    language: str
    size_bytes: int


@dataclass(frozen=True)
class SkippedFile:
    relative_path: str
    reason: str


@dataclass(frozen=True)
class ScanResult:
    root_path: Path
    files: list[ScannedFile] = field(default_factory=list)
    skipped_files: list[SkippedFile] = field(default_factory=list)
    language_summary: dict[str, int] = field(default_factory=dict)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def supported_file_count(self) -> int:
        return sum(1 for file in self.files if file.language in SUPPORTED_LANGUAGES)

    @property
    def skipped_file_count(self) -> int:
        return len(self.skipped_files)


def detect_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return CodeLanguage.PYTHON.value
    if suffix in {".ts", ".tsx"}:
        return CodeLanguage.TYPESCRIPT.value
    if suffix in {".js", ".jsx"}:
        return CodeLanguage.JAVASCRIPT.value
    return CodeLanguage.UNKNOWN.value


def scan_repository(root_path: Path, rules: ScanRules | None = None) -> ScanResult:
    rules = rules or ScanRules()
    root = root_path.expanduser().resolve()
    if not root.exists():
        raise ScannerError("Repository scan root does not exist.")
    if not root.is_dir():
        raise ScannerError("Repository scan root is not a directory.")

    files: list[ScannedFile] = []
    skipped_files: list[SkippedFile] = []
    language_summary: dict[str, int] = {}

    for current_dir_raw, dir_names, file_names in os.walk(root):
        current_dir = Path(current_dir_raw)
        dir_names[:] = [
            dir_name
            for dir_name in sorted(dir_names)
            if not _should_ignore_dir(dir_name, current_dir / dir_name, root, rules, skipped_files)
        ]

        for file_name in sorted(file_names):
            path = current_dir / file_name
            relative_path = _relative_path(path, root)
            skip_reason = _skip_reason(path, relative_path, rules)
            if skip_reason:
                skipped_files.append(SkippedFile(relative_path=relative_path, reason=skip_reason))
                continue

            language = detect_language(path)
            files.append(
                ScannedFile(
                    path=path,
                    relative_path=relative_path,
                    language=language,
                    size_bytes=path.stat().st_size,
                )
            )
            if language in SUPPORTED_LANGUAGES:
                language_summary[language] = language_summary.get(language, 0) + 1

    files.sort(key=lambda item: item.relative_path)
    skipped_files.sort(key=lambda item: item.relative_path)
    return ScanResult(
        root_path=root,
        files=files,
        skipped_files=skipped_files,
        language_summary=dict(sorted(language_summary.items())),
    )


def _should_ignore_dir(
    dir_name: str,
    path: Path,
    root: Path,
    rules: ScanRules,
    skipped_files: list[SkippedFile],
) -> bool:
    if dir_name in rules.ignored_dirs:
        return True
    if path.is_symlink():
        skipped_files.append(
            SkippedFile(relative_path=_relative_path(path, root), reason="symlink_directory")
        )
        return True
    return False


def _skip_reason(path: Path, relative_path: str, rules: ScanRules) -> str | None:
    if path.is_symlink():
        return "symlink_file"
    if _matches_ignored_file(path.name, rules.ignored_files):
        return "ignored_file"

    try:
        size = path.stat().st_size
    except OSError:
        return "stat_failed"

    if size > rules.max_file_size_bytes:
        return "file_too_large"
    if _looks_binary(path):
        return "binary_file"
    if _escapes_root_marker(relative_path):
        return "path_escapes_root"
    return None


def _matches_ignored_file(file_name: str, ignored_files: tuple[str, ...]) -> bool:
    lowered = file_name.lower()
    return any(fnmatchcase(lowered, pattern.lower()) for pattern in ignored_files)


def _looks_binary(path: Path) -> bool:
    try:
        with path.open("rb") as file:
            sample = file.read(4096)
    except OSError:
        return True
    return b"\0" in sample


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.name


def _escapes_root_marker(relative_path: str) -> bool:
    return relative_path == ".." or relative_path.startswith("../")
