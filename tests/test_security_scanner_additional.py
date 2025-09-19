"""Additional tests for security scanner to increase coverage."""

import pytest
import subprocess
import os
from unittest.mock import patch, MagicMock
from ai_guard.security_scanner import (
    run_bandit,
    run_safety_check,
    SecurityScanner
)


class TestBandit:
    """Test bandit security scanner functions."""

    @patch('subprocess.call')
    def test_run_bandit_success(self, mock_call):
        """Test successful bandit run."""
        mock_call.return_value = 0
        
        result = run_bandit()
        
        assert result == 0
        mock_call.assert_called_once()

    @patch('subprocess.call')
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test bandit run with extra arguments."""
        mock_call.return_value = 0
        extra_args = ["-f", "json"]
        
        result = run_bandit(extra_args)
        
        assert result == 0
        mock_call.assert_called_once()
        
        # Check that extra args were included
        call_args = mock_call.call_args[0][0]
        assert "-f" in call_args
        assert "json" in call_args

    @patch('os.path.exists')
    @patch('subprocess.call')
    def test_run_bandit_with_config_file(self, mock_call, mock_exists):
        """Test bandit run with config file."""
        mock_exists.return_value = True
        mock_call.return_value = 0
        
        result = run_bandit()
        
        assert result == 0
        mock_exists.assert_called_once_with(".bandit")
        
        # Check that config file was included
        call_args = mock_call.call_args[0][0]
        assert "-c" in call_args
        assert ".bandit" in call_args

    @patch('os.path.exists')
    @patch('subprocess.call')
    def test_run_bandit_without_config_file(self, mock_call, mock_exists):
        """Test bandit run without config file."""
        mock_exists.return_value = False
        mock_call.return_value = 0
        
        result = run_bandit()
        
        assert result == 0
        mock_exists.assert_called_once_with(".bandit")
        
        # Check that default settings were used
        call_args = mock_call.call_args[0][0]
        assert "-f" in call_args
        assert "json" in call_args
        assert "-ll" in call_args

    @patch('subprocess.call')
    def test_run_bandit_failure(self, mock_call):
        """Test bandit run with failure."""
        mock_call.return_value = 1
        
        result = run_bandit()
        
        assert result == 1

    @patch('subprocess.call')
    def test_run_bandit_with_multiple_extra_args(self, mock_call):
        """Test bandit run with multiple extra arguments."""
        mock_call.return_value = 0
        extra_args = ["-f", "json", "-ll", "-r", "src"]
        
        result = run_bandit(extra_args)
        
        assert result == 0
        call_args = mock_call.call_args[0][0]
        assert "-f" in call_args
        assert "json" in call_args
        assert "-ll" in call_args
        assert "-r" in call_args
        assert "src" in call_args


class TestSafetyCheck:
    """Test safety check functions."""

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_call):
        """Test successful safety check."""
        mock_call.return_value = 0
        
        result = run_safety_check()
        
        assert result == 0
        mock_call.assert_called_once_with(["safety", "check"])

    @patch('subprocess.call')
    def test_run_safety_check_failure(self, mock_call):
        """Test safety check with failure."""
        mock_call.return_value = 1
        
        result = run_safety_check()
        
        assert result == 1

    @patch('subprocess.call')
    def test_run_safety_check_file_not_found(self, mock_call):
        """Test safety check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError()
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
        
        assert result == 0
        mock_print.assert_called_once_with("Warning: safety not installed, skipping dependency security check")

    @patch('subprocess.call')
    def test_run_safety_check_generic_exception(self, mock_call):
        """Test safety check with generic exception."""
        mock_call.side_effect = Exception("Generic error")
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
        
        assert result == 0
        mock_print.assert_called_once_with("Warning: Error running safety check: Generic error")

    @patch('subprocess.call')
    def test_run_safety_check_value_error(self, mock_call):
        """Test safety check with ValueError."""
        mock_call.side_effect = ValueError("Value error")
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
        
        assert result == 0
        mock_print.assert_called_once_with("Warning: Error running safety check: Value error")


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        
        assert scanner is not None

    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_bandit_scan(self, mock_run_bandit):
        """Test running bandit scan through scanner."""
        mock_run_bandit.return_value = 0
        
        scanner = SecurityScanner()
        result = scanner.run_bandit_scan()
        
        assert result == 0
        mock_run_bandit.assert_called_once()

    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_bandit_scan_with_args(self, mock_run_bandit):
        """Test running bandit scan with extra arguments."""
        mock_run_bandit.return_value = 0
        extra_args = ["-f", "json"]
        
        scanner = SecurityScanner()
        result = scanner.run_bandit_scan(extra_args)
        
        assert result == 0
        mock_run_bandit.assert_called_once_with(extra_args)

    @patch('ai_guard.security_scanner.run_safety_check')
    def test_run_safety_scan(self, mock_run_safety):
        """Test running safety scan through scanner."""
        mock_run_safety.return_value = 0
        
        scanner = SecurityScanner()
        result = scanner.run_safety_scan()
        
        assert result == 0
        mock_run_safety.assert_called_once()

    @patch('ai_guard.security_scanner.run_safety_check')
    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_both_pass(self, mock_run_bandit, mock_run_safety):
        """Test running all security checks when both pass."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 0
        
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        
        assert result == 0
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('ai_guard.security_scanner.run_safety_check')
    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_bandit_fails(self, mock_run_bandit, mock_run_safety):
        """Test running all security checks when bandit fails."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 0
        
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        
        assert result == 1
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('ai_guard.security_scanner.run_safety_check')
    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_safety_fails(self, mock_run_bandit, mock_run_safety):
        """Test running all security checks when safety fails."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 1
        
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        
        assert result == 1
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('ai_guard.security_scanner.run_safety_check')
    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_both_fail(self, mock_run_bandit, mock_run_safety):
        """Test running all security checks when both fail."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 1
        
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        
        assert result == 1
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('ai_guard.security_scanner.run_safety_check')
    @patch('ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_bandit_fails_safety_not_installed(self, mock_run_bandit, mock_run_safety):
        """Test running all security checks when bandit fails and safety is not installed."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 0  # Safety returns 0 when not installed
        
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        
        assert result == 1
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('subprocess.call')
    def test_run_bandit_with_empty_extra_args(self, mock_call):
        """Test bandit run with empty extra arguments."""
        mock_call.return_value = 0
        extra_args = []
        
        result = run_bandit(extra_args)
        
        assert result == 0
        mock_call.assert_called_once()

    @patch('subprocess.call')
    def test_run_bandit_with_none_extra_args(self, mock_call):
        """Test bandit run with None extra arguments."""
        mock_call.return_value = 0
        
        result = run_bandit(None)
        
        assert result == 0
        mock_call.assert_called_once()

    @patch('subprocess.call')
    def test_run_bandit_subprocess_error(self, mock_call):
        """Test bandit run with subprocess error."""
        mock_call.side_effect = subprocess.CalledProcessError(1, "bandit")
        
        with pytest.raises(subprocess.CalledProcessError):
            run_bandit()

    @patch('subprocess.call')
    def test_run_safety_check_subprocess_error(self, mock_call):
        """Test safety check with subprocess error."""
        mock_call.side_effect = subprocess.CalledProcessError(1, "safety")
        
        with pytest.raises(subprocess.CalledProcessError):
            run_safety_check()

    def test_security_scanner_multiple_instances(self):
        """Test creating multiple SecurityScanner instances."""
        scanner1 = SecurityScanner()
        scanner2 = SecurityScanner()
        
        assert scanner1 is not None
        assert scanner2 is not None
        assert scanner1 is not scanner2

    @patch('ai_guard.security_scanner.run_bandit')
    def test_security_scanner_bandit_scan_multiple_calls(self, mock_run_bandit):
        """Test multiple calls to bandit scan."""
        mock_run_bandit.return_value = 0
        
        scanner = SecurityScanner()
        
        result1 = scanner.run_bandit_scan()
        result2 = scanner.run_bandit_scan()
        
        assert result1 == 0
        assert result2 == 0
        assert mock_run_bandit.call_count == 2

    @patch('ai_guard.security_scanner.run_safety_check')
    def test_security_scanner_safety_scan_multiple_calls(self, mock_run_safety):
        """Test multiple calls to safety scan."""
        mock_run_safety.return_value = 0
        
        scanner = SecurityScanner()
        
        result1 = scanner.run_safety_scan()
        result2 = scanner.run_safety_scan()
        
        assert result1 == 0
        assert result2 == 0
        assert mock_run_safety.call_count == 2

    @patch('ai_guard.security_scanner.run_safety_check')
    @patch('ai_guard.security_scanner.run_bandit')
    def test_security_scanner_all_checks_multiple_calls(self, mock_run_bandit, mock_run_safety):
        """Test multiple calls to all security checks."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 0
        
        scanner = SecurityScanner()
        
        result1 = scanner.run_all_security_checks()
        result2 = scanner.run_all_security_checks()
        
        assert result1 == 0
        assert result2 == 0
        assert mock_run_bandit.call_count == 2
        assert mock_run_safety.call_count == 2
