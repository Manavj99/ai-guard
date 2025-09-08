"""Tests for testgen module."""

from unittest.mock import patch, mock_open

from ai_guard.generators.testgen import generate_speculative_tests, main


class TestGenerateSpeculativeTests:
    """Test speculative test generation."""

    def test_generate_speculative_tests_empty(self):
        """Test generating tests with empty file list."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_single_file(self):
        """Test generating tests for a single file."""
        changed_files = ["src/module.py"]
        result = generate_speculative_tests(changed_files)

        assert "# Auto-generated speculative tests (MVP)" in result
        assert "# Generated for the following changed files:" in result
        assert "# - src/module.py" in result
        assert "import pytest" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_multiple_files(self):
        """Test generating tests for multiple files."""
        changed_files = ["src/module1.py", "src/module2.py", "src/module3.py"]
        result = generate_speculative_tests(changed_files)

        assert "# - src/module1.py" in result
        assert "# - src/module2.py" in result
        assert "# - src/module3.py" in result
        assert "def test_generated_imports():" in result
        assert "def test_generated_smoke():" in result

    def test_generate_speculative_tests_whitespace_handling(self):
        """Test handling of whitespace in file paths."""
        changed_files = [
            "  src/module.py  ",
            "\tsrc/module2.py\t",
            "\n  src/module3.py  \n",
        ]
        result = generate_speculative_tests(changed_files)

        # Should preserve the original whitespace in comments
        assert "# -   src/module.py  " in result
        assert "# - \tsrc/module2.py\t" in result  # Note the space after the dash
        # The newline is preserved in the output
        assert "# - \n  src/module3.py  \n" in result


class TestMainFunction:
    """Test main function functionality."""

    @patch("ai_guard.generators.testgen.changed_python_files")
    @patch("builtins.print")
    def test_main_with_changed_files(self, mock_print, mock_changed_files):
        """Test main function with changed files."""
        mock_changed_files.return_value = ["src/module.py", "src/another.py"]

        with patch("sys.argv", ["testgen.py"]):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("pathlib.Path.mkdir"):
                    main()

        # Should call changed_python_files
        mock_changed_files.assert_called_once()

        # Should print the generated tests info
        mock_print.assert_called()
        printed_content = str(mock_print.call_args_list)
        assert "Generated speculative tests for 2 files" in printed_content

    @patch("ai_guard.generators.testgen.changed_python_files")
    @patch("builtins.print")
    def test_main_without_changed_files(self, mock_print, mock_changed_files):
        """Test main function without changed files."""
        mock_changed_files.return_value = []

        with patch("sys.argv", ["testgen.py"]):
            main()

        # Should call changed_python_files
        mock_changed_files.assert_called_once()

        # Should print no files message
        mock_print.assert_called_with(
            "[testgen] No Python files changed, skipping test generation"
        )

    def test_main_writes_to_file(self):
        """Test that main function writes generated tests to file."""
        with patch(
            "ai_guard.generators.testgen.changed_python_files"
        ) as mock_changed_files:
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                with patch("builtins.open", mock_open()) as mock_file:
                    mock_changed_files.return_value = ["src/test_module.py"]

                    with patch(
                        "sys.argv", ["testgen.py", "--output", "custom_output.py"]
                    ):
                        main()

                    # Should create output directory
                    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

                    # Should write to file (Path object gets converted to string)
                    mock_file.assert_called()
                    call_args = mock_file.call_args
                    # Handle Windows path separators
                    path_str = str(call_args[0][0]).replace("\\", "/")
                    assert path_str.endswith("custom_output.py")
                    assert call_args[0][1] == "w"
                    assert call_args[1]["encoding"] == "utf-8"

                    # Should write test content
                    written_content = (
                        mock_file.return_value.__enter__.return_value.write.call_args[
                            0
                        ][0]
                    )
                    assert "# Auto-generated speculative tests (MVP)" in written_content
                    assert "# - src/test_module.py" in written_content

    @patch("ai_guard.generators.testgen.changed_python_files")
    def test_main_with_custom_output_path(self, mock_changed_files):
        """Test main function with custom output path."""
        mock_changed_files.return_value = ["src/module.py"]

        with patch(
            "sys.argv", ["testgen.py", "--output", "tests/custom/test_generated.py"]
        ):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("pathlib.Path.mkdir"):
                    main()

        # Should write to custom path (Path object gets converted to string)
        mock_file.assert_called()
        call_args = mock_file.call_args
        # Handle Windows path separators
        path_str = str(call_args[0][0]).replace("\\", "/")
        assert path_str.endswith("tests/custom/test_generated.py")
        assert call_args[0][1] == "w"
        assert call_args[1]["encoding"] == "utf-8"

    @patch("ai_guard.generators.testgen.changed_python_files")
    def test_main_with_event_file(self, mock_changed_files):
        """Test main function with event file argument."""
        mock_changed_files.return_value = ["src/module.py"]

        with patch("sys.argv", ["testgen.py", "--event", "event.json"]):
            with patch("builtins.open", mock_open()):
                with patch("pathlib.Path.mkdir"):
                    main()

        # Should pass event file to changed_python_files
        mock_changed_files.assert_called_once_with("event.json")
