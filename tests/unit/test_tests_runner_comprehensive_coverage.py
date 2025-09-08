"""
Comprehensive test coverage for src/ai_guard/tests_runner.py
"""
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys

# Import the tests_runner module
from src.ai_guard.tests_runner import (
    run_pytest,
    run_pytest_with_coverage,
    TestsRunner
)


class TestRunPytest(unittest.TestCase):
    """Test run_pytest function."""
    
    @patch('subprocess.call')
    def test_run_pytest_no_extra_args(self, mock_call):
        """Test run_pytest with no extra arguments."""
        mock_call.return_value = 0
        
        result = run_pytest()
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check subprocess was called correctly
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        self.assertEqual(call_args[0], sys.executable)
        self.assertEqual(call_args[1], "-m")
        self.assertEqual(call_args[2], "pytest")
        self.assertEqual(call_args[3], "-q")
    
    @patch('subprocess.call')
    def test_run_pytest_with_extra_args(self, mock_call):
        """Test run_pytest with extra arguments."""
        mock_call.return_value = 0
        
        extra_args = ["-v", "--tb=short", "tests/"]
        result = run_pytest(extra_args)
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check subprocess was called with extra args
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        self.assertEqual(call_args[0], sys.executable)
        self.assertEqual(call_args[1], "-m")
        self.assertEqual(call_args[2], "pytest")
        self.assertEqual(call_args[3], "-q")
        self.assertEqual(call_args[4], "-v")
        self.assertEqual(call_args[5], "--tb=short")
        self.assertEqual(call_args[6], "tests/")
    
    @patch('subprocess.call')
    def test_run_pytest_with_failure(self, mock_call):
        """Test run_pytest with test failures."""
        mock_call.return_value = 1
        
        result = run_pytest()
        
        # Check result
        self.assertEqual(result, 1)
    
    @patch('subprocess.call')
    def test_run_pytest_with_exception(self, mock_call):
        """Test run_pytest when subprocess raises exception."""
        mock_call.side_effect = subprocess.CalledProcessError(1, "pytest")
        
        # The actual implementation doesn't catch the exception, it propagates it
        with self.assertRaises(subprocess.CalledProcessError):
            run_pytest()


class TestRunPytestWithCoverage(unittest.TestCase):
    """Test run_pytest_with_coverage function."""
    
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_with_coverage(self, mock_run_pytest):
        """Test run_pytest_with_coverage function."""
        mock_run_pytest.return_value = 0
        
        result = run_pytest_with_coverage()
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest was called with coverage args
        mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
    
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_with_coverage_failure(self, mock_run_pytest):
        """Test run_pytest_with_coverage with failures."""
        mock_run_pytest.return_value = 1
        
        result = run_pytest_with_coverage()
        
        # Check result
        self.assertEqual(result, 1)


class TestTestsRunner(unittest.TestCase):
    """Test TestsRunner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = TestsRunner()
    
    def test_tests_runner_initialization(self):
        """Test TestsRunner initialization."""
        self.assertIsInstance(self.runner, TestsRunner)
    
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_method(self, mock_run_pytest):
        """Test TestsRunner.run_pytest method."""
        mock_run_pytest.return_value = 0
        
        result = self.runner.run_pytest()
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest was called
        mock_run_pytest.assert_called_once_with(None)
    
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_pytest_method_with_args(self, mock_run_pytest):
        """Test TestsRunner.run_pytest method with extra args."""
        mock_run_pytest.return_value = 0
        
        extra_args = ["-v", "--tb=short"]
        result = self.runner.run_pytest(extra_args)
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest was called with args
        mock_run_pytest.assert_called_once_with(extra_args)
    
    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_pytest_with_coverage_method(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_pytest_with_coverage method."""
        mock_run_pytest_with_coverage.return_value = 0
        
        result = self.runner.run_pytest_with_coverage()
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest_with_coverage was called
        mock_run_pytest_with_coverage.assert_called_once()
    
    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_tests_with_coverage(self, mock_run_pytest, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests with coverage."""
        mock_run_pytest_with_coverage.return_value = 0
        
        result = self.runner.run_tests(with_coverage=True)
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest_with_coverage was called
        mock_run_pytest_with_coverage.assert_called_once()
        mock_run_pytest.assert_not_called()
    
    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_tests_without_coverage(self, mock_run_pytest, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests without coverage."""
        mock_run_pytest.return_value = 0
        
        result = self.runner.run_tests(with_coverage=False)
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest was called
        mock_run_pytest.assert_called_once_with(None)
        mock_run_pytest_with_coverage.assert_not_called()
    
    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_tests_default_coverage(self, mock_run_pytest, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests with default coverage setting."""
        mock_run_pytest_with_coverage.return_value = 0
        
        result = self.runner.run_tests()  # Default is with_coverage=True
        
        # Check result
        self.assertEqual(result, 0)
        
        # Check run_pytest_with_coverage was called (default behavior)
        mock_run_pytest_with_coverage.assert_called_once()
        mock_run_pytest.assert_not_called()
    
    @patch('src.ai_guard.tests_runner.run_pytest_with_coverage')
    def test_run_tests_with_coverage_failure(self, mock_run_pytest_with_coverage):
        """Test TestsRunner.run_tests with coverage when tests fail."""
        mock_run_pytest_with_coverage.return_value = 1
        
        result = self.runner.run_tests(with_coverage=True)
        
        # Check result
        self.assertEqual(result, 1)
    
    @patch('src.ai_guard.tests_runner.run_pytest')
    def test_run_tests_without_coverage_failure(self, mock_run_pytest):
        """Test TestsRunner.run_tests without coverage when tests fail."""
        mock_run_pytest.return_value = 1
        
        result = self.runner.run_tests(with_coverage=False)
        
        # Check result
        self.assertEqual(result, 1)


class TestTestsRunnerIntegration(unittest.TestCase):
    """Integration tests for TestsRunner."""
    
    def test_full_workflow_with_coverage(self):
        """Test complete workflow with coverage."""
        runner = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest_with_coverage') as mock_coverage:
            mock_coverage.return_value = 0
            
            result = runner.run_tests(with_coverage=True)
            
            self.assertEqual(result, 0)
            mock_coverage.assert_called_once()
    
    def test_full_workflow_without_coverage(self):
        """Test complete workflow without coverage."""
        runner = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_pytest:
            mock_pytest.return_value = 0
            
            result = runner.run_tests(with_coverage=False)
            
            self.assertEqual(result, 0)
            mock_pytest.assert_called_once_with(None)
    
    def test_multiple_instances(self):
        """Test that multiple TestsRunner instances work independently."""
        runner1 = TestsRunner()
        runner2 = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_pytest:
            mock_pytest.return_value = 0
            
            result1 = runner1.run_pytest()
            result2 = runner2.run_pytest()
            
            self.assertEqual(result1, 0)
            self.assertEqual(result2, 0)
            self.assertEqual(mock_pytest.call_count, 2)
    
    def test_error_handling(self):
        """Test error handling in TestsRunner."""
        runner = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_pytest:
            mock_pytest.side_effect = subprocess.CalledProcessError(1, "pytest")
            
            # The actual implementation doesn't catch the exception, it propagates it
            with self.assertRaises(subprocess.CalledProcessError):
                runner.run_pytest()


if __name__ == '__main__':
    unittest.main()