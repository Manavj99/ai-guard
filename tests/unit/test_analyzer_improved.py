"""Comprehensive tests for analyzer.py to achieve maximum coverage."""

import os
import json
from unittest.mock import patch, MagicMock, mock_open

from ai_guard.analyzer import (
    RuleIdStyle,
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    SarifResult,
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
    main,
    CodeAnalyzer,
)
from ai_guard.report import GateResult


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
        """Test tool style."""
        assert _rule_style() == RuleIdStyle.TOOL

    @patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"})
    def test_rule_style_bare(self):
        """Test bare style."""
        assert _rule_style() == RuleIdStyle.BARE

    @patch.dict(os.environ, {}, clear=True)
    def test_rule_style_default(self):
        """Test default style."""
        assert _rule_style() == RuleIdStyle.BARE

    @patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "invalid"})
    def test_rule_style_invalid(self):
        """Test invalid style defaults to bare."""
        assert _rule_style() == RuleIdStyle.BARE


class TestMakeRuleId:
    """Test _make_rule_id function."""

    @patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_tool_style(self, mock_style):
        """Test rule ID with tool style."""
        result = _make_rule_id("flake8", "E501")
        assert result == "flake8:E501"

    @patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE)
    def test_make_rule_id_bare_style(self, mock_style):
        """Test rule ID with bare style."""
        result = _make_rule_id("flake8", "E501")
        assert result == "E501"

    @patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_no_code(self, mock_style):
        """Test rule ID with no code."""
        result = _make_rule_id("flake8", None)
        assert result == "flake8:flake8"

    @patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL)
    def test_make_rule_id_empty_code(self, mock_style):
        """Test rule ID with empty code."""
        result = _make_rule_id("flake8", "")
        assert result == "flake8:flake8"


class TestStrictSubprocessFail:
    """Test _strict_subprocess_fail function."""

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "1"})
    def test_strict_subprocess_fail_true_1(self):
        """Test strict subprocess fail with '1'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"})
    def test_strict_subprocess_fail_true_true(self):
        """Test strict subprocess fail with 'true'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "yes"})
    def test_strict_subprocess_fail_true_yes(self):
        """Test strict subprocess fail with 'yes'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "on"})
    def test_strict_subprocess_fail_true_on(self):
        """Test strict subprocess fail with 'on'."""
        assert _strict_subprocess_fail() is True

    @patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "0"})
    def test_strict_subprocess_fail_false_0(self):
        """Test strict subprocess fail with '0'."""
        assert _strict_subprocess_fail() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_strict_subprocess_fail_default(self):
        """Test strict subprocess fail default."""
        assert _strict_subprocess_fail() is False


class TestToText:
    """Test _to_text function."""

    def test_to_text_none(self):
        """Test _to_text with None."""
        assert _to_text(None) == ""

    def test_to_text_string(self):
        """Test _to_text with string."""
        assert _to_text("hello") == "hello"

    def test_to_text_bytes(self):
        """Test _to_text with bytes."""
        assert _to_text(b"hello") == "hello"

    def test_to_text_bytearray(self):
        """Test _to_text with bytearray."""
        assert _to_text(bytearray(b"hello")) == "hello"

    def test_to_text_invalid_utf8(self):
        """Test _to_text with invalid UTF-8."""
        result = _to_text(b"\xff\xfe")
        assert result == ""  # Replacement characters for invalid UTF-8


class TestDataclasses:
    """Test dataclass definitions."""

    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        loc = ArtifactLocation(uri="test.py")
        assert loc.uri == "test.py"

    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=10, start_column=5)
        assert region.start_line == 10
        assert region.start_column == 5

    def test_region_defaults(self):
        """Test Region dataclass defaults."""
        region = Region()
        assert region.start_line is None
        assert region.start_column is None

    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        loc = PhysicalLocation(artifact_location=artifact, region=region)
        assert loc.artifact_location.uri == "test.py"
        assert loc.region.start_line == 10

    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        loc = Location(physical_location=physical)
        assert loc.physical_location.artifact_location.uri == "test.py"

    def test_sarif_result(self):
        """Test SarifResult dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)

        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            locations=[location],
            level="error",
        )
        assert result.rule_id == "test-rule"
        assert result.message == "Test message"
        assert result.level == "error"
        assert len(result.locations) == 1

    def test_sarif_result_default_level(self):
        """Test SarifResult dataclass default level."""
        result = SarifResult(rule_id="test-rule", message="Test message", locations=[])
        assert result.level == "note"


class TestNormalizeRuleId:
    """Test _normalize_rule_id function."""

    def test_normalize_rule_id_with_colon(self):
        """Test normalizing rule ID with colon."""
        result = _normalize_rule_id("flake8:E501")
        assert result == "E501"

    def test_normalize_rule_id_without_colon(self):
        """Test normalizing rule ID without colon."""
        result = _normalize_rule_id("E501")
        assert result == "E501"


class TestNorm:
    """Test _norm function."""

    def test_norm_none(self):
        """Test _norm with None."""
        assert _norm(None) == ""

    def test_norm_string(self):
        """Test _norm with string."""
        assert _norm("hello") == "hello"

    def test_norm_bytes(self):
        """Test _norm with bytes."""
        assert _norm(b"hello") == "hello"

    def test_norm_bytearray(self):
        """Test _norm with bytearray."""
        assert _norm(bytearray(b"hello")) == "hello"


class TestCoveragePercentFromXml:
    """Test _coverage_percent_from_xml function."""

    def test_coverage_percent_from_xml_file_not_found(self):
        """Test with non-existent file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None

    def test_coverage_percent_from_xml_line_rate(self):
        """Test parsing with line-rate attribute."""
        xml_content = '<?xml version="1.0"?><coverage line-rate="0.85"></coverage>'
        with patch("builtins.open", mock_open(read_data=xml_content)):
            with patch("xml.etree.ElementTree.parse") as mock_parse:
                mock_tree = MagicMock()
                mock_root = MagicMock()
                mock_root.attrib = {"line-rate": "0.85"}
                mock_tree.getroot.return_value = mock_root
                mock_parse.return_value = mock_tree

                result = _coverage_percent_from_xml("coverage.xml")
                assert result == 85

    def test_coverage_percent_from_xml_counters(self):
        """Test parsing with counter elements."""
        xml_content = """<?xml version="1.0"?>
        <coverage>
            <counter type="LINE" covered="85" missed="15"/>
        </coverage>"""
        with patch("builtins.open", mock_open(read_data=xml_content)):
            with patch("xml.etree.ElementTree.parse") as mock_parse:
                mock_tree = MagicMock()
                mock_root = MagicMock()
                mock_root.attrib = {}
                mock_counter = MagicMock()
                mock_counter.attrib = {"type": "LINE", "covered": "85", "missed": "15"}
                mock_root.findall.return_value = [mock_counter]
                mock_tree.getroot.return_value = mock_root
                mock_parse.return_value = mock_tree

                result = _coverage_percent_from_xml("coverage.xml")
                assert result == 85

    def test_coverage_percent_from_xml_invalid_line_rate(self):
        """Test parsing with invalid line-rate."""
        xml_content = '<?xml version="1.0"?><coverage line-rate="invalid"></coverage>'
        with patch("builtins.open", mock_open(read_data=xml_content)):
            with patch("xml.etree.ElementTree.parse") as mock_parse:
                mock_tree = MagicMock()
                mock_root = MagicMock()
                mock_root.attrib = {"line-rate": "invalid"}
                mock_tree.getroot.return_value = mock_root
                mock_parse.return_value = mock_tree

                result = _coverage_percent_from_xml("coverage.xml")
                assert result is None

    def test_coverage_percent_from_xml_exception(self):
        """Test parsing with exception."""
        with patch("builtins.open", side_effect=Exception):
            result = _coverage_percent_from_xml("coverage.xml")
            assert result is None


class TestCovPercent:
    """Test cov_percent function."""

    @patch("ai_guard.analyzer._coverage_percent_from_xml", return_value=85)
    def test_cov_percent_success(self, mock_coverage):
        """Test successful coverage parsing."""
        result = cov_percent()
        assert result == 85

    @patch("ai_guard.analyzer._coverage_percent_from_xml", return_value=None)
    def test_cov_percent_failure(self, mock_coverage):
        """Test failed coverage parsing."""
        result = cov_percent()
        assert result == 0


class TestParseFlake8Output:
    """Test _parse_flake8_output function."""

    def test_parse_flake8_output_empty(self):
        """Test parsing empty output."""
        result = _parse_flake8_output("")
        assert result == []

    def test_parse_flake8_output_single_issue(self):
        """Test parsing single issue."""
        output = "test.py:10:5: E501 line too long"
        result = _parse_flake8_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "E501"
        assert result[0].message == "line too long"
        assert result[0].level == "warning"

    def test_parse_flake8_output_multiple_issues(self):
        """Test parsing multiple issues."""
        output = """test.py:10:5: E501 line too long
test.py:15:1: F401 unused import"""
        result = _parse_flake8_output(output)
        assert len(result) == 2
        assert result[0].rule_id == "E501"
        assert result[1].rule_id == "F401"

    def test_parse_flake8_output_invalid_format(self):
        """Test parsing invalid format."""
        output = "This is not a flake8 output"
        result = _parse_flake8_output(output)
        assert result == []

    def test_parse_flake8_output_whitespace_lines(self):
        """Test parsing with whitespace lines."""
        output = """
test.py:10:5: E501 line too long

test.py:15:1: F401 unused import
"""
        result = _parse_flake8_output(output)
        assert len(result) == 2


class TestParseMypyOutput:
    """Test _parse_mypy_output function."""

    def test_parse_mypy_output_empty(self):
        """Test parsing empty output."""
        result = _parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_with_code(self):
        """Test parsing output with bracketed code."""
        output = "test.py:10: error: Argument 1 has incompatible type [arg-type]"
        result = _parse_mypy_output(output)
        assert len(result) == 1
        assert result[0].rule_id == "arg-type"
        assert result[0].level == "error"

    def test_parse_mypy_output_without_code(self):
        """Test parsing output without bracketed code."""
        output = "test.py:10: error: Some error message"
        with patch("ai_guard.analyzer._make_rule_id", return_value="mypy:mypy-error"):
            result = _parse_mypy_output(output)
            assert len(result) == 1
            assert result[0].rule_id == "mypy:mypy-error"

    def test_parse_mypy_output_with_column(self):
        """Test parsing output with column number."""
        output = "test.py:10:5: error: Some error message [arg-type]"
        result = _parse_mypy_output(output)
        assert len(result) == 1
        assert result[0].locations[0].physical_location.region.start_column == 5

    def test_parse_mypy_output_invalid_severity(self):
        """Test parsing output with invalid severity."""
        output = "test.py:10: info: Some info message"
        result = _parse_mypy_output(output)
        assert result == []

    def test_parse_mypy_output_invalid_format(self):
        """Test parsing invalid format."""
        output = "This is not a mypy output"
        result = _parse_mypy_output(output)
        assert result == []


class TestRunLintCheck:
    """Test run_lint_check function."""

    @patch("subprocess.run")
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result, sarif = run_lint_check(["test.py"])
        assert result.passed is True
        assert sarif is None

    @patch("subprocess.run")
    def test_run_lint_check_with_issues(self, mock_run):
        """Test lint check with issues."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="test.py:10:5: E501 line too long", stderr=""
        )
        result, sarif = run_lint_check(["test.py"])
        assert result.passed is False
        assert sarif is not None
        assert sarif.rule_id == "E501"

    @patch("subprocess.run")
    def test_run_lint_check_tool_error(self, mock_run):
        """Test lint check with tool error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="flake8: command not found"
        )
        result, sarif = run_lint_check(["test.py"])
        assert result.passed is False
        assert sarif is None
        assert "flake8 error" in result.details


class TestRunTypeCheck:
    """Test run_type_check function."""

    @patch("subprocess.run")
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result, sarif = run_type_check(["test.py"])
        assert result.passed is True
        assert sarif is None

    @patch("subprocess.run")
    def test_run_type_check_with_issues(self, mock_run):
        """Test type check with issues."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="test.py:10: error: Argument 1 has incompatible type [arg-type]",
            stderr="",
        )
        result, sarif = run_type_check(["test.py"])
        assert result.passed is False
        assert sarif is not None
        assert sarif.rule_id == "arg-type"

    @patch("subprocess.run")
    def test_run_type_check_tool_error(self, mock_run):
        """Test type check with tool error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="mypy: command not found"
        )
        result, sarif = run_type_check(["test.py"])
        assert result.passed is False
        assert sarif is None
        assert "mypy error" in result.details


class TestParseBanditJson:
    """Test _parse_bandit_json function."""

    def test_parse_bandit_json_empty(self):
        """Test parsing empty JSON."""
        result = _parse_bandit_json("")
        assert result == []

    def test_parse_bandit_json_valid(self):
        """Test parsing valid JSON."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Test issue",
                    "test_id": "B101",
                }
            ]
        }
        result = _parse_bandit_json(json.dumps(json_data))
        assert len(result) == 1
        assert result[0].rule_id == "B101"
        assert result[0].message == "Test issue"

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid JSON."""
        result = _parse_bandit_json("invalid json")
        assert result == []

    def test_parse_bandit_json_bytes(self):
        """Test parsing bytes input."""
        json_data = b'{"results": []}'
        result = _parse_bandit_json(json_data)
        assert result == []

    def test_parse_bandit_json_no_results(self):
        """Test parsing JSON with no results."""
        json_data = {"results": []}
        result = _parse_bandit_json(json.dumps(json_data))
        assert result == []


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""

    def test_parse_bandit_output(self):
        """Test _parse_bandit_output is alias for _parse_bandit_json."""
        with patch(
            "ai_guard.analyzer._parse_bandit_json", return_value=[]
        ) as mock_parse:
            _parse_bandit_output("test")
            mock_parse.assert_called_once_with("test")


class TestRunSecurityCheck:
    """Test run_security_check function."""

    @patch("subprocess.run")
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"results": []}', stderr=""
        )
        result, sarif = run_security_check()
        assert result.passed is True
        assert sarif is None

    @patch("subprocess.run")
    def test_run_security_check_with_issues(self, mock_run):
        """Test security check with issues."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Test security issue",
                    "test_id": "B101",
                }
            ]
        }
        mock_run.return_value = MagicMock(
            returncode=1, stdout=json.dumps(json_data), stderr=""
        )
        result, sarif = run_security_check()
        assert result.passed is False
        assert sarif is not None
        assert sarif.rule_id == "B101"

    @patch("subprocess.run")
    def test_run_security_check_tool_error(self, mock_run):
        """Test security check with tool error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="bandit: command not found"
        )
        result, sarif = run_security_check()
        assert result.passed is False
        assert sarif is None
        assert "bandit error" in result.details


class TestToFindings:
    """Test _to_findings function."""

    def test_to_findings_empty(self):
        """Test with empty results."""
        result = _to_findings([])
        assert result == []

    def test_to_findings_dict_location(self):
        """Test with dictionary location."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10, start_column=5)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)

        sarif_result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            locations=[location],
            level="error",
        )

        result = _to_findings([sarif_result])
        assert len(result) == 1
        assert result[0]["rule_id"] == "test-rule"
        assert result[0]["path"] == "test.py"
        assert result[0]["line"] == 10

    def test_to_findings_no_locations(self):
        """Test with no locations."""
        sarif_result = SarifResult(
            rule_id="test-rule", message="Test message", locations=[], level="error"
        )

        result = _to_findings([sarif_result])
        assert len(result) == 1
        assert result[0]["path"] == "unknown"
        assert result[0]["line"] is None


class TestRunCoverageCheck:
    """Test run_coverage_check function."""

    @patch("ai_guard.analyzer.cov_percent", return_value=85)
    def test_run_coverage_check_pass(self, mock_cov):
        """Test coverage check that passes."""
        result = run_coverage_check(80)
        assert result.passed is True
        assert "85% >= 80%" in result.details

    @patch("ai_guard.analyzer.cov_percent", return_value=75)
    def test_run_coverage_check_fail(self, mock_cov):
        """Test coverage check that fails."""
        result = run_coverage_check(80)
        assert result.passed is False
        assert "75% >= 80%" in result.details

    @patch("ai_guard.analyzer.cov_percent", return_value=85)
    def test_run_coverage_check_no_minimum(self, mock_cov):
        """Test coverage check with no minimum."""
        result = run_coverage_check(None)
        assert result.passed is True
        assert "85% (no minimum set)" in result.details

    @patch("ai_guard.analyzer.cov_percent", return_value=None)
    def test_run_coverage_check_no_data(self, mock_cov):
        """Test coverage check with no data."""
        result = run_coverage_check(80)
        assert result.passed is False
        assert "No coverage data" in result.details


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_init_default(self):
        """Test CodeAnalyzer initialization with default config."""
        with patch("ai_guard.analyzer.load_config") as mock_load:
            mock_load.return_value = {"min_coverage": 80}
            analyzer = CodeAnalyzer()
            assert analyzer.config["min_coverage"] == 80

    def test_code_analyzer_init_custom(self):
        """Test CodeAnalyzer initialization with custom config."""
        config = {"min_coverage": 90}
        analyzer = CodeAnalyzer(config)
        assert analyzer.config["min_coverage"] == 90

    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_lint_check")
    def test_run_all_checks(self, mock_lint, mock_type, mock_security):
        """Test run_all_checks method."""
        mock_lint.return_value = (GateResult("Lint", True), None)
        mock_type.return_value = (GateResult("Type", True), None)
        mock_security.return_value = (GateResult("Security", True), None)

        with patch("ai_guard.analyzer.run_coverage_check") as mock_coverage:
            mock_coverage.return_value = GateResult("Coverage", True)

            analyzer = CodeAnalyzer()
            results = analyzer.run_all_checks(["test.py"])

            assert len(results) == 4
            assert all(r.passed for r in results)


class TestMain:
    """Test main function."""

    @patch("ai_guard.analyzer.run", return_value=0)
    def test_main_success(self, mock_run):
        """Test main function success."""
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)

    @patch("ai_guard.analyzer.run", return_value=1)
    def test_main_failure(self, mock_run):
        """Test main function failure."""
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)
