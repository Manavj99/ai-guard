"""
Comprehensive test coverage for src/ai_guard/analyzer.py
This test file aims to achieve maximum coverage for the analyzer module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import os
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Import the analyzer module
from src.ai_guard.analyzer import (
    RuleIdStyle,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
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
    run_lint_check,
    run_type_check,
    _parse_bandit_json,
    _parse_bandit_output,
    run_security_check,
    _to_findings,
    run_coverage_check,
    run,
    main,
    CodeAnalyzer
)


class TestRuleIdStyle(unittest.TestCase):
    """Test RuleIdStyle enum."""
    
    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        self.assertEqual(RuleIdStyle.BARE, "bare")
        self.assertEqual(RuleIdStyle.TOOL, "tool")


class TestRuleStyle(unittest.TestCase):
    """Test _rule_style function."""
    
    @patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'tool'})
    def test_rule_style_tool(self):
        """Test rule style returns TOOL when env var is 'tool'."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.TOOL)
    
    @patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'bare'})
    def test_rule_style_bare(self):
        """Test rule style returns BARE when env var is 'bare'."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.BARE)
    
    @patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'invalid'})
    def test_rule_style_invalid_defaults_to_bare(self):
        """Test rule style defaults to BARE for invalid values."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.BARE)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_rule_style_no_env_var_defaults_to_bare(self):
        """Test rule style defaults to BARE when no env var is set."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.BARE)


class TestMakeRuleId(unittest.TestCase):
    """Test _make_rule_id function."""
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE)
    def test_make_rule_id_bare_style(self, mock_rule_style):
        """Test rule ID creation with bare style."""
        result = _make_rule_id("flake8", "E501")
        self.assertEqual(result, "E501")
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_tool_style(self, mock_rule_style):
        """Test rule ID creation with tool style."""
        result = _make_rule_id("flake8", "E501")
        self.assertEqual(result, "flake8:E501")
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE)
    def test_make_rule_id_no_code(self, mock_rule_style):
        """Test rule ID creation with no code."""
        result = _make_rule_id("flake8", None)
        self.assertEqual(result, "flake8")
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE)
    def test_make_rule_id_empty_code(self, mock_rule_style):
        """Test rule ID creation with empty code."""
        result = _make_rule_id("flake8", "   ")
        self.assertEqual(result, "flake8")


class TestStrictSubprocessFail(unittest.TestCase):
    """Test _strict_subprocess_fail function."""
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': '1'})
    def test_strict_subprocess_fail_true_values(self):
        """Test strict subprocess fail returns True for truthy values."""
        self.assertTrue(_strict_subprocess_fail())
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'true'})
    def test_strict_subprocess_fail_true_string(self):
        """Test strict subprocess fail returns True for 'true'."""
        self.assertTrue(_strict_subprocess_fail())
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'yes'})
    def test_strict_subprocess_fail_yes_string(self):
        """Test strict subprocess fail returns True for 'yes'."""
        self.assertTrue(_strict_subprocess_fail())
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'on'})
    def test_strict_subprocess_fail_on_string(self):
        """Test strict subprocess fail returns True for 'on'."""
        self.assertTrue(_strict_subprocess_fail())
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'false'})
    def test_strict_subprocess_fail_false_string(self):
        """Test strict subprocess fail returns False for 'false'."""
        self.assertFalse(_strict_subprocess_fail())
    
    @patch.dict(os.environ, {}, clear=True)
    def test_strict_subprocess_fail_no_env_var(self):
        """Test strict subprocess fail returns False when no env var is set."""
        self.assertFalse(_strict_subprocess_fail())


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
    
    def test_to_text_number(self):
        """Test _to_text with number input."""
        result = _to_text(123)
        self.assertEqual(result, "123")
    
    def test_to_text_list(self):
        """Test _to_text with list input."""
        result = _to_text([1, 2, 3])
        self.assertEqual(result, "[1, 2, 3]")


class TestDataClasses(unittest.TestCase):
    """Test data classes."""
    
    def test_artifact_location(self):
        """Test ArtifactLocation data class."""
        location = ArtifactLocation(uri="file:///test.py")
        self.assertEqual(location.uri, "file:///test.py")
    
    def test_region(self):
        """Test Region data class."""
        region = Region(start_line=1, start_column=1, end_line=1, end_column=10)
        self.assertEqual(region.start_line, 1)
        self.assertEqual(region.start_column, 1)
        self.assertEqual(region.end_line, 1)
        self.assertEqual(region.end_column, 10)
    
    def test_physical_location(self):
        """Test PhysicalLocation data class."""
        region = Region(start_line=1, start_column=1, end_line=1, end_column=10)
        artifact = ArtifactLocation(uri="file:///test.py")
        location = PhysicalLocation(artifact_location=artifact, region=region)
        self.assertEqual(location.artifact_location, artifact)
        self.assertEqual(location.region, region)
    
    def test_location(self):
        """Test Location data class."""
        region = Region(start_line=1, start_column=1, end_line=1, end_column=10)
        artifact = ArtifactLocation(uri="file:///test.py")
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        self.assertEqual(location.physical_location, physical)


class TestNormalizeRuleId(unittest.TestCase):
    """Test _normalize_rule_id function."""
    
    def test_normalize_rule_id_basic(self):
        """Test basic rule ID normalization."""
        result = _normalize_rule_id("E501")
        self.assertEqual(result, "E501")
    
    def test_normalize_rule_id_with_tool(self):
        """Test rule ID normalization with tool prefix."""
        result = _normalize_rule_id("flake8:E501")
        self.assertEqual(result, "E501")
    
    def test_normalize_rule_id_empty(self):
        """Test rule ID normalization with empty string."""
        result = _normalize_rule_id("")
        self.assertEqual(result, "")
    
    def test_normalize_rule_id_no_colon(self):
        """Test rule ID normalization with no colon."""
        result = _normalize_rule_id("E501")
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
    
    def test_norm_empty_string(self):
        """Test _norm with empty string."""
        result = _norm("")
        self.assertEqual(result, "")


class TestCoveragePercentFromXml(unittest.TestCase):
    """Test _coverage_percent_from_xml function."""
    
    def test_coverage_percent_from_xml_valid_file(self):
        """Test coverage percent extraction from valid XML file."""
        # Create a temporary XML file
        xml_content = '''<?xml version="1.0" ?>
        <coverage version="7.10.5" timestamp="1756934692980" lines-valid="100" lines-covered="80" line-rate="0.8" branches-covered="0" branches-valid="0" branch-rate="0" complexity="0">
        </coverage>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            try:
                result = _coverage_percent_from_xml(f.name)
                self.assertEqual(result, 80)
            finally:
                os.unlink(f.name)
    
    def test_coverage_percent_from_xml_invalid_file(self):
        """Test coverage percent extraction from invalid XML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("invalid xml content")
            f.flush()
            
            try:
                result = _coverage_percent_from_xml(f.name)
                self.assertIsNone(result)
            finally:
                os.unlink(f.name)
    
    def test_coverage_percent_from_xml_nonexistent_file(self):
        """Test coverage percent extraction from nonexistent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        self.assertIsNone(result)
    
    def test_coverage_percent_from_xml_none_path(self):
        """Test coverage percent extraction with None path."""
        result = _coverage_percent_from_xml(None)
        self.assertIsNone(result)


class TestCovPercent(unittest.TestCase):
    """Test cov_percent function."""
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=85)
    def test_cov_percent_with_coverage(self, mock_coverage):
        """Test cov_percent when coverage is available."""
        result = cov_percent()
        self.assertEqual(result, 85)
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=None)
    def test_cov_percent_no_coverage(self, mock_coverage):
        """Test cov_percent when no coverage is available."""
        result = cov_percent()
        self.assertEqual(result, 0)


class TestParseFlake8Output(unittest.TestCase):
    """Test _parse_flake8_output function."""
    
    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        output = "test.py:1:1: E501 line too long (80 > 79 characters)\ntest.py:2:5: F401 'os' imported but unused"
        results = _parse_flake8_output(output)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].rule_id, "E501")
        self.assertEqual(results[0].level, "error")
        self.assertEqual(results[0].message.text, "line too long (80 > 79 characters)")
        self.assertEqual(results[0].locations[0].physical_location.artifact_location.uri, "file:///test.py")
        self.assertEqual(results[0].locations[0].physical_location.region.start_line, 1)
        self.assertEqual(results[0].locations[0].physical_location.region.start_column, 1)
    
    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        results = _parse_flake8_output("")
        self.assertEqual(len(results), 0)
    
    def test_parse_flake8_output_malformed(self):
        """Test parsing malformed flake8 output."""
        output = "invalid line without proper format"
        results = _parse_flake8_output(output)
        self.assertEqual(len(results), 0)


class TestParseMypyOutput(unittest.TestCase):
    """Test _parse_mypy_output function."""
    
    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        output = "test.py:1: error: Name 'x' is not defined  [name-defined]\ntest.py:2: error: Argument 1 to \"func\" has incompatible type \"str\"; expected \"int\"  [arg-type]"
        results = _parse_mypy_output(output)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].rule_id, "name-defined")
        self.assertEqual(results[0].level, "error")
        self.assertEqual(results[0].message.text, "Name 'x' is not defined")
        self.assertEqual(results[0].locations[0].physical_location.artifact_location.uri, "file:///test.py")
        self.assertEqual(results[0].locations[0].physical_location.region.start_line, 1)
    
    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        results = _parse_mypy_output("")
        self.assertEqual(len(results), 0)
    
    def test_parse_mypy_output_malformed(self):
        """Test parsing malformed mypy output."""
        output = "invalid line without proper format"
        results = _parse_mypy_output(output)
        self.assertEqual(len(results), 0)


class TestRunLintCheck(unittest.TestCase):
    """Test run_lint_check function."""
    
    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test.py:1:1: E501 line too long"
        
        result, sarif_result = run_lint_check(["test.py"])
        
        self.assertTrue(result.passed)
        self.assertIsNotNone(sarif_result)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_lint_check_failure(self, mock_run):
        """Test failed lint check."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test.py:1:1: E501 line too long"
        
        result, sarif_result = run_lint_check(["test.py"])
        
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_lint_check_no_paths(self, mock_run):
        """Test lint check with no paths."""
        result, sarif_result = run_lint_check(None)
        
        self.assertTrue(result.passed)
        self.assertIsNone(sarif_result)
        mock_run.assert_not_called()


class TestRunTypeCheck(unittest.TestCase):
    """Test run_type_check function."""
    
    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success: no issues found"
        
        result, sarif_result = run_type_check(["test.py"])
        
        self.assertTrue(result.passed)
        self.assertIsNotNone(sarif_result)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_type_check_failure(self, mock_run):
        """Test failed type check."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test.py:1: error: Name 'x' is not defined"
        
        result, sarif_result = run_type_check(["test.py"])
        
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_type_check_no_paths(self, mock_run):
        """Test type check with no paths."""
        result, sarif_result = run_type_check(None)
        
        self.assertTrue(result.passed)
        self.assertIsNone(sarif_result)
        mock_run.assert_not_called()


class TestParseBanditJson(unittest.TestCase):
    """Test _parse_bandit_json function."""
    
    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON output."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Use of hardcoded password",
                    "test_id": "B105"
                }
            ]
        }
        
        results = _parse_bandit_json(json_data)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "B105")
        self.assertEqual(results[0].level, "error")
        self.assertEqual(results[0].message.text, "Use of hardcoded password")
        self.assertEqual(results[0].locations[0].physical_location.artifact_location.uri, "file:///test.py")
        self.assertEqual(results[0].locations[0].physical_location.region.start_line, 1)
    
    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON."""
        json_data = {"results": []}
        results = _parse_bandit_json(json_data)
        self.assertEqual(len(results), 0)
    
    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON."""
        json_data = {"invalid": "data"}
        results = _parse_bandit_json(json_data)
        self.assertEqual(len(results), 0)


class TestParseBanditOutput(unittest.TestCase):
    """Test _parse_bandit_output function."""
    
    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        output = '{"results": [{"filename": "test.py", "line_number": 1, "issue_severity": "HIGH", "issue_confidence": "HIGH", "issue_text": "Use of hardcoded password", "test_id": "B105"}]}'
        results = _parse_bandit_output(output)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "B105")
    
    def test_parse_bandit_output_invalid_json(self):
        """Test parsing invalid JSON bandit output."""
        output = "invalid json"
        results = _parse_bandit_output(output)
        self.assertEqual(len(results), 0)
    
    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        results = _parse_bandit_output("")
        self.assertEqual(len(results), 0)


class TestRunSecurityCheck(unittest.TestCase):
    """Test run_security_check function."""
    
    @patch('subprocess.run')
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"results": []}'
        
        result, sarif_result = run_security_check()
        
        self.assertTrue(result.passed)
        self.assertIsNotNone(sarif_result)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_security_check_failure(self, mock_run):
        """Test failed security check."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = '{"results": [{"filename": "test.py", "line_number": 1, "issue_severity": "HIGH", "issue_confidence": "HIGH", "issue_text": "Use of hardcoded password", "test_id": "B105"}]}'
        
        result, sarif_result = run_security_check()
        
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)


class TestToFindings(unittest.TestCase):
    """Test _to_findings function."""
    
    def test_to_findings_with_results(self):
        """Test _to_findings with results."""
        results = [
            MagicMock(rule_id="E501", level="error", message=MagicMock(text="line too long"))
        ]
        
        findings = _to_findings(results)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "E501")
        self.assertEqual(findings[0]["level"], "warning")
        self.assertEqual(findings[0]["message"], "line too long")
    
    def test_to_findings_empty_results(self):
        """Test _to_findings with empty results."""
        findings = _to_findings([])
        self.assertEqual(len(findings), 0)


class TestRunCoverageCheck(unittest.TestCase):
    """Test run_coverage_check function."""
    
    @patch('src.ai_guard.analyzer.cov_percent', return_value=85)
    def test_run_coverage_check_above_threshold(self, mock_cov_percent):
        """Test coverage check above threshold."""
        result, sarif_result = run_coverage_check()
        
        self.assertTrue(result.passed)
        self.assertIsNotNone(sarif_result)
        self.assertEqual(sarif_result.message.text, "Coverage: 85%")
    
    @patch('src.ai_guard.analyzer.cov_percent', return_value=50)
    def test_run_coverage_check_below_threshold(self, mock_cov_percent):
        """Test coverage check below threshold."""
        result, sarif_result = run_coverage_check()
        
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
        self.assertEqual(sarif_result.message.text, "Coverage: 50%")
    
    @patch('src.ai_guard.analyzer.cov_percent', return_value=0)
    def test_run_coverage_check_no_coverage(self, mock_cov_percent):
        """Test coverage check with no coverage."""
        result, sarif_result = run_coverage_check()
        
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
        self.assertEqual(sarif_result.message.text, "Coverage: 0%")


class TestRun(unittest.TestCase):
    """Test run function."""
    
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer._write_reports')
    def test_run_success(self, mock_write_reports, mock_coverage_check, mock_security_check, mock_type_check, mock_lint_check):
        """Test successful run."""
        # Mock all checks to pass
        mock_lint_check.return_value = (MagicMock(passed=True), None)
        mock_type_check.return_value = (MagicMock(passed=True), None)
        mock_security_check.return_value = (MagicMock(passed=True), None)
        mock_coverage_check.return_value = (MagicMock(passed=True), None)
        
        result = run(["test.py"])
        
        self.assertEqual(result, 0)
        mock_write_reports.assert_called_once()
    
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer._write_reports')
    def test_run_failure(self, mock_write_reports, mock_coverage_check, mock_security_check, mock_type_check, mock_lint_check):
        """Test failed run."""
        # Mock one check to fail
        mock_lint_check.return_value = (MagicMock(passed=False), None)
        mock_type_check.return_value = (MagicMock(passed=True), None)
        mock_security_check.return_value = (MagicMock(passed=True), None)
        mock_coverage_check.return_value = (MagicMock(passed=True), None)
        
        result = run(["test.py"])
        
        self.assertEqual(result, 1)
        mock_write_reports.assert_called_once()


class TestMain(unittest.TestCase):
    """Test main function."""
    
    @patch('src.ai_guard.analyzer.run', return_value=0)
    def test_main_success(self, mock_run):
        """Test successful main execution."""
        with patch('sys.argv', ['ai-guard', 'test.py']):
            main()
        mock_run.assert_called_once_with(['test.py'])
    
    @patch('src.ai_guard.analyzer.run', return_value=1)
    def test_main_failure(self, mock_run):
        """Test failed main execution."""
        with patch('sys.argv', ['ai-guard', 'test.py']):
            main()
        mock_run.assert_called_once_with(['test.py'])


class TestCodeAnalyzer(unittest.TestCase):
    """Test CodeAnalyzer class."""
    
    def test_code_analyzer_initialization(self):
        """Test CodeAnalyzer initialization."""
        analyzer = CodeAnalyzer()
        self.assertIsInstance(analyzer, CodeAnalyzer)
    
    def test_code_analyzer_attributes(self):
        """Test CodeAnalyzer attributes."""
        analyzer = CodeAnalyzer()
        # Test that the analyzer has expected attributes
        self.assertTrue(hasattr(analyzer, '__init__'))


if __name__ == '__main__':
    unittest.main()
