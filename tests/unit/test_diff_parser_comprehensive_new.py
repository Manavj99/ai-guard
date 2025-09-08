"""Comprehensive tests for diff_parser.py to achieve high coverage."""

import tempfile

from ai_guard.diff_parser import (
    DiffParser,
    changed_python_files,
    parse_diff,
    get_changed_files,
)


class TestDiffParser:
    """Test DiffParser class."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_parse_diff_basic(self):
        """Test basic diff parsing."""
        parser = DiffParser()

        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def existing_function():
     pass
 
+def new_function():
+    return "new"
"""

        result = parser.parse_diff(diff)
        assert result is not None
        assert len(result) > 0

    def test_parse_diff_multiple_files(self):
        """Test parsing diff with multiple files."""
        parser = DiffParser()

        diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def func1():
     pass
+    # new comment
 
diff --git a/file2.py b/file2.py
index 1234567..abcdefg 100644
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,3 @@
 def func2():
     pass
+    # another comment
"""

        result = parser.parse_diff(diff)
        assert result is not None
        assert len(result) >= 2

    def test_parse_diff_empty(self):
        """Test parsing empty diff."""
        parser = DiffParser()

        result = parser.parse_diff("")
        assert result is not None
        assert len(result) == 0

    def test_parse_diff_invalid(self):
        """Test parsing invalid diff."""
        parser = DiffParser()

        invalid_diff = "This is not a valid diff"
        result = parser.parse_diff(invalid_diff)
        assert result is not None
        assert len(result) == 0

    def test_get_changed_files(self):
        """Test getting changed files from diff."""
        parser = DiffParser()

        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line

diff --git a/tests/test_file.py b/tests/test_file.py
index 1234567..abcdefg 100644
--- a/tests/test_file.py
+++ b/tests/test_file.py
@@ -1,2 +1,3 @@
 def test_function():
     pass
+    # another new line
"""

        files = parser.get_changed_files(diff)
        assert len(files) == 2
        assert "src/test.py" in files
        assert "tests/test_file.py" in files

    def test_get_changed_files_python_only(self):
        """Test getting only Python files."""
        parser = DiffParser()

        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line

diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Test
 Some content
+New content
"""

        files = parser.get_changed_files(diff, python_only=True)
        assert len(files) == 1
        assert "test.py" in files
        assert "README.md" not in files

    def test_extract_function_changes(self):
        """Test extracting function changes."""
        parser = DiffParser()

        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,8 @@
 def existing_function():
     pass
 
+def new_function():
+    return "new"
+
 class TestClass:
     def method(self):
         pass
"""

        changes = parser.extract_function_changes(diff)
        assert len(changes) > 0

        # Check for new function
        new_functions = [
            c
            for c in changes
            if c.get("type") == "added" and "new_function" in c.get("content", "")
        ]
        assert len(new_functions) > 0

    def test_extract_class_changes(self):
        """Test extracting class changes."""
        parser = DiffParser()

        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,10 @@
 def existing_function():
     pass
 
+class NewClass:
+    def __init__(self):
+        self.value = "test"
+
 class ExistingClass:
     def method(self):
         pass
"""

        changes = parser.extract_class_changes(diff)
        assert len(changes) > 0

        # Check for new class
        new_classes = [
            c
            for c in changes
            if c.get("type") == "added" and "NewClass" in c.get("content", "")
        ]
        assert len(new_classes) > 0

    def test_parse_hunk_header(self):
        """Test parsing hunk headers."""
        parser = DiffParser()

        # Test various hunk header formats
        headers = [
            "@@ -1,3 +1,4 @@",
            "@@ -10,5 +15,8 @@ context",
            "@@ -1 +1,2 @@",
            "@@ -5,0 +6,3 @@",
        ]

        for header in headers:
            result = parser.parse_hunk_header(header)
            assert result is not None
            assert "old_start" in result
            assert "old_count" in result
            assert "new_start" in result
            assert "new_count" in result

    def test_parse_hunk_header_invalid(self):
        """Test parsing invalid hunk headers."""
        parser = DiffParser()

        invalid_headers = ["not a hunk header", "@@ invalid @@", "@@ -1,3 +1,4", ""]

        for header in invalid_headers:
            result = parser.parse_hunk_header(header)
            assert result is None

    def test_get_line_type(self):
        """Test determining line type."""
        parser = DiffParser()

        # Test different line types
        assert parser.get_line_type("+added line") == "added"
        assert parser.get_line_type("-removed line") == "removed"
        assert parser.get_line_type(" context line") == "context"
        assert parser.get_line_type("\\ No newline at end of file") == "no_newline"
        assert parser.get_line_type("@@ -1,3 +1,4 @@") == "hunk_header"
        assert parser.get_line_type("diff --git a/file b/file") == "file_header"
        assert parser.get_line_type("index 1234567..abcdefg") == "index_header"
        assert parser.get_line_type("--- a/file") == "old_file"
        assert parser.get_line_type("+++ b/file") == "new_file"
        assert parser.get_line_type("regular line") == "unknown"


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    def test_changed_python_files_basic(self):
        """Test basic functionality."""
        diff = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line
"""

        files = changed_python_files(diff)
        assert len(files) == 1
        assert "src/test.py" in files

    def test_changed_python_files_multiple(self):
        """Test with multiple Python files."""
        diff = """diff --git a/src/module1.py b/src/module1.py
index 1234567..abcdefg 100644
--- a/src/module1.py
+++ b/src/module1.py
@@ -1,2 +1,3 @@
 def func1():
     pass
+    # new line

diff --git a/src/module2.py b/src/module2.py
index 1234567..abcdefg 100644
--- a/src/module2.py
+++ b/src/module2.py
@@ -1,2 +1,3 @@
 def func2():
     pass
+    # another new line
"""

        files = changed_python_files(diff)
        assert len(files) == 2
        assert "src/module1.py" in files
        assert "src/module2.py" in files

    def test_changed_python_files_non_python(self):
        """Test filtering out non-Python files."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line

diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Test
 Some content
+New content

diff --git a/config.json b/config.json
index 1234567..abcdefg 100644
--- a/config.json
+++ b/config.json
@@ -1,2 +1,3 @@
 {
   "key": "value"
+  "new_key": "new_value"
 }
"""

        files = changed_python_files(diff)
        assert len(files) == 1
        assert "test.py" in files
        assert "README.md" not in files
        assert "config.json" not in files

    def test_changed_python_files_empty(self):
        """Test with empty diff."""
        files = changed_python_files("")
        assert len(files) == 0

    def test_changed_python_files_invalid(self):
        """Test with invalid diff."""
        files = changed_python_files("This is not a diff")
        assert len(files) == 0


class TestParseDiff:
    """Test parse_diff function."""

    def test_parse_diff_basic(self):
        """Test basic diff parsing."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line
"""

        result = parse_diff(diff)
        assert result is not None
        assert len(result) > 0

    def test_parse_diff_complex(self):
        """Test parsing complex diff."""
        diff = """diff --git a/src/complex.py b/src/complex.py
index 1234567..abcdefg 100644
--- a/src/complex.py
+++ b/src/complex.py
@@ -1,10 +1,15 @@
 class ComplexClass:
     def __init__(self):
         self.value = 0
+        self.new_value = None
 
     def existing_method(self):
         return self.value
+    
+    def new_method(self):
+        return self.new_value
 
 def existing_function():
     pass
+    # new comment
"""

        result = parse_diff(diff)
        assert result is not None
        assert len(result) > 0


class TestGetChangedFiles:
    """Test get_changed_files function."""

    def test_get_changed_files_basic(self):
        """Test basic file extraction."""
        diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def func1():
     pass
+    # new line

diff --git a/file2.py b/file2.py
index 1234567..abcdefg 100644
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,3 @@
 def func2():
     pass
+    # another new line
"""

        files = get_changed_files(diff)
        assert len(files) == 2
        assert "file1.py" in files
        assert "file2.py" in files


class TestExtractFunctionChanges:
    """Test extract_function_changes function."""

    def test_extract_function_changes_basic(self):
        """Test basic function change extraction."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,8 @@
 def existing_function():
     pass
 
+def new_function():
+    return "new"
+
 class TestClass:
     def method(self):
         pass
"""

        changes = extract_function_changes(diff)
        assert len(changes) > 0


class TestExtractClassChanges:
    """Test extract_class_changes function."""

    def test_extract_class_changes_basic(self):
        """Test basic class change extraction."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,10 @@
 def existing_function():
     pass
 
+class NewClass:
+    def __init__(self):
+        self.value = "test"
+
 class ExistingClass:
     def method(self):
         pass
"""

        changes = extract_class_changes(diff)
        assert len(changes) > 0


class TestDiffParserIntegration:
    """Integration tests for diff parser."""

    def test_parser_with_real_diff(self):
        """Test parser with realistic diff."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(
                """diff --git a/src/ai_guard/analyzer.py b/src/ai_guard/analyzer.py
index 1234567..abcdefg 100644
--- a/src/ai_guard/analyzer.py
+++ b/src/ai_guard/analyzer.py
@@ -1,5 +1,8 @@
 def main():
     pass
 
+def new_function():
+    return "new"
+
 class Analyzer:
     def analyze(self):
         pass
"""
            )
            f.flush()

            try:
                with open(f.name, "r") as diff_file:
                    diff_content = diff_file.read()

                parser = DiffParser()
                result = parser.parse_diff(diff_content)

                assert result is not None
                assert len(result) > 0

                files = parser.get_changed_files(diff_content)
                assert len(files) == 1
                assert "src/ai_guard/analyzer.py" in files

            finally:
                os.unlink(f.name)

    def test_parser_edge_cases(self):
        """Test parser with edge cases."""
        parser = DiffParser()

        # Test with binary file diff
        binary_diff = """diff --git a/binary.bin b/binary.bin
index 1234567..abcdefg 100644
Binary files a/binary.bin and b/binary.bin differ
"""

        result = parser.parse_diff(binary_diff)
        assert result is not None

        # Test with rename
        rename_diff = """diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
index 1234567..abcdefg 100644
--- a/old_name.py
+++ b/new_name.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line
"""

        result = parser.parse_diff(rename_diff)
        assert result is not None

        files = parser.get_changed_files(rename_diff)
        assert "new_name.py" in files
