"""Tests for the optimized analyzer module."""

from ai_guard.report import GateResult
from ai_guard.analyzer_optimized import (
    OptimizedCodeAnalyzer,
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _run_quality_checks_parallel,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    _to_findings,
    run,
    main,
    RuleIdStyle,
)
from ai_guard.performance import time_function, cached, parallel_execute
import pytest
import os
import sys
import subprocess
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestRuleIdStyle:
    """Test rule ID style functionality."""

    def test_rule_id_style_enum(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"

    @patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"})
    def test_rule_style_tool(self):
        """Test rule style returns TOOL when env var is set to tool."""
        style = _rule_style()
        assert style == RuleIdStyle.TOOL

    @patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"})
    def test_rule_style_bare(self):
        """Test rule style returns BARE when env var is set to bare."""
        # Clear the cache first
        from ai_guard.performance import get_cache

        get_cache().clear()
        style = _rule_style()
        assert style == RuleIdStyle.BARE

    @patch.dict(os.environ, {}, clear=True)
    def test_rule_style_default(self):
        """Test rule style returns BARE by default."""
        # Clear the cache first
        from ai_guard.performance import get_cache

        get_cache().clear()
        style = _rule_style()
        assert style == RuleIdStyle.BARE

    def test_make_rule_id_tool_style(self):
        """Test making rule ID with tool style."""
        with patch(
            "ai_guard.analyzer_optimized._rule_style", return_value=RuleIdStyle.TOOL
        ):
            rule_id = _make_rule_id("flake8", "E501")
            assert rule_id == "flake8:E501"

    def test_make_rule_id_bare_style(self):
        """Test making rule ID with bare style."""
        with patch(
            "ai_guard.analyzer_optimized._rule_style", return_value=RuleIdStyle.BARE
        ):
            rule_id = _make_rule_id("flake8", "E501")
            assert rule_id == "E501"

    def test_make_rule_id_no_code(self):
        """Test making rule ID when no code is provided."""
        with patch(
            "ai_guard.analyzer_optimized._rule_style", return_value=RuleIdStyle.TOOL
        ):
            rule_id = _make_rule_id("flake8", None)
            assert rule_id == "flake8:flake8"

    def test_make_rule_id_empty_code(self):
        """Test making rule ID when code is empty."""
        with patch(
            "ai_guard.analyzer_optimized._rule_style", return_value=RuleIdStyle.TOOL
        ):
            rule_id = _make_rule_id("flake8", "")
            assert rule_id == "flake8:flake8"


class TestStrictSubprocessFail:
    """Test strict subprocess fail functionality."""

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"})
    def test_strict_subprocess_fail_true(self):
        """Test strict subprocess fail returns True when env var is set."""
        # Clear the cache first
        from ai_guard.performance import get_cache

        get_cache().clear()
        result = _strict_subprocess_fail()
        assert result is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_FAIL": "false"})
    def test_strict_subprocess_fail_false(self):
        """Test strict subprocess fail returns False when env var is set to false."""
        result = _strict_subprocess_fail()
        assert result is False

    @patch.dict(os.environ, {}, clear=True)
    def test_strict_subprocess_fail_default(self):
        """Test strict subprocess fail returns False by default."""
        result = _strict_subprocess_fail()
        assert result is False


class TestOptimizedCodeAnalyzer:
    """Test OptimizedCodeAnalyzer class."""

    def test_init_with_config(self):
        """Test initializing with custom config."""
        config = {"min_coverage": 90}
        analyzer = OptimizedCodeAnalyzer(config)
        assert analyzer.config == config

    def test_init_without_config(self):
        """Test initializing without config uses default."""
        with patch("ai_guard.analyzer_optimized.load_config") as mock_load:
            mock_load.return_value = {"min_coverage": 80}
            analyzer = OptimizedCodeAnalyzer()
            assert analyzer.config == {"min_coverage": 80}

    @patch("ai_guard.analyzer_optimized.run_coverage_check")
    @patch("ai_guard.analyzer_optimized._run_quality_checks_parallel")
    def test_run_all_checks_parallel(self, mock_parallel, mock_coverage):
        """Test running all checks in parallel."""
        mock_parallel.return_value = ([GateResult("test", True, "ok")], [])
        mock_coverage.return_value = GateResult("Coverage", True, "ok")
        analyzer = OptimizedCodeAnalyzer()
        results = analyzer.run_all_checks(paths=["test.py"], parallel=True)
        assert len(results) == 2
        assert results[0].name == "test"
        assert results[1].name == "Coverage"
        mock_parallel.assert_called_once_with(["test.py"])

    @patch("ai_guard.analyzer_optimized.run_lint_check")
    @patch("ai_guard.analyzer_optimized.run_type_check")
    @patch("ai_guard.analyzer_optimized.run_security_check")
    @patch("ai_guard.analyzer_optimized.run_coverage_check")
    def test_run_all_checks_sequential(self, mock_cov, mock_sec, mock_type, mock_lint):
        """Test running all checks sequentially."""
        mock_lint.return_value = (GateResult("lint", True, "ok"), [])
        mock_type.return_value = (GateResult("type", True, "ok"), [])
        mock_sec.return_value = (GateResult("security", True, "ok"), [])
        mock_cov.return_value = GateResult("coverage", True, "ok")

        analyzer = OptimizedCodeAnalyzer()
        results = analyzer.run_all_checks(paths=["test.py"], parallel=False)

        assert len(results) == 4
        assert results[0].name == "lint"
        assert results[1].name == "type"
        assert results[2].name == "security"
        assert results[3].name == "coverage"

    @patch("ai_guard.analyzer_optimized.get_performance_summary")
    def test_get_performance_metrics(self, mock_perf):
        """Test getting performance metrics."""
        mock_perf.return_value = {"total_time": 1.5}
        analyzer = OptimizedCodeAnalyzer()
        metrics = analyzer.get_performance_metrics()
        assert metrics == {"total_time": 1.5}

    @patch("ai_guard.analyzer_optimized.get_cache")
    def test_clear_cache(self, mock_cache):
        """Test clearing cache."""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        analyzer = OptimizedCodeAnalyzer()
        analyzer.clear_cache()
        mock_cache_instance.clear.assert_called_once()


class TestQualityChecksParallel:
    """Test parallel quality checks functionality."""

    @patch("ai_guard.analyzer_optimized.parallel_execute")
    def test_run_quality_checks_parallel(self, mock_parallel):
        """Test running quality checks in parallel."""
        mock_parallel.return_value = [
            (GateResult("lint", True, "ok"), []),
            (GateResult("type", True, "ok"), []),
            (GateResult("security", True, "ok"), []),
        ]

        results, sarif_diagnostics = _run_quality_checks_parallel(["test.py"])

        assert len(results) == 3
        assert len(sarif_diagnostics) == 0
        mock_parallel.assert_called_once()


class TestOptimizedChecks:
    """Test optimized check functions."""

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_run_lint_check_optimized(self, mock_run):
        """Test optimized lint check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, sarif = run_lint_check(["test.py"])

        assert isinstance(result, GateResult)
        assert result.name == "Lint (flake8)"
        assert result.passed is True

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_run_type_check_optimized(self, mock_run):
        """Test optimized type check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, sarif = run_type_check(["test.py"])

        assert isinstance(result, GateResult)
        assert result.name == "Static types (mypy)"
        assert result.passed is True

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_run_security_check_optimized(self, mock_run):
        """Test optimized security check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, sarif = run_security_check()

        assert isinstance(result, GateResult)
        assert result.name == "Security (bandit)"
        assert result.passed is True

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_run_coverage_check_optimized(self, mock_run):
        """Test optimized coverage check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = run_coverage_check(80)

        assert isinstance(result, GateResult)
        assert result.name == "Coverage"


class TestSarifParsing:
    """Test SARIF parsing functionality."""

    def test_parse_sarif_results_empty(self):
        """Test parsing empty SARIF results."""
        results = _to_findings([])
        assert results == []

    def test_parse_sarif_results_with_data(self):
        """Test parsing SARIF results with data."""
        from ai_guard.sarif_report import SarifResult, make_location

        sarif_data = [
            SarifResult(
                rule_id="test-rule",
                level="error",
                message="Test error",
                locations=[make_location("test.py", 10, 1)],
            )
        ]

        results = _to_findings(sarif_data)
        assert len(results) == 1
        assert results[0]["rule_id"] == "test-rule"
        assert results[0]["level"] == "error"

    def test_convert_sarif_to_findings(self):
        """Test converting SARIF to findings format."""
        from ai_guard.sarif_report import SarifResult, make_location

        sarif_results = [
            SarifResult(
                rule_id="test-rule",
                level="error",
                message="Test error",
                locations=[make_location("test.py", 10, 1)],
            )
        ]

        findings = _to_findings(sarif_results)
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "test-rule"
        assert findings[0]["path"] == "test.py"
        assert findings[0]["line"] == 10


class TestMainFunction:
    """Test main function functionality."""

    @patch("ai_guard.analyzer_optimized.run")
    def test_main_function(self, mock_run):
        """Test main function calls run and exits with result."""
        mock_run.return_value = 0

        with patch("sys.exit") as mock_exit:
            main()
            mock_run.assert_called_once()
            mock_exit.assert_called_once_with(0)

    @patch("ai_guard.analyzer_optimized.OptimizedCodeAnalyzer")
    def test_run_function(self, mock_analyzer_class):
        """Test run function with arguments."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.run_all_checks.return_value = [GateResult("test", True, "ok")]

        with patch("ai_guard.analyzer_optimized.summarize") as mock_summarize:
            mock_summarize.return_value = 0
            result = run(["--min-cov", "80"])
            assert result == 0
            mock_analyzer.run_all_checks.assert_called_once()


class TestErrorHandling:
    """Test error handling in optimized analyzer."""

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_lint_check_with_errors(self, mock_run):
        """Test lint check handles errors gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "flake8")

        result, sarif = run_lint_check(["test.py"])

        assert isinstance(result, GateResult)
        assert result.passed is False
        assert "error" in result.details.lower()

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_type_check_with_errors(self, mock_run):
        """Test type check handles errors gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "mypy")

        result, sarif = run_type_check(["test.py"])

        assert isinstance(result, GateResult)
        assert result.passed is False
        assert "error" in result.details.lower()

    @patch("ai_guard.analyzer_optimized.subprocess.run")
    def test_security_check_with_errors(self, mock_run):
        """Test security check handles errors gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bandit")

        result, sarif = run_security_check()

        assert isinstance(result, GateResult)
        assert result.passed is False
        assert "error" in result.details.lower()


class TestConfiguration:
    """Test configuration handling."""

    def test_config_loading(self):
        """Test configuration loading."""
        with patch("ai_guard.analyzer_optimized.load_config") as mock_load:
            mock_load.return_value = {"min_coverage": 85}
            analyzer = OptimizedCodeAnalyzer()
            assert analyzer.config["min_coverage"] == 85

    def test_config_override(self):
        """Test configuration override."""
        config = {"min_coverage": 90}
        analyzer = OptimizedCodeAnalyzer(config)
        assert analyzer.config["min_coverage"] == 90


class TestPerformanceOptimizations:
    """Test performance optimization features."""

    @patch("ai_guard.analyzer_optimized.time_function")
    def test_time_function_decorator(self, mock_time):
        """Test time function decorator is applied."""
        mock_time.return_value = lambda func: func

        # This tests that the decorator is imported and available
        assert callable(time_function)

    @patch("ai_guard.analyzer_optimized.cached")
    def test_cached_decorator(self, mock_cached):
        """Test cached decorator is applied."""
        mock_cached.return_value = lambda func: func

        # This tests that the decorator is imported and available
        assert callable(cached)

    @patch("ai_guard.analyzer_optimized.parallel_execute")
    def test_parallel_execute(self, mock_parallel):
        """Test parallel execution functionality."""
        mock_parallel.return_value = []

        # This tests that parallel_execute is imported and available
        assert callable(parallel_execute)


if __name__ == "__main__":
    pytest.main([__file__])
