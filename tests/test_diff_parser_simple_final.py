"""Comprehensive tests for diff_parser.py module - simplified version."""

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
)


class TestChangedPythonFiles:
    """Test the changed_python_files function."""

    @patch("src.ai_guard.diff_parser.subprocess.run")
    def test_changed_python_files_success(self, mock_run):
        """Test successful extraction of changed Python files."""
        mock_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        result = changed_python_files()

        assert isinstance(result, list)

    @patch("src.ai_guard.diff_parser.subprocess.run")
    def test_changed_python_files_no_changes(self, mock_run):
        """Test when no Python files are changed."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        result = changed_python_files()

        assert isinstance(result, list)
        assert len(result) == 0

    @patch("src.ai_guard.diff_parser.subprocess.run")
    def test_changed_python_files_subprocess_error(self, mock_run):
        """Test handling of subprocess errors."""
        mock_run.side_effect = Exception("Git error")

        result = changed_python_files()

        assert isinstance(result, list)
        assert len(result) == 0


class TestParseDiffOutput:
    """Test the parse_diff_output function."""

    def test_parse_diff_output_success(self):
        """Test successful diff output parsing."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""

        result = parse_diff_output(diff_output)

        assert isinstance(result, list)

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
        file_paths = ["src/test.py", "docs/README.md", "config.json"]

        result = get_file_extensions(file_paths)

        assert isinstance(result, list)
        assert "py" in result
        assert "md" in result
        assert "json" in result

    def test_get_file_extensions_empty_list(self):
        """Test with empty file paths list."""
        result = get_file_extensions([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_file_extensions_none(self):
        """Test with None file paths."""
        result = get_file_extensions(None)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_file_extensions_no_extensions(self):
        """Test with files that have no extensions."""
        file_paths = ["README", "Makefile", "LICENSE"]

        result = get_file_extensions(file_paths)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_file_extensions_backup_files(self):
        """Test filtering out backup files."""
        file_paths = ["src/test.py", "src/test.py~", "src/test.py.bak"]

        result = get_file_extensions(file_paths)

        assert isinstance(result, list)
        assert "py" in result
        assert len(result) == 1


class TestFilterPythonFiles:
    """Test the filter_python_files function."""

    def test_filter_python_files_success(self):
        """Test successful Python file filtering."""
        file_paths = [
            "src/test.py",
            "docs/README.md",
            "tests/test_main.py",
            "config.json",
        ]

        result = filter_python_files(file_paths)

        assert isinstance(result, list)
        assert len(result) == 2
        assert "src/test.py" in result
        assert "tests/test_main.py" in result
        assert "docs/README.md" not in result
        assert "config.json" not in result

    def test_filter_python_files_empty_list(self):
        """Test with empty file paths list."""
        result = filter_python_files([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_filter_python_files_none(self):
        """Test with None file paths."""
        result = filter_python_files(None)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_filter_python_files_no_python_files(self):
        """Test with no Python files."""
        file_paths = ["docs/README.md", "config.json", "Makefile"]

        result = filter_python_files(file_paths)

        assert isinstance(result, list)
        assert len(result) == 0


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

    @patch("src.ai_guard.diff_parser.subprocess.run")
    def test_full_diff_analysis_workflow(self, mock_run):
        """Test full diff analysis workflow."""
        mock_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("Hello World")
"""
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        # Test changed Python files
        changed_files = changed_python_files()
        assert isinstance(changed_files, list)

        # Test diff parsing
        parsed_diff = parse_diff(mock_output)
        assert isinstance(parsed_diff, list)

        # Test file extensions extraction
        file_extensions = get_file_extensions(changed_files)
        assert isinstance(file_extensions, list)

        # Test Python file filtering
        python_files = filter_python_files(changed_files)
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
        diff_output = parse_diff_output(complex_diff)

        assert isinstance(parsed_diff, list)
        assert isinstance(diff_output, list)


if __name__ == "__main__":
    pytest.main([__file__])
