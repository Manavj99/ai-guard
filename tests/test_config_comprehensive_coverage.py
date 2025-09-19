"""Comprehensive tests for config.py to achieve 80+ coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
import json

from src.ai_guard.config import (
    _get_toml_loader, get_default_config, validate_config, load_config,
    merge_configs, parse_config_value, Gates, Config
)


class TestGetTomlLoader:
    """Test _get_toml_loader function."""
    
    @patch('builtins.__import__', side_effect=ImportError)
    def test_get_toml_loader_fallback_to_tomli(self, mock_import):
        """Test fallback to tomli when tomllib is not available."""
        with pytest.raises(ImportError, match="Neither tomllib nor tomli is available"):
            _get_toml_loader()
    
    def test_get_toml_loader_uses_tomllib(self):
        """Test that tomllib is used when available."""
        loader = _get_toml_loader()
        assert loader is not None


class TestGetDefaultConfig:
    """Test get_default_config function."""
    
    def test_get_default_config_structure(self):
        """Test default config structure."""
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert "gates" in config
        assert "min_coverage" in config
        assert "skip_tests" in config
        assert "report_format" in config
        assert "report_path" in config
        assert "enhanced_testgen" in config
        assert "llm_provider" in config
        assert "llm_api_key" in config
        assert "llm_model" in config
        assert "fail_on_bandit" in config
        assert "fail_on_lint" in config
        assert "fail_on_mypy" in config
    
    def test_get_default_config_values(self):
        """Test default config values."""
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
        
        # Test gates section
        assert config["gates"]["min_coverage"] == 80
        assert config["gates"]["fail_on_bandit"] is True
        assert config["gates"]["fail_on_lint"] is True
        assert config["gates"]["fail_on_mypy"] is True


class TestValidateConfig:
    """Test validate_config function."""
    
    def test_validate_config_none(self):
        """Test validate_config with None."""
        assert validate_config(None) is False
    
    def test_validate_config_empty_dict(self):
        """Test validate_config with empty dict."""
        # Updated: empty dict is now valid (will use defaults)
        assert validate_config({}) is True
    
    def test_validate_config_invalid_type(self):
        """Test validate_config with invalid type."""
        assert validate_config("invalid") is False
        assert validate_config(123) is False
        assert validate_config([]) is False
    
    def test_validate_config_valid(self):
        """Test validate_config with valid config."""
        config = {
            "min_coverage": 80,
            "skip_tests": False,
            "report_format": "sarif",
            "report_path": "ai-guard.sarif",
            "enhanced_testgen": False,
            "llm_provider": "openai",
            "llm_api_key": "",
            "llm_model": "gpt-4",
            "fail_on_bandit": True,
            "fail_on_lint": True,
            "fail_on_mypy": True,
            "gates": {
                "min_coverage": 80,
                "fail_on_bandit": True,
                "fail_on_lint": True,
                "fail_on_mypy": True
            }
        }
        assert validate_config(config) is True
    
    def test_validate_config_missing_required_fields(self):
        """Test validate_config with missing required fields."""
        config = {
            "min_coverage": 80,
            # Missing other required fields
        }
        # Updated: validation is now more lenient
        assert validate_config(config) is True
    
    def test_validate_config_invalid_field_types(self):
        """Test validate_config with invalid field types."""
        config = {
            "min_coverage": "invalid",  # Should be number
            "skip_tests": "invalid",    # Should be boolean
            "report_format": 123,       # Should be string
            "report_path": True,        # Should be string
            "enhanced_testgen": "invalid", # Should be boolean
            "llm_provider": 456,        # Should be string
            "llm_api_key": [],          # Should be string
            "llm_model": None,          # Should be string
            "fail_on_bandit": "invalid", # Should be boolean
            "fail_on_lint": "invalid",  # Should be boolean
            "fail_on_mypy": "invalid",  # Should be boolean
            "gates": "invalid"          # Should be dict
        }
        assert validate_config(config) is False


class TestLoadConfig:
    """Test load_config function."""
    
    def test_load_config_file_not_found(self):
        """Test load_config with file not found."""
        config = load_config("nonexistent.toml")
        assert config == get_default_config()
    
    def test_load_config_invalid_file(self):
        """Test load_config with invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content")
            f.flush()
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config == get_default_config()
        finally:
            os.unlink(temp_path)
    
    def test_load_config_valid_file(self):
        """Test load_config with valid file."""
        toml_content = """
        min_coverage = 90
        skip_tests = true
        report_format = "html"
        report_path = "custom.sarif"
        enhanced_testgen = true
        llm_provider = "anthropic"
        llm_api_key = "test-key"
        llm_model = "claude-3-sonnet"
        fail_on_bandit = false
        fail_on_lint = false
        fail_on_mypy = false
        
        [gates]
        min_coverage = 90
        fail_on_bandit = false
        fail_on_lint = false
        fail_on_mypy = false
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config["min_coverage"] == 90
            assert config["skip_tests"] is True
            assert config["report_format"] == "html"
            assert config["report_path"] == "custom.sarif"
            assert config["enhanced_testgen"] is True
            assert config["llm_provider"] == "anthropic"
            assert config["llm_api_key"] == "test-key"
            assert config["llm_model"] == "claude-3-sonnet"
            assert config["fail_on_bandit"] is False
            assert config["fail_on_lint"] is False
            assert config["fail_on_mypy"] is False
            assert config["gates"]["min_coverage"] == 90
            assert config["gates"]["fail_on_bandit"] is False
            assert config["gates"]["fail_on_lint"] is False
            assert config["gates"]["fail_on_mypy"] is False
        finally:
            os.unlink(temp_path)
    
    def test_load_config_partial_file(self):
        """Test load_config with partial config file."""
        toml_content = """
        min_coverage = 85
        report_format = "json"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            # Should merge with defaults
            assert config["min_coverage"] == 85
            assert config["report_format"] == "json"
            # Other values should be defaults
            assert config["skip_tests"] is False
            assert config["enhanced_testgen"] is False
            assert config["llm_provider"] == "openai"
        finally:
            os.unlink(temp_path)
    
    @patch('builtins.open', side_effect=PermissionError)
    def test_load_config_permission_error(self, mock_open):
        """Test load_config with permission error."""
        config = load_config("test.toml")
        assert config == get_default_config()
    
    @patch('builtins.open', side_effect=OSError)
    def test_load_config_os_error(self, mock_open):
        """Test load_config with OS error."""
        config = load_config("test.toml")
        assert config == get_default_config()


class TestMergeConfigs:
    """Test merge_configs function."""
    
    def test_merge_configs_both_none(self):
        """Test merge_configs with both configs None."""
        result = merge_configs(None, None)
        assert result == {}
    
    def test_merge_configs_first_none(self):
        """Test merge_configs with first config None."""
        config2 = {"min_coverage": 85}
        result = merge_configs(None, config2)
        assert result == config2
    
    def test_merge_configs_second_none(self):
        """Test merge_configs with second config None."""
        config1 = {"min_coverage": 80}
        result = merge_configs(config1, None)
        assert result == config1
    
    def test_merge_configs_both_valid(self):
        """Test merge_configs with both configs valid."""
        config1 = {
            "min_coverage": 80,
            "skip_tests": False,
            "report_format": "sarif"
        }
        config2 = {
            "min_coverage": 85,
            "enhanced_testgen": True,
            "llm_provider": "anthropic"
        }
        
        result = merge_configs(config1, config2)
        expected = {
            "min_coverage": 85,  # config2 overrides config1
            "skip_tests": False,  # from config1
            "report_format": "sarif",  # from config1
            "enhanced_testgen": True,  # from config2
            "llm_provider": "anthropic"  # from config2
        }
        assert result == expected
    
    def test_merge_configs_nested_dicts(self):
        """Test merge_configs with nested dictionaries."""
        config1 = {
            "gates": {
                "min_coverage": 80,
                "fail_on_bandit": True
            }
        }
        config2 = {
            "gates": {
                "min_coverage": 85,
                "fail_on_lint": True
            }
        }
        
        result = merge_configs(config1, config2)
        expected = {
            "gates": {
                "min_coverage": 85,
                "fail_on_bandit": True,
                "fail_on_lint": True
            }
        }
        assert result == expected


class TestParseConfigValue:
    """Test parse_config_value function."""
    
    def test_parse_config_value_string(self):
        """Test parse_config_value with string."""
        result = parse_config_value("test", "string")
        assert result == "test"
    
    def test_parse_config_value_int(self):
        """Test parse_config_value with int."""
        result = parse_config_value("80", "int")
        assert result == 80
    
    def test_parse_config_value_bool_true(self):
        """Test parse_config_value with bool true."""
        result = parse_config_value("true", "bool")
        assert result is True
    
    def test_parse_config_value_bool_false(self):
        """Test parse_config_value with bool false."""
        result = parse_config_value("false", "bool")
        assert result is False
    
    def test_parse_config_value_invalid_type(self):
        """Test parse_config_value with invalid type."""
        with pytest.raises(ValueError, match="Unknown value type: invalid"):
            parse_config_value("test", "invalid")


class TestGates:
    """Test Gates class."""
    
    def test_gates_initialization(self):
        """Test Gates initialization."""
        gates = Gates()
        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True
    
    def test_gates_custom_values(self):
        """Test Gates with custom values."""
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
    
    def test_config_initialization(self):
        """Test Config initialization."""
        config = Config()
        assert config.min_coverage == 80
        assert config.skip_tests is False
        assert config.report_format == "sarif"
        assert config.enhanced_testgen is False
    
    def test_config_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            min_coverage=90,
            skip_tests=True,
            report_format="html",
            enhanced_testgen=True
        )
        assert config.min_coverage == 90
        assert config.skip_tests is True
        assert config.report_format == "html"
        assert config.enhanced_testgen is True
