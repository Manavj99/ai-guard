"""Additional tests for security scanner and tests runner modules."""

import pytest
import subprocess
import json
from unittest.mock import patch, MagicMock, mock_open
from ai_guard.security_scanner import (
    scan_for_vulnerabilities,
    check_dependencies,
    analyze_security_patterns,
    SecurityScanner,
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer
)
from ai_guard.tests_runner import (
    run_tests,
    discover_test_files,
    execute_test_suite,
    TestRunner,
    TestDiscoverer,
    TestExecutor
)


class TestSecurityScanner:
    """Test security scanner functionality."""

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_success(self, mock_run):
        """Test successful vulnerability scanning."""
        mock_output = json.dumps([
            {
                "vulnerability": "SQL Injection",
                "severity": "high",
                "file": "test.py",
                "line": 10,
                "description": "Potential SQL injection vulnerability"
            }
        ])
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        result = scan_for_vulnerabilities(["test.py"])
        
        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["vulnerability"] == "SQL Injection"
        assert result["vulnerabilities"][0]["severity"] == "high"

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_failure(self, mock_run):
        """Test vulnerability scanning failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bandit")
        
        result = scan_for_vulnerabilities(["test.py"])
        
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_check_dependencies_success(self, mock_run):
        """Test successful dependency checking."""
        mock_output = json.dumps([
            {
                "package": "requests",
                "version": "2.25.1",
                "vulnerabilities": [
                    {
                        "id": "CVE-2021-1234",
                        "severity": "medium",
                        "description": "Security vulnerability in requests"
                    }
                ]
            }
        ])
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        result = check_dependencies()
        
        assert result["success"] is True
        assert len(result["packages"]) == 1
        assert result["packages"][0]["package"] == "requests"
        assert len(result["packages"][0]["vulnerabilities"]) == 1

    @patch('subprocess.run')
    def test_check_dependencies_failure(self, mock_run):
        """Test dependency checking failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip-audit")
        
        result = check_dependencies()
        
        assert result["success"] is False
        assert "error" in result

    def test_analyze_security_patterns_success(self):
        """Test successful security pattern analysis."""
        code_content = """
        import sqlite3
        user_input = input("Enter name: ")
        query = f"SELECT * FROM users WHERE name = '{user_input}'"
        cursor.execute(query)
        """
        
        result = analyze_security_patterns(code_content, "test.py")
        
        assert result["success"] is True
        assert len(result["patterns"]) > 0
        # Should detect SQL injection pattern
        sql_patterns = [p for p in result["patterns"] if "sql" in p["type"].lower()]
        assert len(sql_patterns) > 0

    def test_analyze_security_patterns_no_issues(self):
        """Test security pattern analysis with no issues."""
        code_content = """
        def safe_function():
            return "Hello World"
        """
        
        result = analyze_security_patterns(code_content, "test.py")
        
        assert result["success"] is True
        assert len(result["patterns"]) == 0


class TestSecurityScannerClass:
    """Test SecurityScanner class."""

    def test_scanner_init(self):
        """Test scanner initialization."""
        scanner = SecurityScanner()
        
        assert scanner.scanner_name == "Security Scanner"
        assert scanner.supported_tools == ["bandit", "pip-audit"]

    def test_scan_file_success(self):
        """Test successful file scanning."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, '_run_bandit_scan') as mock_scan:
            mock_scan.return_value = {
                "success": True,
                "vulnerabilities": [
                    {
                        "vulnerability": "Hardcoded Password",
                        "severity": "medium",
                        "line": 5
                    }
                ]
            }
            
            result = scanner.scan_file("test.py")
            
            assert result["success"] is True
            assert len(result["vulnerabilities"]) == 1
            assert result["vulnerabilities"][0]["vulnerability"] == "Hardcoded Password"

    def test_scan_file_failure(self):
        """Test file scanning failure."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, '_run_bandit_scan') as mock_scan:
            mock_scan.return_value = {"success": False, "error": "Scan failed"}
            
            result = scanner.scan_file("test.py")
            
            assert result["success"] is False
            assert "error" in result

    def test_scan_directory(self):
        """Test directory scanning."""
        scanner = SecurityScanner()
        
        with patch.object(scanner, 'scan_file') as mock_scan_file:
            mock_scan_file.return_value = {
                "success": True,
                "vulnerabilities": []
            }
            
            result = scanner.scan_directory("test_dir")
            
            assert result["success"] is True
            assert "files_scanned" in result
            assert "total_vulnerabilities" in result


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""

    def test_checker_init(self):
        """Test checker initialization."""
        checker = VulnerabilityChecker()
        
        assert checker.checker_name == "Vulnerability Checker"
        assert checker.severity_levels == ["low", "medium", "high", "critical"]

    def test_check_vulnerability_patterns(self):
        """Test vulnerability pattern checking."""
        checker = VulnerabilityChecker()
        
        code_with_vulnerability = """
        password = "admin123"
        query = "SELECT * FROM users WHERE password = '" + password + "'"
        """
        
        result = checker.check_vulnerability_patterns(code_with_vulnerability, "test.py")
        
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0
        
        # Should detect hardcoded password
        password_vulns = [v for v in result["vulnerabilities"] if "password" in v["type"].lower()]
        assert len(password_vulns) > 0

    def test_check_sql_injection_patterns(self):
        """Test SQL injection pattern checking."""
        checker = VulnerabilityChecker()
        
        code_with_sql_injection = """
        user_input = input("Enter name: ")
        query = f"SELECT * FROM users WHERE name = '{user_input}'"
        cursor.execute(query)
        """
        
        result = checker.check_sql_injection_patterns(code_with_sql_injection, "test.py")
        
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0
        
        sql_vulns = [v for v in result["vulnerabilities"] if "sql" in v["type"].lower()]
        assert len(sql_vulns) > 0

    def test_check_xss_patterns(self):
        """Test XSS pattern checking."""
        checker = VulnerabilityChecker()
        
        code_with_xss = """
        user_input = request.GET.get('input')
        html = f"<div>{user_input}</div>"
        return HttpResponse(html)
        """
        
        result = checker.check_xss_patterns(code_with_xss, "test.py")
        
        assert result["success"] is True
        assert len(result["vulnerabilities"]) > 0
        
        xss_vulns = [v for v in result["vulnerabilities"] if "xss" in v["type"].lower()]
        assert len(xss_vulns) > 0


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_analyzer_init(self):
        """Test analyzer initialization."""
        analyzer = DependencyAnalyzer()
        
        assert analyzer.analyzer_name == "Dependency Analyzer"
        assert analyzer.requirements_file == "requirements.txt"

    def test_analyze_requirements_file(self):
        """Test requirements file analysis."""
        analyzer = DependencyAnalyzer()
        
        requirements_content = """
        requests==2.25.1
        django==3.2.0
        pytest==6.2.0
        """
        
        with patch("builtins.open", mock_open(read_data=requirements_content)):
            result = analyzer.analyze_requirements_file("requirements.txt")
        
        assert result["success"] is True
        assert len(result["packages"]) == 3
        assert any(p["name"] == "requests" for p in result["packages"])
        assert any(p["name"] == "django" for p in result["packages"])
        assert any(p["name"] == "pytest" for p in result["packages"])

    def test_analyze_requirements_file_not_found(self):
        """Test requirements file analysis with file not found."""
        analyzer = DependencyAnalyzer()
        
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = analyzer.analyze_requirements_file("nonexistent.txt")
        
        assert result["success"] is False
        assert "error" in result

    def test_check_package_vulnerabilities(self):
        """Test package vulnerability checking."""
        analyzer = DependencyAnalyzer()
        
        packages = [
            {"name": "requests", "version": "2.25.1"},
            {"name": "django", "version": "3.2.0"}
        ]
        
        with patch.object(analyzer, '_run_pip_audit') as mock_audit:
            mock_audit.return_value = {
                "success": True,
                "vulnerabilities": [
                    {
                        "package": "requests",
                        "vulnerability": "CVE-2021-1234",
                        "severity": "medium"
                    }
                ]
            }
            
            result = analyzer.check_package_vulnerabilities(packages)
            
            assert result["success"] is True
            assert len(result["vulnerabilities"]) == 1
            assert result["vulnerabilities"][0]["package"] == "requests"


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""

    def test_analyzer_init(self):
        """Test analyzer initialization."""
        analyzer = SecurityPatternAnalyzer()
        
        assert analyzer.analyzer_name == "Security Pattern Analyzer"
        assert len(analyzer.patterns) > 0

    def test_analyze_code_patterns(self):
        """Test code pattern analysis."""
        analyzer = SecurityPatternAnalyzer()
        
        code_with_patterns = """
        import os
        password = "secret123"
        os.system("rm -rf /")
        eval(user_input)
        """
        
        result = analyzer.analyze_code_patterns(code_with_patterns, "test.py")
        
        assert result["success"] is True
        assert len(result["patterns"]) > 0
        
        # Should detect dangerous patterns
        dangerous_patterns = [p for p in result["patterns"] if p["severity"] in ["high", "critical"]]
        assert len(dangerous_patterns) > 0

    def test_check_hardcoded_secrets(self):
        """Test hardcoded secrets checking."""
        analyzer = SecurityPatternAnalyzer()
        
        code_with_secrets = """
        api_key = "sk-1234567890abcdef"
        password = "admin123"
        secret_token = "secret123"
        """
        
        result = analyzer.check_hardcoded_secrets(code_with_secrets, "test.py")
        
        assert result["success"] is True
        assert len(result["patterns"]) > 0
        
        secret_patterns = [p for p in result["patterns"] if "secret" in p["type"].lower() or "password" in p["type"].lower()]
        assert len(secret_patterns) > 0

    def test_check_dangerous_functions(self):
        """Test dangerous functions checking."""
        analyzer = SecurityPatternAnalyzer()
        
        code_with_dangerous_functions = """
        import os
        import subprocess
        
        os.system("rm -rf /")
        subprocess.call(["rm", "-rf", "/"])
        eval("malicious_code()")
        exec("malicious_code()")
        """
        
        result = analyzer.check_dangerous_functions(code_with_dangerous_functions, "test.py")
        
        assert result["success"] is True
        assert len(result["patterns"]) > 0
        
        dangerous_patterns = [p for p in result["patterns"] if p["severity"] in ["high", "critical"]]
        assert len(dangerous_patterns) > 0


class TestTestRunner:
    """Test test runner functionality."""

    @patch('subprocess.run')
    def test_run_tests_success(self, mock_run):
        """Test successful test run."""
        mock_output = """
        ========================== test session starts ==========================
        test_file.py::test_function PASSED                                    [100%]
        ========================== 1 passed in 0.01s ==========================
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        result = run_tests(["test_file.py"])
        
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1

    @patch('subprocess.run')
    def test_run_tests_failure(self, mock_run):
        """Test failed test run."""
        mock_output = """
        ========================== test session starts ==========================
        test_file.py::test_function FAILED                                    [100%]
        ========================== 1 failed in 0.01s ==========================
        """
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=mock_output,
            stderr=""
        )
        
        result = run_tests(["test_file.py"])
        
        assert result["success"] is False
        assert result["passed"] == 0
        assert result["failed"] == 1
        assert result["total"] == 1

    @patch('subprocess.run')
    def test_run_tests_error(self, mock_run):
        """Test test run error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")
        
        result = run_tests(["test_file.py"])
        
        assert result["success"] is False
        assert "error" in result

    def test_discover_test_files_success(self):
        """Test successful test file discovery."""
        test_files = ["test_file1.py", "test_file2.py", "test_file3.py"]
        
        with patch("os.listdir") as mock_listdir, \
             patch("os.path.isfile") as mock_isfile:
            mock_listdir.return_value = test_files + ["not_test.py", "other_file.txt"]
            mock_isfile.return_value = True
            
            result = discover_test_files("test_dir")
        
        assert result["success"] is True
        assert len(result["test_files"]) == 3
        assert all(f.startswith("test_") for f in result["test_files"])

    def test_discover_test_files_empty(self):
        """Test test file discovery with no test files."""
        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = ["not_test.py", "other_file.txt"]
            
            result = discover_test_files("test_dir")
        
        assert result["success"] is True
        assert len(result["test_files"]) == 0

    def test_execute_test_suite_success(self):
        """Test successful test suite execution."""
        test_files = ["test_file1.py", "test_file2.py"]
        
        with patch('ai_guard.tests_runner.run_tests') as mock_run_tests:
            mock_run_tests.return_value = {
                "success": True,
                "passed": 5,
                "failed": 0,
                "total": 5
            }
            
            result = execute_test_suite(test_files)
        
        assert result["success"] is True
        assert result["passed"] == 5
        assert result["failed"] == 0
        assert result["total"] == 5

    def test_execute_test_suite_failure(self):
        """Test test suite execution failure."""
        test_files = ["test_file1.py", "test_file2.py"]
        
        with patch('ai_guard.tests_runner.run_tests') as mock_run_tests:
            mock_run_tests.return_value = {
                "success": False,
                "error": "Test execution failed"
            }
            
            result = execute_test_suite(test_files)
        
        assert result["success"] is False
        assert "error" in result


class TestTestRunnerClass:
    """Test TestRunner class."""

    def test_runner_init(self):
        """Test runner initialization."""
        runner = TestRunner()
        
        assert runner.runner_name == "Test Runner"
        assert runner.test_command == "pytest"
        assert runner.test_pattern == "test_*.py"

    def test_run_test_file(self):
        """Test running a single test file."""
        runner = TestRunner()
        
        with patch.object(runner, '_execute_test_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "passed": 3,
                "failed": 0,
                "total": 3
            }
            
            result = runner.run_test_file("test_file.py")
            
            assert result["success"] is True
            assert result["passed"] == 3
            assert result["failed"] == 0

    def test_run_test_directory(self):
        """Test running tests in a directory."""
        runner = TestRunner()
        
        with patch.object(runner, 'discover_test_files') as mock_discover, \
             patch.object(runner, 'run_test_file') as mock_run:
            mock_discover.return_value = {
                "success": True,
                "test_files": ["test_file1.py", "test_file2.py"]
            }
            mock_run.return_value = {
                "success": True,
                "passed": 2,
                "failed": 0,
                "total": 2
            }
            
            result = runner.run_test_directory("test_dir")
            
            assert result["success"] is True
            assert result["files_run"] == 2
            assert result["total_passed"] == 4
            assert result["total_failed"] == 0

    def test_run_test_directory_no_files(self):
        """Test running tests in directory with no test files."""
        runner = TestRunner()
        
        with patch.object(runner, 'discover_test_files') as mock_discover:
            mock_discover.return_value = {
                "success": True,
                "test_files": []
            }
            
            result = runner.run_test_directory("test_dir")
            
            assert result["success"] is True
            assert result["files_run"] == 0
            assert result["total_passed"] == 0
            assert result["total_failed"] == 0


class TestTestDiscoverer:
    """Test TestDiscoverer class."""

    def test_discoverer_init(self):
        """Test discoverer initialization."""
        discoverer = TestDiscoverer()
        
        assert discoverer.discoverer_name == "Test Discoverer"
        assert discoverer.test_patterns == ["test_*.py", "*_test.py"]

    def test_discover_test_files(self):
        """Test test file discovery."""
        discoverer = TestDiscoverer()
        
        with patch("os.listdir") as mock_listdir, \
             patch("os.path.isfile") as mock_isfile:
            mock_listdir.return_value = [
                "test_file1.py",
                "test_file2.py",
                "other_file.py",
                "not_test.txt"
            ]
            mock_isfile.return_value = True
            
            result = discoverer.discover_test_files("test_dir")
        
        assert result["success"] is True
        assert len(result["test_files"]) == 2
        assert "test_file1.py" in result["test_files"]
        assert "test_file2.py" in result["test_files"]

    def test_discover_test_files_recursive(self):
        """Test recursive test file discovery."""
        discoverer = TestDiscoverer()
        
        with patch("os.walk") as mock_walk:
            mock_walk.return_value = [
                ("test_dir", [], ["test_file1.py", "other_file.py"]),
                ("test_dir/subdir", [], ["test_file2.py", "not_test.txt"])
            ]
            
            result = discoverer.discover_test_files("test_dir", recursive=True)
        
        assert result["success"] is True
        assert len(result["test_files"]) == 2
        assert "test_file1.py" in result["test_files"]
        assert "test_file2.py" in result["test_files"]


class TestTestExecutor:
    """Test TestExecutor class."""

    def test_executor_init(self):
        """Test executor initialization."""
        executor = TestExecutor()
        
        assert executor.executor_name == "Test Executor"
        assert executor.timeout == 300

    def test_execute_tests(self):
        """Test test execution."""
        executor = TestExecutor()
        
        with patch.object(executor, '_run_pytest') as mock_run:
            mock_run.return_value = {
                "success": True,
                "passed": 5,
                "failed": 1,
                "total": 6
            }
            
            result = executor.execute_tests(["test_file1.py", "test_file2.py"])
            
            assert result["success"] is True
            assert result["passed"] == 5
            assert result["failed"] == 1
            assert result["total"] == 6

    def test_execute_tests_timeout(self):
        """Test test execution with timeout."""
        executor = TestExecutor(timeout=1)
        
        with patch.object(executor, '_run_pytest') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("pytest", 1)
            
            result = executor.execute_tests(["test_file.py"])
            
            assert result["success"] is False
            assert "timeout" in result["error"].lower()

    def test_execute_tests_error(self):
        """Test test execution error."""
        executor = TestExecutor()
        
        with patch.object(executor, '_run_pytest') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")
            
            result = executor.execute_tests(["test_file.py"])
            
            assert result["success"] is False
            assert "error" in result
