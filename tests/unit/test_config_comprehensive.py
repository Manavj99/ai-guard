"""Comprehensive tests for config.py module."""

from unittest.mock import patch, mock_open
from ai_guard.config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_config_initialization(self):
        """Test config initialization."""
        config = Config()
        assert config is not None

    def test_load_config_file(self):
        """Test loading config from file."""
        config = Config()

        mock_config_data = """
[ai_guard]
coverage_threshold = 90
quality_gate = true
"""

        with patch("builtins.open", mock_open(read_data=mock_config_data)):
            with patch("tomli.load") as mock_load:
                mock_load.return_value = {"ai_guard": {"coverage_threshold": 90}}
                result = config.load_config("config.toml")
                assert result is not None

    def test_get_setting(self):
        """Test getting configuration setting."""
        config = Config()
        config.settings = {"coverage_threshold": 90}

        result = config.get_setting("coverage_threshold")
        assert result == 90

    def test_set_setting(self):
        """Test setting configuration value."""
        config = Config()
        config.set_setting("test_setting", "test_value")
        assert config.get_setting("test_setting") == "test_value"
