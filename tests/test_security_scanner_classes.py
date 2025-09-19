"""Tests for security_scanner classes."""

import tempfile
import pytest
from unittest.mock import patch, mock_open
from src.ai_guard.security_scanner import (
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer
)


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""
    
    def test_vulnerability_checker_init(self):
        """Test VulnerabilityChecker initialization."""
        checker = VulnerabilityChecker()
        assert checker.checker_name == "Vulnerability Checker"
        assert checker.severity_levels == ["low", "medium", "high", "critical"]
    
    def test_check_vulnerability_patterns_hardcoded_password(self):
        """Test vulnerability pattern checking for hardcoded password."""
        checker = VulnerabilityChecker()
        code = 'password = "secret123"'
        
        result = checker.check_vulnerability_patterns(code, 'test.py')
        assert result['success'] is True
        assert result['file'] == 'test.py'
        assert len(result['vulnerabilities']) == 1
        assert result['vulnerabilities'][0]['type'] == 'hardcoded_password'
    
    def test_check_sql_injection_patterns(self):
        """Test SQL injection pattern checking."""
        checker = VulnerabilityChecker()
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'
        
        result = checker.check_sql_injection_patterns(code, 'test.py')
        assert result['success'] is True
        assert len(result['vulnerabilities']) == 1
        assert result['vulnerabilities'][0]['type'] == 'sql_injection'
        assert result['vulnerabilities'][0]['severity'] == 'high'
    
    def test_check_xss_patterns(self):
        """Test XSS pattern checking."""
        checker = VulnerabilityChecker()
        code = 'html = f"<div>{request.GET.get(\'name\')}</div>"'
        
        result = checker.check_xss_patterns(code, 'test.py')
        assert result['success'] is True
        assert len(result['vulnerabilities']) == 1
        assert result['vulnerabilities'][0]['type'] == 'xss'
        assert result['vulnerabilities'][0]['severity'] == 'medium'


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""
    
    def test_dependency_analyzer_init(self):
        """Test DependencyAnalyzer initialization."""
        analyzer = DependencyAnalyzer()
        assert analyzer.analyzer_name == "Dependency Analyzer"
        assert analyzer.requirements_file == "requirements.txt"
    
    def test_analyze_requirements_file_success(self):
        """Test successful requirements file analysis."""
        analyzer = DependencyAnalyzer()
        requirements_content = """
        requests==2.25.1
        pytest==6.2.0
        # This is a comment
        """
        
        with patch('builtins.open', mock_open(read_data=requirements_content)):
            result = analyzer.analyze_requirements_file('requirements.txt')
            assert result['success'] is True
            assert len(result['packages']) == 2
            assert result['packages'][0]['name'] == 'requests'
            assert result['packages'][0]['version'] == '2.25.1'
    
    def test_analyze_requirements_file_not_found(self):
        """Test requirements file analysis when file not found."""
        analyzer = DependencyAnalyzer()
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = analyzer.analyze_requirements_file('nonexistent.txt')
            assert result['success'] is False
            assert result['error'] == "Requirements file not found"
    
    def test_analyze_requirements_file_exception(self):
        """Test requirements file analysis with exception."""
        analyzer = DependencyAnalyzer()
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = analyzer.analyze_requirements_file('requirements.txt')
            assert result['success'] is False
            assert result['error'] == "Test error"
    
    def test_check_package_vulnerabilities(self):
        """Test package vulnerability checking."""
        analyzer = DependencyAnalyzer()
        packages = [
            {"name": "requests", "version": "2.25.1"},
            {"name": "pytest", "version": "6.2.0"}
        ]
        
        result = analyzer.check_package_vulnerabilities(packages)
        assert result['success'] is True
        assert len(result['vulnerabilities']) == 1
        assert result['vulnerabilities'][0]['package'] == 'requests'
        assert result['vulnerabilities'][0]['vulnerability'] == 'CVE-2021-1234'


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""
    
    def test_security_pattern_analyzer_init(self):
        """Test SecurityPatternAnalyzer initialization."""
        analyzer = SecurityPatternAnalyzer()
        assert analyzer.analyzer_name == "Security Pattern Analyzer"
        assert len(analyzer.patterns) == 4
        assert analyzer.patterns[0]['name'] == 'sql_injection'
    
    def test_analyze_code_patterns_os_system(self):
        """Test code pattern analysis for os.system."""
        analyzer = SecurityPatternAnalyzer()
        code = 'os.system("rm -rf /")'
        
        result = analyzer.analyze_code_patterns(code, 'test.py')
        assert result['success'] is True
        assert len(result['patterns']) == 1
        assert result['patterns'][0]['type'] == 'dangerous_function'
        assert result['patterns'][0]['severity'] == 'critical'
    
    def test_analyze_code_patterns_eval(self):
        """Test code pattern analysis for eval."""
        analyzer = SecurityPatternAnalyzer()
        code = 'result = eval(user_input)'
        
        result = analyzer.analyze_code_patterns(code, 'test.py')
        assert result['success'] is True
        assert len(result['patterns']) == 1
        assert result['patterns'][0]['type'] == 'dangerous_function'
        assert result['patterns'][0]['severity'] == 'critical'
    
    def test_check_hardcoded_secrets_api_key(self):
        """Test hardcoded secrets checking for API key."""
        analyzer = SecurityPatternAnalyzer()
        code = 'api_key = "sk-1234567890abcdef"'
        
        result = analyzer.check_hardcoded_secrets(code, 'test.py')
        assert result['success'] is True
        assert len(result['patterns']) == 1
        assert result['patterns'][0]['type'] == 'api_key'
        assert result['patterns'][0]['severity'] == 'high'
    
    def test_check_hardcoded_secrets_password(self):
        """Test hardcoded secrets checking for password."""
        analyzer = SecurityPatternAnalyzer()
        code = 'password = "secret123"'
        
        result = analyzer.check_hardcoded_secrets(code, 'test.py')
        assert result['success'] is True
        assert len(result['patterns']) == 1
        assert result['patterns'][0]['type'] == 'password'
        assert result['patterns'][0]['severity'] == 'medium'
    
    def test_check_dangerous_functions(self):
        """Test dangerous functions checking."""
        analyzer = SecurityPatternAnalyzer()
        code = '''
        os.system("rm -rf /")
        subprocess.call(["ls"])
        eval("1+1")
        exec("print('hello')")
        '''
        
        result = analyzer.check_dangerous_functions(code, 'test.py')
        assert result['success'] is True
        assert len(result['patterns']) == 4
        assert all(pattern['type'] == 'dangerous_function' for pattern in result['patterns'])
        assert all(pattern['severity'] == 'critical' for pattern in result['patterns'])
