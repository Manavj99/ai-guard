"""Comprehensive tests for parser modules to improve coverage."""

import pytest
import json
from unittest.mock import patch, mock_open
from src.ai_guard.parsers.common import normalize_rule, _extract_mypy_rule
from src.ai_guard.parsers.typescript import parse_eslint, parse_jest


class TestCommonParserComprehensive:
    """Comprehensive tests for common parser functions."""

    def test_extract_mypy_rule_valid_format(self):
        """Test _extract_mypy_rule with valid error format."""
        assert _extract_mypy_rule("error[name-defined]") == "mypy:name-defined"
        assert _extract_mypy_rule("error[unused-import]") == "mypy:unused-import"
        assert _extract_mypy_rule("error[no-return]") == "mypy:no-return"

    def test_extract_mypy_rule_invalid_format(self):
        """Test _extract_mypy_rule with invalid format."""
        assert _extract_mypy_rule("error") == "mypy:error"
        assert _extract_mypy_rule("warning") == "mypy:warning"
        assert _extract_mypy_rule("") == "mypy:"

    def test_extract_mypy_rule_already_prefixed(self):
        """Test _extract_mypy_rule with already prefixed rule."""
        assert _extract_mypy_rule("mypy:name-defined") == "mypy:name-defined"
        assert _extract_mypy_rule("mypy:unused-import") == "mypy:unused-import"

    def test_extract_mypy_rule_malformed_brackets(self):
        """Test _extract_mypy_rule with malformed brackets."""
        assert _extract_mypy_rule("error[") == "mypy:error["
        assert _extract_mypy_rule("error]") == "mypy:error]"
        assert _extract_mypy_rule("error[]") == "mypy:"

    def test_normalize_rule_flake8(self):
        """Test normalize_rule for flake8."""
        assert normalize_rule("flake8", "E501") == "flake8:E501"
        assert normalize_rule("flake8", "W291") == "flake8:W291"
        assert normalize_rule("flake8", "F401") == "flake8:F401"
        assert normalize_rule("flake8", "flake8:E501") == "flake8:E501"

    def test_normalize_rule_mypy(self):
        """Test normalize_rule for mypy."""
        assert normalize_rule("mypy", "error[name-defined]") == "mypy:name-defined"
        assert normalize_rule("mypy", "error[unused-import]") == "mypy:unused-import"
        assert normalize_rule("mypy", "mypy:name-defined") == "mypy:name-defined"

    def test_normalize_rule_bandit(self):
        """Test normalize_rule for bandit."""
        assert normalize_rule("bandit", "B101") == "bandit:B101"
        assert normalize_rule("bandit", "B102") == "bandit:B102"
        assert normalize_rule("bandit", "bandit:B101") == "bandit:B101"

    def test_normalize_rule_eslint(self):
        """Test normalize_rule for eslint."""
        assert normalize_rule("eslint", "no-unused") == "eslint:no-unused"
        assert normalize_rule("eslint", "no-console") == "eslint:no-console"
        assert normalize_rule("eslint", "eslint:no-unused") == "eslint:no-unused"

    def test_normalize_rule_jest(self):
        """Test normalize_rule for jest."""
        assert normalize_rule("jest", "test-name") == "jest:test-name"
        assert normalize_rule("jest", "expect") == "jest:expect"
        assert normalize_rule("jest", "jest:test-name") == "jest:test-name"

    def test_normalize_rule_unknown_tool(self):
        """Test normalize_rule for unknown tool."""
        assert normalize_rule("unknown", "rule123") == "unknown:rule123"
        assert normalize_rule("custom", "my-rule") == "custom:my-rule"

    def test_normalize_rule_none_values(self):
        """Test normalize_rule with None values."""
        assert normalize_rule(None, "rule") == "none:rule"
        assert normalize_rule("tool", None) == "tool:None"
        assert normalize_rule(None, None) == "none:None"

    def test_normalize_rule_empty_values(self):
        """Test normalize_rule with empty values."""
        assert normalize_rule("", "rule") == "none:rule"
        assert normalize_rule("tool", "") == "tool:"
        assert normalize_rule("", "") == "none:"

    def test_normalize_rule_case_insensitive(self):
        """Test normalize_rule is case insensitive."""
        assert normalize_rule("FLAKE8", "E501") == "flake8:E501"
        assert normalize_rule("MyPy", "error[name]") == "mypy:name"
        assert normalize_rule("BANDIT", "B101") == "bandit:B101"


class TestTypeScriptParserComprehensive:
    """Comprehensive tests for TypeScript parser functions."""

    def test_parse_eslint_json_format(self):
        """Test parse_eslint with JSON format."""
        json_output = json.dumps([
            {
                "filePath": "src/test.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 5,
                        "column": 10,
                        "message": "Variable 'x' is defined but never used"
                    },
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "line": 8,
                        "column": 5,
                        "message": "Unexpected console statement"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable 'x' is defined but never used"
        assert result[0]["severity"] == "error"
        
        assert result[1]["file"] == "src/test.ts"
        assert result[1]["line"] == 8
        assert result[1]["col"] == 5
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Unexpected console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_json_format_missing_fields(self):
        """Test parse_eslint with JSON format missing some fields."""
        json_output = json.dumps([
            {
                "filePath": "src/test.ts",
                "messages": [
                    {
                        "ruleId": None,
                        "severity": None,
                        "line": None,
                        "column": None,
                        "message": None
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 1
        assert result[0]["col"] == 1
        assert result[0]["rule"] == "eslint:unknown"
        assert result[0]["message"] is None
        assert result[0]["severity"] == "warning"

    def test_parse_eslint_json_format_invalid_json(self):
        """Test parse_eslint with invalid JSON falls back to text parsing."""
        invalid_json = '{"invalid": json}'
        
        result = parse_eslint(invalid_json)
        
        # Should return empty list since no text format matches
        assert result == []

    def test_parse_eslint_text_format(self):
        """Test parse_eslint with text format."""
        text_output = """src/test.ts:5:10  error  Variable 'x' is defined but never used  no-unused-vars
src/test.ts:8:5   warning  Unexpected console statement  no-console"""
        
        result = parse_eslint(text_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable 'x' is defined but never used"
        assert result[0]["severity"] == "error"
        
        assert result[1]["file"] == "src/test.ts"
        assert result[1]["line"] == 8
        assert result[1]["col"] == 5
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Unexpected console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_text_format_no_matches(self):
        """Test parse_eslint with text that doesn't match pattern."""
        text_output = "This is not a valid eslint output line"
        
        result = parse_eslint(text_output)
        
        assert result == []

    def test_parse_eslint_empty_output(self):
        """Test parse_eslint with empty output."""
        result = parse_eslint("")
        assert result == []

    def test_parse_eslint_none_output(self):
        """Test parse_eslint with None output."""
        result = parse_eslint(None)
        assert result == []

    def test_parse_jest_valid_output(self):
        """Test parse_jest with valid output."""
        output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_failed(self):
        """Test parse_jest with no failed tests."""
        output = "Tests:       12 passed, 12 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 12
        assert result["passed"] == 12
        assert result["failed"] == 0

    def test_parse_jest_no_passed(self):
        """Test parse_jest with no passed tests."""
        output = "Tests:       5 failed, 5 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 5

    def test_parse_jest_no_match(self):
        """Test parse_jest with no matching pattern."""
        output = "This is not a jest output"
        
        result = parse_jest(output)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_empty_output(self):
        """Test parse_jest with empty output."""
        result = parse_jest("")
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_none_output(self):
        """Test parse_jest with None output."""
        result = parse_jest(None)
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_complex_output(self):
        """Test parse_jest with complex output."""
        output = "Tests:       3 failed, 15 passed, 18 total, 2 skipped"
        
        result = parse_jest(output)
        
        assert result["tests"] == 18
        assert result["passed"] == 15
        assert result["failed"] == 3

    def test_parse_jest_whitespace_variations(self):
        """Test parse_jest with various whitespace."""
        output = "Tests:   2 failed,   8 passed,   10 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 10
        assert result["passed"] == 8
        assert result["failed"] == 2
