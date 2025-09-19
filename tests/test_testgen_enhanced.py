"""Enhanced tests for testgen module to improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
from src.ai_guard.generators.testgen import (
    generate_speculative_tests,
    main
)


class TestGenerateSpeculativeTests:
    """Test generate_speculative_tests function."""

    def test_generate_speculative_tests_empty_list(self):
        """Test with empty list."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_single_file(self):
        """Test with single file."""
        files = ["test.py"]
        result = generate_speculative_tests(files)
        
        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# Generated for the following changed files:" in result
        assert "# - test.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result
        assert "assert True" in result

    def test_generate_speculative_tests_multiple_files(self):
        """Test with multiple files."""
        files = ["test.py", "script.py", "module.py"]
        result = generate_speculative_tests(files)
        
        assert "# - test.py" in result
        assert "# - script.py" in result
        assert "# - module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_content_structure(self):
        """Test content structure."""
        files = ["test.py"]
        result = generate_speculative_tests(files)
        
        lines = result.split('\n')
        
        # Check that all expected sections are present
        assert any("# Auto-generated speculative tests (MVP)" in line for line in lines)
        assert any("# Generated for the following changed files:" in line for line in lines)
        assert any("# - test.py" in line for line in lines)
        assert any("import pytest" in line for line in lines)
        assert any("def test_generated_imports():" in line for line in lines)
        assert any('"""Test that all changed modules can be imported."""' in line for line in lines)
        assert any("assert True" in line for line in lines)
        assert any("def test_generated_smoke():" in line for line in lines)
        assert any('"""Basic smoke test for changed code."""' in line for line in lines)

    def test_generate_speculative_tests_empty_strings(self):
        """Test with empty strings in file list."""
        files = ["", "test.py", ""]
        result = generate_speculative_tests(files)
        
        assert "# - test.py" in result
        assert result.count("# - ") == 3  # All files are included, even empty ones

    def test_generate_speculative_tests_none_values(self):
        """Test with None values in file list."""
        files = [None, "test.py", None]
        result = generate_speculative_tests(files)
        
        assert "# - test.py" in result
        assert result.count("# - ") == 3  # All files are included, even None ones


class TestMain:
    """Test main function."""

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_main_with_changed_files(self, mock_mkdir, mock_open_func, mock_changed_files):
        """Test main with changed files."""
        mock_changed_files.return_value = ["test.py", "script.py"]
        
        # Mock argparse
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(
                event="event.json",
                output="tests/unit/test_generated.py"
            )
            
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                main()
                
                # Verify changed_python_files was called
                mock_changed_files.assert_called_once_with("event.json")
                
                # Verify file was written
                mock_open_func.assert_called_once()
                
                # Verify print statements
                assert mock_print.call_count >= 2
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("Generated speculative tests for 2 files" in call for call in print_calls)
                assert any("Output: tests/unit/test_generated.py" in call for call in print_calls)

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('builtins.print')
    def test_main_no_changed_files(self, mock_print, mock_changed_files):
        """Test main with no changed files."""
        mock_changed_files.return_value = []
        
        # Mock argparse
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(
                event="event.json",
                output="tests/unit/test_generated.py"
            )
            
            main()
            
            # Verify changed_python_files was called
            mock_changed_files.assert_called_once_with("event.json")
            
            # Verify print statement
            mock_print.assert_called_with("[testgen] No Python files changed, skipping test generation")

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_main_default_output(self, mock_mkdir, mock_open_func, mock_changed_files):
        """Test main with default output path."""
        mock_changed_files.return_value = ["test.py"]
        
        # Mock argparse with default output
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(
                event=None,
                output="tests/unit/test_generated.py"  # Default value
            )
            
            with patch('builtins.print'):
                main()
                
                # Verify changed_python_files was called with None
                mock_changed_files.assert_called_once_with(None)
                
                # Verify file was written
                mock_open_func.assert_called_once()

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_main_custom_output(self, mock_mkdir, mock_open_func, mock_changed_files):
        """Test main with custom output path."""
        mock_changed_files.return_value = ["test.py"]
        
        # Mock argparse with custom output
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(
                event="event.json",
                output="custom/path/test_generated.py"
            )
            
            with patch('builtins.print') as mock_print:
                main()
                
                # Verify changed_python_files was called
                mock_changed_files.assert_called_once_with("event.json")
                
                # Verify file was written to custom path
                mock_open_func.assert_called_once()
                
                # Verify print statements include custom path
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("custom/path/test_generated.py" in call for call in print_calls)

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_main_file_content_written(self, mock_mkdir, mock_open_func, mock_changed_files):
        """Test that correct content is written to file."""
        mock_changed_files.return_value = ["test.py", "script.py"]
        
        # Mock argparse
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(
                event="event.json",
                output="tests/unit/test_generated.py"
            )
            
            with patch('builtins.print'):
                main()
                
                # Get the content that was written
                mock_open_func.assert_called_once()
                written_content = mock_open_func().write.call_args[0][0]
                
                # Verify content structure
                assert "# Auto-generated speculative tests (MVP)" in written_content
                assert "# Generated for the following changed files:" in written_content
                assert "# - test.py" in written_content
                assert "# - script.py" in written_content
                assert "import pytest" in written_content
                assert "def test_generated_imports():" in written_content
                assert "def test_generated_smoke():" in written_content
                assert "assert True" in written_content

    @patch('src.ai_guard.generators.testgen.changed_python_files')
    @patch('pathlib.Path.mkdir')
    def test_main_directory_creation(self, mock_mkdir, mock_changed_files):
        """Test that output directory is created."""
        mock_changed_files.return_value = ["test.py"]
        
        # Mock argparse
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(
                event="event.json",
                output="tests/unit/test_generated.py"
            )
            
            with patch('builtins.open', new_callable=mock_open), \
                 patch('builtins.print'):
                main()
                
                # Verify directory creation
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_main_argument_parser_setup(self):
        """Test that argument parser is set up correctly."""
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Mock the parse_args to return our test args
            mock_parser.parse_args.return_value = MagicMock(
                event="event.json",
                output="tests/unit/test_generated.py"
            )
            
            with patch('src.ai_guard.generators.testgen.changed_python_files') as mock_changed_files, \
                 patch('builtins.open', new_callable=mock_open), \
                 patch('pathlib.Path.mkdir'), \
                 patch('builtins.print'):
                
                mock_changed_files.return_value = ["test.py"]
                main()
                
                # Verify parser was created
                mock_parser_class.assert_called_once_with(
                    description="Generate speculative tests for changed code"
                )
                
                # Verify arguments were added
                assert mock_parser.add_argument.call_count == 2
                
                # Check first argument (event)
                first_call = mock_parser.add_argument.call_args_list[0]
                assert first_call[0][0] == "--event"
                assert first_call[1]["help"] == "Path to GitHub event JSON file"
                
                # Check second argument (output)
                second_call = mock_parser.add_argument.call_args_list[1]
                assert second_call[0][0] == "--output"
                assert second_call[1]["default"] == "tests/unit/test_generated.py"
                assert second_call[1]["help"] == "Output path for generated tests"
