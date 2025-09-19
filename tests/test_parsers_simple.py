"""Simple tests for parsers to achieve high coverage."""

import pytest
import json
from unittest.mock import patch

from src.ai_guard.parsers.common import (
    _extract_mypy_rule,
    _RULE_NORMALIZERS,
    normalize_rule,
)

from src.ai_guard.parsers.typescript import (
    parse_eslint,
    parse_jest,
)


class TestExtractMypyRule:
    """Test MyPy rule extraction."""
    
    def test_extract_mypy_rule_with_brackets(self):
        """Test extracting rule from bracketed format."""
        assert _extract_mypy_rule("error[name-defined]") == "mypy:name-defined"
        assert _extract_mypy_rule("warning[unused-var]") == "mypy:unused-var"
    
    def test_extract_mypy_rule_without_brackets(self):
        """Test extracting rule from non-bracketed format."""
        assert _extract_mypy_rule("error") == "mypy:error"
        assert _extract_mypy_rule("warning") == "mypy:warning"
    
    def test_extract_mypy_rule_already_prefixed(self):
        """Test extracting rule that's already prefixed."""
        assert _extract_mypy_rule("mypy:name-defined") == "mypy:name-defined"
    
    def test_extract_mypy_rule_malformed_brackets(self):
        """Test extracting rule with malformed brackets."""
        assert _extract_mypy_rule("error[") == "mypy:error["
        assert _extract_mypy_rule("error]") == "mypy:error]"
    
    def test_extract_mypy_rule_empty(self):
        """Test extracting rule from empty string."""
        assert _extract_mypy_rule("") == "mypy:"
    
    def test_extract_mypy_rule_none(self):
        """Test extracting rule from None."""
        # This will raise a TypeError, which is expected behavior
        with pytest.raises(TypeError):
            _extract_mypy_rule(None)


class TestNormalizeRule:
    """Test rule normalization function."""
    
    def test_normalize_rule_flake8_with_colon(self):
        """Test normalizing flake8 rule with colon."""
        result = normalize_rule("flake8", "flake8:E501")
        assert result == "flake8:E501"
    
    def test_normalize_rule_flake8_without_colon(self):
        """Test normalizing flake8 rule without colon."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"
    
    def test_normalize_rule_mypy_with_brackets(self):
        """Test normalizing mypy rule with brackets."""
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"
    
    def test_normalize_rule_unknown_tool(self):
        """Test normalizing rule for unknown tool."""
        result = normalize_rule("unknown", "rule")
        assert result == "unknown:rule"
    
    def test_normalize_rule_none_tool(self):
        """Test normalizing rule with None tool."""
        result = normalize_rule(None, "rule")
        assert result == "none:rule"
    
    def test_normalize_rule_none_raw(self):
        """Test normalizing rule with None raw value."""
        result = normalize_rule("flake8", None)
        assert result == "flake8:None"
    
    def test_normalize_rule_empty_raw(self):
        """Test normalizing rule with empty raw value."""
        result = normalize_rule("flake8", "")
        assert result == "flake8:"


class TestParseEslint:
    """Test ESLint output parsing."""
    
    def test_parse_eslint_empty(self):
        """Test parsing empty ESLint output."""
        result = parse_eslint("")
        assert result == []
    
    def test_parse_eslint_none(self):
        """Test parsing None ESLint output."""
        result = parse_eslint(None)
        assert result == []
    
    def test_parse_eslint_json_format(self):
        """Test parsing ESLint JSON format."""
        json_output = json.dumps([
            {
                "filePath": "src/test.ts",
                "messages": [
                    {
                        "severity": 2,
                        "line": 10,
                        "column": 5,
                        "ruleId": "no-unused-vars",
                        "message": "Variable 'x' is defined but never used"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable 'x' is defined but never used"
        assert result[0]["severity"] == "error"
    
    def test_parse_eslint_json_format_invalid_json(self):
        """Test parsing invalid ESLint JSON."""
        with patch('builtins.print') as mock_print:
            result = parse_eslint("invalid json")
            assert result == []
            mock_print.assert_called()
    
    def test_parse_eslint_stylish_format(self):
        """Test parsing ESLint stylish format."""
        stylish_output = "src/test.ts:10:5  error  Variable 'x' is defined but never used  no-unused-vars"
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable 'x' is defined but never used"
        assert result[0]["severity"] == "error"


class TestParseJest:
    """Test Jest output parsing."""
    
    def test_parse_jest_empty(self):
        """Test parsing empty Jest output."""
        result = parse_jest("")
        assert result == {"tests": 0, "passed": 0, "failed": 0}
    
    def test_parse_jest_none(self):
        """Test parsing None Jest output."""
        result = parse_jest(None)
        assert result == {"tests": 0, "passed": 0, "failed": 0}
    
    def test_parse_jest_all_passed(self):
        """Test parsing Jest output with all tests passed."""
        output = "Tests:       12 passed, 12 total"
        result = parse_jest(output)
        
        assert result["tests"] == 12
        assert result["passed"] == 12
        assert result["failed"] == 0
    
    def test_parse_jest_some_failed(self):
        """Test parsing Jest output with some tests failed."""
        output = "Tests:       2 failed, 10 passed, 12 total"
        result = parse_jest(output)
        
        assert result["tests"] == 12
        assert result["passed"] == 10
        assert result["failed"] == 2
    
    def test_parse_jest_invalid_format(self):
        """Test parsing Jest output with invalid format."""
        output = "Invalid test output format"
        result = parse_jest(output)
        
        assert result == {"tests": 0, "passed": 0, "failed": 0}