"""Extended tests for subprocess runner to improve coverage."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.ai_guard.utils.subprocess_runner import (
    ToolExecutionError,
    run_cmd,
    run_command,
    _format_command_output,
    run_command_with_output,
    run_command_safe,
    SubprocessRunner,
    CommandExecutor,
    SafeCommandRunner
)


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_tool_execution_error_creation(self):
        """Test ToolExecutionError creation."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, RuntimeError)


class TestRunCmd:
    """Test run_cmd function."""

    def test_run_cmd_empty_command(self):
        """Test run_cmd with empty command."""
        with pytest.raises(ToolExecutionError):
            run_cmd([])

    def test_run_cmd_none_command(self):
        """Test run_cmd with None command."""
        with pytest.raises(ToolExecutionError):
            run_cmd(None)

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_success(self, mock_run):
        """Test run_cmd with successful execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(['echo', 'test'])
        
        assert returncode == 0
        assert output == "Success output"

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_with_output(self, mock_run):
        """Test run_cmd with failure but output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(['false'])
        
        assert returncode == 1
        assert output == "Error output"

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_failure_no_output(self, mock_run):
        """Test run_cmd with failure and no output."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        with pytest.raises(ToolExecutionError):
            run_cmd(['false'])

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_exception(self, mock_run):
        """Test run_cmd with exception."""
        mock_run.side_effect = Exception("Test error")
        
        with pytest.raises(ToolExecutionError):
            run_cmd(['echo', 'test'])

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_cwd(self, mock_run):
        """Test run_cmd with working directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(['echo', 'test'], cwd='/tmp')
        
        assert returncode == 0
        mock_run.assert_called_once()

    @patch('src.ai_guard.utils.subprocess_runner.run')
    def test_run_cmd_with_timeout(self, mock_run):
        """Test run_cmd with timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_run.return_value = mock_result
        
        returncode, output = run_cmd(['echo', 'test'], timeout=60)
        
        assert returncode == 0
        mock_run.assert_called_once()


class TestRunCommand:
    """Test run_command function."""

    @patch('subprocess.run')
    def test_run_command_none(self, mock_run):
        """Test run_command with None command."""
        result = run_command(None)
        assert result['success'] is False
        assert 'error' in result

    @patch('subprocess.run')
    def test_run_command_empty(self, mock_run):
        """Test run_command with empty command."""
        result = run_command([])
        assert result['success'] is False
        assert 'error' in result

    @patch('subprocess.run')
    def test_run_command_valid(self, mock_run):
        """Test run_command with valid command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command(['echo', 'test'])
        
        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "Success"


class TestFormatCommandOutput:
    """Test _format_command_output function."""

    def test_format_command_output_both(self):
        """Test formatting with both stdout and stderr."""
        result = _format_command_output("stdout", "stderr")
        assert result == "stdout\nstderr"

    def test_format_command_output_stdout_only(self):
        """Test formatting with stdout only."""
        result = _format_command_output("stdout", "")
        assert result == "stdout"

    def test_format_command_output_stderr_only(self):
        """Test formatting with stderr only."""
        result = _format_command_output("", "stderr")
        assert result == "stderr"

    def test_format_command_output_neither(self):
        """Test formatting with neither stdout nor stderr."""
        result = _format_command_output("", "")
        assert result == "No output"


class TestRunCommandWithOutput:
    """Test run_command_with_output function."""

    @patch('subprocess.run')
    def test_run_command_with_output_success(self, mock_run):
        """Test run_command_with_output with success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_with_output(['echo', 'test'])
        
        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "Success"

    @patch('subprocess.run')
    def test_run_command_with_output_failure(self, mock_run):
        """Test run_command_with_output with failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result
        
        result = run_command_with_output(['false'])
        
        assert result['success'] is False
        assert result['returncode'] == 1

    @patch('subprocess.run')
    def test_run_command_with_output_timeout(self, mock_run):
        """Test run_command_with_output with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('echo', 30)
        
        result = run_command_with_output(['echo', 'test'])
        
        assert result['success'] is False
        assert result['error'] == "Command timeout"

    @patch('subprocess.run')
    def test_run_command_with_output_called_process_error(self, mock_run):
        """Test run_command_with_output with CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'echo')
        
        result = run_command_with_output(['echo', 'test'])
        
        assert result['success'] is False
        assert 'error' in result

    @patch('subprocess.run')
    def test_run_command_with_output_general_exception(self, mock_run):
        """Test run_command_with_output with general exception."""
        mock_run.side_effect = Exception("General error")
        
        result = run_command_with_output(['echo', 'test'])
        
        assert result['success'] is False
        assert result['error'] == "General error"


class TestRunCommandSafe:
    """Test run_command_safe function."""

    @patch('subprocess.run')
    def test_run_command_safe_success(self, mock_run):
        """Test run_command_safe with success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_safe(['echo', 'test'])
        
        assert result['success'] is True
        assert result['returncode'] == 0

    @patch('subprocess.run')
    def test_run_command_safe_with_timeout(self, mock_run):
        """Test run_command_safe with custom timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_safe(['echo', 'test'], timeout=60)
        
        assert result['success'] is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_command_safe_timeout_expired(self, mock_run):
        """Test run_command_safe with timeout expired."""
        mock_run.side_effect = subprocess.TimeoutExpired('echo', 30)
        
        result = run_command_safe(['echo', 'test'], timeout=30)
        
        assert result['success'] is False
        assert "Command timeout after 30s" in result['error']


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

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test execute_command with success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        runner = SubprocessRunner()
        result = runner.execute_command(['echo', 'test'])
        
        assert result['success'] is True
        assert result['returncode'] == 0

    @patch('subprocess.run')
    def test_execute_command_without_capture(self, mock_run):
        """Test execute_command without output capture."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        runner = SubprocessRunner(capture_output=False)
        result = runner.execute_command(['echo', 'test'])
        
        assert result['success'] is True
        assert result['stdout'] == ""
        assert result['stderr'] == ""

    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test execute_command with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('echo', 30)
        
        runner = SubprocessRunner(timeout=30)
        result = runner.execute_command(['echo', 'test'])
        
        assert result['success'] is False
        assert "Command timeout after 30s" in result['error']

    @patch('subprocess.run')
    def test_execute_command_with_output(self, mock_run):
        """Test execute_command_with_output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        runner = SubprocessRunner()
        result = runner.execute_command_with_output(['echo', 'test'])
        
        assert result['success'] is True
        assert result['stdout'] == "Success"

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_execute_command_safe(self, mock_run_safe):
        """Test execute_command_safe."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        runner = SubprocessRunner()
        result = runner.execute_command_safe(['echo', 'test'])
        
        assert result['success'] is True
        mock_run_safe.assert_called_once_with(['echo', 'test'], 30)


class TestCommandExecutor:
    """Test CommandExecutor class."""

    def test_command_executor_init(self):
        """Test CommandExecutor initialization."""
        executor = CommandExecutor()
        assert executor.executor_name == "Command Executor"
        assert executor.default_timeout == 30

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_execute_command(self, mock_run_safe):
        """Test execute_command method."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        executor = CommandExecutor()
        result = executor.execute_command(['echo', 'test'])
        
        assert result['success'] is True
        mock_run_safe.assert_called_once_with(['echo', 'test'], 30)

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_execute_command_with_timeout(self, mock_run_safe):
        """Test execute_command with custom timeout."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        executor = CommandExecutor()
        result = executor.execute_command(['echo', 'test'], timeout=60)
        
        assert result['success'] is True
        mock_run_safe.assert_called_once_with(['echo', 'test'], 60)

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_execute_multiple_commands(self, mock_run_safe):
        """Test execute_multiple_commands method."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        executor = CommandExecutor()
        commands = [['echo', 'test1'], ['echo', 'test2']]
        results = executor.execute_multiple_commands(commands)
        
        assert len(results) == 2
        assert all(result['success'] for result in results)
        assert mock_run_safe.call_count == 2


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

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_run_command_safe_success_first_try(self, mock_run_safe):
        """Test run_command_safe with success on first try."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        runner = SafeCommandRunner()
        result = runner.run_command_safe(['echo', 'test'])
        
        assert result['success'] is True
        assert result['attempts'] == 1
        assert result['validated'] is True
        assert mock_run_safe.call_count == 1

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_run_command_safe_success_with_validation(self, mock_run_safe):
        """Test run_command_safe with validation function."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        def validation_func(result):
            return result['returncode'] == 0
        
        runner = SafeCommandRunner()
        result = runner.run_command_safe(['echo', 'test'], validation_func=validation_func)
        
        assert result['success'] is True
        assert result['validated'] is True

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_run_command_safe_failure_all_retries(self, mock_run_safe):
        """Test run_command_safe with failure after all retries."""
        mock_run_safe.return_value = {'success': False, 'error': 'Test error'}
        
        runner = SafeCommandRunner(max_retries=2)
        result = runner.run_command_safe(['echo', 'test'])
        
        assert result['success'] is False
        assert result['attempts'] == 2
        assert "Failed after 2 attempts" in result['error']
        assert mock_run_safe.call_count == 2

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_run_command_safe_success_after_retries(self, mock_run_safe):
        """Test run_command_safe with success after retries."""
        mock_run_safe.side_effect = [
            {'success': False, 'error': 'First failure'},
            {'success': True, 'returncode': 0}
        ]
        
        runner = SafeCommandRunner(max_retries=3)
        result = runner.run_command_safe(['echo', 'test'])
        
        assert result['success'] is True
        assert result['attempts'] == 2
        assert mock_run_safe.call_count == 2

    @patch('src.ai_guard.utils.subprocess_runner.run_command_safe')
    def test_run_command_safe_with_custom_timeout(self, mock_run_safe):
        """Test run_command_safe with custom timeout."""
        mock_run_safe.return_value = {'success': True, 'returncode': 0}
        
        runner = SafeCommandRunner()
        result = runner.run_command_safe(['echo', 'test'], timeout=60)
        
        assert result['success'] is True
        mock_run_safe.assert_called_once_with(['echo', 'test'], 60)
