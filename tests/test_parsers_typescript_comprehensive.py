"""Comprehensive tests for parsers.typescript module."""

import json
import pytest
from unittest.mock import patch

from src.ai_guard.parsers.typescript import (
    parse_eslint,
    parse_jest,
)


class TestParseEslint:
    """Test parse_eslint function."""

    def test_parse_eslint_json_format(self):
        """Test parsing ESLint JSON output."""
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
        
        # Check first finding
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable 'x' is defined but never used"
        assert result[0]["severity"] == "error"
        
        # Check second finding
        assert result[1]["file"] == "src/test.ts"
        assert result[1]["line"] == 8
        assert result[1]["col"] == 5
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Unexpected console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_json_format_multiple_files(self):
        """Test parsing ESLint JSON output with multiple files."""
        json_output = json.dumps([
            {
                "filePath": "src/file1.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 1,
                        "column": 1,
                        "message": "Message 1"
                    }
                ]
            },
            {
                "filePath": "src/file2.ts",
                "messages": [
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "line": 2,
                        "column": 2,
                        "message": "Message 2"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/file1.ts"
        assert result[1]["file"] == "src/file2.ts"

    def test_parse_eslint_json_format_missing_fields(self):
        """Test parsing ESLint JSON output with missing fields."""
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
        assert result[0]["line"] == 1  # Default value
        assert result[0]["col"] == 1   # Default value
        assert result[0]["rule"] == "eslint:unknown"
        assert result[0]["message"] == ""
        assert result[0]["severity"] == "warning"  # Default for severity != 2

    def test_parse_eslint_json_format_empty_messages(self):
        """Test parsing ESLint JSON output with empty messages."""
        json_output = json.dumps([
            {
                "filePath": "src/test.ts",
                "messages": []
            }
        ])
        
        result = parse_eslint(json_output)
        assert result == []

    def test_parse_eslint_json_format_no_filepath(self):
        """Test parsing ESLint JSON output without filePath."""
        json_output = json.dumps([
            {
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 5,
                        "column": 10,
                        "message": "Test message"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] is None

    def test_parse_eslint_stylish_format(self):
        """Test parsing ESLint stylish format."""
        stylish_output = """src/test.ts:5:10  error  Variable 'x' is defined but never used  no-unused-vars
src/test.ts:8:5  warning  Unexpected console statement  no-console"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        
        # Check first finding
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable 'x' is defined but never used"
        assert result[0]["severity"] == "error"
        
        # Check second finding
        assert result[1]["file"] == "src/test.ts"
        assert result[1]["line"] == 8
        assert result[1]["col"] == 5
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Unexpected console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_stylish_format_multiple_files(self):
        """Test parsing ESLint stylish format with multiple files."""
        stylish_output = """src/file1.ts:1:1  error  Message 1  rule1
src/file2.ts:2:2  warning  Message 2  rule2"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/file1.ts"
        assert result[1]["file"] == "src/file2.ts"

    def test_parse_eslint_stylish_format_no_matches(self):
        """Test parsing ESLint stylish format with no matching lines."""
        stylish_output = """This is not a valid ESLint output line
Another invalid line"""
        
        result = parse_eslint(stylish_output)
        assert result == []

    def test_parse_eslint_stylish_format_mixed_lines(self):
        """Test parsing ESLint stylish format with mixed valid and invalid lines."""
        stylish_output = """src/test.ts:5:10  error  Valid message  rule1
This is not a valid line
src/test.ts:8:5  warning  Another valid message  rule2"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/test.ts"
        assert result[1]["file"] == "src/test.ts"

    def test_parse_eslint_invalid_json_fallback(self):
        """Test that invalid JSON falls back to stylish format."""
        invalid_json = "This is not valid JSON"
        
        with patch("builtins.print") as mock_print:
            result = parse_eslint(invalid_json)
            
            # Should print warning about JSON parsing error
            mock_print.assert_called_once()
            assert "Warning: TypeScript parsing error:" in str(mock_print.call_args[0][0])
        
        assert result == []

    def test_parse_eslint_json_exception_fallback(self):
        """Test that JSON parsing exception falls back to stylish format."""
        json_output = '{"invalid": json}'  # Invalid JSON
        
        with patch("builtins.print") as mock_print:
            result = parse_eslint(json_output)
            
            # Should print warning about JSON parsing error
            mock_print.assert_called_once()
            assert "Warning: TypeScript parsing error:" in str(mock_print.call_args[0][0])
        
        assert result == []

    def test_parse_eslint_none_input(self):
        """Test with None input."""
        result = parse_eslint(None)
        assert result == []

    def test_parse_eslint_empty_input(self):
        """Test with empty input."""
        result = parse_eslint("")
        assert result == []

    def test_parse_eslint_whitespace_input(self):
        """Test with whitespace-only input."""
        result = parse_eslint("   \n  \t  ")
        assert result == []

    def test_parse_eslint_stylish_format_edge_cases(self):
        """Test stylish format with edge cases."""
        # Test with extra whitespace
        stylish_output = "  src/test.ts:5:10  error  Message  rule1  "
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "src/test.ts"
        assert result[0]["line"] == 5
        assert result[0]["col"] == 10
        assert result[0]["rule"] == "eslint:rule1"
        assert result[0]["message"] == "Message"
        assert result[0]["severity"] == "error"

    def test_parse_eslint_stylish_format_complex_message(self):
        """Test stylish format with complex message containing spaces."""
        stylish_output = "src/test.ts:5:10  error  This is a complex message with spaces  rule1"
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["message"] == "This is a complex message with spaces"

    def test_parse_eslint_stylish_format_rule_with_dashes(self):
        """Test stylish format with rule containing dashes."""
        stylish_output = "src/test.ts:5:10  error  Message  no-unused-vars"
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["rule"] == "eslint:no-unused-vars"


class TestParseJest:
    """Test parse_jest function."""

    def test_parse_jest_standard_format(self):
        """Test parsing standard Jest output format."""
        output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_failed_tests(self):
        """Test parsing Jest output with no failed tests."""
        output = "Tests:       12 passed, 12 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 12
        assert result["passed"] == 12
        assert result["failed"] == 0

    def test_parse_jest_no_passed_tests(self):
        """Test parsing Jest output with no passed tests."""
        output = "Tests:       5 failed, 5 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 5

    def test_parse_jest_only_total(self):
        """Test parsing Jest output with only total count."""
        output = "Tests:       10 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 10
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_different_order(self):
        """Test parsing Jest output with different order."""
        output = "Tests:       12 passed, 1 failed, 13 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_with_commas(self):
        """Test parsing Jest output with commas."""
        output = "Tests:       1,234 failed, 5,678 passed, 6,912 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 6912
        assert result["passed"] == 5678
        assert result["failed"] == 1234

    def test_parse_jest_no_match(self):
        """Test parsing Jest output with no matching pattern."""
        output = "This is not a Jest output"
        
        result = parse_jest(output)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_empty_input(self):
        """Test parsing Jest output with empty input."""
        result = parse_jest("")
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_none_input(self):
        """Test parsing Jest output with None input."""
        result = parse_jest(None)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_whitespace_input(self):
        """Test parsing Jest output with whitespace-only input."""
        result = parse_jest("   \n  \t  ")
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_multiple_matches(self):
        """Test parsing Jest output with multiple matches (should take first)."""
        output = """Some other text
Tests:       1 failed, 12 passed, 13 total
Tests:       5 failed, 10 passed, 15 total
More text"""
        
        result = parse_jest(output)
        
        # Should match the first occurrence
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_partial_match(self):
        """Test parsing Jest output with partial match."""
        output = "Tests:       1 failed, 12 passed"  # Missing total
        
        result = parse_jest(output)
        
        # Should calculate total from failed + passed
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_zero_values(self):
        """Test parsing Jest output with zero values."""
        output = "Tests:       0 failed, 0 passed, 0 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_large_numbers(self):
        """Test parsing Jest output with large numbers."""
        output = "Tests:       999999 failed, 888888 passed, 1888887 total"
        
        result = parse_jest(output)
        
        assert result["tests"] == 1888887
        assert result["passed"] == 888888
        assert result["failed"] == 999999

    def test_parse_jest_extra_whitespace(self):
        """Test parsing Jest output with extra whitespace."""
        output = "  Tests:       1 failed, 12 passed, 13 total  "
        
        result = parse_jest(output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_case_insensitive(self):
        """Test parsing Jest output with different case."""
        output = "tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(output)
        
        # Should not match due to case sensitivity
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0