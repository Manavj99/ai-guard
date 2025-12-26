"""Basic tests for enhanced_testgen.py module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    EnhancedTestGenerator,
    CodeChange,
    TestGenTemplate,
)


class TestTestGenConfig:
    """Test TestGenConfig class."""

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

    def test_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = TestGenConfig(
            llm_provider="anthropic", llm_api_key="test-key", test_framework="unittest"
        )

        config_dict = config.to_dict()

        assert config_dict["llm_provider"] == "anthropic"
        assert config_dict["llm_api_key"] == "test-key"
        assert config_dict["test_framework"] == "unittest"

    def test_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "llm_provider": "local",
            "llm_api_key": None,
            "test_framework": "pytest",
        }

        config = TestGenConfig.from_dict(config_dict)

        assert config.llm_provider == "local"
        assert config.llm_api_key is None
        assert config.test_framework == "pytest"

    def test_validate_valid_config(self):
        """Test validation with valid configuration."""
        config = TestGenConfig(
            llm_provider="openai", llm_api_key="test-key", test_framework="pytest"
        )

        assert config.validate() is True

    def test_validate_invalid_llm_provider(self):
        """Test validation with invalid LLM provider."""
        config = TestGenConfig(llm_provider="invalid")
        assert config.validate() is False

    def test_validate_missing_api_key(self):
        """Test validation with missing API key."""
        config = TestGenConfig(llm_provider="openai", llm_api_key=None)
        assert config.validate() is False


class TestCodeChange:
    """Test CodeChange class."""

    def test_code_change_creation(self):
        """Test CodeChange creation."""
        change = CodeChange(
            file_path="test_file.py",
            function_name="test_function",
            class_name="TestClass",
            change_type="added",
            line_numbers=(1, 5),
            code_snippet="def test_function(): pass",
        )

        assert change.file_path == "test_file.py"
        assert change.function_name == "test_function"
        assert change.class_name == "TestClass"
        assert change.change_type == "added"
        assert change.line_numbers == (1, 5)
        assert change.code_snippet == "def test_function(): pass"

    def test_code_change_to_dict(self):
        """Test CodeChange to dictionary conversion."""
        change = CodeChange(
            file_path="test_file.py", function_name="test_function", change_type="added"
        )

        change_dict = change.to_dict()

        assert change_dict["file_path"] == "test_file.py"
        assert change_dict["function_name"] == "test_function"
        assert change_dict["change_type"] == "added"


class TestTestGenTemplate:
    """Test TestGenTemplate class."""

    def test_test_gen_template_creation(self):
        """Test TestGenTemplate creation."""
        template = TestGenTemplate(
            name="unit_test",
            description="Unit test template",
            template="def test_{function_name}(): pass",
            variables=["function_name"],
            applicable_to=["function"],
        )

        assert template.name == "unit_test"
        assert template.description == "Unit test template"
        assert template.template == "def test_{function_name}(): pass"
        assert template.variables == ["function_name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator class."""

    def test_init_default_config(self):
        """Test initialization with default configuration."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        assert generator.config.llm_provider == "openai"
        assert generator.config.test_framework == "pytest"
        assert generator.llm_client is None

    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        config = TestGenConfig(llm_provider="anthropic", llm_api_key="test-key")

        generator = EnhancedTestGenerator(config=config)

        assert generator.config.llm_provider == "anthropic"
        assert generator.config.llm_api_key == "test-key"

    def test_analyze_file_structure(self):
        """Test file structure analysis."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class TestClass:
    def method1(self):
        return True

def standalone_function():
    return "hello"
"""
            )
            temp_file = f.name

        try:
            structure = generator._analyze_file_structure(temp_file)

            assert "classes" in structure
            assert "functions" in structure
            assert "imports" in structure

            # Check classes
            assert len(structure["classes"]) == 1
            assert structure["classes"][0]["name"] == "TestClass"

            # Check functions
            assert len(structure["functions"]) == 1
            assert structure["functions"][0]["name"] == "standalone_function"

        finally:
            os.unlink(temp_file)

    def test_analyze_file_structure_nonexistent_file(self):
        """Test file structure analysis with non-existent file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        structure = generator._analyze_file_structure("nonexistent.py")

        assert structure == {"classes": [], "functions": [], "imports": []}

    def test_generate_test_context(self):
        """Test test context generation."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class Calculator:
    def add(self, a, b):
        return a + b
"""
            )
            temp_file = f.name

        try:
            context = generator._generate_test_context(temp_file, "Calculator.add")

            assert context.file_path == temp_file
            assert context.function_name == "add"
            assert context.class_name == "Calculator"

        finally:
            os.unlink(temp_file)

    def test_generate_test_context_function_not_found(self):
        """Test test context generation for non-existent function."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def existing_function(): pass")
            temp_file = f.name

        try:
            context = generator._generate_test_context(
                temp_file, "nonexistent_function"
            )

            # Should return None for non-existent function
            assert context is None

        finally:
            os.unlink(temp_file)

    def test_generate_unit_test(self):
        """Test unit test generation."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        context = TestContext(
            file_path="test_file.py", function_name="add", class_name="Calculator"
        )

        test_case = generator._generate_unit_test(context)

        assert test_case.name == "test_add"
        assert test_case.test_type == "unit"
        assert test_case.complexity == "simple"
        assert "def test_add" in test_case.code

    def test_generate_test_suite(self):
        """Test test suite generation."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class Calculator:
    def add(self, a, b):
        return a + b
"""
            )
            temp_file = f.name

        try:
            suite = generator._generate_test_suite(temp_file)

            assert suite.file_path == temp_file
            assert suite.framework == "pytest"
            assert len(suite.test_cases) > 0

        finally:
            os.unlink(temp_file)

    def test_generate_test_suite_nonexistent_file(self):
        """Test test suite generation for non-existent file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        suite = generator._generate_test_suite("nonexistent.py")

        # Should return None for non-existent file
        assert suite is None

    def test_save_test_suite(self):
        """Test test suite saving."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_cases = [
                TestCase("test_example", "unit", "simple", "def test_example(): pass")
            ]

            suite = TestSuite(
                file_path="test_file.py", test_cases=test_cases, framework="pytest"
            )

            # Update config to use temp directory
            generator.config.output_directory = temp_dir

            result = generator._save_test_suite(suite)

            assert result is True

            # Check if file was created
            test_file_path = Path(temp_dir) / "test_file_test.py"
            assert test_file_path.exists()

    def test_generate_tests_for_file(self):
        """Test test generation for a file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def simple_function(x):
    return x * 2
"""
            )
            temp_file = f.name

        try:
            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                generator.config.output_directory = temp_dir

                result = generator.generate_tests_for_file(temp_file)

                assert result is True

                # Check if test file was created
                test_file_path = Path(temp_dir) / f"{Path(temp_file).stem}_test.py"
                assert test_file_path.exists()

        finally:
            os.unlink(temp_file)

    def test_generate_tests_for_file_nonexistent(self):
        """Test test generation for non-existent file."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        result = generator.generate_tests_for_file("nonexistent.py")

        # Should return False for non-existent file
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
