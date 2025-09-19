"""Basic tests for tests_runner.py module."""

import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest

from src.ai_guard.tests_runner import (
    run_pytest,
    run_pytest_with_coverage,
    TestsRunner,
    run_tests,
    discover_test_files,
    TestRunner,
    TestDiscoverer,
    TestExecutor,
)


class TestRunPytest:
    """Test run_pytest function."""

    @patch("subprocess.call")
    def test_run_pytest_no_args(self, mock_call):
        """Test run_pytest with no extra arguments."""
        mock_call.return_value = 0
        result = run_pytest()
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_run_pytest_with_args(self, mock_call):
        """Test run_pytest with extra arguments."""
        mock_call.return_value = 0
        extra_args = ["--verbose", "--tb=short"]
        result = run_pytest(extra_args)
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--verbose", "--tb=short"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0


class TestRunPytestWithCoverage:
    """Test run_pytest_with_coverage function."""

    @patch("src.ai_guard.tests_runner.run_pytest")
    def test_run_pytest_with_coverage(self, mock_run_pytest):
        """Test run_pytest_with_coverage calls run_pytest with coverage args."""
        mock_run_pytest.return_value = 0
        result = run_pytest_with_coverage()
        mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
        assert result == 0


class TestTestsRunner:
    """Test TestsRunner class."""

    def test_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None

    @patch("src.ai_guard.tests_runner.run_pytest")
    def test_run_pytest(self, mock_run_pytest):
        """Test run_pytest method."""
        runner = TestsRunner()
        mock_run_pytest.return_value = 0
        result = runner.run_pytest(["--verbose"])
        mock_run_pytest.assert_called_once_with(["--verbose"])
        assert result == 0

    @patch("src.ai_guard.tests_runner.run_pytest_with_coverage")
    def test_run_pytest_with_coverage(self, mock_run_coverage):
        """Test run_pytest_with_coverage method."""
        runner = TestsRunner()
        mock_run_coverage.return_value = 0
        result = runner.run_pytest_with_coverage()
        mock_run_coverage.assert_called_once()
        assert result == 0

    @patch("src.ai_guard.tests_runner.run_pytest_with_coverage")
    def test_run_tests_with_coverage(self, mock_run_coverage):
        """Test run_tests with coverage."""
        runner = TestsRunner()
        mock_run_coverage.return_value = 0
        result = runner.run_tests(with_coverage=True)
        mock_run_coverage.assert_called_once()
        assert result == 0

    @patch("src.ai_guard.tests_runner.run_pytest")
    def test_run_tests_without_coverage(self, mock_run_pytest):
        """Test run_tests without coverage."""
        runner = TestsRunner()
        mock_run_pytest.return_value = 0
        result = runner.run_tests(with_coverage=False)
        mock_run_pytest.assert_called_once_with(None)
        assert result == 0


class TestRunTests:
    """Test run_tests function."""

    @patch("subprocess.run")
    def test_run_tests_success(self, mock_run):
        """Test successful test run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_module.py::test_function PASSED\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_tests(["test_module.py"])
        
        expected_cmd = [sys.executable, "-m", "pytest", "-v", "test_module.py"]
        mock_run.assert_called_once_with(expected_cmd, capture_output=True, text=True, timeout=300)
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1

    @patch("subprocess.run")
    def test_run_tests_failure(self, mock_run):
        """Test failed test run."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test_module.py::test_function FAILED\n"
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is False
        assert result["passed"] == 0
        assert result["failed"] == 1
        assert result["total"] == 1

    @patch("subprocess.run")
    def test_run_tests_timeout(self, mock_run):
        """Test test run timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)
        result = run_tests(["test_module.py"])
        assert result["success"] is False
        assert result["error"] == "Test timeout"


class TestDiscoverTestFiles:
    """Test discover_test_files function."""

    @patch("os.listdir")
    def test_discover_test_files_success(self, mock_listdir):
        """Test successful test file discovery."""
        mock_listdir.return_value = ["test_module.py", "test_another.py", "not_test.py", "test_file.txt"]
        result = discover_test_files("/test/dir")
        assert result["success"] is True
        assert result["test_files"] == ["test_module.py", "test_another.py"]

    @patch("os.listdir")
    def test_discover_test_files_no_tests(self, mock_listdir):
        """Test discovery with no test files."""
        mock_listdir.return_value = ["module.py", "script.py", "readme.txt"]
        result = discover_test_files("/test/dir")
        assert result["success"] is True
        assert result["test_files"] == []

    @patch("os.listdir")
    def test_discover_test_files_exception(self, mock_listdir):
        """Test discovery with exception."""
        mock_listdir.side_effect = OSError("Permission denied")
        result = discover_test_files("/test/dir")
        assert result["success"] is False
        assert "Permission denied" in result["error"]


class TestTestRunner:
    """Test TestRunner class."""

    def test_init(self):
        """Test TestRunner initialization."""
        runner = TestRunner()
        assert runner.runner_name == "Test Runner"
        assert runner.test_command == "pytest"
        assert runner.test_pattern == "test_*.py"

    @patch("src.ai_guard.tests_runner.subprocess.run")
    def test_run_test_file_success(self, mock_run):
        """Test successful single test file run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_module.py::test_function PASSED\n"
        mock_run.return_value = mock_result
        
        runner = TestRunner()
        result = runner.run_test_file("test_module.py")
        
        expected_cmd = [sys.executable, "-m", "pytest", "-v", "test_module.py"]
        mock_run.assert_called_once_with(expected_cmd, capture_output=True, text=True, timeout=300)
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0


class TestTestDiscoverer:
    """Test TestDiscoverer class."""

    def test_init(self):
        """Test TestDiscoverer initialization."""
        discoverer = TestDiscoverer()
        assert discoverer.discoverer_name == "Test Discoverer"
        assert discoverer.test_patterns == ["test_*.py", "*_test.py"]

    @patch("os.listdir")
    def test_discover_test_files_non_recursive(self, mock_listdir):
        """Test non-recursive test file discovery."""
        mock_listdir.return_value = ["test_module.py", "test_another.py", "not_test.py"]
        discoverer = TestDiscoverer()
        result = discoverer.discover_test_files("/test/dir", recursive=False)
        assert result["success"] is True
        assert result["test_files"] == ["test_module.py", "test_another.py"]


class TestTestExecutor:
    """Test TestExecutor class."""

    def test_init_default_timeout(self):
        """Test TestExecutor initialization with default timeout."""
        executor = TestExecutor()
        assert executor.executor_name == "Test Executor"
        assert executor.timeout == 300

    def test_init_custom_timeout(self):
        """Test TestExecutor initialization with custom timeout."""
        executor = TestExecutor(timeout=600)
        assert executor.timeout == 600

    @patch("subprocess.run")
    def test_execute_tests_success(self, mock_run):
        """Test successful test execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test PASSED\n"
        mock_run.return_value = mock_result
        
        executor = TestExecutor()
        result = executor.execute_tests(["test.py"])
        
        expected_cmd = [sys.executable, "-m", "pytest", "-v", "test.py"]
        mock_run.assert_called_once_with(expected_cmd, capture_output=True, text=True, timeout=300)
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0

    @patch("subprocess.run")
    def test_execute_tests_timeout(self, mock_run):
        """Test test execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)
        executor = TestExecutor()
        result = executor.execute_tests(["test.py"])
        assert result["success"] is False
        assert result["error"] == "Test execution timeout"


if __name__ == "__main__":
    pytest.main([__file__])