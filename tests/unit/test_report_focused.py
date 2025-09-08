"""Focused tests for the report module."""

import unittest
from unittest.mock import patch
from io import StringIO
import sys

from src.ai_guard.report import GateResult, summarize, ReportGenerator


class TestGateResult(unittest.TestCase):
    """Test the GateResult dataclass."""

    def test_gate_result_creation(self):
        """Test creating a GateResult with all parameters."""
        result = GateResult(
            name="test_gate",
            passed=True,
            details="Test details",
            exit_code=0
        )
        self.assertEqual(result.name, "test_gate")
        self.assertTrue(result.passed)
        self.assertEqual(result.details, "Test details")
        self.assertEqual(result.exit_code, 0)

    def test_gate_result_minimal(self):
        """Test creating a GateResult with minimal parameters."""
        result = GateResult(name="minimal_gate", passed=False)
        self.assertEqual(result.name, "minimal_gate")
        self.assertFalse(result.passed)
        self.assertEqual(result.details, "")
        self.assertEqual(result.exit_code, 0)

    def test_gate_result_failed(self):
        """Test creating a failed GateResult."""
        result = GateResult(
            name="failed_gate",
            passed=False,
            details="Gate failed",
            exit_code=1
        )
        self.assertEqual(result.name, "failed_gate")
        self.assertFalse(result.passed)
        self.assertEqual(result.details, "Gate failed")
        self.assertEqual(result.exit_code, 1)


class TestSummarize(unittest.TestCase):
    """Test the summarize function."""

    def setUp(self):
        """Set up test fixtures."""
        self.passed_result = GateResult(
            name="passed_gate",
            passed=True,
            details="All good",
            exit_code=0
        )
        self.failed_result = GateResult(
            name="failed_gate",
            passed=False,
            details="Something wrong",
            exit_code=1
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_summarize_all_passed(self, mock_stdout):
        """Test summarize with all gates passed."""
        results = [self.passed_result, self.passed_result]
        exit_code = summarize(results)
        
        self.assertEqual(exit_code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("✅ All gates passed!", output)
        self.assertIn("passed_gate: PASSED", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_summarize_some_failed(self, mock_stdout):
        """Test summarize with some gates failed."""
        results = [self.passed_result, self.failed_result]
        exit_code = summarize(results)
        
        self.assertEqual(exit_code, 1)
        output = mock_stdout.getvalue()
        self.assertIn("❌ 1 gate(s) failed", output)
        self.assertIn("failed_gate: FAILED", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_summarize_all_failed(self, mock_stdout):
        """Test summarize with all gates failed."""
        results = [self.failed_result, self.failed_result]
        exit_code = summarize(results)
        
        self.assertEqual(exit_code, 1)
        output = mock_stdout.getvalue()
        self.assertIn("❌ 2 gate(s) failed", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_summarize_empty_results(self, mock_stdout):
        """Test summarize with empty results."""
        results = []
        exit_code = summarize(results)
        
        self.assertEqual(exit_code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("✅ All gates passed!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_summarize_with_details(self, mock_stdout):
        """Test summarize with detailed results."""
        results = [
            GateResult(name="gate1", passed=True, details="Details 1"),
            GateResult(name="gate2", passed=False, details="Details 2")
        ]
        exit_code = summarize(results)
        
        self.assertEqual(exit_code, 1)
        output = mock_stdout.getvalue()
        self.assertIn("gate1: PASSED - Details 1", output)
        self.assertIn("gate2: FAILED - Details 2", output)


class TestReportGenerator(unittest.TestCase):
    """Test the ReportGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = ReportGenerator()
        self.passed_result = GateResult(
            name="passed_gate",
            passed=True,
            details="All good",
            exit_code=0
        )
        self.failed_result = GateResult(
            name="failed_gate",
            passed=False,
            details="Something wrong",
            exit_code=1
        )

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        self.assertIsNotNone(generator)

    def test_generate_summary_all_passed(self):
        """Test generating summary with all gates passed."""
        results = [self.passed_result, self.passed_result]
        summary = self.generator.generate_summary(results)
        
        self.assertIn("Total: 2", summary)
        self.assertIn("Passed: 2", summary)
        self.assertIn("Failed: 0", summary)
        self.assertNotIn("Failed Gates:", summary)

    def test_generate_summary_some_failed(self):
        """Test generating summary with some gates failed."""
        results = [self.passed_result, self.failed_result]
        summary = self.generator.generate_summary(results)
        
        self.assertIn("Total: 2", summary)
        self.assertIn("Passed: 1", summary)
        self.assertIn("Failed: 1", summary)
        self.assertIn("Failed Gates:", summary)
        self.assertIn("failed_gate: Something wrong", summary)

    def test_generate_summary_all_failed(self):
        """Test generating summary with all gates failed."""
        results = [self.failed_result, self.failed_result]
        summary = self.generator.generate_summary(results)
        
        self.assertIn("Total: 2", summary)
        self.assertIn("Passed: 0", summary)
        self.assertIn("Failed: 2", summary)
        self.assertIn("Failed Gates:", summary)

    def test_generate_summary_empty_results(self):
        """Test generating summary with empty results."""
        results = []
        summary = self.generator.generate_summary(results)
        
        self.assertIn("Total: 0", summary)
        self.assertIn("Passed: 0", summary)
        self.assertIn("Failed: 0", summary)

    def test_generate_detailed_report(self):
        """Test generating detailed report."""
        results = [self.passed_result, self.failed_result]
        report = self.generator.generate_detailed_report(results)
        
        self.assertIn("AI-Guard Quality Gates Detailed Report", report)
        self.assertIn("Gate: passed_gate", report)
        self.assertIn("Status: PASSED", report)
        self.assertIn("Details: All good", report)
        self.assertIn("Exit Code: 0", report)
        self.assertIn("Gate: failed_gate", report)
        self.assertIn("Status: FAILED", report)
        self.assertIn("Details: Something wrong", report)
        self.assertIn("Exit Code: 1", report)

    def test_generate_detailed_report_empty_results(self):
        """Test generating detailed report with empty results."""
        results = []
        report = self.generator.generate_detailed_report(results)
        
        self.assertIn("AI-Guard Quality Gates Detailed Report", report)
        self.assertNotIn("Gate:", report)

    def test_generate_detailed_report_no_details(self):
        """Test generating detailed report with results without details."""
        result = GateResult(name="no_details_gate", passed=True)
        results = [result]
        report = self.generator.generate_detailed_report(results)
        
        self.assertIn("Gate: no_details_gate", report)
        self.assertIn("Status: PASSED", report)
        self.assertNotIn("Details:", report)
        self.assertIn("Exit Code: 0", report)


if __name__ == "__main__":
    unittest.main()
