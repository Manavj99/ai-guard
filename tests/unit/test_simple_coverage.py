"""Simple tests to improve coverage for core modules."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from src.ai_guard.config import get_default_config, validate_config, load_config
from src.ai_guard.report import GateResult, summarize
from src.ai_guard.diff_parser import changed_python_files, filter_python_files, get_file_extensions


class TestConfig:
    """Test config module functions."""
    
    def test_get_default_config(self):
        """Test get_default_config returns expected structure."""
        config = get_default_config()
        assert isinstance(config, dict)
        assert "min_coverage" in config
        assert "skip_tests" in config
        assert "report_format" in config
        assert config["min_coverage"] == 80
    
    def test_validate_config_valid(self):
        """Test validate_config with valid config."""
        config = {"min_coverage": 85}
        assert validate_config(config) is True
    
    def test_validate_config_invalid(self):
        """Test validate_config with invalid config."""
        config = {}  # Missing min_coverage
        assert validate_config(config) is False
    
    def test_validate_config_negative_coverage(self):
        """Test validate_config with negative coverage."""
        config = {"min_coverage": -10}
        assert validate_config(config) is False
    
    def test_validate_config_high_coverage(self):
        """Test validate_config with coverage > 100."""
        config = {"min_coverage": 150}
        assert validate_config(config) is False
    
    def test_load_config_default(self):
        """Test load_config returns default config."""
        config = load_config()
        assert isinstance(config, dict)
        assert "min_coverage" in config
    
    def test_load_config_from_file(self):
        """Test load_config from file."""
        config_data = """
[gates]
min_coverage = 90
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_data)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config["min_coverage"] == 90
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        """Test load_config with non-existent file."""
        config = load_config("nonexistent.toml")
        # Should return default config
        assert isinstance(config, dict)
        assert "min_coverage" in config


class TestReport:
    """Test report module functions."""
    
    def test_gate_result_creation(self):
        """Test GateResult creation."""
        gate = GateResult("Test Gate", True, "All tests passed")
        assert gate.name == "Test Gate"
        assert gate.passed is True
        assert gate.details == "All tests passed"
        assert gate.exit_code == 0
    
    def test_gate_result_with_exit_code(self):
        """Test GateResult with custom exit code."""
        gate = GateResult("Test Gate", False, "Failed", 1)
        assert gate.name == "Test Gate"
        assert gate.passed is False
        assert gate.details == "Failed"
        assert gate.exit_code == 1
    
    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        gates = [
            GateResult("Lint (flake8)", True, ""),
            GateResult("Static types (mypy)", True, ""),
            GateResult("Security (bandit)", True, ""),
            GateResult("Coverage", True, "85% >= 80%")
        ]
        
        exit_code = summarize(gates)
        assert exit_code == 0  # All passed
    
    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        gates = [
            GateResult("Lint (flake8)", False, "E501 line too long"),
            GateResult("Static types (mypy)", True, ""),
            GateResult("Security (bandit)", True, ""),
            GateResult("Coverage", False, "75% < 80%")
        ]
        
        exit_code = summarize(gates)
        assert exit_code == 1  # Some failed
    
    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        gates = [
            GateResult("Lint (flake8)", False, "Multiple errors"),
            GateResult("Static types (mypy)", False, "Type errors"),
            GateResult("Security (bandit)", False, "Security issues"),
            GateResult("Coverage", False, "Low coverage")
        ]
        
        exit_code = summarize(gates)
        assert exit_code == 1  # All failed
    
    def test_summarize_empty_gates(self):
        """Test summarize with no gates."""
        gates = []
        
        exit_code = summarize(gates)
        assert exit_code == 0  # Empty gates should pass


class TestDiffParser:
    """Test diff_parser module functions."""
    
    def test_get_file_extensions(self):
        """Test get_file_extensions function."""
        files = ["file1.py", "file2.js", "file3.txt", "file4.py"]
        extensions = get_file_extensions(files)
        assert extensions == ["js", "py", "txt"]  # Unique, sorted, no dots
    
    def test_get_file_extensions_empty(self):
        """Test get_file_extensions with empty list."""
        extensions = get_file_extensions([])
        assert extensions == []
    
    def test_get_file_extensions_no_extension(self):
        """Test get_file_extensions with files without extensions."""
        files = ["README", "Makefile", "Dockerfile"]
        extensions = get_file_extensions(files)
        assert extensions == []  # No extensions found
    
    def test_filter_python_files(self):
        """Test filter_python_files function."""
        files = ["file1.py", "file2.js", "file3.py", "file4.txt"]
        python_files = filter_python_files(files)
        assert python_files == ["file1.py", "file3.py"]
    
    def test_filter_python_files_empty(self):
        """Test filter_python_files with empty list."""
        python_files = filter_python_files([])
        assert python_files == []
    
    def test_filter_python_files_no_python(self):
        """Test filter_python_files with no Python files."""
        files = ["file1.js", "file2.txt", "file3.md"]
        python_files = filter_python_files(files)
        assert python_files == []
    
    def test_changed_python_files_no_event(self):
        """Test changed_python_files without event file."""
        with patch('src.ai_guard.diff_parser._git_ls_files') as mock_ls_files:
            mock_ls_files.return_value = ["file1.py", "file2.js", "file3.py"]
            
            files = changed_python_files()
            assert files == ["file1.py", "file3.py"]
    
    def test_changed_python_files_with_event(self):
        """Test changed_python_files with event file."""
        with patch('src.ai_guard.diff_parser._get_base_head_from_event') as mock_get_base_head:
            mock_get_base_head.return_value = ("main", "feature")
            with patch('src.ai_guard.diff_parser._git_changed_files') as mock_changed:
                mock_changed.return_value = ["file1.py", "file2.js", "file3.py"]
                
                files = changed_python_files("event.json")
                assert files == ["file1.py", "file3.py"]
    
    def test_changed_python_files_error(self):
        """Test changed_python_files with error."""
        with patch('src.ai_guard.diff_parser._git_ls_files') as mock_ls_files:
            mock_ls_files.side_effect = Exception("Git error")
            
            files = changed_python_files()
            assert files == []
