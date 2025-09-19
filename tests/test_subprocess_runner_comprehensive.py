"""Comprehensive tests for subprocess_runner module to increase coverage."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from ai_guard.utils.subprocess_runner import (
    ToolExecutionError,
    run_cmd,
    run_command,
    run_command_dict,
    run_command_with_output,
    run_command_safe,
    SubprocessRunner,
    CommandExecutor,
    SafeCommandRunner
)


class TestToolExecutionError:
    """Test ToolExecutionError class."""
    
    def test_tool_execution_error_creation(self):
        """Test creating ToolExecutionError."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)


class TestRunCmd:
    """Test run_cmd function."""
    
    @patch('subprocess.run')
    def test_run_cmd_success(self, mock_run):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["echo", "hello"])
        assert returncode == 0
        assert output == "Success output"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test command failure with output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(["false"])
        assert returncode == 1
        assert output == "Error output"
    
    @patch('subprocess.run')
    def test_run_cmd_failure_no_output(self, mock_run):
        """Test command failure with no output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        with pytest.raises(ToolExecutionError, match="Command failed with code 1 and no output"):
            run_cmd(["false"])
    
    def test_run_cmd_empty_command(self):
        """Test run_cmd with empty command."""
        with pytest.raises(ToolExecutionError, match="Empty or None command provided"):
            run_cmd([])
    
    def test_run_cmd_none_command(self):
        """Test run_cmd with None command."""
        with pytest.raises(ToolExecutionError, match="Empty or None command provided"):
            run_cmd(None)
    
    @patch('subprocess.run')
    def test_run_cmd_exception(self, mock_run):
        """Test run_cmd with exception."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)
        
        with pytest.raises(ToolExecutionError, match="Command execution failed"):
            run_cmd(["sleep", "60"])
    
    @patch('subprocess.run')
    def test_run_cmd_with_cwd_and_timeout(self, mock_run):
        """Test run_cmd with custom cwd and timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Output"
        mock_run.return_value = mock_result
        
        run_cmd(["ls"], cwd="/tmp", timeout=60)
        mock_run.assert_called_once_with(
            ["ls"],
            cwd="/tmp",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60,
            check=False
        )


class TestRunCommand:
    """Test run_command function."""
    
    def test_run_command_none(self):
        """Test run_command with None."""
        returncode, output = run_command(None)
        assert returncode == 1
        assert output == "No command provided"
    
    def test_run_command_empty(self):
        """Test run_command with empty list."""
        returncode, output = run_command([])
        assert returncode == 1
        assert output == "Empty command"
    
    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_command_success(self, mock_run_cmd):
        """Test run_command with valid command."""
        mock_run_cmd.return_value = (0, "Success")
        returncode, output = run_command(["echo", "hello"])
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(["echo", "hello"])


class TestRunCommandDict:
    """Test run_command_dict function."""
    
    @patch('subprocess.run')
    def test_run_command_dict_success(self, mock_run):
        """Test run_command_dict success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_dict(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["stdout"] == "Success"
        assert result["stderr"] == ""
    
    @patch('subprocess.run')
    def test_run_command_dict_failure(self, mock_run):
        """Test run_command_dict failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result
        
        result = run_command_dict(["false"])
        assert result["success"] is False
        assert result["returncode"] == 1
        assert result["stdout"] == ""
        assert result["stderr"] == "Error"
    
    @patch('subprocess.run')
    def test_run_command_dict_timeout(self, mock_run):
        """Test run_command_dict timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)
        
        result = run_command_dict(["sleep", "60"])
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
    
    @patch('subprocess.run')
    def test_run_command_dict_called_process_error(self, mock_run):
        """Test run_command_dict with CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        
        result = run_command_dict(["false"])
        assert result["success"] is False
        assert "error" in result
    
    @patch('subprocess.run')
    def test_run_command_dict_general_exception(self, mock_run):
        """Test run_command_dict with general exception."""
        mock_run.side_effect = Exception("General error")
        
        result = run_command_dict(["invalid"])
        assert result["success"] is False
        assert "error" in result


class TestRunCommandWithOutput:
    """Test run_command_with_output function."""
    
    @patch('subprocess.run')
    def test_run_command_with_output_success(self, mock_run):
        """Test run_command_with_output success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_with_output(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["stdout"] == "Output"
        assert result["stderr"] == ""
    
    @patch('subprocess.run')
    def test_run_command_with_output_failure(self, mock_run):
        """Test run_command_with_output failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result
        
        result = run_command_with_output(["false"])
        assert result["success"] is False
        assert result["returncode"] == 1
        assert result["stderr"] == "Error"


class TestRunCommandSafe:
    """Test run_command_safe function."""
    
    @patch('subprocess.run')
    def test_run_command_safe_success(self, mock_run):
        """Test run_command_safe success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_safe(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["stdout"] == "Success"
        assert result["stderr"] == ""
    
    @patch('subprocess.run')
    def test_run_command_safe_with_timeout(self, mock_run):
        """Test run_command_safe with custom timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_safe(["echo", "hello"], timeout=60)
        assert result["success"] is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["timeout"] == 60


class TestSubprocessRunner:
    """Test SubprocessRunner class."""
    
    def test_subprocess_runner_init(self):
        """Test SubprocessRunner initialization."""
        runner = SubprocessRunner()
        assert runner is not None
    
    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_subprocess_runner_run_command(self, mock_run_cmd):
        """Test SubprocessRunner run_command method."""
        mock_run_cmd.return_value = (0, "Success")
        runner = SubprocessRunner()
        
        returncode, output = runner.run_command(["echo", "hello"])
        assert returncode == 0
        assert output == "Success"
        mock_run_cmd.assert_called_once_with(["echo", "hello"])
    
    @patch('ai_guard.utils.subprocess_runner.run_cmd')
    def test_subprocess_runner_run_command_with_cwd(self, mock_run_cmd):
        """Test SubprocessRunner run_command with cwd."""
        mock_run_cmd.return_value = (0, "Success")
        runner = SubprocessRunner()
        
        returncode, output = runner.run_command(["ls"], cwd="/tmp")
        assert returncode == 0
        mock_run_cmd.assert_called_once_with(["ls"], cwd="/tmp")


class TestCommandExecutor:
    """Test CommandExecutor class."""
    
    def test_command_executor_init(self):
        """Test CommandExecutor initialization."""
        executor = CommandExecutor()
        assert executor is not None
    
    @patch('ai_guard.utils.subprocess_runner.run_command_dict')
    def test_command_executor_execute(self, mock_run_command_dict):
        """Test CommandExecutor execute method."""
        mock_run_command_dict.return_value = {"success": True, "returncode": 0}
        executor = CommandExecutor()
        
        result = executor.execute(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        mock_run_command_dict.assert_called_once_with(["echo", "hello"])


class TestSafeCommandRunner:
    """Test SafeCommandRunner class."""
    
    def test_safe_command_runner_init(self):
        """Test SafeCommandRunner initialization."""
        runner = SafeCommandRunner()
        assert runner is not None
    
    @patch('ai_guard.utils.subprocess_runner.run_command_safe')
    def test_safe_command_runner_run_command_safe(self, mock_run_command_safe):
        """Test SafeCommandRunner run_command_safe method."""
        mock_run_command_safe.return_value = {"success": True, "returncode": 0}
        runner = SafeCommandRunner()
        
        result = runner.run_command_safe(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        mock_run_command_safe.assert_called_once_with(["echo", "hello"])
    
    @patch('ai_guard.utils.subprocess_runner.run_command_safe')
    def test_safe_command_runner_run_command_safe_with_timeout(self, mock_run_command_safe):
        """Test SafeCommandRunner run_command_safe with timeout."""
        mock_run_command_safe.return_value = {"success": True, "returncode": 0}
        runner = SafeCommandRunner()
        
        result = runner.run_command_safe(["echo", "hello"], timeout=60)
        assert result["success"] is True
        mock_run_command_safe.assert_called_once_with(["echo", "hello"], timeout=60)
    
    @patch('ai_guard.utils.subprocess_runner.run_command_safe')
    def test_safe_command_runner_run_command_safe_with_validation(self, mock_run_command_safe):
        """Test SafeCommandRunner run_command_safe with validation function."""
        mock_run_command_safe.return_value = {"success": True, "returncode": 0}
        runner = SafeCommandRunner()
        
        def validation_func(result):
            return result["success"]
        
        result = runner.run_command_safe(["echo", "hello"], validation_func=validation_func)
        assert result["success"] is True
        mock_run_command_safe.assert_called_once_with(["echo", "hello"], validation_func=validation_func)