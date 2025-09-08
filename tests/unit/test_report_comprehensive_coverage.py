"""Comprehensive tests for report.py to achieve maximum coverage."""

import pytest
from unittest.mock import patch
from io import StringIO

from ai_guard.report import GateResult, summarize, ReportGenerator


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_basic(self):
        """Test basic GateResult creation."""
        result = GateResult("Test Gate", True)

        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == ""
        assert result.exit_code == 0

    def test_gate_result_with_details(self):
        """Test GateResult with details."""
        result = GateResult("Test Gate", False, "Test failed", 1)

        assert result.name == "Test Gate"
        assert result.passed is False
        assert result.details == "Test failed"
        assert result.exit_code == 1

    def test_gate_result_with_custom_exit_code(self):
        """Test GateResult with custom exit code."""
        result = GateResult("Test Gate", True, "Test passed", 2)

        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == "Test passed"
        assert result.exit_code == 2

    def test_gate_result_failed_with_details(self):
        """Test failed GateResult with details."""
        result = GateResult("Lint Check", False, "Found 5 linting errors", 1)

        assert result.name == "Lint Check"
        assert result.passed is False
        assert result.details == "Found 5 linting errors"
        assert result.exit_code == 1

    def test_gate_result_passed_with_details(self):
        """Test passed GateResult with details."""
        result = GateResult("Coverage Check", True, "Coverage: 85%", 0)

        assert result.name == "Coverage Check"
        assert result.passed is True
        assert result.details == "Coverage: 85%"
        assert result.exit_code == 0


class TestSummarizeFunction:
    """Test summarize function."""

    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        results = [
            GateResult("Lint", True, "No issues found"),
            GateResult("Type Check", True, "All types correct"),
            GateResult("Security", True, "No security issues"),
            GateResult("Coverage", True, "Coverage: 85%"),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 0
            assert "AI-Guard Quality Gates Summary" in output
            assert "✅ All gates passed!" in output
            assert "✅ Lint: PASSED - No issues found" in output
            assert "✅ Type Check: PASSED - All types correct" in output
            assert "✅ Security: PASSED - No security issues" in output
            assert "✅ Coverage: PASSED - Coverage: 85%" in output

    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        results = [
            GateResult("Lint", True, "No issues found"),
            GateResult("Type Check", False, "Found 3 type errors"),
            GateResult("Security", True, "No security issues"),
            GateResult("Coverage", False, "Coverage: 75% < 80%"),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 1
            assert "AI-Guard Quality Gates Summary" in output
            assert "❌ 2 gate(s) failed" in output
            assert "✅ Lint: PASSED - No issues found" in output
            assert "❌ Type Check: FAILED - Found 3 type errors" in output
            assert "✅ Security: PASSED - No security issues" in output
            assert "❌ Coverage: FAILED - Coverage: 75% < 80%" in output

    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        results = [
            GateResult("Lint", False, "Found 10 linting errors"),
            GateResult("Type Check", False, "Found 5 type errors"),
            GateResult("Security", False, "Found 2 security issues"),
            GateResult("Coverage", False, "Coverage: 60% < 80%"),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 1
            assert "AI-Guard Quality Gates Summary" in output
            assert "❌ 4 gate(s) failed" in output
            assert "❌ Lint: FAILED - Found 10 linting errors" in output
            assert "❌ Type Check: FAILED - Found 5 type errors" in output
            assert "❌ Security: FAILED - Found 2 security issues" in output
            assert "❌ Coverage: FAILED - Coverage: 60% < 80%" in output

    def test_summarize_empty_results(self):
        """Test summarize with empty results list."""
        results = []

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 0
            assert "AI-Guard Quality Gates Summary" in output
            assert "✅ All gates passed!" in output

    def test_summarize_no_details(self):
        """Test summarize with results that have no details."""
        results = [
            GateResult("Lint", True),
            GateResult("Type Check", False),
            GateResult("Security", True),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 1
            assert "✅ Lint: PASSED" in output
            assert "❌ Type Check: FAILED" in output
            assert "✅ Security: PASSED" in output

    def test_summarize_mixed_details(self):
        """Test summarize with mixed details (some have, some don't)."""
        results = [
            GateResult("Lint", True, "No issues found"),
            GateResult("Type Check", False),  # No details
            GateResult("Security", True),  # No details
            GateResult("Coverage", False, "Coverage: 75% < 80%"),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 1
            assert "✅ Lint: PASSED - No issues found" in output
            assert "❌ Type Check: FAILED" in output
            assert "✅ Security: PASSED" in output
            assert "❌ Coverage: FAILED - Coverage: 75% < 80%" in output

    def test_summarize_single_result_passed(self):
        """Test summarize with single passed result."""
        results = [GateResult("Single Gate", True, "All good")]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 0
            assert "✅ All gates passed!" in output
            assert "✅ Single Gate: PASSED - All good" in output

    def test_summarize_single_result_failed(self):
        """Test summarize with single failed result."""
        results = [GateResult("Single Gate", False, "Something wrong")]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)

            output = mock_stdout.getvalue()

            assert exit_code == 1
            assert "❌ 1 gate(s) failed" in output
            assert "❌ Single Gate: FAILED - Something wrong" in output


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
            GateResult("Lint", True, "No issues found"),
            GateResult("Type Check", True, "All types correct"),
            GateResult("Security", True, "No security issues"),
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
            GateResult("Lint", True, "No issues found"),
            GateResult("Type Check", False, "Found 3 type errors"),
            GateResult("Security", True, "No security issues"),
            GateResult("Coverage", False, "Coverage: 75% < 80%"),
        ]

        summary = generator.generate_summary(results)

        assert "Quality Gates Summary:" in summary
        assert "Total: 4" in summary
        assert "Passed: 2" in summary
        assert "Failed: 2" in summary
        assert "Failed Gates:" in summary
        assert "- Type Check: Found 3 type errors" in summary
        assert "- Coverage: Coverage: 75% < 80%" in summary

    def test_generate_summary_all_failed(self):
        """Test generating summary with all gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("Lint", False, "Found 10 linting errors"),
            GateResult("Type Check", False, "Found 5 type errors"),
            GateResult("Security", False, "Found 2 security issues"),
        ]

        summary = generator.generate_summary(results)

        assert "Quality Gates Summary:" in summary
        assert "Total: 3" in summary
        assert "Passed: 0" in summary
        assert "Failed: 3" in summary
        assert "Failed Gates:" in summary
        assert "- Lint: Found 10 linting errors" in summary
        assert "- Type Check: Found 5 type errors" in summary
        assert "- Security: Found 2 security issues" in summary

    def test_generate_summary_empty_results(self):
        """Test generating summary with empty results."""
        generator = ReportGenerator()
        results = []

        summary = generator.generate_summary(results)

        assert "Quality Gates Summary:" in summary
        assert "Total: 0" in summary
        assert "Passed: 0" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary

    def test_generate_summary_no_details(self):
        """Test generating summary with results that have no details."""
        generator = ReportGenerator()
        results = [
            GateResult("Lint", True),
            GateResult("Type Check", False),
            GateResult("Security", True),
        ]

        summary = generator.generate_summary(results)

        assert "Total: 3" in summary
        assert "Passed: 2" in summary
        assert "Failed: 1" in summary
        assert "- Type Check: " in summary  # Empty details

    def test_generate_detailed_report_all_passed(self):
        """Test generating detailed report with all gates passed."""
        generator = ReportGenerator()
        results = [
            GateResult("Lint", True, "No issues found", 0),
            GateResult("Type Check", True, "All types correct", 0),
            GateResult("Security", True, "No security issues", 0),
        ]

        report = generator.generate_detailed_report(results)

        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" * 50 in report
        assert "Gate: Lint" in report
        assert "Status: PASSED" in report
        assert "Details: No issues found" in report
        assert "Exit Code: 0" in report
        assert "-" * 30 in report

    def test_generate_detailed_report_some_failed(self):
        """Test generating detailed report with some gates failed."""
        generator = ReportGenerator()
        results = [
            GateResult("Lint", True, "No issues found", 0),
            GateResult("Type Check", False, "Found 3 type errors", 1),
            GateResult("Security", True, "No security issues", 0),
        ]

        report = generator.generate_detailed_report(results)

        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate: Lint" in report
        assert "Status: PASSED" in report
        assert "Details: No issues found" in report
        assert "Exit Code: 0" in report

        assert "Gate: Type Check" in report
        assert "Status: FAILED" in report
        assert "Details: Found 3 type errors" in report
        assert "Exit Code: 1" in report

        assert "Gate: Security" in report
        assert "Status: PASSED" in report
        assert "Details: No security issues" in report
        assert "Exit Code: 0" in report

    def test_generate_detailed_report_no_details(self):
        """Test generating detailed report with results that have no details."""
        generator = ReportGenerator()
        results = [
            GateResult("Lint", True, "", 0),
            GateResult("Type Check", False, "", 1),
        ]

        report = generator.generate_detailed_report(results)

        assert "Gate: Lint" in report
        assert "Status: PASSED" in report
        assert "Exit Code: 0" in report
        # Should not include "Details:" line when details is empty

        assert "Gate: Type Check" in report
        assert "Status: FAILED" in report
        assert "Exit Code: 1" in report

    def test_generate_detailed_report_empty_results(self):
        """Test generating detailed report with empty results."""
        generator = ReportGenerator()
        results = []

        report = generator.generate_detailed_report(results)

        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "=" * 50 in report
        # Should not have any gate entries

    def test_generate_detailed_report_custom_exit_codes(self):
        """Test generating detailed report with custom exit codes."""
        generator = ReportGenerator()
        results = [
            GateResult("Lint", True, "No issues found", 0),
            GateResult("Type Check", False, "Found errors", 2),
            GateResult("Security", True, "No issues", 0),
        ]

        report = generator.generate_detailed_report(results)

        assert "Gate: Lint" in report
        assert "Exit Code: 0" in report

        assert "Gate: Type Check" in report
        assert "Exit Code: 2" in report

        assert "Gate: Security" in report
        assert "Exit Code: 0" in report

    def test_generate_detailed_report_single_result(self):
        """Test generating detailed report with single result."""
        generator = ReportGenerator()
        results = [GateResult("Single Gate", True, "All good", 0)]

        report = generator.generate_detailed_report(results)

        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate: Single Gate" in report
        assert "Status: PASSED" in report
        assert "Details: All good" in report
        assert "Exit Code: 0" in report

    def test_generate_detailed_report_multiple_separators(self):
        """Test that detailed report has proper separators between gates."""
        generator = ReportGenerator()
        results = [
            GateResult("Gate 1", True, "Details 1", 0),
            GateResult("Gate 2", False, "Details 2", 1),
            GateResult("Gate 3", True, "Details 3", 0),
        ]

        report = generator.generate_detailed_report(results)

        # Count the number of separator lines
        separator_count = report.count("-" * 30)
        assert separator_count == 3  # One after each gate


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_gate_result_with_empty_name(self):
        """Test GateResult with empty name."""
        result = GateResult("", True)
        assert result.name == ""
        assert result.passed is True

    def test_gate_result_with_very_long_details(self):
        """Test GateResult with very long details."""
        long_details = "x" * 1000
        result = GateResult("Test", False, long_details)
        assert result.details == long_details

    def test_summarize_with_none_results(self):
        """Test summarize with None results (should handle gracefully)."""
        with pytest.raises((TypeError, AttributeError)):
            summarize(None)

    def test_report_generator_with_none_results(self):
        """Test ReportGenerator with None results (should handle gracefully)."""
        generator = ReportGenerator()

        with pytest.raises((TypeError, AttributeError)):
            generator.generate_summary(None)

        with pytest.raises((TypeError, AttributeError)):
            generator.generate_detailed_report(None)

    def test_gate_result_with_special_characters(self):
        """Test GateResult with special characters in name and details."""
        result = GateResult(
            "Test-Gate_123", True, "Details with émojis 🚀 and symbols @#$%"
        )

        assert result.name == "Test-Gate_123"
        assert result.details == "Details with émojis 🚀 and symbols @#$%"

    def test_summarize_with_unicode_characters(self):
        """Test summarize with unicode characters in results."""
        results = [
            GateResult("Lint", True, "No issues found ✅"),
            GateResult("Type Check", False, "Found errors ❌"),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = summarize(results)
            output = mock_stdout.getvalue()

            assert exit_code == 1
            assert "No issues found ✅" in output
            assert "Found errors ❌" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
