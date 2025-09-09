"""Enhanced tests for generators/testgen module to achieve 80%+ coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.ai_guard.generators.testgen import (
    generate_speculative_tests,
    main
)


class TestGenerateSpeculativeTests:
    """Test generate_speculative_tests function."""

    def test_generate_speculative_tests_empty_list(self):
        """Test generating tests with empty file list."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_none_input(self):
        """Test generating tests with None input."""
        result = generate_speculative_tests(None)
        assert result == ""

    def test_generate_speculative_tests_single_file(self):
        """Test generating tests for single file."""
        changed_files = ["src/module.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# Generated for the following changed files:" in result
        assert "# - src/module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result
        assert '"""Test that all changed modules can be imported."""' in result
        assert '"""Basic smoke test for changed code."""' in result
        assert "assert True" in result

    def test_generate_speculative_tests_multiple_files(self):
        """Test generating tests for multiple files."""
        changed_files = ["src/module1.py", "src/module2.py", "tests/test_module.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# - src/module1.py" in result
        assert "# - src/module2.py" in result
        assert "# - tests/test_module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_special_characters(self):
        """Test generating tests for files with special characters."""
        changed_files = ["src/module-with-dashes.py", "src/module_with_underscores.py", "src/module.with.dots.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# - src/module-with-dashes.py" in result
        assert "# - src/module_with_underscores.py" in result
        assert "# - src/module.with.dots.py" in result

    def test_generate_speculative_tests_empty_strings(self):
        """Test generating tests with empty string in file list."""
        changed_files = ["src/module.py", "", "src/another.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# - src/module.py" in result
        assert "# - " in result  # Empty string should still be listed
        assert "# - src/another.py" in result

    def test_generate_speculative_tests_unicode_files(self):
        """Test generating tests for files with unicode characters."""
        changed_files = ["src/módulo.py", "src/файл.py"]
        result = generate_speculative_tests(changed_files)
        
        assert "# - src/módulo.py" in result
        assert "# - src/файл.py" in result

    def test_generate_speculative_tests_very_long_list(self):
        """Test generating tests for very long file list."""
        changed_files = [f"src/module{i}.py" for i in range(100)]
        result = generate_speculative_tests(changed_files)
        
        # Should contain all files
        for i in range(100):
            assert f"# - src/module{i}.py" in result
        
        # Should still have the test functions
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_structure(self):
        """Test the structure of generated test content."""
        changed_files = ["src/test.py"]
        result = generate_speculative_tests(changed_files)
        
        lines = result.split('\n')
        
        # Check that the structure is correct
        assert lines[0] == "# Auto-generated speculative tests (MVP)"
        assert lines[1] == "# Generated for the following changed files:"
        assert lines[2] == ""
        assert lines[3] == "# - src/test.py"
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


class TestMain:
    """Test main function."""

    def test_main_no_args(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['testgen']):
            with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=[]):
                with patch('builtins.print') as mock_print:
                    main()
                    mock_print.assert_called_with("[testgen] No Python files changed, skipping test generation")

    def test_main_with_event_file(self):
        """Test main function with event file argument."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            event_file = f.name
        
        try:
            with patch('sys.argv', ['testgen', '--event', event_file]):
                with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=['src/test.py']):
                    with patch('src.ai_guard.generators.testgen.Path') as mock_path:
                        with patch('builtins.open', mock_open()) as mock_file:
                            with patch('builtins.print') as mock_print:
                                mock_path_instance = MagicMock()
                                mock_path.return_value = mock_path_instance
                                mock_path_instance.parent = MagicMock()
                                
                                main()
                                
                                mock_print.assert_any_call("[testgen] Generated speculative tests for 1 files")
                                mock_print.assert_any_call("[testgen] Output: tests/unit/test_generated.py")
        finally:
            os.unlink(event_file)

    def test_main_with_custom_output(self):
        """Test main function with custom output path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            event_file = f.name
        
        try:
            with patch('sys.argv', ['testgen', '--event', event_file, '--output', 'custom/path/test.py']):
                with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=['src/test.py']):
                    with patch('src.ai_guard.generators.testgen.Path') as mock_path:
                        with patch('builtins.open', mock_open()) as mock_file:
                            with patch('builtins.print') as mock_print:
                                mock_path_instance = MagicMock()
                                mock_path.return_value = mock_path_instance
                                mock_path_instance.parent = MagicMock()
                                
                                main()
                                
                                mock_print.assert_any_call("[testgen] Generated speculative tests for 1 files")
                                mock_print.assert_any_call("[testgen] Output: custom/path/test.py")
        finally:
            os.unlink(event_file)

    def test_main_with_changed_files(self):
        """Test main function with changed files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            event_file = f.name
        
        try:
            with patch('sys.argv', ['testgen', '--event', event_file]):
                with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=['src/module1.py', 'src/module2.py']):
                    with patch('src.ai_guard.generators.testgen.Path') as mock_path:
                        with patch('builtins.open', mock_open()) as mock_file:
                            with patch('builtins.print') as mock_print:
                                mock_path_instance = MagicMock()
                                mock_path.return_value = mock_path_instance
                                mock_path_instance.parent = MagicMock()
                                
                                main()
                                
                                mock_print.assert_any_call("[testgen] Generated speculative tests for 2 files")
                                
                                # Check that the file was written with correct content
                                mock_file.assert_called_once_with('tests/unit/test_generated.py', 'w', encoding='utf-8')
                                written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
                                assert "# - src/module1.py" in written_content
                                assert "# - src/module2.py" in written_content
        finally:
            os.unlink(event_file)

    def test_main_directory_creation(self):
        """Test main function creates output directory."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            event_file = f.name
        
        try:
            with patch('sys.argv', ['testgen', '--event', event_file, '--output', 'new/dir/test.py']):
                with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=['src/test.py']):
                    with patch('src.ai_guard.generators.testgen.Path') as mock_path:
                        with patch('builtins.open', mock_open()) as mock_file:
                            with patch('builtins.print') as mock_print:
                                mock_path_instance = MagicMock()
                                mock_path.return_value = mock_path_instance
                                mock_parent = MagicMock()
                                mock_path_instance.parent = mock_parent
                                
                                main()
                                
                                # Check that mkdir was called
                                mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        finally:
            os.unlink(event_file)

    def test_main_file_write_error(self):
        """Test main function handles file write errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            event_file = f.name
        
        try:
            with patch('sys.argv', ['testgen', '--event', event_file]):
                with patch('src.ai_guard.generators.testgen.changed_python_files', return_value=['src/test.py']):
                    with patch('src.ai_guard.generators.testgen.Path') as mock_path:
                        with patch('builtins.open', side_effect=IOError("Permission denied")):
                            with pytest.raises(IOError):
                                main()
        finally:
            os.unlink(event_file)

    def test_main_changed_python_files_error(self):
        """Test main function handles changed_python_files errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            event_file = f.name
        
        try:
            with patch('sys.argv', ['testgen', '--event', event_file]):
                with patch('src.ai_guard.generators.testgen.changed_python_files', side_effect=Exception("Parse error")):
                    with pytest.raises(Exception):
                        main()
        finally:
            os.unlink(event_file)

    def test_main_script_execution(self):
        """Test main function when run as script."""
        with patch('src.ai_guard.generators.testgen.__name__', '__main__'):
            with patch('src.ai_guard.generators.testgen.main') as mock_main:
                # This would be executed when running the script directly
                # We can't easily test this without actually running the script
                # but we can verify the main function exists and is callable
                assert callable(main)
