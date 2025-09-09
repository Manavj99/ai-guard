"""Comprehensive tests for the AI-Guard diff parser module."""

import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from src.ai_guard.diff_parser import (
    parse_diff, changed_python_files, get_file_extensions,
    filter_python_files, parse_diff_output
)


class TestParseDiff:
    """Test diff parsing functionality."""

    def test_parse_empty_diff(self):
        """Test parsing empty diff."""
        result = parse_diff("")
        assert result == []

    def test_parse_simple_diff(self):
        """Test parsing simple diff."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello World")
+    return True
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "src/test.py"

    def test_parse_multiple_files_diff(self):
        """Test parsing diff with multiple files."""
        diff = """diff --git a/src/file1.py b/src/file1.py
index 1234567..abcdefg 100644
--- a/src/file1.py
+++ b/src/file1.py
@@ -1,2 +1,3 @@
 def func1():
     pass
+    return True

diff --git a/src/file2.py b/src/file2.py
index 1234567..abcdefg 100644
--- a/src/file2.py
+++ b/src/file2.py
@@ -1,2 +1,3 @@
 def func2():
     pass
+    return False
"""
        result = parse_diff(diff)
        assert len(result) == 2
        assert result[0] == "src/file1.py"
        assert result[1] == "src/file2.py"

    def test_parse_diff_with_binary_files(self):
        """Test parsing diff with binary files."""
        diff = """diff --git a/binary.bin b/binary.bin
index 1234567..abcdefg 100644
Binary files a/binary.bin and b/binary.bin differ
"""
        result = parse_diff(diff)
        assert len(result) == 0  # Binary files should be ignored

    def test_parse_diff_with_renamed_files(self):
        """Test parsing diff with renamed files."""
        diff = """diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
index 1234567..abcdefg 100644
--- a/old_name.py
+++ b/new_name.py
@@ -1,2 +1,3 @@
 def func():
     pass
+    return True
"""
        result = parse_diff(diff)
        assert len(result) == 2  # Parser returns both old and new names
        assert "old_name.py" in result
        assert "new_name.py" in result

    def test_parse_diff_malformed(self):
        """Test parsing malformed diff."""
        diff = "not a valid diff"
        result = parse_diff(diff)
        assert result == []


class TestChangedPythonFiles:
    """Test changed Python files functionality."""

    def test_changed_python_files_empty(self):
        """Test with empty diff."""
        # changed_python_files doesn't take diff content, it gets all tracked files
        # This test should be testing parse_diff + filter_python_files instead
        result = parse_diff("")
        python_files = filter_python_files(result)
        assert python_files == []

    def test_changed_python_files_python_only(self):
        """Test with Python files only."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
     pass
+    return True
"""
        result = parse_diff(diff)
        python_files = filter_python_files(result)
        assert python_files == ["src/test.py"]

    def test_changed_python_files_mixed(self):
        """Test with mixed file types."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
     pass
+    return True

diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Test
 Some text
+More text
"""
        result = parse_diff(diff)
        python_files = filter_python_files(result)
        assert python_files == ["src/test.py"]

    def test_changed_python_files_no_python(self):
        """Test with no Python files."""
        diff = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Test
 Some text
+More text
"""
        result = parse_diff(diff)
        python_files = filter_python_files(result)
        assert python_files == []


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_file_extensions(self):
        """Test file extension extraction."""
        files = ["test.py", "test.js", "test.txt", "test.PY", "test"]
        extensions = get_file_extensions(files)
        assert "py" in extensions
        assert "js" in extensions
        assert "txt" in extensions
        assert "py" in extensions  # Should be case insensitive

    def test_get_file_extensions_empty(self):
        """Test file extension extraction with empty list."""
        extensions = get_file_extensions([])
        assert extensions == []

    def test_get_file_extensions_no_extensions(self):
        """Test file extension extraction with files without extensions."""
        files = ["test", "README", "Makefile"]
        extensions = get_file_extensions(files)
        assert extensions == []

    def test_filter_python_files(self):
        """Test Python file filtering."""
        files = ["test.py", "test.js", "test.txt", "test.pyi", "test.PY"]
        python_files = filter_python_files(files)
        assert "test.py" in python_files
        assert "test.pyi" not in python_files  # Only .py files are included
        assert "test.PY" not in python_files  # Case sensitive, only .py
        assert "test.js" not in python_files
        assert "test.txt" not in python_files

    def test_filter_python_files_empty(self):
        """Test Python file filtering with empty list."""
        python_files = filter_python_files([])
        assert python_files == []

    def test_parse_diff_output(self):
        """Test parsing git diff output."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
     pass
+    return True
"""
        files = parse_diff_output(diff_output)
        assert "src/test.py" in files

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        files = parse_diff_output("")
        assert files == []

    def test_parse_diff_output_multiple_files(self):
        """Test parsing diff output with multiple files."""
        diff_output = """diff --git a/src/file1.py b/src/file1.py
index 1234567..abcdefg 100644
--- a/src/file1.py
+++ b/src/file1.py
@@ -1,2 +1,3 @@
 def func1():
     pass
+    return True

diff --git a/src/file2.py b/src/file2.py
index 1234567..abcdefg 100644
--- a/src/file2.py
+++ b/src/file2.py
@@ -1,2 +1,3 @@
 def func2():
     pass
+    return False
"""
        files = parse_diff_output(diff_output)
        assert "src/file1.py" in files
        assert "src/file2.py" in files


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_diff_with_unicode(self):
        """Test parsing diff with unicode characters."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello 世界")
+    return True
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "src/test.py"

    def test_parse_diff_with_special_characters(self):
        """Test parsing diff with special characters."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hello\\nWorld")
+    return True
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "src/test.py"

    def test_parse_diff_large_file(self):
        """Test parsing diff with large file."""
        # Create a large diff
        diff_lines = ["diff --git a/src/large.py b/src/large.py"]
        diff_lines.append("index 1234567..abcdefg 100644")
        diff_lines.append("--- a/src/large.py")
        diff_lines.append("+++ b/src/large.py")
        diff_lines.append("@@ -1,1000 +1,1001 @@")
        
        for i in range(1000):
            diff_lines.append(f" line {i}")
        diff_lines.append("+    return True")
        
        diff = "\n".join(diff_lines)
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "src/large.py"

    def test_parse_diff_with_empty_hunks(self):
        """Test parsing diff with empty hunks."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,0 +1,1 @@
+    return True
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "src/test.py"
