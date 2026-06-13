from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from app.core.config import Settings

STATIC_CHECK_MAX_FILES: Final = 50
STATIC_CHECK_DEFAULT_ALLOWED_CHECKERS: Final = ("python_ast_parse",)

STATIC_CHECK_STATUS_COMPLETED: Final = "completed"
STATIC_CHECK_STATUS_DENIED: Final = "denied"
STATIC_CHECK_STATUS_DISABLED: Final = "disabled"


class StaticCheckError(ValueError):
    """Raised when static check input violates the placeholder tool contract."""


@dataclass(frozen=True)
class StaticCheckResult:
    checker: str
    file_paths: list[str]
    permission_decision: str
    status: str
    executed: bool
    output_summary: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "checker": self.checker,
            "file_paths": self.file_paths,
            "permission_decision": self.permission_decision,
            "status": self.status,
            "executed": self.executed,
            "output_summary": self.output_summary,
            "warnings": self.warnings,
        }


def run_safe_static_check(
    *,
    checker: str,
    file_paths: list[str],
    settings: Settings,
) -> StaticCheckResult:
    normalized_checker = checker.strip()
    if not normalized_checker:
        raise StaticCheckError("checker is required.")
    normalized_paths = _validate_file_paths(file_paths)

    if not settings.safe_static_check_enabled:
        return StaticCheckResult(
            checker=normalized_checker,
            file_paths=normalized_paths,
            permission_decision="disabled",
            status=STATIC_CHECK_STATUS_DISABLED,
            executed=False,
            output_summary="run_safe_static_check is disabled by configuration.",
            warnings=["No static check was executed."],
        )

    allowed_checkers = set(
        settings.safe_static_check_allowed_checkers or STATIC_CHECK_DEFAULT_ALLOWED_CHECKERS
    )
    if normalized_checker not in allowed_checkers:
        return StaticCheckResult(
            checker=normalized_checker,
            file_paths=normalized_paths,
            permission_decision="deny",
            status=STATIC_CHECK_STATUS_DENIED,
            executed=False,
            output_summary="Checker is not in the allowed checker whitelist.",
            warnings=["No static check was executed."],
        )

    return StaticCheckResult(
        checker=normalized_checker,
        file_paths=normalized_paths,
        permission_decision="allow",
        status=STATIC_CHECK_STATUS_COMPLETED,
        executed=False,
        output_summary="Checker is allowed, but Phase 4 implements a no-execution placeholder only.",
        warnings=["Placeholder only: no shell command or checker process was executed."],
    )


def _validate_file_paths(file_paths: list[str]) -> list[str]:
    if not file_paths:
        raise StaticCheckError("file_paths is required.")
    if len(file_paths) > STATIC_CHECK_MAX_FILES:
        raise StaticCheckError(f"file_paths cannot contain more than {STATIC_CHECK_MAX_FILES} items.")

    normalized_paths: list[str] = []
    seen: set[str] = set()
    for raw_path in file_paths:
        normalized = raw_path.strip().replace("\\", "/")
        path = Path(normalized)
        if not normalized:
            raise StaticCheckError("file_paths cannot contain empty paths.")
        if path.is_absolute():
            raise StaticCheckError("Absolute file paths are not allowed.")
        if any(part in {"", ".", ".."} for part in path.parts):
            raise StaticCheckError("Path traversal is not allowed.")
        if normalized not in seen:
            normalized_paths.append(normalized)
            seen.add(normalized)
    return normalized_paths
