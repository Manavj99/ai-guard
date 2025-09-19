"""Comprehensive tests for utils modules to achieve high coverage."""

import pytest
import subprocess
from unittest.mock import Mock, patch, call
from subprocess import CompletedProcess

from src.ai_guard.utils.subprocess_runner import (
    ToolExecutionError,
    run_cmd,
    run_command,
    _format_command_output,
)


class TestToolExecutionError:
    """Test ToolExecutionError exception."""
    
    def test_tool_execution_error_creation(self):
        """Test creating ToolExecutionError."""
        error = ToolExecutionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, RuntimeError)


class TestRunCmd:
    """Test run_cmd function."""
    
    @patch('subprocess.run')
    def test_run_cmd_success(self, mock_run):
        """Test successful command execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Success output"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["echo", "test"])
        
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_cmd_with_cwd_and_timeout(self, mock_run):
        """Test command execution with custom cwd and timeout."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Success output"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["echo", "test"], cwd="/tmp", timeout=30)
        
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test command execution failure with output."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "Error output"
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["invalid", "command"])
        
        assert returncode == 1
        assert output == "Error output"
    
    @patch('subprocess.run')
    def test_run_cmd_failure_without_output(self, mock_run):
        """Test command execution failure without output."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        with pytest.raises(ToolExecutionError, match="Command failed with code 1 and no output"):
            run_cmd(["invalid", "command"])
    
    @patch('subprocess.run')
    def test_run_cmd_failure_with_whitespace_output(self, mock_run):
        """Test command execution failure with whitespace-only output."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "   \n\t  "
        mock_run.return_value = mock_process
        
        with pytest.raises(ToolExecutionError, match="Command failed with code 1 and no output"):
            run_cmd(["invalid", "command"])
    
    @patch('subprocess.run')
    def test_run_cmd_none_command(self, mock_run):
        """Test command execution with None command."""
        with pytest.raises(ToolExecutionError, match="Empty or None command provided"):
            run_cmd(None)
    
    @patch('subprocess.run')
    def test_run_cmd_empty_command(self, mock_run):
        """Test command execution with empty command."""
        with pytest.raises(ToolExecutionError, match="Empty or None command provided"):
            run_cmd([])
    
    @patch('subprocess.run')
    def test_run_cmd_none_stdout(self, mock_run):
        """Test command execution with None stdout."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = None
        mock_run.return_value = mock_process
        
        returncode, output = run_cmd(["echo", "test"])
        
        assert returncode == 0
        assert output == ""


class TestRunCommand:
    """Test run_command function."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_with_cmd(self, mock_run_cmd):
        """Test run_command with valid command."""
        mock_run_cmd.return_value = (0, "Success")
        
        returncode, output = run_command(["echo", "test"])
        
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(["echo", "test"])
    
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


class TestFormatCommandOutput:
    """Test _format_command_output function."""
    
    def test_format_command_output_both(self):
        """Test formatting when both stdout and stderr have content."""
        result = _format_command_output("stdout content", "stderr content")
        assert result == "stdout content\nstderr content"
    
    def test_format_command_output_stdout_only(self):
        """Test formatting when only stdout has content."""
        result = _format_command_output("stdout content", "")
        assert result == "stdout content"
    
    def test_format_command_output_stderr_only(self):
        """Test formatting when only stderr has content."""
        result = _format_command_output("", "stderr content")
        assert result == "stderr content"
    
    def test_format_command_output_neither(self):
        """Test formatting when neither stdout nor stderr has content."""
        result = _format_command_output("", "")
        assert result == "No output"
    
    def test_format_command_output_none_values(self):
        """Test formatting with None values."""
        result = _format_command_output(None, None)
        assert result == "No output"
    
    def test_format_command_output_mixed_none(self):
        """Test formatting with mixed None and string values."""
        result = _format_command_output("stdout content", None)
        assert result == "stdout content"
        
        result = _format_command_output(None, "stderr content")
        assert result == "stderr content"