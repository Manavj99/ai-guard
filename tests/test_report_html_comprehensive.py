"""Comprehensive tests for HTML report module."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open

from src.ai_guard.report_html import write_html, HTMLReportGenerator
from src.ai_guard.report import GateResult


class TestWriteHTML:
    """Test write_html function."""

    def test_write_html_all_passed(self):
        """Test writing HTML report with all gates passed."""
        gates = [
            GateResult("Gate1", True, "All good"),
            GateResult("Gate2", True, "Perfect"),
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "ALL GATES PASSED" in content
            assert "Gate1" in content
            assert "Gate2" in content
            assert "All good" in content
            assert "Perfect" in content
            assert "badge pass" in content
            assert "badge fail" not in content
        finally:
            os.unlink(temp_path)

    def test_write_html_some_failed(self):
        """Test writing HTML report with some gates failed."""
        gates = [
            GateResult("Gate1", True, "All good"),
            GateResult("Gate2", False, "Failed check"),
        ]
        findings = [
            {"rule_id": "TEST001", "level": "error", "message": "Test error", "path": "test.py", "line": 10},
            {"rule_id": "TEST002", "level": "warning", "message": "Test warning", "path": "test2.py", "line": 20},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "GATES FAILED" in content
            assert "badge pass" in content
            assert "badge fail" in content
            assert "TEST001" in content
            assert "TEST002" in content
            assert "test.py:10" in content
            assert "test2.py:20" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_no_findings(self):
        """Test writing HTML report with no findings."""
        gates = [
            GateResult("Gate1", True, "All good"),
        ]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "No findings 🎉" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_with_none_values(self):
        """Test writing HTML report with None values in findings."""
        gates = [
            GateResult("Gate1", False, "Failed"),
        ]
        findings = [
            {"rule_id": "TEST001", "level": "error", "message": "Test error", "path": None, "line": None},
            {"rule_id": "TEST002", "level": None, "message": None, "path": "test.py", "line": 10},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "TEST001" in content
            assert "TEST002" in content
            assert "test.py:10" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_html_escaping(self):
        """Test HTML escaping in report."""
        gates = [
            GateResult("Gate with <script>", True, "Details with & symbols"),
        ]
        findings = [
            {"rule_id": "TEST<001>", "level": "error", "message": "Message with \"quotes\"", "path": "test<script>.py", "line": 10},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check that HTML is properly escaped
            assert "&lt;script&gt;" in content
            assert "&amp;" in content
            assert "&quot;" in content
            assert "<script>" not in content
        finally:
            os.unlink(temp_path)

    def test_write_html_file_write_error(self):
        """Test write_html with file write error."""
        gates = [GateResult("Gate1", True, "All good")]
        findings = []
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_html("/invalid/path/report.html", gates, findings)

    def test_write_html_empty_gates(self):
        """Test write_html with empty gates list."""
        gates = []
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "ALL GATES PASSED" in content
            assert "No findings 🎉" in content
        finally:
            os.unlink(temp_path)

    def test_write_html_large_findings(self):
        """Test write_html with large number of findings."""
        gates = [GateResult("Gate1", False, "Failed")]
        findings = []
        
        for i in range(1000):
            findings.append({
                "rule_id": f"TEST{i:03d}",
                "level": "error",
                "message": f"Test error {i}",
                "path": f"test{i}.py",
                "line": i
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "TEST000" in content
            assert "TEST999" in content
            assert "test0.py:0" in content
            assert "test999.py:999" in content
        finally:
            os.unlink(temp_path)


class TestHTMLReportGenerator:
    """Test HTMLReportGenerator class."""

    def test_html_report_generator_init(self):
        """Test HTMLReportGenerator initialization."""
        generator = HTMLReportGenerator()
        assert generator is not None

    def test_generate_html_report(self):
        """Test generate_html_report method."""
        generator = HTMLReportGenerator()
        results = [
            GateResult("Gate1", True, "All good"),
            GateResult("Gate2", False, "Failed"),
        ]
        findings = [
            {"rule_id": "TEST001", "level": "error", "message": "Test error", "path": "test.py", "line": 10},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            generator.generate_html_report(results, findings, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "Gate1" in content
            assert "Gate2" in content
            assert "TEST001" in content
        finally:
            os.unlink(temp_path)

    def test_generate_summary_html_all_passed(self):
        """Test generate_summary_html with all gates passed."""
        generator = HTMLReportGenerator()
        results = [
            GateResult("Gate1", True, "All good"),
            GateResult("Gate2", True, "Perfect"),
        ]
        
        html = generator.generate_summary_html(results)
        
        assert "Total: 2" in html
        assert "Passed: 2" in html
        assert "Failed: 0" in html
        assert "badge pass" in html
        assert "badge fail" not in html

    def test_generate_summary_html_some_failed(self):
        """Test generate_summary_html with some gates failed."""
        generator = HTMLReportGenerator()
        results = [
            GateResult("Gate1", True, "All good"),
            GateResult("Gate2", False, "Failed check"),
            GateResult("Gate3", False, "Another failure"),
        ]
        
        html = generator.generate_summary_html(results)
        
        assert "Total: 3" in html
        assert "Passed: 1" in html
        assert "Failed: 2" in html
        assert "badge pass" in html
        assert "badge fail" in html
        assert "Failed Gates:" in html
        assert "Gate2: Failed check" in html
        assert "Gate3: Another failure" in html

    def test_generate_summary_html_empty_results(self):
        """Test generate_summary_html with empty results."""
        generator = HTMLReportGenerator()
        results = []
        
        html = generator.generate_summary_html(results)
        
        assert "Total: 0" in html
        assert "Passed: 0" in html
        assert "Failed: 0" in html

    def test_generate_summary_html_html_escaping(self):
        """Test HTML escaping in summary generation."""
        generator = HTMLReportGenerator()
        results = [
            GateResult("Gate with <script>", False, "Details with & symbols"),
        ]
        
        html = generator.generate_summary_html(results)
        
        assert "&lt;script&gt;" in html
        assert "&amp;" in html
        assert "<script>" not in html

    def test_generate_html_report_with_mock_write_html(self):
        """Test generate_html_report with mocked write_html."""
        generator = HTMLReportGenerator()
        results = [GateResult("Gate1", True, "All good")]
        findings = []
        
        with patch('src.ai_guard.report_html.write_html') as mock_write_html:
            generator.generate_html_report(results, findings, "/test/path")
            mock_write_html.assert_called_once_with("/test/path", results, findings)

    def test_html_report_generator_edge_cases(self):
        """Test HTMLReportGenerator edge cases."""
        generator = HTMLReportGenerator()
        
        # Test with results containing None details
        results = [
            GateResult("Gate1", True, None),
            GateResult("Gate2", False, ""),
        ]
        
        html = generator.generate_summary_html(results)
        
        assert "Gate1" in html
        assert "Gate2" in html
        assert "None" not in html  # Should handle None gracefully

    def test_html_report_generator_large_results(self):
        """Test HTMLReportGenerator with large number of results."""
        generator = HTMLReportGenerator()
        results = []
        
        for i in range(100):
            results.append(GateResult(f"Gate{i}", i % 2 == 0, f"Details {i}"))
        
        html = generator.generate_summary_html(results)
        
        assert "Total: 100" in html
        assert "Passed: 50" in html
        assert "Failed: 50" in html

    def test_html_report_generator_findings_edge_cases(self):
        """Test HTMLReportGenerator with edge case findings."""
        generator = HTMLReportGenerator()
        results = [GateResult("Gate1", False, "Failed")]
        
        # Test with various finding formats
        findings = [
            {"rule_id": "TEST001", "level": "error", "message": "Test error", "path": "test.py", "line": 10},
            {"rule_id": "TEST002", "level": "warning", "message": "Test warning", "path": "test2.py", "line": 20},
            {"rule_id": "TEST003", "level": "note", "message": "Test note", "path": "test3.py", "line": 30},
            {"rule_id": "TEST004", "level": "info", "message": "Test info", "path": "test4.py", "line": 40},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            generator.generate_html_report(results, findings, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "TEST001" in content
            assert "TEST002" in content
            assert "TEST003" in content
            assert "TEST004" in content
            assert "ERROR" in content
            assert "WARNING" in content
            assert "NOTE" in content
            assert "INFO" in content
        finally:
            os.unlink(temp_path)

    def test_html_report_generator_css_styles(self):
        """Test that CSS styles are included in generated HTML."""
        generator = HTMLReportGenerator()
        results = [GateResult("Gate1", True, "All good")]
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            generator.generate_html_report(results, findings, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check that CSS styles are included
            assert "font-family" in content
            assert "badge" in content
            assert "table" in content
            assert "border-collapse" in content
        finally:
            os.unlink(temp_path)

    def test_html_report_generator_unicode_content(self):
        """Test HTMLReportGenerator with unicode content."""
        generator = HTMLReportGenerator()
        results = [
            GateResult("Gate with émojis 🎉", True, "Unicode details: café, naïve"),
        ]
        findings = [
            {"rule_id": "TEST001", "level": "error", "message": "Unicode message: café", "path": "tëst.py", "line": 10},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            generator.generate_html_report(results, findings, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "émojis" in content
            assert "café" in content
            assert "naïve" in content
            assert "tëst.py" in content
        finally:
            os.unlink(temp_path)