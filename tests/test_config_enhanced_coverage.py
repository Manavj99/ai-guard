"""Enhanced tests for config module to significantly improve coverage."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, mock_open, MagicMock

from src.ai_guard.config import (
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
    load_config,
    Gates,
    Config,
    _get_toml_loader
)


class TestGetDefaultConfig:
    """Test get_default_config function."""

    def test_get_default_config(self):
        """Test get_default_config returns expected values."""
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
        """Test validate_config with valid config."""
        config = {"min_coverage": 80}
        assert validate_config(config) is True

    def test_validate_config_missing_required_field(self):
        """Test validate_config with missing required field."""
        config = {"other_field": "value"}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_type(self):
        """Test validate_config with invalid min_coverage type."""
        config = {"min_coverage": "80"}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_negative(self):
        """Test validate_config with negative min_coverage."""
        config = {"min_coverage": -1}
        assert validate_config(config) is False

    def test_validate_config_invalid_min_coverage_too_high(self):
        """Test validate_config with min_coverage > 100."""
        config = {"min_coverage": 101}
        assert validate_config(config) is False

    def test_validate_config_invalid_report_format(self):
        """Test validate_config with invalid report_format."""
        config = {"min_coverage": 80, "report_format": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_valid_report_format(self):
        """Test validate_config with valid report_format."""
        config = {"min_coverage": 80, "report_format": "json"}
        assert validate_config(config) is True

    def test_validate_config_invalid_llm_provider(self):
        """Test validate_config with invalid llm_provider."""
        config = {"min_coverage": 80, "llm_provider": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_valid_llm_provider(self):
        """Test validate_config with valid llm_provider."""
        config = {"min_coverage": 80, "llm_provider": "anthropic"}
        assert validate_config(config) is True

    def test_validate_config_invalid_boolean_field(self):
        """Test validate_config with invalid boolean field."""
        config = {"min_coverage": 80, "skip_tests": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_valid_boolean_fields(self):
        """Test validate_config with valid boolean fields."""
        config = {
            "min_coverage": 80,
            "skip_tests": True,
            "enhanced_testgen": False,
            "fail_on_bandit": True,
            "fail_on_lint": False,
            "fail_on_mypy": True
        }
        assert validate_config(config) is True


class TestMergeConfigs:
    """Test merge_configs function."""

    def test_merge_configs_none_override(self):
        """Test merge_configs with None override."""
        base = {"min_coverage": 80, "skip_tests": False}
        result = merge_configs(base, None)
        assert result == base

    def test_merge_configs_all_fields_overridden(self):
        """Test merge_configs with all main fields overridden."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "custom.json",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "key123",
            "llm_model": "claude-3"
        }
        result = merge_configs(base, override)
        assert result == override

    def test_merge_configs_partial_override(self):
        """Test merge_configs with partial override."""
        base = {"min_coverage": 80, "skip_tests": False, "report_format": "sarif"}
        override = {"min_coverage": 90}
        result = merge_configs(base, override)
        expected = {"min_coverage": 90, "skip_tests": False, "report_format": "sarif"}
        assert result == expected

    def test_merge_configs_extra_fields(self):
        """Test merge_configs with extra fields in override."""
        base = {"min_coverage": 80}
        override = {"min_coverage": 90, "extra_field": "value"}
        result = merge_configs(base, override)
        expected = {"min_coverage": 90, "extra_field": "value"}
        assert result == expected


class TestParseConfigValue:
    """Test parse_config_value function."""

    def test_parse_config_value_none(self):
        """Test parse_config_value with None input."""
        result = parse_config_value(None)
        assert result is None

    def test_parse_config_value_auto_boolean_true(self):
        """Test parse_config_value auto-detecting boolean true."""
        result = parse_config_value("true")
        assert result is True

    def test_parse_config_value_auto_boolean_false(self):
        """Test parse_config_value auto-detecting boolean false."""
        result = parse_config_value("false")
        assert result is False

    def test_parse_config_value_auto_integer(self):
        """Test parse_config_value auto-detecting integer."""
        result = parse_config_value("123")
        assert result == 123

    def test_parse_config_value_auto_float(self):
        """Test parse_config_value auto-detecting float."""
        result = parse_config_value("123.45")
        assert result == 123.45

    def test_parse_config_value_auto_string(self):
        """Test parse_config_value auto-detecting string."""
        result = parse_config_value("hello world")
        assert result == "hello world"

    def test_parse_config_value_string_type(self):
        """Test parse_config_value with string type."""
        result = parse_config_value("123", "string")
        assert result == "123"

    def test_parse_config_value_int_type(self):
        """Test parse_config_value with int type."""
        result = parse_config_value("123", "int")
        assert result == 123

    def test_parse_config_value_int_type_empty(self):
        """Test parse_config_value with int type and empty string."""
        result = parse_config_value("", "int")
        assert result == 0

    def test_parse_config_value_float_type(self):
        """Test parse_config_value with float type."""
        result = parse_config_value("123.45", "float")
        assert result == 123.45

    def test_parse_config_value_float_type_empty(self):
        """Test parse_config_value with float type and empty string."""
        result = parse_config_value("", "float")
        assert result == 0.0

    def test_parse_config_value_bool_type_true(self):
        """Test parse_config_value with bool type and true values."""
        for value in ["true", "1", "yes"]:
            result = parse_config_value(value, "bool")
            assert result is True

    def test_parse_config_value_bool_type_false(self):
        """Test parse_config_value with bool type and false values."""
        for value in ["false", "0", "no"]:
            result = parse_config_value(value, "bool")
            assert result is False

    def test_parse_config_value_bool_type_invalid(self):
        """Test parse_config_value with bool type and invalid value."""
        with pytest.raises(ValueError):
            parse_config_value("invalid", "bool")

    def test_parse_config_value_unknown_type(self):
        """Test parse_config_value with unknown type."""
        with pytest.raises(ValueError):
            parse_config_value("value", "unknown")


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_file_not_found(self):
        """Test load_config with nonexistent file."""
        result = load_config("nonexistent.toml")
        assert result == get_default_config()

    def test_load_config_json_format(self):
        """Test load_config with JSON format."""
        json_data = {"min_coverage": 90, "skip_tests": True}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                result = load_config(f.name)
                assert result["min_coverage"] == 90
                assert result["skip_tests"] is True
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    def test_load_config_toml_format_with_gates(self):
        """Test load_config with TOML format containing gates section."""
        toml_content = """[gates]
min_coverage = 90
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                result = load_config(f.name)
                assert result["min_coverage"] == 90
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    def test_load_config_toml_format_flat(self):
        """Test load_config with TOML format without gates section."""
        toml_content = """min_coverage = 90
skip_tests = true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                result = load_config(f.name)
                assert result["min_coverage"] == 90
                assert result["skip_tests"] is True
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    def test_load_config_parse_error(self):
        """Test load_config with parse error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content")
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                result = load_config(f.name)
                assert result == get_default_config()
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_toml_loader_exception(self, mock_loader):
        """Test load_config with TOML loader exception."""
        mock_loader.side_effect = Exception("Loader error")
        result = load_config("test.toml")
        assert result == get_default_config()


class TestGatesClass:
    """Test Gates class."""

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
            fail_on_mypy=False
        )
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is False


class TestConfigClass:
    """Test Config class."""

    def test_config_init_default(self):
        """Test Config initialization with default config."""
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

    def test_config_init_custom_path(self):
        """Test Config initialization with custom path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""[gates]
min_coverage = 90
""")
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                config = Config(f.name)
                assert config.min_coverage == 90
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows

    def test_config_get_existing_key(self):
        """Test Config.get with existing key."""
        config = Config()
        result = config.get("min_coverage")
        assert result == 80

    def test_config_get_nonexistent_key(self):
        """Test Config.get with nonexistent key."""
        config = Config()
        result = config.get("nonexistent_key")
        assert result is None

    def test_config_get_nonexistent_key_with_default(self):
        """Test Config.get with nonexistent key and default value."""
        config = Config()
        result = config.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_config_set(self):
        """Test Config.set method."""
        config = Config()
        config.set("custom_key", "custom_value")
        assert config.get("custom_key") == "custom_value"

    def test_config_reload(self):
        """Test Config.reload method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""[gates]
min_coverage = 90
""")
            f.flush()
            f.close()  # Close the file handle before reading
            try:
                config = Config(f.name)
                assert config.min_coverage == 90
                
                # Modify the file
                with open(f.name, 'w') as f2:
                    f2.write("""[gates]
min_coverage = 95
""")
                
                # Reload and check
                config.reload()
                assert config.min_coverage == 95
            finally:
                try:
                    os.unlink(f.name)
                except (PermissionError, FileNotFoundError):
                    pass  # Ignore cleanup errors on Windows


class TestGetTomlLoader:
    """Test _get_toml_loader function."""

    def test_get_toml_loader_returns_module(self):
        """Test _get_toml_loader returns a module."""
        result = _get_toml_loader()
        assert result is not None
        assert hasattr(result, 'load')

    def test_get_toml_loader_has_load_method(self):
        """Test _get_toml_loader returns module with load method."""
        result = _get_toml_loader()
        assert hasattr(result, 'load')
        assert callable(result.load)
