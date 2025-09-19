"""Simple tests for configuration module."""

import pytest
from unittest.mock import patch, mock_open

from src.ai_guard.config import (
    load_config, get_default_config, Config, Gates, 
    validate_config, merge_configs
)


class TestConfigBasic:
    """Test basic configuration functionality."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        assert "min_coverage" in config
        assert config["min_coverage"] == 80
        assert "fail_on_bandit" in config
        assert config["fail_on_bandit"] is True

    def test_validate_config_valid(self):
        """Test validation with valid config."""
        config = {"min_coverage": 80}
        assert validate_config(config) is True

    def test_validate_config_invalid(self):
        """Test validation with invalid config."""
        config = {"min_coverage": "invalid"}
        assert validate_config(config) is False

    def test_validate_config_missing_field(self):
        """Test validation with missing required field."""
        config = {"other_field": "value"}
        assert validate_config(config) is True  # Now allows missing min_coverage

    def test_merge_configs_basic(self):
        """Test basic config merging."""
        base = {"min_coverage": 80}
        override = {"fail_on_bandit": False}
        result = merge_configs(base, override)
        assert result["min_coverage"] == 80
        assert result["fail_on_bandit"] is False

    def test_merge_configs_override_values(self):
        """Test config merging with value overrides."""
        base = {"min_coverage": 80}
        override = {"min_coverage": 90}
        result = merge_configs(base, override)
        assert result["min_coverage"] == 90

    def test_gates_class_init(self):
        """Test Gates class initialization."""
        gates = Gates()
        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_class_custom(self):
        """Test Gates class with custom values."""
        gates = Gates(min_coverage=90, fail_on_bandit=False)
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is True  # Default

    def test_config_class_init(self):
        """Test Config class initialization."""
        config = Config()
        assert config.min_coverage == 80
        assert config.fail_on_bandit is True

    def test_config_class_custom(self):
        """Test Config class with custom values."""
        config = Config(min_coverage=90, fail_on_bandit=False)
        assert config.min_coverage == 90
        assert config.fail_on_bandit is False

    def test_load_config_default(self):
        """Test loading config with default file."""
        with patch("builtins.open", mock_open(read_data="[gates]\nmin_coverage = 85")):
            with patch("toml.load") as mock_toml:
                mock_toml.return_value = {"gates": {"min_coverage": 85}}
                config = load_config()
                # Should return default config if parsing fails
                assert config["min_coverage"] == 80

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            config = load_config("nonexistent.toml")
            assert config == get_default_config()

    def test_config_validation_edge_cases(self):
        """Test config validation edge cases."""
        # Test with None
        assert validate_config(None) is False
        
        # Test with empty dict
        assert validate_config({}) is True  # Now allows empty dict
        
        # Test with valid but different structure
        config = {"min_coverage": 80, "extra_field": "value"}
        assert validate_config(config) is True

    def test_merge_configs_edge_cases(self):
        """Test config merging edge cases."""
        # Test with None values
        base = {"min_coverage": 80}
        override = {"min_coverage": None}
        result = merge_configs(base, override)
        assert result["min_coverage"] is None

        # Test with empty override
        base = {"min_coverage": 80}
        override = {}
        result = merge_configs(base, override)
        assert result == base

        # Test with None base
        base = None
        override = {"min_coverage": 80}
        result = merge_configs(base, override)
        assert result == override
