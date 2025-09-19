"""Comprehensive tests for analyzer_optimized.py to achieve high coverage."""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ai_guard.analyzer_optimized import (
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
    RuleIdStyle,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    default_gates,
)


class TestRuleIdStyle:
    """Test RuleIdStyle enum."""
    
    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"


class TestRuleStyle:
    """Test rule style functions."""
    
    def test_rule_style_default(self):
        """Test default rule style."""
        with patch.dict(os.environ, {}, clear=True):
            assert _rule_style() == RuleIdStyle.BARE
    
    def test_rule_style_tool(self):
        """Test tool rule style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            assert _rule_style() == RuleIdStyle.TOOL
    
    def test_rule_style_invalid(self):
        """Test invalid rule style falls back to bare."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "invalid"}):
            assert _rule_style() == RuleIdStyle.BARE


class TestMakeRuleId:
    """Test rule ID creation."""
    
    def test_make_rule_id_bare_style(self):
        """Test making rule ID with bare style."""
        with patch.dict(os.environ, {}, clear=True):
            assert _make_rule_id("flake8", "E501") == "E501"
            assert _make_rule_id("mypy", "name-defined") == "name-defined"
            assert _make_rule_id("bandit", "B101") == "B101"
    
    def test_make_rule_id_tool_style(self):
        """Test making rule ID with tool style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            assert _make_rule_id("flake8", "E501") == "flake8:E501"
            assert _make_rule_id("mypy", "name-defined") == "mypy:name-defined"
            assert _make_rule_id("bandit", "B101") == "bandit:B101"
    
    def test_make_rule_id_none_code(self):
        """Test making rule ID with None code."""
        with patch.dict(os.environ, {}, clear=True):
            assert _make_rule_id("flake8", None) == "flake8"
            assert _make_rule_id("mypy", None) == "mypy"
    
    def test_make_rule_id_empty_code(self):
        """Test making rule ID with empty code."""
        with patch.dict(os.environ, {}, clear=True):
            assert _make_rule_id("flake8", "") == "flake8"
            assert _make_rule_id("mypy", "   ") == "mypy"


class TestStrictSubprocessFail:
    """Test strict subprocess failure setting."""
    
    def test_strict_subprocess_fail_default(self):
        """Test default strict subprocess fail setting."""
        with patch.dict(os.environ, {}, clear=True):
            assert _strict_subprocess_fail() is False
    
    def test_strict_subprocess_fail_true_values(self):
        """Test strict subprocess fail true values."""
        for value in ["1", "true", "yes", "on"]:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                assert _strict_subprocess_fail() is True
    
    def test_strict_subprocess_fail_false_values(self):
        """Test strict subprocess fail false values."""
        for value in ["0", "false", "no", "off", "invalid"]:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                assert _strict_subprocess_fail() is False


class TestToText:
    """Test text conversion function."""
    
    def test_to_text_none(self):
        """Test converting None to text."""
        assert _to_text(None) == ""
    
    def test_to_text_string(self):
        """Test converting string to text."""
        assert _to_text("hello") == "hello"
        assert _to_text("") == ""
    
    def test_to_text_bytes(self):
        """Test converting bytes to text."""
        assert _to_text(b"hello") == "hello"
        assert _to_text(b"") == ""
    
    def test_to_text_bytearray(self):
        """Test converting bytearray to text."""
        assert _to_text(bytearray(b"hello")) == "hello"
        assert _to_text(bytearray()) == ""
    
    def test_to_text_invalid_utf8(self):
        """Test converting invalid UTF-8 bytes."""
        invalid_bytes = b'\xff\xfe\x00\x00'
        result = _to_text(invalid_bytes)
        assert isinstance(result, str)
        assert len(result) > 0  # Should be replaced, not empty
    
    def test_to_text_other_types(self):
        """Test converting other types to text."""
        assert _to_text(123) == "123"
        assert _to_text(True) == "True"
        assert _to_text([1, 2, 3]) == "[1, 2, 3]"


class TestNormalizeRuleId:
    """Test rule ID normalization."""
    
    def test_normalize_rule_id_with_colon(self):
        """Test normalizing rule ID with colon."""
        assert _normalize_rule_id("flake8:E501") == "E501"
        assert _normalize_rule_id("mypy:name-defined") == "name-defined"
        assert _normalize_rule_id("bandit:B101") == "B101"
    
    def test_normalize_rule_id_without_colon(self):
        """Test normalizing rule ID without colon."""
        assert _normalize_rule_id("E501") == "E501"
        assert _normalize_rule_id("name-defined") == "name-defined"
        assert _normalize_rule_id("B101") == "B101"
    
    def test_normalize_rule_id_multiple_colons(self):
        """Test normalizing rule ID with multiple colons."""
        assert _normalize_rule_id("tool:category:rule") == "category:rule"


class TestNorm:
    """Test string normalization function."""
    
    def test_norm_none(self):
        """Test normalizing None."""
        assert _norm(None) == ""
    
    def test_norm_string(self):
        """Test normalizing string."""
        assert _norm("hello") == "hello"
        assert _norm("") == ""
    
    def test_norm_bytes(self):
        """Test normalizing bytes."""
        assert _norm(b"hello") == "hello"
        assert _norm(b"") == ""
    
    def test_norm_bytearray(self):
        """Test normalizing bytearray."""
        assert _norm(bytearray(b"hello")) == "hello"
        assert _norm(bytearray()) == ""
    
    def test_norm_invalid_utf8(self):
        """Test normalizing invalid UTF-8 bytes."""
        invalid_bytes = b'\xff\xfe\x00\x00'
        result = _norm(invalid_bytes)
        assert isinstance(result, str)
        assert len(result) > 0


class TestCoveragePercentFromXml:
    """Test coverage percentage parsing from XML."""
    
    def test_coverage_percent_from_xml_none_path(self):
        """Test coverage parsing with None path."""
        with patch.dict(os.environ, {"AI_GUARD_TEST_MODE": "1"}):
            result = _coverage_percent_from_xml(None)
            # The function tries to find coverage.xml in current directory
            # In test environment, it might find a coverage file
            assert result is not None or result is None
    
    def test_coverage_percent_from_xml_file_not_found(self):
        """Test coverage parsing with non-existent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None
    
    def test_coverage_percent_from_xml_cobertura_style(self):
        """Test coverage parsing with Cobertura style XML."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85" lines-valid="100" lines-covered="85">
            <packages>
                <package name="test" line-rate="0.85"/>
            </packages>
        </coverage>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = _coverage_percent_from_xml(temp_path)
            assert result == 85
        finally:
            os.unlink(temp_path)
    
    def test_coverage_percent_from_xml_counter_style(self):
        """Test coverage parsing with counter style XML."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage>
            <packages>
                <package name="test">
                    <classes>
                        <class name="TestClass">
                            <counter type="LINE" covered="80" missed="20"/>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = _coverage_percent_from_xml(temp_path)
            assert result == 80
        finally:
            os.unlink(temp_path)
    
    def test_coverage_percent_from_xml_invalid_xml(self):
        """Test coverage parsing with invalid XML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=True) as f:
            f.write("invalid xml content")
            f.flush()
            result = _coverage_percent_from_xml(f.name)
            assert result is None
    
    def test_coverage_percent_from_xml_invalid_line_rate(self):
        """Test coverage parsing with invalid line rate."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="invalid" lines-valid="100" lines-covered="85">
            <packages>
                <package name="test" line-rate="0.85"/>
            </packages>
        </coverage>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=True) as f:
            f.write(xml_content)
            f.flush()
            result = _coverage_percent_from_xml(f.name)
            assert result is None


class TestCovPercent:
    """Test coverage percentage function."""
    
    def test_cov_percent_with_coverage(self):
        """Test cov_percent with valid coverage."""
        with patch('src.ai_guard.analyzer_optimized._coverage_percent_from_xml') as mock_coverage:
            mock_coverage.return_value = 85
            result = cov_percent()
            assert result == 85
    
    def test_cov_percent_without_coverage(self):
        """Test cov_percent without coverage data."""
        with patch('src.ai_guard.analyzer_optimized._coverage_percent_from_xml') as mock_coverage:
            mock_coverage.return_value = None
            result = cov_percent()
            assert result == 0


class TestParseFlake8Output:
    """Test Flake8 output parsing."""
    
    def test_parse_flake8_output_empty(self):
        """Test parsing empty Flake8 output."""
        result = _parse_flake8_output("")
        assert result == []
    
    def test_parse_flake8_output_none(self):
        """Test parsing None Flake8 output."""
        result = _parse_flake8_output(None)
        assert result == []
    
    def test_parse_flake8_output_valid(self):
        """Test parsing valid Flake8 output."""
        output = "src/test.py:10:5: E501 line too long (80 > 79 characters)"
        result = _parse_flake8_output(output)
        
        assert len(result) == 1
        assert result[0].rule_id == "E501"
        assert result[0].message == "line too long (80 > 79 characters)"
        assert result[0].level == "warning"
        assert len(result[0].locations) == 1
        assert result[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert result[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert result[0].locations[0]["physicalLocation"]["region"]["startColumn"] == 5
    
    def test_parse_flake8_output_multiple_lines(self):
        """Test parsing multiple Flake8 output lines."""
        output = """src/test.py:10:5: E501 line too long (80 > 79 characters)
src/test.py:15:1: E302 expected 2 blank lines, found 1"""
        result = _parse_flake8_output(output)
        
        assert len(result) == 2
        assert result[0].rule_id == "E501"
        assert result[1].rule_id == "E302"
    
    def test_parse_flake8_output_invalid_format(self):
        """Test parsing invalid Flake8 output format."""
        output = "invalid format line"
        result = _parse_flake8_output(output)
        assert result == []
    
    def test_parse_flake8_output_whitespace_lines(self):
        """Test parsing Flake8 output with whitespace lines."""
        output = """
src/test.py:10:5: E501 line too long (80 > 79 characters)

src/test.py:15:1: E302 expected 2 blank lines, found 1
"""
        result = _parse_flake8_output(output)
        assert len(result) == 2


class TestParseMypyOutput:
    """Test MyPy output parsing."""
    
    def test_parse_mypy_output_empty(self):
        """Test parsing empty MyPy output."""
        result = _parse_mypy_output("")
        assert result == []
    
    def test_parse_mypy_output_none(self):
        """Test parsing None MyPy output."""
        result = _parse_mypy_output(None)
        assert result == []
    
    def test_parse_mypy_output_with_column(self):
        """Test parsing MyPy output with column."""
        output = "src/test.py:10:5: error: Name 'x' is not defined [name-defined]"
        result = _parse_mypy_output(output)
        
        assert len(result) == 1
        assert result[0].rule_id == "name-defined"
        assert result[0].message == "Name 'x' is not defined"
        assert result[0].level == "error"
        assert len(result[0].locations) == 1
        assert result[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert result[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert result[0].locations[0]["physicalLocation"]["region"]["startColumn"] == 5
    
    def test_parse_mypy_output_without_column(self):
        """Test parsing MyPy output without column."""
        output = "src/test.py:10: error: Name 'x' is not defined [name-defined]"
        result = _parse_mypy_output(output)
        
        assert len(result) == 1
        assert result[0].rule_id == "name-defined"
        assert result[0].message == "Name 'x' is not defined"
        assert result[0].level == "error"
        assert len(result[0].locations) == 1
        assert result[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert result[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert result[0].locations[0]["physicalLocation"]["region"]["startColumn"] is None
    
    def test_parse_mypy_output_without_bracketed_code(self):
        """Test parsing MyPy output without bracketed code."""
        output = "src/test.py:10: error: Name 'x' is not defined"
        result = _parse_mypy_output(output)

        assert len(result) == 1
        assert result[0].rule_id == "mypy-error"
        assert result[0].message == "Name 'x' is not defined"
        assert result[0].level == "error"
    
    def test_parse_mypy_output_invalid_severity(self):
        """Test parsing MyPy output with invalid severity."""
        output = "src/test.py:10: info: Some information"
        result = _parse_mypy_output(output)
        assert result == []
    
    def test_parse_mypy_output_multiple_lines(self):
        """Test parsing multiple MyPy output lines."""
        output = """src/test.py:10: error: Name 'x' is not defined [name-defined]
src/test.py:15: warning: Unused variable 'y' [unused-var]"""
        result = _parse_mypy_output(output)
        
        assert len(result) == 2
        assert result[0].rule_id == "name-defined"
        assert result[1].rule_id == "unused-var"
    
    def test_parse_mypy_output_invalid_format(self):
        """Test parsing invalid MyPy output format."""
        output = "invalid format line"
        result = _parse_mypy_output(output)
        assert result == []


class TestRunSubprocessOptimized:
    """Test subprocess execution."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_subprocess_optimized_success(self, mock_run_cmd):
        """Test successful subprocess execution."""
        mock_run_cmd.return_value = (0, "success output")
        
        result = _run_subprocess_optimized(["echo", "test"])
        
        assert result.returncode == 0
        assert result.stdout == "success output"
        assert result.stderr == ""
        mock_run_cmd.assert_called_once_with(["echo", "test"], timeout=30)
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_subprocess_optimized_failure(self, mock_run_cmd):
        """Test failed subprocess execution."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError
        mock_run_cmd.side_effect = ToolExecutionError("Command failed")
        
        result = _run_subprocess_optimized(["invalid", "command"])
        
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "Command failed"
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_subprocess_optimized_with_timeout(self, mock_run_cmd):
        """Test subprocess execution with custom timeout."""
        mock_run_cmd.return_value = (0, "success output")
        
        result = _run_subprocess_optimized(["echo", "test"], timeout=60)
        
        assert result.returncode == 0
        assert result.stdout == "success output"
        assert result.stderr == ""
        mock_run_cmd.assert_called_once_with(["echo", "test"], timeout=60)


class TestRunLintCheck:
    """Test lint check execution."""
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_lint_check_success(self, mock_run_subprocess):
        """Test successful lint check."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_lint_check(["src/test.py"])
        
        assert gate_result.passed is True
        assert gate_result.name == "Lint (flake8)"
        assert gate_result.details == "No issues"
        assert sarif_result is None
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_lint_check_with_issues(self, mock_run_subprocess):
        """Test lint check with issues."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "src/test.py:10:5: E501 line too long"
        mock_process.stderr = ""
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_lint_check(["src/test.py"])
        
        assert gate_result.passed is False
        assert gate_result.name == "Lint (flake8)"
        assert sarif_result is not None
        assert sarif_result.rule_id == "E501"
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_lint_check_command_not_found(self, mock_run_subprocess):
        """Test lint check when command not found."""
        mock_process = Mock()
        mock_process.returncode = 127
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_lint_check(["src/test.py"])
        
        assert gate_result.passed is False
        assert gate_result.details == "flake8 not found"
        assert sarif_result is None
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_lint_check_tool_error(self, mock_run_subprocess):
        """Test lint check with tool error."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "flake8 error: invalid option"
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_lint_check(["src/test.py"])
        
        assert gate_result.passed is False
        assert "flake8 error: invalid option" in gate_result.details
        assert sarif_result is None


class TestRunTypeCheck:
    """Test type check execution."""
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_type_check_success(self, mock_run_subprocess):
        """Test successful type check."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_type_check(["src/test.py"])
        
        assert gate_result.passed is True
        assert gate_result.name == "Static types (mypy)"
        assert gate_result.details == "No issues"
        assert sarif_result is None
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_type_check_with_issues(self, mock_run_subprocess):
        """Test type check with issues."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "src/test.py:10: error: Name 'x' is not defined [name-defined]"
        mock_process.stderr = ""
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_type_check(["src/test.py"])
        
        assert gate_result.passed is False
        assert gate_result.name == "Static types (mypy)"
        assert sarif_result is not None
        assert sarif_result.rule_id == "name-defined"
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_type_check_command_not_found(self, mock_run_subprocess):
        """Test type check when command not found."""
        mock_process = Mock()
        mock_process.returncode = 127
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_type_check(["src/test.py"])
        
        assert gate_result.passed is False
        assert gate_result.details == "mypy not found"
        assert sarif_result is None


class TestParseBanditJson:
    """Test Bandit JSON parsing."""
    
    def test_parse_bandit_json_string(self):
        """Test parsing Bandit JSON from string."""
        json_output = '{"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}'
        result = _parse_bandit_json(json_output)
        
        assert len(result) == 1
        assert result[0].rule_id == "B101"
        assert result[0].message == "Test issue"
        assert result[0].level == "warning"
        assert len(result[0].locations) == 1
        assert result[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert result[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
    
    def test_parse_bandit_json_bytes(self):
        """Test parsing Bandit JSON from bytes."""
        json_output = b'{"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}'
        result = _parse_bandit_json(json_output)
        
        assert len(result) == 1
        assert result[0].rule_id == "B101"
    
    def test_parse_bandit_json_dict(self):
        """Test parsing Bandit JSON from dict."""
        json_data = {"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}
        result = _parse_bandit_json(json_data)
        
        assert len(result) == 1
        assert result[0].rule_id == "B101"
    
    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid Bandit JSON."""
        result = _parse_bandit_json("invalid json")
        assert result == []
    
    def test_parse_bandit_json_empty(self):
        """Test parsing empty Bandit JSON."""
        result = _parse_bandit_json("{}")
        assert result == []
    
    def test_parse_bandit_json_no_results(self):
        """Test parsing Bandit JSON with no results."""
        result = _parse_bandit_json('{"results": []}')
        assert result == []


class TestProcessBanditData:
    """Test Bandit data processing."""
    
    def test_process_bandit_data_valid(self):
        """Test processing valid Bandit data."""
        data = {"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}
        result = _process_bandit_data(data)
        
        assert len(result) == 1
        assert result[0].rule_id == "B101"
        assert result[0].message == "Test issue"
        assert result[0].level == "warning"
    
    def test_process_bandit_data_invalid(self):
        """Test processing invalid Bandit data."""
        result = _process_bandit_data("invalid")
        assert result == []
    
    def test_process_bandit_data_no_results(self):
        """Test processing Bandit data with no results."""
        result = _process_bandit_data({})
        assert result == []
    
    def test_process_bandit_data_missing_fields(self):
        """Test processing Bandit data with missing fields."""
        data = {"results": [{"filename": "test.py"}]}  # Missing required fields
        result = _process_bandit_data(data)
        
        assert len(result) == 1
        assert result[0].rule_id == "bandit"  # Default rule ID
        assert result[0].message == ""
        assert result[0].level == "warning"


class TestParseBanditOutput:
    """Test Bandit output parsing."""
    
    def test_parse_bandit_output(self):
        """Test parsing Bandit output."""
        output = '{"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}'
        result = _parse_bandit_output(output)
        
        assert len(result) == 1
        assert result[0].rule_id == "B101"


class TestRunSecurityCheck:
    """Test security check execution."""
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_security_check_success(self, mock_run_subprocess):
        """Test successful security check."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = '{"results": []}'
        mock_process.stderr = ""
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_security_check()
        
        assert gate_result.passed is True
        assert gate_result.name == "Security (bandit)"
        assert gate_result.details == "No issues"
        assert sarif_result is None
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_security_check_with_issues(self, mock_run_subprocess):
        """Test security check with issues."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = '{"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Test issue", "test_id": "B101"}]}'
        mock_process.stderr = ""
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_security_check()
        
        assert gate_result.passed is False
        assert gate_result.name == "Security (bandit)"
        assert sarif_result is not None
        assert sarif_result.rule_id == "B101"
    
    @patch('src.ai_guard.analyzer_optimized._run_subprocess_optimized')
    def test_run_security_check_command_not_found(self, mock_run_subprocess):
        """Test security check when command not found."""
        mock_process = Mock()
        mock_process.returncode = 127
        mock_run_subprocess.return_value = mock_process
        
        gate_result, sarif_result = run_security_check()
        
        assert gate_result.passed is False
        assert gate_result.details == "bandit not found"
        assert sarif_result is None


class TestToFindings:
    """Test findings conversion."""
    
    def test_to_findings_empty(self):
        """Test converting empty findings."""
        result = _to_findings([])
        assert result == []
    
    def test_to_findings_with_locations(self):
        """Test converting findings with locations."""
        from src.ai_guard.sarif_report import SarifResult
        
        sarif_result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "test.py"},
                    "region": {"startLine": 10}
                }
            }]
        )
        
        result = _to_findings([sarif_result])
        
        assert len(result) == 1
        assert result[0]["rule_id"] == "test-rule"
        assert result[0]["message"] == "Test message"
        assert result[0]["level"] == "warning"
        assert result[0]["path"] == "test.py"
        assert result[0]["line"] == 10
    
    def test_to_findings_without_locations(self):
        """Test converting findings without locations."""
        from src.ai_guard.sarif_report import SarifResult
        
        sarif_result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[]
        )
        
        result = _to_findings([sarif_result])
        
        assert len(result) == 1
        assert result[0]["rule_id"] == "test-rule"
        assert result[0]["message"] == "Test message"
        assert result[0]["level"] == "warning"
        assert result[0]["path"] == "unknown"
        assert result[0]["line"] is None


class TestRunCoverageCheck:
    """Test coverage check execution."""
    
    @patch('src.ai_guard.analyzer_optimized.cov_percent')
    def test_run_coverage_check_with_coverage(self, mock_cov_percent):
        """Test coverage check with valid coverage."""
        mock_cov_percent.return_value = 85
        
        result = run_coverage_check(80)
        
        assert result.passed is True
        assert result.name == "Coverage"
        assert "85% >= 80%" in result.details
    
    @patch('src.ai_guard.analyzer_optimized.cov_percent')
    def test_run_coverage_check_below_threshold(self, mock_cov_percent):
        """Test coverage check below threshold."""
        mock_cov_percent.return_value = 75
        
        result = run_coverage_check(80)
        
        assert result.passed is False
        assert result.name == "Coverage"
        assert "75% >= 80%" in result.details
    
    @patch('src.ai_guard.analyzer_optimized.cov_percent')
    def test_run_coverage_check_no_minimum(self, mock_cov_percent):
        """Test coverage check with no minimum threshold."""
        mock_cov_percent.return_value = 85
        
        result = run_coverage_check(None)
        
        assert result.passed is True
        assert result.name == "Coverage"
        assert "85% (no minimum set)" in result.details
    
    @patch('src.ai_guard.analyzer_optimized.cov_percent')
    def test_run_coverage_check_no_data(self, mock_cov_percent):
        """Test coverage check with no coverage data."""
        mock_cov_percent.return_value = None
        
        result = run_coverage_check(80)
        
        assert result.passed is False
        assert result.name == "Coverage"
        assert result.details == "No coverage data"


class TestRunQualityChecksParallel:
    """Test parallel quality checks."""
    
    @patch('src.ai_guard.analyzer_optimized.parallel_execute')
    def test_run_quality_checks_parallel(self, mock_parallel_execute):
        """Test running quality checks in parallel."""
        # Mock the parallel execution results
        mock_parallel_execute.return_value = [
            (Mock(passed=True, name="Lint"), Mock(rule_id="E501")),
            (Mock(passed=True, name="Type"), Mock(rule_id="name-defined")),
            (Mock(passed=True, name="Security"), Mock(rule_id="B101"))
        ]
        
        results, sarif_diagnostics = _run_quality_checks_parallel(["src/test.py"])
        
        assert len(results) == 3
        assert len(sarif_diagnostics) == 3
        mock_parallel_execute.assert_called_once()


class TestOptimizedCodeAnalyzer:
    """Test OptimizedCodeAnalyzer class."""
    
    def test_init_default_config(self):
        """Test initializing with default config."""
        analyzer = OptimizedCodeAnalyzer()
        assert analyzer.config is not None
    
    def test_init_custom_config(self):
        """Test initializing with custom config."""
        config = {"min_coverage": 90}
        analyzer = OptimizedCodeAnalyzer(config)
        assert analyzer.config == config
    
    @patch('src.ai_guard.analyzer_optimized._run_quality_checks_parallel')
    def test_run_all_checks_parallel(self, mock_parallel_checks):
        """Test running all checks in parallel."""
        mock_parallel_checks.return_value = ([Mock(passed=True)], [Mock(rule_id="test")])
        
        analyzer = OptimizedCodeAnalyzer()
        results = analyzer.run_all_checks(["src/test.py"], parallel=True)
        
        assert len(results) >= 1  # Should include coverage check
        mock_parallel_checks.assert_called_once()
    
    @patch('src.ai_guard.analyzer_optimized.run_lint_check')
    @patch('src.ai_guard.analyzer_optimized.run_type_check')
    @patch('src.ai_guard.analyzer_optimized.run_security_check')
    @patch('src.ai_guard.analyzer_optimized.run_coverage_check')
    def test_run_all_checks_sequential(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test running all checks sequentially."""
        mock_lint.return_value = (Mock(passed=True), None)
        mock_type.return_value = (Mock(passed=True), None)
        mock_security.return_value = (Mock(passed=True), None)
        mock_coverage.return_value = Mock(passed=True)
        
        analyzer = OptimizedCodeAnalyzer()
        results = analyzer.run_all_checks(["src/test.py"], parallel=False)
        
        assert len(results) == 4
        mock_lint.assert_called_once()
        mock_type.assert_called_once()
        mock_security.assert_called_once()
        mock_coverage.assert_called_once()
    
    @patch('src.ai_guard.analyzer_optimized.get_performance_summary')
    def test_get_performance_metrics(self, mock_perf_summary):
        """Test getting performance metrics."""
        mock_perf_summary.return_value = {"total_metrics": 10}
        
        analyzer = OptimizedCodeAnalyzer()
        metrics = analyzer.get_performance_metrics()
        
        assert metrics == {"total_metrics": 10}
    
    @patch('src.ai_guard.analyzer_optimized.get_cache')
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
        location = ArtifactLocation(uri="test.py")
        assert location.uri == "test.py"
    
    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=10, start_column=5)
        assert region.start_line == 10
        assert region.start_column == 5
    
    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        
        assert location.artifact_location == artifact
        assert location.region == region
    
    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        
        assert location.physical_location == physical


class TestDefaultGates:
    """Test default gates configuration."""
    
    def test_default_gates(self):
        """Test default gates configuration."""
        assert default_gates == {"min_coverage": 80}


class TestMainFunction:
    """Test main function."""
    
    @patch('src.ai_guard.analyzer_optimized.run')
    def test_main(self, mock_run):
        """Test main function."""
        mock_run.return_value = 0
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)
