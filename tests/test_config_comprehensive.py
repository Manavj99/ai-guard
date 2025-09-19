"""Comprehensive tests for config.py module."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, mock_open

from src.ai_guard.config import (
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
    load_config,
    Gates,
    Config,
)


class TestGetDefaultConfig:
    """Test get_default_config function."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert "min_coverage" in config
        assert "skip_tests" in config
        assert "report_format" in config
        assert "report_path" in config
        assert "enhanced_testgen" in config
        assert "llm_provider" in config
        assert "llm_api_key" in config
        assert "llm_model" in config
        assert "gates" in config
        
        # Check default values
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"
        assert config["report_path"] == "ai-guard.sarif"
        assert config["enhanced_testgen"] is False
        assert config["llm_provider"] == "openai"
        assert config["llm_api_key"] == ""
        assert config["llm_model"] == "gpt-4"
        
        # Check gates defaults
        gates = config["gates"]
        assert gates["fail_on_bandit"] is True
        assert gates["fail_on_lint"] is True
        assert gates["fail_on_mypy"] is True


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_none(self):
        """Test validating None config."""
        assert validate_config(None) is False

    def test_validate_config_not_dict(self):
        """Test validating non-dict config."""
        assert validate_config("not a dict") is False
        assert validate_config(123) is False
        assert validate_config([]) is False

    def test_validate_config_empty(self):
        """Test validating empty config."""
        assert validate_config({}) is True

    def test_validate_config_valid_min_coverage(self):
        """Test validating config with valid min_coverage."""
        config = {"min_coverage": 85}
        assert validate_config(config) is True

    def test_validate_config_invalid_min_coverage_negative(self):
        """Test validating config with negative min_coverage."""
        config = {"min_coverage": -1}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_over_100(self):
        """Test validating config with min_coverage over 100."""
        config = {"min_coverage": 101}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_not_int(self):
        """Test validating config with non-int min_coverage."""
        config = {"min_coverage": "85"}
        assert validate_config(config) is False

    def test_validate_config_gates_invalid_structure(self):
        """Test validating config with invalid gates structure."""
        config = {"gates": "not a dict"}
        assert validate_config(config) is False

    def test_validate_config_gates_invalid_boolean_fields(self):
        """Test validating config with invalid boolean fields in gates."""
        config = {
            "gates": {
                "fail_on_bandit": "not a boolean",
                "fail_on_lint": True,
                "fail_on_mypy": True
            }
        }
        assert validate_config(config) is False

    def test_validate_config_gates_valid(self):
        """Test validating config with valid gates."""
        config = {
            "gates": {
                "fail_on_bandit": True,
                "fail_on_lint": False,
                "fail_on_mypy": True
            }
        }
        assert validate_config(config) is True

    def test_validate_config_report_format_invalid(self):
        """Test validating config with invalid report format."""
        config = {"report_format": "invalid_format"}
        assert validate_config(config) is False

    def test_validate_config_report_format_valid(self):
        """Test validating config with valid report format."""
        config = {"report_format": "json"}
        assert validate_config(config) is True


class TestMergeConfigs:
    """Test merge_configs function."""

    def test_merge_configs_base_none(self):
        """Test merging with None base config."""
        override = {"min_coverage": 90}
        result = merge_configs(None, override)
        assert result == override

    def test_merge_configs_override_none(self):
        """Test merging with None override config."""
        base = {"min_coverage": 80}
        result = merge_configs(base, None)
        assert result == base

    def test_merge_configs_both_none(self):
        """Test merging with both configs None."""
        result = merge_configs(None, None)
        assert result == {}

    def test_merge_configs_simple_merge(self):
        """Test simple config merge."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {"min_coverage": 90}
        result = merge_configs(base, override)
        
        assert result["min_coverage"] == 90
        assert result["skip_tests"] is False

    def test_merge_configs_gates_merge(self):
        """Test merging configs with gates."""
        base = {
            "min_coverage": 80,
            "gates": {
                "fail_on_bandit": True,
                "fail_on_lint": True
            }
        }
        override = {
            "gates": {
                "fail_on_mypy": False
            }
        }
        result = merge_configs(base, override)
        
        assert result["min_coverage"] == 80
        assert result["gates"]["fail_on_bandit"] is True
        assert result["gates"]["fail_on_lint"] is True
        assert result["gates"]["fail_on_mypy"] is False

    def test_merge_configs_gates_override(self):
        """Test overriding gates values."""
        base = {
            "gates": {
                "fail_on_bandit": True,
                "fail_on_lint": True
            }
        }
        override = {
            "gates": {
                "fail_on_bandit": False
            }
        }
        result = merge_configs(base, override)
        
        assert result["gates"]["fail_on_bandit"] is False
        assert result["gates"]["fail_on_lint"] is True


class TestParseConfigValue:
    """Test parse_config_value function."""

    def test_parse_config_value_string(self):
        """Test parsing string value."""
        assert parse_config_value("hello", "string") == "hello"
        assert parse_config_value("hello") == "hello"  # auto type

    def test_parse_config_value_int(self):
        """Test parsing int value."""
        assert parse_config_value("123", "int") == 123
        assert parse_config_value("123") == 123  # auto type

    def test_parse_config_value_float(self):
        """Test parsing float value."""
        assert parse_config_value("123.45", "float") == 123.45
        assert parse_config_value("123.45") == 123.45  # auto type

    def test_parse_config_value_bool_true(self):
        """Test parsing boolean true values."""
        assert parse_config_value("true", "bool") is True
        assert parse_config_value("True", "bool") is True
        assert parse_config_value("1", "bool") is True
        assert parse_config_value("yes", "bool") is True

    def test_parse_config_value_bool_false(self):
        """Test parsing boolean false values."""
        assert parse_config_value("false", "bool") is False
        assert parse_config_value("False", "bool") is False
        assert parse_config_value("0", "bool") is False
        assert parse_config_value("no", "bool") is False

    def test_parse_config_value_auto_type(self):
        """Test auto type detection."""
        assert parse_config_value("hello") == "hello"
        assert parse_config_value("123") == 123
        assert parse_config_value("123.45") == 123.45
        assert parse_config_value("true") is True
        assert parse_config_value("false") is False

    def test_parse_config_value_invalid_type(self):
        """Test parsing with invalid type."""
        with pytest.raises(ValueError):
            parse_config_value("hello", "invalid_type")


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        config = load_config("nonexistent.toml")
        default_config = get_default_config()
        assert config == default_config

    def test_load_config_json_file(self):
        """Test loading JSON config file."""
        config_data = {
            "min_coverage": 90,
            "skip_tests": True,
            "gates": {
                "fail_on_bandit": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = load_config(temp_file)
            assert config["min_coverage"] == 90
            assert config["skip_tests"] is True
            assert config["gates"]["fail_on_bandit"] is False
        finally:
            os.unlink(temp_file)

    def test_load_config_toml_file(self):
        """Test loading TOML config file."""
        toml_content = """
min_coverage = 90
skip_tests = true

[gates]
fail_on_bandit = false
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            temp_file = f.name
        
        try:
            config = load_config(temp_file)
            assert config["min_coverage"] == 90
            assert config["skip_tests"] is True
            assert config["gates"]["fail_on_bandit"] is False
        finally:
            os.unlink(temp_file)

    def test_load_config_parse_error(self):
        """Test loading config with parse error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            config = load_config(temp_file)
            default_config = get_default_config()
            assert config == default_config
        finally:
            os.unlink(temp_file)


class TestGates:
    """Test Gates class."""

    def test_gates_init_default(self):
        """Test Gates initialization with defaults."""
        gates = Gates()
        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_init_custom(self):
        """Test Gates initialization with custom values."""
        gates = Gates(
            min_coverage=90,
            fail_on_bandit=False,
            fail_on_lint=False,
            fail_on_mypy=False
        )
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is False


class TestConfig:
    """Test Config class."""

    def test_config_init_default(self):
        """Test Config initialization with defaults."""
        config = Config()
        assert config.min_coverage == 80
        assert config.skip_tests is False
        assert config.report_format == "sarif"
        assert config.report_path == "ai-guard.sarif"
        assert config.enhanced_testgen is False
        assert config.llm_provider == "openai"
        assert config.llm_api_key == ""
        assert config.llm_model == "gpt-4"
        assert config.fail_on_bandit is True
        assert config.fail_on_lint is True
        assert config.fail_on_mypy is True

    def test_config_init_with_kwargs(self):
        """Test Config initialization with kwargs."""
        config = Config(min_coverage=90, skip_tests=True)
        assert config.min_coverage == 90
        assert config.skip_tests is True

    def test_config_get(self):
        """Test Config get method."""
        config = Config()
        assert config.get("min_coverage") == 80
        assert config.get("nonexistent_key") is None
        assert config.get("nonexistent_key", "default") == "default"

    def test_config_set(self):
        """Test Config set method."""
        config = Config()
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"

    def test_config_reload(self):
        """Test Config reload method."""
        config = Config()
        original_coverage = config.min_coverage
        
        # Change the config file
        config_data = {"min_coverage": 95}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config.config_path = temp_file
            config.reload()
            assert config.min_coverage == 95
        finally:
            os.unlink(temp_file)

    def test_config_from_dict(self):
        """Test Config creation from dictionary."""
        config_dict = {
            "min_coverage": 90,
            "skip_tests": True,
            "gates": {
                "fail_on_bandit": False
            }
        }
        config = Config.from_dict(config_dict)
        assert config.min_coverage == 90
        assert config.skip_tests is True
        # Note: fail_on_bandit is read from gates section, but Config class reads from top-level
        assert config.fail_on_bandit is True  # Default value since it's not at top level

    def test_config_to_dict(self):
        """Test Config conversion to dictionary."""
        config = Config(min_coverage=90)
        config_dict = config.to_dict()
        assert config_dict["min_coverage"] == 90
        assert isinstance(config_dict, dict)

    def test_config_validate(self):
        """Test Config validation."""
        config = Config()
        assert config.validate() is True
        
        # Test with invalid config
        config.set("min_coverage", -1)
        assert config.validate() is False