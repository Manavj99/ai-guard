"""Simple tests for diff_parser.py module."""

import pytest

from src.ai_guard.diff_parser import changed_python_files


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    def test_changed_python_files_empty_diff(self):
        """Test with empty diff."""
        result = changed_python_files("")
        assert isinstance(result, list)

    def test_changed_python_files_basic_diff(self):
        """Test with basic diff."""
        diff = """
diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello World")
+    print("New line")
"""
        result = changed_python_files(diff)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_changed_python_files_no_python_files(self):
        """Test with diff containing no Python files."""
        diff = """
diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # Test Project
 This is a test project.
+Added a new line.
"""
        result = changed_python_files(diff)
        assert isinstance(result, list)
