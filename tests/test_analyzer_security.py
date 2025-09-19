"""Tests for SecurityAnalyzer class."""

import pytest
import tempfile
import os

from src.ai_guard.analyzer import SecurityAnalyzer


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_security_analyzer_init(self):
        """Test SecurityAnalyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.rules == []

    def test_security_analyzer_load_rules(self):
        """Test loading security rules."""
        analyzer = SecurityAnalyzer()
        analyzer.load_rules()
        assert analyzer.rules == ["rule1", "rule2", "rule3"]

    def test_security_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = SecurityAnalyzer()
        issues = analyzer.analyze_file("nonexistent.py")
        assert issues == ["File not found: nonexistent.py"]

    def test_security_analyzer_analyze_file_with_os_system(self):
        """Test analyzing file with os.system call."""
        analyzer = SecurityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nos.system('ls')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert "Dangerous os.system call detected" in issues
        finally:
            os.unlink(temp_file)

    def test_security_analyzer_analyze_file_with_eval(self):
        """Test analyzing file with eval call."""
        analyzer = SecurityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("eval('1+1')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert "Dangerous eval() call detected" in issues
        finally:
            os.unlink(temp_file)

    def test_security_analyzer_analyze_file_safe(self):
        """Test analyzing safe file."""
        analyzer = SecurityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello World')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert issues == []
        finally:
            os.unlink(temp_file)

    def test_security_analyzer_add_issue(self):
        """Test adding security issue."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "high")
        
        issues = analyzer.get_issues()
        assert len(issues) == 1
        assert issues[0]["file"] == "test.py"
        assert issues[0]["line"] == 10
        assert issues[0]["message"] == "Test issue"
        assert issues[0]["severity"] == "high"

    def test_security_analyzer_clear_issues(self):
        """Test clearing security issues."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "high")
        analyzer.clear_issues()
        
        issues = analyzer.get_issues()
        assert issues == []
