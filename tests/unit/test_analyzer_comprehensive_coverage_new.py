"""Comprehensive tests for analyzer.py to achieve maximum coverage."""

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
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    main,
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
            temp_file = f.name

        try:
            result = _coverage_percent_from_xml(temp_file)
            assert result == 85
        finally:
            try:
                os.unlink(temp_file)
            except (OSError, PermissionError):
                # On Windows, sometimes the file is still locked
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
            temp_file = f.name

        try:
            result = _coverage_percent_from_xml(temp_file)
            assert result == 85  # 85/(85+15) * 100
        finally:
            try:
                os.unlink(temp_file)
            except (OSError, PermissionError):
                # On Windows, sometimes the file is still locked
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
            temp_file = f.name

        try:
            result = _coverage_percent_from_xml(temp_file)
            assert result is None
        finally:
            try:
                os.unlink(temp_file)
            except (OSError, PermissionError):
                # On Windows, sometimes the file is still locked
                pass

    def test_coverage_percent_from_xml_invalid_line_rate(self):
        """Test coverage parsing with invalid line-rate value."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="invalid">
        </coverage>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()
            temp_file = f.name

        try:
            result = _coverage_percent_from_xml(temp_file)
            assert result is None
        finally:
            try:
                os.unlink(temp_file)
            except (OSError, PermissionError):
                # On Windows, sometimes the file is still locked
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
            temp_file = f.name

        try:
            result = _coverage_percent_from_xml(temp_file)
            assert result is None
        finally:
            try:
                os.unlink(temp_file)
            except (OSError, PermissionError):
                # On Windows, sometimes the file is still locked
                pass

    def test_coverage_percent_from_xml_default_paths(self):
        """Test coverage parsing with default paths."""
        xml_content = """<?xml version="1.0"?>
        <coverage line-rate="0.90">
        </coverage>"""

        # Clear the cache first
        from ai_guard.performance import get_cache

        get_cache().clear()

        # Test with coverage.xml in current directory
        with patch("os.path.exists", return_value=True):
            with patch("defusedxml.ElementTree.parse") as mock_parse:
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
        """Test parsing valid bandit JSON output."""
        bandit_output = """{
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "Use of assert detected",
                    "issue_severity": "MEDIUM"
                },
                {
                    "filename": "test.py",
                    "line_number": 15,
                    "test_id": "B603",
                    "issue_text": "subprocess call - check for execution of untrusted input",
                    "issue_severity": "HIGH"
                }
            ]
        }"""

        results = _parse_bandit_output(bandit_output)

        assert len(results) == 2
        assert results[0].rule_id == "B101"
        assert results[0].message == "Use of assert detected"
        assert results[0].level == "warning"
        assert (
            results[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "test.py"
        )
        assert results[0].locations[0]["physicalLocation"]["region"]["startLine"] == 10

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        results = _parse_bandit_output("")
        assert results == []

    def test_parse_bandit_output_invalid_json(self):
        """Test parsing bandit output with invalid JSON."""
        bandit_output = "invalid json content"

        results = _parse_bandit_output(bandit_output)
        assert len(results) == 0


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
        # Clear the cache first
        from ai_guard.performance import get_cache

        get_cache().clear()
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _rule_style()
            assert result == RuleIdStyle.TOOL

    def test_rule_style_default(self):
        """Test _rule_style default behavior."""
        # Clear the cache first
        from ai_guard.performance import get_cache

        get_cache().clear()
        with patch.dict(os.environ, {}, clear=True):
            result = _rule_style()
            assert result == RuleIdStyle.BARE

    def test_strict_subprocess_fail_true(self):
        """Test _strict_subprocess_fail with various true values."""
        true_values = ["1", "true", "TRUE", "yes", "YES", "on", "ON"]
        for value in true_values:
            # Clear the cache first
            from ai_guard.performance import get_cache

            get_cache().clear()
            with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": value}):
                result = _strict_subprocess_fail()
                assert result is True

    def test_strict_subprocess_fail_false(self):
        """Test _strict_subprocess_fail with false values."""
        false_values = ["0", "false", "no", "off", "", "invalid"]
        for value in false_values:
            # Clear the cache first
            from ai_guard.performance import get_cache

            get_cache().clear()
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
        # The first two bytes (\xff\xfe) are invalid UTF-8 and get replaced with replacement characters
        # The last two bytes (\x00\x00) are valid null characters
        assert len(result) == 4  # 2 replacement chars + 2 null chars
        assert result.endswith("\x00\x00")  # Should decode with errors="replace"

    def test_to_text_other_type(self):
        """Test _to_text with other types."""
        result = _to_text(123)
        assert result == "123"


class TestCheckFunctions:
    """Test the main check functions."""

    def test_run_lint_check_success(self):
        """Test run_lint_check with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result, findings = run_lint_check(None)

            assert result.passed is True
            assert result.name == "Lint (flake8)"
            assert findings is None

    def test_run_lint_check_with_findings(self):
        """Test run_lint_check with findings."""
        flake8_output = "test.py:10:5: E501 line too long"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=flake8_output, stderr=""
            )

            result, findings = run_lint_check(None)

            assert result.passed is False
            assert result.name == "Lint (flake8)"
            assert findings is not None
            assert findings.rule_id == "E501"

    def test_run_lint_check_subprocess_error(self):
        """Test run_lint_check with subprocess error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("flake8 not found")

            result, findings = run_lint_check(None)

            assert result.passed is False
            assert "flake8 not found" in result.details
            assert findings is None

    def test_run_type_check_success(self):
        """Test run_type_check with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result, findings = run_type_check(None)

            assert result.passed is True
            assert result.name == "Static types (mypy)"
            assert findings is None

    def test_run_type_check_with_findings(self):
        """Test run_type_check with findings."""
        mypy_output = "test.py:10: error: Name 'undefined_var' is not defined"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=mypy_output, stderr=""
            )

            result, findings = run_type_check(None)

            assert result.passed is False
            assert result.name == "Static types (mypy)"
            assert findings is not None
            assert findings.rule_id == "mypy-error"

    def test_run_security_check_success(self):
        """Test run_security_check with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result, findings = run_security_check()

            assert result.passed is True
            assert result.name == "Security (bandit)"
            assert findings is None

    def test_run_security_check_with_findings(self):
        """Test run_security_check with findings."""
        bandit_output = """{
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "Use of assert detected",
                    "issue_severity": "MEDIUM"
                }
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=bandit_output, stderr=""
            )

            result, findings = run_security_check()

            assert result.passed is False
            assert result.name == "Security (bandit)"
            assert findings is not None
            assert findings.rule_id == "B101"

    def test_run_coverage_check_success(self):
        """Test run_coverage_check with sufficient coverage."""
        with patch("ai_guard.analyzer._coverage_percent_from_xml", return_value=85):
            result = run_coverage_check(80)

            assert result.passed is True
            assert result.name == "Coverage"
            assert "85%" in result.details

    def test_run_coverage_check_insufficient(self):
        """Test run_coverage_check with insufficient coverage."""
        with patch("ai_guard.analyzer._coverage_percent_from_xml", return_value=75):
            result = run_coverage_check(80)

            assert result.passed is False
            assert result.name == "Coverage"
            assert "75% >= 80%" in result.details

    def test_run_coverage_check_no_file(self):
        """Test run_coverage_check with no coverage file."""
        with patch("ai_guard.analyzer.cov_percent", return_value=None):
            result = run_coverage_check(80)

            assert result.passed is False
            assert result.name == "Coverage"
            assert "No coverage data" in result.details


class TestMainFunction:
    """Test the main function."""

    def test_main_success(self):
        """Test main function with successful execution."""
        with patch(
            "ai_guard.analyzer.run_lint_check",
            return_value=(MagicMock(passed=True), []),
        ):
            with patch(
                "ai_guard.analyzer.run_type_check",
                return_value=(MagicMock(passed=True), []),
            ):
                with patch(
                    "ai_guard.analyzer.run_security_check",
                    return_value=(MagicMock(passed=True), []),
                ):
                    with patch(
                        "ai_guard.analyzer.run_coverage_check",
                        return_value=MagicMock(passed=True),
                    ):
                        with patch("ai_guard.analyzer.write_sarif") as mock_write:
                            with patch("sys.argv", ["ai-guard"]):
                                main()

                                mock_write.assert_called_once()

    def test_main_with_findings(self):
        """Test main function with findings."""
        mock_finding = MagicMock()
        mock_finding.rule_id = "E501"
        mock_finding.message = "line too long"

        with patch(
            "ai_guard.analyzer.run_lint_check",
            return_value=(MagicMock(passed=False), [mock_finding]),
        ):
            with patch(
                "ai_guard.analyzer.run_type_check",
                return_value=(MagicMock(passed=True), []),
            ):
                with patch(
                    "ai_guard.analyzer.run_security_check",
                    return_value=(MagicMock(passed=True), []),
                ):
                    with patch(
                        "ai_guard.analyzer.run_coverage_check",
                        return_value=MagicMock(passed=True),
                    ):
                        with patch("ai_guard.analyzer.write_sarif") as mock_write:
                            with patch("sys.argv", ["ai-guard"]):
                                main()

                                mock_write.assert_called_once()

    def test_main_with_report_format_json(self):
        """Test main function with JSON report format."""
        with patch(
            "ai_guard.analyzer.run_lint_check",
            return_value=(MagicMock(passed=True), []),
        ):
            with patch(
                "ai_guard.analyzer.run_type_check",
                return_value=(MagicMock(passed=True), []),
            ):
                with patch(
                    "ai_guard.analyzer.run_security_check",
                    return_value=(MagicMock(passed=True), []),
                ):
                    with patch(
                        "ai_guard.analyzer.run_coverage_check",
                        return_value=MagicMock(passed=True),
                    ):
                        with patch("ai_guard.analyzer.write_json") as mock_write:
                            with patch(
                                "sys.argv", ["ai-guard", "--report-format", "json"]
                            ):
                                main()

                                mock_write.assert_called_once()

    def test_main_with_report_format_html(self):
        """Test main function with HTML report format."""
        with patch(
            "ai_guard.analyzer.run_lint_check",
            return_value=(MagicMock(passed=True), []),
        ):
            with patch(
                "ai_guard.analyzer.run_type_check",
                return_value=(MagicMock(passed=True), []),
            ):
                with patch(
                    "ai_guard.analyzer.run_security_check",
                    return_value=(MagicMock(passed=True), []),
                ):
                    with patch(
                        "ai_guard.analyzer.run_coverage_check",
                        return_value=MagicMock(passed=True),
                    ):
                        with patch("ai_guard.analyzer.write_html") as mock_write:
                            with patch(
                                "sys.argv", ["ai-guard", "--report-format", "html"]
                            ):
                                main()

                                mock_write.assert_called_once()


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
