"""Additional tests for report modules."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from ai_guard.report import (
    generate_report,
    format_report_summary,
    save_report_to_file,
    load_report_from_file,
    ReportGenerator,
    ReportFormatter
)
from ai_guard.report_html import (
    generate_html_report,
    format_html_summary,
    create_html_table,
    HTMLReportGenerator
)
from ai_guard.report_json import (
    generate_json_report,
    format_json_summary,
    JSONReportGenerator
)
from ai_guard.sarif_report import (
    generate_sarif_report,
    create_sarif_run,
    create_sarif_result,
    SARIFReportGenerator
)


class TestReportGeneration:
    """Test report generation functions."""

    def test_generate_report_success(self):
        """Test successful report generation."""
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {
                "error": 1,
                "warning": 2
            }
        }
        
        report = generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["files_analyzed"] == 5
        assert report["total_issues"] == 3
        assert report["issues_by_type"]["error"] == 1
        assert report["issues_by_type"]["warning"] == 2

    def test_generate_report_empty_results(self):
        """Test report generation with empty results."""
        analysis_results = {
            "files_analyzed": 0,
            "total_issues": 0,
            "issues_by_type": {}
        }
        
        report = generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["files_analyzed"] == 0
        assert report["total_issues"] == 0

    def test_format_report_summary(self):
        """Test report summary formatting."""
        report_data = {
            "files_analyzed": 10,
            "total_issues": 5,
            "issues_by_type": {
                "error": 2,
                "warning": 3
            }
        }
        
        summary = format_report_summary(report_data)
        
        assert "10 files analyzed" in summary
        assert "5 total issues" in summary
        assert "2 errors" in summary
        assert "3 warnings" in summary

    def test_save_report_to_file_success(self):
        """Test successful report saving to file."""
        report_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            result = save_report_to_file(report_data, temp_path)
            
            assert result["success"] is True
            
            # Verify file was created and contains data
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == report_data
        finally:
            os.unlink(temp_path)

    def test_save_report_to_file_error(self):
        """Test report saving error."""
        report_data = {"test": "data"}
        
        # Try to save to invalid path
        result = save_report_to_file(report_data, "/invalid/path/report.json")
        
        assert result["success"] is False
        assert "error" in result

    def test_load_report_from_file_success(self):
        """Test successful report loading from file."""
        report_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(report_data, f)
            temp_path = f.name
        
        try:
            result = load_report_from_file(temp_path)
            
            assert result["success"] is True
            assert result["data"] == report_data
        finally:
            os.unlink(temp_path)

    def test_load_report_from_file_not_found(self):
        """Test report loading from non-existent file."""
        result = load_report_from_file("nonexistent.json")
        
        assert result["success"] is False
        assert "error" in result

    def test_load_report_from_file_invalid_json(self):
        """Test report loading from file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("invalid json")
            temp_path = f.name
        
        try:
            result = load_report_from_file(temp_path)
            
            assert result["success"] is False
            assert "error" in result
        finally:
            os.unlink(temp_path)


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_generator_init(self):
        """Test generator initialization."""
        generator = ReportGenerator()
        
        assert generator.report_format == "json"
        assert generator.include_timestamp is True

    def test_generator_init_custom(self):
        """Test generator initialization with custom settings."""
        generator = ReportGenerator(
            report_format="html",
            include_timestamp=False
        )
        
        assert generator.report_format == "html"
        assert generator.include_timestamp is False

    def test_generate_report_json(self):
        """Test generating JSON report."""
        generator = ReportGenerator(report_format="json")
        
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "json"
        assert report["files_analyzed"] == 3

    def test_generate_report_html(self):
        """Test generating HTML report."""
        generator = ReportGenerator(report_format="html")
        
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "html"
        assert "<html>" in report["content"]

    def test_generate_report_unsupported_format(self):
        """Test generating report with unsupported format."""
        generator = ReportGenerator(report_format="xml")
        
        analysis_results = {"files_analyzed": 3}
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is False
        assert "error" in report


class TestReportFormatter:
    """Test ReportFormatter class."""

    def test_formatter_init(self):
        """Test formatter initialization."""
        formatter = ReportFormatter()
        
        assert formatter.template_dir is None
        assert formatter.custom_styles is None

    def test_format_summary(self):
        """Test formatting summary."""
        formatter = ReportFormatter()
        
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {
                "error": 1,
                "warning": 2
            }
        }
        
        summary = formatter.format_summary(report_data)
        
        assert "5 files analyzed" in summary
        assert "3 total issues" in summary
        assert "1 errors" in summary
        assert "2 warnings" in summary

    def test_format_issues_list(self):
        """Test formatting issues list."""
        formatter = ReportFormatter()
        
        issues = [
            {"type": "error", "message": "Error 1", "file": "test1.py"},
            {"type": "warning", "message": "Warning 1", "file": "test2.py"}
        ]
        
        formatted = formatter.format_issues_list(issues)
        
        assert "Error 1" in formatted
        assert "Warning 1" in formatted
        assert "test1.py" in formatted
        assert "test2.py" in formatted


class TestHTMLReportGeneration:
    """Test HTML report generation."""

    def test_generate_html_report_success(self):
        """Test successful HTML report generation."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues": [
                {"type": "error", "message": "Error 1", "file": "test.py", "line": 10},
                {"type": "warning", "message": "Warning 1", "file": "test.py", "line": 20}
            ]
        }
        
        html_report = generate_html_report(analysis_results)
        
        assert html_report["success"] is True
        assert "<html>" in html_report["content"]
        assert "<head>" in html_report["content"]
        assert "<body>" in html_report["content"]
        assert "Error 1" in html_report["content"]
        assert "Warning 1" in html_report["content"]

    def test_format_html_summary(self):
        """Test HTML summary formatting."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {
                "error": 1,
                "warning": 2
            }
        }
        
        summary = format_html_summary(report_data)
        
        assert "<div" in summary
        assert "5 files analyzed" in summary
        assert "3 total issues" in summary

    def test_create_html_table(self):
        """Test HTML table creation."""
        data = [
            {"file": "test1.py", "issues": 2, "status": "warning"},
            {"file": "test2.py", "issues": 1, "status": "error"}
        ]
        
        table = create_html_table(data, ["file", "issues", "status"])
        
        assert "<table>" in table
        assert "<thead>" in table
        assert "<tbody>" in table
        assert "test1.py" in table
        assert "test2.py" in table

    def test_html_report_generator(self):
        """Test HTML report generator class."""
        generator = HTMLReportGenerator()
        
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "html"
        assert "<html>" in report["content"]


class TestJSONReportGeneration:
    """Test JSON report generation."""

    def test_generate_json_report_success(self):
        """Test successful JSON report generation."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues": [
                {"type": "error", "message": "Error 1", "file": "test.py"},
                {"type": "warning", "message": "Warning 1", "file": "test.py"}
            ]
        }
        
        json_report = generate_json_report(analysis_results)
        
        assert json_report["success"] is True
        assert json_report["format"] == "json"
        
        # Parse the JSON content
        content = json.loads(json_report["content"])
        assert content["files_analyzed"] == 3
        assert content["total_issues"] == 2
        assert len(content["issues"]) == 2

    def test_format_json_summary(self):
        """Test JSON summary formatting."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {
                "error": 1,
                "warning": 2
            }
        }
        
        summary = format_json_summary(report_data)
        
        # Parse the JSON summary
        summary_data = json.loads(summary)
        assert summary_data["files_analyzed"] == 5
        assert summary_data["total_issues"] == 3
        assert summary_data["issues_by_type"]["error"] == 1

    def test_json_report_generator(self):
        """Test JSON report generator class."""
        generator = JSONReportGenerator()
        
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "json"
        
        # Parse the JSON content
        content = json.loads(report["content"])
        assert content["files_analyzed"] == 2


class TestSARIFReportGeneration:
    """Test SARIF report generation."""

    def test_generate_sarif_report_success(self):
        """Test successful SARIF report generation."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues": [
                {
                    "type": "error",
                    "message": "Error 1",
                    "file": "test.py",
                    "line": 10,
                    "rule_id": "rule1"
                },
                {
                    "type": "warning",
                    "message": "Warning 1",
                    "file": "test.py",
                    "line": 20,
                    "rule_id": "rule2"
                }
            ]
        }
        
        sarif_report = generate_sarif_report(analysis_results)
        
        assert sarif_report["success"] is True
        assert sarif_report["format"] == "sarif"
        
        # Parse the SARIF content
        content = json.loads(sarif_report["content"])
        assert content["$schema"] == "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
        assert content["version"] == "2.1.0"
        assert len(content["runs"]) == 1

    def test_create_sarif_run(self):
        """Test SARIF run creation."""
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1,
            "issues": [
                {
                    "type": "error",
                    "message": "Error 1",
                    "file": "test.py",
                    "line": 10,
                    "rule_id": "rule1"
                }
            ]
        }
        
        sarif_run = create_sarif_run(analysis_results)
        
        assert sarif_run["tool"]["driver"]["name"] == "AI-Guard"
        assert len(sarif_run["results"]) == 1
        assert sarif_run["results"][0]["ruleId"] == "rule1"

    def test_create_sarif_result(self):
        """Test SARIF result creation."""
        issue = {
            "type": "error",
            "message": "Error 1",
            "file": "test.py",
            "line": 10,
            "rule_id": "rule1"
        }
        
        result = create_sarif_result(issue)
        
        assert result["ruleId"] == "rule1"
        assert result["level"] == "error"
        assert result["message"]["text"] == "Error 1"
        assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 10

    def test_sarif_report_generator(self):
        """Test SARIF report generator class."""
        generator = SARIFReportGenerator()
        
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1,
            "issues": [
                {
                    "type": "error",
                    "message": "Error 1",
                    "file": "test.py",
                    "line": 10,
                    "rule_id": "rule1"
                }
            ]
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "sarif"
        
        # Parse the SARIF content
        content = json.loads(report["content"])
        assert content["version"] == "2.1.0"
        assert len(content["runs"]) == 1
