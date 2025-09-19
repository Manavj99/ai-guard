"""Basic tests for subprocess_runner module."""

import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.utils.subprocess_runner import (
    run_cmd,
    run_command,
    ToolExecutionError,
    run_command_with_output,
    run_command_safe,
    SubprocessRunner,
    CommandExecutor
)


class TestRunCmd:
    """Test run_cmd function."""

    def test_run_cmd_success(self):
        """Test successful command execution."""
        returncode, output = run_cmd(["python", "-c", "print('test')"])
        assert returncode == 0
        assert "test" in output

    def test_run_cmd_empty_command(self):
        """Test empty command raises ToolExecutionError."""
        with pytest.raises(ToolExecutionError, match="Empty or None command"):
            run_cmd([])

    def test_run_cmd_none_command(self):
        """Test None command raises ToolExecutionError."""
        with pytest.raises(ToolExecutionError, match="Empty or None command"):
            run_cmd(None)


class TestRunCommand:
    """Test run_command function."""

    def test_run_command_success(self):
        """Test successful command execution."""
        returncode, output = run_command(["python", "-c", "print('test')"])
        assert returncode == 0
        assert "test" in output

    def test_run_command_none(self):
        """Test None command returns error."""
        returncode, output = run_command(None)
        assert returncode == 1
        assert "No command provided" in output


class TestRunCommandWithOutput:
    """Test run_command_with_output function."""

    def test_run_command_with_output_success(self):
        """Test successful command execution with output."""
        result = run_command_with_output(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]


class TestRunCommandSafe:
    """Test run_command_safe function."""

    def test_run_command_safe_success(self):
        """Test successful safe command execution."""
        result = run_command_safe(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]


class TestSubprocessRunner:
    """Test SubprocessRunner class."""

    def test_subprocess_runner_init(self):
        """Test SubprocessRunner initialization."""
        runner = SubprocessRunner()
        assert runner is not None

    def test_subprocess_runner_execute_command(self):
        """Test SubprocessRunner execute_command method."""
        runner = SubprocessRunner()
        result = runner.execute_command(["python", "-c", "print('test')"])
        assert result["success"] is True


class TestCommandExecutor:
    """Test CommandExecutor class."""

    def test_command_executor_init(self):
        """Test CommandExecutor initialization."""
        executor = CommandExecutor()
        assert executor is not None

    def test_command_executor_execute_command(self):
        """Test CommandExecutor execute_command method."""
        executor = CommandExecutor()
        result = executor.execute_command(["python", "-c", "print('test')"])
        assert result["success"] is True


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_tool_execution_error_init(self):
        """Test ToolExecutionError initialization."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)
