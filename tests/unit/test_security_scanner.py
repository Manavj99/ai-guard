"""Tests for security scanner module."""

import pytest
from unittest.mock import patch, Mock
from src.ai_guard.security_scanner import run_bandit, run_safety_check


class TestSecurityScanner:
    """Test security scanner functionality."""

    @patch('subprocess.call')
    def test_run_bandit_basic(self, mock_call):
        """Test basic bandit execution."""
        mock_call.return_value = 0
        
        result = run_bandit()
        
        mock_call.assert_called_once_with(["bandit", "-r", "src", "-c", ".bandit"])
        assert result == 0

    @patch('subprocess.call')
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test bandit execution with extra arguments."""
        mock_call.return_value = 0
        extra_args = ["--verbose", "--exclude", "tests"]
        
        result = run_bandit(extra_args)
        
        expected_cmd = ["bandit", "-r", "src", "-c", ".bandit", "--verbose", "--exclude", "tests"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_call):
        """Test successful safety check execution."""
        mock_call.return_value = 0
        
        result = run_safety_check()
        
        mock_call.assert_called_once_with(["safety", "check"])
        assert result == 0

    @patch('subprocess.call')
    def test_run_safety_check_not_found(self, mock_call):
        """Test safety check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError("safety: command not found")
        
        result = run_safety_check()
        
        assert result == 0
