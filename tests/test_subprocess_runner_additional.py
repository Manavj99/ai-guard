"""Additional tests for subprocess runner to increase coverage."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from ai_guard.utils.subprocess_runner import (
    ToolExecutionError,
    run_cmd,
    run_command,
    _format_command_output
)


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_tool_execution_error_init(self):
        """Test ToolExecutionError initialization."""
        error = ToolExecutionError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, RuntimeError)

    def test_tool_execution_error_with_empty_message(self):
        """Test ToolExecutionError with empty message."""
        error = ToolExecutionError("")
        
        assert str(error) == ""

    def test_tool_execution_error_inheritance(self):
        """Test ToolExecutionError inheritance."""
        error = ToolExecutionError("Test error")
        
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)


class TestRunCmd:
    """Test run_cmd function."""

    @patch('subprocess.run')
    def test_run_cmd_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success output"
        
        cmd = ["echo", "hello"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once_with(
            cmd,
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=900,
            check=False
        )

    @patch('subprocess.run')
    def test_run_cmd_with_cwd(self, mock_run):
        """Test command execution with working directory."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success output"
        
        cmd = ["echo", "hello"]
        cwd = "/tmp"
        returncode, output = run_cmd(cmd, cwd=cwd)
        
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once_with(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=900,
            check=False
        )

    @patch('subprocess.run')
    def test_run_cmd_with_timeout(self, mock_run):
        """Test command execution with custom timeout."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success output"
        
        cmd = ["echo", "hello"]
        timeout = 300
        returncode, output = run_cmd(cmd, timeout=timeout)
        
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once_with(
            cmd,
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False
        )

    @patch('subprocess.run')
    def test_run_cmd_non_zero_exit_with_output(self, mock_run):
        """Test command with non-zero exit code but with output."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "Error output"
        
        cmd = ["false"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 1
        assert output == "Error output"

    @patch('subprocess.run')
    def test_run_cmd_non_zero_exit_no_output(self, mock_run):
        """Test command with non-zero exit code and no output."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        
        cmd = ["false"]
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Command failed with code 1 and no output" in str(exc_info.value)
        assert "false" in str(exc_info.value)

    @patch('subprocess.run')
    def test_run_cmd_non_zero_exit_whitespace_output(self, mock_run):
        """Test command with non-zero exit code and whitespace-only output."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "   \n\t  "
        
        cmd = ["false"]
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Command failed with code 1 and no output" in str(exc_info.value)

    @patch('subprocess.run')
    def test_run_cmd_empty_command(self, mock_run):
        """Test run_cmd with empty command."""
        cmd = []
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Empty or None command provided" in str(exc_info.value)
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_run_cmd_none_command(self, mock_run):
        """Test run_cmd with None command."""
        cmd = None
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Empty or None command provided" in str(exc_info.value)
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_run_cmd_subprocess_exception(self, mock_run):
        """Test run_cmd with subprocess exception."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "test")
        
        cmd = ["test"]
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Command execution failed" in str(exc_info.value)

    @patch('subprocess.run')
    def test_run_cmd_generic_exception(self, mock_run):
        """Test run_cmd with generic exception."""
        mock_run.side_effect = OSError("Permission denied")
        
        cmd = ["test"]
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Command execution failed" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)

    @patch('subprocess.run')
    def test_run_cmd_timeout_error(self, mock_run):
        """Test run_cmd with timeout error."""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 30)
        
        cmd = ["test"]
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(cmd)
        
        assert "Command execution failed" in str(exc_info.value)

    @patch('subprocess.run')
    def test_run_cmd_none_stdout(self, mock_run):
        """Test run_cmd with None stdout."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = None
        
        cmd = ["echo", "hello"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == ""

    @patch('subprocess.run')
    def test_run_cmd_long_command(self, mock_run):
        """Test run_cmd with long command."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        
        cmd = ["python", "-c", "print('hello world')"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == "Success"


class TestRunCommand:
    """Test run_command function."""

    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_success(self, mock_run_cmd):
        """Test successful command execution."""
        mock_run_cmd.return_value = (0, "Success output")
        
        cmd = ["echo", "hello"]
        returncode, output = run_command(cmd)
        
        assert returncode == 0
        assert output == "Success output"
        mock_run_cmd.assert_called_once_with(cmd)

    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_failure(self, mock_run_cmd):
        """Test command execution failure."""
        mock_run_cmd.return_value = (1, "Error output")
        
        cmd = ["false"]
        returncode, output = run_command(cmd)
        
        assert returncode == 1
        assert output == "Error output"

    def test_run_command_none(self):
        """Test run_command with None command."""
        returncode, output = run_command(None)
        
        assert returncode == 1
        assert output == "No command provided"

    def test_run_command_empty(self):
        """Test run_command with empty command."""
        returncode, output = run_command([])
        
        assert returncode == 1
        assert output == "Empty command"

    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_args(self, mock_run_cmd):
        """Test run_command with command arguments."""
        mock_run_cmd.return_value = (0, "Success")
        
        cmd = ["python", "-m", "pytest", "--version"]
        returncode, output = run_command(cmd)
        
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(cmd)

    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_single_arg(self, mock_run_cmd):
        """Test run_command with single argument."""
        mock_run_cmd.return_value = (0, "Success")
        
        cmd = ["ls"]
        returncode, output = run_command(cmd)
        
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(cmd)


class TestFormatCommandOutput:
    """Test _format_command_output function."""

    def test_format_command_output_both_stdout_stderr(self):
        """Test formatting when both stdout and stderr have content."""
        stdout = "Standard output"
        stderr = "Error output"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Standard output\nError output"

    def test_format_command_output_stdout_only(self):
        """Test formatting when only stdout has content."""
        stdout = "Standard output"
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Standard output"

    def test_format_command_output_stderr_only(self):
        """Test formatting when only stderr has content."""
        stdout = ""
        stderr = "Error output"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Error output"

    def test_format_command_output_neither(self):
        """Test formatting when neither stdout nor stderr has content."""
        stdout = ""
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "No output"

    def test_format_command_output_none_stdout(self):
        """Test formatting when stdout is None."""
        stdout = None
        stderr = "Error output"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Error output"

    def test_format_command_output_none_stderr(self):
        """Test formatting when stderr is None."""
        stdout = "Standard output"
        stderr = None
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Standard output"

    def test_format_command_output_both_none(self):
        """Test formatting when both stdout and stderr are None."""
        stdout = None
        stderr = None
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "No output"

    def test_format_command_output_multiline_stdout(self):
        """Test formatting with multiline stdout."""
        stdout = "Line 1\nLine 2\nLine 3"
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Line 1\nLine 2\nLine 3"

    def test_format_command_output_multiline_stderr(self):
        """Test formatting with multiline stderr."""
        stdout = ""
        stderr = "Error 1\nError 2\nError 3"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Error 1\nError 2\nError 3"

    def test_format_command_output_whitespace_stdout(self):
        """Test formatting with whitespace-only stdout."""
        stdout = "   \n\t  \n  "
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "   \n\t  \n  "


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('subprocess.run')
    def test_run_cmd_with_unicode_output(self, mock_run):
        """Test run_cmd with unicode output."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Hello 世界 🌍"
        
        cmd = ["echo", "hello"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == "Hello 世界 🌍"

    @patch('subprocess.run')
    def test_run_cmd_with_large_output(self, mock_run):
        """Test run_cmd with large output."""
        large_output = "x" * 10000
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = large_output
        
        cmd = ["echo", "large"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == large_output
        assert len(output) == 10000

    @patch('subprocess.run')
    def test_run_cmd_with_special_characters(self, mock_run):
        """Test run_cmd with special characters in command."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        
        cmd = ["echo", "special!@#$%^&*()"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == "Success"

    @patch('subprocess.run')
    def test_run_cmd_zero_timeout(self, mock_run):
        """Test run_cmd with zero timeout."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        
        cmd = ["echo", "hello"]
        returncode, output = run_cmd(cmd, timeout=0)
        
        assert returncode == 0
        assert output == "Success"
        mock_run.assert_called_once_with(
            cmd,
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=0,
            check=False
        )

    @patch('subprocess.run')
    def test_run_cmd_very_long_timeout(self, mock_run):
        """Test run_cmd with very long timeout."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        
        cmd = ["echo", "hello"]
        returncode, output = run_cmd(cmd, timeout=3600)
        
        assert returncode == 0
        assert output == "Success"
        mock_run.assert_called_once_with(
            cmd,
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=3600,
            check=False
        )

    def test_run_command_with_various_empty_inputs(self):
        """Test run_command with various empty inputs."""
        # Test with None
        returncode, output = run_command(None)
        assert returncode == 1
        assert output == "No command provided"
        
        # Test with empty list
        returncode, output = run_command([])
        assert returncode == 1
        assert output == "Empty command"
        
        # Test with list containing empty string
        returncode, output = run_command([""])
        assert returncode == 1
        assert output == "Empty command"

    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_exception_propagation(self, mock_run_cmd):
        """Test that exceptions are propagated from run_cmd."""
        mock_run_cmd.side_effect = ToolExecutionError("Test error")
        
        cmd = ["test"]
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_command(cmd)
        
        assert "Test error" in str(exc_info.value)
