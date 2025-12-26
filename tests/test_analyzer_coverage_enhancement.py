"""Enhanced coverage tests for analyzer.py to reach 70% coverage."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

from src.ai_guard.analyzer import (
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    _normalize_rule_id,
    _norm,
    _coverage_percent_from_xml,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_json,
    _parse_bandit_output,
    _to_findings,
    _run_tool,
    _write_reports,
    _should_skip_file,
    _parse_coverage_output,
    _parse_sarif_output,
    _get_git_diff,
    _get_changed_files,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    run,
    main,
    AnalysisConfig,
    AnalysisResult,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    analyze_files_parallel,
    benchmark_analyzer,
    analyze_code,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    generate_report,
    run_analysis,
)


class TestUtilityFunctions:
    """Test utility functions for better coverage."""

    def test_make_rule_id_bare_style(self):
        """Test _make_rule_id with bare style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value="bare"):
            assert _make_rule_id("flake8", "E501") == "E501"
            assert _make_rule_id("mypy", None) == "mypy"

    def test_make_rule_id_tool_style(self):
        """Test _make_rule_id with tool style."""
        with patch("src.ai_guard.analyzer._rule_style", return_value="tool"):
            assert _make_rule_id("flake8", "E501") == "flake8:E501"
            assert _make_rule_id("mypy", None) == "mypy:mypy"

    def test_strict_subprocess_fail_true(self):
        """Test _strict_subprocess_fail returns True."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "1"}):
            assert _strict_subprocess_fail() is True

        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"}):
            assert _strict_subprocess_fail() is True

    def test_strict_subprocess_fail_false(self):
        """Test _strict_subprocess_fail returns False."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "false"}):
            assert _strict_subprocess_fail() is False

    def test_to_text_with_bytes(self):
        """Test _to_text with bytes input."""
        assert _to_text(b"hello") == "hello"
        assert _to_text(b"\xff\xfe") == ""  # Invalid UTF-8
        assert _to_text(None) == ""
        assert _to_text("string") == "string"

    def test_normalize_rule_id(self):
        """Test _normalize_rule_id function."""
        assert _normalize_rule_id("flake8:E501") == "E501"
        assert _normalize_rule_id("E501") == "E501"

    def test_norm_function(self):
        """Test _norm function."""
        assert _norm("hello") == "hello"
        assert _norm(b"hello") == "hello"
        assert _norm(None) == ""

    def test_should_skip_file(self):
        """Test _should_skip_file function."""
        assert _should_skip_file("test.py") is False
        assert _should_skip_file("test.txt") is True
        assert _should_skip_file(".hidden.py") is True
        assert _should_skip_file("__pycache__/test.py") is True
        assert _should_skip_file("test_test.py") is True


class TestCoverageParsing:
    """Test coverage parsing functions."""

    def test_coverage_percent_from_xml_none_path(self):
        """Test _coverage_percent_from_xml with None path."""
        with patch.dict(os.environ, {"AI_GUARD_TEST_MODE": "1"}):
            assert _coverage_percent_from_xml(None) is None

    def test_coverage_percent_from_xml_missing_file(self):
        """Test _coverage_percent_from_xml with missing file."""
        assert _coverage_percent_from_xml("nonexistent.xml") is None

    def test_coverage_percent_from_xml_valid_file(self):
        """Test _coverage_percent_from_xml with valid XML."""
        xml_content = """<?xml version="1.0" ?>
        <coverage line-rate="0.85">
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 85
            finally:
                os.unlink(f.name)

    def test_parse_coverage_output(self):
        """Test _parse_coverage_output function."""
        output = "TOTAL 85%"
        assert _parse_coverage_output(output) == 85

        output = "Coverage: 90%"
        assert _parse_coverage_output(output) == 90

        output = "No coverage info"
        assert _parse_coverage_output(output) is None


class TestOutputParsing:
    """Test output parsing functions."""

    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output with empty input."""
        assert _parse_flake8_output("") == []
        assert _parse_flake8_output(None) == []

    def test_parse_flake8_output_valid(self):
        """Test _parse_flake8_output with valid input."""
        output = "test.py:10:5: E501 line too long"
        results = _parse_flake8_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "E501"
        assert results[0].message == "line too long"

    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output with empty input."""
        assert _parse_mypy_output("") == []
        assert _parse_mypy_output(None) == []

    def test_parse_mypy_output_valid(self):
        """Test _parse_mypy_output with valid input."""
        output = "test.py:10:5: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "name-defined"
        assert results[0].message == "Name 'x' is not defined"

    def test_parse_bandit_json_empty(self):
        """Test _parse_bandit_json with empty input."""
        assert _parse_bandit_json("") == []
        assert _parse_bandit_json("{}") == []

    def test_parse_bandit_json_valid(self):
        """Test _parse_bandit_json with valid input."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Test issue",
                    "test_id": "B101",
                }
            ]
        }
        results = _parse_bandit_json(json.dumps(json_data))
        assert len(results) == 1
        assert results[0].rule_id == "bandit:B101"

    def test_parse_bandit_output_with_bandit_keyword(self):
        """Test _parse_bandit_output with 'bandit' keyword."""
        output = "bandit found issues"
        results = _parse_bandit_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "bandit:B101"

    def test_parse_sarif_output_valid(self):
        """Test _parse_sarif_output with valid SARIF."""
        sarif_data = {
            "runs": [
                {
                    "results": [
                        {"ruleId": "test-rule", "message": {"text": "Test message"}}
                    ]
                }
            ]
        }
        results = _parse_sarif_output(json.dumps(sarif_data))
        assert len(results) == 1
        assert results[0]["ruleId"] == "test-rule"

    def test_parse_sarif_output_invalid(self):
        """Test _parse_sarif_output with invalid JSON."""
        assert _parse_sarif_output("invalid json") == []


class TestGitFunctions:
    """Test git-related functions."""

    def test_get_git_diff_success(self):
        """Test _get_git_diff with successful git command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "diff content"
            result = _get_git_diff()
            assert result == "diff content"

    def test_get_git_diff_failure(self):
        """Test _get_git_diff with failed git command."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            result = _get_git_diff()
            assert result == ""

    def test_get_changed_files_success(self):
        """Test _get_changed_files with successful git command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "file1.py\nfile2.py\n"
            result = _get_changed_files()
            assert result == ["file1.py", "file2.py"]

    def test_get_changed_files_failure(self):
        """Test _get_changed_files with failed git command."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            result = _get_changed_files()
            assert result == []


class TestToolExecution:
    """Test tool execution functions."""

    def test_run_tool_success(self):
        """Test _run_tool with successful execution."""
        with patch("src.ai_guard.analyzer.run_cmd") as mock_run_cmd:
            mock_run_cmd.return_value = (0, "output")
            result = _run_tool(["echo", "test"])
            assert result.returncode == 0
            assert result.stdout == "output"

    def test_run_tool_failure(self):
        """Test _run_tool with failed execution."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError

        with patch("src.ai_guard.analyzer.run_cmd") as mock_run_cmd:
            mock_run_cmd.side_effect = ToolExecutionError("Command failed")
            result = _run_tool(["invalid", "command"])
            assert result.returncode == 1
            assert result.stderr == "Command failed"


class TestReportWriting:
    """Test report writing functions."""

    def test_write_reports_sarif(self):
        """Test _write_reports with SARIF format."""
        issues = [
            {
                "rule_id": "test-rule",
                "level": "warning",
                "message": "Test message",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "sarif", "report_path": "test.sarif"}

        with patch("src.ai_guard.analyzer.write_sarif") as mock_write:
            _write_reports(issues, config)
            mock_write.assert_called_once()

    def test_write_reports_json(self):
        """Test _write_reports with JSON format."""
        issues = [
            {
                "rule_id": "test-rule",
                "level": "warning",
                "message": "Test message",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "json", "report_path": "test.json"}

        with patch("src.ai_guard.analyzer.write_json") as mock_write:
            _write_reports(issues, config)
            mock_write.assert_called_once()

    def test_write_reports_html(self):
        """Test _write_reports with HTML format."""
        issues = [
            {
                "rule_id": "test-rule",
                "level": "warning",
                "message": "Test message",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "html", "report_path": "test.html"}

        with patch("src.ai_guard.analyzer.write_html") as mock_write:
            _write_reports(issues, config)
            mock_write.assert_called_once()

    def test_write_reports_exception(self):
        """Test _write_reports with exception."""
        issues = []
        config = {"report_format": "unknown"}

        with patch("builtins.print") as mock_print:
            _write_reports(issues, config)
            mock_print.assert_called()


class TestFindingsConversion:
    """Test findings conversion functions."""

    def test_to_findings_empty(self):
        """Test _to_findings with empty list."""
        assert _to_findings([]) == []

    def test_to_findings_with_locations(self):
        """Test _to_findings with SARIF results."""
        from src.ai_guard.sarif_report import SarifResult

        sarif_results = [
            SarifResult(
                rule_id="test-rule",
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
        ]

        findings = _to_findings(sarif_results)
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "test-rule"
        assert findings[0]["level"] == "warning"  # Converted from error
        assert findings[0]["path"] == "test.py"
        assert findings[0]["line"] == 10


class TestMainFunctions:
    """Test main execution functions."""

    def test_run_lint_check_file_not_found(self):
        """Test run_lint_check when flake8 is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result, sarif = run_lint_check(["test.py"])
            assert result.passed is False
            assert "Tool not found" in result.details

    def test_run_type_check_file_not_found(self):
        """Test run_type_check when mypy is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result, sarif = run_type_check(["test.py"])
            assert result.passed is False
            assert "Tool not found" in result.details

    def test_run_security_check_file_not_found(self):
        """Test run_security_check when bandit is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result, sarif = run_security_check()
            assert result.passed is False
            assert "Tool not found" in result.details

    def test_run_coverage_check_no_coverage(self):
        """Test run_coverage_check with no coverage data."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=None):
            result, sarif = run_coverage_check(80)
            assert result.passed is False
            assert "No coverage data" in result.details

    def test_run_coverage_check_with_coverage(self):
        """Test run_coverage_check with coverage data."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=85):
            result, sarif = run_coverage_check(80)
            assert result.passed is True
            assert "85%" in result.details

    def test_run_coverage_check_no_minimum(self):
        """Test run_coverage_check with no minimum coverage."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=85):
            result, sarif = run_coverage_check(None)
            assert result.passed is True
            assert "no minimum set" in result.details


class TestAnalyzerClasses:
    """Test analyzer classes for better coverage."""

    def test_security_analyzer_load_rules(self):
        """Test SecurityAnalyzer.load_rules."""
        analyzer = SecurityAnalyzer()
        analyzer.load_rules()
        assert analyzer.rules == ["rule1", "rule2", "rule3"]

    def test_security_analyzer_analyze_file_missing(self):
        """Test SecurityAnalyzer.analyze_file with missing file."""
        analyzer = SecurityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_security_analyzer_analyze_file_with_issues(self):
        """Test SecurityAnalyzer.analyze_file with security issues."""
        analyzer = SecurityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nos.system('ls')\n")
            f.flush()

            try:
                result = analyzer.analyze_file(f.name)
                assert len(result) > 0
                assert "os.system" in result[0]
            finally:
                os.unlink(f.name)

    def test_performance_analyzer_analyze_file_missing(self):
        """Test PerformanceAnalyzer.analyze_file with missing file."""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_quality_analyzer_analyze_file_missing(self):
        """Test QualityAnalyzer.analyze_file with missing file."""
        analyzer = QualityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_coverage_analyzer_analyze_file_missing(self):
        """Test CoverageAnalyzer.analyze_file with missing file."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == {}

    def test_coverage_analyzer_set_threshold(self):
        """Test CoverageAnalyzer.set_threshold."""
        analyzer = CoverageAnalyzer()
        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0

    def test_coverage_analyzer_get_coverage_data(self):
        """Test CoverageAnalyzer.get_coverage_data."""
        analyzer = CoverageAnalyzer()
        data = analyzer.get_coverage_data()
        assert isinstance(data, dict)

    def test_coverage_analyzer_clear_data(self):
        """Test CoverageAnalyzer.clear_data."""
        analyzer = CoverageAnalyzer()
        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_analyze_file_missing(self):
        """Test CodeAnalyzer.analyze_file with missing file."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result.security_issues == ["File not found: nonexistent.py"]
        assert result.performance_issues == ["File not found: nonexistent.py"]
        assert result.quality_issues == ["File not found: nonexistent.py"]

    def test_code_analyzer_analyze_directory_missing(self):
        """Test CodeAnalyzer.analyze_directory with missing directory."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_directory("nonexistent")
        assert result == []

    def test_code_analyzer_generate_summary(self):
        """Test CodeAnalyzer.generate_summary."""
        analyzer = CodeAnalyzer()
        results = [
            AnalysisResult(
                security_issues=["issue1"],
                performance_issues=["issue2"],
                quality_issues=["issue3"],
                execution_time=1.0,
            )
        ]
        summary = analyzer.generate_summary(results)
        assert summary["total_files"] == 1
        assert summary["total_security_issues"] == 1
        assert summary["total_performance_issues"] == 1
        assert summary["total_quality_issues"] == 1

    def test_code_analyzer_run_all_checks(self):
        """Test CodeAnalyzer.run_all_checks."""
        analyzer = CodeAnalyzer()
        with (
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_sec,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_cov,
        ):

            mock_lint.return_value = (Mock(passed=True), None)
            mock_type.return_value = (Mock(passed=True), None)
            mock_sec.return_value = (Mock(passed=True), None)
            mock_cov.return_value = (Mock(passed=True), None)

            results = analyzer.run_all_checks()
            assert len(results) == 4

    def test_code_analyzer_get_performance_metrics(self):
        """Test CodeAnalyzer.get_performance_metrics."""
        analyzer = CodeAnalyzer()
        metrics = analyzer.get_performance_metrics()
        assert isinstance(metrics, dict)

    def test_code_analyzer_clear_cache(self):
        """Test CodeAnalyzer.clear_cache."""
        analyzer = CodeAnalyzer()
        analyzer.clear_cache()  # Should not raise exception

    def test_code_analyzer_get_cache_stats(self):
        """Test CodeAnalyzer.get_cache_stats."""
        analyzer = CodeAnalyzer()
        stats = analyzer.get_cache_stats()
        assert isinstance(stats, dict)
        assert "file_cache" in stats
        assert "total_cache" in stats


class TestUtilityFunctions:
    """Test utility functions for better coverage."""

    def test_analyze_files_parallel_small_list(self):
        """Test analyze_files_parallel with small file list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                results = analyze_files_parallel([f.name], max_workers=2)
                assert len(results) == 1
            finally:
                os.unlink(f.name)

    def test_benchmark_analyzer(self):
        """Test benchmark_analyzer function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                results = benchmark_analyzer([f.name], iterations=2)
                assert "sequential_time" in results
                assert "parallel_time" in results
                assert "speedup" in results
            finally:
                os.unlink(f.name)

    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                result = analyze_code(f.name)
                assert isinstance(result, AnalysisResult)
            finally:
                os.unlink(f.name)

    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                result = analyze_security(f.name)
                assert isinstance(result, list)
            finally:
                os.unlink(f.name)

    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                result = analyze_performance(f.name)
                assert isinstance(result, list)
            finally:
                os.unlink(f.name)

    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                result = analyze_quality(f.name)
                assert isinstance(result, list)
            finally:
                os.unlink(f.name)

    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                result = analyze_coverage(f.name)
                assert isinstance(result, dict)
            finally:
                os.unlink(f.name)

    def test_generate_report_json(self):
        """Test generate_report with JSON format."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        report = generate_report(result, "json")
        assert "issue1" in report

    def test_generate_report_html(self):
        """Test generate_report with HTML format."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        report = generate_report(result, "html")
        assert "Analysis Report" in report

    def test_generate_report_xml(self):
        """Test generate_report with XML format."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        report = generate_report(result, "xml")
        assert "<report>" in report

    def test_generate_report_other(self):
        """Test generate_report with other format."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        report = generate_report(result, "other")
        assert "issue1" in report

    def test_run_analysis(self):
        """Test run_analysis function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)
                assert isinstance(result, AnalysisResult)
            finally:
                os.unlink(f.name)


class TestMainFunction:
    """Test main function execution."""

    def test_main_function(self):
        """Test main function."""
        with patch("src.ai_guard.analyzer.run", return_value=0) as mock_run:
            with patch("sys.exit") as mock_exit:
                main()
                mock_run.assert_called_once()
                mock_exit.assert_called_once_with(0)

    def test_run_function_help(self):
        """Test run function with --help argument."""
        with patch("sys.exit") as mock_exit:
            result = run(["--help"])
            # Should exit with 0 for help
            assert result == 0

    def test_run_function_basic(self):
        """Test run function with basic arguments."""
        with (
            patch("src.ai_guard.analyzer.changed_python_files", return_value=[]),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_sec,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (Mock(passed=True), None)
            mock_type.return_value = (Mock(passed=True), None)
            mock_sec.return_value = (Mock(passed=True), None)
            mock_cov.return_value = (Mock(passed=True), None)

            result = run(["--skip-tests"])
            assert result == 0
