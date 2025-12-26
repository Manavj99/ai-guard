"""Comprehensive tests for enhanced_testgen.py to improve coverage."""

import pytest
import tempfile
import json
import ast
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    TestGenTemplate,
    CodeChange,
    EnhancedTestGenerator,
)


class TestTestGenConfig:
    """Test TestGenConfig class."""

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

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_model="claude-3",
            llm_temperature=0.5,
            max_tests_per_file=20,
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.llm_temperature == 0.5
        assert config.max_tests_per_file == 20


class TestTestGenTemplate:
    """Test TestGenTemplate class."""

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
        assert template.variables == ["name"]
        assert template.applicable_to == ["function"]


class TestCodeChange:
    """Test CodeChange class."""

    def test_code_change_creation(self):
        """Test creating a code change."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            code_snippet="def test_func(): pass",
            line_number=10,
        )
        assert change.file_path == "test.py"
        assert change.function_name == "test_func"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_number == 10


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator class."""

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

    def test_initialize_llm_client_local(self, config):
        """Test initializing local LLM client."""
        config.llm_provider = "local"
        config.llm_api_key = "test-key"  # Add API key for local provider
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is not None

    def test_initialize_llm_client_openai(self, config):
        """Test initializing OpenAI LLM client."""
        config.llm_provider = "openai"
        config.llm_api_key = "test-key"

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                Mock() if name == "openai" else __import__(name, *args, **kwargs)
            ),
        ):
            generator = EnhancedTestGenerator(config)
            # The generator should initialize without error
            assert generator.llm_client is not None

    def test_initialize_llm_client_anthropic(self, config):
        """Test initializing Anthropic LLM client."""
        config.llm_provider = "anthropic"
        config.llm_api_key = "test-key"

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                Mock() if name == "anthropic" else __import__(name, *args, **kwargs)
            ),
        ):
            generator = EnhancedTestGenerator(config)
            # The generator should initialize without error
            assert generator.llm_client is not None

    def test_initialize_llm_client_invalid(self, config):
        """Test initializing invalid LLM client."""
        config.llm_provider = "invalid"

        # Should not raise an exception, just return None
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is None

    def test_analyze_code_changes_empty_files(self, generator):
        """Test analyzing empty file list."""
        result = generator.analyze_code_changes([])
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

    def test_get_base_head_from_event_invalid_path(self, generator):
        """Test getting base/head from invalid event path."""
        result = generator._get_base_head_from_event("nonexistent.json")
        assert result is None

    def test_get_base_head_from_event_valid_event(self, generator):
        """Test getting base/head from valid event."""
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

    def test_get_class_name(self, generator):
        """Test getting class name from function node."""
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

    def test_get_function_context(self, generator):
        """Test getting function context."""
        # Create a mock function node
        func_node = Mock()
        func_node.name = "test_function"
        func_node.args = Mock()
        func_node.args.args = [Mock(arg="param1"), Mock(arg="param2")]

        result = generator._get_function_context(func_node)
        assert "test_function" in result
        assert "param1" in result
        assert "param2" in result

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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function():\n    return 'hello'")
            f.flush()

            try:
                with patch.object(generator, "analyze_code_changes", return_value=[]):
                    result = generator.generate_tests([f.name])
                    assert result == ""
            finally:
                Path(f.name).unlink()

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

    def test_analyze_coverage_gaps(self, generator):
        """Test analyzing coverage gaps."""
        result = generator.analyze_coverage_gaps(["test.py"])
        assert isinstance(result, dict)

    def test_analyze_coverage_gaps_empty(self, generator):
        """Test analyzing coverage gaps with empty file list."""
        result = generator.analyze_coverage_gaps([])
        assert result == {}


class TestEnhancedTestGeneratorIntegration:
    """Integration tests for EnhancedTestGenerator."""

    def test_full_workflow(self):
        """Test full workflow from config to test generation."""
        config = TestGenConfig(
            llm_provider="local", test_framework="pytest", generate_mocks=True
        )

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=Mock()
        ):
            generator = EnhancedTestGenerator(config)

            # Create a test file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(
                    """
def add_numbers(a, b):
    '''Add two numbers together.'''
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""
                )
                f.flush()

                try:
                    # Analyze the file
                    changes = generator.analyze_code_changes([f.name])

                    # Generate tests
                    test_content = generator.generate_tests_for_changes(changes)

                    assert isinstance(test_content, str)
                    assert len(test_content) > 0
                finally:
                    Path(f.name).unlink()


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
