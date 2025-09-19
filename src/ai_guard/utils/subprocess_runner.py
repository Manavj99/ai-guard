"""Subprocess runner utility functions."""

from __future__ import annotations

import subprocess
from subprocess import run, PIPE, STDOUT
from typing import Tuple, Sequence, Optional, Dict, Any, List


class ToolExecutionError(RuntimeError):
    """Raised when a tool fails in a way that produces no parseable output."""


def run_cmd(
    cmd: Sequence[str],
    cwd: Optional[str] = None,
    timeout: int = 900,
) -> Tuple[int, str]:
    """
    Run a CLI command and ALWAYS return (returncode, combined_output).

    Many dev tools (flake8, mypy, bandit, eslint, jest) use a non-zero exit code
    to indicate findings. We still want to parse their output. Only when there is
    no output at all do we raise ToolExecutionError so callers can decide.
    """
    if not cmd or cmd is None:
        raise ToolExecutionError("Empty or None command provided")

    try:
        p = run(
            cmd,
            cwd=cwd,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = p.stdout or ""
        if p.returncode != 0 and not out.strip():
            raise ToolExecutionError(
                f"Command failed with code {p.returncode} and no output: {' '.join(cmd)}"
            )
        return p.returncode, out
    except Exception as e:
        raise ToolExecutionError(f"Command execution failed: {str(e)}")


def run_command(cmd: Optional[Sequence[str]]) -> Tuple[int, str]:
    """
    Run a command with optional arguments.

    Args:
        cmd: Command and arguments, or None

    Returns:
        Tuple of (returncode, output)
    """
    if cmd is None:
        return 1, "No command provided"
    if not cmd:
        return 1, "Empty command"
    return run_cmd(cmd)


def _format_command_output(stdout: str, stderr: str) -> str:
    """
    Format command output for display.

    Args:
        stdout: Standard output
        stderr: Standard error

    Returns:
        Formatted output string
    """
    if stdout and stderr:
        return f"{stdout}\n{stderr}"
    elif stdout:
        return stdout
    elif stderr:
        return stderr
    else:
        return "No output"


def run_command_dict(cmd: List[str]) -> Dict[str, Any]:
    """Run a command and return results.

    Args:
        cmd: Command to run

    Returns:
        Dictionary with command results
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_command_with_output(cmd: List[str]) -> Dict[str, Any]:
    """Run a command and capture output.

    Args:
        cmd: Command to run

    Returns:
        Dictionary with command results and output
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_command_safe(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    """Run a command safely with error handling.

    Args:
        cmd: Command to run
        timeout: Timeout in seconds

    Returns:
        Dictionary with command results
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timeout after {timeout}s"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


class SubprocessRunner:
    """Subprocess runner with configuration options."""

    def __init__(self, timeout: int = 30, capture_output: bool = True):
        """Initialize the subprocess runner.

        Args:
            timeout: Default timeout in seconds
            capture_output: Whether to capture output
        """
        self.timeout = timeout
        self.capture_output = capture_output

    def execute_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute a command.

        Args:
            cmd: Command to execute

        Returns:
            Dictionary with execution results
        """
        try:
            result = subprocess.run(
                cmd, capture_output=self.capture_output, text=True, timeout=self.timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if self.capture_output else "",
                "stderr": result.stderr if self.capture_output else "",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timeout after {self.timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_command_with_output(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute a command and capture output.

        Args:
            cmd: Command to execute

        Returns:
            Dictionary with execution results and output
        """
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timeout after {self.timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_command_safe(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute a command safely.

        Args:
            cmd: Command to execute

        Returns:
            Dictionary with execution results
        """
        return run_command_safe(cmd, self.timeout)


class CommandExecutor:
    """Command executor with advanced features."""

    def __init__(self):
        """Initialize the command executor."""
        self.executor_name = "Command Executor"
        self.default_timeout = 30

    def execute_command(
        self, cmd: List[str], timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a command.

        Args:
            cmd: Command to execute
            timeout: Optional timeout override

        Returns:
            Dictionary with execution results
        """
        timeout = timeout or self.default_timeout
        return run_command_safe(cmd, timeout)

    def execute_multiple_commands(
        self, commands: List[List[str]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple commands.

        Args:
            commands: List of commands to execute

        Returns:
            List of execution results
        """
        results = []
        for cmd in commands:
            results.append(self.execute_command(cmd))
        return results


class SafeCommandRunner:
    """Safe command runner with retry logic."""

    def __init__(self, max_retries: int = 3):
        """Initialize the safe command runner.

        Args:
            max_retries: Maximum number of retries
        """
        self.runner_name = "Safe Command Runner"
        self.max_retries = max_retries

    def run_command_safe(
        self,
        cmd: List[str],
        timeout: int = 30,
        validation_func: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Run a command safely with retry logic.

        Args:
            cmd: Command to run
            timeout: Timeout in seconds
            validation_func: Optional validation function

        Returns:
            Dictionary with execution results
        """
        attempts = 0
        last_error = None

        while attempts < self.max_retries:
            attempts += 1
            result = run_command_safe(cmd, timeout)

            if result["success"]:
                # Validate result if validation function provided
                if validation_func:
                    result["validated"] = validation_func(result)
                else:
                    result["validated"] = True

                result["attempts"] = attempts
                return result

            last_error = result.get("error", "Unknown error")

        return {
            "success": False,
            "error": f"Failed after {attempts} attempts: {last_error}",
            "attempts": attempts,
        }
