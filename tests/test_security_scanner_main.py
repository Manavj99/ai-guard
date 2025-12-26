"""Comprehensive tests for AI Guard security scanner main module."""

import tempfile
import os
import json
import pytest
import subprocess
from unittest.mock import patch, mock_open, MagicMock
from src.ai_guard.security_scanner import (
    run_bandit,
    run_safety_check,
    SecurityScanner,
    scan_for_vulnerabilities,
    check_dependencies,
    analyze_security_patterns,
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer,
)


class TestRunBandit:
    """Test run_bandit function."""

    @patch("subprocess.call")
    def test_run_bandit_with_config_file(self, mock_call):
        """Test run_bandit with .bandit config file."""
        mock_call.return_value = 0

        with patch("os.path.exists", return_value=True):
            result = run_bandit()

        expected_cmd = ["bandit", "-r", "src", "-c", ".bandit"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_run_bandit_without_config_file(self, mock_call):
        """Test run_bandit without .bandit config file."""
        mock_call.return_value = 0

        with patch("os.path.exists", return_value=False):
            result = run_bandit()

        expected_cmd = ["bandit", "-r", "src", "-f", "json", "-ll"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_run_bandit_with_extra_args(self, mock_call):
        """Test run_bandit with extra arguments."""
        mock_call.return_value = 0

        with patch("os.path.exists", return_value=False):
            result = run_bandit(["-v", "--skip", "B101"])

        expected_cmd = [
            "bandit",
            "-r",
            "src",
            "-f",
            "json",
            "-ll",
            "-v",
            "--skip",
            "B101",
        ]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0

    @patch("subprocess.call")
    def test_run_bandit_with_none_extra_args(self, mock_call):
        """Test run_bandit with None extra arguments."""
        mock_call.return_value = 0

        with patch("os.path.exists", return_value=False):
            result = run_bandit(None)

        expected_cmd = ["bandit", "-r", "src", "-f", "json", "-ll"]
        mock_call.assert_called_once_with(expected_cmd)
        assert result == 0


class TestRunSafetyCheck:
    """Test run_safety_check function."""

    @patch("subprocess.call")
    def test_run_safety_check_success(self, mock_call):
        """Test successful safety check."""
        mock_call.return_value = 0

        result = run_safety_check()

        mock_call.assert_called_once_with(["safety", "check"])
        assert result == 0

    @patch("subprocess.call")
    def test_run_safety_check_file_not_found(self, mock_call):
        """Test safety check when safety is not installed."""
        mock_call.side_effect = FileNotFoundError()

        with patch("builtins.print") as mock_print:
            result = run_safety_check()

        mock_print.assert_called_once_with(
            "Warning: safety not installed, skipping dependency security check"
        )
        assert result == 0

    @patch("subprocess.call")
    def test_run_safety_check_exception(self, mock_call):
        """Test safety check with general exception."""
        mock_call.side_effect = Exception("Test error")

        with patch("builtins.print") as mock_print:
            result = run_safety_check()

        mock_print.assert_called_once_with(
            "Warning: Error running safety check: Test error"
        )
        assert result == 0


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_scanner_initialization(self):
        """Test scanner initialization."""
        scanner = SecurityScanner()

        assert scanner.issues == []

    def test_add_issue(self):
        """Test adding security issue."""
        scanner = SecurityScanner()

        scanner.add_issue("test.py", 10, "Test issue", "high")

        assert len(scanner.issues) == 1
        assert scanner.issues[0] == {
            "file": "test.py",
            "line": 10,
            "message": "Test issue",
            "severity": "high",
        }

    @patch("src.ai_guard.security_scanner.run_bandit")
    def test_run_bandit_scan(self, mock_run_bandit):
        """Test running bandit scan."""
        mock_run_bandit.return_value = 0
        scanner = SecurityScanner()

        result = scanner.run_bandit_scan()

        mock_run_bandit.assert_called_once_with(None)
        assert result == 0

    @patch("src.ai_guard.security_scanner.run_bandit")
    def test_run_bandit_scan_with_args(self, mock_run_bandit):
        """Test running bandit scan with extra arguments."""
        mock_run_bandit.return_value = 0
        scanner = SecurityScanner()

        result = scanner.run_bandit_scan(["-v"])

        mock_run_bandit.assert_called_once_with(["-v"])
        assert result == 0

    @patch("src.ai_guard.security_scanner.run_safety_check")
    def test_run_safety_scan(self, mock_run_safety):
        """Test running safety scan."""
        mock_run_safety.return_value = 0
        scanner = SecurityScanner()

        result = scanner.run_safety_scan()

        mock_run_safety.assert_called_once()
        assert result == 0

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("src.ai_guard.security_scanner.run_bandit")
    def test_run_all_security_checks_both_pass(self, mock_run_bandit, mock_run_safety):
        """Test running all security checks when both pass."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 0
        scanner = SecurityScanner()

        result = scanner.run_all_security_checks()

        assert result == 0

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("src.ai_guard.security_scanner.run_bandit")
    def test_run_all_security_checks_bandit_fails(
        self, mock_run_bandit, mock_run_safety
    ):
        """Test running all security checks when bandit fails."""
        mock_run_bandit.return_value = 1
        mock_run_safety.return_value = 0
        scanner = SecurityScanner()

        result = scanner.run_all_security_checks()

        assert result == 1

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("src.ai_guard.security_scanner.run_bandit")
    def test_run_all_security_checks_safety_fails(
        self, mock_run_bandit, mock_run_safety
    ):
        """Test running all security checks when safety fails."""
        mock_run_bandit.return_value = 0
        mock_run_safety.return_value = 1
        scanner = SecurityScanner()

        result = scanner.run_all_security_checks()

        assert result == 1

    @patch("src.ai_guard.security_scanner.scan_for_vulnerabilities")
    def test_scan_file_success(self, mock_scan):
        """Test scanning a single file successfully."""
        mock_scan.return_value = {"success": True, "vulnerabilities": []}
        scanner = SecurityScanner()

        result = scanner.scan_file("test.py")

        mock_scan.assert_called_once_with(["test.py"])
        assert result == {"success": True, "vulnerabilities": []}

    @patch("src.ai_guard.security_scanner.scan_for_vulnerabilities")
    def test_scan_file_exception(self, mock_scan):
        """Test scanning a single file with exception."""
        mock_scan.side_effect = Exception("Test error")
        scanner = SecurityScanner()

        result = scanner.scan_file("test.py")

        assert result == {"success": False, "error": "Test error", "file": "test.py"}

    @patch("src.ai_guard.security_scanner.scan_for_vulnerabilities")
    def test_scan_directory_success(self, mock_scan):
        """Test scanning a directory successfully."""
        mock_scan.return_value = {"success": True, "vulnerabilities": []}
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("print('hello')")

            result = scanner.scan_directory(temp_dir)

            mock_scan.assert_called_once()
            assert result == {"success": True, "vulnerabilities": []}

    @patch("src.ai_guard.security_scanner.scan_for_vulnerabilities")
    def test_scan_directory_no_python_files(self, mock_scan):
        """Test scanning a directory with no Python files."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a non-Python file
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("hello")

            result = scanner.scan_directory(temp_dir)

            mock_scan.assert_not_called()
            assert result == {
                "success": True,
                "files_scanned": 0,
                "message": "No Python files found",
            }

    @patch("src.ai_guard.security_scanner.scan_for_vulnerabilities")
    def test_scan_directory_exception(self, mock_scan):
        """Test scanning a directory with exception."""
        mock_scan.side_effect = Exception("Test error")
        scanner = SecurityScanner()

        # Use a directory that exists and has Python files to trigger scan_for_vulnerabilities
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Python file to ensure scan_for_vulnerabilities is called
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("print('hello')")

            result = scanner.scan_directory(temp_dir)

        assert result == {
            "success": False,
            "error": "Test error",
            "directory": temp_dir,
        }


class TestScanForVulnerabilities:
    """Test scan_for_vulnerabilities function."""

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("subprocess.run")
    def test_scan_for_vulnerabilities_success(self, mock_run, mock_safety):
        """Test successful vulnerability scan."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"results": []}', stderr=""
        )
        mock_safety.return_value = 0

        result = scan_for_vulnerabilities(["test.py"])

        assert result["success"] is True
        assert result["files_scanned"] == 1
        assert result["bandit"]["exit_code"] == 0
        assert result["safety"]["exit_code"] == 0

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("subprocess.run")
    def test_scan_for_vulnerabilities_timeout(self, mock_run, mock_safety):
        """Test vulnerability scan with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("bandit", 300)

        result = scan_for_vulnerabilities(["test.py"])

        assert result == {"success": False, "error": "Scan timeout"}

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("subprocess.run")
    def test_scan_for_vulnerabilities_called_process_error(self, mock_run, mock_safety):
        """Test vulnerability scan with CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bandit")

        result = scan_for_vulnerabilities(["test.py"])

        assert result["success"] is False
        assert "Command 'bandit' returned non-zero exit status 1" in result["error"]

    @patch("src.ai_guard.security_scanner.run_safety_check")
    @patch("subprocess.run")
    def test_scan_for_vulnerabilities_general_exception(self, mock_run, mock_safety):
        """Test vulnerability scan with general exception."""
        mock_run.side_effect = Exception("Test error")

        result = scan_for_vulnerabilities(["test.py"])

        assert result == {"success": False, "error": "Test error"}


class TestCheckDependencies:
    """Test check_dependencies function."""

    @patch("src.ai_guard.security_scanner.run_safety_check")
    def test_check_dependencies_success(self, mock_safety):
        """Test successful dependency check."""
        mock_safety.return_value = 0

        result = check_dependencies()

        assert result["success"] is True
        assert result["safety_check"]["exit_code"] == 0

    @patch("src.ai_guard.security_scanner.run_safety_check")
    def test_check_dependencies_failure(self, mock_safety):
        """Test dependency check failure."""
        mock_safety.return_value = 1

        result = check_dependencies()

        assert result["success"] is False
        assert result["safety_check"]["exit_code"] == 1

    @patch("src.ai_guard.security_scanner.run_safety_check")
    def test_check_dependencies_exception(self, mock_safety):
        """Test dependency check with exception."""
        mock_safety.side_effect = Exception("Test error")

        result = check_dependencies()

        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["safety_check"]["exit_code"] == 1


class TestAnalyzeSecurityPatterns:
    """Test analyze_security_patterns function."""

    def test_analyze_sql_injection_pattern(self):
        """Test SQL injection pattern detection."""
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'

        result = analyze_security_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "sql_injection"
        assert result["patterns"][0]["severity"] == "high"

    def test_analyze_hardcoded_password_pattern(self):
        """Test hardcoded password pattern detection."""
        code = 'password = "secret123"'

        result = analyze_security_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "hardcoded_password"
        assert result["patterns"][0]["severity"] == "medium"

    def test_analyze_dangerous_functions(self):
        """Test dangerous function detection."""
        code = "result = eval(user_input)"

        result = analyze_security_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "dangerous_function"
        assert result["patterns"][0]["severity"] == "high"

    def test_analyze_multiple_patterns(self):
        """Test multiple pattern detection."""
        code = """
        password = "secret"
        query = f"SELECT * FROM users WHERE id = {user_id}"
        result = eval(user_input)
        """

        result = analyze_security_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 3
        assert result["risk_level"] == "high"

    def test_analyze_no_patterns(self):
        """Test code with no security patterns."""
        code = 'def safe_function():\n    return "safe"'

        result = analyze_security_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 0
        assert result["risk_level"] == "low"

    def test_analyze_risk_level_calculation(self):
        """Test risk level calculation."""
        # High severity only
        code = "result = eval(user_input)"
        result = analyze_security_patterns(code, "test.py")
        assert result["risk_level"] == "high"

        # Medium severity only
        code = 'password = "secret"'
        result = analyze_security_patterns(code, "test.py")
        assert result["risk_level"] == "medium"

        # No patterns
        code = "def safe(): pass"
        result = analyze_security_patterns(code, "test.py")
        assert result["risk_level"] == "low"


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""

    def test_checker_initialization(self):
        """Test checker initialization."""
        checker = VulnerabilityChecker()

        assert checker.checker_name == "Vulnerability Checker"
        assert checker.severity_levels == ["low", "medium", "high", "critical"]

    @patch("src.ai_guard.security_scanner.scan_for_vulnerabilities")
    def test_check_vulnerabilities(self, mock_scan):
        """Test checking vulnerabilities in multiple files."""
        mock_scan.return_value = {"success": True, "vulnerabilities": []}
        checker = VulnerabilityChecker()

        result = checker.check_vulnerabilities(["test.py"])

        mock_scan.assert_called_once_with(["test.py"])
        assert result == {"success": True, "vulnerabilities": []}

    @patch("src.ai_guard.security_scanner.analyze_security_patterns")
    def test_check_file_vulnerabilities(self, mock_analyze):
        """Test checking vulnerabilities in a single file."""
        mock_analyze.return_value = {"success": True, "patterns": []}
        checker = VulnerabilityChecker()

        result = checker.check_file_vulnerabilities("code", "test.py")

        mock_analyze.assert_called_once_with("code", "test.py")
        assert result == {"success": True, "patterns": []}

    def test_check_vulnerability_patterns_hardcoded_password(self):
        """Test checking for hardcoded password patterns."""
        checker = VulnerabilityChecker()
        code = 'password = "secret"'

        result = checker.check_vulnerability_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["type"] == "hardcoded_password"

    def test_check_vulnerability_patterns_no_password(self):
        """Test checking code without hardcoded password."""
        checker = VulnerabilityChecker()
        code = "def safe(): pass"

        result = checker.check_vulnerability_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 0

    def test_check_sql_injection_patterns(self):
        """Test checking for SQL injection patterns."""
        checker = VulnerabilityChecker()
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'

        result = checker.check_sql_injection_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["type"] == "sql_injection"

    def test_check_sql_injection_patterns_no_sql(self):
        """Test checking code without SQL injection patterns."""
        checker = VulnerabilityChecker()
        code = "def safe(): pass"

        result = checker.check_sql_injection_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 0

    def test_check_xss_patterns(self):
        """Test checking for XSS patterns."""
        checker = VulnerabilityChecker()
        code = "html = f\"<div>{request.GET.get('name')}</div>\""

        result = checker.check_xss_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["type"] == "xss"

    def test_check_xss_patterns_no_xss(self):
        """Test checking code without XSS patterns."""
        checker = VulnerabilityChecker()
        code = "def safe(): pass"

        result = checker.check_xss_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 0


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = DependencyAnalyzer()

        assert analyzer.analyzer_name == "Dependency Analyzer"
        assert analyzer.requirements_file == "requirements.txt"

    @patch("src.ai_guard.security_scanner.check_dependencies")
    def test_analyze_dependencies(self, mock_check):
        """Test analyzing dependencies."""
        mock_check.return_value = {"success": True}
        analyzer = DependencyAnalyzer()

        result = analyzer.analyze_dependencies()

        mock_check.assert_called_once()
        assert result == {"success": True}

    def test_check_package_vulnerabilities_list_input(self):
        """Test checking package vulnerabilities with list input."""
        analyzer = DependencyAnalyzer()
        packages = [{"name": "requests", "version": "2.25.1"}]

        result = analyzer.check_package_vulnerabilities(packages)

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["package"] == "requests"

    def test_analyze_requirements_file_success(self):
        """Test analyzing requirements file successfully."""
        analyzer = DependencyAnalyzer()

        requirements_content = "requests==2.25.1\nnumpy==1.21.0\n# comment\n"

        with patch("builtins.open", mock_open(read_data=requirements_content)):
            result = analyzer.analyze_requirements_file("requirements.txt")

        assert result["success"] is True
        assert len(result["packages"]) == 2
        assert result["packages"][0] == {"name": "requests", "version": "2.25.1"}
        assert result["packages"][1] == {"name": "numpy", "version": "1.21.0"}

    def test_analyze_requirements_file_not_found(self):
        """Test analyzing requirements file that doesn't exist."""
        analyzer = DependencyAnalyzer()

        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = analyzer.analyze_requirements_file("nonexistent.txt")

        assert result["success"] is False
        assert result["error"] == "Requirements file not found"

    def test_analyze_requirements_file_exception(self):
        """Test analyzing requirements file with exception."""
        analyzer = DependencyAnalyzer()

        with patch("builtins.open", side_effect=Exception("Test error")):
            result = analyzer.analyze_requirements_file("requirements.txt")

        assert result["success"] is False
        assert result["error"] == "Test error"

    def test_check_package_vulnerabilities_list(self):
        """Test checking package vulnerabilities with list input."""
        analyzer = DependencyAnalyzer()
        packages = [
            {"name": "requests", "version": "2.25.1"},
            {"name": "numpy", "version": "1.21.0"},
        ]

        result = analyzer.check_package_vulnerabilities(packages)

        assert result["success"] is True
        assert len(result["vulnerabilities"]) == 1
        assert result["vulnerabilities"][0]["package"] == "requests"
        assert result["vulnerabilities"][0]["vulnerability"] == "CVE-2021-1234"


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = SecurityPatternAnalyzer()

        assert analyzer.analyzer_name == "Security Pattern Analyzer"
        assert len(analyzer.patterns) == 4

    @patch("src.ai_guard.security_scanner.analyze_security_patterns")
    def test_analyze_patterns(self, mock_analyze):
        """Test analyzing security patterns."""
        mock_analyze.return_value = {"success": True, "patterns": []}
        analyzer = SecurityPatternAnalyzer()

        result = analyzer.analyze_patterns("code", "test.py")

        mock_analyze.assert_called_once_with("code", "test.py")
        assert result == {"success": True, "patterns": []}

    def test_check_pattern(self):
        """Test checking for a specific pattern."""
        analyzer = SecurityPatternAnalyzer()

        result = analyzer.check_pattern("sql_injection", "test.py")

        assert result["pattern"] == "sql_injection"
        assert result["file"] == "test.py"
        assert result["found"] is False  # "sql_injection" not in "test.py"
        assert result["severity"] == "medium"

    def test_analyze_code_patterns_os_system(self):
        """Test analyzing code patterns for os.system."""
        analyzer = SecurityPatternAnalyzer()
        code = 'os.system("rm -rf /")'

        result = analyzer.analyze_code_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "dangerous_function"
        assert result["patterns"][0]["severity"] == "critical"

    def test_analyze_code_patterns_eval(self):
        """Test analyzing code patterns for eval."""
        analyzer = SecurityPatternAnalyzer()
        code = "result = eval(user_input)"

        result = analyzer.analyze_code_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "dangerous_function"
        assert result["patterns"][0]["severity"] == "critical"

    def test_analyze_code_patterns_multiple(self):
        """Test analyzing code patterns with multiple dangerous functions."""
        analyzer = SecurityPatternAnalyzer()
        code = 'os.system("cmd")\nresult = eval(input)'

        result = analyzer.analyze_code_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 2

    def test_analyze_code_patterns_safe(self):
        """Test analyzing code patterns with safe code."""
        analyzer = SecurityPatternAnalyzer()
        code = "def safe(): pass"

        result = analyzer.analyze_code_patterns(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 0

    def test_check_hardcoded_secrets_api_key(self):
        """Test checking for hardcoded API keys."""
        analyzer = SecurityPatternAnalyzer()
        code = 'api_key = "sk-1234567890"'

        result = analyzer.check_hardcoded_secrets(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "api_key"
        assert result["patterns"][0]["severity"] == "high"

    def test_check_hardcoded_secrets_password(self):
        """Test checking for hardcoded passwords."""
        analyzer = SecurityPatternAnalyzer()
        code = 'password = "secret123"'

        result = analyzer.check_hardcoded_secrets(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 1
        assert result["patterns"][0]["type"] == "password"
        assert result["patterns"][0]["severity"] == "medium"

    def test_check_hardcoded_secrets_multiple(self):
        """Test checking for multiple hardcoded secrets."""
        analyzer = SecurityPatternAnalyzer()
        code = 'api_key = "sk-123"\npassword = "secret"'

        result = analyzer.check_hardcoded_secrets(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 2

    def test_check_dangerous_functions(self):
        """Test checking for dangerous functions."""
        analyzer = SecurityPatternAnalyzer()
        code = 'os.system("cmd")\nsubprocess.call(["ls"])\neval("code")\nexec("code")'

        result = analyzer.check_dangerous_functions(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 4
        for pattern in result["patterns"]:
            assert pattern["type"] == "dangerous_function"
            assert pattern["severity"] == "critical"

    def test_check_dangerous_functions_safe(self):
        """Test checking for dangerous functions in safe code."""
        analyzer = SecurityPatternAnalyzer()
        code = "def safe(): pass"

        result = analyzer.check_dangerous_functions(code, "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 0


# Additional edge case tests
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_scan_for_vulnerabilities_empty_files_list(self):
        """Test scanning with empty files list."""
        result = scan_for_vulnerabilities([])

        assert result["success"] is True
        assert result["files_scanned"] == 0

    def test_analyze_security_patterns_empty_code(self):
        """Test analyzing empty code."""
        result = analyze_security_patterns("", "test.py")

        assert result["success"] is True
        assert len(result["patterns"]) == 0
        assert result["risk_level"] == "low"

    def test_analyze_security_patterns_none_code(self):
        """Test analyzing None code."""
        # This will raise a TypeError, so we expect it to fail
        with pytest.raises(TypeError):
            analyze_security_patterns(None, "test.py")

    def test_security_scanner_add_multiple_issues(self):
        """Test adding multiple issues to scanner."""
        scanner = SecurityScanner()

        scanner.add_issue("file1.py", 1, "Issue 1", "high")
        scanner.add_issue("file2.py", 2, "Issue 2", "medium")
        scanner.add_issue("file3.py", 3, "Issue 3", "low")

        assert len(scanner.issues) == 3
        assert scanner.issues[0]["severity"] == "high"
        assert scanner.issues[1]["severity"] == "medium"
        assert scanner.issues[2]["severity"] == "low"

    def test_vulnerability_checker_empty_files_list(self):
        """Test vulnerability checker with empty files list."""
        checker = VulnerabilityChecker()

        with patch(
            "src.ai_guard.security_scanner.scan_for_vulnerabilities"
        ) as mock_scan:
            mock_scan.return_value = {"success": True, "vulnerabilities": []}
            result = checker.check_vulnerabilities([])

        mock_scan.assert_called_once_with([])
        assert result["success"] is True

    def test_dependency_analyzer_requirements_with_comments_and_empty_lines(self):
        """Test analyzing requirements file with comments and empty lines."""
        analyzer = DependencyAnalyzer()

        requirements_content = """
# This is a comment
requests==2.25.1

# Another comment
numpy==1.21.0

# Empty line above
"""

        with patch("builtins.open", mock_open(read_data=requirements_content)):
            result = analyzer.analyze_requirements_file("requirements.txt")

        assert result["success"] is True
        assert len(result["packages"]) == 2
        assert result["packages"][0]["name"] == "requests"
        assert result["packages"][1]["name"] == "numpy"

    def test_security_pattern_analyzer_check_pattern_in_filename(self):
        """Test checking pattern that exists in filename."""
        analyzer = SecurityPatternAnalyzer()

        result = analyzer.check_pattern("sql_injection", "sql_injection_test.py")

        assert result["pattern"] == "sql_injection"
        assert result["file"] == "sql_injection_test.py"
        assert result["found"] is True  # "sql_injection" in "sql_injection_test.py"
        assert result["severity"] == "medium"
