"""Additional tests to improve coverage for low-coverage files."""

import pytest
import sys
import os
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_guard.generators.testgen import generate_speculative_tests, main
from ai_guard.parsers.typescript import parse_eslint, parse_jest
from ai_guard.parsers.common import normalize_rule, _extract_mypy_rule
from src.ai_guard.utils.subprocess_runner import run_cmd, run_command, _format_command_output
from src.ai_guard.security_scanner import SecurityScanner
from src.ai_guard.report import ReportGenerator
from src.ai_guard.report_html import HTMLReportGenerator
from src.ai_guard.sarif_report import SarifResult, SarifRun
from src.ai_guard.tests_runner import TestsRunner


class TestCoverageGaps:
    """Test coverage gaps in low-coverage files."""

    def test_generate_speculative_tests_with_files(self):
        """Test generate_speculative_tests with actual files."""
        changed_files = ["src/test_module.py", "src/another_module.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# - src/test_module.py" in result
        assert "# - src/another_module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result
        assert "assert True" in result

    def test_main_function_execution(self):
        """Test main function execution path."""
        with patch('ai_guard.generators.testgen.changed_python_files', return_value=["src/test.py"]):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('pathlib.Path.mkdir'):
                    with patch('builtins.print'):
                        # Mock argparse
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(
                                event=None, 
                                output="tests/unit/test_generated.py"
                            )
                            main()
                            
                            # Verify file was written
                            mock_file.assert_called_once()
                            written_content = mock_file.return_value.write.call_args[0][0]
                            assert "Auto-generated speculative tests" in written_content

    def test_parse_eslint_json_format_execution(self):
        """Test parse_eslint JSON format execution."""
        import json
        json_data = [{
            "filePath": "src/test.ts",
            "messages": [{
                "ruleId": "no-unused-vars",
                "severity": 2,
                "line": 10,
                "column": 5,
                "message": "Test message"
            }]
        }]
        
        result = parse_eslint(json.dumps(json_data))
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["rule"] == "eslint:no-unused-vars"

    def test_parse_eslint_stylish_format_execution(self):
        """Test parse_eslint stylish format execution."""
        stylish_output = "src/test.ts:10:5  error  Test message  test-rule"
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["severity"] == "error"

    def test_parse_jest_standard_format_execution(self):
        """Test parse_jest standard format execution."""
        jest_output = "Tests:       2 failed, 10 passed, 12 total"
        result = parse_jest(jest_output)
        
        assert result["tests"] == 12
        assert result["passed"] == 10
        assert result["failed"] == 2

    def test_normalize_rule_all_tools(self):
        """Test normalize_rule for all supported tools."""
        # Test flake8
        assert normalize_rule("flake8", "E501") == "flake8:E501"
        assert normalize_rule("flake8", "flake8:E501") == "flake8:E501"
        
        # Test mypy
        assert normalize_rule("mypy", "error[name-defined]") == "mypy:name-defined"
        assert normalize_rule("mypy", "error") == "mypy:error"
        
        # Test bandit
        assert normalize_rule("bandit", "B101") == "bandit:B101"
        assert normalize_rule("bandit", "bandit:B101") == "bandit:B101"
        
        # Test eslint
        assert normalize_rule("eslint", "no-unused") == "eslint:no-unused"
        assert normalize_rule("eslint", "eslint:no-unused") == "eslint:no-unused"
        
        # Test jest
        assert normalize_rule("jest", "expect") == "jest:expect"
        assert normalize_rule("jest", "jest:expect") == "jest:expect"

    def test_extract_mypy_rule_edge_cases(self):
        """Test _extract_mypy_rule edge cases."""
        assert _extract_mypy_rule("error[name-defined]") == "mypy:name-defined"
        assert _extract_mypy_rule("error") == "mypy:error"
        assert _extract_mypy_rule("mypy:error") == "mypy:error"
        assert _extract_mypy_rule("") == "mypy:"

    def test_subprocess_runner_basic(self):
        """Test subprocess runner basic functionality."""
        # Test with a simple command that should work
        returncode, output = run_cmd(["python", "-c", "print('test')"])
        assert returncode == 0
        assert "test" in output

    def test_security_scanner_basic(self):
        """Test SecurityScanner basic functionality."""
        scanner = SecurityScanner()
        
        # Test basic initialization
        assert scanner is not None

    def test_report_basic(self):
        """Test ReportGenerator basic functionality."""
        report = ReportGenerator()
        
        # Test basic initialization
        assert report is not None

    def test_html_report_basic(self):
        """Test HTMLReportGenerator basic functionality."""
        html_report = HTMLReportGenerator()
        
        # Test basic initialization
        assert html_report is not None

    def test_sarif_report_basic(self):
        """Test SARIF report basic functionality."""
        sarif_result = SarifResult("test", "error", "test message")
        
        # Test basic initialization
        assert sarif_result.rule_id == "test"

    def test_tests_runner_basic(self):
        """Test TestsRunner basic functionality."""
        runner = TestsRunner()
        
        # Test basic initialization
        assert runner is not None
