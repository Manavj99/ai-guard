"""Test runner for AI-Guard."""

import subprocess
import sys
from typing import Optional, List


def run_pytest(extra_args: Optional[List[str]] = None) -> int:
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


class TestsRunner:
    """Test runner for AI-Guard."""

    def __init__(self) -> None:
        """Initialize the test runner."""

    def run_pytest(self, extra_args: Optional[List[str]] = None) -> int:
        """Run pytest with the given arguments.

        Args:
            extra_args: Additional arguments to pass to pytest

        Returns:
            Exit code from pytest
        """
        return run_pytest(extra_args)

    def run_pytest_with_coverage(self) -> int:
        """Run pytest with coverage reporting.

        Returns:
            Exit code from pytest
        """
        return run_pytest_with_coverage()

    def run_tests(self, with_coverage: bool = True) -> int:
        """Run tests with optional coverage.

        Args:
            with_coverage: Whether to run with coverage reporting

        Returns:
            Exit code from test run
        """
        if with_coverage:
            return self.run_pytest_with_coverage()
        else:
            return self.run_pytest()
