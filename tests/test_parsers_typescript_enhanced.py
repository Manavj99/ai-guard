"""Enhanced tests for parsers/typescript module to achieve 80%+ coverage."""

import pytest
import json
from unittest.mock import patch

from src.ai_guard.parsers.typescript import (
    parse_eslint,
    parse_jest
)


class TestParseEslint:
    """Test parse_eslint function."""

    def test_parse_eslint_json_format(self):
        """Test parsing ESLint JSON format."""
        json_output = json.dumps([
            {
                "filePath": "src/file.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 10,
                        "column": 5,
                        "message": "Variable is defined but never used"
                    },
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "line": 15,
                        "column": 1,
                        "message": "Unexpected console statement"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/file.ts"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is defined but never used"
        assert result[0]["severity"] == "error"
        
        assert result[1]["file"] == "src/file.ts"
        assert result[1]["line"] == 15
        assert result[1]["col"] == 1
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Unexpected console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_json_format_missing_fields(self):
        """Test parsing ESLint JSON with missing optional fields."""
        json_output = json.dumps([
            {
                "filePath": "src/file.ts",
                "messages": [
                    {
                        "ruleId": None,
                        "severity": 2,
                        "line": None,
                        "column": None,
                        "message": None
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "src/file.ts"
        assert result[0]["line"] == 1
        assert result[0]["col"] == 1
        assert result[0]["rule"] == "eslint:unknown"
        assert result[0]["message"] is None
        assert result[0]["severity"] == "error"

    def test_parse_eslint_json_format_empty_messages(self):
        """Test parsing ESLint JSON with empty messages array."""
        json_output = json.dumps([
            {
                "filePath": "src/file.ts",
                "messages": []
            }
        ])
        
        result = parse_eslint(json_output)
        assert len(result) == 0

    def test_parse_eslint_json_format_missing_filepath(self):
        """Test parsing ESLint JSON with missing filePath."""
        json_output = json.dumps([
            {
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 10,
                        "column": 5,
                        "message": "Variable is defined but never used"
                    }
                ]
            }
        ])
        
        result = parse_eslint(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] is None

    def test_parse_eslint_json_format_invalid_json(self):
        """Test parsing ESLint with invalid JSON falls back to text parsing."""
        invalid_json = "invalid json content"
        
        with patch('builtins.print') as mock_print:
            result = parse_eslint(invalid_json)
            mock_print.assert_called_once()
            assert "Warning: TypeScript parsing error" in mock_print.call_args[0][0]
            assert result == []

    def test_parse_eslint_json_format_exception_handling(self):
        """Test parsing ESLint JSON with exception during processing."""
        json_output = json.dumps([
            {
                "filePath": "src/file.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "line": 10,
                        "column": 5,
                        "message": "Variable is defined but never used"
                    }
                ]
            }
        ])
        
        with patch('src.ai_guard.parsers.typescript.json.loads', side_effect=Exception("JSON error")):
            with patch('builtins.print') as mock_print:
                result = parse_eslint(json_output)
                mock_print.assert_called_once()
                assert "Warning: TypeScript parsing error" in mock_print.call_args[0][0]
                assert result == []

    def test_parse_eslint_stylish_format(self):
        """Test parsing ESLint stylish format."""
        stylish_output = """src/file.ts:10:5  error  Variable is defined but never used  no-unused-vars
src/file.ts:15:1  warning  Unexpected console statement  no-console"""
        
        result = parse_eslint(stylish_output)
        
        assert len(result) == 2
        assert result[0]["file"] == "src/file.ts"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 5
        assert result[0]["rule"] == "eslint:no-unused-vars"
        assert result[0]["message"] == "Variable is defined but never used"
        assert result[0]["severity"] == "error"
        
        assert result[1]["file"] == "src/file.ts"
        assert result[1]["line"] == 15
        assert result[1]["col"] == 1
        assert result[1]["rule"] == "eslint:no-console"
        assert result[1]["message"] == "Unexpected console statement"
        assert result[1]["severity"] == "warning"

    def test_parse_eslint_stylish_format_no_matches(self):
        """Test parsing ESLint stylish format with no matching lines."""
        stylish_output = """Some other output that doesn't match the pattern"""
        
        result = parse_eslint(stylish_output)
        assert result == []

    def test_parse_eslint_stylish_format_partial_matches(self):
        """Test parsing ESLint stylish format with partial matches."""
        stylish_output = """src/file.ts:10:5  error  Variable is defined but never used  no-unused-vars
Some other line that doesn't match
src/file.ts:15:1  warning  Unexpected console statement  no-console"""
        
        result = parse_eslint(stylish_output)
        assert len(result) == 2

    def test_parse_eslint_empty_output(self):
        """Test parsing ESLint with empty output."""
        result = parse_eslint("")
        assert result == []

    def test_parse_eslint_none_output(self):
        """Test parsing ESLint with None output."""
        result = parse_eslint(None)
        assert result == []

    def test_parse_eslint_mixed_format(self):
        """Test parsing ESLint with mixed JSON and text format."""
        mixed_output = """{"invalid": json}
src/file.ts:10:5  error  Variable is defined but never used  no-unused-vars"""
        
        result = parse_eslint(mixed_output)
        assert len(result) == 1
        assert result[0]["file"] == "src/file.ts"

    def test_parse_eslint_stylish_format_edge_cases(self):
        """Test parsing ESLint stylish format with edge cases."""
        stylish_output = """src/file.ts:1:1  error  Message with spaces  rule-name
src/file.ts:999:999  warning  Another message  another-rule"""
        
        result = parse_eslint(stylish_output)
        assert len(result) == 2
        assert result[0]["line"] == 1
        assert result[0]["col"] == 1
        assert result[1]["line"] == 999
        assert result[1]["col"] == 999


class TestParseJest:
    """Test parse_jest function."""

    def test_parse_jest_standard_format(self):
        """Test parsing Jest standard format."""
        jest_output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_failed(self):
        """Test parsing Jest with no failed tests."""
        jest_output = "Tests:       12 passed, 12 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 12
        assert result["passed"] == 12
        assert result["failed"] == 0

    def test_parse_jest_no_passed(self):
        """Test parsing Jest with no passed tests."""
        jest_output = "Tests:       5 failed, 5 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 5

    def test_parse_jest_only_total(self):
        """Test parsing Jest with only total count."""
        jest_output = "Tests:       10 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 10
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_no_matches(self):
        """Test parsing Jest with no matching pattern."""
        jest_output = "Some other output that doesn't match"
        
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

    def test_parse_jest_whitespace_variations(self):
        """Test parsing Jest with various whitespace patterns."""
        jest_output = "Tests:   1 failed,   12 passed,   13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_no_commas(self):
        """Test parsing Jest without commas."""
        jest_output = "Tests:       1 failed 12 passed 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_different_order(self):
        """Test parsing Jest with different order of counts."""
        jest_output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_large_numbers(self):
        """Test parsing Jest with large numbers."""
        jest_output = "Tests:       1000 failed, 2000 passed, 3000 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 3000
        assert result["passed"] == 2000
        assert result["failed"] == 1000

    def test_parse_jest_zero_values(self):
        """Test parsing Jest with zero values."""
        jest_output = "Tests:       0 failed, 0 passed, 0 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_parse_jest_missing_total(self):
        """Test parsing Jest with missing total (should calculate)."""
        jest_output = "Tests:       1 failed, 12 passed, 13 total"
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1

    def test_parse_jest_multiple_matches(self):
        """Test parsing Jest with multiple matching lines (first match wins)."""
        jest_output = """Tests:       1 failed, 12 passed, 13 total
Tests:       5 failed, 10 passed, 15 total"""
        
        result = parse_jest(jest_output)
        
        assert result["tests"] == 13
        assert result["passed"] == 12
        assert result["failed"] == 1
