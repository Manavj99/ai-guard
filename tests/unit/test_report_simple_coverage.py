"""Simple tests for report.py to achieve maximum coverage."""

import pytest
from unittest.mock import patch
from ai_guard.report import GateResult, summarize, ReportGenerator


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_creation(self):
        """Test creating a GateResult instance."""
        result = GateResult(
            name="test_gate", passed=True, details="Test passed", exit_code=0
        )

        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == "Test passed"
        assert result.exit_code == 0

    def test_gate_result_with_defaults(self):
        """Test GateResult with default values."""
        result = GateResult(name="test_gate", passed=False)

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
            GateResult("gate2", True, "Passed"),
            GateResult("gate3", True, "Passed"),
        ]

        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 0
        mock_print.assert_called()

    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", True, "Passed"),
        ]

        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 1
        mock_print.assert_called()

    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        results = [
            GateResult("gate1", False, "Failed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", False, "Failed"),
        ]

        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)

        assert exit_code == 1
        mock_print.assert_called()

    def test_summarize_empty_results(self):
        """Test summarize with empty results."""
        results = []

        with patch("builtins.print") as mock_print:
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
        """Test generate_summary with all gates passed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Passed"),
        ]

        generator = ReportGenerator()
        summary = generator.generate_summary(results)

        assert "Quality Gates Summary:" in summary
        assert "Total: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary

    def test_generate_summary_some_failed(self):
        """Test generate_summary with some gates failed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]

        generator = ReportGenerator()
        summary = generator.generate_summary(results)

        assert "Quality Gates Summary:" in summary
        assert "Total: 2" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary
        assert "Failed Gates:" in summary
        assert "- gate2: Failed" in summary

    def test_generate_detailed_report(self):
        """Test generate_detailed_report."""
        results = [
            GateResult("gate1", True, "Passed", 0),
            GateResult("gate2", False, "Failed", 1),
        ]

        generator = ReportGenerator()
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

    def test_generate_detailed_report_empty_details(self):
        """Test generate_detailed_report with empty details."""
        results = [GateResult("gate1", True, "", 0)]

        generator = ReportGenerator()
        report = generator.generate_detailed_report(results)

        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate: gate1" in report
        assert "Status: PASSED" in report
        assert "Exit Code: 0" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
