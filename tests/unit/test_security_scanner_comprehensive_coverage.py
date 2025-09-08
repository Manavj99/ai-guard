"""Comprehensive tests for security_scanner.py module to achieve high coverage."""

import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import os

from src.ai_guard.security_scanner import (
    run_bandit,
    run_safety_check,
    SecurityScanner
)


class TestSecurityScannerComprehensive(unittest.TestCase):
    """Comprehensive tests for security_scanner module."""

    def setUp(self):
        """Set up test fixtures."""
        self.scanner = SecurityScanner()

    @patch('subprocess.call')
    def test_run_bandit_basic(self, mock_call):
        """Test running bandit with basic configuration."""
        mock_call.return_value = 0
        
        result = run_bandit()
        
        self.assertEqual(result, 0)
        mock_call.assert_called_once()
        
        # Check the command structure
        call_args = mock_call.call_args[0][0]
        self.assertIn("bandit", call_args)
        self.assertIn("-r", call_args)
        self.assertIn("src", call_args)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_with_config(self, mock_exists, mock_call):
        """Test running bandit with existing config file."""
        mock_exists.return_value = True
        mock_call.return_value = 0
        
        result = run_bandit()
        
        self.assertEqual(result, 0)
        mock_call.assert_called_once()
        
        # Check that config file is included
        call_args = mock_call.call_args[0][0]
        self.assertIn("-c", call_args)
        self.assertIn(".bandit", call_args)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_without_config(self, mock_exists, mock_call):
        """Test running bandit without config file."""
        mock_exists.return_value = False
        mock_call.return_value = 0
        
        result = run_bandit()
        
        self.assertEqual(result, 0)
        mock_call.assert_called_once()
        
        # Check that default settings are used
        call_args = mock_call.call_args[0][0]
        self.assertIn("-f", call_args)
        self.assertIn("json", call_args)
        self.assertIn("-ll", call_args)

    @patch('subprocess.call')
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test running bandit with extra arguments."""
        mock_call.return_value = 0
        extra_args = ["-x", "tests/", "-s", "B101"]
        
        result = run_bandit(extra_args)
        
        self.assertEqual(result, 0)
        mock_call.assert_called_once()
        
        # Check that extra args are included
        call_args = mock_call.call_args[0][0]
        self.assertIn("-x", call_args)
        self.assertIn("tests/", call_args)
        self.assertIn("-s", call_args)
        self.assertIn("B101", call_args)

    @patch('subprocess.call')
    def test_run_bandit_failure(self, mock_call):
        """Test running bandit when it fails."""
        mock_call.return_value = 1
        
        result = run_bandit()
        
        self.assertEqual(result, 1)

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_call):
        """Test running safety check successfully."""
        mock_call.return_value = 0
        
        result = run_safety_check()
        
        self.assertEqual(result, 0)
        mock_call.assert_called_once_with(["safety", "check"])

    @patch('subprocess.call')
    def test_run_safety_check_failure(self, mock_call):
        """Test running safety check when it fails."""
        mock_call.return_value = 1
        
        result = run_safety_check()
        
        self.assertEqual(result, 1)

    @patch('subprocess.call')
    def test_run_safety_check_not_installed(self, mock_call):
        """Test running safety check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError("safety not found")
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
        
        self.assertEqual(result, 0)
        mock_print.assert_called_once_with(
            "Warning: safety not installed, skipping dependency security check"
        )

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        self.assertIsInstance(scanner, SecurityScanner)

    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_security_scanner_run_bandit_scan(self, mock_run_bandit):
        """Test SecurityScanner run_bandit_scan method."""
        mock_run_bandit.return_value = 0
        
        result = self.scanner.run_bandit_scan()
        
        self.assertEqual(result, 0)
        mock_run_bandit.assert_called_once_with(None)

    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_security_scanner_run_bandit_scan_with_args(self, mock_run_bandit):
        """Test SecurityScanner run_bandit_scan method with extra args."""
        mock_run_bandit.return_value = 0
        extra_args = ["-x", "tests/"]
        
        result = self.scanner.run_bandit_scan(extra_args)
        
        self.assertEqual(result, 0)
        mock_run_bandit.assert_called_once_with(extra_args)

    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_security_scanner_run_safety_scan(self, mock_run_safety):
        """Test SecurityScanner run_safety_scan method."""
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_safety_scan()
        
        self.assertEqual(result, 0)
        mock_run_safety.assert_called_once()

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_security_scanner_run_all_security_checks_success(self, mock_run_bandit, mock_run_safety):
        """Test SecurityScanner run_all_security_checks when all checks pass."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_all_security_checks()
        
        self.assertEqual(result, 0)
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_security_scanner_run_all_security_checks_bandit_fails(self, mock_run_bandit, mock_run_safety):
        """Test SecurityScanner run_all_security_checks when bandit fails."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 0
        
        result = self.scanner.run_all_security_checks()
        
        self.assertEqual(result, 1)
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_security_scanner_run_all_security_checks_safety_fails(self, mock_run_bandit, mock_run_safety):
        """Test SecurityScanner run_all_security_checks when safety fails."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 1
        
        result = self.scanner.run_all_security_checks()
        
        self.assertEqual(result, 1)
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('src.ai_guard.security_scanner.run_safety_check')
    @patch('src.ai_guard.security_scanner.run_bandit')
    def test_security_scanner_run_all_security_checks_both_fail(self, mock_run_bandit, mock_run_safety):
        """Test SecurityScanner run_all_security_checks when both checks fail."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 1
        
        result = self.scanner.run_all_security_checks()
        
        self.assertEqual(result, 1)
        mock_run_bandit.assert_called_once()
        mock_run_safety.assert_called_once()

    @patch('subprocess.call')
    def test_run_bandit_command_structure(self, mock_call):
        """Test the exact command structure for bandit."""
        mock_call.return_value = 0
        
        run_bandit()
        
        # Verify the call was made
        mock_call.assert_called_once()
        
        # Get the actual command that was called
        call_args = mock_call.call_args[0][0]
        
        # Check basic structure
        self.assertEqual(call_args[0], "bandit")
        self.assertIn("-r", call_args)
        self.assertIn("src", call_args)

    @patch('subprocess.call')
    @patch('os.path.exists')
    def test_run_bandit_config_file_handling(self, mock_exists, mock_call):
        """Test bandit config file handling logic."""
        mock_call.return_value = 0
        
        # Test with config file existing
        mock_exists.return_value = True
        run_bandit()
        
        call_args = mock_call.call_args[0][0]
        self.assertIn("-c", call_args)
        self.assertIn(".bandit", call_args)
        
        # Reset mock
        mock_call.reset_mock()
        
        # Test without config file
        mock_exists.return_value = False
        run_bandit()
        
        call_args = mock_call.call_args[0][0]
        self.assertIn("-f", call_args)
        self.assertIn("json", call_args)
        self.assertIn("-ll", call_args)

    @patch('subprocess.call')
    def test_run_bandit_extra_args_handling(self, mock_call):
        """Test bandit extra arguments handling."""
        mock_call.return_value = 0
        extra_args = ["-x", "tests/", "-s", "B101", "B102"]
        
        run_bandit(extra_args)
        
        call_args = mock_call.call_args[0][0]
        
        # Check that all extra args are included
        for arg in extra_args:
            self.assertIn(arg, call_args)

    @patch('subprocess.call')
    def test_run_bandit_no_extra_args(self, mock_call):
        """Test bandit with no extra arguments."""
        mock_call.return_value = 0
        
        run_bandit()
        
        call_args = mock_call.call_args[0][0]
        
        # Should have basic args: bandit, -r, src, and config/default args
        self.assertGreaterEqual(len(call_args), 3)  # At least bandit, -r, src
        self.assertIn("bandit", call_args)
        self.assertIn("-r", call_args)
        self.assertIn("src", call_args)

    @patch('subprocess.call')
    def test_run_safety_check_command_structure(self, mock_call):
        """Test the exact command structure for safety."""
        mock_call.return_value = 0
        
        run_safety_check()
        
        mock_call.assert_called_once_with(["safety", "check"])

    @patch('subprocess.call')
    def test_run_safety_check_exception_handling(self, mock_call):
        """Test safety check exception handling."""
        # Test FileNotFoundError
        mock_call.side_effect = FileNotFoundError("safety not found")
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
        
        self.assertEqual(result, 0)
        mock_print.assert_called_once()
        
        # Test other exceptions
        mock_call.side_effect = Exception("Other error")
        
        with self.assertRaises(Exception):
            run_safety_check()


if __name__ == '__main__':
    unittest.main()
