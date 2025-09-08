"""Comprehensive tests for the report module."""

import pytest
from io import StringIO
from unittest.mock import patch
from src.ai_guard.report import GateResult, summarize, ReportGenerator


class TestGateResult:
    """Test GateResult dataclass."""
    
    def test_gate_result_creation(self):
        """Test creating a GateResult."""
        result = GateResult("test_gate", True, "Test details", 0)
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == "Test details"
        assert result.exit_code == 0
    
    def test_gate_result_defaults(self):
        """Test GateResult with default values."""
        result = GateResult("test_gate", False)
        assert result.name == "test_gate"
        assert result.passed is False
        assert result.details == ""
        assert result.exit_code == 0


class TestSummarize:
    """Test summarize function."""
    
    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed")
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
        
        assert exit_code == 0
        output = mock_stdout.getvalue()
        assert "✅ All gates passed!" in output
        assert "✅ gate1: PASSED" in output
        assert "✅ gate2: PASSED" in output
    
    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", True, "Passed")
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
        
        assert exit_code == 1
        output = mock_stdout.getvalue()
        assert "❌ 1 gate(s) failed" in output
        assert "✅ gate1: PASSED" in output
        assert "❌ gate2: FAILED" in output
        assert "✅ gate3: PASSED" in output
    
    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        results = [
            GateResult("gate1", False, "Failed 1"),
            GateResult("gate2", False, "Failed 2")
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
        
        assert exit_code == 1
        output = mock_stdout.getvalue()
        assert "❌ 2 gate(s) failed" in output
        assert "❌ gate1: FAILED" in output
        assert "❌ gate2: FAILED" in output
    
    def test_summarize_empty_results(self):
        """Test summarize with empty results."""
        results = []
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
        
        assert exit_code == 0
        output = mock_stdout.getvalue()
        assert "✅ All gates passed!" in output
    
    def test_summarize_with_details(self):
        """Test summarize with detailed messages."""
        results = [
            GateResult("gate1", True, "Detailed success message"),
            GateResult("gate2", False, "Detailed failure message")
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
        
        assert exit_code == 1
        output = mock_stdout.getvalue()
        assert "✅ gate1: PASSED - Detailed success message" in output
        assert "❌ gate2: FAILED - Detailed failure message" in output
    
    def test_summarize_without_details(self):
        """Test summarize without detailed messages."""
        results = [
            GateResult("gate1", True),
            GateResult("gate2", False)
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
        
        assert exit_code == 1
        output = mock_stdout.getvalue()
        assert "✅ gate1: PASSED" in output
        assert "❌ gate2: FAILED" in output


class TestReportGenerator:
    """Test ReportGenerator class."""
    
    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None
    
    def test_generate_summary_all_passed(self):
        """Test generate_summary with all gates passed."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary
    
    def test_generate_summary_some_failed(self):
        """Test generate_summary with some gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", True, "Passed")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 3" in summary
        assert "Passed: 2" in summary
        assert "Failed: 1" in summary
        assert "Failed Gates:" in summary
        assert "- gate2: Failed" in summary
    
    def test_generate_summary_all_failed(self):
        """Test generate_summary with all gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", False, "Failed 1"),
            GateResult("gate2", False, "Failed 2")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 2" in summary
        assert "Passed: 0" in summary
        assert "Failed: 2" in summary
        assert "Failed Gates:" in summary
        assert "- gate1: Failed 1" in summary
        assert "- gate2: Failed 2" in summary
    
    def test_generate_summary_empty_results(self):
        """Test generate_summary with empty results."""
        generator = ReportGenerator()
        results = []
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 0" in summary
        assert "Passed: 0" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary
    
    def test_generate_detailed_report(self):
        """Test generate_detailed_report."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Success details", 0),
            GateResult("gate2", False, "Failure details", 1)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" * 50 in report
        assert "Gate: gate1" in report
        assert "Status: PASSED" in report
        assert "Details: Success details" in report
        assert "Exit Code: 0" in report
        assert "Gate: gate2" in report
        assert "Status: FAILED" in report
        assert "Details: Failure details" in report
        assert "Exit Code: 1" in report
        assert "-" * 30 in report
    
    def test_generate_detailed_report_without_details(self):
        """Test generate_detailed_report without details."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "", 0),
            GateResult("gate2", False, "", 1)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "Gate: gate1" in report
        assert "Status: PASSED" in report
        assert "Exit Code: 0" in report
        assert "Gate: gate2" in report
        assert "Status: FAILED" in report
        assert "Exit Code: 1" in report
        # Should not include "Details:" line when details is empty
        lines = report.split('\n')
        detail_lines = [line for line in lines if line.startswith("Details:")]
        assert len(detail_lines) == 0
    
    def test_generate_detailed_report_empty_results(self):
        """Test generate_detailed_report with empty results."""
        generator = ReportGenerator()
        results = []
        
        report = generator.generate_detailed_report(results)
        
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" * 50 in report
        # Should only have header, no gate details
        lines = report.split('\n')
        gate_lines = [line for line in lines if line.startswith("Gate:")]
        assert len(gate_lines) == 0