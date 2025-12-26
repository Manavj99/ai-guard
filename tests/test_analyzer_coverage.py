"""Comprehensive tests for analyzer.py to improve coverage."""

import pytest
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.ai_guard.analyzer import (
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    AnalysisResult,
    AnalysisConfig,
    RuleIdStyle,
    _rule_style,
    _to_text,
    _make_rule_id,
    _parse_coverage_output,
    analyze_code,
    run_lint_check,
    run_type_check,
    run_security_check,
    GateResult,
    run_coverage_check,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    generate_report,
    run_analysis,
)


class TestRuleIdStyle:
    """Test RuleIdStyle enum."""

    def test_rule_id_style_values(self):
        """Test rule ID style values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"


class TestRuleStyleFunction:
    """Test _rule_style function."""

    def test_rule_style_default(self):
        """Test default rule style."""
        style = _rule_style()
        assert style in [RuleIdStyle.BARE, RuleIdStyle.TOOL]


class TestMakeRuleId:
    """Test _make_rule_id function."""

    def test_make_rule_id_bare_style(self):
        """Test making rule ID with bare style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            from src.ai_guard.analyzer import _make_rule_id

            result = _make_rule_id("flake8", "E501")
            assert result == "E501"

    def test_make_rule_id_tool_style(self):
        """Test making rule ID with tool style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL):
            from src.ai_guard.analyzer import _make_rule_id

            result = _make_rule_id("flake8", "E501")
            assert result == "flake8:E501"


class TestAnalysisConfig:
    """Test AnalysisConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True
        assert config.output_format == "json"
        assert config.verbose is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = AnalysisConfig(
            enable_security_analysis=False,
            enable_performance_analysis=False,
            min_coverage=90.0,
        )
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is False
        assert config.min_coverage == 90.0


class TestAnalysisResult:
    """Test AnalysisResult class."""

    def test_initialization(self):
        """Test result initialization."""
        result = AnalysisResult()
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.execution_time == 0.0

    def test_add_security_issue(self):
        """Test adding security issue."""
        result = AnalysisResult()
        result.add_security_issue("test issue")
        assert len(result.security_issues) == 1
        assert result.security_issues[0] == "test issue"

    def test_add_performance_issue(self):
        """Test adding performance issue."""
        result = AnalysisResult()
        result.add_performance_issue("test issue")
        assert len(result.performance_issues) == 1
        assert result.performance_issues[0] == "test issue"

    def test_add_quality_issue(self):
        """Test adding quality issue."""
        result = AnalysisResult()
        result.add_quality_issue("test issue")
        assert len(result.quality_issues) == 1
        assert result.quality_issues[0] == "test issue"

    def test_set_coverage_data(self):
        """Test setting coverage data."""
        result = AnalysisResult()
        result.set_coverage_data({"file.py": 85.5})
        assert result.coverage_data == {"file.py": 85.5}

    def test_set_execution_time(self):
        """Test setting execution time."""
        result = AnalysisResult()
        result.set_execution_time(1.5)
        assert result.execution_time == 1.5

    def test_clear_issues(self):
        """Test clearing issues."""
        result = AnalysisResult()
        result.add_security_issue("test")
        result.add_performance_issue("test")
        result.add_quality_issue("test")
        result.clear_issues()
        assert len(result.security_issues) == 0
        assert len(result.performance_issues) == 0
        assert len(result.quality_issues) == 0


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []

    def test_analyze_file_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = SecurityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_analyze_file_existent(self):
        """Test analyzing existent file."""
        analyzer = SecurityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nprint('test')")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_add_issue(self):
        """Test adding security issue."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "test issue", "HIGH")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["message"] == "test issue"

    def test_clear_issues(self):
        """Test clearing issues."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "test issue", "HIGH")
        analyzer.clear_issues()
        assert len(analyzer.issues) == 0


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.issues == []

    def test_analyze_file_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_analyze_file_existent(self):
        """Test analyzing existent file."""
        analyzer = PerformanceAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def slow_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_add_issue(self):
        """Test adding performance issue."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "test issue", "HIGH")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["message"] == "test issue"

    def test_clear_issues(self):
        """Test clearing issues."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "test issue", "HIGH")
        analyzer.clear_issues()
        assert len(analyzer.issues) == 0


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.issues == []

    def test_analyze_file_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = QualityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_analyze_file_existent(self):
        """Test analyzing existent file."""
        analyzer = QualityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_add_issue(self):
        """Test adding quality issue."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "test issue", "HIGH")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["message"] == "test issue"

    def test_clear_issues(self):
        """Test clearing issues."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "test issue", "HIGH")
        analyzer.clear_issues()
        assert len(analyzer.issues) == 0


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}
        assert analyzer.threshold == 80.0

    def test_analyze_file_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == {}

    def test_analyze_file_existent(self):
        """Test analyzing existent file."""
        analyzer = CoverageAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_file)

    def test_set_threshold(self):
        """Test setting coverage threshold."""
        analyzer = CoverageAnalyzer()
        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0

    def test_get_coverage_data(self):
        """Test getting coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"file.py": 85.5}
        result = analyzer.get_coverage_data()
        assert result == {"file.py": 85.5}

    def test_clear_data(self):
        """Test clearing coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"file.py": 85.5}
        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_initialization_default(self):
        """Test default initialization."""
        analyzer = CodeAnalyzer()
        assert isinstance(analyzer.config, AnalysisConfig)
        assert isinstance(analyzer.security_analyzer, SecurityAnalyzer)
        assert isinstance(analyzer.performance_analyzer, PerformanceAnalyzer)
        assert isinstance(analyzer.quality_analyzer, QualityAnalyzer)
        assert isinstance(analyzer.coverage_analyzer, CoverageAnalyzer)

    def test_initialization_custom(self):
        """Test custom initialization."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        assert analyzer.config == config

    def test_analyze_file_security_disabled(self):
        """Test analyzing file with security disabled."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            assert len(result.security_issues) == 0
        finally:
            os.unlink(temp_file)

    def test_analyze_file_performance_disabled(self):
        """Test analyzing file with performance disabled."""
        config = AnalysisConfig(enable_performance_analysis=False)
        analyzer = CodeAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            assert len(result.performance_issues) == 0
        finally:
            os.unlink(temp_file)

    def test_analyze_file_quality_disabled(self):
        """Test analyzing file with quality disabled."""
        config = AnalysisConfig(enable_quality_analysis=False)
        analyzer = CodeAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            assert len(result.quality_issues) == 0
        finally:
            os.unlink(temp_file)

    def test_analyze_file_coverage_disabled(self):
        """Test analyzing file with coverage disabled."""
        config = AnalysisConfig(enable_coverage_analysis=False)
        analyzer = CodeAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            assert result.coverage_data == {}
        finally:
            os.unlink(temp_file)

    def test_analyze_directory_nonexistent(self):
        """Test analyzing nonexistent directory."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_directory("nonexistent_dir")
        assert result == []

    def test_analyze_directory_existent(self):
        """Test analyzing existent directory."""
        analyzer = CodeAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("def test_function():\n    pass")

            result = analyzer.analyze_directory(temp_dir)
            assert len(result) == 1
            assert isinstance(result[0], AnalysisResult)

    def test_generate_summary_empty(self):
        """Test generating summary with empty results."""
        analyzer = CodeAnalyzer()
        summary = analyzer.generate_summary([])
        assert summary["total_files"] == 0
        assert summary["total_security_issues"] == 0
        assert summary["total_performance_issues"] == 0
        assert summary["total_quality_issues"] == 0
        assert summary["total_coverage_issues"] == 0
        assert summary["total_issues"] == 0
        assert summary["average_execution_time"] == 0

    def test_generate_summary_with_data(self):
        """Test generating summary with data."""
        analyzer = CodeAnalyzer()

        # Create mock results
        result1 = AnalysisResult()
        result1.add_security_issue("issue1")
        result1.add_performance_issue("issue2")
        result1.set_execution_time(1.0)

        result2 = AnalysisResult()
        result2.add_quality_issue("issue3")
        result2.set_coverage_data({"file.py": 85.5})
        result2.set_execution_time(2.0)

        summary = analyzer.generate_summary([result1, result2])
        assert summary["total_files"] == 2
        assert summary["total_security_issues"] == 1
        assert summary["total_performance_issues"] == 1
        assert summary["total_quality_issues"] == 1
        assert summary["total_coverage_issues"] == 1
        assert summary["total_issues"] == 3
        assert summary["average_execution_time"] == 1.5

    @patch("src.ai_guard.analyzer.run_lint_check")
    @patch("src.ai_guard.analyzer.run_type_check")
    @patch("src.ai_guard.analyzer.run_security_check")
    @patch("src.ai_guard.analyzer.run_coverage_check")
    def test_run_all_checks(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test running all checks."""
        analyzer = CodeAnalyzer()

        # Mock the check functions
        mock_lint.return_value = (Mock(), "")
        mock_type.return_value = (Mock(), "")
        mock_security.return_value = (Mock(), "")
        mock_coverage.return_value = (Mock(), "")

        results = analyzer.run_all_checks(["test.py"])
        assert len(results) == 4


class TestGateCheckFunctions:
    """Test gate check functions."""

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_lint_check(self, mock_run):
        """Test running lint check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, output = run_lint_check(["test.py"])
        assert isinstance(result, GateResult)
        assert output is None

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_type_check(self, mock_run):
        """Test running type check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, output = run_type_check(["test.py"])
        assert isinstance(result, GateResult)
        assert output is None

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_security_check(self, mock_run):
        """Test running security check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, output = run_security_check()
        assert isinstance(result, GateResult)
        assert output is None

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_coverage_check(self, mock_run):
        """Test running coverage check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result, output = run_coverage_check(80)
        assert isinstance(result, GateResult)
        assert output is None


class TestCoverageAnalyzerMethods:
    """Test CoverageAnalyzer specific methods."""

    def test_get_coverage_data(self):
        """Test get_coverage_data method."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.5}

        result = analyzer.get_coverage_data()
        assert result == {"test.py": 85.5}

    def test_clear_data(self):
        """Test clear_data method."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.5}

        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzerMethods:
    """Test CodeAnalyzer specific methods."""

    def test_generate_summary(self):
        """Test generate_summary method."""
        analyzer = CodeAnalyzer()

        # Create mock results
        result1 = AnalysisResult()
        result1.security_issues = ["issue1"]
        result1.performance_issues = ["perf1"]
        result1.quality_issues = ["qual1"]
        result1.coverage_data = {"file1.py": 85.0}
        result1.execution_time = 1.5

        result2 = AnalysisResult()
        result2.security_issues = ["issue2"]
        result2.performance_issues = []
        result2.quality_issues = []
        result2.coverage_data = {"file2.py": 90.0}
        result2.execution_time = 2.0

        results = [result1, result2]
        summary = analyzer.generate_summary(results)

        assert summary["total_files"] == 2
        assert summary["total_security_issues"] == 2
        assert summary["total_performance_issues"] == 1
        assert summary["total_quality_issues"] == 1
        assert summary["total_coverage_issues"] == 2
        assert summary["total_issues"] == 4
        assert summary["average_execution_time"] == 1.75

    def test_generate_summary_empty_results(self):
        """Test generate_summary with empty results."""
        analyzer = CodeAnalyzer()
        summary = analyzer.generate_summary([])

        assert summary["total_files"] == 0
        assert summary["total_security_issues"] == 0
        assert summary["total_performance_issues"] == 0
        assert summary["total_quality_issues"] == 0
        assert summary["total_coverage_issues"] == 0
        assert summary["total_issues"] == 0
        assert summary["average_execution_time"] == 0

    def test_analyze_directory_nonexistent(self):
        """Test analyze_directory with nonexistent directory."""
        analyzer = CodeAnalyzer()
        results = analyzer.analyze_directory("/nonexistent/path")
        assert results == []

    def test_analyze_directory_existing(self):
        """Test analyze_directory with existing directory."""
        analyzer = CodeAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("def test_function():\n    pass")

            results = analyzer.analyze_directory(temp_dir)
            assert len(results) == 1
            assert isinstance(results[0], AnalysisResult)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyze_code(temp_file)
            assert isinstance(result, AnalysisResult)
        finally:
            os.unlink(temp_file)

    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nos.system('ls')")
            temp_file = f.name

        try:
            result = analyze_security(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("for i in range(1000000):\n    pass")
            temp_file = f.name

        try:
            result = analyze_performance(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: Fix this\n# FIXME: Remove this")
            temp_file = f.name

        try:
            result = analyze_quality(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            result = analyze_coverage(temp_file)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_file)

    def test_generate_report_json(self):
        """Test generate_report function with JSON format."""
        result = AnalysisResult()
        result.add_security_issue("test issue")

        report = generate_report(result, "json")
        assert isinstance(report, str)
        assert "test issue" in report

    def test_generate_report_html(self):
        """Test generate_report function with HTML format."""
        result = AnalysisResult()
        result.add_security_issue("test issue")

        report = generate_report(result, "html")
        assert isinstance(report, str)
        assert "<html>" in report

    def test_generate_report_xml(self):
        """Test generate_report function with XML format."""
        result = AnalysisResult()
        result.add_security_issue("test issue")

        report = generate_report(result, "xml")
        assert isinstance(report, str)
        assert "<report>" in report

    def test_generate_report_default(self):
        """Test generate_report function with default format."""
        result = AnalysisResult()
        result.add_security_issue("test issue")

        report = generate_report(result, "unknown")
        assert isinstance(report, str)

    def test_run_analysis(self):
        """Test run_analysis function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    pass")
            temp_file = f.name

        try:
            config = AnalysisConfig()
            result = run_analysis([temp_file], config)
            assert isinstance(result, AnalysisResult)
        finally:
            os.unlink(temp_file)


class TestRuleStyleFunctions:
    """Test rule style functions."""

    def test_rule_style_bare(self):
        """Test _rule_style function returns bare style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"}):
            from src.ai_guard.analyzer import _rule_style

            style = _rule_style()
            assert style == RuleIdStyle.BARE

    def test_rule_style_tool(self):
        """Test _rule_style function returns tool style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            from src.ai_guard.analyzer import _rule_style

            style = _rule_style()
            assert style == RuleIdStyle.TOOL

    def test_rule_style_default(self):
        """Test _rule_style function returns default style."""
        with patch.dict(os.environ, {}, clear=True):
            from src.ai_guard.analyzer import _rule_style

            style = _rule_style()
            assert style == RuleIdStyle.BARE

    def test_make_rule_id_bare(self):
        """Test _make_rule_id function with bare style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            from src.ai_guard.analyzer import _make_rule_id

            result = _make_rule_id("flake8", "E501")
            assert result == "E501"

    def test_make_rule_id_tool(self):
        """Test _make_rule_id function with tool style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL):
            from src.ai_guard.analyzer import _make_rule_id

            result = _make_rule_id("flake8", "E501")
            assert result == "flake8:E501"

    def test_make_rule_id_none_code(self):
        """Test _make_rule_id function with None code."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            from src.ai_guard.analyzer import _make_rule_id

            result = _make_rule_id("flake8", None)
            assert result == "flake8"

    def test_make_rule_id_empty_code(self):
        """Test _make_rule_id function with empty code."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            from src.ai_guard.analyzer import _make_rule_id

            result = _make_rule_id("flake8", "")
            assert result == "flake8"


class TestStrictSubprocessFail:
    """Test strict subprocess fail function."""

    def test_strict_subprocess_fail_true(self):
        """Test _strict_subprocess_fail function returns True."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "1"}):
            from src.ai_guard.analyzer import _strict_subprocess_fail

            result = _strict_subprocess_fail()
            assert result is True

    def test_strict_subprocess_fail_false(self):
        """Test _strict_subprocess_fail function returns False."""
        with patch.dict(os.environ, {}, clear=True):
            from src.ai_guard.analyzer import _strict_subprocess_fail

            result = _strict_subprocess_fail()
            assert result is False


class TestToTextFunction:
    """Test _to_text function."""

    def test_to_text_none(self):
        """Test _to_text function with None."""
        from src.ai_guard.analyzer import _to_text

        result = _to_text(None)
        assert result == ""

    def test_to_text_string(self):
        """Test _to_text function with string."""
        from src.ai_guard.analyzer import _to_text

        result = _to_text("test")
        assert result == "test"

    def test_to_text_bytes(self):
        """Test _to_text function with bytes."""
        from src.ai_guard.analyzer import _to_text

        result = _to_text(b"test")
        assert result == "test"

    def test_to_text_invalid_bytes(self):
        """Test _to_text function with invalid bytes."""
        from src.ai_guard.analyzer import _to_text

        result = _to_text(b"\xff\xfe")
        assert result == ""


class TestNormalizeRuleId:
    """Test _normalize_rule_id function."""

    def test_normalize_rule_id_with_colon(self):
        """Test _normalize_rule_id function with colon."""
        from src.ai_guard.analyzer import _normalize_rule_id

        result = _normalize_rule_id("flake8:E501")
        assert result == "E501"

    def test_normalize_rule_id_without_colon(self):
        """Test _normalize_rule_id function without colon."""
        from src.ai_guard.analyzer import _normalize_rule_id

        result = _normalize_rule_id("E501")
        assert result == "E501"


class TestNormFunction:
    """Test _norm function."""

    def test_norm_none(self):
        """Test _norm function with None."""
        from src.ai_guard.analyzer import _norm

        result = _norm(None)
        assert result == ""

    def test_norm_string(self):
        """Test _norm function with string."""
        from src.ai_guard.analyzer import _norm

        result = _norm("test")
        assert result == "test"

    def test_norm_bytes(self):
        """Test _norm function with bytes."""
        from src.ai_guard.analyzer import _norm

        result = _norm(b"test")
        assert result == "test"


class TestCoveragePercentFromXml:
    """Test _coverage_percent_from_xml function."""

    def test_coverage_percent_from_xml_none(self):
        """Test _coverage_percent_from_xml function with None."""
        from src.ai_guard.analyzer import _coverage_percent_from_xml

        result = _coverage_percent_from_xml(None)
        assert result is None

    def test_coverage_percent_from_xml_test_mode(self):
        """Test _coverage_percent_from_xml function in test mode."""
        with patch.dict(os.environ, {"AI_GUARD_TEST_MODE": "1"}):
            from src.ai_guard.analyzer import _coverage_percent_from_xml

            result = _coverage_percent_from_xml(None)
            assert result is None

    def test_coverage_percent_from_xml_nonexistent_file(self):
        """Test _coverage_percent_from_xml function with nonexistent file."""
        from src.ai_guard.analyzer import _coverage_percent_from_xml

        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None


class TestCovPercentFunction:
    """Test cov_percent function."""

    def test_cov_percent_no_files(self):
        """Test cov_percent function with no coverage files."""
        from src.ai_guard.analyzer import cov_percent

        result = cov_percent()
        # The function might return a value if coverage.xml exists
        assert result is None or isinstance(result, int)


class TestParseFlake8Output:
    """Test _parse_flake8_output function."""

    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output function with empty input."""
        from src.ai_guard.analyzer import _parse_flake8_output

        result = _parse_flake8_output("")
        assert result == []

    def test_parse_flake8_output_valid(self):
        """Test _parse_flake8_output function with valid input."""
        from src.ai_guard.analyzer import _parse_flake8_output

        output = "test.py:10:5: E501 line too long"
        result = _parse_flake8_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "E501"
        assert result[0].message == "line too long"

    def test_parse_flake8_output_invalid(self):
        """Test _parse_flake8_output function with invalid input."""
        from src.ai_guard.analyzer import _parse_flake8_output

        output = "invalid format"
        result = _parse_flake8_output(output)
        assert result == []


class TestParseMypyOutput:
    """Test _parse_mypy_output function."""

    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output function with empty input."""
        from src.ai_guard.analyzer import _parse_mypy_output

        result = _parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_valid(self):
        """Test _parse_mypy_output function with valid input."""
        from src.ai_guard.analyzer import _parse_mypy_output

        output = "test.py:10:5: error: Name 'x' is not defined [name-defined]"
        result = _parse_mypy_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "name-defined"
        assert result[0].message == "Name 'x' is not defined"

    def test_parse_mypy_output_invalid(self):
        """Test _parse_mypy_output function with invalid input."""
        from src.ai_guard.analyzer import _parse_mypy_output

        output = "invalid format"
        result = _parse_mypy_output(output)
        assert result == []


class TestParseBanditJson:
    """Test _parse_bandit_json function."""

    def test_parse_bandit_json_empty(self):
        """Test _parse_bandit_json function with empty input."""
        from src.ai_guard.analyzer import _parse_bandit_json

        result = _parse_bandit_json("")
        assert result == []

    def test_parse_bandit_json_valid(self):
        """Test _parse_bandit_json function with valid input."""
        from src.ai_guard.analyzer import _parse_bandit_json

        json_data = '{"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}'
        result = _parse_bandit_json(json_data)
        assert len(result) == 1
        # The rule_id format depends on the rule style configuration
        assert result[0].rule_id in ["B101", "bandit:B101"]
        assert result[0].message == "Test issue"

    def test_parse_bandit_json_invalid(self):
        """Test _parse_bandit_json function with invalid input."""
        from src.ai_guard.analyzer import _parse_bandit_json

        result = _parse_bandit_json("invalid json")
        assert result == []


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""

    def test_parse_bandit_output_with_bandit(self):
        """Test _parse_bandit_output function with bandit in output."""
        from src.ai_guard.analyzer import _parse_bandit_output

        output = "bandit output"
        result = _parse_bandit_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "bandit:B101"

    def test_parse_bandit_output_without_bandit(self):
        """Test _parse_bandit_output function without bandit in output."""
        from src.ai_guard.analyzer import _parse_bandit_output

        output = "regular output"
        result = _parse_bandit_output(output)
        assert result == []


class TestToFindings:
    """Test _to_findings function."""

    def test_to_findings_empty(self):
        """Test _to_findings function with empty input."""
        from src.ai_guard.analyzer import _to_findings

        result = _to_findings([])
        assert result == []

    def test_to_findings_with_results(self):
        """Test _to_findings function with results."""
        from src.ai_guard.analyzer import _to_findings, SarifResult

        sarif_result = SarifResult(
            rule_id="test:rule",
            level="error",
            message="Test message",
            locations=[
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": "test.py"},
                        "region": {"startLine": 10},
                    }
                }
            ],
        )
        result = _to_findings([sarif_result])
        assert len(result) == 1
        assert result[0]["rule_id"] == "test:rule"
        assert result[0]["level"] == "warning"  # error converted to warning


class TestRunTool:
    """Test _run_tool function."""

    def test_run_tool_success(self):
        """Test _run_tool function with success."""
        from src.ai_guard.analyzer import _run_tool

        # Test with a simple command that should work
        result = _run_tool(["echo", "test"])
        # The result should be a CompletedProcess-like object
        assert hasattr(result, "returncode")
        assert hasattr(result, "stdout")

    def test_run_tool_error(self):
        """Test _run_tool function with error."""
        from src.ai_guard.analyzer import _run_tool

        # Test with a command that should fail
        result = _run_tool(["nonexistent_command_12345"])
        # The result should be a CompletedProcess-like object
        assert hasattr(result, "returncode")
        assert hasattr(result, "stderr")


class TestWriteReports:
    """Test _write_reports function."""

    @patch("src.ai_guard.analyzer.write_sarif")
    def test_write_reports_sarif(self, mock_write_sarif):
        """Test _write_reports function with SARIF format."""
        from src.ai_guard.analyzer import _write_reports

        issues = [
            {
                "rule_id": "test",
                "level": "error",
                "message": "test",
                "path": "test.py",
                "line": 1,
            }
        ]
        config = {"report_format": "sarif", "report_path": "test.sarif"}

        _write_reports(issues, config)
        mock_write_sarif.assert_called_once()

    @patch("src.ai_guard.analyzer.write_json")
    def test_write_reports_json(self, mock_write_json):
        """Test _write_reports function with JSON format."""
        from src.ai_guard.analyzer import _write_reports

        issues = [
            {
                "rule_id": "test",
                "level": "error",
                "message": "test",
                "path": "test.py",
                "line": 1,
            }
        ]
        config = {"report_format": "json", "report_path": "test.json"}

        _write_reports(issues, config)
        mock_write_json.assert_called_once()

    @patch("src.ai_guard.analyzer.write_html")
    def test_write_reports_html(self, mock_write_html):
        """Test _write_reports function with HTML format."""
        from src.ai_guard.analyzer import _write_reports

        issues = [
            {
                "rule_id": "test",
                "level": "error",
                "message": "test",
                "path": "test.py",
                "line": 1,
            }
        ]
        config = {"report_format": "html", "report_path": "test.html"}

        _write_reports(issues, config)
        mock_write_html.assert_called_once()


class TestShouldSkipFile:
    """Test _should_skip_file function."""

    def test_should_skip_file_python(self):
        """Test _should_skip_file function with Python file."""
        from src.ai_guard.analyzer import _should_skip_file

        result = _should_skip_file("test.py")
        assert result is False

    def test_should_skip_file_non_python(self):
        """Test _should_skip_file function with non-Python file."""
        from src.ai_guard.analyzer import _should_skip_file

        result = _should_skip_file("test.txt")
        assert result is True

    def test_should_skip_file_hidden(self):
        """Test _should_skip_file function with hidden file."""
        from src.ai_guard.analyzer import _should_skip_file

        result = _should_skip_file(".test.py")
        assert result is True

    def test_should_skip_file_cache(self):
        """Test _should_skip_file function with cache file."""
        from src.ai_guard.analyzer import _should_skip_file

        result = _should_skip_file("__pycache__/test.py")
        assert result is True

    def test_should_skip_file_test(self):
        """Test _should_skip_file function with test file."""
        from src.ai_guard.analyzer import _should_skip_file

        result = _should_skip_file("test_test.py")
        assert result is True


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""

    def test_parse_coverage_output_empty(self):
        """Test _parse_coverage_output function with empty input."""
        from src.ai_guard.analyzer import _parse_coverage_output

        result = _parse_coverage_output("")
        assert result is None

    def test_parse_coverage_output_with_percentage(self):
        """Test _parse_coverage_output function with percentage."""
        from src.ai_guard.analyzer import _parse_coverage_output

        output = "TOTAL 85%"
        result = _parse_coverage_output(output)
        assert result == 85

    def test_parse_coverage_output_with_coverage_text(self):
        """Test _parse_coverage_output function with coverage text."""
        from src.ai_guard.analyzer import _parse_coverage_output

        output = "Coverage: 90%"
        result = _parse_coverage_output(output)
        assert result == 90


class TestParseSarifOutput:
    """Test _parse_sarif_output function."""

    def test_parse_sarif_output_empty(self):
        """Test _parse_sarif_output function with empty input."""
        from src.ai_guard.analyzer import _parse_sarif_output

        result = _parse_sarif_output("")
        assert result == []

    def test_parse_sarif_output_valid(self):
        """Test _parse_sarif_output function with valid input."""
        from src.ai_guard.analyzer import _parse_sarif_output

        sarif_data = (
            '{"runs": [{"results": [{"ruleId": "test", "message": {"text": "test"}}]}]}'
        )
        result = _parse_sarif_output(sarif_data)
        assert len(result) == 1
        assert result[0]["ruleId"] == "test"

    def test_parse_sarif_output_invalid(self):
        """Test _parse_sarif_output function with invalid input."""
        from src.ai_guard.analyzer import _parse_sarif_output

        result = _parse_sarif_output("invalid json")
        assert result == []


class TestGitFunctions:
    """Test git-related functions."""

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_get_git_diff_success(self, mock_run):
        """Test _get_git_diff function with success."""
        from src.ai_guard.analyzer import _get_git_diff

        mock_run.return_value = Mock(stdout="diff output")

        result = _get_git_diff()
        assert result == "diff output"

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_get_git_diff_error(self, mock_run):
        """Test _get_git_diff function with error."""
        from src.ai_guard.analyzer import _get_git_diff

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = _get_git_diff()
        assert result == ""

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_get_changed_files_success(self, mock_run):
        """Test _get_changed_files function with success."""
        from src.ai_guard.analyzer import _get_changed_files

        mock_run.return_value = Mock(stdout="file1.py\nfile2.py\n")

        result = _get_changed_files()
        assert result == ["file1.py", "file2.py"]

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_get_changed_files_error(self, mock_run):
        """Test _get_changed_files function with error."""
        from src.ai_guard.analyzer import _get_changed_files

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = _get_changed_files()
        assert result == []


class TestAnalysisResultMethods:
    """Test AnalysisResult additional methods."""

    def test_get_total_issues_count(self):
        """Test get_total_issues_count method."""
        result = AnalysisResult()
        result.add_security_issue("issue1")
        result.add_performance_issue("issue2")
        result.add_quality_issue("issue3")

        count = result.get_total_issues_count()
        assert count == 3

    def test_has_issues_true(self):
        """Test has_issues method returns True when issues exist."""
        result = AnalysisResult()
        result.add_security_issue("issue1")

        assert result.has_issues() is True

    def test_has_issues_false(self):
        """Test has_issues method returns False when no issues exist."""
        result = AnalysisResult()

        assert result.has_issues() is False

    def test_get_issues_summary(self):
        """Test get_issues_summary method."""
        result = AnalysisResult()
        result.add_security_issue("issue1")
        result.add_performance_issue("issue2")

        summary = result.get_issues_summary()
        assert summary["security"] == 1
        assert summary["performance"] == 1
        assert summary["quality"] == 0
        assert summary["total"] == 2


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_initialization(self):
        """Test coverage analyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}
        assert analyzer.threshold == 80.0

    def test_analyze_file_existing(self):
        """Test analyzing existing file."""
        analyzer = CoverageAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, dict)
            assert temp_file in result
            assert result[temp_file] == 85.5
        finally:
            os.unlink(temp_file)

    def test_analyze_file_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == {}

    def test_set_threshold(self):
        """Test setting coverage threshold."""
        analyzer = CoverageAnalyzer()
        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0

    def test_get_coverage_data(self):
        """Test getting coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.0}
        result = analyzer.get_coverage_data()
        assert result == {"test.py": 85.0}

    def test_clear_data(self):
        """Test clearing coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.0}
        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_initialization_default_config(self):
        """Test analyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        assert analyzer.config is not None
        assert analyzer.security_analyzer is not None
        assert analyzer.performance_analyzer is not None
        assert analyzer.quality_analyzer is not None
        assert analyzer.coverage_analyzer is not None

    def test_initialization_custom_config(self):
        """Test analyzer initialization with custom config."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        assert analyzer.config == config

    def test_analyze_file_existing(self):
        """Test analyzing existing file."""
        analyzer = CodeAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
        finally:
            os.unlink(temp_file)

    def test_analyze_file_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert isinstance(result, AnalysisResult)
        assert result.security_issues == ["File not found: nonexistent.py"]
        assert result.performance_issues == ["File not found: nonexistent.py"]
        assert result.quality_issues == ["File not found: nonexistent.py"]
        assert result.coverage_data == {}

    def test_analyze_directory_existing(self):
        """Test analyzing existing directory."""
        analyzer = CodeAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("print('hello')")

            results = analyzer.analyze_directory(temp_dir)
            assert isinstance(results, list)
            assert len(results) >= 1

    def test_analyze_directory_nonexistent(self):
        """Test analyzing nonexistent directory."""
        analyzer = CodeAnalyzer()
        results = analyzer.analyze_directory("nonexistent_dir")
        assert results == []

    def test_generate_summary(self):
        """Test generating analysis summary."""
        analyzer = CodeAnalyzer()

        # Create test results
        results = []
        for i in range(3):
            result = AnalysisResult()
            result.add_security_issue(f"security_issue_{i}")
            result.add_performance_issue(f"performance_issue_{i}")
            result.add_quality_issue(f"quality_issue_{i}")
            result.execution_time = 1.0
            results.append(result)

        summary = analyzer.generate_summary(results)
        assert summary["total_files"] == 3
        assert summary["total_security_issues"] == 3
        assert summary["total_performance_issues"] == 3
        assert summary["total_quality_issues"] == 3
        assert summary["average_execution_time"] == 1.0

    def test_run_all_checks(self):
        """Test running all checks."""
        analyzer = CodeAnalyzer()
        results = analyzer.run_all_checks()
        assert isinstance(results, list)
        assert len(results) >= 4  # lint, type, security, coverage


class TestUtilityFunctions:
    """Test utility functions."""

    def test_analyze_code(self):
        """Test analyze_code utility function."""
        result = analyze_code("nonexistent.py")
        assert isinstance(result, AnalysisResult)

    def test_to_text_utf8(self):
        """Test _to_text with UTF-8 string."""
        result = _to_text(b"hello world")
        assert result == "hello world"

    def test_to_text_invalid_utf8(self):
        """Test _to_text with invalid UTF-8."""
        result = _to_text(b"\xff\xfe")
        assert result == ""

    def test_to_text_with_replacement_char(self):
        """Test _to_text with replacement character."""
        result = _to_text(
            b"hello\xffworld".decode("utf-8", errors="replace").encode("utf-8")
        )
        assert result == ""

    def test_to_text_string_input(self):
        """Test _to_text with string input."""
        result = _to_text("hello world")
        assert result == "hello world"

    def test_rule_style_default(self):
        """Test default rule style."""
        style = _rule_style()
        assert style == RuleIdStyle.BARE

    def test_make_rule_id_bare(self):
        """Test making bare rule ID."""
        rule_id = _make_rule_id("tool", "rule")
        assert rule_id == "rule"  # BARE style returns just the code

    def test_make_rule_id_tool_style(self):
        """Test making rule ID with TOOL style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL):
            rule_id = _make_rule_id("tool", "rule")
            assert rule_id == "tool:rule"  # TOOL style returns tool:code

    def test_parse_coverage_output_valid(self):
        """Test parsing valid coverage output."""
        # Mock coverage output that would contain percentage
        coverage_output = "Total coverage: 85%"

        result = _parse_coverage_output(coverage_output)
        assert result == 85

    def test_parse_coverage_output_invalid(self):
        """Test parsing invalid coverage output."""
        result = _parse_coverage_output("invalid output")
        assert result is None

    def test_parse_coverage_output_no_percentage(self):
        """Test parsing coverage output without percentage."""
        result = _parse_coverage_output("No coverage information found")
        assert result is None
