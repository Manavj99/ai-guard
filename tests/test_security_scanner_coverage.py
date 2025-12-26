"""Comprehensive tests for security_scanner.py to improve coverage."""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.ai_guard.security_scanner import (
    SecurityScanner,
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer,
    run_bandit,
    run_safety_check,
    scan_for_vulnerabilities,
    check_dependencies,
    analyze_security_patterns,
)


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_initialization(self):
        """Test scanner initialization."""
        scanner = SecurityScanner()
        assert scanner.issues == []
        assert scanner.scan_results == {}

    def test_scan_file_nonexistent(self):
        """Test scanning nonexistent file."""
        scanner = SecurityScanner()
        result = scanner.scan_file("nonexistent.py")
        assert result == []

    def test_scan_file_existent(self):
        """Test scanning existent file."""
        scanner = SecurityScanner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nprint('test')")
            temp_file = f.name

        try:
            result = scanner.scan_file(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_scan_directory_nonexistent(self):
        """Test scanning nonexistent directory."""
        scanner = SecurityScanner()
        result = scanner.scan_directory("nonexistent_dir")
        assert result == []

    def test_scan_directory_existent(self):
        """Test scanning existent directory."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("import os\nprint('test')")

            result = scanner.scan_directory(temp_dir)
            assert isinstance(result, list)

    def test_add_issue(self):
        """Test adding security issue."""
        scanner = SecurityScanner()
        scanner.add_issue("test.py", 10, "Test issue", "HIGH")
        assert len(scanner.issues) == 1
        assert scanner.issues[0]["file"] == "test.py"
        assert scanner.issues[0]["line"] == 10
        assert scanner.issues[0]["message"] == "Test issue"
        assert scanner.issues[0]["severity"] == "HIGH"

    def test_get_issues(self):
        """Test getting issues."""
        scanner = SecurityScanner()
        scanner.add_issue("test.py", 10, "Test issue", "HIGH")
        issues = scanner.get_issues()
        assert len(issues) == 1
        assert issues[0]["file"] == "test.py"

    def test_clear_issues(self):
        """Test clearing issues."""
        scanner = SecurityScanner()
        scanner.add_issue("test.py", 10, "Test issue", "HIGH")
        scanner.clear_issues()
        assert len(scanner.issues) == 0

    def test_get_summary(self):
        """Test getting summary."""
        scanner = SecurityScanner()
        scanner.add_issue("test.py", 10, "High severity issue", "HIGH")
        scanner.add_issue("test.py", 20, "Low severity issue", "LOW")

        summary = scanner.get_summary()
        assert summary["total_issues"] == 2
        assert summary["high_severity"] == 1
        assert summary["low_severity"] == 1

    def test_export_results_json(self):
        """Test exporting results to JSON."""
        scanner = SecurityScanner()
        scanner.add_issue("test.py", 10, "Test issue", "HIGH")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            scanner.export_results_json(temp_file)
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                data = json.load(f)
            assert "issues" in data
            assert len(data["issues"]) == 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_results_sarif(self):
        """Test exporting results to SARIF."""
        scanner = SecurityScanner()
        scanner.add_issue("test.py", 10, "Test issue", "HIGH")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as f:
            temp_file = f.name

        try:
            scanner.export_results_sarif(temp_file)
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""

    def test_initialization(self):
        """Test checker initialization."""
        checker = VulnerabilityChecker()
        assert checker.vulnerabilities == []

    def test_check_file_nonexistent(self):
        """Test checking nonexistent file."""
        checker = VulnerabilityChecker()
        result = checker.check_file("nonexistent.py")
        assert result["success"] is False

    def test_check_file_existent(self):
        """Test checking existent file."""
        checker = VulnerabilityChecker()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nprint('test')")
            temp_file = f.name

        try:
            result = checker.check_file(temp_file)
            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_file)

    def test_add_vulnerability(self):
        """Test adding vulnerability."""
        checker = VulnerabilityChecker()
        checker.add_vulnerability("test.py", 10, "Test vulnerability", "HIGH")
        assert len(checker.vulnerabilities) == 1
        assert checker.vulnerabilities[0]["file"] == "test.py"
        assert checker.vulnerabilities[0]["line"] == 10
        assert checker.vulnerabilities[0]["message"] == "Test vulnerability"
        assert checker.vulnerabilities[0]["severity"] == "HIGH"

    def test_get_vulnerabilities(self):
        """Test getting vulnerabilities."""
        checker = VulnerabilityChecker()
        checker.add_vulnerability("test.py", 10, "Test vulnerability", "HIGH")
        vulnerabilities = checker.get_vulnerabilities()
        assert len(vulnerabilities) == 1
        assert vulnerabilities[0]["file"] == "test.py"

    def test_clear_vulnerabilities(self):
        """Test clearing vulnerabilities."""
        checker = VulnerabilityChecker()
        checker.add_vulnerability("test.py", 10, "Test vulnerability", "HIGH")
        checker.clear_vulnerabilities()
        assert len(checker.vulnerabilities) == 0


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = DependencyAnalyzer()
        assert analyzer.dependencies == []
        assert analyzer.vulnerabilities == []

    def test_analyze_requirements_nonexistent(self):
        """Test analyzing nonexistent requirements file."""
        analyzer = DependencyAnalyzer()
        result = analyzer.analyze_requirements("nonexistent.txt")
        assert result["success"] is False

    def test_analyze_requirements_existent(self):
        """Test analyzing existent requirements file."""
        analyzer = DependencyAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("requests==2.25.1\nnumpy==1.21.0")
            temp_file = f.name

        try:
            result = analyzer.analyze_requirements(temp_file)
            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_file)

    def test_add_dependency(self):
        """Test adding dependency."""
        analyzer = DependencyAnalyzer()
        analyzer.add_dependency("requests", "2.25.1", "HIGH")
        assert len(analyzer.dependencies) == 1
        assert analyzer.dependencies[0]["name"] == "requests"
        assert analyzer.dependencies[0]["version"] == "2.25.1"
        assert analyzer.dependencies[0]["severity"] == "HIGH"

    def test_get_dependencies(self):
        """Test getting dependencies."""
        analyzer = DependencyAnalyzer()
        analyzer.add_dependency("requests", "2.25.1", "HIGH")
        dependencies = analyzer.get_dependencies()
        assert len(dependencies) == 1
        assert dependencies[0]["name"] == "requests"

    def test_clear_dependencies(self):
        """Test clearing dependencies."""
        analyzer = DependencyAnalyzer()
        analyzer.add_dependency("requests", "2.25.1", "HIGH")
        analyzer.clear_dependencies()
        assert len(analyzer.dependencies) == 0


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = SecurityPatternAnalyzer()
        assert analyzer.patterns == []
        assert analyzer.issues == []

    def test_analyze_code_nonexistent(self):
        """Test analyzing nonexistent file."""
        analyzer = SecurityPatternAnalyzer()
        result = analyzer.analyze_code("nonexistent.py")
        assert result["success"] is False

    def test_analyze_code_existent(self):
        """Test analyzing existent file."""
        analyzer = SecurityPatternAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nprint('test')")
            temp_file = f.name

        try:
            result = analyzer.analyze_code(temp_file)
            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_file)

    def test_add_pattern(self):
        """Test adding pattern."""
        analyzer = SecurityPatternAnalyzer()
        analyzer.add_pattern("os.system", "Dangerous system call", "HIGH")
        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0]["pattern"] == "os.system"
        assert analyzer.patterns[0]["description"] == "Dangerous system call"
        assert analyzer.patterns[0]["severity"] == "HIGH"

    def test_get_patterns(self):
        """Test getting patterns."""
        analyzer = SecurityPatternAnalyzer()
        analyzer.add_pattern("os.system", "Dangerous system call", "HIGH")
        patterns = analyzer.get_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "os.system"

    def test_clear_patterns(self):
        """Test clearing patterns."""
        analyzer = SecurityPatternAnalyzer()
        analyzer.add_pattern("os.system", "Dangerous system call", "HIGH")
        analyzer.clear_patterns()
        assert len(analyzer.patterns) == 0


class TestSecurityScanFunctions:
    """Test security scan functions."""

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_run_bandit(self, mock_run):
        """Test running bandit."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = run_bandit()
        assert isinstance(result, int)

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_run_bandit_with_args(self, mock_run):
        """Test running bandit with extra args."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = run_bandit(["--json"])
        assert isinstance(result, int)

    @patch("src.ai_guard.security_scanner.subprocess.run")
    def test_run_safety_check(self, mock_run):
        """Test running safety check."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = run_safety_check()
        assert isinstance(result, int)

    def test_scan_for_vulnerabilities(self):
        """Test scanning for vulnerabilities."""
        result = scan_for_vulnerabilities(["test.py"])
        assert isinstance(result, dict)
        assert "success" in result

    def test_check_dependencies(self):
        """Test checking dependencies."""
        result = check_dependencies()
        assert isinstance(result, dict)
        assert "success" in result

    def test_analyze_security_patterns(self):
        """Test analyzing security patterns."""
        result = analyze_security_patterns("import os", "test.py")
        assert isinstance(result, dict)
        assert "success" in result
