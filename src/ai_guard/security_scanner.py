"""Security scanning for AI-Guard."""

import subprocess
from typing import Optional, List


def run_bandit(extra_args: Optional[List[str]] = None) -> int:
    """Run bandit security scanner.

    Args:
        extra_args: Additional arguments to pass to bandit

    Returns:
        Exit code from bandit
    """
    cmd = ["bandit", "-r", "src", "-c", ".bandit"]
    if extra_args:
        cmd.extend(extra_args)

    return subprocess.call(cmd)


def run_safety_check() -> int:
    """Run safety check for known vulnerabilities in dependencies.

    Returns:
        Exit code from safety check
    """
    try:
        return subprocess.call(["safety", "check"])
    except FileNotFoundError:
        # Safety not installed, skip
        print("Warning: safety not installed, skipping dependency security check")
        return 0
