"""Additional tests for subprocess_runner.py to improve coverage."""

import pytest
from unittest.mock import patch, Mock, call
import subprocess

from src.ai_guard.utils.subprocess_runner import (
    ToolExecutionError,
    run_cmd,
    run_command,
    _format_command_output
)


class TestToolExecutionError:
    """Test ToolExecutionError exception class."""
    
    def test_tool_execution_error_with_message(self):
        """Test ToolExecutionError with custom message."""
        error = ToolExecutionError("Custom error message")
        assert str(error) == "Custom error message"
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
    
    def test_tool_execution_error_empty_message(self):
        """Test ToolExecutionError with empty message."""
        error = ToolExecutionError("")
        assert str(error) == ""
        assert isinstance(error, RuntimeError)
    
    def test_tool_execution_error_none_message(self):
        """Test ToolExecutionError with None message."""
        error = ToolExecutionError(None)
        assert str(error) == "None"
        assert isinstance(error, RuntimeError)


class TestRunCmd:
    """Test run_cmd function with comprehensive scenarios."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_success_with_output(self, mock_run):
        """Test successful command execution with output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Success output\nwith multiple lines"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["echo", "test"])
        
        assert returncode == 0
        assert output == "Success output\nwith multiple lines"
        mock_run.assert_called_once_with(
            ["echo", "test"],
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=900,
            check=False
        )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_success_empty_output(self, mock_run):
        """Test successful command execution with empty output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["touch", "empty_file"])
        
        assert returncode == 0
        assert output == ""
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_success_none_output(self, mock_run):
        """Test successful command execution with None output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = None
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["echo", "test"])
        
        assert returncode == 0
        assert output == ""
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test failed command execution with output."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "Error output"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["false"])
        
        assert returncode == 1
        assert output == "Error output"
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_no_output(self, mock_run):
        """Test failed command execution with no output."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["false"])
        
        assert "Command failed with code 1 and no output" in str(exc_info.value)
        assert "false" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_whitespace_output(self, mock_run):
        """Test failed command execution with whitespace-only output."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "   \n\t  \n  "
        mock_run.return_value = mock_process
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["false"])
        
        assert "Command failed with code 1 and no output" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_cwd(self, mock_run):
        """Test command execution with custom working directory."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Output"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["ls"], cwd="/tmp")
        
        assert returncode == 0
        assert output == "Output"
        mock_run.assert_called_once_with(
            ["ls"],
            cwd="/tmp",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=900,
            check=False
        )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_custom_timeout(self, mock_run):
        """Test command execution with custom timeout."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Output"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["sleep", "1"], timeout=30)
        
        assert returncode == 0
        assert output == "Output"
        mock_run.assert_called_once_with(
            ["sleep", "1"],
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
            check=False
        )
    
    def test_run_cmd_empty_command(self):
        """Test run_cmd with empty command."""
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd([])
        
        assert "Empty or None command provided" in str(exc_info.value)
    
    def test_run_cmd_none_command(self):
        """Test run_cmd with None command."""
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(None)
        
        assert "Empty or None command provided" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_subprocess_exception(self, mock_run):
        """Test run_cmd with subprocess exception."""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 30)
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["sleep", "infinity"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_generic_exception(self, mock_run):
        """Test run_cmd with generic exception."""
        mock_run.side_effect = Exception("Generic error")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["test"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_file_not_found_error(self, mock_run):
        """Test run_cmd with FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["nonexistent_command"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_permission_error(self, mock_run):
        """Test run_cmd with PermissionError."""
        mock_run.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["restricted_command"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_os_error(self, mock_run):
        """Test run_cmd with OSError."""
        mock_run.side_effect = OSError("OS error")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["test"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_value_error(self, mock_run):
        """Test run_cmd with ValueError."""
        mock_run.side_effect = ValueError("Invalid value")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["test"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_type_error(self, mock_run):
        """Test run_cmd with TypeError."""
        mock_run.side_effect = TypeError("Type error")
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["test"])
        
        assert "Command execution failed" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_keyboard_interrupt(self, mock_run):
        """Test run_cmd with KeyboardInterrupt."""
        mock_run.side_effect = KeyboardInterrupt()
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["test"])
        
        assert "Command execution failed" in str(exc_info.value)


class TestRunCommand:
    """Test run_command function."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_valid_cmd(self, mock_run_cmd):
        """Test run_command with valid command."""
        mock_run_cmd.return_value = (0, "Success")
        
        returncode, output = run_command(["echo", "test"])
        
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(["echo", "test"])
    
    def test_run_command_with_none_cmd(self):
        """Test run_command with None command."""
        returncode, output = run_command(None)
        
        assert returncode == 1
        assert output == "No command provided"
    
    def test_run_command_with_empty_cmd(self):
        """Test run_command with empty command."""
        returncode, output = run_command([])
        
        assert returncode == 1
        assert output == "Empty command"
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_single_element_cmd(self, mock_run_cmd):
        """Test run_command with single element command."""
        mock_run_cmd.return_value = (0, "Success")
        
        returncode, output = run_command(["ls"])
        
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(["ls"])
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_multiple_elements_cmd(self, mock_run_cmd):
        """Test run_command with multiple elements command."""
        mock_run_cmd.return_value = (0, "Success")
        
        returncode, output = run_command(["python", "-m", "pytest", "--version"])
        
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(["python", "-m", "pytest", "--version"])
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_failed_cmd(self, mock_run_cmd):
        """Test run_command with failed command."""
        mock_run_cmd.return_value = (1, "Error output")
        
        returncode, output = run_command(["false"])
        
        assert returncode == 1
        assert output == "Error output"
        mock_run_cmd.assert_called_once_with(["false"])
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_exception(self, mock_run_cmd):
        """Test run_command with exception from run_cmd."""
        mock_run_cmd.side_effect = ToolExecutionError("Command failed")
        
        with pytest.raises(ToolExecutionError):
            run_command(["test"])


class TestFormatCommandOutput:
    """Test _format_command_output function."""
    
    def test_format_command_output_both_stdout_stderr(self):
        """Test formatting output when both stdout and stderr have content."""
        stdout = "Standard output"
        stderr = "Error output"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Standard output\nError output"
    
    def test_format_command_output_only_stdout(self):
        """Test formatting output when only stdout has content."""
        stdout = "Standard output"
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Standard output"
    
    def test_format_command_output_only_stderr(self):
        """Test formatting output when only stderr has content."""
        stdout = ""
        stderr = "Error output"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Error output"
    
    def test_format_command_output_neither_stdout_stderr(self):
        """Test formatting output when neither stdout nor stderr has content."""
        stdout = ""
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "No output"
    
    def test_format_command_output_none_stdout_stderr(self):
        """Test formatting output when both stdout and stderr are None."""
        stdout = None
        stderr = None
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "No output"
    
    def test_format_command_output_none_stdout_empty_stderr(self):
        """Test formatting output when stdout is None and stderr is empty."""
        stdout = None
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "No output"
    
    def test_format_command_output_empty_stdout_none_stderr(self):
        """Test formatting output when stdout is empty and stderr is None."""
        stdout = ""
        stderr = None
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "No output"
    
    def test_format_command_output_multiline_stdout(self):
        """Test formatting output with multiline stdout."""
        stdout = "Line 1\nLine 2\nLine 3"
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Line 1\nLine 2\nLine 3"
    
    def test_format_command_output_multiline_stderr(self):
        """Test formatting output with multiline stderr."""
        stdout = ""
        stderr = "Error 1\nError 2\nError 3"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Error 1\nError 2\nError 3"
    
    def test_format_command_output_multiline_both(self):
        """Test formatting output with multiline both stdout and stderr."""
        stdout = "Line 1\nLine 2"
        stderr = "Error 1\nError 2"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Line 1\nLine 2\nError 1\nError 2"
    
    def test_format_command_output_whitespace_stdout(self):
        """Test formatting output with whitespace-only stdout."""
        stdout = "   \n\t  \n  "
        stderr = ""
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "   \n\t  \n  "
    
    def test_format_command_output_whitespace_stderr(self):
        """Test formatting output with whitespace-only stderr."""
        stdout = ""
        stderr = "   \n\t  \n  "
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "   \n\t  \n  "
    
    def test_format_command_output_unicode_content(self):
        """Test formatting output with unicode content."""
        stdout = "Standard output with unicode: 你好世界"
        stderr = "Error output with unicode: 🚨"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Standard output with unicode: 你好世界\nError output with unicode: 🚨"
    
    def test_format_command_output_special_characters(self):
        """Test formatting output with special characters."""
        stdout = "Output with special chars: !@#$%^&*()"
        stderr = "Error with special chars: <>?:\"{}|"
        
        result = _format_command_output(stdout, stderr)
        
        assert result == "Output with special chars: !@#$%^&*()\nError with special chars: <>?:\"{}|"
    
    def test_format_command_output_very_long_content(self):
        """Test formatting output with very long content."""
        stdout = "A" * 10000
        stderr = "B" * 10000
        
        result = _format_command_output(stdout, stderr)
        
        assert len(result) == 20001  # 10000 + 10000 + 1 (newline)
        assert result.startswith("A" * 10000)
        assert result.endswith("B" * 10000)


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_realistic_commands(self, mock_run):
        """Test run_cmd with realistic command scenarios."""
        # Test with different return codes and outputs
        test_cases = [
            (0, "Success output", ["echo", "hello"]),
            (1, "Error: command failed", ["false"]),
            (2, "Warning: deprecated command", ["deprecated_cmd"]),
            (127, "Command not found", ["nonexistent"]),
            (130, "", ["interrupted_cmd"])  # Should raise ToolExecutionError
        ]
        
        for expected_code, expected_output, cmd in test_cases:
            mock_process = Mock()
            mock_process.returncode = expected_code
            mock_process.stdout = expected_output
            mock_run.return_value = mock_process
            
            if expected_code == 130 and not expected_output.strip():
                with pytest.raises(ToolExecutionError):
                    run_cmd(cmd)
            else:
                returncode, output = run_cmd(cmd)
                assert returncode == expected_code
                assert output == expected_output
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_different_working_directories(self, mock_run):
        """Test run_cmd with different working directories."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Directory listing"
        mock_run.return_value = mock_process
        
        directories = ["/tmp", "/home", "/usr/local/bin", "relative/path"]
        
        for cwd in directories:
            run_cmd(["ls"], cwd=cwd)
            mock_run.assert_called_with(
                ["ls"],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=900,
                check=False
            )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_different_timeouts(self, mock_run):
        """Test run_cmd with different timeout values."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Quick output"
        mock_run.return_value = mock_process
        
        timeouts = [1, 5, 30, 60, 300, 900, 3600]
        
        for timeout in timeouts:
            run_cmd(["quick_command"], timeout=timeout)
            mock_run.assert_called_with(
                ["quick_command"],
                cwd=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False
            )
