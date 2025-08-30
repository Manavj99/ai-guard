"""Security scanning for AI-Guard."""

import subprocess
import os
from typing import Optional, List


def run_bandit(extra_args: Optional[List[str]] = None) -> int:
    """Run bandit security scanner.

    Args:
        extra_args: Additional arguments to pass to bandit

    Returns:
        Exit code from bandit
    """
    cmd = ["bandit", "-r", "src"]

    # Check if .bandit config exists, if not use default settings
    if os.path.exists(".bandit"):
        cmd.extend(["-c", ".bandit"])
    else:
        # Use default bandit settings if no config file
        cmd.extend(["-f", "json", "-ll"])

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
