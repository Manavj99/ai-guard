"""Tests for the report_json module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from src.ai_guard.report_json import write_json
from src.ai_guard.report import GateResult


class TestWriteJson:
    """Test write_json function."""
    
    def test_write_json_all_passed(self):
        """Test write_json with all gates passed."""
        gates = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed")
        ]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "file.py", "line": 10},
            {"rule_id": "W293", "level": "warning", "message": "Blank line contains whitespace", "path": "file.py", "line": 5}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is True
            assert len(data["summary"]["gates"]) == 2
            assert data["summary"]["gates"][0]["name"] == "gate1"
            assert data["summary"]["gates"][0]["passed"] is True
            assert data["summary"]["gates"][0]["details"] == "Passed"
            assert data["summary"]["gates"][1]["name"] == "gate2"
            assert data["summary"]["gates"][1]["passed"] is True
            assert data["summary"]["gates"][1]["details"] == "Also passed"
            assert len(data["findings"]) == 2
            assert data["findings"][0]["rule_id"] == "E501"
            assert data["findings"][0]["level"] == "error"
            assert data["findings"][0]["message"] == "Line too long"
            assert data["findings"][0]["path"] == "file.py"
            assert data["findings"][0]["line"] == 10
        finally:
            Path(report_path).unlink()
    
    def test_write_json_some_failed(self):
        """Test write_json with some gates failed."""
        gates = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
            GateResult("gate3", True, "Passed")
        ]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "file.py", "line": 10}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is False
            assert len(data["summary"]["gates"]) == 3
            assert data["summary"]["gates"][0]["passed"] is True
            assert data["summary"]["gates"][1]["passed"] is False
            assert data["summary"]["gates"][1]["details"] == "Failed"
            assert data["summary"]["gates"][2]["passed"] is True
            assert len(data["findings"]) == 1
        finally:
            Path(report_path).unlink()
    
    def test_write_json_all_failed(self):
        """Test write_json with all gates failed."""
        gates = [
            GateResult("gate1", False, "Failed 1"),
            GateResult("gate2", False, "Failed 2")
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is False
            assert len(data["summary"]["gates"]) == 2
            assert data["summary"]["gates"][0]["passed"] is False
            assert data["summary"]["gates"][1]["passed"] is False
            assert len(data["findings"]) == 0
        finally:
            Path(report_path).unlink()
    
    def test_write_json_empty_gates(self):
        """Test write_json with empty gates list."""
        gates = []
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "file.py", "line": 10}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is True  # Empty list means all passed
            assert len(data["summary"]["gates"]) == 0
            assert len(data["findings"]) == 1
        finally:
            Path(report_path).unlink()
    
    def test_write_json_gates_with_empty_details(self):
        """Test write_json with gates that have empty details."""
        gates = [
            GateResult("gate1", True, ""),
            GateResult("gate2", False, "")
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is False
            assert len(data["summary"]["gates"]) == 2
            assert data["summary"]["gates"][0]["details"] == ""
            assert data["summary"]["gates"][1]["details"] == ""
        finally:
            Path(report_path).unlink()
    
    def test_write_json_gates_with_none_details(self):
        """Test write_json with gates that have None details."""
        gates = [
            GateResult("gate1", True, None),
            GateResult("gate2", False, None)
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is False
            assert len(data["summary"]["gates"]) == 2
            assert data["summary"]["gates"][0]["details"] == ""
            assert data["summary"]["gates"][1]["details"] == ""
        finally:
            Path(report_path).unlink()
    
    def test_write_json_complex_findings(self):
        """Test write_json with complex findings."""
        gates = [GateResult("gate1", True, "Passed")]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "file1.py", "line": 10},
            {"rule_id": "W293", "level": "warning", "message": "Blank line contains whitespace", "path": "file2.py", "line": 5},
            {"rule_id": "F401", "level": "error", "message": "Imported but unused", "path": "file3.py", "line": 1, "extra": "field"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            write_json(report_path, gates, findings)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is True
            assert len(data["findings"]) == 3
            assert data["findings"][2]["extra"] == "field"  # Extra fields should be preserved
        finally:
            Path(report_path).unlink()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_write_json_file_operations(self, mock_json_dump, mock_file):
        """Test write_json file operations."""
        gates = [GateResult("gate1", True, "Passed")]
        findings = [{"rule_id": "E501", "level": "error", "message": "Line too long", "path": "file.py", "line": 10}]
        
        write_json("test.json", gates, findings)
        
        mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()
        
        # Check the payload structure
        call_args = mock_json_dump.call_args
        payload = call_args[0][0]
        
        assert payload["version"] == "1.0"
        assert payload["summary"]["passed"] is True
        assert len(payload["summary"]["gates"]) == 1
        assert len(payload["findings"]) == 1