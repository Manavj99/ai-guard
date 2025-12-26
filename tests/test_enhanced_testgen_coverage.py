"""Comprehensive tests for enhanced_testgen.py to improve coverage."""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    TestGenTemplate,
    CodeChange,
    EnhancedTestGenerator,
)


class TestTestGenConfig:
    """Test TestGenConfig class."""

    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = TestGenConfig()
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.1
        assert config.test_framework == "pytest"
        assert config.generate_mocks is True
        assert config.generate_parametrized_tests is True
        assert config.generate_edge_cases is True
        assert config.max_tests_per_file == 10
        assert config.analyze_coverage_gaps is True
        assert config.min_coverage_threshold == 80.0
        assert config.output_directory == "tests/unit"
        assert config.test_file_suffix == "_test.py"
        assert config.include_docstrings is True
        assert config.include_type_hints is True

    def test_custom_initialization(self):
        """Test custom configuration initialization."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_model="claude-3",
            llm_temperature=0.5,
            test_framework="unittest",
            generate_mocks=False,
            max_tests_per_file=5,
            output_directory="custom_tests",
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.llm_temperature == 0.5
        assert config.test_framework == "unittest"
        assert config.generate_mocks is False
        assert config.max_tests_per_file == 5
        assert config.output_directory == "custom_tests"

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = TestGenConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "openai"
        assert config_dict["llm_model"] == "gpt-4"
        assert config_dict["test_framework"] == "pytest"

    def test_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3",
            "test_framework": "unittest",
        }
        config = TestGenConfig.from_dict(config_dict)
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.test_framework == "unittest"
        # Check that defaults are still applied for missing keys
        assert config.llm_temperature == 0.1
        assert config.generate_mocks is True


class TestTestGenTemplate:
    """Test TestGenTemplate class."""

    def test_template_initialization(self):
        """Test template initialization."""
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

    def test_render_template(self):
        """Test template rendering."""
        template = TestGenTemplate(
            name="test_template",
            description="A test template",
            template="def test_{name}(): {content}",
            variables=["name", "content"],
            applicable_to=["function"],
        )

        rendered = template.render(name="my_function", content="assert True")
        assert "def test_my_function():" in rendered
        assert "assert True" in rendered

    def test_render_template_missing_variables(self):
        """Test template rendering with missing variables."""
        template = TestGenTemplate(
            name="test_template",
            description="A test template",
            template="def test_{name}(): pass",
            variables=["name"],
            applicable_to=["function"],
        )

        # Should handle missing variables gracefully
        rendered = template.render()
        assert "def test_" in rendered


class TestCodeChange:
    """Test CodeChange class."""

    def test_code_change_initialization(self):
        """Test code change initialization."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def test_func(): pass",
            context="test context",
        )
        assert change.file_path == "test.py"
        assert change.function_name == "test_func"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_numbers == (10, 15)
        assert change.code_snippet == "def test_func(): pass"
        assert change.context == "test context"

    def test_to_dict(self):
        """Test converting code change to dictionary."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )
        change_dict = change.to_dict()
        assert isinstance(change_dict, dict)
        assert change_dict["file_path"] == "test.py"
        assert change_dict["function_name"] == "test_func"


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator class."""

    def test_initialization(self):
        """Test generator initialization."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)
        assert generator.config == config
        assert generator.test_templates is not None
        assert generator.llm_client is not None

    def test_load_test_templates(self):
        """Test loading test templates."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)
        templates = generator._load_test_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Check that we have expected template types
        template_names = [t.name for t in templates]
        assert "function_test" in template_names
        assert "function_parametrized_test" in template_names
        assert "function_error_test" in template_names

    @patch("src.ai_guard.generators.enhanced_testgen.openai")
    def test_initialize_llm_client_openai(self, mock_openai):
        """Test LLM client initialization with OpenAI."""
        config = TestGenConfig(llm_provider="openai")
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is not None
        mock_openai.OpenAI.assert_called_once()

    @patch("src.ai_guard.generators.enhanced_testgen.anthropic")
    def test_initialize_llm_client_anthropic(self, mock_anthropic):
        """Test LLM client initialization with Anthropic."""
        config = TestGenConfig(llm_provider="anthropic")
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is not None
        mock_anthropic.Anthropic.assert_called_once()

    def test_initialize_llm_client_local(self):
        """Test LLM client initialization with local provider."""
        config = TestGenConfig(llm_provider="local")
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is not None

    def test_initialize_llm_client_invalid(self):
        """Test LLM client initialization with invalid provider."""
        config = TestGenConfig(llm_provider="invalid")
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is not None  # Should fallback to mock

    def test_analyze_source_code_function(self):
        """Test analyzing source code for function."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        source_code = """
def add(a, b):
    return a + b
"""

        changes = generator.analyze_source_code(source_code, "test.py")
        assert isinstance(changes, list)
        assert len(changes) > 0

        # Should find the function
        function_changes = [c for c in changes if c.change_type == "function"]
        assert len(function_changes) > 0
        assert function_changes[0].function_name == "add"

    def test_analyze_source_code_class(self):
        """Test analyzing source code for class."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        source_code = """
class Calculator:
    def add(self, a, b):
        return a + b
"""

        changes = generator.analyze_source_code(source_code, "test.py")
        assert isinstance(changes, list)

        # Should find the class
        class_changes = [c for c in changes if c.change_type == "class"]
        assert len(class_changes) > 0
        assert class_changes[0].class_name == "Calculator"

    def test_analyze_source_code_invalid_syntax(self):
        """Test analyzing source code with invalid syntax."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        source_code = "invalid syntax here"

        changes = generator.analyze_source_code(source_code, "test.py")
        assert changes == []

    def test_generate_test_function(self):
        """Test generating test for function."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="test.py",
            function_name="add",
            change_type="function",
            code_snippet="def add(a, b): return a + b",
        )

        test_code = generator.generate_test(change)
        assert isinstance(test_code, str)
        assert "def test_add" in test_code
        assert "add(" in test_code

    def test_generate_test_class(self):
        """Test generating test for class."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="test.py",
            class_name="Calculator",
            change_type="class",
            code_snippet="class Calculator: pass",
        )

        test_code = generator.generate_test(change)
        assert isinstance(test_code, str)
        assert "Calculator" in test_code

    @patch("src.ai_guard.generators.enhanced_testgen.LLMTestGenerator")
    def test_generate_test_with_llm(self, mock_llm_generator):
        """Test generating test with LLM."""
        config = TestGenConfig(llm_provider="openai")
        generator = EnhancedTestGenerator(config)

        # Mock LLM response
        mock_llm_generator.return_value.generate_test.return_value = (
            "def test_add(): assert True"
        )

        change = CodeChange(
            file_path="test.py",
            function_name="add",
            change_type="function",
            code_snippet="def add(a, b): return a + b",
        )

        test_code = generator.generate_test(change)
        assert isinstance(test_code, str)
        assert "def test_add" in test_code

    def test_generate_test_file(self):
        """Test generating test file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="calculator.py",
                function_name="add",
                change_type="function",
                code_snippet="def add(a, b): return a + b",
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_calculator.py")
            generator.generate_test_file(changes, output_path)

            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
                assert "def test_add" in content

    def test_generate_tests_for_file(self):
        """Test generating tests for a file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        source_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(source_code)
            temp_file = f.name

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "test_temp.py")
                generator.generate_tests_for_file(temp_file, output_path)

                assert os.path.exists(output_path)
                with open(output_path, "r") as f:
                    content = f.read()
                    assert "def test_add" in content
                    assert "def test_subtract" in content
        finally:
            os.unlink(temp_file)

    def test_generate_tests_for_file_nonexistent(self):
        """Test generating tests for nonexistent file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_nonexistent.py")
            generator.generate_tests_for_file("nonexistent.py", output_path)

            # Should not create output file for nonexistent input
            assert not os.path.exists(output_path)

    def test_generate_tests_for_directory(self):
        """Test generating tests for directory."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test Python files
            test_file1 = os.path.join(temp_dir, "module1.py")
            test_file2 = os.path.join(temp_dir, "module2.py")

            with open(test_file1, "w") as f:
                f.write("def func1(): pass")

            with open(test_file2, "w") as f:
                f.write("def func2(): pass")

            output_dir = os.path.join(temp_dir, "tests")
            os.makedirs(output_dir, exist_ok=True)

            generator.generate_tests_for_directory(temp_dir, output_dir)

            # Check that test files were created
            test_files = [f for f in os.listdir(output_dir) if f.endswith("_test.py")]
            assert len(test_files) >= 2

    def test_analyze_coverage_gaps(self):
        """Test analyzing coverage gaps."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        source_code = """
def covered_function():
    return "covered"

def uncovered_function():
    return "uncovered"
"""

        # Mock coverage data
        coverage_data = {
            "covered_function": {"covered": True, "lines": [1, 2, 3]},
            "uncovered_function": {"covered": False, "lines": [5, 6, 7]},
        }

        gaps = generator.analyze_coverage_gaps(source_code, coverage_data)
        assert isinstance(gaps, list)
        assert len(gaps) > 0

    def test_validate_generated_tests(self):
        """Test validating generated tests."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        test_code = """
import pytest

def test_add():
    assert add(1, 2) == 3

def add(a, b):
    return a + b
"""

        is_valid = generator.validate_generated_tests(test_code)
        assert is_valid is True

    def test_validate_generated_tests_invalid(self):
        """Test validating invalid generated tests."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        test_code = "invalid python syntax"

        is_valid = generator.validate_generated_tests(test_code)
        assert is_valid is False

    def test_get_test_statistics(self):
        """Test getting test statistics."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        stats = generator.get_test_statistics()
        assert isinstance(stats, dict)
        assert "total_tests_generated" in stats
        assert "total_files_processed" in stats
        assert "average_tests_per_file" in stats

    def test_clear_statistics(self):
        """Test clearing test statistics."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Generate some statistics
        generator.get_test_statistics()

        # Clear statistics
        generator.clear_statistics()

        stats = generator.get_test_statistics()
        assert stats["total_tests_generated"] == 0
        assert stats["total_files_processed"] == 0
