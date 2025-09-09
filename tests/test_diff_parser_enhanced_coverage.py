"""Enhanced tests for diff_parser module to significantly improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open

from src.ai_guard.diff_parser import (
    changed_python_files,
    parse_diff_output,
    filter_python_files,
    get_file_extensions,
    parse_diff
)


class TestFilterPythonFiles:
    """Test filter_python_files function."""

    def test_filter_python_files_py_extension(self):
        """Test filter_python_files with .py extension."""
        files = ["test.py", "src/module.py", "path/to/file.py"]
        result = filter_python_files(files)
        assert result == files

    def test_filter_python_files_mixed_extensions(self):
        """Test filter_python_files with mixed extensions."""
        files = ["test.py", "README.md", "script.js", "module.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "module.py"]

    def test_filter_python_files_no_python(self):
        """Test filter_python_files with no Python files."""
        files = ["README.md", "script.js", "data.json"]
        result = filter_python_files(files)
        assert result == []

    def test_filter_python_files_empty_list(self):
        """Test filter_python_files with empty list."""
        result = filter_python_files([])
        assert result == []

    def test_filter_python_files_none(self):
        """Test filter_python_files with None."""
        result = filter_python_files(None)
        assert result == []


class TestParseDiff:
    """Test parse_diff function."""

    def test_parse_diff_unified_diff(self):
        """Test parse_diff with unified diff format."""
        diff_content = """--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        result = parse_diff(diff_content)
        assert "src/test.py" in result

    def test_parse_diff_git_diff(self):
        """Test parse_diff with git diff format."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        result = parse_diff(diff_content)
        assert "src/test.py" in result

    def test_parse_diff_multiple_files(self):
        """Test parse_diff with multiple files."""
        diff_content = """--- a/src/test1.py
+++ b/src/test1.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")

--- a/src/test2.py
+++ b/src/test2.py
@@ -1,3 +1,3 @@
 def world():
-    print("old")
+    print("new")
"""
        result = parse_diff(diff_content)
        assert "src/test1.py" in result
        assert "src/test2.py" in result

    def test_parse_diff_no_matches(self):
        """Test parse_diff with no file path matches."""
        diff_content = "some random text without file paths"
        result = parse_diff(diff_content)
        assert result == []

    def test_parse_diff_empty(self):
        """Test parse_diff with empty content."""
        result = parse_diff("")
        assert result == []

    def test_parse_diff_none(self):
        """Test parse_diff with None content."""
        result = parse_diff(None)
        assert result == []


class TestGetFileExtensions:
    """Test get_file_extensions function."""

    def test_get_file_extensions_python_files(self):
        """Test get_file_extensions with Python files."""
        files = ["test.py", "module.py", "script.py"]
        result = get_file_extensions(files)
        assert "py" in result

    def test_get_file_extensions_mixed_files(self):
        """Test get_file_extensions with mixed file types."""
        files = ["test.py", "README.md", "script.js", "data.json"]
        result = get_file_extensions(files)
        assert "py" in result
        assert "md" in result
        assert "js" in result
        assert "json" in result

    def test_get_file_extensions_no_extensions(self):
        """Test get_file_extensions with files without extensions."""
        files = ["README", "LICENSE", "Makefile"]
        result = get_file_extensions(files)
        assert result == []

    def test_get_file_extensions_empty_list(self):
        """Test get_file_extensions with empty list."""
        result = get_file_extensions([])
        assert result == []

    def test_get_file_extensions_none(self):
        """Test get_file_extensions with None."""
        result = get_file_extensions(None)
        assert result == []


class TestParseDiffOutput:
    """Test parse_diff_output function."""

    def test_parse_diff_output_unified_diff(self):
        """Test parse_diff_output with unified diff format."""
        diff_content = """--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        result = parse_diff_output(diff_content)
        assert "src/test.py" in result

    def test_parse_diff_output_git_diff(self):
        """Test parse_diff_output with git diff format."""
        diff_content = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        result = parse_diff_output(diff_content)
        assert "src/test.py" in result

    def test_parse_diff_output_multiple_files(self):
        """Test parse_diff_output with multiple files."""
        diff_content = """--- a/src/test1.py
+++ b/src/test1.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")

--- a/src/test2.py
+++ b/src/test2.py
@@ -1,3 +1,3 @@
 def world():
-    print("old")
+    print("new")
"""
        result = parse_diff_output(diff_content)
        assert "src/test1.py" in result
        assert "src/test2.py" in result

    def test_parse_diff_output_no_matches(self):
        """Test parse_diff_output with no file path matches."""
        diff_content = "some random text without file paths"
        result = parse_diff_output(diff_content)
        assert result == []

    def test_parse_diff_output_empty(self):
        """Test parse_diff_output with empty content."""
        result = parse_diff_output("")
        assert result == []

    def test_parse_diff_output_none(self):
        """Test parse_diff_output with None content."""
        result = parse_diff_output(None)
        assert result == []


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    def test_changed_python_files_git_success(self):
        """Test changed_python_files with successful git diff."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = changed_python_files()
            assert "src/test.py" in result

    def test_changed_python_files_git_fallback_to_unified(self):
        """Test changed_python_files with git failure and unified diff success."""
        # First call (git) fails, second call (unified diff) succeeds
        git_result = MagicMock()
        git_result.returncode = 1
        git_result.stdout = ""
        git_result.stderr = "git error"

        unified_result = MagicMock()
        unified_result.returncode = 0
        unified_result.stdout = """--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        unified_result.stderr = ""

        with patch('subprocess.run', side_effect=[git_result, unified_result]):
            result = changed_python_files()
            assert "src/test.py" in result

    def test_changed_python_files_both_fail(self):
        """Test changed_python_files with both git and unified diff failing."""
        git_result = MagicMock()
        git_result.returncode = 1
        git_result.stdout = ""
        git_result.stderr = "git error"

        unified_result = MagicMock()
        unified_result.returncode = 1
        unified_result.stdout = ""
        unified_result.stderr = "diff error"

        with patch('subprocess.run', side_effect=[git_result, unified_result]):
            result = changed_python_files()
            assert result == []

    def test_changed_python_files_git_exception(self):
        """Test changed_python_files with git exception and unified diff success."""
        unified_result = MagicMock()
        unified_result.returncode = 0
        unified_result.stdout = """--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        unified_result.stderr = ""

        with patch('subprocess.run', side_effect=[FileNotFoundError(), unified_result]):
            result = changed_python_files()
            assert "src/test.py" in result

    def test_changed_python_files_both_exceptions(self):
        """Test changed_python_files with both git and unified diff exceptions."""
        with patch('subprocess.run', side_effect=[FileNotFoundError(), FileNotFoundError()]):
            result = changed_python_files()
            assert result == []

    def test_changed_python_files_filters_python_only(self):
        """Test changed_python_files filters to Python files only."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")

diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,3 @@
 # Test
-old content
+new content
"""
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = changed_python_files()
            assert "src/test.py" in result
            assert "README.md" not in result

    def test_changed_python_files_empty_output(self):
        """Test changed_python_files with empty output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = changed_python_files()
            assert result == []

    def test_changed_python_files_no_python_files(self):
        """Test changed_python_files with no Python files in diff."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,3 @@
 # Test
-old content
+new content
"""
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            result = changed_python_files()
            assert result == []
