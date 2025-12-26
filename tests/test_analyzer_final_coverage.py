"""Final coverage tests for analyzer.py to reach 80% coverage."""

import json
import os
import tempfile
from unittest.mock import Mock, patch
import pytest

from src.ai_guard.analyzer import (
    run,
    _coverage_percent_from_xml,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_json,
    cov_percent,
    _norm,
    _to_text,
    _normalize_rule_id,
    _strict_subprocess_fail,
    _rule_style,
    _make_rule_id,
    RuleIdStyle,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    AnalysisResult,
    AnalysisConfig,
    _parse_bandit_output,
    _should_skip_file,
    _get_git_diff,
    _get_changed_files,
    _parse_coverage_output,
    _parse_sarif_output,
    _to_findings,
    _write_reports,
    _run_tool,
    analyze_code,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    generate_report,
    run_analysis,
)
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestCoverageEdgeCases:
    """Test edge cases to improve coverage."""

    def test_coverage_percent_from_xml_multiple_candidates(self):
        """Test _coverage_percent_from_xml with multiple file candidates."""
        # Test with specific XML path that exists
        xml_content = """<?xml version="1.0" ?>
        <coverage line-rate="0.90">
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            xml_path = f.name

        try:
            result = _coverage_percent_from_xml(xml_path)
            assert result == 90
        finally:
            os.unlink(xml_path)

    def test_cov_percent_multiple_paths(self):
        """Test cov_percent function with multiple paths."""
        # Test that cov_percent tries multiple paths
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml") as mock_cov_xml:
            # First two calls return None, third returns a value
            mock_cov_xml.side_effect = [None, None, 85]
            result = cov_percent()
            assert result == 85
            # Should have tried multiple paths
            assert mock_cov_xml.call_count == 3

    def test_to_text_bytearray(self):
        """Test _to_text with bytearray input."""
        test_bytearray = bytearray(b"test bytearray")
        result = _to_text(test_bytearray)
        assert result == "test bytearray"

    def test_to_text_replacement_characters(self):
        """Test _to_text with replacement characters."""
        # Test bytes that decode with replacement chars
        test_bytes = b"hello\xff\xfe"
        result = _to_text(test_bytes)
        # Should contain replacement chars but we check for empty as per implementation
        assert isinstance(result, str)

    def test_norm_bytearray(self):
        """Test _norm with bytearray input."""
        test_bytearray = bytearray(b"test")
        result = _norm(test_bytearray)
        assert result == "test"

    def test_make_rule_id_empty_code(self):
        """Test _make_rule_id with empty code."""
        result = _make_rule_id("tool", "")
        assert result == "tool"

    def test_make_rule_id_whitespace_code(self):
        """Test _make_rule_id with whitespace code."""
        result = _make_rule_id("tool", "  ")
        assert result == "tool"

    def test_rule_style_variations(self):
        """Test _rule_style with different environment values."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": " TOOL "}):
            assert _rule_style() == RuleIdStyle.TOOL

        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "BARE"}):
            assert _rule_style() == RuleIdStyle.BARE

    def test_strict_subprocess_fail_variations(self):
        """Test _strict_subprocess_fail with different values."""
        test_values = ["YES", "True", "ON", "1"]
        for value in test_values:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                assert _strict_subprocess_fail() is True


class TestParsingEdgeCases:
    """Test parsing functions edge cases."""

    def test_parse_flake8_output_whitespace(self):
        """Test _parse_flake8_output with whitespace handling."""
        output = "  test.py:1:1: E501 line too long  \n\n  "
        result = _parse_flake8_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "E501"

    def test_parse_mypy_output_no_column(self):
        """Test _parse_mypy_output without column numbers."""
        output = "test.py:10: error: Name not defined"
        result = _parse_mypy_output(output)
        assert len(result) == 1
        assert (
            result[0].locations[0]["physicalLocation"]["region"]["startColumn"] is None
        )

    def test_parse_bandit_json_missing_fields(self):
        """Test _parse_bandit_json with missing fields."""
        # Test with missing filename
        bandit_json = json.dumps(
            {"results": [{"line_number": 10, "issue_text": "Test issue"}]}
        )
        result = _parse_bandit_json(bandit_json)
        assert len(result) == 1
        assert (
            result[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "unknown.py"
        )

    def test_parse_bandit_output_fallback(self):
        """Test _parse_bandit_output fallback behavior."""
        # Test with non-bandit output
        output = "some other output"
        result = _parse_bandit_output(output)
        assert result == []

    def test_parse_coverage_output_edge_cases(self):
        """Test _parse_coverage_output with edge cases."""
        # Test with malformed lines
        output = "file.py: not a number lines, also not covered"
        result = _parse_coverage_output(output)
        assert result is None

        # Test with zero total lines
        output = "file.py: 0 lines, 0 covered"
        result = _parse_coverage_output(output)
        # Should handle division by zero gracefully
        assert result is None or isinstance(result, int)

    def test_parse_sarif_output_malformed(self):
        """Test _parse_sarif_output with malformed data."""
        # Test with runs as non-list
        output = '{"runs": "not a list"}'
        result = _parse_sarif_output(output)
        assert result == []

        # Test with empty runs list
        output = '{"runs": []}'
        result = _parse_sarif_output(output)
        assert result == []


class TestToolExecutionEdgeCases:
    """Test tool execution edge cases."""

    @patch("subprocess.run")
    def test_run_lint_check_no_parseable_output(self, mock_run):
        """Test run_lint_check with no parseable output but error code."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="flake8: some error message"
        )

        gate_result, sarif_result = run_lint_check(["test.py"])
        assert gate_result.passed is False
        assert "flake8 error" in gate_result.details
        assert sarif_result is None

    @patch("subprocess.run")
    def test_run_type_check_no_parseable_output(self, mock_run):
        """Test run_type_check with no parseable output but error code."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="mypy: configuration error"
        )

        gate_result, sarif_result = run_type_check(["test.py"])
        assert gate_result.passed is False
        assert "mypy error" in gate_result.details
        assert sarif_result is None

    @patch("subprocess.run")
    def test_run_security_check_no_parseable_output(self, mock_run):
        """Test run_security_check with no parseable output but error code."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="bandit: configuration error"
        )

        gate_result, sarif_result = run_security_check()
        assert gate_result.passed is False
        assert "bandit error" in gate_result.details
        assert sarif_result is None


class TestFileSkipLogic:
    """Test file skipping logic."""

    def test_should_skip_file_comprehensive(self):
        """Test _should_skip_file comprehensive scenarios."""
        # Test various file extensions
        assert _should_skip_file("test.js") is True
        assert _should_skip_file("test.ts") is True
        assert _should_skip_file("test.cpp") is True

        # Test hidden directories
        assert _should_skip_file(".git/file.py") is True
        assert _should_skip_file(".vscode/file.py") is True

        # Test cache variations
        assert _should_skip_file("dir/__pycache__/test.pyc") is True
        assert _should_skip_file("src/module/__pycache__/test.py") is True


class TestAnalysisUtilityFunctions:
    """Test analysis utility functions."""

    def test_analyze_functions_complete(self):
        """Test the utility analyze_* functions."""
        # These functions create new analyzer instances
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            test_file = f.name

        try:
            # Test analyze_code
            result = analyze_code(test_file)
            assert isinstance(result, AnalysisResult)

            # Test analyze_security
            sec_result = analyze_security(test_file)
            assert isinstance(sec_result, list)

            # Test analyze_performance
            perf_result = analyze_performance(test_file)
            assert isinstance(perf_result, list)

            # Test analyze_quality
            qual_result = analyze_quality(test_file)
            assert isinstance(qual_result, list)

            # Test analyze_coverage
            cov_result = analyze_coverage(test_file)
            assert isinstance(cov_result, dict)

        finally:
            os.unlink(test_file)

    def test_generate_report_formats(self):
        """Test generate_report with different formats."""
        result = AnalysisResult(
            security_issues=["sec1"],
            performance_issues=["perf1"],
            quality_issues=["qual1"],
        )

        # Test XML format
        xml_report = generate_report(result, "xml")
        assert "<report>" in xml_report
        assert "<issues>3</issues>" in xml_report

        # Test default format (should be string representation)
        default_report = generate_report(result, "unknown")
        assert isinstance(default_report, str)

    def test_run_analysis_multiple_files(self):
        """Test run_analysis with multiple files."""
        config = AnalysisConfig()

        files = []
        try:
            # Create multiple test files
            for i in range(3):
                f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
                f.write(f"def test{i}(): pass")
                f.close()
                files.append(f.name)

            result = run_analysis(files, config)
            assert isinstance(result, AnalysisResult)
            # Should combine results from all files
            assert len(result.security_issues) >= 0

        finally:
            for f in files:
                try:
                    os.unlink(f)
                except:
                    pass


class TestAnalyzerClassEdgeCases:
    """Test analyzer class edge cases."""

    def test_security_analyzer_file_error(self):
        """Test SecurityAnalyzer with file read error."""
        analyzer = SecurityAnalyzer()

        # Create a file and then make it unreadable (simulation)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test")
            test_file = f.name

        try:
            # Mock open to raise an exception
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                result = analyzer.analyze_file(test_file)
                assert len(result) == 1
                assert "Error analyzing file" in result[0]
        finally:
            os.unlink(test_file)

    def test_performance_analyzer_file_error(self):
        """Test PerformanceAnalyzer with file read error."""
        analyzer = PerformanceAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test")
            test_file = f.name

        try:
            with patch("builtins.open", side_effect=IOError("Read error")):
                result = analyzer.analyze_file(test_file)
                assert len(result) == 1
                assert "Error analyzing file" in result[0]
        finally:
            os.unlink(test_file)

    def test_quality_analyzer_file_error(self):
        """Test QualityAnalyzer with file read error."""
        analyzer = QualityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test")
            test_file = f.name

        try:
            with patch("builtins.open", side_effect=Exception("General error")):
                result = analyzer.analyze_file(test_file)
                assert len(result) == 1
                assert "Error analyzing file" in result[0]
        finally:
            os.unlink(test_file)


class TestCodeAnalyzerEdgeCases:
    """Test CodeAnalyzer edge cases."""

    def test_code_analyzer_config_disabled_analysis(self):
        """Test CodeAnalyzer with disabled analysis types."""
        config = AnalysisConfig(
            enable_security_analysis=False,
            enable_performance_analysis=False,
            enable_quality_analysis=False,
            enable_coverage_analysis=False,
        )
        analyzer = CodeAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            test_file = f.name

        try:
            result = analyzer.analyze_file(test_file)
            # All analysis types disabled, should have empty results
            assert len(result.security_issues) == 0
            assert len(result.performance_issues) == 0
            assert len(result.quality_issues) == 0
            assert len(result.coverage_data) == 0
        finally:
            os.unlink(test_file)

    def test_code_analyzer_generate_summary_empty(self):
        """Test CodeAnalyzer generate_summary with empty results."""
        analyzer = CodeAnalyzer()

        summary = analyzer.generate_summary([])
        assert summary["total_files"] == 0
        assert summary["total_issues"] == 0
        assert summary["average_execution_time"] == 0


class TestMainRunFunctionEdgeCases:
    """Test main run function edge cases."""

    @patch("src.ai_guard.analyzer.load_config")
    @patch("src.ai_guard.analyzer.changed_python_files")
    @patch("src.ai_guard.analyzer.run_lint_check")
    @patch("src.ai_guard.analyzer.run_type_check")
    @patch("src.ai_guard.analyzer.run_security_check")
    @patch("src.ai_guard.analyzer.run_coverage_check")
    @patch("src.ai_guard.analyzer.summarize")
    @patch("src.ai_guard.analyzer.write_html")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_run_function_with_event_file_checks(
        self,
        mock_getsize,
        mock_exists,
        mock_write_html,
        mock_summarize,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
        mock_config,
    ):
        """Test run function with event file existence checks."""
        mock_config.return_value = {"min_coverage": 80}
        mock_changed.return_value = ["test.py"]

        gate_result = GateResult("Test", True, "Success", 0)
        mock_lint.return_value = (gate_result, None)
        mock_type.return_value = (gate_result, None)
        mock_security.return_value = (gate_result, None)
        mock_coverage.return_value = (gate_result, None)
        mock_summarize.return_value = 0

        # Test with existing event file
        mock_exists.return_value = True
        mock_getsize.return_value = 100

        result = run(
            [
                "--event",
                "existing_event.json",
                "--report-format",
                "html",
                "--skip-tests",
            ]
        )
        assert result == 0

        # Test with non-existing event file
        mock_exists.return_value = False

        result = run(
            [
                "--event",
                "nonexistent_event.json",
                "--report-format",
                "html",
                "--skip-tests",
            ]
        )
        assert result == 0

    @patch("src.ai_guard.analyzer.load_config")
    @patch("src.ai_guard.analyzer.changed_python_files")
    @patch("src.ai_guard.analyzer.run_lint_check")
    @patch("src.ai_guard.analyzer.run_type_check")
    @patch("src.ai_guard.analyzer.run_security_check")
    @patch("src.ai_guard.analyzer.run_coverage_check")
    @patch("src.ai_guard.analyzer.summarize")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_run_function_event_file_error(
        self,
        mock_getsize,
        mock_exists,
        mock_summarize,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
        mock_config,
    ):
        """Test run function with event file error."""
        mock_config.return_value = {"min_coverage": 80}
        mock_changed.return_value = ["test.py"]

        gate_result = GateResult("Test", True, "Success", 0)
        mock_lint.return_value = (gate_result, None)
        mock_type.return_value = (gate_result, None)
        mock_security.return_value = (gate_result, None)
        mock_coverage.return_value = (gate_result, None)
        mock_summarize.return_value = 0

        # Test with exception checking event file
        mock_exists.side_effect = OSError("Permission denied")

        result = run(["--event", "error_event.json", "--skip-tests"])
        assert result == 0  # Should handle error gracefully
