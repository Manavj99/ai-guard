"""Comprehensive tests for analyzer module to improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from src.ai_guard.analyzer import (
    run_lint_check,
    run_type_check, 
    run_security_check,
    run_coverage_check,
    _coverage_percent_from_xml,
    main
)
from src.ai_guard.gates.coverage_eval import CoverageResult, evaluate_coverage_str, _percent_from_root


class TestAnalyzerFunctions:
    """Test analyzer functions for better coverage."""

    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"No issues found"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_lint_check(["src/test.py"])
        assert result.passed is True
        assert "No issues" in result.details

    @patch('subprocess.run')
    def test_run_lint_check_failure(self, mock_run):
        """Test failed lint check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b"src/test.py:10:5: E501 line too long (80 > 79 characters)"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_lint_check(["src/test.py"])
        assert result.passed is False
        assert "line too long" in result.details

    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"Success: no issues found"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_type_check(["src/test.py"])
        assert result.passed is True
        assert "No issues" in result.details

    @patch('subprocess.run')
    def test_run_type_check_failure(self, mock_run):
        """Test failed type check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b"src/test.py:10: error: Argument 1 to \"func\" has incompatible type \"str\"; expected \"int\" [arg-type]"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_type_check(["src/test.py"])
        assert result.passed is False
        assert "incompatible type" in result.details

    def test_run_security_check_success(self):
        """Test successful security check."""
        with patch('src.ai_guard.security_scanner.SecurityScanner') as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.run_all_security_checks.return_value = 0
            mock_scanner.return_value = mock_instance

            result, sarif_result = run_security_check()
            assert result.passed is True
            assert "No issues" in result.details

    @patch('subprocess.run')
    def test_run_security_check_failure(self, mock_run):
        """Test failed security check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b'{"results": [{"filename": "test.py", "line_number": 10, "issue_text": "Use of insecure random generator", "test_id": "B311"}]}'
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        result, sarif_result = run_security_check()
        assert result.passed is False

    @patch('subprocess.run')
    def test_run_coverage_check_success(self, mock_run):
        """Test successful coverage check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"Coverage: 85%"
        mock_run.return_value = mock_result

        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=85.0):
            result, sarif_result = run_coverage_check(80)
            assert result.passed is True
            assert "85.0%" in result.details

    @patch('subprocess.run')
    def test_run_coverage_check_failure(self, mock_run):
        """Test failed coverage check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"Coverage: 75%"
        mock_run.return_value = mock_result

        with patch('src.ai_guard.analyzer._coverage_percent_from_xml', return_value=75.0):
            result, sarif_result = run_coverage_check(80)
            assert result.passed is False
            assert "75.0%" in result.details

    def test_coverage_percent_from_xml_valid(self):
        """Test coverage percentage extraction from valid XML."""
        xml_content = '''<?xml version="1.0" ?>
<coverage version="6.0.2" timestamp="1234567890">
    <counter type="LINE" missed="20" covered="80"/>
</coverage>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            temp_path = f.name
        
        try:
            result = _coverage_percent_from_xml(temp_path)
            assert result == 80.0
        finally:
            os.unlink(temp_path)

    def test_coverage_percent_from_xml_invalid_file(self):
        """Test coverage percentage extraction from invalid file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None

    def test_coverage_percent_from_xml_invalid_xml(self):
        """Test coverage percentage extraction from invalid XML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("invalid xml content")
            temp_path = f.name

        try:
            result = _coverage_percent_from_xml(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    @patch('sys.argv', ['analyzer', '--help'])
    def test_main_help(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit):
            main()

    @patch('sys.argv', ['analyzer', '--version'])
    def test_main_version(self):
        """Test main function with version argument."""
        with pytest.raises(SystemExit):
            main()


class TestCoverageEvaluation:
    """Test coverage evaluation functions for better coverage."""

    def test_coverage_result(self):
        """Test CoverageResult creation."""
        result = CoverageResult(passed=True, percent=85.0)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_success(self):
        """Test successful coverage evaluation from XML string."""
        xml_content = '''<?xml version="1.0" ?>
<coverage version="6.0.2" timestamp="1234567890" line-rate="0.85">
    <counter type="LINE" missed="20" covered="80"/>
</coverage>'''
        
        result = evaluate_coverage_str(xml_content, 80.0)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_failure(self):
        """Test failed coverage evaluation from XML string."""
        xml_content = '''<?xml version="1.0" ?>
<coverage version="6.0.2" timestamp="1234567890" line-rate="0.75">
    <counter type="LINE" missed="30" covered="70"/>
</coverage>'''
        
        result = evaluate_coverage_str(xml_content, 80.0)
        assert result.passed is False
        assert result.percent == 75.0

    def test_percent_from_root_line_rate(self):
        """Test _percent_from_root with line-rate attribute."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "0.85"
        
        result = _percent_from_root(root)
        assert result == 85.0

    def test_percent_from_root_lines_valid_covered(self):
        """Test _percent_from_root with lines-valid and lines-covered."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "100"
        root.attrib["lines-covered"] = "80"
        
        result = _percent_from_root(root)
        assert result == 80.0

    def test_percent_from_root_counters(self):
        """Test _percent_from_root with counter elements."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("coverage")
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "LINE"
        counter.attrib["covered"] = "80"
        counter.attrib["missed"] = "20"
        
        result = _percent_from_root(root)
        assert result == 80.0

    def test_percent_from_root_no_data(self):
        """Test _percent_from_root with no coverage data."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("coverage")
        result = _percent_from_root(root)
        assert result == 0.0
