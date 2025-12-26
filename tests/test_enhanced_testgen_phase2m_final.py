"""Phase 2M Final Test Suite for enhanced_testgen.py - Focused Coverage Testing."""

import ast
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open, call
import pytest

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    CodeChange,
    TestGenTemplate,
    EnhancedTestGenerator,
    main,
    TestGenerationConfig,
)


class TestTestGenConfig:
    """Test TestGenConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TestGenConfig()
        assert config.llm_provider == "openai"
        assert config.llm_api_key is None
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.1
        assert config.test_framework == "pytest"
        assert config.generate_mocks is True
        assert config.max_tests_per_file == 10
        assert config.analyze_coverage_gaps is True
        assert config.min_coverage_threshold == 80.0
        assert config.output_directory == "tests/unit"
        assert config.test_file_suffix == "_test.py"

    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model="claude-3",
            test_framework="unittest",
        )
        config_dict = config.to_dict()

        assert config_dict["llm_provider"] == "anthropic"
        assert config_dict["llm_api_key"] == "test_key"
        assert config_dict["llm_model"] == "claude-3"
        assert config_dict["test_framework"] == "unittest"
        assert config_dict["generate_mocks"] is True
        assert config_dict["max_tests_per_file"] == 10

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "llm_provider": "local",
            "llm_model": "custom-model",
            "test_framework": "pytest",
            "generate_mocks": False,
        }
        config = TestGenConfig.from_dict(config_dict)

        assert config.llm_provider == "local"
        assert config.llm_model == "custom-model"
        assert config.test_framework == "pytest"
        assert config.generate_mocks is False

    def test_config_validation_valid(self):
        """Test configuration validation with valid values."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=90.0,
            output_directory="custom_tests",
        )
        assert config.validate() is True

    def test_config_validation_invalid_provider(self):
        """Test configuration validation with invalid provider."""
        config = TestGenConfig(llm_provider="invalid")
        assert config.validate() is False

    def test_config_validation_missing_api_key(self):
        """Test configuration validation with missing API key."""
        config = TestGenConfig(llm_provider="openai", llm_api_key=None)
        assert config.validate() is False

    def test_config_validation_invalid_temperature(self):
        """Test configuration validation with invalid temperature."""
        config = TestGenConfig(llm_temperature=1.5)
        assert config.validate() is False

    def test_config_validation_invalid_framework(self):
        """Test configuration validation with invalid framework."""
        config = TestGenConfig(test_framework="invalid")
        assert config.validate() is False

    def test_config_validation_invalid_max_tests(self):
        """Test configuration validation with invalid max tests."""
        config = TestGenConfig(max_tests_per_file=0)
        assert config.validate() is False

    def test_config_validation_invalid_coverage_threshold(self):
        """Test configuration validation with invalid coverage threshold."""
        config = TestGenConfig(min_coverage_threshold=150.0)
        assert config.validate() is False

    def test_config_validation_empty_output_directory(self):
        """Test configuration validation with empty output directory."""
        config = TestGenConfig(output_directory="")
        assert config.validate() is False


class TestCodeChange:
    """Test CodeChange dataclass."""

    def test_code_change_creation(self):
        """Test CodeChange creation with all parameters."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            line_numbers=(10, 20),
            code_snippet="def test_func(): pass",
            context="Test context",
        )

        assert change.file_path == "test.py"
        assert change.function_name == "test_func"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_numbers == (10, 20)
        assert change.code_snippet == "def test_func(): pass"
        assert change.context == "Test context"

    def test_code_change_defaults(self):
        """Test CodeChange with default values."""
        change = CodeChange(file_path="test.py")

        assert change.file_path == "test.py"
        assert change.function_name is None
        assert change.class_name is None
        assert change.change_type == "added"
        assert change.line_numbers == (0, 0)
        assert change.code_snippet == ""
        assert change.context == ""

    def test_code_change_to_dict(self):
        """Test CodeChange to dictionary conversion."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            line_numbers=(5, 15),
            code_snippet="def test_func(): return 42",
        )
        change_dict = change.to_dict()

        assert change_dict["file_path"] == "test.py"
        assert change_dict["function_name"] == "test_func"
        assert change_dict["line_numbers"] == (5, 15)
        assert change_dict["code_snippet"] == "def test_func(): return 42"


class TestTestGenTemplate:
    """Test TestGenTemplate dataclass."""

    def test_template_creation(self):
        """Test TestGenTemplate creation."""
        template = TestGenTemplate(
            name="test_template",
            description="A test template",
            template="def test_{name}(): assert True",
            variables=["name"],
            applicable_to=["function"],
        )

        assert template.name == "test_template"
        assert template.description == "A test template"
        assert template.template == "def test_{name}(): assert True"
        assert template.variables == ["name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="local",
            llm_api_key=None,
            analyze_coverage_gaps=False,
        )

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_initialization_without_api_key(self, mock_logger):
        """Test EnhancedTestGenerator initialization without API key."""
        generator = EnhancedTestGenerator(self.config)

        assert generator.config == self.config
        assert len(generator.test_templates) > 0
        assert generator.llm_client is not None
        mock_logger.warning.assert_called_once()

    @patch("builtins.__import__")
    def test_initialization_with_openai(self, mock_import):
        """Test EnhancedTestGenerator initialization with OpenAI."""
        mock_openai = Mock()
        mock_openai.api_key = "test_key"
        mock_import.return_value = mock_openai

        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test_key",
        )

        generator = EnhancedTestGenerator(config)

        assert generator.config == config
        assert generator.llm_client == mock_openai
        assert mock_openai.api_key == "test_key"

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_initialization_openai_import_error(self, mock_logger):
        """Test EnhancedTestGenerator initialization with OpenAI import error."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test_key",
        )

        with patch.dict("sys.modules", {}, clear=True):
            generator = EnhancedTestGenerator(config)

        assert generator.llm_client is None
        mock_logger.warning.assert_called()

    @patch("builtins.__import__")
    def test_initialization_with_anthropic(self, mock_import):
        """Test EnhancedTestGenerator initialization with Anthropic."""
        mock_anthropic = Mock()
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_import.return_value = mock_anthropic

        config = TestGenConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
        )

        generator = EnhancedTestGenerator(config)

        assert generator.llm_client == mock_client
        mock_anthropic.Anthropic.assert_called_once_with(api_key="test_key")

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_initialization_anthropic_import_error(self, mock_logger):
        """Test EnhancedTestGenerator initialization with Anthropic import error."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
        )

        with patch.dict("sys.modules", {}, clear=True):
            generator = EnhancedTestGenerator(config)

        assert generator.llm_client is None
        mock_logger.warning.assert_called()

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_initialization_unsupported_provider(self, mock_logger):
        """Test EnhancedTestGenerator initialization with unsupported provider."""
        config = TestGenConfig(
            llm_provider="unsupported",
            llm_api_key="test_key",
        )

        generator = EnhancedTestGenerator(config)

        assert generator.llm_client is None
        mock_logger.warning.assert_called()

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_initialization_exception_handling(self, mock_logger):
        """Test EnhancedTestGenerator initialization with exception handling."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test_key",
        )

        with patch("builtins.__import__", side_effect=Exception("Test error")):
            generator = EnhancedTestGenerator(config)

        assert generator.llm_client is None
        mock_logger.warning.assert_called()

    def test_load_test_templates(self):
        """Test test templates loading."""
        generator = EnhancedTestGenerator(self.config)
        templates = generator.test_templates

        assert len(templates) > 0
        template_names = [t.name for t in templates]
        assert "function_test" in template_names
        assert "function_parametrized_test" in template_names
        assert "function_error_test" in template_names
        assert "class_test" in template_names
        assert "edge_case_test" in template_names
        assert "integration_test" in template_names
        assert "performance_test" in template_names
        assert "coverage_test" in template_names

    def test_template_structure(self):
        """Test test template structure."""
        generator = EnhancedTestGenerator(self.config)
        template = next(
            t for t in generator.test_templates if t.name == "function_test"
        )

        assert template.description
        assert "{function_name}" in template.template
        assert "function_name" in template.variables
        assert "function" in template.applicable_to


class TestCodeAnalysis:
    """Test code analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(analyze_coverage_gaps=False)
        self.generator = EnhancedTestGenerator(self.config)

    def test_analyze_code_changes_empty(self):
        """Test analyze_code_changes with empty file list."""
        changes = self.generator.analyze_code_changes([])
        assert changes == []

    def test_analyze_code_changes_non_python_files(self):
        """Test analyze_code_changes with non-Python files."""
        changes = self.generator.analyze_code_changes(["test.txt", "test.js"])
        assert changes == []

    def test_parse_diff_lines(self):
        """Test _parse_diff_lines parsing."""
        diff_content = """@@ -1,3 +1,3 @@
 def test():
-    old line
+    new line
     other line"""

        lines = self.generator._parse_diff_lines(diff_content)

        assert len(lines) > 0
        assert all(isinstance(line, int) for line in lines)

    def test_is_function_changed(self):
        """Test _is_function_changed method."""
        mock_node = Mock()
        mock_node.lineno = 5
        mock_node.end_lineno = 10

        # Function is changed
        changed_lines = [1, 5, 15]
        assert self.generator._is_function_changed(mock_node, changed_lines) is True

        # Function is not changed
        changed_lines = [1, 15, 25]
        assert self.generator._is_function_changed(mock_node, changed_lines) is False

    def test_is_class_changed(self):
        """Test _is_class_changed method."""
        mock_node = Mock()
        mock_node.lineno = 10
        mock_node.end_lineno = 20

        # Class is changed
        changed_lines = [1, 15, 25]
        assert self.generator._is_class_changed(mock_node, changed_lines) is True

        # Class is not changed
        changed_lines = [1, 5, 25]
        assert self.generator._is_class_changed(mock_node, changed_lines) is False

    def test_get_function_context(self):
        """Test _get_function_context method."""
        mock_node = Mock()
        mock_node.decorator_list = []
        mock_node.args = Mock()
        mock_node.args.args = []
        mock_node.returns = None

        context = self.generator._get_function_context(mock_node)
        assert context == ""

    def test_get_class_context(self):
        """Test _get_class_context method."""
        mock_node = Mock()
        mock_node.bases = []
        mock_node.body = []

        context = self.generator._get_class_context(mock_node)
        assert context == ""


class TestTestGeneration:
    """Test test generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(analyze_coverage_gaps=False)
        self.generator = EnhancedTestGenerator(self.config)

    def test_generate_tests_with_llm_no_client(self):
        """Test generate_tests_with_llm without LLM client."""
        self.generator.llm_client = None

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): return 42",
        )

        result = self.generator.generate_tests_with_llm(change)
        assert result != ""

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_generate_tests_with_llm_openai_success(self, mock_logger):
        """Test generate_tests_with_llm with OpenAI success."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated test code"
        mock_client.ChatCompletion.create.return_value = mock_response

        self.generator.llm_client = mock_client
        self.generator.config.llm_provider = "openai"

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): return 42",
        )

        result = self.generator.generate_tests_with_llm(change)
        assert result == "Generated test code"

    @patch("src.ai_guard.generators.enhanced_testgen.logger")
    def test_generate_tests_with_llm_openai_exception(self, mock_logger):
        """Test generate_tests_with_llm with OpenAI exception."""
        mock_client = Mock()
        mock_client.ChatCompletion.create.side_effect = Exception("API error")

        self.generator.llm_client = mock_client
        self.generator.config.llm_provider = "openai"

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): return 42",
        )

        result = self.generator.generate_tests_with_llm(change)
        assert result != ""  # Should fallback to templates
        mock_logger.warning.assert_called()

    def test_create_llm_prompt(self):
        """Test _create_llm_prompt method."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): return 42",
            context="Test context",
        )

        prompt = self.generator._create_llm_prompt(change)

        assert "test.py" in prompt
        assert "test_func" in prompt
        assert "function" in prompt
        assert "def test_func(): return 42" in prompt
        assert "pytest framework" in prompt

    def test_generate_tests_with_templates_function(self):
        """Test _generate_tests_with_templates for function."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(x): return x * 2",
        )

        result = self.generator._generate_tests_with_templates(change)
        assert "def test_test_func():" in result

    def test_generate_tests_with_templates_class(self):
        """Test _generate_tests_with_templates for class."""
        change = CodeChange(
            file_path="test.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass: pass",
        )

        result = self.generator._generate_tests_with_templates(change)
        assert "class TestTestClass:" in result or "test_testclass" in result.lower()

    def test_generate_tests_with_templates_generic(self):
        """Test _generate_tests_with_templates for generic change."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="import",
            code_snippet="import os",
        )

        result = self.generator._generate_tests_with_templates(change)
        assert "def test_import_test_func():" in result

    def test_generate_test_cases(self):
        """Test _generate_test_cases method."""
        mock_func = Mock()
        mock_func.args = Mock()
        mock_func.args.args = [Mock(), Mock()]
        mock_func.args.args[0].arg = "arg1"
        mock_func.args.args[1].arg = "arg2"

        test_cases = self.generator._generate_test_cases(mock_func)

        assert "test_input" in test_cases
        assert "expected_output" in test_cases
        assert "arg1" in test_cases or "arg2" in test_cases

    def test_generate_coverage_tests(self):
        """Test _generate_coverage_tests method."""
        mock_func = Mock()
        mock_func.name = "test_func"
        mock_func.args = Mock()
        mock_func.args.args = [Mock(), Mock()]
        mock_func.args.args[0].arg = "arg1"
        mock_func.args.args[1].arg = "arg2"

        coverage_tests = self.generator._generate_coverage_tests(mock_func)

        assert "test_func" in coverage_tests
        assert "assert result is not None" in coverage_tests

    def test_generate_class_tests(self):
        """Test _generate_class_tests method."""
        change = CodeChange(
            file_path="test.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass: pass",
        )

        result = self.generator._generate_class_tests(change)
        assert "TestClass" in result

    def test_generate_generic_tests(self):
        """Test _generate_generic_tests method."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="import",
            code_snippet="import os",
        )

        result = self.generator._generate_generic_tests(change)

        assert "def test_import_test_func():" in result
        assert "def test_import_test_func_import():" in result
        assert "assert True" in result


class TestCoverageAnalysis:
    """Test coverage analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(analyze_coverage_gaps=True)
        self.generator = EnhancedTestGenerator(self.config)

    def test_analyze_coverage_gaps_disabled(self):
        """Test analyze_coverage_gaps when disabled."""
        config = TestGenConfig(analyze_coverage_gaps=False)
        generator = EnhancedTestGenerator(config)

        gaps = generator.analyze_coverage_gaps(["test.py"])
        assert gaps == {}

    def test_analyze_coverage_gaps_empty_files(self):
        """Test analyze_coverage_gaps with empty file list."""
        gaps = self.generator.analyze_coverage_gaps([])
        assert gaps == {}

    def test_analyze_coverage_gaps_non_python_files(self):
        """Test analyze_coverage_gaps with non-Python files."""
        gaps = self.generator.analyze_coverage_gaps(["test.txt", "test.js"])
        assert gaps == {}


class TestFileOperations:
    """Test file operations and test file generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(analyze_coverage_gaps=False)
        self.generator = EnhancedTestGenerator(self.config)

    def test_generate_test_file_empty_changes(self):
        """Test generate_test_file with empty changes."""
        result = self.generator.generate_test_file([], "output.py")
        assert result == ""

    def test_generate_test_file_with_changes(self):
        """Test generate_test_file with changes."""
        changes = [
            CodeChange(
                file_path="src/module.py",
                function_name="test_func",
                change_type="function",
                code_snippet="def test_func(): return 42",
            ),
            CodeChange(
                file_path="src/other.py",
                class_name="TestClass",
                change_type="class",
                code_snippet="class TestClass: pass",
            ),
        ]

        with patch.object(
            self.generator,
            "generate_tests_with_llm",
            return_value="def test_test_func(): assert True",
        ):
            result = self.generator.generate_test_file(changes, "output.py")

        assert "Auto-generated tests" in result
        assert "src/module.py" in result
        assert "src/other.py" in result
        assert "import pytest" in result
        assert "from unittest.mock import Mock, patch" in result

    def test_generate_tests_empty_files(self):
        """Test generate_tests with empty file list."""
        result = self.generator.generate_tests([])
        assert result == ""

    def test_generate_tests_no_changes(self):
        """Test generate_tests with no code changes."""
        with patch.object(self.generator, "analyze_code_changes", return_value=[]):
            result = self.generator.generate_tests(["test.py"])

        assert result == ""

    def test_generate_tests_with_changes(self):
        """Test generate_tests with changes."""
        changes = [
            CodeChange(
                file_path="test.py",
                function_name="test_func",
                change_type="function",
                code_snippet="def test_func(): return 42",
            ),
        ]

        with patch.object(self.generator, "analyze_code_changes", return_value=changes):
            with patch.object(
                self.generator,
                "generate_test_file",
                return_value="Generated test content",
            ):
                result = self.generator.generate_tests(["test.py"])

        assert result == "Generated test content"

    def test_generate_tests_for_changes_empty(self):
        """Test generate_tests_for_changes with empty changes."""
        result = self.generator.generate_tests_for_changes([])
        assert result == ""

    def test_generate_tests_for_changes_with_changes(self):
        """Test generate_tests_for_changes with changes."""
        changes = [
            CodeChange(
                file_path="test.py",
                function_name="test_func",
                change_type="function",
                code_snippet="def test_func(): return 42",
            ),
        ]

        with patch.object(
            self.generator, "generate_test_file", return_value="Generated test content"
        ):
            result = self.generator.generate_tests_for_changes(changes)

        assert result == "Generated test content"

    def test_generate_function_test(self):
        """Test _generate_function_test method."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): return 42",
        )

        with patch.object(
            self.generator,
            "_generate_function_tests",
            return_value="Generated function test",
        ):
            result = self.generator._generate_function_test(change)

        assert result == "Generated function test"


class TestMainFunction:
    """Test main function and CLI interface."""

    @patch("src.ai_guard.generators.enhanced_testgen.changed_python_files")
    @patch("src.ai_guard.generators.enhanced_testgen.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_main_with_changes(self, mock_open, mock_path, mock_changed_files):
        """Test main function with file changes."""
        mock_changed_files.return_value = ["test.py"]

        with patch.object(
            EnhancedTestGenerator, "generate_tests", return_value="Generated tests"
        ):
            with patch("sys.argv", ["enhanced_testgen.py", "--event", "event.json"]):
                main()

        # Test should complete without raising SystemExit
        assert True

    @patch("src.ai_guard.generators.enhanced_testgen.changed_python_files")
    def test_main_no_changes(self, mock_changed_files):
        """Test main function with no file changes."""
        mock_changed_files.return_value = []

        with patch("sys.argv", ["enhanced_testgen.py", "--event", "event.json"]):
            main()

        # Test should complete without raising SystemExit
        assert True

    @patch("src.ai_guard.generators.enhanced_testgen.changed_python_files")
    @patch("src.ai_guard.generators.enhanced_testgen.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_main_with_api_key(self, mock_open, mock_path, mock_changed_files):
        """Test main function with API key."""
        mock_changed_files.return_value = ["test.py"]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch.object(
                EnhancedTestGenerator, "generate_tests", return_value="Generated tests"
            ):
                with patch(
                    "sys.argv",
                    [
                        "enhanced_testgen.py",
                        "--event",
                        "event.json",
                        "--llm-provider",
                        "openai",
                    ],
                ):
                    main()

        # Test should complete without raising SystemExit
        assert True

    @patch("src.ai_guard.generators.enhanced_testgen.changed_python_files")
    @patch("src.ai_guard.generators.enhanced_testgen.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_main_with_custom_output(self, mock_open, mock_path, mock_changed_files):
        """Test main function with custom output path."""
        mock_changed_files.return_value = ["test.py"]

        with patch.object(
            EnhancedTestGenerator, "generate_tests", return_value="Generated tests"
        ):
            with patch(
                "sys.argv",
                [
                    "enhanced_testgen.py",
                    "--event",
                    "event.json",
                    "--output",
                    "custom_test.py",
                ],
            ):
                main()

        # Test should complete without raising SystemExit
        assert True


class TestBackwardCompatibility:
    """Test backward compatibility aliases."""

    def test_test_generation_config_alias(self):
        """Test TestGenerationConfig alias."""
        assert TestGenerationConfig == TestGenConfig

    def test_test_template_alias(self):
        """Test TestTemplate alias."""
        from src.ai_guard.generators.enhanced_testgen import TestTemplate

        assert TestTemplate == TestGenTemplate


if __name__ == "__main__":
    unittest.main()
