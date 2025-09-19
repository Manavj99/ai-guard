"""Comprehensive tests for report.py and report_html.py modules."""

import pytest
from unittest.mock import Mock, patch, mock_open
from dataclasses import asdict

from src.ai_guard.report import GateResult, summarize, ReportGenerator
from src.ai_guard.report_html import write_html, _BASE_CSS


class TestGateResult:
    """Test GateResult dataclass."""

    def test_gate_result_creation(self):
        """Test creating GateResult."""
        result = GateResult(
            name="Test Gate",
            passed=True,
            details="All tests passed",
            exit_code=0
        )
        
        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == "All tests passed"
        assert result.exit_code == 0

    def test_gate_result_minimal(self):
        """Test creating GateResult with minimal data."""
        result = GateResult(
            name="Minimal Gate",
            passed=False
        )
        
        assert result.name == "Minimal Gate"
        assert result.passed is False
        assert result.details == ""
        assert result.exit_code == 0

    def test_gate_result_failed(self):
        """Test creating failed GateResult."""
        result = GateResult(
            name="Failed Gate",
            passed=False,
            details="Tests failed",
            exit_code=1
        )
        
        assert result.name == "Failed Gate"
        assert result.passed is False
        assert result.details == "Tests failed"
        assert result.exit_code == 1


class TestSummarize:
    """Test summarize function."""

    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", True, "Passed"),
            GateResult("Gate 3", True, "Passed")
        ]
        
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 0
            mock_print.assert_called()
            
            # Check that success message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("All gates passed!" in call for call in print_calls)

    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", True, "Passed")
        ]
        
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 1
            mock_print.assert_called()
            
            # Check that failure message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("1 gate(s) failed" in call for call in print_calls)

    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        results = [
            GateResult("Gate 1", False, "Failed 1"),
            GateResult("Gate 2", False, "Failed 2"),
            GateResult("Gate 3", False, "Failed 3")
        ]
        
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 1
            mock_print.assert_called()
            
            # Check that failure message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("3 gate(s) failed" in call for call in print_calls)

    def test_summarize_empty_results(self):
        """Test summarize with empty results."""
        results = []
        
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            
            assert exit_code == 0
            mock_print.assert_called()
            
            # Check that success message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("All gates passed!" in call for call in print_calls)

    def test_summarize_output_format(self):
        """Test that summarize produces correct output format."""
        results = [
            GateResult("Linting", True, "No issues found"),
            GateResult("Tests", False, "2 tests failed"),
            GateResult("Coverage", True, "85% coverage")
        ]
        
        with patch("builtins.print") as mock_print:
            summarize(results)
            
            # Check that all gates were printed with correct format
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Should have header
            assert any("AI-Guard Quality Gates Summary" in call for call in print_calls)
            
            # Should have individual gate results
            assert any("✅ Linting: PASSED" in call for call in print_calls)
            assert any("❌ Tests: FAILED" in call for call in print_calls)
            assert any("✅ Coverage: PASSED" in call for call in print_calls)


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator.results == []

    def test_add_result(self):
        """Test adding results to generator."""
        generator = ReportGenerator()
        
        result1 = GateResult("Gate 1", True, "Passed")
        result2 = GateResult("Gate 2", False, "Failed")
        
        generator.add_result(result1)
        generator.add_result(result2)
        
        assert len(generator.results) == 2
        assert generator.results[0] == result1
        assert generator.results[1] == result2

    def test_get_summary(self):
        """Test getting summary from generator."""
        generator = ReportGenerator()
        
        generator.add_result(GateResult("Gate 1", True, "Passed"))
        generator.add_result(GateResult("Gate 2", False, "Failed"))
        generator.add_result(GateResult("Gate 3", True, "Passed"))
        
        summary = generator.get_summary()
        
        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == 2/3

    def test_get_summary_empty(self):
        """Test getting summary with no results."""
        generator = ReportGenerator()
        
        summary = generator.get_summary()
        
        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["success_rate"] == 0

    def test_clear_results(self):
        """Test clearing results."""
        generator = ReportGenerator()
        
        generator.add_result(GateResult("Gate 1", True, "Passed"))
        generator.add_result(GateResult("Gate 2", False, "Failed"))
        
        assert len(generator.results) == 2
        
        generator.clear_results()
        
        assert len(generator.results) == 0

    def test_get_failed_results(self):
        """Test getting only failed results."""
        generator = ReportGenerator()
        
        generator.add_result(GateResult("Gate 1", True, "Passed"))
        generator.add_result(GateResult("Gate 2", False, "Failed"))
        generator.add_result(GateResult("Gate 3", True, "Passed"))
        generator.add_result(GateResult("Gate 4", False, "Failed"))
        
        failed_results = generator.get_failed_results()
        
        assert len(failed_results) == 2
        assert all(not result.passed for result in failed_results)

    def test_get_passed_results(self):
        """Test getting only passed results."""
        generator = ReportGenerator()
        
        generator.add_result(GateResult("Gate 1", True, "Passed"))
        generator.add_result(GateResult("Gate 2", False, "Failed"))
        generator.add_result(GateResult("Gate 3", True, "Passed"))
        generator.add_result(GateResult("Gate 4", False, "Failed"))
        
        passed_results = generator.get_passed_results()
        
        assert len(passed_results) == 2
        assert all(result.passed for result in passed_results)

    def test_export_results(self):
        """Test exporting results."""
        generator = ReportGenerator()
        
        generator.add_result(GateResult("Gate 1", True, "Passed"))
        generator.add_result(GateResult("Gate 2", False, "Failed"))
        
        exported = generator.export_results()
        
        assert "results" in exported
        assert "summary" in exported
        assert "timestamp" in exported
        
        assert len(exported["results"]) == 2
        assert exported["summary"]["total"] == 2
        assert exported["summary"]["passed"] == 1
        assert exported["summary"]["failed"] == 1


class TestWriteHTML:
    """Test write_html function."""

    def test_write_html_basic(self):
        """Test writing basic HTML report."""
        results = [
            GateResult("Linting", True, "No issues found"),
            GateResult("Tests", False, "2 tests failed"),
            GateResult("Coverage", True, "85% coverage")
        ]
        
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line too long",
                "path": "test.py",
                "line": 10
            },
            {
                "rule_id": "W001",
                "level": "warning",
                "message": "Unused import",
                "path": "test.py",
                "line": 5
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            mock_file.assert_called_once_with("test_report.html", "w", encoding="utf-8")
            
            # Check that HTML content was written
            written_content = mock_file().write.call_args[0][0]
            assert "<html>" in written_content
            assert "<head>" in written_content
            assert "<body>" in written_content
            assert "AI-Guard Report" in written_content

    def test_write_html_with_results(self):
        """Test writing HTML report with gate results."""
        results = [
            GateResult("Linting", True, "No issues found"),
            GateResult("Tests", False, "2 tests failed")
        ]
        
        findings = []
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that results are included
            assert "Linting" in written_content
            assert "Tests" in written_content
            assert "No issues found" in written_content
            assert "2 tests failed" in written_content

    def test_write_html_with_findings(self):
        """Test writing HTML report with findings."""
        results = []
        
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line too long",
                "path": "test.py",
                "line": 10
            },
            {
                "rule_id": "W001",
                "level": "warning",
                "message": "Unused import",
                "path": "test.py",
                "line": 5
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that findings are included
            assert "E501" in written_content
            assert "W001" in written_content
            assert "Line too long" in written_content
            assert "Unused import" in written_content
            assert "test.py" in written_content

    def test_write_html_empty_results(self):
        """Test writing HTML report with empty results."""
        results = []
        findings = []
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Should still generate valid HTML
            assert "<html>" in written_content
            assert "<body>" in written_content
            assert "AI-Guard Report" in written_content

    def test_write_html_css_included(self):
        """Test that CSS is included in HTML report."""
        results = [GateResult("Test", True, "Passed")]
        findings = []
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that CSS is included
            assert "font-family" in written_content
            assert ".badge" in written_content
            assert ".badge.pass" in written_content
            assert ".badge.fail" in written_content

    def test_write_html_findings_table(self):
        """Test that findings are displayed in a table."""
        results = []
        
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line too long",
                "path": "test.py",
                "line": 10
            },
            {
                "rule_id": "W001",
                "level": "warning",
                "message": "Unused import",
                "path": "test.py",
                "line": 5
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that table structure is present
            assert "<table>" in written_content
            assert "<th>" in written_content
            assert "<td>" in written_content
            assert "Rule ID" in written_content
            assert "Level" in written_content
            assert "Message" in written_content
            assert "Path" in written_content
            assert "Line" in written_content

    def test_write_html_results_summary(self):
        """Test that results summary is included."""
        results = [
            GateResult("Linting", True, "No issues found"),
            GateResult("Tests", False, "2 tests failed"),
            GateResult("Coverage", True, "85% coverage")
        ]
        
        findings = []
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that summary is included
            assert "Summary" in written_content
            assert "3" in written_content  # Total results
            assert "2" in written_content  # Passed results
            assert "1" in written_content  # Failed results

    def test_write_html_error_levels(self):
        """Test that different error levels are styled correctly."""
        results = []
        
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line too long",
                "path": "test.py",
                "line": 10
            },
            {
                "rule_id": "W001",
                "level": "warning",
                "message": "Unused import",
                "path": "test.py",
                "line": 5
            },
            {
                "rule_id": "I001",
                "level": "note",
                "message": "Style suggestion",
                "path": "test.py",
                "line": 1
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that different levels are styled
            assert "finding-error" in written_content
            assert "finding-warning" in written_content
            assert "finding-note" in written_content

    def test_write_html_file_error(self):
        """Test handling file write errors."""
        results = [GateResult("Test", True, "Passed")]
        findings = []
        
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Should not raise exception
            write_html("test_report.html", results, findings)

    def test_write_html_special_characters(self):
        """Test that special characters are properly escaped."""
        results = [
            GateResult("Test <script>", True, "Details with & special chars")
        ]
        
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line with <script>alert('xss')</script>",
                "path": "test.py",
                "line": 10
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("test_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Check that special characters are escaped
            assert "&lt;script&gt;" in written_content
            assert "&amp;" in written_content
            assert "alert('xss')" not in written_content  # Should be escaped


class TestBaseCSS:
    """Test _BASE_CSS constant."""

    def test_base_css_content(self):
        """Test that _BASE_CSS contains expected styles."""
        assert "font-family" in _BASE_CSS
        assert ".badge" in _BASE_CSS
        assert ".badge.pass" in _BASE_CSS
        assert ".badge.fail" in _BASE_CSS
        assert "table" in _BASE_CSS
        assert "th, td" in _BASE_CSS
        assert "code" in _BASE_CSS
        assert ".finding-error" in _BASE_CSS
        assert ".finding-warning" in _BASE_CSS
        assert ".finding-note" in _BASE_CSS

    def test_base_css_structure(self):
        """Test that _BASE_CSS has proper CSS structure."""
        # Should contain basic CSS properties
        assert "background:" in _BASE_CSS
        assert "color:" in _BASE_CSS
        assert "border:" in _BASE_CSS
        assert "padding:" in _BASE_CSS
        assert "margin:" in _BASE_CSS


class TestIntegration:
    """Integration tests for report modules."""

    def test_full_report_workflow(self):
        """Test full workflow from results to HTML report."""
        # Create test results
        results = [
            GateResult("Linting", True, "No issues found"),
            GateResult("Tests", False, "2 tests failed"),
            GateResult("Coverage", True, "85% coverage"),
            GateResult("Security", False, "1 vulnerability found")
        ]
        
        # Create test findings
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line too long (120 > 79 characters)",
                "path": "src/main.py",
                "line": 10
            },
            {
                "rule_id": "B101",
                "level": "error",
                "message": "Use of hardcoded password strings",
                "path": "src/auth.py",
                "line": 5
            },
            {
                "rule_id": "W001",
                "level": "warning",
                "message": "Unused import 'os'",
                "path": "src/utils.py",
                "line": 1
            }
        ]
        
        # Test summarize function
        with patch("builtins.print") as mock_print:
            exit_code = summarize(results)
            assert exit_code == 1  # Some gates failed
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("2 gate(s) failed" in call for call in print_calls)
        
        # Test ReportGenerator
        generator = ReportGenerator()
        for result in results:
            generator.add_result(result)
        
        summary = generator.get_summary()
        assert summary["total"] == 4
        assert summary["passed"] == 2
        assert summary["failed"] == 2
        assert summary["success_rate"] == 0.5
        
        failed_results = generator.get_failed_results()
        assert len(failed_results) == 2
        assert all(not result.passed for result in failed_results)
        
        # Test HTML report generation
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("integration_test.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Verify all components are present
            assert "<html>" in written_content
            assert "AI-Guard Report" in written_content
            assert "Linting" in written_content
            assert "Tests" in written_content
            assert "Coverage" in written_content
            assert "Security" in written_content
            assert "E501" in written_content
            assert "B101" in written_content
            assert "W001" in written_content
            assert "src/main.py" in written_content
            assert "src/auth.py" in written_content
            assert "src/utils.py" in written_content

    def test_report_generator_with_real_data(self):
        """Test ReportGenerator with realistic data."""
        generator = ReportGenerator()
        
        # Add realistic gate results
        gates = [
            ("Code Style", True, "All files follow style guidelines"),
            ("Type Checking", True, "No type errors found"),
            ("Security Scan", False, "3 vulnerabilities detected"),
            ("Test Coverage", False, "Coverage below 80% threshold"),
            ("Performance", True, "No performance regressions"),
            ("Documentation", True, "All public APIs documented")
        ]
        
        for name, passed, details in gates:
            generator.add_result(GateResult(name, passed, details))
        
        # Test summary
        summary = generator.get_summary()
        assert summary["total"] == 6
        assert summary["passed"] == 4
        assert summary["failed"] == 2
        assert summary["success_rate"] == 4/6
        
        # Test filtering
        failed_gates = generator.get_failed_results()
        assert len(failed_gates) == 2
        assert failed_gates[0].name == "Security Scan"
        assert failed_gates[1].name == "Test Coverage"
        
        passed_gates = generator.get_passed_results()
        assert len(passed_gates) == 4
        assert all(gate.passed for gate in passed_gates)
        
        # Test export
        exported = generator.export_results()
        assert "results" in exported
        assert "summary" in exported
        assert "timestamp" in exported
        assert len(exported["results"]) == 6

    def test_html_report_with_complex_findings(self):
        """Test HTML report with complex findings."""
        results = [
            GateResult("Linting", False, "5 style violations found"),
            GateResult("Security", False, "2 security issues found"),
            GateResult("Tests", True, "All tests passed")
        ]
        
        findings = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Line too long (120 > 79 characters)",
                "path": "src/very/long/path/to/file.py",
                "line": 42
            },
            {
                "rule_id": "B101",
                "level": "error",
                "message": "Use of hardcoded password strings",
                "path": "src/auth.py",
                "line": 15
            },
            {
                "rule_id": "W001",
                "level": "warning",
                "message": "Unused import 'os'",
                "path": "src/utils.py",
                "line": 1
            },
            {
                "rule_id": "C901",
                "level": "warning",
                "message": "Function is too complex (15 > 10)",
                "path": "src/complex.py",
                "line": 25
            },
            {
                "rule_id": "I001",
                "level": "note",
                "message": "Consider using f-strings instead of .format()",
                "path": "src/formatting.py",
                "line": 8
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            write_html("complex_report.html", results, findings)
            
            written_content = mock_file().write.call_args[0][0]
            
            # Verify all findings are present
            for finding in findings:
                assert finding["rule_id"] in written_content
                assert finding["message"] in written_content
                assert finding["path"] in written_content
                assert str(finding["line"]) in written_content
            
            # Verify proper styling for different levels
            assert "finding-error" in written_content
            assert "finding-warning" in written_content
            assert "finding-note" in written_content
            
            # Verify table structure
            assert "<table>" in written_content
            assert "<th>Rule ID</th>" in written_content
            assert "<th>Level</th>" in written_content
            assert "<th>Message</th>" in written_content
            assert "<th>Path</th>" in written_content
            assert "<th>Line</th>" in written_content
