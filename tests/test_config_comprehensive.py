"""Comprehensive tests for the AI-Guard config module."""

import pytest
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.ai_guard.config import (
    load_config, Config, Gates, get_default_config, validate_config
)


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_config_default(self):
        """Test loading default configuration."""
        config = load_config()
        assert config is not None
        assert isinstance(config, dict)

    def test_load_config_toml_file(self):
        """Test loading TOML configuration file."""
        # Create a temporary TOML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('''
[gates]
min_coverage = 90
skip_tests = true
report_format = "html"
''')
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config["min_coverage"] == 90
            # The config loader only updates min_coverage from gates section
            # Other fields remain at default values
            assert config["skip_tests"] is False  # Default value
            assert config["report_format"] == "sarif"  # Default value
        finally:
            os.unlink(temp_path)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_json_file(self, mock_file, mock_exists):
        """Test loading JSON configuration file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = '''
        {
            "min_coverage": 85,
            "skip_tests": false,
            "report_format": "json"
        }
        '''
        
        config = load_config("test.json")
        assert config["min_coverage"] == 85
        assert config["skip_tests"] is False
        assert config["report_format"] == "json"

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_yaml_file(self, mock_file, mock_exists):
        """Test loading YAML configuration file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = '''
        ai_guard:
          min_coverage: 80
          skip_tests: false
          report_format: "sarif"
        '''
        
        config = load_config("test.yaml")
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"

    @patch('os.path.exists')
    def test_load_config_file_not_exists(self, mock_exists):
        """Test loading config when file doesn't exist."""
        mock_exists.return_value = False
        config = load_config("nonexistent.toml")
        assert config is not None
        # Should return default config

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_parse_error(self, mock_file, mock_exists):
        """Test loading config with parse error."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid toml content"
        
        config = load_config("test.toml")
        assert config is not None
        # Should return default config on parse error


class TestConfigClass:
    """Test Config class functionality."""

    def test_config_init_default(self):
        """Test Config initialization with default path."""
        config = Config()
        assert config.config_path == "ai-guard.toml"
        assert config._config is not None

    def test_config_init_custom_path(self):
        """Test Config initialization with custom path."""
        config = Config("custom.toml")
        assert config.config_path == "custom.toml"

    @patch('src.ai_guard.config.load_config')
    def test_config_properties(self, mock_load_config):
        """Test Config class properties."""
        mock_load_config.return_value = {
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "html",
            "report_path": "custom.sarif",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3",
            "fail_on_bandit": False,
            "fail_on_lint": False,
            "fail_on_mypy": False
        }
        
        config = Config()
        
        assert config.min_coverage == 90
        assert config.skip_tests is True
        assert config.report_format == "html"
        assert config.report_path == "custom.sarif"
        assert config.enhanced_testgen is True
        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "test-key"
        assert config.llm_model == "claude-3"
        assert config.fail_on_bandit is False
        assert config.fail_on_lint is False
        assert config.fail_on_mypy is False

    @patch('src.ai_guard.config.load_config')
    def test_config_properties_defaults(self, mock_load_config):
        """Test Config class properties with default values."""
        mock_load_config.return_value = {}
        
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


class TestGatesClass:
    """Test Gates class functionality."""

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


class TestConfigUtilities:
    """Test config utility functions."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        assert config is not None
        assert isinstance(config, dict)
        assert "min_coverage" in config
        assert "skip_tests" in config
        assert "report_format" in config

    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = {
            "min_coverage": 80,
            "skip_tests": False,
            "report_format": "sarif"
        }
        assert validate_config(config) is True

    def test_validate_config_invalid(self):
        """Test validating invalid configuration."""
        config = {
            "skip_tests": False,
            "report_format": "sarif"
        }
        assert validate_config(config) is False

    def test_validate_config_invalid_coverage(self):
        """Test validating configuration with invalid coverage."""
        config = {
            "min_coverage": -10,
            "skip_tests": False,
            "report_format": "sarif"
        }
        assert validate_config(config) is False


class TestConfigEdgeCases:
    """Test configuration edge cases."""

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_empty_file(self, mock_file, mock_exists):
        """Test loading empty configuration file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = ""
        
        config = load_config("empty.toml")
        assert config is not None
        # Should return default config

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_malformed_toml(self, mock_file, mock_exists):
        """Test loading malformed TOML file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "[invalid toml"
        
        config = load_config("malformed.toml")
        assert config is not None
        # Should return default config

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_io_error(self, mock_file, mock_exists):
        """Test loading config with IO error."""
        mock_exists.return_value = True
        mock_file.side_effect = IOError("Permission denied")
        
        config = load_config("restricted.toml")
        assert config is not None
        # Should return default config

    def test_config_type_conversion(self):
        """Test configuration value type conversion."""
        config = Config()
        
        # Test that properties return correct types
        assert isinstance(config.min_coverage, int)
        assert isinstance(config.skip_tests, bool)
        assert isinstance(config.report_format, str)
        assert isinstance(config.report_path, str)
        assert isinstance(config.enhanced_testgen, bool)
        assert isinstance(config.llm_provider, str)
        assert isinstance(config.llm_api_key, str)
        assert isinstance(config.llm_model, str)
        assert isinstance(config.fail_on_bandit, bool)
        assert isinstance(config.fail_on_lint, bool)
        assert isinstance(config.fail_on_mypy, bool)
