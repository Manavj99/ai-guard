"""Integration tests for analyzer.py module to improve coverage."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.ai_guard.analyzer import (
    run,
    main,
    _write_reports,
    _run_tool,
    _get_git_diff,
    _get_changed_files,
    _parse_sarif_output,
    _parse_coverage_output,
    _should_skip_file,
    _to_findings,
    _parse_bandit_json,
    _parse_bandit_output,
    _parse_flake8_output,
    _parse_mypy_output,
    _coverage_percent_from_xml,
    cov_percent,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    CodeAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    analyze_files_parallel,
    benchmark_analyzer,
    analyze_code,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    run_analysis,
    generate_report,
)
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestRunFunctionIntegration:
    """Test the main run function with various scenarios."""

    def test_run_with_enhanced_testgen(self):
        """Test run function with enhanced test generation enabled."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif,
            patch("src.ai_guard.analyzer.EnhancedTestGenerator") as mock_testgen,
            patch("builtins.open", mock_open()),
            patch("pathlib.Path.mkdir"),
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            mock_testgen_instance = MagicMock()
            mock_testgen_instance.generate_tests.return_value = "test content"
            mock_testgen.return_value = mock_testgen_instance

            exit_code = run(["--enhanced-testgen", "--llm-provider", "openai"])
            assert exit_code == 0
            mock_write_sarif.assert_called_once()

    def test_run_with_pr_annotations(self):
        """Test run function with PR annotations enabled."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif,
            patch("src.ai_guard.analyzer.PRAnnotator") as mock_annotator,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            mock_annotator_instance = MagicMock()
            mock_annotator_instance.generate_review_summary.return_value = MagicMock(
                overall_status="pass", quality_score=0.85, annotations=[]
            )
            mock_annotator.return_value = mock_annotator_instance

            exit_code = run(["--pr-annotations"])
            assert exit_code == 0
            mock_write_sarif.assert_called_once()

    def test_run_with_performance_report(self):
        """Test run function with performance report enabled."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif,
            patch("src.ai_guard.analyzer.get_performance_summary") as mock_perf,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)
            mock_perf.return_value = {
                "total_metrics": 10,
                "cache_size": 5,
                "functions_tracked": 3,
                "average_times": {"func1": 0.1, "func2": 0.2},
            }

            exit_code = run(["--performance-report"])
            assert exit_code == 0
            mock_write_sarif.assert_called_once()

    def test_run_with_json_format(self):
        """Test run function with JSON output format."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_json") as mock_write_json,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            exit_code = run(["--report-format", "json"])
            assert exit_code == 0
            mock_write_json.assert_called_once()

    def test_run_with_html_format(self):
        """Test run function with HTML output format."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_html") as mock_write_html,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            exit_code = run(["--report-format", "html"])
            assert exit_code == 0
            mock_write_html.assert_called_once()

    def test_run_with_skip_tests(self):
        """Test run function with tests skipped."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage") as mock_pytest,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            exit_code = run(["--skip-tests"])
            assert exit_code == 0
            mock_pytest.assert_not_called()
            mock_write_sarif.assert_called_once()

    def test_run_with_event_file(self):
        """Test run function with GitHub event file."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif,
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            exit_code = run(["--event", "event.json"])
            assert exit_code == 0
            mock_write_sarif.assert_called_once()

    def test_run_with_deprecated_sarif_arg(self):
        """Test run function with deprecated --sarif argument."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif,
            patch("builtins.print") as mock_print,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            exit_code = run(["--sarif", "custom.sarif"])
            assert exit_code == 0
            mock_write_sarif.assert_called_once()
            # Check that deprecation warning was printed
            mock_print.assert_called()

    def test_run_with_unknown_format(self):
        """Test run function with unknown report format."""
        with (
            patch(
                "src.ai_guard.analyzer.changed_python_files",
                return_value=["src/test.py"],
            ),
            patch("src.ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("src.ai_guard.analyzer.run_type_check") as mock_type,
            patch("src.ai_guard.analyzer.run_security_check") as mock_security,
            patch("src.ai_guard.analyzer.run_coverage_check") as mock_coverage,
            patch("src.ai_guard.analyzer.run_pytest_with_coverage", return_value=0),
            patch("src.ai_guard.analyzer.summarize", return_value=0),
            patch("sys.exit") as mock_exit,
        ):
            mock_lint.return_value = (GateResult("Lint", True), None)
            mock_type.return_value = (GateResult("Type", True), None)
            mock_security.return_value = (GateResult("Security", True), None)
            mock_coverage.return_value = (GateResult("Coverage", True), None)

            # This should cause an error due to unknown format
            run(["--report-format", "unknown"])
            mock_exit.assert_called_with(2)


class TestMainFunction:
    """Test main function."""

    def test_main_success(self):
        """Test main function success."""
        with patch("src.ai_guard.analyzer.run", return_value=0) as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            mock_run.assert_called_once()

    def test_main_failure(self):
        """Test main function failure."""
        with patch("src.ai_guard.analyzer.run", return_value=1) as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            mock_run.assert_called_once()


class TestCoverageFunctions:
    """Test coverage-related functions."""

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

    def test_parse_coverage_output_exception(self):
        """Test parsing coverage output with exception."""
        output = None
        assert _parse_coverage_output(output) is None


class TestShouldSkipFile:
    """Test _should_skip_file function."""

    def test_should_skip_file_python(self):
        """Test _should_skip_file with Python file."""
        assert not _should_skip_file("src/test.py")

    def test_should_skip_file_non_python(self):
        """Test _should_skip_file with non-Python file."""
        assert _should_skip_file("src/test.txt")

    def test_should_skip_file_hidden(self):
        """Test _should_skip_file with hidden file."""
        assert _should_skip_file(".hidden.py")

    def test_should_skip_file_cache(self):
        """Test _should_skip_file with cache directory."""
        assert _should_skip_file("src/__pycache__/test.py")

    def test_should_skip_file_test_file(self):
        """Test _should_skip_file with test file."""
        assert _should_skip_file("test_file.py")
        assert _should_skip_file("src/test_module_test.py")


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
            locations=[
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": "test.py"},
                        "region": {"startLine": 10},
                    }
                }
            ],
        )
        findings = _to_findings([sarif_result])
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "test:rule"
        assert findings[0]["level"] == "warning"  # Converted from error
        assert findings[0]["path"] == "test.py"
        assert findings[0]["line"] == 10

    def test_to_findings_with_object_locations(self):
        """Test _to_findings with object locations."""
        from src.ai_guard.analyzer import (
            ArtifactLocation,
            Region,
            PhysicalLocation,
            Location,
        )

        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)

        sarif_result = SarifResult(
            rule_id="test:rule",
            message="Test message",
            level="error",
            locations=[location],
        )
        findings = _to_findings([sarif_result])
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "test:rule"
        assert findings[0]["path"] == "test.py"
        assert findings[0]["line"] == 10

    def test_to_findings_without_locations(self):
        """Test _to_findings without locations."""
        sarif_result = SarifResult(
            rule_id="test:rule",
            message="Test message",
            level="error",
            locations=[],
        )
        findings = _to_findings([sarif_result])
        assert len(findings) == 1
        assert findings[0]["rule_id"] == "test:rule"
        assert findings[0]["path"] == "unknown"
        assert findings[0]["line"] is None


class TestParseBanditJson:
    """Test _parse_bandit_json function."""

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
                    "test_id": "B101",
                }
            ]
        }
        json_str = json.dumps(bandit_data)
        results = _parse_bandit_json(json_str)
        assert len(results) == 1
        assert results[0].rule_id == "B101"
        assert results[0].message == "Test issue"
        assert results[0].level == "warning"

    def test_parse_bandit_json_bytes(self):
        """Test parsing Bandit JSON from bytes."""
        bandit_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Test issue",
                    "test_id": "B101",
                }
            ]
        }
        json_bytes = json.dumps(bandit_data).encode("utf-8")
        results = _parse_bandit_json(json_bytes)
        assert len(results) == 1
        assert results[0].rule_id == "B101"

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid Bandit JSON."""
        results = _parse_bandit_json("invalid json")
        assert results == []

    def test_parse_bandit_json_not_dict(self):
        """Test parsing Bandit JSON that's not a dict."""
        results = _parse_bandit_json('["not", "a", "dict"]')
        assert results == []

    def test_parse_bandit_json_no_results(self):
        """Test parsing Bandit JSON with no results."""
        bandit_data = {"results": []}
        json_str = json.dumps(bandit_data)
        results = _parse_bandit_json(json_str)
        assert results == []


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""

    def test_parse_bandit_output_with_bandit_keyword(self):
        """Test parsing bandit output with 'bandit' keyword."""
        output = "bandit found issues"
        results = _parse_bandit_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "bandit:B101"
        assert results[0].message == "Sample bandit issue"

    def test_parse_bandit_output_without_bandit_keyword(self):
        """Test parsing bandit output without 'bandit' keyword."""
        output = "some other output"
        results = _parse_bandit_output(output)
        assert results == []


class TestParseFlake8Output:
    """Test _parse_flake8_output function."""

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

    def test_parse_flake8_output_invalid_format(self):
        """Test parsing Flake8 output with invalid format."""
        output = "invalid format line"
        results = _parse_flake8_output(output)
        assert results == []


class TestParseMypyOutput:
    """Test _parse_mypy_output function."""

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
        assert results[0].rule_id == "mypy-error"
        assert results[0].message == "Name 'x' is not defined"
        assert results[0].level == "error"

    def test_parse_mypy_output_with_column(self):
        """Test parsing MyPy output with column information."""
        output = "src/test.py:10:5: error: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)
        assert len(results) == 1
        assert results[0].locations[0]["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_mypy_output_warning_severity(self):
        """Test parsing MyPy output with warning severity."""
        output = "src/test.py:10:5: warning: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)
        assert len(results) == 1
        assert results[0].level == "warning"

    def test_parse_mypy_output_invalid_severity(self):
        """Test parsing MyPy output with invalid severity."""
        output = "src/test.py:10:5: info: Name 'x' is not defined [name-defined]"
        results = _parse_mypy_output(output)
        assert results == []

    def test_parse_mypy_output_invalid_format(self):
        """Test parsing MyPy output with invalid format."""
        output = "invalid format line"
        results = _parse_mypy_output(output)
        assert results == []


class TestCoveragePercentFromXml:
    """Test _coverage_percent_from_xml function."""

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

        with (
            patch("os.path.exists", side_effect=mock_exists),
            patch("defusedxml.ElementTree.parse") as mock_parse,
        ):
            mock_tree = MagicMock()
            mock_root = MagicMock()
            mock_root.attrib = {"line-rate": "0.86"}
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree

            result = _coverage_percent_from_xml("test_coverage.xml")
            assert result == 86

    def test_coverage_percent_from_xml_package_style(self):
        """Test coverage percent from XML with package style."""

        def mock_exists(path):
            return path == "test_coverage.xml"

        with (
            patch("os.path.exists", side_effect=mock_exists),
            patch("defusedxml.ElementTree.parse") as mock_parse,
        ):
            mock_tree = MagicMock()
            mock_root = MagicMock()
            mock_root.attrib = {}  # No line-rate in root
            mock_package = MagicMock()
            mock_package.attrib = {"line-rate": "0.75"}
            mock_root.findall.return_value = [mock_package]
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree

            result = _coverage_percent_from_xml("test_coverage.xml")
            assert result == 75

    def test_coverage_percent_from_xml_counter_style(self):
        """Test coverage percent from XML with counter style."""

        def mock_exists(path):
            return path == "test_coverage.xml"

        with (
            patch("os.path.exists", side_effect=mock_exists),
            patch("defusedxml.ElementTree.parse") as mock_parse,
        ):
            mock_tree = MagicMock()
            mock_root = MagicMock()
            mock_root.attrib = {}  # No line-rate in root
            mock_root.findall.return_value = []  # No packages

            # Mock counter elements
            mock_counter1 = MagicMock()
            mock_counter1.attrib = {"type": "LINE", "covered": "80", "missed": "20"}
            mock_counter2 = MagicMock()
            mock_counter2.attrib = {"type": "BRANCH", "covered": "10", "missed": "5"}

            # Mock the second findall call for counters
            def findall_side_effect(xpath):
                if xpath == ".//package":
                    return []
                elif xpath == ".//counter":
                    return [mock_counter1, mock_counter2]
                return []

            mock_root.findall.side_effect = findall_side_effect

            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree

            result = _coverage_percent_from_xml("test_coverage.xml")
            assert result == 80  # 80/(80+20) * 100 = 80

    def test_coverage_percent_from_xml_exception(self):
        """Test coverage percent from XML with exception."""

        def mock_exists(path):
            return path == "test_coverage.xml"

        with (
            patch("os.path.exists", side_effect=mock_exists),
            patch("defusedxml.ElementTree.parse", side_effect=Exception("Parse error")),
        ):
            result = _coverage_percent_from_xml("test_coverage.xml")
            assert result is None


class TestCovPercent:
    """Test cov_percent function."""

    def test_cov_percent_success(self):
        """Test cov_percent function success."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml", return_value=85):
            assert cov_percent() == 85

    def test_cov_percent_none(self):
        """Test cov_percent function with None result."""
        with patch(
            "src.ai_guard.analyzer._coverage_percent_from_xml", return_value=None
        ):
            assert cov_percent() is None

    def test_cov_percent_multiple_paths(self):
        """Test cov_percent function with multiple paths."""
        with patch("src.ai_guard.analyzer._coverage_percent_from_xml") as mock_func:
            mock_func.side_effect = [
                None,
                None,
                90,
            ]  # First two return None, third returns 90
            assert cov_percent() == 90


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report_json(self):
        """Test generating JSON report."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5,
        )

        report = generate_report(result, "json")
        assert isinstance(report, str)
        assert "issue1" in report

    def test_generate_report_html(self):
        """Test generating HTML report."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5,
        )

        report = generate_report(result, "html")
        assert isinstance(report, str)
        assert "<html>" in report
        assert "Issues: 3" in report  # The HTML report shows total issues count

    def test_generate_report_xml(self):
        """Test generating XML report."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5,
        )

        report = generate_report(result, "xml")
        assert isinstance(report, str)
        assert "<report>" in report

    def test_generate_report_unknown_format(self):
        """Test generating report with unknown format."""
        result = AnalysisResult()
        report = generate_report(result, "unknown")
        assert isinstance(report, str)
