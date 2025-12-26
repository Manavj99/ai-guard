"""Simplified comprehensive tests for enhanced_testgen.py - Phase 2M Complete Coverage."""

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

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "llm_provider": "openai",
            "llm_api_key": "test_key",
            "llm_model": "gpt-3.5-turbo",
            "test_framework": "pytest",
        }

        config = TestGenConfig.from_dict(config_dict)

        assert config.llm_provider == "openai"
        assert config.llm_api_key == "test_key"
        assert config.llm_model == "gpt-3.5-turbo"
        assert config.test_framework == "pytest"

    def test_config_validation_valid(self):
        """Test configuration validation with valid values."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=85.0,
            output_directory="tests",
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
            change_type="function",
            name="test_function",
            line_number=10,
            context="def test_function():",
            diff_lines=["+def test_function():"],
        )

        assert change.file_path == "test.py"
        assert change.change_type == "function"
        assert change.name == "test_function"
        assert change.line_number == 10
        assert change.context == "def test_function():"
        assert change.diff_lines == ["+def test_function():"]

    def test_code_change_defaults(self):
        """Test CodeChange creation with default values."""
        change = CodeChange(
            file_path="test.py",
            change_type="function",
            name="test_function",
        )

        assert change.file_path == "test.py"
        assert change.change_type == "function"
        assert change.name == "test_function"
        assert change.line_number is None
        assert change.context is None
        assert change.diff_lines == []

    def test_code_change_to_dict(self):
        """Test CodeChange to dictionary conversion."""
        change = CodeChange(
            file_path="test.py",
            change_type="function",
            name="test_function",
            line_number=10,
            context="def test_function():",
            diff_lines=["+def test_function():"],
        )

        change_dict = change.to_dict()

        assert change_dict["file_path"] == "test.py"
        assert change_dict["change_type"] == "function"
        assert change_dict["name"] == "test_function"
        assert change_dict["line_number"] == 10
        assert change_dict["context"] == "def test_function():"
        assert change_dict["diff_lines"] == ["+def test_function():"]


class TestTestGenTemplate:
    """Test TestGenTemplate functionality."""

    def test_template_creation(self):
        """Test TestGenTemplate creation."""
        template = TestGenTemplate(
            name="function_test",
            description="Test template for functions",
            template="def test_{name}():",
        )

        assert template.name == "function_test"
        assert template.description == "Test template for functions"
        assert template.template == "def test_{name}():"


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="local",
            llm_api_key=None,
            analyze_coverage_gaps=False,
        )

    def test_initialization_basic(self):
        """Test basic EnhancedTestGenerator initialization."""
        generator = EnhancedTestGenerator(self.config)

        assert generator.config == self.config
        assert len(generator.test_templates) > 0
        assert generator.llm_client is not None

    def test_load_test_templates(self):
        """Test test templates loading."""
        generator = EnhancedTestGenerator(self.config)
        templates = generator.test_templates

        assert len(templates) > 0
        assert "function_test" in templates
        assert "class_test" in templates
        assert "generic_test" in templates

    def test_template_structure(self):
        """Test test template structure."""
        generator = EnhancedTestGenerator(self.config)
        template = generator.test_templates["function_test"]

        assert "name" in template
        assert "description" in template
        assert "template" in template
        assert "{name}" in template["template"]


class TestCodeAnalysis:
    """Test code analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="local",
            llm_api_key=None,
            analyze_coverage_gaps=False,
        )
        self.generator = EnhancedTestGenerator(self.config)

    def test_analyze_code_changes_empty(self):
        """Test analyze_code_changes with empty input."""
        changes = self.generator.analyze_code_changes([])
        assert changes == []

    def test_analyze_code_changes_non_python_files(self):
        """Test analyze_code_changes with non-Python files."""
        files = ["test.txt", "test.md", "test.json"]
        changes = self.generator.analyze_code_changes(files)
        assert changes == []

    @patch("subprocess.run")
    def test_get_base_head_from_event_pull_request(self, mock_run):
        """Test get_base_head_from_event with pull request event."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\nfeature-branch\n"

        event = {
            "pull_request": {"base": {"ref": "main"}, "head": {"ref": "feature-branch"}}
        }
        base, head = self.generator._get_base_head_from_event(event)

        assert base == "main"
        assert head == "feature-branch"

    @patch("subprocess.run")
    def test_get_base_head_from_event_push(self, mock_run):
        """Test get_base_head_from_event with push event."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\nHEAD~1\n"

        event = {"ref": "refs/heads/main"}
        base, head = self.generator._get_base_head_from_event(event)

        assert base == "HEAD~1"
        assert head == "HEAD"

    def test_get_base_head_from_event_invalid(self):
        """Test get_base_head_from_event with invalid event."""
        event = {"invalid": "data"}
        base, head = self.generator._get_base_head_from_event(event)

        assert base is None
        assert head is None

    def test_parse_diff_lines(self):
        """Test parse_diff_lines method."""
        diff_lines = [
            "@@ -1,3 +1,4 @@",
            " def test_function():",
            "+    return True",
            " pass",
        ]

        parsed = self.generator._parse_diff_lines(diff_lines)

        assert len(parsed) > 0
        assert any("return True" in line for line in parsed)

    def test_is_function_changed(self):
        """Test is_function_changed method."""
        diff_lines = ["+def new_function():", "-def old_function():"]

        assert self.generator._is_function_changed(diff_lines, "new_function") is True
        assert self.generator._is_function_changed(diff_lines, "old_function") is True
        assert (
            self.generator._is_function_changed(diff_lines, "other_function") is False
        )

    def test_is_class_changed(self):
        """Test is_class_changed method."""
        diff_lines = ["+class NewClass:", "-class OldClass:"]

        assert self.generator._is_class_changed(diff_lines, "NewClass") is True
        assert self.generator._is_class_changed(diff_lines, "OldClass") is True
        assert self.generator._is_class_changed(diff_lines, "OtherClass") is False

    def test_get_class_name(self):
        """Test get_class_name method."""
        # Test with valid class definition
        line = "class TestClass:"
        class_name = self.generator._get_class_name(line)
        assert class_name == "TestClass"

        # Test with invalid line
        line = "def test_function():"
        class_name = self.generator._get_class_name(line)
        assert class_name is None

    def test_get_function_context(self):
        """Test get_function_context method."""
        lines = [
            "def test_function():",
            "    return True",
            "    ",
            "def other_function():",
        ]

        context = self.generator._get_function_context(lines, 0)
        assert "def test_function():" in context
        assert "return True" in context

    def test_get_class_context(self):
        """Test get_class_context method."""
        lines = [
            "class TestClass:",
            "    def method(self):",
            "        return True",
            "    ",
            "class OtherClass:",
        ]

        context = self.generator._get_class_context(lines, 0)
        assert "class TestClass:" in context
        assert "def method(self):" in context


class TestTestGeneration:
    """Test test generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="local",
            llm_api_key=None,
            analyze_coverage_gaps=False,
        )
        self.generator = EnhancedTestGenerator(self.config)

    def test_generate_tests_with_llm_no_client(self):
        """Test generate_tests_with_llm when no client available."""
        changes = [CodeChange("test.py", "function", "test_func")]

        result = self.generator._generate_tests_with_llm(changes)
        assert result == []

    def test_create_llm_prompt(self):
        """Test create_llm_prompt method."""
        changes = [
            CodeChange("test.py", "function", "test_func", context="def test_func():")
        ]

        prompt = self.generator._create_llm_prompt(changes)

        assert "test_func" in prompt
        assert "def test_func():" in prompt
        assert "test case" in prompt.lower()

    def test_generate_tests_with_templates_function(self):
        """Test generate_tests_with_templates for function."""
        changes = [CodeChange("test.py", "function", "test_func")]

        tests = self.generator._generate_tests_with_templates(changes)

        assert len(tests) > 0
        assert any("test_func" in test for test in tests)

    def test_generate_tests_with_templates_class(self):
        """Test generate_tests_with_templates for class."""
        changes = [CodeChange("test.py", "class", "TestClass")]

        tests = self.generator._generate_tests_with_templates(changes)

        assert len(tests) > 0
        assert any("TestClass" in test for test in tests)

    def test_generate_tests_with_templates_generic(self):
        """Test generate_tests_with_templates for generic changes."""
        changes = [CodeChange("test.py", "generic", "unknown")]

        tests = self.generator._generate_tests_with_templates(changes)

        assert len(tests) > 0

    def test_generate_test_cases(self):
        """Test generate_test_cases method."""
        changes = [CodeChange("test.py", "function", "test_func")]

        test_cases = self.generator._generate_test_cases(changes)

        assert len(test_cases) > 0
        assert all("def test_" in case for case in test_cases)

    def test_generate_coverage_tests(self):
        """Test generate_coverage_tests method."""
        changes = [CodeChange("test.py", "function", "test_func")]

        tests = self.generator._generate_coverage_tests(changes)

        assert len(tests) > 0

    def test_generate_class_tests(self):
        """Test generate_class_tests method."""
        changes = [CodeChange("test.py", "class", "TestClass")]

        tests = self.generator._generate_class_tests(changes)

        assert len(tests) > 0

    def test_generate_generic_tests(self):
        """Test generate_generic_tests method."""
        changes = [CodeChange("test.py", "generic", "unknown")]

        tests = self.generator._generate_generic_tests(changes)

        assert len(tests) > 0


class TestCoverageAnalysis:
    """Test coverage analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="local",
            llm_api_key=None,
            analyze_coverage_gaps=True,
        )
        self.generator = EnhancedTestGenerator(self.config)

    def test_analyze_coverage_gaps_disabled(self):
        """Test analyze_coverage_gaps when disabled."""
        config = TestGenConfig(analyze_coverage_gaps=False)
        generator = EnhancedTestGenerator(config)

        gaps = generator._analyze_coverage_gaps(["test.py"])
        assert gaps == []

    def test_analyze_coverage_gaps_empty_files(self):
        """Test analyze_coverage_gaps with empty file list."""
        gaps = self.generator._analyze_coverage_gaps([])
        assert gaps == []

    def test_analyze_coverage_gaps_non_python_files(self):
        """Test analyze_coverage_gaps with non-Python files."""
        gaps = self.generator._analyze_coverage_gaps(["test.txt", "test.md"])
        assert gaps == []


class TestFileOperations:
    """Test file operations functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="local",
            llm_api_key=None,
            analyze_coverage_gaps=False,
        )
        self.generator = EnhancedTestGenerator(self.config)

    @patch("builtins.open", mock_open())
    @patch("pathlib.Path.exists", return_value=True)
    def test_generate_test_file_empty_changes(self, mock_exists, mock_file):
        """Test generate_test_file with empty changes."""
        result = self.generator._generate_test_file("test.py", [])
        assert result is None

    @patch("builtins.open", mock_open())
    @patch("pathlib.Path.exists", return_value=True)
    def test_generate_test_file_with_changes(self, mock_exists, mock_file):
        """Test generate_test_file with changes."""
        changes = [CodeChange("test.py", "function", "test_func")]

        result = self.generator._generate_test_file("test.py", changes)

        assert result is not None
        mock_file.assert_called()

    def test_generate_tests_empty_files(self):
        """Test generate_tests with empty file list."""
        result = self.generator.generate_tests([])
        assert result == []

    def test_generate_tests_no_changes(self):
        """Test generate_tests with no changes."""
        with patch.object(self.generator, "analyze_code_changes", return_value=[]):
            result = self.generator.generate_tests(["test.py"])
            assert result == []

    def test_generate_tests_with_changes(self):
        """Test generate_tests with changes."""
        changes = [CodeChange("test.py", "function", "test_func")]

        with patch.object(self.generator, "analyze_code_changes", return_value=changes):
            with patch.object(
                self.generator, "_generate_test_file", return_value="test_test.py"
            ):
                result = self.generator.generate_tests(["test.py"])
                assert len(result) > 0

    def test_generate_tests_for_changes_empty(self):
        """Test generate_tests_for_changes with empty changes."""
        result = self.generator.generate_tests_for_changes([])
        assert result == []

    def test_generate_tests_for_changes_with_changes(self):
        """Test generate_tests_for_changes with changes."""
        changes = [CodeChange("test.py", "function", "test_func")]

        with patch.object(
            self.generator, "_generate_test_file", return_value="test_test.py"
        ):
            result = self.generator.generate_tests_for_changes(changes)
            assert len(result) > 0

    def test_generate_function_test(self):
        """Test generate_function_test method."""
        change = CodeChange("test.py", "function", "test_func")

        test = self.generator._generate_function_test(change)

        assert "def test_test_func" in test
        assert "test_func" in test


class TestMainFunction:
    """Test main function and CLI interface."""

    def test_main_function_no_args(self):
        """Test main function with no arguments."""
        with patch("sys.argv", ["enhanced_testgen.py"]):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
            ) as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.generate_tests.return_value = []

                result = main()
                assert result == 0

    def test_main_function_with_args(self):
        """Test main function with arguments."""
        with patch("sys.argv", ["enhanced_testgen.py", "--files", "test.py"]):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
            ) as mock_generator:
                mock_instance = Mock()
                mock_generator.return_value = mock_instance
                mock_instance.generate_tests.return_value = []

                result = main()
                assert result == 0

    def test_main_function_exception(self):
        """Test main function with exception."""
        with patch("sys.argv", ["enhanced_testgen.py"]):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator",
                side_effect=Exception("Test error"),
            ):
                result = main()
                assert result == 1

    def test_main_function_keyboard_interrupt(self):
        """Test main function with keyboard interrupt."""
        with patch("sys.argv", ["enhanced_testgen.py"]):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator",
                side_effect=KeyboardInterrupt(),
            ):
                result = main()
                assert result == 1


class TestBackwardCompatibility:
    """Test backward compatibility aliases."""

    def test_test_generation_config_alias(self):
        """Test TestGenerationConfig alias."""
        assert TestGenerationConfig is TestGenConfig

    def test_test_template_alias(self):
        """Test TestTemplate alias."""
        assert TestGenTemplate is not None
