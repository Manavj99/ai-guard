"""Comprehensive tests for diff_parser.py to achieve 80% coverage."""

import pytest
import tempfile
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from typing import List, Dict, Any, Optional

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
    get_changed_files,
)


class TestGetFileExtensions:
    """Test get_file_extensions function comprehensively."""

    def test_get_file_extensions_none(self):
        """Test with None input."""
        result = get_file_extensions(None)
        assert result == []

    def test_get_file_extensions_empty_list(self):
        """Test with empty list."""
        result = get_file_extensions([])
        assert result == []

    def test_get_file_extensions_with_valid_extensions(self):
        """Test with valid file extensions."""
        file_paths = ["file1.py", "file2.js", "file3.txt", "file4.json"]
        result = get_file_extensions(file_paths)
        assert "py" in result
        assert "js" in result
        assert "txt" in result
        assert "json" in result
        assert len(result) == 4

    def test_get_file_extensions_no_extensions(self):
        """Test with files that have no extensions."""
        file_paths = ["README", "Makefile", "LICENSE"]
        result = get_file_extensions(file_paths)
        assert result == []

    def test_get_file_extensions_duplicate_extensions(self):
        """Test with duplicate extensions."""
        file_paths = ["file1.py", "file2.py", "file3.js", "file4.js"]
        result = get_file_extensions(file_paths)
        assert len(result) == 2
        assert "py" in result
        assert "js" in result

    def test_get_file_extensions_backup_files(self):
        """Test filtering out backup files."""
        file_paths = ["file1.py", "file2.py~", "file3.py.bak", "file4.py.tmp"]
        result = get_file_extensions(file_paths)
        assert result == ["py"]

    def test_get_file_extensions_temp_files(self):
        """Test filtering out temp files."""
        file_paths = ["file1.py", "file2.py.temp", "file3.py.tmp"]
        result = get_file_extensions(file_paths)
        assert result == ["py"]

    def test_get_file_extensions_non_alphanumeric(self):
        """Test filtering out non-alphanumeric extensions."""
        file_paths = ["file1.py", "file2.py-", "file3.py_", "file4.py."]
        result = get_file_extensions(file_paths)
        assert result == ["py"]

    def test_get_file_extensions_mixed_case(self):
        """Test with mixed case extensions."""
        file_paths = ["file1.PY", "file2.Js", "file3.TXT"]
        result = get_file_extensions(file_paths)
        assert "py" in result
        assert "js" in result
        assert "txt" in result

    def test_get_file_extensions_single_dot(self):
        """Test with files that have single dot but no extension."""
        file_paths = ["file1.", "file2..", "file3..."]
        result = get_file_extensions(file_paths)
        assert result == []

    def test_get_file_extensions_edge_cases(self):
        """Test edge cases for file extensions."""
        file_paths = ["file1.py", "file2.py.", "file3.py..", "file4.py..."]
        result = get_file_extensions(file_paths)
        assert result == ["py"]

    def test_get_file_extensions_empty_strings(self):
        """Test with empty strings in file paths."""
        file_paths = ["file1.py", "", "file2.js", "   "]
        result = get_file_extensions(file_paths)
        assert "py" in result
        assert "js" in result

    def test_get_file_extensions_whitespace_only(self):
        """Test with whitespace-only file paths."""
        file_paths = ["   ", "\t", "\n", "file1.py"]
        result = get_file_extensions(file_paths)
        assert result == ["py"]


class TestFilterPythonFiles:
    """Test filter_python_files function comprehensively."""

    def test_filter_python_files_none(self):
        """Test with None input."""
        result = filter_python_files(None)
        assert result == []

    def test_filter_python_files_empty_list(self):
        """Test with empty list."""
        result = filter_python_files([])
        assert result == []

    def test_filter_python_files_mixed_types(self):
        """Test with mixed file types."""
        files = ["test.py", "test.js", "test.txt", "another.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "another.py"]

    def test_filter_python_files_no_python(self):
        """Test with no Python files."""
        files = ["test.js", "test.txt", "test.md"]
        result = filter_python_files(files)
        assert result == []

    def test_filter_python_files_all_python(self):
        """Test with all Python files."""
        files = ["test1.py", "test2.py", "module.py"]
        result = filter_python_files(files)
        assert result == files

    def test_filter_python_files_with_none_values(self):
        """Test with None values in list."""
        files = ["test.py", "test.js", "another.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "another.py"]

    def test_filter_python_files_empty_strings(self):
        """Test with empty strings."""
        files = ["test.py", "", "test.js", "another.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "another.py"]

    def test_filter_python_files_case_sensitivity(self):
        """Test case sensitivity for .py extension."""
        files = ["test.PY", "test.py", "test.Py", "test.js"]
        result = filter_python_files(files)
        assert result == ["test.py"]  # filter_python_files is case-sensitive

    def test_filter_python_files_with_paths(self):
        """Test with full file paths."""
        files = ["/path/to/test.py", "/path/to/test.js", "relative/test.py"]
        result = filter_python_files(files)
        assert result == ["/path/to/test.py", "relative/test.py"]


class TestParseDiffOutput:
    """Test parse_diff_output function comprehensively."""

    def test_parse_diff_output_none(self):
        """Test with None input."""
        result = parse_diff_output(None)
        assert result == []

    def test_parse_diff_output_empty_string(self):
        """Test with empty string."""
        result = parse_diff_output("")
        assert result == []

    def test_parse_diff_output_standard_format(self):
        """Test with standard diff format."""
        diff_output = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    return "old"
+    return "new"
"""
        result = parse_diff_output(diff_output)
        assert "test.py" in result

    def test_parse_diff_output_multiple_files(self):
        """Test with multiple files."""
        diff_output = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-change1
+change1_new

diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-change2
+change2_new
"""
        result = parse_diff_output(diff_output)
        assert "file1.py" in result
        assert "file2.py" in result
        assert len(result) == 2

    def test_parse_diff_output_no_files(self):
        """Test with no file changes."""
        diff_output = """Some other content
that doesn't contain
file paths
"""
        result = parse_diff_output(diff_output)
        assert result == []

    def test_parse_diff_output_with_whitespace(self):
        """Test with whitespace in diff."""
        diff_output = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-change
+change_new
"""
        result = parse_diff_output(diff_output)
        assert "test.py" in result

    def test_parse_diff_output_duplicate_files(self):
        """Test with duplicate file entries."""
        diff_output = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-change
+change_new

diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-another change
+another_change_new
"""
        result = parse_diff_output(diff_output)
        assert result == ["test.py"]  # Should not duplicate

    def test_parse_diff_output_mixed_formats(self):
        """Test with mixed diff formats."""
        diff_output = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-change1
+change1_new

diff --git a/file2.js b/file2.js
--- a/file2.js
+++ b/file2.js
@@ -1,1 +1,1 @@
-change2
+change2_new
"""
        result = parse_diff_output(diff_output)
        assert "file1.py" in result
        assert "file2.js" in result

    def test_parse_diff_output_only_plus_lines(self):
        """Test with only +++ lines."""
        diff_output = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
+new line
"""
        result = parse_diff_output(diff_output)
        assert "test.py" in result

    def test_parse_diff_output_only_minus_lines(self):
        """Test with only --- lines."""
        diff_output = """diff --git a/test.py b/test.py
--- a/test.py
@@ -1,1 +1,1 @@
-old line
"""
        result = parse_diff_output(diff_output)
        assert "test.py" in result

    def test_parse_diff_output_with_newlines(self):
        """Test with various newline characters."""
        diff_output = "--- a/test.py\r\n+++ b/test.py\r\n@@ -1,1 +1,1 @@\r\n-change\r\n+change_new"
        result = parse_diff_output(diff_output)
        assert "test.py" in result

    def test_parse_diff_output_empty_lines(self):
        """Test with empty lines in diff."""
        diff_output = """diff --git a/test.py b/test.py

--- a/test.py
+++ b/test.py

@@ -1,1 +1,1 @@
-change
+change_new
"""
        result = parse_diff_output(diff_output)
        assert "test.py" in result


class TestGitLsFiles:
    """Test _git_ls_files function comprehensively."""

    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_ls_files_success(self, mock_exists, mock_check_output):
        """Test successful git ls-files execution."""
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.txt\n"
        mock_exists.return_value = True

        result = _git_ls_files()
        assert result == ["file1.py", "file2.js", "file3.txt"]
        mock_check_output.assert_called_once_with(["git", "ls-files"], text=True)

    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_ls_files_with_nonexistent_files(self, mock_exists, mock_check_output):
        """Test git ls-files with nonexistent files."""
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.txt\n"
        mock_exists.side_effect = [True, False, True]

        result = _git_ls_files()
        assert result == ["file1.py", "file3.txt"]

    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_ls_files_with_empty_lines(self, mock_exists, mock_check_output):
        """Test git ls-files with empty lines."""
        mock_check_output.return_value = "file1.py\n\nfile2.js\n  \nfile3.txt\n"
        mock_exists.return_value = True

        result = _git_ls_files()
        assert result == ["file1.py", "file2.js", "file3.txt"]

    @patch("subprocess.check_output")
    def test_git_ls_files_called_process_error(self, mock_check_output):
        """Test git ls-files with CalledProcessError."""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")

        result = _git_ls_files()
        assert result == []

    @patch("subprocess.check_output")
    def test_git_ls_files_file_not_found_error(self, mock_check_output):
        """Test git ls-files with FileNotFoundError."""
        mock_check_output.side_effect = FileNotFoundError("Git not found")

        result = _git_ls_files()
        assert result == []

    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_ls_files_with_whitespace_only_lines(
        self, mock_exists, mock_check_output
    ):
        """Test git ls-files with whitespace-only lines."""
        mock_check_output.return_value = "file1.py\n   \nfile2.js\n\t\nfile3.txt\n"
        mock_exists.return_value = True

        result = _git_ls_files()
        assert result == ["file1.py", "file2.js", "file3.txt"]

    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_ls_files_with_mixed_existing_files(
        self, mock_exists, mock_check_output
    ):
        """Test git ls-files with mixed existing/non-existing files."""
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.txt\nfile4.py\n"
        mock_exists.side_effect = [True, False, True, False]

        result = _git_ls_files()
        assert result == ["file1.py", "file3.txt"]


class TestGitChangedFiles:
    """Test _git_changed_files function comprehensively."""

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_changed_files_success(
        self, mock_exists, mock_check_output, mock_check_call
    ):
        """Test successful git diff execution."""
        mock_check_call.return_value = None
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.txt\n"
        mock_exists.return_value = True

        result = _git_changed_files("base", "head")
        assert result == ["file1.py", "file2.js", "file3.txt"]
        mock_check_call.assert_has_calls(
            [
                call(
                    ["git", "rev-parse", "--verify", "base"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
                call(
                    ["git", "rev-parse", "--verify", "head"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
            ]
        )
        mock_check_output.assert_called_once_with(
            ["git", "diff", "--name-only", "base...head"], text=True
        )

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_changed_files_with_nonexistent_files(
        self, mock_exists, mock_check_output, mock_check_call
    ):
        """Test git diff with nonexistent files."""
        mock_check_call.return_value = None
        mock_check_output.return_value = "file1.py\nfile2.js\nfile3.txt\n"
        mock_exists.side_effect = [True, False, True]

        result = _git_changed_files("base", "head")
        assert result == ["file1.py", "file3.txt"]

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_called_process_error(
        self, mock_check_output, mock_check_call
    ):
        """Test git diff with CalledProcessError."""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "git")

        result = _git_changed_files("base", "head")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_file_not_found_error(
        self, mock_check_output, mock_check_call
    ):
        """Test git diff with FileNotFoundError."""
        mock_check_call.side_effect = FileNotFoundError("Git not found")

        result = _git_changed_files("base", "head")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_base_ref_invalid(
        self, mock_check_output, mock_check_call
    ):
        """Test git diff with invalid base ref."""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "git")

        result = _git_changed_files("invalid_base", "head")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_head_ref_invalid(
        self, mock_check_output, mock_check_call
    ):
        """Test git diff with invalid head ref."""
        mock_check_call.side_effect = [None, subprocess.CalledProcessError(1, "git")]

        result = _git_changed_files("base", "invalid_head")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_changed_files_with_empty_output(
        self, mock_exists, mock_check_output, mock_check_call
    ):
        """Test git diff with empty output."""
        mock_check_call.return_value = None
        mock_check_output.return_value = ""
        mock_exists.return_value = True

        result = _git_changed_files("base", "head")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_changed_files_with_whitespace_lines(
        self, mock_exists, mock_check_output, mock_check_call
    ):
        """Test git diff with whitespace-only lines."""
        mock_check_call.return_value = None
        mock_check_output.return_value = "file1.py\n   \nfile2.js\n\t\nfile3.txt\n"
        mock_exists.return_value = True

        result = _git_changed_files("base", "head")
        assert result == ["file1.py", "file2.js", "file3.txt"]


class TestParseGithubEvent:
    """Test parse_github_event function comprehensively."""

    def test_parse_github_event_nonexistent_file(self):
        """Test parsing nonexistent event file."""
        result = parse_github_event("nonexistent.json")
        assert result == {}

    def test_parse_github_event_valid_file(self):
        """Test parsing valid event file."""
        event_data = {
            "pull_request": {
                "head": {"ref": "feature"},
                "base": {"ref": "main"},
                "number": 123,
            },
            "repository": {"name": "test-repo", "full_name": "user/test-repo"},
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            result = parse_github_event("test.json")
            assert result is not None
            assert result["pull_request"]["number"] == 123
            assert result["repository"]["name"] == "test-repo"

    def test_parse_github_event_invalid_json(self):
        """Test parsing invalid JSON file."""
        with patch("builtins.open", mock_open(read_data="invalid json content")):
            result = parse_github_event("test.json")
            assert result == {}

    def test_parse_github_event_empty_file(self):
        """Test parsing empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            result = parse_github_event("test.json")
            assert result == {}

    def test_parse_github_event_encoding_error(self):
        """Test parsing file with encoding error."""
        # Test with a file that doesn't exist (FileNotFoundError)
        result = parse_github_event("nonexistent_file.json")
        assert result == {}

    def test_parse_github_event_with_io_error(self):
        """Test parsing file with IO error."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                parse_github_event("test.json")

    def test_parse_github_event_with_unicode_error(self):
        """Test parsing file with unicode error."""
        with patch(
            "builtins.open",
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
        ):
            with pytest.raises(UnicodeDecodeError):
                parse_github_event("test.json")


class TestGetBaseHeadFromEvent:
    """Test _get_base_head_from_event function comprehensively."""

    def test_get_base_head_nonexistent_file(self):
        """Test getting base/head from nonexistent file."""
        result = _get_base_head_from_event("nonexistent.json")
        assert result is None

    def test_get_base_head_valid_pull_request(self):
        """Test getting base/head from valid pull request event."""
        event_data = {
            "pull_request": {"head": {"sha": "head-sha"}, "base": {"sha": "base-sha"}}
        }

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result == ("base-sha", "head-sha")

    def test_get_base_head_push_event(self):
        """Test getting base/head from push event."""
        event_data = {
            "ref": "refs/heads/main",
            "before": "old-commit",
            "after": "new-commit",
        }

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result == ("old-commit", "new-commit")

    def test_get_base_head_workflow_dispatch_event(self):
        """Test getting base/head from workflow_dispatch event."""
        event_data = {"event_name": "workflow_dispatch"}

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_invalid_event(self):
        """Test getting base/head from invalid event."""
        event_data = {"some": "other", "data": "here"}

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_invalid_pull_request_structure(self):
        """Test getting base/head from invalid pull request structure."""
        event_data = {"pull_request": {"head": "invalid", "base": "invalid"}}

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_missing_sha_fields(self):
        """Test getting base/head with missing sha fields."""
        event_data = {
            "pull_request": {"head": {"ref": "feature"}, "base": {"ref": "main"}}
        }

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_invalid_sha_types(self):
        """Test getting base/head with invalid sha types."""
        event_data = {"pull_request": {"head": {"sha": 123}, "base": {"sha": 456}}}

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_empty_event(self):
        """Test getting base/head from empty event."""
        event_data = {}

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_push_event_invalid_types(self):
        """Test getting base/head from push event with invalid types."""
        event_data = {"before": 123, "after": 456}

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None

    def test_get_base_head_push_event_missing_fields(self):
        """Test getting base/head from push event with missing fields."""
        event_data = {
            "before": "old-commit"
            # missing "after"
        }

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            result = _get_base_head_from_event("test.json")
            assert result is None


class TestChangedPythonFiles:
    """Test changed_python_files function comprehensively."""

    def test_changed_python_files_with_list(self):
        """Test getting changed files with file list."""
        files = ["test1.py", "test2.py", "test3.js"]
        result = changed_python_files(files)
        assert result == ["test1.py", "test2.py"]

    def test_changed_python_files_with_none(self):
        """Test getting changed files with None."""
        with patch(
            "src.ai_guard.diff_parser._git_ls_files",
            return_value=["test.py", "test.js"],
        ):
            result = changed_python_files(None)
            assert result == ["test.py"]

    def test_changed_python_files_with_valid_event(self):
        """Test getting changed files with valid event."""
        event_data = {
            "pull_request": {"head": {"sha": "head-sha"}, "base": {"sha": "base-sha"}}
        }

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value=event_data
        ):
            with patch(
                "src.ai_guard.diff_parser._get_base_head_from_event",
                return_value=("base-sha", "head-sha"),
            ):
                with patch(
                    "src.ai_guard.diff_parser._git_changed_files",
                    return_value=["test.py", "test.js"],
                ):
                    result = changed_python_files("test.json")
                    assert result == ["test.py"]

    def test_changed_python_files_with_invalid_event(self):
        """Test getting changed files with invalid event."""
        with patch("src.ai_guard.diff_parser.parse_github_event", return_value={}):
            with patch(
                "src.ai_guard.diff_parser._git_ls_files",
                return_value=["test.py", "test.js"],
            ):
                result = changed_python_files("test.json")
                assert result == ["test.py"]

    def test_changed_python_files_with_git_error(self):
        """Test getting changed files with git error."""
        with patch(
            "src.ai_guard.diff_parser._git_ls_files", side_effect=Exception("Git error")
        ):
            result = changed_python_files()
            assert result == []

    def test_changed_python_files_with_event_parsing_error(self):
        """Test getting changed files with event parsing error."""
        with patch(
            "src.ai_guard.diff_parser.parse_github_event",
            side_effect=Exception("Parse error"),
        ):
            with patch(
                "src.ai_guard.diff_parser._git_ls_files",
                return_value=["test.py", "test.js"],
            ):
                result = changed_python_files("test.json")
                assert result == ["test.py"]

    def test_changed_python_files_with_empty_git_result(self):
        """Test getting changed files with empty git result."""
        with patch("src.ai_guard.diff_parser._git_changed_files", return_value=[]):
            with patch("src.ai_guard.diff_parser._git_ls_files", return_value=[]):
                result = changed_python_files("event.json")
                assert result == []

    def test_changed_python_files_with_none_base_head(self):
        """Test getting changed files with None base/head."""
        with patch(
            "src.ai_guard.diff_parser._get_base_head_from_event", return_value=None
        ):
            with patch(
                "src.ai_guard.diff_parser._git_ls_files",
                return_value=["test.py", "test.js"],
            ):
                result = changed_python_files("event.json")
                assert result == ["test.py"]

    def test_changed_python_files_with_list_containing_none(self):
        """Test getting changed files with list containing None values."""
        files = ["test1.py", None, "test2.py", "test3.js"]
        result = changed_python_files(files)
        assert result == ["test1.py", "test2.py"]

    def test_changed_python_files_with_empty_strings(self):
        """Test getting changed files with empty strings."""
        files = ["test1.py", "", "test2.py", "test3.js"]
        result = changed_python_files(files)
        assert result == ["test1.py", "test2.py"]


class TestDiffParser:
    """Test DiffParser class comprehensively."""

    def test_diff_parser_init(self):
        """Test DiffParser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_parse_changed_files_no_event(self):
        """Test parsing changed files without event."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = parser.parse_changed_files()
            assert result == ["test.py"]
            mock_func.assert_called_once_with(None)

    def test_parse_changed_files_with_event(self):
        """Test parsing changed files with event."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = parser.parse_changed_files("event.json")
            assert result == ["test.py"]
            mock_func.assert_called_once_with("event.json")

    def test_parse_github_event(self):
        """Test parsing GitHub event."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value={"test": "data"}
        ) as mock_func:
            result = parser.parse_github_event("event.json")
            assert result == {"test": "data"}
            mock_func.assert_called_once_with("event.json")

    def test_get_file_extensions(self):
        """Test getting file extensions."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.get_file_extensions", return_value=["py", "js"]
        ) as mock_func:
            result = parser.get_file_extensions(["test.py", "test.js"])
            assert result == ["py", "js"]
            mock_func.assert_called_once_with(["test.py", "test.js"])

    def test_filter_python_files(self):
        """Test filtering Python files."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.filter_python_files", return_value=["test.py"]
        ) as mock_func:
            result = parser.filter_python_files(["test.py", "test.js"])
            assert result == ["test.py"]
            mock_func.assert_called_once_with(["test.py", "test.js"])


class TestParseDiff:
    """Test parse_diff function comprehensively."""

    def test_parse_diff_none(self):
        """Test parsing diff with None content."""
        result = parse_diff(None)
        assert result == []

    def test_parse_diff_empty(self):
        """Test parsing diff with empty content."""
        result = parse_diff("")
        assert result == []

    def test_parse_diff_valid(self):
        """Test parsing diff with valid content."""
        diff_content = """--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old
+new
"""
        result = parse_diff(diff_content)
        assert isinstance(result, list)

    def test_parse_diff_multiple_files(self):
        """Test parsing diff with multiple files."""
        diff_content = """--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-change1
+change1_new

--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-change2
+change2_new
"""
        result = parse_diff(diff_content)
        assert isinstance(result, list)


class TestGetChangedFiles:
    """Test get_changed_files function comprehensively."""

    def test_get_changed_files_no_event(self):
        """Test getting changed files without event."""
        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = get_changed_files()
            assert result == ["test.py"]
            mock_func.assert_called_once_with(None)

    def test_get_changed_files_with_event(self):
        """Test getting changed files with event."""
        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = get_changed_files("event.json")
            assert result == ["test.py"]
            mock_func.assert_called_once_with("event.json")


class TestDiffParserIntegration:
    """Integration tests for DiffParser."""

    def test_full_workflow(self):
        """Test full workflow from event to file list."""
        parser = DiffParser()

        # Mock the git command
        with patch(
            "src.ai_guard.diff_parser._git_changed_files",
            return_value=["test.py", "test.js"],
        ):
            # Test the full workflow
            changed_files = parser.parse_changed_files("event.json")
            assert isinstance(changed_files, list)

            # Test filtering
            python_files = parser.filter_python_files(changed_files)
            assert isinstance(python_files, list)

            # Test getting extensions
            extensions = parser.get_file_extensions(python_files)
            assert isinstance(extensions, list)

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        parser = DiffParser()

        # Test with invalid event file
        with patch("src.ai_guard.diff_parser.changed_python_files", return_value=[]):
            result = parser.parse_changed_files("nonexistent.json")
            assert result == []

        # Test with invalid JSON
        with patch("src.ai_guard.diff_parser.parse_github_event", return_value={}):
            result = parser.parse_github_event("test.json")
            assert result == {}


if __name__ == "__main__":
    pytest.main([__file__])
