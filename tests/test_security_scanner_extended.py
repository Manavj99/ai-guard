"""Extended tests for security scanner to improve coverage."""

import pytest
import json
import os
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from src.ai_guard.security_scanner import (
    run_bandit,
    run_safety_check,
    SecurityScanner,
    scan_for_vulnerabilities,
    check_dependencies,
    analyze_security_patterns,
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer
)


class TestSecurityScannerExtended:
    """Extended tests for SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    @patch('subprocess.call')
    def test_run_bandit_with_config(self, mock_call):
        """Test run_bandit with config file."""
        mock_call.return_value = 0
        
        # Create a mock .bandit file
        with patch('os.path.exists', return_value=True):
            result = run_bandit()
            assert result == 0
            mock_call.assert_called_once()

    @patch('subprocess.call')
    def test_run_bandit_without_config(self, mock_call):
        """Test run_bandit without config file."""
        mock_call.return_value = 0
        
        with patch('os.path.exists', return_value=False):
            result = run_bandit()
            assert result == 0
            mock_call.assert_called_once()

    @patch('subprocess.call')
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test run_bandit with extra arguments."""
        mock_call.return_value = 0
        
        result = run_bandit(['--skip', 'B101'])
        assert result == 0
        mock_call.assert_called_once()

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_call):
        """Test successful safety check."""
        mock_call.return_value = 0
        
        result = run_safety_check()
        assert result == 0
        mock_call.assert_called_once_with(['safety', 'check'])

    @patch('subprocess.call')
    def test_run_safety_check_not_found(self, mock_call):
        """Test safety check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError()
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
            assert result == 0
            mock_print.assert_called_once()

    @patch('subprocess.call')
    def test_run_safety_check_exception(self, mock_call):
        """Test safety check with exception."""
        mock_call.side_effect = Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            result = run_safety_check()
            assert result == 0
            mock_print.assert_called_once()

    def test_security_scanner_run_bandit_scan(self):
        """Test SecurityScanner.run_bandit_scan."""
        scanner = SecurityScanner()
        
        with patch('src.ai_guard.security_scanner.run_bandit', return_value=0) as mock_run:
            result = scanner.run_bandit_scan(['--skip', 'B101'])
            assert result == 0
            mock_run.assert_called_once_with(['--skip', 'B101'])

    def test_security_scanner_run_safety_scan(self):
        """Test SecurityScanner.run_safety_scan."""
        scanner = SecurityScanner()
        
        with patch('src.ai_guard.security_scanner.run_safety_check', return_value=0) as mock_run:
            result = scanner.run_safety_scan()
            assert result == 0
            mock_run.assert_called_once()

    def test_security_scanner_run_all_checks_success(self):
        """Test SecurityScanner.run_all_security_checks success."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=0), \
             patch.object(scanner, 'run_safety_scan', return_value=0):
            result = scanner.run_all_security_checks()
            assert result == 0

    def test_security_scanner_run_all_checks_failure(self):
        """Test SecurityScanner.run_all_security_checks with failure."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'run_bandit_scan', return_value=1), \
             patch.object(scanner, 'run_safety_scan', return_value=0):
            result = scanner.run_all_security_checks()
            assert result == 1


class TestScanForVulnerabilities:
    """Test scan_for_vulnerabilities function."""

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_success(self, mock_run):
        """Test successful vulnerability scan."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{"test": "vulnerability"}])
        mock_run.return_value = mock_result
        
        result = scan_for_vulnerabilities(['test.py'])
        
        assert result['success'] is True
        assert result['files_scanned'] == 1
        assert 'vulnerabilities' in result

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_failure(self, mock_run):
        """Test failed vulnerability scan."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Scan failed"
        mock_run.return_value = mock_result
        
        result = scan_for_vulnerabilities(['test.py'])
        
        assert result['success'] is False
        assert result['error'] == "Scan failed"
        assert result['returncode'] == 1

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_timeout(self, mock_run):
        """Test vulnerability scan timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('bandit', 300)
        
        result = scan_for_vulnerabilities(['test.py'])
        
        assert result['success'] is False
        assert result['error'] == "Scan timeout"

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_called_process_error(self, mock_run):
        """Test vulnerability scan with CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'bandit')
        
        result = scan_for_vulnerabilities(['test.py'])
        
        assert result['success'] is False
        assert 'error' in result

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_general_exception(self, mock_run):
        """Test vulnerability scan with general exception."""
        mock_run.side_effect = Exception("General error")
        
        result = scan_for_vulnerabilities(['test.py'])
        
        assert result['success'] is False
        assert result['error'] == "General error"


class TestCheckDependencies:
    """Test check_dependencies function."""

    @patch('subprocess.run')
    def test_check_dependencies_success(self, mock_run):
        """Test successful dependency check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{"package": "test"}])
        mock_run.return_value = mock_result
        
        result = check_dependencies()
        
        assert result['success'] is True
        assert 'packages' in result

    @patch('subprocess.run')
    def test_check_dependencies_failure(self, mock_run):
        """Test failed dependency check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Check failed"
        mock_run.return_value = mock_result
        
        result = check_dependencies()
        
        assert result['success'] is False
        assert result['error'] == "Check failed"

    @patch('subprocess.run')
    def test_check_dependencies_timeout(self, mock_run):
        """Test dependency check timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('pip-audit', 300)
        
        result = check_dependencies()
        
        assert result['success'] is False
        assert result['error'] == "Dependency check timeout"


class TestAnalyzeSecurityPatterns:
    """Test analyze_security_patterns function."""

    def test_analyze_security_patterns_sql_injection(self):
        """Test SQL injection pattern detection."""
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'
        
        result = analyze_security_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) > 0
        assert result['patterns'][0]['type'] == 'sql_injection'

    def test_analyze_security_patterns_hardcoded_password(self):
        """Test hardcoded password pattern detection."""
        code = 'password = "secret123"'
        
        result = analyze_security_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) > 0
        assert result['patterns'][0]['type'] == 'hardcoded_password'

    def test_analyze_security_patterns_dangerous_function(self):
        """Test dangerous function pattern detection."""
        code = 'result = eval(user_input)'
        
        result = analyze_security_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) > 0
        assert result['patterns'][0]['type'] == 'dangerous_function'

    def test_analyze_security_patterns_no_patterns(self):
        """Test code with no security patterns."""
        code = 'x = 1 + 2'
        
        result = analyze_security_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) == 0


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""

    def test_vulnerability_checker_init(self):
        """Test VulnerabilityChecker initialization."""
        checker = VulnerabilityChecker()
        assert checker.checker_name == "Vulnerability Checker"
        assert "low" in checker.severity_levels

    def test_check_vulnerability_patterns(self):
        """Test vulnerability pattern checking."""
        checker = VulnerabilityChecker()
        code = 'password = "secret"'
        
        result = checker.check_vulnerability_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert 'vulnerabilities' in result

    def test_check_sql_injection_patterns(self):
        """Test SQL injection pattern checking."""
        checker = VulnerabilityChecker()
        code = 'query = f"SELECT * FROM users WHERE id = {id}"'
        
        result = checker.check_sql_injection_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['vulnerabilities']) > 0

    def test_check_xss_patterns(self):
        """Test XSS pattern checking."""
        checker = VulnerabilityChecker()
        code = 'html = f"<div>{request.GET.get(\'name\')}</div>"'
        
        result = checker.check_xss_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['vulnerabilities']) > 0


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_dependency_analyzer_init(self):
        """Test DependencyAnalyzer initialization."""
        analyzer = DependencyAnalyzer()
        assert analyzer.analyzer_name == "Dependency Analyzer"
        assert analyzer.requirements_file == "requirements.txt"

    @patch('builtins.open', mock_open(read_data='requests==2.25.1\nnumpy==1.21.0'))
    def test_analyze_requirements_file_success(self):
        """Test successful requirements file analysis."""
        analyzer = DependencyAnalyzer()
        
        result = analyzer.analyze_requirements_file('requirements.txt')
        
        assert result['success'] is True
        assert len(result['packages']) == 2

    def test_analyze_requirements_file_not_found(self):
        """Test requirements file not found."""
        analyzer = DependencyAnalyzer()
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = analyzer.analyze_requirements_file('missing.txt')
            
            assert result['success'] is False
            assert 'error' in result

    def test_check_package_vulnerabilities(self):
        """Test package vulnerability checking."""
        analyzer = DependencyAnalyzer()
        packages = [{"name": "requests", "version": "2.25.1"}]
        
        result = analyzer.check_package_vulnerabilities(packages)
        
        assert result['success'] is True
        assert len(result['vulnerabilities']) > 0


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""

    def test_security_pattern_analyzer_init(self):
        """Test SecurityPatternAnalyzer initialization."""
        analyzer = SecurityPatternAnalyzer()
        assert analyzer.analyzer_name == "Security Pattern Analyzer"
        assert len(analyzer.patterns) > 0

    def test_analyze_code_patterns(self):
        """Test code pattern analysis."""
        analyzer = SecurityPatternAnalyzer()
        code = 'os.system("rm -rf /")'
        
        result = analyzer.analyze_code_patterns(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) > 0

    def test_check_hardcoded_secrets(self):
        """Test hardcoded secret checking."""
        analyzer = SecurityPatternAnalyzer()
        code = 'api_key = "sk-1234567890"'
        
        result = analyzer.check_hardcoded_secrets(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) > 0

    def test_check_dangerous_functions(self):
        """Test dangerous function checking."""
        analyzer = SecurityPatternAnalyzer()
        code = 'eval(user_input)'
        
        result = analyzer.check_dangerous_functions(code, 'test.py')
        
        assert result['success'] is True
        assert len(result['patterns']) > 0
