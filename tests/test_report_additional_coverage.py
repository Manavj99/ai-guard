"""Additional tests for report modules to increase coverage."""

import pytest
import tempfile
import json
from unittest.mock import patch, mock_open
from ai_guard.report import (
    GateResult,
    summarize,
    ReportGenerator
)


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_minimal(self):
        """Test creating GateResult with minimal data."""
        result = GateResult(
            name="Test Gate",
            passed=True
        )
        
        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == ""
        assert result.exit_code == 0

    def test_gate_result_full(self):
        """Test creating GateResult with all data."""
        result = GateResult(
            name="Test Gate",
            passed=False,
            details="Gate failed due to low coverage",
            exit_code=1
        )
        
        assert result.name == "Test Gate"
        assert result.passed is False
        assert result.details == "Gate failed due to low coverage"
        assert result.exit_code == 1

    def test_gate_result_passed_true(self):
        """Test GateResult with passed=True."""
        result = GateResult(name="Passed Gate", passed=True)
        assert result.passed is True

    def test_gate_result_passed_false(self):
        """Test GateResult with passed=False."""
        result = GateResult(name="Failed Gate", passed=False)
        assert result.passed is False

    def test_gate_result_empty_name(self):
        """Test GateResult with empty name."""
        result = GateResult(name="", passed=True)
        assert result.name == ""

    def test_gate_result_none_details(self):
        """Test GateResult with None details."""
        result = GateResult(name="Test Gate", passed=True, details=None)
        assert result.details is None


class TestSummarize:
    """Test summarize function."""

    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        results = [
            GateResult("Gate 1", True, "All good"),
            GateResult("Gate 2", True, "Perfect"),
            GateResult("Gate 3", True, "Excellent")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 0
        assert mock_print.call_count >= 4  # Header + 3 gates + summary

    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        results = [
            GateResult("Gate 1", True, "All good"),
            GateResult("Gate 2", False, "Failed check"),
            GateResult("Gate 3", True, "Perfect")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1
        assert mock_print.call_count >= 4  # Header + 3 gates + summary

    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        results = [
            GateResult("Gate 1", False, "Failed check 1"),
            GateResult("Gate 2", False, "Failed check 2"),
            GateResult("Gate 3", False, "Failed check 3")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1
        assert mock_print.call_count >= 4  # Header + 3 gates + summary

    def test_summarize_empty_list(self):
        """Test summarize with empty results list."""
        results = []
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 0
        assert mock_print.call_count >= 2  # Header + summary

    def test_summarize_single_result(self):
        """Test summarize with single result."""
        results = [
            GateResult("Single Gate", True, "Only one gate")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 0
        assert mock_print.call_count >= 2  # Header + gate + summary

    def test_summarize_with_details(self):
        """Test summarize with detailed results."""
        results = [
            GateResult("Gate 1", True, "Coverage: 85%"),
            GateResult("Gate 2", False, "Coverage: 65% (threshold: 80%)"),
            GateResult("Gate 3", True, "No issues found")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1
        
        # Check that details were printed
        printed_text = ' '.join([str(call) for call in mock_print.call_args_list])
        assert "Coverage: 85%" in printed_text
        assert "Coverage: 65%" in printed_text
        assert "No issues found" in printed_text

    def test_summarize_without_details(self):
        """Test summarize with results without details."""
        results = [
            GateResult("Gate 1", True),
            GateResult("Gate 2", False),
            GateResult("Gate 3", True)
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1

    def test_summarize_mixed_details(self):
        """Test summarize with mixed details (some with, some without)."""
        results = [
            GateResult("Gate 1", True, "Has details"),
            GateResult("Gate 2", False),
            GateResult("Gate 3", True, "Also has details")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1

    def test_summarize_exit_codes(self):
        """Test summarize with different exit codes."""
        results = [
            GateResult("Gate 1", True, exit_code=0),
            GateResult("Gate 2", False, exit_code=1),
            GateResult("Gate 3", False, exit_code=2)
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_generate_summary_all_passed(self):
        """Test generating summary with all gates passed."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "All good"),
            GateResult("Gate 2", True, "Perfect"),
            GateResult("Gate 3", True, "Excellent")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 3" in summary
        assert "Passed: 3" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary

    def test_generate_summary_some_failed(self):
        """Test generating summary with some gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "All good"),
            GateResult("Gate 2", False, "Failed check"),
            GateResult("Gate 3", False, "Another failure")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Quality Gates Summary:" in summary
        assert "Total: 3" in summary
        assert "Passed: 1" in summary
        assert "Failed: 2" in summary
        assert "Failed Gates:" in summary
        assert "Gate 2: Failed check" in summary
        assert "Gate 3: Another failure" in summary

    def test_generate_summary_all_failed(self):
        """Test generating summary with all gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", False, "Failed check 1"),
            GateResult("Gate 2", False, "Failed check 2")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Total: 2" in summary
        assert "Passed: 0" in summary
        assert "Failed: 2" in summary
        assert "Failed Gates:" in summary
        assert "Gate 1: Failed check 1" in summary
        assert "Gate 2: Failed check 2" in summary

    def test_generate_summary_empty_results(self):
        """Test generating summary with empty results."""
        generator = ReportGenerator()
        results = []
        
        summary = generator.generate_summary(results)
        
        assert "Total: 0" in summary
        assert "Passed: 0" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary

    def test_generate_summary_single_result(self):
        """Test generating summary with single result."""
        generator = ReportGenerator()
        results = [
            GateResult("Single Gate", True, "Only one gate")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Total: 1" in summary
        assert "Passed: 1" in summary
        assert "Failed: 0" in summary

    def test_generate_summary_without_details(self):
        """Test generating summary with results without details."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True),
            GateResult("Gate 2", False)
        ]
        
        summary = generator.generate_summary(results)
        
        assert "Total: 2" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary
        assert "Failed Gates:" in summary
        assert "Gate 2: " in summary  # Empty details

    def test_generate_detailed_report_all_passed(self):
        """Test generating detailed report with all gates passed."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "All good", 0),
            GateResult("Gate 2", True, "Perfect", 0)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" in report
        assert "Gate: Gate 1" in report
        assert "Status: PASSED" in report
        assert "Details: All good" in report
        assert "Exit Code: 0" in report
        assert "Gate: Gate 2" in report
        assert "Status: PASSED" in report
        assert "Details: Perfect" in report

    def test_generate_detailed_report_some_failed(self):
        """Test generating detailed report with some gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "All good", 0),
            GateResult("Gate 2", False, "Failed check", 1)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "Gate: Gate 1" in report
        assert "Status: PASSED" in report
        assert "Gate: Gate 2" in report
        assert "Status: FAILED" in report
        assert "Details: Failed check" in report
        assert "Exit Code: 1" in report

    def test_generate_detailed_report_empty_results(self):
        """Test generating detailed report with empty results."""
        generator = ReportGenerator()
        results = []
        
        report = generator.generate_detailed_report(results)
        
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" in report
        # Should not contain any gate information

    def test_generate_detailed_report_without_details(self):
        """Test generating detailed report with results without details."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "", 0),
            GateResult("Gate 2", False, "", 1)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "Gate: Gate 1" in report
        assert "Gate: Gate 2" in report
        # Details should be empty but still present

    def test_generate_detailed_report_with_different_exit_codes(self):
        """Test generating detailed report with different exit codes."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "Success", 0),
            GateResult("Gate 2", False, "Warning", 1),
            GateResult("Gate 3", False, "Error", 2)
        ]
        
        report = generator.generate_detailed_report(results)
        
        assert "Exit Code: 0" in report
        assert "Exit Code: 1" in report
        assert "Exit Code: 2" in report

    def test_generate_detailed_report_separators(self):
        """Test that detailed report has proper separators."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "Details 1", 0),
            GateResult("Gate 2", False, "Details 2", 1)
        ]
        
        report = generator.generate_detailed_report(results)
        
        # Should have separators between gates
        separator_count = report.count("-" * 30)
        assert separator_count == 2  # One after each gate


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_gate_result_with_special_characters(self):
        """Test GateResult with special characters in name and details."""
        result = GateResult(
            name="Gate with special chars: @#$%",
            passed=True,
            details="Details with unicode: 中文 🎉"
        )
        
        assert result.name == "Gate with special chars: @#$%"
        assert result.details == "Details with unicode: 中文 🎉"

    def test_gate_result_with_long_strings(self):
        """Test GateResult with long strings."""
        long_name = "A" * 1000
        long_details = "B" * 2000
        
        result = GateResult(
            name=long_name,
            passed=False,
            details=long_details
        )
        
        assert len(result.name) == 1000
        assert len(result.details) == 2000

    def test_summarize_with_many_results(self):
        """Test summarize with many results."""
        results = []
        for i in range(100):
            results.append(GateResult(f"Gate {i}", i % 2 == 0, f"Details {i}"))
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1  # Half should fail
        assert mock_print.call_count >= 102  # Header + 100 gates + summary

    def test_report_generator_with_many_results(self):
        """Test ReportGenerator with many results."""
        generator = ReportGenerator()
        results = []
        for i in range(50):
            results.append(GateResult(f"Gate {i}", i % 2 == 0, f"Details {i}"))
        
        summary = generator.generate_summary(results)
        
        assert "Total: 50" in summary
        assert "Passed: 25" in summary
        assert "Failed: 25" in summary

    def test_report_generator_detailed_report_with_many_results(self):
        """Test detailed report generation with many results."""
        generator = ReportGenerator()
        results = []
        for i in range(20):
            results.append(GateResult(f"Gate {i}", i % 2 == 0, f"Details {i}", i % 3))
        
        report = generator.generate_detailed_report(results)
        
        assert "Gate: Gate 0" in report
        assert "Gate: Gate 19" in report
        assert len(report) > 1000  # Should be a substantial report

    def test_summarize_unicode_output(self):
        """Test summarize with unicode characters."""
        results = [
            GateResult("测试门", True, "所有都好"),
            GateResult("🚀 Gate", False, "失败检查 ❌")
        ]
        
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
        
        assert exit_code == 1
        assert mock_print.call_count >= 4

    def test_report_generator_unicode_summary(self):
        """Test ReportGenerator with unicode characters."""
        generator = ReportGenerator()
        results = [
            GateResult("测试门", True, "所有都好"),
            GateResult("🚀 Gate", False, "失败检查 ❌")
        ]
        
        summary = generator.generate_summary(results)
        
        assert "测试门" in summary
        assert "🚀 Gate" in summary
        assert "所有都好" in summary
        assert "失败检查 ❌" in summary

    def test_gate_result_boolean_edge_cases(self):
        """Test GateResult with boolean edge cases."""
        # Test with explicit True/False
        result1 = GateResult("Test 1", True)
        result2 = GateResult("Test 2", False)
        
        assert result1.passed is True
        assert result2.passed is False
        
        # Test with truthy/falsy values
        result3 = GateResult("Test 3", 1)  # Truthy
        result4 = GateResult("Test 4", 0)  # Falsy
        
        assert result3.passed == 1
        assert result4.passed == 0

    def test_summarize_none_results(self):
        """Test summarize with None results."""
        results = None
        
        with pytest.raises(TypeError):
            summarize(results)

    def test_report_generator_none_results(self):
        """Test ReportGenerator with None results."""
        generator = ReportGenerator()
        
        with pytest.raises(TypeError):
            generator.generate_summary(None)
        
        with pytest.raises(TypeError):
            generator.generate_detailed_report(None)
