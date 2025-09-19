"""Comprehensive tests for utils modules to achieve high coverage."""

import pytest
import tempfile
import os
import subprocess
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

from src.ai_guard.utils.error_formatter import (
    ErrorContext, ErrorSeverity, ErrorCategory,
    format_error, format_coverage_message
)
from src.ai_guard.utils.subprocess_runner import run_command


class TestErrorContext:
    """Test ErrorContext class."""
    
    def test_error_context_creation(self):
        """Test creating ErrorContext."""
        context = ErrorContext(
            file_path="test.py",
            line_number=10,
            column_number=5,
            function_name="test_func",
            code_snippet="print('hello')"
        )
        assert context.file_path == "test.py"
        assert context.line_number == 10
        assert context.column_number == 5
        assert context.function_name == "test_func"
        assert context.code_snippet == "print('hello')"
    
    def test_error_context_minimal(self):
        """Test creating ErrorContext with minimal data."""
        context = ErrorContext(file_path="test.py")
        assert context.file_path == "test.py"
        assert context.line_number is None
        assert context.column_number is None
        assert context.function_name is None
        assert context.code_snippet is None


class TestErrorSeverity:
    """Test ErrorSeverity enum."""
    
    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"


class TestErrorCategory:
    """Test ErrorCategory enum."""
    
    def test_error_category_values(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.SYNTAX == "syntax"
        assert ErrorCategory.TYPE == "type"
        assert ErrorCategory.SECURITY == "security"
        assert ErrorCategory.PERFORMANCE == "performance"
        assert ErrorCategory.STYLE == "style"
        assert ErrorCategory.COVERAGE == "coverage"


class TestFormatError:
    """Test format_error function."""
    
    def test_format_error_basic(self):
        """Test basic error formatting."""
        context = ErrorContext(file_path="test.py", line_number=10)
        formatted = format_error(
            message="Test error",
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYNTAX
        )
        assert "Test error" in formatted
        assert "test.py" in formatted
        assert "line 10" in formatted
    
    def test_format_error_with_function(self):
        """Test error formatting with function context."""
        context = ErrorContext(
            file_path="test.py",
            line_number=10,
            function_name="test_func"
        )
        formatted = format_error(
            message="Test error",
            context=context,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TYPE
        )
        assert "Test error" in formatted
        assert "test_func" in formatted
    
    def test_format_error_with_code_snippet(self):
        """Test error formatting with code snippet."""
        context = ErrorContext(
            file_path="test.py",
            line_number=10,
            code_snippet="print('hello')"
        )
        formatted = format_error(
            message="Test error",
            context=context,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.STYLE
        )
        assert "Test error" in formatted
        assert "print('hello')" in formatted
    
    def test_format_error_critical_severity(self):
        """Test error formatting with critical severity."""
        context = ErrorContext(file_path="test.py")
        formatted = format_error(
            message="Critical error",
            context=context,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY
        )
        assert "Critical error" in formatted
        assert "CRITICAL" in formatted.upper()
    
    def test_format_error_no_context(self):
        """Test error formatting without context."""
        formatted = format_error(
            message="Test error",
            context=None,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PERFORMANCE
        )
        assert "Test error" in formatted
    
    def test_format_error_all_fields(self):
        """Test error formatting with all fields."""
        context = ErrorContext(
            file_path="src/test.py",
            line_number=25,
            column_number=10,
            function_name="complex_function",
            code_snippet="result = complex_calculation()"
        )
        formatted = format_error(
            message="Complex error message",
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.TYPE
        )
        assert "Complex error message" in formatted
        assert "src/test.py" in formatted
        assert "line 25" in formatted
        assert "column 10" in formatted
        assert "complex_function" in formatted
        assert "complex_calculation()" in formatted


class TestFormatCoverageMessage:
    """Test format_coverage_message function."""
    
    def test_format_coverage_message_basic(self):
        """Test basic coverage message formatting."""
        message = format_coverage_message(
            current_coverage=75.5,
            required_coverage=80.0,
            file_path="test.py"
        )
        assert "75.5%" in message
        assert "80.0%" in message
        assert "test.py" in message
    
    def test_format_coverage_message_above_threshold(self):
        """Test coverage message when above threshold."""
        message = format_coverage_message(
            current_coverage=85.0,
            required_coverage=80.0,
            file_path="test.py"
        )
        assert "85.0%" in message
        assert "80.0%" in message
        assert "test.py" in message
    
    def test_format_coverage_message_below_threshold(self):
        """Test coverage message when below threshold."""
        message = format_coverage_message(
            current_coverage=70.0,
            required_coverage=80.0,
            file_path="test.py"
        )
        assert "70.0%" in message
        assert "80.0%" in message
        assert "test.py" in message
    
    def test_format_coverage_message_exact_threshold(self):
        """Test coverage message when exactly at threshold."""
        message = format_coverage_message(
            current_coverage=80.0,
            required_coverage=80.0,
            file_path="test.py"
        )
        assert "80.0%" in message
        assert "test.py" in message
    
    def test_format_coverage_message_no_file(self):
        """Test coverage message without file path."""
        message = format_coverage_message(
            current_coverage=75.0,
            required_coverage=80.0,
            file_path=None
        )
        assert "75.0%" in message
        assert "80.0%" in message
    
    def test_format_coverage_message_zero_coverage(self):
        """Test coverage message with zero coverage."""
        message = format_coverage_message(
            current_coverage=0.0,
            required_coverage=80.0,
            file_path="test.py"
        )
        assert "0.0%" in message
        assert "80.0%" in message
        assert "test.py" in message
    
    def test_format_coverage_message_high_coverage(self):
        """Test coverage message with high coverage."""
        message = format_coverage_message(
            current_coverage=95.5,
            required_coverage=80.0,
            file_path="test.py"
        )
        assert "95.5%" in message
        assert "80.0%" in message
        assert "test.py" in message


class TestRunCommand:
    """Test run_command function."""
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        
        result = run_command(["echo", "test"])
        assert result.returncode == 0
        assert result.stdout == "Success"
        assert result.stderr == ""
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Error occurred"
        
        result = run_command(["false"])
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "Error occurred"
    
    @patch('subprocess.run')
    def test_run_command_with_input(self, mock_run):
        """Test command execution with input."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Processed input"
        mock_run.return_value.stderr = ""
        
        result = run_command(["cat"], input_text="test input")
        assert result.returncode == 0
        assert result.stdout == "Processed input"
    
    @patch('subprocess.run')
    def test_run_command_with_cwd(self, mock_run):
        """Test command execution with working directory."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        
        result = run_command(["pwd"], cwd="/tmp")
        assert result.returncode == 0
        assert result.stdout == "Success"
    
    @patch('subprocess.run')
    def test_run_command_with_env(self, mock_run):
        """Test command execution with environment variables."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        
        env = {"TEST_VAR": "test_value"}
        result = run_command(["env"], env=env)
        assert result.returncode == 0
        assert result.stdout == "Success"
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command execution with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("sleep", 1)
        
        result = run_command(["sleep", "10"], timeout=1)
        assert result.returncode == -1
        assert "timeout" in result.stderr.lower()
    
    @patch('subprocess.run')
    def test_run_command_file_not_found(self, mock_run):
        """Test command execution with file not found."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        result = run_command(["nonexistent_command"])
        assert result.returncode == -1
        assert "not found" in result.stderr.lower()
    
    @patch('subprocess.run')
    def test_run_command_permission_error(self, mock_run):
        """Test command execution with permission error."""
        mock_run.side_effect = PermissionError("Permission denied")
        
        result = run_command(["restricted_command"])
        assert result.returncode == -1
        assert "permission" in result.stderr.lower()
    
    def test_run_command_empty_command(self):
        """Test command execution with empty command."""
        result = run_command([])
        assert result.returncode == -1
        assert "empty" in result.stderr.lower()
    
    def test_run_command_none_command(self):
        """Test command execution with None command."""
        result = run_command(None)
        assert result.returncode == -1
        assert "invalid" in result.stderr.lower()
    
    @patch('subprocess.run')
    def test_run_command_large_output(self, mock_run):
        """Test command execution with large output."""
        large_output = "x" * 10000
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = large_output
        mock_run.return_value.stderr = ""
        
        result = run_command(["echo", "large"])
        assert result.returncode == 0
        assert len(result.stdout) == 10000
    
    @patch('subprocess.run')
    def test_run_command_binary_output(self, mock_run):
        """Test command execution with binary output."""
        binary_output = b"\x00\x01\x02\x03"
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = binary_output
        mock_run.return_value.stderr = b""
        
        result = run_command(["cat", "binary_file"])
        assert result.returncode == 0
        assert isinstance(result.stdout, str)
