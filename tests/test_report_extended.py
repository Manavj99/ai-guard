"""Extended tests for report modules to improve coverage."""

import pytest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from src.ai_guard.report import (
    GateResult,
    summarize,
    ReportGenerator,
    generate_report,
    format_report_summary,
    save_report_to_file,
    load_report_from_file,
    ReportFormatter
)
from src.ai_guard.report_html import (
    write_html,
    HTMLReportGenerator,
    generate_html_report,
    format_html_summary,
    create_html_table
)


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_creation(self):
        """Test GateResult creation with all parameters."""
        result = GateResult(
            name="test_gate",
            passed=True,
            details="Test details",
            exit_code=0
        )
        
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == "Test details"
        assert result.exit_code == 0

    def test_gate_result_defaults(self):
        """Test GateResult creation with defaults."""
        result = GateResult(name="test_gate", passed=False)
        
        assert result.name == "test_gate"
        assert result.passed is False
        assert result.details == ""
        assert result.exit_code == 0


class TestSummarize:
    """Test summarize function."""

    @patch('builtins.print')
    def test_summarize_all_passed(self, mock_print):
        """Test summarize with all gates passed."""
        results = [
            GateResult("gate1", True, "Success"),
            GateResult("gate2", True, "Success")
        ]
        
        exit_code = summarize(results)
        
        assert exit_code == 0
        assert mock_print.call_count >= 3  # Header, gates, footer

    @patch('builtins.print')
    def test_summarize_some_failed(self, mock_print):
        """Test summarize with some gates failed."""
        results = [
            GateResult("gate1", True, "Success"),
            GateResult("gate2", False, "Failed")
        ]
        
        exit_code = summarize(results)
        
        assert exit_code == 1
        assert mock_print.call_count >= 3

    @patch('builtins.print')
    def test_summarize_empty_results(self, mock_print):
        """Test summarize with empty results."""
        results = []
        
        exit_code = summarize(results)
        
        assert exit_code == 0


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_generate_report_json(self):
        """Test JSON report generation."""
        generator = ReportGenerator("json")
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        result = generator.generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['format'] == "json"
        assert 'content' in result

    def test_generate_report_html(self):
        """Test HTML report generation."""
        generator = ReportGenerator("html")
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        result = generator.generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['format'] == "html"
        assert 'content' in result

    def test_report_generator_with_format(self):
        """Test ReportGenerator with specific format."""
        generator = ReportGenerator("json", True)
        
        assert generator.report_format == "json"
        assert generator.include_timestamp is True

    def test_generate_report_json(self):
        """Test JSON report generation."""
        generator = ReportGenerator("json")
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        result = generator.generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['format'] == "json"
        assert 'content' in result

    def test_generate_report_html(self):
        """Test HTML report generation."""
        generator = ReportGenerator("html")
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        result = generator.generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['format'] == "html"
        assert 'content' in result

    def test_generate_report_unsupported_format(self):
        """Test unsupported format handling."""
        generator = ReportGenerator("xml")
        analysis_results = {}
        
        result = generator.generate_report(analysis_results)
        
        assert result['success'] is False
        assert 'error' in result


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report_basic(self):
        """Test basic report generation."""
        analysis_results = {
            "files_analyzed": 10,
            "total_issues": 5,
            "issues_by_type": {"error": 3, "warning": 2}
        }
        
        result = generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['files_analyzed'] == 10
        assert result['total_issues'] == 5
        assert 'summary' in result

    def test_generate_report_empty(self):
        """Test report generation with empty results."""
        analysis_results = {}
        
        result = generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['files_analyzed'] == 0
        assert result['total_issues'] == 0


class TestFormatReportSummary:
    """Test format_report_summary function."""

    def test_format_report_summary_basic(self):
        """Test basic report summary formatting."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        summary = format_report_summary(report_data)
        
        assert "5 files analyzed" in summary
        assert "3 total issues" in summary
        assert "2 errors" in summary
        assert "1 warnings" in summary

    def test_format_report_summary_empty(self):
        """Test report summary formatting with empty data."""
        report_data = {}
        
        summary = format_report_summary(report_data)
        
        assert "0 files analyzed" in summary
        assert "0 total issues" in summary


class TestSaveLoadReport:
    """Test save and load report functions."""

    @patch('builtins.open', mock_open())
    def test_save_report_to_file_success(self):
        """Test successful report saving."""
        report_data = {"test": "data"}
        
        result = save_report_to_file(report_data, "test.json")
        
        assert result['success'] is True

    def test_save_report_to_file_error(self):
        """Test report saving with error."""
        report_data = {"test": "data"}
        
        with patch('builtins.open', side_effect=Exception("Write error")):
            result = save_report_to_file(report_data, "test.json")
            
            assert result['success'] is False
            assert 'error' in result

    @patch('builtins.open', mock_open(read_data='{"test": "data"}'))
    def test_load_report_from_file_success(self):
        """Test successful report loading."""
        result = load_report_from_file("test.json")
        
        assert result['success'] is True
        assert result['data']['test'] == "data"

    def test_load_report_from_file_not_found(self):
        """Test report loading with file not found."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = load_report_from_file("missing.json")
            
            assert result['success'] is False
            assert result['error'] == "File not found"

    def test_load_report_from_file_invalid_json(self):
        """Test report loading with invalid JSON."""
        with patch('builtins.open', mock_open(read_data='invalid json')):
            result = load_report_from_file("test.json")
            
            assert result['success'] is False
            assert 'error' in result

    def test_load_report_from_file_general_error(self):
        """Test report loading with general error."""
        with patch('builtins.open', side_effect=Exception("General error")):
            result = load_report_from_file("test.json")
            
            assert result['success'] is False
            assert 'error' in result


class TestReportFormatter:
    """Test ReportFormatter class."""

    def test_report_formatter_init(self):
        """Test ReportFormatter initialization."""
        formatter = ReportFormatter()
        assert formatter.template_dir is None
        assert formatter.custom_styles is None

    def test_report_formatter_init_with_params(self):
        """Test ReportFormatter initialization with parameters."""
        custom_styles = {"color": "red"}
        formatter = ReportFormatter("templates", custom_styles)
        
        assert formatter.template_dir == "templates"
        assert formatter.custom_styles == custom_styles

    def test_format_summary(self):
        """Test format_summary method."""
        formatter = ReportFormatter()
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        summary = formatter.format_summary(report_data)
        
        assert "5 files analyzed" in summary
        assert "3 total issues" in summary

    def test_format_issues_list_empty(self):
        """Test format_issues_list with empty list."""
        formatter = ReportFormatter()
        
        result = formatter.format_issues_list([])
        
        assert result == "No issues found."

    def test_format_issues_list_with_issues(self):
        """Test format_issues_list with issues."""
        formatter = ReportFormatter()
        issues = [
            {"type": "error", "message": "Test error", "file": "test.py"},
            {"type": "warning", "message": "Test warning", "file": "test.py"}
        ]
        
        result = formatter.format_issues_list(issues)
        
        assert "ERROR: Test error" in result
        assert "WARNING: Test warning" in result


class TestHTMLReportFunctions:
    """Test HTML report functions."""

    @patch('builtins.open', mock_open())
    def test_write_html(self):
        """Test write_html function."""
        gates = [
            GateResult("gate1", True, "Success"),
            GateResult("gate2", False, "Failed")
        ]
        findings = [
            {"path": "test.py", "line": 10, "level": "error", "rule_id": "E501", "message": "Line too long"}
        ]
        
        write_html("test.html", gates, findings)
        
        # Function should complete without error

    def test_generate_html_report(self):
        """Test generate_html_report function."""
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues": [
                {"type": "error", "message": "Test error", "file": "test.py", "line": 10}
            ]
        }
        
        result = generate_html_report(analysis_results)
        
        assert result['success'] is True
        assert result['format'] == "html"
        assert 'content' in result

    def test_format_html_summary(self):
        """Test format_html_summary function."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 2, "warning": 1}
        }
        
        result = format_html_summary(report_data)
        
        assert "Files analyzed: 5" in result
        assert "Total issues: 3" in result

    def test_create_html_table(self):
        """Test create_html_table function."""
        data = [
            {"name": "test1", "value": 1},
            {"name": "test2", "value": 2}
        ]
        columns = ["name", "value"]
        
        result = create_html_table(data, columns)
        
        assert "<table>" in result
        assert "test1" in result
        assert "test2" in result


class TestHTMLReportGenerator:
    """Test HTMLReportGenerator class."""

    def test_html_report_generator_init(self):
        """Test HTMLReportGenerator initialization."""
        generator = HTMLReportGenerator()
        assert generator is not None

    def test_generate_report_method(self):
        """Test generate_report method."""
        generator = HTMLReportGenerator()
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues": []
        }
        
        result = generator.generate_report(analysis_results)
        
        assert result['success'] is True
        assert result['format'] == "html"
