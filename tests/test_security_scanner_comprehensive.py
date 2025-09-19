"""Comprehensive tests for security scanner module."""

import pytest
import subprocess
import os
from unittest.mock import Mock, patch, call

from src.ai_guard.security_scanner import (
    run_bandit,
    run_safety_check,
    SecurityScanner,
)


class TestRunBandit:
    """Test run_bandit function."""

    def test_run_bandit_with_config_file(self):
        """Test run_bandit with existing config file."""
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 0
                
                result = run_bandit()
                
                expected_cmd = ["bandit", "-r", "src", "-c", ".bandit"]
                mock_call.assert_called_once_with(expected_cmd)
                assert result == 0

    def test_run_bandit_without_config_file(self):
        """Test run_bandit without config file."""
        with patch('os.path.exists', return_value=False):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 0
                
                result = run_bandit()
                
                expected_cmd = ["bandit", "-r", "src", "-f", "json", "-ll"]
                mock_call.assert_called_once_with(expected_cmd)
                assert result == 0

    def test_run_bandit_with_extra_args(self):
        """Test run_bandit with extra arguments."""
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 1
                
                extra_args = ["-v", "--skip", "B101"]
                result = run_bandit(extra_args)
                
                expected_cmd = ["bandit", "-r", "src", "-c", ".bandit", "-v", "--skip", "B101"]
                mock_call.assert_called_once_with(expected_cmd)
                assert result == 1

    def test_run_bandit_without_config_and_extra_args(self):
        """Test run_bandit without config file but with extra args."""
        with patch('os.path.exists', return_value=False):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 2
                
                extra_args = ["-v"]
                result = run_bandit(extra_args)
                
                expected_cmd = ["bandit", "-r", "src", "-f", "json", "-ll", "-v"]
                mock_call.assert_called_once_with(expected_cmd)
                assert result == 2

    def test_run_bandit_subprocess_error(self):
        """Test run_bandit with subprocess error."""
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.call', side_effect=subprocess.CalledProcessError(1, "bandit")):
                result = run_bandit()
                assert result == 1

    def test_run_bandit_file_not_found(self):
        """Test run_bandit with file not found error."""
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.call', side_effect=FileNotFoundError):
                result = run_bandit()
                assert result == 1


class TestRunSafetyCheck:
    """Test run_safety_check function."""

    def test_run_safety_check_success(self):
        """Test run_safety_check with successful execution."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            result = run_safety_check()
            
            mock_call.assert_called_once_with(["safety", "check"])
            assert result == 0

    def test_run_safety_check_with_vulnerabilities(self):
        """Test run_safety_check with vulnerabilities found."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 1
            
            result = run_safety_check()
            
            mock_call.assert_called_once_with(["safety", "check"])
            assert result == 1

    def test_run_safety_check_not_installed(self):
        """Test run_safety_check when safety is not installed."""
        with patch('subprocess.call', side_effect=FileNotFoundError):
            with patch('builtins.print') as mock_print:
                result = run_safety_check()
                
                mock_print.assert_called_once_with("Warning: safety not installed, skipping dependency security check")
                assert result == 0

    def test_run_safety_check_general_exception(self):
        """Test run_safety_check with general exception."""
        with patch('subprocess.call', side_effect=Exception("Unexpected error")):
            with patch('builtins.print') as mock_print:
                result = run_safety_check()
                
                mock_print.assert_called_once_with("Warning: Error running safety check: Unexpected error")
                assert result == 0

    def test_run_safety_check_permission_error(self):
        """Test run_safety_check with permission error."""
        with patch('subprocess.call', side_effect=PermissionError("Permission denied")):
            with patch('builtins.print') as mock_print:
                result = run_safety_check()
                
                mock_print.assert_called_once_with("Warning: Error running safety check: Permission denied")
                assert result == 0


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    def test_run_bandit_scan_with_config(self):
        """Test run_bandit_scan with config file."""
        scanner = SecurityScanner()
        
        with patch('src.ai_guard.security_scanner.run_bandit') as mock_run_bandit:
            mock_run_bandit.return_value = 0
            
            result = scanner.run_bandit_scan()
            
            mock_run_bandit.assert_called_once_with(None)
            assert result == 0

    def test_run_bandit_scan_with_extra_args(self):
        """Test run_bandit_scan with extra arguments."""
        scanner = SecurityScanner()
        
        with patch('src.ai_guard.security_scanner.run_bandit') as mock_run_bandit:
            mock_run_bandit.return_value = 1
            
            extra_args = ["-v", "--skip", "B101"]
            result = scanner.run_bandit_scan(extra_args)
            
            mock_run_bandit.assert_called_once_with(extra_args)
            assert result == 1

    def test_run_safety_scan(self):
        """Test run_safety_scan."""
        scanner = SecurityScanner()
        
        with patch('src.ai_guard.security_scanner.run_safety_check') as mock_run_safety:
            mock_run_safety.return_value = 0
            
            result = scanner.run_safety_scan()
            
            mock_run_safety.assert_called_once()
            assert result == 0

    def test_run_all_security_checks_both_pass(self):
        """Test run_all_security_checks with both checks passing."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=0) as mock_bandit:
            with patch.object(scanner, 'run_safety_scan', return_value=0) as mock_safety:
                result = scanner.run_all_security_checks()
                
                mock_bandit.assert_called_once()
                mock_safety.assert_called_once()
                assert result == 0

    def test_run_all_security_checks_bandit_fails(self):
        """Test run_all_security_checks with bandit failing."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=1) as mock_bandit:
            with patch.object(scanner, 'run_safety_scan', return_value=0) as mock_safety:
                result = scanner.run_all_security_checks()
                
                mock_bandit.assert_called_once()
                mock_safety.assert_called_once()
                assert result == 1

    def test_run_all_security_checks_safety_fails(self):
        """Test run_all_security_checks with safety failing."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=0) as mock_bandit:
            with patch.object(scanner, 'run_safety_scan', return_value=1) as mock_safety:
                result = scanner.run_all_security_checks()
                
                mock_bandit.assert_called_once()
                mock_safety.assert_called_once()
                assert result == 1

    def test_run_all_security_checks_both_fail(self):
        """Test run_all_security_checks with both checks failing."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=1) as mock_bandit:
            with patch.object(scanner, 'run_safety_scan', return_value=1) as mock_safety:
                result = scanner.run_all_security_checks()
                
                mock_bandit.assert_called_once()
                mock_safety.assert_called_once()
                assert result == 1

    def test_security_scanner_edge_cases(self):
        """Test SecurityScanner edge cases."""
        scanner = SecurityScanner()
        
        # Test with empty extra_args
        with patch('src.ai_guard.security_scanner.run_bandit') as mock_run_bandit:
            mock_run_bandit.return_value = 0
            
            result = scanner.run_bandit_scan([])
            
            mock_run_bandit.assert_called_once_with([])
            assert result == 0

    def test_security_scanner_integration(self):
        """Test SecurityScanner integration with real subprocess calls."""
        scanner = SecurityScanner()
        
        # Test that the scanner can be instantiated and methods exist
        assert hasattr(scanner, 'run_bandit_scan')
        assert hasattr(scanner, 'run_safety_scan')
        assert hasattr(scanner, 'run_all_security_checks')
        
        # Test method signatures
        assert callable(scanner.run_bandit_scan)
        assert callable(scanner.run_safety_scan)
        assert callable(scanner.run_all_security_checks)

    def test_security_scanner_error_handling(self):
        """Test SecurityScanner error handling."""
        scanner = SecurityScanner()
        
        # Test with subprocess errors
        with patch('src.ai_guard.security_scanner.run_bandit', side_effect=Exception("Bandit error")):
            with pytest.raises(Exception):
                scanner.run_bandit_scan()
        
        with patch('src.ai_guard.security_scanner.run_safety_check', side_effect=Exception("Safety error")):
            with pytest.raises(Exception):
                scanner.run_safety_scan()

    def test_security_scanner_performance(self):
        """Test SecurityScanner performance with multiple calls."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=0) as mock_bandit:
            with patch.object(scanner, 'run_safety_scan', return_value=0) as mock_safety:
                # Run multiple times to test performance
                for _ in range(10):
                    result = scanner.run_all_security_checks()
                    assert result == 0
                
                assert mock_bandit.call_count == 10
                assert mock_safety.call_count == 10

    def test_security_scanner_with_none_args(self):
        """Test SecurityScanner with None arguments."""
        scanner = SecurityScanner()
        
        with patch('src.ai_guard.security_scanner.run_bandit') as mock_run_bandit:
            mock_run_bandit.return_value = 0
            
            result = scanner.run_bandit_scan(None)
            
            mock_run_bandit.assert_called_once_with(None)
            assert result == 0

    def test_security_scanner_return_code_combinations(self):
        """Test SecurityScanner with various return code combinations."""
        scanner = SecurityScanner()
        
        test_cases = [
            (0, 0, 0),  # Both pass
            (1, 0, 1),  # Bandit fails
            (0, 1, 1),  # Safety fails
            (1, 1, 1),  # Both fail
            (2, 0, 2),  # Bandit fails with code 2
            (0, 2, 2),  # Safety fails with code 2
            (3, 4, 3),  # Both fail with different codes
        ]
        
        for bandit_code, safety_code, expected in test_cases:
            with patch.object(scanner, 'run_bandit_scan', return_value=bandit_code):
                with patch.object(scanner, 'run_safety_scan', return_value=safety_code):
                    result = scanner.run_all_security_checks()
                    assert result == expected, f"Expected {expected}, got {result} for bandit={bandit_code}, safety={safety_code}"

    def test_security_scanner_method_chaining(self):
        """Test SecurityScanner method chaining."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=0) as mock_bandit:
            with patch.object(scanner, 'run_safety_scan', return_value=0) as mock_safety:
                # Test that methods can be called in sequence
                bandit_result = scanner.run_bandit_scan()
                safety_result = scanner.run_safety_scan()
                all_result = scanner.run_all_security_checks()
                
                assert bandit_result == 0
                assert safety_result == 0
                assert all_result == 0
                
                assert mock_bandit.call_count == 2  # Called once directly, once in run_all_security_checks
                assert mock_safety.call_count == 2  # Called once directly, once in run_all_security_checks