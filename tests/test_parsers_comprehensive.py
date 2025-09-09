"""Comprehensive tests for parsers module to improve coverage."""

import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.parsers.common import normalize_rule, _extract_mypy_rule
from src.ai_guard.parsers.typescript import parse_eslint, parse_jest


class TestCommonParsers:
    """Test common parser functionality."""

    def test_normalize_rule_flake8(self):
        """Test flake8 rule normalization."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_mypy(self):
        """Test mypy rule normalization."""
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"

    def test_normalize_rule_bandit(self):
        """Test bandit rule normalization."""
        result = normalize_rule("bandit", "B101")
        assert result == "bandit:B101"

    def test_normalize_rule_eslint(self):
        """Test eslint rule normalization."""
        result = normalize_rule("eslint", "no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_unknown_tool(self):
        """Test rule normalization for unknown tool."""
        result = normalize_rule("unknown", "rule123")
        assert result == "unknown:rule123"

    def test_normalize_rule_empty_tool(self):
        """Test rule normalization with empty tool."""
        result = normalize_rule("", "rule123")
        assert result == ":rule123"

    def test_normalize_rule_none_tool(self):
        """Test rule normalization with None tool."""
        result = normalize_rule(None, "rule123")
        assert result == "none:rule123"

    def test_extract_mypy_rule_basic(self):
        """Test basic mypy rule extraction."""
        result = _extract_mypy_rule("error[name-defined]")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_no_brackets(self):
        """Test mypy rule extraction without brackets."""
        result = _extract_mypy_rule("error")
        assert result == "mypy:error"

    def test_extract_mypy_rule_already_prefixed(self):
        """Test mypy rule extraction with already prefixed rule."""
        result = _extract_mypy_rule("mypy:name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_malformed(self):
        """Test mypy rule extraction with malformed input."""
        result = _extract_mypy_rule("error[incomplete")
        assert result == "mypy:error[incomplete"


class TestTypeScriptParsers:
    """Test TypeScript parser functionality."""

    def test_parse_eslint_json(self):
        """Test parsing ESLint JSON output."""
        json_output = '''[
            {
                "filePath": "src/test.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 5,
                        "column": 10,
                        "message": "Variable 'x' is defined but never used"
                    }
                ]
            }
        ]'''
        
        result = parse_eslint(json_output)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["severity"] == "error"

    def test_parse_eslint_stylish(self):
        """Test parsing ESLint stylish output."""
        stylish_output = "src/test.ts:5:10  error  Variable 'x' is defined but never used  no-unused-vars"
        
        result = parse_eslint(stylish_output)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"

    def test_parse_eslint_empty(self):
        """Test parsing empty ESLint output."""
        result = parse_eslint("")
        assert result == []

    def test_parse_eslint_none(self):
        """Test parsing None ESLint output."""
        result = parse_eslint(None)
        assert result == []

    def test_parse_jest_basic(self):
        """Test parsing Jest output."""
        jest_output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        assert isinstance(result, dict)
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_failures(self):
        """Test parsing Jest output with no failures."""
        jest_output = "Tests:       15 passed, 15 total"
        
        result = parse_jest(jest_output)
        assert result["tests"] == 15
        assert result["passed"] == 15
        assert result["failed"] == 0

    def test_parse_jest_empty(self):
        """Test parsing empty Jest output."""
        result = parse_jest("")
        assert result == {"tests": 0, "passed": 0, "failed": 0}

    def test_parse_jest_none(self):
        """Test parsing None Jest output."""
        result = parse_jest(None)
        assert result == {"tests": 0, "passed": 0, "failed": 0}


class TestParserEdgeCases:
    """Test parser edge cases and error handling."""

    def test_parse_eslint_invalid_json(self):
        """Test parsing invalid ESLint JSON."""
        invalid_json = "invalid json content"
        result = parse_eslint(invalid_json)
        assert isinstance(result, list)
        # Should fallback to stylish parsing

    def test_parse_eslint_malformed_stylish(self):
        """Test parsing malformed stylish output."""
        malformed_output = "not a valid stylish line"
        result = parse_eslint(malformed_output)
        assert result == []

    def test_parse_jest_malformed(self):
        """Test parsing malformed Jest output."""
        malformed_output = "not a valid jest summary"
        result = parse_jest(malformed_output)
        assert result == {"tests": 0, "passed": 0, "failed": 0}

    def test_normalize_rule_edge_cases(self):
        """Test rule normalization edge cases."""
        # Test with None values
        result = normalize_rule("flake8", None)
        assert result == "flake8:None"
        
        # Test with empty string
        result = normalize_rule("flake8", "")
        assert result == "flake8:"
