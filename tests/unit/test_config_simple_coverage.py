"""Simple tests for config.py to achieve maximum coverage."""

import pytest
import os
import tempfile
from pathlib import Path

from ai_guard.config import (
    get_default_config,
    validate_config,
    load_config,
    merge_configs,
    parse_config_value,
    Gates,
    Config,
)


class TestDefaultConfig:
    """Test default configuration functions."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()

        assert isinstance(config, dict)
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


class TestConfigValidation:
    """Test configuration validation functions."""

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        config = {"min_coverage": 85, "report_format": "json", "skip_tests": True}

        assert validate_config(config) is True

    def test_validate_config_missing_required_field(self):
        """Test validation with missing required field."""
        config = {"report_format": "json", "skip_tests": True}

        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_type(self):
        """Test validation with invalid min_coverage type."""
        config = {"min_coverage": "85", "report_format": "json"}  # Should be int

        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_negative(self):
        """Test validation with negative min_coverage."""
        config = {"min_coverage": -10, "report_format": "json"}

        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_over_100(self):
        """Test validation with min_coverage over 100."""
        config = {"min_coverage": 150, "report_format": "json"}

        assert validate_config(config) is False

    def test_validate_config_invalid_report_format(self):
        """Test validation with invalid report_format."""
        config = {"min_coverage": 80, "report_format": "invalid_format"}

        assert validate_config(config) is False

    def test_validate_config_valid_report_formats(self):
        """Test validation with all valid report formats."""
        valid_formats = ["sarif", "json", "html"]

        for format_type in valid_formats:
            config = {"min_coverage": 80, "report_format": format_type}
            assert validate_config(config) is True

    def test_validate_config_invalid_llm_provider(self):
        """Test validation with invalid llm_provider."""
        config = {"min_coverage": 80, "llm_provider": "invalid_provider"}

        assert validate_config(config) is False

    def test_validate_config_valid_llm_providers(self):
        """Test validation with all valid llm_providers."""
        valid_providers = ["openai", "anthropic", "azure", "local"]

        for provider in valid_providers:
            config = {"min_coverage": 80, "llm_provider": provider}
            assert validate_config(config) is True

    def test_validate_config_invalid_boolean_fields(self):
        """Test validation with invalid boolean fields."""
        boolean_fields = [
            "skip_tests",
            "enhanced_testgen",
            "fail_on_bandit",
            "fail_on_lint",
            "fail_on_mypy",
        ]

        for field in boolean_fields:
            config = {"min_coverage": 80, field: "not_a_boolean"}
            assert validate_config(config) is False

    def test_validate_config_valid_boolean_fields(self):
        """Test validation with valid boolean fields."""
        boolean_fields = [
            "skip_tests",
            "enhanced_testgen",
            "fail_on_bandit",
            "fail_on_lint",
            "fail_on_mypy",
        ]

        for field in boolean_fields:
            for value in [True, False]:
                config = {"min_coverage": 80, field: value}
                assert validate_config(config) is True

    def test_validate_config_empty_config(self):
        """Test validation with empty configuration."""
        config = {}
        assert validate_config(config) is False

    def test_validate_config_none(self):
        """Test validation with None configuration."""
        assert validate_config(None) is False


class TestConfigLoading:
    """Test configuration loading functions."""

    def test_load_config_toml(self):
        """Test loading TOML configuration."""
        toml_content = """
min_coverage = 90
skip_tests = true
report_format = "json"
enhanced_testgen = true
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()

            try:
                config = load_config(f.name)
                assert config["min_coverage"] == 90
                assert config["skip_tests"] is True
                assert config["report_format"] == "json"
                assert config["enhanced_testgen"] is True
            finally:
                if Path(f.name).exists():
                    os.unlink(f.name)

    def test_load_config_json(self):
        """Test loading JSON configuration."""
        json_content = """
{
    "min_coverage": 85,
    "skip_tests": false,
    "report_format": "html",
    "enhanced_testgen": false
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            f.flush()

            try:
                config = load_config(f.name)
                assert config["min_coverage"] == 85
                assert config["skip_tests"] is False
                assert config["report_format"] == "html"
                assert config["enhanced_testgen"] is False
            finally:
                if Path(f.name).exists():
                    os.unlink(f.name)

    def test_load_config_file_not_found(self):
        """Test loading configuration from non-existent file."""
        config = load_config("nonexistent.toml")
        assert config == get_default_config()

    def test_load_config_invalid_toml(self):
        """Test loading invalid TOML configuration."""
        invalid_toml = """
min_coverage = 90
skip_tests = true
invalid_syntax = 
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(invalid_toml)
            f.flush()

            try:
                config = load_config(f.name)
                assert config == get_default_config()
            finally:
                if Path(f.name).exists():
                    os.unlink(f.name)

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON configuration."""
        invalid_json = """
{
    "min_coverage": 90,
    "skip_tests": true,
    "invalid_syntax": 
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(invalid_json)
            f.flush()

            try:
                config = load_config(f.name)
                assert config == get_default_config()
            finally:
                if Path(f.name).exists():
                    os.unlink(f.name)

    def test_load_config_unsupported_format(self):
        """Test loading configuration with unsupported format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("min_coverage: 90")
            f.flush()

            try:
                config = load_config(f.name)
                assert config == get_default_config()
            finally:
                if Path(f.name).exists():
                    os.unlink(f.name)


class TestConfigMerging:
    """Test configuration merging functions."""

    def test_merge_configs_basic(self):
        """Test basic configuration merging."""
        base_config = {
            "min_coverage": 80,
            "skip_tests": False,
            "report_format": "sarif",
        }

        override_config = {"min_coverage": 90, "skip_tests": True}

        merged = merge_configs(base_config, override_config)

        assert merged["min_coverage"] == 90
        assert merged["skip_tests"] is True
        assert merged["report_format"] == "sarif"

    def test_merge_configs_empty_override(self):
        """Test merging with empty override configuration."""
        base_config = {"min_coverage": 80, "skip_tests": False}

        override_config = {}

        merged = merge_configs(base_config, override_config)

        assert merged == base_config

    def test_merge_configs_empty_base(self):
        """Test merging with empty base configuration."""
        base_config = {}

        override_config = {"min_coverage": 90, "skip_tests": True}

        merged = merge_configs(base_config, override_config)

        assert merged == override_config

    def test_merge_configs_both_empty(self):
        """Test merging with both configurations empty."""
        merged = merge_configs({}, {})
        assert merged == {}

    def test_merge_configs_nested_dicts(self):
        """Test merging with nested dictionaries."""
        base_config = {
            "llm": {"provider": "openai", "model": "gpt-4"},
            "min_coverage": 80,
        }

        override_config = {"llm": {"model": "gpt-3.5-turbo"}, "skip_tests": True}

        merged = merge_configs(base_config, override_config)

        assert merged["llm"]["provider"] == "openai"
        assert merged["llm"]["model"] == "gpt-3.5-turbo"
        assert merged["min_coverage"] == 80
        assert merged["skip_tests"] is True


class TestConfigValueParsing:
    """Test configuration value parsing functions."""

    def test_parse_config_value_string(self):
        """Test parsing string values."""
        assert parse_config_value("test", "string") == "test"
        assert parse_config_value("123", "string") == "123"

    def test_parse_config_value_integer(self):
        """Test parsing integer values."""
        assert parse_config_value("123", "int") == 123
        assert parse_config_value("0", "int") == 0
        assert parse_config_value("-45", "int") == -45

    def test_parse_config_value_float(self):
        """Test parsing float values."""
        assert parse_config_value("123.45", "float") == 123.45
        assert parse_config_value("0.0", "float") == 0.0
        assert parse_config_value("-45.67", "float") == -45.67

    def test_parse_config_value_boolean(self):
        """Test parsing boolean values."""
        assert parse_config_value("true", "bool") is True
        assert parse_config_value("false", "bool") is False
        assert parse_config_value("True", "bool") is True
        assert parse_config_value("False", "bool") is False
        assert parse_config_value("1", "bool") is True
        assert parse_config_value("0", "bool") is False

    def test_parse_config_value_invalid_type(self):
        """Test parsing with invalid type."""
        assert parse_config_value("test", "invalid_type") == "test"

    def test_parse_config_value_invalid_conversion(self):
        """Test parsing with invalid conversion."""
        assert parse_config_value("not_a_number", "int") == "not_a_number"
        assert parse_config_value("not_a_float", "float") == "not_a_float"
        assert parse_config_value("not_a_bool", "bool") == "not_a_bool"


class TestGatesClass:
    """Test Gates dataclass."""

    def test_gates_init(self):
        """Test Gates initialization."""
        gates = Gates()
        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_custom_values(self):
        """Test Gates with custom values."""
        gates = Gates(
            min_coverage=90, fail_on_bandit=False, fail_on_lint=False, fail_on_mypy=True
        )
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is True


class TestConfigClass:
    """Test Config class."""

    def test_config_init(self):
        """Test Config initialization."""
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

    def test_config_custom_values(self):
        """Test Config with custom values using set method."""
        config = Config()
        config.set("min_coverage", 90)
        config.set("skip_tests", True)
        config.set("report_format", "json")
        config.set("enhanced_testgen", True)

        assert config.get("min_coverage") == 90
        assert config.get("skip_tests") is True
        assert config.get("report_format") == "json"
        assert config.get("enhanced_testgen") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
