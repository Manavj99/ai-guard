"""Tests for security scanner and tests runner modules."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.ai_guard.security_scanner import (
    SecurityScanner,
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer,
    run_bandit,
    run_safety_check,
    scan_for_vulnerabilities,
    check_dependencies,
    analyze_security_patterns
)
from src.ai_guard.tests_runner import (
    TestsRunner,
    TestRunner,
    TestDiscoverer,
    TestExecutor,
    run_pytest_with_coverage,
    run_pytest,
    run_tests,
    discover_test_files,
    execute_test_suite
)


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    @patch('subprocess.call')
    def test_run_bandit_scan(self, mock_call):
        """Test running bandit scan."""
        mock_call.return_value = 0
        scanner = SecurityScanner()
        result = scanner.run_bandit_scan()
        assert result == 0

    @patch('subprocess.call')
    def test_run_safety_scan(self, mock_call):
        """Test running safety scan."""
        mock_call.return_value = 0
        scanner = SecurityScanner()
        result = scanner.run_safety_scan()
        assert result == 0

    @patch('subprocess.call')
    def test_run_all_security_checks(self, mock_call):
        """Test running all security checks."""
        mock_call.return_value = 0
        scanner = SecurityScanner()
        result = scanner.run_all_security_checks()
        assert result == 0


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""

    def test_vulnerability_checker_init(self):
        """Test VulnerabilityChecker initialization."""
        checker = VulnerabilityChecker()
        assert checker.checker_name == "Vulnerability Checker"
        assert "low" in checker.severity_levels

    def test_check_vulnerability_patterns(self):
        """Test checking vulnerability patterns."""
        checker = VulnerabilityChecker()
        result = checker.check_vulnerability_patterns("password = 'secret'", "test.py")
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0

    def test_check_sql_injection_patterns(self):
        """Test checking SQL injection patterns."""
        checker = VulnerabilityChecker()
        result = checker.check_sql_injection_patterns("f\"SELECT * FROM users WHERE id = {user_id}\"", "test.py")
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0

    def test_check_xss_patterns(self):
        """Test checking XSS patterns."""
        checker = VulnerabilityChecker()
        result = checker.check_xss_patterns("f\"Hello {request.GET['name']}\"", "test.py")
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_dependency_analyzer_init(self):
        """Test DependencyAnalyzer initialization."""
        analyzer = DependencyAnalyzer()
        assert analyzer.analyzer_name == "Dependency Analyzer"
        assert analyzer.requirements_file == "requirements.txt"

    def test_analyze_requirements_file(self):
        """Test analyzing requirements file."""
        analyzer = DependencyAnalyzer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            req_file = os.path.join(temp_dir, "requirements.txt")
            with open(req_file, 'w') as f:
                f.write("requests==2.25.1\npytest==6.0.0\n")
            
            result = analyzer.analyze_requirements_file(req_file)
            assert result["success"] is True
            assert len(result["packages"]) == 2

    def test_check_package_vulnerabilities(self):
        """Test checking package vulnerabilities."""
        analyzer = DependencyAnalyzer()
        packages = [{"name": "requests", "version": "2.25.1"}]
        result = analyzer.check_package_vulnerabilities(packages)
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""

    def test_security_pattern_analyzer_init(self):
        """Test SecurityPatternAnalyzer initialization."""
        analyzer = SecurityPatternAnalyzer()
        assert analyzer.analyzer_name == "Security Pattern Analyzer"
        assert len(analyzer.patterns) > 0

    def test_analyze_code_patterns(self):
        """Test analyzing code patterns."""
        analyzer = SecurityPatternAnalyzer()
        result = analyzer.analyze_code_patterns("os.system('rm -rf /')", "test.py")
        assert result["success"] is True
        assert len(result["patterns"]) > 0

    def test_check_hardcoded_secrets(self):
        """Test checking hardcoded secrets."""
        analyzer = SecurityPatternAnalyzer()
        result = analyzer.check_hardcoded_secrets("sk-1234567890abcdef", "test.py")
        assert result["success"] is True
        assert len(result["patterns"]) > 0

    def test_check_dangerous_functions(self):
        """Test checking dangerous functions."""
        analyzer = SecurityPatternAnalyzer()
        result = analyzer.check_dangerous_functions("eval('malicious_code')", "test.py")
        assert result["success"] is True
        assert len(result["patterns"]) > 0


class TestSecurityFunctions:
    """Test security functions."""

    @patch('subprocess.call')
    def test_run_bandit(self, mock_call):
        """Test run_bandit function."""
        mock_call.return_value = 0
        result = run_bandit()
        assert result == 0

    @patch('subprocess.call')
    def test_run_safety_check(self, mock_call):
        """Test run_safety_check function."""
        mock_call.return_value = 0
        result = run_safety_check()
        assert result == 0

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities(self, mock_run):
        """Test scan_for_vulnerabilities function."""
        mock_run.return_value = MagicMock(returncode=0, stdout='[]')
        result = scan_for_vulnerabilities(["test.py"])
        assert result["success"] is True

    @patch('subprocess.run')
    def test_check_dependencies(self, mock_run):
        """Test check_dependencies function."""
        mock_run.return_value = MagicMock(returncode=0, stdout='[]')
        result = check_dependencies()
        assert result["success"] is True

    def test_analyze_security_patterns(self):
        """Test analyze_security_patterns function."""
        result = analyze_security_patterns("password = 'secret'", "test.py")
        assert result["success"] is True
        assert len(result["patterns"]) > 0


class TestTestsRunner:
    """Test TestsRunner class."""

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None

    @patch('subprocess.call')
    def test_run_pytest(self, mock_call):
        """Test running pytest."""
        mock_call.return_value = 0
        runner = TestsRunner()
        result = runner.run_pytest()
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_coverage(self, mock_call):
        """Test running pytest with coverage."""
        mock_call.return_value = 0
        runner = TestsRunner()
        result = runner.run_pytest_with_coverage()
        assert result == 0

    @patch('subprocess.call')
    def test_run_tests(self, mock_call):
        """Test running tests."""
        mock_call.return_value = 0
        runner = TestsRunner()
        result = runner.run_tests()
        assert result == 0


class TestTestRunner:
    """Test TestRunner class."""

    def test_test_runner_init(self):
        """Test TestRunner initialization."""
        runner = TestRunner()
        assert runner.runner_name == "Test Runner"
        assert runner.test_command == "pytest"

    @patch('subprocess.run')
    def test_run_test_file(self, mock_run):
        """Test running a test file."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test PASSED")
        runner = TestRunner()
        result = runner.run_test_file("test_file.py")
        assert result["success"] is True

    @patch('subprocess.run')
    def test_run_test_directory(self, mock_run):
        """Test running tests in a directory."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test PASSED")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_example.py")
            with open(test_file, 'w') as f:
                f.write("def test_example(): pass")
            
            runner = TestRunner()
            result = runner.run_test_directory(temp_dir)
            assert result["success"] is True

    def test_discover_test_files(self):
        """Test discovering test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_example.py")
            with open(test_file, 'w') as f:
                f.write("def test_example(): pass")
            
            runner = TestRunner()
            result = runner.discover_test_files(temp_dir)
            assert result["success"] is True
            assert len(result["test_files"]) > 0


class TestTestDiscoverer:
    """Test TestDiscoverer class."""

    def test_test_discoverer_init(self):
        """Test TestDiscoverer initialization."""
        discoverer = TestDiscoverer()
        assert discoverer.discoverer_name == "Test Discoverer"
        assert len(discoverer.test_patterns) > 0

    def test_discover_test_files(self):
        """Test discovering test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_example.py")
            with open(test_file, 'w') as f:
                f.write("def test_example(): pass")
            
            discoverer = TestDiscoverer()
            result = discoverer.discover_test_files(temp_dir)
            assert result["success"] is True
            assert len(result["test_files"]) > 0


class TestTestExecutor:
    """Test TestExecutor class."""

    def test_test_executor_init(self):
        """Test TestExecutor initialization."""
        executor = TestExecutor()
        assert executor.executor_name == "Test Executor"
        assert executor.timeout == 300

    @patch('subprocess.run')
    def test_execute_tests(self, mock_run):
        """Test executing tests."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test PASSED")
        executor = TestExecutor()
        result = executor.execute_tests(["test_file.py"])
        assert result["success"] is True

    @patch('subprocess.run')
    def test_run_pytest(self, mock_run):
        """Test running pytest."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test PASSED")
        executor = TestExecutor()
        result = executor._run_pytest(["test_file.py"])
        assert result["success"] is True


class TestTestFunctions:
    """Test test functions."""

    @patch('subprocess.call')
    def test_run_pytest_function(self, mock_call):
        """Test run_pytest function."""
        mock_call.return_value = 0
        result = run_pytest()
        assert result == 0

    @patch('subprocess.call')
    def test_run_pytest_with_coverage_function(self, mock_call):
        """Test run_pytest_with_coverage function."""
        mock_call.return_value = 0
        result = run_pytest_with_coverage()
        assert result == 0

    @patch('subprocess.run')
    def test_run_tests_function(self, mock_run):
        """Test run_tests function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test PASSED")
        result = run_tests(["test_file.py"])
        assert result["success"] is True

    def test_discover_test_files_function(self):
        """Test discover_test_files function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_example.py")
            with open(test_file, 'w') as f:
                f.write("def test_example(): pass")
            
            result = discover_test_files(temp_dir)
            assert result["success"] is True
            assert len(result["test_files"]) > 0

    @patch('subprocess.run')
    def test_execute_test_suite(self, mock_run):
        """Test execute_test_suite function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test PASSED")
        result = execute_test_suite(["test_file.py"])
        assert result["success"] is True
