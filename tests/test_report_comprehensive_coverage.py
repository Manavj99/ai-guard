"""Comprehensive coverage tests for report.py module to achieve 80% coverage."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, mock_open, MagicMock

from src.ai_guard.report import (
    GateResult,
    summarize,
    ReportGenerator,
    ReportGeneratorV2,
    ReportFormatter,
    generate_report,
    format_report_summary,
    save_report_to_file,
    load_report_from_file,
)


class TestGateResultComprehensive:
    """Comprehensive tests for GateResult dataclass."""

    def test_gate_result_all_fields(self):
        """Test GateResult with all fields specified."""
        result = GateResult(
            name="test_gate",
            passed=False,
            details="Gate failed due to security issues",
            exit_code=2,
        )
        assert result.name == "test_gate"
        assert result.passed is False
        assert result.details == "Gate failed due to security issues"
        assert result.exit_code == 2

    def test_gate_result_minimal(self):
        """Test GateResult with minimal required fields."""
        result = GateResult(name="minimal", passed=True)
        assert result.name == "minimal"
        assert result.passed is True
        assert result.details == ""
        assert result.exit_code == 0


class TestSummarizeComprehensive:
    """Comprehensive tests for summarize function."""

    def test_summarize_single_pass(self):
        """Test summarizing single passing result."""
        results = [GateResult(name="test", passed=True)]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 0
        # Check that success message was printed
        mock_print.assert_called_with("✅ All gates passed!")

    def test_summarize_single_fail(self):
        """Test summarizing single failing result."""
        results = [GateResult(name="test", passed=False, details="Failed")]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 1
        # Check that failure message was printed
        assert any(
            "❌ 1 gate(s) failed" in str(call) for call in mock_print.call_args_list
        )

    def test_summarize_multiple_mixed(self):
        """Test summarizing multiple mixed results."""
        results = [
            GateResult(name="gate1", passed=True),
            GateResult(name="gate2", passed=False, details="Security issue"),
            GateResult(name="gate3", passed=True),
        ]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 1

    def test_summarize_with_details(self):
        """Test summarizing results with details."""
        results = [
            GateResult(name="gate1", passed=True, details="All good"),
            GateResult(name="gate2", passed=False, details="Critical failure"),
        ]
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 1
        # Verify details are printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Critical failure" in call for call in print_calls)


class TestReportGeneratorComprehensive:
    """Comprehensive tests for ReportGenerator class."""

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

    def test_generate_summary_with_failures(self):
        """Test generating summary with failures."""
        generator = ReportGenerator()
        results = [
            GateResult(name="gate1", passed=True),
            GateResult(name="gate2", passed=False, details="Failed"),
            GateResult(name="gate3", passed=False, details="Critical error"),
        ]
        summary = generator.generate_summary(results)

        assert "Total: 3" in summary
        assert "Passed: 1" in summary
        assert "Failed: 2" in summary
        assert "Failed Gates:" in summary
        assert "gate2: Failed" in summary
        assert "gate3: Critical error" in summary

    def test_generate_summary_no_failures(self):
        """Test generating summary with no failures."""
        generator = ReportGenerator()
        results = [
            GateResult(name="gate1", passed=True),
            GateResult(name="gate2", passed=True),
        ]
        summary = generator.generate_summary(results)

        assert "Total: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary

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
            GateResult(name="security", passed=True, exit_code=0),
            GateResult(
                name="quality", passed=False, details="Low coverage", exit_code=1
            ),
        ]
        report = generator.generate_detailed_report(results)

        assert "Gate: security" in report
        assert "Status: PASSED" in report
        assert "Gate: quality" in report
        assert "Status: FAILED" in report
        assert "Details: Low coverage" in report
        assert "Exit Code: 0" in report
        assert "Exit Code: 1" in report


class TestReportGeneratorV2Comprehensive:
    """Comprehensive tests for ReportGeneratorV2 class."""

    def test_report_generator_v2_init_defaults(self):
        """Test ReportGeneratorV2 initialization with defaults."""
        generator = ReportGeneratorV2()
        assert generator.report_format == "json"
        assert generator.include_timestamp is True

    def test_report_generator_v2_init_custom(self):
        """Test ReportGeneratorV2 initialization with custom values."""
        generator = ReportGeneratorV2(report_format="html", include_timestamp=False)
        assert generator.report_format == "html"
        assert generator.include_timestamp is False

    def test_generate_report_json_format(self):
        """Test generating JSON format report."""
        generator = ReportGeneratorV2(report_format="json")
        analysis_results = {
            "files_analyzed": 10,
            "total_issues": 5,
            "issues_by_type": {"security": 2, "quality": 3},
        }

        report = generator.generate_report(analysis_results)

        assert report["success"] is True
        assert report["format"] == "json"
        assert "content" in report
        assert report["files_analyzed"] == 10
        assert report["total_issues"] == 5

    def test_generate_report_html_format(self):
        """Test generating HTML format report."""
        generator = ReportGeneratorV2(report_format="html")
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 1,
            "issues_by_type": {"security": 1},
        }

        report = generator.generate_report(analysis_results)

        assert report["success"] is True
        assert report["format"] == "html"
        assert "content" in report
        assert "<html>" in report["content"]
        assert "<title>AI-Guard Report</title>" in report["content"]

    def test_generate_report_unsupported_format(self):
        """Test generating report with unsupported format."""
        generator = ReportGeneratorV2(report_format="xml")
        analysis_results = {"files_analyzed": 5}

        report = generator.generate_report(analysis_results)

        assert report["success"] is False
        assert "Unsupported format: xml" in report["error"]

    def test_generate_json_report_private_method(self):
        """Test the private _generate_json_report method."""
        generator = ReportGeneratorV2()
        analysis_results = {
            "files_analyzed": 7,
            "total_issues": 4,
            "issues_by_type": {"performance": 4},
        }

        report = generator._generate_json_report(analysis_results)

        assert report["success"] is True
        assert report["format"] == "json"
        assert "content" in report
        assert report["files_analyzed"] == 7

    def test_generate_html_report_private_method(self):
        """Test the private _generate_html_report method."""
        generator = ReportGeneratorV2()
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 0,
            "issues_by_type": {},
        }

        report = generator._generate_html_report(analysis_results)

        assert report["success"] is True
        assert report["format"] == "html"
        assert "content" in report
        assert "Files analyzed: 2" in report["content"]
        assert "Total issues: 0" in report["content"]


class TestReportFormatterComprehensive:
    """Comprehensive tests for ReportFormatter class."""

    def test_report_formatter_init_defaults(self):
        """Test ReportFormatter initialization with defaults."""
        formatter = ReportFormatter()
        assert formatter.template_dir is None
        assert formatter.custom_styles is None

    def test_report_formatter_init_custom(self):
        """Test ReportFormatter initialization with custom values."""
        custom_styles = {"color": "red", "font": "Arial"}
        formatter = ReportFormatter(
            template_dir="/templates", custom_styles=custom_styles
        )
        assert formatter.template_dir == "/templates"
        assert formatter.custom_styles == custom_styles

    def test_format_summary(self):
        """Test formatting summary."""
        formatter = ReportFormatter()
        report_data = {
            "files_analyzed": 15,
            "total_issues": 8,
            "issues_by_type": {"security": 3, "quality": 5},
        }

        summary = formatter.format_summary(report_data)

        assert "15 files analyzed" in summary
        assert "8 total issues" in summary
        assert "3 securitys" in summary
        assert "5 qualitys" in summary

    def test_format_issues_list_empty(self):
        """Test formatting empty issues list."""
        formatter = ReportFormatter()
        issues = []

        formatted = formatter.format_issues_list(issues)

        assert formatted == "No issues found."

    def test_format_issues_list_with_issues(self):
        """Test formatting issues list with issues."""
        formatter = ReportFormatter()
        issues = [
            {"type": "security", "message": "SQL injection", "file": "app.py"},
            {"type": "quality", "message": "Low coverage", "file": "test.py"},
            {"type": "performance", "message": "Slow query", "file": "db.py"},
        ]

        formatted = formatter.format_issues_list(issues)

        assert "SECURITY: SQL injection (app.py)" in formatted
        assert "QUALITY: Low coverage (test.py)" in formatted
        assert "PERFORMANCE: Slow query (db.py)" in formatted

    def test_format_issues_list_missing_fields(self):
        """Test formatting issues list with missing fields."""
        formatter = ReportFormatter()
        issues = [{"type": "security"}, {"message": "Some issue"}, {}]

        formatted = formatter.format_issues_list(issues)

        assert "SECURITY: No message (unknown)" in formatted
        assert "UNKNOWN: Some issue (unknown)" in formatted
        assert "UNKNOWN: No message (unknown)" in formatted


class TestGenerateReportComprehensive:
    """Comprehensive tests for generate_report function."""

    def test_generate_report_full_data(self):
        """Test generating report with full data."""
        analysis_results = {
            "files_analyzed": 20,
            "total_issues": 12,
            "issues_by_type": {"security": 4, "quality": 6, "performance": 2},
        }

        report = generate_report(analysis_results)

        assert report["success"] is True
        assert report["timestamp"] == "2024-01-01T00:00:00Z"
        assert report["files_analyzed"] == 20
        assert report["total_issues"] == 12
        assert report["issues_by_type"] == {
            "security": 4,
            "quality": 6,
            "performance": 2,
        }
        assert "summary" in report

    def test_generate_report_minimal_data(self):
        """Test generating report with minimal data."""
        analysis_results = {}

        report = generate_report(analysis_results)

        assert report["success"] is True
        assert report["files_analyzed"] == 0
        assert report["total_issues"] == 0
        assert report["issues_by_type"] == {}

    def test_generate_report_partial_data(self):
        """Test generating report with partial data."""
        analysis_results = {"files_analyzed": 5}

        report = generate_report(analysis_results)

        assert report["files_analyzed"] == 5
        assert report["total_issues"] == 0
        assert report["issues_by_type"] == {}


class TestFormatReportSummaryComprehensive:
    """Comprehensive tests for format_report_summary function."""

    def test_format_summary_full_data(self):
        """Test formatting summary with full data."""
        report_data = {
            "files_analyzed": 25,
            "total_issues": 15,
            "issues_by_type": {"security": 5, "quality": 7, "performance": 3},
        }

        summary = format_report_summary(report_data)

        assert "25 files analyzed" in summary
        assert "15 total issues" in summary
        assert "5 securitys" in summary
        assert "7 qualitys" in summary
        assert "3 performances" in summary
        assert " | " in summary

    def test_format_summary_empty_data(self):
        """Test formatting summary with empty data."""
        report_data = {}

        summary = format_report_summary(report_data)

        assert "0 files analyzed" in summary
        assert "0 total issues" in summary

    def test_format_summary_no_issues_by_type(self):
        """Test formatting summary without issues_by_type."""
        report_data = {"files_analyzed": 10, "total_issues": 0}

        summary = format_report_summary(report_data)

        assert "10 files analyzed" in summary
        assert "0 total issues" in summary
        assert " | " in summary  # The function always uses " | " as separator


class TestSaveReportToFileComprehensive:
    """Comprehensive tests for save_report_to_file function."""

    def test_save_report_success(self):
        """Test successful report saving."""
        report_data = {"success": True, "files_analyzed": 5, "total_issues": 3}

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = temp_file.name

        try:
            result = save_report_to_file(report_data, temp_path)

            assert result["success"] is True
            assert os.path.exists(temp_path)

            # Verify file contents
            with open(temp_path, "r") as f:
                saved_data = json.load(f)
            assert saved_data == report_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_report_permission_error(self):
        """Test saving report with permission error."""
        report_data = {"test": "data"}
        invalid_path = "/invalid/path/that/does/not/exist/report.json"

        result = save_report_to_file(report_data, invalid_path)

        assert result["success"] is False
        assert "error" in result

    def test_save_report_json_error(self):
        """Test saving report with JSON serialization error."""
        # Create data that can't be JSON serialized
        report_data = {"circular_ref": {}}
        report_data["circular_ref"]["self"] = report_data

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = temp_file.name

        try:
            result = save_report_to_file(report_data, temp_path)
            assert result["success"] is False
            assert "error" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestLoadReportFromFileComprehensive:
    """Comprehensive tests for load_report_from_file function."""

    def test_load_report_success(self):
        """Test successful report loading."""
        report_data = {"success": True, "files_analyzed": 8, "total_issues": 4}

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            json.dump(report_data, temp_file)
            temp_path = temp_file.name

        try:
            result = load_report_from_file(temp_path)

            assert result["success"] is True
            assert "data" in result
            assert result["data"] == report_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_report_file_not_found(self):
        """Test loading non-existent report file."""
        result = load_report_from_file("/non/existent/file.json")

        assert result["success"] is False
        assert result["error"] == "File not found"

    def test_load_report_invalid_json(self):
        """Test loading report with invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_file.write("invalid json content")
            temp_path = temp_file.name

        try:
            result = load_report_from_file(temp_path)

            assert result["success"] is False
            assert result["error"] == "Invalid JSON format"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_report_permission_error(self):
        """Test loading report with permission error."""
        # This test might not work on all systems, but we can try
        result = load_report_from_file("/root/protected/file.json")

        # Should either fail with permission error or file not found
        assert result["success"] is False
        assert "error" in result

    def test_load_report_general_exception(self):
        """Test loading report with general exception."""
        # Mock open to raise a general exception
        with patch("builtins.open", side_effect=Exception("General error")):
            result = load_report_from_file("test.json")

            assert result["success"] is False
            assert result["error"] == "General error"


class TestIntegrationComprehensive:
    """Integration tests combining multiple functions."""

    def test_full_report_workflow(self):
        """Test complete report generation and saving workflow."""
        # Create analysis results
        analysis_results = {
            "files_analyzed": 12,
            "total_issues": 6,
            "issues_by_type": {"security": 2, "quality": 4},
        }

        # Generate report
        report = generate_report(analysis_results)
        assert report["success"] is True

        # Save report
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = temp_file.name

        try:
            save_result = save_report_to_file(report, temp_path)
            assert save_result["success"] is True

            # Load report
            load_result = load_report_from_file(temp_path)
            assert load_result["success"] is True
            assert load_result["data"] == report
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_gate_results_to_report_workflow(self):
        """Test workflow from gate results to final report."""
        # Create gate results
        gate_results = [
            GateResult(name="security", passed=True),
            GateResult(name="coverage", passed=False, details="Below threshold"),
            GateResult(name="performance", passed=True),
        ]

        # Summarize (should return 1 due to failed coverage gate)
        with patch("builtins.print"):
            exit_code = summarize(gate_results)
        assert exit_code == 1

        # Generate summary report
        generator = ReportGenerator()
        summary = generator.generate_summary(gate_results)
        assert "Failed: 1" in summary
        assert "coverage: Below threshold" in summary

        # Generate detailed report
        detailed = generator.generate_detailed_report(gate_results)
        assert "coverage" in detailed
        assert "Below threshold" in detailed

    def test_report_formatter_v2_workflow(self):
        """Test ReportGeneratorV2 with ReportFormatter workflow."""
        analysis_results = {
            "files_analyzed": 30,
            "total_issues": 20,
            "issues_by_type": {"security": 8, "quality": 12},
        }

        # Generate JSON report
        json_generator = ReportGeneratorV2(report_format="json")
        json_report = json_generator.generate_report(analysis_results)
        assert json_report["success"] is True
        assert json_report["format"] == "json"

        # Generate HTML report
        html_generator = ReportGeneratorV2(report_format="html")
        html_report = html_generator.generate_report(analysis_results)
        assert html_report["success"] is True
        assert html_report["format"] == "html"

        # Format with ReportFormatter
        formatter = ReportFormatter()
        summary = formatter.format_summary(analysis_results)
        assert "30 files analyzed" in summary
        assert "20 total issues" in summary
