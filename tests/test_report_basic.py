"""Comprehensive tests for report modules."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, mock_open
from src.ai_guard.report import (
    GateResult,
    summarize,
    format_report_summary,
    ReportGenerator,
    generate_report,
    save_report_to_file,
    load_report_from_file,
    ReportFormatter
)
from src.ai_guard.report_json import (
    write_json,
    generate_json_report,
    format_json_summary,
    JSONReportGenerator
)
from src.ai_guard.report_html import (
    write_html,
    HTMLReportGenerator,
    generate_html_report,
    format_html_summary,
    create_html_table
)
from src.ai_guard.sarif_report import (
    SarifRun,
    SarifResult,
    write_sarif,
    make_location,
    create_sarif_report,
    parse_issue_to_sarif,
    generate_sarif_report,
    create_sarif_run,
    create_sarif_result,
    SARIFReportGenerator
)


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_init(self):
        """Test GateResult initialization."""
        result = GateResult(
            name="test_gate",
            passed=True,
            details="Test passed"
        )
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == "Test passed"


class TestSummarize:
    """Test summarize function."""

    def test_summarize_all_passed(self):
        """Test summarization when all gates pass."""
        results = [
            GateResult(name="lint", passed=True, details="No linting issues"),
            GateResult(name="type", passed=True, details="No type issues"),
            GateResult(name="security", passed=True, details="No security issues"),
            GateResult(name="coverage", passed=True, details="Coverage: 85.0%")
        ]
        
        exit_code = summarize(results)
        assert exit_code == 0

    def test_summarize_with_issues(self):
        """Test summarization with issues."""
        results = [
            GateResult(name="lint", passed=False, details="Line too long in test.py:1"),
            GateResult(name="type", passed=True, details="No type issues"),
            GateResult(name="security", passed=True, details="No security issues"),
            GateResult(name="coverage", passed=False, details="Coverage: 75.0% (below threshold)")
        ]
        
        exit_code = summarize(results)
        assert exit_code == 1


class TestFormatSummary:
    """Test format_summary function."""

    def test_format_summary_passed(self):
        """Test formatting summary for passed gates."""
        report_data = {
            "files_analyzed": 10,
            "total_issues": 0,
            "issues_by_type": {"error": 0, "warning": 0}
        }
        
        formatted = format_report_summary(report_data)
        assert "10 files analyzed" in formatted
        assert "0 total issues" in formatted


class TestWriteJson:
    """Test write_json function."""

    def test_write_json(self):
        """Test writing JSON report."""
        gates = [
            GateResult(name="lint", passed=True, details="No issues"),
            GateResult(name="coverage", passed=True, details="Coverage: 85.0%")
        ]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "line too long", "path": "test.py", "line": 1}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.close()
            
            try:
                write_json(f.name, gates, findings)
                
                # Verify file was created and contains valid JSON
                assert os.path.exists(f.name)
                with open(f.name, 'r') as json_file:
                    data = json.load(json_file)
                    assert data["summary"]["passed"] is True
                    assert len(data["findings"]) == 1
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)


class TestWriteHtml:
    """Test write_html function."""

    def test_write_html(self):
        """Test writing HTML report."""
        gates = [
            GateResult(name="lint", passed=True, details="No issues"),
            GateResult(name="coverage", passed=True, details="Coverage: 85.0%")
        ]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "line too long", "path": "test.py", "line": 1}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.close()
            
            try:
                write_html(f.name, gates, findings)
                
                # Verify file was created and contains HTML
                assert os.path.exists(f.name)
                with open(f.name, 'r') as html_file:
                    content = html_file.read()
                    assert "<html>" in content
                    assert "85.0%" in content
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)


class TestSarifRun:
    """Test SarifRun dataclass."""

    def test_sarif_run_init(self):
        """Test SarifRun initialization."""
        run = SarifRun(
            tool_name="ai-guard",
            tool_version="1.0.0",
            results=[]
        )
        assert run.tool_name == "ai-guard"
        assert run.tool_version == "1.0.0"
        assert run.results == []


class TestSarifResult:
    """Test SarifResult dataclass."""

    def test_sarif_result_init(self):
        """Test SarifResult initialization."""
        result = SarifResult(
            rule_id="E501",
            level="error",
            message="line too long",
            locations=[{"file": "test.py", "line": 1}]
        )
        assert result.rule_id == "E501"
        assert result.level == "error"
        assert result.message == "line too long"
        assert len(result.locations) == 1


class TestWriteSarif:
    """Test write_sarif function."""

    def test_write_sarif(self):
        """Test writing SARIF report."""
        run = SarifRun(
            tool_name="ai-guard",
            tool_version="1.0.0",
            results=[]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            f.close()
            
            try:
                write_sarif(f.name, run)
                
                # Verify file was created and contains SARIF structure
                assert os.path.exists(f.name)
                with open(f.name, 'r') as sarif_file:
                    data = json.load(sarif_file)
                    assert "runs" in data
                    assert len(data["runs"]) == 1
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)


class TestMakeLocation:
    """Test make_location function."""

    def test_make_location(self):
        """Test making SARIF location."""
        location = make_location("test.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_make_location_no_line(self):
        """Test making SARIF location without line."""
        location = make_location("test.py")
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert "region" not in location["physicalLocation"]

    def test_make_location_no_column(self):
        """Test making SARIF location without column."""
        location = make_location("test.py", 10)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert "startColumn" not in location["physicalLocation"]["region"]

    def test_make_location_windows_path(self):
        """Test making SARIF location with Windows path."""
        location = make_location("C:\\test\\file.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "C:/test/file.py"


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_report_generator_with_format(self):
        """Test ReportGenerator with different formats."""
        generator = ReportGenerator("json", include_timestamp=True)
        assert generator.report_format == "json"
        assert generator.include_timestamp is True

    def test_generate_report_json(self):
        """Test JSON report generation."""
        generator = ReportGenerator("json")
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 1,
            "issues_by_type": {"error": 1}
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "json"
        assert "content" in report
        assert report["files_analyzed"] == 3

    def test_generate_report_html(self):
        """Test HTML report generation."""
        generator = ReportGenerator("html")
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 1,
            "issues_by_type": {"error": 1}
        }
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "html"
        assert "content" in report
        assert "<html>" in report["content"]

    def test_generate_unsupported_format(self):
        """Test unsupported format handling."""
        generator = ReportGenerator("xml")
        analysis_results = {"files_analyzed": 3}
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is False
        assert "Unsupported format: xml" in report["error"]


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report(self):
        """Test generate_report function."""
        analysis_results = {
            "files_analyzed": 5,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1}
        }
        
        report = generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["files_analyzed"] == 5
        assert report["total_issues"] == 2
        assert report["issues_by_type"] == {"error": 1, "warning": 1}
        assert "summary" in report

    def test_generate_report_empty(self):
        """Test generate_report with empty results."""
        analysis_results = {}
        
        report = generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["files_analyzed"] == 0
        assert report["total_issues"] == 0
        assert report["issues_by_type"] == {}


class TestSaveLoadReport:
    """Test save_report_to_file and load_report_from_file functions."""

    def test_save_report_to_file(self):
        """Test saving report to file."""
        report_data = {"test": "data", "files_analyzed": 5}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.close()
            
            try:
                result = save_report_to_file(report_data, f.name)
                assert result["success"] is True
                
                with open(f.name, 'r') as json_file:
                    loaded_data = json.load(json_file)
                    assert loaded_data == report_data
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_save_report_to_file_error(self):
        """Test saving report to file with error."""
        report_data = {"test": "data"}
        
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = save_report_to_file(report_data, "/invalid/path")
            assert result["success"] is False
            assert "error" in result

    def test_load_report_from_file(self):
        """Test loading report from file."""
        report_data = {"test": "data", "files_analyzed": 5}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f)
            f.close()
            
            try:
                result = load_report_from_file(f.name)
                assert result["success"] is True
                assert result["data"] == report_data
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_load_report_from_file_not_found(self):
        """Test loading report from non-existent file."""
        result = load_report_from_file("/nonexistent/file.json")
        assert result["success"] is False
        assert result["error"] == "File not found"

    def test_load_report_from_file_invalid_json(self):
        """Test loading report from file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            f.close()
            
            try:
                result = load_report_from_file(f.name)
                assert result["success"] is False
                assert "Invalid JSON format" in result["error"]
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)




class TestReportFormatter:
    """Test ReportFormatter class."""

    def test_report_formatter_init(self):
        """Test ReportFormatter initialization."""
        formatter = ReportFormatter()
        assert formatter.template_dir is None
        assert formatter.custom_styles is None

    def test_report_formatter_init_with_params(self):
        """Test ReportFormatter initialization with parameters."""
        formatter = ReportFormatter("/templates", {"color": "blue"})
        assert formatter.template_dir == "/templates"
        assert formatter.custom_styles == {"color": "blue"}

    def test_format_summary(self):
        """Test format_summary method."""
        formatter = ReportFormatter()
        report_data = {
            "files_analyzed": 5,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1}
        }
        
        summary = formatter.format_summary(report_data)
        assert "5 files analyzed" in summary
        assert "2 total issues" in summary

    def test_format_issues_list(self):
        """Test format_issues_list method."""
        formatter = ReportFormatter()
        issues = [
            {"type": "error", "message": "Syntax error", "file": "test.py"},
            {"type": "warning", "message": "Unused variable", "file": "test2.py"}
        ]
        
        formatted = formatter.format_issues_list(issues)
        assert "ERROR: Syntax error (test.py)" in formatted
        assert "WARNING: Unused variable (test2.py)" in formatted

    def test_format_issues_list_empty(self):
        """Test format_issues_list with empty list."""
        formatter = ReportFormatter()
        formatted = formatter.format_issues_list([])
        assert formatted == "No issues found."


class TestJSONReportGenerator:
    """Test JSONReportGenerator class."""

    def test_json_report_generator_init(self):
        """Test JSONReportGenerator initialization."""
        generator = JSONReportGenerator()
        assert generator is not None

    def test_generate_json_report(self):
        """Test generate_json_report function."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 1,
            "issues_by_type": {"error": 1},
            "issues": [{"type": "error", "message": "Test error"}]
        }
        
        report = generate_json_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "json"
        assert report["files_analyzed"] == 3
        assert report["total_issues"] == 1
        assert "content" in report

    def test_format_json_summary(self):
        """Test format_json_summary function."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1}
        }
        
        summary = format_json_summary(report_data)
        summary_data = json.loads(summary)
        
        assert summary_data["files_analyzed"] == 5
        assert summary_data["total_issues"] == 2
        assert summary_data["issues_by_type"] == {"error": 1, "warning": 1}

    def test_json_report_generator_generate_report(self):
        """Test JSONReportGenerator.generate_report method."""
        generator = JSONReportGenerator()
        analysis_results = {"files_analyzed": 3}
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "json"


class TestHTMLReportGenerator:
    """Test HTMLReportGenerator class."""

    def test_html_report_generator_init(self):
        """Test HTMLReportGenerator initialization."""
        generator = HTMLReportGenerator()
        assert generator is not None

    def test_generate_html_report(self):
        """Test generate_html_report function."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 1,
            "issues": [{"type": "error", "message": "Test error", "file": "test.py", "line": 1}]
        }
        
        report = generate_html_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "html"
        assert report["files_analyzed"] == 3
        assert report["total_issues"] == 1
        assert "<html>" in report["content"]

    def test_format_html_summary(self):
        """Test format_html_summary function."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1}
        }
        
        summary = format_html_summary(report_data)
        
        assert "<div class=\"summary\">" in summary
        assert "Files analyzed: 5" in summary
        assert "Total issues: 2" in summary
        assert "Errors: 1" in summary
        assert "Warnings: 1" in summary

    def test_create_html_table(self):
        """Test create_html_table function."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        columns = ["name", "age"]
        
        table = create_html_table(data, columns)
        
        assert "<table>" in table
        assert "<th>Name</th>" in table
        assert "<th>Age</th>" in table
        assert "<td>John</td>" in table
        assert "<td>30</td>" in table

    def test_html_report_generator_generate_report(self):
        """Test HTMLReportGenerator.generate_report method."""
        generator = HTMLReportGenerator()
        analysis_results = {"files_analyzed": 3}
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "html"


class TestSARIFReportGenerator:
    """Test SARIFReportGenerator class."""

    def test_sarif_report_generator_init(self):
        """Test SARIFReportGenerator initialization."""
        generator = SARIFReportGenerator()
        assert generator is not None

    def test_create_sarif_report(self):
        """Test create_sarif_report function."""
        runs = [
            SarifRun(
                tool_name="test-tool",
                tool_version="1.0.0",
                results=[
                    SarifResult(
                        rule_id="TEST001",
                        level="error",
                        message="Test error",
                        locations=[{"file": "test.py", "line": 1}]
                    )
                ]
            )
        ]
        
        report = create_sarif_report(runs)
        
        assert report["version"] == "2.1.0"
        assert "$schema" in report
        assert len(report["runs"]) == 1
        assert report["runs"][0]["tool"]["driver"]["name"] == "test-tool"

    def test_create_sarif_report_with_metadata(self):
        """Test create_sarif_report with metadata."""
        runs = [SarifRun(tool_name="test", results=[])]
        metadata = {"author": "test", "version": "1.0"}
        
        report = create_sarif_report(runs, metadata)
        
        assert report["metadata"] == metadata

    def test_parse_issue_to_sarif(self):
        """Test parse_issue_to_sarif function."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 10,
            "column": 5
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "TEST001"
        assert result.level == "error"
        assert result.message == "Test error"
        assert result.locations is not None
        assert len(result.locations) == 1

    def test_parse_issue_to_sarif_no_location(self):
        """Test parse_issue_to_sarif without location info."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error"
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "TEST001"
        assert result.level == "error"
        assert result.message == "Test error"
        assert result.locations is None

    def test_generate_sarif_report(self):
        """Test generate_sarif_report function."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 1,
            "issues": [{
                "rule_id": "TEST001",
                "type": "error",
                "message": "Test error",
                "file": "test.py",
                "line": 1
            }]
        }
        
        report = generate_sarif_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "sarif"
        assert report["files_analyzed"] == 3
        assert report["total_issues"] == 1
        assert "content" in report

    def test_create_sarif_run(self):
        """Test create_sarif_run function."""
        analysis_results = {
            "issues": [{
                "rule_id": "TEST001",
                "type": "error",
                "message": "Test error",
                "file": "test.py",
                "line": 1
            }]
        }
        
        run = create_sarif_run(analysis_results)
        
        assert "tool" in run
        assert run["tool"]["driver"]["name"] == "AI-Guard"
        assert len(run["results"]) == 1
        assert run["results"][0]["ruleId"] == "TEST001"

    def test_create_sarif_result(self):
        """Test create_sarif_result function."""
        issue = {
            "rule_id": "TEST001",
            "type": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 1,
            "column": 5
        }
        
        result = create_sarif_result(issue)
        
        assert result["ruleId"] == "TEST001"
        assert result["level"] == "error"
        assert result["message"]["text"] == "Test error"
        assert len(result["locations"]) == 1

    def test_sarif_report_generator_generate_report(self):
        """Test SARIFReportGenerator.generate_report method."""
        generator = SARIFReportGenerator()
        analysis_results = {"files_analyzed": 3}
        
        report = generator.generate_report(analysis_results)
        
        assert report["success"] is True
        assert report["format"] == "sarif"


class TestAdditionalCoverage:
    """Test additional functionality for better coverage."""

    def test_gate_result_with_exit_code(self):
        """Test GateResult with exit code."""
        result = GateResult(
            name="test_gate",
            passed=False,
            details="Test failed",
            exit_code=1
        )
        assert result.exit_code == 1

    def test_summarize_with_exit_codes(self):
        """Test summarize with different exit codes."""
        results = [
            GateResult(name="gate1", passed=True, exit_code=0),
            GateResult(name="gate2", passed=False, exit_code=1)
        ]
        
        exit_code = summarize(results)
        assert exit_code == 1

    def test_format_report_summary_empty_data(self):
        """Test format_report_summary with empty data."""
        report_data = {}
        summary = format_report_summary(report_data)
        assert "0 files analyzed" in summary
        assert "0 total issues" in summary

    def test_write_json_with_empty_findings(self):
        """Test write_json with empty findings."""
        gates = [GateResult(name="lint", passed=True, details="No issues")]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.close()
            
            try:
                write_json(f.name, gates, findings)
                
                with open(f.name, 'r') as json_file:
                    data = json.load(json_file)
                    assert data["summary"]["passed"] is True
                    assert len(data["findings"]) == 0
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_write_html_with_empty_findings(self):
        """Test write_html with empty findings."""
        gates = [GateResult(name="lint", passed=True, details="No issues")]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.close()
            
            try:
                write_html(f.name, gates, findings)
                
                with open(f.name, 'r') as html_file:
                    content = html_file.read()
                    assert "<html>" in content
                    assert "No findings" in content
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_write_html_with_none_details(self):
        """Test write_html with None details."""
        gates = [GateResult(name="lint", passed=True, details=None)]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.close()
            
            try:
                write_html(f.name, gates, findings)
                
                with open(f.name, 'r') as html_file:
                    content = html_file.read()
                    assert "<html>" in content
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_sarif_result_with_locations(self):
        """Test SarifResult with locations."""
        locations = [{"file": "test.py", "line": 1}]
        result = SarifResult(
            rule_id="TEST001",
            level="error",
            message="Test error",
            locations=locations
        )
        assert result.locations == locations

    def test_write_sarif_with_empty_results(self):
        """Test write_sarif with empty results."""
        run = SarifRun(tool_name="test-tool", results=[])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            f.close()
            
            try:
                write_sarif(f.name, run)
                
                with open(f.name, 'r') as sarif_file:
                    data = json.load(sarif_file)
                    assert "runs" in data
                    assert len(data["runs"]) == 1
                    assert len(data["runs"][0]["results"]) == 0
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)


    def test_sarif_with_locations_condition(self):
        """Test SARIF with locations condition."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 10
        }
        
        result = parse_issue_to_sarif(issue)
        assert result.locations is not None
        assert len(result.locations) == 1

    def test_sarif_without_locations_condition(self):
        """Test SARIF without locations condition."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error"
        }
        
        result = parse_issue_to_sarif(issue)
        assert result.locations is None

    def test_sarif_with_column_condition(self):
        """Test SARIF with column condition."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 10,
            "column": 5
        }
        
        result = parse_issue_to_sarif(issue)
        assert result.locations is not None
        assert len(result.locations) == 1

    def test_sarif_create_result_with_column(self):
        """Test create_sarif_result with column."""
        issue = {
            "rule_id": "TEST001",
            "type": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 1,
            "column": 5
        }
        
        result = create_sarif_result(issue)
        assert result["ruleId"] == "TEST001"
        assert result["level"] == "error"
        assert result["message"]["text"] == "Test error"
        assert len(result["locations"]) == 1

    def test_sarif_create_result_without_column(self):
        """Test create_sarif_result without column."""
        issue = {
            "rule_id": "TEST001",
            "type": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 1
        }
        
        result = create_sarif_result(issue)
        assert result["ruleId"] == "TEST001"
        assert result["level"] == "error"
        assert result["message"]["text"] == "Test error"
        assert len(result["locations"]) == 1
