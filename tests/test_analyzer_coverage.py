"""Tests for CoverageAnalyzer class."""

import pytest
import tempfile
import os

from src.ai_guard.analyzer import CoverageAnalyzer


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_coverage_analyzer_init(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}

    def test_coverage_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = CoverageAnalyzer()
        data = analyzer.analyze_file("nonexistent.py")
        assert data == {}

    def test_coverage_analyzer_analyze_file(self):
        """Test analyzing file."""
        analyzer = CoverageAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello World')\n")
            temp_file = f.name
        
        try:
            data = analyzer.analyze_file(temp_file)
            assert isinstance(data, dict)
        finally:
            os.unlink(temp_file)

    def test_coverage_analyzer_clear_data(self):
        """Test clearing coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"file1": 85.0}
        analyzer.clear_data()
        
        assert analyzer.coverage_data == {}
