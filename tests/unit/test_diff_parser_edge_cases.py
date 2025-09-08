"""Edge case tests for diff parser module to improve coverage to 90%+."""

from unittest.mock import patch

from ai_guard.diff_parser import (
    changed_python_files,
    parse_github_event,
    get_file_extensions,
    filter_python_files,
    parse_diff_output,
)


class TestDiffParserEdgeCases:
    """Test edge cases and error handling in diff parser module."""

    def test_get_file_extensions_basic(self):
        """Test basic file extension extraction."""
        extensions = get_file_extensions(["src/test.py", "tests/test_file.py"])

        assert extensions == {".py"}

    def test_get_file_extensions_mixed(self):
        """Test file extension extraction with mixed file types."""
        extensions = get_file_extensions(
            ["src/test.py", "src/config.js", "src/style.css", "README.md"]
        )

        assert extensions == {".py", ".js", ".css", ".md"}

    def test_get_file_extensions_no_files(self):
        """Test file extension extraction with no files."""
        extensions = get_file_extensions([])

        assert extensions == set()

    def test_get_file_extensions_no_extension(self):
        """Test file extension extraction with files without extensions."""
        extensions = get_file_extensions(["Makefile", "Dockerfile", "README"])

        assert extensions == set()

    def test_get_file_extensions_hidden_files(self):
        """Test file extension extraction with hidden files."""
        extensions = get_file_extensions([".env", ".gitignore", "src/.DS_Store"])

        assert extensions == {".env", ".gitignore", ".DS_Store"}

    def test_filter_python_files_basic(self):
        """Test basic Python file filtering."""
        files = ["src/test.py", "tests/test_file.py", "src/config.js", "README.md"]

        python_files = filter_python_files(files)

        assert python_files == ["src/test.py", "tests/test_file.py"]

    def test_filter_python_files_no_python(self):
        """Test Python file filtering with no Python files."""
        files = ["src/config.js", "src/style.css", "README.md"]

        python_files = filter_python_files(files)

        assert python_files == []

    def test_filter_python_files_empty_list(self):
        """Test Python file filtering with empty list."""
        python_files = filter_python_files([])

        assert python_files == []

    def test_filter_python_files_case_sensitive(self):
        """Test Python file filtering is case sensitive."""
        files = ["src/test.py", "src/TEST.PY", "src/Test.py"]

        python_files = filter_python_files(files)

        assert python_files == ["src/test.py", "src/Test.py"]

    def test_filter_python_files_with_directories(self):
        """Test Python file filtering with directory names."""
        files = ["src/", "tests/", "src/test.py", "tests/test_file.py"]

        python_files = filter_python_files(files)

        assert python_files == ["src/test.py", "tests/test_file.py"]

    @patch("subprocess.run")
    def test_changed_python_files_success(self, mock_run):
        """Test successful execution of changed_python_files."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"src/test.py\ntests/test_file.py\nREADME.md"

        result = changed_python_files("event.json")

        assert result == ["src/test.py", "tests/test_file.py"]
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_changed_python_files_git_failure(self, mock_run):
        """Test changed_python_files when git command fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = b"fatal: not a git repository"

        result = changed_python_files("event.json")

        assert result == []

    @patch("subprocess.run")
    def test_changed_python_files_no_event_file(self, mock_run):
        """Test changed_python_files with no event file."""
        result = changed_python_files(None)

        assert result == []
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_changed_python_files_empty_output(self, mock_run):
        """Test changed_python_files with empty git output."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result = changed_python_files("event.json")

        assert result == []

    @patch("subprocess.run")
    def test_changed_python_files_with_binary_files(self, mock_run):
        """Test changed_python_files with binary files in output."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            b"src/test.py\nsrc/image.png\nsrc/data.bin\ntests/test_file.py"
        )

        result = changed_python_files("event.json")

        assert result == ["src/test.py", "tests/test_file.py"]

    @patch("subprocess.run")
    def test_changed_python_files_with_special_characters(self, mock_run):
        """Test changed_python_files with special characters in filenames."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            b"src/test file.py\nsrc/test-file.py\nsrc/test_file.py"
        )

        result = changed_python_files("event.json")

        assert result == ["src/test file.py", "src/test-file.py", "src/test_file.py"]

    @patch("subprocess.run")
    def test_changed_python_files_with_unicode(self, mock_run):
        """Test changed_python_files with unicode filenames."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "src/тест.py\nsrc/test.py".encode("utf-8")

        result = changed_python_files("event.json")

        assert result == ["src/тест.py", "src/test.py"]

    @patch("subprocess.run")
    def test_changed_python_files_with_newlines(self, mock_run):
        """Test changed_python_files with various newline formats."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            b"src/test.py\r\ntests/test_file.py\nsrc/config.py\r"
        )

        result = changed_python_files("event.json")

        assert result == ["src/test.py", "tests/test_file.py", "src/config.py"]

    def test_parse_github_event_pull_request(self):
        """Test parsing GitHub pull request event."""
        event_data = {
            "pull_request": {"head": {"sha": "abc123"}, "base": {"sha": "def456"}}
        }

        result = parse_github_event(event_data)

        assert result == ("abc123", "def456")

    def test_parse_github_event_push(self):
        """Test parsing GitHub push event."""
        event_data = {"before": "abc123", "after": "def456"}

        result = parse_github_event(event_data)

        assert result == ("def456", "abc123")

    def test_parse_github_event_unknown_type(self):
        """Test parsing unknown GitHub event type."""
        event_data = {"unknown": "data"}

        result = parse_github_event(event_data)

        assert result == (None, None)

    def test_parse_github_event_empty(self):
        """Test parsing empty GitHub event."""
        result = parse_github_event({})

        assert result == (None, None)

    def test_parse_github_event_none(self):
        """Test parsing None GitHub event."""
        result = parse_github_event(None)

        assert result == (None, None)

    def test_parse_github_event_missing_fields(self):
        """Test parsing GitHub event with missing fields."""
        event_data = {"pull_request": {}}  # Missing head/base

        result = parse_github_event(event_data)

        assert result == (None, None)

    def test_parse_diff_output_basic(self):
        """Test basic diff output parsing."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index abc123..def456 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 import os
+import sys
 def test_function():
     pass"""

        result = parse_diff_output(diff_output)

        assert "src/test.py" in result

    def test_parse_diff_output_multiple_files(self):
        """Test parsing diff output with multiple files."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index abc123..def456 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 import os
+import sys
 def test_function():
     pass
diff --git a/tests/test_file.py b/tests/test_file.py
index ghi789..jkl012 100644
--- a/tests/test_file.py
+++ b/tests/test_file.py
@@ -1,2 +1,3 @@
 def test_something():
     pass
+def test_another():
+    pass"""

        result = parse_diff_output(diff_output)

        assert "src/test.py" in result
        assert "tests/test_file.py" in result

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        result = parse_diff_output("")

        assert result == []

    def test_parse_diff_output_no_files(self):
        """Test parsing diff output with no file changes."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index abc123..abc123 100644
--- a/src/test.py
+++ b/src/test.py
@@ -0,0 +0,0 @@"""

        result = parse_diff_output(diff_output)

        assert result == []

    def test_parse_diff_output_malformed(self):
        """Test parsing malformed diff output."""
        diff_output = "This is not a valid diff output"

        result = parse_diff_output(diff_output)

        assert result == []

    def test_parse_diff_output_with_binary_files(self):
        """Test parsing diff output with binary files."""
        diff_output = """diff --git a/src/image.png b/src/image.png
index abc123..def456 100644
Binary files a/src/image.png and b/src/image.png differ
diff --git a/src/test.py b/src/test.py
index ghi789..jkl012 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 import os
+import sys
 def test_function():
     pass"""

        result = parse_diff_output(diff_output)

        assert "src/test.py" in result
        assert "src/image.png" not in result  # Binary files should be ignored

    def test_parse_diff_output_with_renamed_files(self):
        """Test parsing diff output with renamed files."""
        diff_output = """diff --git a/src/old_name.py b/src/new_name.py
similarity index 95%
rename from src/old_name.py
rename to src/new_name.py
index abc123..def456 100644
--- a/src/old_name.py
+++ b/src/new_name.py
@@ -1,3 +1,4 @@
 import os
+import sys
 def test_function():
     pass"""

        result = parse_diff_output(diff_output)

        assert "src/new_name.py" in result

    def test_parse_diff_output_with_deleted_files(self):
        """Test parsing diff output with deleted files."""
        diff_output = """diff --git a/src/deleted.py b/src/deleted.py
deleted file mode 100644
index abc123..000000
--- a/src/deleted.py
+++ /dev/null
@@ -1,3 +0,0 @@
-import os
-def test_function():
-    pass"""

        result = parse_diff_output(diff_output)

        assert result == []  # Deleted files should not be included

    def test_parse_diff_output_with_added_files(self):
        """Test parsing diff output with added files."""
        diff_output = """diff --git a/src/new_file.py b/src/new_file.py
new file mode 100644
index 000000..abc123
--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1,3 @@
+import os
+def test_function():
+    pass"""

        result = parse_diff_output(diff_output)

        assert "src/new_file.py" in result

    def test_parse_diff_output_with_complex_paths(self):
        """Test parsing diff output with complex file paths."""
        diff_output = """diff --git "a/src/subdir/test file.py" "b/src/subdir/test file.py"
index abc123..def456 100644
--- "a/src/subdir/test file.py"
+++ "b/src/subdir/test file.py"
@@ -1,3 +1,4 @@
 import os
+import sys
 def test_function():
     pass"""

        result = parse_diff_output(diff_output)

        assert "src/subdir/test file.py" in result

    def test_parse_diff_output_with_unicode_paths(self):
        """Test parsing diff output with unicode file paths."""
        diff_output = """diff --git a/src/тест.py b/src/тест.py
index abc123..def456 100644
--- a/src/тест.py
+++ b/src/тест.py
@@ -1,3 +1,4 @@
 import os
+import sys
 def test_function():
     pass"""

        result = parse_diff_output(diff_output)

        assert "src/тест.py" in result
