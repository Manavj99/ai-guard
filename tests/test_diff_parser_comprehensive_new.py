"""Comprehensive tests for diff_parser.py to achieve high coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from pathlib import Path

from src.ai_guard.diff_parser import changed_python_files


class TestChangedPythonFiles:
    """Test changed_python_files function."""
    
    @patch('src.ai_guard.diff_parser._git_ls_files', return_value=['src/__init__.py', 'src/ai_guard/__init__.py', 'src/ai_guard/config.py'])
    def test_changed_python_files_none(self, mock_git_ls_files):
        """Test with None input."""
        result = changed_python_files(None)
        # When None is passed, it falls back to getting all tracked Python files
        assert result == ['src/__init__.py', 'src/ai_guard/__init__.py', 'src/ai_guard/config.py']
    
    def test_changed_python_files_empty_list(self):
        """Test with empty list."""
        result = changed_python_files([])
        assert result == []
    
    def test_changed_python_files_no_python_files(self):
        """Test with no Python files."""
        files = ["test.txt", "README.md", "config.json"]
        result = changed_python_files(files)
        assert result == []
    
    def test_changed_python_files_python_files(self):
        """Test with Python files."""
        files = ["test.py", "src/module.py", "test.txt"]
        result = changed_python_files(files)
        assert result == ["test.py", "src/module.py"]
    
    def test_changed_python_files_python_files_with_paths(self):
        """Test with Python files including paths."""
        files = [
            "src/ai_guard/analyzer.py",
            "tests/test_analyzer.py",
            "README.md",
            "src/utils/helper.py"
        ]
        result = changed_python_files(files)
        expected = [
            "src/ai_guard/analyzer.py",
            "tests/test_analyzer.py",
            "src/utils/helper.py"
        ]
        assert result == expected
    
    def test_changed_python_files_case_sensitivity(self):
        """Test case sensitivity."""
        files = ["test.PY", "Test.Py", "TEST.py", "test.py"]
        result = changed_python_files(files)
        # Only .py files are recognized (case sensitive)
        assert result == ["TEST.py", "test.py"]
    
    def test_changed_python_files_duplicates(self):
        """Test with duplicate files."""
        files = ["test.py", "test.py", "module.py"]
        result = changed_python_files(files)
        assert result == ["test.py", "test.py", "module.py"]
    
    def test_changed_python_files_mixed_extensions(self):
        """Test with mixed file extensions."""
        files = [
            "test.py",
            "test.pyc",
            "test.pyo",
            "test.pyi",
            "test.pyw",
            "test.txt"
        ]
        result = changed_python_files(files)
        # Only .py files are recognized
        expected = ["test.py"]
        assert result == expected
    
    def test_changed_python_files_nested_directories(self):
        """Test with nested directory structures."""
        files = [
            "src/package/__init__.py",
            "src/package/module.py",
            "tests/test_package.py",
            "docs/README.md",
            "src/package/subpackage/helper.py"
        ]
        result = changed_python_files(files)
        expected = [
            "src/package/__init__.py",
            "src/package/module.py",
            "tests/test_package.py",
            "src/package/subpackage/helper.py"
        ]
        assert result == expected
    
    def test_changed_python_files_absolute_paths(self):
        """Test with absolute paths."""
        files = [
            "/home/user/project/test.py",
            "/home/user/project/src/module.py",
            "/home/user/project/README.md"
        ]
        result = changed_python_files(files)
        expected = [
            "/home/user/project/test.py",
            "/home/user/project/src/module.py"
        ]
        assert result == expected
    
    def test_changed_python_files_relative_paths(self):
        """Test with relative paths."""
        files = [
            "./test.py",
            "../module.py",
            "src/../test.py",
            "README.md"
        ]
        result = changed_python_files(files)
        expected = ["./test.py", "../module.py", "src/../test.py"]
        assert result == expected
    
    def test_changed_python_files_special_characters(self):
        """Test with special characters in filenames."""
        files = [
            "test-file.py",
            "test_file.py",
            "test.file.py",
            "test123.py",
            "test-file.txt"
        ]
        result = changed_python_files(files)
        expected = ["test-file.py", "test_file.py", "test.file.py", "test123.py"]
        assert result == expected
    
    def test_changed_python_files_unicode_names(self):
        """Test with unicode filenames."""
        files = [
            "测试.py",
            "тест.py",
            "test.py",
            "README.md"
        ]
        result = changed_python_files(files)
        expected = ["测试.py", "тест.py", "test.py"]
        assert result == expected
    
    def test_changed_python_files_empty_strings(self):
        """Test with empty strings."""
        files = ["", "test.py", "", "module.py"]
        result = changed_python_files(files)
        assert result == ["test.py", "module.py"]
    
    def test_changed_python_files_none_values(self):
        """Test with None values in list."""
        files = [None, "test.py", None, "module.py"]
        result = changed_python_files(files)
        assert result == ["test.py", "module.py"]
    
    def test_changed_python_files_large_list(self):
        """Test with large list of files."""
        files = []
        for i in range(100):
            if i % 3 == 0:
                files.append(f"test{i}.py")
            else:
                files.append(f"file{i}.txt")
        
        result = changed_python_files(files)
        expected = [f"test{i}.py" for i in range(0, 100, 3)]
        assert result == expected
    
    def test_changed_python_files_complex_structure(self):
        """Test with complex directory structure."""
        files = [
            "src/ai_guard/__init__.py",
            "src/ai_guard/analyzer.py",
            "src/ai_guard/config.py",
            "src/ai_guard/utils/__init__.py",
            "src/ai_guard/utils/error_formatter.py",
            "tests/conftest.py",
            "tests/test_analyzer.py",
            "tests/test_config.py",
            "docs/README.md",
            "pyproject.toml",
            "requirements.txt"
        ]
        result = changed_python_files(files)
        expected = [
            "src/ai_guard/__init__.py",
            "src/ai_guard/analyzer.py",
            "src/ai_guard/config.py",
            "src/ai_guard/utils/__init__.py",
            "src/ai_guard/utils/error_formatter.py",
            "tests/conftest.py",
            "tests/test_analyzer.py",
            "tests/test_config.py"
        ]
        assert result == expected
    
    def test_changed_python_files_edge_cases(self):
        """Test edge cases."""
        # Test with just .py extension
        files = [".py"]
        result = changed_python_files(files)
        assert result == [".py"]
        
        # Test with files starting with dot
        files = [".test.py", ".hidden.py"]
        result = changed_python_files(files)
        assert result == [".test.py", ".hidden.py"]
        
        # Test with very long filenames
        long_name = "a" * 200 + ".py"
        files = [long_name, "test.py"]
        result = changed_python_files(files)
        assert result == [long_name, "test.py"]
