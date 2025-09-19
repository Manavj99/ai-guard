"""Enhanced tests for tests_runner module to improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.ai_guard.tests_runner import (
    run_pytest,
    run_pytest_with_coverage,
    TestsRunner,
    run_tests,
    discover_test_files,
    execute_test_suite,
    TestRunner,
    TestDiscoverer,
    TestExecutor
)


class TestRunPytest:
    """Test run_pytest function."""

    @patch('subprocess.call')
    def test_run_pytest_no_args(self, mock_call):
        """Test run_pytest with no extra args."""
        mock_call.return_value = 0
        
        result = run_pytest()
        
        assert result == 0
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert "python" in call_args[0] or "pytest" in call_args[2]

    @patch('subprocess.call')
    def test_run_pytest_with_args(self, mock_call):
        """Test run_pytest with extra args."""
        mock_call.return_value = 0
        extra_args = ["--verbose", "--tb=short"]
        
        result = run_pytest(extra_args)
        
        assert result == 0
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert "--verbose" in call_args
        assert "--tb=short" in call_args

    @patch('subprocess.call')
    def test_run_pytest_failure(self, mock_call):
        """Test run_pytest with failure."""
        mock_call.return_value = 1
        
        result = run_pytest()
        
        assert result == 1

    @patch('subprocess.call')
    def test_run_pytest_none_args(self, mock_call):
        """Test run_pytest with None args."""
        mock_call.return_value = 0
        
        result = run_pytest(None)
        
        assert result == 0
        mock_call.assert_called_once()


class TestRunPytestWithCoverage:
    """Test run_pytest_with_coverage function."""

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_with_coverage(self, mock_run_pytest):
        """Test run_pytest_with_coverage."""
        mock_run_pytest.return_value = 0
        
        result = run_pytest_with_coverage()
        
        assert result == 0
        mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])


class TestTestsRunner:
    """Test TestsRunner class."""

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_pytest(self, mock_run_pytest):
        """Test TestsRunner run_pytest method."""
        mock_run_pytest.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_pytest(["--verbose"])
        
        assert result == 0
        mock_run_pytest.assert_called_once_with(["--verbose"])

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_tests_runner_run_pytest_with_coverage(self, mock_run_coverage):
        """Test TestsRunner run_pytest_with_coverage method."""
        mock_run_coverage.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_pytest_with_coverage()
        
        assert result == 0
        mock_run_coverage.assert_called_once()

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_tests_runner_run_tests_with_coverage(self, mock_run_coverage):
        """Test TestsRunner run_tests with coverage."""
        mock_run_coverage.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_tests(with_coverage=True)
        
        assert result == 0
        mock_run_coverage.assert_called_once()

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_tests_without_coverage(self, mock_run_pytest):
        """Test TestsRunner run_tests without coverage."""
        mock_run_pytest.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_tests(with_coverage=False)
        
        assert result == 0
        mock_run_pytest.assert_called_once_with(None)


class TestRunTests:
    """Test run_tests function."""

    @patch('subprocess.run')
    def test_run_tests_success(self, mock_run):
        """Test run_tests with success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_module.py::test_function PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1
        assert "PASSED" in result["stdout"]

    @patch('subprocess.run')
    def test_run_tests_failure(self, mock_run):
        """Test run_tests with failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test_module.py::test_function FAILED"
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is False
        assert result["passed"] == 0
        assert result["failed"] == 1
        assert result["total"] == 1
        assert "FAILED" in result["stdout"]

    @patch('subprocess.run')
    def test_run_tests_mixed_results(self, mock_run):
        """Test run_tests with mixed results."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = """test_module.py::test_function1 PASSED
test_module.py::test_function2 FAILED
test_module.py::test_function3 PASSED"""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is False
        assert result["passed"] == 2
        assert result["failed"] == 1
        assert result["total"] == 3

    @patch('subprocess.run')
    def test_run_tests_timeout(self, mock_run):
        """Test run_tests with timeout."""
        mock_run.side_effect = Exception("timeout")
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_run_tests_called_process_error(self, mock_run):
        """Test run_tests with CalledProcessError."""
        mock_run.side_effect = Exception("CalledProcessError")
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_run_tests_general_exception(self, mock_run):
        """Test run_tests with general exception."""
        mock_run.side_effect = Exception("General error")
        
        result = run_tests(["test_module.py"])
        
        assert result["success"] is False
        assert "error" in result


class TestDiscoverTestFiles:
    """Test discover_test_files function."""

    def test_discover_test_files_success(self):
        """Test discover_test_files with success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ["test_module1.py", "test_module2.py", "not_test.py"]
            for file in test_files:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write("# Test file")
            
            result = discover_test_files(temp_dir)
            
            assert result["success"] is True
            assert "test_module1.py" in result["test_files"]
            assert "test_module2.py" in result["test_files"]
            assert "not_test.py" not in result["test_files"]

    def test_discover_test_files_no_tests(self):
        """Test discover_test_files with no test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-test files
            non_test_files = ["module.py", "script.py", "data.json"]
            for file in non_test_files:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write("# Not a test file")
            
            result = discover_test_files(temp_dir)
            
            assert result["success"] is True
            assert result["test_files"] == []

    def test_discover_test_files_nonexistent_directory(self):
        """Test discover_test_files with nonexistent directory."""
        result = discover_test_files("nonexistent_directory")
        
        assert result["success"] is False
        assert "error" in result


class TestExecuteTestSuite:
    """Test execute_test_suite function."""

    @patch('src.ai_guard.tests_runner.run_tests')
    def test_execute_test_suite(self, mock_run_tests):
        """Test execute_test_suite."""
        mock_run_tests.return_value = {"success": True, "passed": 5, "failed": 0}
        
        result = execute_test_suite(["test1.py", "test2.py"])
        
        assert result["success"] is True
        assert result["passed"] == 5
        assert result["failed"] == 0
        mock_run_tests.assert_called_once_with(["test1.py", "test2.py"])


class TestTestRunner:
    """Test TestRunner class."""

    def test_test_runner_init(self):
        """Test TestRunner initialization."""
        runner = TestRunner()
        assert runner.runner_name == "Test Runner"
        assert runner.test_command == "pytest"
        assert runner.test_pattern == "test_*.py"

    @patch('subprocess.run')
    def test_test_runner_run_test_file(self, mock_run):
        """Test TestRunner run_test_file method."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_file.py::test_function PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        runner = TestRunner()
        result = runner.run_test_file("test_file.py")
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0

    @patch('src.ai_guard.tests_runner.discover_test_files')
    def test_test_runner_run_test_directory_success(self, mock_discover):
        """Test TestRunner run_test_directory with success."""
        mock_discover.return_value = {
            "success": True,
            "test_files": ["test1.py", "test2.py"]
        }
        
        runner = TestRunner()
        
        with patch.object(runner, 'run_test_file') as mock_run_file:
            mock_run_file.return_value = {"success": True, "passed": 2, "failed": 0}
            
            result = runner.run_test_directory("test_dir")
            
            assert result["success"] is True
            assert result["files_run"] == 2
            assert result["total_passed"] == 4
            assert result["total_failed"] == 0

    @patch('src.ai_guard.tests_runner.discover_test_files')
    def test_test_runner_run_test_directory_discovery_failure(self, mock_discover):
        """Test TestRunner run_test_directory with discovery failure."""
        mock_discover.return_value = {"success": False, "error": "Discovery failed"}
        
        runner = TestRunner()
        result = runner.run_test_directory("test_dir")
        
        assert result["success"] is False
        assert "error" in result

    @patch('src.ai_guard.tests_runner.discover_test_files')
    def test_test_runner_run_test_directory_no_tests(self, mock_discover):
        """Test TestRunner run_test_directory with no tests."""
        mock_discover.return_value = {"success": True, "test_files": []}
        
        runner = TestRunner()
        result = runner.run_test_directory("test_dir")
        
        assert result["success"] is True
        assert result["files_run"] == 0
        assert result["total_passed"] == 0
        assert result["total_failed"] == 0

    def test_test_runner_discover_test_files(self):
        """Test TestRunner discover_test_files method."""
        runner = TestRunner()
        
        with patch('src.ai_guard.tests_runner.discover_test_files') as mock_discover:
            mock_discover.return_value = {"success": True, "test_files": ["test.py"]}
            
            result = runner.discover_test_files("test_dir")
            
            assert result["success"] is True
            assert result["test_files"] == ["test.py"]
            mock_discover.assert_called_once_with("test_dir")

    @patch('subprocess.run')
    def test_test_runner_execute_test_command_success(self, mock_run):
        """Test TestRunner _execute_test_command with success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_file.py::test_function PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        runner = TestRunner()
        result = runner._execute_test_command(["test_file.py"])
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0

    @patch('subprocess.run')
    def test_test_runner_execute_test_command_failure(self, mock_run):
        """Test TestRunner _execute_test_command with failure."""
        mock_run.side_effect = Exception("Command failed")
        
        runner = TestRunner()
        result = runner._execute_test_command(["test_file.py"])
        
        assert result["success"] is False
        assert "error" in result


class TestTestDiscoverer:
    """Test TestDiscoverer class."""

    def test_test_discoverer_init(self):
        """Test TestDiscoverer initialization."""
        discoverer = TestDiscoverer()
        assert discoverer.discoverer_name == "Test Discoverer"
        assert discoverer.test_patterns == ["test_*.py", "*_test.py"]

    def test_test_discoverer_discover_test_files_non_recursive(self):
        """Test TestDiscoverer discover_test_files non-recursive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ["test_module1.py", "test_module2.py", "not_test.py"]
            for file in test_files:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write("# Test file")
            
            discoverer = TestDiscoverer()
            result = discoverer.discover_test_files(temp_dir, recursive=False)
            
            assert result["success"] is True
            assert "test_module1.py" in result["test_files"]
            assert "test_module2.py" in result["test_files"]
            assert "not_test.py" not in result["test_files"]

    def test_test_discoverer_discover_test_files_recursive(self):
        """Test TestDiscoverer discover_test_files recursive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            sub_dir = os.path.join(temp_dir, "subdir")
            os.makedirs(sub_dir)
            
            # Create test files in both directories
            test_files_main = ["test_main.py"]
            test_files_sub = ["test_sub.py"]
            
            for file in test_files_main:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write("# Test file")
            
            for file in test_files_sub:
                with open(os.path.join(sub_dir, file), 'w') as f:
                    f.write("# Test file")
            
            discoverer = TestDiscoverer()
            result = discoverer.discover_test_files(temp_dir, recursive=True)
            
            assert result["success"] is True
            assert "test_main.py" in result["test_files"]
            assert "test_sub.py" in result["test_files"]

    def test_test_discoverer_discover_test_files_exception(self):
        """Test TestDiscoverer discover_test_files with exception."""
        discoverer = TestDiscoverer()
        result = discoverer.discover_test_files("nonexistent_directory")
        
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
        assert executor.timeout == 600

    @patch('subprocess.run')
    def test_test_executor_execute_tests_success(self, mock_run):
        """Test TestExecutor execute_tests with success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_file.py::test_function PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1

    @patch('subprocess.run')
    def test_test_executor_execute_tests_timeout(self, mock_run):
        """Test TestExecutor execute_tests with timeout."""
        mock_run.side_effect = Exception("timeout")
        
        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_test_executor_execute_tests_called_process_error(self, mock_run):
        """Test TestExecutor execute_tests with CalledProcessError."""
        mock_run.side_effect = Exception("CalledProcessError")
        
        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_test_executor_execute_tests_general_exception(self, mock_run):
        """Test TestExecutor execute_tests with general exception."""
        mock_run.side_effect = Exception("General error")
        
        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_test_executor_run_pytest(self, mock_run):
        """Test TestExecutor _run_pytest method."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_file.py::test_function PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        executor = TestExecutor()
        result = executor._run_pytest(["test_file.py"])
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
