"""Comprehensive tests for coverage evaluation module."""

import pytest
from src.ai_guard.gates.coverage_eval import (
    CoverageResult,
    evaluate_coverage_str,
    _percent_from_root
)
import xml.etree.ElementTree as ET


class TestCoverageResult:
    """Test CoverageResult dataclass."""

    def test_coverage_result_creation(self):
        """Test creating CoverageResult instances."""
        result = CoverageResult(passed=True, percent=85.5)
        assert result.passed is True
        assert result.percent == 85.5

    def test_coverage_result_failed(self):
        """Test CoverageResult with failed status."""
        result = CoverageResult(passed=False, percent=45.2)
        assert result.passed is False
        assert result.percent == 45.2


class TestPercentFromRoot:
    """Test _percent_from_root function."""

    def test_percent_from_line_rate(self):
        """Test extracting percentage from line-rate attribute."""
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "0.85"
        
        result = _percent_from_root(root)
        assert result == 85.0

    def test_percent_from_line_rate_invalid(self):
        """Test handling invalid line-rate value."""
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "invalid"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_lines_valid_covered(self):
        """Test extracting percentage from lines-valid and lines-covered."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "100"
        root.attrib["lines-covered"] = "80"
        
        result = _percent_from_root(root)
        assert result == 80.0

    def test_percent_from_lines_invalid_values(self):
        """Test handling invalid lines-valid/covered values."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "invalid"
        root.attrib["lines-covered"] = "80"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_lines_zero_valid(self):
        """Test handling zero lines-valid."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "0"
        root.attrib["lines-covered"] = "80"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters(self):
        """Test extracting percentage from counter elements."""
        root = ET.Element("coverage")
        
        # Add counter elements
        counter1 = ET.SubElement(root, "counter")
        counter1.attrib["type"] = "LINE"
        counter1.attrib["covered"] = "50"
        counter1.attrib["missed"] = "30"
        
        counter2 = ET.SubElement(root, "counter")
        counter2.attrib["type"] = "LINE"
        counter2.attrib["covered"] = "20"
        counter2.attrib["missed"] = "10"
        
        result = _percent_from_root(root)
        # The actual calculation is (50+20)/(50+30+20+10) * 100 = 70/110 * 100 = 63.636...
        assert abs(result - 63.636) < 0.1  # Allow small floating point differences

    def test_percent_from_counters_non_line_type(self):
        """Test ignoring non-LINE counter types."""
        root = ET.Element("coverage")
        
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "BRANCH"
        counter.attrib["covered"] = "50"
        counter.attrib["missed"] = "30"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters_missing_attributes(self):
        """Test handling missing counter attributes."""
        root = ET.Element("coverage")
        
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "LINE"
        # Missing covered and missed attributes
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters_zero_total(self):
        """Test handling zero total valid lines."""
        root = ET.Element("coverage")
        
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "LINE"
        counter.attrib["covered"] = "0"
        counter.attrib["missed"] = "0"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_root_fallback(self):
        """Test fallback when no valid data is found."""
        root = ET.Element("coverage")
        # No attributes or counters
        
        result = _percent_from_root(root)
        assert result == 0.0


class TestEvaluateCoverageStr:
    """Test evaluate_coverage_str function."""

    def test_evaluate_coverage_str_passed(self):
        """Test coverage evaluation that passes threshold."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_failed(self):
        """Test coverage evaluation that fails threshold."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage line-rate="0.75">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is False
        assert result.percent == 75.0

    def test_evaluate_coverage_str_exactly_threshold(self):
        """Test coverage evaluation at exactly the threshold."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage line-rate="0.80">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is True
        assert result.percent == 80.0

    def test_evaluate_coverage_str_with_lines_attributes(self):
        """Test coverage evaluation using lines-valid/covered attributes."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage lines-valid="100" lines-covered="90">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is True
        assert result.percent == 90.0

    def test_evaluate_coverage_str_with_counters(self):
        """Test coverage evaluation using counter elements."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage>
            <counter type="LINE" covered="80" missed="20"/>
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is True
        assert result.percent == 80.0

    def test_evaluate_coverage_str_invalid_xml(self):
        """Test handling invalid XML."""
        xml_text = "invalid xml"
        
        with pytest.raises(ET.ParseError):
            evaluate_coverage_str(xml_text, 80.0)

    def test_evaluate_coverage_str_default_threshold(self):
        """Test coverage evaluation with default threshold."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_zero_coverage(self):
        """Test coverage evaluation with zero coverage."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage line-rate="0.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is False
        assert result.percent == 0.0

    def test_evaluate_coverage_str_100_percent(self):
        """Test coverage evaluation with 100% coverage."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage line-rate="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is True
        assert result.percent == 100.0

    def test_evaluate_coverage_str_complex_xml(self):
        """Test coverage evaluation with complex XML structure."""
        xml_text = '''<?xml version="1.0" ?>
        <coverage>
            <packages>
                <package>
                    <counter type="LINE" covered="40" missed="10"/>
                </package>
                <package>
                    <counter type="LINE" covered="30" missed="20"/>
                </package>
            </packages>
        </coverage>'''
        
        result = evaluate_coverage_str(xml_text, 80.0)
        assert result.passed is False
        assert result.percent == 70.0  # (40+30)/(40+10+30+20) * 100
