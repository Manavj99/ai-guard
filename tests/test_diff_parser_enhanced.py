"""Enhanced tests for diff_parser module to improve coverage."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch
from src.ai_guard.diff_parser import (
    get_file_extensions,
    filter_python_files,
    parse_diff_output,
    changed_python_files,
    _git_ls_files,
    _git_changed_files,
    parse_github_event,
    _get_base_head_from_event,
    DiffParser,
    parse_diff,
    get_changed_files
)


class TestGetFileExtensions:
    """Test get_file_extensions function."""

    def test_get_file_extensions_none_input(self):
        """Test with None input."""
        result = get_file_extensions(None)
        assert result == []

    def test_get_file_extensions_empty_list(self):
        """Test with empty list."""
        result = get_file_extensions([])
        assert result == []

    def test_get_file_extensions_single_file(self):
        """Test with single file."""
        result = get_file_extensions(["test.py"])
        assert result == ["py"]

    def test_get_file_extensions_multiple_files(self):
        """Test with multiple files."""
        files = ["test.py", "script.js", "data.json", "README.md"]
        result = get_file_extensions(files)
        assert result == ["js", "json", "md", "py"]

    def test_get_file_extensions_no_extension(self):
        """Test with files without extensions."""
        files = ["README", "Makefile", "LICENSE"]
        result = get_file_extensions(files)
        assert result == []

    def test_get_file_extensions_backup_files(self):
        """Test with backup/temp files."""
        files = ["test.py", "test.py~", "test.py.bak", "test.py.tmp", "test.py.temp"]
        result = get_file_extensions(files)
        assert result == ["py"]

    def test_get_file_extensions_case_insensitive(self):
        """Test case insensitive extensions."""
        files = ["test.PY", "script.JS", "data.JSON"]
        result = get_file_extensions(files)
        assert result == ["js", "json", "py"]

    def test_get_file_extensions_duplicate_extensions(self):
        """Test with duplicate extensions."""
        files = ["test1.py", "test2.py", "script.js", "data.js"]
        result = get_file_extensions(files)
        assert result == ["js", "py"]


class TestFilterPythonFiles:
    """Test filter_python_files function."""

    def test_filter_python_files_none_input(self):
        """Test with None input."""
        result = filter_python_files(None)
        assert result == []

    def test_filter_python_files_empty_list(self):
        """Test with empty list."""
        result = filter_python_files([])
        assert result == []

    def test_filter_python_files_only_python(self):
        """Test with only Python files."""
        files = ["test.py", "script.py", "module.py"]
        result = filter_python_files(files)
        assert result == files

    def test_filter_python_files_mixed_files(self):
        """Test with mixed file types."""
        files = ["test.py", "script.js", "data.json", "module.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "module.py"]

    def test_filter_python_files_no_python(self):
        """Test with no Python files."""
        files = ["script.js", "data.json", "README.md"]
        result = filter_python_files(files)
        assert result == []

    def test_filter_python_files_case_sensitive(self):
        """Test case sensitivity."""
        files = ["test.py", "script.PY", "module.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "module.py"]


class TestParseDiffOutput:
    """Test parse_diff_output function."""

    def test_parse_diff_output_none_input(self):
        """Test with None input."""
        result = parse_diff_output(None)
        assert result == []

    def test_parse_diff_output_empty_string(self):
        """Test with empty string."""
        result = parse_diff_output("")
        assert result == []

    def test_parse_diff_output_basic_diff(self):
        """Test with basic diff."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
"""
        result = parse_diff_output(diff)
        assert "test.py" in result

    def test_parse_diff_output_multiple_files(self):
        """Test with multiple files."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")

diff --git a/script.js b/script.js
index 1234567..abcdefg 100644
--- a/script.js
+++ b/script.js
@@ -1,3 +1,4 @@
 function hello() {
     console.log("Hello");
+    console.log("World");
}
"""
        result = parse_diff_output(diff)
        assert "test.py" in result
        assert "script.js" in result

    def test_parse_diff_output_no_changes(self):
        """Test with no changes."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
"""
        result = parse_diff_output(diff)
        assert "test.py" in result

    def test_parse_diff_output_whitespace_lines(self):
        """Test with whitespace lines."""
        diff = """
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")

"""
        result = parse_diff_output(diff)
        assert "test.py" in result
