"""Edge case and error handling tests for comprehensive coverage."""

import pytest
import tempfile
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from concurrent.futures import ThreadPoolExecutor

from src.ai_guard.analyzer import (
    run_analysis,
    AnalysisConfig,
    CodeAnalyzer,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_output,
    _run_tool,
    _to_text,
    _coverage_percent_from_xml,
    cov_percent,
)
from src.ai_guard.config import (
    load_config,
    save_config,
    _load_toml_config,
    _load_json_config,
    _load_yaml_config,
    _validate_config_section,
)
from src.ai_guard.cache import LRUCache, TTLCache, CacheManager
from src.ai_guard.security_scanner import (
    scan_file,
    scan_directory,
    scan_code_string,
    _get_file_hash,
    _parse_bandit_output as scanner_parse_bandit,
)
from src.ai_guard.analytics import AnalyticsSystem, MetricsCollector, KPIManager


class TestAnalyzerEdgeCases:
    """Test analyzer edge cases and error handling."""

    def test_analysis_with_empty_file(self):
        """Test analysis with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")  # Empty file
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                assert result is not None
                assert result.execution_time >= 0
                assert isinstance(result.security_issues, list)
                assert isinstance(result.performance_issues, list)
                assert isinstance(result.quality_issues, list)
                assert isinstance(result.coverage_data, dict)

            finally:
                os.unlink(f.name)

    def test_analysis_with_invalid_python_syntax(self):
        """Test analysis with invalid Python syntax."""
        invalid_code = """
def broken_function(
    # Missing closing parenthesis
    x, y, z

def another_broken_function:
    # Missing parentheses
    pass

# Invalid syntax
if True
    print("missing colon")
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                # Should handle gracefully without crashing
                assert result is not None
                assert result.execution_time >= 0

            finally:
                os.unlink(f.name)

    def test_analysis_with_very_long_lines(self):
        """Test analysis with very long lines."""
        long_line = "x = " + "1 + " * 10000 + "1"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(long_line)
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                # Should handle long lines gracefully
                assert result is not None
                assert result.execution_time >= 0

            finally:
                os.unlink(f.name)

    def test_analysis_with_special_characters(self):
        """Test analysis with special characters and encoding."""
        special_code = """
# Unicode characters
name = "José María"
price = "€100.50"

# Special characters in strings
path = "C:\\Users\\Test\\file.txt"
regex = r"[\\w\\d\\s]+"

# Non-ASCII identifiers
def función_especial(x):
    return x * 2

# Emoji in comments
# 🚀 This is a rocket comment
result = 42
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", encoding="utf-8", delete=False
        ) as f:
            f.write(special_code)
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                # Should handle special characters gracefully
                assert result is not None
                assert result.execution_time >= 0

            finally:
                os.unlink(f.name)

    def test_analysis_with_nested_directories(self):
        """Test analysis with deeply nested directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure
            nested_path = temp_dir
            for i in range(10):
                nested_path = os.path.join(nested_path, f"level_{i}")
                os.makedirs(nested_path)

            # Create file in deepest directory
            test_file = os.path.join(nested_path, "test.py")
            with open(test_file, "w") as f:
                f.write("print('hello from deep directory')")

            try:
                config = AnalysisConfig()
                result = run_analysis([test_file], config)

                # Should handle deep paths
                assert result is not None
                assert result.execution_time >= 0

            except Exception as e:
                # Should not crash, but may have path length limitations
                assert "path" in str(e).lower() or "too long" in str(e).lower()

    def test_analysis_with_symbolic_links(self):
        """Test analysis with symbolic links."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create original file
            original_file = os.path.join(temp_dir, "original.py")
            with open(original_file, "w") as f:
                f.write("print('original file')")

            # Create symbolic link
            link_file = os.path.join(temp_dir, "link.py")
            try:
                os.symlink(original_file, link_file)

                config = AnalysisConfig()
                result = run_analysis([link_file], config)

                # Should handle symbolic links
                assert result is not None
                assert result.execution_time >= 0

            except OSError:
                # Symlinks may not be supported on all systems
                pytest.skip("Symbolic links not supported on this system")

    def test_analysis_with_concurrent_access(self):
        """Test analysis with concurrent file access."""
        test_code = "print('concurrent test')"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                config = AnalysisConfig()

                def analyze_file():
                    return run_analysis([f.name], config)

                # Run multiple analyses concurrently
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(analyze_file) for _ in range(10)]
                    results = [future.result() for future in futures]

                # All should complete successfully
                assert len(results) == 10
                for result in results:
                    assert result is not None
                    assert result.execution_time >= 0

            finally:
                os.unlink(f.name)

    def test_analysis_with_network_paths(self):
        """Test analysis with network/UNC paths."""
        # Test with UNC path format (Windows)
        unc_path = "\\\\server\\share\\file.py"

        config = AnalysisConfig()
        result = run_analysis([unc_path], config)

        # Should handle network paths gracefully
        assert result is not None
        assert result.execution_time >= 0

    def test_analysis_with_read_only_files(self):
        """Test analysis with read-only files."""
        test_code = "print('read only test')"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # Make file read-only
                os.chmod(f.name, 0o444)

                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                # Should handle read-only files
                assert result is not None
                assert result.execution_time >= 0

            finally:
                # Restore permissions
                os.chmod(f.name, 0o644)
                os.unlink(f.name)

    def test_analysis_with_zero_size_file(self):
        """Test analysis with zero-size file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Don't write anything, creating zero-size file
            f.flush()

            try:
                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                # Should handle zero-size files
                assert result is not None
                assert result.execution_time >= 0

            finally:
                os.unlink(f.name)


class TestParserEdgeCases:
    """Test parser edge cases and error handling."""

    def test_parse_flake8_output_malformed(self):
        """Test parsing malformed flake8 output."""
        malformed_outputs = [
            "invalid format",
            "file.py:invalid:line: E501 message",
            "file.py:1:invalid_column: E501 message",
            "file.py:1:5: message without code",
            "file.py:1:5: E message",
            "",
            "\n\n\n",
            "file.py:1:5: E501",
        ]

        for output in malformed_outputs:
            result = _parse_flake8_output(output)
            # Should not crash, return empty list or valid results
            assert isinstance(result, list)

    def test_parse_mypy_output_malformed(self):
        """Test parsing malformed mypy output."""
        malformed_outputs = [
            "invalid format",
            "file.py:invalid: error: message",
            "file.py:1: invalid_severity: message",
            "file.py:1: error: message [invalid_code",
            "",
            "\n\n\n",
        ]

        for output in malformed_outputs:
            result = _parse_mypy_output(output)
            # Should not crash, return empty list or valid results
            assert isinstance(result, list)

    def test_parse_bandit_output_malformed(self):
        """Test parsing malformed bandit output."""
        malformed_outputs = [
            "invalid json",
            '{"invalid": "structure"}',
            '{"results": "not_a_list"}',
            '{"results": [{"invalid": "structure"}]}',
            "",
            "\n\n\n",
        ]

        for output in malformed_outputs:
            result = _parse_bandit_output(output)
            # Should not crash, return empty list or valid results
            assert isinstance(result, list)

    def test_run_tool_timeout(self):
        """Test tool execution timeout."""
        # Test with command that would hang
        result = _run_tool(["python", "-c", "import time; time.sleep(10)"])

        # Should handle timeout gracefully
        assert result is not None
        assert result.returncode != 0

    def test_run_tool_invalid_command(self):
        """Test tool execution with invalid command."""
        result = _run_tool(["nonexistent_command_12345"])

        # Should handle invalid command gracefully
        assert result is not None
        assert result.returncode != 0

    def test_to_text_edge_cases(self):
        """Test _to_text function with edge cases."""
        test_cases = [
            None,
            "",
            b"",
            bytearray(),
            b"\x00\x01\x02\x03",  # Null bytes
            b"\xff\xfe\xfd",  # Invalid UTF-8
            "normal string",
            b"normal bytes",
            bytearray(b"normal bytearray"),
        ]

        for case in test_cases:
            result = _to_text(case)
            # Should always return a string
            assert isinstance(result, str)

    def test_coverage_percent_edge_cases(self):
        """Test coverage percentage parsing edge cases."""
        # Test with invalid XML
        invalid_xml = """<?xml version="1.0"?>
        <invalid>
            <not-coverage>
                <wrong-structure/>
            </not-coverage>
        </invalid>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(invalid_xml)
            f.flush()

            try:
                result = _coverage_percent_from_xml(f.name)
                # Should handle invalid XML gracefully
                assert result is None

            finally:
                os.unlink(f.name)

    def test_cov_percent_edge_cases(self):
        """Test cov_percent function edge cases."""
        # Test with nonexistent files
        result = cov_percent()
        # Should handle missing files gracefully
        assert result is None or isinstance(result, int)


class TestConfigEdgeCases:
    """Test configuration edge cases and error handling."""

    def test_load_config_nonexistent_file(self):
        """Test loading nonexistent configuration file."""
        result = load_config("nonexistent_config.json")
        assert result == {}

    def test_load_config_permission_denied(self):
        """Test loading config with permission denied."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "value"}')
            f.flush()

            try:
                # Make file unreadable
                os.chmod(f.name, 0o000)

                result = load_config(f.name)
                # Should handle permission denied gracefully
                assert result == {}

            finally:
                # Restore permissions
                os.chmod(f.name, 0o644)
                os.unlink(f.name)

    def test_load_config_corrupted_file(self):
        """Test loading corrupted configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "value"')  # Missing closing brace
            f.flush()

            try:
                result = load_config(f.name)
                # Should handle corrupted file gracefully
                assert result == {}

            finally:
                os.unlink(f.name)

    def test_load_toml_config_edge_cases(self):
        """Test TOML config loading edge cases."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("[invalid toml syntax")  # Invalid TOML
            f.flush()

            try:
                result = _load_toml_config(f.name)
                # Should handle invalid TOML gracefully
                assert result == {}

            finally:
                os.unlink(f.name)

    def test_load_json_config_edge_cases(self):
        """Test JSON config loading edge cases."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "value"')  # Incomplete JSON
            f.flush()

            try:
                result = _load_json_config(f.name)
                # Should handle invalid JSON gracefully
                assert result == {}

            finally:
                os.unlink(f.name)

    def test_load_yaml_config_edge_cases(self):
        """Test YAML config loading edge cases."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML
            f.flush()

            try:
                result = _load_yaml_config(f.name)
                # Should handle invalid YAML gracefully
                assert result == {}

            finally:
                os.unlink(f.name)

    def test_validate_config_section_edge_cases(self):
        """Test config section validation edge cases."""
        edge_cases = [
            {},  # Empty config
            None,  # None config
            {"invalid_key": "invalid_value"},  # Invalid keys
            {"coverage_threshold": -1},  # Invalid values
            {"coverage_threshold": 101},  # Out of range
            {"enable_security": "maybe"},  # Invalid boolean
            {"output_format": "invalid_format"},  # Invalid format
            {"llm_provider": "invalid_provider"},  # Invalid provider
        ]

        for config in edge_cases:
            result, errors = _validate_config_section(config)
            # Should always return tuple with boolean and list
            assert isinstance(result, bool)
            assert isinstance(errors, list)

    def test_save_config_edge_cases(self):
        """Test saving config edge cases."""
        config = {"test": "value"}

        # Test saving to invalid path
        result = save_config(config, "/invalid/path/config.json")
        assert result is False

        # Test saving to read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only
            os.chmod(temp_dir, 0o444)

            config_file = os.path.join(temp_dir, "config.json")
            result = save_config(config, config_file)
            # Should handle permission denied gracefully
            assert result is False


class TestCacheEdgeCases:
    """Test cache edge cases and error handling."""

    def test_lru_cache_edge_cases(self):
        """Test LRU cache edge cases."""
        cache = LRUCache(max_size=0)  # Zero size cache

        # Should handle zero size gracefully
        cache.set("key", "value")
        assert cache.get("key") is None

        cache = LRUCache(max_size=1)  # Size of 1
        cache.set("key1", "value1")
        cache.set("key2", "value2")  # Should evict key1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_ttl_cache_edge_cases(self):
        """Test TTL cache edge cases."""
        cache = TTLCache(max_size=100, ttl=0)  # Zero TTL

        cache.set("key", "value")
        # Should expire immediately
        assert cache.get("key") is None

        cache = TTLCache(max_size=100, ttl=None)  # No expiration
        cache.set("key", "value")
        # Should never expire
        assert cache.get("key") == "value"

    def test_cache_concurrent_edge_cases(self):
        """Test cache concurrent access edge cases."""
        cache = LRUCache(max_size=10)

        def worker(thread_id, num_operations):
            for i in range(num_operations):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"

                # Mix of operations
                cache.set(key, value)
                retrieved = cache.get(key)
                cache.delete(key)

                # Should not crash
                assert retrieved == value or retrieved is None

        # Run concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i, 100))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Cache should still be functional
        cache.set("final_key", "final_value")
        assert cache.get("final_key") == "final_value"

    def test_cache_memory_edge_cases(self):
        """Test cache memory edge cases."""
        cache = LRUCache(max_size=1000)

        # Test with very large values
        large_value = "x" * 100000  # 100KB value

        cache.set("large_key", large_value)
        retrieved = cache.get("large_key")
        assert retrieved == large_value

        # Test with None values
        cache.set("none_key", None)
        retrieved = cache.get("none_key")
        assert retrieved is None

        # Test with empty string
        cache.set("empty_key", "")
        retrieved = cache.get("empty_key")
        assert retrieved == ""


class TestSecurityScannerEdgeCases:
    """Test security scanner edge cases and error handling."""

    def test_security_scan_nonexistent_file(self):
        """Test security scanning nonexistent file."""
        result = scan_file("nonexistent.py")

        assert result["total_issues"] == 0
        assert result["files_scanned"] == 0
        assert result["scan_duration"] >= 0

    def test_security_scan_permission_denied(self):
        """Test security scanning file with permission denied."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('test')")
            f.flush()

            try:
                # Make file unreadable
                os.chmod(f.name, 0o000)

                result = scan_file(f.name)
                # Should handle permission denied gracefully
                assert result["total_issues"] == 0
                assert result["files_scanned"] == 0

            finally:
                # Restore permissions
                os.chmod(f.name, 0o644)
                os.unlink(f.name)

    def test_security_scan_empty_directory(self):
        """Test security scanning empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = scan_directory(temp_dir)

            assert result["total_issues"] == 0
            assert result["files_scanned"] == 0
            assert result["scan_duration"] >= 0

    def test_security_scan_directory_with_non_python_files(self):
        """Test security scanning directory with non-Python files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various file types
            files = [
                "test.py",
                "test.txt",
                "test.json",
                "test.xml",
                "test.md",
                "test.js",
                "test.html",
                "test.css",
            ]

            for filename in files:
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, "w") as f:
                    f.write(f"content for {filename}")

            result = scan_directory(temp_dir)

            # Should only scan Python files
            assert result["files_scanned"] == 1
            assert result["total_issues"] == 0

    def test_security_scan_code_string_edge_cases(self):
        """Test security scanning code string edge cases."""
        edge_cases = [
            "",  # Empty string
            "\n\n\n",  # Only newlines
            "# Only comments\n# Another comment",  # Only comments
            "    \t  \n  \t",  # Only whitespace
            "def function():\n    pass",  # Valid but minimal code
            "x = 1\n" * 10000,  # Very long code
        ]

        for code in edge_cases:
            result = scan_code_string(code, "test.py")
            # Should handle all edge cases gracefully
            assert isinstance(result, list)

    def test_get_file_hash_edge_cases(self):
        """Test file hashing edge cases."""
        # Test with nonexistent file
        result = _get_file_hash("nonexistent.py")
        assert result == ""

        # Test with empty file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.flush()  # Empty file

            try:
                result = _get_file_hash(f.name)
                # Should handle empty file
                assert isinstance(result, str)

            finally:
                os.unlink(f.name)

    def test_scanner_parse_bandit_edge_cases(self):
        """Test security scanner bandit parsing edge cases."""
        edge_cases = [
            "",  # Empty output
            "invalid json",  # Invalid JSON
            '{"results": null}',  # Null results
            '{"results": []}',  # Empty results
            '{"results": [{"invalid": "structure"}]}',  # Invalid structure
        ]

        for output in edge_cases:
            result = scanner_parse_bandit(output)
            # Should handle all edge cases gracefully
            assert isinstance(result, list)


class TestAnalyticsEdgeCases:
    """Test analytics edge cases and error handling."""

    def test_analytics_with_empty_data(self):
        """Test analytics with empty data."""
        analytics = AnalyticsSystem()

        # Generate report with no data
        report = analytics.generate_executive_report()

        assert report is not None
        assert report.report_type == "executive"
        assert "kpis" in report.data

    def test_analytics_with_invalid_metrics(self):
        """Test analytics with invalid metrics."""
        analytics = AnalyticsSystem()

        # Add invalid metric data
        analytics.metrics_collector.add_metric(
            name="",  # Empty name
            value=None,  # None value
            metric_type=analytics.metrics_collector.MetricType.GAUGE,
            tags={"invalid": "tag"},
        )

        # Should handle gracefully
        metrics = analytics.metrics_collector.get_metrics()
        assert isinstance(metrics, list)

    def test_analytics_concurrent_access(self):
        """Test analytics with concurrent access."""
        analytics = AnalyticsSystem()

        def add_metrics(thread_id):
            for i in range(100):
                analytics.metrics_collector.add_metric(
                    name=f"metric_{thread_id}_{i}",
                    value=i,
                    metric_type=analytics.metrics_collector.MetricType.GAUGE,
                )

        # Run concurrent metric addition
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_metrics, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access gracefully
        metrics = analytics.metrics_collector.get_metrics()
        assert isinstance(metrics, list)

    def test_kpi_manager_edge_cases(self):
        """Test KPI manager edge cases."""
        metrics_collector = MetricsCollector()
        kpi_manager = KPIManager(metrics_collector)

        # Test with no metrics
        statuses = kpi_manager.get_all_kpi_statuses()
        assert isinstance(statuses, list)

        # Test creating KPI with invalid data
        try:
            kpi = kpi_manager.create_kpi(
                name="",  # Empty name
                description="",  # Empty description
                kpi_type="invalid_type",  # Invalid type
                metric_name="",  # Empty metric name
                target_value=-1,  # Negative target
                warning_threshold=-2,  # Negative warning
                critical_threshold=-3,  # Negative critical
            )
            # Should handle gracefully or raise appropriate exception
        except Exception:
            # Expected for invalid data
            pass


class TestSystemEdgeCases:
    """Test system-level edge cases and error handling."""

    def test_analysis_with_system_resources_exhausted(self):
        """Test analysis when system resources are exhausted."""
        # This is a theoretical test - in practice, we can't easily exhaust
        # system resources in a test, but we can test graceful handling

        config = AnalysisConfig()

        # Test with very large file that might cause memory issues
        large_code = "x = 1\n" * 100000  # 100k lines

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(large_code)
            f.flush()

            try:
                result = run_analysis([f.name], config)

                # Should handle large files gracefully
                assert result is not None
                assert result.execution_time >= 0

            finally:
                os.unlink(f.name)

    def test_analysis_with_network_issues(self):
        """Test analysis with simulated network issues."""
        config = AnalysisConfig()

        # Mock network-dependent operations to simulate failures
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")
        ):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("print('test')")
                f.flush()

                try:
                    result = run_analysis([f.name], config)

                    # Should handle network issues gracefully
                    assert result is not None
                    assert result.execution_time >= 0

                finally:
                    os.unlink(f.name)

    def test_analysis_with_disk_space_issues(self):
        """Test analysis with disk space issues."""
        config = AnalysisConfig()

        # Mock file operations to simulate disk space issues
        with patch("builtins.open", side_effect=OSError(28, "No space left on device")):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("print('test')")
                f.flush()

                try:
                    result = run_analysis([f.name], config)

                    # Should handle disk space issues gracefully
                    assert result is not None
                    assert result.execution_time >= 0

                finally:
                    os.unlink(f.name)

    def test_analysis_with_timeout_issues(self):
        """Test analysis with timeout issues."""
        config = AnalysisConfig()

        # Mock slow operations to simulate timeout
        def slow_operation(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow operation
            return MagicMock()

        with patch("subprocess.run", side_effect=slow_operation):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("print('test')")
                f.flush()

                try:
                    result = run_analysis([f.name], config)

                    # Should handle timeout issues gracefully
                    assert result is not None
                    assert result.execution_time >= 0

                finally:
                    os.unlink(f.name)
