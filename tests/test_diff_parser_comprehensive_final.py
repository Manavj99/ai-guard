"""Comprehensive tests for diff_parser.py module."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ai_guard.diff_parser import (
    changed_python_files,
    parse_diff_output,
    get_file_extensions,
    filter_python_files,
    parse_diff,
    DiffParser,
    extract_file_changes,
    get_added_lines,
    get_removed_lines,
    get_modified_files,
    FileChange,
    LineChange,
    get_changed_files,
)


class TestChangedPythonFiles:
    """Test the changed_python_files function."""

    def test_changed_python_files_success(self):
        """Test successful extraction of changed Python files."""
        result = changed_python_files()

        assert isinstance(result, list)

    def test_changed_python_files_no_changes(self):
        """Test when no Python files are changed."""
        result = changed_python_files([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_changed_python_files_with_list(self):
        """Test filtering out non-Python files."""
        files = ["src/test.py", "README.md", "src/utils.py"]
        result = changed_python_files(files)

        assert isinstance(result, list)
        assert "src/test.py" in result
        assert "src/utils.py" in result
        assert "README.md" not in result


class TestParseDiff:
    """Test the parse_diff function."""

    def test_parse_diff_success(self):
        """Test successful diff parsing."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""

        result = parse_diff(diff_content)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_diff_empty(self):
        """Test parsing empty diff."""
        result = parse_diff("")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_diff_invalid_format(self):
        """Test parsing invalid diff format."""
        invalid_diff = "This is not a valid diff"

        result = parse_diff(invalid_diff)

        assert isinstance(result, list)
        assert len(result) == 0


class TestParseDiffOutput:
    """Test the parse_diff_output function."""

    def test_parse_diff_output_success(self):
        """Test successful diff output parsing."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""

        result = parse_diff_output(diff_content)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        result = parse_diff_output("")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_diff_output_none(self):
        """Test parsing None diff output."""
        result = parse_diff_output(None)

        assert isinstance(result, list)
        assert len(result) == 0


class TestGetFileExtensions:
    """Test the get_file_extensions function."""

    def test_get_file_extensions_success(self):
        """Test successful file extension extraction."""
        files = ["src/test.py", "src/utils.js", "README.md"]
        result = get_file_extensions(files)

        assert isinstance(result, list)
        assert "py" in result
        assert "js" in result
        assert "md" in result

    def test_get_file_extensions_empty(self):
        """Test with empty file list."""
        result = get_file_extensions([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_file_extensions_none(self):
        """Test with None input."""
        result = get_file_extensions(None)

        assert isinstance(result, list)
        assert len(result) == 0


class TestFilterPythonFiles:
    """Test the filter_python_files function."""

    def test_filter_python_files_success(self):
        """Test successful Python file filtering."""
        files = ["src/test.py", "README.md", "src/utils.py", "config.json"]
        result = filter_python_files(files)

        assert isinstance(result, list)
        assert "src/test.py" in result
        assert "src/utils.py" in result
        assert "README.md" not in result
        assert "config.json" not in result

    def test_filter_python_files_empty(self):
        """Test with empty file list."""
        result = filter_python_files([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_filter_python_files_none(self):
        """Test with None input."""
        result = filter_python_files(None)

        assert isinstance(result, list)
        assert len(result) == 0


class TestDiffParser:
    """Test the DiffParser class."""

    def test_init(self):
        """Test DiffParser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_parse_changed_files(self):
        """Test parsing changed files."""
        parser = DiffParser()
        result = parser.parse_changed_files()

        assert isinstance(result, list)

    def test_parse_changed_files_with_event(self):
        """Test parsing changed files with event."""
        parser = DiffParser()
        result = parser.parse_changed_files("event.json")

        assert isinstance(result, list)

    def test_parse_github_event(self):
        """Test parsing GitHub event."""
        parser = DiffParser()
        result = parser.parse_github_event("event.json")

        assert isinstance(result, dict)

    def test_get_file_extensions(self):
        """Test getting file extensions."""
        parser = DiffParser()
        files = ["test.py", "test.js"]
        result = parser.get_file_extensions(files)

        assert isinstance(result, list)
        assert "py" in result
        assert "js" in result

    def test_filter_python_files(self):
        """Test filtering Python files."""
        parser = DiffParser()
        files = ["test.py", "test.js", "README.md"]
        result = parser.filter_python_files(files)

        assert isinstance(result, list)
        assert "test.py" in result
        assert "test.js" not in result
        assert "README.md" not in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_parse_diff_with_binary_files(self):
        """Test parsing diff with binary files."""
        diff_content = """diff --git a/binary.bin b/binary.bin
index 1234567..abcdefg 100644
Binary files a/binary.bin and b/binary.bin differ
"""

        result = parse_diff(diff_content)

        assert isinstance(result, list)

    def test_parse_diff_with_renamed_files(self):
        """Test parsing diff with renamed files."""
        diff_content = """diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
index 1234567..abcdefg 100644
--- a/old_name.py
+++ b/new_name.py
@@ -1,1 +1,1 @@
-print("Old")
+print("New")
"""

        result = parse_diff(diff_content)

        assert isinstance(result, list)

    def test_parse_diff_with_deleted_files(self):
        """Test parsing diff with deleted files."""
        diff_content = """diff --git a/deleted.py b/deleted.py
deleted file mode 100644
index 1234567..0000000
--- a/deleted.py
+++ /dev/null
@@ -1,1 +0,0 @@
-print("This file was deleted")
"""

        result = parse_diff(diff_content)

        assert isinstance(result, list)

    def test_parse_diff_with_added_files(self):
        """Test parsing diff with added files."""
        diff_content = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,1 @@
+print("This is a new file")
"""

        result = parse_diff(diff_content)

        assert isinstance(result, list)


class TestIntegration:
    """Test integration scenarios."""

    def test_full_diff_analysis_workflow(self):
        """Test full diff analysis workflow."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("Hello World")
"""

        # Test changed Python files
        changed_files = changed_python_files()
        assert isinstance(changed_files, list)

        # Test diff parsing
        parsed_diff = parse_diff(diff_output)
        assert isinstance(parsed_diff, list)

        # Test diff output parsing
        file_changes = parse_diff_output(diff_output)
        assert isinstance(file_changes, list)

        # Test file extensions
        extensions = get_file_extensions(["test.py", "test.js"])
        assert isinstance(extensions, list)

        # Test Python file filtering
        python_files = filter_python_files(["test.py", "test.js", "README.md"])
        assert isinstance(python_files, list)

    def test_complex_diff_scenario(self):
        """Test complex diff scenario with multiple changes."""
        complex_diff = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,6 @@
 def main():
-    print("Hello")
+    print("Hello World")
     return True
 
+def new_function():
+    return "New function"
+
diff --git a/src/utils.py b/src/utils.py
index 1234567..abcdefg 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,3 +1,4 @@
 def helper():
-    return "help"
+    return "help me"
+
+def another_helper():
+    return "more help"
"""

        # Test all functions with complex diff
        parsed_diff = parse_diff(complex_diff)
        file_changes = parse_diff_output(complex_diff)
        extensions = get_file_extensions(["main.py", "utils.py"])
        python_files = filter_python_files(["main.py", "utils.py", "README.md"])

        assert isinstance(parsed_diff, list)
        assert isinstance(file_changes, list)
        assert isinstance(extensions, list)
        assert isinstance(python_files, list)
        assert len(python_files) == 2


class TestExtractFileChanges:
    """Test the extract_file_changes function."""

    def test_extract_file_changes_success(self):
        """Test successful file change extraction."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""

        result = extract_file_changes(diff_content)

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["file_path"] == "src/test.py"
        assert result[0]["change_type"] == "modified"

    def test_extract_file_changes_multiple_files(self):
        """Test extracting changes from multiple files."""
        diff_content = """diff --git a/src/test1.py b/src/test1.py
index 1234567..abcdefg 100644
--- a/src/test1.py
+++ b/src/test1.py
@@ -1,1 +1,1 @@
-print("Hello")
+print("Hello World")

diff --git a/src/test2.py b/src/test2.py
index 1234567..abcdefg 100644
--- a/src/test2.py
+++ b/src/test2.py
@@ -1,1 +1,1 @@
-print("Goodbye")
+print("Goodbye World")
"""

        result = extract_file_changes(diff_content)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_extract_file_changes_empty(self):
        """Test with empty diff content."""
        result = extract_file_changes("")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_file_changes_none(self):
        """Test with None diff content."""
        result = extract_file_changes(None)
        assert isinstance(result, list)
        assert len(result) == 0


class TestGetAddedLines:
    """Test the get_added_lines function."""

    def test_get_added_lines_success(self):
        """Test successful extraction of added lines."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("New line")
"""

        result = get_added_lines(diff_content)

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["change_type"] == "added"

    def test_get_added_lines_no_additions(self):
        """Test when no lines are added."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""

        result = get_added_lines(diff_content)

        assert isinstance(result, list)
        # This diff actually has a line change, so we expect 1 added line
        assert len(result) == 1
        assert result[0]["change_type"] == "added"

    def test_get_added_lines_empty(self):
        """Test with empty diff content."""
        result = get_added_lines("")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_added_lines_truly_no_additions(self):
        """Test when truly no lines are added (only removals)."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,2 @@
 def hello():
-    print("Hello")
     print("Goodbye")
"""

        result = get_added_lines(diff_content)

        assert isinstance(result, list)
        assert len(result) == 0


class TestGetRemovedLines:
    """Test the get_removed_lines function."""

    def test_get_removed_lines_success(self):
        """Test successful extraction of removed lines."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,2 @@
 def hello():
-    print("Hello")
     print("Hello World")
"""

        result = get_removed_lines(diff_content)

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["change_type"] == "removed"

    def test_get_removed_lines_no_removals(self):
        """Test when no lines are removed."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("New line")
"""

        result = get_removed_lines(diff_content)

        assert isinstance(result, list)
        assert len(result) == 0


class TestGetModifiedFiles:
    """Test the get_modified_files function."""

    def test_get_modified_files_success(self):
        """Test successful extraction of modified files."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""

        result = get_modified_files(diff_content)

        assert isinstance(result, list)
        assert "src/test.py" in result

    def test_get_modified_files_multiple_files(self):
        """Test extraction of multiple modified files."""
        diff_content = """diff --git a/src/test1.py b/src/test1.py
index 1234567..abcdefg 100644
--- a/src/test1.py
+++ b/src/test1.py
@@ -1,1 +1,1 @@
-print("Hello")
+print("Hello World")

diff --git a/src/test2.py b/src/test2.py
index 1234567..abcdefg 100644
--- a/src/test2.py
+++ b/src/test2.py
@@ -1,1 +1,1 @@
-print("Goodbye")
+print("Goodbye World")
"""

        result = get_modified_files(diff_content)

        assert isinstance(result, list)
        assert len(result) == 2
        assert "src/test1.py" in result
        assert "src/test2.py" in result


class TestFileChange:
    """Test the FileChange class."""

    def test_file_change_creation(self):
        """Test creating a FileChange."""
        change = FileChange(
            file_path="src/test.py",
            change_type="modified",
            added_lines=5,
            removed_lines=3,
        )

        assert change.file_path == "src/test.py"
        assert change.change_type == "modified"
        assert change.added_lines == 5
        assert change.removed_lines == 3

    def test_file_change_to_dict(self):
        """Test converting FileChange to dictionary."""
        change = FileChange(
            file_path="src/test.py",
            change_type="modified",
            added_lines=5,
            removed_lines=3,
        )

        change_dict = change.to_dict()

        assert isinstance(change_dict, dict)
        assert change_dict["file_path"] == "src/test.py"
        assert change_dict["change_type"] == "modified"
        assert change_dict["added_lines"] == 5
        assert change_dict["removed_lines"] == 3


class TestLineChange:
    """Test the LineChange class."""

    def test_line_change_creation(self):
        """Test creating a LineChange."""
        change = LineChange(
            line_number=10,
            change_type="added",
            content="print('Hello World')",
            file_path="src/test.py",
        )

        assert change.line_number == 10
        assert change.change_type == "added"
        assert change.content == "print('Hello World')"
        assert change.file_path == "src/test.py"

    def test_line_change_to_dict(self):
        """Test converting LineChange to dictionary."""
        change = LineChange(
            line_number=10,
            change_type="added",
            content="print('Hello World')",
            file_path="src/test.py",
        )

        change_dict = change.to_dict()

        assert isinstance(change_dict, dict)
        assert change_dict["line_number"] == 10
        assert change_dict["change_type"] == "added"
        assert change_dict["content"] == "print('Hello World')"
        assert change_dict["file_path"] == "src/test.py"


class TestGetChangedFiles:
    """Test the get_changed_files function."""

    def test_get_changed_files_success(self):
        """Test successful file change retrieval."""
        result = get_changed_files()

        assert isinstance(result, list)

    def test_get_changed_files_with_event(self):
        """Test with event path."""
        result = get_changed_files("event.json")

        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__])
