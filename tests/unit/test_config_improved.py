"""Comprehensive tests for config.py to achieve maximum coverage."""

import pytest
from unittest.mock import patch, mock_open

from ai_guard.config import (
    get_default_config,
    validate_config,
    load_config,
    merge_configs,
    parse_config_value,
    Gates,
    Config,
)


class TestGetDefaultConfig:
    """Test get_default_config function."""

    def test_get_default_config_returns_dict(self):
        """Test that get_default_config returns a dictionary."""
        config = get_default_config()
        assert isinstance(config, dict)

    def test_get_default_config_contains_expected_keys(self):
        """Test that default config contains expected keys."""
        config = get_default_config()
        expected_keys = {
            "min_coverage",
            "skip_tests",
            "report_format",
            "report_path",
            "enhanced_testgen",
            "llm_provider",
            "llm_api_key",
            "llm_model",
            "fail_on_bandit",
            "fail_on_lint",
            "fail_on_mypy",
        }
        assert set(config.keys()) == expected_keys

    def test_get_default_config_values(self):
        """Test that default config has correct default values."""
        config = get_default_config()
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"
        assert config["report_path"] == "ai-guard.sarif"
        assert config["enhanced_testgen"] is False
        assert config["llm_provider"] == "openai"
        assert config["llm_api_key"] == ""
        assert config["llm_model"] == "gpt-4"
        assert config["fail_on_bandit"] is True
        assert config["fail_on_lint"] is True
        assert config["fail_on_mypy"] is True


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_valid(self):
        """Test validation with valid config."""
        config = {"min_coverage": 85}
        assert validate_config(config) is True

    def test_validate_config_missing_required_field(self):
        """Test validation with missing required field."""
        config = {"skip_tests": True}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_type(self):
        """Test validation with invalid min_coverage type."""
        config = {"min_coverage": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_negative(self):
        """Test validation with negative min_coverage."""
        config = {"min_coverage": -1}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_over_100(self):
        """Test validation with min_coverage over 100."""
        config = {"min_coverage": 101}
        assert validate_config(config) is False

    def test_validate_config_invalid_report_format(self):
        """Test validation with invalid report_format."""
        config = {"min_coverage": 80, "report_format": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_invalid_llm_provider(self):
        """Test validation with invalid llm_provider."""
        config = {"min_coverage": 80, "llm_provider": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_invalid_boolean_field(self):
        """Test validation with invalid boolean field."""
        config = {"min_coverage": 80, "skip_tests": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_valid_with_all_fields(self):
        """Test validation with all valid fields."""
        config = {
            "min_coverage": 85,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "custom.json",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3",
            "fail_on_bandit": False,
            "fail_on_lint": False,
            "fail_on_mypy": False,
        }
        assert validate_config(config) is True


class TestParseConfigValue:
    """Test parse_config_value function."""

    def test_parse_config_value_auto_bool_true(self):
        """Test auto-parsing boolean true."""
        assert parse_config_value("true") is True
        assert parse_config_value("True") is True
        assert parse_config_value("TRUE") is True

    def test_parse_config_value_auto_bool_false(self):
        """Test auto-parsing boolean false."""
        assert parse_config_value("false") is False
        assert parse_config_value("False") is False
        assert parse_config_value("FALSE") is False

    def test_parse_config_value_auto_int(self):
        """Test auto-parsing integer."""
        assert parse_config_value("42") == 42
        assert parse_config_value("-10") == -10
        assert parse_config_value("0") == 0

    def test_parse_config_value_auto_float(self):
        """Test auto-parsing float."""
        assert parse_config_value("3.14") == 3.14
        assert parse_config_value("-2.5") == -2.5
        assert parse_config_value("0.0") == 0.0

    def test_parse_config_value_auto_string(self):
        """Test auto-parsing string."""
        assert parse_config_value("hello") == "hello"
        assert parse_config_value("test-value") == "test-value"

    def test_parse_config_value_string_type(self):
        """Test explicit string type."""
        assert parse_config_value("42", "string") == "42"
        assert parse_config_value("true", "string") == "true"

    def test_parse_config_value_int_type(self):
        """Test explicit int type."""
        assert parse_config_value("42", "int") == 42
        assert parse_config_value("", "int") == 0

    def test_parse_config_value_float_type(self):
        """Test explicit float type."""
        assert parse_config_value("3.14", "float") == 3.14
        assert parse_config_value("", "float") == 0.0

    def test_parse_config_value_bool_type(self):
        """Test explicit bool type."""
        assert parse_config_value("true", "bool") is True
        assert parse_config_value("false", "bool") is False
        assert parse_config_value("1", "bool") is True
        assert parse_config_value("0", "bool") is False
        assert parse_config_value("yes", "bool") is True
        assert parse_config_value("no", "bool") is False

    def test_parse_config_value_bool_type_invalid(self):
        """Test explicit bool type with invalid value."""
        with pytest.raises(ValueError):
            parse_config_value("invalid", "bool")

    def test_parse_config_value_unknown_type(self):
        """Test unknown type raises ValueError."""
        with pytest.raises(ValueError):
            parse_config_value("test", "unknown")

    def test_parse_config_value_none(self):
        """Test parsing None value."""
        assert parse_config_value(None) is None


class TestMergeConfigs:
    """Test merge_configs function."""

    def test_merge_configs_none_override(self):
        """Test merging with None override."""
        base = {"min_coverage": 80, "skip_tests": False}
        result = merge_configs(base, None)
        assert result == base

    def test_merge_configs_partial_override(self):
        """Test merging with partial override."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {"min_coverage": 90}
        result = merge_configs(base, override)
        expected = {"min_coverage": 90, "skip_tests": False}
        assert result == expected

    def test_merge_configs_complete_override(self):
        """Test merging with complete override."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "custom.json",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3",
        }
        result = merge_configs(base, override)
        assert result == override

    def test_merge_configs_extra_fields(self):
        """Test merging with extra fields in override."""
        base = {"min_coverage": 80}
        override = {"min_coverage": 90, "extra_field": "value"}
        result = merge_configs(base, override)
        expected = {"min_coverage": 90, "extra_field": "value"}
        assert result == expected


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            config = load_config("nonexistent.toml")
            assert config == get_default_config()

    def test_load_config_toml_format(self):
        """Test loading TOML config file."""
        toml_content = """
[gates]
min_coverage = 85
"""
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("ai_guard.config.tomli.load") as mock_load:
                mock_load.return_value = {"gates": {"min_coverage": 85}}
                config = load_config("test.toml")
                assert config["min_coverage"] == 85

    def test_load_config_json_format(self):
        """Test loading JSON config file."""
        json_content = '{"min_coverage": 90}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            config = load_config("test.json")
            assert config["min_coverage"] == 90

    def test_load_config_parse_error(self):
        """Test loading config with parse error."""
        with patch("builtins.open", mock_open(read_data="invalid content")):
            with patch("ai_guard.config.tomli.load", side_effect=Exception):
                config = load_config("test.toml")
                assert config == get_default_config()

    def test_load_config_flat_structure(self):
        """Test loading config with flat structure."""
        json_content = '{"min_coverage": 75, "skip_tests": true}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            config = load_config("test.json")
            assert config["min_coverage"] == 75
            assert config["skip_tests"] is True

    def test_load_config_preserves_extra_fields(self):
        """Test that extra fields are preserved."""
        json_content = '{"min_coverage": 80, "custom_field": "value"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            config = load_config("test.json")
            assert config["min_coverage"] == 80
            assert config["custom_field"] == "value"


class TestGates:
    """Test Gates class for backward compatibility."""

    def test_gates_init_default(self):
        """Test Gates initialization with default values."""
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
            fail_on_mypy=False,
        )
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is False


class TestConfig:
    """Test Config class."""

    def test_config_init_default_path(self):
        """Test Config initialization with default path."""
        with patch("ai_guard.config.load_config") as mock_load:
            mock_load.return_value = {"min_coverage": 80}
            config = Config()
            assert config.config_path == "ai-guard.toml"
            mock_load.assert_called_once_with("ai-guard.toml")

    def test_config_init_custom_path(self):
        """Test Config initialization with custom path."""
        with patch("ai_guard.config.load_config") as mock_load:
            mock_load.return_value = {"min_coverage": 85}
            config = Config("custom.toml")
            assert config.config_path == "custom.toml"
            mock_load.assert_called_once_with("custom.toml")

    def test_config_properties(self):
        """Test Config class properties."""
        test_config = {
            "min_coverage": 85,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "custom.json",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3",
            "fail_on_bandit": False,
            "fail_on_lint": False,
            "fail_on_mypy": False,
        }
        with patch("ai_guard.config.load_config", return_value=test_config):
            config = Config()
            assert config.min_coverage == 85
            assert config.skip_tests is True
            assert config.report_format == "json"
            assert config.report_path == "custom.json"
            assert config.enhanced_testgen is True
            assert config.llm_provider == "anthropic"
            assert config.llm_api_key == "test-key"
            assert config.llm_model == "claude-3"
            assert config.fail_on_bandit is False
            assert config.fail_on_lint is False
            assert config.fail_on_mypy is False

    def test_config_get_method(self):
        """Test Config get method."""
        test_config = {"min_coverage": 80, "custom_field": "value"}
        with patch("ai_guard.config.load_config", return_value=test_config):
            config = Config()
            assert config.get("min_coverage") == 80
            assert config.get("custom_field") == "value"
            assert config.get("nonexistent") is None
            assert config.get("nonexistent", "default") == "default"

    def test_config_set_method(self):
        """Test Config set method."""
        with patch("ai_guard.config.load_config", return_value={}):
            config = Config()
            config.set("test_key", "test_value")
            assert config.get("test_key") == "test_value"

    def test_config_reload_method(self):
        """Test Config reload method."""
        with patch("ai_guard.config.load_config") as mock_load:
            mock_load.return_value = {"min_coverage": 80}
            config = Config()
            mock_load.reset_mock()
            config.reload()
            mock_load.assert_called_once_with("ai-guard.toml")
