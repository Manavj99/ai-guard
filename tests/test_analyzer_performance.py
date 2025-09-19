"""Tests for PerformanceAnalyzer class."""

import pytest
import tempfile
import os

from src.ai_guard.analyzer import PerformanceAnalyzer


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    def test_performance_analyzer_init(self):
        """Test PerformanceAnalyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.issues == []
        assert analyzer.benchmarks == {}

    def test_performance_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = PerformanceAnalyzer()
        issues = analyzer.analyze_file("nonexistent.py")
        assert issues == ["File not found: nonexistent.py"]

    def test_performance_analyzer_analyze_file_with_large_loop(self):
        """Test analyzing file with large range loop."""
        analyzer = PerformanceAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("for i in range(1000000):\n    pass\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert "Potential performance issue: large range loop" in issues
        finally:
            os.unlink(temp_file)

    def test_performance_analyzer_analyze_file_with_sleep(self):
        """Test analyzing file with sleep call."""
        analyzer = PerformanceAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import time\ntime.sleep(1)\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert "Blocking sleep call detected" in issues
        finally:
            os.unlink(temp_file)

    def test_performance_analyzer_analyze_file_safe(self):
        """Test analyzing safe file."""
        analyzer = PerformanceAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello World')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert issues == []
        finally:
            os.unlink(temp_file)

    def test_performance_analyzer_add_issue(self):
        """Test adding performance issue."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "medium")
        
        issues = analyzer.get_issues()
        assert len(issues) == 1
        assert issues[0]["file"] == "test.py"
        assert issues[0]["line"] == 10
        assert issues[0]["message"] == "Test issue"
        assert issues[0]["severity"] == "medium"

    def test_performance_analyzer_clear_issues(self):
        """Test clearing performance issues."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "medium")
        analyzer.clear_issues()
        
        issues = analyzer.get_issues()
        assert issues == []
