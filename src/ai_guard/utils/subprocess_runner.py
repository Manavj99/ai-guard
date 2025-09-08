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
