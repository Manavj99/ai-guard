"""Comprehensive tests for parsers modules to achieve high coverage."""

import pytest
import json
from unittest.mock import patch, MagicMock

from src.ai_guard.parsers.common import normalize_rule, _extract_mypy_rule, _RULE_NORMALIZERS
from src.ai_guard.parsers.typescript import parse_eslint, parse_jest


class TestCommonParsers:
    """Test common parser functions."""

    def test_extract_mypy_rule_valid(self):
        """Test extracting mypy rule from valid format."""
        result = _extract_mypy_rule("error[name-defined]")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_no_brackets(self):
        """Test extracting mypy rule from format without brackets."""
        result = _extract_mypy_rule("name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_already_prefixed(self):
        """Test extracting mypy rule that already has mypy: prefix."""
        result = _extract_mypy_rule("mypy:name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_malformed(self):
        """Test extracting mypy rule from malformed input."""
        result = _extract_mypy_rule("error[name-defined")
        assert result == "mypy:error[name-defined"

    def test_normalize_rule_flake8(self):
        """Test normalizing flake8 rule."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_flake8_already_prefixed(self):
        """Test normalizing flake8 rule that already has prefix."""
        result = normalize_rule("flake8", "flake8:E501")
        assert result == "flake8:E501"

    def test_normalize_rule_mypy(self):
        """Test normalizing mypy rule."""
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"

    def test_normalize_rule_bandit(self):
        """Test normalizing bandit rule."""
        result = normalize_rule("bandit", "B101")
        assert result == "bandit:B101"

    def test_normalize_rule_bandit_already_prefixed(self):
        """Test normalizing bandit rule that already has prefix."""
        result = normalize_rule("bandit", "bandit:B101")
        assert result == "bandit:B101"

    def test_normalize_rule_eslint(self):
        """Test normalizing eslint rule."""
        result = normalize_rule("eslint", "no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_eslint_already_prefixed(self):
        """Test normalizing eslint rule that already has prefix."""
        result = normalize_rule("eslint", "eslint:no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_jest(self):
        """Test normalizing jest rule."""
        result = normalize_rule("jest", "test-failed")
        assert result == "jest:test-failed"

    def test_normalize_rule_jest_already_prefixed(self):
        """Test normalizing jest rule that already has prefix."""
        result = normalize_rule("jest", "jest:test-failed")
        assert result == "jest:test-failed"

    def test_normalize_rule_unknown_tool(self):
        """Test normalizing rule for unknown tool."""
        result = normalize_rule("unknown", "rule123")
        assert result == "unknown:rule123"

    def test_normalize_rule_none_tool(self):
        """Test normalizing rule with None tool."""
        result = normalize_rule(None, "rule123")
        assert result == "none:rule123"

    def test_normalize_rule_none_raw(self):
        """Test normalizing rule with None raw."""
        result = normalize_rule("flake8", None)
        assert result == "flake8:None"

    def test_normalize_rule_empty_raw(self):
        """Test normalizing rule with empty raw."""
        result = normalize_rule("flake8", "")
        assert result == "flake8:"

    def test_normalize_rule_non_string_raw(self):
        """Test normalizing rule with non-string raw."""
        result = normalize_rule("flake8", 123)
        assert result == "flake8:123"

    def test_rule_normalizers_dict(self):
        """Test that _RULE_NORMALIZERS contains expected tools."""
        expected_tools = ["flake8", "mypy", "bandit", "eslint", "jest"]
        for tool in expected_tools:
            assert tool in _RULE_NORMALIZERS
            assert callable(_RULE_NORMALIZERS[tool])


class TestTypeScriptParsers:
    """Test TypeScript parser functions."""

    def test_parse_eslint_json_format(self):
        """Test parsing ESLint JSON output."""
        json_output = json.dumps([
            {
                "filePath": "test.js",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 5,
                        "column": 10,
                        "message": "Variable is not used"
                    },
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "line": 10,
                        "column": 5,
                        "message": "Console statement"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "test.js"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is not used"
        assert result[0]["severity"] == "error"
        
        assert result[1]["file"] == "test.js"
        assert result[1]["line"] == 10
        assert result[1]["col"] == 5
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_json_format_missing_fields(self):
        """Test parsing ESLint JSON output with missing fields."""
        json_output = json.dumps([
            {
                "filePath": "test.js",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2
                        # Missing line, column, message
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.js"
        assert result[0]["line"] == 1  # Default value
        assert result[0]["col"] == 1   # Default value
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == ""  # Default value
        assert result[0]["severity"] == "error"

    def test_parse_eslint_stylish_format(self):
        """Test parsing ESLint stylish format output."""
        stylish_output = """
test.js:5:10  error  Variable is not used  no-unused-vars
test.js:10:5  warning  Console statement  no-console
        """.strip()
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "test.js"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is not used"
        assert result[0]["severity"] == "error"
        
        assert result[1]["file"] == "test.js"
        assert result[1]["line"] == 10
        assert result[1]["col"] == 5
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_stylish_format_no_match(self):
        """Test parsing ESLint stylish format with no matching lines."""
        stylish_output = """
This is not a valid ESLint output line
Another invalid line
        """.strip()
        
        result = parse_eslint(stylish_output)
        assert len(result) == 0

    def test_parse_eslint_invalid_json(self):
        """Test parsing ESLint with invalid JSON falls back to stylish."""
        invalid_json = '{"invalid": json}'
        stylish_output = "test.js:5:10  error  Variable is not used  no-unused-vars"
        
        with patch('builtins.print') as mock_print:
            result = parse_eslint(invalid_json + "\n" + stylish_output)
            
            # Should print warning about JSON parsing error
            mock_print.assert_called()
            assert len(result) == 1
            assert result[0]["file"] == "test.js"

    def test_parse_eslint_empty_output(self):
        """Test parsing ESLint with empty output."""
        result = parse_eslint("")
        assert len(result) == 0

    def test_parse_eslint_none_output(self):
        """Test parsing ESLint with None output."""
        result = parse_eslint(None)
        assert len(result) == 0

    def test_parse_jest_valid_output(self):
        """Test parsing Jest output with valid format."""
        jest_output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_failed(self):
        """Test parsing Jest output with no failed tests."""
        jest_output = "Tests:       12 passed, 12 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 12
        assert result["passed"] == 12
        assert result["failed"] == 0

    def test_parse_jest_no_passed(self):
        """Test parsing Jest output with no passed tests."""
        jest_output = "Tests:       5 failed, 5 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 5

    def test_parse_jest_no_match(self):
        """Test parsing Jest output with no matching pattern."""
        jest_output = "This is not a Jest output"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_empty_output(self):
        """Test parsing Jest with empty output."""
        result = parse_jest("")
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_none_output(self):
        """Test parsing Jest with None output."""
        result = parse_jest(None)
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_complex_output(self):
        """Test parsing Jest output with complex format."""
        jest_output = """
Running tests...
✓ Test 1 passed
✗ Test 2 failed
Tests:       1 failed, 1 passed, 2 total
        """.strip()
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 2
        assert result["passed"] == 1
        assert result["failed"] == 1