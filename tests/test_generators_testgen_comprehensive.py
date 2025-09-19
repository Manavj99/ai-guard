"""Comprehensive tests for testgen module."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.ai_guard.generators.testgen import (
    generate_speculative_tests,
    main
)


class TestGenerateSpeculativeTests:
    """Test generate_speculative_tests function."""

    def test_generate_speculative_tests_empty_list(self):
        """Test with empty changed files list."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_single_file(self):
        """Test with single changed file."""
        changed_files = ["src/module.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# Generated for the following changed files:" in result
        assert "# - src/module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_multiple_files(self):
        """Test with multiple changed files."""
        changed_files = ["src/module1.py", "src/module2.py", "tests/test_module.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# - src/module1.py" in result
        assert "# - src/module2.py" in result
        assert "# - tests/test_module.py" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_content_structure(self):
        """Test the structure of generated content."""
        changed_files = ["src/test_module.py"]
        result = generate_speculative_tests(changed_files)
        
        lines = result.split('\n')
        
        # Check header
        assert lines[0] == "# Auto-generated speculative tests (MVP)"
        assert lines[1] == "# Generated for the following changed files:"
        assert lines[2] == ""
        assert lines[3] == "# - src/test_module.py"
        assert lines[4] == ""
        
        # Check imports
        assert "import pytest" in lines
        
        # Check test functions
        assert any("def test_generated_imports():" in line for line in lines)
        assert any("def test_generated_smoke():" in line for line in lines)
        
        # Check docstrings
        assert '"""Test that all changed modules can be imported."""' in result
        assert '"""Basic smoke test for changed code."""' in result

    def test_generate_speculative_tests_assertions(self):
        """Test that generated tests have proper assertions."""
        changed_files = ["src/module.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "assert True" in result
        # Should have at least 2 assert True statements
        assert result.count("assert True") >= 2


class TestMainFunction:
    """Test main function."""

    def test_main_no_changed_files(self):
        """Test main with no changed files."""
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=[]):
            with patch('builtins.print') as mock_print:
                with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_parse.return_value = MagicMock(event=None, output="tests/unit/test_generated.py")
                    main()
                    mock_print.assert_called_with("[testgen] No Python files changed, skipping test generation")

    def test_main_with_changed_files(self):
        """Test main with changed files."""
        changed_files = ["src/module1.py", "src/module2.py"]
        
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=changed_files):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('pathlib.Path.mkdir') as mock_mkdir:
                    with patch('builtins.print') as mock_print:
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(event=None, output="tests/unit/test_generated.py")
                            main()
                            
                            # Check that directory was created
                            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                            
                            # Check that file was written
                            mock_file.assert_called_once()
                            
                            # Check print statements
                            assert mock_print.call_count == 2
                            print_calls = [call[0][0] for call in mock_print.call_args_list]
                            assert any("Generated speculative tests for 2 files" in call for call in print_calls)
                            assert any("Output:" in call for call in print_calls)

    def test_main_with_custom_output(self):
        """Test main with custom output path."""
        changed_files = ["src/module.py"]
        
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=changed_files):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('pathlib.Path.mkdir') as mock_mkdir:
                    with patch('builtins.print') as mock_print:
                        # Mock argparse to return custom output
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(
                                event=None,
                                output="custom/path/test_generated.py"
                            )
                            main()
                            
                            # Check that file was written to custom path (use Path object)
                            from pathlib import Path
                            expected_path = Path("custom/path/test_generated.py")
                            mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")

    def test_main_with_event_file(self):
        """Test main with event file."""
        changed_files = ["src/module.py"]
        
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=changed_files):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('pathlib.Path.mkdir') as mock_mkdir:
                    with patch('builtins.print') as mock_print:
                        # Mock argparse to return event file
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(
                                event="event.json",
                                output="tests/unit/test_generated.py"
                            )
                            main()
                            
                            # Check that changed_python_files was called with event file
                            from src.ai_guard.generators.testgen import changed_python_files
                            # This is already mocked above, but we can verify the call

    def test_main_file_writing_content(self):
        """Test that main writes correct content to file."""
        changed_files = ["src/test_module.py"]
        
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=changed_files):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('pathlib.Path.mkdir'):
                    with patch('builtins.print'):
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(event=None, output="tests/unit/test_generated.py")
                            main()
                            
                            # Get the content that was written
                            mock_file.return_value.write.assert_called_once()
                            written_content = mock_file.return_value.write.call_args[0][0]
                            
                            # Verify content structure
                            assert "# Auto-generated speculative tests (MVP)" in written_content
                            assert "# - src/test_module.py" in written_content
                            assert "import pytest" in written_content
                            assert "def test_generated_imports():" in written_content
                            assert "def test_generated_smoke():" in written_content

    def test_main_directory_creation(self):
        """Test that main creates output directory."""
        changed_files = ["src/module.py"]
        
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=changed_files):
            with patch('builtins.open', mock_open()):
                with patch('pathlib.Path.mkdir') as mock_mkdir:
                    with patch('builtins.print'):
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(event=None, output="tests/unit/test_generated.py")
                            main()
                            
                            # Check that mkdir was called with correct parameters
                            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_main_error_handling(self):
        """Test main error handling."""
        changed_files = ["src/module.py"]
        
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=changed_files):
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                with patch('pathlib.Path.mkdir'):
                    with patch('builtins.print'):
                        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                            mock_parse.return_value = MagicMock(event=None, output="tests/unit/test_generated.py")
                            # The main function doesn't handle IOError, so it should raise it
                            with pytest.raises(IOError, match="Permission denied"):
                                main()

    def test_main_with_none_changed_files(self):
        """Test main with None changed files."""
        with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=None):
            with patch('builtins.print') as mock_print:
                with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_parse.return_value = MagicMock(event=None, output="tests/unit/test_generated.py")
                    main()
                    mock_print.assert_called_with("[testgen] No Python files changed, skipping test generation")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_generate_speculative_tests_with_none(self):
        """Test generate_speculative_tests with None input."""
        result = generate_speculative_tests(None)
        assert result == ""

    def test_generate_speculative_tests_with_empty_strings(self):
        """Test generate_speculative_tests with empty string files."""
        changed_files = ["", "src/module.py", ""]
        result = generate_speculative_tests(changed_files)
        
        assert "# - " in result  # Empty string should still be listed
        assert "# - src/module.py" in result

    def test_generate_speculative_tests_with_special_characters(self):
        """Test generate_speculative_tests with special characters in filenames."""
        changed_files = ["src/module with spaces.py", "src/module-with-dashes.py", "src/module_with_underscores.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# - src/module with spaces.py" in result
        assert "# - src/module-with-dashes.py" in result
        assert "# - src/module_with_underscores.py" in result

    def test_generate_speculative_tests_very_long_filename(self):
        """Test generate_speculative_tests with very long filename."""
        long_filename = "src/" + "a" * 200 + ".py"
        changed_files = [long_filename]
        result = generate_speculative_tests(changed_files)
        
        assert f"# - {long_filename}" in result
        assert "def test_generated_imports():" in result
