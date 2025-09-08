"""
Basic test coverage for src/ai_guard/analyzer.py
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
    _get_changed_files,
    _get_git_diff,
    changed_python_files,
    _should_skip_file,
    _write_reports,
    _parse_coverage_output,
    _parse_sarif_output,
    _run_tool,
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
        """Test _rule_style returns TOOL when environment variable is 'tool'."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.TOOL)
    
    @patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'bare'})
    def test_rule_style_bare(self):
        """Test _rule_style returns BARE when environment variable is 'bare'."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.BARE)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_rule_style_default(self):
        """Test _rule_style returns BARE by default."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.BARE)
    
    @patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'invalid'})
    def test_rule_style_invalid(self):
        """Test _rule_style returns BARE for invalid values."""
        result = _rule_style()
        self.assertEqual(result, RuleIdStyle.BARE)


class TestMakeRuleId(unittest.TestCase):
    """Test _make_rule_id function."""
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_tool_style(self, mock_rule_style):
        """Test _make_rule_id with tool style."""
        result = _make_rule_id("flake8", "E501")
        self.assertEqual(result, "flake8:E501")
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.BARE)
    def test_make_rule_id_bare_style(self, mock_rule_style):
        """Test _make_rule_id with bare style."""
        result = _make_rule_id("flake8", "E501")
        self.assertEqual(result, "E501")
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_no_code(self, mock_rule_style):
        """Test _make_rule_id with no code."""
        result = _make_rule_id("flake8", None)
        self.assertEqual(result, "flake8:flake8")
    
    @patch('src.ai_guard.analyzer._rule_style', return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_empty_code(self, mock_rule_style):
        """Test _make_rule_id with empty code."""
        result = _make_rule_id("flake8", "")
        self.assertEqual(result, "flake8:flake8")


class TestStrictSubprocessFail(unittest.TestCase):
    """Test _strict_subprocess_fail function."""
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': '1'})
    def test_strict_subprocess_fail_true_1(self):
        """Test _strict_subprocess_fail returns True for '1'."""
        result = _strict_subprocess_fail()
        self.assertTrue(result)
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'true'})
    def test_strict_subprocess_fail_true_true(self):
        """Test _strict_subprocess_fail returns True for 'true'."""
        result = _strict_subprocess_fail()
        self.assertTrue(result)
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'yes'})
    def test_strict_subprocess_fail_true_yes(self):
        """Test _strict_subprocess_fail returns True for 'yes'."""
        result = _strict_subprocess_fail()
        self.assertTrue(result)
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'on'})
    def test_strict_subprocess_fail_true_on(self):
        """Test _strict_subprocess_fail returns True for 'on'."""
        result = _strict_subprocess_fail()
        self.assertTrue(result)
    
    @patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': 'false'})
    def test_strict_subprocess_fail_false(self):
        """Test _strict_subprocess_fail returns False for 'false'."""
        result = _strict_subprocess_fail()
        self.assertFalse(result)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_strict_subprocess_fail_default(self):
        """Test _strict_subprocess_fail returns False by default."""
        result = _strict_subprocess_fail()
        self.assertFalse(result)


class TestToText(unittest.TestCase):
    """Test _to_text function."""
    
    def test_to_text_none(self):
        """Test _to_text with None."""
        result = _to_text(None)
        self.assertEqual(result, "")
    
    def test_to_text_string(self):
        """Test _to_text with string."""
        result = _to_text("hello")
        self.assertEqual(result, "hello")
    
    def test_to_text_bytes(self):
        """Test _to_text with bytes."""
        result = _to_text(b"hello")
        self.assertEqual(result, "hello")
    
    def test_to_text_bytearray(self):
        """Test _to_text with bytearray."""
        result = _to_text(bytearray(b"hello"))
        self.assertEqual(result, "hello")
    
    def test_to_text_invalid_bytes(self):
        """Test _to_text with invalid bytes."""
        result = _to_text(b"\xff\xfe")
        self.assertEqual(result, "")
    
    def test_to_text_int(self):
        """Test _to_text with int."""
        result = _to_text(123)
        self.assertEqual(result, "123")
    
    def test_to_text_bytes_with_replacement_char(self):
        """Test _to_text with bytes containing replacement characters."""
        # Create bytes that decode to string with replacement characters
        result = _to_text(b'\xef\xbf\xbd')  # UTF-8 replacement character
        self.assertEqual(result, "")
    
    def test_to_text_unicode_decode_error(self):
        """Test _to_text with bytes that cause UnicodeDecodeError."""
        # Create bytes that can't be decoded as UTF-8
        result = _to_text(b'\xff\xfe\x00\x00')
        self.assertEqual(result, "")


class TestNormalizeRuleId(unittest.TestCase):
    """Test _normalize_rule_id function."""
    
    def test_normalize_rule_id_with_colon(self):
        """Test _normalize_rule_id with colon."""
        result = _normalize_rule_id("flake8:E501")
        self.assertEqual(result, "E501")
    
    def test_normalize_rule_id_without_colon(self):
        """Test _normalize_rule_id without colon."""
        result = _normalize_rule_id("E501")
        self.assertEqual(result, "E501")
    
    def test_normalize_rule_id_multiple_colons(self):
        """Test _normalize_rule_id with multiple colons."""
        result = _normalize_rule_id("tool:category:E501")
        self.assertEqual(result, "category:E501")


class TestNorm(unittest.TestCase):
    """Test _norm function."""
    
    def test_norm_none(self):
        """Test _norm with None."""
        result = _norm(None)
        self.assertEqual(result, "")
    
    def test_norm_string(self):
        """Test _norm with string."""
        result = _norm("hello")
        self.assertEqual(result, "hello")
    
    def test_norm_bytes(self):
        """Test _norm with bytes."""
        result = _norm(b"hello")
        self.assertEqual(result, "hello")
    
    def test_norm_bytearray(self):
        """Test _norm with bytearray."""
        result = _norm(bytearray(b"hello"))
        self.assertEqual(result, "hello")


class TestParseFlake8Output(unittest.TestCase):
    """Test _parse_flake8_output function."""
    
    def test_parse_flake8_output_empty(self):
        """Test _parse_flake8_output with empty output."""
        result = _parse_flake8_output("")
        self.assertEqual(result, [])
    
    def test_parse_flake8_output_single_line(self):
        """Test _parse_flake8_output with single line."""
        output = "src/test.py:1:1: E501 line too long (80 > 79 characters)"
        result = _parse_flake8_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "E501")
        self.assertEqual(result[0].message, "line too long (80 > 79 characters)")
        # Check location info
        self.assertIsNotNone(result[0].locations)
        self.assertEqual(len(result[0].locations), 1)
        loc = result[0].locations[0]
        self.assertEqual(loc["physicalLocation"]["artifactLocation"]["uri"], "src/test.py")
        self.assertEqual(loc["physicalLocation"]["region"]["startLine"], 1)
        self.assertEqual(loc["physicalLocation"]["region"]["startColumn"], 1)
    
    def test_parse_flake8_output_multiple_lines(self):
        """Test _parse_flake8_output with multiple lines."""
        output = """src/test.py:1:1: E501 line too long (80 > 79 characters)
src/test.py:2:5: W293 blank line contains whitespace"""
        result = _parse_flake8_output(output)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].rule_id, "E501")
        self.assertEqual(result[1].rule_id, "W293")
    
    def test_parse_flake8_output_invalid_line(self):
        """Test _parse_flake8_output with invalid line format."""
        output = "invalid line format"
        result = _parse_flake8_output(output)
        self.assertEqual(result, [])


class TestParseMypyOutput(unittest.TestCase):
    """Test _parse_mypy_output function."""
    
    def test_parse_mypy_output_empty(self):
        """Test _parse_mypy_output with empty output."""
        result = _parse_mypy_output("")
        self.assertEqual(result, [])
    
    def test_parse_mypy_output_single_line(self):
        """Test _parse_mypy_output with single line."""
        output = "src/test.py:1: error: Incompatible return type"
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "mypy-error")
        self.assertEqual(result[0].message, "Incompatible return type")
        # Check location info
        self.assertIsNotNone(result[0].locations)
        self.assertEqual(len(result[0].locations), 1)
        loc = result[0].locations[0]
        self.assertEqual(loc["physicalLocation"]["artifactLocation"]["uri"], "src/test.py")
        self.assertEqual(loc["physicalLocation"]["region"]["startLine"], 1)
    
    def test_parse_mypy_output_multiple_lines(self):
        """Test _parse_mypy_output with multiple lines."""
        output = """src/test.py:1: error: Incompatible return type
src/test.py:2: warning: Unused variable"""
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].rule_id, "mypy-error")
        self.assertEqual(result[1].rule_id, "mypy-error")
    
    def test_parse_mypy_output_with_bracketed_code(self):
        """Test _parse_mypy_output with bracketed code."""
        output = "src/test.py:1: error: Incompatible return type [name-defined]"
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "name-defined")  # Should use bare format for bracketed codes
        self.assertEqual(result[0].message, "Incompatible return type")
    
    def test_parse_mypy_output_with_column(self):
        """Test _parse_mypy_output with column information."""
        output = "src/test.py:1:5: error: Incompatible return type"
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "mypy-error")
        loc = result[0].locations[0]
        self.assertEqual(loc["physicalLocation"]["region"]["startColumn"], 5)
    
    def test_parse_mypy_output_invalid_severity(self):
        """Test _parse_mypy_output with invalid severity."""
        output = "src/test.py:1: info: Some information"
        result = _parse_mypy_output(output)
        self.assertEqual(result, [])  # Should skip invalid severity
    
    def test_parse_mypy_output_note_severity(self):
        """Test _parse_mypy_output with note severity."""
        output = "src/test.py:1: note: Some note"
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].level, "note")
    
    def test_parse_mypy_output_warning_severity(self):
        """Test _parse_mypy_output with warning severity."""
        output = "src/test.py:1: warning: Some warning"
        result = _parse_mypy_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].level, "warning")


class TestParseBanditOutput(unittest.TestCase):
    """Test _parse_bandit_output function."""
    
    def test_parse_bandit_output_empty(self):
        """Test _parse_bandit_output with empty output."""
        result = _parse_bandit_output("")
        self.assertEqual(result, [])
    
    def test_parse_bandit_output_single_line(self):
        """Test _parse_bandit_output with single line."""
        output = "bandit: src/test.py:1:1: B101: Use of assert detected"
        result = _parse_bandit_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "bandit:B101")
        self.assertEqual(result[0].message, "Sample bandit issue")
        # Check location info
        self.assertIsNotNone(result[0].locations)
        self.assertEqual(len(result[0].locations), 1)
        loc = result[0].locations[0]
        self.assertEqual(loc["physicalLocation"]["artifactLocation"]["uri"], "test.py")
        self.assertEqual(loc["physicalLocation"]["region"]["startLine"], 1)


class TestParseBanditJson(unittest.TestCase):
    """Test _parse_bandit_json function."""
    
    def test_parse_bandit_json_empty(self):
        """Test _parse_bandit_json with empty output."""
        result = _parse_bandit_json("")
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_valid_data(self):
        """Test _parse_bandit_json with valid JSON data."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 5,
                    "issue_text": "Use of assert detected",
                    "test_id": "B101"
                }
            ]
        }
        result = _parse_bandit_json(json.dumps(json_data))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "B101")  # Should be bare format by default
        self.assertEqual(result[0].message, "Use of assert detected")
        self.assertEqual(result[0].level, "warning")
    
    def test_parse_bandit_json_invalid_json(self):
        """Test _parse_bandit_json with invalid JSON."""
        result = _parse_bandit_json("invalid json")
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_bytes_input(self):
        """Test _parse_bandit_json with bytes input."""
        json_data = b'{"results": []}'
        result = _parse_bandit_json(json_data)
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_no_results(self):
        """Test _parse_bandit_json with no results."""
        json_data = {"results": []}
        result = _parse_bandit_json(json.dumps(json_data))
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_non_string_input(self):
        """Test _parse_bandit_json with non-string input."""
        result = _parse_bandit_json(123)
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_bytearray_input(self):
        """Test _parse_bandit_json with bytearray input."""
        json_data = bytearray(b'{"results": []}')
        result = _parse_bandit_json(json_data)
        self.assertEqual(result, [])
    
    def test_parse_bandit_json_with_test_name(self):
        """Test _parse_bandit_json with test_name instead of test_id."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 5,
                    "issue_text": "Use of assert detected",
                    "test_name": "B102"
                }
            ]
        }
        result = _parse_bandit_json(json.dumps(json_data))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "B102")
    
    def test_parse_bandit_json_no_test_id_or_name(self):
        """Test _parse_bandit_json with no test_id or test_name."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 5,
                    "issue_text": "Use of assert detected"
                }
            ]
        }
        result = _parse_bandit_json(json.dumps(json_data))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "bandit")
    
    def test_parse_bandit_json_missing_fields(self):
        """Test _parse_bandit_json with missing fields."""
        json_data = {
            "results": [
                {
                    "filename": "src/test.py"
                }
            ]
        }
        result = _parse_bandit_json(json.dumps(json_data))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rule_id, "bandit")
        self.assertEqual(result[0].message, "")
        self.assertEqual(result[0].locations[0]["physicalLocation"]["region"]["startLine"], 1)


class TestCoveragePercentFromXml(unittest.TestCase):
    """Test _coverage_percent_from_xml function."""
    
    def setUp(self):
        """Clear cache before each test."""
        from src.ai_guard.performance import clear_performance_data
        clear_performance_data()
    
    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_line_rate(self, mock_parse, mock_exists):
        """Test _coverage_percent_from_xml with line-rate attribute."""
        # Mock that only our test file exists
        def mock_exists_side_effect(path):
            return path == "test_coverage.xml"
        mock_exists.side_effect = mock_exists_side_effect
        
        mock_root = MagicMock()
        mock_root.attrib = {"line-rate": "0.85"}
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        result = _coverage_percent_from_xml("test_coverage.xml")
        self.assertEqual(result, 85)
    
    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_counters(self, mock_parse, mock_exists):
        """Test _coverage_percent_from_xml with counter elements."""
        mock_exists.return_value = True
        mock_root = MagicMock()
        mock_root.attrib = {}
        
        # Mock counter elements
        counter1 = MagicMock()
        counter1.attrib = {"type": "LINE", "covered": "80", "missed": "20"}
        counter2 = MagicMock()
        counter2.attrib = {"type": "BRANCH", "covered": "10", "missed": "5"}
        
        mock_root.findall.return_value = [counter1, counter2]
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        result = _coverage_percent_from_xml("test_coverage.xml")
        self.assertEqual(result, 80)  # 80/(80+20) = 80%
    
    @patch('os.path.exists')
    def test_coverage_percent_from_xml_file_not_found(self, mock_exists):
        """Test _coverage_percent_from_xml when file doesn't exist."""
        mock_exists.return_value = False
        result = _coverage_percent_from_xml("nonexistent.xml")
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'AI_GUARD_TEST_MODE': '1'})
    def test_coverage_percent_from_xml_test_mode(self):
        """Test _coverage_percent_from_xml in test mode."""
        result = _coverage_percent_from_xml(None)
        self.assertIsNone(result)
    
    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_exception(self, mock_parse, mock_exists):
        """Test _coverage_percent_from_xml with parsing exception."""
        # Mock that only our test file exists
        def mock_exists_side_effect(path):
            return path == "test_coverage.xml"
        mock_exists.side_effect = mock_exists_side_effect
        
        mock_parse.side_effect = Exception("Parse error")
        
        result = _coverage_percent_from_xml("test_coverage.xml")
        self.assertIsNone(result)
    
    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_value_error(self, mock_parse, mock_exists):
        """Test _coverage_percent_from_xml with ValueError in line-rate conversion."""
        mock_exists.return_value = True
        mock_root = MagicMock()
        mock_root.attrib = {"line-rate": "invalid"}
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        result = _coverage_percent_from_xml("test_coverage.xml")
        self.assertIsNone(result)
    
    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_no_line_counters(self, mock_parse, mock_exists):
        """Test _coverage_percent_from_xml with no LINE type counters."""
        mock_exists.return_value = True
        mock_root = MagicMock()
        mock_root.attrib = {}
        
        # Mock counter elements with non-LINE type
        counter1 = MagicMock()
        counter1.attrib = {"type": "BRANCH", "covered": "10", "missed": "5"}
        
        mock_root.findall.return_value = [counter1]
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        result = _coverage_percent_from_xml("test_coverage.xml")
        self.assertIsNone(result)
    
    @patch('os.path.exists')
    @patch('defusedxml.ElementTree.parse')
    def test_coverage_percent_from_xml_zero_total(self, mock_parse, mock_exists):
        """Test _coverage_percent_from_xml with zero total lines."""
        mock_exists.return_value = True
        mock_root = MagicMock()
        mock_root.attrib = {}
        
        # Mock counter elements with zero total
        counter1 = MagicMock()
        counter1.attrib = {"type": "LINE", "covered": "0", "missed": "0"}
        
        mock_root.findall.return_value = [counter1]
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        result = _coverage_percent_from_xml("test_coverage.xml")
        self.assertIsNone(result)


class TestCovPercent(unittest.TestCase):
    """Test cov_percent function."""
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_with_result(self, mock_coverage):
        """Test cov_percent with valid result."""
        mock_coverage.return_value = 85
        result = cov_percent()
        self.assertEqual(result, 85)
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_with_none(self, mock_coverage):
        """Test cov_percent with None result."""
        mock_coverage.return_value = None
        result = cov_percent()
        self.assertEqual(result, 0)


class TestToFindings(unittest.TestCase):
    """Test _to_findings function."""
    
    def test_to_findings_empty_list(self):
        """Test _to_findings with empty list."""
        result = _to_findings([])
        self.assertEqual(result, [])
    
    def test_to_findings_with_dict_locations(self):
        """Test _to_findings with dictionary locations."""
        from src.ai_guard.sarif_report import SarifResult
        sarif_result = SarifResult(
            rule_id="E501",
            level="error",
            message="line too long",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "src/test.py"},
                    "region": {"startLine": 5}
                }
            }]
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "E501")
        self.assertEqual(result[0]["level"], "warning")  # error converted to warning
        self.assertEqual(result[0]["message"], "line too long")
        self.assertEqual(result[0]["path"], "src/test.py")
        self.assertEqual(result[0]["line"], 5)
    
    def test_to_findings_with_object_locations(self):
        """Test _to_findings with object locations."""
        from src.ai_guard.sarif_report import SarifResult
        from src.ai_guard.analyzer import ArtifactLocation, Region, PhysicalLocation, Location
        
        artifact = ArtifactLocation(uri="src/test.py")
        region = Region(start_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        
        sarif_result = SarifResult(
            rule_id="W293",
            level="warning",
            message="blank line contains whitespace",
            locations=[location]
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "W293")
        self.assertEqual(result[0]["path"], "src/test.py")
        self.assertEqual(result[0]["line"], 10)
    
    def test_to_findings_with_object_locations_no_region(self):
        """Test _to_findings with object locations but no region."""
        from src.ai_guard.sarif_report import SarifResult
        from src.ai_guard.analyzer import ArtifactLocation, PhysicalLocation, Location
        
        artifact = ArtifactLocation(uri="src/test.py")
        physical = PhysicalLocation(artifact_location=artifact, region=None)
        location = Location(physical_location=physical)
        
        sarif_result = SarifResult(
            rule_id="W293",
            level="warning",
            message="blank line contains whitespace",
            locations=[location]
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "W293")
        self.assertEqual(result[0]["path"], "src/test.py")
        self.assertIsNone(result[0]["line"])
    
    def test_to_findings_with_dict_locations_missing_region(self):
        """Test _to_findings with dictionary locations missing region."""
        from src.ai_guard.sarif_report import SarifResult
        sarif_result = SarifResult(
            rule_id="E501",
            level="error",
            message="line too long",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "src/test.py"}
                    # Missing region
                }
            }]
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "E501")
        self.assertEqual(result[0]["level"], "warning")  # error converted to warning
        self.assertEqual(result[0]["message"], "line too long")
        self.assertEqual(result[0]["path"], "src/test.py")
        self.assertIsNone(result[0]["line"])
    
    def test_to_findings_with_dict_locations_missing_artifact(self):
        """Test _to_findings with dictionary locations missing artifact."""
        from src.ai_guard.sarif_report import SarifResult
        sarif_result = SarifResult(
            rule_id="E501",
            level="error",
            message="line too long",
            locations=[{
                "physicalLocation": {
                    "region": {"startLine": 5}
                    # Missing artifactLocation
                }
            }]
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "E501")
        self.assertEqual(result[0]["level"], "warning")  # error converted to warning
        self.assertEqual(result[0]["message"], "line too long")
        self.assertEqual(result[0]["path"], "unknown")
        self.assertEqual(result[0]["line"], 5)
    
    def test_to_findings_with_empty_locations(self):
        """Test _to_findings with empty locations."""
        from src.ai_guard.sarif_report import SarifResult
        sarif_result = SarifResult(
            rule_id="E501",
            level="error",
            message="line too long",
            locations=[]
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "E501")
        self.assertEqual(result[0]["level"], "warning")  # error converted to warning
        self.assertEqual(result[0]["message"], "line too long")
        self.assertEqual(result[0]["path"], "unknown")
        self.assertIsNone(result[0]["line"])
    
    def test_to_findings_with_none_locations(self):
        """Test _to_findings with None locations."""
        from src.ai_guard.sarif_report import SarifResult
        sarif_result = SarifResult(
            rule_id="E501",
            level="error",
            message="line too long",
            locations=None
        )
        result = _to_findings([sarif_result])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "E501")
        self.assertEqual(result[0]["level"], "warning")  # error converted to warning
        self.assertEqual(result[0]["message"], "line too long")
        self.assertEqual(result[0]["path"], "unknown")
        self.assertIsNone(result[0]["line"])


class TestShouldSkipFile(unittest.TestCase):
    """Test _should_skip_file function."""
    
    def test_should_skip_file_python(self):
        """Test _should_skip_file with Python file."""
        result = _should_skip_file("src/test.py")
        self.assertFalse(result)
    
    def test_should_skip_file_non_python(self):
        """Test _should_skip_file with non-Python file."""
        result = _should_skip_file("src/test.txt")
        self.assertTrue(result)
    
    def test_should_skip_file_test_file(self):
        """Test _should_skip_file with test file."""
        result = _should_skip_file("tests/test_test.py")
        self.assertTrue(result)
    
    def test_should_skip_file_ends_with_test(self):
        """Test _should_skip_file with file ending in _test.py."""
        result = _should_skip_file("src/module_test.py")
        self.assertTrue(result)


class TestCodeAnalyzer(unittest.TestCase):
    """Test CodeAnalyzer class."""
    
    @patch('src.ai_guard.analyzer.load_config')
    def test_code_analyzer_init_default_config(self, mock_load_config):
        """Test CodeAnalyzer initialization with default config."""
        mock_load_config.return_value = {"min_coverage": 80}
        analyzer = CodeAnalyzer()
        self.assertEqual(analyzer.config, {"min_coverage": 80})
    
    def test_code_analyzer_init_custom_config(self):
        """Test CodeAnalyzer initialization with custom config."""
        config = {"min_coverage": 90}
        analyzer = CodeAnalyzer(config)
        self.assertEqual(analyzer.config, config)
    
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    def test_run_all_checks(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test run_all_checks method."""
        from src.ai_guard.report import GateResult
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85%"), None)
        
        analyzer = CodeAnalyzer({"min_coverage": 80})
        results = analyzer.run_all_checks(["src/test.py"])
        
        self.assertEqual(len(results), 4)
        self.assertTrue(all(result.passed for result in results))
        mock_lint.assert_called_once_with(["src/test.py"])
        mock_type.assert_called_once_with(["src/test.py"])
        mock_security.assert_called_once()
        mock_coverage.assert_called_once_with(80)


class TestParseCoverageOutput(unittest.TestCase):
    """Test _parse_coverage_output function."""
    
    def test_parse_coverage_output_empty(self):
        """Test _parse_coverage_output with empty output."""
        result = _parse_coverage_output("")
        self.assertEqual(result, 0)
    
    def test_parse_coverage_output_with_coverage(self):
        """Test _parse_coverage_output with coverage data."""
        output = "TOTAL 84%"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 84)
    
    def test_parse_coverage_output_coverage_pattern(self):
        """Test _parse_coverage_output with 'Coverage:' pattern."""
        output = "Coverage: 75%"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 75)
    
    def test_parse_coverage_output_total_coverage_pattern(self):
        """Test _parse_coverage_output with 'Total coverage:' pattern."""
        output = "Total coverage: 90%"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 90)
    
    def test_parse_coverage_output_coverage_percent_pattern(self):
        """Test _parse_coverage_output with 'coverage X%' pattern."""
        output = "coverage 65%"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 65)
    
    def test_parse_coverage_output_percent_coverage_pattern(self):
        """Test _parse_coverage_output with 'X% coverage' pattern."""
        output = "85% coverage"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 85)
    
    def test_parse_coverage_output_percent_total_pattern(self):
        """Test _parse_coverage_output with 'X% total' pattern."""
        output = "70% total"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 70)
    
    def test_parse_coverage_output_line_by_line(self):
        """Test _parse_coverage_output with line-by-line coverage."""
        output = "file.py: 100 lines, 80 covered\nother.py: 50 lines, 30 covered"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 73)  # (80+30)/(100+50) = 110/150 = 73%
    
    def test_parse_coverage_output_no_match(self):
        """Test _parse_coverage_output with no matching patterns."""
        output = "No coverage information found"
        result = _parse_coverage_output(output)
        self.assertEqual(result, 0)
    
    def test_parse_coverage_output_exception(self):
        """Test _parse_coverage_output with exception during parsing."""
        # This should not raise an exception
        result = _parse_coverage_output(None)
        self.assertEqual(result, 0)


class TestWriteReports(unittest.TestCase):
    """Test _write_reports function."""
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_sarif(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with SARIF format."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "sarif", "report_path": "test.sarif"}
        
        _write_reports(issues, config)
        mock_sarif.assert_called_once()
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_json(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with JSON format."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "json", "report_path": "test.json"}
        
        _write_reports(issues, config)
        mock_json.assert_called_once()
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_html(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with HTML format."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "html", "report_path": "test.html"}
        
        _write_reports(issues, config)
        mock_html.assert_called_once()
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_default_paths(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with default paths."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "sarif"}  # No report_path specified
        
        _write_reports(issues, config)
        mock_sarif.assert_called_once()
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_exception(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with exception."""
        mock_sarif.side_effect = Exception("Write error")
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "sarif", "report_path": "test.sarif"}
        
        # Should not raise exception
        _write_reports(issues, config)


class TestRunCoverageCheck(unittest.TestCase):
    """Test run_coverage_check function."""
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_success(self, mock_cov_percent):
        """Test run_coverage_check with successful execution."""
        mock_cov_percent.return_value = 85
        
        result, sarif_result = run_coverage_check(80)
        self.assertTrue(result.passed)
        self.assertIn("85.0%", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_failure(self, mock_cov_percent):
        """Test run_coverage_check with failed execution."""
        mock_cov_percent.return_value = 70
        
        result, sarif_result = run_coverage_check(80)
        self.assertFalse(result.passed)
        self.assertIn("70.0%", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_no_minimum(self, mock_cov_percent):
        """Test run_coverage_check with no minimum coverage."""
        mock_cov_percent.return_value = 75
        
        result, sarif_result = run_coverage_check(None)
        self.assertTrue(result.passed)
        self.assertIn("75.0%", result.details)
        self.assertIn("no minimum set", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_zero_minimum(self, mock_cov_percent):
        """Test run_coverage_check with zero minimum coverage."""
        mock_cov_percent.return_value = 50
        
        result, sarif_result = run_coverage_check(0)
        self.assertTrue(result.passed)
        self.assertIn("50.0%", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_none_coverage(self, mock_cov_percent):
        """Test run_coverage_check with None coverage."""
        mock_cov_percent.return_value = None
        
        result, sarif_result = run_coverage_check(80)
        self.assertFalse(result.passed)
        self.assertIn("No coverage data", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_none_coverage_zero_minimum(self, mock_cov_percent):
        """Test run_coverage_check with None coverage and zero minimum."""
        mock_cov_percent.return_value = None
        
        result, sarif_result = run_coverage_check(0)
        self.assertFalse(result.passed)
        self.assertIn("No coverage data", result.details)
        self.assertIsNone(sarif_result)


class TestRunFunction(unittest.TestCase):
    """Test run function."""
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_success(self, mock_exit, mock_pytest, mock_write_sarif, mock_coverage, 
                        mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with successful execution."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        result = run(['ai-guard', '--min-cov', '80'])
        self.assertEqual(result, 0)
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_lint_failure(self, mock_exit, mock_pytest, mock_write_sarif, mock_lint, 
                             mock_changed_files, mock_config):
        """Test run function with lint failure."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", False, "E501 line too long"), None)
        mock_pytest.return_value = 0
        
        result = run(['ai-guard', '--min-cov', '80'])
        self.assertEqual(result, 1)
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_skip_tests(self, mock_exit, mock_pytest, mock_write_sarif, mock_coverage, 
                           mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with skip tests."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        
        result = run(['ai-guard', '--skip-tests'])
        self.assertEqual(result, 0)
        mock_pytest.assert_not_called()
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_json_format(self, mock_exit, mock_pytest, mock_write_json, mock_coverage, 
                            mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with JSON format."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        result = run(['ai-guard', '--report-format', 'json', '--report-path', 'test.json'])
        self.assertEqual(result, 0)
        mock_write_json.assert_called_once()
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_html')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_html_format(self, mock_exit, mock_pytest, mock_write_html, mock_coverage, 
                            mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with HTML format."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        result = run(['ai-guard', '--report-format', 'html', '--report-path', 'test.html'])
        self.assertEqual(result, 0)
        mock_write_html.assert_called_once()
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_deprecated_sarif_arg(self, mock_exit, mock_pytest, mock_write_sarif, mock_coverage, 
                                     mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with deprecated --sarif argument."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        result = run(['ai-guard', '--sarif', 'test.sarif'])
        self.assertEqual(result, 0)
        mock_write_sarif.assert_called_once()
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_with_event_file(self, mock_exit, mock_pytest, mock_write_sarif, mock_coverage, 
                                mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with event file."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=1024):
                result = run(['ai-guard', '--event', 'event.json'])
                self.assertEqual(result, 0)
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('sys.exit')
    def test_run_with_event_file_error(self, mock_exit, mock_pytest, mock_write_sarif, mock_coverage, 
                                      mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with event file error."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        def mock_exists_side_effect(path):
            if path == "event.json":
                raise Exception("Permission denied")
            return False  # Default for other paths
        
        with patch('os.path.exists', side_effect=mock_exists_side_effect):
            result = run(['ai-guard', '--event', 'event.json'])
            self.assertEqual(result, 0)
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    def test_run_unknown_report_format(self, mock_pytest, mock_write_sarif, mock_coverage, 
                                      mock_security, mock_type, mock_lint, mock_changed_files, mock_config):
        """Test run function with unknown report format."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        with patch('sys.stderr') as mock_stderr:
            with patch('sys.exit') as mock_sys_exit:
                mock_sys_exit.side_effect = SystemExit(2)  # Make sys.exit raise SystemExit
                with self.assertRaises(SystemExit) as cm:
                    run(['ai-guard', '--report-format', 'unknown'])
                self.assertEqual(cm.exception.code, 2)


class TestParseSarifOutput(unittest.TestCase):
    """Test _parse_sarif_output function."""
    
    def test_parse_sarif_output_empty(self):
        """Test _parse_sarif_output with empty output."""
        result = _parse_sarif_output("")
        self.assertEqual(result, [])
    
    def test_parse_sarif_output_valid_json(self):
        """Test _parse_sarif_output with valid JSON."""
        sarif_data = {
            "runs": [{
                "results": [{
                    "ruleId": "E501",
                    "message": {"text": "line too long"},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": "src/test.py"},
                            "region": {"startLine": 1, "startColumn": 1}
                        }
                    }]
                }]
            }]
        }
        output = json.dumps(sarif_data)
        result = _parse_sarif_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["ruleId"], "E501")
        self.assertEqual(result[0]["message"]["text"], "line too long")
        self.assertEqual(result[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "src/test.py")
        self.assertEqual(result[0]["locations"][0]["physicalLocation"]["region"]["startLine"], 1)
        self.assertEqual(result[0]["locations"][0]["physicalLocation"]["region"]["startColumn"], 1)
    
    def test_parse_sarif_output_invalid_json(self):
        """Test _parse_sarif_output with invalid JSON."""
        result = _parse_sarif_output("invalid json")
        self.assertEqual(result, [])
    
    def test_parse_sarif_output_no_runs(self):
        """Test _parse_sarif_output with no runs."""
        sarif_data = {}
        output = json.dumps(sarif_data)
        result = _parse_sarif_output(output)
        self.assertEqual(result, [])
    
    def test_parse_sarif_output_empty_runs(self):
        """Test _parse_sarif_output with empty runs."""
        sarif_data = {"runs": []}
        output = json.dumps(sarif_data)
        result = _parse_sarif_output(output)
        self.assertEqual(result, [])
    
    def test_parse_sarif_output_non_dict_run(self):
        """Test _parse_sarif_output with non-dict run."""
        sarif_data = {"runs": ["not a dict"]}
        output = json.dumps(sarif_data)
        result = _parse_sarif_output(output)
        self.assertEqual(result, [])
    
    def test_parse_sarif_output_no_results(self):
        """Test _parse_sarif_output with no results."""
        sarif_data = {"runs": [{}]}
        output = json.dumps(sarif_data)
        result = _parse_sarif_output(output)
        self.assertEqual(result, [])
    
    def test_parse_sarif_output_non_list_results(self):
        """Test _parse_sarif_output with non-list results."""
        sarif_data = {"runs": [{"results": "not a list"}]}
        output = json.dumps(sarif_data)
        result = _parse_sarif_output(output)
        self.assertEqual(result, [])


class TestRunTool(unittest.TestCase):
    """Test _run_tool function."""
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_success(self, mock_run_cmd):
        """Test _run_tool with successful execution."""
        mock_run_cmd.return_value = (0, "output")
        
        result = _run_tool(["flake8", "src/"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "output")
        self.assertEqual(result.stderr, "")
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_failure(self, mock_run_cmd):
        """Test _run_tool with failed execution."""
        mock_run_cmd.return_value = (1, "output")
        
        result = _run_tool(["flake8", "src/"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "output")
        self.assertEqual(result.stderr, "")
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_exception(self, mock_run_cmd):
        """Test _run_tool with exception."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError
        mock_run_cmd.side_effect = ToolExecutionError("Command failed")
        
        result = _run_tool(["flake8", "src/"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Command failed", result.stderr)


class TestRunLintCheck(unittest.TestCase):
    """Test run_lint_check function."""
    
    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test run_lint_check with successful execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["flake8", "src/test.py"], 0, "", ""
        )
        
        result, sarif_result = run_lint_check(["src/test.py"])
        self.assertTrue(result.passed)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_lint_check_with_issues(self, mock_run):
        """Test run_lint_check with issues found."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["flake8", "src/test.py"], 1, "src/test.py:1:1: E501 line too long", ""
        )
        
        result, sarif_result = run_lint_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_lint_check_file_not_found(self, mock_run):
        """Test run_lint_check with FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("flake8 not found")
        
        result, sarif_result = run_lint_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertIn("Tool not found", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_lint_check_error_no_parseable_output(self, mock_run):
        """Test run_lint_check with error but no parseable output."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["flake8", "src/test.py"], 1, "", "flake8 error message"
        )
        
        result, sarif_result = run_lint_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertIn("flake8 error", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_lint_check_with_issues_and_message(self, mock_run):
        """Test run_lint_check with issues and message in result."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["flake8", "src/test.py"], 1, "src/test.py:1:1: E501 line too long", ""
        )
        
        result, sarif_result = run_lint_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertEqual(result.details, "line too long")
        self.assertIsNotNone(sarif_result)


class TestRunTypeCheck(unittest.TestCase):
    """Test run_type_check function."""
    
    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test run_type_check with successful execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["mypy", "src/test.py"], 0, "", ""
        )
        
        result, sarif_result = run_type_check(["src/test.py"])
        self.assertTrue(result.passed)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_type_check_with_issues(self, mock_run):
        """Test run_type_check with issues found."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["mypy", "src/test.py"], 1, "src/test.py:1: error: Incompatible return type", ""
        )
        
        result, sarif_result = run_type_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_type_check_file_not_found(self, mock_run):
        """Test run_type_check with FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("mypy not found")
        
        result, sarif_result = run_type_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertIn("Tool not found", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_type_check_error_no_parseable_output(self, mock_run):
        """Test run_type_check with error but no parseable output."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["mypy", "src/test.py"], 1, "", "mypy error message"
        )
        
        result, sarif_result = run_type_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertIn("mypy error", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_type_check_with_issues_and_message(self, mock_run):
        """Test run_type_check with issues and message in result."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["mypy", "src/test.py"], 1, "src/test.py:1: error: Incompatible return type", ""
        )
        
        result, sarif_result = run_type_check(["src/test.py"])
        self.assertFalse(result.passed)
        self.assertEqual(result.details, "Incompatible return type")
        self.assertIsNotNone(sarif_result)


class TestRunSecurityCheck(unittest.TestCase):
    """Test run_security_check function."""
    
    @patch('subprocess.run')
    def test_run_security_check_success(self, mock_run):
        """Test run_security_check with successful execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["bandit", "-q", "-r", "src", "-f", "json", "-c", ".bandit"], 0, '{"results": []}', ""
        )
        
        result, sarif_result = run_security_check()
        self.assertTrue(result.passed)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_security_check_with_issues(self, mock_run):
        """Test run_security_check with issues found."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["bandit", "-q", "-r", "src", "-f", "json", "-c", ".bandit"], 1, 
            '{"results": [{"filename": "src/test.py", "line_number": 1, "issue_text": "Use of assert detected", "test_id": "B101"}]}', ""
        )
        
        result, sarif_result = run_security_check()
        self.assertFalse(result.passed)
        self.assertIsNotNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_security_check_file_not_found(self, mock_run):
        """Test run_security_check with FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("bandit not found")
        
        result, sarif_result = run_security_check()
        self.assertFalse(result.passed)
        self.assertIn("Tool not found", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_security_check_error_no_parseable_output(self, mock_run):
        """Test run_security_check with error but no parseable output."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["bandit", "-q", "-r", "src", "-f", "json", "-c", ".bandit"], 1, "", "bandit error message"
        )
        
        result, sarif_result = run_security_check()
        self.assertFalse(result.passed)
        self.assertIn("bandit error", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_security_check_with_issues_and_message(self, mock_run):
        """Test run_security_check with issues and message in result."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["bandit", "-q", "-r", "src", "-f", "json", "-c", ".bandit"], 1, 
            '{"results": [{"filename": "src/test.py", "line_number": 1, "issue_text": "Use of assert detected", "test_id": "B101"}]}', ""
        )
        
        result, sarif_result = run_security_check()
        self.assertFalse(result.passed)
        self.assertEqual(result.details, "Use of assert detected")
        self.assertIsNotNone(sarif_result)
    
    @patch('subprocess.run')
    def test_run_security_check_zero_returncode_with_issues(self, mock_run):
        """Test run_security_check with zero returncode but issues found."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["bandit", "-q", "-r", "src", "-f", "json", "-c", ".bandit"], 0, 
            '{"results": [{"filename": "src/test.py", "line_number": 1, "issue_text": "Use of assert detected", "test_id": "B101"}]}', ""
        )
        
        result, sarif_result = run_security_check()
        self.assertFalse(result.passed)  # Should fail because issues were found
        self.assertIsNotNone(sarif_result)


class TestRunCoverageCheck(unittest.TestCase):
    """Test run_coverage_check function."""
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_success(self, mock_cov_percent):
        """Test run_coverage_check with successful execution."""
        mock_cov_percent.return_value = 85
        
        result, sarif_result = run_coverage_check(80)
        self.assertTrue(result.passed)
        self.assertIn("85.0%", result.details)
        self.assertIsNone(sarif_result)
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_failure(self, mock_cov_percent):
        """Test run_coverage_check with failed execution."""
        mock_cov_percent.return_value = 70
        
        result, sarif_result = run_coverage_check(80)
        self.assertFalse(result.passed)
        self.assertIn("70.0%", result.details)
        self.assertIsNone(sarif_result)


class TestWriteReports(unittest.TestCase):
    """Test _write_reports function."""
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_sarif(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with SARIF format."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "sarif", "report_path": "test.sarif"}
        
        _write_reports(issues, config)
        mock_sarif.assert_called_once()
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_json(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with JSON format."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "json", "report_path": "test.json"}
        
        _write_reports(issues, config)
        mock_json.assert_called_once()
    
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.write_json')
    @patch('src.ai_guard.analyzer.write_html')
    def test_write_reports_html(self, mock_html, mock_json, mock_sarif):
        """Test _write_reports with HTML format."""
        issues = [{"rule_id": "E501", "message": "line too long", "path": "test.py", "line": 1}]
        config = {"report_format": "html", "report_path": "test.html"}
        
        _write_reports(issues, config)
        mock_html.assert_called_once()


class TestGetGitDiff(unittest.TestCase):
    """Test _get_git_diff function."""
    
    @patch('subprocess.run')
    def test_get_git_diff_success(self, mock_run):
        """Test _get_git_diff with successful execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["git", "diff"], 0, "diff --git a/src/test.py b/src/test.py", ""
        )
        
        result = _get_git_diff()
        self.assertEqual(result, "diff --git a/src/test.py b/src/test.py")
    
    @patch('subprocess.run')
    def test_get_git_diff_failure(self, mock_run):
        """Test _get_git_diff with failed execution."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        result = _get_git_diff()
        self.assertEqual(result, "")


class TestGetChangedFiles(unittest.TestCase):
    """Test _get_changed_files function."""
    
    @patch('subprocess.run')
    def test_get_changed_files_success(self, mock_run):
        """Test _get_changed_files with successful execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["git", "diff", "--name-only"], 0, "src/test.py\nsrc/other.py", ""
        )
        
        result = _get_changed_files()
        self.assertEqual(result, ["src/test.py", "src/other.py"])
    
    @patch('subprocess.run')
    def test_get_changed_files_no_git(self, mock_run):
        """Test _get_changed_files with no git repository."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        result = _get_changed_files()
        self.assertEqual(result, [])


class TestShouldSkipFile(unittest.TestCase):
    """Test _should_skip_file function."""
    
    def test_should_skip_file_python(self):
        """Test _should_skip_file with Python file."""
        result = _should_skip_file("src/test.py")
        self.assertFalse(result)
    
    def test_should_skip_file_non_python(self):
        """Test _should_skip_file with non-Python file."""
        result = _should_skip_file("src/test.txt")
        self.assertTrue(result)
    
    def test_should_skip_file_test_file(self):
        """Test _should_skip_file with test file."""
        result = _should_skip_file("tests/test_test.py")
        self.assertTrue(result)


class TestDataclasses(unittest.TestCase):
    """Test dataclasses."""
    
    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="src/test.py")
        self.assertEqual(location.uri, "src/test.py")
    
    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=1, start_column=5)
        self.assertEqual(region.start_line, 1)
        self.assertEqual(region.start_column, 5)
    
    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="src/test.py")
        region = Region(start_line=1, start_column=5)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        self.assertEqual(location.artifact_location.uri, "src/test.py")
        self.assertEqual(location.region.start_line, 1)
    
    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="src/test.py")
        region = Region(start_line=1, start_column=5)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        self.assertEqual(location.physical_location.artifact_location.uri, "src/test.py")


class TestMain(unittest.TestCase):
    """Test main function."""
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    def test_main_success(self, mock_pytest, mock_write_sarif, mock_coverage, mock_security, 
                         mock_type, mock_lint, mock_changed_files, mock_config):
        """Test main function with successful execution."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        with patch('sys.argv', ['ai-guard']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    def test_main_lint_failure(self, mock_pytest, mock_write_sarif, mock_coverage, mock_security, 
                              mock_type, mock_lint, mock_changed_files, mock_config):
        """Test main function with lint failure."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 80}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", False, "E501 line too long"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", True, "85% >= 80%"), None)
        mock_pytest.return_value = 0
        
        with patch('sys.argv', ['ai-guard']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)
    
    @patch('src.ai_guard.analyzer.load_config')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    def test_main_coverage_failure(self, mock_pytest, mock_write_sarif, mock_coverage, mock_security, 
                                  mock_type, mock_lint, mock_changed_files, mock_config):
        """Test main function with coverage failure."""
        from src.ai_guard.report import GateResult
        mock_config.return_value = {"min_coverage": 90}
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint.return_value = (GateResult("Lint", True, "No issues"), None)
        mock_type.return_value = (GateResult("Type", True, "No issues"), None)
        mock_security.return_value = (GateResult("Security", True, "No issues"), None)
        mock_coverage.return_value = (GateResult("Coverage", False, "85% >= 90%"), None)
        mock_pytest.return_value = 0
        
        with patch('sys.argv', ['ai-guard']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
