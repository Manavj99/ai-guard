"""Comprehensive tests for report modules to achieve high coverage."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.ai_guard.report import GateResult, summarize
from src.ai_guard.report_json import write_json
from src.ai_guard.report_html import write_html
from src.ai_guard.sarif_report import SarifRun, SarifResult, write_sarif, make_location


class TestGateResult:
    """Test GateResult class."""
    
    def test_gate_result_creation(self):
        """Test creating GateResult."""
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
    
    def test_gate_result_failed(self):
        """Test creating failed GateResult."""
        result = GateResult(
            name="test_gate",
            passed=False,
            message="Test failed",
            details={"error": "Something went wrong"}
        )
        assert result.name == "test_gate"
        assert result.passed is False
        assert result.message == "Test failed"
        assert result.details == {"error": "Something went wrong"}
    
    def test_gate_result_minimal(self):
        """Test creating minimal GateResult."""
        result = GateResult(name="test_gate", passed=True)
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.message is None
        assert result.details is None


class TestSummarize:
    """Test summarize function."""
    
    def test_summarize_empty_results(self):
        """Test summarizing empty results."""
        summary = summarize([])
        assert summary.total_gates == 0
        assert summary.passed_gates == 0
        assert summary.failed_gates == 0
        assert summary.success_rate == 0.0
    
    def test_summarize_all_passed(self):
        """Test summarizing all passed results."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Passed"),
            GateResult("gate3", True, "Passed")
        ]
        summary = summarize(results)
        assert summary.total_gates == 3
        assert summary.passed_gates == 3
        assert summary.failed_gates == 0
        assert summary.success_rate == 100.0
    
    def test_summarize_all_failed(self):
        """Test summarizing all failed results."""
        results = [
            GateResult("gate1", False, "Failed"),
            GateResult("gate2", False, "Failed")
        ]
        summary = summarize(results)
        assert summary.total_gates == 2
        assert summary.passed_gates == 0
        assert summary.failed_gates == 2
        assert summary.success_rate == 0.0
    
    def test_summarize_mixed_results(self):
        """Test summarizing mixed results."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", True, "Passed"),
            GateResult("gate4", False, "Failed")
        ]
        summary = summarize(results)
        assert summary.total_gates == 4
        assert summary.passed_gates == 2
        assert summary.failed_gates == 2
        assert summary.success_rate == 50.0
    
    def test_summarize_with_details(self):
        """Test summarizing results with details."""
        results = [
            GateResult("gate1", True, "Passed", {"coverage": 85.0}),
            GateResult("gate2", False, "Failed", {"error": "Low coverage"})
        ]
        summary = summarize(results)
        assert summary.total_gates == 2
        assert summary.passed_gates == 1
        assert summary.failed_gates == 1
        assert summary.success_rate == 50.0


class TestWriteJson:
    """Test write_json function."""
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_json_basic(self, mock_file):
        """Test basic JSON writing."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed")
        ]
        
        write_json(results, "output.json")
        mock_file.assert_called_once_with("output.json", "w")
        
        # Check that JSON was written
        written_content = mock_file.return_value.write.call_args[0][0]
        data = json.loads(written_content)
        assert len(data["results"]) == 2
        assert data["results"][0]["name"] == "gate1"
        assert data["results"][0]["passed"] is True
        assert data["results"][1]["name"] == "gate2"
        assert data["results"][1]["passed"] is False
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_json_with_summary(self, mock_file):
        """Test JSON writing with summary."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Passed")
        ]
        
        write_json(results, "output.json", include_summary=True)
        written_content = mock_file.return_value.write.call_args[0][0]
        data = json.loads(written_content)
        
        assert "summary" in data
        assert data["summary"]["total_gates"] == 2
        assert data["summary"]["passed_gates"] == 2
        assert data["summary"]["success_rate"] == 100.0
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_json_with_metadata(self, mock_file):
        """Test JSON writing with metadata."""
        results = [GateResult("gate1", True, "Passed")]
        metadata = {"version": "1.0", "timestamp": "2023-01-01"}
        
        write_json(results, "output.json", metadata=metadata)
        written_content = mock_file.return_value.write.call_args[0][0]
        data = json.loads(written_content)
        
        assert data["metadata"]["version"] == "1.0"
        assert data["metadata"]["timestamp"] == "2023-01-01"
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_write_json_permission_error(self, mock_file):
        """Test JSON writing with permission error."""
        results = [GateResult("gate1", True, "Passed")]
        
        # Should not raise exception
        write_json(results, "/restricted/output.json")


class TestWriteHtml:
    """Test write_html function."""
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_html_basic(self, mock_file):
        """Test basic HTML writing."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed")
        ]
        
        write_html(results, "output.html")
        mock_file.assert_called_once_with("output.html", "w")
        
        # Check that HTML was written
        written_content = mock_file.return_value.write.call_args[0][0]
        assert "<html>" in written_content
        assert "gate1" in written_content
        assert "gate2" in written_content
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_html_with_title(self, mock_file):
        """Test HTML writing with custom title."""
        results = [GateResult("gate1", True, "Passed")]
        
        write_html(results, "output.html", title="Custom Title")
        written_content = mock_file.return_value.write.call_args[0][0]
        assert "Custom Title" in written_content
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_html_with_styles(self, mock_file):
        """Test HTML writing with custom styles."""
        results = [GateResult("gate1", True, "Passed")]
        
        write_html(results, "output.html", include_styles=True)
        written_content = mock_file.return_value.write.call_args[0][0]
        assert "<style>" in written_content
    
    @patch('builtins.open', side_effect=OSError("Disk full"))
    def test_write_html_io_error(self, mock_file):
        """Test HTML writing with IO error."""
        results = [GateResult("gate1", True, "Passed")]
        
        # Should not raise exception
        write_html(results, "output.html")


class TestSarifRun:
    """Test SarifRun class."""
    
    def test_sarif_run_creation(self):
        """Test creating SarifRun."""
        run = SarifRun(tool_name="ai-guard", tool_version="1.0.0")
        assert run.tool_name == "ai-guard"
        assert run.tool_version == "1.0.0"
        assert run.results == []
    
    def test_sarif_run_add_result(self):
        """Test adding result to SarifRun."""
        run = SarifRun(tool_name="ai-guard", tool_version="1.0.0")
        result = SarifResult(
            rule_id="E501",
            message="Line too long",
            level="error"
        )
        run.add_result(result)
        assert len(run.results) == 1
        assert run.results[0] == result


class TestSarifResult:
    """Test SarifResult class."""
    
    def test_sarif_result_creation(self):
        """Test creating SarifResult."""
        result = SarifResult(
            rule_id="E501",
            message="Line too long",
            level="error"
        )
        assert result.rule_id == "E501"
        assert result.message == "Line too long"
        assert result.level == "error"
    
    def test_sarif_result_with_location(self):
        """Test creating SarifResult with location."""
        location = make_location("test.py", 10, 5)
        result = SarifResult(
            rule_id="E501",
            message="Line too long",
            level="error",
            locations=[location]
        )
        assert result.rule_id == "E501"
        assert len(result.locations) == 1
        assert result.locations[0] == location


class TestMakeLocation:
    """Test make_location function."""
    
    def test_make_location_basic(self):
        """Test creating basic location."""
        location = make_location("test.py", 10, 5)
        assert location.physical_location.artifact_location.uri == "test.py"
        assert location.physical_location.region.start_line == 10
        assert location.physical_location.region.end_line == 10
    
    def test_make_location_with_end_line(self):
        """Test creating location with end line."""
        location = make_location("test.py", 10, 5, end_line=15)
        assert location.physical_location.region.start_line == 10
        assert location.physical_location.region.end_line == 15
    
    def test_make_location_with_column(self):
        """Test creating location with column."""
        location = make_location("test.py", 10, 5, end_column=20)
        assert location.physical_location.region.start_column == 5
        assert location.physical_location.region.end_column == 20


class TestWriteSarif:
    """Test write_sarif function."""
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_sarif_basic(self, mock_file):
        """Test basic SARIF writing."""
        run = SarifRun(tool_name="ai-guard", tool_version="1.0.0")
        result = SarifResult(
            rule_id="E501",
            message="Line too long",
            level="error"
        )
        run.add_result(result)
        
        write_sarif([run], "output.sarif")
        mock_file.assert_called_once_with("output.sarif", "w")
        
        # Check that SARIF was written
        written_content = mock_file.return_value.write.call_args[0][0]
        data = json.loads(written_content)
        assert data["$schema"] == "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
        assert data["version"] == "2.1.0"
        assert len(data["runs"]) == 1
        assert data["runs"][0]["tool"]["driver"]["name"] == "ai-guard"
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_sarif_multiple_runs(self, mock_file):
        """Test SARIF writing with multiple runs."""
        run1 = SarifRun(tool_name="ai-guard", tool_version="1.0.0")
        run2 = SarifRun(tool_name="ai-guard", tool_version="1.0.0")
        
        write_sarif([run1, run2], "output.sarif")
        written_content = mock_file.return_value.write.call_args[0][0]
        data = json.loads(written_content)
        assert len(data["runs"]) == 2
    
    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_write_sarif_io_error(self, mock_file):
        """Test SARIF writing with IO error."""
        run = SarifRun(tool_name="ai-guard", tool_version="1.0.0")
        
        # Should not raise exception
        write_sarif([run], "output.sarif")
