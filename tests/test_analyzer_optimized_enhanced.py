"""Enhanced tests for analyzer_optimized module to achieve 80%+ coverage."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, mock_open, MagicMock, call
from pathlib import Path

from src.ai_guard.analyzer_optimized import (
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    _normalize_rule_id,
    _run_subprocess_optimized,
    _parse_bandit_json,
    _parse_bandit_output,
    _parse_flake8_output,
    _parse_mypy_output,
    _to_findings,
    _coverage_percent_from_xml,
    _run_quality_checks_parallel,
    RuleIdStyle,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    default_gates
)


class TestRuleIdStyle:
    """Test RuleIdStyle enum."""

    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"


class TestRuleStyle:
    """Test _rule_style function."""

    def test_rule_style_default(self):
        """Test _rule_style with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_rule_style_tool(self):
        """Test _rule_style with tool environment variable."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'tool'}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL

    def test_rule_style_tool_case_insensitive(self):
        """Test _rule_style with tool environment variable case insensitive."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'TOOL'}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL

    def test_rule_style_bare(self):
        """Test _rule_style with bare environment variable."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'bare'}):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_rule_style_other_value(self):
        """Test _rule_style with other value defaults to bare."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'other'}):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_rule_style_whitespace(self):
        """Test _rule_style with whitespace in environment variable."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': '  tool  '}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL


class TestMakeRuleId:
    """Test _make_rule_id function."""

    def test_make_rule_id_tool_style(self):
        """Test _make_rule_id with tool style."""
        with patch('src.ai_guard.analyzer_optimized._rule_style', return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("flake8", "E501")
            assert result == "flake8:E501"

    def test_make_rule_id_bare_style(self):
        """Test _make_rule_id with bare style."""
        with patch('src.ai_guard.analyzer_optimized._rule_style', return_value=RuleIdStyle.BARE):
            result = _make_rule_id("flake8", "E501")
            assert result == "E501"

    def test_make_rule_id_none_code(self):
        """Test _make_rule_id with None code."""
        with patch('src.ai_guard.analyzer_optimized._rule_style', return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("flake8", None)
            assert result == "flake8:flake8"

    def test_make_rule_id_empty_code(self):
        """Test _make_rule_id with empty code."""
        with patch('src.ai_guard.analyzer_optimized._rule_style', return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("flake8", "")
            assert result == "flake8:flake8"

    def test_make_rule_id_whitespace_code(self):
        """Test _make_rule_id with whitespace code."""
        with patch('src.ai_guard.analyzer_optimized._rule_style', return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("flake8", "  ")
            assert result == "flake8:flake8"


class TestStrictSubprocessFail:
    """Test _strict_subprocess_fail function."""

    def test_strict_subprocess_fail_default(self):
        """Test _strict_subprocess_fail with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = _strict_subprocess_fail()
            assert result is False

    def test_strict_subprocess_fail_true_values(self):
        """Test _strict_subprocess_fail with true values."""
        true_values = ["1", "true", "yes", "on"]
        for value in true_values:
            with patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': value}):
                result = _strict_subprocess_fail()
                assert result is True

    def test_strict_subprocess_fail_case_insensitive(self):
        """Test _strict_subprocess_fail with case insensitive values."""
        with patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'TRUE'}):
            result = _strict_subprocess_fail()
            assert result is True

    def test_strict_subprocess_fail_whitespace(self):
        """Test _strict_subprocess_fail with whitespace."""
        with patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': '  true  '}):
            result = _strict_subprocess_fail()
            assert result is True

    def test_strict_subprocess_fail_false_values(self):
        """Test _strict_subprocess_fail with false values."""
        false_values = ["0", "false", "no", "off", "other"]
        for value in false_values:
            with patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': value}):
                result = _strict_subprocess_fail()
                assert result is False


class TestToText:
    """Test _to_text function."""

    def test_to_text_none(self):
        """Test _to_text with None input."""
        result = _to_text(None)
        assert result == ""

    def test_to_text_string(self):
        """Test _to_text with string input."""
        result = _to_text("hello")
        assert result == "hello"

    def test_to_text_bytes(self):
        """Test _to_text with bytes input."""
        result = _to_text(b"hello")
        assert result == "hello"

    def test_to_text_bytearray(self):
        """Test _to_text with bytearray input."""
        result = _to_text(bytearray(b"hello"))
        assert result == "hello"

    def test_to_text_unicode_bytes(self):
        """Test _to_text with unicode bytes."""
        result = _to_text("hello ñáéíóú".encode('utf-8'))
        assert result == "hello ñáéíóú"

    def test_to_text_invalid_bytes(self):
        """Test _to_text with invalid bytes uses replace."""
        result = _to_text(b'\xff\xfe')
        assert result == ""

    def test_to_text_numeric(self):
        """Test _to_text with numeric input."""
        result = _to_text(123)
        assert result == "123"

    def test_to_text_float(self):
        """Test _to_text with float input."""
        result = _to_text(123.45)
        assert result == "123.45"

    def test_to_text_list(self):
        """Test _to_text with list input."""
        result = _to_text([1, 2, 3])
        assert result == "[1, 2, 3]"


class TestNormalizeRuleId:
    """Test _normalize_rule_id function."""

    def test_normalize_rule_id_with_colon(self):
        """Test _normalize_rule_id with colon separator."""
        result = _normalize_rule_id("flake8:E501")
        assert result == "E501"

    def test_normalize_rule_id_without_colon(self):
        """Test _normalize_rule_id without colon separator."""
        result = _normalize_rule_id("E501")
        assert result == "E501"

    def test_normalize_rule_id_multiple_colons(self):
        """Test _normalize_rule_id with multiple colons."""
        result = _normalize_rule_id("tool:category:rule")
        assert result == "category:rule"

    def test_normalize_rule_id_empty_string(self):
        """Test _normalize_rule_id with empty string."""
        result = _normalize_rule_id("")
        assert result == ""

    def test_normalize_rule_id_only_colon(self):
        """Test _normalize_rule_id with only colon."""
        result = _normalize_rule_id(":")
        assert result == ""


class TestRunSubprocessOptimized:
    """Test _run_subprocess_optimized function."""

    def test_run_subprocess_optimized_success(self):
        """Test _run_subprocess_optimized with successful execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = b"output"
            mock_run.return_value.stderr = b"error"
            
            result = _run_subprocess_optimized(["command", "arg"])
            
            assert result == "output"
            mock_run.assert_called_once_with(
                ["command", "arg"],
                capture_output=True,
                text=False,
                timeout=300
            )

    def test_run_subprocess_optimized_failure_strict(self):
        """Test _run_subprocess_optimized with failure in strict mode."""
        with patch('src.ai_guard.analyzer_optimized._strict_subprocess_fail', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = b"output"
                mock_run.return_value.stderr = b"error"
                
                with pytest.raises(subprocess.CalledProcessError):
                    _run_subprocess_optimized(["command", "arg"])

    def test_run_subprocess_optimized_failure_non_strict(self):
        """Test _run_subprocess_optimized with failure in non-strict mode."""
        with patch('src.ai_guard.analyzer_optimized._strict_subprocess_fail', return_value=False):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = b"output"
                mock_run.return_value.stderr = b"error"
                
                result = _run_subprocess_optimized(["command", "arg"])
                assert result == "output"

    def test_run_subprocess_optimized_timeout(self):
        """Test _run_subprocess_optimized with timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("command", 300)
            
            with pytest.raises(subprocess.TimeoutExpired):
                _run_subprocess_optimized(["command", "arg"])

    def test_run_subprocess_optimized_other_exception(self):
        """Test _run_subprocess_optimized with other exception."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = OSError("Command not found")
            
            with pytest.raises(OSError):
                _run_subprocess_optimized(["command", "arg"])


class TestParseBanditJson:
    """Test _parse_bandit_json function."""

    def test_parse_bandit_json_success(self):
        """Test _parse_bandit_json with successful parsing."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test issue",
                    "test_id": "B101"
                }
            ]
        }
        
        result = _parse_bandit_json(json_data)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.py"
        assert result[0]["line"] == 10
        assert result[0]["rule"] == "bandit:B101"
        assert result[0]["message"] == "Test issue"
        assert result[0]["severity"] == "error"

    def test_parse_bandit_json_empty_results(self):
        """Test _parse_bandit_json with empty results."""
        json_data = {"results": []}
        result = _parse_bandit_json(json_data)
        assert result == []

    def test_parse_bandit_json_missing_results(self):
        """Test _parse_bandit_json with missing results key."""
        json_data = {}
        result = _parse_bandit_json(json_data)
        assert result == []

    def test_parse_bandit_json_missing_fields(self):
        """Test _parse_bandit_json with missing fields."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10
                }
            ]
        }
        
        result = _parse_bandit_json(json_data)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.py"
        assert result[0]["line"] == 10
        assert result[0]["rule"] == "bandit:"
        assert result[0]["message"] == ""
        assert result[0]["severity"] == "error"

    def test_parse_bandit_json_low_severity(self):
        """Test _parse_bandit_json with low severity."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH",
                    "issue_text": "Test issue",
                    "test_id": "B101"
                }
            ]
        }
        
        result = _parse_bandit_json(json_data)
        
        assert len(result) == 1
        assert result[0]["severity"] == "warning"


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""

    def test_parse_bandit_output_json(self):
        """Test _parse_bandit_output with JSON format."""
        json_output = '{"results": [{"filename": "test.py", "line_number": 10, "issue_severity": "HIGH", "issue_confidence": "MEDIUM", "issue_text": "Test issue", "test_id": "B101"}]}'
        
        result = _parse_bandit_output(json_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.py"

    def test_parse_bandit_output_text(self):
        """Test _parse_bandit_output with text format."""
        text_output = "test.py:10:1: B101: Test issue"
        
        result = _parse_bandit_output(text_output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.py"
        assert result[0]["line"] == 10
        assert result[0]["rule"] == "bandit:B101"

    def test_parse_bandit_output_invalid_json(self):
        """Test _parse_bandit_output with invalid JSON falls back to text."""
        invalid_json = "invalid json"
        
        result = _parse_bandit_output(invalid_json)
        assert result == []

    def test_parse_bandit_output_empty(self):
        """Test _parse_bandit_output with empty output."""
        result = _parse_bandit_output("")
        assert result == []


class TestParseFlake8Output:
    """Test _parse_flake8_output function."""

    def test_parse_flake8_output_success(self):
        """Test _parse_flake8_output with successful parsing."""
        output = "test.py:10:1: E501 line too long"
        
        result = _parse_flake8_output(output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.py"
        assert result[0]["line"] == 10
        assert result[0]["col"] == 1
        assert result[0]["rule"] == "flake8:E501"
        assert result[0]["message"] == "line too long"
        assert result[0]["severity"] == "error"

    def test_parse_flake8_output_multiple_lines(self):
        """Test _parse_flake8_output with multiple lines."""
        output = "test.py:10:1: E501 line too long\ntest.py:15:5: W292 no newline at end of file"
        
        result = _parse_flake8_output(output)
        
        assert len(result) == 2
        assert result[0]["rule"] == "flake8:E501"
        assert result[1]["rule"] == "flake8:W292"

    def test_parse_flake8_output_no_matches(self):
        """Test _parse_flake8_output with no matching lines."""
        output = "Some other output"
        
        result = _parse_flake8_output(output)
        assert result == []

    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output with empty output."""
        result = _parse_flake8_output("")
        assert result == []


class TestParseMypyOutput:
    """Test _parse_mypy_output function."""

    def test_parse_mypy_output_success(self):
        """Test _parse_mypy_output with successful parsing."""
        output = "test.py:10: error: Name 'x' is not defined  [name-defined]"
        
        result = _parse_mypy_output(output)
        
        assert len(result) == 1
        assert result[0]["file"] == "test.py"
        assert result[0]["line"] == 10
        assert result[0]["rule"] == "mypy:name-defined"
        assert result[0]["message"] == "Name 'x' is not defined"
        assert result[0]["severity"] == "error"

    def test_parse_mypy_output_note(self):
        """Test _parse_mypy_output with note severity."""
        output = "test.py:10: note: Some note  [note]"
        
        result = _parse_mypy_output(output)
        
        assert len(result) == 1
        assert result[0]["severity"] == "info"

    def test_parse_mypy_output_warning(self):
        """Test _parse_mypy_output with warning severity."""
        output = "test.py:10: warning: Some warning  [warn]"
        
        result = _parse_mypy_output(output)
        
        assert len(result) == 1
        assert result[0]["severity"] == "warning"

    def test_parse_mypy_output_no_matches(self):
        """Test _parse_mypy_output with no matching lines."""
        output = "Some other output"
        
        result = _parse_mypy_output(output)
        assert result == []

    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output with empty output."""
        result = _parse_mypy_output("")
        assert result == []


class TestToFindings:
    """Test _to_findings function."""

    def test_to_findings_success(self):
        """Test _to_findings with successful conversion."""
        findings = [
            {
                "file": "test.py",
                "line": 10,
                "rule": "flake8:E501",
                "message": "line too long",
                "severity": "error"
            }
        ]
        
        result = _to_findings(findings)
        
        assert len(result) == 1
        assert result[0].rule_id == "E501"
        assert result[0].message == "line too long"
        assert result[0].level == "error"

    def test_to_findings_empty(self):
        """Test _to_findings with empty findings."""
        result = _to_findings([])
        assert result == []

    def test_to_findings_missing_fields(self):
        """Test _to_findings with missing fields."""
        findings = [
            {
                "file": "test.py",
                "line": 10
            }
        ]
        
        result = _to_findings(findings)
        
        assert len(result) == 1
        assert result[0].rule_id == ""
        assert result[0].message == ""
        assert result[0].level == "error"




class TestDataclasses:
    """Test dataclass definitions."""

    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="file://test.py")
        assert location.uri == "file://test.py"

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
        artifact = ArtifactLocation(uri="file://test.py")
        region = Region(start_line=10, start_column=5)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        
        assert location.artifact_location == artifact
        assert location.region == region

    def test_physical_location_no_region(self):
        """Test PhysicalLocation dataclass without region."""
        artifact = ArtifactLocation(uri="file://test.py")
        location = PhysicalLocation(artifact_location=artifact)
        
        assert location.artifact_location == artifact
        assert location.region is None

    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="file://test.py")
        region = Region(start_line=10, start_column=5)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        
        assert location.physical_location == physical


class TestDefaultGates:
    """Test default_gates configuration."""

    def test_default_gates(self):
        """Test default_gates configuration."""
        assert default_gates == {"min_coverage": 80}
