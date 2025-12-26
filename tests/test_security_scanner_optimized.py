"""Comprehensive tests for optimized security_scanner.py module."""

import os
import tempfile
import threading
import time
import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.ai_guard.security_scanner import (
    SecurityScanner,
    analyze_security_patterns,
    scan_for_vulnerabilities,
    check_dependencies,
    SECURITY_PATTERNS,
    SEVERITY_LEVELS,
    _get_file_hash,
    _is_cache_valid,
    _cache_security_result,
    _get_cached_security_result,
    _clear_security_cache,
    VulnerabilityChecker,
    DependencyAnalyzer,
    SecurityPatternAnalyzer,
)


class TestSecurityScannerOptimizations:
    """Test optimized security scanner functionality."""

    def test_security_patterns_compilation(self):
        """Test that all security patterns are properly compiled."""
        for pattern_name, pattern_regex in SECURITY_PATTERNS.items():
            assert pattern_regex is not None
            assert hasattr(pattern_regex, "search")
            assert hasattr(pattern_regex, "findall")

    def test_enhanced_pattern_detection(self):
        """Test enhanced security pattern detection."""
        test_code = """
import os
import subprocess
import pickle

# SQL injection vulnerability
query = f"SELECT * FROM users WHERE id = {user_id}"

# Hardcoded password
password = "secret123"

# API key exposure
api_key = "sk-1234567890abcdef"

# Dangerous function usage
os.system("rm -rf /")
eval("dangerous_code()")
exec("malicious_code")
subprocess.call(["rm", "-rf", "/"], shell=True)

# Weak cryptography
import hashlib
hash_value = hashlib.md5(data).hexdigest()

# Insecure random
import random
token = random.random()

# Deserialization vulnerability
data = pickle.loads(untrusted_data)

# Path traversal
file_path = "../../../etc/passwd"

# XSS patterns (in web context)
element.innerHTML = user_input
"""

        result = analyze_security_patterns(test_code, "test_file.py")

        assert result["success"] == True
        assert result["patterns_found"] > 0
        assert "severity_counts" in result
        assert result["risk_level"] in ["low", "medium", "high", "critical"]

        # Check specific patterns were detected
        pattern_types = [p["type"] for p in result["patterns"]]
        assert "dangerous_functions" in pattern_types
        assert "hardcoded_password" in pattern_types
        assert "hardcoded_api_key" in pattern_types

    def test_caching_functionality(self):
        """Test security scan caching."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello world')")
            file_path = f.name

        try:
            # Get file hash
            file_hash = _get_file_hash(file_path)
            assert file_hash != ""

            # Cache a result
            test_result = {"test": "data", "cached": True}
            _cache_security_result(file_path, file_hash, test_result)

            # Retrieve cached result
            cached_result = _get_cached_security_result(file_path, file_hash)
            assert cached_result is not None
            assert cached_result["test"] == "data"
            assert cached_result["cached"] == True

            # Check cache validation
            assert _is_cache_valid(file_path, file_hash) == True

        finally:
            os.unlink(file_path)
            _clear_security_cache()

    def test_cache_invalidation(self):
        """Test cache invalidation mechanisms."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("original content")
            file_path = f.name

        try:
            # Cache original file
            file_hash1 = _get_file_hash(file_path)
            test_result = {"version": 1}
            _cache_security_result(file_path, file_hash1, test_result)

            # Modify file
            with open(file_path, "w") as f:
                f.write("modified content")

            # New hash should be different
            file_hash2 = _get_file_hash(file_path)
            assert file_hash2 != file_hash1

            # Old cache should not be valid for new hash
            cached_result = _get_cached_security_result(file_path, file_hash2)
            assert cached_result is None

        finally:
            os.unlink(file_path)
            _clear_security_cache()

    def test_security_scanner_parallel_processing(self):
        """Test parallel processing in SecurityScanner."""
        scanner = SecurityScanner(max_workers=2)

        # Create multiple test files
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(
                    f"""
import os
# Test file {i}
password = "test{i}"
os.system("echo test{i}")
"""
                )
                test_files.append(f.name)

        try:
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Move files to temp directory
                for i, src_file in enumerate(test_files):
                    dst_file = os.path.join(temp_dir, f"test_{i}.py")
                    os.rename(src_file, dst_file)
                    test_files[i] = dst_file

                # Scan directory
                result = scanner.scan_directory(temp_dir)

                assert result["success"] == True
                assert result["files_scanned"] == 3
                assert result["total_patterns_found"] > 0
                assert "severity_counts" in result

        finally:
            # Cleanup any remaining files
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_thread_safety(self):
        """Test thread safety of SecurityScanner."""
        scanner = SecurityScanner()
        errors = []

        def worker():
            try:
                for i in range(50):
                    scanner.add_issue(f"file_{i}.py", i + 1, f"Issue {i}", "medium")
                    scanner.get_issues_summary()
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for _ in range(3):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0

        # Check total issues
        summary = scanner.get_issues_summary()
        assert summary["total_issues"] == 150  # 3 threads * 50 issues

    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        scanner = SecurityScanner()

        # Get initial stats
        stats = scanner.get_cache_stats()
        assert "cached_files" in stats
        assert "cache_ttl" in stats
        assert "cache_keys" in stats

        # Add some cache entries
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test content")
            file_path = f.name

        try:
            # Scan to create cache entry
            scanner.scan_file(file_path)

            # Check updated stats
            stats = scanner.get_cache_stats()
            assert stats["cached_files"] > 0

        finally:
            os.unlink(file_path)
            scanner.clear_cache()

    def test_severity_level_mapping(self):
        """Test severity level mapping and calculations."""
        test_code = """
import os
import hashlib

# Critical
os.system("dangerous")
eval("code")

# High
query = f"SELECT * FROM users WHERE id = {id}"
api_key = "sk-12345"

# Medium
password = "secret"
path = "../etc/passwd"

# Low
import random
token = random.random()
"""

        result = analyze_security_patterns(test_code, "test.py")

        # Should detect critical issues and classify as critical
        assert result["risk_level"] == "critical"
        assert result["severity_counts"]["critical"] > 0
        assert result["severity_counts"]["high"] > 0
        assert result["severity_counts"]["medium"] > 0
        assert result["severity_counts"]["low"] > 0

    def test_scan_file_with_caching(self):
        """Test file scanning with caching mechanisms."""
        scanner = SecurityScanner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
password = "secret"
os.system("rm file")
"""
            )
            file_path = f.name

        try:
            # First scan
            start_time = time.time()
            result1 = scanner.scan_file(file_path)
            first_scan_time = time.time() - start_time

            # Second scan (should use cache)
            start_time = time.time()
            result2 = scanner.scan_file(file_path)
            second_scan_time = time.time() - start_time

            # Results should be identical
            assert result1["success"] == result2["success"]
            assert result1["file"] == result2["file"]

            # Second scan should be faster (due to caching)
            assert second_scan_time <= first_scan_time

        finally:
            os.unlink(file_path)

    def test_vulnerability_checker_compatibility(self):
        """Test backward compatibility with VulnerabilityChecker."""
        checker = VulnerabilityChecker()

        test_files = ["test1.py", "test2.py"]
        result = checker.check_vulnerabilities(test_files)

        assert isinstance(result, dict)
        assert "success" in result

    def test_dependency_analyzer_functionality(self):
        """Test DependencyAnalyzer functionality."""
        analyzer = DependencyAnalyzer()

        # Test dependency analysis
        result = analyzer.analyze_dependencies()
        assert isinstance(result, dict)

        # Test package vulnerability checking
        packages = [{"name": "requests", "version": "2.25.1"}]
        vuln_result = analyzer.check_package_vulnerabilities(packages)
        assert isinstance(vuln_result, dict)
        assert "success" in vuln_result

    def test_security_pattern_analyzer(self):
        """Test SecurityPatternAnalyzer functionality."""
        analyzer = SecurityPatternAnalyzer()

        test_code = """
import os
password = "secret"
os.system("dangerous")
"""

        result = analyzer.analyze_patterns(test_code, "test.py")
        assert result["success"] == True
        assert "patterns" in result

        # Test specific pattern checks
        pattern_result = analyzer.check_pattern("password", "test.py")
        assert isinstance(pattern_result, dict)

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        scanner = SecurityScanner()

        # Test with non-existent file
        result = scanner.scan_file("non_existent_file.py")
        assert result["success"] == False
        assert "error" in result

        # Test with non-existent directory - this actually succeeds but returns no files
        result = scanner.scan_directory("non_existent_directory")
        # The scanner walks the directory, and if it doesn't exist, os.walk handles it gracefully
        # So we check for either success with 0 files or failure
        if result["success"]:
            assert result["files_scanned"] == 0
        else:
            assert "error" in result

    def test_parallel_security_checks(self):
        """Test parallel execution of security checks."""
        scanner = SecurityScanner(max_workers=2)

        # Mock the security check functions to return predictable results
        with (
            patch("src.ai_guard.security_scanner.run_bandit") as mock_bandit,
            patch("src.ai_guard.security_scanner.run_safety_check") as mock_safety,
        ):

            mock_bandit.return_value = 0
            mock_safety.return_value = 0

            result = scanner.run_all_security_checks()

            # Both checks should have been called
            mock_bandit.assert_called_once()
            mock_safety.assert_called_once()

            # Result should be successful
            assert result == 0

    def test_file_hash_calculation(self):
        """Test file hash calculation for caching."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content for hashing")
            file_path = f.name

        try:
            hash1 = _get_file_hash(file_path)
            hash2 = _get_file_hash(file_path)

            # Same file should produce same hash
            assert hash1 == hash2
            assert len(hash1) == 32  # MD5 hash length

        finally:
            os.unlink(file_path)

    def test_performance_benchmarks(self):
        """Test performance improvements."""
        scanner = SecurityScanner()

        # Create test files with various security patterns
        test_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(
                    f"""
import os
import subprocess
import random

# File {i} with various patterns
password_{i} = "secret{i}"
api_key_{i} = "sk-{i}234567890"
os.system("command_{i}")
eval(f"code_{i}")
random_val = random.random()

def process_data_{i}():
    query = f"SELECT * FROM table_{i} WHERE id = {{user_id}}"
    subprocess.call(["ls", "-la"], shell=True)
    return query
"""
                )
                test_files.append(f.name)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Move files to temp directory
                for i, src_file in enumerate(test_files):
                    dst_file = os.path.join(temp_dir, f"perf_test_{i}.py")
                    os.rename(src_file, dst_file)
                    test_files[i] = dst_file

                # Benchmark first scan
                start_time = time.time()
                result1 = scanner.scan_directory(temp_dir)
                first_scan_time = time.time() - start_time

                # Benchmark second scan (should use cache)
                start_time = time.time()
                result2 = scanner.scan_directory(temp_dir)
                second_scan_time = time.time() - start_time

                # Results should be consistent
                assert result1["success"] == result2["success"]
                assert result1["files_scanned"] == result2["files_scanned"]

                # Second scan should be faster due to caching
                assert second_scan_time <= first_scan_time

        finally:
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test content")
            file_path = f.name

        try:
            file_hash = _get_file_hash(file_path)

            # Cache a result
            test_result = {"test": "data"}
            _cache_security_result(file_path, file_hash, test_result)

            # Should be valid initially
            assert _is_cache_valid(file_path, file_hash) == True

            # Manually expire cache by modifying timestamp
            from src.ai_guard.security_scanner import _cache_timestamps

            cache_key = f"{file_path}:{file_hash}"
            _cache_timestamps[cache_key] = time.time() - 700  # 700 seconds ago

            # Should now be invalid
            assert _is_cache_valid(file_path, file_hash) == False

        finally:
            os.unlink(file_path)
            _clear_security_cache()

    def test_advanced_pattern_matching(self):
        """Test advanced security pattern matching."""
        advanced_test_code = """
# Advanced SQL injection patterns
query1 = f"SELECT * FROM users WHERE name = '{user_name}' AND active = 1"
query2 = "INSERT INTO logs VALUES (%s, %s)" % (user_id, message)
query3 = f"UPDATE accounts SET balance = balance + {amount} WHERE id = {account_id}"

# Advanced hardcoded secrets
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
database_password = "P@ssw0rd123!"
secret_token = "ghp_1234567890abcdef1234567890abcdef123456"

# Advanced dangerous operations
import subprocess
import marshal
import yaml

subprocess.run(user_command, shell=True, capture_output=False)
dangerous_data = marshal.loads(untrusted_input)
config = yaml.load(user_config, Loader=yaml.Loader)

# Advanced path traversal
file_path = f"../../../{user_input}/config.txt"
with open(f"uploads/{filename}", "w") as f:
    pass

# Advanced XSS patterns (for web frameworks)
html_content = f"<div>{user_content}</div>"
element.innerHTML = request.form.get("content")
document.write(user_data)
"""

        result = analyze_security_patterns(advanced_test_code, "advanced_test.py")

        assert result["success"] == True
        assert result["patterns_found"] > 10  # Should detect many patterns
        assert (
            result["risk_level"] == "critical"
        )  # Should be critical due to dangerous functions

        # Check that different severity levels are detected
        assert result["severity_counts"]["critical"] > 0
        assert result["severity_counts"]["high"] > 0
        assert result["severity_counts"]["medium"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
