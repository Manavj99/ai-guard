"""Comprehensive tests for the AI-Guard utils modules."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from src.ai_guard.utils.error_formatter import (
    ErrorContext, ErrorSeverity, ErrorCategory, ErrorFormatter,
    format_error, format_coverage_message
)

from src.ai_guard.utils.subprocess_runner import (
    run_cmd, ToolExecutionError, run_command, _format_command_output
)


class TestErrorContext:
    """Test ErrorContext class."""

    def test_error_context_init(self):
        """Test ErrorContext initialization."""
        context = ErrorContext(
            module="test_module",
            function="test_function",
            file_path="test.py",
            line_number=10,
            column=5,
            tool="flake8",
            rule_id="E501"
        )
        
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.file_path == "test.py"
        assert context.line_number == 10
        assert context.column == 5
        assert context.tool == "flake8"
        assert context.rule_id == "E501"

    def test_error_context_defaults(self):
        """Test ErrorContext with default values."""
        context = ErrorContext(
            module="test_module",
            function="test_function"
        )
        
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.file_path is None
        assert context.line_number is None
        assert context.column is None
        assert context.tool is None
        assert context.rule_id is None


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.INFO == "info"

    def test_error_severity_comparison(self):
        """Test ErrorSeverity comparison."""
        assert ErrorSeverity.ERROR != ErrorSeverity.WARNING
        assert ErrorSeverity.WARNING != ErrorSeverity.INFO


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_error_category_values(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.LINT == "lint"
        assert ErrorCategory.TYPE == "type"
        assert ErrorCategory.SECURITY == "security"
        assert ErrorCategory.COVERAGE == "coverage"

    def test_error_category_comparison(self):
        """Test ErrorCategory comparison."""
        assert ErrorCategory.LINT != ErrorCategory.TYPE
        assert ErrorCategory.TYPE != ErrorCategory.SECURITY


class TestErrorFormatter:
    """Test ErrorFormatter class."""

    def test_error_formatter_init(self):
        """Test ErrorFormatter initialization."""
        formatter = ErrorFormatter()
        assert formatter is not None
        assert formatter.include_context is True
        assert formatter.include_emoji is True

    def test_error_formatter_init_custom(self):
        """Test ErrorFormatter initialization with custom settings."""
        formatter = ErrorFormatter(include_context=False, include_emoji=False)
        assert formatter.include_context is False
        assert formatter.include_emoji is False

    def test_error_formatter_format_error(self):
        """Test ErrorFormatter format_error method."""
        formatter = ErrorFormatter()
        context = ErrorContext(
            module="test_module",
            function="test_function",
            file_path="test.py",
            line_number=10,
            tool="flake8",
            rule_id="E501"
        )
        
        result = formatter.format_error(
            "line too long",
            ErrorSeverity.ERROR, 
            ErrorCategory.VALIDATION,
            context
        )
        
        assert isinstance(result, str)
        assert "test.py" in result
        assert "E501" in result
        assert "line too long" in result

    def test_error_formatter_format_error_minimal(self):
        """Test ErrorFormatter with minimal context."""
        formatter = ErrorFormatter()
        context = ErrorContext(
            module="test_module",
            function="test_function"
        )
        
        result = formatter.format_error(
            "test message",
            ErrorSeverity.INFO, 
            ErrorCategory.EXECUTION,
            context
        )
        
        assert isinstance(result, str)
        assert "test message" in result


class TestSubprocessRunner:
    """Test subprocess runner functionality."""

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_success(self, mock_run):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_run.return_value = mock_result

        returncode, output = run_cmd(["python", "-c", "print('test')"])
        assert returncode == 0
        assert output == "success output"

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test failed command execution with output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error output"
        mock_run.return_value = mock_result

        returncode, output = run_cmd(["python", "-c", "exit(1)"])
        assert returncode == 1
        assert output == "error output"

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_no_output(self, mock_run):
        """Test failed command execution with no output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        with pytest.raises(ToolExecutionError):
            run_cmd(["python", "-c", "exit(1)"])

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_cwd(self, mock_run):
        """Test command execution with working directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_run.return_value = mock_result

        returncode, output = run_cmd(["python", "-c", "print('output')"], cwd=".")
        assert returncode == 0
        assert output == "output"

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_timeout(self, mock_run):
        """Test command execution with timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_run.return_value = mock_result

        returncode, output = run_cmd(["python", "-c", "print('output')"], timeout=5)
        assert returncode == 0
        assert output == "output"


class TestToolExecutionError:
    """Test ToolExecutionError class."""

    def test_tool_execution_error_init(self):
        """Test ToolExecutionError initialization."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_error_context_with_none_values(self):
        """Test ErrorContext with None values."""
        context = ErrorContext(
            module="test",
            function="test_function",
            file_path=None,
            line_number=None,
            column=None,
            tool=None,
            rule_id=None,
            suggestion=None,
            fix_code=None
        )
        
        assert context.file_path is None
        assert context.line_number is None
        assert context.column is None
        assert context.tool is None
        assert context.rule_id is None

    def test_format_error_with_none_context(self):
        """Test format_error with None context."""
        result = format_error("Test error", ErrorSeverity.ERROR, ErrorCategory.LINT, None)
        assert result is not None
        assert isinstance(result, str)

    def test_format_coverage_message_with_zero_coverage(self):
        """Test format_coverage_message with zero coverage."""
        result = format_coverage_message(0.0, 80.0)
        assert "0.0%" in result
        assert "80.0%" in result

    def test_format_coverage_message_with_high_coverage(self):
        """Test format_coverage_message with high coverage."""
        result = format_coverage_message(100.0, 80.0)
        assert "100.0%" in result
        assert "80.0%" in result

    def test_run_command_with_empty_args(self):
        """Test run_command with empty arguments."""
        returncode, output = run_command([])
        assert returncode == 1
        assert "Empty command" in output

    def test_run_command_with_none_args(self):
        """Test run_command with None arguments."""
        returncode, output = run_command(None)
        assert returncode == 1
        assert "No command provided" in output

    def test_format_command_output_with_unicode(self):
        """Test format_command_output with unicode characters."""
        result = _format_command_output("测试输出", "错误信息")
        assert "测试输出" in result
        assert "错误信息" in result
