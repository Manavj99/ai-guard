"""Basic tests for tests_runner.py."""

from unittest.mock import patch
from ai_guard.tests_runner import TestsRunner, run_pytest_with_coverage


def test_tests_runner_init():
    """Test TestsRunner initialization."""
    runner = TestsRunner()
    assert runner is not None


def test_run_tests_basic():
    """Test basic test running."""
    runner = TestsRunner()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test passed"
        result = runner.run_tests("test_dir")
        assert result is not None


def test_run_tests_failure():
    """Test test running with failure."""
    runner = TestsRunner()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test failed"
        result = runner.run_tests("test_dir")
        assert result is not None


def test_run_pytest_with_coverage():
    """Test run_pytest_with_coverage function."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "coverage: 85%"

        exit_code, coverage = run_pytest_with_coverage("test_dir")
        assert exit_code == 0
        assert coverage >= 0
