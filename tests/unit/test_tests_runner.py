"""Tests for tests runner module."""

import sys
import pytest  # noqa: F401
from unittest.mock import patch, Mock  # noqa: F401
from src.ai_guard.tests_runner import run_pytest, run_pytest_with_coverage


class TestTestsRunner:
    """Test tests runner functionality."""

    @patch('subprocess.call')
    def test_run_pytest_basic(self, mock_call):
        """Test basic pytest execution."""
        mock_call.return_value = 0

        result = run_pytest()

        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert call_args[0] == sys.executable
        assert call_args[1] == "-m"
        assert call_args[2] == "pytest"
        assert call_args[3] == "-q"
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_extra_args(self, mock_call):
        """Test pytest execution with extra arguments."""
        mock_call.return_value = 0
        extra_args = ["--verbose", "--tb=short"]

        result = run_pytest(extra_args)

        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert call_args[0] == sys.executable
        assert call_args[1] == "-m"
        assert call_args[2] == "pytest"
        assert call_args[3] == "-q"
        assert call_args[4:] == ["--verbose", "--tb=short"]
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_coverage(self, mock_call):
        """Test pytest execution with coverage."""
        mock_call.return_value = 0

        result = run_pytest_with_coverage()

        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert call_args[0] == sys.executable
        assert call_args[1] == "-m"
        assert call_args[2] == "pytest"
        assert call_args[3] == "-q"
        assert "--cov=src" in call_args
        assert "--cov-report=xml" in call_args
        assert result == 0
