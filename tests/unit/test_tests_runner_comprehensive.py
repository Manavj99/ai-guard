"""Comprehensive tests for tests runner module."""

import sys
from unittest.mock import patch

from ai_guard.tests_runner import run_pytest, run_pytest_with_coverage


class TestTestsRunnerComprehensive:
    """Comprehensive tests for tests runner functionality."""

    def test_run_pytest_success(self):
        """Test successful pytest run."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 0

            result = run_pytest()

            assert result == 0
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert sys.executable in call_args
            assert "-m" in call_args
            assert "pytest" in call_args
            assert "-q" in call_args

    def test_run_pytest_with_extra_args(self):
        """Test pytest run with extra arguments."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 1

            result = run_pytest(["-v", "--tb=short"])

            assert result == 1
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "-v" in call_args
            assert "--tb=short" in call_args

    def test_run_pytest_with_coverage(self):
        """Test pytest run with coverage."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 0

            result = run_pytest_with_coverage()

            assert result == 0
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "--cov=src" in call_args
            assert "--cov-report=xml" in call_args

    def test_run_pytest_with_coverage_failure(self):
        """Test pytest run with coverage when tests fail."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 1

            result = run_pytest_with_coverage()

            assert result == 1
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "--cov=src" in call_args
            assert "--cov-report=xml" in call_args

    def test_run_pytest_no_extra_args(self):
        """Test pytest run with no extra arguments."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 0

            result = run_pytest(None)

            assert result == 0
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "-q" in call_args
            # Should not have extra args beyond the base command
            assert len(call_args) == 4  # python, -m, pytest, -q
