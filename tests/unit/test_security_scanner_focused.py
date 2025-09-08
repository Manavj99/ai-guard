"""Focused tests for the security_scanner module."""

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os

from src.ai_guard.security_scanner import (
    run_bandit, 
    run_safety_check, 
    SecurityScanner
)


class TestRunBandit(unittest.TestCase):
    """Test the run_bandit function."""

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_with_config(self, mock_exists, mock_call):
        """Test run_bandit with .bandit config file."""
        mock_exists.return_value = True
        mock_call.return_value = 0
        
        result = run_bandit()
        
        mock_call.assert_called_once_with(["bandit", "-r", "src", "-c", ".bandit"])
        self.assertEqual(result, 0)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_without_config(self, mock_exists, mock_call):
        """Test run_bandit without .bandit config file."""
        mock_exists.return_value = False
        mock_call.return_value = 1
        
        result = run_bandit()
        
        mock_call.assert_called_once_with(["bandit", "-r", "src", "-f", "json", "-ll"])
        self.assertEqual(result, 1)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_with_extra_args(self, mock_exists, mock_call):
        """Test run_bandit with extra arguments."""
        mock_exists.return_value = False
        mock_call.return_value = 0
        extra_args = ["-x", "tests/", "-s", "B101"]
        
        result = run_bandit(extra_args)
        
        expected_cmd = ["bandit", "-r", "src", "-f", "json", "-ll", "-x", "tests/", "-s", "B101"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 0)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_with_config_and_extra_args(self, mock_exists, mock_call):
        """Test run_bandit with config file and extra arguments."""
        mock_exists.return_value = True
        mock_call.return_value = 2
        extra_args = ["-x", "tests/"]
        
        result = run_bandit(extra_args)
        
        expected_cmd = ["bandit", "-r", "src", "-c", ".bandit", "-x", "tests/"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 2)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_no_extra_args(self, mock_exists, mock_call):
        """Test run_bandit with None extra_args."""
        mock_exists.return_value = False
        mock_call.return_value = 0
        
        result = run_bandit(None)
        
        mock_call.assert_called_once_with(["bandit", "-r", "src", "-f", "json", "-ll"])
        self.assertEqual(result, 0)


class TestRunSafetyCheck(unittest.TestCase):
    """Test the run_safety_check function."""

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_call):
        """Test run_safety_check with successful execution."""
        mock_call.return_value = 0
        
        result = run_safety_check()
        
        mock_call.assert_called_once_with(["safety", "check"])
        self.assertEqual(result, 0)

    @patch('subprocess.call')
    def test_run_safety_check_failure(self, mock_call):
        """Test run_safety_check with failed execution."""
        mock_call.return_value = 1
        
        result = run_safety_check()
        
        mock_call.assert_called_once_with(["safety", "check"])
        self.assertEqual(result, 1)

    @patch('subprocess.call')
    @patch('builtins.print')
    def test_run_safety_check_not_installed(self, mock_print, mock_call):
        """Test run_safety_check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError("safety not found")
        
        result = run_safety_check()
        
        mock_call.assert_called_once_with(["safety", "check"])
        mock_print.assert_called_once_with("Warning: safety not installed, skipping dependency security check")
        self.assertEqual(result, 0)

    @patch('subprocess.call')
    def test_run_safety_check_vulnerabilities_found(self, mock_call):
        """Test run_safety_check when vulnerabilities are found."""
        mock_call.return_value = 2
        
        result = run_safety_check()
        
        mock_call.assert_called_once_with(["safety", "check"])
        self.assertEqual(result, 2)


class TestSecurityScanner(unittest.TestCase):
    """Test the SecurityScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scanner = SecurityScanner()

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        self.assertIsNotNone(scanner)

    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_bandit_scan(self, mock_run_bandit):
        """Test SecurityScanner.run_bandit_scan method."""
        mock_run_bandit.return_value = 0
        extra_args = ["-x", "tests/"]
        
        result = self.scanner.run_bandit_scan(extra_args)
        
        mock_run_bandit.assert_called_once_with(extra_args)
        self.assertEqual(result, 0)

    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_bandit_scan_no_args(self, mock_run_bandit):
        """Test SecurityScanner.run_bandit_scan method without extra args."""
        mock_run_bandit.return_value = 1
        
        result = self.scanner.run_bandit_scan()
        
        mock_run_bandit.assert_called_once_with(None)
        self.assertEqual(result, 1)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_run_safety_scan(self, mock_run_safety):
        """Test SecurityScanner.run_safety_scan method."""
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_safety_scan()
        
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 0)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_run_safety_scan_failure(self, mock_run_safety):
        """Test SecurityScanner.run_safety_scan method with failure."""
        mock_run_safety.return_value = 1
        
        result = self.scanner.run_safety_scan()
        
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 1)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_both_pass(self, mock_run_bandit, mock_run_safety):
        """Test run_all_security_checks when both checks pass."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_all_security_checks()
        
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 0)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_bandit_fails(self, mock_run_bandit, mock_run_safety):
        """Test run_all_security_checks when bandit fails."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_all_security_checks()
        
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 1)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_safety_fails(self, mock_run_bandit, mock_run_safety):
        """Test run_all_security_checks when safety fails."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 1
        
        result = self.scanner.run_all_security_checks()
        
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 1)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_both_fail(self, mock_run_bandit, mock_run_safety):
        """Test run_all_security_checks when both checks fail."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 1
        
        result = self.scanner.run_all_security_checks()
        
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 1)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_run_all_security_checks_bandit_fails_safety_passes(self, mock_run_bandit, mock_run_safety):
        """Test run_all_security_checks when bandit fails but safety passes."""
        mock_run_bandit.return_value = 2
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_all_security_checks()
        
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()
        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
