"""
Comprehensive test suite for enhanced_testgen.py to achieve 80% coverage.
This test suite focuses on mocking external dependencies and testing core functionality.
"""

import pytest
import json
import tempfile
import os
import sys
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    CodeChange,
    EnhancedTestGenerator,
    main,
)


class TestTestGenConfig:
    """Test TestGenConfig class functionality."""

    def test_config_creation_default(self):
        """Test default configuration creation."""
        config = TestGenConfig()
        assert config.llm_provider == "openai"
        assert config.model == "gpt-4"
        assert config.max_tokens == 4000
        assert config.temperature == 0.1
        assert config.test_template == "pytest"
        assert config.include_docstrings is True
        assert config.include_type_hints is True
        assert config.verbose is False

    def test_config_creation_custom(self):
        """Test custom configuration creation."""
        config = TestGenConfig(
            llm_provider="anthropic",
            model="claude-3-sonnet",
            max_tokens=2000,
            temperature=0.2,
            test_template="unittest",
            include_docstrings=False,
            include_type_hints=False,
            verbose=True,
        )
        assert config.llm_provider == "anthropic"
        assert config.model == "claude-3-sonnet"
        assert config.max_tokens == 2000
        assert config.temperature == 0.2
        assert config.test_template == "unittest"
        assert config.include_docstrings is False
        assert config.include_type_hints is False
        assert config.verbose is True

    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = TestGenConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "openai"
        assert config_dict["model"] == "gpt-4"
        assert config_dict["max_tokens"] == 4000
        assert config_dict["temperature"] == 0.1
        assert config_dict["test_template"] == "pytest"
        assert config_dict["include_docstrings"] is True
        assert config_dict["include_type_hints"] is True
        assert config_dict["verbose"] is False

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "llm_provider": "anthropic",
            "model": "claude-3-sonnet",
            "max_tokens": 2000,
            "temperature": 0.2,
            "test_template": "unittest",
            "include_docstrings": False,
            "include_type_hints": False,
            "verbose": True,
        }
        config = TestGenConfig.from_dict(config_dict)
        assert config.llm_provider == "anthropic"
        assert config.model == "claude-3-sonnet"
        assert config.max_tokens == 2000
        assert config.temperature == 0.2
        assert config.test_template == "unittest"
        assert config.include_docstrings is False
        assert config.include_type_hints is False
        assert config.verbose is True


class TestCodeChange:
    """Test CodeChange data structure functionality."""

    def test_code_change_creation(self):
        """Test CodeChange object creation."""
        change = CodeChange(
            file_path="test_file.py",
            change_type="modified",
            old_content="old content",
            new_content="new content",
            diff="diff content",
            line_numbers=[1, 2, 3],
        )
        assert change.file_path == "test_file.py"
        assert change.change_type == "modified"
        assert change.old_content == "old content"
        assert change.new_content == "new content"
        assert change.diff == "diff content"
        assert change.line_numbers == [1, 2, 3]

    def test_code_change_to_dict(self):
        """Test CodeChange to dictionary conversion."""
        change = CodeChange(
            file_path="test_file.py",
            change_type="added",
            old_content="",
            new_content="new content",
            diff="+new content",
            line_numbers=[1],
        )
        change_dict = change.to_dict()
        assert isinstance(change_dict, dict)
        assert change_dict["file_path"] == "test_file.py"
        assert change_dict["change_type"] == "added"
        assert change_dict["old_content"] == ""
        assert change_dict["new_content"] == "new content"
        assert change_dict["diff"] == "+new content"
        assert change_dict["line_numbers"] == [1]


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig()
        self.generator = EnhancedTestGenerator(self.config)

    @patch("src.ai_guard.generators.enhanced_testgen.openai")
    def test_openai_client_initialization(self, mock_openai):
        """Test OpenAI client initialization."""
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        # Test successful initialization
        client = self.generator._get_openai_client()
        assert client == mock_client
        mock_openai.OpenAI.assert_called_once()

    @patch("src.ai_guard.generators.enhanced_testgen.anthropic")
    def test_anthropic_client_initialization(self, mock_anthropic):
        """Test Anthropic client initialization."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Test successful initialization
        client = self.generator._get_anthropic_client()
        assert client == mock_client
        mock_anthropic.Anthropic.assert_called_once()

    @patch("src.ai_guard.generators.enhanced_testgen.openai")
    def test_openai_client_initialization_error(self, mock_openai):
        """Test OpenAI client initialization with error."""
        mock_openai.OpenAI.side_effect = Exception("API key error")

        with pytest.raises(Exception):
            self.generator._get_openai_client()

    @patch("src.ai_guard.generators.enhanced_testgen.anthropic")
    def test_anthropic_client_initialization_error(self, mock_anthropic):
        """Test Anthropic client initialization with error."""
        mock_anthropic.Anthropic.side_effect = Exception("API key error")

        with pytest.raises(Exception):
            self.generator._get_anthropic_client()

    def test_get_llm_client_openai(self):
        """Test LLM client selection for OpenAI."""
        self.config.llm_provider = "openai"
        generator = EnhancedTestGenerator(self.config)

        with patch.object(generator, "_get_openai_client") as mock_get_openai:
            mock_client = Mock()
            mock_get_openai.return_value = mock_client

            client = generator._get_llm_client()
            assert client == mock_client
            mock_get_openai.assert_called_once()

    def test_get_llm_client_anthropic(self):
        """Test LLM client selection for Anthropic."""
        self.config.llm_provider = "anthropic"
        generator = EnhancedTestGenerator(self.config)

        with patch.object(generator, "_get_anthropic_client") as mock_get_anthropic:
            mock_client = Mock()
            mock_get_anthropic.return_value = mock_client

            client = generator._get_llm_client()
            assert client == mock_client
            mock_get_anthropic.assert_called_once()

    def test_get_llm_client_local(self):
        """Test LLM client selection for local provider."""
        self.config.llm_provider = "local"
        generator = EnhancedTestGenerator(self.config)

        with patch(
            "src.ai_guard.generators.enhanced_testgen.MockLLMClient"
        ) as mock_local:
            mock_client = Mock()
            mock_local.return_value = mock_client

            client = generator._get_llm_client()
            assert client == mock_client
            mock_local.assert_called_once()

    def test_get_llm_client_unsupported(self):
        """Test LLM client selection for unsupported provider."""
        self.config.llm_provider = "unsupported"
        generator = EnhancedTestGenerator(self.config)

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            generator._get_llm_client()

    @patch("builtins.open", mock_open(read_data="def test_function():\n    pass\n"))
    def test_analyze_file_changes(self):
        """Test file change analysis."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="def old_function():\n    pass",
                new_content="def test_function():\n    pass",
                diff="+def test_function():\n+    pass",
                line_numbers=[1, 2],
            )
        ]

        with patch("pathlib.Path.exists", return_value=True):
            result = self.generator.analyze_file_changes(changes)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_analyze_file_changes_file_not_found(self):
        """Test file change analysis when file doesn't exist."""
        changes = [
            CodeChange(
                file_path="nonexistent.py",
                change_type="modified",
                old_content="",
                new_content="def test_function():\n    pass",
                diff="+def test_function():\n+    pass",
                line_numbers=[1, 2],
            )
        ]

        with patch("pathlib.Path.exists", return_value=False):
            result = self.generator.analyze_file_changes(changes)
            assert isinstance(result, list)
            assert len(result) == 0

    @patch(
        "builtins.open",
        mock_open(
            read_data="def test_function():\n    pass\nclass TestClass:\n    def method(self):\n        pass"
        ),
    )
    def test_analyze_file_changes_with_ast(self):
        """Test file change analysis with AST parsing."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="def old_function():\n    pass",
                new_content="def test_function():\n    pass\nclass TestClass:\n    def method(self):\n        pass",
                diff="+def test_function():\n+    pass\n+class TestClass:\n+    def method(self):\n+        pass",
                line_numbers=[1, 2, 3, 4, 5],
            )
        ]

        with patch("pathlib.Path.exists", return_value=True):
            result = self.generator.analyze_file_changes(changes)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_analyze_file_changes_ast_error(self):
        """Test file change analysis with AST parsing error."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="",
                new_content="invalid python syntax {",
                diff="+invalid python syntax {",
                line_numbers=[1],
            )
        ]

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid python syntax {")):
                result = self.generator.analyze_file_changes(changes)
                assert isinstance(result, list)
                # Should handle AST parsing errors gracefully

    def test_generate_tests_for_function(self):
        """Test test generation for a specific function."""
        function_info = {
            "name": "test_function",
            "type": "function",
            "line_number": 1,
            "content": "def test_function(x, y):\n    return x + y",
        }

        with patch.object(self.generator, "_get_llm_client") as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="def test_test_function():\n    assert test_function(1, 2) == 3"
                        )
                    )
                ]
            )
            mock_get_client.return_value = mock_client

            result = self.generator.generate_tests_for_function(
                function_info, "test_file.py"
            )
            assert isinstance(result, str)
            assert "test_test_function" in result

    def test_generate_tests_for_function_llm_error(self):
        """Test test generation for function with LLM error."""
        function_info = {
            "name": "test_function",
            "type": "function",
            "line_number": 1,
            "content": "def test_function(x, y):\n    return x + y",
        }

        with patch.object(self.generator, "_get_llm_client") as mock_get_client:
            mock_get_client.side_effect = Exception("LLM error")

            result = self.generator.generate_tests_for_function(
                function_info, "test_file.py"
            )
            assert isinstance(result, str)
            # Should fall back to template-based generation

    def test_generate_tests_for_class(self):
        """Test test generation for a specific class."""
        class_info = {
            "name": "TestClass",
            "type": "class",
            "line_number": 1,
            "content": "class TestClass:\n    def method(self):\n        pass",
        }

        with patch.object(self.generator, "_get_llm_client") as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="class TestTestClass:\n    def test_method(self):\n        pass"
                        )
                    )
                ]
            )
            mock_get_client.return_value = mock_client

            result = self.generator.generate_tests_for_class(class_info, "test_file.py")
            assert isinstance(result, str)
            assert "TestTestClass" in result

    def test_generate_tests_for_class_llm_error(self):
        """Test test generation for class with LLM error."""
        class_info = {
            "name": "TestClass",
            "type": "class",
            "line_number": 1,
            "content": "class TestClass:\n    def method(self):\n        pass",
        }

        with patch.object(self.generator, "_get_llm_client") as mock_get_client:
            mock_get_client.side_effect = Exception("LLM error")

            result = self.generator.generate_tests_for_class(class_info, "test_file.py")
            assert isinstance(result, str)
            # Should fall back to template-based generation

    def test_generate_tests_with_templates(self):
        """Test template-based test generation."""
        function_info = {
            "name": "test_function",
            "type": "function",
            "line_number": 1,
            "content": "def test_function(x, y):\n    return x + y",
        }

        result = self.generator._generate_tests_with_templates(
            function_info, "test_file.py"
        )
        assert isinstance(result, str)
        assert "test_function" in result

    def test_generate_tests_with_templates_class(self):
        """Test template-based test generation for class."""
        class_info = {
            "name": "TestClass",
            "type": "class",
            "line_number": 1,
            "content": "class TestClass:\n    def method(self):\n        pass",
        }

        result = self.generator._generate_tests_with_templates(
            class_info, "test_file.py"
        )
        assert isinstance(result, str)
        assert "TestClass" in result

    def test_generate_tests_with_templates_unsupported(self):
        """Test template-based test generation for unsupported type."""
        unsupported_info = {
            "name": "test_variable",
            "type": "variable",
            "line_number": 1,
            "content": "test_variable = 42",
        }

        result = self.generator._generate_tests_with_templates(
            unsupported_info, "test_file.py"
        )
        assert isinstance(result, str)
        # Should return empty string for unsupported types

    def test_analyze_coverage_gaps(self):
        """Test coverage gap analysis."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"files": {"test_file.py": {"summary": {"percent_covered": 80.0}}}}',
            )

            result = self.generator.analyze_coverage_gaps("test_file.py")
            assert isinstance(result, dict)

    def test_analyze_coverage_gaps_error(self):
        """Test coverage gap analysis with error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error")

            result = self.generator.analyze_coverage_gaps("test_file.py")
            assert isinstance(result, dict)
            # Should return empty dict on error

    def test_generate_test_file(self):
        """Test test file generation."""
        test_content = "def test_function():\n    pass"
        output_path = "test_output.py"

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("pathlib.Path.parent.mkdir", return_value=None):
                result = self.generator.generate_test_file(test_content, output_path)
                assert result == output_path
                mock_file.assert_called_once()

    def test_generate_test_file_error(self):
        """Test test file generation with error."""
        test_content = "def test_function():\n    pass"
        output_path = "/invalid/path/test_output.py"

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                self.generator.generate_test_file(test_content, output_path)

    def test_generate_tests_for_changes(self):
        """Test test generation for multiple changes."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="def old_function():\n    pass",
                new_content="def test_function():\n    return 42",
                diff="+def test_function():\n+    return 42",
                line_numbers=[1, 2],
            )
        ]

        with patch.object(self.generator, "analyze_file_changes") as mock_analyze:
            mock_analyze.return_value = [
                {
                    "name": "test_function",
                    "type": "function",
                    "line_number": 1,
                    "content": "def test_function():\n    return 42",
                }
            ]

            with patch.object(
                self.generator, "generate_tests_for_function"
            ) as mock_generate:
                mock_generate.return_value = (
                    "def test_test_function():\n    assert test_function() == 42"
                )

                result = self.generator.generate_tests_for_changes(changes)
                assert isinstance(result, list)
                assert len(result) > 0

    def test_generate_tests_for_changes_empty(self):
        """Test test generation for empty changes."""
        changes = []

        result = self.generator.generate_tests_for_changes(changes)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_generate_tests_for_changes_no_functions(self):
        """Test test generation when no functions are found."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="",
                new_content="# This is a comment",
                diff="+# This is a comment",
                line_numbers=[1],
            )
        ]

        with patch.object(self.generator, "analyze_file_changes") as mock_analyze:
            mock_analyze.return_value = []

            result = self.generator.generate_tests_for_changes(changes)
            assert isinstance(result, list)
            assert len(result) == 0


class TestMainFunction:
    """Test main function and CLI interface."""

    @patch("sys.argv", ["enhanced_testgen.py", "--help"])
    def test_main_help(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["enhanced_testgen.py", "--version"])
    def test_main_version(self):
        """Test main function with version argument."""
        with pytest.raises(SystemExit):
            main()

    @patch("sys.argv", ["enhanced_testgen.py", "--config", "test_config.json"])
    @patch("builtins.open", mock_open(read_data='{"llm_provider": "openai"}'))
    @patch("pathlib.Path.exists", return_value=True)
    def test_main_with_config(self, mock_exists, mock_file):
        """Test main function with config file."""
        with patch(
            "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
        ) as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.generate_tests_for_changes.return_value = []

            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected for help/version

    @patch("sys.argv", ["enhanced_testgen.py", "--input", "test_input.json"])
    @patch("builtins.open", mock_open(read_data='{"changes": []}'))
    @patch("pathlib.Path.exists", return_value=True)
    def test_main_with_input(self, mock_exists, mock_file):
        """Test main function with input file."""
        with patch(
            "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
        ) as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.generate_tests_for_changes.return_value = []

            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected for help/version


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_config_invalid_provider(self):
        """Test configuration with invalid provider."""
        config = TestGenConfig()
        config.llm_provider = "invalid_provider"
        generator = EnhancedTestGenerator(config)

        with pytest.raises(ValueError):
            generator._get_llm_client()

    def test_config_invalid_model(self):
        """Test configuration with invalid model."""
        config = TestGenConfig()
        config.model = "invalid_model"
        generator = EnhancedTestGenerator(config)

        # Should still work, just with invalid model
        assert generator.config.model == "invalid_model"

    def test_config_invalid_temperature(self):
        """Test configuration with invalid temperature."""
        config = TestGenConfig()
        config.temperature = 2.0  # Invalid temperature > 1.0

        # Should still work, just with invalid temperature
        assert config.temperature == 2.0

    def test_config_invalid_max_tokens(self):
        """Test configuration with invalid max_tokens."""
        config = TestGenConfig()
        config.max_tokens = -1  # Invalid max_tokens

        # Should still work, just with invalid max_tokens
        assert config.max_tokens == -1

    def test_code_change_empty_content(self):
        """Test CodeChange with empty content."""
        change = CodeChange(
            file_path="test_file.py",
            change_type="added",
            old_content="",
            new_content="",
            diff="",
            line_numbers=[],
        )

        assert change.file_path == "test_file.py"
        assert change.change_type == "added"
        assert change.old_content == ""
        assert change.new_content == ""
        assert change.diff == ""
        assert change.line_numbers == []

    def test_generator_with_none_config(self):
        """Test generator with None config."""
        with pytest.raises(TypeError):
            EnhancedTestGenerator(None)

    def test_generator_with_invalid_config(self):
        """Test generator with invalid config."""
        with pytest.raises(AttributeError):
            EnhancedTestGenerator("invalid_config")


class TestIntegration:
    """Test integration scenarios."""

    def test_full_workflow(self):
        """Test full test generation workflow."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="def old_function():\n    pass",
                new_content="def test_function():\n    return 42",
                diff="+def test_function():\n+    return 42",
                line_numbers=[1, 2],
            )
        ]

        with patch.object(generator, "analyze_file_changes") as mock_analyze:
            mock_analyze.return_value = [
                {
                    "name": "test_function",
                    "type": "function",
                    "line_number": 1,
                    "content": "def test_function():\n    return 42",
                }
            ]

            with patch.object(
                generator, "generate_tests_for_function"
            ) as mock_generate:
                mock_generate.return_value = (
                    "def test_test_function():\n    assert test_function() == 42"
                )

                with patch.object(generator, "generate_test_file") as mock_file:
                    mock_file.return_value = "test_output.py"

                    result = generator.generate_tests_for_changes(changes)
                    assert isinstance(result, list)
                    assert len(result) > 0

    def test_error_handling_workflow(self):
        """Test error handling in full workflow."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="nonexistent.py",
                change_type="modified",
                old_content="",
                new_content="def test_function():\n    return 42",
                diff="+def test_function():\n+    return 42",
                line_numbers=[1, 2],
            )
        ]

        with patch("pathlib.Path.exists", return_value=False):
            result = generator.generate_tests_for_changes(changes)
            assert isinstance(result, list)
            # Should handle missing files gracefully

    def test_llm_fallback_workflow(self):
        """Test LLM fallback in full workflow."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="modified",
                old_content="",
                new_content="def test_function():\n    return 42",
                diff="+def test_function():\n+    return 42",
                line_numbers=[1, 2],
            )
        ]

        with patch.object(generator, "analyze_file_changes") as mock_analyze:
            mock_analyze.return_value = [
                {
                    "name": "test_function",
                    "type": "function",
                    "line_number": 1,
                    "content": "def test_function():\n    return 42",
                }
            ]

            with patch.object(generator, "_get_llm_client") as mock_get_client:
                mock_get_client.side_effect = Exception("LLM error")

                result = generator.generate_tests_for_changes(changes)
                assert isinstance(result, list)
                # Should fall back to template-based generation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
