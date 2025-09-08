"""Unit tests for diff parser."""

import pytest  # noqa: F401
from unittest.mock import patch, Mock, mock_open  # noqa: F401
import json
import subprocess  # noqa: F401
from ai_guard.diff_parser import (
    changed_python_files,
    _get_base_head_from_event,
    _git_changed_files,
    parse_github_event,
)


class TestDiffParser:
    """Test diff parser functionality."""

    def test_parse_github_event_valid(self):
        """Test parsing valid GitHub event JSON."""
        event_data = {
            "pull_request": {"base": {"sha": "base123"}, "head": {"sha": "head456"}}
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            result = parse_github_event("dummy_path")
            assert result == event_data

    def test_parse_github_event_file_not_found(self):
        """Test parsing GitHub event when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = parse_github_event("nonexistent_path")
            assert result == {}

    def test_parse_github_event_invalid_json(self):
        """Test parsing GitHub event with invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("json.load", side_effect=json.JSONDecodeError("", "", 0)):
                result = parse_github_event("dummy_path")
                assert result == {}

    def test_get_base_head_from_event_pull_request(self):
        """Test extracting base/head from pull request event."""
        event_data = {
            "pull_request": {"base": {"sha": "base123"}, "head": {"sha": "head456"}}
        }

        # Mock parse_github_event to return our test data
        with patch("ai_guard.diff_parser.parse_github_event", return_value=event_data):
            result = _get_base_head_from_event("dummy_path")
            assert result == ("base123", "head456")

    def test_get_base_head_from_event_push(self):
        """Test extracting base/head from push event."""
        event_data = {"before": "before123", "after": "after456"}

        with patch("ai_guard.diff_parser.parse_github_event", return_value=event_data):
            result = _get_base_head_from_event("dummy_path")
            assert result == ("before123", "after456")

    def test_get_base_head_from_event_workflow_dispatch(self):
        """Test handling workflow_dispatch event."""
        event_data = {"event_name": "workflow_dispatch"}

        with patch("ai_guard.diff_parser.parse_github_event", return_value=event_data):
            result = _get_base_head_from_event("dummy_path")
            assert result is None

    def test_get_base_head_from_event_invalid(self):
        """Test handling invalid event data."""
        event_data = {"invalid": "data"}

        with patch("ai_guard.diff_parser.parse_github_event", return_value=event_data):
            result = _get_base_head_from_event("dummy_path")
            assert result is None

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_success(self, mock_output, mock_check):
        """Test successful Git diff operation."""
        mock_check.return_value = 0
        mock_output.return_value = "file1.py\nfile2.py\n"

        result = _git_changed_files("base123", "head456")

        assert result == ["file1.py", "file2.py"]
        assert mock_check.call_count == 2  # Two rev-parse calls

    @patch("subprocess.check_call")
    def test_git_changed_files_invalid_refs(self, mock_check):
        """Test Git diff with invalid references."""
        mock_check.side_effect = subprocess.CalledProcessError(1, "git")

        result = _git_changed_files("invalid", "invalid")
        assert result == []

    @patch("subprocess.check_call")
    @patch("subprocess.check_output")
    def test_git_changed_files_diff_fails(self, mock_output, mock_check):
        """Test Git diff when diff command fails."""
        mock_check.return_value = 0
        mock_output.side_effect = subprocess.CalledProcessError(1, "git")

        result = _git_changed_files("base123", "head456")
        assert result == []

    @patch("subprocess.check_output")
    def test_git_ls_files_success(self, mock_output):
        """Test successful git ls-files operation."""
        mock_output.return_value = "file1.py\nfile2.py\nfile3.txt\n"

        with patch("ai_guard.diff_parser._git_ls_files") as mock_ls:
            mock_ls.return_value = ["file1.py", "file2.py", "file3.txt"]
            result = changed_python_files()
            assert result == ["file1.py", "file2.py"]

    def test_changed_python_files_with_event_success(self):
        """Test changed_python_files with successful event parsing."""
        with patch("ai_guard.diff_parser._get_base_head_from_event") as mock_get:
            mock_get.return_value = ("base123", "head456")
            with patch("ai_guard.diff_parser._git_changed_files") as mock_diff:
                mock_diff.return_value = ["file1.py", "file2.py"]

                result = changed_python_files("event_path")
                assert result == ["file1.py", "file2.py"]

    def test_changed_python_files_with_event_failure(self):
        """Test changed_python_files when event parsing fails."""
        with patch("ai_guard.diff_parser._get_base_head_from_event") as mock_get:
            mock_get.return_value = None

            with patch("ai_guard.diff_parser._git_ls_files") as mock_ls:
                mock_ls.return_value = ["file1.py", "file2.py"]

                result = changed_python_files("event_path")
                assert result == ["file1.py", "file2.py"]

    def test_changed_python_files_exception_handling(self):
        """Test changed_python_files exception handling."""
        with patch(
            "ai_guard.diff_parser._get_base_head_from_event",
            side_effect=Exception("Test error"),
        ):
            with patch("ai_guard.diff_parser._git_ls_files") as mock_ls:
                mock_ls.return_value = ["file1.py", "file2.py"]

                result = changed_python_files("event_path")
                assert result == ["file1.py", "file2.py"]
