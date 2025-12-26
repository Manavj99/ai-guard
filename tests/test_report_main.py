"""Comprehensive tests for report.py module."""

import json
import tempfile
import pytest
from unittest.mock import patch, mock_open
from src.ai_guard.report import (
    GateResult,
    summarize,
    ReportGenerator,
    generate_report,
    format_report_summary,
    save_report_to_file,
    load_report_from_file,
    ReportGeneratorV2,
    ReportFormatter,
)


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_creation(self):
        """Test creating GateResult with all parameters."""
        result = GateResult(
            name="test_gate", passed=True, details="Test passed", exit_code=0
        )
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == "Test passed"
        assert result.exit_code == 0

    def test_gate_result_minimal(self):
        """Test creating GateResult with minimal parameters."""
        result = GateResult(name="test_gate", passed=True)
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == ""
        assert result.exit_code == 0

    def test_gate_result_failed(self):
        """Test creating failed GateResult."""
        result = GateResult(
            name="test_gate", passed=False, details="Test failed", exit_code=1
        )
        assert result.name == "test_gate"
        assert result.passed is False
        assert result.details == "Test failed"
        assert result.exit_code == 1


class TestSummarize:
    """Test summarize function."""

    def test_summarize_empty_results(self):
        """Test summarizing empty results."""
        with patch("builtins.print") as mock_print:
            exit_code = summarize([])
            assert exit_code == 0
            mock_print.assert_called()

    def test_summarize_all_passed(self):
        """Test summarizing all passed results."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Passed"),
            GateResult("gate3", True, "Passed"),
        ]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 0
            mock_print.assert_called()

    def test_summarize_all_failed(self):
        """Test summarizing all failed results."""
        results = [
            GateResult("gate1", False, "Failed"),
            GateResult("gate2", False, "Failed"),
        ]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 1
            mock_print.assert_called()

    def test_summarize_mixed_results(self):
        """Test summarizing mixed results."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", True, "Passed"),
            GateResult("gate4", False, "Failed"),
        ]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 1
            mock_print.assert_called()

    def test_summarize_with_details(self):
        """Test summarizing results with details."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 1
            mock_print.assert_called()


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_generate_summary_empty(self):
        """Test generating summary with empty results."""
        generator = ReportGenerator()
        summary = generator.generate_summary([])
        assert "Total: 0" in summary
        assert "Passed: 0" in summary
        assert "Failed: 0" in summary

    def test_generate_summary_all_passed(self):
        """Test generating summary with all passed results."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Passed"),
        ]
        summary = generator.generate_summary(results)
        assert "Total: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary

    def test_generate_summary_with_failures(self):
        """Test generating summary with failed results."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]
        summary = generator.generate_summary(results)
        assert "Total: 2" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary
        assert "gate2: Failed" in summary

    def test_generate_detailed_report_empty(self):
        """Test generating detailed report with empty results."""
        generator = ReportGenerator()
        report = generator.generate_detailed_report([])
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" * 50 in report

    def test_generate_detailed_report_with_results(self):
        """Test generating detailed report with results."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed", 0),
            GateResult("gate2", False, "Failed", 1),
        ]
        report = generator.generate_detailed_report(results)
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate: gate1" in report
        assert "Gate: gate2" in report
        assert "Status: PASSED" in report
        assert "Status: FAILED" in report
        assert "Details: Passed" in report
        assert "Details: Failed" in report
        assert "Exit Code: 0" in report
        assert "Exit Code: 1" in report


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report_empty(self):
        """Test generating report with empty analysis results."""
        report = generate_report({})
        assert report["success"] is True
        assert report["timestamp"] == "2024-01-01T00:00:00Z"
        assert report["files_analyzed"] == 0
        assert report["total_issues"] == 0
        assert report["issues_by_type"] == {}

    def test_generate_report_with_data(self):
        """Test generating report with analysis data."""
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 10,
            "issues_by_type": {"error": 5, "warning": 3, "info": 2},
        }
        report = generate_report(analysis_results)
        assert report["success"] is True
        assert report["files_analyzed"] == 5
        assert report["total_issues"] == 10
        assert report["issues_by_type"] == {"error": 5, "warning": 3, "info": 2}


class TestFormatReportSummary:
    """Test format_report_summary function."""

    def test_format_report_summary_empty(self):
        """Test formatting empty report summary."""
        summary = format_report_summary({})
        assert "0 files analyzed" in summary
        assert "0 total issues" in summary

    def test_format_report_summary_with_data(self):
        """Test formatting report summary with data."""
        report_data = {
            "files_analyzed": 3,
            "total_issues": 5,
            "issues_by_type": {"error": 2, "warning": 3},
        }
        summary = format_report_summary(report_data)
        assert "3 files analyzed" in summary
        assert "5 total issues" in summary
        assert "2 errors" in summary
        assert "3 warnings" in summary


class TestSaveReportToFile:
    """Test save_report_to_file function."""

    def test_save_report_to_file_success(self):
        """Test successful report saving."""
        report_data = {"test": "data"}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            file_path = f.name

        try:
            result = save_report_to_file(report_data, file_path)
            assert result["success"] is True

            # Verify file was created and contains correct data
            with open(file_path, "r") as f:
                saved_data = json.load(f)
            assert saved_data == report_data
        finally:
            import os

            os.unlink(file_path)

    def test_save_report_to_file_error(self):
        """Test report saving with error."""
        report_data = {"test": "data"}
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = save_report_to_file(report_data, "/invalid/path.json")
            assert result["success"] is False
            assert "error" in result
            assert "Permission denied" in result["error"]


class TestLoadReportFromFile:
    """Test load_report_from_file function."""

    def test_load_report_from_file_success(self):
        """Test successful report loading."""
        report_data = {"test": "data"}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(report_data, f)
            file_path = f.name

        try:
            result = load_report_from_file(file_path)
            assert result["success"] is True
            assert result["data"] == report_data
        finally:
            import os

            os.unlink(file_path)

    def test_load_report_from_file_not_found(self):
        """Test loading non-existent file."""
        result = load_report_from_file("/nonexistent/file.json")
        assert result["success"] is False
        assert result["error"] == "File not found"

    def test_load_report_from_file_invalid_json(self):
        """Test loading file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("invalid json content")
            file_path = f.name

        try:
            result = load_report_from_file(file_path)
            assert result["success"] is False
            assert result["error"] == "Invalid JSON format"
        finally:
            import os

            os.unlink(file_path)

    def test_load_report_from_file_other_error(self):
        """Test loading file with other error."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = load_report_from_file("/restricted/file.json")
            assert result["success"] is False
            assert "error" in result


class TestReportGeneratorV2:
    """Test ReportGeneratorV2 class."""

    def test_report_generator_v2_init_default(self):
        """Test ReportGeneratorV2 initialization with default parameters."""
        generator = ReportGeneratorV2()
        assert generator.report_format == "json"
        assert generator.include_timestamp is True

    def test_report_generator_v2_init_custom(self):
        """Test ReportGeneratorV2 initialization with custom parameters."""
        generator = ReportGeneratorV2(report_format="html", include_timestamp=False)
        assert generator.report_format == "html"
        assert generator.include_timestamp is False

    def test_generate_report_json(self):
        """Test generating JSON report."""
        generator = ReportGeneratorV2(report_format="json")
        analysis_results = {"files_analyzed": 2, "total_issues": 3}
        report = generator.generate_report(analysis_results)
        assert report["success"] is True
        assert report["format"] == "json"
        assert "content" in report
        assert "files_analyzed" in report

    def test_generate_report_html(self):
        """Test generating HTML report."""
        generator = ReportGeneratorV2(report_format="html")
        analysis_results = {"files_analyzed": 2, "total_issues": 3}
        report = generator.generate_report(analysis_results)
        assert report["success"] is True
        assert report["format"] == "html"
        assert "content" in report
        assert "<html>" in report["content"]
        assert "Files analyzed: 2" in report["content"]

    def test_generate_report_unsupported_format(self):
        """Test generating report with unsupported format."""
        generator = ReportGeneratorV2(report_format="xml")
        analysis_results = {"files_analyzed": 2, "total_issues": 3}
        report = generator.generate_report(analysis_results)
        assert report["success"] is False
        assert "Unsupported format: xml" in report["error"]


class TestReportFormatter:
    """Test ReportFormatter class."""

    def test_report_formatter_init_default(self):
        """Test ReportFormatter initialization with default parameters."""
        formatter = ReportFormatter()
        assert formatter.template_dir is None
        assert formatter.custom_styles is None

    def test_report_formatter_init_custom(self):
        """Test ReportFormatter initialization with custom parameters."""
        custom_styles = {"color": "red"}
        formatter = ReportFormatter(
            template_dir="/templates", custom_styles=custom_styles
        )
        assert formatter.template_dir == "/templates"
        assert formatter.custom_styles == custom_styles

    def test_format_summary(self):
        """Test formatting summary."""
        formatter = ReportFormatter()
        report_data = {
            "files_analyzed": 2,
            "total_issues": 3,
            "issues_by_type": {"error": 1, "warning": 2},
        }
        summary = formatter.format_summary(report_data)
        assert "2 files analyzed" in summary
        assert "3 total issues" in summary
        assert "1 errors" in summary
        assert "2 warnings" in summary

    def test_format_issues_list_empty(self):
        """Test formatting empty issues list."""
        formatter = ReportFormatter()
        issues = []
        result = formatter.format_issues_list(issues)
        assert result == "No issues found."

    def test_format_issues_list_with_issues(self):
        """Test formatting issues list with issues."""
        formatter = ReportFormatter()
        issues = [
            {"type": "error", "message": "Syntax error", "file": "test.py"},
            {"type": "warning", "message": "Unused variable", "file": "main.py"},
        ]
        result = formatter.format_issues_list(issues)
        assert "ERROR: Syntax error (test.py)" in result
        assert "WARNING: Unused variable (main.py)" in result

    def test_format_issues_list_missing_fields(self):
        """Test formatting issues list with missing fields."""
        formatter = ReportFormatter()
        issues = [
            {"type": "error"},  # Missing message and file
            {"message": "Some message"},  # Missing type and file
        ]
        result = formatter.format_issues_list(issues)
        assert "ERROR: No message (unknown)" in result
        assert "UNKNOWN: Some message (unknown)" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_summarize_with_none_details(self):
        """Test summarize with None details."""
        results = [GateResult("test", True, None)]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 0

    def test_generate_summary_with_none_details(self):
        """Test generate_summary with None details."""
        generator = ReportGenerator()
        results = [GateResult("test", False, None)]
        summary = generator.generate_summary(results)
        assert "test: " in summary  # Should handle None details gracefully

    def test_format_report_summary_with_none_values(self):
        """Test format_report_summary with None values."""
        report_data = {
            "files_analyzed": None,
            "total_issues": None,
            "issues_by_type": None,
        }
        summary = format_report_summary(report_data)
        assert "None files analyzed" in summary
        assert "None total issues" in summary

    def test_save_report_to_file_with_none_data(self):
        """Test saving None data to file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            file_path = f.name

        try:
            result = save_report_to_file(None, file_path)
            assert result["success"] is True
        finally:
            import os

            os.unlink(file_path)

    def test_load_report_from_file_with_none_path(self):
        """Test loading report with None file path."""
        result = load_report_from_file(None)
        assert result["success"] is False
        assert "error" in result


class TestIntegration:
    """Test integration scenarios."""

    def test_full_workflow(self):
        """Test full workflow from results to report generation."""
        # Create test results
        results = [
            GateResult("Linting", True, "No issues found"),
            GateResult("Tests", False, "2 tests failed"),
            GateResult("Coverage", True, "85% coverage"),
            GateResult("Security", False, "1 vulnerability found"),
        ]

        # Test summarize function
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 1  # Some gates failed

        # Test ReportGenerator
        generator = ReportGenerator()
        summary = generator.generate_summary(results)
        assert "Total: 4" in summary
        assert "Passed: 2" in summary
        assert "Failed: 2" in summary

        # Test detailed report
        detailed_report = generator.generate_detailed_report(results)
        assert "AI-Guard Quality Gates Detailed Report" in detailed_report

        # Test report generation
        analysis_results = {
            "files_analyzed": 10,
            "total_issues": 5,
            "issues_by_type": {"error": 2, "warning": 3},
        }
        report = generate_report(analysis_results)
        assert report["success"] is True
        assert report["files_analyzed"] == 10

    def test_report_generator_v2_workflow(self):
        """Test ReportGeneratorV2 workflow."""
        generator = ReportGeneratorV2(report_format="json")
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 1, "warning": 2},
        }

        report = generator.generate_report(analysis_results)
        assert report["success"] is True
        assert report["format"] == "json"
        assert "content" in report

    def test_file_operations_workflow(self):
        """Test file save and load workflow."""
        report_data = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1},
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            file_path = f.name

        try:
            # Save report
            save_result = save_report_to_file(report_data, file_path)
            assert save_result["success"] is True

            # Load report
            load_result = load_report_from_file(file_path)
            assert load_result["success"] is True
            assert load_result["data"] == report_data
        finally:
            import os

            os.unlink(file_path)
