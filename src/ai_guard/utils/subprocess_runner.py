from __future__ import annotations

from subprocess import run, PIPE, STDOUT
from typing import Tuple, Sequence, Optional


class ToolExecutionError(RuntimeError):
    """Raised when a tool fails in a way that produces no parseable output."""
    pass


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
        return f"STDOUT: {stdout}\nSTDERR: {stderr}"
    elif stdout:
        return f"STDOUT: {stdout}"
    elif stderr:
        return f"STDERR: {stderr}"
    else:
        return "No output"
