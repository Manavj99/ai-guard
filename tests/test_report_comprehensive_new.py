"""Comprehensive tests for report module to achieve high coverage."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open

from src.ai_guard.report import GateResult, summarize, ReportGenerator


class TestGateResult:
    """Test GateResult dataclass."""
    
    def test_gate_result_creation(self):
        """Test creating a GateResult."""
        result = GateResult(
            name="Test Gate",
            passed=True,
            details="Test details",
            exit_code=0
        )
        
        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == "Test details"
        assert result.exit_code == 0
    
    def test_gate_result_minimal(self):
        """Test creating a minimal GateResult."""
        result = GateResult(
            name="Test Gate",
            passed=False,
            details="Test details"
        )
        
        assert result.exit_code == 0  # Default value


class TestSummarize:
    """Test summarize function."""
    
    def test_summarize_all_passed(self):
        """Test summarizing when all gates pass."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", True, "Passed"),
            GateResult("Gate 3", True, "Passed")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 0
            mock_print.assert_called()
    
    def test_summarize_some_failed(self):
        """Test summarizing when some gates fail."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", True, "Passed")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 1
            mock_print.assert_called()
    
    def test_summarize_all_failed(self):
        """Test summarizing when all gates fail."""
        results = [
            GateResult("Gate 1", False, "Failed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", False, "Failed")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 1
            mock_print.assert_called()
    
    def test_summarize_empty(self):
        """Test summarizing empty results."""
        results = []
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 0
            mock_print.assert_called()


class TestReportGenerator:
    """Test ReportGenerator class."""
    
    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        
        assert generator is not None
    
    def test_generate_summary_all_passed(self):
        """Test generating summary when all gates pass."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", True, "Passed")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary
    
    def test_generate_summary_some_failed(self):
        """Test generating summary when some gates fail."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", False, "Also failed")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 3" in summary
        assert "Passed: 1" in summary
        assert "Failed: 2" in summary
        assert "Failed Gates:" in summary
        assert "Gate 2: Failed" in summary
        assert "Gate 3: Also failed" in summary
    
    def test_generate_summary_empty(self):
        """Test generating summary with empty results."""
        generator = ReportGenerator()
        results = []
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 0" in summary
        assert "Passed: 0" in summary
        assert "Failed: 0" in summary
    
    def test_generate_detailed_report(self):
        """Test generating detailed report."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "Passed", 0),
            GateResult("Gate 2", False, "Failed", 1)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate: Gate 1" in report
        assert "Status: PASSED" in report
        assert "Details: Passed" in report
        assert "Exit Code: 0" in report
        assert "Gate: Gate 2" in report
        assert "Status: FAILED" in report
        assert "Details: Failed" in report
        assert "Exit Code: 1" in report
    
    def test_generate_detailed_report_empty(self):
        """Test generating detailed report with empty results."""
        generator = ReportGenerator()
        results = []
        
        report = generator.generate_detailed_report(results)
        
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate:" not in report
    
    def test_generate_detailed_report_no_details(self):
        """Test generating detailed report with no details."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "", 0)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "Gate: Gate 1" in report
        assert "Status: PASSED" in report
        assert "Details:" not in report  # Details only shown if result.details is truthy
        assert "Exit Code: 0" in report
