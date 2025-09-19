"""Basic tests for security scanner module using actual functions."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
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


class TestRunBandit:
    """Test run_bandit function."""

    @patch('subprocess.call')
    def test_run_bandit_success(self, mock_subprocess_call):
        """Test successful bandit run."""
        mock_subprocess_call.return_value = 0
        
        result = run_bandit()
        assert result == 0

    @patch('subprocess.call')
    def test_run_bandit_with_issues(self, mock_subprocess_call):
        """Test bandit run with issues."""
        mock_subprocess_call.return_value = 1
        
        result = run_bandit()
        assert result == 1

    @patch('subprocess.call')
    def test_run_bandit_with_extra_args(self, mock_subprocess_call):
        """Test bandit run with extra arguments."""
        mock_subprocess_call.return_value = 0
        
        result = run_bandit(["-r", "src/"])
        assert result == 0
        mock_subprocess_call.assert_called_once()


class TestRunSafetyCheck:
    """Test run_safety_check function."""

    @patch('subprocess.call')
    def test_run_safety_check_success(self, mock_subprocess_call):
        """Test successful safety check."""
        mock_subprocess_call.return_value = 0
        
        result = run_safety_check()
        assert result == 0

    @patch('subprocess.call')
    def test_run_safety_check_with_vulnerabilities(self, mock_subprocess_call):
        """Test safety check with vulnerabilities."""
        mock_subprocess_call.return_value = 1
        
        result = run_safety_check()
        assert result == 1


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    def test_scan_file(self):
        """Test scanning a file."""
        scanner = SecurityScanner()
        
        content = "import os\nprint('hello')"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            result = scanner.scan_file(temp_file)
            assert isinstance(result, dict)
        finally:
            try:
                os.unlink(temp_file)
            except (OSError, PermissionError):
                # File might be locked on Windows, ignore cleanup errors
                pass

    def test_scan_directory(self):
        """Test scanning a directory."""
        scanner = SecurityScanner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("import os\nprint('hello')")
            
            result = scanner.scan_directory(temp_dir)
            assert isinstance(result, dict)


class TestScanForVulnerabilities:
    """Test scan_for_vulnerabilities function."""

    @patch('src.ai_guard.security_scanner.run_bandit')
    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_scan_for_vulnerabilities(self, mock_safety, mock_bandit):
        """Test scanning for vulnerabilities."""
        mock_bandit.return_value = 0
        mock_safety.return_value = 0
        
        result = scan_for_vulnerabilities(["test.py"])
        assert isinstance(result, dict)
        assert "bandit" in result
        assert "safety" in result

    @patch('src.ai_guard.security_scanner.run_bandit')
    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_scan_for_vulnerabilities_with_issues(self, mock_safety, mock_bandit):
        """Test scanning for vulnerabilities with issues."""
        mock_bandit.return_value = 1
        mock_safety.return_value = 1
        
        result = scan_for_vulnerabilities(["test.py"])
        assert isinstance(result, dict)
        assert result["bandit"]["exit_code"] == 1
        assert result["safety"]["exit_code"] == 1


class TestCheckDependencies:
    """Test check_dependencies function."""

    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_check_dependencies(self, mock_safety):
        """Test checking dependencies."""
        mock_safety.return_value = 0
        
        result = check_dependencies()
        assert isinstance(result, dict)
        assert "safety_check" in result

    @patch('src.ai_guard.security_scanner.run_safety_check')
    def test_check_dependencies_with_vulnerabilities(self, mock_safety):
        """Test checking dependencies with vulnerabilities."""
        mock_safety.return_value = 1
        
        result = check_dependencies()
        assert isinstance(result, dict)
        assert result["safety_check"]["exit_code"] == 1


class TestAnalyzeSecurityPatterns:
    """Test analyze_security_patterns function."""

    def test_analyze_security_patterns_safe_code(self):
        """Test analyzing safe code."""
        code_content = "print('hello world')"
        result = analyze_security_patterns(code_content, "test.py")
        
        assert isinstance(result, dict)
        assert "patterns_found" in result
        assert "risk_level" in result

    def test_analyze_security_patterns_risky_code(self):
        """Test analyzing risky code."""
        code_content = "import os\nos.system('rm -rf /')"
        result = analyze_security_patterns(code_content, "test.py")
        
        assert isinstance(result, dict)
        assert "patterns_found" in result
        assert "risk_level" in result

    def test_analyze_security_patterns_empty_code(self):
        """Test analyzing empty code."""
        result = analyze_security_patterns("", "test.py")
        
        assert isinstance(result, dict)
        assert "patterns_found" in result
        assert "risk_level" in result


class TestVulnerabilityChecker:
    """Test VulnerabilityChecker class."""

    def test_vulnerability_checker_init(self):
        """Test VulnerabilityChecker initialization."""
        checker = VulnerabilityChecker()
        assert checker is not None

    def test_check_vulnerabilities(self):
        """Test checking vulnerabilities."""
        checker = VulnerabilityChecker()
        
        result = checker.check_vulnerabilities(["test.py"])
        assert isinstance(result, dict)

    def test_check_file_vulnerabilities(self):
        """Test checking file vulnerabilities."""
        checker = VulnerabilityChecker()
        
        content = "import os\nprint('hello')"
        result = checker.check_file_vulnerabilities(content, "test.py")
        assert isinstance(result, dict)


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_dependency_analyzer_init(self):
        """Test DependencyAnalyzer initialization."""
        analyzer = DependencyAnalyzer()
        assert analyzer is not None

    def test_analyze_dependencies(self):
        """Test analyzing dependencies."""
        analyzer = DependencyAnalyzer()
        
        result = analyzer.analyze_dependencies()
        assert isinstance(result, dict)

    def test_check_package_vulnerabilities(self):
        """Test checking package vulnerabilities."""
        analyzer = DependencyAnalyzer()
        
        result = analyzer.check_package_vulnerabilities("requests")
        assert isinstance(result, dict)


class TestSecurityPatternAnalyzer:
    """Test SecurityPatternAnalyzer class."""

    def test_security_pattern_analyzer_init(self):
        """Test SecurityPatternAnalyzer initialization."""
        analyzer = SecurityPatternAnalyzer()
        assert analyzer is not None

    def test_analyze_patterns(self):
        """Test analyzing security patterns."""
        analyzer = SecurityPatternAnalyzer()
        
        code_content = "import os\nprint('hello')"
        result = analyzer.analyze_patterns(code_content, "test.py")
        assert isinstance(result, dict)

    def test_check_pattern(self):
        """Test checking specific pattern."""
        analyzer = SecurityPatternAnalyzer()
        
        result = analyzer.check_pattern("os.system", "test.py")
        assert isinstance(result, dict)