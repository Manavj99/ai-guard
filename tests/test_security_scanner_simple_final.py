"""Simple tests for security_scanner.py module."""

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


class TestRunBandit:
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


class TestRunSafetyCheck:
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


class TestScanForVulnerabilities:
    """Test the scan_for_vulnerabilities function."""

    def test_scan_for_vulnerabilities_empty_list(self):
        """Test scanning with empty file list."""
        result = scan_for_vulnerabilities([])

        assert isinstance(result, dict)
        assert "vulnerabilities" in result
        assert "total_files" in result

    def test_scan_for_vulnerabilities_with_files(self):
        """Test scanning with file list."""
        files = ["src/test.py", "src/main.py"]

        result = scan_for_vulnerabilities(files)

        assert isinstance(result, dict)
        assert "vulnerabilities" in result
        assert "total_files" in result
        assert result["total_files"] == 2

    def test_scan_for_vulnerabilities_nonexistent_files(self):
        """Test scanning with nonexistent files."""
        files = ["nonexistent.py"]

        result = scan_for_vulnerabilities(files)

        assert isinstance(result, dict)
        assert "vulnerabilities" in result
        assert "total_files" in result


class TestCheckDependencies:
    """Test the check_dependencies function."""

    def test_check_dependencies(self):
        """Test dependency checking."""
        result = check_dependencies()

        assert isinstance(result, dict)
        assert "dependencies" in result
        assert "vulnerabilities" in result

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_check_dependencies_with_subprocess(self, mock_run):
        """Test dependency checking with subprocess."""
        mock_run.return_value = Mock(returncode=0, stdout="No vulnerabilities found")

        result = check_dependencies()

        assert isinstance(result, dict)
        assert "dependencies" in result
        assert "vulnerabilities" in result


class TestAnalyzeSecurityPatterns:
    """Test the analyze_security_patterns function."""

    def test_analyze_security_patterns_safe_code(self):
        """Test analyzing safe code."""
        code_content = "def hello():\n    print('Hello World')"
        file_path = "test.py"

        result = analyze_security_patterns(code_content, file_path)

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "file_path" in result
        assert result["file_path"] == file_path

    def test_analyze_security_patterns_with_assert(self):
        """Test analyzing code with assert statement."""
        code_content = "def test():\n    assert password == 'secret'"
        file_path = "test.py"

        result = analyze_security_patterns(code_content, file_path)

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "file_path" in result

    def test_analyze_security_patterns_with_eval(self):
        """Test analyzing code with eval statement."""
        code_content = "def dangerous():\n    eval(user_input)"
        file_path = "test.py"

        result = analyze_security_patterns(code_content, file_path)

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "file_path" in result

    def test_analyze_security_patterns_empty_code(self):
        """Test analyzing empty code."""
        code_content = ""
        file_path = "test.py"

        result = analyze_security_patterns(code_content, file_path)

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "file_path" in result

    def test_analyze_security_patterns_none_code(self):
        """Test analyzing None code."""
        code_content = None
        file_path = "test.py"

        result = analyze_security_patterns(code_content, file_path)

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "file_path" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_run_bandit_with_none_args(self):
        """Test bandit run with None arguments."""
        with patch("src.ai_guard.security_scanner.subprocess.call") as mock_call:
            mock_call.return_value = 0

            result = run_bandit(None)

            assert result == 0
            mock_call.assert_called_once()

    def test_scan_for_vulnerabilities_with_none(self):
        """Test scanning with None file list."""
        result = scan_for_vulnerabilities(None)

        assert isinstance(result, dict)
        assert "vulnerabilities" in result

    def test_analyze_security_patterns_with_none_file_path(self):
        """Test analyzing with None file path."""
        code_content = "def test():\n    pass"

        result = analyze_security_patterns(code_content, None)

        assert isinstance(result, dict)
        assert "patterns" in result


class TestIntegration:
    """Test integration scenarios."""

    def test_full_security_workflow(self):
        """Test full security analysis workflow."""
        files = ["src/test.py"]

        # Test vulnerability scanning
        vulnerabilities = scan_for_vulnerabilities(files)
        assert isinstance(vulnerabilities, dict)

        # Test dependency checking
        dependencies = check_dependencies()
        assert isinstance(dependencies, dict)

        # Test pattern analysis
        patterns = analyze_security_patterns("def test():\n    pass", "test.py")
        assert isinstance(patterns, dict)

    @patch("src.ai_guard.security_scanner.subprocess.call")
    def test_bandit_and_safety_integration(self, mock_call):
        """Test integration of bandit and safety checks."""
        mock_call.return_value = 0

        # Test bandit
        bandit_result = run_bandit()
        assert bandit_result == 0

        # Test safety
        safety_result = run_safety_check()
        assert safety_result == 0


if __name__ == "__main__":
    pytest.main([__file__])
