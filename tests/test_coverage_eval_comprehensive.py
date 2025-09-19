"""Comprehensive tests for coverage_eval module."""

import xml.etree.ElementTree as ET
import pytest
from src.ai_guard.gates.coverage_eval import (
    CoverageResult,
    _percent_from_root,
    evaluate_coverage_str
)


class TestCoverageResult:
    """Test CoverageResult dataclass."""

    def test_coverage_result_creation(self):
        """Test CoverageResult creation."""
        result = CoverageResult(passed=True, percent=85.5)
        assert result.passed is True
        assert result.percent == 85.5

    def test_coverage_result_failed(self):
        """Test CoverageResult with failed result."""
        result = CoverageResult(passed=False, percent=45.0)
        assert result.passed is False
        assert result.percent == 45.0


class TestPercentFromRoot:
    """Test _percent_from_root function."""

    def test_percent_from_line_rate(self):
        """Test percentage calculation from line-rate attribute."""
        root = ET.Element("coverage")
        root.set("line-rate", "0.85")
        
        result = _percent_from_root(root)
        assert result == 85.0

    def test_percent_from_line_rate_decimal(self):
        """Test percentage calculation from decimal line-rate."""
        root = ET.Element("coverage")
        root.set("line-rate", "0.1234")
        
        result = _percent_from_root(root)
        assert result == 12.34

    def test_percent_from_lines_valid_covered(self):
        """Test percentage calculation from lines-valid and lines-covered."""
        root = ET.Element("coverage")
        root.set("lines-valid", "100")
        root.set("lines-covered", "75")
        
        result = _percent_from_root(root)
        assert result == 75.0

    def test_percent_from_lines_zero_valid(self):
        """Test percentage calculation with zero valid lines."""
        root = ET.Element("coverage")
        root.set("lines-valid", "0")
        root.set("lines-covered", "0")
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_counters(self):
        """Test percentage calculation from counter elements."""
        root = ET.Element("coverage")
        
        # Add package with counter
        package = ET.SubElement(root, "package")
        counter = ET.SubElement(package, "counter")
        counter.set("type", "LINE")
        counter.set("covered", "80")
        counter.set("missed", "20")
        
        result = _percent_from_root(root)
        assert result == 80.0

    def test_percent_from_multiple_counters(self):
        """Test percentage calculation from multiple counter elements."""
        root = ET.Element("coverage")
        
        # Add multiple packages with counters
        for covered, missed in [(50, 10), (30, 20)]:
            package = ET.SubElement(root, "package")
            counter = ET.SubElement(package, "counter")
            counter.set("type", "LINE")
            counter.set("covered", str(covered))
            counter.set("missed", str(missed))
        
        result = _percent_from_root(root)
        assert abs(result - 72.73) < 0.01  # (50+30)/(50+10+30+20) * 100 = 80/110 * 100

    def test_percent_from_counters_non_line_type(self):
        """Test percentage calculation ignoring non-LINE counter types."""
        root = ET.Element("coverage")
        
        # Add non-LINE counter
        package = ET.SubElement(root, "package")
        counter = ET.SubElement(package, "counter")
        counter.set("type", "BRANCH")
        counter.set("covered", "50")
        counter.set("missed", "50")
        
        result = _percent_from_root(root)
        assert result == 0.0  # No LINE counters

    def test_percent_from_invalid_line_rate(self):
        """Test percentage calculation with invalid line-rate."""
        root = ET.Element("coverage")
        root.set("line-rate", "invalid")
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_invalid_lines_valid(self):
        """Test percentage calculation with invalid lines-valid."""
        root = ET.Element("coverage")
        root.set("lines-valid", "invalid")
        root.set("lines-covered", "50")
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_invalid_counter_values(self):
        """Test percentage calculation with invalid counter values."""
        root = ET.Element("coverage")
        
        package = ET.SubElement(root, "package")
        counter = ET.SubElement(package, "counter")
        counter.set("type", "LINE")
        counter.set("covered", "invalid")
        counter.set("missed", "invalid")
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_empty_root(self):
        """Test percentage calculation with empty root."""
        root = ET.Element("coverage")
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_missing_attributes(self):
        """Test percentage calculation with missing attributes."""
        root = ET.Element("coverage")
        # No attributes set
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_mixed_attributes(self):
        """Test percentage calculation with mixed valid/invalid attributes."""
        root = ET.Element("coverage")
        root.set("line-rate", "invalid")
        root.set("lines-valid", "100")
        root.set("lines-covered", "75")
        
        result = _percent_from_root(root)
        assert result == 75.0  # Should fall back to lines-valid/covered

    def test_percent_from_counter_missing_values(self):
        """Test percentage calculation with counter missing values."""
        root = ET.Element("coverage")
        
        package = ET.SubElement(root, "package")
        counter = ET.SubElement(package, "counter")
        counter.set("type", "LINE")
        # Missing covered and missed attributes
        
        result = _percent_from_root(root)
        assert result == 0.0


class TestEvaluateCoverageStr:
    """Test evaluate_coverage_str function."""

    def test_evaluate_coverage_str_passing(self):
        """Test coverage evaluation with passing threshold."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.85">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_failing(self):
        """Test coverage evaluation with failing threshold."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.75">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is False
        assert result.percent == 75.0

    def test_evaluate_coverage_str_exact_threshold(self):
        """Test coverage evaluation at exact threshold."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.80">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 80.0

    def test_evaluate_coverage_str_default_threshold(self):
        """Test coverage evaluation with default threshold."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.85">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content)
        assert result.passed is True
        assert result.percent == 85.0

    def test_evaluate_coverage_str_with_lines_valid_covered(self):
        """Test coverage evaluation using lines-valid and lines-covered."""
        xml_content = """<?xml version="1.0" ?>
<coverage lines-valid="100" lines-covered="90">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 90.0

    def test_evaluate_coverage_str_with_counters(self):
        """Test coverage evaluation using counter elements."""
        xml_content = """<?xml version="1.0" ?>
<coverage>
    <package>
        <counter type="LINE" covered="80" missed="20"/>
    </package>
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 80.0

    def test_evaluate_coverage_str_zero_coverage(self):
        """Test coverage evaluation with zero coverage."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.0">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is False
        assert result.percent == 0.0

    def test_evaluate_coverage_str_100_percent(self):
        """Test coverage evaluation with 100% coverage."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="1.0">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 100.0

    def test_evaluate_coverage_str_invalid_xml(self):
        """Test coverage evaluation with invalid XML."""
        xml_content = "invalid xml content"
        
        with pytest.raises(ET.ParseError):
            evaluate_coverage_str(xml_content)

    def test_evaluate_coverage_str_empty_xml(self):
        """Test coverage evaluation with empty XML."""
        xml_content = ""
        
        with pytest.raises(ET.ParseError):
            evaluate_coverage_str(xml_content)

    def test_evaluate_coverage_str_complex_xml(self):
        """Test coverage evaluation with complex XML structure."""
        xml_content = """<?xml version="1.0" ?>
<coverage>
    <package name="test">
        <class name="TestClass">
            <counter type="LINE" covered="10" missed="5"/>
        </class>
    </package>
    <package name="other">
        <class name="OtherClass">
            <counter type="LINE" covered="20" missed="10"/>
        </class>
    </package>
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=60.0)
        assert result.passed is True
        assert abs(result.percent - 66.67) < 0.01  # (10+20)/(10+5+20+10) * 100

    def test_evaluate_coverage_str_mixed_counter_types(self):
        """Test coverage evaluation with mixed counter types."""
        xml_content = """<?xml version="1.0" ?>
<coverage>
    <package>
        <counter type="LINE" covered="80" missed="20"/>
        <counter type="BRANCH" covered="50" missed="50"/>
        <counter type="METHOD" covered="10" missed="5"/>
    </package>
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 80.0  # Only LINE counters should be used

    def test_evaluate_coverage_str_precision(self):
        """Test coverage evaluation with high precision."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.123456789">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=12.0)
        assert result.passed is True
        assert abs(result.percent - 12.3456789) < 0.0000001

    def test_evaluate_coverage_str_very_low_threshold(self):
        """Test coverage evaluation with very low threshold."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.01">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=0.5)
        assert result.passed is True  # 1.0% > 0.5%
        assert result.percent == 1.0

    def test_evaluate_coverage_str_very_high_threshold(self):
        """Test coverage evaluation with very high threshold."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.99">
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=99.5)
        assert result.passed is False
        assert result.percent == 99.0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_percent_from_root_nonexistent_element(self):
        """Test _percent_from_root with nonexistent element."""
        root = ET.Element("nonexistent")
        
        result = _percent_from_root(root)
        assert result == 0.0

    def test_percent_from_root_deeply_nested_counters(self):
        """Test _percent_from_root with deeply nested counters."""
        root = ET.Element("coverage")
        
        # Create deeply nested structure
        level1 = ET.SubElement(root, "level1")
        level2 = ET.SubElement(level1, "level2")
        level3 = ET.SubElement(level2, "level3")
        counter = ET.SubElement(level3, "counter")
        counter.set("type", "LINE")
        counter.set("covered", "100")
        counter.set("missed", "0")
        
        result = _percent_from_root(root)
        assert result == 100.0

    def test_percent_from_root_multiple_line_counters(self):
        """Test _percent_from_root with multiple LINE counters."""
        root = ET.Element("coverage")
        
        # Add multiple LINE counters
        for covered, missed in [(10, 5), (20, 10), (30, 15)]:
            package = ET.SubElement(root, "package")
            counter = ET.SubElement(package, "counter")
            counter.set("type", "LINE")
            counter.set("covered", str(covered))
            counter.set("missed", str(missed))
        
        result = _percent_from_root(root)
        assert abs(result - 66.67) < 0.01  # (10+20+30)/(10+5+20+10+30+15) * 100 = 60/90 * 100

    def test_evaluate_coverage_str_unicode_xml(self):
        """Test coverage evaluation with Unicode XML."""
        xml_content = """<?xml version="1.0" encoding="utf-8" ?>
<coverage line-rate="0.85">
    <package name="测试">
        <counter type="LINE" covered="85" missed="15"/>
    </package>
</coverage>"""
        
        result = evaluate_coverage_str(xml_content, threshold=80.0)
        assert result.passed is True
        assert result.percent == 85.0