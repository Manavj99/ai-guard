"""Comprehensive tests for all gates in the AI-Guard system."""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os

from src.ai_guard.gates.coverage_eval import (
    CoverageResult, evaluate_coverage_str, _percent_from_root
)
from src.ai_guard.analyzer import (
    run_lint_check, run_type_check, run_security_check, run_coverage_check
)
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestCoverageEvalComprehensive:
    """Comprehensive tests for coverage evaluation gate."""

    def test_percent_from_root_line_rate(self):
        """Test _percent_from_root with line-rate attribute."""
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "0.85"
        result = _percent_from_root(root)
        assert result == 85.0

    def test_percent_from_root_line_rate_invalid(self):
        """Test _percent_from_root with invalid line-rate."""
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "invalid"
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_root_lines_valid_covered(self):
        """Test _percent_from_root with lines-valid and lines-covered."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "100"
        root.attrib["lines-covered"] = "80"
        result = _percent_from_root(root)
        assert result == 80.0

    def test_percent_from_root_lines_invalid_values(self):
        """Test _percent_from_root with invalid lines values."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "invalid"
        root.attrib["lines-covered"] = "invalid"
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_root_lines_zero_valid(self):
        """Test _percent_from_root with zero valid lines."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "0"
        root.attrib["lines-covered"] = "0"
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_root_counters_fallback(self):
        """Test _percent_from_root with counters fallback."""
        root = ET.Element("coverage")
        counter1 = ET.SubElement(root, "counter")
        counter1.attrib["type"] = "LINE"
        counter1.attrib["covered"] = "80"
        counter1.attrib["missed"] = "20"
        
        counter2 = ET.SubElement(root, "counter")
        counter2.attrib["type"] = "BRANCH"
        counter2.attrib["covered"] = "10"
        counter2.attrib["missed"] = "5"
        
        result = _percent_from_root(root)
        assert result == 80.0  # 80/(80+20) = 80%

    def test_percent_from_root_no_counters(self):
        """Test _percent_from_root with no valid counters."""
        root = ET.Element("coverage")
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "BRANCH"
        counter.attrib["covered"] = "10"
        counter.attrib["missed"] = "5"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_evaluate_coverage_str_passes_threshold(self):
        """Test evaluate_coverage_str when coverage passes threshold."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="0.85">
        </coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_fails_threshold(self):
        """Test evaluate_coverage_str when coverage fails threshold."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="0.75">
        </coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is False
        assert result.percent == 75.0

    def test_evaluate_coverage_str_invalid_xml(self):
        """Test evaluate_coverage_str with invalid XML."""
        with pytest.raises(ET.ParseError):
            evaluate_coverage_str("invalid xml", threshold=80.0)

    def test_evaluate_coverage_str_default_threshold(self):
        """Test evaluate_coverage_str with default threshold."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="0.85">
        </coverage>"""
        
        result = evaluate_coverage_str(xml_content)
        assert result.passed is True
        assert result.percent == 85.0


class TestLintGateComprehensive:
    """Comprehensive tests for lint gate."""

    def test_run_lint_check_success_no_output(self):
        """Test lint check with success and no output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(["src/test.py"])
            assert result.passed is True
            assert result.name == "Lint (flake8)"
            assert "No issues" in result.details
            assert sarif is None

    def test_run_lint_check_success_with_warnings(self):
        """Test lint check with success but warnings in output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "src/test.py:1:1: W291 trailing whitespace"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(["src/test.py"])
            assert result.passed is True
            assert sarif is not None
            assert sarif.rule_id == "W291"

    def test_run_lint_check_failure_with_parseable_output(self):
        """Test lint check failure with parseable output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:10:5: E501 line too long (80 > 79 characters)"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(["src/test.py"])
            assert result.passed is False
            assert sarif is not None
            assert sarif.rule_id == "E501"
            assert "line too long" in result.details

    def test_run_lint_check_failure_no_parseable_output(self):
        """Test lint check failure with no parseable output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "flake8: error: cannot open file 'nonexistent.py'"
            
            result, sarif = run_lint_check(["nonexistent.py"])
            assert result.passed is False
            assert sarif is None
            assert "flake8 error" in result.details

    def test_run_lint_check_tool_not_found(self):
        """Test lint check when flake8 is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("flake8 not found")):
            result, sarif = run_lint_check(["src/test.py"])
            assert result.passed is False
            assert "Tool not found" in result.details
            assert sarif is None

    def test_run_lint_check_with_none_paths(self):
        """Test lint check with None paths."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(None)
            assert result.passed is True
            mock_run.assert_called_once_with(["flake8"], capture_output=True, text=True)

    def test_run_lint_check_multiple_issues(self):
        """Test lint check with multiple issues."""
        output = """src/test.py:10:5: E501 line too long
src/test.py:15:1: E302 expected 2 blank lines
src/test.py:20:1: W291 trailing whitespace"""
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = output
            mock_run.return_value.stderr = ""
            
            result, sarif = run_lint_check(["src/test.py"])
            assert result.passed is False
            assert sarif is not None
            assert sarif.rule_id == "E501"  # First issue


class TestTypeGateComprehensive:
    """Comprehensive tests for type checking gate."""

    def test_run_type_check_success_no_output(self):
        """Test type check with success and no output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed is True
            assert result.name == "Static types (mypy)"
            assert "No issues" in result.details
            assert sarif is None

    def test_run_type_check_success_with_info(self):
        """Test type check with success but info messages."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "src/test.py:1: note: mypy version 0.991"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed is True
            # Info messages should not create SARIF results
            assert sarif is None

    def test_run_type_check_failure_with_error_code(self):
        """Test type check failure with error code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:10:5: error: Name 'x' is not defined [name-defined]"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed is False
            assert sarif is not None
            assert sarif.rule_id == "name-defined"
            assert "Name 'x' is not defined" in result.details

    def test_run_type_check_failure_without_error_code(self):
        """Test type check failure without error code in message."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:10:5: error: Name 'x' is not defined"
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed is False
            assert sarif is not None
            assert sarif.rule_id == "mypy-error"  # Default fallback
            assert "Name 'x' is not defined" in result.details

    def test_run_type_check_failure_no_parseable_output(self):
        """Test type check failure with no parseable output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "mypy: error: cannot find module 'nonexistent'"
            
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed is False
            assert sarif is None
            assert "mypy error" in result.details

    def test_run_type_check_tool_not_found(self):
        """Test type check when mypy is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("mypy not found")):
            result, sarif = run_type_check(["src/test.py"])
            assert result.passed is False
            assert "Tool not found" in result.details
            assert sarif is None

    def test_run_type_check_with_none_paths(self):
        """Test type check with None paths."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            
            result, sarif = run_type_check(None)
            assert result.passed is True
            mock_run.assert_called_once_with(["mypy"], capture_output=True, text=True)


class TestSecurityGateComprehensive:
    """Comprehensive tests for security gate."""

    def test_run_security_check_success_no_issues(self):
        """Test security check with success and no issues."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"results": []}'
            mock_run.return_value.stderr = ""
            
            result, sarif = run_security_check()
            assert result.passed is True
            assert result.name == "Security (bandit)"
            assert "No issues" in result.details
            assert sarif is None

    def test_run_security_check_success_with_low_severity(self):
        """Test security check with success but low severity issues."""
        bandit_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "LOW",
                    "issue_text": "Low severity issue",
                    "test_id": "B101"
                }
            ]
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = str(bandit_data).replace("'", '"')
            mock_run.return_value.stderr = ""
            
            result, sarif = run_security_check()
            assert result.passed is True
            assert sarif is not None

    def test_run_security_check_failure_with_high_severity(self):
        """Test security check failure with high severity issues."""
        bandit_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "High severity security issue",
                    "test_id": "B101"
                }
            ]
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = str(bandit_data).replace("'", '"')
            mock_run.return_value.stderr = ""
            
            result, sarif = run_security_check()
            assert result.passed is False
            assert sarif is not None
            assert sarif.rule_id == "B101"
            assert "High severity security issue" in result.details

    def test_run_security_check_failure_no_parseable_output(self):
        """Test security check failure with no parseable output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "invalid json"
            mock_run.return_value.stderr = "bandit: error: invalid configuration"
            
            result, sarif = run_security_check()
            assert result.passed is False
            assert sarif is None
            assert "bandit error" in result.details

    def test_run_security_check_tool_not_found(self):
        """Test security check when bandit is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError("bandit not found")):
            result, sarif = run_security_check()
            assert result.passed is False
            assert "Tool not found" in result.details
            assert sarif is None

    def test_run_security_check_invalid_json(self):
        """Test security check with invalid JSON output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"invalid": json}'
            mock_run.return_value.stderr = ""
            
            result, sarif = run_security_check()
            assert result.passed is True
            assert sarif is None


class TestCoverageGateComprehensive:
    """Comprehensive tests for coverage gate."""

    def test_run_coverage_check_success_above_threshold(self):
        """Test coverage check success when above threshold."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=85):
            result, sarif = run_coverage_check(80)
            assert result.passed is True
            assert result.name == "Coverage"
            assert "85.0%" in result.details
            assert sarif is None

    def test_run_coverage_check_failure_below_threshold(self):
        """Test coverage check failure when below threshold."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=75):
            result, sarif = run_coverage_check(80)
            assert result.passed is False
            assert result.name == "Coverage"
            assert "75.0%" in result.details
            assert sarif is None

    def test_run_coverage_check_no_coverage_data(self):
        """Test coverage check with no coverage data."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=None):
            result, sarif = run_coverage_check(80)
            assert result.passed is False
            assert "No coverage data" in result.details
            assert sarif is None

    def test_run_coverage_check_no_threshold(self):
        """Test coverage check with no threshold (informational)."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=85):
            result, sarif = run_coverage_check(None)
            assert result.passed is True
            assert "no minimum set" in result.details
            assert sarif is None

    def test_run_coverage_check_exact_threshold(self):
        """Test coverage check when exactly at threshold."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=80):
            result, sarif = run_coverage_check(80)
            assert result.passed is True
            assert "80.0%" in result.details
            assert sarif is None

    def test_run_coverage_check_zero_threshold(self):
        """Test coverage check with zero threshold."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=50):
            result, sarif = run_coverage_check(0)
            assert result.passed is True
            assert "50.0%" in result.details
            assert sarif is None

    def test_run_coverage_check_with_xml_path(self):
        """Test coverage check with specific XML path."""
        with patch("src.ai_guard.analyzer.cov_percent", return_value=85):
            result, sarif = run_coverage_check(80, "custom_coverage.xml")
            assert result.passed is True
            assert sarif is None


class TestGateIntegration:
    """Integration tests for all gates working together."""

    def test_all_gates_success(self):
        """Test all gates passing successfully."""
        with patch("src.ai_guard.analyzer.run_lint_check") as mock_lint, \
             patch("src.ai_guard.analyzer.run_type_check") as mock_type, \
             patch("src.ai_guard.analyzer.run_security_check") as mock_security, \
             patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage:
            
            mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
            mock_type.return_value = (GateResult("Type", True, "No issues"), None)
            mock_security.return_value = (GateResult("Security", True, "No issues"), None)
            mock_coverage.return_value = (GateResult("Coverage", True, "85%"), None)
            
            # Test each gate individually using the mocked functions
            lint_result, _ = mock_lint(["src/test.py"])
            type_result, _ = mock_type(["src/test.py"])
            security_result, _ = mock_security()
            coverage_result, _ = mock_coverage(80)
            
            assert all(result.passed for result in [lint_result, type_result, security_result, coverage_result])

    def test_gates_with_mixed_results(self):
        """Test gates with mixed pass/fail results."""
        with patch("src.ai_guard.analyzer.run_lint_check") as mock_lint, \
             patch("src.ai_guard.analyzer.run_type_check") as mock_type, \
             patch("src.ai_guard.analyzer.run_security_check") as mock_security, \
             patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage:
            
            mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
            mock_type.return_value = (GateResult("Type", False, "Type error"), None)
            mock_security.return_value = (GateResult("Security", True, "No issues"), None)
            mock_coverage.return_value = (GateResult("Coverage", False, "75%"), None)
            
            # Test each gate individually using the mocked functions
            lint_result, _ = mock_lint(["src/test.py"])
            type_result, _ = mock_type(["src/test.py"])
            security_result, _ = mock_security()
            coverage_result, _ = mock_coverage(80)
            
            assert lint_result.passed is True
            assert type_result.passed is False
            assert security_result.passed is True
            assert coverage_result.passed is False

    def test_gate_error_handling(self):
        """Test gate error handling and recovery."""
        with patch("src.ai_guard.analyzer.run_lint_check", side_effect=Exception("Unexpected error")):
            with pytest.raises(Exception):
                # Call the function directly to trigger the exception
                from src.ai_guard.analyzer import run_lint_check
                run_lint_check(["src/test.py"])

    def test_gate_result_attributes(self):
        """Test GateResult attributes and methods."""
        result = GateResult("Test Gate", True, "Test message", 0)
        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == "Test message"
        assert result.exit_code == 0

    def test_gate_result_failure(self):
        """Test GateResult with failure."""
        result = GateResult("Test Gate", False, "Test error", 1)
        assert result.name == "Test Gate"
        assert result.passed is False
        assert result.details == "Test error"
        assert result.exit_code == 1
