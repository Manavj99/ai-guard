"""Core tests for analyzer.py module."""

import pytest
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open

from src.ai_guard.analyzer import (
    _rule_style, _make_rule_id, _strict_subprocess_fail, _to_text, _norm,
    _coverage_percent_from_xml, cov_percent, _parse_flake8_output,
    _parse_mypy_output, _parse_bandit_json, _parse_bandit_output,
    run_lint_check, run_type_check, run_security_check, run_coverage_check,
    _to_findings, _should_skip_file, _parse_coverage_output, _parse_sarif_output,
    CodeAnalyzer, run, main
)
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestRuleStyle:
    """Test rule style functions."""

    def test_rule_style_default(self):
        """Test default rule style."""
        with patch.dict(os.environ, {}, clear=True):
            assert _rule_style().value == "bare"

    def test_rule_style_tool(self):
        """Test tool rule style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            assert _rule_style().value == "tool"

    def test_make_rule_id_bare(self):
        """Test making rule ID in bare format."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"}):
            assert _make_rule_id("flake8", "E501") == "E501"
            assert _make_rule_id("flake8", None) == "flake8"

    def test_make_rule_id_tool(self):
        """Test making rule ID in tool format."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            assert _make_rule_id("flake8", "E501") == "flake8:E501"
            assert _make_rule_id("flake8", None) == "flake8:flake8"


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

    def test_to_text_bytes_invalid_utf8(self):
        """Test _to_text with invalid UTF-8 bytes."""
        assert _to_text(b"\xff\xfe") == ""

    def test_to_text_other(self):
        """Test _to_text with other types."""
        assert _to_text(123) == "123"


class TestCoveragePercentFromXml:
    """Test coverage percentage from XML functions."""

    def test_coverage_percent_from_xml_none(self):
        """Test coverage percent from XML with None path."""
        with patch.dict(os.environ, {"AI_GUARD_TEST_MODE": "1"}):
            assert _coverage_percent_from_xml(None) is None

    def test_coverage_percent_from_xml_file_not_found(self):
        """Test coverage percent from XML with non-existent file."""
        assert _coverage_percent_from_xml("nonexistent.xml") is None

    def test_coverage_percent_from_xml_cobertura_style(self):
        """Test coverage percent from XML with Cobertura style."""
        def mock_exists(path):
            return path == "test_coverage.xml"
        
        with patch("os.path.exists", side_effect=mock_exists), \
             patch("defusedxml.ElementTree.parse") as mock_parse:
            mock_tree = MagicMock()
            mock_root = MagicMock()
            mock_root.attrib = {"line-rate": "0.86"}
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree
            
            result = _coverage_percent_from_xml("test_coverage.xml")
            assert result == 86  # 0.86 * 100 = 86.0, rounds to 86

    def test_cov_percent(self):
        """Test cov_percent function."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml", return_value=85):
            assert cov_percent() == 85

    def test_cov_percent_none(self):
        """Test cov_percent function with None result."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml", return_value=None):
            assert cov_percent() is None


class TestParseFlake8Output:
    """Test Flake8 output parsing."""

    def test_parse_flake8_output_empty(self):
        """Test parsing empty Flake8 output."""
        assert _parse_flake8_output("") == []
        assert _parse_flake8_output(None) == []

    def test_parse_flake8_output_valid(self):
        """Test parsing valid Flake8 output."""
        output = "src/test.py:10:5: E501 line too long (80 > 79 characters)"
        results = _parse_flake8_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "E501"
        assert results[0].message == "line too long (80 > 79 characters)"
        assert results[0].level == "error"

    def test_parse_flake8_output_multiple(self):
        """Test parsing multiple Flake8 issues."""
        output = """src/test.py:10:5: E501 line too long
src/test.py:15:1: E302 expected 2 blank lines
"""
        results = _parse_flake8_output(output)
        assert len(results) == 2
        assert results[0].rule_id == "E501"
        assert results[1].rule_id == "E302"


class TestParseMypyOutput:
    """Test MyPy output parsing."""

    def test_parse_mypy_output_empty(self):
        """Test parsing empty MyPy output."""
        assert _parse_mypy_output("") == []
        assert _parse_mypy_output(None) == []

    def test_parse_mypy_output_valid_with_code(self):
        """Test parsing valid MyPy output with code."""
        output = "src/test.py:10:5: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "name-defined"
        assert results[0].message == "Name 'x' is not defined"
        assert results[0].level == "error"

    def test_parse_mypy_output_valid_without_code(self):
        """Test parsing valid MyPy output without code."""
        output = "src/test.py:10:5: error: Name 'x' is not defined"
        results = _parse_mypy_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "mypy-error"  # Default rule style is bare
        assert results[0].message == "Name 'x' is not defined"
        assert results[0].level == "error"


class TestParseBanditJson:
    """Test Bandit JSON parsing."""

    def test_parse_bandit_json_empty(self):
        """Test parsing empty Bandit JSON."""
        assert _parse_bandit_json("") == []
        assert _parse_bandit_json("{}") == []

    def test_parse_bandit_json_valid(self):
        """Test parsing valid Bandit JSON."""
        bandit_data = {
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
        json_str = json.dumps(bandit_data)
        results = _parse_bandit_json(json_str)
        assert len(results) == 1
        assert results[0].rule_id == "B101"  # Default rule style is bare
        assert results[0].message == "Test issue"
        assert results[0].level == "warning"


class TestRunLintCheck:
    """Test lint check function."""

    def test_run_lint_check_success(self):
        """Test successful lint check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(["src/test.py"])
            assert result.passed
            assert sarif is None

    def test_run_lint_check_with_issues(self):
        """Test lint check with issues."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:10:5: E501 line too long"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(["src/test.py"])
            assert not result.passed
            assert sarif is not None
            assert sarif.rule_id == "E501"

    def test_run_lint_check_tool_not_found(self):
        """Test lint check when tool not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("flake8 not found")):
            result, sarif = run_lint_check(["src/test.py"])
            assert not result.passed
            assert "Tool not found" in result.details
            assert sarif is None


class TestRunTypeCheck:
    """Test type check function."""

    def test_run_type_check_success(self):
        """Test successful type check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed
            assert sarif is None

    def test_run_type_check_with_issues(self):
        """Test type check with issues."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:10:5: error: Name 'x' is not defined [name-defined]"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(["src/test.py"])
            assert not result.passed
            assert sarif is not None
            assert sarif.rule_id == "name-defined"

    def test_run_type_check_tool_not_found(self):
        """Test type check when tool not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("mypy not found")):
            result, sarif = run_type_check(["src/test.py"])
            assert not result.passed
            assert "Tool not found" in result.details
            assert sarif is None


class TestRunSecurityCheck:
    """Test security check function."""

    def test_run_security_check_success(self):
        """Test successful security check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"results": []}'
            mock_run.return_value.stderr = ""
            
            result, sarif = run_security_check()
            assert result.passed
            assert sarif is None

    def test_run_security_check_with_issues(self):
        """Test security check with issues."""
        bandit_data = {
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
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = json.dumps(bandit_data)
            mock_run.return_value.stderr = ""
            
            result, sarif = run_security_check()
            assert not result.passed
            assert sarif is not None
            assert sarif.rule_id == "B101"  # Default rule style is bare

    def test_run_security_check_tool_not_found(self):
        """Test security check when tool not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("bandit not found")):
            result, sarif = run_security_check()
            assert not result.passed
            assert "Tool not found" in result.details
            assert sarif is None


class TestRunCoverageCheck:
    """Test coverage check function."""

    def test_run_coverage_check_success(self):
        """Test successful coverage check."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml", return_value=85):
            result, sarif = run_coverage_check(80)
            assert result.passed
            assert sarif is None

    def test_run_coverage_check_failure(self):
        """Test coverage check failure."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml", return_value=75):
            result, sarif = run_coverage_check(80)
            assert not result.passed
            assert sarif is None  # run_coverage_check always returns None for sarif
            assert "coverage" in result.details.lower()

    def test_run_coverage_check_no_coverage(self):
        """Test coverage check with no coverage data."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml", return_value=None):
            result, sarif = run_coverage_check(80)
            assert not result.passed
            assert "coverage" in result.details.lower()  # The actual message format
            assert sarif is None


class TestToFindings:
    """Test _to_findings function."""

    def test_to_findings_empty(self):
        """Test _to_findings with empty list."""
        assert _to_findings([]) == []

    def test_to_findings_with_dict_locations(self):
        """Test _to_findings with dictionary locations."""
        sarif_result = SarifResult(
            rule_id="test:rule",
            message="Test message",
            level="error",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "test.py"},
                    "region": {"startLine": 10}
                }
            }]
        )
        findings = _to_findings([sarif_result])
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "test:rule"
        assert findings[0]["level"] == "warning"  # Converted from error
        assert findings[0]["path"] == "test.py"  # Uses "path" not "file"
        assert findings[0]["line"] == 10


class TestShouldSkipFile:
    """Test _should_skip_file function."""

    def test_should_skip_file_python(self):
        """Test _should_skip_file with Python file."""
        assert not _should_skip_file("src/test.py")

    def test_should_skip_file_non_python(self):
        """Test _should_skip_file with non-Python file."""
        assert _should_skip_file("src/test.txt")

    def test_should_skip_file_test_file(self):
        """Test _should_skip_file with test file."""
        assert _should_skip_file("test_file.py")
        assert _should_skip_file("src/test_module_test.py")


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""

    def test_parse_coverage_output_total_pattern(self):
        """Test parsing coverage output with TOTAL pattern."""
        output = "TOTAL 85%"
        assert _parse_coverage_output(output) == 85

    def test_parse_coverage_output_coverage_pattern(self):
        """Test parsing coverage output with Coverage pattern."""
        output = "Coverage: 90%"
        assert _parse_coverage_output(output) == 90

    def test_parse_coverage_output_lines_covered(self):
        """Test parsing coverage output with lines covered."""
        output = "file.py: 100 lines, 80 covered"
        assert _parse_coverage_output(output) == 80

    def test_parse_coverage_output_no_match(self):
        """Test parsing coverage output with no match."""
        output = "no coverage information"
        assert _parse_coverage_output(output) is None


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_init_default(self):
        """Test CodeAnalyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        # The config should be an AnalysisConfig object with default values
        assert analyzer.config is not None
        assert hasattr(analyzer.config, 'enable_security_analysis')
        assert hasattr(analyzer.config, 'enable_performance_analysis')
        assert hasattr(analyzer.config, 'enable_quality_analysis')
        assert hasattr(analyzer.config, 'enable_coverage_analysis')

    def test_code_analyzer_init_custom(self):
        """Test CodeAnalyzer initialization with custom config."""
        from src.ai_guard.analyzer import AnalysisConfig
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        assert analyzer.config == config

    def test_run_all_checks(self):
        """Test running all checks."""
        with patch("src.ai_guard.analyzer.run_lint_check") as mock_lint, \
             patch("src.ai_guard.analyzer.run_type_check") as mock_type, \
             patch("src.ai_guard.analyzer.run_security_check") as mock_security, \
             patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage:
            
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)
            
            analyzer = CodeAnalyzer()
            results = analyzer.run_all_checks(["src/test.py"])
            
            assert len(results) == 4  # Lint, Type, Security, Coverage
            assert all(result.passed for result in results)


class TestRunFunction:
    """Test run function."""

    def test_run_basic(self):
        """Test basic run function."""
        with patch("src.ai_guard.analyzer.changed_python_files", return_value=[]), \
             patch("src.ai_guard.analyzer.run_lint_check") as mock_lint, \
             patch("src.ai_guard.analyzer.run_type_check") as mock_type, \
             patch("src.ai_guard.analyzer.run_security_check") as mock_security, \
             patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage, \
             patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0), \
             patch("src.ai_guard.analyzer.summarize", return_value=0), \
             patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif:
            
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)
            
            exit_code = run([])
            assert exit_code == 0
            mock_write_sarif.assert_called_once()


class TestMainFunction:
    """Test main function."""

    def test_main(self):
        """Test main function."""
        with patch("src.ai_guard.analyzer.run", return_value=0) as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            mock_run.assert_called_once()
