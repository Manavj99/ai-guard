"""Tests for config module."""

import pytest  # noqa: F401
from unittest.mock import patch, mock_open  # noqa: F401
from ai_guard.config import (
    load_config,
    Gates,
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
)


class TestConfig:
    """Test configuration functionality."""

    def test_gates_default_values(self):
        """Test Gates dataclass default values."""
        gates = Gates()

        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_custom_values(self):
        """Test Gates dataclass with custom values."""
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

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        result = load_config("nonexistent.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 80  # Default value

    def test_load_config_valid_toml(self):
        """Test loading config from valid TOML file."""
        toml_content = """
        [gates]
        min_coverage = 95
        """

        with patch("builtins.open", mock_open(read_data=toml_content.encode())):
            with patch("tomli.load") as mock_tomli:
                mock_tomli.return_value = {"gates": {"min_coverage": 95}}
                result = load_config("ai-guard.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 95

    def test_load_config_missing_gates_section(self):
        """Test loading config when gates section is missing."""
        toml_content = """
        [other_section]
        some_value = "test"
        """

        with patch("builtins.open", mock_open(read_data=toml_content.encode())):
            with patch("tomli.load") as mock_tomli:
                mock_tomli.return_value = {"other_section": {"some_value": "test"}}
                result = load_config("ai-guard.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 80  # Default value

    def test_load_config_missing_min_coverage(self):
        """Test loading config when min_coverage is missing."""
        toml_content = """
        [gates]
        other_setting = "value"
        """

        with patch("builtins.open", mock_open(read_data=toml_content.encode())):
            with patch("tomli.load") as mock_tomli:
                mock_tomli.return_value = {"gates": {"other_setting": "value"}}
                result = load_config("ai-guard.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 80  # Default value

    def test_load_config_parse_error(self):
        """Test loading config when TOML parsing fails."""
        with patch("builtins.open", mock_open(read_data=b"invalid toml")):
            with patch("tomli.load", side_effect=Exception("Parse error")):
                result = load_config("ai-guard.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 80  # Default value

    def test_load_config_custom_path(self):
        """Test loading config from custom path."""
        toml_content = """
        [gates]
        min_coverage = 85
        """

        with patch("builtins.open", mock_open(read_data=toml_content.encode())):
            with patch("tomli.load") as mock_tomli:
                mock_tomli.return_value = {"gates": {"min_coverage": 85}}
                result = load_config("custom/path/config.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 85

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()

        assert isinstance(config, dict)
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"
        assert config["enhanced_testgen"] is False
        assert config["fail_on_bandit"] is True
        assert config["fail_on_lint"] is True
        assert config["fail_on_mypy"] is True

    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = {"min_coverage": 85}
        assert validate_config(config) is True

        config = {
            "min_coverage": 90,
            "report_format": "json",
            "llm_provider": "openai",
            "skip_tests": True,
        }
        assert validate_config(config) is True

    def test_validate_config_invalid(self):
        """Test validating invalid configuration."""
        # Missing required field
        config = {"other_field": "value"}
        assert validate_config(config) is False

        # Invalid min_coverage
        config = {"min_coverage": -1}
        assert validate_config(config) is False

        config = {"min_coverage": 101}
        assert validate_config(config) is False

        config = {"min_coverage": "invalid"}
        assert validate_config(config) is False

        # Invalid report_format
        config = {"min_coverage": 80, "report_format": "invalid"}
        assert validate_config(config) is False

        # Invalid llm_provider
        config = {"min_coverage": 80, "llm_provider": "invalid"}
        assert validate_config(config) is False

        # Invalid boolean field
        config = {"min_coverage": 80, "skip_tests": "invalid"}
        assert validate_config(config) is False

    def test_merge_configs(self):
        """Test merging configurations."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {"min_coverage": 90}

        result = merge_configs(base, override)
        assert result["min_coverage"] == 90
        assert result["skip_tests"] is False

        # Test with None override
        result = merge_configs(base, None)
        assert result == base

        # Test with all main fields overridden
        base = {"min_coverage": 80, "skip_tests": False, "report_format": "sarif"}
        override = {
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "json",
            "enhanced_testgen": True,
            "llm_provider": "openai",
            "llm_api_key": "test",
            "llm_model": "gpt-4",
        }
        result = merge_configs(base, override)
        assert result == override

    def test_parse_config_value_auto(self):
        """Test parsing config values with auto type detection."""
        # Boolean values
        assert parse_config_value("true") is True
        assert parse_config_value("false") is False
        assert parse_config_value("TRUE") is True
        assert parse_config_value("FALSE") is False

        # Integer values
        assert parse_config_value("123") == 123
        assert parse_config_value("-456") == -456

        # Float values
        assert parse_config_value("123.45") == 123.45
        assert parse_config_value("-67.89") == -67.89

        # String values
        assert parse_config_value("hello") == "hello"
        assert parse_config_value("123abc") == "123abc"

        # None value
        assert parse_config_value(None) is None

    def test_parse_config_value_specific_types(self):
        """Test parsing config values with specific types."""
        # String type
        assert parse_config_value("123", "string") == "123"

        # Integer type
        assert parse_config_value("123", "int") == 123
        assert parse_config_value("", "int") == 0

        # Float type
        assert parse_config_value("123.45", "float") == 123.45
        assert parse_config_value("", "float") == 0.0

        # Boolean type
        assert parse_config_value("true", "bool") is True
        assert parse_config_value("false", "bool") is False
        assert parse_config_value("1", "bool") is True
        assert parse_config_value("0", "bool") is False
        assert parse_config_value("yes", "bool") is True
        assert parse_config_value("no", "bool") is False

        # Invalid boolean
        with pytest.raises(ValueError):
            parse_config_value("invalid", "bool")

        # Unknown type
        with pytest.raises(ValueError):
            parse_config_value("value", "unknown")

    def test_load_config_json_format(self):
        """Test loading config from JSON file."""
        json_content = '{"min_coverage": 95, "skip_tests": true}'

        with patch("builtins.open", mock_open(read_data=json_content.encode())):
            with patch("json.load") as mock_json:
                mock_json.return_value = {"min_coverage": 95, "skip_tests": True}
                result = load_config("config.json")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 95
        assert result["skip_tests"] is True

    def test_load_config_flat_structure(self):
        """Test loading config with flat structure (no gates section)."""
        toml_content = """
        min_coverage = 85
        skip_tests = true
        """

        with patch("builtins.open", mock_open(read_data=toml_content.encode())):
            with patch("tomli.load") as mock_tomli:
                mock_tomli.return_value = {"min_coverage": 85, "skip_tests": True}
                result = load_config("ai-guard.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 85
        assert result["skip_tests"] is True
