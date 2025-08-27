"""Test runner for AI-Guard."""

import subprocess
import sys
from typing import Optional


def run_pytest(extra_args: Optional[list] = None) -> int:
    """Run pytest with the given arguments.
    
    Args:
        extra_args: Additional arguments to pass to pytest
        
    Returns:
        Exit code from pytest
    """
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if extra_args:
        cmd.extend(extra_args)
    
    return subprocess.call(cmd)


def run_pytest_with_coverage() -> int:
    """Run pytest with coverage reporting.
    
    Returns:
        Exit code from pytest
    """
    return run_pytest(["--cov=src", "--cov-report=xml"])
