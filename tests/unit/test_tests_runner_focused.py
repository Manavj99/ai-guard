"""Focused tests for the tests_runner module."""

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys

from src.ai_guard.tests_runner import (
    run_pytest, 
    run_pytest_with_coverage, 
    TestsRunner
)


class TestRunPytest(unittest.TestCase):
    """Test the run_pytest function."""

    @patch('subprocess.call')
    def test_run_pytest_no_extra_args(self, mock_call):
        """Test run_pytest without extra arguments."""
        mock_call.return_value = 0
        
        result = run_pytest()
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 0)

    @patch('subprocess.call')
    def test_run_pytest_with_extra_args(self, mock_call):
        """Test run_pytest with extra arguments."""
        mock_call.return_value = 1
        extra_args = ["-v", "--tb=short", "tests/unit/"]
        
        result = run_pytest(extra_args)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "-v", "--tb=short", "tests/unit/"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 1)

    @patch('subprocess.call')
    def test_run_pytest_with_single_extra_arg(self, mock_call):
        """Test run_pytest with single extra argument."""
        mock_call.return_value = 2
        extra_args = ["--maxfail=1"]
        
        result = run_pytest(extra_args)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q", "--maxfail=1"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 2)

    @patch('subprocess.call')
    def test_run_pytest_with_none_extra_args(self, mock_call):
        """Test run_pytest with None extra_args."""
        mock_call.return_value = 0
        
        result = run_pytest(None)
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 0)

    @patch('subprocess.call')
    def test_run_pytest_failure(self, mock_call):
        """Test run_pytest with failure."""
        mock_call.return_value = 3
        
        result = run_pytest()
        
        expected_cmd = [sys.executable, "-m", "pytest", "-q"]
        mock_call.assert_called_once_with(expected_cmd)
        self.assertEqual(result, 3)


class TestRunPytestWithCoverage(unittest.TestCase):
    """Test the run_pytest_with_coverage function."""

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_with_coverage(self, mock_run_pytest):
        """Test run_pytest_with_coverage function."""
        mock_run_pytest.return_value = 0
        
        result = run_pytest_with_coverage()
        
        mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
        self.assertEqual(result, 0)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_with_coverage_failure(self, mock_run_pytest):
        """Test run_pytest_with_coverage function with failure."""
        mock_run_pytest.return_value = 1
        
        result = run_pytest_with_coverage()
        
        mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
        self.assertEqual(result, 1)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_with_coverage_tests_fail(self, mock_run_pytest):
        """Test run_pytest_with_coverage function when tests fail."""
        mock_run_pytest.return_value = 2
        
        result = run_pytest_with_coverage()
        
        mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
        self.assertEqual(result, 2)


class TestTestsRunner(unittest.TestCase):
    """Test the TestsRunner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = TestsRunner()

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        self.assertIsNotNone(runner)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_method(self, mock_run_pytest):
        """Test TestsRunner.run_pytest method."""
        mock_run_pytest.return_value = 0
        extra_args = ["-v", "--tb=short"]
        
        result = self.runner.run_pytest(extra_args)
        
        mock_run_pytest.assert_called_once_with(extra_args)
        self.assertEqual(result, 0)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_method_no_args(self, mock_run_pytest):
        """Test TestsRunner.run_pytest method without extra args."""
        mock_run_pytest.return_value = 1
        
        result = self.runner.run_pytest()
        
        mock_run_pytest.assert_called_once_with(None)
        self.assertEqual(result, 1)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_method_failure(self, mock_run_pytest):
        """Test TestsRunner.run_pytest method with failure."""
        mock_run_pytest.return_value = 2
        extra_args = ["--maxfail=1"]
        
        result = self.runner.run_pytest(extra_args)
        
        mock_run_pytest.assert_called_once_with(extra_args)
        self.assertEqual(result, 2)

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_pytest_with_coverage_method(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_pytest_with_coverage method."""
        mock_run_pytest_with_coverage.return_value = 0
        
        result = self.runner.run_pytest_with_coverage()
        
        mock_run_pytest_with_coverage.assert_called_once()
        self.assertEqual(result, 0)

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_pytest_with_coverage_method_failure(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_pytest_with_coverage method with failure."""
        mock_run_pytest_with_coverage.return_value = 1
        
        result = self.runner.run_pytest_with_coverage()
        
        mock_run_pytest_with_coverage.assert_called_once()
        self.assertEqual(result, 1)

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_tests_with_coverage_true(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests with coverage enabled."""
        mock_run_pytest_with_coverage.return_value = 0
        
        result = self.runner.run_tests(with_coverage=True)
        
        mock_run_pytest_with_coverage.assert_called_once()
        self.assertEqual(result, 0)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_tests_with_coverage_false(self, mock_run_pytest):
        """Test TestsRunner.run_tests with coverage disabled."""
        mock_run_pytest.return_value = 1
        
        result = self.runner.run_tests(with_coverage=False)
        
        mock_run_pytest.assert_called_once_with(None)
        self.assertEqual(result, 1)

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_tests_default_coverage(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests with default coverage setting."""
        mock_run_pytest_with_coverage.return_value = 0
        
        result = self.runner.run_tests()
        
        mock_run_pytest_with_coverage.assert_called_once()
        self.assertEqual(result, 0)

    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_tests_explicit_coverage_false(self, mock_run_pytest):
        """Test TestsRunner.run_tests with explicit coverage=False."""
        mock_run_pytest.return_value = 2
        
        result = self.runner.run_tests(with_coverage=False)
        
        mock_run_pytest.assert_called_once_with(None)
        self.assertEqual(result, 2)

    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_tests_coverage_failure(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests with coverage when tests fail."""
        mock_run_pytest_with_coverage.return_value = 3
        
        result = self.runner.run_tests(with_coverage=True)
        
        mock_run_pytest_with_coverage.assert_called_once()
        self.assertEqual(result, 3)


if __name__ == "__main__":
    unittest.main()
