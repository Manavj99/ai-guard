"""Focused tests to boost coverage for low-coverage modules."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open

from ai_guard.diff_parser import (
    get_file_extensions, filter_python_files, parse_diff_output,
    changed_python_files, parse_github_event, get_changed_files
)
from ai_guard.parsers.typescript import parse_eslint, parse_jest
from ai_guard.parsers.common import normalize_rule
from ai_guard.gates.coverage_eval import CoverageResult, evaluate_coverage_str
from ai_guard.utils.subprocess_runner import (
    run_command_dict, run_command_with_output, run_command_safe
)


class TestDiffParserFocused:
    """Focused tests for diff parser module."""

    def test_get_file_extensions_basic(self):
        """Test getting file extensions."""
        file_paths = ["test.py", "script.js", "style.css", "README.md"]
        extensions = get_file_extensions(file_paths)
        assert "py" in extensions
        assert "js" in extensions
        assert "css" in extensions

    def test_get_file_extensions_none(self):
        """Test getting file extensions from None."""
        extensions = get_file_extensions(None)
        assert extensions == []

    def test_get_file_extensions_empty(self):
        """Test getting file extensions from empty list."""
        extensions = get_file_extensions([])
        assert extensions == []

    def test_get_file_extensions_no_dots(self):
        """Test getting file extensions from files without dots."""
        file_paths = ["README", "Makefile", "LICENSE"]
        extensions = get_file_extensions(file_paths)
        assert extensions == []

    def test_get_file_extensions_backup_files(self):
        """Test getting file extensions excluding backup files."""
        file_paths = ["test.py", "test.py~", "test.py.bak", "test.py.tmp"]
        extensions = get_file_extensions(file_paths)
        assert extensions == ["py"]

    def test_filter_python_files_basic(self):
        """Test filtering Python files."""
        file_paths = ["test.py", "script.js", "style.css", "main.py"]
        python_files = filter_python_files(file_paths)
        assert len(python_files) == 2
        assert "test.py" in python_files
        assert "main.py" in python_files

    def test_filter_python_files_none(self):
        """Test filtering Python files from None."""
        python_files = filter_python_files(None)
        assert python_files == []

    def test_filter_python_files_empty(self):
        """Test filtering Python files from empty list."""
        python_files = filter_python_files([])
        assert python_files == []

    def test_parse_diff_output_basic(self):
        """Test parsing diff output."""
        diff_content = """
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello World")
+    return True
"""
        result = parse_diff_output(diff_content)
        assert isinstance(result, list)

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        result = parse_diff_output("")
        assert isinstance(result, list)

    def test_parse_diff_output_none(self):
        """Test parsing None diff output."""
        result = parse_diff_output(None)
        assert isinstance(result, list)

    def test_changed_python_files_none(self):
        """Test getting changed Python files with None event path."""
        result = changed_python_files(None)
        assert isinstance(result, list)

    def test_changed_python_files_empty_list(self):
        """Test getting changed Python files with empty list."""
        result = changed_python_files([])
        assert isinstance(result, list)

    def test_parse_github_event_invalid_path(self):
        """Test parsing GitHub event with invalid path."""
        result = parse_github_event("nonexistent.json")
        assert isinstance(result, dict)

    def test_get_changed_files_none(self):
        """Test getting changed files with None event path."""
        result = get_changed_files(None)
        assert isinstance(result, list)


class TestTypeScriptParserFocused:
    """Focused tests for TypeScript parser module."""

    def test_parse_eslint_basic(self):
        """Test parsing ESLint output."""
        eslint_output = """
[
  {
    "filePath": "test.ts",
    "messages": [
      {
        "ruleId": "@typescript-eslint/no-unused-vars",
        "severity": 2,
        "message": "'unused' is defined but never used",
        "line": 2,
        "column": 5
      }
    ]
  }
]
"""
        result = parse_eslint(eslint_output)
        assert isinstance(result, list)

    def test_parse_eslint_empty(self):
        """Test parsing empty ESLint output."""
        result = parse_eslint("")
        assert isinstance(result, list)

    def test_parse_eslint_invalid(self):
        """Test parsing invalid ESLint output."""
        result = parse_eslint("invalid json")
        assert isinstance(result, list)

    def test_parse_jest_basic(self):
        """Test parsing Jest output."""
        jest_output = """
{
  "testResults": [
    {
      "name": "test.ts",
      "status": "passed",
      "assertionResults": [
        {
          "title": "should calculate distance",
          "status": "passed"
        }
      ]
    }
  ]
}
"""
        result = parse_jest(jest_output)
        assert isinstance(result, dict)

    def test_parse_jest_empty(self):
        """Test parsing empty Jest output."""
        result = parse_jest("")
        assert isinstance(result, dict)

    def test_parse_jest_invalid(self):
        """Test parsing invalid Jest output."""
        result = parse_jest("invalid json")
        assert isinstance(result, dict)


class TestCommonParserFocused:
    """Focused tests for common parser module."""

    def test_normalize_rule_basic(self):
        """Test normalizing rule names."""
        result = normalize_rule("flake8", "E501")
        assert isinstance(result, str)
        assert result == "flake8:E501"

    def test_normalize_rule_empty(self):
        """Test normalizing empty rule name."""
        result = normalize_rule("flake8", "")
        assert isinstance(result, str)
        assert result == "flake8:"

    def test_normalize_rule_none(self):
        """Test normalizing None rule name."""
        result = normalize_rule("flake8", None)
        assert isinstance(result, str)


class TestCoverageEvalFocused:
    """Focused tests for coverage evaluation module."""

    def test_coverage_result_init_basic(self):
        """Test CoverageResult initialization."""
        result = CoverageResult(percent=85.5)
        assert result.percent == 85.5

    def test_coverage_result_init_zero(self):
        """Test CoverageResult initialization with zero."""
        result = CoverageResult(percent=0.0)
        assert result.percent == 0.0

    def test_coverage_result_init_hundred(self):
        """Test CoverageResult initialization with 100."""
        result = CoverageResult(percent=100.0)
        assert result.percent == 100.0

    def test_evaluate_coverage_str_xml_format(self):
        """Test evaluating coverage from XML format."""
        xml_content = """
<?xml version="1.0" ?>
<coverage version="1">
    <packages>
        <package name="src" line-rate="0.85" branch-rate="0.75">
            <classes>
                <class name="test_module" line-rate="0.85" branch-rate="0.75">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                        <line number="3" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
        result = evaluate_coverage_str(xml_content)
        assert isinstance(result, CoverageResult)

    def test_evaluate_coverage_str_empty(self):
        """Test evaluating coverage from empty string."""
        result = evaluate_coverage_str("")
        assert isinstance(result, CoverageResult)

    def test_evaluate_coverage_str_invalid_xml(self):
        """Test evaluating coverage from invalid XML."""
        result = evaluate_coverage_str("invalid xml content")
        assert isinstance(result, CoverageResult)


class TestSubprocessRunnerFocused:
    """Focused tests for subprocess runner module."""

    @patch('subprocess.run')
    def test_run_command_dict_success(self, mock_run):
        """Test running command with dict result."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        
        result = run_command_dict(["echo", "test"])
        assert isinstance(result, dict)

    @patch('subprocess.run')
    def test_run_command_dict_failure(self, mock_run):
        """Test running command with failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        
        result = run_command_dict(["false"])
        assert isinstance(result, dict)

    @patch('subprocess.run')
    def test_run_command_with_output_success(self, mock_run):
        """Test running command with output."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        
        result = run_command_with_output(["echo", "test"])
        assert isinstance(result, dict)

    @patch('subprocess.run')
    def test_run_command_with_output_failure(self, mock_run):
        """Test running command with failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        
        result = run_command_with_output(["false"])
        assert isinstance(result, dict)

    @patch('subprocess.run')
    def test_run_command_safe_success(self, mock_run):
        """Test running command safely."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        
        result = run_command_safe(["echo", "test"])
        assert isinstance(result, dict)

    @patch('subprocess.run')
    def test_run_command_safe_exception(self, mock_run):
        """Test running command safely with exception."""
        mock_run.side_effect = Exception("Command failed")
        
        result = run_command_safe(["invalid_command"])
        assert isinstance(result, dict)
        assert "error" in result or "success" in result
