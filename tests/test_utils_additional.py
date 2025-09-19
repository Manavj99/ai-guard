"""Additional tests for utils modules."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from ai_guard.utils.error_formatter import (
    format_error_message,
    format_exception,
    format_traceback,
    ErrorFormatter,
    ExceptionFormatter,
    TracebackFormatter
)
from ai_guard.utils.subprocess_runner import (
    run_command,
    run_command_with_output,
    run_command_safe,
    SubprocessRunner,
    CommandExecutor,
    SafeCommandRunner
)


class TestErrorFormatter:
    """Test error formatting functionality."""

    def test_format_error_message_simple(self):
        """Test simple error message formatting."""
        error_msg = "Something went wrong"
        
        formatted = format_error_message(error_msg)
        
        assert formatted == error_msg

    def test_format_error_message_with_context(self):
        """Test error message formatting with context."""
        error_msg = "File not found"
        context = {"file": "test.py", "line": 10}
        
        formatted = format_error_message(error_msg, context=context)
        
        assert error_msg in formatted
        assert "test.py" in formatted
        assert "10" in formatted

    def test_format_error_message_with_suggestion(self):
        """Test error message formatting with suggestion."""
        error_msg = "Import error"
        suggestion = "Check if the module is installed"
        
        formatted = format_error_message(error_msg, suggestion=suggestion)
        
        assert error_msg in formatted
        assert suggestion in formatted

    def test_format_error_message_with_all_options(self):
        """Test error message formatting with all options."""
        error_msg = "Configuration error"
        context = {"config_file": "config.toml", "section": "database"}
        suggestion = "Check the configuration file format"
        severity = "error"
        
        formatted = format_error_message(
            error_msg,
            context=context,
            suggestion=suggestion,
            severity=severity
        )
        
        assert error_msg in formatted
        assert "config.toml" in formatted
        assert "database" in formatted
        assert suggestion in formatted
        assert severity.upper() in formatted

    def test_format_exception_basic(self):
        """Test basic exception formatting."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            formatted = format_exception(e)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted

    def test_format_exception_with_traceback(self):
        """Test exception formatting with traceback."""
        try:
            def inner_function():
                raise RuntimeError("Inner error")
            
            def outer_function():
                inner_function()
            
            outer_function()
        except RuntimeError as e:
            formatted = format_exception(e, include_traceback=True)
            
            assert "RuntimeError" in formatted
            assert "Inner error" in formatted
            assert "inner_function" in formatted
            assert "outer_function" in formatted

    def test_format_traceback(self):
        """Test traceback formatting."""
        try:
            def test_function():
                raise ValueError("Test error")
            
            test_function()
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            formatted = format_traceback(tb)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted
            assert "test_function" in formatted


class TestErrorFormatterClass:
    """Test ErrorFormatter class."""

    def test_formatter_init(self):
        """Test formatter initialization."""
        formatter = ErrorFormatter()
        
        assert formatter.max_message_length == 1000
        assert formatter.include_timestamp is False
        assert formatter.include_context is True

    def test_formatter_init_custom(self):
        """Test formatter initialization with custom settings."""
        formatter = ErrorFormatter(
            max_message_length=500,
            include_timestamp=True,
            include_context=False
        )
        
        assert formatter.max_message_length == 500
        assert formatter.include_timestamp is True
        assert formatter.include_context is False

    def test_format_error(self):
        """Test error formatting."""
        formatter = ErrorFormatter()
        
        error_msg = "Test error"
        context = {"file": "test.py", "line": 10}
        
        formatted = formatter.format_error(error_msg, context=context)
        
        assert error_msg in formatted
        assert "test.py" in formatted
        assert "10" in formatted

    def test_format_error_long_message(self):
        """Test error formatting with long message."""
        formatter = ErrorFormatter(max_message_length=50)
        
        long_error = "This is a very long error message that should be truncated because it exceeds the maximum length"
        
        formatted = formatter.format_error(long_error)
        
        assert len(formatted) <= 50
        assert "..." in formatted

    def test_format_multiple_errors(self):
        """Test formatting multiple errors."""
        formatter = ErrorFormatter()
        
        errors = [
            {"message": "Error 1", "context": {"file": "test1.py"}},
            {"message": "Error 2", "context": {"file": "test2.py"}}
        ]
        
        formatted = formatter.format_multiple_errors(errors)
        
        assert "Error 1" in formatted
        assert "Error 2" in formatted
        assert "test1.py" in formatted
        assert "test2.py" in formatted


class TestExceptionFormatter:
    """Test ExceptionFormatter class."""

    def test_formatter_init(self):
        """Test formatter initialization."""
        formatter = ExceptionFormatter()
        
        assert formatter.include_traceback is True
        assert formatter.max_traceback_lines == 10

    def test_format_exception(self):
        """Test exception formatting."""
        formatter = ExceptionFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            formatted = formatter.format_exception(e)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted

    def test_format_exception_without_traceback(self):
        """Test exception formatting without traceback."""
        formatter = ExceptionFormatter(include_traceback=False)
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            formatted = formatter.format_exception(e)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted
            # Should not include traceback details
            assert "Traceback" not in formatted

    def test_format_exception_with_context(self):
        """Test exception formatting with additional context."""
        formatter = ExceptionFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            context = {"operation": "file_processing", "file": "test.py"}
            formatted = formatter.format_exception(e, context=context)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted
            assert "file_processing" in formatted
            assert "test.py" in formatted


class TestTracebackFormatter:
    """Test TracebackFormatter class."""

    def test_formatter_init(self):
        """Test formatter initialization."""
        formatter = TracebackFormatter()
        
        assert formatter.max_lines == 20
        assert formatter.include_locals is False

    def test_format_traceback(self):
        """Test traceback formatting."""
        formatter = TracebackFormatter()
        
        try:
            def test_function():
                raise ValueError("Test error")
            
            test_function()
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            formatted = formatter.format_traceback(tb)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted
            assert "test_function" in formatted

    def test_format_traceback_with_locals(self):
        """Test traceback formatting with locals."""
        formatter = TracebackFormatter(include_locals=True)
        
        try:
            def test_function():
                local_var = "test_value"
                raise ValueError("Test error")
            
            test_function()
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            formatted = formatter.format_traceback(tb)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted
            assert "test_function" in formatted

    def test_format_traceback_limit_lines(self):
        """Test traceback formatting with line limit."""
        formatter = TracebackFormatter(max_lines=5)
        
        try:
            def level1():
                def level2():
                    def level3():
                        def level4():
                            def level5():
                                raise ValueError("Deep error")
                            level5()
                        level4()
                    level3()
                level2()
            level1()
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            formatted = formatter.format_traceback(tb)
            
            # Should limit the number of lines
            lines = formatted.split('\n')
            assert len(lines) <= 5


class TestSubprocessRunner:
    """Test subprocess runner functionality."""

    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = run_command(["echo", "hello"])
        
        assert result["success"] is True
        assert result["returncode"] == 0

    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = run_command(["false"])
        
        assert result["success"] is False
        assert result["returncode"] == 1

    @patch('subprocess.run')
    def test_run_command_exception(self, mock_run):
        """Test command execution with exception."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "command")
        
        result = run_command(["invalid_command"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_run_command_with_output_success(self, mock_run):
        """Test successful command execution with output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Hello World",
            stderr=""
        )
        
        result = run_command_with_output(["echo", "Hello World"])
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["stdout"] == "Hello World"
        assert result["stderr"] == ""

    @patch('subprocess.run')
    def test_run_command_with_output_failure(self, mock_run):
        """Test failed command execution with output."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Command failed"
        )
        
        result = run_command_with_output(["false"])
        
        assert result["success"] is False
        assert result["returncode"] == 1
        assert result["stderr"] == "Command failed"

    @patch('subprocess.run')
    def test_run_command_safe_success(self, mock_run):
        """Test safe command execution success."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = run_command_safe(["echo", "hello"])
        
        assert result["success"] is True
        assert result["returncode"] == 0

    @patch('subprocess.run')
    def test_run_command_safe_failure(self, mock_run):
        """Test safe command execution failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "command")
        
        result = run_command_safe(["invalid_command"])
        
        assert result["success"] is False
        assert "error" in result
        # Should not raise exception

    def test_run_command_safe_timeout(self):
        """Test safe command execution with timeout."""
        result = run_command_safe(["sleep", "10"], timeout=1)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()


class TestSubprocessRunnerClass:
    """Test SubprocessRunner class."""

    def test_runner_init(self):
        """Test runner initialization."""
        runner = SubprocessRunner()
        
        assert runner.timeout == 30
        assert runner.capture_output is True

    def test_runner_init_custom(self):
        """Test runner initialization with custom settings."""
        runner = SubprocessRunner(timeout=60, capture_output=False)
        
        assert runner.timeout == 60
        assert runner.capture_output is False

    @patch('subprocess.run')
    def test_execute_command(self, mock_run):
        """Test command execution."""
        runner = SubprocessRunner()
        mock_run.return_value = MagicMock(returncode=0)
        
        result = runner.execute_command(["echo", "hello"])
        
        assert result["success"] is True
        assert result["returncode"] == 0

    @patch('subprocess.run')
    def test_execute_command_with_output(self, mock_run):
        """Test command execution with output capture."""
        runner = SubprocessRunner()
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Hello World",
            stderr=""
        )
        
        result = runner.execute_command_with_output(["echo", "Hello World"])
        
        assert result["success"] is True
        assert result["stdout"] == "Hello World"
        assert result["stderr"] == ""

    def test_execute_command_timeout(self):
        """Test command execution with timeout."""
        runner = SubprocessRunner(timeout=1)
        
        result = runner.execute_command(["sleep", "5"])
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    def test_execute_command_safe(self):
        """Test safe command execution."""
        runner = SubprocessRunner()
        
        result = runner.execute_command_safe(["echo", "hello"])
        
        assert result["success"] is True
        assert result["returncode"] == 0

    def test_execute_command_safe_error(self):
        """Test safe command execution with error."""
        runner = SubprocessRunner()
        
        result = runner.execute_command_safe(["invalid_command"])
        
        assert result["success"] is False
        assert "error" in result


class TestCommandExecutor:
    """Test CommandExecutor class."""

    def test_executor_init(self):
        """Test executor initialization."""
        executor = CommandExecutor()
        
        assert executor.executor_name == "Command Executor"
        assert executor.default_timeout == 30

    def test_execute_command(self):
        """Test command execution."""
        executor = CommandExecutor()
        
        result = executor.execute_command(["echo", "hello"])
        
        assert result["success"] is True
        assert result["returncode"] == 0

    def test_execute_command_with_custom_timeout(self):
        """Test command execution with custom timeout."""
        executor = CommandExecutor()
        
        result = executor.execute_command(["echo", "hello"], timeout=10)
        
        assert result["success"] is True
        assert result["returncode"] == 0

    def test_execute_command_failure(self):
        """Test command execution failure."""
        executor = CommandExecutor()
        
        result = executor.execute_command(["false"])
        
        assert result["success"] is False
        assert result["returncode"] == 1

    def test_execute_multiple_commands(self):
        """Test executing multiple commands."""
        executor = CommandExecutor()
        
        commands = [
            ["echo", "hello"],
            ["echo", "world"]
        ]
        
        results = executor.execute_multiple_commands(commands)
        
        assert len(results) == 2
        assert all(result["success"] for result in results)


class TestSafeCommandRunner:
    """Test SafeCommandRunner class."""

    def test_runner_init(self):
        """Test runner initialization."""
        runner = SafeCommandRunner()
        
        assert runner.runner_name == "Safe Command Runner"
        assert runner.max_retries == 3

    def test_runner_init_custom(self):
        """Test runner initialization with custom settings."""
        runner = SafeCommandRunner(max_retries=5)
        
        assert runner.max_retries == 5

    def test_run_command_safe(self):
        """Test safe command execution."""
        runner = SafeCommandRunner()
        
        result = runner.run_command_safe(["echo", "hello"])
        
        assert result["success"] is True
        assert result["returncode"] == 0

    def test_run_command_safe_with_retry(self):
        """Test safe command execution with retry."""
        runner = SafeCommandRunner(max_retries=2)
        
        # This should succeed on first try
        result = runner.run_command_safe(["echo", "hello"])
        
        assert result["success"] is True
        assert result["attempts"] == 1

    def test_run_command_safe_failure(self):
        """Test safe command execution failure."""
        runner = SafeCommandRunner()
        
        result = runner.run_command_safe(["invalid_command"])
        
        assert result["success"] is False
        assert "error" in result

    def test_run_command_safe_timeout(self):
        """Test safe command execution with timeout."""
        runner = SafeCommandRunner()
        
        result = runner.run_command_safe(["sleep", "10"], timeout=1)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    def test_run_command_safe_with_validation(self):
        """Test safe command execution with validation."""
        runner = SafeCommandRunner()
        
        def validate_output(result):
            return "hello" in result.get("stdout", "")
        
        result = runner.run_command_safe(
            ["echo", "hello"],
            validation_func=validate_output
        )
        
        assert result["success"] is True
        assert result["validated"] is True

    def test_run_command_safe_validation_failure(self):
        """Test safe command execution with validation failure."""
        runner = SafeCommandRunner()
        
        def validate_output(result):
            return "world" in result.get("stdout", "")
        
        result = runner.run_command_safe(
            ["echo", "hello"],
            validation_func=validate_output
        )
        
        assert result["success"] is True
        assert result["validated"] is False
