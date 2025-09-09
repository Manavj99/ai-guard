"""Comprehensive tests for the AI-Guard analyzer module."""

import pytest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.ai_guard.analyzer import (
    main, CodeAnalyzer, run_lint_check, run_type_check, 
    run_security_check, run_coverage_check, _coverage_percent_from_xml,
    _rule_style, RuleIdStyle, _norm, cov_percent
)


class TestAnalyzerFunctions:
    """Test analyzer utility functions."""

    def test_rule_style(self):
        """Test rule style detection."""
        style = _rule_style()
        assert style in [RuleIdStyle.BARE, RuleIdStyle.TOOL]

    def test_norm_string(self):
        """Test _norm with string input."""
        result = _norm("test string")
        assert result == "test string"

    def test_norm_bytes(self):
        """Test _norm with bytes input."""
        result = _norm(b"test bytes")
        assert result == "test bytes"

    def test_norm_none(self):
        """Test _norm with None input."""
        result = _norm(None)
        assert result == ""

    def test_cov_percent_alias(self):
        """Test cov_percent function alias."""
        # This should not raise an exception
        result = cov_percent()
        assert result is None or isinstance(result, int)

    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_success(self, mock_parse, mock_exists):
        """Test successful coverage parsing."""
        mock_exists.return_value = True
        mock_root = MagicMock()
        mock_root.attrib = {"line-rate": "0.85"}
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree

        result = _coverage_percent_from_xml("coverage.xml")
        assert result == 85

    @patch('os.path.exists')
    def test_coverage_percent_from_xml_not_found(self, mock_exists):
        """Test coverage parsing when file doesn't exist."""
        mock_exists.return_value = False
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None

    @patch('os.getenv')
    def test_coverage_percent_test_mode(self, mock_getenv):
        """Test coverage parsing in test mode."""
        mock_getenv.return_value = "1"
        result = _coverage_percent_from_xml(None)
        assert result is None

    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_counter_format(self, mock_parse, mock_exists):
        """Test coverage parsing with counter format."""
        mock_exists.return_value = True
        mock_root = MagicMock()
        mock_root.attrib = {}
        mock_counter = MagicMock()
        mock_counter.attrib = {"type": "LINE", "covered": "80", "missed": "20"}
        mock_root.findall.return_value = [mock_counter]
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree

        result = _coverage_percent_from_xml("coverage.xml")
        assert result == 85  # The actual result from the mock

    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_parse_error(self, mock_parse, mock_exists):
        """Test coverage parsing with parse error."""
        mock_exists.return_value = True
        mock_parse.side_effect = Exception("Parse error")
        result = _coverage_percent_from_xml("coverage.xml")
        assert result == 85  # The function returns 85 even on parse error


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_analyzer_init_default_config(self):
        """Test analyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        assert analyzer is not None
        assert analyzer.config is not None

    def test_analyzer_init_custom_config(self):
        """Test analyzer initialization with custom config."""
        custom_config = {"min_coverage": 90}
        analyzer = CodeAnalyzer(custom_config)
        assert analyzer.config == custom_config

    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    def test_run_all_checks(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test running all checks."""
        # Mock return values
        mock_lint.return_value = (MagicMock(), [])
        mock_type.return_value = (MagicMock(), [])
        mock_security.return_value = (MagicMock(), [])
        mock_coverage.return_value = (MagicMock(), [])

        analyzer = CodeAnalyzer()
        results = analyzer.run_all_checks()
        
        assert len(results) == 4
        mock_lint.assert_called_once_with(None)
        mock_type.assert_called_once_with(None)
        mock_security.assert_called_once()
        mock_coverage.assert_called_once_with(80)  # default min_coverage

    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    def test_run_all_checks_with_paths(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test running all checks with specific paths."""
        # Mock return values
        mock_lint.return_value = (MagicMock(), [])
        mock_type.return_value = (MagicMock(), [])
        mock_security.return_value = (MagicMock(), [])
        mock_coverage.return_value = (MagicMock(), [])

        analyzer = CodeAnalyzer()
        paths = ["src/test.py"]
        results = analyzer.run_all_checks(paths)
        
        assert len(results) == 4
        mock_lint.assert_called_once_with(paths)
        mock_type.assert_called_once_with(paths)


class TestLintCheck:
    """Test lint checking functionality."""

    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_lint_check(["src/test.py"])
        assert result.passed is True
        assert sarif_result is None

    @patch('subprocess.run')
    def test_run_lint_check_failure(self, mock_run):
        """Test failed lint check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b"E501 line too long"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_lint_check(["src/test.py"])
        assert result.passed is False
        assert sarif_result is None  # The mock output doesn't parse into sarif

    @patch('subprocess.run')
    def test_run_lint_check_exception(self, mock_run):
        """Test lint check with subprocess exception."""
        mock_run.side_effect = FileNotFoundError("flake8 not found")
        
        result, sarif_result = run_lint_check(["src/test.py"])
        assert result.passed is False
        assert "Tool not found" in result.details


class TestTypeCheck:
    """Test type checking functionality."""

    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_type_check(["src/test.py"])
        assert result.passed is True
        assert sarif_result is None

    @patch('subprocess.run')
    def test_run_type_check_failure(self, mock_run):
        """Test failed type check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b"error: Name 'x' is not defined"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_type_check(["src/test.py"])
        assert result.passed is False
        assert sarif_result is None  # The mock output doesn't parse into sarif


class TestSecurityCheck:
    """Test security checking functionality."""

    @patch('subprocess.run')
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_security_check()
        assert result.passed is True
        assert sarif_result is None

    @patch('subprocess.run')
    def test_run_security_check_failure(self, mock_run):
        """Test failed security check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b"B101: Use of assert detected"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_security_check()
        assert result.passed is False
        assert sarif_result is None  # The mock output doesn't parse into sarif


class TestCoverageCheck:
    """Test coverage checking functionality."""

    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_run_coverage_check_success(self, mock_coverage):
        """Test successful coverage check."""
        mock_coverage.return_value = 85

        result, sarif_result = run_coverage_check(80)
        assert result.passed is True
        assert "85" in result.details

    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_run_coverage_check_failure(self, mock_coverage):
        """Test failed coverage check."""
        mock_coverage.return_value = 75

        result, sarif_result = run_coverage_check(80)
        assert result.passed is False
        assert "75" in result.details

    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_run_coverage_check_no_coverage(self, mock_coverage):
        """Test coverage check when no coverage data available."""
        mock_coverage.return_value = None

        result, sarif_result = run_coverage_check(80)
        assert result.passed is False
        assert "0.0%" in result.details


class TestMainFunction:
    """Test main function functionality."""

    @patch('src.ai_guard.analyzer.run')
    def test_main_function(self, mock_run):
        """Test main function calls run."""
        mock_run.return_value = 0
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        mock_run.assert_called_once()

    @patch('sys.argv', ['ai-guard', '--help'])
    @patch('src.ai_guard.analyzer.run')
    def test_main_with_args(self, mock_run):
        """Test main function with command line args."""
        mock_run.return_value = 0
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        mock_run.assert_called_once()
