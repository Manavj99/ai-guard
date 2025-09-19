"""Comprehensive tests for tests runner module."""

import pytest
import subprocess
import sys
from unittest.mock import Mock, patch, call

from src.ai_guard.tests_runner import (
    run_pytest,
    run_pytest_with_coverage,
    TestsRunner,
)


class TestRunPytest:
    """Test run_pytest function."""

    def test_run_pytest_basic(self):
        """Test basic run_pytest execution."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            result = run_pytest()
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q"]
            mock_call.assert_called_once_with(expected_cmd)
            assert result == 0

    def test_run_pytest_with_extra_args(self):
        """Test run_pytest with extra arguments."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 1
            
            extra_args = ["-v", "--tb=short", "tests/test_specific.py"]
            result = run_pytest(extra_args)
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q", "-v", "--tb=short", "tests/test_specific.py"]
            mock_call.assert_called_once_with(expected_cmd)
            assert result == 1

    def test_run_pytest_with_empty_args(self):
        """Test run_pytest with empty extra arguments."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            result = run_pytest([])
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q"]
            mock_call.assert_called_once_with(expected_cmd)
            assert result == 0

    def test_run_pytest_with_none_args(self):
        """Test run_pytest with None extra arguments."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            result = run_pytest(None)
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q"]
            mock_call.assert_called_once_with(expected_cmd)
            assert result == 0

    def test_run_pytest_subprocess_error(self):
        """Test run_pytest with subprocess error."""
        with patch('subprocess.call', side_effect=subprocess.CalledProcessError(1, "pytest")):
            result = run_pytest()
            assert result == 1

    def test_run_pytest_file_not_found(self):
        """Test run_pytest with file not found error."""
        with patch('subprocess.call', side_effect=FileNotFoundError):
            result = run_pytest()
            assert result == 1

    def test_run_pytest_permission_error(self):
        """Test run_pytest with permission error."""
        with patch('subprocess.call', side_effect=PermissionError("Permission denied")):
            result = run_pytest()
            assert result == 1

    def test_run_pytest_with_specific_test_file(self):
        """Test run_pytest with specific test file."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            extra_args = ["tests/test_specific.py"]
            result = run_pytest(extra_args)
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q", "tests/test_specific.py"]
            mock_call.assert_called_once_with(expected_cmd)
            assert result == 0

    def test_run_pytest_with_multiple_args(self):
        """Test run_pytest with multiple arguments."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            extra_args = ["-v", "--tb=short", "--maxfail=5", "tests/"]
            result = run_pytest(extra_args)
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q", "-v", "--tb=short", "--maxfail=5", "tests/"]
            mock_call.assert_called_once_with(expected_cmd)
            assert result == 0


class TestRunPytestWithCoverage:
    """Test run_pytest_with_coverage function."""

    def test_run_pytest_with_coverage_basic(self):
        """Test basic run_pytest_with_coverage execution."""
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 0
            
            result = run_pytest_with_coverage()
            
            mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
            assert result == 0

    def test_run_pytest_with_coverage_failure(self):
        """Test run_pytest_with_coverage with failure."""
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 1
            
            result = run_pytest_with_coverage()
            
            mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])
            assert result == 1

    def test_run_pytest_with_coverage_subprocess_error(self):
        """Test run_pytest_with_coverage with subprocess error."""
        with patch('src.ai_guard.tests_runner.run_pytest', side_effect=Exception("Subprocess error")):
            with pytest.raises(Exception, match="Subprocess error"):
                run_pytest_with_coverage()


class TestTestsRunner:
    """Test TestsRunner class."""

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None

    def test_run_pytest_method(self):
        """Test TestsRunner.run_pytest method."""
        runner = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 0
            
            result = runner.run_pytest()
            
            mock_run_pytest.assert_called_once_with(None)
            assert result == 0

    def test_run_pytest_method_with_args(self):
        """Test TestsRunner.run_pytest method with arguments."""
        runner = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 1
            
            extra_args = ["-v", "--tb=short"]
            result = runner.run_pytest(extra_args)
            
            mock_run_pytest.assert_called_once_with(extra_args)
            assert result == 1

    def test_run_pytest_with_coverage_method(self):
        """Test TestsRunner.run_pytest_with_coverage method."""
        runner = TestsRunner()
        
        with patch('src.ai_guard.tests_runner.run_pytest_with_coverage') as mock_run_pytest_with_coverage:
            mock_run_pytest_with_coverage.return_value = 0
            
            result = runner.run_pytest_with_coverage()
            
            mock_run_pytest_with_coverage.assert_called_once()
            assert result == 0

    def test_run_tests_with_coverage(self):
        """Test TestsRunner.run_tests with coverage."""
        runner = TestsRunner()
        
        with patch.object(runner, 'run_pytest_with_coverage', return_value=0) as mock_run_pytest_with_coverage:
            result = runner.run_tests(with_coverage=True)
            
            mock_run_pytest_with_coverage.assert_called_once()
            assert result == 0

    def test_run_tests_without_coverage(self):
        """Test TestsRunner.run_tests without coverage."""
        runner = TestsRunner()
        
        with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
            result = runner.run_tests(with_coverage=False)
            
            mock_run_pytest.assert_called_once()
            assert result == 0

    def test_run_tests_default_coverage(self):
        """Test TestsRunner.run_tests with default coverage setting."""
        runner = TestsRunner()
        
        with patch.object(runner, 'run_pytest_with_coverage', return_value=0) as mock_run_pytest_with_coverage:
            result = runner.run_tests()  # Default should be with_coverage=True
            
            mock_run_pytest_with_coverage.assert_called_once()
            assert result == 0

    def test_tests_runner_integration(self):
        """Test TestsRunner integration with real subprocess calls."""
        runner = TestsRunner()
        
        # Test that the runner can be instantiated and methods exist
        assert hasattr(runner, 'run_pytest')
        assert hasattr(runner, 'run_pytest_with_coverage')
        assert hasattr(runner, 'run_tests')
        
        # Test method signatures
        assert callable(runner.run_pytest)
        assert callable(runner.run_pytest_with_coverage)
        assert callable(runner.run_tests)

    def test_tests_runner_error_handling(self):
        """Test TestsRunner error handling."""
        runner = TestsRunner()
        
        # Test with subprocess errors
        with patch('src.ai_guard.tests_runner.run_pytest', side_effect=Exception("Pytest error")):
            with pytest.raises(Exception):
                runner.run_pytest()
        
        with patch('src.ai_guard.tests_runner.run_pytest_with_coverage', side_effect=Exception("Coverage error")):
            with pytest.raises(Exception):
                runner.run_pytest_with_coverage()

    def test_tests_runner_performance(self):
        """Test TestsRunner performance with multiple calls."""
        runner = TestsRunner()
        
        with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
            # Run multiple times to test performance
            for _ in range(10):
                result = runner.run_pytest()
                assert result == 0
            
            assert mock_run_pytest.call_count == 10

    def test_tests_runner_with_different_exit_codes(self):
        """Test TestsRunner with different exit codes."""
        runner = TestsRunner()
        
        test_cases = [0, 1, 2, 3, 4, 5]
        
        for expected_code in test_cases:
            with patch.object(runner, 'run_pytest', return_value=expected_code):
                result = runner.run_pytest()
                assert result == expected_code

    def test_tests_runner_method_chaining(self):
        """Test TestsRunner method chaining."""
        runner = TestsRunner()
        
        with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
            with patch.object(runner, 'run_pytest_with_coverage', return_value=0) as mock_run_pytest_with_coverage:
                # Test that methods can be called in sequence
                pytest_result = runner.run_pytest()
                coverage_result = runner.run_pytest_with_coverage()
                tests_result = runner.run_tests()
                
                assert pytest_result == 0
                assert coverage_result == 0
                assert tests_result == 0
                
                assert mock_run_pytest.call_count == 2  # Called once directly, once in run_tests
                assert mock_run_pytest_with_coverage.call_count == 2  # Called once directly, once in run_tests

    def test_tests_runner_with_none_args(self):
        """Test TestsRunner with None arguments."""
        runner = TestsRunner()
        
        with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
            result = runner.run_pytest(None)
            
            mock_run_pytest.assert_called_once_with(None)
            assert result == 0

    def test_tests_runner_edge_cases(self):
        """Test TestsRunner edge cases."""
        runner = TestsRunner()
        
        # Test with empty args
        with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
            result = runner.run_pytest([])
            
            mock_run_pytest.assert_called_once_with([])
            assert result == 0

    def test_tests_runner_coverage_parameter_variations(self):
        """Test TestsRunner with different coverage parameter values."""
        runner = TestsRunner()
        
        # Test with explicit True
        with patch.object(runner, 'run_pytest_with_coverage', return_value=0) as mock_run_pytest_with_coverage:
            result = runner.run_tests(with_coverage=True)
            mock_run_pytest_with_coverage.assert_called_once()
            assert result == 0
        
        # Test with explicit False
        with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
            result = runner.run_tests(with_coverage=False)
            mock_run_pytest.assert_called_once()
            assert result == 0

    def test_tests_runner_with_specific_test_patterns(self):
        """Test TestsRunner with specific test patterns."""
        runner = TestsRunner()
        
        test_patterns = [
            ["tests/test_specific.py"],
            ["tests/test_*.py"],
            ["-k", "test_specific_function"],
            ["--maxfail=1"],
            ["-v", "--tb=short"],
        ]
        
        for pattern in test_patterns:
            with patch.object(runner, 'run_pytest', return_value=0) as mock_run_pytest:
                result = runner.run_pytest(pattern)
                
                mock_run_pytest.assert_called_once_with(pattern)
                assert result == 0

    def test_tests_runner_with_coverage_options(self):
        """Test TestsRunner with different coverage options."""
        runner = TestsRunner()
        
        # Test that run_pytest_with_coverage uses the correct coverage arguments
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 0
            
            runner.run_pytest_with_coverage()
            
            mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])

    def test_tests_runner_subprocess_integration(self):
        """Test TestsRunner subprocess integration."""
        runner = TestsRunner()
        
        # Test that the runner properly delegates to subprocess functions
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            
            runner.run_pytest()
            
            expected_cmd = [sys.executable, "-m", "pytest", "-q"]
            mock_call.assert_called_once_with(expected_cmd)

    def test_tests_runner_error_propagation(self):
        """Test TestsRunner error propagation."""
        runner = TestsRunner()
        
        # Test that errors from subprocess are properly propagated
        with patch('subprocess.call', side_effect=subprocess.CalledProcessError(1, "pytest")):
            result = runner.run_pytest()
            assert result == 1
        
        with patch('subprocess.call', side_effect=FileNotFoundError):
            result = runner.run_pytest()
            assert result == 1