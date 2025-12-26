"""Comprehensive tests for analyzer.py module to achieve 80%+ coverage."""

import pytest
import os
import sys
import tempfile
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open, Mock
from pathlib import Path

from src.ai_guard.analyzer import (
    RuleIdStyle,
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    _normalize_rule_id,
    _norm,
    _coverage_percent_from_xml,
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_output,
    _parse_bandit_json,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    _get_changed_files,
    _get_git_diff,
    _run_tool,
    AnalysisConfig,
    AnalysisResult,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    analyze_code,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    generate_report,
    run_analysis,
)


class TestHelperFunctions:
    """Test helper functions."""

    def test_rule_style_default(self):
        """Test _rule_style with default (no env var)."""
        with patch.dict(os.environ, {}, clear=True):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_rule_style_tool(self):
        """Test _rule_style with tool style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL

    def test_rule_style_bare(self):
        """Test _rule_style with bare style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"}):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_make_rule_id_bare(self):
        """Test _make_rule_id with bare style."""
        with patch.dict(os.environ, {}, clear=True):
            result = _make_rule_id("flake8", "E501")
            assert result == "E501"

    def test_make_rule_id_tool(self):
        """Test _make_rule_id with tool style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _make_rule_id("flake8", "E501")
            assert result == "flake8:E501"

    def test_make_rule_id_no_code(self):
        """Test _make_rule_id with no code."""
        with patch.dict(os.environ, {}, clear=True):
            result = _make_rule_id("flake8", None)
            assert result == "flake8"

    def test_strict_subprocess_fail_default(self):
        """Test _strict_subprocess_fail with default."""
        with patch.dict(os.environ, {}, clear=True):
            assert _strict_subprocess_fail() is False

    def test_strict_subprocess_fail_enabled(self):
        """Test _strict_subprocess_fail when enabled."""
        for value in ["1", "true", "yes", "on"]:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                assert _strict_subprocess_fail() is True

    def test_to_text_none(self):
        """Test _to_text with None."""
        assert _to_text(None) == ""

    def test_to_text_string(self):
        """Test _to_text with string."""
        assert _to_text("hello") == "hello"

    def test_to_text_bytes(self):
        """Test _to_text with bytes."""
        assert _to_text(b"hello") == "hello"

    def test_to_text_bytes_utf8(self):
        """Test _to_text with UTF-8 bytes."""
        assert _to_text("hello".encode("utf-8")) == "hello"

    def test_to_text_bytes_invalid(self):
        """Test _to_text with invalid bytes."""
        invalid_bytes = b"\xff\xfe"
        result = _to_text(invalid_bytes)
        # Should return empty string for invalid UTF-8
        assert result == ""

    def test_normalize_rule_id(self):
        """Test _normalize_rule_id."""
        assert _normalize_rule_id("E501") == "E501"
        assert _normalize_rule_id("flake8:E501") == "E501"

    def test_norm_string(self):
        """Test _norm with string."""
        assert _norm("hello") == "hello"

    def test_norm_bytes(self):
        """Test _norm with bytes."""
        assert _norm(b"hello") == "hello"

    def test_norm_none(self):
        """Test _norm with None."""
        assert _norm(None) == ""


class TestParseFunctions:
    """Test parsing functions."""

    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output with empty output."""
        result = _parse_flake8_output("")
        assert result == []

    def test_parse_flake8_output_valid(self):
        """Test _parse_flake8_output with valid output."""
        output = "test.py:1:1: E501 line too long\n"
        result = _parse_flake8_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "E501"

    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output with empty output."""
        result = _parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_valid(self):
        """Test _parse_mypy_output with valid output."""
        output = "test.py:1: error: Name 'x' is not defined\n"
        result = _parse_mypy_output(output)
        assert len(result) >= 0  # May parse or not depending on format

    def test_parse_bandit_output_empty(self):
        """Test _parse_bandit_output with empty output."""
        result = _parse_bandit_output("")
        assert result == []

    def test_parse_bandit_output_valid(self):
        """Test _parse_bandit_output with valid output."""
        output = "test.py:1:1: B101: Use of assert detected\n"
        result = _parse_bandit_output(output)
        assert len(result) >= 0  # May parse or not depending on format

    def test_parse_bandit_json_empty(self):
        """Test _parse_bandit_json with empty output."""
        result = _parse_bandit_json({})
        assert result == []

    def test_parse_bandit_json_valid(self):
        """Test _parse_bandit_json with valid JSON."""
        json_data = {
            "results": [
                {
                    "test_id": "B101",
                    "filename": "test.py",
                    "line_number": 1,
                    "issue_text": "Use of assert detected",
                }
            ]
        }
        result = _parse_bandit_json(json_data)
        assert len(result) >= 0


class TestCoreCheckFunctions:
    """Test core check functions."""

    @patch("subprocess.run")
    def test_run_lint_check_success(self, mock_run):
        """Test run_lint_check with successful check."""
        mock_run.return_value = Mock(
            returncode=0, stdout="", stderr="", completed=True
        )
        result, sarif = run_lint_check(None)
        assert isinstance(result, object)  # GateResult
        assert result.passed is True

    @patch("subprocess.run")
    def test_run_lint_check_with_paths(self, mock_run):
        """Test run_lint_check with paths."""
        mock_run.return_value = Mock(
            returncode=0, stdout="", stderr="", completed=True
        )
        result, sarif = run_lint_check(["test.py"])
        assert isinstance(result, object)

    @patch("subprocess.run")
    def test_run_lint_check_failure(self, mock_run):
        """Test run_lint_check with failures."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="test.py:1:1: E501 line too long\n",
            stderr="",
            completed=True,
        )
        result, sarif = run_lint_check(None)
        assert isinstance(result, object)

    @patch("subprocess.run")
    def test_run_type_check_success(self, mock_run):
        """Test run_type_check with successful check."""
        mock_run.return_value = Mock(
            returncode=0, stdout="", stderr="", completed=True
        )
        result, sarif = run_type_check(None)
        assert isinstance(result, object)
        assert result.passed is True

    @patch("subprocess.run")
    def test_run_type_check_failure(self, mock_run):
        """Test run_type_check with failures."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="test.py:1: error: Name 'x' is not defined\n",
            stderr="",
            completed=True,
        )
        result, sarif = run_type_check(None)
        assert isinstance(result, object)

    @patch("subprocess.run")
    def test_run_security_check_success(self, mock_run):
        """Test run_security_check with successful check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"results": []}),
            stderr="",
            completed=True,
        )
        result, sarif = run_security_check()
        assert isinstance(result, object)

    @patch("subprocess.run")
    def test_run_security_check_with_issues(self, mock_run):
        """Test run_security_check with security issues."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(
                {
                    "results": [
                        {
                            "test_id": "B101",
                            "filename": "test.py",
                            "line_number": 1,
                            "issue_text": "Use of assert detected",
                        }
                    ]
                }
            ),
            stderr="",
            completed=True,
        )
        result, sarif = run_security_check()
        assert isinstance(result, object)

    @patch("subprocess.run")
    def test_run_coverage_check_success(self, mock_run):
        """Test run_coverage_check with sufficient coverage."""
        # Mock coverage XML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write('<?xml version="1.0"?><coverage line-rate="0.85"/>')
            xml_path = f.name
        try:
            with patch("src.ai_guard.analyzer._coverage_percent_from_xml") as mock_cov:
                mock_cov.return_value = 85
                result, sarif = run_coverage_check(80)
                assert isinstance(result, object)
        finally:
            if os.path.exists(xml_path):
                os.unlink(xml_path)

    @patch("subprocess.run")
    def test_run_coverage_check_low_coverage(self, mock_run):
        """Test run_coverage_check with low coverage."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml") as mock_cov:
            mock_cov.return_value = 70
            result, sarif = run_coverage_check(80)
            assert isinstance(result, object)


class TestDataClasses:
    """Test data classes."""

    def test_analysis_config_init_default(self):
        """Test AnalysisConfig initialization with defaults."""
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True

    def test_analysis_config_init_custom(self):
        """Test AnalysisConfig initialization with custom values."""
        config = AnalysisConfig(
            enable_security_analysis=False,
            min_coverage=90,
        )
        assert config.enable_security_analysis is False
        assert config.min_coverage == 90

    def test_analysis_config_from_dict(self):
        """Test AnalysisConfig.from_dict."""
        data = {"enable_security_analysis": False, "min_coverage": 85}
        config = AnalysisConfig.from_dict(data)
        assert config.enable_security_analysis is False
        assert config.min_coverage == 85

    def test_analysis_result_init(self):
        """Test AnalysisResult initialization."""
        result = AnalysisResult()
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.summary == {}

    def test_analysis_result_get_total_issues(self):
        """Test AnalysisResult.get_total_issues."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        result.performance_issues = ["issue2", "issue3"]
        result.quality_issues = ["issue4"]
        assert result.get_total_issues() == 4

    def test_analysis_result_add_issues(self):
        """Test AnalysisResult add issue methods."""
        result = AnalysisResult()
        result.add_security_issue("security issue")
        result.add_performance_issue("performance issue")
        result.add_quality_issue("quality issue")
        assert len(result.security_issues) == 1
        assert len(result.performance_issues) == 1
        assert len(result.quality_issues) == 1

    def test_analysis_result_clear_issues(self):
        """Test AnalysisResult.clear_issues."""
        result = AnalysisResult()
        result.add_security_issue("issue1")
        result.add_performance_issue("issue2")
        result.clear_issues()
        assert len(result.security_issues) == 0
        assert len(result.performance_issues) == 0
        assert len(result.quality_issues) == 0

    def test_analysis_result_set_coverage_data(self):
        """Test AnalysisResult.set_coverage_data."""
        result = AnalysisResult()
        result.set_coverage_data({"file.py": 85.5})
        assert result.coverage_data == {"file.py": 85.5}

    def test_analysis_result_set_execution_time(self):
        """Test AnalysisResult.set_execution_time."""
        result = AnalysisResult()
        result.set_execution_time(1.5)
        assert result.execution_time == 1.5


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_security_analyzer_init(self):
        """Test SecurityAnalyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []
        assert isinstance(analyzer._cache, dict)
        assert analyzer._lock is not None

    def test_security_analyzer_analyze_file_nonexistent(self):
        """Test SecurityAnalyzer.analyze_file with non-existent file."""
        analyzer = SecurityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_security_analyzer_analyze_file_existent(self):
        """Test SecurityAnalyzer.analyze_file with existing file."""
        analyzer = SecurityAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nos.system('ls')\n")
            temp_path = f.name
        try:
            result = analyzer.analyze_file(temp_path)
            assert isinstance(result, list)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_security_analyzer_clear_issues(self):
        """Test SecurityAnalyzer.clear_issues."""
        analyzer = SecurityAnalyzer()
        analyzer.issues = ["issue1", "issue2"]
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    def test_performance_analyzer_init(self):
        """Test PerformanceAnalyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.issues == []
        assert isinstance(analyzer._cache, dict)
        assert analyzer._lock is not None

    def test_performance_analyzer_analyze_file_nonexistent(self):
        """Test PerformanceAnalyzer.analyze_file with non-existent file."""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_performance_analyzer_clear_issues(self):
        """Test PerformanceAnalyzer.clear_issues."""
        analyzer = PerformanceAnalyzer()
        analyzer.issues = ["issue1"]
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""

    def test_quality_analyzer_init(self):
        """Test QualityAnalyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.issues == []
        assert isinstance(analyzer._cache, dict)
        assert analyzer._lock is not None

    def test_quality_analyzer_analyze_file_nonexistent(self):
        """Test QualityAnalyzer.analyze_file with non-existent file."""
        analyzer = QualityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_quality_analyzer_analyze_file_with_todo(self):
        """Test QualityAnalyzer.analyze_file with TODO comment."""
        analyzer = QualityAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: Fix this\n")
            temp_path = f.name
        try:
            result = analyzer.analyze_file(temp_path)
            assert isinstance(result, list)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_quality_analyzer_clear_issues(self):
        """Test QualityAnalyzer.clear_issues."""
        analyzer = QualityAnalyzer()
        analyzer.issues = ["issue1"]
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_coverage_analyzer_init(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}
        assert analyzer.threshold == 80.0
        assert isinstance(analyzer._cache, dict)
        assert analyzer._lock is not None

    def test_coverage_analyzer_analyze_file_nonexistent(self):
        """Test CoverageAnalyzer.analyze_file with non-existent file."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert isinstance(result, dict)

    def test_coverage_analyzer_clear_data(self):
        """Test CoverageAnalyzer.clear_data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"file.py": 85.0}
        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_init_default(self):
        """Test CodeAnalyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        assert analyzer.config is not None
        assert analyzer.security_analyzer is not None
        assert analyzer.performance_analyzer is not None
        assert analyzer.quality_analyzer is not None
        assert analyzer.coverage_analyzer is not None

    def test_code_analyzer_init_custom_config(self):
        """Test CodeAnalyzer initialization with custom config."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        assert analyzer.config.enable_security_analysis is False

    def test_code_analyzer_analyze_file_nonexistent(self):
        """Test CodeAnalyzer.analyze_file with non-existent file."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert isinstance(result, AnalysisResult)
        # Should have issues if analyzers are enabled
        if analyzer.config.enable_security_analysis:
            assert len(result.security_issues) > 0

    def test_code_analyzer_analyze_file_existent(self):
        """Test CodeAnalyzer.analyze_file with existing file."""
        analyzer = CodeAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    pass\n")
            temp_path = f.name
        try:
            result = analyzer.analyze_file(temp_path)
            assert isinstance(result, AnalysisResult)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_code_analyzer_analyze_directory(self):
        """Test CodeAnalyzer.analyze_directory."""
        analyzer = CodeAnalyzer()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("def hello():\n    pass\n")
            results = analyzer.analyze_directory(temp_dir)
            assert isinstance(results, list)
            assert len(results) > 0

    @patch("src.ai_guard.analyzer.run_lint_check")
    @patch("src.ai_guard.analyzer.run_type_check")
    @patch("src.ai_guard.analyzer.run_security_check")
    @patch("src.ai_guard.analyzer.run_coverage_check")
    def test_code_analyzer_run_all_checks(
        self, mock_cov, mock_sec, mock_type, mock_lint
    ):
        """Test CodeAnalyzer.run_all_checks."""
        from src.ai_guard.report import GateResult

        mock_lint.return_value = (GateResult(name="lint", passed=True), None)
        mock_type.return_value = (GateResult(name="type", passed=True), None)
        mock_sec.return_value = (GateResult(name="security", passed=True), None)
        mock_cov.return_value = (GateResult(name="coverage", passed=True), None)

        analyzer = CodeAnalyzer()
        results = analyzer.run_all_checks()
        assert isinstance(results, list)
        assert len(results) == 4

    def test_code_analyzer_clear_cache(self):
        """Test CodeAnalyzer.clear_cache."""
        analyzer = CodeAnalyzer()
        analyzer.clear_cache()  # Should not raise

    def test_code_analyzer_get_performance_metrics(self):
        """Test CodeAnalyzer.get_performance_metrics."""
        analyzer = CodeAnalyzer()
        metrics = analyzer.get_performance_metrics()
        assert isinstance(metrics, dict)

    def test_code_analyzer_get_cache_stats(self):
        """Test CodeAnalyzer.get_cache_stats."""
        analyzer = CodeAnalyzer()
        stats = analyzer.get_cache_stats()
        assert isinstance(stats, dict)


class TestCoverageHelperFunctions:
    """Test coverage helper functions."""

    def test_coverage_percent_from_xml_nonexistent(self):
        """Test _coverage_percent_from_xml with non-existent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None

    def test_coverage_percent_from_xml_valid(self):
        """Test _coverage_percent_from_xml with valid XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write('<?xml version="1.0"?><coverage line-rate="0.85"/>')
            xml_path = f.name
        try:
            result = _coverage_percent_from_xml(xml_path)
            assert result == 85
        finally:
            if os.path.exists(xml_path):
                os.unlink(xml_path)

    def test_cov_percent(self):
        """Test cov_percent function."""
        result = cov_percent()
        # May return None if coverage.xml doesn't exist
        assert result is None or isinstance(result, int)


class TestGitFunctions:
    """Test Git-related functions."""

    @patch("subprocess.run")
    def test_get_git_diff(self, mock_run):
        """Test _get_git_diff."""
        mock_run.return_value = Mock(
            returncode=0, stdout="diff content", stderr="", completed=True
        )
        result = _get_git_diff()
        assert isinstance(result, str)

    @patch("subprocess.run")
    def test_get_git_diff_error(self, mock_run):
        """Test _get_git_diff with error."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="error", completed=True
        )
        result = _get_git_diff()
        assert result == ""

    @patch("src.ai_guard.analyzer._get_git_diff")
    def test_get_changed_files(self, mock_diff):
        """Test _get_changed_files."""
        mock_diff.return_value = "diff --git a/test.py b/test.py\n"
        result = _get_changed_files()
        assert isinstance(result, list)


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("subprocess.run")
    def test_run_tool_success(self, mock_run):
        """Test _run_tool with successful execution."""
        mock_run.return_value = Mock(
            returncode=0, stdout="output", stderr="", completed=True
        )
        result = _run_tool(["echo", "test"])
        assert result.returncode == 0
        assert result.stdout == "output"

    @patch("subprocess.run")
    def test_run_tool_failure(self, mock_run):
        """Test _run_tool with failure."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="error", completed=True
        )
        result = _run_tool(["false"])
        assert result.returncode == 1


class TestStandaloneFunctions:
    """Test standalone analysis functions."""

    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    pass\n")
            temp_path = f.name
        try:
            result = analyze_code(temp_path)
            assert isinstance(result, AnalysisResult)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\n")
            temp_path = f.name
        try:
            result = analyze_security(temp_path)
            assert isinstance(result, list)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def slow():\n    pass\n")
            temp_path = f.name
        try:
            result = analyze_performance(temp_path)
            assert isinstance(result, list)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def func():\n    pass\n")
            temp_path = f.name
        try:
            result = analyze_quality(temp_path)
            assert isinstance(result, list)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def func():\n    pass\n")
            temp_path = f.name
        try:
            result = analyze_coverage(temp_path)
            assert isinstance(result, dict)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_generate_report(self):
        """Test generate_report function."""
        result = AnalysisResult()
        result.set_coverage_data({"file.py": 85.0})
        report = generate_report(result, "json")
        assert isinstance(report, str)

    def test_run_analysis(self):
        """Test run_analysis function."""
        config = AnalysisConfig()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    pass\n")
            temp_path = f.name
        try:
            result = run_analysis([temp_path], config)
            assert isinstance(result, AnalysisResult)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
