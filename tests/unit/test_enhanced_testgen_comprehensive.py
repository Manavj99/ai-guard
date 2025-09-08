"""Comprehensive tests for enhanced test generator module to achieve 90%+ coverage."""

import subprocess
from unittest.mock import patch, MagicMock
from src.ai_guard.generators.enhanced_testgen import (
    TestGenerationConfig,
    CodeChange,
    TestTemplate,
    EnhancedTestGenerator,
)


class TestTestGenerationConfig:
    """Test the TestGenerationConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TestGenerationConfig()
        assert config.llm_provider == "openai"
        assert config.llm_api_key is None
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

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TestGenerationConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model="claude-3",
            llm_temperature=0.5,
            test_framework="unittest",
            generate_mocks=False,
            generate_parametrized_tests=False,
            generate_edge_cases=False,
            max_tests_per_file=5,
            analyze_coverage_gaps=False,
            min_coverage_threshold=90.0,
            output_directory="__tests__",
            test_file_suffix=".test.py",
            include_docstrings=False,
            include_type_hints=False,
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "test_key"
        assert config.llm_model == "claude-3"
        assert config.llm_temperature == 0.5
        assert config.test_framework == "unittest"
        assert config.generate_mocks is False
        assert config.generate_parametrized_tests is False
        assert config.generate_edge_cases is False
        assert config.max_tests_per_file == 5
        assert config.analyze_coverage_gaps is False
        assert config.min_coverage_threshold == 90.0
        assert config.output_directory == "__tests__"
        assert config.test_file_suffix == ".test.py"
        assert config.include_docstrings is False
        assert config.include_type_hints is False


class TestCodeChange:
    """Test the CodeChange dataclass."""

    def test_code_change_creation(self):
        """Test creating a CodeChange with all fields."""
        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function for basic arithmetic",
        )
        assert change.file_path == "src/utils.py"
        assert change.function_name == "calculate_sum"
        assert change.class_name is None
        assert change.change_type == "function"
        assert change.line_numbers == (10, 15)
        assert change.code_snippet == "def calculate_sum(a, b): return a + b"
        assert change.context == "Utility function for basic arithmetic"

    def test_code_change_class_change(self):
        """Test creating a CodeChange for a class change."""
        change = CodeChange(
            file_path="src/models/user.py",
            function_name=None,
            class_name="User",
            change_type="class",
            line_numbers=(5, 25),
            code_snippet="class User: pass",
            context="User model class",
        )
        assert change.class_name == "User"
        assert change.function_name is None
        assert change.change_type == "class"


class TestTestTemplate:
    """Test the TestTemplate dataclass."""

    def test_test_template_creation(self):
        """Test creating a TestTemplate with all fields."""
        template = TestTemplate(
            name="function_test",
            description="Basic function test",
            template="def test_{function_name}(): pass",
            variables=["function_name"],
            applicable_to=["function"],
        )
        assert template.name == "function_test"
        assert template.description == "Basic function test"
        assert template.template == "def test_{function_name}(): pass"
        assert template.variables == ["function_name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGenerator:
    """Test the EnhancedTestGenerator class."""

    @patch("src.ai_guard.generators.enhanced_testgen.openai")
    def test_init_with_openai(self, mock_openai):
        """Test initialization with OpenAI provider."""
        config = TestGenerationConfig(llm_provider="openai")
        generator = EnhancedTestGenerator(config)
        assert generator.config == config
        assert len(generator.test_templates) > 0

    @patch("src.ai_guard.generators.enhanced_testgen.anthropic")
    def test_init_with_anthropic(self, mock_anthropic):
        """Test initialization with Anthropic provider."""
        config = TestGenerationConfig(llm_provider="anthropic")
        generator = EnhancedTestGenerator(config)
        assert generator.config == config

    def test_init_with_local_provider(self):
        """Test initialization with local provider."""
        config = TestGenerationConfig(llm_provider="local")
        generator = EnhancedTestGenerator(config)
        assert generator.config == config
        assert generator.llm_client is None

    def test_load_test_templates(self):
        """Test loading of test templates."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)
        templates = generator._load_test_templates()

        assert len(templates) > 0
        assert any(t.name == "function_test" for t in templates)
        assert any(t.name == "class_test" for t in templates)

    def test_analyze_code_changes(self):
        """Test code change analysis."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                file_path="src/utils.py",
                function_name="calculate_sum",
                class_name=None,
                change_type="function",
                line_numbers=(10, 15),
                code_snippet="def calculate_sum(a, b): return a + b",
                context="Utility function",
            )
        ]

        analysis = generator.analyze_code_changes(changes)
        assert "utils.py" in analysis
        assert analysis["utils.py"]["functions"] == ["calculate_sum"]

    def test_analyze_code_changes_multiple_files(self):
        """Test code change analysis with multiple files."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                "src/utils.py",
                "calculate_sum",
                None,
                "function",
                (10, 15),
                "def calculate_sum(a, b): return a + b",
                "Utility function",
            ),
            CodeChange(
                "src/models/user.py",
                None,
                "User",
                "class",
                (5, 25),
                "class User: pass",
                "User model",
            ),
        ]

        analysis = generator.analyze_code_changes(changes)
        assert "utils.py" in analysis
        assert "user.py" in analysis
        assert analysis["utils.py"]["functions"] == ["calculate_sum"]
        assert analysis["user.py"]["classes"] == ["User"]

    def test_generate_test_file_path(self):
        """Test test file path generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        test_path = generator.generate_test_file_path("src/utils.py")
        assert test_path == "tests/unit/utils_test.py"

        # Test with custom config
        custom_config = TestGenerationConfig(
            output_directory="__tests__", test_file_suffix=".test.py"
        )
        generator.config = custom_config
        test_path = generator.generate_test_file_path("src/models/user.py")
        assert test_path == "__tests__/models/user.test.py"

    def test_generate_test_content_function(self):
        """Test test content generation for functions."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        test_content = generator.generate_test_content(change)
        assert "def test_calculate_sum" in test_content
        assert "calculate_sum" in test_content

    def test_generate_test_content_class(self):
        """Test test content generation for classes."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/models/user.py",
            function_name=None,
            class_name="User",
            change_type="class",
            line_numbers=(5, 25),
            code_snippet="class User: pass",
            context="User model",
        )

        test_content = generator.generate_test_content(change)
        assert "class TestUser" in test_content or "def test_user" in test_content

    def test_generate_test_content_with_mocks(self):
        """Test test content generation with mocks enabled."""
        config = TestGenerationConfig(generate_mocks=True)
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        test_content = generator.generate_test_content(change)
        assert "mock" in test_content.lower() or "patch" in test_content.lower()

    def test_generate_test_content_without_mocks(self):
        """Test test content generation without mocks."""
        config = TestGenerationConfig(generate_mocks=False)
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        test_content = generator.generate_test_content(change)
        # Should not contain mock-related content
        assert "mock" not in test_content.lower()

    def test_generate_parametrized_tests(self):
        """Test parametrized test generation."""
        config = TestGenerationConfig(generate_parametrized_tests=True)
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        test_content = generator.generate_test_content(change)
        # Should contain parametrized test patterns
        assert (
            "pytest.mark.parametrize" in test_content or "parametrize" in test_content
        )

    def test_generate_edge_cases(self):
        """Test edge case test generation."""
        config = TestGenerationConfig(generate_edge_cases=True)
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        test_content = generator.generate_test_content(change)
        # Should contain edge case tests
        assert (
            "edge" in test_content.lower()
            or "boundary" in test_content.lower()
            or "zero" in test_content.lower()
        )

    def test_parse_python_code(self):
        """Test Python code parsing."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        code = """
def calculate_sum(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""

        parsed = generator.parse_python_code(code)
        assert "calculate_sum" in parsed["functions"]
        assert "Calculator" in parsed["classes"]
        assert "multiply" in parsed["methods"]

    def test_parse_python_code_empty(self):
        """Test parsing empty Python code."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        parsed = generator.parse_python_code("")
        assert parsed["functions"] == []
        assert parsed["classes"] == []
        assert parsed["methods"] == []

    def test_parse_python_code_invalid_syntax(self):
        """Test parsing invalid Python syntax."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        invalid_code = "def invalid syntax {"
        parsed = generator.parse_python_code(invalid_code)
        # Should handle syntax errors gracefully
        assert isinstance(parsed, dict)

    def test_generate_test_imports(self):
        """Test test import generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        imports = generator.generate_test_imports("src/utils.py")
        assert "import pytest" in imports
        assert "from src.utils import" in imports

    def test_generate_test_imports_with_mocks(self):
        """Test test import generation with mocks."""
        config = TestGenerationConfig(generate_mocks=True)
        generator = EnhancedTestGenerator(config)

        imports = generator.generate_test_imports("src/utils.py")
        assert "unittest.mock" in imports or "pytest-mock" in imports

    def test_generate_test_imports_without_mocks(self):
        """Test test import generation without mocks."""
        config = TestGenerationConfig(generate_mocks=False)
        generator = EnhancedTestGenerator(config)

        imports = generator.generate_test_imports("src/utils.py")
        assert "unittest.mock" not in imports

    def test_generate_test_setup(self):
        """Test test setup generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        setup = generator.generate_test_setup(change)
        assert "setup" in setup.lower() or "arrange" in setup.lower()

    def test_generate_test_assertions(self):
        """Test test assertion generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        assertions = generator.generate_test_assertions(change)
        assert "assert" in assertions.lower()

    def test_generate_test_teardown(self):
        """Test test teardown generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/utils.py",
            function_name="calculate_sum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def calculate_sum(a, b): return a + b",
            context="Utility function",
        )

        teardown = generator.generate_test_teardown(change)
        assert "teardown" in teardown.lower() or "cleanup" in teardown.lower()

    def test_validate_test_content(self):
        """Test test content validation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        valid_content = """
def test_calculate_sum():
    assert calculate_sum(1, 2) == 3
"""

        validation = generator.validate_test_content(valid_content)
        assert validation["is_valid"] is True

    def test_validate_test_content_invalid(self):
        """Test test content validation with invalid content."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        invalid_content = "def invalid syntax {"

        validation = generator.validate_test_content(invalid_content)
        assert validation["is_valid"] is False

    def test_generate_coverage_report(self):
        """Test coverage report generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                "src/utils.py",
                "calculate_sum",
                None,
                "function",
                (10, 15),
                "def calculate_sum(a, b): return a + b",
                "Utility function",
            )
        ]

        report = generator.generate_coverage_report(changes)
        assert "coverage" in report
        assert "files" in report

    def test_export_test_results(self):
        """Test test results export."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        results = {"tests_generated": 5, "files_processed": 2, "coverage": 85.5}

        exported = generator.export_test_results(results)
        assert "timestamp" in exported
        assert "results" in exported
        assert exported["results"] == results

    @patch("subprocess.run")
    def test_run_tests_success(self, mock_run):
        """Test successful test execution."""
        mock_run.return_value = MagicMock(returncode=0, stdout=b"Tests passed")

        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        result = generator.run_tests("tests/")
        assert result["success"] is True
        assert result["output"] == "Tests passed"

    @patch("subprocess.run")
    def test_run_tests_failure(self, mock_run):
        """Test failed test execution."""
        mock_run.return_value = MagicMock(returncode=1, stdout=b"Tests failed")

        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        result = generator.run_tests("tests/")
        assert result["success"] is False
        assert result["output"] == "Tests failed"

    @patch("subprocess.run")
    def test_run_tests_exception(self, mock_run):
        """Test test execution with exception."""
        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        result = generator.run_tests("tests/")
        assert result["success"] is False
        assert "Command failed" in result["error"]

    def test_get_test_recommendations(self):
        """Test getting test recommendations."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        analysis = {
            "src/utils.py": {
                "functions": ["calculate_sum", "multiply"],
                "classes": [],
                "methods": [],
            }
        }

        recommendations = generator.get_test_recommendations(analysis)
        assert len(recommendations) > 0
        assert any("test" in rec.lower() for rec in recommendations)

    def test_generate_test_summary(self):
        """Test test summary generation."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        changes = [
            CodeChange(
                "src/utils.py",
                "calculate_sum",
                None,
                "function",
                (10, 15),
                "def calculate_sum(a, b): return a + b",
                "Utility function",
            )
        ]

        summary = generator.generate_test_summary(changes)
        assert "summary" in summary
        assert "files_processed" in summary
        assert "tests_generated" in summary
