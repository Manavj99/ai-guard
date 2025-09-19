"""Enhanced tests for subprocess_runner module to improve coverage."""

import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.utils.subprocess_runner import (
    run_cmd,
    run_command,
    _format_command_output,
    run_command_dict,
    run_command_with_output,
    run_command_safe,
    SubprocessRunner,
    CommandExecutor,
    SafeCommandRunner,
    ToolExecutionError
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

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_no_output(self, mock_run):
        """Test command failure with no output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        with pytest.raises(ToolExecutionError, match="Command failed with code 1"):
            run_cmd(["invalid_command"])

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test command failure with output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error message"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["command_with_error"])
        assert returncode == 1
        assert output == "Error message"

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_exception(self, mock_run):
        """Test command execution exception."""
        mock_run.side_effect = Exception("Command execution failed")
        
        with pytest.raises(ToolExecutionError, match="Command execution failed"):
            run_cmd(["command"])


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

    def test_run_command_empty(self):
        """Test empty command returns error."""
        returncode, output = run_command([])
        assert returncode == 1
        assert "Empty command" in output


class TestFormatCommandOutput:
    """Test _format_command_output function."""

    def test_format_command_output_both(self):
        """Test with both stdout and stderr."""
        result = _format_command_output("stdout", "stderr")
        assert result == "stdout\nstderr"

    def test_format_command_output_stdout_only(self):
        """Test with stdout only."""
        result = _format_command_output("stdout", "")
        assert result == "stdout"

    def test_format_command_output_stderr_only(self):
        """Test with stderr only."""
        result = _format_command_output("", "stderr")
        assert result == "stderr"

    def test_format_command_output_neither(self):
        """Test with neither stdout nor stderr."""
        result = _format_command_output("", "")
        assert result == "No output"


class TestRunCommandDict:
    """Test run_command_dict function."""

    def test_run_command_dict_success(self):
        """Test successful command execution."""
        result = run_command_dict(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "test" in result["stdout"]

    def test_run_command_dict_failure(self):
        """Test command failure."""
        result = run_command_dict(["python", "-c", "exit(1)"])
        assert result["success"] is False
        assert result["returncode"] == 1

    @patch('subprocess.run')
    def test_run_command_dict_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = Exception("timeout")
        result = run_command_dict(["command"])
        assert result["success"] is False
        assert "error" in result


class TestRunCommandWithOutput:
    """Test run_command_with_output function."""

    def test_run_command_with_output_success(self):
        """Test successful command execution with output."""
        result = run_command_with_output(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_run_command_with_output_failure(self):
        """Test command failure."""
        result = run_command_with_output(["python", "-c", "exit(1)"])
        assert result["success"] is False
        assert result["returncode"] == 1

    @patch('subprocess.run')
    def test_run_command_with_output_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = Exception("timeout")
        result = run_command_with_output(["command"])
        assert result["success"] is False
        assert "error" in result


class TestRunCommandSafe:
    """Test run_command_safe function."""

    def test_run_command_safe_success(self):
        """Test successful safe command execution."""
        result = run_command_safe(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_run_command_safe_failure(self):
        """Test command failure."""
        result = run_command_safe(["python", "-c", "exit(1)"])
        assert result["success"] is False
        assert result["returncode"] == 1

    def test_run_command_safe_custom_timeout(self):
        """Test with custom timeout."""
        result = run_command_safe(["python", "-c", "print('test')"], timeout=60)
        assert result["success"] is True
        assert "test" in result["stdout"]

    @patch('subprocess.run')
    def test_run_command_safe_timeout_expired(self, mock_run):
        """Test timeout expired."""
        mock_run.side_effect = Exception("timeout")
        result = run_command_safe(["command"], timeout=1)
        assert result["success"] is False
        assert "error" in result


class TestSubprocessRunner:
    """Test SubprocessRunner class."""

    def test_subprocess_runner_init_default(self):
        """Test SubprocessRunner initialization with defaults."""
        runner = SubprocessRunner()
        assert runner.timeout == 30
        assert runner.capture_output is True

    def test_subprocess_runner_init_custom(self):
        """Test SubprocessRunner initialization with custom values."""
        runner = SubprocessRunner(timeout=60, capture_output=False)
        assert runner.timeout == 60
        assert runner.capture_output is False

    def test_subprocess_runner_execute_command(self):
        """Test SubprocessRunner execute_command method."""
        runner = SubprocessRunner()
        result = runner.execute_command(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_subprocess_runner_execute_command_with_output(self):
        """Test SubprocessRunner execute_command_with_output method."""
        runner = SubprocessRunner()
        result = runner.execute_command_with_output(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_subprocess_runner_execute_command_safe(self):
        """Test SubprocessRunner execute_command_safe method."""
        runner = SubprocessRunner()
        result = runner.execute_command_safe(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_subprocess_runner_execute_command_no_capture(self):
        """Test SubprocessRunner with no output capture."""
        runner = SubprocessRunner(capture_output=False)
        result = runner.execute_command(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert result["stdout"] == ""
        assert result["stderr"] == ""


class TestCommandExecutor:
    """Test CommandExecutor class."""

    def test_command_executor_init(self):
        """Test CommandExecutor initialization."""
        executor = CommandExecutor()
        assert executor.executor_name == "Command Executor"
        assert executor.default_timeout == 30

    def test_command_executor_execute_command(self):
        """Test CommandExecutor execute_command method."""
        executor = CommandExecutor()
        result = executor.execute_command(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_command_executor_execute_command_custom_timeout(self):
        """Test CommandExecutor execute_command with custom timeout."""
        executor = CommandExecutor()
        result = executor.execute_command(["python", "-c", "print('test')"], timeout=60)
        assert result["success"] is True
        assert "test" in result["stdout"]

    def test_command_executor_execute_multiple_commands(self):
        """Test CommandExecutor execute_multiple_commands method."""
        executor = CommandExecutor()
        commands = [
            ["python", "-c", "print('test1')"],
            ["python", "-c", "print('test2')"]
        ]
        results = executor.execute_multiple_commands(commands)
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is True


class TestSafeCommandRunner:
    """Test SafeCommandRunner class."""

    def test_safe_command_runner_init_default(self):
        """Test SafeCommandRunner initialization with defaults."""
        runner = SafeCommandRunner()
        assert runner.runner_name == "Safe Command Runner"
        assert runner.max_retries == 3

    def test_safe_command_runner_init_custom(self):
        """Test SafeCommandRunner initialization with custom retries."""
        runner = SafeCommandRunner(max_retries=5)
        assert runner.max_retries == 5

    def test_safe_command_runner_run_command_safe_success(self):
        """Test SafeCommandRunner run_command_safe with success."""
        runner = SafeCommandRunner()
        result = runner.run_command_safe(["python", "-c", "print('test')"])
        assert result["success"] is True
        assert result["attempts"] == 1
        assert result["validated"] is True

    def test_safe_command_runner_run_command_safe_with_validation(self):
        """Test SafeCommandRunner run_command_safe with validation."""
        runner = SafeCommandRunner()
        
        def validation_func(result):
            return "test" in result.get("stdout", "")
        
        result = runner.run_command_safe(
            ["python", "-c", "print('test')"],
            validation_func=validation_func
        )
        assert result["success"] is True
        assert result["validated"] is True

    def test_safe_command_runner_run_command_safe_with_validation_failure(self):
        """Test SafeCommandRunner run_command_safe with validation failure."""
        runner = SafeCommandRunner()
        
        def validation_func(result):
            return False  # Always fail validation
        
        result = runner.run_command_safe(
            ["python", "-c", "print('test')"],
            validation_func=validation_func
        )
        assert result["success"] is True
        assert result["validated"] is False

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_safe_command_runner_run_command_safe_retry(self, mock_run_command_safe):
        """Test SafeCommandRunner run_command_safe with retries."""
        runner = SafeCommandRunner(max_retries=2)
        
        # First call fails, second succeeds
        mock_run_command_safe.side_effect = [
            {"success": False, "error": "First attempt failed"},
            {"success": True, "stdout": "test"}
        ]
        
        result = runner.run_command_safe(["command"])
        assert result["success"] is True
        assert result["attempts"] == 2
        assert mock_run_command_safe.call_count == 2

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_safe_command_runner_run_command_safe_max_retries(self, mock_run_command_safe):
        """Test SafeCommandRunner run_command_safe with max retries exceeded."""
        runner = SafeCommandRunner(max_retries=2)
        
        # All calls fail
        mock_run_command_safe.return_value = {"success": False, "error": "Failed"}
        
        result = runner.run_command_safe(["command"])
        assert result["success"] is False
        assert result["attempts"] == 2
        assert "Failed after 2 attempts" in result["error"]
        assert mock_run_command_safe.call_count == 2


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_tool_execution_error_init(self):
        """Test ToolExecutionError initialization."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)

    def test_tool_execution_error_inheritance(self):
        """Test ToolExecutionError inheritance."""
        error = ToolExecutionError("Test error")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
