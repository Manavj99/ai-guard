"""Tests for QualityAnalyzer class."""

import pytest
import tempfile
import os

from src.ai_guard.analyzer import QualityAnalyzer


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""

    def test_quality_analyzer_init(self):
        """Test QualityAnalyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.metrics == {}

    def test_quality_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = QualityAnalyzer()
        issues = analyzer.analyze_file("nonexistent.py")
        assert issues == ["File not found: nonexistent.py"]

    def test_quality_analyzer_analyze_file_with_todo(self):
        """Test analyzing file with TODO comment."""
        analyzer = QualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# TODO: Fix this\nprint('Hello World')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert "TODO comment found" in issues
        finally:
            os.unlink(temp_file)

    def test_quality_analyzer_analyze_file_with_fixme(self):
        """Test analyzing file with FIXME comment."""
        analyzer = QualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# FIXME: Fix this\nprint('Hello World')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert "FIXME comment found" in issues
        finally:
            os.unlink(temp_file)

    def test_quality_analyzer_analyze_file_safe(self):
        """Test analyzing safe file."""
        analyzer = QualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello World')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert issues == []
        finally:
            os.unlink(temp_file)

    def test_quality_analyzer_add_issue(self):
        """Test adding quality issue."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "low")
        
        issues = analyzer.get_issues()
        assert len(issues) == 1
        assert issues[0]["file"] == "test.py"
        assert issues[0]["line"] == 10
        assert issues[0]["message"] == "Test issue"
        assert issues[0]["severity"] == "low"

    def test_quality_analyzer_clear_issues(self):
        """Test clearing quality issues."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "low")
        analyzer.clear_issues()
        
        issues = analyzer.get_issues()
        assert issues == []
