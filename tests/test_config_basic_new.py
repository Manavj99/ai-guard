"""Basic tests for config module using actual functions."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.ai_guard.config import (
    _get_toml_loader,
    get_default_config,
    validate_config,
    load_config,
    merge_configs,
    Gates,
    Config
)


class TestGetTomlLoader:
    """Test _get_toml_loader function."""

    def test_get_toml_loader_tomllib(self):
        """Test getting tomllib loader."""
        with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                   mock_tomllib if name == 'tomllib' else __import__(name, *args, **kwargs)):
            mock_tomllib = MagicMock()
            loader = _get_toml_loader()
            assert loader == mock_tomllib

    def test_get_toml_loader_tomli_fallback(self):
        """Test getting tomli loader as fallback."""
        def mock_import(name, *args, **kwargs):
            if name == 'tomllib':
                raise ImportError("No module named 'tomllib'")
            elif name == 'tomli':
                return mock_tomli
            else:
                return __import__(name, *args, **kwargs)
        
        mock_tomli = MagicMock()
        with patch('builtins.__import__', side_effect=mock_import):
            loader = _get_toml_loader()
            assert loader == mock_tomli

    def test_get_toml_loader_no_loader_available(self):
        """Test error when no TOML loader is available."""
        def mock_import(name, *args, **kwargs):
            if name in ('tomllib', 'tomli'):
                raise ImportError(f"No module named '{name}'")
            else:
                return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ImportError, match="Neither tomllib nor tomli is available"):
                _get_toml_loader()


class TestGetDefaultConfig:
    """Test get_default_config function."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        
        assert "gates" in config
        assert "min_coverage" in config
        assert "skip_tests" in config
        assert "report_format" in config
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_valid(self):
        """Test validation of valid config."""
        config = get_default_config()
        assert validate_config(config) is True

    def test_validate_config_invalid_coverage(self):
        """Test validation with invalid coverage value."""
        config = get_default_config()
        config["min_coverage"] = -10
        assert validate_config(config) is False

    def test_validate_config_invalid_gates(self):
        """Test validation with invalid gates."""
        config = get_default_config()
        config["gates"] = "invalid"
        assert validate_config(config) is False

    def test_validate_config_missing_required(self):
        """Test validation with missing required fields."""
        config = {}
        assert validate_config(config) is True  # Empty config is valid (uses defaults)


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_file_exists(self):
        """Test loading config from existing file."""
        config_data = """
[gates]
min_coverage = 90
fail_on_bandit = true

skip_tests = false
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_data)
            f.flush()
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config["min_coverage"] == 90
            assert config["gates"]["min_coverage"] == 90
        finally:
            try:
                os.unlink(temp_path)
            except (OSError, PermissionError):
                pass  # Ignore cleanup errors on Windows

    def test_load_config_file_not_exists(self):
        """Test loading config from non-existent file returns default."""
        config = load_config("nonexistent.toml")
        assert config == get_default_config()

    def test_load_config_invalid_toml(self):
        """Test loading config with invalid TOML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content")
            f.flush()
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            # Should return default config on error
            assert config == get_default_config()
        finally:
            try:
                os.unlink(temp_path)
            except (OSError, PermissionError):
                pass  # Ignore cleanup errors on Windows


class TestMergeConfigs:
    """Test merge_configs function."""

    def test_merge_configs_basic(self):
        """Test basic config merging."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        
        merged = merge_configs(base, override)
        assert merged["a"] == 1
        assert merged["b"] == 3
        assert merged["c"] == 4

    def test_merge_configs_nested(self):
        """Test merging nested configs."""
        base = {"gates": {"min_coverage": 80, "fail_on_bandit": True}}
        override = {"gates": {"min_coverage": 90}}
        
        merged = merge_configs(base, override)
        assert merged["gates"]["min_coverage"] == 90
        assert merged["gates"]["fail_on_bandit"] is True

    def test_merge_configs_empty_base(self):
        """Test merging with empty base config."""
        override = {"a": 1, "b": 2}
        merged = merge_configs({}, override)
        assert merged == override


class TestGates:
    """Test Gates class."""

    def test_gates_init(self):
        """Test Gates initialization."""
        gates = Gates()
        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_custom_values(self):
        """Test Gates with custom values."""
        gates = Gates(min_coverage=90, fail_on_bandit=False)
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is True  # default value


class TestConfig:
    """Test Config class."""

    def test_config_init(self):
        """Test Config initialization."""
        config = Config()
        assert config.gates is not None
        assert config.min_coverage == 80
        assert config.skip_tests is False
        assert config.report_format == "sarif"

    def test_config_custom_values(self):
        """Test Config with custom values."""
        gates = Gates(min_coverage=90)
        config = Config(gates=gates, min_coverage=90, skip_tests=True)
        assert config.gates.min_coverage == 90
        assert config.min_coverage == 90
        assert config.skip_tests is True

    def test_config_to_dict(self):
        """Test Config to_dict method."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "gates" in config_dict
        assert "min_coverage" in config_dict
        assert "skip_tests" in config_dict
        assert "report_format" in config_dict

    def test_config_from_dict(self):
        """Test Config from_dict method."""
        config_data = {
            "gates": {"min_coverage": 90, "fail_on_bandit": False},
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "json"
        }
        
        config = Config.from_dict(config_data)
        assert config.gates.min_coverage == 90
        assert config.gates.fail_on_bandit is False
        assert config.min_coverage == 90
        assert config.skip_tests is True
        assert config.report_format == "json"
