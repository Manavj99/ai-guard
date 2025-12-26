"""Comprehensive tests for enhanced_testgen.py to achieve 80% coverage."""

import pytest
import tempfile
import json
import ast
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    TestGenTemplate,
    CodeChange,
    EnhancedTestGenerator,
)


class TestTestGenConfigComprehensive:
    """Comprehensive tests for TestGenConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TestGenConfig()
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.1
        assert config.test_framework == "pytest"
        assert config.generate_mocks is True
        assert config.max_tests_per_file == 10
        assert config.min_coverage_threshold == 80.0

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = TestGenConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "openai"
        assert config_dict["test_framework"] == "pytest"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3",
            "llm_temperature": 0.5,
            "max_tests_per_file": 20,
        }
        config = TestGenConfig.from_dict(config_dict)
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.llm_temperature == 0.5
        assert config.max_tests_per_file == 20

    def test_config_validation_valid(self):
        """Test config validation with valid values."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=90.0,
            output_directory="tests",
        )
        assert config.validate() is True

    def test_config_validation_invalid_provider(self):
        """Test config validation with invalid provider."""
        config = TestGenConfig(llm_provider="invalid")
        assert config.validate() is False

    def test_config_validation_missing_api_key(self):
        """Test config validation with missing API key."""
        config = TestGenConfig(llm_provider="openai", llm_api_key=None)
        assert config.validate() is False

    def test_config_validation_invalid_temperature(self):
        """Test config validation with invalid temperature."""
        config = TestGenConfig(llm_temperature=1.5)
        assert config.validate() is False

    def test_config_validation_invalid_framework(self):
        """Test config validation with invalid framework."""
        config = TestGenConfig(test_framework="invalid")
        assert config.validate() is False

    def test_config_validation_invalid_max_tests(self):
        """Test config validation with invalid max tests."""
        config = TestGenConfig(max_tests_per_file=0)
        assert config.validate() is False

    def test_config_validation_invalid_coverage_threshold(self):
        """Test config validation with invalid coverage threshold."""
        config = TestGenConfig(min_coverage_threshold=150.0)
        assert config.validate() is False

    def test_config_validation_empty_output_directory(self):
        """Test config validation with empty output directory."""
        config = TestGenConfig(output_directory="")
        assert config.validate() is False


class TestCodeChangeComprehensive:
    """Comprehensive tests for CodeChange class."""

    def test_code_change_creation(self):
        """Test creating a code change."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            line_numbers=(10, 20),
            code_snippet="def test_func(): pass",
            context="Test function",
            line_number=10,
            content="def test_func(): pass",
        )
        assert change.file_path == "test.py"
        assert change.function_name == "test_func"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_numbers == (10, 20)
        assert change.code_snippet == "def test_func(): pass"
        assert change.context == "Test function"
        assert change.line_number == 10
        assert change.content == "def test_func(): pass"

    def test_code_change_to_dict(self):
        """Test converting code change to dictionary."""
        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )
        change_dict = change.to_dict()
        assert isinstance(change_dict, dict)
        assert change_dict["file_path"] == "test.py"
        assert change_dict["function_name"] == "test_func"
        assert change_dict["change_type"] == "function"


class TestTestGenTemplateComprehensive:
    """Comprehensive tests for TestGenTemplate class."""

    def test_template_creation(self):
        """Test creating a test template."""
        template = TestGenTemplate(
            name="test_template",
            description="A test template",
            template="def test_{name}(): pass",
            variables=["name"],
            applicable_to=["function"],
        )
        assert template.name == "test_template"
        assert template.description == "A test template"
        assert template.template == "def test_{name}(): pass"
        assert template.variables == ["name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGeneratorComprehensive:
    """Comprehensive tests for EnhancedTestGenerator class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return TestGenConfig(
            llm_provider="local", llm_api_key="test-key", llm_model="test-model"
        )

    @pytest.fixture
    def generator(self, config):
        """Create a test generator with mocked LLM client."""
        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=Mock()
        ):
            return EnhancedTestGenerator(config)

    def test_generator_initialization(self, config):
        """Test generator initialization."""
        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=Mock()
        ):
            generator = EnhancedTestGenerator(config)
            assert generator.config == config
            assert generator.test_templates is not None
            assert generator.llm_client is not None

    def test_load_test_templates(self, generator):
        """Test loading test templates."""
        templates = generator._load_test_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Check that we have the expected templates
        template_names = [t.name for t in templates]
        assert "function_test" in template_names
        assert "function_parametrized_test" in template_names
        assert "function_error_test" in template_names
        assert "class_test" in template_names
        assert "edge_case_test" in template_names
        assert "integration_test" in template_names
        assert "performance_test" in template_names
        assert "coverage_test" in template_names

    def test_initialize_llm_client_no_api_key(self, config):
        """Test initializing LLM client without API key."""
        config.llm_api_key = None
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is None

    def test_initialize_llm_client_local(self, config):
        """Test initializing local LLM client."""
        config.llm_provider = "local"
        config.llm_api_key = "test-key"
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is not None

    def test_initialize_llm_client_openai_success(self, config):
        """Test successful OpenAI LLM client initialization."""
        config.llm_provider = "openai"
        config.llm_api_key = "test-key"

        mock_openai = Mock()
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                mock_openai if name == "openai" else __import__(name, *args, **kwargs)
            ),
        ):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is not None

    def test_initialize_llm_client_openai_import_error(self, config):
        """Test OpenAI LLM client initialization with import error."""
        config.llm_provider = "openai"
        config.llm_api_key = "test-key"

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("No module named 'openai'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is None

    def test_initialize_llm_client_anthropic_success(self, config):
        """Test successful Anthropic LLM client initialization."""
        config.llm_provider = "anthropic"
        config.llm_api_key = "test-key"

        mock_anthropic = Mock()
        mock_anthropic.Anthropic.return_value = Mock()
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                mock_anthropic
                if name == "anthropic"
                else __import__(name, *args, **kwargs)
            ),
        ):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is not None

    def test_initialize_llm_client_anthropic_import_error(self, config):
        """Test Anthropic LLM client initialization with import error."""
        config.llm_provider = "anthropic"
        config.llm_api_key = "test-key"

        def mock_import(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("No module named 'anthropic'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is None

    def test_initialize_llm_client_invalid_provider(self, config):
        """Test initializing invalid LLM client."""
        config.llm_provider = "invalid"
        config.llm_api_key = "test-key"

        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is None

    def test_initialize_llm_client_exception(self, config):
        """Test LLM client initialization with exception."""
        config.llm_provider = "openai"
        config.llm_api_key = "test-key"

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                raise Exception("Unexpected error")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is None

    def test_analyze_code_changes_empty_files(self, generator):
        """Test analyzing empty file list."""
        result = generator.analyze_code_changes([])
        assert result == []

    def test_analyze_code_changes_non_python_files(self, generator):
        """Test analyzing non-Python files."""
        result = generator.analyze_code_changes(["test.txt", "test.js"])
        assert result == []

    def test_analyze_code_changes_nonexistent_file(self, generator):
        """Test analyzing nonexistent file."""
        result = generator.analyze_code_changes(["nonexistent.py"])
        assert result == []

    def test_analyze_code_changes_valid_file(self, generator):
        """Test analyzing valid Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as f:
            f.write("def test_function():\n    return 'hello'")
            f.flush()

            result = generator.analyze_code_changes([f.name])
            assert len(result) > 0
            assert any(change.function_name == "test_function" for change in result)

    def test_analyze_code_changes_syntax_error(self, generator):
        """Test analyzing file with syntax error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as f:
            f.write(
                "def test_function(\n    return 'hello'"
            )  # Missing closing parenthesis
            f.flush()

            result = generator.analyze_code_changes([f.name])
            assert result == []

    def test_analyze_code_changes_with_event_path(self, generator):
        """Test analyzing code changes with event path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            event_data = {
                "pull_request": {"head": {"ref": "feature"}, "base": {"ref": "main"}}
            }
            json.dump(event_data, f)
            f.flush()

            with patch.object(
                generator, "_get_base_head_from_event", return_value=("main", "feature")
            ):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "+++ b/test.py"

                    result = generator.analyze_code_changes(["test.py"], f.name)
                    assert isinstance(result, list)

    def test_get_file_diff_with_event_path(self, generator):
        """Test getting file diff with event path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            event_data = {
                "pull_request": {
                    "base": {"sha": "main_sha"},
                    "head": {"sha": "feature_sha"},
                }
            }
            json.dump(event_data, f)
            f.flush()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "+++ b/test.py\n@@ -1,3 +1,3 @@"

                result = generator._get_file_diff("test.py", f.name)
                assert result == "+++ b/test.py\n@@ -1,3 +1,3 @@"

    def test_get_file_diff_without_event_path(self, generator):
        """Test getting file diff without event path."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "+++ b/test.py\n@@ -1,3 +1,3 @@"

            result = generator._get_file_diff("test.py", None)
            assert result == "+++ b/test.py\n@@ -1,3 +1,3 @@"

    def test_get_file_diff_git_error(self, generator):
        """Test getting file diff with git error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""

            result = generator._get_file_diff("test.py", None)
            assert result is None

    def test_get_base_head_from_event_invalid_path(self, generator):
        """Test getting base/head from invalid event path."""
        result = generator._get_base_head_from_event("nonexistent.json")
        assert result is None

    def test_get_base_head_from_event_valid_pr_event(self, generator):
        """Test getting base/head from valid PR event."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            event_data = {
                "pull_request": {
                    "base": {"sha": "main_sha"},
                    "head": {"sha": "feature_sha"},
                }
            }
            json.dump(event_data, f)
            f.flush()

            result = generator._get_base_head_from_event(f.name)
            assert result == ("main_sha", "feature_sha")

    def test_get_base_head_from_event_valid_push_event(self, generator):
        """Test getting base/head from valid push event."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            event_data = {"before": "old_sha", "after": "new_sha"}
            json.dump(event_data, f)
            f.flush()

            result = generator._get_base_head_from_event(f.name)
            assert result == ("old_sha", "new_sha")

    def test_get_base_head_from_event_invalid_json(self, generator):
        """Test getting base/head from invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            f.write("invalid json")
            f.flush()

            result = generator._get_base_head_from_event(f.name)
            assert result is None

    def test_parse_diff_lines(self, generator):
        """Test parsing diff lines."""
        diff_content = """@@ -1,3 +1,3 @@
 def test():
-    return "old"
+    return "new"
@@ -10,5 +10,5 @@
 def another():
-    return "old2"
+    return "new2"
"""
        result = generator._parse_diff_lines(diff_content)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_diff_lines_no_matches(self, generator):
        """Test parsing diff lines with no matches."""
        diff_content = "This is not a diff"
        result = generator._parse_diff_lines(diff_content)
        assert result == []

    def test_is_function_changed(self, generator):
        """Test checking if function was changed."""
        # Create a mock function node
        func_node = Mock()
        func_node.lineno = 10
        func_node.end_lineno = 15

        changed_lines = [5, 10, 12, 20]
        result = generator._is_function_changed(func_node, changed_lines)
        assert result is True

        changed_lines = [1, 2, 3, 4]
        result = generator._is_function_changed(func_node, changed_lines)
        assert result is False

    def test_is_class_changed(self, generator):
        """Test checking if class was changed."""
        # Create a mock class node
        class_node = Mock()
        class_node.lineno = 20
        class_node.end_lineno = 30

        changed_lines = [15, 25, 35]
        result = generator._is_class_changed(class_node, changed_lines)
        assert result is True

        changed_lines = [1, 2, 3, 4]
        result = generator._is_class_changed(class_node, changed_lines)
        assert result is False

    def test_get_class_name_with_parent(self, generator):
        """Test getting class name from function node with parent."""
        # Create mock nodes
        class_node = Mock()
        class_node.name = "TestClass"

        func_node = Mock()
        func_node.parent = class_node

        result = generator._get_class_name(func_node)
        assert result == "TestClass"

    def test_get_class_name_no_parent(self, generator):
        """Test getting class name when function has no parent."""
        func_node = Mock()
        func_node.parent = None

        result = generator._get_class_name(func_node)
        assert result is None

    def test_get_class_name_nested_parents(self, generator):
        """Test getting class name with nested parents."""
        # Create mock nodes
        outer_class = Mock()
        outer_class.name = "OuterClass"

        inner_class = Mock()
        inner_class.name = "InnerClass"
        inner_class.parent = outer_class

        func_node = Mock()
        func_node.parent = inner_class

        result = generator._get_class_name(func_node)
        assert result == "InnerClass"

    def test_get_function_context(self, generator):
        """Test getting function context."""
        # Create a mock function node
        func_node = Mock()
        func_node.name = "test_function"
        func_node.args = Mock()
        func_node.args.args = [Mock(arg="param1"), Mock(arg="param2")]
        func_node.decorator_list = []
        func_node.returns = None

        result = generator._get_function_context(func_node)
        assert "test_function" in result
        assert "param1" in result
        assert "param2" in result

    def test_get_function_context_with_decorators(self, generator):
        """Test getting function context with decorators."""
        # Create a mock function node
        func_node = Mock()
        func_node.name = "test_function"
        func_node.args = Mock()
        func_node.args.args = []
        func_node.decorator_list = [Mock()]
        func_node.returns = None

        # Mock the decorator unparse
        with patch("ast.unparse", return_value="@decorator"):
            result = generator._get_function_context(func_node)
            assert "Decorators: @decorator" in result

    def test_get_function_context_with_return_annotation(self, generator):
        """Test getting function context with return annotation."""
        # Create a mock function node
        func_node = Mock()
        func_node.name = "test_function"
        func_node.args = Mock()
        func_node.args.args = []
        func_node.decorator_list = []
        func_node.returns = Mock()

        # Mock the return annotation unparse
        with patch("ast.unparse", return_value="str"):
            result = generator._get_function_context(func_node)
            assert "Returns: str" in result

    def test_get_class_context(self, generator):
        """Test getting class context."""
        # Create a mock class node
        class_node = Mock()
        class_node.name = "TestClass"
        class_node.bases = []
        class_node.body = [Mock(name="method1"), Mock(name="method2")]

        # Mock isinstance for body items
        with patch("isinstance", side_effect=lambda obj, cls: cls == ast.FunctionDef):
            result = generator._get_class_context(class_node)
            assert "Methods: method1, method2" in result

    def test_get_class_context_with_bases(self, generator):
        """Test getting class context with base classes."""
        # Create a mock class node
        class_node = Mock()
        class_node.name = "TestClass"
        class_node.bases = [Mock(), Mock()]
        class_node.body = []

        # Mock the base unparse
        with patch("ast.unparse", side_effect=["Base1", "Base2"]):
            result = generator._get_class_context(class_node)
            assert "Bases: Base1, Base2" in result

    def test_generate_tests_with_llm_no_client(self, generator):
        """Test generating tests with LLM when no client available."""
        generator.llm_client = None
        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )

        result = generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_with_llm_openai_success(self, generator):
        """Test generating tests with OpenAI LLM successfully."""
        # Mock the LLM client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def test_func(): assert True"
        mock_client.ChatCompletion.create.return_value = mock_response
        generator.llm_client = mock_client
        generator.config.llm_provider = "openai"

        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )

        result = generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_with_llm_anthropic_success(self, generator):
        """Test generating tests with Anthropic LLM successfully."""
        # Mock the LLM client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "def test_func(): assert True"
        mock_client.messages.create.return_value = mock_response
        generator.llm_client = mock_client
        generator.config.llm_provider = "anthropic"

        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )

        result = generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_with_llm_exception(self, generator):
        """Test generating tests with LLM when exception occurs."""
        # Mock the LLM client to raise an exception
        mock_client = Mock()
        mock_client.ChatCompletion.create.side_effect = Exception("API Error")
        generator.llm_client = mock_client
        generator.config.llm_provider = "openai"

        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )

        result = generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_create_llm_prompt(self, generator):
        """Test creating LLM prompt."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            context="Test function",
            code_snippet="def test_func(): pass",
        )

        prompt = generator._create_llm_prompt(change)
        assert isinstance(prompt, str)
        assert "test.py" in prompt
        assert "test_func" in prompt
        assert "function" in prompt
        assert "Test function" in prompt
        assert "def test_func(): pass" in prompt

    def test_generate_tests_with_templates_function(self, generator):
        """Test generating tests with templates for function."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(x): return x * 2",
        )

        result = generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_with_templates_class(self, generator):
        """Test generating tests with templates for class."""
        change = CodeChange(
            file_path="test.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass: pass",
        )

        result = generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "TestClass" in result

    def test_generate_tests_with_templates_other(self, generator):
        """Test generating tests with templates for other change types."""
        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="import"
        )

        result = generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_function_tests(self, generator):
        """Test generating function tests."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(x): return x * 2",
        )

        result = generator._generate_function_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_function_tests_parse_error(self, generator):
        """Test generating function tests with parse error."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="invalid python code",
        )

        result = generator._generate_function_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_test_cases(self, generator):
        """Test generating test cases."""
        # Create a mock function definition
        func_def = Mock()
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="param1"), Mock(arg="param2")]

        result = generator._generate_test_cases(func_def)
        assert isinstance(result, str)
        assert "test_input" in result
        assert "expected_output" in result

    def test_generate_coverage_tests(self, generator):
        """Test generating coverage tests."""
        # Create a mock function definition
        func_def = Mock()
        func_def.name = "test_func"
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="param1")]

        result = generator._generate_coverage_tests(func_def)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_class_tests(self, generator):
        """Test generating class tests."""
        change = CodeChange(
            file_path="test.py", class_name="TestClass", change_type="class"
        )

        result = generator._generate_class_tests(change)
        assert isinstance(result, str)
        assert "TestClass" in result

    def test_generate_generic_tests(self, generator):
        """Test generating generic tests."""
        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )

        result = generator._generate_generic_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_test_file_empty_changes(self, generator):
        """Test generating test file with empty changes."""
        result = generator.generate_test_file([], "output.py")
        assert result == ""

    def test_generate_test_file_with_changes(self, generator):
        """Test generating test file with changes."""
        changes = [
            CodeChange(
                file_path="test.py",
                function_name="test_func",
                change_type="function",
                code_snippet="def test_func(): pass",
            )
        ]

        result = generator.generate_test_file(changes, "output.py")
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_empty_files(self, generator):
        """Test generating tests with empty file list."""
        result = generator.generate_tests([])
        assert result == ""

    def test_generate_tests_with_files(self, generator):
        """Test generating tests with files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as f:
            f.write("def test_function():\n    return 'hello'")
            f.flush()

            with patch.object(generator, "analyze_code_changes", return_value=[]):
                result = generator.generate_tests([f.name])
                assert result == ""

    def test_generate_tests_for_changes_empty(self, generator):
        """Test generating tests for empty changes."""
        result = generator.generate_tests_for_changes([])
        assert result == ""

    def test_generate_tests_for_changes_with_data(self, generator):
        """Test generating tests for changes with data."""
        changes = [
            CodeChange(
                file_path="test.py", function_name="test_func", change_type="function"
            )
        ]

        result = generator.generate_tests_for_changes(changes)
        assert isinstance(result, str)

    def test_generate_function_test(self, generator):
        """Test generating function test."""
        change = CodeChange(
            file_path="test.py", function_name="test_func", change_type="function"
        )

        result = generator._generate_function_test(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_analyze_coverage_gaps_disabled(self, generator):
        """Test analyzing coverage gaps when disabled."""
        generator.config.analyze_coverage_gaps = False
        result = generator.analyze_coverage_gaps(["test.py"])
        assert result == {}

    def test_analyze_coverage_gaps_enabled(self, generator):
        """Test analyzing coverage gaps when enabled."""
        generator.config.analyze_coverage_gaps = True
        with patch.object(
            generator, "_analyze_file_coverage", return_value=["Line 10 not covered"]
        ):
            result = generator.analyze_coverage_gaps(["test.py"])
            assert isinstance(result, dict)
            assert "test.py" in result

    def test_analyze_coverage_gaps_non_python_files(self, generator):
        """Test analyzing coverage gaps with non-Python files."""
        generator.config.analyze_coverage_gaps = True
        result = generator.analyze_coverage_gaps(["test.txt", "test.js"])
        assert result == {}

    def test_analyze_file_coverage(self, generator):
        """Test analyzing file coverage."""
        with patch("subprocess.run") as mock_run:
            # Mock coverage run
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""

            result = generator._analyze_file_coverage("test.py")
            assert isinstance(result, list)

    def test_analyze_file_coverage_error(self, generator):
        """Test analyzing file coverage with error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""

            result = generator._analyze_file_coverage("test.py")
            assert result == []

    def test_analyze_function_coverage(self, generator):
        """Test analyzing function coverage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as f:
            f.write("def test_func():\n    '''Docstring'''\n    pass")
            f.flush()

            result = generator._analyze_function_coverage(f.name)
            assert isinstance(result, list)

    def test_analyze_function_coverage_error(self, generator):
        """Test analyzing function coverage with error."""
        result = generator._analyze_function_coverage("nonexistent.py")
        assert result == []

    def test_analyze_branch_coverage(self, generator):
        """Test analyzing branch coverage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as f:
            f.write(
                """
if True:
    pass
for i in range(10):
    pass
while True:
    break
try:
    pass
except:
    pass
"""
            )
            f.flush()

            result = generator._analyze_branch_coverage(f.name)
            assert isinstance(result, list)

    def test_analyze_branch_coverage_error(self, generator):
        """Test analyzing branch coverage with error."""
        result = generator._analyze_branch_coverage("nonexistent.py")
        assert result == []


def test_main_function():
    """Test the main function."""
    import sys
    from unittest.mock import patch

    test_args = [
        "enhanced_testgen.py",
        "--output",
        "test_output.py",
        "--llm-provider",
        "local",
    ]

    with patch.object(sys, "argv", test_args):
        with patch(
            "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
        ) as mock_gen:
            with patch(
                "src.ai_guard.generators.enhanced_testgen.changed_python_files",
                return_value=[],
            ):
                # This should not raise an exception
                try:
                    from src.ai_guard.generators.enhanced_testgen import main

                    main()
                except SystemExit:
                    pass  # Expected when no files changed


if __name__ == "__main__":
    pytest.main([__file__])
