"""
Simple test coverage for src/ai_guard/analyzer.py
Tests only the functions that actually exist in the module.
"""
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import json

# Import the analyzer module
from src.ai_guard.analyzer import (
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    _normalize_rule_id,
    _norm,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_output,
    _parse_bandit_json,
    _to_findings,
    _coverage_percent_from_xml,
    cov_percent,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    run,
    main,
    CodeAnalyzer,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    RuleIdStyle,
)


class TestRuleIdStyle(unittest.TestCase):
    """Test RuleIdStyle enum."""
    
    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        self.assertEqual(RuleIdStyle.BARE, "bare")
        self.assertEqual(RuleIdStyle.TOOL, "tool")


class TestRuleStyle(unittest.TestCase):
    """Test _rule_style function."""
    
    def test_rule_style_default(self):
        """Test _rule_style with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = _rule_style()
            self.assertEqual(result, RuleIdStyle.BARE)
    
    def test_rule_style_tool(self):
        """Test _rule_style with tool environment."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _rule_style()
            self.assertEqual(result, RuleIdStyle.TOOL)


class TestMakeRuleId(unittest.TestCase):
    """Test _make_rule_id function."""
    
    def test_make_rule_id_bare(self):
        """Test _make_rule_id with bare style."""
        with patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE):
            result = _make_rule_id("flake8", "E501")
            self.assertEqual(result, "E501")
    
    def test_make_rule_id_tool(self):
        """Test _make_rule_id with tool style."""
        with patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("flake8", "E501")
            self.assertEqual(result, "flake8:E501")


class TestStrictSubprocessFail(unittest.TestCase):
    """Test _strict_subprocess_fail function."""
    
    def test_strict_subprocess_fail_default(self):
        """Test _strict_subprocess_fail with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = _strict_subprocess_fail()
            self.assertFalse(result)
    
    def test_strict_subprocess_fail_true(self):
        """Test _strict_subprocess_fail with true environment."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"}):
            result = _strict_subprocess_fail()
            self.assertTrue(result)


class TestToText(unittest.TestCase):
    """Test _to_text function."""
    
    def test_to_text_string(self):
        """Test _to_text with string input."""
        result = _to_text("hello")
        self.assertEqual(result, "hello")
    
    def test_to_text_bytes(self):
        """Test _to_text with bytes input."""
        result = _to_text(b"hello")
        self.assertEqual(result, "hello")
    
    def test_to_text_none(self):
        """Test _to_text with None input."""
        result = _to_text(None)
        self.assertEqual(result, "")


class TestNormalizeRuleId(unittest.TestCase):
    """Test _normalize_rule_id function."""
    
    def test_normalize_rule_id_simple(self):
        """Test _normalize_rule_id with simple rule ID."""
        result = _normalize_rule_id("E501")
        self.assertEqual(result, "E501")
    
    def test_normalize_rule_id_with_tool(self):
        """Test _normalize_rule_id with tool prefix."""
        result = _normalize_rule_id("flake8:E501")
        self.assertEqual(result, "E501")


class TestNorm(unittest.TestCase):
    """Test _norm function."""
    
    def test_norm_string(self):
        """Test _norm with string input."""
        result = _norm("hello")
        self.assertEqual(result, "hello")
    
    def test_norm_bytes(self):
        """Test _norm with bytes input."""
        result = _norm(b"hello")
        self.assertEqual(result, "hello")
    
    def test_norm_none(self):
        """Test _norm with None input."""
        result = _norm(None)
        self.assertEqual(result, "")


class TestParseFlake8Output(unittest.TestCase):
    """Test _parse_flake8_output function."""
    
    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output with empty input."""
        result = _parse_flake8_output("")
        self.assertEqual(result, [])
    
    def test_parse_flake8_output_single_line(self):
        """Test _parse_flake8_output with single line."""
        output = "src/test.py:1:1: E501 line too long"
        result = _parse_flake8_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "E501")


class TestParseMypyOutput(unittest.TestCase):
    """Test _parse_mypy_output function."""
    
    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output with empty input."""
        result = _parse_mypy_output("")
        self.assertEqual(result, [])
    
    def test_parse_mypy_output_single_line(self):
        """Test _parse_mypy_output with single line."""
        output = "src/test.py:1: error: Name 'x' is not defined"
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "name-defined")


class TestParseBanditOutput(unittest.TestCase):
    """Test _parse_bandit_output function."""
    
    def test_parse_bandit_output_empty(self):
        """Test _parse_bandit_output with empty input."""
        result = _parse_bandit_output("")
        self.assertEqual(result, [])
    
    def test_parse_bandit_output_single_line(self):
        """Test _parse_bandit_output with single line."""
        output = "src/test.py:1:1: B101: Use of assert detected"
        result = _parse_bandit_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "B101")


class TestParseBanditJson(unittest.TestCase):
    """Test _parse_bandit_json function."""
    
    def test_parse_bandit_json_empty(self):
        """Test _parse_bandit_json with empty input."""
        result = _parse_bandit_json({})
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_with_results(self):
        """Test _parse_bandit_json with results."""
        data = {
            "results": [{
                "test_id": "B101",
                "filename": "src/test.py",
                "line_number": 1,
                "issue_severity": "HIGH",
                "issue_text": "Use of assert detected"
            }]
        }
        result = _parse_bandit_json(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "B101")


class TestCoveragePercentFromXml(unittest.TestCase):
    """Test _coverage_percent_from_xml function."""
    
    def test_coverage_percent_from_xml_none(self):
        """Test _coverage_percent_from_xml with None input."""
        result = _coverage_percent_from_xml(None)
        self.assertIsNone(result)
    
    def test_coverage_percent_from_xml_nonexistent_file(self):
        """Test _coverage_percent_from_xml with nonexistent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        self.assertIsNone(result)


class TestCovPercent(unittest.TestCase):
    """Test cov_percent function."""
    
    def test_cov_percent_default(self):
        """Test cov_percent with default behavior."""
        result = cov_percent()
        self.assertIsInstance(result, int)


class TestRunLintCheck(unittest.TestCase):
    """Test run_lint_check function."""
    
    def test_run_lint_check_none_paths(self):
        """Test run_lint_check with None paths."""
        result = run_lint_check(None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestRunTypeCheck(unittest.TestCase):
    """Test run_type_check function."""
    
    def test_run_type_check_none_paths(self):
        """Test run_type_check with None paths."""
        result = run_type_check(None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestRunSecurityCheck(unittest.TestCase):
    """Test run_security_check function."""
    
    def test_run_security_check(self):
        """Test run_security_check."""
        result = run_security_check()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestRunCoverageCheck(unittest.TestCase):
    """Test run_coverage_check function."""
    
    def test_run_coverage_check(self):
        """Test run_coverage_check."""
        result = run_coverage_check()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestRun(unittest.TestCase):
    """Test run function."""
    
    def test_run_none_args(self):
        """Test run with None args."""
        result = run(None)
        self.assertIsInstance(result, int)


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def test_main(self):
        """Test main function."""
        # This should not raise an exception
        try:
            main()
        except SystemExit:
            pass  # Expected for main function


class TestCodeAnalyzer(unittest.TestCase):
    """Test CodeAnalyzer class."""
    
    def test_code_analyzer_initialization(self):
        """Test CodeAnalyzer initialization."""
        analyzer = CodeAnalyzer()
        self.assertIsInstance(analyzer, CodeAnalyzer)


class TestDataClasses(unittest.TestCase):
    """Test data classes."""
    
    def test_artifact_location(self):
        """Test ArtifactLocation class."""
        location = ArtifactLocation(uri="test.py")
        self.assertEqual(location.uri, "test.py")
    
    def test_region(self):
        """Test Region class."""
        region = Region(start_line=1, start_column=1)
        self.assertEqual(region.start_line, 1)
        self.assertEqual(region.start_column, 1)
    
    def test_physical_location(self):
        """Test PhysicalLocation class."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=1, start_column=1)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        self.assertEqual(location.artifact_location.uri, "test.py")
        self.assertEqual(location.region.start_line, 1)
    
    def test_location(self):
        """Test Location class."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=1, start_column=1)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        self.assertEqual(location.physical_location.artifact_location.uri, "test.py")


if __name__ == '__main__':
    unittest.main()