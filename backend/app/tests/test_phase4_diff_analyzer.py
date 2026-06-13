import pytest

from app.services.tools import (
    CHANGE_TYPE_ADDED,
    CHANGE_TYPE_DELETED,
    CHANGE_TYPE_MODIFIED,
    CHANGE_TYPE_RENAMED,
    DIFF_MAX_CHARS,
    HUNK_MAX_LINES,
    DiffAnalyzerError,
    analyze_diff,
)


def test_analyze_diff_parses_modified_file_hunk_lines_and_counts() -> None:
    diff_text = """diff --git a/app/service.py b/app/service.py
index 1111111..2222222 100644
--- a/app/service.py
+++ b/app/service.py
@@ -10,5 +10,6 @@ def save():
 context = load()
-return old_value
+return new_value
+audit_change()
"""

    analysis = analyze_diff(diff_text)

    assert analysis.file_count == 1
    assert analysis.added_line_count == 2
    assert analysis.removed_line_count == 1

    file = analysis.files[0]
    assert file.old_path == "app/service.py"
    assert file.new_path == "app/service.py"
    assert file.change_type == CHANGE_TYPE_MODIFIED
    assert file.binary is False

    hunk = file.hunks[0]
    assert hunk.old_start == 10
    assert hunk.old_count == 5
    assert hunk.new_start == 10
    assert hunk.new_count == 6
    assert hunk.section_header == "def save():"
    assert hunk.context_line_count == 1
    assert [(line.line, line.content) for line in hunk.removed_lines] == [
        (11, "return old_value")
    ]
    assert [(line.line, line.content) for line in hunk.added_lines] == [
        (11, "return new_value"),
        (12, "audit_change()"),
    ]


def test_analyze_diff_parses_added_and_deleted_files() -> None:
    diff_text = """diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+print("hello")
+main()
diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-print("bye")
-main()
"""

    analysis = analyze_diff(diff_text)

    assert analysis.file_count == 2
    assert analysis.added_line_count == 2
    assert analysis.removed_line_count == 2
    assert analysis.files[0].old_path is None
    assert analysis.files[0].new_path == "new.py"
    assert analysis.files[0].change_type == CHANGE_TYPE_ADDED
    assert analysis.files[1].old_path == "old.py"
    assert analysis.files[1].new_path is None
    assert analysis.files[1].change_type == CHANGE_TYPE_DELETED


def test_analyze_diff_parses_renamed_and_binary_files() -> None:
    diff_text = """diff --git a/app/old_name.py b/app/new_name.py
similarity index 88%
rename from app/old_name.py
rename to app/new_name.py
diff --git a/assets/logo.png b/assets/logo.png
index 1111111..2222222 100644
Binary files a/assets/logo.png and b/assets/logo.png differ
"""

    analysis = analyze_diff(diff_text)

    assert analysis.file_count == 2
    assert analysis.files[0].old_path == "app/old_name.py"
    assert analysis.files[0].new_path == "app/new_name.py"
    assert analysis.files[0].change_type == CHANGE_TYPE_RENAMED
    assert analysis.files[1].new_path == "assets/logo.png"
    assert analysis.files[1].binary is True
    assert analysis.files[1].hunks == []


def test_analyze_diff_to_dict_matches_tool_output_shape() -> None:
    analysis = analyze_diff(
        """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-old()
+new()
"""
    )

    payload = analysis.to_dict()

    assert payload["file_count"] == 1
    assert payload["added_line_count"] == 1
    assert payload["removed_line_count"] == 1
    assert payload["files"][0]["hunks"][0]["added_lines"] == [
        {"line": 1, "content": "new()"}
    ]


def test_analyze_diff_rejects_empty_or_unsupported_diff() -> None:
    with pytest.raises(DiffAnalyzerError, match="empty"):
        analyze_diff("")

    with pytest.raises(DiffAnalyzerError, match="not supported"):
        analyze_diff("not a unified diff")


def test_analyze_diff_rejects_diff_and_hunk_size_limits() -> None:
    with pytest.raises(DiffAnalyzerError, match=str(DIFF_MAX_CHARS)):
        analyze_diff("x" * (DIFF_MAX_CHARS + 1))

    hunk_body = "\n".join("+line" for _ in range(HUNK_MAX_LINES + 1))
    diff_text = "\n".join(
        [
            "diff --git a/app.py b/app.py",
            "--- a/app.py",
            "+++ b/app.py",
            f"@@ -0,0 +1,{HUNK_MAX_LINES + 1} @@",
            hunk_body,
        ]
    )
    with pytest.raises(DiffAnalyzerError, match=str(HUNK_MAX_LINES)):
        analyze_diff(diff_text)
