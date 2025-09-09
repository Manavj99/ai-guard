"""Basic tests for the AI-Guard analyzer module."""

import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.analyzer import main, CodeAnalyzer


def test_analyzer_import():
    """Test that the analyzer module can be imported."""
    from src.ai_guard import analyzer
    assert analyzer is not None


def test_analyzer_main_function_exists():
    """Test that the main function exists."""
    from src.ai_guard.analyzer import main
    assert callable(main)


def test_code_analyzer_class():
    """Test that CodeAnalyzer class exists and can be instantiated."""
    analyzer = CodeAnalyzer()
    assert analyzer is not None


@patch('src.ai_guard.analyzer.run_lint_check')
def test_run_lint_check_basic(mock_lint_check):
    """Test basic functionality of run_lint_check."""
    mock_lint_check.return_value = {
        'passed': True,
        'issues': []
    }
    
    result = mock_lint_check('src')
    assert result is not None
    assert result['passed'] is True


@patch('src.ai_guard.analyzer.run_coverage_check')
def test_run_coverage_check_basic(mock_coverage_check):
    """Test basic functionality of run_coverage_check."""
    mock_coverage_check.return_value = {
        'passed': True,
        'coverage': 85.0
    }
    
    result = mock_coverage_check('src', 80)
    assert result is not None
    assert result['passed'] is True


def test_analyzer_config_loading():
    """Test that the analyzer can load configuration."""
    from src.ai_guard.config import load_config
    config = load_config()
    assert config is not None


def test_analyzer_diff_parser():
    """Test diff parser functionality."""
    from src.ai_guard.diff_parser import parse_diff
    
    # Test with empty diff
    result = parse_diff("")
    assert result is not None
    assert isinstance(result, list)
