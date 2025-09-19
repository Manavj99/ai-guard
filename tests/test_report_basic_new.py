"""Basic tests for report module using actual functions."""

import pytest
import tempfile
import os
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


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_init(self):
        """Test GateResult initialization."""
        result = GateResult(
            name="test_gate",
            passed=True,
            message="Test passed",
            details={"coverage": 85.0}
        )
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.message == "Test passed"
        assert result.details == {"coverage": 85.0}

    def test_gate_result_minimal(self):
        """Test GateResult with minimal parameters."""
        result = GateResult(name="test_gate", passed=True)
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.message is None
        assert result.details is None


class TestSummarize:
    """Test summarize function."""

    def test_summarize_all_passed(self):
        """Test summarization when all gates pass."""
        results = [
            GateResult("lint", True, "No lint issues"),
            GateResult("type", True, "No type issues"),
            GateResult("security", True, "No security issues"),
            GateResult("coverage", True, "Coverage: 85%", {"coverage": 85.0})
        ]
        
        summary = summarize(results)
        assert summary == 0  # 0 means all passed

    def test_summarize_with_failures(self):
        """Test summarization with failures."""
        results = [
            GateResult("lint", False, "Lint issues found"),
            GateResult("type", True, "No type issues"),
            GateResult("security", False, "Security issues found"),
            GateResult("coverage", True, "Coverage: 85%", {"coverage": 85.0})
        ]
        
        summary = summarize(results)
        assert summary == 2  # 2 failures

    def test_summarize_empty_results(self):
        """Test summarization with empty results."""
        results = []
        summary = summarize(results)
        assert summary == 0


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_generate_report(self):
        """Test generating report."""
        generator = ReportGenerator()
        
        analysis_results = {
            "lint": [],
            "type": [],
            "security": [],
            "coverage": {"passed": True, "coverage": 85.0}
        }
        
        report = generator.generate_report(analysis_results)
        assert isinstance(report, dict)
        assert "summary" in report
        assert "results" in report


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report(self):
        """Test generating report."""
        analysis_results = {
            "lint": [],
            "type": [],
            "security": [],
            "coverage": {"passed": True, "coverage": 85.0}
        }
        
        report = generate_report(analysis_results)
        assert isinstance(report, dict)
        assert "summary" in report
        assert "results" in report


class TestFormatReportSummary:
    """Test format_report_summary function."""

    def test_format_report_summary(self):
        """Test formatting report summary."""
        report_data = {
            "summary": {
                "passed": True,
                "total_issues": 0,
                "coverage": 85.0
            }
        }
        
        formatted = format_report_summary(report_data)
        assert isinstance(formatted, str)
        assert "PASSED" in formatted or "FAILED" in formatted


class TestSaveReportToFile:
    """Test save_report_to_file function."""

    def test_save_report_to_file(self):
        """Test saving report to file."""
        report_data = {
            "summary": {"passed": True, "total_issues": 0},
            "results": {"coverage": {"passed": True, "coverage": 85.0}}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.close()
            
            try:
                result = save_report_to_file(report_data, f.name)
                assert result["success"] is True
                assert os.path.exists(f.name)
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)


class TestLoadReportFromFile:
    """Test load_report_from_file function."""

    def test_load_report_from_file(self):
        """Test loading report from file."""
        report_data = {
            "summary": {"passed": True, "total_issues": 0},
            "results": {"coverage": {"passed": True, "coverage": 85.0}}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(report_data, f)
            f.flush()
            
            try:
                loaded = load_report_from_file(f.name)
                assert loaded["success"] is True
                assert loaded["data"]["summary"]["passed"] is True
            finally:
                os.unlink(f.name)

    def test_load_report_from_nonexistent_file(self):
        """Test loading report from nonexistent file."""
        result = load_report_from_file("nonexistent.json")
        assert result["success"] is False
        assert "error" in result


class TestReportFormatter:
    """Test ReportFormatter class."""

    def test_report_formatter_init(self):
        """Test ReportFormatter initialization."""
        formatter = ReportFormatter()
        assert formatter is not None

    def test_format_report(self):
        """Test formatting report."""
        formatter = ReportFormatter()
        
        report_data = {
            "summary": {"passed": True, "total_issues": 0},
            "results": {"coverage": {"passed": True, "coverage": 85.0}}
        }
        
        formatted = formatter.format_report(report_data)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
