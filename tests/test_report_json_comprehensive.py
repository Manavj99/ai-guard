"""Comprehensive tests for report_json module."""

import pytest
from unittest.mock import patch, mock_open
import json
import tempfile
import os

from src.ai_guard.report_json import write_json
from src.ai_guard.report import GateResult


class TestWriteJson:
    """Test write_json function."""

    def test_write_json_basic(self):
        """Test basic JSON report writing."""
        gates = [
            GateResult(name="coverage", passed=True, details="85% coverage"),
            GateResult(name="linting", passed=False, details="3 errors found")
        ]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "test.py", "line": 10},
            {"rule_id": "W293", "level": "warning", "message": "Trailing whitespace", "path": "test.py", "line": 15}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            write_json(tmp_path, gates, findings)
            
            # Read and verify the written content
            with open(tmp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["version"] == "1.0"
            assert data["summary"]["passed"] is False  # One gate failed
            assert len(data["summary"]["gates"]) == 2
            assert data["summary"]["gates"][0]["name"] == "coverage"
            assert data["summary"]["gates"][0]["passed"] is True
            assert data["summary"]["gates"][0]["details"] == "85% coverage"
            assert data["summary"]["gates"][1]["name"] == "linting"
            assert data["summary"]["gates"][1]["passed"] is False
            assert data["summary"]["gates"][1]["details"] == "3 errors found"
            assert data["findings"] == findings
        finally:
            os.unlink(tmp_path)

    def test_write_json_all_passed(self):
        """Test JSON report writing when all gates pass."""
        gates = [
            GateResult(name="coverage", passed=True, details="90% coverage"),
            GateResult(name="linting", passed=True, details="No issues found")
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["summary"]["passed"] is True
            assert data["findings"] == []
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_empty_gates(self):
        """Test JSON report writing with empty gates list."""
        gates = []
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["summary"]["passed"] is True
            assert data["summary"]["gates"] == []
            assert data["findings"] == []
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_gates_with_none_details(self):
        """Test JSON report writing with gates having None details."""
        gates = [
            GateResult(name="coverage", passed=True, details=None),
            GateResult(name="linting", passed=False, details=None)
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["summary"]["gates"][0]["details"] == ""
            assert data["summary"]["gates"][1]["details"] == ""
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_gates_with_empty_details(self):
        """Test JSON report writing with gates having empty details."""
        gates = [
            GateResult(name="coverage", passed=True, details=""),
            GateResult(name="linting", passed=False, details="")
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["summary"]["gates"][0]["details"] == ""
            assert data["summary"]["gates"][1]["details"] == ""
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_complex_findings(self):
        """Test JSON report writing with complex findings."""
        gates = [GateResult(name="test", passed=True)]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "test.py", "line": 10},
            {"rule_id": "W293", "level": "warning", "message": "Trailing whitespace", "path": "test.py", "line": 15},
            {"rule_id": "B101", "level": "error", "message": "Use of assert detected", "path": "test.py", "line": 20},
            {"rule_id": "F401", "level": "error", "message": "Imported but unused", "path": "test.py", "line": 5}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data["findings"]) == 4
            assert data["findings"] == findings
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_findings_with_none_values(self):
        """Test JSON report writing with findings containing None values."""
        gates = [GateResult(name="test", passed=True)]
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "test.py", "line": 10},
            {"rule_id": "W293", "level": "warning", "message": None, "path": None, "line": None},
            {"rule_id": None, "level": None, "message": "Some issue", "path": "test.py", "line": 5}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data["findings"]) == 3
            assert data["findings"] == findings
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_different_file_paths(self):
        """Test JSON report writing to different file paths."""
        gates = [GateResult(name="test", passed=True)]
        findings = []
        
        test_paths = [
            "report.json",
            "reports/coverage.json",
            "/tmp/report.json",
            "reports/2024/01/15/report.json",
            "report with spaces.json"
        ]
        
        for path in test_paths:
            with patch('builtins.open', mock_open()) as mock_file:
                write_json(path, gates, findings)
                mock_file.assert_called_once_with(path, "w", encoding="utf-8")

    def test_write_json_encoding(self):
        """Test JSON report writing with proper encoding."""
        gates = [GateResult(name="test", passed=True)]
        findings = [{"rule_id": "E501", "level": "error", "message": "测试消息", "path": "测试.py", "line": 10}]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["findings"][0]["message"] == "测试消息"
            assert data["findings"][0]["path"] == "测试.py"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_indentation(self):
        """Test JSON report writing with proper indentation."""
        gates = [GateResult(name="test", passed=True)]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check that the JSON is properly formatted with indentation
            lines = content.split('\n')
            assert len(lines) > 1  # Should have multiple lines due to indentation
            assert '  "version": "1.0",' in lines  # Should have 2-space indentation
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_large_data(self):
        """Test JSON report writing with large amounts of data."""
        gates = [GateResult(name=f"gate_{i}", passed=i % 2 == 0, details=f"Details for gate {i}") for i in range(100)]
        findings = [{"rule_id": f"E{i:03d}", "level": "error", "message": f"Error {i}", "path": f"file{i}.py", "line": i} for i in range(1000)]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data["summary"]["gates"]) == 100
            assert len(data["findings"]) == 1000
            assert data["summary"]["passed"] is False  # Some gates should fail
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_mixed_gate_results(self):
        """Test JSON report writing with mixed gate results."""
        gates = [
            GateResult(name="coverage", passed=True, details="85% coverage", exit_code=0),
            GateResult(name="linting", passed=False, details="3 errors found", exit_code=1),
            GateResult(name="security", passed=True, details="No vulnerabilities", exit_code=0),
            GateResult(name="tests", passed=False, details="2 tests failed", exit_code=2)
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["summary"]["passed"] is False
            assert len(data["summary"]["gates"]) == 4
            assert data["summary"]["gates"][0]["passed"] is True
            assert data["summary"]["gates"][1]["passed"] is False
            assert data["summary"]["gates"][2]["passed"] is True
            assert data["summary"]["gates"][3]["passed"] is False
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_write_json_io_error(self):
        """Test JSON report writing with IO error."""
        gates = [GateResult(name="test", passed=True)]
        findings = []
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError, match="Permission denied"):
                write_json("report.json", gates, findings)

    def test_write_json_json_serialization_error(self):
        """Test JSON report writing with non-serializable data."""
        gates = [GateResult(name="test", passed=True)]
        findings = [{"rule_id": "E501", "level": "error", "message": "Test", "path": "test.py", "line": 10, "non_serializable": object()}]
        
        with patch('builtins.open', mock_open()):
            with pytest.raises(TypeError):
                write_json("report.json", gates, findings)

    def test_write_json_empty_string_path(self):
        """Test JSON report writing with empty string path."""
        gates = [GateResult(name="test", passed=True)]
        findings = []
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_json("", gates, findings)
            mock_file.assert_called_once_with("", "w", encoding="utf-8")

    def test_write_json_very_long_details(self):
        """Test JSON report writing with very long details."""
        long_details = "x" * 10000
        gates = [GateResult(name="test", passed=True, details=long_details)]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["summary"]["gates"][0]["details"] == long_details
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_json_special_characters_in_names(self):
        """Test JSON report writing with special characters in gate names."""
        gates = [
            GateResult(name="gate-with-dashes", passed=True),
            GateResult(name="gate_with_underscores", passed=True),
            GateResult(name="gate.with.dots", passed=True),
            GateResult(name="gate with spaces", passed=True)
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            write_json(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data["summary"]["gates"]) == 4
            assert data["summary"]["gates"][0]["name"] == "gate-with-dashes"
            assert data["summary"]["gates"][1]["name"] == "gate_with_underscores"
            assert data["summary"]["gates"][2]["name"] == "gate.with.dots"
            assert data["summary"]["gates"][3]["name"] == "gate with spaces"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
