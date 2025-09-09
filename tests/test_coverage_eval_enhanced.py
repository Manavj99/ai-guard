"""Enhanced tests for coverage_eval module to achieve 80%+ coverage."""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import patch, mock_open

from src.ai_guard.gates.coverage_eval import (
    CoverageResult,
    evaluate_coverage_str,
    _percent_from_root
)


class TestCoverageResult:
    """Test CoverageResult dataclass."""

    def test_coverage_result_creation(self):
        """Test CoverageResult creation with different values."""
        result = CoverageResult(passed=True, percent=85.5)
        assert result.passed is True
        assert result.percent == 85.5

    def test_coverage_result_failed(self):
        """Test CoverageResult with failed status."""
        result = CoverageResult(passed=False, percent=45.0)
        assert result.passed is False
        assert result.percent == 45.0


class TestPercentFromRoot:
    """Test _percent_from_root function."""

    def test_percent_from_line_rate(self):
        """Test percentage calculation from line-rate attribute."""
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "0.85"
        
        result = _percent_from_root(root)
        assert result == 85.0

    def test_percent_from_line_rate_invalid(self):
        """Test percentage calculation with invalid line-rate."""
        root = ET.Element("coverage")
        root.attrib["line-rate"] = "invalid"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_lines_valid_covered(self):
        """Test percentage calculation from lines-valid and lines-covered."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "100"
        root.attrib["lines-covered"] = "80"
        
        result = _percent_from_root(root)
        assert result == 80.0

    def test_percent_from_lines_invalid_values(self):
        """Test percentage calculation with invalid lines values."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "invalid"
        root.attrib["lines-covered"] = "invalid"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_lines_zero_valid(self):
        """Test percentage calculation with zero valid lines."""
        root = ET.Element("coverage")
        root.attrib["lines-valid"] = "0"
        root.attrib["lines-covered"] = "0"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters(self):
        """Test percentage calculation from counter elements."""
        root = ET.Element("coverage")
        
        # Add counter elements
        counter1 = ET.SubElement(root, "counter")
        counter1.attrib["type"] = "LINE"
        counter1.attrib["covered"] = "50"
        counter1.attrib["missed"] = "10"
        
        counter2 = ET.SubElement(root, "counter")
        counter2.attrib["type"] = "LINE"
        counter2.attrib["covered"] = "30"
        counter2.attrib["missed"] = "20"
        
        result = _percent_from_root(root)
        assert result == 72.72727272727273  # (50+30)/(50+10+30+20) = 80/110 = 72.7%

    def test_percent_from_counters_missing_attributes(self):
        """Test percentage calculation with missing counter attributes."""
        root = ET.Element("coverage")
        
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "LINE"
        # Missing covered and missed attributes
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters_non_line_type(self):
        """Test percentage calculation with non-LINE counter types."""
        root = ET.Element("coverage")
        
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "BRANCH"
        counter.attrib["covered"] = "50"
        counter.attrib["missed"] = "10"
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters_invalid_values(self):
        """Test percentage calculation with invalid counter values."""
        root = ET.Element("coverage")
        
        counter = ET.SubElement(root, "counter")
        counter.attrib["type"] = "LINE"
        counter.attrib["covered"] = "invalid"
        counter.attrib["missed"] = "invalid"
        
        # The function should handle invalid values gracefully
        with pytest.raises(ValueError):
            _percent_from_root(root)

    def test_percent_from_root_no_attributes(self):
        """Test percentage calculation with no relevant attributes."""
        root = ET.Element("coverage")
        
        result = _percent_from_root(root)
        assert result == 0.0


class TestEvaluateCoverageStr:
    """Test evaluate_coverage_str function."""

    def test_evaluate_coverage_str_passing(self):
        """Test coverage evaluation with passing threshold."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85" branch-rate="0.75" version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_failing(self):
        """Test coverage evaluation with failing threshold."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.75" branch-rate="0.65" version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is False
        assert result.percent == 75.0

    def test_evaluate_coverage_str_exact_threshold(self):
        """Test coverage evaluation at exact threshold."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.80" branch-rate="0.70" version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 80.0

    def test_evaluate_coverage_str_with_counters(self):
        """Test coverage evaluation using counter elements."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage version="1.0">
            <counter type="LINE" covered="80" missed="20"/>
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=75.0)
        assert result.passed is True
        assert result.percent == 80.0

    def test_evaluate_coverage_str_empty_xml(self):
        """Test coverage evaluation with empty XML."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is False
        assert result.percent == 0.0

    def test_evaluate_coverage_str_invalid_xml(self):
        """Test coverage evaluation with invalid XML."""
        xml_content = "invalid xml content"
        
        with pytest.raises(ET.ParseError):
            evaluate_coverage_str(xml_content, threshold=80.0)

    def test_evaluate_coverage_str_default_threshold(self):
        """Test coverage evaluation with default threshold."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85" branch-rate="0.75" version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_zero_threshold(self):
        """Test coverage evaluation with zero threshold."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.0" branch-rate="0.0" version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=0.0)
        assert result.passed is True
        assert result.percent == 0.0

    def test_evaluate_coverage_str_high_threshold(self):
        """Test coverage evaluation with very high threshold."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.95" branch-rate="0.90" version="1.0">
        </coverage>'''
        
        result = evaluate_coverage_str(xml_content, threshold=99.0)
        assert result.passed is False
        assert result.percent == 95.0

    def test_evaluate_coverage_str_mixed_attributes(self):
        """Test coverage evaluation with mixed line-rate and counters."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85" version="1.0">
            <counter type="LINE" covered="80" missed="20"/>
        </coverage>'''
        
        # Should use line-rate (0.85) over counters
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 85.0
