"""Tests for test generation module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from src.ai_guard.generators.testgen import (
    generate_speculative_tests,
    main
)


class TestTestGen:
    """Test test generation functionality."""

    def test_generate_speculative_tests_empty(self):
        """Test test generation with no changed files."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_with_files(self):
        """Test test generation with changed files."""
        changed_files = ["src/ai_guard/analyzer.py", "src/ai_guard/config.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# - src/ai_guard/analyzer.py" in result
        assert "# - src/ai_guard/config.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_no_changed_files(self, mock_parse_args, mock_changed_files):
        """Test main function when no files have changed."""
        mock_parse_args.return_value = Mock(event=None, output="tests/unit/test_generated.py")
        mock_changed_files.return_value = []
        
        with patch('builtins.print') as mock_print:
            main()
            mock_print.assert_called_with("[testgen] No Python files changed, skipping test generation")

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    def test_main_with_changed_files(self, mock_mkdir, mock_open, mock_parse_args, mock_changed_files):
        """Test main function with changed files."""
        mock_parse_args.return_value = Mock(event=None, output="tests/unit/test_generated.py")
        mock_changed_files.return_value = ["src/ai_guard/analyzer.py"]
        
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify output - handle path separators
            mock_print.assert_any_call("[testgen] Generated speculative tests for 1 files")
            # Check that the output message contains the expected path (allowing for different separators)
            output_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("tests" in call and "test_generated.py" in call for call in output_calls)

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_custom_output_path(self, mock_parse_args, mock_changed_files):
        """Test main function with custom output path."""
        mock_parse_args.return_value = Mock(event=None, output="custom/path/test.py")
        mock_changed_files.return_value = ["src/ai_guard/config.py"]
        
        with patch('builtins.open'):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.print'):
                    main()

    def test_generated_test_content_structure(self):
        """Test that generated test content has proper structure."""
        changed_files = ["src/ai_guard/report.py"]
        content = generate_speculative_tests(changed_files)
        
        lines = content.split('\n')
        
        # Check header
        assert lines[0] == "# Auto-generated speculative tests (MVP)"
        assert lines[1] == "# Generated for the following changed files:"
        assert lines[3] == "# - src/ai_guard/report.py"
        
        # Check test functions
        assert "def test_generated_imports():" in content
        assert "def test_generated_smoke():" in content
        assert "assert True" in content
