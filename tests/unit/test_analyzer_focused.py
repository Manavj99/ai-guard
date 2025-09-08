"""Focused tests for analyzer.py module to improve coverage."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import tempfile
import os

from src.ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_output,
    main
)


class TestAnalyzerFunctions(unittest.TestCase):
    """Test analyzer module functions."""

    def test_cov_percent_basic(self):
        """Test cov_percent function with basic input."""
        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=85):
            result = cov_percent()
            self.assertEqual(result, 85)

    def test_cov_percent_missing_file(self):
        """Test cov_percent with missing file."""
        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=None):
            result = cov_percent()
            self.assertEqual(result, 0)

    def test_cov_percent_invalid_xml(self):
        """Test cov_percent with invalid XML."""
        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=None):
            result = cov_percent()
            self.assertEqual(result, 0)

    def test_parse_flake8_output(self):
        """Test parsing flake8 output."""
        flake8_output = "test.py:10:5: E501 line too long (80 > 79 characters)"
        
        result = _parse_flake8_output(flake8_output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "E501")

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = "test.py:15: error: Incompatible types in assignment"
        
        result = _parse_mypy_output(mypy_output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "error")

    def test_parse_bandit_output(self):
        """Test parsing bandit output."""
        bandit_output = "test.py:20:1: B101 Use of assert detected"
        
        result = _parse_bandit_output(bandit_output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "B101")

    @patch('src.ai_guard.analyzer.subprocess.run')
    def test_main_function_basic(self, mock_run):
        """Test main function with basic arguments."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('sys.argv', ['analyzer.py', '--min-cov', '80']):
            with patch('src.ai_guard.analyzer.cov_percent', return_value=85):
                with patch('sys.exit'):
                    result = main()
                    self.assertIsNotNone(result)

    @patch('src.ai_guard.analyzer.subprocess.run')
    def test_main_function_with_skip_tests(self, mock_run):
        """Test main function with skip tests."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('sys.argv', ['analyzer.py', '--skip-tests']):
            with patch('sys.exit'):
                result = main()
                self.assertIsNotNone(result)

    @patch('src.ai_guard.analyzer.subprocess.run')
    def test_main_function_with_report_format(self, mock_run):
        """Test main function with report format."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('sys.argv', ['analyzer.py', '--report-format', 'json']):
            with patch('sys.exit'):
                result = main()
                self.assertIsNotNone(result)

    @patch('src.ai_guard.analyzer.subprocess.run')
    def test_main_function_with_pr_annotations(self, mock_run):
        """Test main function with PR annotations."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('sys.argv', ['analyzer.py', '--pr-annotations']):
            with patch('sys.exit'):
                result = main()
                self.assertIsNotNone(result)

    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        result = _parse_flake8_output("")
        self.assertEqual(len(result), 0)

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        result = _parse_mypy_output("")
        self.assertEqual(len(result), 0)

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        result = _parse_bandit_output("")
        self.assertEqual(len(result), 0)

    def test_cov_percent_zero_coverage(self):
        """Test cov_percent with zero coverage."""
        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=0):
            result = cov_percent()
            self.assertEqual(result, 0)

    def test_cov_percent_full_coverage(self):
        """Test cov_percent with full coverage."""
        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=100):
            result = cov_percent()
            self.assertEqual(result, 100)


if __name__ == "__main__":
    unittest.main()
