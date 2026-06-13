import pytest

from app.core.config import Settings
from app.services.tools import (
    STATIC_CHECK_MAX_FILES,
    STATIC_CHECK_STATUS_COMPLETED,
    STATIC_CHECK_STATUS_DENIED,
    STATIC_CHECK_STATUS_DISABLED,
    StaticCheckError,
    run_safe_static_check,
)


def test_run_safe_static_check_returns_disabled_by_default() -> None:
    result = run_safe_static_check(
        checker="python_ast_parse",
        file_paths=["backend/app/main.py"],
        settings=Settings(),
    )

    assert result.permission_decision == "disabled"
    assert result.status == STATIC_CHECK_STATUS_DISABLED
    assert result.executed is False
    assert result.warnings == ["No static check was executed."]
    assert result.to_dict()["status"] == STATIC_CHECK_STATUS_DISABLED


def test_run_safe_static_check_allows_whitelisted_checker_without_execution() -> None:
    settings = Settings(
        safe_static_check_enabled=True,
        safe_static_check_allowed_checkers=["python_ast_parse"],
    )

    result = run_safe_static_check(
        checker="python_ast_parse",
        file_paths=["backend/app/main.py", "backend/app/main.py"],
        settings=settings,
    )

    assert result.permission_decision == "allow"
    assert result.status == STATIC_CHECK_STATUS_COMPLETED
    assert result.executed is False
    assert result.file_paths == ["backend/app/main.py"]
    assert "no shell command" in result.warnings[0]


def test_run_safe_static_check_denies_non_whitelisted_checker_when_enabled() -> None:
    settings = Settings(
        safe_static_check_enabled=True,
        safe_static_check_allowed_checkers=["python_ast_parse"],
    )

    result = run_safe_static_check(
        checker="npm_test",
        file_paths=["frontend/app/page.tsx"],
        settings=settings,
    )

    assert result.permission_decision == "deny"
    assert result.status == STATIC_CHECK_STATUS_DENIED
    assert result.executed is False
    assert "whitelist" in result.output_summary


def test_run_safe_static_check_validates_input_paths() -> None:
    settings = Settings(safe_static_check_enabled=True)

    with pytest.raises(StaticCheckError, match="checker"):
        run_safe_static_check(checker=" ", file_paths=["app.py"], settings=settings)

    with pytest.raises(StaticCheckError, match="file_paths"):
        run_safe_static_check(checker="python_ast_parse", file_paths=[], settings=settings)

    with pytest.raises(StaticCheckError, match="Absolute"):
        run_safe_static_check(
            checker="python_ast_parse",
            file_paths=["C:/repo/app.py"],
            settings=settings,
        )

    with pytest.raises(StaticCheckError, match="traversal"):
        run_safe_static_check(
            checker="python_ast_parse",
            file_paths=["../app.py"],
            settings=settings,
        )

    with pytest.raises(StaticCheckError, match=str(STATIC_CHECK_MAX_FILES)):
        run_safe_static_check(
            checker="python_ast_parse",
            file_paths=[f"file_{index}.py" for index in range(STATIC_CHECK_MAX_FILES + 1)],
            settings=settings,
        )
