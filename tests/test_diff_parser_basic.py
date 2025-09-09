"""Basic tests for the AI-Guard diff parser module."""

import pytest
from src.ai_guard.diff_parser import parse_diff


def test_diff_parser_import():
    """Test that the diff parser module can be imported."""
    from src.ai_guard import diff_parser
    assert diff_parser is not None


def test_parse_diff_empty():
    """Test parsing an empty diff."""
    result = parse_diff("")
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 0


def test_parse_diff_basic():
    """Test parsing a basic diff."""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
"""
    result = parse_diff(diff)
    assert result is not None
    assert isinstance(result, list)


def test_parse_diff_with_new_file():
    """Test parsing diff with a new file."""
    diff = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def new_function():
+    return "new"
+"""
    result = parse_diff(diff)
    assert result is not None
    assert isinstance(result, list)


def test_parse_diff_with_deleted_file():
    """Test parsing diff with a deleted file."""
    diff = """diff --git a/old_file.py b/old_file.py
deleted file mode 100644
index 1234567..0000000
--- a/old_file.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_function():
-    return "old"
-"""
    result = parse_diff(diff)
    assert result is not None
    assert isinstance(result, list)
