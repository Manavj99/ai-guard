"""Comprehensive tests for SARIF report module."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open

from src.ai_guard.sarif_report import (
    SarifResult,
    SarifRun,
    create_sarif_report,
    parse_issue_to_sarif,
    write_sarif,
    make_location,
)


class TestSarifResult:
    """Test SarifResult dataclass."""

    def test_sarif_result_creation(self):
        """Test creating SarifResult."""
        result = SarifResult(
            rule_id="TEST001",
            level="error",
            message="Test error message",
            locations=[{"file": "test.py", "line": 10}]
        )
        
        assert result.rule_id == "TEST001"
        assert result.level == "error"
        assert result.message == "Test error message"
        assert result.locations == [{"file": "test.py", "line": 10}]

    def test_sarif_result_minimal(self):
        """Test creating SarifResult with minimal fields."""
        result = SarifResult(
            rule_id="TEST002",
            level="warning",
            message="Test warning message"
        )
        
        assert result.rule_id == "TEST002"
        assert result.level == "warning"
        assert result.message == "Test warning message"
        assert result.locations is None

    def test_sarif_result_all_levels(self):
        """Test SarifResult with all supported levels."""
        levels = ["none", "note", "warning", "error"]
        
        for level in levels:
            result = SarifResult(
                rule_id="TEST001",
                level=level,
                message=f"Test {level} message"
            )
            assert result.level == level


class TestSarifRun:
    """Test SarifRun dataclass."""

    def test_sarif_run_creation(self):
        """Test creating SarifRun."""
        results = [
            SarifResult("TEST001", "error", "Error message"),
            SarifResult("TEST002", "warning", "Warning message")
        ]
        
        run = SarifRun(
            tool_name="AI-Guard",
            results=results,
            tool_version="1.0.0"
        )
        
        assert run.tool_name == "AI-Guard"
        assert len(run.results) == 2
        assert run.tool_version == "1.0.0"

    def test_sarif_run_minimal(self):
        """Test creating SarifRun with minimal fields."""
        run = SarifRun(
            tool_name="Test Tool",
            results=[]
        )
        
        assert run.tool_name == "Test Tool"
        assert run.results == []
        assert run.tool_version == "unknown"

    def test_sarif_run_empty_results(self):
        """Test SarifRun with empty results."""
        run = SarifRun(
            tool_name="Empty Tool",
            results=[]
        )
        
        assert run.tool_name == "Empty Tool"
        assert run.results == []


class TestCreateSarifReport:
    """Test create_sarif_report function."""

    def test_create_sarif_report_basic(self):
        """Test creating basic SARIF report."""
        results = [
            SarifResult("TEST001", "error", "Error message"),
            SarifResult("TEST002", "warning", "Warning message")
        ]
        
        run = SarifRun("AI-Guard", results)
        sarif = create_sarif_report([run])
        
        assert sarif["version"] == "2.1.0"
        assert sarif["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
        assert len(sarif["runs"]) == 1
        
        run_data = sarif["runs"][0]
        assert run_data["tool"]["driver"]["name"] == "AI-Guard"
        assert len(run_data["results"]) == 2

    def test_create_sarif_report_with_metadata(self):
        """Test creating SARIF report with metadata."""
        results = [SarifResult("TEST001", "error", "Error message")]
        run = SarifRun("AI-Guard", results)
        
        metadata = {
            "scan_time": "2023-01-01T00:00:00Z",
            "scanner_version": "1.0.0"
        }
        
        sarif = create_sarif_report([run], metadata)
        
        assert sarif["metadata"] == metadata

    def test_create_sarif_report_multiple_runs(self):
        """Test creating SARIF report with multiple runs."""
        run1 = SarifRun("Tool1", [SarifResult("TEST001", "error", "Error 1")])
        run2 = SarifRun("Tool2", [SarifResult("TEST002", "warning", "Warning 1")])
        
        sarif = create_sarif_report([run1, run2])
        
        assert len(sarif["runs"]) == 2
        assert sarif["runs"][0]["tool"]["driver"]["name"] == "Tool1"
        assert sarif["runs"][1]["tool"]["driver"]["name"] == "Tool2"

    def test_create_sarif_report_with_locations(self):
        """Test creating SARIF report with locations."""
        result = SarifResult(
            "TEST001",
            "error",
            "Error message",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "test.py"},
                    "region": {"startLine": 10}
                }
            }]
        )
        
        run = SarifRun("AI-Guard", [result])
        sarif = create_sarif_report([run])
        
        result_data = sarif["runs"][0]["results"][0]
        assert "locations" in result_data
        assert result_data["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "test.py"

    def test_create_sarif_report_empty_runs(self):
        """Test creating SARIF report with empty runs."""
        sarif = create_sarif_report([])
        
        assert sarif["version"] == "2.1.0"
        assert sarif["runs"] == []

    def test_create_sarif_report_without_metadata(self):
        """Test creating SARIF report without metadata."""
        results = [SarifResult("TEST001", "error", "Error message")]
        run = SarifRun("AI-Guard", results)
        
        sarif = create_sarif_report([run])
        
        assert "metadata" not in sarif


class TestParseIssueToSarif:
    """Test parse_issue_to_sarif function."""

    def test_parse_issue_to_sarif_basic(self):
        """Test parsing basic issue to SARIF."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error message"
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "TEST001"
        assert result.level == "error"
        assert result.message == "Test error message"
        assert result.locations is None

    def test_parse_issue_to_sarif_with_location(self):
        """Test parsing issue with location information."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error message",
            "file": "test.py",
            "line": 10,
            "column": 5
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "TEST001"
        assert result.level == "error"
        assert result.message == "Test error message"
        assert result.locations is not None
        assert len(result.locations) == 1
        
        location = result.locations[0]
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_parse_issue_to_sarif_with_file_only(self):
        """Test parsing issue with file but no line."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error message",
            "file": "test.py"
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.locations is None  # No line information

    def test_parse_issue_to_sarif_with_line_only(self):
        """Test parsing issue with line but no file."""
        issue = {
            "rule_id": "TEST001",
            "level": "error",
            "message": "Test error message",
            "line": 10
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.locations is None  # No file information

    def test_parse_issue_to_sarif_missing_fields(self):
        """Test parsing issue with missing fields."""
        issue = {}
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "unknown"
        assert result.level == "warning"
        assert result.message == "No message provided"

    def test_parse_issue_to_sarif_partial_fields(self):
        """Test parsing issue with partial fields."""
        issue = {
            "rule_id": "TEST001"
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "TEST001"
        assert result.level == "warning"  # Default
        assert result.message == "No message provided"  # Default

    def test_parse_issue_to_sarif_with_none_values(self):
        """Test parsing issue with None values."""
        issue = {
            "rule_id": None,
            "level": None,
            "message": None,
            "file": "test.py",
            "line": 10
        }
        
        result = parse_issue_to_sarif(issue)
        
        assert result.rule_id == "unknown"
        assert result.level == "warning"
        assert result.message == "No message provided"
        assert result.locations is not None


class TestWriteSarif:
    """Test write_sarif function."""

    def test_write_sarif_basic(self):
        """Test writing basic SARIF file."""
        results = [
            SarifResult("TEST001", "error", "Error message"),
            SarifResult("TEST002", "warning", "Warning message")
        ]
        
        run = SarifRun("AI-Guard", results)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name
        
        try:
            write_sarif(temp_path, run)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            assert content["version"] == "2.1.0"
            assert content["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
            assert len(content["runs"]) == 1
            
            run_data = content["runs"][0]
            assert run_data["tool"]["driver"]["name"] == "AI-Guard"
            assert len(run_data["results"]) == 2
        finally:
            os.unlink(temp_path)

    def test_write_sarif_with_locations(self):
        """Test writing SARIF file with locations."""
        result = SarifResult(
            "TEST001",
            "error",
            "Error message",
            locations=[{
                "physicalLocation": {
                    "artifactLocation": {"uri": "test.py"},
                    "region": {"startLine": 10}
                }
            }]
        )
        
        run = SarifRun("AI-Guard", [result])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name
        
        try:
            write_sarif(temp_path, run)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            result_data = content["runs"][0]["results"][0]
            assert "locations" in result_data
            assert result_data["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        finally:
            os.unlink(temp_path)

    def test_write_sarif_empty_results(self):
        """Test writing SARIF file with empty results."""
        run = SarifRun("AI-Guard", [])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name
        
        try:
            write_sarif(temp_path, run)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            assert content["version"] == "2.1.0"
            assert len(content["runs"]) == 1
            assert content["runs"][0]["results"] == []
        finally:
            os.unlink(temp_path)

    def test_write_sarif_file_write_error(self):
        """Test write_sarif with file write error."""
        run = SarifRun("AI-Guard", [SarifResult("TEST001", "error", "Error message")])
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_sarif("/invalid/path/report.sarif", run)

    def test_write_sarif_json_serialization_error(self):
        """Test write_sarif with JSON serialization error."""
        # Create a result with non-serializable data
        result = SarifResult("TEST001", "error", "Error message")
        run = SarifRun("AI-Guard", [result])
        
        with patch('json.dump', side_effect=TypeError("Object not serializable")):
            with pytest.raises(TypeError):
                write_sarif("/tmp/test.sarif", run)


class TestMakeLocation:
    """Test make_location function."""

    def test_make_location_with_file_line_column(self):
        """Test make_location with file, line, and column."""
        location = make_location("test.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_make_location_with_file_line_only(self):
        """Test make_location with file and line only."""
        location = make_location("test.py", 10)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert "startColumn" not in location["physicalLocation"]["region"]

    def test_make_location_with_file_only(self):
        """Test make_location with file only."""
        location = make_location("test.py")
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert "region" not in location["physicalLocation"]

    def test_make_location_with_column_only(self):
        """Test make_location with column only."""
        location = make_location("test.py", None, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startColumn"] == 5
        assert "startLine" not in location["physicalLocation"]["region"]

    def test_make_location_path_normalization(self):
        """Test make_location path normalization."""
        location = make_location("test\\path\\file.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test/path/file.py"

    def test_make_location_with_none_values(self):
        """Test make_location with None values."""
        location = make_location("test.py", None, None)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert "region" not in location["physicalLocation"]

    def test_make_location_with_zero_values(self):
        """Test make_location with zero values."""
        location = make_location("test.py", 0, 0)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 0
        assert location["physicalLocation"]["region"]["startColumn"] == 0

    def test_make_location_with_negative_values(self):
        """Test make_location with negative values."""
        location = make_location("test.py", -1, -1)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == -1
        assert location["physicalLocation"]["region"]["startColumn"] == -1

    def test_make_location_with_large_values(self):
        """Test make_location with large values."""
        location = make_location("test.py", 999999, 999999)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 999999
        assert location["physicalLocation"]["region"]["startColumn"] == 999999

    def test_make_location_with_special_characters(self):
        """Test make_location with special characters in path."""
        location = make_location("test with spaces.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test with spaces.py"

    def test_make_location_with_unicode_path(self):
        """Test make_location with unicode path."""
        location = make_location("tëst.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "tëst.py"


class TestSarifReportIntegration:
    """Test SARIF report integration scenarios."""

    def test_full_sarif_workflow(self):
        """Test complete SARIF workflow."""
        # Create issues
        issues = [
            {
                "rule_id": "TEST001",
                "level": "error",
                "message": "Error message",
                "file": "test.py",
                "line": 10,
                "column": 5
            },
            {
                "rule_id": "TEST002",
                "level": "warning",
                "message": "Warning message",
                "file": "test2.py",
                "line": 20
            }
        ]
        
        # Parse issues to SARIF results
        results = [parse_issue_to_sarif(issue) for issue in issues]
        
        # Create SARIF run
        run = SarifRun("AI-Guard", results)
        
        # Create SARIF report
        sarif = create_sarif_report([run])
        
        # Write to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name
        
        try:
            write_sarif(temp_path, run)
            
            # Verify file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            assert content["version"] == "2.1.0"
            assert len(content["runs"]) == 1
            assert len(content["runs"][0]["results"]) == 2
        finally:
            os.unlink(temp_path)

    def test_sarif_report_with_multiple_tools(self):
        """Test SARIF report with multiple tools."""
        # Create runs for different tools
        bandit_run = SarifRun("Bandit", [SarifResult("B101", "warning", "Hardcoded password")])
        safety_run = SarifRun("Safety", [SarifResult("S001", "error", "Vulnerable dependency")])
        
        # Create combined report
        sarif = create_sarif_report([bandit_run, safety_run])
        
        assert len(sarif["runs"]) == 2
        assert sarif["runs"][0]["tool"]["driver"]["name"] == "Bandit"
        assert sarif["runs"][1]["tool"]["driver"]["name"] == "Safety"

    def test_sarif_report_edge_cases(self):
        """Test SARIF report edge cases."""
        # Test with very long messages
        long_message = "A" * 10000
        result = SarifResult("TEST001", "error", long_message)
        run = SarifRun("AI-Guard", [result])
        
        sarif = create_sarif_report([run])
        assert len(sarif["runs"][0]["results"][0]["message"]["text"]) == 10000

        # Test with special characters
        special_message = "Message with émojis 🎉 and unicode: café"
        result = SarifResult("TEST001", "error", special_message)
        run = SarifRun("AI-Guard", [result])
        
        sarif = create_sarif_report([run])
        assert "émojis" in sarif["runs"][0]["results"][0]["message"]["text"]
        assert "🎉" in sarif["runs"][0]["results"][0]["message"]["text"]
        assert "café" in sarif["runs"][0]["results"][0]["message"]["text"]

    def test_sarif_report_performance(self):
        """Test SARIF report performance with many results."""
        # Create many results
        results = []
        for i in range(1000):
            result = SarifResult(f"TEST{i:03d}", "error", f"Error message {i}")
            results.append(result)
        
        run = SarifRun("AI-Guard", results)
        sarif = create_sarif_report([run])
        
        assert len(sarif["runs"][0]["results"]) == 1000
        assert sarif["runs"][0]["results"][0]["ruleId"] == "TEST000"
        assert sarif["runs"][0]["results"][999]["ruleId"] == "TEST999"