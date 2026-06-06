from pathlib import Path

import pytest

from app.models import CodeLanguage
from app.services.scanner import ScanRules, ScannerError, detect_language, scan_repository


@pytest.mark.parametrize(
    ("file_name", "language"),
    [
        ("app.py", CodeLanguage.PYTHON.value),
        ("page.ts", CodeLanguage.TYPESCRIPT.value),
        ("page.tsx", CodeLanguage.TYPESCRIPT.value),
        ("widget.js", CodeLanguage.JAVASCRIPT.value),
        ("widget.jsx", CodeLanguage.JAVASCRIPT.value),
        ("README.md", CodeLanguage.UNKNOWN.value),
    ],
)
def test_detect_language_by_extension(file_name: str, language: str) -> None:
    assert detect_language(Path(file_name)) == language


def test_scan_repository_filters_sensitive_binary_and_large_files(tmp_path: Path) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (tmp_path / "app" / "page.tsx").write_text("export function Page() {}\n", encoding="utf-8")
    (tmp_path / "tool.js").write_text("export const value = 1;\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    (tmp_path / "cert.pem").write_text("secret\n", encoding="utf-8")
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01")
    (tmp_path / "large.py").write_text("x" * 101, encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.py").write_text("print('skip')\n", encoding="utf-8")

    result = scan_repository(tmp_path, ScanRules(max_file_size_bytes=100))

    assert [file.relative_path for file in result.files] == [
        "README.md",
        "app/main.py",
        "app/page.tsx",
        "tool.js",
    ]
    assert result.file_count == 4
    assert result.supported_file_count == 3
    assert result.skipped_file_count == 4
    assert result.language_summary == {
        CodeLanguage.JAVASCRIPT.value: 1,
        CodeLanguage.PYTHON.value: 1,
        CodeLanguage.TYPESCRIPT.value: 1,
    }
    assert {file.relative_path: file.reason for file in result.skipped_files} == {
        ".env": "ignored_file",
        "binary.bin": "binary_file",
        "cert.pem": "ignored_file",
        "large.py": "file_too_large",
    }


def test_scan_repository_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(ScannerError):
        scan_repository(tmp_path / "missing")
