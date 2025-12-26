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
    TestGenTemplate,
    EnhancedTestGenerator,
    main,
)


class TestTestGenConfig:
    """Test TestGenConfig class functionality."""

    def test_config_creation_default(self):
        """Test default configuration creation."""
        config = TestGenConfig()
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.1
        assert config.test_framework == "pytest"
        assert config.include_docstrings is True
        assert config.include_type_hints is True
        assert config.generate_mocks is True
        assert config.generate_parametrized_tests is True
        assert config.generate_edge_cases is True
        assert config.max_tests_per_file == 10
        assert config.analyze_coverage_gaps is True
        assert config.min_coverage_threshold == 80.0
        assert config.output_directory == "tests/unit"
        assert config.test_file_suffix == "_test.py"

    def test_config_creation_custom(self):
        """Test custom configuration creation."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            llm_temperature=0.2,
            test_framework="unittest",
            include_docstrings=False,
            include_type_hints=False,
            generate_mocks=False,
            generate_parametrized_tests=False,
            generate_edge_cases=False,
            max_tests_per_file=5,
            analyze_coverage_gaps=False,
            min_coverage_threshold=90.0,
            output_directory="custom_tests",
            test_file_suffix="_spec.py",
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3-sonnet"
        assert config.llm_temperature == 0.2
        assert config.test_framework == "unittest"
        assert config.include_docstrings is False
        assert config.include_type_hints is False
        assert config.generate_mocks is False
        assert config.generate_parametrized_tests is False
        assert config.generate_edge_cases is False
        assert config.max_tests_per_file == 5
        assert config.analyze_coverage_gaps is False
        assert config.min_coverage_threshold == 90.0
        assert config.output_directory == "custom_tests"
        assert config.test_file_suffix == "_spec.py"

    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = TestGenConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "openai"
        assert config_dict["llm_model"] == "gpt-4"
        assert config_dict["llm_temperature"] == 0.1
        assert config_dict["test_framework"] == "pytest"
        assert config_dict["include_docstrings"] is True
        assert config_dict["include_type_hints"] is True
        assert config_dict["generate_mocks"] is True
        assert config_dict["generate_parametrized_tests"] is True
        assert config_dict["generate_edge_cases"] is True
        assert config_dict["max_tests_per_file"] == 10
        assert config_dict["analyze_coverage_gaps"] is True
        assert config_dict["min_coverage_threshold"] == 80.0
        assert config_dict["output_directory"] == "tests/unit"
        assert config_dict["test_file_suffix"] == "_test.py"

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3-sonnet",
            "llm_temperature": 0.2,
            "test_framework": "unittest",
            "include_docstrings": False,
            "include_type_hints": False,
            "generate_mocks": False,
            "generate_parametrized_tests": False,
            "generate_edge_cases": False,
            "max_tests_per_file": 5,
            "analyze_coverage_gaps": False,
            "min_coverage_threshold": 90.0,
            "output_directory": "custom_tests",
            "test_file_suffix": "_spec.py",
        }
        config = TestGenConfig.from_dict(config_dict)
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3-sonnet"
        assert config.llm_temperature == 0.2
        assert config.test_framework == "unittest"
        assert config.include_docstrings is False
        assert config.include_type_hints is False
        assert config.generate_mocks is False
        assert config.generate_parametrized_tests is False
        assert config.generate_edge_cases is False
        assert config.max_tests_per_file == 5
        assert config.analyze_coverage_gaps is False
        assert config.min_coverage_threshold == 90.0
        assert config.output_directory == "custom_tests"
        assert config.test_file_suffix == "_spec.py"

    def test_config_validate_valid(self):
        """Test configuration validation with valid config."""
        config = TestGenConfig()
        config.llm_api_key = "test_key"
        assert config.validate() is True

    def test_config_validate_invalid_provider(self):
        """Test configuration validation with invalid provider."""
        config = TestGenConfig()
        config.llm_provider = "invalid_provider"
        assert config.validate() is False

    def test_config_validate_missing_api_key(self):
        """Test configuration validation with missing API key."""
        config = TestGenConfig()
        config.llm_provider = "openai"
        config.llm_api_key = None
        assert config.validate() is False

    def test_config_validate_invalid_temperature(self):
        """Test configuration validation with invalid temperature."""
        config = TestGenConfig()
        config.llm_temperature = 2.0
        assert config.validate() is False

    def test_config_validate_invalid_framework(self):
        """Test configuration validation with invalid framework."""
        config = TestGenConfig()
        config.test_framework = "invalid_framework"
        assert config.validate() is False

    def test_config_validate_invalid_max_tests(self):
        """Test configuration validation with invalid max tests."""
        config = TestGenConfig()
        config.max_tests_per_file = 0
        assert config.validate() is False

    def test_config_validate_invalid_coverage_threshold(self):
        """Test configuration validation with invalid coverage threshold."""
        config = TestGenConfig()
        config.min_coverage_threshold = 150.0
        assert config.validate() is False

    def test_config_validate_empty_output_directory(self):
        """Test configuration validation with empty output directory."""
        config = TestGenConfig()
        config.output_directory = ""
        assert config.validate() is False


class TestCodeChange:
    """Test CodeChange data structure functionality."""

    def test_code_change_creation_minimal(self):
        """Test CodeChange object creation with minimal parameters."""
        change = CodeChange(file_path="test_file.py")
        assert change.file_path == "test_file.py"
        assert change.function_name is None
        assert change.class_name is None
        assert change.change_type == "added"
        assert change.line_numbers == (0, 0)
        assert change.code_snippet == ""
        assert change.context == ""
        assert change.line_number is None
        assert change.content is None

    def test_code_change_creation_full(self):
        """Test CodeChange object creation with all parameters."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            class_name="TestClass",
            change_type="modified",
            line_numbers=(1, 10),
            code_snippet="def test_function():\n    pass",
            context="class TestClass:",
            line_number=5,
            content="def test_function():\n    pass",
        )
        assert change.file_path == "test_file.py"
        assert change.function_name == "test_function"
        assert change.class_name == "TestClass"
        assert change.change_type == "modified"
        assert change.line_numbers == (1, 10)
        assert change.code_snippet == "def test_function():\n    pass"
        assert change.context == "class TestClass:"
        assert change.line_number == 5
        assert change.content == "def test_function():\n    pass"

    def test_code_change_to_dict(self):
        """Test CodeChange to dictionary conversion."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            class_name="TestClass",
            change_type="added",
            line_numbers=(1, 5),
            code_snippet="def test_function():\n    pass",
            context="class TestClass:",
            line_number=3,
            content="def test_function():\n    pass",
        )
        change_dict = change.to_dict()
        assert isinstance(change_dict, dict)
        assert change_dict["file_path"] == "test_file.py"
        assert change_dict["function_name"] == "test_function"
        assert change_dict["class_name"] == "TestClass"
        assert change_dict["change_type"] == "added"
        assert change_dict["line_numbers"] == (1, 5)
        assert change_dict["code_snippet"] == "def test_function():\n    pass"
        assert change_dict["context"] == "class TestClass:"
        assert change_dict["line_number"] == 3
        assert change_dict["content"] == "def test_function():\n    pass"


class TestTestGenTemplate:
    """Test TestGenTemplate data structure functionality."""

    def test_template_creation(self):
        """Test TestGenTemplate object creation."""
        template = TestGenTemplate(
            name="function_test",
            description="Test template for functions",
            template="def test_{function_name}():\n    pass",
            variables=["function_name"],
            applicable_to=["function"],
        )
        assert template.name == "function_test"
        assert template.description == "Test template for functions"
        assert template.template == "def test_{function_name}():\n    pass"
        assert template.variables == ["function_name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig()
        self.config.llm_api_key = "test_key"
        self.generator = EnhancedTestGenerator(self.config)

    def test_generator_initialization(self):
        """Test generator initialization."""
        assert self.generator.config == self.config
        assert isinstance(self.generator.test_templates, list)
        assert len(self.generator.test_templates) > 0

    def test_generator_initialization_no_api_key(self):
        """Test generator initialization without API key."""
        config = TestGenConfig()
        config.llm_api_key = None
        generator = EnhancedTestGenerator(config)
        assert generator.config == config
        assert generator.llm_client is None

    def test_generator_initialization_invalid_provider(self):
        """Test generator initialization with invalid provider."""
        config = TestGenConfig()
        config.llm_provider = "invalid_provider"
        config.llm_api_key = "test_key"
        generator = EnhancedTestGenerator(config)
        assert generator.config == config
        assert generator.llm_client is None

    def test_load_test_templates(self):
        """Test loading of test templates."""
        templates = self.generator._load_test_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Check that all templates have required attributes
        for template in templates:
            assert hasattr(template, "name")
            assert hasattr(template, "description")
            assert hasattr(template, "template")
            assert hasattr(template, "variables")
            assert hasattr(template, "applicable_to")

    def test_initialize_llm_client_openai(self):
        """Test LLM client initialization for OpenAI."""
        self.config.llm_provider = "openai"
        self.config.llm_api_key = "test_key"
        generator = EnhancedTestGenerator(self.config)

        # Should initialize without error
        assert generator.llm_client is not None

    def test_initialize_llm_client_anthropic(self):
        """Test LLM client initialization for Anthropic."""
        self.config.llm_provider = "anthropic"
        self.config.llm_api_key = "test_key"
        generator = EnhancedTestGenerator(self.config)

        # Should initialize without error
        assert generator.llm_client is not None

    def test_initialize_llm_client_local(self):
        """Test LLM client initialization for local provider."""
        self.config.llm_provider = "local"
        generator = EnhancedTestGenerator(self.config)

        # Should initialize without error
        assert generator.llm_client is not None

    def test_initialize_llm_client_no_api_key(self):
        """Test LLM client initialization without API key."""
        self.config.llm_api_key = None
        generator = EnhancedTestGenerator(self.config)

        # Should not initialize LLM client
        assert generator.llm_client is None

    def test_generate_tests_with_llm(self):
        """Test test generation with LLM."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="function",
            code_snippet="def test_function():\n    return 42",
        )

        with patch.object(self.generator, "llm_client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="def test_test_function():\n    assert test_function() == 42"
                        )
                    )
                ]
            )

            result = self.generator.generate_tests_with_llm(change)
            assert isinstance(result, str)
            assert "test_test_function" in result

    def test_generate_tests_with_llm_no_client(self):
        """Test test generation with LLM when no client available."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="function",
            code_snippet="def test_function():\n    return 42",
        )

        self.generator.llm_client = None
        result = self.generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        # Should fall back to template-based generation

    def test_generate_tests_with_llm_error(self):
        """Test test generation with LLM when error occurs."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="function",
            code_snippet="def test_function():\n    return 42",
        )

        with patch.object(self.generator, "llm_client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("LLM error")

            result = self.generator.generate_tests_with_llm(change)
            assert isinstance(result, str)
            # Should fall back to template-based generation

    def test_generate_tests_with_templates_function(self):
        """Test template-based test generation for function."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="function",
            code_snippet="def test_function():\n    return 42",
        )

        result = self.generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "test_function" in result

    def test_generate_tests_with_templates_class(self):
        """Test template-based test generation for class."""
        change = CodeChange(
            file_path="test_file.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass:\n    def method(self):\n        pass",
        )

        result = self.generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "TestClass" in result

    def test_generate_tests_with_templates_unsupported(self):
        """Test template-based test generation for unsupported type."""
        change = CodeChange(
            file_path="test_file.py",
            change_type="variable",
            code_snippet="test_variable = 42",
        )

        result = self.generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        # Should return empty string for unsupported types

    def test_generate_function_tests(self):
        """Test function test generation."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="function",
            code_snippet="def test_function():\n    return 42",
        )

        result = self.generator._generate_function_tests(change)
        assert isinstance(result, str)
        assert "test_function" in result

    def test_generate_class_tests(self):
        """Test class test generation."""
        change = CodeChange(
            file_path="test_file.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass:\n    def method(self):\n        pass",
        )

        result = self.generator._generate_class_tests(change)
        assert isinstance(result, str)
        assert "TestClass" in result

    def test_generate_generic_tests(self):
        """Test generic test generation."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="variable",
            code_snippet="test_variable = 42",
        )

        result = self.generator._generate_generic_tests(change)
        assert isinstance(result, str)
        assert "test_function" in result

    def test_generate_test_cases(self):
        """Test test case generation for parametrized tests."""
        # Create a mock function definition
        func_def = Mock()
        func_def.name = "test_function"
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="x"), Mock(arg="y")]

        result = self.generator._generate_test_cases(func_def)
        assert isinstance(result, str)
        assert "test_function" in result

    def test_generate_coverage_tests(self):
        """Test coverage test generation."""
        # Create a mock function definition
        func_def = Mock()
        func_def.name = "test_function"
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="x"), Mock(arg="y")]

        result = self.generator._generate_coverage_tests(func_def)
        assert isinstance(result, str)
        assert "test_function" in result

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
        changes = [
            CodeChange(
                file_path="test_file.py",
                function_name="test_function",
                change_type="function",
                code_snippet="def test_function():\n    return 42",
            )
        ]
        output_path = "test_output.py"

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("pathlib.Path.parent.mkdir", return_value=None):
                result = self.generator.generate_test_file(changes, output_path)
                assert result == output_path
                mock_file.assert_called_once()

    def test_generate_test_file_error(self):
        """Test test file generation with error."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                function_name="test_function",
                change_type="function",
                code_snippet="def test_function():\n    return 42",
            )
        ]
        output_path = "/invalid/path/test_output.py"

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                self.generator.generate_test_file(changes, output_path)

    def test_generate_tests_for_changes(self):
        """Test test generation for multiple changes."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                function_name="test_function",
                change_type="function",
                code_snippet="def test_function():\n    return 42",
            )
        ]

        with patch.object(self.generator, "generate_tests_with_llm") as mock_generate:
            mock_generate.return_value = (
                "def test_test_function():\n    assert test_function() == 42"
            )

            result = self.generator.generate_tests_for_changes(changes)
            assert isinstance(result, str)
            assert "test_test_function" in result

    def test_generate_tests_for_changes_empty(self):
        """Test test generation for empty changes."""
        changes = []

        result = self.generator.generate_tests_for_changes(changes)
        assert isinstance(result, str)
        assert result == ""

    def test_generate_tests_for_changes_no_functions(self):
        """Test test generation when no functions are found."""
        changes = [
            CodeChange(
                file_path="test_file.py",
                change_type="comment",
                code_snippet="# This is a comment",
            )
        ]

        with patch.object(self.generator, "generate_tests_with_llm") as mock_generate:
            mock_generate.return_value = ""

            result = self.generator.generate_tests_for_changes(changes)
            assert isinstance(result, str)
            # Should still process the changes

    def test_generate_tests(self):
        """Test main test generation method."""
        changed_files = ["test_file.py"]

        with patch.object(
            self.generator, "generate_tests_for_changes"
        ) as mock_generate:
            mock_generate.return_value = "def test_function():\n    pass"

            result = self.generator.generate_tests(changed_files)
            assert isinstance(result, dict)
            assert "test_file.py" in result

    def test_generate_tests_with_event_path(self):
        """Test test generation with event path."""
        changed_files = ["test_file.py"]
        event_path = "test_event.json"

        with patch.object(
            self.generator, "generate_tests_for_changes"
        ) as mock_generate:
            mock_generate.return_value = "def test_function():\n    pass"

            with patch("builtins.open", mock_open(read_data='{"changes": []}')):
                result = self.generator.generate_tests(changed_files, event_path)
                assert isinstance(result, dict)

    def test_generate_function_test(self):
        """Test function test generation."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            change_type="function",
            code_snippet="def test_function():\n    return 42",
        )

        result = self.generator._generate_function_test(change)
        assert isinstance(result, str)
        assert "test_function" in result


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
            mock_instance.generate_tests_for_changes.return_value = ""

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
            mock_instance.generate_tests_for_changes.return_value = ""

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
        assert config.validate() is False

    def test_config_invalid_model(self):
        """Test configuration with invalid model."""
        config = TestGenConfig()
        config.llm_model = "invalid_model"
        # Should still work, just with invalid model
        assert config.llm_model == "invalid_model"

    def test_config_invalid_temperature(self):
        """Test configuration with invalid temperature."""
        config = TestGenConfig()
        config.llm_temperature = 2.0  # Invalid temperature > 1.0
        assert config.validate() is False

    def test_config_invalid_max_tests(self):
        """Test configuration with invalid max tests."""
        config = TestGenConfig()
        config.max_tests_per_file = 0  # Invalid max_tests
        assert config.validate() is False

    def test_code_change_empty_content(self):
        """Test CodeChange with empty content."""
        change = CodeChange(
            file_path="test_file.py", change_type="added", code_snippet="", context=""
        )

        assert change.file_path == "test_file.py"
        assert change.change_type == "added"
        assert change.code_snippet == ""
        assert change.context == ""

    def test_generator_with_none_config(self):
        """Test generator with None config."""
        with pytest.raises(AttributeError):
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
        config.llm_api_key = "test_key"
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="test_file.py",
                function_name="test_function",
                change_type="function",
                code_snippet="def test_function():\n    return 42",
            )
        ]

        with patch.object(generator, "generate_tests_with_llm") as mock_generate:
            mock_generate.return_value = (
                "def test_test_function():\n    assert test_function() == 42"
            )

            with patch.object(generator, "generate_test_file") as mock_file:
                mock_file.return_value = "test_output.py"

                result = generator.generate_tests_for_changes(changes)
                assert isinstance(result, str)
                assert "test_test_function" in result

    def test_error_handling_workflow(self):
        """Test error handling in full workflow."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="nonexistent.py",
                change_type="modified",
                code_snippet="def test_function():\n    return 42",
            )
        ]

        result = generator.generate_tests_for_changes(changes)
        assert isinstance(result, str)
        # Should handle missing files gracefully

    def test_llm_fallback_workflow(self):
        """Test LLM fallback in full workflow."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="test_file.py",
                function_name="test_function",
                change_type="function",
                code_snippet="def test_function():\n    return 42",
            )
        ]

        with patch.object(generator, "generate_tests_with_llm") as mock_generate:
            mock_generate.side_effect = Exception("LLM error")

            result = generator.generate_tests_for_changes(changes)
            assert isinstance(result, str)
            # Should fall back to template-based generation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
