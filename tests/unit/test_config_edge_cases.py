"""Edge case tests for config module to improve coverage to 90%+."""

import pytest
from unittest.mock import patch, mock_open

from ai_guard.config import (
    load_config,
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
)


class TestConfigEdgeCases:
    """Test edge cases and error handling in config module."""

    def test_get_default_config(self):
        """Test default configuration values."""
        config = get_default_config()

        assert "min_coverage" in config
        assert "skip_tests" in config
        assert "report_format" in config
        assert "report_path" in config
        assert "enhanced_testgen" in config
        assert "llm_provider" in config
        assert "llm_api_key" in config
        assert "llm_model" in config

    def test_get_default_config_values(self):
        """Test specific default configuration values."""
        config = get_default_config()

        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"
        assert config["report_path"] == "ai-guard.sarif"
        assert config["enhanced_testgen"] is False
        assert config["llm_provider"] == "openai"
        assert config["llm_api_key"] == ""
        assert config["llm_model"] == "gpt-4"

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = {
            "min_coverage": 85,
            "skip_tests": False,
            "report_format": "json",
            "report_path": "report.json",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3-sonnet-20240229",
        }

        result = validate_config(config)

        assert result is True

    def test_validate_config_invalid_coverage(self):
        """Test validation with invalid coverage value."""
        config = get_default_config()
        config["min_coverage"] = -10

        result = validate_config(config)

        assert result is False

    def test_validate_config_invalid_coverage_high(self):
        """Test validation with coverage value too high."""
        config = get_default_config()
        config["min_coverage"] = 150

        result = validate_config(config)

        assert result is False

    def test_validate_config_invalid_report_format(self):
        """Test validation with invalid report format."""
        config = get_default_config()
        config["report_format"] = "invalid"

        result = validate_config(config)

        assert result is False

    def test_validate_config_valid_report_formats(self):
        """Test validation with all valid report formats."""
        valid_formats = ["sarif", "json", "html"]

        for format_type in valid_formats:
            config = get_default_config()
            config["report_format"] = format_type

            result = validate_config(config)
            assert result is True, f"Format {format_type} should be valid"

    def test_validate_config_invalid_llm_provider(self):
        """Test validation with invalid LLM provider."""
        config = get_default_config()
        config["llm_provider"] = "invalid"

        result = validate_config(config)

        assert result is False

    def test_validate_config_valid_llm_providers(self):
        """Test validation with all valid LLM providers."""
        valid_providers = ["openai", "anthropic"]

        for provider in valid_providers:
            config = get_default_config()
            config["llm_provider"] = provider

            result = validate_config(config)
            assert result is True, f"Provider {provider} should be valid"

    def test_validate_config_missing_required_fields(self):
        """Test validation with missing required fields."""
        config = {}

        result = validate_config(config)

        assert result is False

    def test_validate_config_extra_fields(self):
        """Test validation with extra fields (should be allowed)."""
        config = get_default_config()
        config["extra_field"] = "extra_value"
        config["another_field"] = 123

        result = validate_config(config)

        assert result is True

    def test_merge_configs_basic(self):
        """Test basic configuration merging."""
        base_config = get_default_config()
        override_config = {"min_coverage": 90, "report_format": "html"}

        merged = merge_configs(base_config, override_config)

        assert merged["min_coverage"] == 90
        assert merged["report_format"] == "html"
        assert merged["skip_tests"] is False  # Should remain from base
        assert merged["llm_provider"] == "openai"  # Should remain from base

    def test_merge_configs_empty_override(self):
        """Test configuration merging with empty override."""
        base_config = get_default_config()
        override_config = {}

        merged = merge_configs(base_config, override_config)

        assert merged == base_config

    def test_merge_configs_none_override(self):
        """Test configuration merging with None override."""
        base_config = get_default_config()

        merged = merge_configs(base_config, None)

        assert merged == base_config

    def test_merge_configs_all_overrides(self):
        """Test configuration merging with all fields overridden."""
        base_config = get_default_config()
        override_config = {
            "min_coverage": 95,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "custom.json",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "override-key",
            "llm_model": "claude-3-sonnet-20240229",
        }

        merged = merge_configs(base_config, override_config)

        assert merged == override_config

    def test_merge_configs_nested_override(self):
        """Test configuration merging with nested override."""
        base_config = get_default_config()
        override_config = {
            "min_coverage": 85,
            "extra_nested": {"level1": "value1", "level2": {"deep": "value2"}},
        }

        merged = merge_configs(base_config, override_config)

        assert merged["min_coverage"] == 85
        assert "extra_nested" in merged
        assert merged["extra_nested"]["level1"] == "value1"
        assert merged["extra_nested"]["level2"]["deep"] == "value2"

    def test_parse_config_value_string(self):
        """Test parsing string configuration values."""
        assert parse_config_value("test", "string") == "test"
        assert parse_config_value("123", "string") == "123"
        assert parse_config_value("", "string") == ""

    def test_parse_config_value_integer(self):
        """Test parsing integer configuration values."""
        assert parse_config_value("123", "int") == 123
        assert parse_config_value("0", "int") == 0
        assert parse_config_value("-42", "int") == -42

    def test_parse_config_value_integer_invalid(self):
        """Test parsing invalid integer configuration values."""
        with pytest.raises(ValueError):
            parse_config_value("not_a_number", "int")

        with pytest.raises(ValueError):
            parse_config_value("12.34", "int")

    def test_parse_config_value_float(self):
        """Test parsing float configuration values."""
        assert parse_config_value("123.45", "float") == 123.45
        assert parse_config_value("0.0", "float") == 0.0
        assert parse_config_value("-42.1", "float") == -42.1

    def test_parse_config_value_float_invalid(self):
        """Test parsing invalid float configuration values."""
        with pytest.raises(ValueError):
            parse_config_value("not_a_number", "float")

    def test_parse_config_value_boolean(self):
        """Test parsing boolean configuration values."""
        assert parse_config_value("true", "bool") is True
        assert parse_config_value("True", "bool") is True
        assert parse_config_value("TRUE", "bool") is True
        assert parse_config_value("false", "bool") is False
        assert parse_config_value("False", "bool") is False
        assert parse_config_value("FALSE", "bool") is False

    def test_parse_config_value_boolean_invalid(self):
        """Test parsing invalid boolean configuration values."""
        with pytest.raises(ValueError):
            parse_config_value("yes", "bool")

        with pytest.raises(ValueError):
            parse_config_value("no", "bool")

    def test_parse_config_value_unknown_type(self):
        """Test parsing configuration values with unknown type."""
        with pytest.raises(ValueError):
            parse_config_value("test", "unknown")

    def test_parse_config_value_none(self):
        """Test parsing None configuration values."""
        assert parse_config_value(None, "string") is None
        assert parse_config_value(None, "int") is None
        assert parse_config_value(None, "bool") is None

    @patch("builtins.open", new_callable=mock_open, read_data='{"min_coverage": 90}')
    def test_load_config_from_file_success(self, mock_file):
        """Test successful configuration loading from file."""
        config = load_config("config.json")

        assert config["min_coverage"] == 90
        mock_file.assert_called_once_with("config.json", "r", encoding="utf-8")

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_load_config_file_not_found(self, mock_file):
        """Test configuration loading when file not found."""
        config = load_config("nonexistent.json")

        assert config == get_default_config()

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_load_config_permission_error(self, mock_file):
        """Test configuration loading with permission error."""
        config = load_config("/root/config.json")

        assert config == get_default_config()

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_load_config_invalid_json(self, mock_file):
        """Test configuration loading with invalid JSON."""
        config = load_config("invalid.json")

        assert config == get_default_config()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"min_coverage": "not_a_number"}',
    )
    def test_load_config_invalid_values(self, mock_file):
        """Test configuration loading with invalid values."""
        config = load_config("invalid_values.json")

        assert config == get_default_config()

    def test_load_config_none_path(self):
        """Test configuration loading with None path."""
        config = load_config(None)

        assert config == get_default_config()

    def test_load_config_empty_path(self):
        """Test configuration loading with empty path."""
        config = load_config("")

        assert config == get_default_config()

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    def test_load_config_empty_json(self, mock_file):
        """Test configuration loading with empty JSON."""
        config = load_config("empty.json")

        assert config == get_default_config()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"min_coverage": 85, "extra": "value"}',
    )
    def test_load_config_with_extra_fields(self, mock_file):
        """Test configuration loading with extra fields."""
        config = load_config("extra_fields.json")

        assert config["min_coverage"] == 85
        assert config["extra"] == "value"
        assert "skip_tests" in config  # Should have default values

    def test_validate_config_edge_cases(self):
        """Test configuration validation with edge case values."""
        config = get_default_config()

        # Test boundary values
        config["min_coverage"] = 0
        assert validate_config(config) is True

        config["min_coverage"] = 100
        assert validate_config(config) is True

        config["min_coverage"] = 50
        assert validate_config(config) is True

    def test_validate_config_type_validation(self):
        """Test configuration validation with type checking."""
        config = get_default_config()

        # Test wrong types
        config["min_coverage"] = "not_a_number"
        assert validate_config(config) is False

        config = get_default_config()
        config["skip_tests"] = "not_a_bool"
        assert validate_config(config) is False

        config = get_default_config()
        config["report_format"] = 123
        assert validate_config(config) is False

    def test_merge_configs_deep_copy(self):
        """Test that configuration merging creates deep copies."""
        base_config = get_default_config()
        base_config["nested"] = {"key": "value"}

        override_config = {"nested": {"key": "new_value"}}

        merged = merge_configs(base_config, override_config)

        # Modify the original to ensure it doesn't affect merged
        base_config["nested"]["key"] = "modified"

        assert merged["nested"]["key"] == "new_value"

    def test_parse_config_value_edge_cases(self):
        """Test configuration value parsing with edge cases."""
        # Test empty strings
        assert parse_config_value("", "string") == ""
        assert parse_config_value("", "int") == 0

        # Test whitespace
        assert parse_config_value("  test  ", "string") == "  test  "
        assert parse_config_value("  123  ", "int") == 123

        # Test zero values
        assert parse_config_value("0", "int") == 0
        assert parse_config_value("0.0", "float") == 0.0
        assert parse_config_value("false", "bool") is False
