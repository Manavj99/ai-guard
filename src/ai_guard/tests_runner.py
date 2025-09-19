"""Test runner for AI-Guard."""

import subprocess
import sys
import os
from typing import Optional, List, Dict, Any


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


def run_tests(test_files: List[str]) -> Dict[str, Any]:
    """Run tests on specified files.

    Args:
        test_files: List of test files to run

    Returns:
        Dictionary with test results
    """
    try:
        cmd = [sys.executable, "-m", "pytest", "-v"] + test_files
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Parse pytest output
        passed = 0
        failed = 0

        for line in result.stdout.split("\n"):
            if "PASSED" in line:
                passed += 1
            elif "FAILED" in line:
                failed += 1

        total = passed + failed

        return {
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "total": total,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Test timeout"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def discover_test_files(directory: str) -> Dict[str, Any]:
    """Discover test files in a directory.

    Args:
        directory: Directory to search for test files

    Returns:
        Dictionary with discovered test files
    """
    try:
        test_files = []

        for file in os.listdir(directory):
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(file)

        return {"success": True, "test_files": test_files}
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_test_suite(test_files: List[str]) -> Dict[str, Any]:
    """Execute a test suite.

    Args:
        test_files: List of test files to execute

    Returns:
        Dictionary with test suite results
    """
    return run_tests(test_files)


class TestRunner:
    """Test runner class."""

    def __init__(self) -> None:
        """Initialize the test runner."""
        self.runner_name = "Test Runner"
        self.test_command = "pytest"
        self.test_pattern = "test_*.py"

    def run_test_file(self, file_path: str) -> Dict[str, Any]:
        """Run a single test file.

        Args:
            file_path: Path to test file

        Returns:
            Dictionary with test results
        """
        return self._execute_test_command([file_path])

    def run_test_directory(self, directory: str) -> Dict[str, Any]:
        """Run tests in a directory.

        Args:
            directory: Directory containing tests

        Returns:
            Dictionary with test results
        """
        discovery_result = self.discover_test_files(directory)
        if not discovery_result["success"]:
            return discovery_result

        test_files = discovery_result["test_files"]
        if not test_files:
            return {
                "success": True,
                "files_run": 0,
                "total_passed": 0,
                "total_failed": 0,
            }

        total_passed = 0
        total_failed = 0

        for test_file in test_files:
            result = self.run_test_file(os.path.join(directory, test_file))
            if result["success"]:
                total_passed += result.get("passed", 0)
                total_failed += result.get("failed", 0)

        return {
            "success": True,
            "files_run": len(test_files),
            "total_passed": total_passed,
            "total_failed": total_failed,
        }

    def discover_test_files(self, directory: str) -> Dict[str, Any]:
        """Discover test files in directory.

        Args:
            directory: Directory to search

        Returns:
            Dictionary with discovered files
        """
        return discover_test_files(directory)

    def _execute_test_command(self, args: List[str]) -> Dict[str, Any]:
        """Execute test command.

        Args:
            args: Command arguments

        Returns:
            Dictionary with execution results
        """
        try:
            cmd = [sys.executable, "-m", "pytest", "-v"] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            passed = 0
            failed = 0

            for line in result.stdout.split("\n"):
                if "PASSED" in line:
                    passed += 1
                elif "FAILED" in line:
                    failed += 1

            return {
                "success": result.returncode == 0,
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class TestDiscoverer:
    """Test file discoverer."""

    def __init__(self) -> None:
        """Initialize the test discoverer."""
        self.discoverer_name = "Test Discoverer"
        self.test_patterns = ["test_*.py", "*_test.py"]

    def discover_test_files(
        self, directory: str, recursive: bool = False
    ) -> Dict[str, Any]:
        """Discover test files.

        Args:
            directory: Directory to search
            recursive: Whether to search recursively

        Returns:
            Dictionary with discovered files
        """
        try:
            test_files = []

            if recursive:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.startswith("test_") and file.endswith(".py"):
                            test_files.append(file)
            else:
                for file in os.listdir(directory):
                    if file.startswith("test_") and file.endswith(".py"):
                        test_files.append(file)

            return {"success": True, "test_files": test_files}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TestExecutor:
    """Test executor."""

    def __init__(self, timeout: int = 300):
        """Initialize the test executor.

        Args:
            timeout: Timeout in seconds
        """
        self.executor_name = "Test Executor"
        self.timeout = timeout

    def execute_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """Execute tests.

        Args:
            test_files: List of test files

        Returns:
            Dictionary with execution results
        """
        try:
            cmd = [sys.executable, "-m", "pytest", "-v"] + test_files
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )

            passed = 0
            failed = 0

            for line in result.stdout.split("\n"):
                if "PASSED" in line:
                    passed += 1
                elif "FAILED" in line:
                    failed += 1

            return {
                "success": result.returncode == 0,
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timeout"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_pytest(self, test_files: List[str]) -> Dict[str, Any]:
        """Run pytest on test files.

        Args:
            test_files: List of test files

        Returns:
            Dictionary with pytest results
        """
        return self.execute_tests(test_files)
