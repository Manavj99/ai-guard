"""Comprehensive tests for testgen module."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from src.ai_guard.generators.testgen import (
    generate_speculative_tests,
    main,
)


class TestGenerateSpeculativeTests:
    """Test generate_speculative_tests function."""

    def test_generate_speculative_tests_empty_list(self):
        """Test with empty file list."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_single_file(self):
        """Test with single file."""
        files = ["test_module.py"]
        result = generate_speculative_tests(files)
        
        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# Generated for the following changed files:" in result
        assert "# - test_module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_multiple_files(self):
        """Test with multiple files."""
        files = ["module1.py", "module2.py", "module3.py"]
        result = generate_speculative_tests(files)
        
        assert "# - module1.py" in result
        assert "# - module2.py" in result
        assert "# - module3.py" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_mixed_files(self):
        """Test with mixed file types."""
        files = ["module.py", "script.js", "style.css", "test.py"]
        result = generate_speculative_tests(files)
        
        # Should include all files in the comment
        assert "# - module.py" in result
        assert "# - script.js" in result
        assert "# - style.css" in result
        assert "# - test.py" in result

    def test_generate_speculative_tests_special_characters(self):
        """Test with files containing special characters."""
        files = ["module-with-dashes.py", "module_with_underscores.py", "module.with.dots.py"]
        result = generate_speculative_tests(files)
        
        assert "# - module-with-dashes.py" in result
        assert "# - module_with_underscores.py" in result
        assert "# - module.with.dots.py" in result

    def test_generate_speculative_tests_structure(self):
        """Test the structure of generated content."""
        files = ["test_module.py"]
        result = generate_speculative_tests(files)
        
        lines = result.split('\n')
        
        # Check that the structure is correct
        assert lines[0] == "# Auto-generated speculative tests (MVP)"
        assert lines[1] == "# Generated for the following changed files:"
        assert lines[2] == ""
        assert lines[3] == "# - test_module.py"
        assert lines[4] == ""
        assert lines[5] == "import pytest"
        assert lines[6] == ""
        assert lines[7] == "def test_generated_imports():"
        assert lines[8] == '    """Test that all changed modules can be imported."""'
        assert lines[9] == "    assert True"
        assert lines[10] == ""
        assert lines[11] == "def test_generated_smoke():"
        assert lines[12] == '    """Basic smoke test for changed code."""'
        assert lines[13] == "    assert True"
        assert lines[14] == ""

    def test_generate_speculative_tests_unicode_files(self):
        """Test with unicode file names."""
        files = ["módulo.py", "файл.py", "文件.py"]
        result = generate_speculative_tests(files)
        
        assert "# - módulo.py" in result
        assert "# - файл.py" in result
        assert "# - 文件.py" in result


class TestMain:
    """Test main function."""

    def test_main_no_changed_files(self):
        """Test main with no changed files."""
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=[]), \
             patch("builtins.print") as mock_print:
            main()
            
            # Should print no files message
            mock_print.assert_called_with("[testgen] No Python files changed, skipping test generation")

    def test_main_with_changed_files(self):
        """Test main with changed files."""
        files = ["module1.py", "module2.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print") as mock_print:
            
            # Mock argparse to avoid sys.argv issues
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="tests/unit/test_generated.py"
            )):
                main()
            
            # Should write to file
            mock_file.assert_called_once()
            
            # Should print success messages
            assert any("Generated speculative tests for 2 files" in str(call) for call in mock_print.call_args_list)
            assert any("Output: tests/unit/test_generated.py" in str(call) for call in mock_print.call_args_list)

    def test_main_custom_output_path(self):
        """Test main with custom output path."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print"):
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="custom/path/test_generated.py"
            )):
                main()
            
            # Should write to custom path
            mock_file.assert_called_once_with("custom/path/test_generated.py", "w", encoding="utf-8")

    def test_main_default_output_path(self):
        """Test main with default output path."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print"):
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event=None,
                output="tests/unit/test_generated.py"
            )):
                main()
            
            # Should write to default path
            mock_file.assert_called_once_with("tests/unit/test_generated.py", "w", encoding="utf-8")

    def test_main_creates_directory(self):
        """Test that main creates output directory."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", mock_open()), \
             patch("pathlib.Path.mkdir") as mock_mkdir, \
             patch("builtins.print"):
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="custom/path/test_generated.py"
            )):
                main()
            
            # Should create parent directory
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_main_writes_correct_content(self):
        """Test that main writes the correct content."""
        files = ["module1.py", "module2.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print"):
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="tests/unit/test_generated.py"
            )):
                main()
            
            # Get the written content
            written_content = mock_file().write.call_args[0][0]
            
            assert "# Auto-generated speculative tests (MVP)" in written_content
            assert "# - module1.py" in written_content
            assert "# - module2.py" in written_content
            assert "import pytest" in written_content
            assert "def test_generated_imports():" in written_content
            assert "def test_generated_smoke():" in written_content

    def test_main_with_event_path(self):
        """Test main with event path passed to changed_python_files."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files") as mock_changed_files, \
             patch("builtins.open", mock_open()), \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print"):
            
            mock_changed_files.return_value = files
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="tests/unit/test_generated.py"
            )):
                main()
            
            # Should call changed_python_files with event path
            mock_changed_files.assert_called_once_with("event.json")

    def test_main_without_event_path(self):
        """Test main without event path."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files") as mock_changed_files, \
             patch("builtins.open", mock_open()), \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print"):
            
            mock_changed_files.return_value = files
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event=None,
                output="tests/unit/test_generated.py"
            )):
                main()
            
            # Should call changed_python_files with None
            mock_changed_files.assert_called_once_with(None)

    def test_main_file_write_error(self):
        """Test main when file write fails."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", side_effect=IOError("Write failed")), \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.print"):
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="tests/unit/test_generated.py"
            )):
                # Should not raise exception, just fail silently
                main()

    def test_main_directory_creation_error(self):
        """Test main when directory creation fails."""
        files = ["module.py"]
        
        with patch("src.ai_guard.generators.testgen.changed_python_files", return_value=files), \
             patch("builtins.open", mock_open()), \
             patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")), \
             patch("builtins.print"):
            
            with patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
                event="event.json",
                output="tests/unit/test_generated.py"
            )):
                # Should not raise exception, just fail silently
                main()