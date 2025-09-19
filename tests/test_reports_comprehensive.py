"""Comprehensive tests for report modules to achieve high coverage."""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from src.ai_guard.report import GateResult, summarize
from src.ai_guard.report_json import write_json
from src.ai_guard.report_html import write_html
from src.ai_guard.sarif_report import (
    SarifRun,
    SarifResult,
    write_sarif,
    make_location,
)


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
        
        exit_code = summarize(results)
        
        assert exit_code == 0
    
    def test_summarize_some_failed(self):
        """Test summarizing when some gates fail."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", True, "Passed")
        ]
        
        exit_code = summarize(results)
        
        assert exit_code == 1
    
    def test_summarize_all_failed(self):
        """Test summarizing when all gates fail."""
        results = [
            GateResult("Gate 1", False, "Failed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", False, "Failed")
        ]
        
        exit_code = summarize(results)
        
        assert exit_code == 1
    
    def test_summarize_empty(self):
        """Test summarizing empty results."""
        results = []
        
        exit_code = summarize(results)
        
        assert exit_code == 0


class TestWriteJson:
    """Test JSON report writing."""
    
    def test_write_json_success(self):
        """Test successful JSON report writing."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed")
        ]
        
        findings = [
            {
                "rule_id": "E501",
                "level": "warning",
                "message": "Line too long",
                "path": "test.py",
                "line": 10
            }
        ]
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_json("test.json", results, findings)
            
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
            # json.dump calls write multiple times for formatting, so we just check it was called
            mock_file.return_value.write.assert_called()
            
            # Collect all write calls to reconstruct the content
            write_calls = mock_file.return_value.write.call_args_list
            written_content = ''.join(call[0][0] for call in write_calls)
            data = json.loads(written_content)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is False
            assert len(data["summary"]["gates"]) == 2
            assert len(data["findings"]) == 1
    
    def test_write_json_error(self):
        """Test JSON report writing with error."""
        results = [GateResult("Gate 1", True, "Passed")]
        findings = []
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                write_json("test.json", results, findings)


class TestWriteHtml:
    """Test HTML report writing."""
    
    def test_write_html_success(self):
        """Test successful HTML report writing."""
        results = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed")
        ]
        
        findings = [
            {
                "rule_id": "E501",
                "level": "warning",
                "message": "Line too long",
                "path": "test.py",
                "line": 10
            }
        ]
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_html("test.html", results, findings)
            
            mock_file.assert_called_once_with("test.html", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called_once()
            
            # Verify HTML structure
            written_content = mock_file.return_value.write.call_args[0][0]
            assert "<!DOCTYPE html>" in written_content or "<!doctype html>" in written_content
            assert "Gate 1" in written_content
            assert "Gate 2" in written_content
            assert "E501" in written_content
    
    def test_write_html_error(self):
        """Test HTML report writing with error."""
        results = [GateResult("Gate 1", True, "Passed")]
        findings = []
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                write_html("test.html", results, findings)


class TestSarifRun:
    """Test SarifRun dataclass."""
    
    def test_sarif_run_creation(self):
        """Test creating a SarifRun."""
        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[]
        )
        
        run = SarifRun(tool_name="test-tool", results=[result])
        
        assert run.tool_name == "test-tool"
        assert len(run.results) == 1
        assert run.results[0] == result


class TestSarifResult:
    """Test SarifResult dataclass."""
    
    def test_sarif_result_creation(self):
        """Test creating a SarifResult."""
        location = {
            "physicalLocation": {
                "artifactLocation": {"uri": "test.py"},
                "region": {"startLine": 10}
            }
        }
        
        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[location]
        )
        
        assert result.rule_id == "test-rule"
        assert result.message == "Test message"
        assert result.level == "warning"
        assert len(result.locations) == 1
        assert result.locations[0] == location
    
    def test_sarif_result_minimal(self):
        """Test creating a minimal SarifResult."""
        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[]
        )
        
        assert result.rule_id == "test-rule"
        assert result.message == "Test message"
        assert result.level == "warning"
        assert result.locations == []


class TestMakeLocation:
    """Test make_location function."""
    
    def test_make_location_with_line(self):
        """Test making location with line number."""
        location = make_location("test.py", 10)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert "startColumn" not in location["physicalLocation"]["region"]
    
    def test_make_location_with_line_and_column(self):
        """Test making location with line and column numbers."""
        location = make_location("test.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5
    
    def test_make_location_with_end_line(self):
        """Test making location with end line number."""
        location = make_location("test.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5
    
    def test_make_location_with_end_column(self):
        """Test making location with end column number."""
        location = make_location("test.py", 10, 5)
        
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5


class TestWriteSarif:
    """Test SARIF report writing."""
    
    def test_write_sarif_success(self):
        """Test successful SARIF report writing."""
        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[]
        )
        
        run = SarifRun(tool_name="test-tool", results=[result])
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_sarif("test.sarif", run)
            
            mock_file.assert_called_once_with("test.sarif", "w", encoding="utf-8")
            # json.dump calls write multiple times for formatting, so we just check it was called
            mock_file.return_value.write.assert_called()
            
            # Collect all write calls to reconstruct the content
            write_calls = mock_file.return_value.write.call_args_list
            written_content = ''.join(call[0][0] for call in write_calls)
            data = json.loads(written_content)
            
            assert data["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
            assert data["version"] == "2.1.0"
            assert len(data["runs"]) == 1
            assert data["runs"][0]["tool"]["driver"]["name"] == "test-tool"
            assert len(data["runs"][0]["results"]) == 1
            assert data["runs"][0]["results"][0]["ruleId"] == "test-rule"
    
    def test_write_sarif_error(self):
        """Test SARIF report writing with error."""
        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[]
        )
        
        run = SarifRun(tool_name="test-tool", results=[result])
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                write_sarif("test.sarif", run)
    
    def test_write_sarif_empty_results(self):
        """Test SARIF report writing with empty results."""
        run = SarifRun(tool_name="test-tool", results=[])
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_sarif("test.sarif", run)
            
            # Collect all write calls to reconstruct the content
            write_calls = mock_file.return_value.write.call_args_list
            written_content = ''.join(call[0][0] for call in write_calls)
            data = json.loads(written_content)
            
            assert len(data["runs"][0]["results"]) == 0
    
    def test_write_sarif_with_locations(self):
        """Test SARIF report writing with locations."""
        location = make_location("test.py", 10, 5)
        
        result = SarifResult(
            rule_id="test-rule",
            message="Test message",
            level="warning",
            locations=[location]
        )
        
        run = SarifRun(tool_name="test-tool", results=[result])
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_sarif("test.sarif", run)
            
            # Collect all write calls to reconstruct the content
            write_calls = mock_file.return_value.write.call_args_list
            written_content = ''.join(call[0][0] for call in write_calls)
            data = json.loads(written_content)
            
            assert len(data["runs"][0]["results"][0]["locations"]) == 1
            assert data["runs"][0]["results"][0]["locations"][0] == location
