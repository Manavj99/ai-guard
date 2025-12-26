"""Simple tests for diff_parser.py module."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.ai_guard.diff_parser import (
    changed_python_files,
    get_file_extensions,
    filter_python_files,
    parse_diff_output,
    parse_github_event,
    get_changed_files,
    parse_diff,
)


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    def test_changed_python_files_no_event(self):
        """Test changed_python_files with no event."""
        result = changed_python_files()
        assert isinstance(result, list)

    def test_changed_python_files_with_event(self):
        """Test changed_python_files with event path."""
        result = changed_python_files("test_event.json")
        assert isinstance(result, list)


class TestGetFileExtensions:
    """Test get_file_extensions function."""

    def test_get_file_extensions(self):
        """Test getting file extensions from file paths."""
        file_paths = ["file1.py", "file2.txt", "file3.js", "file4.py"]
        extensions = get_file_extensions(file_paths)

        assert "py" in extensions
        assert "txt" in extensions
        assert "js" in extensions
        assert len(extensions) == 3

    def test_get_file_extensions_none(self):
        """Test getting file extensions with None input."""
        extensions = get_file_extensions(None)
        assert extensions == []

    def test_get_file_extensions_empty(self):
        """Test getting file extensions with empty list."""
        extensions = get_file_extensions([])
        assert extensions == []

    def test_get_file_extensions_no_extensions(self):
        """Test getting file extensions with files that have no extensions."""
        file_paths = ["file1", "file2", "file3"]
        extensions = get_file_extensions(file_paths)
        assert extensions == []


class TestFilterPythonFiles:
    """Test filter_python_files function."""

    def test_filter_python_files(self):
        """Test filtering Python files from list."""
        files = ["file1.py", "file2.txt", "file3.py", "file4.js", "file5.py"]

        python_files = filter_python_files(files)

        assert python_files == ["file1.py", "file3.py", "file5.py"]

    def test_filter_python_files_empty(self):
        """Test filtering from empty list."""
        python_files = filter_python_files([])
        assert python_files == []

    def test_filter_python_files_none(self):
        """Test filtering from None input."""
        python_files = filter_python_files(None)
        assert python_files == []

    def test_filter_python_files_no_python(self):
        """Test filtering when no Python files."""
        files = ["file1.txt", "file2.js", "file3.md"]

        python_files = filter_python_files(files)

        assert python_files == []


class TestParseDiffOutput:
    """Test parse_diff_output function."""

    def test_parse_diff_output(self):
        """Test parsing diff output."""
        diff_output = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""
        files = parse_diff_output(diff_output)

        assert "file1.py" in files

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        files = parse_diff_output("")
        assert files == []

    def test_parse_diff_output_none(self):
        """Test parsing None diff output."""
        files = parse_diff_output(None)
        assert files == []

    def test_parse_diff_output_with_whitespace(self):
        """Test parsing diff output with whitespace."""
        diff_output = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""
        files = parse_diff_output(diff_output)

        assert "file1.py" in files


class TestParseGithubEvent:
    """Test parse_github_event function."""

    def test_parse_github_event_invalid_path(self):
        """Test parsing GitHub event with invalid path."""
        result = parse_github_event("nonexistent.json")
        assert result == {}

    def test_parse_github_event_valid_json(self):
        """Test parsing GitHub event with valid JSON."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(
                '{"pull_request": {"head": {"sha": "abc123"}, "base": {"sha": "def456"}}}'
            )
            temp_file = f.name

        try:
            result = parse_github_event(temp_file)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_file)


class TestGetChangedFiles:
    """Test get_changed_files function."""

    def test_get_changed_files_no_event(self):
        """Test get_changed_files with no event."""
        result = get_changed_files()
        assert isinstance(result, list)

    def test_get_changed_files_with_event(self):
        """Test get_changed_files with event path."""
        result = get_changed_files("test_event.json")
        assert isinstance(result, list)


class TestParseDiff:
    """Test parse_diff function."""

    def test_parse_diff(self):
        """Test parsing diff content."""
        diff_content = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""
        files = parse_diff(diff_content)

        assert "file1.py" in files

    def test_parse_diff_empty(self):
        """Test parsing empty diff content."""
        files = parse_diff("")
        assert files == []

    def test_parse_diff_none(self):
        """Test parsing None diff content."""
        files = parse_diff(None)
        assert files == []


if __name__ == "__main__":
    pytest.main([__file__])
