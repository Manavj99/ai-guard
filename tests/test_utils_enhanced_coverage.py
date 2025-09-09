"""Enhanced tests for utils modules to significantly improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open

from src.ai_guard.utils.error_formatter import (
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    format_error,
    format_coverage_message
)

from src.ai_guard.utils.subprocess_runner import (
    run_cmd,
    run_command,
    _format_command_output
)


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_error_context_creation(self):
        """Test ErrorContext creation with all fields."""
        context = ErrorContext(
            module="test_module",
            function="test_function",
            tool="test_tool",
            file_path="test.py",
            line_number=10
        )
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.tool == "test_tool"
        assert context.file_path == "test.py"
        assert context.line_number == 10

    def test_error_context_minimal(self):
        """Test ErrorContext creation with minimal fields."""
        context = ErrorContext(
            module="test_module",
            function="test_function",
            tool="test_tool"
        )
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.tool == "test_tool"
        assert context.file_path is None
        assert context.line_number is None


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.INFO == "info"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.CRITICAL == "critical"


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_error_category_values(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.SYNTAX == "syntax"
        assert ErrorCategory.LOGIC == "logic"
        assert ErrorCategory.PERFORMANCE == "performance"
        assert ErrorCategory.SECURITY == "security"
        assert ErrorCategory.STYLE == "style"
        assert ErrorCategory.EXECUTION == "execution"
        assert ErrorCategory.CONFIGURATION == "configuration"
        assert ErrorCategory.UNKNOWN == "unknown"


class TestFormatError:
    """Test format_error function."""

    def test_format_error_basic(self):
        """Test format_error with basic parameters."""
        context = ErrorContext("test_module", "test_function", "test_tool")
        result = format_error("Test message", ErrorSeverity.ERROR, ErrorCategory.LOGIC, context)
        
        assert "Test message" in result
        assert "ERROR" in result
        assert "LOGIC" in result
        assert "test_module" in result
        assert "test_function" in result
        assert "test_tool" in result

    def test_format_error_with_file_info(self):
        """Test format_error with file information."""
        context = ErrorContext(
            "test_module", "test_function", "test_tool",
            file_path="test.py", line_number=10
        )
        result = format_error("Test message", ErrorSeverity.WARNING, ErrorCategory.SYNTAX, context)
        
        assert "test.py" in result
        assert "10" in result

    def test_format_error_different_severities(self):
        """Test format_error with different severities."""
        context = ErrorContext("test_module", "test_function", "test_tool")
        
        for severity in ErrorSeverity:
            result = format_error("Test message", severity, ErrorCategory.LOGIC, context)
            assert severity.value.upper() in result

    def test_format_error_different_categories(self):
        """Test format_error with different categories."""
        context = ErrorContext("test_module", "test_function", "test_tool")
        
        for category in ErrorCategory:
            result = format_error("Test message", ErrorSeverity.ERROR, category, context)
            assert category.value.upper() in result

    def test_format_error_minimal_context(self):
        """Test format_error with minimal context."""
        context = ErrorContext("test_module", "test_function", "test_tool")
        result = format_error("Test message", ErrorSeverity.ERROR, ErrorCategory.LOGIC, context)
        
        assert "Test message" in result
        assert "ERROR" in result
        assert "LOGIC" in result

    def test_format_error_empty_message(self):
        """Test format_error with empty message."""
        context = ErrorContext("test_module", "test_function", "test_tool")
        result = format_error("", ErrorSeverity.ERROR, ErrorCategory.LOGIC, context)
        
        assert "ERROR" in result
        assert "LOGIC" in result


class TestFormatCoverageMessage:
    """Test format_coverage_message function."""

    def test_format_coverage_message_passed(self):
        """Test format_coverage_message with passing coverage."""
        result = format_coverage_message(85.5, 80.0)
        assert "85.5%" in result
        assert "80.0%" in result
        assert "PASSED" in result

    def test_format_coverage_message_failed(self):
        """Test format_coverage_message with failing coverage."""
        result = format_coverage_message(75.0, 80.0)
        assert "75.0%" in result
        assert "80.0%" in result
        assert "FAILED" in result

    def test_format_coverage_message_exact_threshold(self):
        """Test format_coverage_message with exact threshold."""
        result = format_coverage_message(80.0, 80.0)
        assert "80.0%" in result
        assert "PASSED" in result

    def test_format_coverage_message_zero_threshold(self):
        """Test format_coverage_message with zero threshold."""
        result = format_coverage_message(50.0, 0.0)
        assert "50.0%" in result
        assert "0.0%" in result
        assert "PASSED" in result

    def test_format_coverage_message_high_coverage(self):
        """Test format_coverage_message with high coverage."""
        result = format_coverage_message(99.9, 80.0)
        assert "99.9%" in result
        assert "80.0%" in result
        assert "PASSED" in result


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_error_context_creation(self):
        """Test ErrorContext creation with all fields."""
        context = ErrorContext(
            module="test_module",
            function="test_function",
            tool="test_tool",
            file_path="test.py",
            line_number=10
        )
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.tool == "test_tool"
        assert context.file_path == "test.py"
        assert context.line_number == 10

    def test_error_context_minimal(self):
        """Test ErrorContext creation with minimal fields."""
        context = ErrorContext(
            module="test_module",
            function="test_function",
            tool="test_tool"
        )
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.tool == "test_tool"
        assert context.file_path is None
        assert context.line_number is None


class TestSubprocessRunner:
    """Test subprocess runner functions."""

    @patch('subprocess.run')
    def test_run_cmd_success(self, mock_run):
        """Test run_cmd with successful execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        returncode, output = run_cmd(["test", "command"])
        assert returncode == 0
        assert output == "success output"

    @patch('subprocess.run')
    def test_run_cmd_failure(self, mock_run):
        """Test run_cmd with failed execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        returncode, output = run_cmd(["test", "command"])
        assert returncode == 1
        assert output == "error message"

    @patch('subprocess.run')
    def test_run_cmd_file_not_found(self, mock_run):
        """Test run_cmd with file not found error."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        with pytest.raises(ToolExecutionError):
            run_cmd(["nonexistent", "command"])

    @patch('subprocess.run')
    def test_run_cmd_timeout(self, mock_run):
        """Test run_cmd with timeout error."""
        mock_run.side_effect = TimeoutError("Command timed out")
        
        with pytest.raises(ToolExecutionError):
            run_cmd(["test", "command"])

    @patch('subprocess.run')
    def test_run_cmd_other_exception(self, mock_run):
        """Test run_cmd with other exception."""
        mock_run.side_effect = Exception("Unexpected error")
        
        with pytest.raises(ToolExecutionError):
            run_cmd(["test", "command"])

    def test_run_command_success(self):
        """Test run_command with successful execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            returncode, output = run_command(["test", "command"])
            assert returncode == 0
            assert output == "success output"

    def test_run_command_failure(self):
        """Test run_command with failed execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error message"
            mock_run.return_value = mock_result

            returncode, output = run_command(["test", "command"])
            assert returncode == 1
            assert output == "error message"

    def test_format_command_output_success(self):
        """Test _format_command_output with successful output."""
        output = _format_command_output("success output", "")
        assert output == "success output"

    def test_format_command_output_failure(self):
        """Test _format_command_output with failed output."""
        output = _format_command_output("", "error message")
        assert output == "error message"

    def test_format_command_output_combined(self):
        """Test _format_command_output with combined stdout and stderr."""
        output = _format_command_output("stdout message", "stderr message")
        assert "stdout message" in output
        assert "stderr message" in output


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_tool_execution_error_creation(self):
        """Test ToolExecutionError creation."""
        error = ToolExecutionError("Test error message")
        assert str(error) == "Test error message"

    def test_tool_execution_error_inheritance(self):
        """Test ToolExecutionError inheritance."""
        error = ToolExecutionError("Test error message")
        assert isinstance(error, Exception)

    def test_tool_execution_error_with_cause(self):
        """Test ToolExecutionError with cause."""
        cause = FileNotFoundError("Command not found")
        error = ToolExecutionError("Test error message")
        error.__cause__ = cause
        
        assert str(error) == "Test error message"
        assert error.__cause__ is cause


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_error_none_context(self):
        """Test format_error with None context."""
        result = format_error("Test message", ErrorSeverity.ERROR, ErrorCategory.LOGIC, None)
        assert "Test message" in result
        assert "ERROR" in result
        assert "LOGIC" in result

    def test_format_coverage_message_negative_coverage(self):
        """Test format_coverage_message with negative coverage."""
        result = format_coverage_message(-10.0, 80.0)
        assert "-10.0%" in result
        assert "80.0%" in result
        assert "FAILED" in result

    def test_format_coverage_message_very_high_coverage(self):
        """Test format_coverage_message with very high coverage."""
        result = format_coverage_message(150.0, 80.0)
        assert "150.0%" in result
        assert "80.0%" in result
        assert "PASSED" in result

    def test_run_cmd_empty_command(self):
        """Test run_cmd with empty command list."""
        with pytest.raises(ToolExecutionError):
            run_cmd([])

    def test_run_cmd_none_command(self):
        """Test run_cmd with None command."""
        with pytest.raises(ToolExecutionError):
            run_cmd(None)
