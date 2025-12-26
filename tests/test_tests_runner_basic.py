"""Basic tests for tests_runner module."""

import subprocess
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from src.ai_guard.tests_runner import (
    run_tests,
    discover_test_files,
    execute_test_suite,
    TestRunner,
    TestDiscoverer,
    TestExecutor,
)


class TestRunTests:
    """Test run_tests function."""

    @patch("subprocess.run")
    def test_run_tests_success(self, mock_run):
        """Test successful test execution."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="test_file.py::test_function PASSED\n", stderr=""
        )

        result = run_tests(["test_file.py"])

        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1

    @patch("subprocess.run")
    def test_run_tests_with_failures(self, mock_run):
        """Test test execution with failures."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="test_file.py::test_function FAILED\ntest_file.py::test_another PASSED\n",
            stderr="",
        )

        result = run_tests(["test_file.py"])

        assert result["success"] is False
        assert result["passed"] == 1
        assert result["failed"] == 1
        assert result["total"] == 2

    @patch("subprocess.run")
    def test_run_tests_timeout(self, mock_run):
        """Test test execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        result = run_tests(["test_file.py"])

        assert result["success"] is False
        assert result["error"] == "Test timeout"

    @patch("subprocess.run")
    def test_run_tests_called_process_error(self, mock_run):
        """Test test execution with CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")

        result = run_tests(["test_file.py"])

        assert result["success"] is False
        assert "Command 'pytest' returned non-zero exit status 1." in result["error"]

    @patch("subprocess.run")
    def test_run_tests_general_exception(self, mock_run):
        """Test test execution with general exception."""
        mock_run.side_effect = Exception("Unexpected error")

        result = run_tests(["test_file.py"])

        assert result["success"] is False
        assert result["error"] == "Unexpected error"


class TestDiscoverTestFiles:
    """Test discover_test_files function."""

    def test_discover_test_files_success(self):
        """Test successful test file discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ["test_file1.py", "test_file2.py", "not_test.py"]
            for file in test_files:
                with open(os.path.join(temp_dir, file), "w") as f:
                    f.write("# Test file")

            result = discover_test_files(temp_dir)

            assert result["success"] is True
            assert "test_file1.py" in result["test_files"]
            assert "test_file2.py" in result["test_files"]
            assert "not_test.py" not in result["test_files"]

    def test_discover_test_files_no_tests(self):
        """Test discovering test files when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-test files
            with open(os.path.join(temp_dir, "regular_file.py"), "w") as f:
                f.write("# Regular file")

            result = discover_test_files(temp_dir)

            assert result["success"] is True
            assert result["test_files"] == []

    def test_discover_test_files_directory_not_found(self):
        """Test discovering test files in non-existent directory."""
        result = discover_test_files("/non/existent/directory")

        assert result["success"] is False
        assert "error" in result

    def test_discover_test_files_permission_error(self):
        """Test discovering test files with permission error."""
        with patch("os.listdir") as mock_listdir:
            mock_listdir.side_effect = PermissionError("Permission denied")

            result = discover_test_files("/some/directory")

            assert result["success"] is False
            assert "error" in result


class TestExecuteTestSuite:
    """Test execute_test_suite function."""

    @patch("src.ai_guard.tests_runner.run_tests")
    def test_execute_test_suite(self, mock_run_tests):
        """Test executing test suite."""
        mock_run_tests.return_value = {"success": True, "passed": 5, "failed": 0}

        result = execute_test_suite(["test1.py", "test2.py"])

        mock_run_tests.assert_called_once_with(["test1.py", "test2.py"])
        assert result["success"] is True
        assert result["passed"] == 5


class TestTestRunner:
    """Test TestRunner class."""

    def test_test_runner_init(self):
        """Test TestRunner initialization."""
        runner = TestRunner()

        assert runner.runner_name == "Test Runner"
        assert runner.test_command == "pytest"
        assert runner.test_pattern == "test_*.py"

    @patch("subprocess.run")
    def test_run_test_file_success(self, mock_run):
        """Test running a single test file successfully."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="test_file.py::test_function PASSED\n", stderr=""
        )

        runner = TestRunner()
        result = runner.run_test_file("test_file.py")

        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0

    @patch("subprocess.run")
    def test_run_test_file_failure(self, mock_run):
        """Test running a single test file with failures."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="test_file.py::test_function FAILED\n", stderr=""
        )

        runner = TestRunner()
        result = runner.run_test_file("test_file.py")

        assert result["success"] is False
        assert result["passed"] == 0
        assert result["failed"] == 1

    @patch("subprocess.run")
    def test_run_test_file_exception(self, mock_run):
        """Test running a single test file with exception."""
        mock_run.side_effect = Exception("Test error")

        runner = TestRunner()
        result = runner.run_test_file("test_file.py")

        assert result["success"] is False
        assert result["error"] == "Test error"

    @patch("src.ai_guard.tests_runner.discover_test_files")
    def test_run_test_directory_success(self, mock_discover):
        """Test running tests in a directory successfully."""
        mock_discover.return_value = {
            "success": True,
            "test_files": ["test1.py", "test2.py"],
        }

        with patch.object(TestRunner, "run_test_file") as mock_run_file:
            mock_run_file.side_effect = [
                {"success": True, "passed": 2, "failed": 0},
                {"success": True, "passed": 1, "failed": 1},
            ]

            runner = TestRunner()
            result = runner.run_test_directory("/test/dir")

            assert result["success"] is True
            assert result["files_run"] == 2
            assert result["total_passed"] == 3
            assert result["total_failed"] == 1

    @patch("src.ai_guard.tests_runner.discover_test_files")
    def test_run_test_directory_discovery_failure(self, mock_discover):
        """Test running tests in directory when discovery fails."""
        mock_discover.return_value = {"success": False, "error": "Discovery failed"}

        runner = TestRunner()
        result = runner.run_test_directory("/test/dir")

        assert result["success"] is False
        assert result["error"] == "Discovery failed"

    @patch("src.ai_guard.tests_runner.discover_test_files")
    def test_run_test_directory_no_tests(self, mock_discover):
        """Test running tests in directory with no test files."""
        mock_discover.return_value = {"success": True, "test_files": []}

        runner = TestRunner()
        result = runner.run_test_directory("/test/dir")

        assert result["success"] is True
        assert result["files_run"] == 0
        assert result["total_passed"] == 0
        assert result["total_failed"] == 0

    @patch("src.ai_guard.tests_runner.discover_test_files")
    def test_discover_test_files_method(self, mock_discover):
        """Test discover_test_files method."""
        mock_discover.return_value = {"success": True, "test_files": ["test.py"]}

        runner = TestRunner()
        result = runner.discover_test_files("/test/dir")

        mock_discover.assert_called_once_with("/test/dir")
        assert result["success"] is True
        assert result["test_files"] == ["test.py"]


class TestTestDiscoverer:
    """Test TestDiscoverer class."""

    def test_test_discoverer_init(self):
        """Test TestDiscoverer initialization."""
        discoverer = TestDiscoverer()

        assert discoverer.discoverer_name == "Test Discoverer"
        assert discoverer.test_patterns == ["test_*.py", "*_test.py"]

    def test_discover_test_files_non_recursive(self):
        """Test discovering test files non-recursively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ["test_file1.py", "test_file2.py", "not_test.py"]
            for file in test_files:
                with open(os.path.join(temp_dir, file), "w") as f:
                    f.write("# Test file")

            discoverer = TestDiscoverer()
            result = discoverer.discover_test_files(temp_dir, recursive=False)

            assert result["success"] is True
            assert "test_file1.py" in result["test_files"]
            assert "test_file2.py" in result["test_files"]
            assert "not_test.py" not in result["test_files"]

    def test_discover_test_files_recursive(self):
        """Test discovering test files recursively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            sub_dir = os.path.join(temp_dir, "subdir")
            os.makedirs(sub_dir)

            # Create test files in root and subdirectory
            with open(os.path.join(temp_dir, "test_root.py"), "w") as f:
                f.write("# Test file")
            with open(os.path.join(sub_dir, "test_sub.py"), "w") as f:
                f.write("# Test file")
            with open(os.path.join(sub_dir, "not_test.py"), "w") as f:
                f.write("# Not test file")

            discoverer = TestDiscoverer()
            result = discoverer.discover_test_files(temp_dir, recursive=True)

            assert result["success"] is True
            assert "test_root.py" in result["test_files"]
            assert "test_sub.py" in result["test_files"]
            assert "not_test.py" not in result["test_files"]

    def test_discover_test_files_exception(self):
        """Test discovering test files with exception."""
        with patch("os.walk") as mock_walk:
            mock_walk.side_effect = Exception("Walk error")

            discoverer = TestDiscoverer()
            result = discoverer.discover_test_files("/some/dir", recursive=True)

            assert result["success"] is False
            assert "error" in result


class TestTestExecutor:
    """Test TestExecutor class."""

    def test_test_executor_init_default(self):
        """Test TestExecutor initialization with default timeout."""
        executor = TestExecutor()

        assert executor.executor_name == "Test Executor"
        assert executor.timeout == 300

    def test_test_executor_init_custom_timeout(self):
        """Test TestExecutor initialization with custom timeout."""
        executor = TestExecutor(timeout=600)

        assert executor.executor_name == "Test Executor"
        assert executor.timeout == 600

    @patch("subprocess.run")
    def test_execute_tests_success(self, mock_run):
        """Test successful test execution."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="test_file.py::test_function PASSED\n", stderr=""
        )

        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])

        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1

    @patch("subprocess.run")
    def test_execute_tests_failure(self, mock_run):
        """Test test execution with failures."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="test_file.py::test_function FAILED\n", stderr=""
        )

        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])

        assert result["success"] is False
        assert result["passed"] == 0
        assert result["failed"] == 1

    @patch("subprocess.run")
    def test_execute_tests_timeout(self, mock_run):
        """Test test execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])

        assert result["success"] is False
        assert result["error"] == "Test execution timeout"

    @patch("subprocess.run")
    def test_execute_tests_called_process_error(self, mock_run):
        """Test test execution with CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")

        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])

        assert result["success"] is False
        assert "Command 'pytest' returned non-zero exit status 1." in result["error"]

    @patch("subprocess.run")
    def test_execute_tests_general_exception(self, mock_run):
        """Test test execution with general exception."""
        mock_run.side_effect = Exception("Unexpected error")

        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])

        assert result["success"] is False
        assert result["error"] == "Unexpected error"

    def test_run_pytest_method(self):
        """Test _run_pytest method."""
        executor = TestExecutor()

        with patch.object(executor, "execute_tests") as mock_execute:
            mock_execute.return_value = {"success": True, "passed": 1}

            result = executor._run_pytest(["test_file.py"])

            mock_execute.assert_called_once_with(["test_file.py"])
            assert result["success"] is True
            assert result["passed"] == 1


class TestMissingCoverage:
    """Test missing coverage lines."""

    @patch("subprocess.call")
    def test_run_pytest_direct_call(self, mock_call):
        """Test direct call to run_pytest function."""
        mock_call.return_value = 0

        from src.ai_guard.tests_runner import run_pytest

        result = run_pytest(["--verbose"])

        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--verbose"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_run_pytest_with_coverage_direct_call(self, mock_call):
        """Test direct call to run_pytest_with_coverage function."""
        mock_call.return_value = 0

        from src.ai_guard.tests_runner import run_pytest_with_coverage

        result = run_pytest_with_coverage()

        expected_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--cov=src",
            "--cov-report=xml",
        ]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_tests_runner_run_pytest_direct(self, mock_call):
        """Test TestsRunner.run_pytest method directly."""
        mock_call.return_value = 0

        from src.ai_guard.tests_runner import TestsRunner

        runner = TestsRunner()
        result = runner.run_pytest(["--verbose"])

        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--verbose"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_tests_runner_run_pytest_with_coverage_direct(self, mock_call):
        """Test TestsRunner.run_pytest_with_coverage method directly."""
        mock_call.return_value = 0

        from src.ai_guard.tests_runner import TestsRunner

        runner = TestsRunner()
        result = runner.run_pytest_with_coverage()

        expected_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--cov=src",
            "--cov-report=xml",
        ]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_tests_runner_run_tests_direct(self, mock_call):
        """Test TestsRunner.run_tests method directly."""
        mock_call.return_value = 0

        from src.ai_guard.tests_runner import TestsRunner

        runner = TestsRunner()
        result = runner.run_tests(with_coverage=True)

        expected_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--cov=src",
            "--cov-report=xml",
        ]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_tests_runner_run_tests_without_coverage_direct(self, mock_call):
        """Test TestsRunner.run_tests method without coverage."""
        mock_call.return_value = 0

        from src.ai_guard.tests_runner import TestsRunner

        runner = TestsRunner()
        result = runner.run_tests(with_coverage=False)

        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0
