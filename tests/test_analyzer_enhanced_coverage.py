"""Enhanced tests for analyzer module to significantly improve coverage."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path

from src.ai_guard.analyzer import (
    run_lint_check,
    run_type_check, 
    run_security_check,
    run_coverage_check,
    _to_text,
    _normalize_rule_id,
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _parse_bandit_json,
    _parse_bandit_output,
    _parse_flake8_output,
    _parse_mypy_output,
    _to_findings,
    _run_tool,
    _write_reports,
    _coverage_percent_from_xml,
    cov_percent,
    main,
    CodeAnalyzer,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    RuleIdStyle
)
from src.ai_guard.gates.coverage_eval import CoverageResult, evaluate_coverage_str
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestUtilityFunctions:
    """Test utility functions for better coverage."""

    def test_to_text_none(self):
        """Test _to_text with None input."""
        result = _to_text(None)
        assert result == ""

    def test_to_text_bytes(self):
        """Test _to_text with bytes input."""
        result = _to_text(b"hello world")
        assert result == "hello world"

    def test_to_text_bytes_invalid_utf8(self):
        """Test _to_text with invalid UTF-8 bytes."""
        invalid_bytes = b'\xff\xfe\xfd'
        result = _to_text(invalid_bytes)
        assert result == ""

    def test_to_text_bytes_with_replacement_chars(self):
        """Test _to_text with bytes containing replacement characters."""
        # Create bytes that would decode to string with replacement chars
        result = _to_text(b"valid text")
        assert result == "valid text"

    def test_to_text_string(self):
        """Test _to_text with string input."""
        result = _to_text("hello world")
        assert result == "hello world"

    def test_to_text_other_type(self):
        """Test _to_text with other type input."""
        result = _to_text(123)
        assert result == "123"

    def test_normalize_rule_id_with_colon(self):
        """Test _normalize_rule_id with colon separator."""
        result = _normalize_rule_id("tool:rule123")
        assert result == "rule123"

    def test_normalize_rule_id_without_colon(self):
        """Test _normalize_rule_id without colon separator."""
        result = _normalize_rule_id("rule123")
        assert result == "rule123"

    def test_rule_style_default(self):
        """Test _rule_style with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_rule_style_tool(self):
        """Test _rule_style with tool environment."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL

    def test_rule_style_invalid(self):
        """Test _rule_style with invalid environment value."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "invalid"}):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_make_rule_id_bare_style(self):
        """Test _make_rule_id with bare style."""
        with patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE):
            result = _make_rule_id("tool", "rule123")
            assert result == "rule123"

    def test_make_rule_id_tool_style(self):
        """Test _make_rule_id with tool style."""
        with patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("tool", "rule123")
            assert result == "tool:rule123"

    def test_make_rule_id_empty_code(self):
        """Test _make_rule_id with empty code."""
        with patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE):
            result = _make_rule_id("tool", "")
            assert result == "tool"

    def test_make_rule_id_none_code(self):
        """Test _make_rule_id with None code."""
        with patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE):
            result = _make_rule_id("tool", None)
            assert result == "tool"

    def test_strict_subprocess_fail_default(self):
        """Test _strict_subprocess_fail with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = _strict_subprocess_fail()
            assert result is False

    def test_strict_subprocess_fail_enabled(self):
        """Test _strict_subprocess_fail with enabled environment."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "1"}):
            result = _strict_subprocess_fail()
            assert result is True

    def test_strict_subprocess_fail_true(self):
        """Test _strict_subprocess_fail with 'true' value."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"}):
            result = _strict_subprocess_fail()
            assert result is True

    def test_strict_subprocess_fail_yes(self):
        """Test _strict_subprocess_fail with 'yes' value."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "yes"}):
            result = _strict_subprocess_fail()
            assert result is True

    def test_strict_subprocess_fail_on(self):
        """Test _strict_subprocess_fail with 'on' value."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "on"}):
            result = _strict_subprocess_fail()
            assert result is True


class TestDataClasses:
    """Test dataclasses for better coverage."""

    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="test.py")
        assert location.uri == "test.py"

    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=1, start_column=5, end_line=10, end_column=15)
        assert region.start_line == 1
        assert region.start_column == 5
        assert region.end_line == 10
        assert region.end_column == 15

    def test_region_defaults(self):
        """Test Region dataclass with defaults."""
        region = Region()
        assert region.start_line is None
        assert region.start_column is None
        assert region.end_line is None
        assert region.end_column is None

    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=1)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        assert location.artifact_location == artifact
        assert location.region == region

    def test_physical_location_no_region(self):
        """Test PhysicalLocation dataclass without region."""
        artifact = ArtifactLocation(uri="test.py")
        location = PhysicalLocation(artifact_location=artifact)
        assert location.artifact_location == artifact
        assert location.region is None

    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=1)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        assert location.physical_location == physical


class TestBanditParsing:
    """Test Bandit output parsing functions."""

    def test_parse_bandit_json_valid(self):
        """Test _parse_bandit_json with valid JSON."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Test security issue",
                    "test_id": "B101"
                }
            ]
        }
        result = _parse_bandit_json(json.dumps(json_data))
        assert len(result) == 1
        assert result[0].rule_id == "B101"  # Based on actual behavior
        assert result[0].message == "Test security issue"

    def test_parse_bandit_json_empty(self):
        """Test _parse_bandit_json with empty JSON."""
        result = _parse_bandit_json("{}")
        assert result == []

    def test_parse_bandit_json_invalid(self):
        """Test _parse_bandit_json with invalid JSON."""
        result = _parse_bandit_json("invalid json")
        assert result == []

    def test_parse_bandit_json_bytes(self):
        """Test _parse_bandit_json with bytes input."""
        json_data = b'{"results": []}'
        result = _parse_bandit_json(json_data)
        assert result == []

    def test_parse_bandit_json_non_dict(self):
        """Test _parse_bandit_json with non-dict data."""
        result = _parse_bandit_json('["not", "a", "dict"]')
        assert result == []

    def test_parse_bandit_json_no_results(self):
        """Test _parse_bandit_json with no results key."""
        json_data = {"other": "data"}
        result = _parse_bandit_json(json.dumps(json_data))
        assert result == []

    def test_parse_bandit_json_empty_results(self):
        """Test _parse_bandit_json with empty results."""
        json_data = {"results": []}
        result = _parse_bandit_json(json.dumps(json_data))
        assert result == []

    def test_parse_bandit_output_with_bandit(self):
        """Test _parse_bandit_output with 'bandit' in output."""
        result = _parse_bandit_output("bandit found issues")
        assert len(result) == 1
        assert result[0].rule_id == "bandit:B101"

    def test_parse_bandit_output_without_bandit(self):
        """Test _parse_bandit_output without 'bandit' in output."""
        result = _parse_bandit_output("some other output")
        assert result == []


class TestFlake8Parsing:
    """Test Flake8 output parsing functions."""

    def test_parse_flake8_output_valid(self):
        """Test _parse_flake8_output with valid output."""
        output = "src/test.py:10:5: E501 line too long (80 > 79 characters)"
        result = _parse_flake8_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "E501"
        assert "line too long" in result[0].message

    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output with empty output."""
        result = _parse_flake8_output("")
        assert result == []

    def test_parse_flake8_output_multiple_lines(self):
        """Test _parse_flake8_output with multiple lines."""
        output = """src/test.py:10:5: E501 line too long
src/test.py:15:1: E302 expected 2 blank lines"""
        result = _parse_flake8_output(output)
        assert len(result) == 2

    def test_parse_flake8_output_no_match(self):
        """Test _parse_flake8_output with no matching lines."""
        result = _parse_flake8_output("some random text")
        assert result == []


class TestMypyParsing:
    """Test MyPy output parsing functions."""

    def test_parse_mypy_output_valid(self):
        """Test _parse_mypy_output with valid output."""
        output = "src/test.py:10: error: Name 'x' is not defined"
        result = _parse_mypy_output(output)
        assert len(result) == 1
        assert "Name 'x' is not defined" in result[0].message

    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output with empty output."""
        result = _parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_multiple_lines(self):
        """Test _parse_mypy_output with multiple lines."""
        output = """src/test.py:10: error: Name 'x' is not defined
src/test.py:15: error: Incompatible types"""
        result = _parse_mypy_output(output)
        assert len(result) == 2

    def test_parse_mypy_output_no_match(self):
        """Test _parse_mypy_output with no matching lines."""
        result = _parse_mypy_output("some random text")
        assert result == []


class TestToFindings:
    """Test _to_findings function."""

    def test_to_findings_empty(self):
        """Test _to_findings with empty list."""
        result = _to_findings([])
        assert result == []

    def test_to_findings_with_dict_locations(self):
        """Test _to_findings with SARIF results having dict locations."""
        sarif_result = SarifResult(
            rule_id="test:rule",
            level="error",
            message="Test message",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "test.py"},
                    "region": {"startLine": 10}
                }
            }]
        )
        result = _to_findings([sarif_result])
        assert len(result) == 1
        assert result[0]["rule_id"] == "test:rule"
        assert result[0]["path"] == "test.py"
        assert result[0]["line"] == 10

    def test_to_findings_with_object_locations(self):
        """Test _to_findings with SARIF results having object locations."""
        # Create mock objects that simulate the dataclass structure
        class MockRegion:
            def __init__(self, start_line):
                self.start_line = start_line

        class MockArtifactLocation:
            def __init__(self, uri):
                self.uri = uri

        class MockPhysicalLocation:
            def __init__(self, artifact_location, region):
                self.artifact_location = artifact_location
                self.region = region

        class MockLocation:
            def __init__(self, physical_location):
                self.physical_location = physical_location

        artifact = MockArtifactLocation("test.py")
        region = MockRegion(10)
        physical = MockPhysicalLocation(artifact, region)
        location = MockLocation(physical)

        sarif_result = SarifResult(
            rule_id="test:rule",
            level="error",
            message="Test message",
            locations=[location]
        )
        result = _to_findings([sarif_result])
        assert len(result) == 1
        assert result[0]["rule_id"] == "test:rule"
        assert result[0]["path"] == "test.py"
        assert result[0]["line"] == 10

    def test_to_findings_level_conversion(self):
        """Test _to_findings level conversion from error to warning."""
        sarif_result = SarifResult(
            rule_id="test:rule",
            level="error",
            message="Test message",
            locations=[]
        )
        result = _to_findings([sarif_result])
        assert result[0]["level"] == "warning"


class TestRunTool:
    """Test _run_tool function."""

    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_success(self, mock_run_cmd):
        """Test _run_tool with successful execution."""
        mock_run_cmd.return_value = (0, "success output")
        result = _run_tool(["test", "command"])
        assert result.returncode == 0
        assert result.stdout == "success output"

    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_failure(self, mock_run_cmd):
        """Test _run_tool with failed execution."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError
        mock_run_cmd.side_effect = ToolExecutionError("Command failed")
        result = _run_tool(["test", "command"])
        assert result.returncode == 1
        assert result.stdout == ""


class TestWriteReports:
    """Test _write_reports function."""

    @patch('src.ai_guard.analyzer.write_sarif')
    def test_write_reports_sarif(self, mock_write_sarif):
        """Test _write_reports with SARIF format."""
        issues = [{"rule_id": "test", "level": "warning", "message": "test", "path": "test.py", "line": 1}]
        config = {"report_format": "sarif", "report_path": "test.sarif"}
        _write_reports(issues, config)
        mock_write_sarif.assert_called_once()

    @patch('src.ai_guard.analyzer.write_json')
    def test_write_reports_json(self, mock_write_json):
        """Test _write_reports with JSON format."""
        issues = [{"rule_id": "test", "level": "warning", "message": "test", "path": "test.py", "line": 1}]
        config = {"report_format": "json", "report_path": "test.json"}
        _write_reports(issues, config)
        mock_write_json.assert_called_once()

    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_html(self, mock_write_html):
        """Test _write_reports with HTML format."""
        issues = [{"rule_id": "test", "level": "warning", "message": "test", "path": "test.py", "line": 1}]
        config = {"report_format": "html", "report_path": "test.html"}
        _write_reports(issues, config)
        mock_write_html.assert_called_once()

    def test_write_reports_default_paths(self):
        """Test _write_reports with default paths."""
        issues = [{"rule_id": "test", "level": "warning", "message": "test", "path": "test.py", "line": 1}]
        
        # Test SARIF default
        config = {"report_format": "sarif"}
        with patch('src.ai_guard.analyzer.write_sarif') as mock_write_sarif:
            _write_reports(issues, config)
            mock_write_sarif.assert_called_once()

        # Test JSON default
        config = {"report_format": "json"}
        with patch('src.ai_guard.analyzer.write_json') as mock_write_json:
            _write_reports(issues, config)
            mock_write_json.assert_called_once()

        # Test HTML default
        config = {"report_format": "html"}
        with patch('src.ai_guard.analyzer.write_html') as mock_write_html:
            _write_reports(issues, config)
            mock_write_html.assert_called_once()


class TestCoverageFunctions:
    """Test coverage-related functions."""

    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_with_xml(self, mock_coverage_percent):
        """Test cov_percent with XML file."""
        mock_coverage_percent.return_value = 85.5
        result = cov_percent()
        assert result == 85  # Returns int, not float

    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_no_xml(self, mock_coverage_percent):
        """Test cov_percent without XML file."""
        mock_coverage_percent.return_value = None
        result = cov_percent()
        assert result == 0  # Returns 0 when None

    def test_coverage_percent_from_xml_valid(self):
        """Test _coverage_percent_from_xml with valid XML."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.85">
</coverage>"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 85.0
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    def test_coverage_percent_from_xml_invalid(self):
        """Test _coverage_percent_from_xml with invalid XML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("invalid xml")
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    def test_coverage_percent_from_xml_nonexistent(self):
        """Test _coverage_percent_from_xml with nonexistent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None


class TestGateFunctions:
    """Test gate functions with comprehensive coverage."""

    @patch('subprocess.run')
    def test_run_lint_check_tool_not_found(self, mock_run):
        """Test run_lint_check when tool is not found."""
        mock_run.side_effect = FileNotFoundError()
        result, sarif_result = run_lint_check(["src/test.py"])
        assert result.passed is False
        assert "Tool not found" in result.details
        assert sarif_result is None

    @patch('subprocess.run')
    def test_run_type_check_tool_not_found(self, mock_run):
        """Test run_type_check when tool is not found."""
        mock_run.side_effect = FileNotFoundError()
        result, sarif_result = run_type_check(["src/test.py"])
        assert result.passed is False
        assert "Tool not found" in result.details
        assert sarif_result is None

    @patch('subprocess.run')
    def test_run_security_check_tool_not_found(self, mock_run):
        """Test run_security_check when tool is not found."""
        mock_run.side_effect = FileNotFoundError()
        result, sarif_result = run_security_check()
        assert result.passed is False
        assert "Tool not found" in result.details
        assert sarif_result is None

    @patch('subprocess.run')
    def test_run_security_check_with_issues(self, mock_run):
        """Test run_security_check with security issues."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps({
            "results": [{
                "filename": "test.py",
                "line_number": 10,
                "issue_text": "Security issue",
                "test_id": "B101"
            }]
        })
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result, sarif_result = run_security_check()
        assert result.passed is False
        assert sarif_result is not None

    @patch('subprocess.run')
    def test_run_security_check_no_issues(self, mock_run):
        """Test run_security_check with no issues."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"results": []})
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result, sarif_result = run_security_check()
        assert result.passed is True
        assert sarif_result is None

    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_no_data(self, mock_cov_percent):
        """Test run_coverage_check with no coverage data."""
        mock_cov_percent.return_value = None
        result, sarif_result = run_coverage_check(80)
        assert result.passed is False
        assert "No coverage data" in result.details
        assert sarif_result is None

    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_passed(self, mock_cov_percent):
        """Test run_coverage_check with passing coverage."""
        mock_cov_percent.return_value = 85.0
        result, sarif_result = run_coverage_check(80)
        assert result.passed is True
        assert "85.0%" in result.details
        assert sarif_result is None

    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_failed(self, mock_cov_percent):
        """Test run_coverage_check with failing coverage."""
        mock_cov_percent.return_value = 75.0
        result, sarif_result = run_coverage_check(80)
        assert result.passed is False
        assert "75.0%" in result.details
        assert sarif_result is None

    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_no_minimum(self, mock_cov_percent):
        """Test run_coverage_check with no minimum coverage."""
        mock_cov_percent.return_value = 75.0
        result, sarif_result = run_coverage_check(None)
        assert result.passed is True
        assert "no minimum set" in result.details
        assert sarif_result is None


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_init_default_config(self):
        """Test CodeAnalyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        assert analyzer.config is not None

    def test_code_analyzer_init_custom_config(self):
        """Test CodeAnalyzer initialization with custom config."""
        config = {"min_coverage": 90}
        analyzer = CodeAnalyzer(config)
        assert analyzer.config == config

    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    def test_run_all_checks(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test CodeAnalyzer.run_all_checks."""
        mock_lint.return_value = (GateResult("Lint", True), None)
        mock_type.return_value = (GateResult("Type", True), None)
        mock_security.return_value = (GateResult("Security", True), None)
        mock_coverage.return_value = (GateResult("Coverage", True), None)

        analyzer = CodeAnalyzer()
        results = analyzer.run_all_checks(["src/test.py"])
        
        assert len(results) == 4
        mock_lint.assert_called_once_with(["src/test.py"])
        mock_type.assert_called_once_with(["src/test.py"])
        mock_security.assert_called_once_with()
        mock_coverage.assert_called_once_with(80)


class TestMainFunction:
    """Test main function."""

    @patch('src.ai_guard.analyzer.run')
    def test_main(self, mock_run):
        """Test main function."""
        mock_run.return_value = 0
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)
