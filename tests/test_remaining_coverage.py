"""Comprehensive tests for remaining low-coverage files."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
from dataclasses import dataclass

from src.ai_guard.report_html import (
    write_html, HTMLReportGenerator, _BASE_CSS
)
from src.ai_guard.sarif_report import (
    SarifResult, SarifRun, create_sarif_report, parse_issue_to_sarif,
    write_sarif, make_location
)
from src.ai_guard.tests_runner import (
    run_pytest, run_pytest_with_coverage, TestsRunner
)
from src.ai_guard.report import GateResult


class TestHTMLReport:
    """Test HTML report functionality."""

    def test_write_html_all_passed(self):
        """Test write_html with all gates passed."""
        gates = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed"),
        ]
        findings = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "ALL GATES PASSED" in content
            assert "AI-Guard Report" in content
            assert "gate1" in content
            assert "gate2" in content
            assert "No findings 🎉" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_some_failed(self):
        """Test write_html with some gates failed."""
        gates = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]
        findings = [
            {
                "path": "src/test.py",
                "line": 10,
                "level": "error",
                "rule_id": "E501",
                "message": "Line too long"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "GATES FAILED" in content
            assert "src/test.py:10" in content
            assert "E501" in content
            assert "Line too long" in content
            assert "ERROR" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_with_findings(self):
        """Test write_html with various findings."""
        gates = [GateResult("gate1", False, "Failed")]
        findings = [
            {
                "path": "src/test1.py",
                "line": 5,
                "level": "warning",
                "rule_id": "W123",
                "message": "Warning message"
            },
            {
                "path": "src/test2.py",
                "line": 15,
                "level": "note",
                "rule_id": "N456",
                "message": "Note message"
            },
            {
                "path": "src/test3.py",
                "level": "error",  # No line number
                "rule_id": "E789",
                "message": "Error message"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "WARNING" in content
            assert "NOTE" in content
            assert "ERROR" in content
            assert "src/test1.py:5" in content
            assert "src/test2.py:15" in content
            assert "src/test3.py:" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_escape_characters(self):
        """Test write_html with characters that need escaping."""
        gates = [GateResult("gate<>&\"'", True, "Details<>&\"'")]
        findings = [
            {
                "path": "file<>&\"'.py",
                "line": 1,
                "level": "error",
                "rule_id": "rule<>&\"'",
                "message": "Message<>&\"'"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check that characters are properly escaped
            assert "&lt;" in content
            assert "&gt;" in content
            assert "&amp;" in content
            assert "&quot;" in content
            assert "&#x27;" in content
        finally:
            os.unlink(temp_path)

    def test_html_report_generator_init(self):
        """Test HTMLReportGenerator initialization."""
        generator = HTMLReportGenerator()
        assert generator is not None

    def test_html_report_generator_generate_html_report(self):
        """Test HTMLReportGenerator.generate_html_report."""
        generator = HTMLReportGenerator()
        gates = [GateResult("gate1", True, "Passed")]
        findings = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            generator.generate_html_report(gates, findings, temp_path)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "AI-Guard Report" in content
        finally:
            os.unlink(temp_path)

    def test_html_report_generator_generate_summary_html_all_passed(self):
        """Test HTMLReportGenerator.generate_summary_html with all passed."""
        generator = HTMLReportGenerator()
        gates = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed"),
        ]
        
        html = generator.generate_summary_html(gates)
        
        assert "Total: 2" in html
        assert "Passed:" in html
        assert "2" in html
        assert "Failed:" in html
        assert "0" in html
        assert "Failed Gates:" not in html

    def test_html_report_generator_generate_summary_html_some_failed(self):
        """Test HTMLReportGenerator.generate_summary_html with some failed."""
        generator = HTMLReportGenerator()
        gates = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]
        
        html = generator.generate_summary_html(gates)
        
        assert "Total: 2" in html
        assert "Passed:" in html
        assert "1" in html
        assert "Failed:" in html
        assert "1" in html
        assert "Failed Gates:" in html
        assert "gate2: Failed" in html


class TestSARIFReport:
    """Test SARIF report functionality."""

    def test_sarif_result_creation(self):
        """Test SarifResult creation."""
        result = SarifResult("rule123", "error", "Test message")
        assert result.rule_id == "rule123"
        assert result.level == "error"
        assert result.message == "Test message"
        assert result.locations is None

    def test_sarif_result_with_locations(self):
        """Test SarifResult creation with locations."""
        locations = [{"physicalLocation": {"artifactLocation": {"uri": "file.py"}}}]
        result = SarifResult("rule123", "error", "Test message", locations)
        assert result.locations == locations

    def test_sarif_run_creation(self):
        """Test SarifRun creation."""
        results = [SarifResult("rule123", "error", "Test message")]
        run = SarifRun("test-tool", results)
        assert run.tool_name == "test-tool"
        assert run.results == results
        assert run.tool_version == "unknown"

    def test_sarif_run_with_version(self):
        """Test SarifRun creation with version."""
        results = [SarifResult("rule123", "error", "Test message")]
        run = SarifRun("test-tool", results, "1.0.0")
        assert run.tool_version == "1.0.0"

    def test_create_sarif_report_basic(self):
        """Test create_sarif_report basic functionality."""
        results = [SarifResult("rule123", "error", "Test message")]
        run = SarifRun("test-tool", results)
        
        sarif = create_sarif_report([run])
        
        assert sarif["version"] == "2.1.0"
        assert sarif["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
        assert len(sarif["runs"]) == 1
        assert sarif["runs"][0]["tool"]["driver"]["name"] == "test-tool"
        assert len(sarif["runs"][0]["results"]) == 1

    def test_create_sarif_report_with_metadata(self):
        """Test create_sarif_report with metadata."""
        results = [SarifResult("rule123", "error", "Test message")]
        run = SarifRun("test-tool", results)
        metadata = {"version": "1.0.0", "timestamp": "2023-01-01"}
        
        sarif = create_sarif_report([run], metadata)
        
        assert sarif["metadata"] == metadata

    def test_create_sarif_report_multiple_runs(self):
        """Test create_sarif_report with multiple runs."""
        results1 = [SarifResult("rule123", "error", "Test message 1")]
        results2 = [SarifResult("rule456", "warning", "Test message 2")]
        run1 = SarifRun("tool1", results1)
        run2 = SarifRun("tool2", results2)
        
        sarif = create_sarif_report([run1, run2])
        
        assert len(sarif["runs"]) == 2
        assert sarif["runs"][0]["tool"]["driver"]["name"] == "tool1"
        assert sarif["runs"][1]["tool"]["driver"]["name"] == "tool2"

    def test_create_sarif_report_with_locations(self):
        """Test create_sarif_report with locations."""
        locations = [{"physicalLocation": {"artifactLocation": {"uri": "file.py"}}}]
        results = [SarifResult("rule123", "error", "Test message", locations)]
        run = SarifRun("test-tool", results)
        
        sarif = create_sarif_report([run])
        
        assert "locations" in sarif["runs"][0]["results"][0]
        assert sarif["runs"][0]["results"][0]["locations"] == locations

    def test_parse_issue_to_sarif_basic(self):
        """Test parse_issue_to_sarif basic functionality."""
        issue = {
            "rule_id": "rule123",
            "level": "error",
            "message": "Test message"
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "rule123"
        assert result.level == "error"
        assert result.message == "Test message"
        assert result.locations is None

    def test_parse_issue_to_sarif_with_location(self):
        """Test parse_issue_to_sarif with file and line."""
        issue = {
            "rule_id": "rule123",
            "level": "error",
            "message": "Test message",
            "file": "src/test.py",
            "line": 10,
            "column": 5
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "rule123"
        assert result.locations is not None
        assert len(result.locations) == 1
        location = result.locations[0]
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_issue_to_sarif_defaults(self):
        """Test parse_issue_to_sarif with default values."""
        issue = {}
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "unknown"
        assert result.level == "warning"
        assert result.message == "No message provided"

    def test_write_sarif(self):
        """Test write_sarif function."""
        results = [SarifResult("rule123", "error", "Test message")]
        run = SarifRun("test-tool", results)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name

        try:
            write_sarif(temp_path, run)

            with open(temp_path, 'r', encoding='utf-8') as f:
                sarif = json.load(f)

            assert sarif["version"] == "2.1.0"
            assert len(sarif["runs"]) == 1
            assert sarif["runs"][0]["tool"]["driver"]["name"] == "test-tool"
        finally:
            os.unlink(temp_path)

    def test_write_sarif_with_locations(self):
        """Test write_sarif with locations."""
        locations = [{"physicalLocation": {"artifactLocation": {"uri": "file.py"}}}]
        results = [SarifResult("rule123", "error", "Test message", locations)]
        run = SarifRun("test-tool", results)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name

        try:
            write_sarif(temp_path, run)

            with open(temp_path, 'r', encoding='utf-8') as f:
                sarif = json.load(f)

            assert "locations" in sarif["runs"][0]["results"][0]
        finally:
            os.unlink(temp_path)

    def test_make_location_basic(self):
        """Test make_location basic functionality."""
        location = make_location("src/test.py")
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert "region" not in location["physicalLocation"]

    def test_make_location_with_line(self):
        """Test make_location with line number."""
        location = make_location("src/test.py", line=10)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert "startColumn" not in location["physicalLocation"]["region"]

    def test_make_location_with_column(self):
        """Test make_location with column number."""
        location = make_location("src/test.py", line=10, column=5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_make_location_normalize_path(self):
        """Test make_location normalizes Windows paths."""
        location = make_location("src\\test.py", line=10)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"


class TestTestsRunner:
    """Test tests_runner functionality."""

    def test_run_pytest_no_args(self):
        """Test run_pytest with no extra args."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            result = run_pytest()
            
            assert result == 0
            mock_call.assert_called_once()
            args = mock_call.call_args[0][0]
            assert "python" in args[0]
            assert "-m" in args
            assert "pytest" in args
            assert "-q" in args

    def test_run_pytest_with_args(self):
        """Test run_pytest with extra args."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            result = run_pytest(["-v", "--tb=short"])
            
            assert result == 0
            mock_call.assert_called_once()
            args = mock_call.call_args[0][0]
            assert "-v" in args
            assert "--tb=short" in args

    def test_run_pytest_with_coverage(self):
        """Test run_pytest_with_coverage."""
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 0
            result = run_pytest_with_coverage()
            
            assert result == 0
            mock_run_pytest.assert_called_once_with(["--cov=src", "--cov-report=xml"])

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None

    def test_tests_runner_run_pytest(self):
        """Test TestsRunner.run_pytest."""
        runner = TestsRunner()
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 0
            result = runner.run_pytest()
            
            assert result == 0
            mock_run_pytest.assert_called_once_with(None)

    def test_tests_runner_run_pytest_with_args(self):
        """Test TestsRunner.run_pytest with args."""
        runner = TestsRunner()
        with patch('src.ai_guard.tests_runner.run_pytest') as mock_run_pytest:
            mock_run_pytest.return_value = 0
            result = runner.run_pytest(["-v"])
            
            assert result == 0
            mock_run_pytest.assert_called_once_with(["-v"])

    def test_tests_runner_run_pytest_with_coverage(self):
        """Test TestsRunner.run_pytest_with_coverage."""
        runner = TestsRunner()
        with patch('src.ai_guard.tests_runner.run_pytest_with_coverage') as mock_run_pytest_with_coverage:
            mock_run_pytest_with_coverage.return_value = 0
            result = runner.run_pytest_with_coverage()
            
            assert result == 0
            mock_run_pytest_with_coverage.assert_called_once()

    def test_tests_runner_run_tests_with_coverage(self):
        """Test TestsRunner.run_tests with coverage."""
        runner = TestsRunner()
        with patch.object(runner, 'run_pytest_with_coverage', return_value=0):
            result = runner.run_tests(with_coverage=True)
            
            assert result == 0

    def test_tests_runner_run_tests_without_coverage(self):
        """Test TestsRunner.run_tests without coverage."""
        runner = TestsRunner()
        with patch.object(runner, 'run_pytest', return_value=0):
            result = runner.run_tests(with_coverage=False)
            
            assert result == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_write_html_empty_gates_and_findings(self):
        """Test write_html with empty gates and findings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, [], [])
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            assert "ALL GATES PASSED" in content
            assert "No findings 🎉" in content
        finally:
            os.unlink(temp_path)

    def test_create_sarif_report_empty_runs(self):
        """Test create_sarif_report with empty runs."""
        sarif = create_sarif_report([])
        
        assert sarif["version"] == "2.1.0"
        assert sarif["runs"] == []

    def test_parse_issue_to_sarif_missing_fields(self):
        """Test parse_issue_to_sarif with missing fields."""
        issue = {"file": "test.py", "line": 10}  # Missing rule_id, level, message
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "unknown"
        assert result.level == "warning"
        assert result.message == "No message provided"
        assert result.locations is not None

    def test_make_location_with_none_values(self):
        """Test make_location with None values."""
        location = make_location("test.py", line=None, column=None)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert "region" not in location["physicalLocation"]

    def test_html_escape_edge_cases(self):
        """Test HTML escaping with edge cases."""
        gates = [GateResult("test", True, "")]
        findings = [{"path": "", "line": None, "level": "", "rule_id": "", "message": ""}]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Should not crash and should produce valid HTML
            assert "AI-Guard Report" in content
        finally:
            os.unlink(temp_path)
