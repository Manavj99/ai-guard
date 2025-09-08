"""Working comprehensive tests for the analyzer module."""

import sys
import json
from unittest.mock import patch, mock_open, MagicMock

from ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_json,
    main,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
)


class TestAnalyzerWorking:
    """Working comprehensive tests for analyzer functionality."""

    def test_cov_percent_with_valid_coverage_xml(self):
        """Test cov_percent with valid coverage.xml file."""
        coverage_xml = """<?xml version="1.0" ?>
        <coverage version="7.10.5" line-rate="0.85" branch-rate="0.75">
            <sources>
                <source>/path/to/src</source>
            </sources>
            <packages>
                <package name="." line-rate="0.85" branch-rate="0.75">
                </package>
            </packages>
        </coverage>"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=coverage_xml)):
                with patch("defusedxml.ElementTree.parse") as mock_parse:
                    mock_tree = MagicMock()
                    mock_root = MagicMock()
                    mock_root.get.return_value = "0.85"
                    mock_tree.getroot.return_value = mock_root
                    mock_parse.return_value = mock_tree

                    result = cov_percent()
                    assert result == 85

    def test_cov_percent_parse_error(self):
        """Test cov_percent when XML parsing fails."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=b"invalid xml")):
                with patch(
                    "defusedxml.ElementTree.parse", side_effect=Exception("Parse error")
                ):
                    result = cov_percent()
                    assert result == 0

    def test_cov_percent_no_file(self):
        """Test cov_percent when no coverage.xml file exists."""
        with patch("os.path.exists", return_value=False):
            result = cov_percent()
            assert result == 0

    def test_parse_flake8_output(self):
        """Test parsing flake8 output."""
        flake8_output = """src/test.py:10:1: E302 expected 2 blank lines, found 1
src/test.py:15:5: E111 indentation is not a multiple of four
src/test.py:20:1: F401 'os' imported but unused"""

        results = _parse_flake8_output(flake8_output)

        assert len(results) == 3

        # Check first result
        assert results[0].rule_id == "flake8:E302"
        assert results[0].level == "warning"
        assert "expected 2 blank lines" in results[0].message
        assert (
            results[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test.py"
        )

    def test_parse_flake8_output_malformed(self):
        """Test parsing malformed flake8 output."""
        malformed_output = """src/test.py:10:1: E302
src/test.py:invalid:line:format
src/test.py:15:5: E111 indentation is not a multiple of four"""

        results = _parse_flake8_output(malformed_output)

        # Should still parse valid lines (only the last one is valid)
        assert len(results) == 1

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = """src/test.py:10: error: Incompatible return type
src/test.py:15: note: Revealed type is 'builtins.int'
src/test.py:20: warning: Unused 'type: ignore' comment"""

        results = _parse_mypy_output(mypy_output)

        assert len(results) == 3

        # Check first result (error)
        assert results[0].rule_id == "mypy:mypy-error"
        assert results[0].level == "error"
        assert "Incompatible return type" in results[0].message
        assert (
            results[0].locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test.py"
        )

    def test_parse_bandit_json(self):
        """Test parsing bandit JSON output."""
        bandit_json = {
            "results": [
                {
                    "test_id": "B101",
                    "test_name": "Test for use of assert detected",
                    "filename": "src/test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test for use of assert detected",
                }
            ]
        }

        results = _parse_bandit_json(json.dumps(bandit_json))

        assert len(results) == 1
        assert results[0].rule_id == "bandit:B101"
        assert results[0].level == "note"
        assert "Test for use of assert detected" in results[0].message

    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON output."""
        bandit_json = {"results": []}
        results = _parse_bandit_json(json.dumps(bandit_json))
        assert len(results) == 0

    @patch("ai_guard.analyzer.subprocess.run")
    def test_run_lint_check(self, mock_run):
        """Test run_lint_check function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result, findings = run_lint_check(["src/test.py"])

        assert result.passed is True
        assert len(findings) == 0

    @patch("ai_guard.analyzer.subprocess.run")
    def test_run_type_check(self, mock_run):
        """Test run_type_check function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result, findings = run_type_check(["src/test.py"])

        assert result.passed is True
        assert len(findings) == 0

    @patch("ai_guard.analyzer.subprocess.run")
    def test_run_security_check(self, mock_run):
        """Test run_security_check function."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"results": []}', stderr=""
        )

        result, findings = run_security_check()

        assert result.passed is True
        assert len(findings) == 0

    @patch("ai_guard.analyzer.cov_percent")
    def test_run_coverage_check(self, mock_cov_percent):
        """Test run_coverage_check function."""
        mock_cov_percent.return_value = 85

        result = run_coverage_check(80)

        assert result.passed is True
        assert "85%" in result.details

    @patch("ai_guard.analyzer.cov_percent")
    def test_run_coverage_check_fails(self, mock_cov_percent):
        """Test run_coverage_check when coverage is below threshold."""
        mock_cov_percent.return_value = 75

        result = run_coverage_check(80)

        assert result.passed is False
        assert "75%" in result.details

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.cov_percent")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_basic_flow(
        self,
        mock_write_sarif,
        mock_cov_percent,
        mock_coverage_check,
        mock_security_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function basic flow."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.min_coverage = 80
        mock_config.skip_tests = False
        mock_config.report_format = "sarif"
        mock_config.report_path = "ai-guard.sarif"
        mock_config.enhanced_testgen_enabled = False
        mock_config.pr_annotations_enabled = False
        mock_load_config.return_value = mock_config

        mock_changed_files.return_value = ["src/test.py"]
        mock_lint_check.return_value = (MagicMock(passed=True), [])
        mock_type_check.return_value = (MagicMock(passed=True), [])
        mock_security_check.return_value = (MagicMock(passed=True), [])
        mock_coverage_check.return_value = MagicMock(passed=True)
        mock_cov_percent.return_value = 85

        # Mock sys.argv
        with patch.object(sys, "argv", ["ai-guard", "--skip-tests"]):
            main()

        # Verify calls were made
        mock_changed_files.assert_called_once()
        mock_lint_check.assert_called_once()
        mock_type_check.assert_called_once()
        mock_security_check.assert_called_once()
        mock_coverage_check.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.cov_percent")
    @patch("ai_guard.analyzer.write_json")
    def test_main_json_report(
        self,
        mock_write_json,
        mock_cov_percent,
        mock_coverage_check,
        mock_security_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with JSON report format."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.min_coverage = 80
        mock_config.skip_tests = False
        mock_config.report_format = "sarif"
        mock_config.report_path = "ai-guard.sarif"
        mock_config.enhanced_testgen_enabled = False
        mock_config.pr_annotations_enabled = False
        mock_load_config.return_value = mock_config

        mock_changed_files.return_value = ["src/test.py"]
        mock_lint_check.return_value = (MagicMock(passed=True), [])
        mock_type_check.return_value = (MagicMock(passed=True), [])
        mock_security_check.return_value = (MagicMock(passed=True), [])
        mock_coverage_check.return_value = MagicMock(passed=True)
        mock_cov_percent.return_value = 85

        # Mock sys.argv
        with patch.object(
            sys,
            "argv",
            ["ai-guard", "--report-format", "json", "--report-path", "report.json"],
        ):
            main()

        # Verify JSON writer was called
        mock_write_json.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.cov_percent")
    @patch("ai_guard.analyzer.write_html")
    def test_main_html_report(
        self,
        mock_write_html,
        mock_cov_percent,
        mock_coverage_check,
        mock_security_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with HTML report format."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.min_coverage = 80
        mock_config.skip_tests = False
        mock_config.report_format = "sarif"
        mock_config.report_path = "ai-guard.sarif"
        mock_config.enhanced_testgen_enabled = False
        mock_config.pr_annotations_enabled = False
        mock_load_config.return_value = mock_config

        mock_changed_files.return_value = ["src/test.py"]
        mock_lint_check.return_value = (MagicMock(passed=True), [])
        mock_type_check.return_value = (MagicMock(passed=True), [])
        mock_security_check.return_value = (MagicMock(passed=True), [])
        mock_coverage_check.return_value = MagicMock(passed=True)
        mock_cov_percent.return_value = 85

        # Mock sys.argv
        with patch.object(
            sys,
            "argv",
            ["ai-guard", "--report-format", "html", "--report-path", "report.html"],
        ):
            main()

        # Verify HTML writer was called
        mock_write_html.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    def test_main_no_changed_files(self, mock_changed_files, mock_load_config):
        """Test main function with no changed files."""
        mock_config = MagicMock()
        mock_config.min_coverage = 80
        mock_config.skip_tests = False
        mock_config.report_format = "sarif"
        mock_config.report_path = "ai-guard.sarif"
        mock_config.enhanced_testgen_enabled = False
        mock_config.pr_annotations_enabled = False
        mock_load_config.return_value = mock_config

        mock_changed_files.return_value = []

        # Mock sys.argv
        with patch.object(sys, "argv", ["ai-guard"]):
            main()

        # Should exit early when no files changed
        mock_changed_files.assert_called_once()
