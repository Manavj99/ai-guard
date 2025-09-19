"""Comprehensive tests for diff_parser.py module."""

import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock
import pytest

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
        files = ["test.py", "script.js", "data.json", "readme.txt"]
        result = get_file_extensions(files)
        assert set(result) == {"py", "js", "json", "txt"}

    def test_get_file_extensions_no_extension(self):
        """Test with files without extensions."""
        files = ["README", "Makefile", "Dockerfile"]
        result = get_file_extensions(files)
        assert result == []

    def test_get_file_extensions_backup_files(self):
        """Test filtering out backup files."""
        files = ["test.py", "test.py~", "test.py.bak", "test.py.tmp"]
        result = get_file_extensions(files)
        assert result == ["py"]

    def test_get_file_extensions_case_insensitive(self):
        """Test case insensitive extensions."""
        files = ["test.PY", "script.JS", "data.JSON"]
        result = get_file_extensions(files)
        assert set(result) == {"py", "js", "json"}

    def test_get_file_extensions_duplicates(self):
        """Test removing duplicate extensions."""
        files = ["test1.py", "test2.py", "script1.js", "script2.js"]
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

    def test_filter_python_files_mixed_files(self):
        """Test filtering mixed file types."""
        files = ["test.py", "script.js", "data.json", "module.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "module.py"]

    def test_filter_python_files_no_python(self):
        """Test with no Python files."""
        files = ["script.js", "data.json", "readme.txt"]
        result = filter_python_files(files)
        assert result == []

    def test_filter_python_files_all_python(self):
        """Test with all Python files."""
        files = ["test.py", "module.py", "main.py"]
        result = filter_python_files(files)
        assert result == files


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

    def test_parse_diff_output_single_file(self):
        """Test with single file diff."""
        diff = "+++ b/test.py\n--- a/test.py\n+new line"
        result = parse_diff_output(diff)
        assert result == ["test.py"]

    def test_parse_diff_output_multiple_files(self):
        """Test with multiple files diff."""
        diff = """+++ b/test1.py
--- a/test1.py
+new line
+++ b/test2.py
--- a/test2.py
+another line"""
        result = parse_diff_output(diff)
        assert set(result) == {"test1.py", "test2.py"}

    def test_parse_diff_output_duplicate_files(self):
        """Test removing duplicate files."""
        diff = """+++ b/test.py
--- a/test.py
+new line
+++ b/test.py
--- a/test.py
+another line"""
        result = parse_diff_output(diff)
        assert result == ["test.py"]

    def test_parse_diff_output_no_diff_markers(self):
        """Test with no diff markers."""
        diff = "just some text\nno diff markers here"
        result = parse_diff_output(diff)
        assert result == []


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    def test_changed_python_files_list_input(self):
        """Test with list input."""
        files = ["test.py", "script.js", "module.py"]
        result = changed_python_files(files)
        assert result == ["test.py", "module.py"]

    def test_changed_python_files_none_input(self):
        """Test with None input."""
        with patch("src.ai_guard.diff_parser._git_ls_files") as mock_git_ls:
            mock_git_ls.return_value = ["test.py", "script.js"]
            result = changed_python_files(None)
            assert result == ["test.py"]

    def test_changed_python_files_github_event_success(self):
        """Test with successful GitHub event parsing."""
        with patch("src.ai_guard.diff_parser._get_base_head_from_event") as mock_get_base_head:
            with patch("src.ai_guard.diff_parser._git_changed_files") as mock_git_changed:
                mock_get_base_head.return_value = ("base", "head")
                mock_git_changed.return_value = ["test.py", "script.js"]
                
                result = changed_python_files("event.json")
                assert result == ["test.py"]

    def test_changed_python_files_github_event_failure(self):
        """Test with failed GitHub event parsing."""
        with patch("src.ai_guard.diff_parser._get_base_head_from_event") as mock_get_base_head:
            with patch("src.ai_guard.diff_parser._git_ls_files") as mock_git_ls:
                mock_get_base_head.return_value = None
                mock_git_ls.return_value = ["test.py", "script.js"]
                
                result = changed_python_files("event.json")
                assert result == ["test.py"]

    def test_changed_python_files_github_event_exception(self):
        """Test with exception in GitHub event parsing."""
        with patch("src.ai_guard.diff_parser._get_base_head_from_event") as mock_get_base_head:
            with patch("src.ai_guard.diff_parser._git_ls_files") as mock_git_ls:
                mock_get_base_head.side_effect = Exception("Parse error")
                mock_git_ls.return_value = ["test.py", "script.js"]
                
                result = changed_python_files("event.json")
                assert result == ["test.py"]


class TestGitLsFiles:
    """Test _git_ls_files function."""

    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_ls_files_success(self, mock_exists, mock_check_output):
        """Test successful git ls-files execution."""
        mock_check_output.return_value = "test.py\nscript.js\nREADME.md"
        mock_exists.side_effect = lambda x: x in ["test.py", "script.js"]
        
        result = _git_ls_files()
        assert result == ["test.py", "script.js"]

    @patch("subprocess.check_output")
    def test_git_ls_files_empty_output(self, mock_check_output):
        """Test with empty git output."""
        mock_check_output.return_value = ""
        
        result = _git_ls_files()
        assert result == []

    @patch("subprocess.check_output")
    def test_git_ls_files_called_process_error(self, mock_check_output):
        """Test with CalledProcessError."""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")
        
        result = _git_ls_files()
        assert result == []

    @patch("subprocess.check_output")
    def test_git_ls_files_file_not_found(self, mock_check_output):
        """Test with FileNotFoundError."""
        mock_check_output.side_effect = FileNotFoundError("Git not found")
        
        result = _git_ls_files()
        assert result == []


class TestGitChangedFiles:
    """Test _git_changed_files function."""

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    @patch("os.path.exists")
    def test_git_changed_files_success(self, mock_exists, mock_check_output, mock_check_call):
        """Test successful git diff execution."""
        mock_check_call.return_value = None
        mock_check_output.return_value = "test.py\nscript.js\nREADME.md"
        mock_exists.side_effect = lambda x: x in ["test.py", "script.js"]
        
        result = _git_changed_files("base", "head")
        assert result == ["test.py", "script.js"]

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_empty_diff(self, mock_check_output, mock_check_call):
        """Test with empty diff."""
        mock_check_call.return_value = None
        mock_check_output.return_value = ""
        
        result = _git_changed_files("base", "head")
        assert result == []

    @patch("subprocess.check_call")
    def test_git_changed_files_verify_failure(self, mock_check_call):
        """Test with ref verification failure."""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "git")
        
        result = _git_changed_files("base", "head")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_diff_failure(self, mock_check_output, mock_check_call):
        """Test with diff execution failure."""
        mock_check_call.return_value = None
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")
        
        result = _git_changed_files("base", "head")
        assert result == []


class TestParseGithubEvent:
    """Test parse_github_event function."""

    def test_parse_github_event_success(self):
        """Test successful event parsing."""
        event_data = {"pull_request": {"number": 123}}
        
        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            result = parse_github_event("event.json")
            assert result == event_data

    def test_parse_github_event_file_not_found(self):
        """Test with file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = parse_github_event("nonexistent.json")
            assert result == {}

    def test_parse_github_event_invalid_json(self):
        """Test with invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            result = parse_github_event("invalid.json")
            assert result == {}


class TestGetBaseHeadFromEvent:
    """Test _get_base_head_from_event function."""

    def test_get_base_head_from_event_pull_request(self):
        """Test with pull request event."""
        event_data = {
            "pull_request": {
                "base": {"sha": "base_sha"},
                "head": {"sha": "head_sha"}
            }
        }
        
        with patch("src.ai_guard.diff_parser.parse_github_event") as mock_parse:
            mock_parse.return_value = event_data
            
            result = _get_base_head_from_event("event.json")
            assert result == ("base_sha", "head_sha")

    def test_get_base_head_from_event_push(self):
        """Test with push event."""
        event_data = {
            "before": "before_sha",
            "after": "after_sha"
        }
        
        with patch("src.ai_guard.diff_parser.parse_github_event") as mock_parse:
            mock_parse.return_value = event_data
            
            result = _get_base_head_from_event("event.json")
            assert result == ("before_sha", "after_sha")

    def test_get_base_head_from_event_workflow_dispatch(self):
        """Test with workflow dispatch event."""
        event_data = {
            "event_name": "workflow_dispatch"
        }
        
        with patch("src.ai_guard.diff_parser.parse_github_event") as mock_parse:
            mock_parse.return_value = event_data
            
            result = _get_base_head_from_event("event.json")
            assert result is None

    def test_get_base_head_from_event_empty(self):
        """Test with empty event."""
        with patch("src.ai_guard.diff_parser.parse_github_event") as mock_parse:
            mock_parse.return_value = {}
            
            result = _get_base_head_from_event("event.json")
            assert result is None


class TestDiffParser:
    """Test DiffParser class."""

    def test_init(self):
        """Test DiffParser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_parse_changed_files(self):
        """Test parse_changed_files method."""
        parser = DiffParser()
        
        with patch("src.ai_guard.diff_parser.changed_python_files") as mock_changed:
            mock_changed.return_value = ["test.py"]
            
            result = parser.parse_changed_files("event.json")
            assert result == ["test.py"]
            mock_changed.assert_called_once_with("event.json")

    def test_parse_github_event(self):
        """Test parse_github_event method."""
        parser = DiffParser()
        
        with patch("src.ai_guard.diff_parser.parse_github_event") as mock_parse:
            mock_parse.return_value = {"test": "data"}
            
            result = parser.parse_github_event("event.json")
            assert result == {"test": "data"}
            mock_parse.assert_called_once_with("event.json")

    def test_get_file_extensions(self):
        """Test get_file_extensions method."""
        parser = DiffParser()
        
        result = parser.get_file_extensions(["test.py", "script.js"])
        assert result == ["js", "py"]

    def test_filter_python_files(self):
        """Test filter_python_files method."""
        parser = DiffParser()
        
        result = parser.filter_python_files(["test.py", "script.js"])
        assert result == ["test.py"]


class TestParseDiff:
    """Test parse_diff function."""

    def test_parse_diff_success(self):
        """Test successful diff parsing."""
        diff_content = "+++ b/test.py\n--- a/test.py\n+new line"
        
        with patch("src.ai_guard.diff_parser.parse_diff_output") as mock_parse:
            mock_parse.return_value = ["test.py"]
            
            result = parse_diff(diff_content)
            assert result == ["test.py"]
            mock_parse.assert_called_once_with(diff_content)

    def test_parse_diff_none(self):
        """Test with None input."""
        with patch("src.ai_guard.diff_parser.parse_diff_output") as mock_parse:
            mock_parse.return_value = []
            
            result = parse_diff(None)
            assert result == []
            mock_parse.assert_called_once_with(None)


class TestGetChangedFiles:
    """Test get_changed_files function."""

    def test_get_changed_files_success(self):
        """Test successful get_changed_files."""
        with patch("src.ai_guard.diff_parser.changed_python_files") as mock_changed:
            mock_changed.return_value = ["test.py"]
            
            result = get_changed_files("event.json")
            assert result == ["test.py"]
            mock_changed.assert_called_once_with("event.json")

    def test_get_changed_files_none(self):
        """Test with None input."""
        with patch("src.ai_guard.diff_parser.changed_python_files") as mock_changed:
            mock_changed.return_value = []
            
            result = get_changed_files(None)
            assert result == []
            mock_changed.assert_called_once_with(None)


class TestIntegration:
    """Integration tests for diff_parser module."""

    def test_end_to_end_python_file_filtering(self):
        """Test end-to-end Python file filtering."""
        files = ["src/test.py", "docs/readme.md", "tests/test_module.py", "script.js"]
        result = filter_python_files(files)
        assert result == ["src/test.py", "tests/test_module.py"]

    def test_end_to_end_extension_extraction(self):
        """Test end-to-end extension extraction."""
        files = ["test.py", "script.js", "data.json", "config.yaml"]
        result = get_file_extensions(files)
        assert set(result) == {"py", "js", "json", "yaml"}

    def test_end_to_end_diff_parsing(self):
        """Test end-to-end diff parsing."""
        diff = """+++ b/src/test.py
--- a/src/test.py
+def new_function():
+    pass
+++ b/tests/test_module.py
--- a/tests/test_module.py
+def test_new_function():
+    pass"""
        
        result = parse_diff_output(diff)
        assert set(result) == {"src/test.py", "tests/test_module.py"}


if __name__ == "__main__":
    pytest.main([__file__])