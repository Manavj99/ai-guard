"""Tests for config module."""

import pytest
from unittest.mock import patch, mock_open
from src.ai_guard.config import load_config, Gates


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
            fail_on_mypy=False
        )
        
        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is False

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        result = load_config("nonexistent.toml")
        
        assert isinstance(result, Gates)
        assert result.min_coverage == 80  # Default value

    def test_load_config_valid_toml(self):
        """Test loading config from valid TOML file."""
        toml_content = """
        [gates]
        min_coverage = 95
        """
        
        with patch('builtins.open', mock_open(read_data=toml_content.encode())):
            with patch('tomli.load') as mock_tomli:
                mock_tomli.return_value = {"gates": {"min_coverage": 95}}
                result = load_config("ai-guard.toml")
        
        assert isinstance(result, Gates)
        assert result.min_coverage == 95

    def test_load_config_missing_gates_section(self):
        """Test loading config when gates section is missing."""
        toml_content = """
        [other_section]
        some_value = "test"
        """
        
        with patch('builtins.open', mock_open(read_data=toml_content.encode())):
            with patch('tomli.load') as mock_tomli:
                mock_tomli.return_value = {"other_section": {"some_value": "test"}}
                result = load_config("ai-guard.toml")
        
        assert isinstance(result, Gates)
        assert result.min_coverage == 80  # Default value

    def test_load_config_missing_min_coverage(self):
        """Test loading config when min_coverage is missing."""
        toml_content = """
        [gates]
        other_setting = "value"
        """
        
        with patch('builtins.open', mock_open(read_data=toml_content.encode())):
            with patch('tomli.load') as mock_tomli:
                mock_tomli.return_value = {"gates": {"other_setting": "value"}}
                result = load_config("ai-guard.toml")
        
        assert isinstance(result, Gates)
        assert result.min_coverage == 80  # Default value

    def test_load_config_parse_error(self):
        """Test loading config when TOML parsing fails."""
        with patch('builtins.open', mock_open(read_data=b"invalid toml")):
            with patch('tomli.load', side_effect=Exception("Parse error")):
                result = load_config("ai-guard.toml")
        
        assert isinstance(result, Gates)
        assert result.min_coverage == 80  # Default value

    def test_load_config_custom_path(self):
        """Test loading config from custom path."""
        toml_content = """
        [gates]
        min_coverage = 85
        """
        
        with patch('builtins.open', mock_open(read_data=toml_content.encode())):
            with patch('tomli.load') as mock_tomli:
                mock_tomli.return_value = {"gates": {"min_coverage": 85}}
                result = load_config("custom/path/config.toml")
        
        assert isinstance(result, Gates)
        assert result.min_coverage == 85
