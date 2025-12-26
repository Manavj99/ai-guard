"""Comprehensive tests for optimized config.py module."""

import os
import tempfile
import threading
import time
import json
import pytest
from unittest.mock import patch, mock_open
from src.ai_guard.config import (
    Config,
    Gates,
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
    load_config,
    _validate_coverage_value,
    _validate_boolean_value,
    _validate_report_format,
    _validate_llm_provider,
    _validate_file_path,
    _clear_cache,
    _get_cached_config,
    _cache_config,
    _is_cache_valid,
)


class TestConfigOptimizations:
    """Test optimized configuration functionality."""

    def test_caching_functionality(self):
        """Test configuration caching with TTL."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
min_coverage = 85
report_format = "json"
skip_tests = true
"""
            )
            config_path = f.name

        try:
            # First load should cache the config
            config1 = load_config(config_path)
            assert config1["min_coverage"] == 85

            # Second load should use cache
            config2 = load_config(config_path)
            assert config2["min_coverage"] == 85

            # Check if config is cached
            cached_config = _get_cached_config(config_path)
            assert cached_config is not None
            assert cached_config["min_coverage"] == 85

        finally:
            os.unlink(config_path)

    def test_cache_invalidation(self):
        """Test cache invalidation when file changes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("min_coverage = 80")
            config_path = f.name

        try:
            # Load initial config
            config1 = load_config(config_path)
            assert config1["min_coverage"] == 80

            # Modify file
            time.sleep(0.1)  # Ensure different timestamp
            with open(config_path, "w") as f:
                f.write("min_coverage = 90")

            # Load again - should detect file change
            config2 = load_config(config_path)
            assert config2["min_coverage"] == 90

        finally:
            os.unlink(config_path)

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("min_coverage = 80")
            config_path = f.name

        try:
            # Load config
            config1 = load_config(config_path)
            assert config1["min_coverage"] == 80

            # Manually expire cache by modifying timestamp
            from src.ai_guard.config import _cache_timestamps

            _cache_timestamps[config_path] = time.time() - 400  # 400 seconds ago

            # Load again - should reload due to TTL expiration
            config2 = load_config(config_path)
            assert config2["min_coverage"] == 80

        finally:
            os.unlink(config_path)

    def test_enhanced_validation(self):
        """Test enhanced validation functions."""
        # Test coverage validation
        assert _validate_coverage_value(80) == True
        assert _validate_coverage_value("85") == True
        assert _validate_coverage_value(150) == False
        assert _validate_coverage_value(-10) == False
        assert _validate_coverage_value("invalid") == False

        # Test boolean validation
        assert _validate_boolean_value(True) == True
        assert _validate_boolean_value("true") == True
        assert _validate_boolean_value("false") == True
        assert _validate_boolean_value("1") == True
        assert _validate_boolean_value("0") == True
        assert _validate_boolean_value("invalid") == False

        # Test report format validation
        assert _validate_report_format("sarif") == True
        assert _validate_report_format("json") == True
        assert _validate_report_format("html") == True
        assert _validate_report_format("xml") == False

        # Test LLM provider validation
        assert _validate_llm_provider("openai") == True
        assert _validate_llm_provider("anthropic") == True
        assert _validate_llm_provider("claude") == False

        # Test file path validation
        assert _validate_file_path("ai-guard.sarif") == True
        assert _validate_file_path("reports/test.json") == True
        assert _validate_file_path("invalid@path") == False

    def test_thread_safety(self):
        """Test thread safety of Config class."""
        config = Config()
        results = []
        errors = []

        def worker():
            try:
                for _ in range(100):
                    config.get("min_coverage")
                    config.set("test_key", "test_value")
                    config.get("test_key")
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0

    def test_config_validation_with_invalid_values(self):
        """Test config validation with invalid values."""
        # Test invalid coverage
        invalid_configs = [
            {"min_coverage": 150},  # Too high
            {"min_coverage": -10},  # Negative
            {"min_coverage": "invalid"},  # Not a number
            {"report_format": "xml"},  # Invalid format
            {"llm_provider": "claude"},  # Invalid provider
            {"report_path": "invalid@path"},  # Invalid path
            {"skip_tests": "maybe"},  # Invalid boolean
        ]

        for config in invalid_configs:
            assert validate_config(config) == False

    def test_config_validation_with_valid_values(self):
        """Test config validation with valid values."""
        valid_configs = [
            {"min_coverage": 80},
            {"min_coverage": "85"},
            {"report_format": "sarif"},
            {"llm_provider": "openai"},
            {"report_path": "ai-guard.sarif"},
            {"skip_tests": True},
            {"skip_tests": "true"},
            {"skip_tests": "1"},
            {"gates": {"min_coverage": 90}},
            {},  # Empty config is valid
        ]

        for config in valid_configs:
            assert validate_config(config) == True

    def test_config_set_with_validation(self):
        """Test Config.set() with validation."""
        config = Config()

        # Valid values should work
        config.set("min_coverage", 85)
        assert config.get("min_coverage") == 85

        config.set("report_format", "json")
        assert config.get("report_format") == "json"

        # Invalid values should raise ValueError
        with pytest.raises(ValueError):
            config.set("min_coverage", 150)

        with pytest.raises(ValueError):
            config.set("report_format", "xml")

        with pytest.raises(ValueError):
            config.set("skip_tests", "maybe")

    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        config = Config()

        # Get initial cache stats
        stats = config.get_cache_stats()
        assert "cached_files" in stats
        assert "cache_ttl" in stats
        assert "files" in stats
        assert "timestamps" in stats

    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("min_coverage = 80")
            config_path = f.name

        try:
            # Load config to cache it
            config1 = load_config(config_path)
            assert _get_cached_config(config_path) is not None

            # Clear cache
            _clear_cache(config_path)
            assert _get_cached_config(config_path) is None

            # Clear all cache
            load_config(config_path)  # Cache again
            _clear_cache()  # Clear all
            assert len(_get_cached_config(config_path) or {}) == 0

        finally:
            os.unlink(config_path)

    def test_json_config_loading(self):
        """Test JSON configuration loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {"min_coverage": 90, "report_format": "json", "skip_tests": True}, f
            )
            config_path = f.name

        try:
            config = load_config(config_path)
            assert config["min_coverage"] == 90
            assert config["report_format"] == "json"
            assert config["skip_tests"] == True

        finally:
            os.unlink(config_path)

    def test_config_reload_with_cache_invalidation(self):
        """Test config reload with cache invalidation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("min_coverage = 80")
            config_path = f.name

        try:
            config = Config(config_path)
            assert config.min_coverage == 80

            # Modify file
            with open(config_path, "w") as f:
                f.write("min_coverage = 90")

            # Reload should pick up changes
            config.reload()
            assert config.min_coverage == 90

        finally:
            os.unlink(config_path)

    def test_parse_config_value(self):
        """Test configuration value parsing."""
        # Test auto-detection
        assert parse_config_value("true") == True
        assert parse_config_value("false") == False
        assert parse_config_value("123") == 123
        assert parse_config_value("123.45") == 123.45
        assert parse_config_value("hello") == "hello"

        # Test specific types
        assert parse_config_value("true", "bool") == True
        assert parse_config_value("123", "int") == 123
        assert parse_config_value("123.45", "float") == 123.45
        assert parse_config_value("hello", "string") == "hello"

        # Test edge cases
        assert parse_config_value("", "int") == 0
        assert parse_config_value("", "float") == 0.0
        assert parse_config_value("1", "bool") == True
        assert parse_config_value("0", "bool") == False

    def test_merge_configs(self):
        """Test configuration merging."""
        base = {
            "min_coverage": 80,
            "report_format": "sarif",
            "gates": {"fail_on_bandit": True},
        }

        override = {"min_coverage": 90, "gates": {"fail_on_lint": False}}

        merged = merge_configs(base, override)
        assert merged["min_coverage"] == 90
        assert merged["report_format"] == "sarif"
        assert merged["gates"]["fail_on_bandit"] == True
        assert merged["gates"]["fail_on_lint"] == False

    def test_config_from_dict(self):
        """Test creating Config from dictionary."""
        config_dict = {"min_coverage": 85, "report_format": "json", "skip_tests": True}

        config = Config.from_dict(config_dict)
        assert config.min_coverage == 85
        assert config.report_format == "json"
        assert config.skip_tests == True

    def test_config_to_dict(self):
        """Test converting Config to dictionary."""
        config = Config()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "min_coverage" in config_dict
        assert "report_format" in config_dict

    def test_config_validation_method(self):
        """Test Config.validate() method."""
        config = Config()
        assert config.validate() == True

        # Test with invalid config by directly modifying _config
        config._config["min_coverage"] = 150
        assert config.validate() == False

    def test_is_cached_method(self):
        """Test Config.is_cached() method."""
        # Create a temporary config file first
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("min_coverage = 80")
            config_path = f.name

        try:
            config = Config(config_path)
            # Should be cached after loading
            assert config.is_cached() == True

        finally:
            os.unlink(config_path)

    def test_performance_benchmark(self):
        """Test performance improvements."""
        import time

        # Create a config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
min_coverage = 80
report_format = "sarif"
skip_tests = false
enhanced_testgen = true
llm_provider = "openai"
llm_model = "gpt-4"
"""
            )
            config_path = f.name

        try:
            # Benchmark first load (should be slower)
            start_time = time.time()
            config1 = load_config(config_path)
            first_load_time = time.time() - start_time

            # Benchmark second load (should use cache)
            start_time = time.time()
            config2 = load_config(config_path)
            second_load_time = time.time() - start_time

            # Second load should be significantly faster
            assert second_load_time < first_load_time
            assert config1 == config2

        finally:
            os.unlink(config_path)

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with non-existent file
        config = load_config("non_existent_file.toml")
        assert config == get_default_config()

        # Test with invalid TOML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("invalid toml content [")
            config_path = f.name

        try:
            config = load_config(config_path)
            assert config == get_default_config()

        finally:
            os.unlink(config_path)

    def test_backward_compatibility(self):
        """Test backward compatibility with existing code."""
        # Test Gates class
        gates = Gates(min_coverage=85, fail_on_bandit=False)
        assert gates.min_coverage == 85
        assert gates.fail_on_bandit == False
        assert gates.get("min_coverage") == 85
        assert gates.get("nonexistent", "default") == "default"

        # Test Config class properties
        config = Config()
        assert isinstance(config.min_coverage, int)
        assert isinstance(config.skip_tests, bool)
        assert isinstance(config.report_format, str)
        assert isinstance(config.fail_on_bandit, bool)

    def test_concurrent_access(self):
        """Test concurrent access to configuration."""
        config = Config()
        results = []

        def reader():
            for _ in range(50):
                results.append(config.min_coverage)

        def writer():
            for i in range(50):
                config.set("test_key", f"value_{i}")

        # Start reader and writer threads
        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)

        reader_thread.start()
        writer_thread.start()

        reader_thread.join()
        writer_thread.join()

        # Should have no errors and correct results
        assert len(results) == 50
        assert all(r == 80 for r in results)  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
