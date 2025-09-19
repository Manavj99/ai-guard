"""Enhanced tests for typescript parser module to improve coverage."""

import pytest
import json
from unittest.mock import patch
from src.ai_guard.parsers.typescript import parse_eslint, parse_jest


class TestParseEslint:
    """Test parse_eslint function."""

    def test_parse_eslint_json_format(self):
        """Test parsing ESLint JSON format."""
        json_output = json.dumps([
            {
                "filePath": "test.ts",
                "messages": [
                    {
                        "severity": 2,
                        "line": 10,
                        "column": 5,
                        "ruleId": "no-unused-vars",
                        "message": "Variable is unused"
                    },
                    {
                        "severity": 1,
                        "line": 15,
                        "column": 8,
                        "ruleId": "prefer-const",
                        "message": "Use const instead of let"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 2
        
        # Check first finding
        assert result[0]["file"] == "test.ts"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is unused"
        assert result[0]["severity"] == "error"
        
        # Check second finding
        assert result[1]["file"] == "test.ts"
        assert result[1]["line"] == 15
        assert result[1]["col"] == 8
        assert result[1]["rule"] == "eslint:prefer-const"
        assert result[1]["message"] == "Use const instead of let"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_json_format_missing_fields(self):
        """Test parsing ESLint JSON format with missing fields."""
        json_output = json.dumps([
            {
                "filePath": "test.ts",
                "messages": [
                    {
                        "severity": 2,
                        "ruleId": "no-unused-vars",
                        "message": "Variable is unused"
                        # Missing line and column
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.ts"
        assert result[0]["line"] == 1  # Default value
        assert result[0]["col"] == 1   # Default value
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is unused"
        assert result[0]["severity"] == "error"

    def test_parse_eslint_json_format_none_values(self):
        """Test parsing ESLint JSON format with None values."""
        json_output = json.dumps([
            {
                "filePath": "test.ts",
                "messages": [
                    {
                        "severity": 2,
                        "line": None,
                        "column": None,
                        "ruleId": None,
                        "message": None
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.ts"
        assert result[0]["line"] == 1  # Default value
        assert result[0]["col"] == 1   # Default value
        assert result[0]["rule"] == "eslint:unknown"
        assert result[0]["message"] == ""
        assert result[0]["severity"] == "error"

    def test_parse_eslint_json_format_empty_messages(self):
        """Test parsing ESLint JSON format with empty messages."""
        json_output = json.dumps([
            {
                "filePath": "test.ts",
                "messages": []
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 0

    def test_parse_eslint_json_format_multiple_files(self):
        """Test parsing ESLint JSON format with multiple files."""
        json_output = json.dumps([
            {
                "filePath": "file1.ts",
                "messages": [
                    {
                        "severity": 2,
                        "line": 5,
                        "column": 3,
                        "ruleId": "no-console",
                        "message": "Console statement"
                    }
                ]
            },
            {
                "filePath": "file2.ts",
                "messages": [
                    {
                        "severity": 1,
                        "line": 10,
                        "column": 7,
                        "ruleId": "no-var",
                        "message": "Use let or const"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "file1.ts"
        assert result[1]["file"] == "file2.ts"

    def test_parse_eslint_stylish_format(self):
        """Test parsing ESLint stylish format."""
        stylish_output = """test.ts:10:5  error  Variable is unused  no-unused-vars
test.ts:15:8  warning  Use const instead of let  prefer-const"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        
        # Check first finding
        assert result[0]["file"] == "test.ts"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is unused"
        assert result[0]["severity"] == "error"
        
        # Check second finding
        assert result[1]["file"] == "test.ts"
        assert result[1]["line"] == 15
        assert result[1]["col"] == 8
        assert result[1]["rule"] == "eslint:prefer-const"
        assert result[1]["message"] == "Use const instead of let"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_stylish_format_with_whitespace(self):
        """Test parsing ESLint stylish format with whitespace."""
        stylish_output = """
test.ts:10:5  error  Variable is unused  no-unused-vars

test.ts:15:8  warning  Use const instead of let  prefer-const
"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "test.ts"
        assert result[1]["file"] == "test.ts"

    def test_parse_eslint_stylish_format_invalid_lines(self):
        """Test parsing ESLint stylish format with invalid lines."""
        stylish_output = """test.ts:10:5  error  Variable is unused  no-unused-vars
invalid line format
test.ts:15:8  warning  Use const instead of let  prefer-const"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "test.ts"
        assert result[1]["file"] == "test.ts"

    def test_parse_eslint_stylish_format_complex_rule_names(self):
        """Test parsing ESLint stylish format with complex rule names."""
        stylish_output = "test.ts:10:5  error  Message  @typescript-eslint/no-unused-vars"
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["rule"] == "eslint:@typescript-eslint/no-unused-vars"

    def test_parse_eslint_stylish_format_dash_in_rule_names(self):
        """Test parsing ESLint stylish format with dashes in rule names."""
        stylish_output = "test.ts:10:5  error  Message  no-unused-vars"
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 1
        assert result[0]["rule"] == "eslint:no-unused-vars"

    def test_parse_eslint_empty_output(self):
        """Test parsing ESLint with empty output."""
        result = parse_eslint("")
        assert len(result) == 0

    def test_parse_eslint_none_output(self):
        """Test parsing ESLint with None output."""
        result = parse_eslint(None)
        assert len(result) == 0

    def test_parse_eslint_invalid_json_fallback(self):
        """Test parsing ESLint with invalid JSON falls back to stylish."""
        invalid_json = "invalid json content"
        stylish_output = "test.ts:10:5  error  Message  no-unused-vars"
        
        with patch('builtins.print') as mock_print:
            result = parse_eslint(invalid_json + "\n" + stylish_output)
            
            # Should print warning about JSON parsing error
            mock_print.assert_called_once()
            assert "Warning: TypeScript parsing error" in str(mock_print.call_args[0][0])
            
            # Should fall back to stylish parsing
            assert len(result) == 1
            assert result[0]["file"] == "test.ts"

    def test_parse_eslint_json_exception_fallback(self):
        """Test parsing ESLint with JSON exception falls back to stylish."""
        # Create JSON that will cause an exception during parsing
        json_output = '{"incomplete": json'
        stylish_output = "test.ts:10:5  error  Message  no-unused-vars"
        
        with patch('builtins.print') as mock_print:
            result = parse_eslint(json_output + "\n" + stylish_output)
            
            # Should print warning about JSON parsing error
            mock_print.assert_called_once()
            assert "Warning: TypeScript parsing error" in str(mock_print.call_args[0][0])
            
            # Should fall back to stylish parsing
            assert len(result) == 1
            assert result[0]["file"] == "test.ts"


class TestParseJest:
    """Test parse_jest function."""

    def test_parse_jest_standard_format(self):
        """Test parsing Jest standard format."""
        jest_output = "Tests: 1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_failed_tests(self):
        """Test parsing Jest with no failed tests."""
        jest_output = "Tests: 10 passed, 10 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 10
        assert result["passed"] == 10
        assert result["failed"] == 0

    def test_parse_jest_no_passed_tests(self):
        """Test parsing Jest with no passed tests."""
        jest_output = "Tests: 5 failed, 5 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 5

    def test_parse_jest_with_commas(self):
        """Test parsing Jest with commas in output."""
        jest_output = "Tests: 1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_without_commas(self):
        """Test parsing Jest without commas."""
        jest_output = "Tests: 1 failed 12 passed 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_mixed_format(self):
        """Test parsing Jest with mixed format."""
        jest_output = "Tests: 2 failed, 8 passed, 10 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 10
        assert result["passed"] == 8
        assert result["failed"] == 2

    def test_parse_jest_only_total(self):
        """Test parsing Jest with only total count."""
        jest_output = "Tests: 5 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_no_match(self):
        """Test parsing Jest with no matching pattern."""
        jest_output = "No test information found"
        
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

    def test_parse_jest_multiline_output(self):
        """Test parsing Jest with multiline output."""
        jest_output = """Some other output
Tests: 3 failed, 7 passed, 10 total
More output here"""
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 10
        assert result["passed"] == 7
        assert result["failed"] == 3

    def test_parse_jest_case_insensitive(self):
        """Test parsing Jest with different case."""
        jest_output = "tests: 2 failed, 8 passed, 10 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 10
        assert result["passed"] == 8
        assert result["failed"] == 2

    def test_parse_jest_extra_spaces(self):
        """Test parsing Jest with extra spaces."""
        jest_output = "Tests:   1   failed,   12   passed,   13   total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_zero_values(self):
        """Test parsing Jest with zero values."""
        jest_output = "Tests: 0 failed, 0 passed, 0 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_large_numbers(self):
        """Test parsing Jest with large numbers."""
        jest_output = "Tests: 100 failed, 900 passed, 1000 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 1000
        assert result["passed"] == 900
        assert result["failed"] == 100
