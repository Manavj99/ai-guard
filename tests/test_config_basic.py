"""Basic tests for the AI-Guard config module."""

import pytest
from unittest.mock import patch, mock_open
from src.ai_guard.config import load_config


def test_config_import():
    """Test that the config module can be imported."""
    from src.ai_guard import config
    assert config is not None


def test_load_config_function_exists():
    """Test that load_config function exists."""
    from src.ai_guard.config import load_config
    assert callable(load_config)


def test_load_config_basic():
    """Test basic load_config functionality."""
    config = load_config()
    assert config is not None


@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
def test_load_config_file_exists(mock_exists, mock_file):
    """Test loading config when file exists."""
    mock_exists.return_value = True
    mock_file.return_value.read.return_value = '''
    [ai_guard]
    min_coverage = 85
    skip_tests = false
    report_format = "json"
    '''
    
    config = load_config()
    assert config is not None


@patch('os.path.exists')
def test_load_config_file_not_exists(mock_exists):
    """Test loading config when file doesn't exist."""
    mock_exists.return_value = False
    
    config = load_config()
    assert config is not None
    # Should return default config
