"""Tests for the subprocess_runner module."""

import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.utils.subprocess_runner import run_cmd, ToolExecutionError


class TestToolExecutionError:
    """Test ToolExecutionError exception."""
    
    def test_tool_execution_error_creation(self):
        """Test creating ToolExecutionError."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)


class TestRunCmd:
    """Test run_cmd function."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_success(self, mock_run):
        """Test run_cmd with successful command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["echo", "test"])
        
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once_with(
            ["echo", "test"],
            cwd=None,
            stdout=-1,  # PIPE
            stderr=-2,  # STDOUT
            text=True,
            timeout=900,
            check=False
        )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_cwd(self, mock_run):
        """Test run_cmd with custom working directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["ls"], cwd="/tmp")
        
        assert returncode == 0
        assert output == "Output"
        mock_run.assert_called_once_with(
            ["ls"],
            cwd="/tmp",
            stdout=-1,
            stderr=-2,
            text=True,
            timeout=900,
            check=False
        )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_timeout(self, mock_run):
        """Test run_cmd with custom timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["sleep", "1"], timeout=30)
        
        assert returncode == 0
        assert output == "Output"
        mock_run.assert_called_once_with(
            ["sleep", "1"],
            cwd=None,
            stdout=-1,
            stderr=-2,
            text=True,
            timeout=30,
            check=False
        )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test run_cmd with failed command that has output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["false"])
        
        assert returncode == 1
        assert output == "Error output"
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_no_output(self, mock_run):
        """Test run_cmd with failed command that has no output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["false"])
        
        assert "Command failed with code 1 and no output: false" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_whitespace_only_output(self, mock_run):
        """Test run_cmd with failed command that has only whitespace output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "   \n\t  "
        mock_run.return_value = mock_result
        
        with pytest.raises(ToolExecutionError) as exc_info:
            run_cmd(["false"])
        
        assert "Command failed with code 1 and no output: false" in str(exc_info.value)
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_none_stdout(self, mock_run):
        """Test run_cmd with None stdout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = None
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["echo", "test"])
        
        assert returncode == 0
        assert output == ""
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_complex_command(self, mock_run):
        """Test run_cmd with complex command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Complex output"
        mock_run.return_value = mock_result
        
        cmd = ["python", "-c", "print('hello world')"]
        returncode, output = run_cmd(cmd, cwd="/tmp", timeout=60)
        
        assert returncode == 0
        assert output == "Complex output"
        mock_run.assert_called_once_with(
            cmd,
            cwd="/tmp",
            stdout=-1,
            stderr=-2,
            text=True,
            timeout=60,
            check=False
        )
    
    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_multiple_args(self, mock_run):
        """Test run_cmd with multiple command arguments."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Multiple args output"
        mock_run.return_value = mock_result
        
        cmd = ["grep", "-r", "pattern", "directory"]
        returncode, output = run_cmd(cmd)
        
        assert returncode == 0
        assert output == "Multiple args output"
        mock_run.assert_called_once_with(
            cmd,
            cwd=None,
            stdout=-1,
            stderr=-2,
            text=True,
            timeout=900,
            check=False
        )
