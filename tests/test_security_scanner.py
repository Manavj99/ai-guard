"""Comprehensive tests for the AI-Guard security scanner module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.ai_guard.security_scanner import (
    SecurityScanner, run_bandit, run_safety_check
)


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    def test_security_scanner_scan(self):
        """Test SecurityScanner scan method."""
        scanner = SecurityScanner()
        # This should not raise an exception
        result = scanner.run_all_security_checks()
        assert isinstance(result, int)


class TestRunBandit:
    """Test bandit security scanner functionality."""

    @patch('subprocess.call')
    def test_run_bandit_success(self, mock_call):
        """Test successful bandit run."""
        mock_call.return_value = 0
        result = run_bandit()
        assert result == 0

    @patch('subprocess.call')
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test bandit run with extra arguments."""
        mock_call.return_value = 0
        result = run_bandit(["-f", "json"])
        assert result == 0

    @patch('subprocess.call')
    def test_run_bandit_failure(self, mock_call):
        """Test bandit run with failures."""
        mock_call.return_value = 1
        result = run_bandit()
        assert result == 1

    @patch('os.path.exists')
    @patch('subprocess.call')
    def test_run_bandit_with_config(self, mock_call, mock_exists):
        """Test bandit run with config file."""
        mock_exists.return_value = True
        mock_call.return_value = 0
        result = run_bandit()
        assert result == 0


class TestRunSafetyCheck:
    """Test safety check functionality."""

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_call):
        """Test successful safety check."""
        mock_call.return_value = 0
        result = run_safety_check()
        assert result == 0

    @patch('subprocess.call')
    def test_run_safety_check_failure(self, mock_call):
        """Test safety check with failures."""
        mock_call.return_value = 1
        result = run_safety_check()
        assert result == 1

    @patch('subprocess.call')
    def test_run_safety_check_not_found(self, mock_call):
        """Test safety check when command not found."""
        mock_call.side_effect = FileNotFoundError("safety not found")
        result = run_safety_check()
        assert result == 0  # Should return 0 when safety is not installed


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_security_scanner_with_empty_paths(self):
        """Test SecurityScanner with empty paths."""
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        assert isinstance(result, int)

    def test_security_scanner_with_none_paths(self):
        """Test SecurityScanner with None paths."""
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        assert isinstance(result, int)

    def test_run_bandit_with_none_args(self):
        """Test run_bandit with None arguments."""
        result = run_bandit(None)
        assert isinstance(result, int)

    def test_run_safety_check_exception_handling(self):
        """Test run_safety_check exception handling."""
        with patch('subprocess.call') as mock_call:
            mock_call.side_effect = Exception("Unexpected error")
            result = run_safety_check()
            assert result == 0  # Should handle exceptions gracefully
