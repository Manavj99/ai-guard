"""Core tests for config module to improve coverage."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.ai_guard.config import load_config, Config


class TestConfig:
    """Test Config class."""
    
    def test_config_defaults(self):
        """Test Config default values."""
        config = Config()
        assert config.flake8_enabled is True
        assert config.mypy_enabled is True
        assert config.bandit_enabled is True
        assert config.coverage_enabled is True
        assert config.coverage_threshold == 80.0
        assert config.output_dir == "ai-guard-output"
    
    def test_config_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            flake8_enabled=False,
            mypy_enabled=False,
            coverage_threshold=90.0,
            output_dir="custom-output"
        )
        assert config.flake8_enabled is False
        assert config.mypy_enabled is False
        assert config.coverage_threshold == 90.0
        assert config.output_dir == "custom-output"


class TestLoadConfig:
    """Test load_config function."""
    
    def test_load_config_default(self):
        """Test load_config with default config."""
        config = load_config()
        assert isinstance(config, Config)
        assert config.flake8_enabled is True
    
    def test_load_config_from_file(self):
        """Test load_config from file."""
        config_data = """
[ai-guard]
flake8_enabled = false
mypy_enabled = false
coverage_threshold = 90.0
output_dir = "test-output"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_data)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config.flake8_enabled is False
            assert config.mypy_enabled is False
            assert config.coverage_threshold == 90.0
            assert config.output_dir == "test-output"
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        """Test load_config with non-existent file."""
        config = load_config("nonexistent.toml")
        # Should return default config
        assert isinstance(config, Config)
        assert config.flake8_enabled is True
    
    def test_load_config_invalid_toml(self):
        """Test load_config with invalid TOML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content [")
            config_path = f.name
        
        try:
            config = load_config(config_path)
            # Should return default config on error
            assert isinstance(config, Config)
            assert config.flake8_enabled is True
        finally:
            Path(config_path).unlink()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('tomllib.load')
    def test_load_config_parsing_error(self, mock_toml_load, mock_file):
        """Test load_config with parsing error."""
        mock_toml_load.side_effect = Exception("Parse error")
        
        config = load_config("test.toml")
        # Should return default config on error
        assert isinstance(config, Config)
        assert config.flake8_enabled is True
    
    def test_load_config_partial_config(self):
        """Test load_config with partial config."""
        config_data = """
[ai-guard]
flake8_enabled = false
# Other settings use defaults
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_data)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config.flake8_enabled is False
            assert config.mypy_enabled is True  # Default value
            assert config.coverage_threshold == 80.0  # Default value
        finally:
            Path(config_path).unlink()
    
    def test_load_config_environment_override(self):
        """Test load_config with environment variable override."""
        with patch.dict('os.environ', {
            'AI_GUARD_FLAKE8_ENABLED': 'false',
            'AI_GUARD_COVERAGE_THRESHOLD': '90.0'
        }):
            config = load_config()
            assert config.flake8_enabled is False
            assert config.coverage_threshold == 90.0
    
    def test_load_config_invalid_environment_values(self):
        """Test load_config with invalid environment values."""
        with patch.dict('os.environ', {
            'AI_GUARD_FLAKE8_ENABLED': 'invalid',
            'AI_GUARD_COVERAGE_THRESHOLD': 'not_a_number'
        }):
            config = load_config()
            # Should use defaults for invalid values
            assert config.flake8_enabled is True
            assert config.coverage_threshold == 80.0


class TestConfigValidation:
    """Test config validation."""
    
    def test_config_negative_coverage_threshold(self):
        """Test config with negative coverage threshold."""
        config = Config(coverage_threshold=-10.0)
        # Should be clamped to 0
        assert config.coverage_threshold == 0.0
    
    def test_config_high_coverage_threshold(self):
        """Test config with coverage threshold > 100."""
        config = Config(coverage_threshold=150.0)
        # Should be clamped to 100
        assert config.coverage_threshold == 100.0
    
    def test_config_empty_output_dir(self):
        """Test config with empty output directory."""
        config = Config(output_dir="")
        # Should use default
        assert config.output_dir == "ai-guard-output"
