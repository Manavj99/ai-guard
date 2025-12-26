"""Comprehensive tests for security_scanner.py module."""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ai_guard.security_scanner import (
    run_bandit,
    run_safety_check,
    scan_for_vulnerabilities,
    check_dependencies,
    analyze_security_patterns,
)


class TestSecurityScanner:
    """Test the SecurityScanner class."""

    def test_init_default(self):
        """Test initialization with default settings."""
        scanner = SecurityScanner()
        assert scanner is not None
        assert hasattr(scanner, "scan_file")
        assert hasattr(scanner, "scan_directory")

    def test_init_with_config(self):
        """Test initialization with custom configuration."""
        config = {"severity_threshold": "HIGH", "enable_bandit": True}
        scanner = SecurityScanner(config)
        assert scanner.config == config

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_file_success(self, mock_run):
        """Test successful file scanning."""
        mock_run.return_value = Mock(returncode=0, stdout='{"results": []}')

        scanner = SecurityScanner()
        result = scanner.scan_file("test.py")

        assert result is not None
        mock_run.assert_called_once()

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_file_with_issues(self, mock_run):
        """Test file scanning with security issues."""
        mock_output = {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "test_name": "B101",
                    "filename": "test.py",
                    "line_number": 10,
                    "code": "assert True",
                }
            ]
        }
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps(mock_output))

        scanner = SecurityScanner()
        result = scanner.scan_file("test.py")

        assert result is not None
        assert len(result) > 0

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_directory_success(self, mock_run):
        """Test successful directory scanning."""
        mock_run.return_value = Mock(returncode=0, stdout='{"results": []}')

        scanner = SecurityScanner()
        result = scanner.scan_directory("src/")

        assert result is not None
        mock_run.assert_called_once()

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_directory_with_issues(self, mock_run):
        """Test directory scanning with security issues."""
        mock_output = {
            "results": [
                {
                    "issue_severity": "MEDIUM",
                    "issue_confidence": "HIGH",
                    "test_name": "B602",
                    "filename": "src/test.py",
                    "line_number": 5,
                    "code": "subprocess.run(user_input)",
                }
            ]
        }
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps(mock_output))

        scanner = SecurityScanner()
        result = scanner.scan_directory("src/")

        assert result is not None
        assert len(result) > 0


class TestBanditFunction:
    """Test the run_bandit function."""

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_run_bandit_success(self, mock_call):
        """Test successful bandit run."""
        mock_call.return_value = 0

        result = run_bandit()

        assert result == 0
        mock_call.assert_called_once()

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test bandit run with extra arguments."""
        mock_call.return_value = 0

        result = run_bandit(["-f", "json"])

        assert result == 0
        mock_call.assert_called_once()

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_run_bandit_with_config_file(self, mock_call):
        """Test bandit run with config file."""
        mock_call.return_value = 0

        with patch("os.path.exists", return_value=True):
            result = run_bandit()

        assert result == 0
        mock_call.assert_called_once()


class TestSafetyFunction:
    """Test the run_safety_check function."""

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_run_safety_check_success(self, mock_call):
        """Test successful safety check."""
        mock_call.return_value = 0

        result = run_safety_check()

        assert result == 0
        mock_call.assert_called_once()

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_run_safety_check_file_not_found(self, mock_call):
        """Test safety check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError()

        result = run_safety_check()

        assert result == 0

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_run_safety_check_exception(self, mock_call):
        """Test safety check with exception."""
        mock_call.side_effect = Exception("Safety error")

        result = run_safety_check()

        assert result == 0


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("src.ai_guard.security_scanner.SecurityScanner")
    def test_scan_file_function(self, mock_scanner_class):
        """Test scan_file utility function."""
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_file.return_value = []

        result = scan_file("test.py")

        assert result == []
        mock_scanner.scan_file.assert_called_once_with("test.py")

    @patch("src.ai_guard.security_scanner.SecurityScanner")
    def test_scan_directory_function(self, mock_scanner_class):
        """Test scan_directory utility function."""
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_directory.return_value = []

        result = scan_directory("src/")

        assert result == []
        mock_scanner.scan_directory.assert_called_once_with("src/")

    def test_get_security_report(self):
        """Test get_security_report function."""
        issues = [
            SecurityIssue(
                severity=SecuritySeverity.HIGH,
                confidence="HIGH",
                rule_id="B101",
                file_path="test.py",
                line_number=10,
                code="assert True",
                description="Use of assert detected",
            )
        ]

        report = get_security_report(issues)

        assert isinstance(report, dict)
        assert "total_issues" in report
        assert "severity_breakdown" in report
        assert "files_affected" in report
        assert report["total_issues"] == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_file_subprocess_error(self, mock_run):
        """Test scan_file with subprocess error."""
        mock_run.side_effect = Exception("Subprocess error")

        scanner = SecurityScanner()
        result = scanner.scan_file("test.py")

        assert result is not None
        assert len(result) == 0

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_file_invalid_json(self, mock_run):
        """Test scan_file with invalid JSON output."""
        mock_run.return_value = Mock(returncode=0, stdout="invalid json")

        scanner = SecurityScanner()
        result = scanner.scan_file("test.py")

        assert result is not None
        assert len(result) == 0

    def test_scan_file_nonexistent_file(self):
        """Test scan_file with nonexistent file."""
        scanner = SecurityScanner()
        result = scanner.scan_file("nonexistent.py")

        assert result is not None
        assert len(result) == 0

    def test_scan_directory_nonexistent_directory(self):
        """Test scan_directory with nonexistent directory."""
        scanner = SecurityScanner()
        result = scanner.scan_directory("nonexistent/")

        assert result is not None
        assert len(result) == 0

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_scan_directory_subprocess_error(self, mock_run):
        """Test scan_directory with subprocess error."""
        mock_run.side_effect = Exception("Subprocess error")

        scanner = SecurityScanner()
        result = scanner.scan_directory("src/")

        assert result is not None
        assert len(result) == 0


class TestConfigurationHandling:
    """Test configuration handling."""

    def test_scanner_with_severity_threshold(self):
        """Test scanner with severity threshold configuration."""
        config = {"severity_threshold": "HIGH"}
        scanner = SecurityScanner(config)

        assert scanner.config["severity_threshold"] == "HIGH"

    def test_scanner_with_enable_bandit(self):
        """Test scanner with bandit enable configuration."""
        config = {"enable_bandit": True}
        scanner = SecurityScanner(config)

        assert scanner.config["enable_bandit"] is True

    def test_scanner_with_enable_safety(self):
        """Test scanner with safety enable configuration."""
        config = {"enable_safety": True}
        scanner = SecurityScanner(config)

        assert scanner.config["enable_safety"] is True


class TestIntegration:
    """Test integration scenarios."""

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_full_scan_workflow(self, mock_run):
        """Test full scanning workflow."""
        mock_run.return_value = Mock(returncode=0, stdout='{"results": []}')

        scanner = SecurityScanner()

        # Test file scanning
        file_result = scanner.scan_file("test.py")
        assert file_result is not None

        # Test directory scanning
        dir_result = scanner.scan_directory("src/")
        assert dir_result is not None

    def test_security_report_generation(self):
        """Test security report generation."""
        issues = [
            SecurityIssue(
                severity=SecuritySeverity.HIGH,
                confidence="HIGH",
                rule_id="B101",
                file_path="test1.py",
                line_number=10,
                code="assert True",
                description="Use of assert detected",
            ),
            SecurityIssue(
                severity=SecuritySeverity.MEDIUM,
                confidence="HIGH",
                rule_id="B602",
                file_path="test2.py",
                line_number=5,
                code="subprocess.run(user_input)",
                description="Subprocess call with user input",
            ),
        ]

        report = get_security_report(issues)

        assert report["total_issues"] == 2
        assert report["severity_breakdown"]["HIGH"] == 1
        assert report["severity_breakdown"]["MEDIUM"] == 1
        assert len(report["files_affected"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])
