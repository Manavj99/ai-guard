"""Simplified test coverage for security_scanner.py module."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, MagicMock

from src.ai_guard.security_scanner import (
    _get_file_hash,
    _is_cache_valid,
    _cache_result,
    _get_cached_result,
    _clear_cache,
    _parse_bandit_output,
    _scan_with_patterns,
    _scan_with_bandit,
    scan_file,
    scan_directory,
    scan_code_string,
    get_security_rules,
    validate_security_config,
    SECURITY_PATTERNS,
    SEVERITY_LEVELS,
)


class TestSecurityPatterns:
    """Test security pattern matching."""

    def test_sql_injection_pattern(self):
        """Test SQL injection pattern detection."""
        pattern = SECURITY_PATTERNS["sql_injection"]

        # Should match SQL injection
        malicious_code = "query = 'SELECT * FROM users WHERE id = ' + user_id"
        assert pattern.search(malicious_code) is not None

        # Should not match safe code
        safe_code = "query = 'SELECT * FROM users'"
        assert pattern.search(safe_code) is None

    def test_hardcoded_password_pattern(self):
        """Test hardcoded password pattern detection."""
        pattern = SECURITY_PATTERNS["hardcoded_password"]

        # Should match hardcoded passwords
        malicious_code = "password = 'secret123'"
        assert pattern.search(malicious_code) is not None

        malicious_code = 'passwd = "admin"'
        assert pattern.search(malicious_code) is not None

        # Should not match safe code
        safe_code = "password = get_password()"
        assert pattern.search(safe_code) is None

    def test_hardcoded_api_key_pattern(self):
        """Test hardcoded API key pattern detection."""
        pattern = SECURITY_PATTERNS["hardcoded_api_key"]

        # Should match hardcoded API keys
        malicious_code = "api_key = 'abc123def456'"
        assert pattern.search(malicious_code) is not None

        malicious_code = 'access_token = "xyz789"'
        assert pattern.search(malicious_code) is not None

        # Should not match safe code
        safe_code = "api_key = os.getenv('API_KEY')"
        assert pattern.search(safe_code) is None

    def test_dangerous_functions_pattern(self):
        """Test dangerous functions pattern detection."""
        pattern = SECURITY_PATTERNS["dangerous_functions"]

        # Should match dangerous functions
        malicious_code = "result = eval(user_input)"
        assert pattern.search(malicious_code) is not None

        malicious_code = "os.system('rm -rf /')"
        assert pattern.search(malicious_code) is not None

        # Should not match safe code
        safe_code = "result = safe_function(user_input)"
        assert pattern.search(safe_code) is None

    def test_shell_injection_pattern(self):
        """Test shell injection pattern detection."""
        pattern = SECURITY_PATTERNS["shell_injection"]

        # Should match shell injection
        malicious_code = "subprocess.run(command, shell=True)"
        assert pattern.search(malicious_code) is not None

        # Should not match safe code
        safe_code = "subprocess.run(['ls', '-la'])"
        assert pattern.search(safe_code) is None


class TestSeverityLevels:
    """Test security severity levels."""

    def test_severity_levels_values(self):
        """Test severity level values."""
        assert SEVERITY_LEVELS["critical"] == 4
        assert SEVERITY_LEVELS["high"] == 3
        assert SEVERITY_LEVELS["medium"] == 2
        assert SEVERITY_LEVELS["low"] == 1
        assert SEVERITY_LEVELS["info"] == 0


class TestFileHash:
    """Test file hashing functions."""

    def test_get_file_hash(self):
        """Test getting file hash."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            try:
                hash1 = _get_file_hash(f.name)
                hash2 = _get_file_hash(f.name)

                assert hash1 == hash2
                assert len(hash1) == 32  # MD5 hash length
            finally:
                os.unlink(f.name)

    def test_get_file_hash_nonexistent(self):
        """Test getting hash of nonexistent file."""
        hash_value = _get_file_hash("nonexistent_file.txt")
        assert hash_value == ""


class TestCacheFunctions:
    """Test cache functions."""

    def test_is_cache_valid_no_timestamp(self):
        """Test cache validity with no timestamp."""
        result = _is_cache_valid("nonexistent_file", "test_key")
        assert result is False

    def test_cache_result_and_get(self):
        """Test caching and retrieving results."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            try:
                # Cache a result
                test_data = {"issues": ["test_issue"]}
                _cache_result(f.name, "test_key", test_data)

                # Retrieve cached result
                cached_data = _get_cached_result(f.name, "test_key")
                assert cached_data == test_data
            finally:
                os.unlink(f.name)

    def test_clear_cache(self):
        """Test clearing cache."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            try:
                # Cache a result
                test_data = {"issues": ["test_issue"]}
                _cache_result(f.name, "test_key", test_data)

                # Clear cache
                _clear_cache()

                # Should not be able to retrieve
                cached_data = _get_cached_result(f.name, "test_key")
                assert cached_data is None
            finally:
                os.unlink(f.name)


class TestBanditOutputParsing:
    """Test bandit output parsing."""

    def test_parse_bandit_output_valid_json(self):
        """Test parsing valid bandit JSON output."""
        bandit_output = {
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

        json_output = json.dumps(bandit_output)
        issues = _parse_bandit_output(json_output)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["rule_id"] == "B101"
        assert issue["severity"] == "HIGH"
        assert issue["file_path"] == "test.py"
        assert issue["line_number"] == 1

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        issues = _parse_bandit_output("")
        assert len(issues) == 0

    def test_parse_bandit_output_invalid_json(self):
        """Test parsing invalid bandit JSON."""
        issues = _parse_bandit_output("invalid json")
        assert len(issues) == 0


class TestPatternScanning:
    """Test pattern-based scanning."""

    def test_scan_with_patterns_hardcoded_password(self):
        """Test scanning with hardcoded password pattern."""
        code = "password = 'secret123'"
        issues = _scan_with_patterns(code, "test.py")

        assert len(issues) == 1
        issue = issues[0]
        assert issue["rule_id"] == "hardcoded_password"
        assert issue["severity"] == "HIGH"
        assert issue["file_path"] == "test.py"

    def test_scan_with_patterns_api_key(self):
        """Test scanning with hardcoded API key pattern."""
        code = "api_key = 'abc123def456'"
        issues = _scan_with_patterns(code, "test.py")

        assert len(issues) == 1
        issue = issues[0]
        assert issue["rule_id"] == "hardcoded_api_key"
        assert issue["severity"] == "HIGH"

    def test_scan_with_patterns_no_issues(self):
        """Test scanning code with no security issues."""
        code = "print('hello world')"
        issues = _scan_with_patterns(code, "test.py")

        assert len(issues) == 0

    def test_scan_with_patterns_multiple_issues(self):
        """Test scanning code with multiple security issues."""
        code = "password = 'secret'\napi_key = 'abc123'"
        issues = _scan_with_patterns(code, "test.py")

        assert len(issues) == 2
        rule_ids = [issue["rule_id"] for issue in issues]
        assert "hardcoded_password" in rule_ids
        assert "hardcoded_api_key" in rule_ids


class TestBanditScanning:
    """Test bandit-based scanning."""

    @patch("subprocess.run")
    def test_scan_with_bandit_success(self, mock_run):
        """Test successful bandit scan."""
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

        issues = _scan_with_bandit("test.py")

        assert len(issues) == 1
        assert issues[0]["rule_id"] == "B101"

    @patch("subprocess.run")
    def test_scan_with_bandit_failure(self, mock_run):
        """Test bandit scan failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bandit")

        issues = _scan_with_bandit("test.py")

        assert len(issues) == 0

    @patch("subprocess.run")
    def test_scan_with_bandit_no_issues(self, mock_run):
        """Test bandit scan with no issues."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"results": []})
        mock_run.return_value = mock_result

        issues = _scan_with_bandit("test.py")

        assert len(issues) == 0


class TestScanFile:
    """Test scan_file function."""

    @patch("src.ai_guard.security_scanner._scan_with_bandit")
    @patch("src.ai_guard.security_scanner._scan_with_patterns")
    def test_scan_file_with_issues(self, mock_patterns, mock_bandit):
        """Test scanning file with security issues."""
        mock_bandit.return_value = []
        mock_patterns.return_value = [
            {
                "rule_id": "hardcoded_password",
                "title": "Hardcoded Password",
                "description": "Password is hardcoded",
                "severity": "HIGH",
                "file_path": "test.py",
                "line_number": 1,
                "column_number": 0,
                "code_snippet": "password = 'secret'",
                "recommendation": "Use environment variables",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("password = 'secret'")
            f.flush()

            try:
                result = scan_file(f.name)

                assert result["total_issues"] == 1
                assert result["high_severity_count"] == 1
                assert len(result["issues"]) == 1
                assert result["issues"][0]["rule_id"] == "hardcoded_password"
            finally:
                os.unlink(f.name)

    def test_scan_file_nonexistent(self):
        """Test scanning nonexistent file."""
        result = scan_file("nonexistent.py")

        assert result["total_issues"] == 0
        assert len(result["issues"]) == 0

    def test_scan_file_no_issues(self):
        """Test scanning file with no security issues."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello world')")
            f.flush()

            try:
                result = scan_file(f.name)

                assert result["total_issues"] == 0
                assert len(result["issues"]) == 0
            finally:
                os.unlink(f.name)


class TestScanDirectory:
    """Test scan_directory function."""

    def test_scan_directory_with_files(self):
        """Test scanning directory with Python files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1_path = os.path.join(temp_dir, "test1.py")
            file2_path = os.path.join(temp_dir, "test2.py")
            file3_path = os.path.join(temp_dir, "test.txt")  # Non-Python file

            with open(file1_path, "w") as f:
                f.write("print('hello')")

            with open(file2_path, "w") as f:
                f.write("print('world')")

            with open(file3_path, "w") as f:
                f.write("text content")

            result = scan_directory(temp_dir)

            assert result["files_scanned"] == 2  # Only Python files
            assert result["total_issues"] == 0

    def test_scan_directory_empty(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = scan_directory(temp_dir)

            assert result["files_scanned"] == 0
            assert result["total_issues"] == 0

    def test_scan_directory_nonexistent(self):
        """Test scanning nonexistent directory."""
        result = scan_directory("nonexistent_directory")

        assert result["files_scanned"] == 0
        assert result["total_issues"] == 0


class TestScanCodeString:
    """Test scan_code_string function."""

    def test_scan_code_string_with_issues(self):
        """Test scanning code string with security issues."""
        code = "password = 'secret123'"
        issues = scan_code_string(code, "test.py")

        assert len(issues) == 1
        assert issues[0]["rule_id"] == "hardcoded_password"
        assert issues[0]["severity"] == "HIGH"

    def test_scan_code_string_no_issues(self):
        """Test scanning code string with no issues."""
        code = "print('hello world')"
        issues = scan_code_string(code, "test.py")

        assert len(issues) == 0

    def test_scan_code_string_multiple_issues(self):
        """Test scanning code string with multiple issues."""
        code = "password = 'secret'\napi_key = 'abc123'"
        issues = scan_code_string(code, "test.py")

        assert len(issues) == 2
        rule_ids = [issue["rule_id"] for issue in issues]
        assert "hardcoded_password" in rule_ids
        assert "hardcoded_api_key" in rule_ids


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_security_rules(self):
        """Test getting security rules."""
        rules = get_security_rules()

        assert isinstance(rules, dict)
        assert "patterns" in rules
        assert "severity_levels" in rules
        assert len(rules["patterns"]) > 0

    def test_validate_security_config(self):
        """Test validating security configuration."""
        config = {
            "enable_bandit": True,
            "enable_pattern_scanning": True,
            "severity_threshold": "MEDIUM",
            "max_issues_per_file": 100,
        }

        is_valid, errors = validate_security_config(config)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_security_config_invalid(self):
        """Test validating invalid security configuration."""
        config = {
            "enable_bandit": "invalid_boolean",
            "severity_threshold": "INVALID_LEVEL",
        }

        is_valid, errors = validate_security_config(config)

        assert is_valid is False
        assert len(errors) > 0
