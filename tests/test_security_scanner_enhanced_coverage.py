"""Enhanced test coverage for security_scanner.py module to achieve 50%+ coverage."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open

from src.ai_guard.security_scanner import (
    SecurityScanner,
    SecurityIssue,
    SecurityLevel,
    SecurityReport,
    scan_file,
    scan_directory,
    scan_code_string,
    get_security_rules,
    validate_security_config,
    SecurityConfig,
    VulnerabilityPattern,
    PatternMatcher,
    SecurityMetrics,
    SecurityDashboard,
)


class TestSecurityLevel:
    """Test SecurityLevel enum."""

    def test_security_level_values(self):
        """Test SecurityLevel enum values."""
        assert SecurityLevel.LOW == "low"
        assert SecurityLevel.MEDIUM == "medium"
        assert SecurityLevel.HIGH == "high"
        assert SecurityLevel.CRITICAL == "critical"


class TestSecurityIssue:
    """Test SecurityIssue dataclass."""

    def test_security_issue_creation(self):
        """Test SecurityIssue creation."""
        issue = SecurityIssue(
            rule_id="B101",
            title="Test Security Issue",
            description="This is a test security issue",
            severity=SecurityLevel.HIGH,
            file_path="test.py",
            line_number=10,
            column_number=5,
            code_snippet="password = 'secret'",
            recommendation="Use environment variables for secrets",
            cwe_id="CWE-798",
            owasp_category="A02:2021",
        )

        assert issue.rule_id == "B101"
        assert issue.title == "Test Security Issue"
        assert issue.description == "This is a test security issue"
        assert issue.severity == SecurityLevel.HIGH
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.code_snippet == "password = 'secret'"
        assert issue.recommendation == "Use environment variables for secrets"
        assert issue.cwe_id == "CWE-798"
        assert issue.owasp_category == "A02:2021"

    def test_security_issue_default_values(self):
        """Test SecurityIssue with default values."""
        issue = SecurityIssue(
            rule_id="B101",
            title="Test Issue",
            description="Test description",
            severity=SecurityLevel.MEDIUM,
            file_path="test.py",
            line_number=1,
        )

        assert issue.column_number == 0
        assert issue.code_snippet == ""
        assert issue.recommendation == ""
        assert issue.cwe_id == ""
        assert issue.owasp_category == ""

    def test_security_issue_to_dict(self):
        """Test SecurityIssue to_dict method."""
        issue = SecurityIssue(
            rule_id="B101",
            title="Test Issue",
            description="Test description",
            severity=SecurityLevel.HIGH,
            file_path="test.py",
            line_number=10,
            column_number=5,
        )

        data = issue.to_dict()
        assert data["rule_id"] == "B101"
        assert data["title"] == "Test Issue"
        assert data["severity"] == "high"
        assert data["file_path"] == "test.py"
        assert data["line_number"] == 10


class TestSecurityReport:
    """Test SecurityReport dataclass."""

    def test_security_report_creation(self):
        """Test SecurityReport creation."""
        issues = [
            SecurityIssue(
                rule_id="B101",
                title="Issue 1",
                description="Description 1",
                severity=SecurityLevel.HIGH,
                file_path="test1.py",
                line_number=1,
            ),
            SecurityIssue(
                rule_id="B102",
                title="Issue 2",
                description="Description 2",
                severity=SecurityLevel.MEDIUM,
                file_path="test2.py",
                line_number=2,
            ),
        ]

        report = SecurityReport(
            issues=issues,
            total_issues=2,
            high_severity_count=1,
            medium_severity_count=1,
            low_severity_count=0,
            critical_severity_count=0,
            scan_duration=1.5,
            files_scanned=2,
            timestamp="2024-01-01T00:00:00Z",
        )

        assert len(report.issues) == 2
        assert report.total_issues == 2
        assert report.high_severity_count == 1
        assert report.medium_severity_count == 1
        assert report.low_severity_count == 0
        assert report.critical_severity_count == 0
        assert report.scan_duration == 1.5
        assert report.files_scanned == 2
        assert report.timestamp == "2024-01-01T00:00:00Z"

    def test_security_report_get_issues_by_severity(self):
        """Test getting issues by severity."""
        issues = [
            SecurityIssue(
                rule_id="B101",
                title="High Issue",
                description="High severity issue",
                severity=SecurityLevel.HIGH,
                file_path="test.py",
                line_number=1,
            ),
            SecurityIssue(
                rule_id="B102",
                title="Medium Issue",
                description="Medium severity issue",
                severity=SecurityLevel.MEDIUM,
                file_path="test.py",
                line_number=2,
            ),
        ]

        report = SecurityReport(issues=issues, total_issues=2)

        high_issues = report.get_issues_by_severity(SecurityLevel.HIGH)
        medium_issues = report.get_issues_by_severity(SecurityLevel.MEDIUM)
        low_issues = report.get_issues_by_severity(SecurityLevel.LOW)

        assert len(high_issues) == 1
        assert len(medium_issues) == 1
        assert len(low_issues) == 0
        assert high_issues[0].rule_id == "B101"
        assert medium_issues[0].rule_id == "B102"

    def test_security_report_get_issues_by_file(self):
        """Test getting issues by file."""
        issues = [
            SecurityIssue(
                rule_id="B101",
                title="Issue 1",
                description="Description 1",
                severity=SecurityLevel.HIGH,
                file_path="test1.py",
                line_number=1,
            ),
            SecurityIssue(
                rule_id="B102",
                title="Issue 2",
                description="Description 2",
                severity=SecurityLevel.MEDIUM,
                file_path="test1.py",
                line_number=2,
            ),
            SecurityIssue(
                rule_id="B103",
                title="Issue 3",
                description="Description 3",
                severity=SecurityLevel.LOW,
                file_path="test2.py",
                line_number=3,
            ),
        ]

        report = SecurityReport(issues=issues, total_issues=3)

        test1_issues = report.get_issues_by_file("test1.py")
        test2_issues = report.get_issues_by_file("test2.py")
        test3_issues = report.get_issues_by_file("test3.py")

        assert len(test1_issues) == 2
        assert len(test2_issues) == 1
        assert len(test3_issues) == 0
        assert test1_issues[0].rule_id == "B101"
        assert test1_issues[1].rule_id == "B102"
        assert test2_issues[0].rule_id == "B103"

    def test_security_report_to_dict(self):
        """Test SecurityReport to_dict method."""
        issues = [
            SecurityIssue(
                rule_id="B101",
                title="Test Issue",
                description="Test description",
                severity=SecurityLevel.HIGH,
                file_path="test.py",
                line_number=1,
            )
        ]

        report = SecurityReport(
            issues=issues,
            total_issues=1,
            high_severity_count=1,
            medium_severity_count=0,
            low_severity_count=0,
            critical_severity_count=0,
            scan_duration=1.0,
            files_scanned=1,
            timestamp="2024-01-01T00:00:00Z",
        )

        data = report.to_dict()
        assert data["total_issues"] == 1
        assert data["high_severity_count"] == 1
        assert data["scan_duration"] == 1.0
        assert len(data["issues"]) == 1


class TestVulnerabilityPattern:
    """Test VulnerabilityPattern dataclass."""

    def test_vulnerability_pattern_creation(self):
        """Test VulnerabilityPattern creation."""
        pattern = VulnerabilityPattern(
            rule_id="B101",
            title="Hardcoded Password",
            description="Password is hardcoded in source code",
            severity=SecurityLevel.HIGH,
            pattern_type="regex",
            pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
            cwe_id="CWE-798",
            owasp_category="A02:2021",
            recommendation="Use environment variables for secrets",
        )

        assert pattern.rule_id == "B101"
        assert pattern.title == "Hardcoded Password"
        assert pattern.description == "Password is hardcoded in source code"
        assert pattern.severity == SecurityLevel.HIGH
        assert pattern.pattern_type == "regex"
        assert pattern.pattern == r"password\s*=\s*['\"][^'\"]+['\"]"
        assert pattern.cwe_id == "CWE-798"
        assert pattern.owasp_category == "A02:2021"
        assert pattern.recommendation == "Use environment variables for secrets"


class TestPatternMatcher:
    """Test PatternMatcher class."""

    def test_pattern_matcher_init(self):
        """Test PatternMatcher initialization."""
        patterns = [
            VulnerabilityPattern(
                rule_id="B101",
                title="Test Pattern",
                description="Test description",
                severity=SecurityLevel.HIGH,
                pattern_type="regex",
                pattern=r"test\s*=",
            )
        ]

        matcher = PatternMatcher(patterns)
        assert len(matcher.patterns) == 1

    def test_pattern_matcher_regex_match(self):
        """Test regex pattern matching."""
        patterns = [
            VulnerabilityPattern(
                rule_id="B101",
                title="Password Pattern",
                description="Hardcoded password",
                severity=SecurityLevel.HIGH,
                pattern_type="regex",
                pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
            )
        ]

        matcher = PatternMatcher(patterns)

        # Test matching code
        matching_code = "password = 'secret123'"
        issues = matcher.match_patterns(matching_code, "test.py")

        assert len(issues) == 1
        assert issues[0].rule_id == "B101"
        assert issues[0].severity == SecurityLevel.HIGH

    def test_pattern_matcher_regex_no_match(self):
        """Test regex pattern with no match."""
        patterns = [
            VulnerabilityPattern(
                rule_id="B101",
                title="Password Pattern",
                description="Hardcoded password",
                severity=SecurityLevel.HIGH,
                pattern_type="regex",
                pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
            )
        ]

        matcher = PatternMatcher(patterns)

        # Test non-matching code
        non_matching_code = "username = 'admin'"
        issues = matcher.match_patterns(non_matching_code, "test.py")

        assert len(issues) == 0

    def test_pattern_matcher_multiple_patterns(self):
        """Test multiple pattern matching."""
        patterns = [
            VulnerabilityPattern(
                rule_id="B101",
                title="Password Pattern",
                description="Hardcoded password",
                severity=SecurityLevel.HIGH,
                pattern_type="regex",
                pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
            ),
            VulnerabilityPattern(
                rule_id="B102",
                title="API Key Pattern",
                description="Hardcoded API key",
                severity=SecurityLevel.MEDIUM,
                pattern_type="regex",
                pattern=r"api_key\s*=\s*['\"][^'\"]+['\"]",
            ),
        ]

        matcher = PatternMatcher(patterns)

        # Test code with both patterns
        code = "password = 'secret'\napi_key = 'abc123'"
        issues = matcher.match_patterns(code, "test.py")

        assert len(issues) == 2
        rule_ids = [issue.rule_id for issue in issues]
        assert "B101" in rule_ids
        assert "B102" in rule_ids

    def test_pattern_matcher_invalid_pattern(self):
        """Test invalid pattern handling."""
        patterns = [
            VulnerabilityPattern(
                rule_id="B101",
                title="Invalid Pattern",
                description="Invalid regex pattern",
                severity=SecurityLevel.HIGH,
                pattern_type="regex",
                pattern=r"[invalid regex",
            )
        ]

        matcher = PatternMatcher(patterns)

        # Should not raise exception
        issues = matcher.match_patterns("test code", "test.py")
        assert len(issues) == 0


class TestSecurityConfig:
    """Test SecurityConfig class."""

    def test_security_config_default(self):
        """Test default SecurityConfig."""
        config = SecurityConfig()

        assert config.enable_bandit is True
        assert config.enable_custom_patterns is True
        assert config.severity_threshold == SecurityLevel.LOW
        assert config.max_issues_per_file == 100
        assert len(config.custom_patterns) >= 0

    def test_security_config_custom(self):
        """Test custom SecurityConfig."""
        custom_patterns = [
            VulnerabilityPattern(
                rule_id="C001",
                title="Custom Pattern",
                description="Custom security pattern",
                severity=SecurityLevel.MEDIUM,
                pattern_type="regex",
                pattern=r"custom\s*=",
            )
        ]

        config = SecurityConfig(
            enable_bandit=False,
            enable_custom_patterns=True,
            severity_threshold=SecurityLevel.HIGH,
            max_issues_per_file=50,
            custom_patterns=custom_patterns,
        )

        assert config.enable_bandit is False
        assert config.enable_custom_patterns is True
        assert config.severity_threshold == SecurityLevel.HIGH
        assert config.max_issues_per_file == 50
        assert len(config.custom_patterns) == 1
        assert config.custom_patterns[0].rule_id == "C001"

    def test_security_config_from_dict(self):
        """Test SecurityConfig from dictionary."""
        config_dict = {
            "enable_bandit": False,
            "enable_custom_patterns": True,
            "severity_threshold": "high",
            "max_issues_per_file": 75,
        }

        config = SecurityConfig.from_dict(config_dict)

        assert config.enable_bandit is False
        assert config.enable_custom_patterns is True
        assert config.severity_threshold == SecurityLevel.HIGH
        assert config.max_issues_per_file == 75

    def test_security_config_to_dict(self):
        """Test SecurityConfig to dictionary."""
        config = SecurityConfig(
            enable_bandit=False,
            severity_threshold=SecurityLevel.MEDIUM,
            max_issues_per_file=25,
        )

        config_dict = config.to_dict()

        assert config_dict["enable_bandit"] is False
        assert config_dict["severity_threshold"] == "medium"
        assert config_dict["max_issues_per_file"] == 25


class TestSecurityMetrics:
    """Test SecurityMetrics class."""

    def test_security_metrics_init(self):
        """Test SecurityMetrics initialization."""
        metrics = SecurityMetrics()

        assert metrics.total_scans == 0
        assert metrics.total_issues_found == 0
        assert metrics.issues_by_severity == {
            SecurityLevel.LOW: 0,
            SecurityLevel.MEDIUM: 0,
            SecurityLevel.HIGH: 0,
            SecurityLevel.CRITICAL: 0,
        }
        assert metrics.scan_times == []
        assert metrics.files_scanned == 0

    def test_security_metrics_record_scan(self):
        """Test recording scan results."""
        metrics = SecurityMetrics()

        issues = [
            SecurityIssue(
                rule_id="B101",
                title="High Issue",
                description="High severity issue",
                severity=SecurityLevel.HIGH,
                file_path="test.py",
                line_number=1,
            ),
            SecurityIssue(
                rule_id="B102",
                title="Medium Issue",
                description="Medium severity issue",
                severity=SecurityLevel.MEDIUM,
                file_path="test.py",
                line_number=2,
            ),
        ]

        metrics.record_scan(issues, 2, 1.5)

        assert metrics.total_scans == 1
        assert metrics.total_issues_found == 2
        assert metrics.issues_by_severity[SecurityLevel.HIGH] == 1
        assert metrics.issues_by_severity[SecurityLevel.MEDIUM] == 1
        assert metrics.scan_times == [1.5]
        assert metrics.files_scanned == 2

    def test_security_metrics_get_average_scan_time(self):
        """Test getting average scan time."""
        metrics = SecurityMetrics()

        metrics.record_scan([], 1, 1.0)
        metrics.record_scan([], 1, 2.0)
        metrics.record_scan([], 1, 3.0)

        avg_time = metrics.get_average_scan_time()
        assert avg_time == 2.0

    def test_security_metrics_get_issue_rate(self):
        """Test getting issue rate."""
        metrics = SecurityMetrics()

        metrics.record_scan([], 5, 1.0)  # 0 issues, 5 files
        metrics.record_scan([], 3, 1.0)  # 0 issues, 3 files

        issue_rate = metrics.get_issue_rate()
        assert issue_rate == 0.0

        # Add some issues
        issues = [
            SecurityIssue(
                rule_id="B101",
                title="Test Issue",
                description="Test description",
                severity=SecurityLevel.HIGH,
                file_path="test.py",
                line_number=1,
            )
        ]

        metrics.record_scan(issues, 2, 1.0)  # 1 issue, 2 files

        issue_rate = metrics.get_issue_rate()
        assert issue_rate == 1.0 / 2.0  # 1 issue in 2 files

    def test_security_metrics_reset(self):
        """Test resetting metrics."""
        metrics = SecurityMetrics()

        metrics.record_scan([], 1, 1.0)
        assert metrics.total_scans == 1

        metrics.reset()

        assert metrics.total_scans == 0
        assert metrics.total_issues_found == 0
        assert metrics.scan_times == []
        assert metrics.files_scanned == 0


class TestSecurityDashboard:
    """Test SecurityDashboard class."""

    def test_security_dashboard_init(self):
        """Test SecurityDashboard initialization."""
        dashboard = SecurityDashboard()

        assert dashboard.metrics is not None
        assert dashboard.recent_scans == []
        assert dashboard.trend_data == {}

    def test_security_dashboard_record_scan(self):
        """Test recording scan in dashboard."""
        dashboard = SecurityDashboard()

        issues = [
            SecurityIssue(
                rule_id="B101",
                title="Test Issue",
                description="Test description",
                severity=SecurityLevel.HIGH,
                file_path="test.py",
                line_number=1,
            )
        ]

        dashboard.record_scan(issues, 1, 1.0)

        assert dashboard.metrics.total_scans == 1
        assert len(dashboard.recent_scans) == 1
        assert dashboard.recent_scans[0]["total_issues"] == 1

    def test_security_dashboard_get_summary(self):
        """Test getting dashboard summary."""
        dashboard = SecurityDashboard()

        issues = [
            SecurityIssue(
                rule_id="B101",
                title="High Issue",
                description="High severity issue",
                severity=SecurityLevel.HIGH,
                file_path="test.py",
                line_number=1,
            ),
            SecurityIssue(
                rule_id="B102",
                title="Medium Issue",
                description="Medium severity issue",
                severity=SecurityLevel.MEDIUM,
                file_path="test.py",
                line_number=2,
            ),
        ]

        dashboard.record_scan(issues, 1, 1.0)

        summary = dashboard.get_summary()

        assert summary["total_scans"] == 1
        assert summary["total_issues"] == 2
        assert summary["high_severity_issues"] == 1
        assert summary["medium_severity_issues"] == 1
        assert summary["average_scan_time"] == 1.0


class TestSecurityScanner:
    """Test SecurityScanner class."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()

        assert scanner.config is not None
        assert scanner.metrics is not None
        assert scanner.dashboard is not None

    def test_security_scanner_init_with_config(self):
        """Test SecurityScanner initialization with config."""
        config = SecurityConfig(enable_bandit=False)
        scanner = SecurityScanner(config)

        assert scanner.config.enable_bandit is False

    @patch("subprocess.run")
    def test_security_scanner_scan_file_bandit(self, mock_run):
        """Test scanning file with bandit."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {
                "results": [
                    {
                        "filename": "test.py",
                        "line_number": 1,
                        "issue_severity": "HIGH",
                        "issue_confidence": "HIGH",
                        "issue_text": "Test security issue",
                        "test_name": "B101",
                    }
                ]
            }
        )
        mock_run.return_value = mock_result

        scanner = SecurityScanner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("password = 'secret'")
            f.flush()

            try:
                report = scanner.scan_file(f.name)

                assert report.total_issues == 1
                assert report.high_severity_count == 1
                assert len(report.issues) == 1
                assert report.issues[0].rule_id == "B101"
            finally:
                os.unlink(f.name)

    def test_security_scanner_scan_file_custom_patterns(self):
        """Test scanning file with custom patterns."""
        custom_patterns = [
            VulnerabilityPattern(
                rule_id="C001",
                title="Custom Pattern",
                description="Custom security pattern",
                severity=SecurityLevel.MEDIUM,
                pattern_type="regex",
                pattern=r"custom\s*=\s*['\"][^'\"]+['\"]",
            )
        ]

        config = SecurityConfig(
            enable_bandit=False,
            enable_custom_patterns=True,
            custom_patterns=custom_patterns,
        )

        scanner = SecurityScanner(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("custom = 'value'")
            f.flush()

            try:
                report = scanner.scan_file(f.name)

                assert report.total_issues == 1
                assert report.medium_severity_count == 1
                assert len(report.issues) == 1
                assert report.issues[0].rule_id == "C001"
            finally:
                os.unlink(f.name)

    def test_security_scanner_scan_file_no_issues(self):
        """Test scanning file with no security issues."""
        config = SecurityConfig(enable_bandit=False, enable_custom_patterns=False)
        scanner = SecurityScanner(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello world')")
            f.flush()

            try:
                report = scanner.scan_file(f.name)

                assert report.total_issues == 0
                assert len(report.issues) == 0
            finally:
                os.unlink(f.name)

    def test_security_scanner_scan_directory(self):
        """Test scanning directory."""
        config = SecurityConfig(enable_bandit=False, enable_custom_patterns=False)
        scanner = SecurityScanner(config)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1_path = os.path.join(temp_dir, "test1.py")
            file2_path = os.path.join(temp_dir, "test2.py")

            with open(file1_path, "w") as f:
                f.write("print('hello')")

            with open(file2_path, "w") as f:
                f.write("print('world')")

            report = scanner.scan_directory(temp_dir)

            assert report.files_scanned == 2
            assert report.total_issues == 0

    def test_security_scanner_scan_code_string(self):
        """Test scanning code string."""
        custom_patterns = [
            VulnerabilityPattern(
                rule_id="C001",
                title="Password Pattern",
                description="Hardcoded password",
                severity=SecurityLevel.HIGH,
                pattern_type="regex",
                pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
            )
        ]

        config = SecurityConfig(
            enable_bandit=False,
            enable_custom_patterns=True,
            custom_patterns=custom_patterns,
        )

        scanner = SecurityScanner(config)

        code = "password = 'secret123'"
        issues = scanner.scan_code_string(code, "test.py")

        assert len(issues) == 1
        assert issues[0].rule_id == "C001"
        assert issues[0].severity == SecurityLevel.HIGH

    def test_security_scanner_get_metrics(self):
        """Test getting scanner metrics."""
        scanner = SecurityScanner()

        metrics = scanner.get_metrics()

        assert "total_scans" in metrics
        assert "total_issues_found" in metrics
        assert "issues_by_severity" in metrics
        assert "average_scan_time" in metrics


class TestUtilityFunctions:
    """Test utility functions."""

    def test_scan_file_function(self):
        """Test scan_file utility function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                report = scan_file(f.name)
                assert isinstance(report, SecurityReport)
            finally:
                os.unlink(f.name)

    def test_scan_directory_function(self):
        """Test scan_directory utility function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.py")

            with open(file_path, "w") as f:
                f.write("print('hello')")

            report = scan_directory(temp_dir)
            assert isinstance(report, SecurityReport)

    def test_scan_code_string_function(self):
        """Test scan_code_string utility function."""
        code = "print('hello world')"
        issues = scan_code_string(code, "test.py")
        assert isinstance(issues, list)

    def test_get_security_rules_function(self):
        """Test get_security_rules function."""
        rules = get_security_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_validate_security_config_function(self):
        """Test validate_security_config function."""
        config = SecurityConfig()
        is_valid, errors = validate_security_config(config)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
