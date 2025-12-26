"""Comprehensive tests for analyzer_optimized.py module."""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ai_guard.analyzer_optimized import (
    OptimizedCodeAnalyzer,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    _run_quality_checks_parallel,
    get_cache,
    main,
    run,
)


class TestOptimizedCodeAnalyzer:
    """Test the OptimizedCodeAnalyzer class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        analyzer = OptimizedCodeAnalyzer()
        assert analyzer.config is not None
        assert isinstance(analyzer.config, dict)

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        custom_config = {"min_coverage": 90, "parallel": True}
        analyzer = OptimizedCodeAnalyzer(custom_config)
        assert analyzer.config == custom_config

    @patch("src.ai_guard.analyzer_optimized._run_quality_checks_parallel")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    def test_run_all_checks_parallel(self, mock_coverage, mock_parallel):
        """Test running all checks in parallel mode."""
        mock_parallel.return_value = ([], [])
        mock_coverage.return_value = Mock()

        analyzer = OptimizedCodeAnalyzer()
        paths = ["src/test.py"]

        results = analyzer.run_all_checks(paths=paths, parallel=True)

        assert len(results) >= 1
        mock_parallel.assert_called_once_with(paths)
        mock_coverage.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    def test_run_all_checks_sequential(
        self, mock_coverage, mock_security, mock_type, mock_lint
    ):
        """Test running all checks in sequential mode."""
        mock_lint.return_value = (Mock(), [])
        mock_type.return_value = (Mock(), [])
        mock_security.return_value = (Mock(), [])
        mock_coverage.return_value = Mock()

        analyzer = OptimizedCodeAnalyzer()
        paths = ["src/test.py"]

        results = analyzer.run_all_checks(paths=paths, parallel=False)

        assert len(results) == 4
        mock_lint.assert_called_once_with(paths)
        mock_type.assert_called_once_with(paths)
        mock_security.assert_called_once()
        mock_coverage.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.get_performance_summary")
    def test_get_performance_metrics(self, mock_summary):
        """Test getting performance metrics."""
        mock_summary.return_value = {"total_time": 1.5, "cache_hits": 10}

        analyzer = OptimizedCodeAnalyzer()
        metrics = analyzer.get_performance_metrics()

        assert metrics == {"total_time": 1.5, "cache_hits": 10}
        mock_summary.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.get_cache")
    def test_clear_cache(self, mock_get_cache):
        """Test clearing the cache."""
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache

        analyzer = OptimizedCodeAnalyzer()
        analyzer.clear_cache()

        mock_cache.clear.assert_called_once()


class TestQualityChecks:
    """Test individual quality check functions."""

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_run.return_value = Mock(returncode=0, stdout="No issues found")

        result, errors = run_lint_check(["src/test.py"])

        assert result is not None
        assert errors == []
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_lint_check_failure(self, mock_run):
        """Test lint check with failures."""
        mock_run.return_value = Mock(returncode=1, stdout="E501 line too long")

        result, errors = run_lint_check(["src/test.py"])

        assert result is not None
        assert len(errors) > 0
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_run.return_value = Mock(returncode=0, stdout="Success")

        result, errors = run_type_check(["src/test.py"])

        assert result is not None
        assert errors == []
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_type_check_failure(self, mock_run):
        """Test type check with failures."""
        mock_run.return_value = Mock(
            returncode=1, stdout="error: Name 'x' is not defined"
        )

        result, errors = run_type_check(["src/test.py"])

        assert result is not None
        assert len(errors) > 0
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_run.return_value = Mock(returncode=0, stdout="No security issues")

        result, errors = run_security_check()

        assert result is not None
        assert errors == []
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_security_check_failure(self, mock_run):
        """Test security check with issues."""
        mock_run.return_value = Mock(
            returncode=1, stdout="B101: Use of assert detected"
        )

        result, errors = run_security_check()

        assert result is not None
        assert len(errors) > 0
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_coverage_check_success(self, mock_run):
        """Test successful coverage check."""
        mock_run.return_value = Mock(returncode=0, stdout="Coverage: 85%")

        result = run_coverage_check(80)

        assert result is not None
        mock_run.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_coverage_check_failure(self, mock_run):
        """Test coverage check below threshold."""
        mock_run.return_value = Mock(returncode=1, stdout="Coverage: 75%")

        result = run_coverage_check(80)

        assert result is not None
        mock_run.assert_called_once()


class TestParallelExecution:
    """Test parallel execution functionality."""

    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    def test_run_quality_checks_parallel(self, mock_security, mock_type, mock_lint):
        """Test parallel execution of quality checks."""
        mock_lint.return_value = (Mock(), [])
        mock_type.return_value = (Mock(), [])
        mock_security.return_value = (Mock(), [])

        paths = ["src/test1.py", "src/test2.py"]
        results, errors = _run_quality_checks_parallel(paths)

        assert len(results) == 3
        assert len(errors) == 0
        mock_lint.assert_called_once_with(paths)
        mock_type.assert_called_once_with(paths)
        mock_security.assert_called_once()


class TestCacheFunctionality:
    """Test cache functionality."""

    def test_get_cache(self):
        """Test getting cache instance."""
        cache = get_cache()
        assert cache is not None


class TestMainFunction:
    """Test main function and entry point."""

    @patch("src.ai_guard.analyzer_optimized.run")
    def test_main_function(self, mock_run):
        """Test main function."""
        mock_run.return_value = 0

        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)

    @patch("src.ai_guard.analyzer_optimized.OptimizedCodeAnalyzer")
    def test_run_function(self, mock_analyzer_class):
        """Test run function."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.run_all_checks.return_value = []

        result = run()

        assert result == 0
        mock_analyzer.run_all_checks.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_run_lint_check_no_paths(self):
        """Test lint check with no paths."""
        result, errors = run_lint_check([])
        assert result is not None
        assert errors == []

    def test_run_type_check_no_paths(self):
        """Test type check with no paths."""
        result, errors = run_type_check([])
        assert result is not None
        assert errors == []

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_lint_check_exception(self, mock_run):
        """Test lint check with subprocess exception."""
        mock_run.side_effect = Exception("Subprocess error")

        result, errors = run_lint_check(["src/test.py"])

        assert result is not None
        assert len(errors) > 0

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_type_check_exception(self, mock_run):
        """Test type check with subprocess exception."""
        mock_run.side_effect = Exception("Subprocess error")

        result, errors = run_type_check(["src/test.py"])

        assert result is not None
        assert len(errors) > 0

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_security_check_exception(self, mock_run):
        """Test security check with subprocess exception."""
        mock_run.side_effect = Exception("Subprocess error")

        result, errors = run_security_check()

        assert result is not None
        assert len(errors) > 0

    @patch("src.ai_guard.analyzer_optimized.subprocess.run")
    def test_run_coverage_check_exception(self, mock_run):
        """Test coverage check with subprocess exception."""
        mock_run.side_effect = Exception("Subprocess error")

        result = run_coverage_check(80)

        assert result is not None


class TestConfigurationHandling:
    """Test configuration handling."""

    def test_analyzer_with_min_coverage_config(self):
        """Test analyzer with min_coverage configuration."""
        config = {"min_coverage": 95}
        analyzer = OptimizedCodeAnalyzer(config)

        assert analyzer.config["min_coverage"] == 95

    def test_analyzer_with_parallel_config(self):
        """Test analyzer with parallel configuration."""
        config = {"parallel": False}
        analyzer = OptimizedCodeAnalyzer(config)

        assert analyzer.config["parallel"] is False

    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    def test_run_all_checks_uses_config_min_coverage(self, mock_coverage):
        """Test that run_all_checks uses config min_coverage."""
        mock_coverage.return_value = Mock()

        config = {"min_coverage": 90}
        analyzer = OptimizedCodeAnalyzer(config)

        analyzer.run_all_checks(parallel=False)

        mock_coverage.assert_called_once_with(90)


class TestPerformanceIntegration:
    """Test performance integration."""

    @patch("src.ai_guard.analyzer_optimized.time_function")
    def test_run_all_checks_timed(self, mock_time_function):
        """Test that run_all_checks is timed."""
        mock_time_function.side_effect = lambda func: func

        analyzer = OptimizedCodeAnalyzer()
        analyzer.run_all_checks(parallel=False)

        mock_time_function.assert_called_once()

    def test_performance_metrics_structure(self):
        """Test performance metrics structure."""
        analyzer = OptimizedCodeAnalyzer()

        with patch(
            "src.ai_guard.analyzer_optimized.get_performance_summary"
        ) as mock_summary:
            mock_summary.return_value = {
                "total_time": 1.5,
                "cache_hits": 10,
                "cache_misses": 2,
                "memory_usage": "50MB",
            }

            metrics = analyzer.get_performance_metrics()

            assert "total_time" in metrics
            assert "cache_hits" in metrics
            assert "cache_misses" in metrics
            assert "memory_usage" in metrics


if __name__ == "__main__":
    pytest.main([__file__])
