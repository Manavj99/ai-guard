"""Tests for tests_runner module."""

import subprocess
import sys
from unittest.mock import patch, MagicMock, call
import pytest

from src.ai_guard.tests_runner import (
    run_pytest,
    run_pytest_with_coverage,
    TestsRunner,
)


class TestRunPytest:
    """Test run_pytest function."""

    @patch('subprocess.call')
    def test_run_pytest_basic(self, mock_call):
        """Test running pytest with no extra arguments."""
        mock_call.return_value = 0
        
        result = run_pytest()
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_extra_args(self, mock_call):
        """Test running pytest with extra arguments."""
        mock_call.return_value = 1
        extra_args = ["--verbose", "--tb=short"]
        
        result = run_pytest(extra_args)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--verbose", "--tb=short"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 1

    @patch('subprocess.call')
    def test_run_pytest_empty_extra_args(self, mock_call):
        """Test running pytest with empty extra arguments."""
        mock_call.return_value = 0
        
        result = run_pytest([])
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_none_extra_args(self, mock_call):
        """Test running pytest with None extra arguments."""
        mock_call.return_value = 0
        
        result = run_pytest(None)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0


class TestRunPytestWithCoverage:
    """Test run_pytest_with_coverage function."""

    @patch('subprocess.call')
    def test_run_pytest_with_coverage(self, mock_call):
        """Test running pytest with coverage reporting."""
        mock_call.return_value = 0
        
        result = run_pytest_with_coverage()
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--cov=src", "--cov-report=xml"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_coverage_failure(self, mock_call):
        """Test running pytest with coverage when it fails."""
        mock_call.return_value = 1
        
        result = run_pytest_with_coverage()
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--cov=src", "--cov-report=xml"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 1


class TestTestsRunner:
    """Test TestsRunner class."""

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_pytest(self, mock_run_pytest):
        """Test TestsRunner.run_pytest method."""
        mock_run_pytest.return_value = 0
        runner = TestsRunner()
        extra_args = ["--verbose"]
        
        result = runner.run_pytest(extra_args)
        
        mock_run_pytest.assert_called_once_with(extra_args)
        assert result == 0

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_pytest_no_args(self, mock_run_pytest):
        """Test TestsRunner.run_pytest with no arguments."""
        mock_run_pytest.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_pytest()
        
        mock_run_pytest.assert_called_once_with(None)
        assert result == 0

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_tests_runner_run_pytest_with_coverage(self, mock_run_coverage):
        """Test TestsRunner.run_pytest_with_coverage method."""
        mock_run_coverage.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_pytest_with_coverage()
        
        mock_run_coverage.assert_called_once()
        assert result == 0

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_tests_with_coverage(self, mock_run_pytest, mock_run_coverage):
        """Test TestsRunner.run_tests with coverage enabled."""
        mock_run_coverage.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_tests(with_coverage=True)
        
        mock_run_coverage.assert_called_once()
        mock_run_pytest.assert_not_called()
        assert result == 0

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_tests_without_coverage(self, mock_run_pytest, mock_run_coverage):
        """Test TestsRunner.run_tests with coverage disabled."""
        mock_run_pytest.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_tests(with_coverage=False)
        
        mock_run_pytest.assert_called_once_with(None)
        mock_run_coverage.assert_not_called()
        assert result == 0

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_tests_default_coverage(self, mock_run_pytest, mock_run_coverage):
        """Test TestsRunner.run_tests with default coverage setting."""
        mock_run_coverage.return_value = 0
        runner = TestsRunner()
        
        result = runner.run_tests()
        
        mock_run_coverage.assert_called_once()
        mock_run_pytest.assert_not_called()
        assert result == 0

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_tests_runner_run_tests_coverage_failure(self, mock_run_coverage):
        """Test TestsRunner.run_tests when coverage run fails."""
        mock_run_coverage.return_value = 1
        runner = TestsRunner()
        
        result = runner.run_tests(with_coverage=True)
        
        mock_run_coverage.assert_called_once()
        assert result == 1

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_run_tests_no_coverage_failure(self, mock_run_pytest):
        """Test TestsRunner.run_tests when pytest run fails."""
        mock_run_pytest.return_value = 1
        runner = TestsRunner()
        
        result = runner.run_tests(with_coverage=False)
        
        mock_run_pytest.assert_called_once_with(None)
        assert result == 1


class TestIntegration:
    """Integration tests for tests_runner module."""

    @patch('subprocess.call')
    def test_integration_run_pytest_flow(self, mock_call):
        """Test the complete flow of running pytest."""
        mock_call.return_value = 0
        
        # Test direct function call
        result1 = run_pytest(["--verbose"])
        assert result1 == 0
        
        # Test through class
        runner = TestsRunner()
        result2 = runner.run_pytest(["--verbose"])
        assert result2 == 0
        
        # Verify subprocess was called twice
        assert mock_call.call_count == 2
        
        # Check the calls
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--verbose"]
        assert mock_call.call_args_list[0] == call(expected_cmd)
        assert mock_call.call_args_list[1] == call(expected_cmd)

    @patch('subprocess.call')
    def test_integration_coverage_flow(self, mock_call):
        """Test the complete flow of running pytest with coverage."""
        mock_call.return_value = 0
        
        # Test direct function call
        result1 = run_pytest_with_coverage()
        assert result1 == 0
        
        # Test through class
        runner = TestsRunner()
        result2 = runner.run_pytest_with_coverage()
        assert result2 == 0
        
        # Verify subprocess was called twice
        assert mock_call.call_count == 2
        
        # Check the calls
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--cov=src", "--cov-report=xml"]
        assert mock_call.call_args_list[0] == call(expected_cmd)
        assert mock_call.call_args_list[1] == call(expected_cmd)

    @patch('subprocess.call')
    def test_integration_run_tests_flow(self, mock_call):
        """Test the complete flow of run_tests method."""
        mock_call.return_value = 0
        runner = TestsRunner()
        
        # Test with coverage
        result1 = runner.run_tests(with_coverage=True)
        assert result1 == 0
        
        # Test without coverage
        result2 = runner.run_tests(with_coverage=False)
        assert result2 == 0
        
        # Verify subprocess was called twice
        assert mock_call.call_count == 2
        
        # Check the calls
        coverage_cmd = [sys.executable, "-m", "pytest", "-q", "--cov=src", "--cov-report=xml"]
        basic_cmd = [sys.executable, "-m", "pytest", "-q"]
        
        assert mock_call.call_args_list[0] == call(coverage_cmd)
        assert mock_call.call_args_list[1] == call(basic_cmd)


class TestErrorHandling:
    """Test error handling in tests_runner module."""

    @patch('subprocess.call')
    def test_subprocess_exception_handling(self, mock_call):
        """Test handling of subprocess exceptions."""
        mock_call.side_effect = subprocess.CalledProcessError(1, "pytest")
        
        # This should raise the exception since we're not catching it
        with pytest.raises(subprocess.CalledProcessError):
            run_pytest()

    @patch('subprocess.call')
    def test_subprocess_file_not_found(self, mock_call):
        """Test handling of FileNotFoundError from subprocess."""
        mock_call.side_effect = FileNotFoundError("pytest not found")
        
        # This should raise the exception since we're not catching it
        with pytest.raises(FileNotFoundError):
            run_pytest()

    @patch('subprocess.call')
    def test_subprocess_other_exception(self, mock_call):
        """Test handling of other subprocess exceptions."""
        mock_call.side_effect = OSError("Permission denied")
        
        # This should raise the exception since we're not catching it
        with pytest.raises(OSError):
            run_pytest()


class TestEdgeCases:
    """Test edge cases in tests_runner module."""

    @patch('subprocess.call')
    def test_run_pytest_with_complex_args(self, mock_call):
        """Test running pytest with complex argument combinations."""
        mock_call.return_value = 0
        complex_args = [
            "--verbose",
            "--tb=short",
            "--maxfail=5",
            "--durations=10",
            "tests/",
            "-k", "test_something"
        ]
        
        result = run_pytest(complex_args)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"] + complex_args
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_empty_string_args(self, mock_call):
        """Test running pytest with empty string arguments."""
        mock_call.return_value = 0
        empty_args = ["", "--verbose", ""]
        
        result = run_pytest(empty_args)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "", "--verbose", ""]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    def test_tests_runner_multiple_instances(self):
        """Test creating multiple TestsRunner instances."""
        runner1 = TestsRunner()
        runner2 = TestsRunner()
        
        assert runner1 is not runner2
        assert isinstance(runner1, TestsRunner)
        assert isinstance(runner2, TestsRunner)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_tests_runner_method_chaining(self, mock_run_pytest):
        """Test calling multiple methods on TestsRunner."""
        mock_run_pytest.return_value = 0
        runner = TestsRunner()
        
        # Call multiple methods
        result1 = runner.run_pytest(["--verbose"])
        result2 = runner.run_pytest(["--quiet"])
        
        assert result1 == 0
        assert result2 == 0
        assert mock_run_pytest.call_count == 2
