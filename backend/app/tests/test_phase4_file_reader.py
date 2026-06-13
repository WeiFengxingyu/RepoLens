from pathlib import Path

import pytest

from app.services.tools import (
    FILE_SLICE_MAX_CHARS,
    FILE_SLICE_MAX_LINES,
    FileSliceError,
    read_file_slice,
)


def test_read_file_slice_reads_repository_relative_line_range(tmp_path: Path) -> None:
    file_path = tmp_path / "backend" / "app.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("line 1\nline 2\nline 3\nline 4\n", encoding="utf-8")

    result = read_file_slice(
        repository_root=tmp_path,
        file_path="backend/app.py",
        start_line=2,
        end_line=3,
    )

    assert result.file_path == "backend/app.py"
    assert result.start_line == 2
    assert result.end_line == 3
    assert result.content == "line 2\nline 3"
    assert result.truncated is False
    assert result.to_dict()["content"] == "line 2\nline 3"


def test_read_file_slice_truncates_line_count(tmp_path: Path) -> None:
    file_path = tmp_path / "app.py"
    file_path.write_text(
        "\n".join(f"line {index}" for index in range(1, FILE_SLICE_MAX_LINES + 11)),
        encoding="utf-8",
    )

    result = read_file_slice(
        repository_root=tmp_path,
        file_path="app.py",
        start_line=1,
        end_line=FILE_SLICE_MAX_LINES + 10,
    )

    assert result.end_line == FILE_SLICE_MAX_LINES
    assert len(result.content.splitlines()) == FILE_SLICE_MAX_LINES
    assert result.truncated is True


def test_read_file_slice_truncates_character_count(tmp_path: Path) -> None:
    file_path = tmp_path / "app.py"
    file_path.write_text("x" * (FILE_SLICE_MAX_CHARS + 10), encoding="utf-8")

    result = read_file_slice(
        repository_root=tmp_path,
        file_path="app.py",
        start_line=1,
        end_line=1,
    )

    assert len(result.content) == FILE_SLICE_MAX_CHARS
    assert result.truncated is True


def test_read_file_slice_rejects_absolute_path_and_traversal(tmp_path: Path) -> None:
    outside_file = tmp_path.parent / "outside.py"
    outside_file.write_text("outside", encoding="utf-8")

    with pytest.raises(FileSliceError, match="Absolute"):
        read_file_slice(
            repository_root=tmp_path,
            file_path=str(outside_file),
            start_line=1,
            end_line=1,
        )

    with pytest.raises(FileSliceError, match="traversal"):
        read_file_slice(
            repository_root=tmp_path,
            file_path="../outside.py",
            start_line=1,
            end_line=1,
        )


def test_read_file_slice_rejects_sensitive_files_and_blocked_dirs(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=secret", encoding="utf-8")
    key_file = tmp_path / "id_rsa"
    key_file.write_text("private key", encoding="utf-8")
    blocked_file = tmp_path / "node_modules" / "pkg" / "index.js"
    blocked_file.parent.mkdir(parents=True)
    blocked_file.write_text("module.exports = {}", encoding="utf-8")

    for file_path in [".env", "id_rsa", "node_modules/pkg/index.js"]:
        with pytest.raises(FileSliceError):
            read_file_slice(
                repository_root=tmp_path,
                file_path=file_path,
                start_line=1,
                end_line=1,
            )


def test_read_file_slice_rejects_missing_binary_and_invalid_ranges(tmp_path: Path) -> None:
    binary_file = tmp_path / "data.bin"
    binary_file.write_bytes(b"abc\x00def")
    text_file = tmp_path / "app.py"
    text_file.write_text("line 1\n", encoding="utf-8")

    with pytest.raises(FileSliceError, match="does not exist"):
        read_file_slice(
            repository_root=tmp_path,
            file_path="missing.py",
            start_line=1,
            end_line=1,
        )

    with pytest.raises(FileSliceError, match="Binary"):
        read_file_slice(
            repository_root=tmp_path,
            file_path="data.bin",
            start_line=1,
            end_line=1,
        )

    with pytest.raises(FileSliceError, match="start_line"):
        read_file_slice(
            repository_root=tmp_path,
            file_path="app.py",
            start_line=0,
            end_line=1,
        )

    with pytest.raises(FileSliceError, match="end_line"):
        read_file_slice(
            repository_root=tmp_path,
            file_path="app.py",
            start_line=2,
            end_line=1,
        )

    with pytest.raises(FileSliceError, match="exceeds"):
        read_file_slice(
            repository_root=tmp_path,
            file_path="app.py",
            start_line=2,
            end_line=2,
        )
