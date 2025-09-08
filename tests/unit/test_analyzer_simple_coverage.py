"""Simple tests for analyzer.py to achieve maximum coverage."""

import pytest
import os
from unittest.mock import patch, MagicMock
import tempfile

from ai_guard.analyzer import (
    _coverage_percent_from_xml,
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_output,
    _make_rule_id,
    _rule_style,
    _strict_subprocess_fail,
    _to_text,
    ArtifactLocation,
    PhysicalLocation,
    Region,
    Location,
    SarifResult,
    RuleIdStyle,
)


class TestCoverageFunctions:
    """Test coverage parsing functions."""

    def test_coverage_percent_from_xml_with_line_rate(self):
        """Test parsing coverage XML with line-rate attribute."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="0.85" branch-rate="0.75">
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 85
            finally:
                try:
                    os.unlink(f.name)
                except:
                    pass

    def test_coverage_percent_from_xml_with_counters(self):
        """Test parsing coverage XML with counter elements."""
        xml_content = """<?xml version="1.0"?>
        <coverage>
            <counter type="LINE" covered="85" missed="15"/>
            <counter type="BRANCH" covered="20" missed="5"/>
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 85  # 85/(85+15) * 100
            finally:
                try:
                    os.unlink(f.name)
                except:
                    pass

    def test_coverage_percent_from_xml_file_not_found(self):
        """Test coverage parsing when file doesn't exist."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None

    def test_coverage_percent_from_xml_invalid_xml(self):
        """Test coverage parsing with invalid XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("invalid xml content")
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                try:
                    os.unlink(f.name)
                except:
                    pass

    def test_coverage_percent_from_xml_invalid_line_rate(self):
        """Test coverage parsing with invalid line-rate value."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="invalid">
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                try:
                    os.unlink(f.name)
                except:
                    pass

    def test_coverage_percent_from_xml_no_counters(self):
        """Test coverage parsing with no LINE counters."""
        xml_content = """<?xml version="1.0"?>
        <coverage>
            <counter type="BRANCH" covered="20" missed="5"/>
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                try:
                    os.unlink(f.name)
                except:
                    pass

    def test_coverage_percent_from_xml_default_paths(self):
        """Test coverage parsing with default paths."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="0.90">
        </coverage>"""

        # Test with coverage.xml in current directory
        with patch("os.path.exists", return_value=True):
            with patch("xml.etree.ElementTree.parse") as mock_parse:
                mock_tree = MagicMock()
                mock_root = MagicMock()
                mock_root.attrib = {"line-rate": "0.90"}
                mock_tree.getroot.return_value = mock_root
                mock_parse.return_value = mock_tree

                result = _coverage_percent_from_xml()
                assert result == 90

    def test_cov_percent_backward_compatibility(self):
        """Test cov_percent function for backward compatibility."""
        with patch("ai_guard.analyzer._coverage_percent_from_xml", return_value=75):
            result = cov_percent()
            assert result == 75

    def test_cov_percent_with_none_result(self):
        """Test cov_percent when _coverage_percent_from_xml returns None."""
        with patch("ai_guard.analyzer._coverage_percent_from_xml", return_value=None):
            result = cov_percent()
            assert result == 0


class TestParsingFunctions:
    """Test output parsing functions."""

    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        flake8_output = """test.py:10:5: E501 line too long
test.py:15:1: F401 'os' imported but unused
test.py:20:10: W293 blank line contains whitespace"""

        results = _parse_flake8_output(flake8_output)

        assert len(results) == 3
        assert results[0].rule_id == "E501"
        assert results[0].message == "line too long"
        assert results[0].level == "warning"
        assert (
            results[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "test.py"
        )
        assert results[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert results[0].locations[0]["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        results = _parse_flake8_output("")
        assert results == []

    def test_parse_flake8_output_invalid_lines(self):
        """Test parsing flake8 output with invalid lines."""
        flake8_output = """invalid line format
test.py:10:5: E501 line too long
another invalid line"""

        results = _parse_flake8_output(flake8_output)
        assert len(results) == 1
        assert results[0].rule_id == "E501"

    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        mypy_output = """test.py:10:5: error: Incompatible types in assignment
test.py:15: error: Name 'undefined_var' is not defined
test.py:20:10: warning: Unused 'type: ignore' comment"""

        results = _parse_mypy_output(mypy_output)

        assert len(results) == 3
        assert results[0].rule_id == "mypy-error"
        assert results[0].message == "Incompatible types in assignment"
        assert results[0].level == "error"
        assert (
            results[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "test.py"
        )
        assert results[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert results[0].locations[0]["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_mypy_output_with_code(self):
        """Test parsing mypy output with bracketed codes."""
        mypy_output = """test.py:10: error: Name 'undefined_var' is not defined [name-defined]
test.py:15: error: Incompatible types [assignment]"""

        results = _parse_mypy_output(mypy_output)

        assert len(results) == 2
        assert results[0].rule_id == "name-defined"
        assert results[1].rule_id == "assignment"

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        results = _parse_mypy_output("")
        assert results == []

    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        bandit_output = """test.py:10:1: B101: Use of assert detected
test.py:15:5: B603: subprocess call - check for execution of untrusted input"""

        results = _parse_bandit_output(bandit_output)

        assert len(results) == 2
        assert results[0].rule_id == "B101"
        assert results[0].message == "Use of assert detected"
        assert results[0].level == "error"
        assert (
            results[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "test.py"
        )
        assert results[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10
        assert results[0].locations[0]["physicalLocation"]["region"]["startColumn"] == 1

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        results = _parse_bandit_output("")
        assert results == []

    def test_parse_bandit_output_invalid_lines(self):
        """Test parsing bandit output with invalid lines."""
        bandit_output = """invalid line format
test.py:10:1: B101: Use of assert detected
another invalid line"""

        results = _parse_bandit_output(bandit_output)
        assert len(results) == 1
        assert results[0].rule_id == "B101"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_make_rule_id_bare_style(self):
        """Test _make_rule_id with bare style."""
        with patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            result = _make_rule_id("flake8", "E501")
            assert result == "E501"

    def test_make_rule_id_tool_style(self):
        """Test _make_rule_id with tool style."""
        with patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.TOOL):
            result = _make_rule_id("flake8", "E501")
            assert result == "flake8:E501"

    def test_make_rule_id_no_code(self):
        """Test _make_rule_id with no code."""
        with patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            result = _make_rule_id("mypy", None)
            assert result == "mypy"

    def test_make_rule_id_empty_code(self):
        """Test _make_rule_id with empty code."""
        with patch("ai_guard.analyzer._rule_style", return_value=RuleIdStyle.BARE):
            result = _make_rule_id("mypy", "")
            assert result == "mypy"

    def test_rule_style_environment_variable(self):
        """Test _rule_style with environment variable."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL

    def test_rule_style_default(self):
        """Test _rule_style default behavior."""
        with patch.dict(os.environ, {}, clear=True):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_strict_subprocess_fail_true(self):
        """Test _strict_subprocess_fail with various true values."""
        true_values = ["1", "true", "TRUE", "yes", "YES", "on", "ON"]
        for value in true_values:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                result = _strict_subprocess_fail()
                assert result is True

    def test_strict_subprocess_fail_false(self):
        """Test _strict_subprocess_fail with false values."""
        false_values = ["0", "false", "no", "off", "", "invalid"]
        for value in false_values:
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                result = _strict_subprocess_fail()
                assert result is False

    def test_to_text_none(self):
        """Test _to_text with None."""
        result = _to_text(None)
        assert result == ""

    def test_to_text_string(self):
        """Test _to_text with string."""
        result = _to_text("test string")
        assert result == "test string"

    def test_to_text_bytes(self):
        """Test _to_text with bytes."""
        result = _to_text(b"test bytes")
        assert result == "test bytes"

    def test_to_text_bytearray(self):
        """Test _to_text with bytearray."""
        result = _to_text(bytearray(b"test bytearray"))
        assert result == "test bytearray"

    def test_to_text_invalid_utf8(self):
        """Test _to_text with invalid UTF-8 bytes."""
        result = _to_text(b"\xff\xfe\x00\x00")
        # Should decode with errors="replace"
        assert isinstance(result, str)

    def test_to_text_other_type(self):
        """Test _to_text with other types."""
        result = _to_text(123)
        assert result == "123"


class TestDataclasses:
    """Test dataclass definitions."""

    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="test.py")
        assert location.uri == "test.py"

    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10, start_column=5)
        location = PhysicalLocation(artifact_location=artifact, region=region)

        assert location.artifact_location.uri == "test.py"
        assert location.region.start_line == 10
        assert location.region.start_column == 5

    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10, start_column=5)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)

        assert location.physical_location.artifact_location.uri == "test.py"
        assert location.physical_location.region.start_line == 10

    def test_sarif_result(self):
        """Test SarifResult dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10, start_column=5)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)

        result = SarifResult(
            rule_id="E501",
            message="line too long",
            locations=[location],
            level="warning",
        )

        assert result.rule_id == "E501"
        assert result.message == "line too long"
        assert len(result.locations) == 1
        assert result.level == "warning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
