"""Comprehensive tests for diff_parser.py to achieve maximum coverage."""

import json
import subprocess
from unittest.mock import patch, mock_open

from ai_guard.diff_parser import (
    get_file_extensions,
    filter_python_files,
    parse_diff_output,
    changed_python_files,
    _git_ls_files,
    _git_changed_files,
    parse_github_event,
    _get_base_head_from_event,
    parse_diff,
    get_changed_files,
)


class TestGetFileExtensions:
    """Test get_file_extensions function."""

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
        files = ["test.py", "script.js", "style.css", "README.md"]
        result = get_file_extensions(files)
        assert set(result) == {"py", "js", "css", "md"}

    def test_get_file_extensions_no_extension(self):
        """Test with files without extensions."""
        files = ["README", "Makefile", "Dockerfile"]
        result = get_file_extensions(files)
        assert result == []

    def test_get_file_extensions_multiple_dots(self):
        """Test with files having multiple dots."""
        files = ["test.min.js", "config.prod.json"]
        result = get_file_extensions(files)
        assert set(result) == {"js", "json"}

    def test_get_file_extensions_case_insensitive(self):
        """Test that extensions are case insensitive."""
        files = ["test.PY", "script.JS", "style.CSS"]
        result = get_file_extensions(files)
        assert set(result) == {"py", "js", "css"}

    def test_get_file_extensions_non_alphanumeric(self):
        """Test with non-alphanumeric extensions."""
        files = ["test.py~", "script.js.bak", "style.css.tmp"]
        result = get_file_extensions(files)
        # "bak" and "tmp" are alphanumeric, so they should be included
        # Only "py~" should be excluded because "~" is not alphanumeric
        assert set(result) == {"bak", "tmp"}

    def test_get_file_extensions_sorted(self):
        """Test that extensions are returned sorted."""
        files = ["test.js", "script.py", "style.css"]
        result = get_file_extensions(files)
        assert result == ["css", "js", "py"]


class TestFilterPythonFiles:
    """Test filter_python_files function."""

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
        files = ["test.py", "script.js", "style.css", "module.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "module.py"]

    def test_filter_python_files_no_python(self):
        """Test with no Python files."""
        files = ["test.js", "script.css", "style.html"]
        result = filter_python_files(files)
        assert result == []

    def test_filter_python_files_case_sensitive(self):
        """Test that filtering is case sensitive."""
        files = ["test.PY", "script.py", "module.Py"]
        result = filter_python_files(files)
        assert result == ["script.py"]


class TestParseDiffOutput:
    """Test parse_diff_output function."""

    def test_parse_diff_output_empty(self):
        """Test with empty diff output."""
        result = parse_diff_output("")
        assert result == []

    def test_parse_diff_output_single_file(self):
        """Test with single file in diff."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""
        result = parse_diff_output(diff)
        assert result == ["test.py"]

    def test_parse_diff_output_multiple_files(self):
        """Test with multiple files in diff."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello World")

diff --git a/script.js b/script.js
index 1234567..abcdefg 100644
--- a/script.js
+++ b/script.js
@@ -1,3 +1,4 @@
 function hello() {
-    console.log("Hello");
+    console.log("Hello World");
}
"""
        result = parse_diff_output(diff)
        assert set(result) == {"test.py", "script.js"}

    def test_parse_diff_output_no_diff_header(self):
        """Test with diff output without proper headers."""
        diff = "This is not a proper diff output"
        result = parse_diff_output(diff)
        assert result == []

    def test_parse_diff_output_malformed_header(self):
        """Test with malformed diff header."""
        diff = """diff --git a/test.py b/test.py
malformed header
"""
        result = parse_diff_output(diff)
        assert result == []


class TestGitLsFiles:
    """Test _git_ls_files function."""

    @patch("subprocess.check_output")
    def test_git_ls_files_success(self, mock_check_output):
        """Test successful git ls-files execution."""
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.py\n"
        result = _git_ls_files()
        assert result == ["file1.py", "file2.js", "file3.py"]
        mock_check_output.assert_called_once_with(["git", "ls-files"], text=True)

    @patch("subprocess.check_output")
    def test_git_ls_files_failure(self, mock_check_output):
        """Test git ls-files execution failure."""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")
        result = _git_ls_files()
        assert result == []
        mock_check_output.assert_called_once_with(["git", "ls-files"], text=True)

    @patch("subprocess.check_output")
    def test_git_ls_files_empty_output(self, mock_check_output):
        """Test git ls-files with empty output."""
        mock_check_output.return_value = ""
        result = _git_ls_files()
        assert result == []
        mock_check_output.assert_called_once_with(["git", "ls-files"], text=True)

    @patch("subprocess.check_output")
    def test_git_ls_files_file_not_found(self, mock_check_output):
        """Test git ls-files with file not found error."""
        mock_check_output.side_effect = FileNotFoundError()
        result = _git_ls_files()
        assert result == []
        mock_check_output.assert_called_once_with(["git", "ls-files"], text=True)


class TestGitChangedFiles:
    """Test _git_changed_files function."""

    @patch("subprocess.check_output")
    def test_git_changed_files_success(self, mock_check_output):
        """Test successful git diff execution."""
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.py\n"
        result = _git_changed_files("main", "feature")
        assert result == ["file1.py", "file2.js", "file3.py"]
        mock_check_output.assert_called_once_with(
            ["git", "diff", "--name-only", "main...feature"], text=True
        )

    @patch("subprocess.check_output")
    def test_git_changed_files_failure(self, mock_check_output):
        """Test git diff execution failure."""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")
        result = _git_changed_files("main", "feature")
        assert result == []
        mock_check_output.assert_called_once_with(
            ["git", "diff", "--name-only", "main...feature"], text=True
        )

    @patch("subprocess.check_output")
    def test_git_changed_files_empty_output(self, mock_check_output):
        """Test git diff with empty output."""
        mock_check_output.return_value = ""
        result = _git_changed_files("main", "feature")
        assert result == []
        mock_check_output.assert_called_once_with(
            ["git", "diff", "--name-only", "main...feature"], text=True
        )


class TestParseGithubEvent:
    """Test parse_github_event function."""

    def test_parse_github_event_success(self):
        """Test successful GitHub event parsing."""
        event_data = {
            "pull_request": {"base": {"ref": "main"}, "head": {"ref": "feature"}}
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            result = parse_github_event("event.json")
            assert result == event_data

    def test_parse_github_event_file_not_found(self):
        """Test GitHub event parsing with file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = parse_github_event("nonexistent.json")
            assert result == {}

    def test_parse_github_event_invalid_json(self):
        """Test GitHub event parsing with invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            result = parse_github_event("event.json")
            assert result == {}

    def test_parse_github_event_empty_file(self):
        """Test GitHub event parsing with empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            result = parse_github_event("event.json")
            assert result == {}


class TestGetBaseHeadFromEvent:
    """Test _get_base_head_from_event function."""

    def test_get_base_head_from_event_success(self):
        """Test successful base/head extraction."""
        event_data = {
            "pull_request": {"base": {"ref": "main"}, "head": {"ref": "feature"}}
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            result = _get_base_head_from_event("event.json")
            assert result == ("main", "feature")

    def test_get_base_head_from_event_no_pull_request(self):
        """Test with no pull request in event."""
        event_data = {"push": {"ref": "refs/heads/main"}}
        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            result = _get_base_head_from_event("event.json")
            assert result is None

    def test_get_base_head_from_event_file_not_found(self):
        """Test with file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = _get_base_head_from_event("nonexistent.json")
            assert result is None

    def test_get_base_head_from_event_invalid_json(self):
        """Test with invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            result = _get_base_head_from_event("event.json")
            assert result is None


class TestParseDiff:
    """Test parse_diff function."""

    def test_parse_diff_empty(self):
        """Test with empty diff content."""
        result = parse_diff("")
        assert result == []

    def test_parse_diff_single_file(self):
        """Test with single file diff."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello World")
"""
        result = parse_diff(diff)
        assert result == ["test.py"]

    def test_parse_diff_multiple_files(self):
        """Test with multiple files diff."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello World")

diff --git a/script.js b/script.js
index 1234567..abcdefg 100644
--- a/script.js
+++ b/script.js
@@ -1,3 +1,4 @@
 function hello() {
-    console.log("Hello");
+    console.log("Hello World");
}
"""
        result = parse_diff(diff)
        assert set(result) == {"test.py", "script.js"}


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    @patch("ai_guard.diff_parser._get_base_head_from_event")
    @patch("ai_guard.diff_parser._git_changed_files")
    def test_changed_python_files_with_event(
        self, mock_git_changed, mock_get_base_head
    ):
        """Test with GitHub event file."""
        mock_get_base_head.return_value = ("main", "feature")
        mock_git_changed.return_value = ["test.py", "script.js", "module.py"]

        result = changed_python_files("event.json")
        assert result == ["test.py", "module.py"]
        mock_get_base_head.assert_called_once_with("event.json")
        mock_git_changed.assert_called_once_with("main", "feature")

    @patch("ai_guard.diff_parser._get_base_head_from_event")
    @patch("ai_guard.diff_parser._git_ls_files")
    def test_changed_python_files_no_event(self, mock_git_ls, mock_get_base_head):
        """Test without GitHub event file."""
        mock_get_base_head.return_value = None
        mock_git_ls.return_value = ["test.py", "script.js", "module.py"]

        result = changed_python_files(None)
        assert result == ["test.py", "module.py"]
        mock_get_base_head.assert_called_once_with(None)
        mock_git_ls.assert_called_once()

    @patch("ai_guard.diff_parser._get_base_head_from_event")
    @patch("ai_guard.diff_parser._git_changed_files")
    def test_changed_python_files_no_base_head(
        self, mock_git_changed, mock_get_base_head
    ):
        """Test when no base/head can be determined."""
        mock_get_base_head.return_value = None
        mock_git_changed.return_value = []

        result = changed_python_files("event.json")
        assert result == []
        mock_get_base_head.assert_called_once_with("event.json")
        mock_git_changed.assert_not_called()


class TestGetChangedFiles:
    """Test get_changed_files function."""

    @patch("ai_guard.diff_parser.changed_python_files")
    def test_get_changed_files_with_event(self, mock_changed_python):
        """Test with event file."""
        mock_changed_python.return_value = ["test.py", "module.py"]

        result = get_changed_files("event.json")
        assert result == ["test.py", "module.py"]
        mock_changed_python.assert_called_once_with("event.json")

    @patch("ai_guard.diff_parser.changed_python_files")
    def test_get_changed_files_no_event(self, mock_changed_python):
        """Test without event file."""
        mock_changed_python.return_value = ["test.py", "module.py"]

        result = get_changed_files(None)
        assert result == ["test.py", "module.py"]
        mock_changed_python.assert_called_once_with(None)

    @patch("ai_guard.diff_parser.changed_python_files")
    def test_get_changed_files_empty_result(self, mock_changed_python):
        """Test with empty result."""
        mock_changed_python.return_value = []

        result = get_changed_files("event.json")
        assert result == []
        mock_changed_python.assert_called_once_with("event.json")
