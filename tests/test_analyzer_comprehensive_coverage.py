"""Comprehensive test coverage for analyzer.py module to achieve 70%+ coverage."""

import pytest
import tempfile
import os
import subprocess
import json
import xml.etree.ElementTree as ET
from unittest.mock import patch, mock_open, MagicMock, call
from pathlib import Path
from dataclasses import dataclass

from src.ai_guard.analyzer import (
    RuleIdStyle,
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    _normalize_rule_id,
    _norm,
    _coverage_percent_from_xml,
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    run_lint_check,
    run_type_check,
    _parse_bandit_json,
    _parse_bandit_output,
    run_security_check,
    _to_findings,
    _run_tool,
    _write_reports,
    _should_skip_file,
    _parse_coverage_output,
    _parse_sarif_output,
    _get_git_diff,
    _get_changed_files,
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


class TestRuleIdStyle:
    """Test RuleIdStyle enum."""

    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"


class TestRuleStyle:
    """Test _rule_style function."""

    @patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"})
    def test_rule_style_tool(self):
        """Test tool rule style."""
        assert _rule_style() == RuleIdStyle.TOOL

    @patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"})
    def test_rule_style_bare(self):
        """Test bare rule style."""
        assert _rule_style() == RuleIdStyle.BARE

    @patch.dict(os.environ, {}, clear=True)
    def test_rule_style_default(self):
        """Test default rule style."""
        assert _rule_style() == RuleIdStyle.BARE


class TestMakeRuleId:
    """Test _make_rule_id function."""

    @patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_tool_style(self, mock_style):
        """Test rule ID creation with tool style."""
        result = _make_rule_id("flake8", "E501")
        assert result == "flake8:E501"

    @patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE)
    def test_make_rule_id_bare_style(self, mock_style):
        """Test rule ID creation with bare style."""
        result = _make_rule_id("flake8", "E501")
        assert result == "E501"

    @patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE)
    def test_make_rule_id_empty_code(self, mock_style):
        """Test rule ID creation with empty code."""
        result = _make_rule_id("flake8", "")
        assert result == "flake8"

    @patch("src.ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE)
    def test_make_rule_id_none_code(self, mock_style):
        """Test rule ID creation with None code."""
        result = _make_rule_id("flake8", None)
        assert result == "flake8"


class TestStrictSubprocessFail:
    """Test _strict_subprocess_fail function."""

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "1"})
    def test_strict_subprocess_true_1(self):
        """Test strict subprocess with '1'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"})
    def test_strict_subprocess_true_true(self):
        """Test strict subprocess with 'true'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "yes"})
    def test_strict_subprocess_true_yes(self):
        """Test strict subprocess with 'yes'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "on"})
    def test_strict_subprocess_true_on(self):
        """Test strict subprocess with 'on'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "false"})
    def test_strict_subprocess_false(self):
        """Test strict subprocess with 'false'."""
        assert _strict_subprocess_fail() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_strict_subprocess_default(self):
        """Test strict subprocess default."""
        assert _strict_subprocess_fail() is False


class TestToText:
    """Test _to_text function."""

    def test_to_text_none(self):
        """Test _to_text with None."""
        assert _to_text(None) == ""

    def test_to_text_string(self):
        """Test _to_text with string."""
        assert _to_text("hello") == "hello"

    def test_to_text_bytes_utf8(self):
        """Test _to_text with UTF-8 bytes."""
        assert _to_text(b"hello") == "hello"

    def test_to_text_bytes_invalid(self):
        """Test _to_text with invalid bytes."""
        invalid_bytes = b"\xff\xfe"
        assert _to_text(invalid_bytes) == ""

    def test_to_text_bytes_with_replacement(self):
        """Test _to_text with bytes containing replacement characters."""
        # This would contain \ufffd after decoding
        result = _to_text(b"\xff\xfe")
        assert result == ""

    def test_to_text_bytearray(self):
        """Test _to_text with bytearray."""
        assert _to_text(bytearray(b"hello")) == "hello"


class TestArtifactLocation:
    """Test ArtifactLocation dataclass."""

    def test_artifact_location(self):
        """Test ArtifactLocation creation."""
        loc = ArtifactLocation(uri="test.py")
        assert loc.uri == "test.py"


class TestRegion:
    """Test Region dataclass."""

    def test_region(self):
        """Test Region creation."""
        region = Region(startLine=1, startColumn=5)
        assert region.startLine == 1
        assert region.startColumn == 5


class TestPhysicalLocation:
    """Test PhysicalLocation dataclass."""

    def test_physical_location(self):
        """Test PhysicalLocation creation."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(startLine=1, startColumn=5)
        loc = PhysicalLocation(artifactLocation=artifact, region=region)
        assert loc.artifactLocation.uri == "test.py"
        assert loc.region.startLine == 1


class TestLocation:
    """Test Location dataclass."""

    def test_location(self):
        """Test Location creation."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(startLine=1, startColumn=5)
        physical = PhysicalLocation(artifactLocation=artifact, region=region)
        loc = Location(physicalLocation=physical)
        assert loc.physicalLocation.artifactLocation.uri == "test.py"


class TestNormalizeRuleId:
    """Test _normalize_rule_id function."""

    def test_normalize_rule_id_basic(self):
        """Test basic rule ID normalization."""
        assert _normalize_rule_id("E501") == "E501"

    def test_normalize_rule_id_with_tool(self):
        """Test rule ID normalization with tool prefix."""
        assert _normalize_rule_id("flake8:E501") == "E501"

    def test_normalize_rule_id_empty(self):
        """Test rule ID normalization with empty string."""
        assert _normalize_rule_id("") == ""


class TestNorm:
    """Test _norm function."""

    def test_norm_string(self):
        """Test _norm with string."""
        assert _norm("hello") == "hello"

    def test_norm_bytes(self):
        """Test _norm with bytes."""
        assert _norm(b"hello") == "hello"

    def test_norm_none(self):
        """Test _norm with None."""
        assert _norm(None) == ""

    def test_norm_bytearray(self):
        """Test _norm with bytearray."""
        assert _norm(bytearray(b"hello")) == "hello"


class TestCoveragePercentFromXml:
    """Test _coverage_percent_from_xml function."""

    def test_coverage_percent_valid_xml(self):
        """Test coverage percentage from valid XML."""
        xml_content = """<?xml version="1.0" ?>
        <coverage version="1.0">
            <sources>
                <source>/path/to/source</source>
            </sources>
            <packages>
                <package name="test" line-rate="0.85" branch-rate="0.75">
                    <classes>
                        <class name="TestClass" filename="test.py" line-rate="0.85" branch-rate="0.75">
                            <lines>
                                <line number="1" hits="1"/>
                                <line number="2" hits="0"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 85
            finally:
                os.unlink(f.name)

    def test_coverage_percent_invalid_xml(self):
        """Test coverage percentage from invalid XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("invalid xml content")
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                os.unlink(f.name)

    def test_coverage_percent_nonexistent_file(self):
        """Test coverage percentage from nonexistent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None


class TestCovPercent:
    """Test cov_percent function."""

    @patch("src.ai_guard.analyzer._coverage_percent_from_xml")
    def test_cov_percent_found(self, mock_coverage):
        """Test cov_percent when coverage is found."""
        mock_coverage.return_value = 85
        result = cov_percent()
        assert result == 85

    @patch("src.ai_guard.analyzer._coverage_percent_from_xml")
    def test_cov_percent_not_found(self, mock_coverage):
        """Test cov_percent when coverage is not found."""
        mock_coverage.return_value = None
        result = cov_percent()
        assert result is None


class TestParseFlake8Output:
    """Test _parse_flake8_output function."""

    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        output = "test.py:1:5: E501 line too long (80 > 79 characters)"
        results = _parse_flake8_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "E501"
        assert result.message == "line too long (80 > 79 characters)"
        assert len(result.locations) == 1

    def test_parse_flake8_output_multiple(self):
        """Test parsing multiple flake8 outputs."""
        output = """test.py:1:5: E501 line too long
test.py:2:10: W292 no newline at end of file"""
        results = _parse_flake8_output(output)

        assert len(results) == 2
        assert results[0].rule_id == "E501"
        assert results[1].rule_id == "W292"

    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        results = _parse_flake8_output("")
        assert len(results) == 0

    def test_parse_flake8_output_invalid(self):
        """Test parsing invalid flake8 output."""
        output = "invalid output format"
        results = _parse_flake8_output(output)
        assert len(results) == 0


class TestParseMyPyOutput:
    """Test _parse_mypy_output function."""

    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        output = "test.py:1: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "name-defined"
        assert result.message == "Name 'x' is not defined"

    def test_parse_mypy_output_with_column(self):
        """Test parsing mypy output with column."""
        output = "test.py:1:5: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        assert len(results[0].locations) == 1

    def test_parse_mypy_output_warning(self):
        """Test parsing mypy warning."""
        output = "test.py:1: warning: Unused variable 'x' [unused-ignore]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        assert results[0].rule_id == "unused-ignore"

    def test_parse_mypy_output_info_ignored(self):
        """Test parsing mypy info (should be ignored)."""
        output = "test.py:1: note: Some info message"
        results = _parse_mypy_output(output)
        assert len(results) == 0

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        results = _parse_mypy_output("")
        assert len(results) == 0


class TestRunLintCheck:
    """Test run_lint_check function."""

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_lint_check_success(self, mock_run_tool):
        """Test successful lint check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test.py:1:5: E501 line too long"
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_lint_check(["test.py"])

        assert gate_result.passed is True
        assert len(sarif_result.results) == 1

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_lint_check_failure(self, mock_run_tool):
        """Test lint check with errors."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test.py:1:5: E501 line too long"
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_lint_check(["test.py"])

        assert gate_result.passed is False
        assert len(sarif_result.results) == 1

    def test_run_lint_check_no_paths(self):
        """Test lint check with no paths."""
        gate_result, sarif_result = run_lint_check(None)
        assert gate_result.passed is True


class TestRunTypeCheck:
    """Test run_type_check function."""

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_type_check_success(self, mock_run_tool):
        """Test successful type check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test.py:1: error: Name 'x' is not defined [name-defined]"
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_type_check(["test.py"])

        assert gate_result.passed is True
        assert len(sarif_result.results) == 1

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_type_check_failure(self, mock_run_tool):
        """Test type check with errors."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test.py:1: error: Name 'x' is not defined [name-defined]"
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_type_check(["test.py"])

        assert gate_result.passed is False
        assert len(sarif_result.results) == 1

    def test_run_type_check_no_paths(self):
        """Test type check with no paths."""
        gate_result, sarif_result = run_type_check(None)
        assert gate_result.passed is True


class TestParseBanditJson:
    """Test _parse_bandit_json function."""

    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Test issue",
                    "test_name": "B101",
                }
            ]
        }

        results = _parse_bandit_json(json_data)
        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "B101"
        assert result.message == "Test issue"

    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON."""
        json_data = {"results": []}
        results = _parse_bandit_json(json_data)
        assert len(results) == 0

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON."""
        results = _parse_bandit_json({"invalid": "data"})
        assert len(results) == 0


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""

    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        output = """test.py:1:1: B101: Test issue
        Severity: High   Confidence: High"""
        results = _parse_bandit_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "B101"
        assert "Test issue" in result.message

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        results = _parse_bandit_output("")
        assert len(results) == 0


class TestRunSecurityCheck:
    """Test run_security_check function."""

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_security_check_success(self, mock_run_tool):
        """Test successful security check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"results": []}'
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_security_check()

        assert gate_result.passed is True

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_security_check_with_issues(self, mock_run_tool):
        """Test security check with issues."""
        json_output = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Test issue",
                    "test_name": "B101",
                }
            ]
        }

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps(json_output)
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_security_check()

        assert gate_result.passed is False
        assert len(sarif_result.results) == 1


class TestToFindings:
    """Test _to_findings function."""

    def test_to_findings_empty(self):
        """Test _to_findings with empty list."""
        findings = _to_findings([])
        assert findings == []

    def test_to_findings_with_data(self):
        """Test _to_findings with data."""
        data = [{"rule_id": "E501", "message": "Test message"}]
        findings = _to_findings(data)
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "E501"


class TestRunTool:
    """Test _run_tool function."""

    @patch("subprocess.run")
    def test_run_tool_success(self, mock_run):
        """Test successful tool run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_run.return_value = mock_result

        result = _run_tool(["echo", "test"])

        assert result.returncode == 0
        assert result.stdout == "output"

    @patch("subprocess.run")
    def test_run_tool_failure(self, mock_run):
        """Test tool run failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        result = _run_tool(["invalid", "command"])

        assert result.returncode == 1


class TestWriteReports:
    """Test _write_reports function."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_write_reports_json(self, mock_json_dump, mock_file):
        """Test writing JSON reports."""
        issues = [{"rule_id": "E501", "message": "Test"}]
        config = {"output_format": "json", "output_file": "test.json"}

        _write_reports(issues, config)

        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_reports_html(self, mock_file):
        """Test writing HTML reports."""
        issues = [{"rule_id": "E501", "message": "Test"}]
        config = {"output_format": "html", "output_file": "test.html"}

        _write_reports(issues, config)

        mock_file.assert_called_once()


class TestShouldSkipFile:
    """Test _should_skip_file function."""

    def test_should_skip_file_pyc(self):
        """Test skipping .pyc files."""
        assert _should_skip_file("test.pyc") is True

    def test_should_skip_file_pyo(self):
        """Test skipping .pyo files."""
        assert _should_skip_file("test.pyo") is True

    def test_should_skip_file_py_normal(self):
        """Test not skipping normal .py files."""
        assert _should_skip_file("test.py") is False

    def test_should_skip_file_pyi(self):
        """Test skipping .pyi files."""
        assert _should_skip_file("test.pyi") is True


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""

    def test_parse_coverage_output_valid(self):
        """Test parsing valid coverage output."""
        output = (
            "Name                    Stmts   Miss  Cover\n"
            "----------------------------------------\n"
            "test.py                     10      2    80%\n"
            "----------------------------------------\n"
            "TOTAL                       10      2    80%"
        )

        result = _parse_coverage_output(output)
        assert result == 80

    def test_parse_coverage_output_no_match(self):
        """Test parsing coverage output with no match."""
        output = "No coverage data available"
        result = _parse_coverage_output(output)
        assert result is None

    def test_parse_coverage_output_empty(self):
        """Test parsing empty coverage output."""
        result = _parse_coverage_output("")
        assert result is None


class TestParseSarifOutput:
    """Test _parse_sarif_output function."""

    def test_parse_sarif_output_valid(self):
        """Test parsing valid SARIF output."""
        sarif_data = {
            "runs": [
                {
                    "results": [
                        {
                            "ruleId": "E501",
                            "message": {"text": "Test message"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "test.py"},
                                        "region": {"startLine": 1},
                                    }
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        output = json.dumps(sarif_data)
        results = _parse_sarif_output(output)

        assert len(results) == 1
        assert results[0]["ruleId"] == "E501"

    def test_parse_sarif_output_invalid_json(self):
        """Test parsing invalid SARIF JSON."""
        results = _parse_sarif_output("invalid json")
        assert len(results) == 0

    def test_parse_sarif_output_empty(self):
        """Test parsing empty SARIF output."""
        results = _parse_sarif_output("")
        assert len(results) == 0


class TestGetGitDiff:
    """Test _get_git_diff function."""

    @patch("src.ai_guard.analyzer._run_tool")
    def test_get_git_diff_success(self, mock_run_tool):
        """Test successful git diff."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "diff content"
        mock_run_tool.return_value = mock_result

        result = _get_git_diff()
        assert result == "diff content"

    @patch("src.ai_guard.analyzer._run_tool")
    def test_get_git_diff_failure(self, mock_run_tool):
        """Test git diff failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run_tool.return_value = mock_result

        result = _get_git_diff()
        assert result == ""


class TestGetChangedFiles:
    """Test _get_changed_files function."""

    @patch("src.ai_guard.analyzer._get_git_diff")
    @patch("src.ai_guard.diff_parser.changed_python_files")
    def test_get_changed_files_success(self, mock_changed_files, mock_git_diff):
        """Test successful changed files retrieval."""
        mock_git_diff.return_value = "diff content"
        mock_changed_files.return_value = ["test.py", "test2.py"]

        result = _get_changed_files()
        assert result == ["test.py", "test2.py"]

    @patch("src.ai_guard.analyzer._get_git_diff")
    def test_get_changed_files_no_diff(self, mock_git_diff):
        """Test changed files with no diff."""
        mock_git_diff.return_value = ""

        result = _get_changed_files()
        assert result == []


class TestRunCoverageCheck:
    """Test run_coverage_check function."""

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_coverage_check_success(self, mock_run_tool):
        """Test successful coverage check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name                    Stmts   Miss  Cover\nTOTAL                       10      2    80%"
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_coverage_check(["test.py"], 70)

        assert gate_result.passed is True
        assert gate_result.coverage_percentage == 80

    @patch("src.ai_guard.analyzer._run_tool")
    def test_run_coverage_check_failure(self, mock_run_tool):
        """Test coverage check failure."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name                    Stmts   Miss  Cover\nTOTAL                       10      8    20%"
        mock_run_tool.return_value = mock_result

        gate_result, sarif_result = run_coverage_check(["test.py"], 70)

        assert gate_result.passed is False
        assert gate_result.coverage_percentage == 20

    def test_run_coverage_check_no_files(self):
        """Test coverage check with no files."""
        gate_result, sarif_result = run_coverage_check([], 70)
        assert gate_result.passed is True


class TestAnalysisConfig:
    """Test AnalysisConfig dataclass."""

    def test_analysis_config_default(self):
        """Test default AnalysisConfig creation."""
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True

    def test_analysis_config_custom(self):
        """Test custom AnalysisConfig creation."""
        config = AnalysisConfig(
            enable_security_analysis=False,
            enable_performance_analysis=True,
            enable_quality_analysis=False,
            enable_coverage_analysis=True,
        )
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is False
        assert config.enable_coverage_analysis is True

    def test_analysis_config_from_dict(self):
        """Test AnalysisConfig creation from dictionary."""
        data = {
            "enable_security_analysis": False,
            "enable_performance_analysis": True,
            "enable_quality_analysis": False,
            "enable_coverage_analysis": True,
        }
        config = AnalysisConfig.from_dict(data)
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is False
        assert config.enable_coverage_analysis is True


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""

    def test_analysis_result_default(self):
        """Test default AnalysisResult creation."""
        result = AnalysisResult()
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.execution_time == 0.0

    def test_analysis_result_custom(self):
        """Test custom AnalysisResult creation."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5,
        )
        assert result.security_issues == ["issue1"]
        assert result.performance_issues == ["issue2"]
        assert result.quality_issues == ["issue3"]
        assert result.coverage_data == {"file1": 85.0}
        assert result.execution_time == 1.5

    def test_analysis_result_to_dict(self):
        """Test AnalysisResult to_dict method."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5,
        )
        data = result.to_dict()
        assert data["security_issues"] == ["issue1"]
        assert data["performance_issues"] == ["issue2"]
        assert data["quality_issues"] == ["issue3"]
        assert data["coverage_data"] == {"file1": 85.0}
        assert data["execution_time"] == 1.5


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_security_analyzer_init(self):
        """Test SecurityAnalyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.name == "Security Analyzer"

    def test_security_analyzer_analyze(self):
        """Test SecurityAnalyzer analyze method."""
        analyzer = SecurityAnalyzer()
        result = analyzer.analyze("test.py")
        assert isinstance(result, AnalysisResult)


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    def test_performance_analyzer_init(self):
        """Test PerformanceAnalyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.name == "Performance Analyzer"

    def test_performance_analyzer_analyze(self):
        """Test PerformanceAnalyzer analyze method."""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze("test.py")
        assert isinstance(result, AnalysisResult)


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""

    def test_quality_analyzer_init(self):
        """Test QualityAnalyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.name == "Quality Analyzer"

    def test_quality_analyzer_analyze(self):
        """Test QualityAnalyzer analyze method."""
        analyzer = QualityAnalyzer()
        result = analyzer.analyze("test.py")
        assert isinstance(result, AnalysisResult)


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_coverage_analyzer_init(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.name == "Coverage Analyzer"

    def test_coverage_analyzer_analyze(self):
        """Test CoverageAnalyzer analyze method."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze("test.py")
        assert isinstance(result, AnalysisResult)


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_init(self):
        """Test CodeAnalyzer initialization."""
        analyzer = CodeAnalyzer()
        assert analyzer.name == "Code Analyzer"

    def test_code_analyzer_analyze(self):
        """Test CodeAnalyzer analyze method."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze("test.py")
        assert isinstance(result, AnalysisResult)

    def test_code_analyzer_analyze_with_config(self):
        """Test CodeAnalyzer analyze method with config."""
        analyzer = CodeAnalyzer()
        config = AnalysisConfig()
        result = analyzer.analyze("test.py", config)
        assert isinstance(result, AnalysisResult)


class TestAnalyzeFilesParallel:
    """Test analyze_files_parallel function."""

    def test_analyze_files_parallel_empty(self):
        """Test analyze_files_parallel with empty list."""
        results = analyze_files_parallel([])
        assert results == []

    def test_analyze_files_parallel_with_files(self):
        """Test analyze_files_parallel with files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                results = analyze_files_parallel([f.name])
                assert len(results) == 1
                assert isinstance(results[0], AnalysisResult)
            finally:
                os.unlink(f.name)


class TestBenchmarkAnalyzer:
    """Test benchmark_analyzer function."""

    def test_benchmark_analyzer(self):
        """Test benchmark_analyzer function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                stats = benchmark_analyzer([f.name], iterations=2)
                assert "avg_execution_time" in stats
                assert "min_execution_time" in stats
                assert "max_execution_time" in stats
            finally:
                os.unlink(f.name)


class TestAnalyzeCode:
    """Test analyze_code function."""

    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                result = analyze_code(f.name)
                assert isinstance(result, AnalysisResult)
            finally:
                os.unlink(f.name)


class TestAnalyzeSecurity:
    """Test analyze_security function."""

    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                issues = analyze_security(f.name)
                assert isinstance(issues, list)
            finally:
                os.unlink(f.name)


class TestAnalyzePerformance:
    """Test analyze_performance function."""

    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                issues = analyze_performance(f.name)
                assert isinstance(issues, list)
            finally:
                os.unlink(f.name)


class TestAnalyzeQuality:
    """Test analyze_quality function."""

    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                issues = analyze_quality(f.name)
                assert isinstance(issues, list)
            finally:
                os.unlink(f.name)


class TestAnalyzeCoverage:
    """Test analyze_coverage function."""

    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                coverage = analyze_coverage(f.name)
                assert isinstance(coverage, dict)
            finally:
                os.unlink(f.name)


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report_json(self):
        """Test generate_report with JSON format."""
        result = AnalysisResult()
        report = generate_report(result, "json")
        assert isinstance(report, str)

    def test_generate_report_html(self):
        """Test generate_report with HTML format."""
        result = AnalysisResult()
        report = generate_report(result, "html")
        assert isinstance(report, str)

    def test_generate_report_sarif(self):
        """Test generate_report with SARIF format."""
        result = AnalysisResult()
        report = generate_report(result, "sarif")
        assert isinstance(report, str)


class TestRunAnalysis:
    """Test run_analysis function."""

    def test_run_analysis(self):
        """Test run_analysis function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)
                assert isinstance(result, AnalysisResult)
            finally:
                os.unlink(f.name)


class TestMain:
    """Test main function."""

    @patch("sys.argv", ["ai-guard", "--help"])
    def test_main_help(self):
        """Test main function with help."""
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["ai-guard"])
    def test_main_no_args(self):
        """Test main function with no args."""
        main()  # Should not raise exception
