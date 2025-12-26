"""Comprehensive tests for analyzer_optimized.py to achieve 80% coverage."""

import pytest
import os
import json
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import xml.etree.ElementTree as ET

from src.ai_guard.analyzer_optimized import (
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
    _run_subprocess_optimized,
    run_lint_check,
    run_type_check,
    _parse_bandit_json,
    _process_bandit_data,
    _parse_bandit_output,
    run_security_check,
    _to_findings,
    run_coverage_check,
    _run_quality_checks_parallel,
    run,
    main,
    OptimizedCodeAnalyzer,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    default_gates,
)


class TestRuleIdHelpers:
    """Test rule ID helper functions."""

    def test_rule_id_style_enum(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"

    def test_rule_style_default(self):
        """Test default rule style."""
        with patch.dict(os.environ, {}, clear=True):
            assert _rule_style() == RuleIdStyle.BARE

    def test_rule_style_tool(self):
        """Test tool rule style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            assert _rule_style() == RuleIdStyle.TOOL

    def test_rule_style_bare(self):
        """Test bare rule style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"}):
            assert _rule_style() == RuleIdStyle.BARE

    def test_rule_style_invalid(self):
        """Test invalid rule style defaults to bare."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "invalid"}):
            assert _rule_style() == RuleIdStyle.BARE

    def test_make_rule_id_bare_style(self):
        """Test making rule ID with bare style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"}):
            assert _make_rule_id("flake8", "E501") == "E501"
            assert _make_rule_id("flake8", None) == "flake8"
            assert _make_rule_id("flake8", "") == "flake8"

    def test_make_rule_id_tool_style(self):
        """Test making rule ID with tool style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            assert _make_rule_id("flake8", "E501") == "flake8:E501"
            assert _make_rule_id("flake8", None) == "flake8:flake8"
            assert _make_rule_id("flake8", "") == "flake8:flake8"

    def test_strict_subprocess_fail_default(self):
        """Test default strict subprocess fail behavior."""
        with patch.dict(os.environ, {}, clear=True):
            assert _strict_subprocess_fail() is False

    def test_strict_subprocess_fail_true(self):
        """Test strict subprocess fail enabled."""
        for value in ["1", "true", "yes", "on"]:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                assert _strict_subprocess_fail() is True

    def test_strict_subprocess_fail_false(self):
        """Test strict subprocess fail disabled."""
        for value in ["0", "false", "no", "off", "invalid"]:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                assert _strict_subprocess_fail() is False

    def test_to_text_none(self):
        """Test _to_text with None."""
        assert _to_text(None) == ""

    def test_to_text_bytes(self):
        """Test _to_text with bytes."""
        assert _to_text(b"hello") == "hello"
        assert _to_text(bytearray(b"world")) == "world"

    def test_to_text_string(self):
        """Test _to_text with string."""
        assert _to_text("hello") == "hello"

    def test_to_text_other(self):
        """Test _to_text with other types."""
        assert _to_text(123) == "123"
        assert _to_text([1, 2, 3]) == "[1, 2, 3]"

    def test_normalize_rule_id_with_colon(self):
        """Test normalizing rule ID with colon."""
        assert _normalize_rule_id("flake8:E501") == "E501"
        assert _normalize_rule_id("mypy:name-defined") == "name-defined"

    def test_normalize_rule_id_without_colon(self):
        """Test normalizing rule ID without colon."""
        assert _normalize_rule_id("E501") == "E501"
        assert _normalize_rule_id("name-defined") == "name-defined"

    def test_norm_none(self):
        """Test _norm with None."""
        assert _norm(None) == ""

    def test_norm_bytes(self):
        """Test _norm with bytes."""
        assert _norm(b"hello") == "hello"
        assert _norm(bytearray(b"world")) == "world"

    def test_norm_string(self):
        """Test _norm with string."""
        assert _norm("hello") == "hello"


class TestCoverageParsing:
    """Test coverage parsing functions."""

    def test_coverage_percent_from_xml_none_path(self):
        """Test coverage parsing with None path."""
        # Mock os.path.exists to return False for coverage files
        with patch("os.path.exists", return_value=False):
            result = _coverage_percent_from_xml(None)
            assert result is None

    def test_coverage_percent_from_xml_nonexistent_file(self):
        """Test coverage parsing with non-existent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None

    def test_coverage_percent_from_xml_cobertura_style(self):
        """Test coverage parsing with Cobertura style XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                '<?xml version="1.0"?><coverage line-rate="0.86" branch-rate="0.75"></coverage>'
            )
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 86
            finally:
                try:
                    os.unlink(f.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows

    def test_coverage_percent_from_xml_counter_style(self):
        """Test coverage parsing with counter style XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
            <coverage>
                <counter type="LINE" covered="80" missed="20"/>
                <counter type="BRANCH" covered="10" missed="5"/>
            </coverage>"""
            )
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 80  # 80/(80+20) * 100
            finally:
                try:
                    os.unlink(f.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows

    def test_coverage_percent_from_xml_invalid_line_rate(self):
        """Test coverage parsing with invalid line rate."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write('<?xml version="1.0"?><coverage line-rate="invalid"></coverage>')
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None  # Invalid line rate, no counters, so None
            finally:
                try:
                    os.unlink(f.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows

    def test_coverage_percent_from_xml_no_counters(self):
        """Test coverage parsing with no counters."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write('<?xml version="1.0"?><coverage></coverage>')
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                try:
                    os.unlink(f.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows

    def test_coverage_percent_from_xml_exception(self):
        """Test coverage parsing with exception."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("invalid xml content")
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                try:
                    os.unlink(f.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows

    def test_cov_percent_success(self):
        """Test cov_percent with successful parsing."""
        with patch(
            "src.ai_guard.analyzer_optimized._coverage_percent_from_xml",
            return_value=85,
        ):
            assert cov_percent() == 85

    def test_cov_percent_none(self):
        """Test cov_percent with None result."""
        with patch(
            "src.ai_guard.analyzer_optimized._coverage_percent_from_xml",
            return_value=None,
        ):
            assert cov_percent() == 0


class TestLintParsing:
    """Test lint parsing functions."""

    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        result = _parse_flake8_output("")
        assert result == []

    def test_parse_flake8_output_none(self):
        """Test parsing None flake8 output."""
        result = _parse_flake8_output(None)
        assert result == []

    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        output = "src/test.py:10:5: E501 line too long (80 > 79 characters)"
        results = _parse_flake8_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "E501"  # Default bare style
        assert result.message == "line too long (80 > 79 characters)"
        assert result.level == "warning"
        assert len(result.locations) == 1
        assert (
            result.locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test.py"
        )
        assert result.locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert result.locations[0]["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_flake8_output_multiple_lines(self):
        """Test parsing multiple flake8 output lines."""
        output = """src/test.py:10:5: E501 line too long
src/test.py:15:1: E302 expected 2 blank lines
src/test2.py:5:10: W291 trailing whitespace"""
        results = _parse_flake8_output(output)

        assert len(results) == 3
        assert results[0].rule_id == "E501"
        assert results[1].rule_id == "E302"
        assert results[2].rule_id == "W291"

    def test_parse_flake8_output_invalid_format(self):
        """Test parsing invalid flake8 output format."""
        output = "invalid format line"
        results = _parse_flake8_output(output)
        assert results == []

    def test_parse_flake8_output_mixed_valid_invalid(self):
        """Test parsing mixed valid and invalid flake8 output."""
        output = """src/test.py:10:5: E501 line too long
invalid format line
src/test.py:15:1: E302 expected 2 blank lines"""
        results = _parse_flake8_output(output)

        assert len(results) == 2
        assert results[0].rule_id == "E501"
        assert results[1].rule_id == "E302"

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        result = _parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_none(self):
        """Test parsing None mypy output."""
        result = _parse_mypy_output(None)
        assert result == []

    def test_parse_mypy_output_with_code(self):
        """Test parsing mypy output with bracketed code."""
        output = "src/test.py:10: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "name-defined"  # Bare format for bracketed codes
        assert result.message == "Name 'x' is not defined"
        assert result.level == "error"
        assert len(result.locations) == 1
        assert (
            result.locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test.py"
        )
        assert result.locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert result.locations[0]["physicalLocation"]["region"]["startColumn"] is None

    def test_parse_mypy_output_with_column(self):
        """Test parsing mypy output with column."""
        output = "src/test.py:10:5: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.locations[0]["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_mypy_output_without_code(self):
        """Test parsing mypy output without bracketed code."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            output = "src/test.py:10: error: Name 'x' is not defined"
            results = _parse_mypy_output(output)

            assert len(results) == 1
            result = results[0]
            assert result.rule_id == "mypy:mypy-error"  # Tool format for no code

    def test_parse_mypy_output_warning(self):
        """Test parsing mypy warning output."""
        output = "src/test.py:10: warning: Unused import [unused-import]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.level == "warning"

    def test_parse_mypy_output_ignore_info(self):
        """Test parsing mypy output ignores info level."""
        output = "src/test.py:10: info: Some info message"
        results = _parse_mypy_output(output)
        assert results == []

    def test_parse_mypy_output_invalid_format(self):
        """Test parsing invalid mypy output format."""
        output = "invalid format line"
        results = _parse_mypy_output(output)
        assert results == []

    def test_parse_mypy_output_multiple_lines(self):
        """Test parsing multiple mypy output lines."""
        output = """src/test.py:10: error: Name 'x' is not defined [name-defined]
src/test.py:15: warning: Unused import [unused-import]
src/test2.py:5: error: Missing return statement [return]"""
        results = _parse_mypy_output(output)

        assert len(results) == 3
        assert results[0].rule_id == "name-defined"
        assert results[1].rule_id == "unused-import"
        assert results[2].rule_id == "return"


class TestSubprocessRunner:
    """Test subprocess runner functions."""

    @patch("src.ai_guard.utils.subprocess_runner.run_cmd")
    def test_run_subprocess_optimized_success(self, mock_run_cmd):
        """Test successful subprocess execution."""
        mock_run_cmd.return_value = (0, "success output")

        result = _run_subprocess_optimized(["echo", "test"])

        assert result.returncode == 0
        assert result.stdout == "success output"
        assert result.stderr == ""
        mock_run_cmd.assert_called_once_with(["echo", "test"], timeout=30)

    @patch("src.ai_guard.utils.subprocess_runner.run_cmd")
    def test_run_subprocess_optimized_error(self, mock_run_cmd):
        """Test subprocess execution with error."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError

        mock_run_cmd.side_effect = ToolExecutionError("Command failed")

        result = _run_subprocess_optimized(["invalid", "command"])

        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "Command failed"

    @patch("src.ai_guard.utils.subprocess_runner.run_cmd")
    def test_run_subprocess_optimized_custom_timeout(self, mock_run_cmd):
        """Test subprocess execution with custom timeout."""
        mock_run_cmd.return_value = (0, "output")

        _run_subprocess_optimized(["echo", "test"], timeout=60)

        mock_run_cmd.assert_called_once_with(["echo", "test"], timeout=60)


class TestQualityChecks:
    """Test quality check functions."""

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_lint_check(["src/test.py"])

        assert gate_result.passed is True
        assert gate_result.name == "Lint (flake8)"
        assert "No issues" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_lint_check_with_issues(self, mock_run):
        """Test lint check with issues."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = "src/test.py:10:5: E501 line too long"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_lint_check(["src/test.py"])

        assert gate_result.passed is False
        assert gate_result.name == "Lint (flake8)"
        assert sarif_result is not None
        assert sarif_result.rule_id == "E501"

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_lint_check_command_not_found(self, mock_run):
        """Test lint check when command not found."""
        mock_proc = Mock()
        mock_proc.returncode = 127
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_lint_check(["src/test.py"])

        assert gate_result.passed is False
        assert gate_result.name == "Lint (flake8)"
        assert "flake8 not found" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_lint_check_tool_error(self, mock_run):
        """Test lint check with tool error."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "flake8 error message"
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_lint_check(["src/test.py"])

        assert gate_result.passed is False
        assert gate_result.name == "Lint (flake8)"
        assert "flake8 error: flake8 error message" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_type_check(["src/test.py"])

        assert gate_result.passed is True
        assert gate_result.name == "Static types (mypy)"
        assert "No issues" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_type_check_with_issues(self, mock_run):
        """Test type check with issues."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = (
            "src/test.py:10: error: Name 'x' is not defined [name-defined]"
        )
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_type_check(["src/test.py"])

        assert gate_result.passed is False
        assert gate_result.name == "Static types (mypy)"
        assert sarif_result is not None
        assert sarif_result.rule_id == "name-defined"

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_type_check_command_not_found(self, mock_run):
        """Test type check when command not found."""
        mock_proc = Mock()
        mock_proc.returncode = 127
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_type_check(["src/test.py"])

        assert gate_result.passed is False
        assert gate_result.name == "Static types (mypy)"
        assert "mypy not found" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_type_check_tool_error(self, mock_run):
        """Test type check with tool error."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "mypy error message"
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_type_check(["src/test.py"])

        assert gate_result.passed is False
        assert gate_result.name == "Static types (mypy)"
        assert "mypy error: mypy error message" in gate_result.details
        assert sarif_result is None


class TestSecurityParsing:
    """Test security parsing functions."""

    def test_parse_bandit_json_string(self):
        """Test parsing bandit JSON from string."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 10,
                    "issue_text": "Use of hardcoded password",
                    "test_id": "B105",
                }
            ]
        }
        results = _parse_bandit_json(json.dumps(json_data))

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "B105"  # Default bare style
        assert result.message == "Use of hardcoded password"
        assert result.level == "warning"
        assert len(result.locations) == 1
        assert (
            result.locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test.py"
        )
        assert result.locations[0]["physicalLocation"]["region"]["startLine"] == 10

    def test_parse_bandit_json_bytes(self):
        """Test parsing bandit JSON from bytes."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 5,
                    "issue_text": "SQL injection vulnerability",
                    "test_name": "B608",
                }
            ]
        }
        results = _parse_bandit_json(json.dumps(json_data).encode())

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "B608"  # Uses test_name when test_id not available

    def test_parse_bandit_json_dict(self):
        """Test parsing bandit JSON from dict."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 15,
                    "issue_text": "Hardcoded secret",
                    "test_id": "B106",
                }
            ]
        }
        results = _parse_bandit_json(json_data)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "B106"

    def test_parse_bandit_json_list(self):
        """Test parsing bandit JSON from list."""
        json_data = [{"invalid": "data"}]
        results = _parse_bandit_json(json_data)
        assert results == []

    def test_parse_bandit_json_invalid_string(self):
        """Test parsing invalid bandit JSON string."""
        results = _parse_bandit_json("invalid json")
        assert results == []

    def test_parse_bandit_json_exception(self):
        """Test parsing bandit JSON with exception."""
        results = _parse_bandit_json(123)  # Non-string, non-dict, non-list
        assert results == []

    def test_parse_bandit_json_empty_results(self):
        """Test parsing bandit JSON with empty results."""
        json_data = {"results": []}
        results = _parse_bandit_json(json_data)
        assert results == []

    def test_parse_bandit_json_no_results(self):
        """Test parsing bandit JSON with no results key."""
        json_data = {"other": "data"}
        results = _parse_bandit_json(json_data)
        assert results == []

    def test_process_bandit_data_invalid(self):
        """Test processing invalid bandit data."""
        results = _process_bandit_data("invalid")
        assert results == []

    def test_parse_bandit_output_alias(self):
        """Test _parse_bandit_output alias."""
        json_data = {"results": []}
        results = _parse_bandit_output(json_data)
        assert results == []

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"results": []}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_security_check()

        assert gate_result.passed is True
        assert gate_result.name == "Security (bandit)"
        assert "No issues" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_security_check_with_issues(self, mock_run):
        """Test security check with issues."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = '{"results": [{"filename": "src/test.py", "line_number": 10, "issue_text": "Hardcoded password", "test_id": "B105"}]}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_security_check()

        assert gate_result.passed is False
        assert gate_result.name == "Security (bandit)"
        assert sarif_result is not None
        assert sarif_result.rule_id == "B105"

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_security_check_command_not_found(self, mock_run):
        """Test security check when command not found."""
        mock_proc = Mock()
        mock_proc.returncode = 127
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_security_check()

        assert gate_result.passed is False
        assert gate_result.name == "Security (bandit)"
        assert "bandit not found" in gate_result.details
        assert sarif_result is None

    @patch("src.ai_guard.analyzer_optimized._run_subprocess_optimized")
    def test_run_security_check_tool_error(self, mock_run):
        """Test security check with tool error."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "bandit error message"
        mock_run.return_value = mock_proc

        gate_result, sarif_result = run_security_check()

        assert gate_result.passed is False
        assert gate_result.name == "Security (bandit)"
        assert "bandit error: bandit error message" in gate_result.details
        assert sarif_result is None


class TestFindingsConversion:
    """Test findings conversion functions."""

    def test_to_findings_empty(self):
        """Test converting empty SARIF results to findings."""
        findings = _to_findings([])
        assert findings == []

    def test_to_findings_with_locations(self):
        """Test converting SARIF results with locations to findings."""
        from src.ai_guard.sarif_report import SarifResult

        sarif_results = [
            SarifResult(
                rule_id="E501",
                level="warning",
                message="Line too long",
                locations=[
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": "src/test.py"},
                            "region": {"startLine": 10, "startColumn": 5},
                        }
                    }
                ],
            )
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 1
        finding = findings[0]
        assert finding["rule_id"] == "E501"
        assert finding["level"] == "warning"
        assert finding["message"] == "Line too long"
        assert finding["path"] == "src/test.py"
        assert finding["line"] == 10

    def test_to_findings_without_locations(self):
        """Test converting SARIF results without locations to findings."""
        from src.ai_guard.sarif_report import SarifResult

        sarif_results = [
            SarifResult(
                rule_id="E501", level="warning", message="Line too long", locations=[]
            )
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 1
        finding = findings[0]
        assert finding["rule_id"] == "E501"
        assert finding["level"] == "warning"
        assert finding["message"] == "Line too long"
        assert finding["path"] == "unknown"
        assert finding["line"] is None

    def test_to_findings_with_object_locations(self):
        """Test converting SARIF results with object locations to findings."""
        from src.ai_guard.sarif_report import SarifResult
        from src.ai_guard.analyzer_optimized import (
            Location,
            PhysicalLocation,
            ArtifactLocation,
            Region,
        )

        # Create object-based location
        artifact_location = ArtifactLocation(uri="src/test.py")
        region = Region(start_line=15, start_column=3)
        physical_location = PhysicalLocation(
            artifact_location=artifact_location, region=region
        )
        location = Location(physical_location=physical_location)

        sarif_results = [
            SarifResult(
                rule_id="E302",
                level="error",
                message="Expected 2 blank lines",
                locations=[location],
            )
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 1
        finding = findings[0]
        assert finding["rule_id"] == "E302"
        assert finding["level"] == "error"
        assert finding["message"] == "Expected 2 blank lines"
        assert finding["path"] == "src/test.py"
        assert finding["line"] == 15


class TestCoverageCheck:
    """Test coverage check functions."""

    @patch("src.ai_guard.analyzer_optimized.cov_percent")
    def test_run_coverage_check_success(self, mock_cov_percent):
        """Test successful coverage check."""
        mock_cov_percent.return_value = 85

        result = run_coverage_check(80)

        assert result.passed is True
        assert result.name == "Coverage"
        assert "85% >= 80%" in result.details

    @patch("src.ai_guard.analyzer_optimized.cov_percent")
    def test_run_coverage_check_failure(self, mock_cov_percent):
        """Test failed coverage check."""
        mock_cov_percent.return_value = 75

        result = run_coverage_check(80)

        assert result.passed is False
        assert result.name == "Coverage"
        assert "75% >= 80%" in result.details

    @patch("src.ai_guard.analyzer_optimized.cov_percent")
    def test_run_coverage_check_no_minimum(self, mock_cov_percent):
        """Test coverage check with no minimum threshold."""
        mock_cov_percent.return_value = 85

        result = run_coverage_check(None)

        assert result.passed is True
        assert result.name == "Coverage"
        assert "85% (no minimum set)" in result.details

    @patch("src.ai_guard.analyzer_optimized.cov_percent")
    def test_run_coverage_check_no_coverage_data(self, mock_cov_percent):
        """Test coverage check with no coverage data."""
        mock_cov_percent.return_value = None

        result = run_coverage_check(80)

        assert result.passed is False
        assert result.name == "Coverage"
        assert "No coverage data" in result.details

    @patch("src.ai_guard.analyzer_optimized.cov_percent")
    def test_run_coverage_check_zero_minimum(self, mock_cov_percent):
        """Test coverage check with zero minimum threshold."""
        mock_cov_percent.return_value = None

        result = run_coverage_check(0)

        assert result.passed is False
        assert result.name == "Coverage"
        assert "No coverage data" in result.details


class TestParallelExecution:
    """Test parallel execution functions."""

    @patch("src.ai_guard.analyzer_optimized.parallel_execute")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    def test_run_quality_checks_parallel_success(
        self, mock_security, mock_type, mock_lint, mock_parallel
    ):
        """Test successful parallel quality checks."""
        from src.ai_guard.report import GateResult
        from src.ai_guard.sarif_report import SarifResult

        # Mock individual check results
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)

        # Mock parallel execution results
        mock_parallel.return_value = [
            (GateResult("Lint", True, "No issues"), None),
            (GateResult("Type", True, "No issues"), None),
            (GateResult("Security", True, "No issues"), None),
        ]

        results, sarif_diagnostics = _run_quality_checks_parallel(["src/test.py"])

        assert len(results) == 3
        assert len(sarif_diagnostics) == 0
        assert all(result.passed for result in results)

    @patch("src.ai_guard.analyzer_optimized.parallel_execute")
    def test_run_quality_checks_parallel_with_issues(self, mock_parallel):
        """Test parallel quality checks with issues."""
        from src.ai_guard.report import GateResult
        from src.ai_guard.sarif_report import SarifResult

        # Mock parallel execution results with issues
        mock_parallel.return_value = [
            (
                GateResult("Lint", False, "E501 line too long"),
                SarifResult("E501", "warning", "Line too long", []),
            ),
            (GateResult("Type", True, "No issues"), None),
            (
                GateResult("Security", False, "B105 hardcoded password"),
                SarifResult("B105", "warning", "Hardcoded password", []),
            ),
        ]

        results, sarif_diagnostics = _run_quality_checks_parallel(["src/test.py"])

        assert len(results) == 3
        assert len(sarif_diagnostics) == 2
        assert results[0].passed is False
        assert results[1].passed is True
        assert results[2].passed is False

    @patch("src.ai_guard.analyzer_optimized.parallel_execute")
    def test_run_quality_checks_parallel_none_results(self, mock_parallel):
        """Test parallel quality checks with None results."""
        mock_parallel.return_value = [None, None, None]

        results, sarif_diagnostics = _run_quality_checks_parallel(["src/test.py"])

        assert len(results) == 0
        assert len(sarif_diagnostics) == 0

    @patch("src.ai_guard.analyzer_optimized.parallel_execute")
    def test_run_quality_checks_parallel_empty_paths(self, mock_parallel):
        """Test parallel quality checks with empty paths."""
        mock_parallel.return_value = []

        results, sarif_diagnostics = _run_quality_checks_parallel([])

        assert len(results) == 0
        assert len(sarif_diagnostics) == 0


class TestMainFunction:
    """Test main function and CLI interface."""

    @patch("src.ai_guard.analyzer_optimized.changed_python_files")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    @patch("src.ai_guard.analyzer_optimized.run_pytest_with_coverage")
    @patch("src.ai_guard.analyzer_optimized.summarize")
    @patch("src.ai_guard.analyzer_optimized.write_sarif")
    def test_run_basic_execution(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_pytest,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
    ):
        """Test basic run execution."""
        from src.ai_guard.report import GateResult

        # Mock dependencies
        mock_changed.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")
        mock_pytest.return_value = 0
        mock_summarize.return_value = 0

        # Test basic execution
        result = run(["--min-cov", "80"])

        assert result == 0
        mock_changed.assert_called_once_with(None)
        mock_lint.assert_called_once()
        mock_type.assert_called_once()
        mock_security.assert_called_once()
        mock_coverage.assert_called_once_with(80)
        mock_pytest.assert_called_once()
        mock_summarize.assert_called_once()
        mock_write_sarif.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.changed_python_files")
    @patch("src.ai_guard.analyzer_optimized._run_quality_checks_parallel")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    @patch("src.ai_guard.analyzer_optimized.run_pytest_with_coverage")
    @patch("src.ai_guard.analyzer_optimized.summarize")
    @patch("src.ai_guard.analyzer_optimized.write_sarif")
    def test_run_parallel_execution(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_pytest,
        mock_coverage,
        mock_parallel,
        mock_changed,
    ):
        """Test parallel execution mode."""
        from src.ai_guard.report import GateResult

        # Mock dependencies
        mock_changed.return_value = ["src/test.py"]
        mock_parallel.return_value = ([GateResult("Test", True, "Passed")], [])
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")
        mock_pytest.return_value = 0
        mock_summarize.return_value = 0

        # Test parallel execution
        result = run(["--parallel", "--min-cov", "80"])

        assert result == 0
        mock_parallel.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.changed_python_files")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    @patch("src.ai_guard.analyzer_optimized.run_pytest_with_coverage")
    @patch("src.ai_guard.analyzer_optimized.summarize")
    @patch("src.ai_guard.analyzer_optimized.write_json")
    def test_run_json_report(
        self,
        mock_write_json,
        mock_summarize,
        mock_pytest,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
    ):
        """Test JSON report generation."""
        from src.ai_guard.report import GateResult

        # Mock dependencies
        mock_changed.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")
        mock_pytest.return_value = 0
        mock_summarize.return_value = 0

        # Test JSON report
        result = run(["--report-format", "json", "--report-path", "test.json"])

        assert result == 0
        mock_write_json.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.changed_python_files")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    @patch("src.ai_guard.analyzer_optimized.run_pytest_with_coverage")
    @patch("src.ai_guard.analyzer_optimized.summarize")
    @patch("src.ai_guard.analyzer_optimized.write_html")
    def test_run_html_report(
        self,
        mock_write_html,
        mock_summarize,
        mock_pytest,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
    ):
        """Test HTML report generation."""
        from src.ai_guard.report import GateResult

        # Mock dependencies
        mock_changed.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")
        mock_pytest.return_value = 0
        mock_summarize.return_value = 0

        # Test HTML report
        result = run(["--report-format", "html", "--report-path", "test.html"])

        assert result == 0
        mock_write_html.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.changed_python_files")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    @patch("src.ai_guard.analyzer_optimized.summarize")
    @patch("src.ai_guard.analyzer_optimized.write_sarif")
    def test_run_skip_tests(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
    ):
        """Test run with skip tests option."""
        from src.ai_guard.report import GateResult

        # Mock dependencies
        mock_changed.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")
        mock_summarize.return_value = 0

        # Test skip tests
        result = run(["--skip-tests", "--min-cov", "80"])

        assert result == 0
        # Should not call pytest

    @patch("src.ai_guard.analyzer_optimized.changed_python_files")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    @patch("src.ai_guard.analyzer_optimized.run_pytest_with_coverage")
    @patch("src.ai_guard.analyzer_optimized.summarize")
    @patch("src.ai_guard.analyzer_optimized.write_sarif")
    def test_run_deprecated_sarif_arg(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_pytest,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
    ):
        """Test run with deprecated --sarif argument."""
        from src.ai_guard.report import GateResult

        # Mock dependencies
        mock_changed.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")
        mock_pytest.return_value = 0
        mock_summarize.return_value = 0

        # Test deprecated --sarif argument
        with patch("sys.stderr") as mock_stderr:
            result = run(["--sarif", "test.sarif", "--min-cov", "80"])

            assert result == 0
            mock_write_sarif.assert_called_once()
            # Check that warning was printed
            mock_stderr.write.assert_called()

    def test_run_invalid_report_format(self):
        """Test run with invalid report format."""
        with patch("sys.exit") as mock_exit:
            run(["--report-format", "invalid"])
            mock_exit.assert_called_once_with(2)

    @patch("src.ai_guard.analyzer_optimized.run")
    def test_main_function(self, mock_run):
        """Test main function."""
        mock_run.return_value = 0

        with patch("sys.exit") as mock_exit:
            main()
            mock_run.assert_called_once()
            mock_exit.assert_called_once_with(0)


class TestOptimizedCodeAnalyzer:
    """Test OptimizedCodeAnalyzer class."""

    def test_init_default_config(self):
        """Test analyzer initialization with default config."""
        analyzer = OptimizedCodeAnalyzer()
        assert analyzer.config is not None

    def test_init_custom_config(self):
        """Test analyzer initialization with custom config."""
        custom_config = {"min_coverage": 90}
        analyzer = OptimizedCodeAnalyzer(custom_config)
        assert analyzer.config == custom_config

    @patch("src.ai_guard.analyzer_optimized._run_quality_checks_parallel")
    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    def test_run_all_checks_parallel(
        self, mock_coverage, mock_security, mock_type, mock_lint, mock_parallel
    ):
        """Test running all checks in parallel."""
        from src.ai_guard.report import GateResult

        # Mock parallel execution
        mock_parallel.return_value = ([GateResult("Test", True, "Passed")], [])
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")

        analyzer = OptimizedCodeAnalyzer()
        results = analyzer.run_all_checks(["src/test.py"], parallel=True)

        assert len(results) == 2  # Parallel results + coverage
        mock_parallel.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.run_lint_check")
    @patch("src.ai_guard.analyzer_optimized.run_type_check")
    @patch("src.ai_guard.analyzer_optimized.run_security_check")
    @patch("src.ai_guard.analyzer_optimized.run_coverage_check")
    def test_run_all_checks_sequential(
        self, mock_coverage, mock_security, mock_type, mock_lint
    ):
        """Test running all checks sequentially."""
        from src.ai_guard.report import GateResult

        # Mock individual checks
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = GateResult("Coverage", True, "85% >= 80%")

        analyzer = OptimizedCodeAnalyzer()
        results = analyzer.run_all_checks(["src/test.py"], parallel=False)

        assert len(results) == 4  # All individual checks + coverage
        mock_lint.assert_called_once_with(["src/test.py"])
        mock_type.assert_called_once_with(["src/test.py"])
        mock_security.assert_called_once()
        mock_coverage.assert_called_once_with(80, None)

    @patch("src.ai_guard.analyzer_optimized.get_performance_summary")
    def test_get_performance_metrics(self, mock_perf):
        """Test getting performance metrics."""
        mock_perf.return_value = {"total_metrics": 10}

        analyzer = OptimizedCodeAnalyzer()
        metrics = analyzer.get_performance_metrics()

        assert metrics == {"total_metrics": 10}
        mock_perf.assert_called_once()

    @patch("src.ai_guard.analyzer_optimized.get_cache")
    def test_clear_cache(self, mock_get_cache):
        """Test clearing cache."""
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache

        analyzer = OptimizedCodeAnalyzer()
        analyzer.clear_cache()

        mock_cache.clear.assert_called_once()


class TestDataclasses:
    """Test dataclass definitions."""

    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="src/test.py")
        assert location.uri == "src/test.py"

    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=10, start_column=5)
        assert region.start_line == 10
        assert region.start_column == 5

    def test_region_defaults(self):
        """Test Region dataclass with defaults."""
        region = Region()
        assert region.start_line is None
        assert region.start_column is None

    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact_location = ArtifactLocation(uri="src/test.py")
        region = Region(start_line=10, start_column=5)
        physical_location = PhysicalLocation(
            artifact_location=artifact_location, region=region
        )

        assert physical_location.artifact_location == artifact_location
        assert physical_location.region == region

    def test_physical_location_no_region(self):
        """Test PhysicalLocation dataclass without region."""
        artifact_location = ArtifactLocation(uri="src/test.py")
        physical_location = PhysicalLocation(artifact_location=artifact_location)

        assert physical_location.artifact_location == artifact_location
        assert physical_location.region is None

    def test_location(self):
        """Test Location dataclass."""
        artifact_location = ArtifactLocation(uri="src/test.py")
        region = Region(start_line=10, start_column=5)
        physical_location = PhysicalLocation(
            artifact_location=artifact_location, region=region
        )
        location = Location(physical_location=physical_location)

        assert location.physical_location == physical_location

    def test_default_gates(self):
        """Test default gates configuration."""
        assert default_gates == {"min_coverage": 80}
