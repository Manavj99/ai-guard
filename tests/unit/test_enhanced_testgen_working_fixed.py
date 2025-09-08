"""Working tests for enhanced_testgen module that match actual source code."""

from unittest.mock import patch, Mock, mock_open
from ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    CodeChange,
    TestGenTemplate,
    EnhancedTestGenerator,
)


class TestEnhancedTestGenWorking:
    """Working test coverage for enhanced_testgen module."""

    def test_test_generation_config_defaults(self):
        """Test TestGenConfig default values."""
        config = TestGenConfig()

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

    def test_test_generation_config_custom_values(self):
        """Test TestGenConfig with custom values."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model="claude-3",
            llm_temperature=0.3,
            test_framework="unittest",
            generate_mocks=False,
            generate_parametrized_tests=False,
            generate_edge_cases=False,
            max_tests_per_file=5,
            analyze_coverage_gaps=False,
            min_coverage_threshold=90.0,
            output_directory="custom/tests",
            test_file_suffix=".test.py",
            include_docstrings=False,
            include_type_hints=False,
        )

        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "test_key"
        assert config.llm_model == "claude-3"
        assert config.llm_temperature == 0.3
        assert config.test_framework == "unittest"
        assert config.generate_mocks is False
        assert config.generate_parametrized_tests is False
        assert config.generate_edge_cases is False
        assert config.max_tests_per_file == 5
        assert config.analyze_coverage_gaps is False
        assert config.min_coverage_threshold == 90.0
        assert config.output_directory == "custom/tests"
        assert config.test_file_suffix == ".test.py"
        assert config.include_docstrings is False
        assert config.include_type_hints is False

    def test_code_change_creation(self):
        """Test CodeChange dataclass creation."""
        change = CodeChange(
            file_path="src/test.py",
            function_name="test_function",
            class_name="TestClass",
            change_type="function",
            line_numbers=(10, 20),
            code_snippet="def test_function(): pass",
            context="Test context",
        )

        assert change.file_path == "src/test.py"
        assert change.function_name == "test_function"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_numbers == (10, 20)
        assert change.code_snippet == "def test_function(): pass"
        assert change.context == "Test context"

    def test_code_change_minimal(self):
        """Test CodeChange with minimal required fields."""
        change = CodeChange(
            file_path="src/test.py",
            function_name=None,
            class_name=None,
            change_type="import",
            line_numbers=(1, 1),
            code_snippet="import os",
            context="",
        )

        assert change.file_path == "src/test.py"
        assert change.function_name is None
        assert change.class_name is None
        assert change.change_type == "import"
        assert change.line_numbers == (1, 1)
        assert change.code_snippet == "import os"
        assert change.context == ""

    def test_test_template_creation(self):
        """Test TestGenTemplate dataclass creation."""
        template = TestGenTemplate(
            name="test_template",
            description="Test template description",
            template="def test_{name}(): pass",
            variables=["name"],
            applicable_to=["function", "class"],
        )

        assert template.name == "test_template"
        assert template.description == "Test template description"
        assert template.template == "def test_{name}(): pass"
        assert template.variables == ["name"]
        assert template.applicable_to == ["function", "class"]

    def test_enhanced_test_generator_init(self):
        """Test EnhancedTestGenerator initialization."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            assert generator.config == config
            assert generator.llm_client is None
            assert len(generator.test_templates) > 0

    def test_load_test_templates(self):
        """Test loading test templates."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            templates = generator._load_test_templates()

            assert len(templates) > 0
            assert all(isinstance(t, TestGenTemplate) for t in templates)

            # Check for specific templates
            template_names = [t.name for t in templates]
            assert "function_test" in template_names

    def test_initialize_llm_client_openai(self):
        """Test initializing OpenAI LLM client."""
        config = TestGenConfig(llm_provider="openai", llm_api_key="test_key")

        with patch("ai_guard.generators.enhanced_testgen.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            with patch.object(
                EnhancedTestGenerator, "_load_test_templates", return_value=[]
            ):
                generator = EnhancedTestGenerator(config)

                assert generator.llm_client == mock_client
                mock_openai.assert_called_once_with(api_key="test_key")

    def test_initialize_llm_client_anthropic(self):
        """Test initializing Anthropic LLM client."""
        config = TestGenConfig(llm_provider="anthropic", llm_api_key="test_key")

        with patch("ai_guard.generators.enhanced_testgen.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            with patch.object(
                EnhancedTestGenerator, "_load_test_templates", return_value=[]
            ):
                generator = EnhancedTestGenerator(config)

                assert generator.llm_client == mock_client
                mock_anthropic.assert_called_once_with(api_key="test_key")

    def test_initialize_llm_client_no_provider(self):
        """Test initializing LLM client with no provider."""
        config = TestGenConfig(llm_provider="none")

        with patch.object(
            EnhancedTestGenerator, "_load_test_templates", return_value=[]
        ):
            generator = EnhancedTestGenerator(config)

            assert generator.llm_client is None

    def test_initialize_llm_client_error(self):
        """Test initializing LLM client with error."""
        config = TestGenConfig(llm_provider="openai", llm_api_key="test_key")

        with patch(
            "ai_guard.generators.enhanced_testgen.OpenAI",
            side_effect=Exception("API error"),
        ):
            with patch.object(
                EnhancedTestGenerator, "_load_test_templates", return_value=[]
            ):
                generator = EnhancedTestGenerator(config)

                assert generator.llm_client is None

    def test_analyze_code_changes_empty(self):
        """Test analyzing empty code changes."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            changes = generator.analyze_code_changes([])

            assert changes == []

    def test_analyze_code_changes_with_files(self):
        """Test analyzing code changes with files."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            with patch(
                "ai_guard.generators.enhanced_testgen.changed_python_files",
                return_value=["src/test.py"],
            ):
                with patch(
                    "builtins.open", mock_open(read_data="def test_function(): pass")
                ):
                    with patch("os.path.exists", return_value=True):
                        generator = EnhancedTestGenerator(config)

                        changes = generator.analyze_code_changes(["src/test.py"])

                        assert len(changes) > 0
                        assert all(isinstance(c, CodeChange) for c in changes)

    def test_generate_tests_for_changes_empty(self):
        """Test generating tests for empty changes."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            tests = generator.generate_tests_for_changes([])

            assert tests == {}

    def test_generate_tests_for_changes_with_llm(self):
        """Test generating tests for changes with LLM."""
        config = TestGenConfig(llm_provider="openai", llm_api_key="test_key")

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def test_function(): assert True"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(
            EnhancedTestGenerator, "_load_test_templates", return_value=[]
        ):
            generator = EnhancedTestGenerator(config)
            generator.llm_client = mock_client

            changes = [
                CodeChange(
                    file_path="src/test.py",
                    function_name="test_function",
                    class_name=None,
                    change_type="function",
                    line_numbers=(10, 15),
                    code_snippet="def test_function(): return True",
                    context="Test context",
                )
            ]

            tests = generator.generate_tests_for_changes(changes)

            assert "src/test.py" in tests
            assert "test_function" in tests["src/test.py"]

    def test_generate_tests_for_changes_without_llm(self):
        """Test generating tests for changes without LLM."""
        config = TestGenConfig(llm_provider="none")

        with patch.object(
            EnhancedTestGenerator, "_load_test_templates", return_value=[]
        ):
            generator = EnhancedTestGenerator(config)

            changes = [
                CodeChange(
                    file_path="src/test.py",
                    function_name="test_function",
                    class_name=None,
                    change_type="function",
                    line_numbers=(10, 15),
                    code_snippet="def test_function(): return True",
                    context="Test context",
                )
            ]

            tests = generator.generate_tests_for_changes(changes)

            assert "src/test.py" in tests
            assert "test_function" in tests["src/test.py"]

    def test_generate_tests_for_changes_llm_error(self):
        """Test generating tests for changes with LLM error."""
        config = TestGenConfig(llm_provider="openai", llm_api_key="test_key")

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with patch.object(
            EnhancedTestGenerator, "_load_test_templates", return_value=[]
        ):
            generator = EnhancedTestGenerator(config)
            generator.llm_client = mock_client

            changes = [
                CodeChange(
                    file_path="src/test.py",
                    function_name="test_function",
                    class_name=None,
                    change_type="function",
                    line_numbers=(10, 15),
                    code_snippet="def test_function(): return True",
                    context="Test context",
                )
            ]

            tests = generator.generate_tests_for_changes(changes)

            # Should fall back to template-based generation
            assert "src/test.py" in tests
            assert "test_function" in tests["src/test.py"]

    def test_create_test_file_path(self):
        """Test creating test file path."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            test_path = generator._create_test_file_path("src/test.py")

            assert test_path == "tests/unit/test_test.py"

    def test_create_test_file_path_custom_output(self):
        """Test creating test file path with custom output directory."""
        config = TestGenConfig(output_directory="custom/tests")

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            test_path = generator._create_test_file_path("src/test.py")

            assert test_path == "custom/tests/test_test.py"

    def test_create_test_file_path_custom_suffix(self):
        """Test creating test file path with custom suffix."""
        config = TestGenConfig(test_file_suffix=".test.py")

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            test_path = generator._create_test_file_path("src/test.py")

            assert test_path == "tests/unit/test.test.py"

    def test_write_test_file(self):
        """Test writing test file."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("builtins.open", mock_open()) as mock_file:
                generator._write_test_file("tests/test_test.py", "test content")

                mock_file.assert_called_once_with(
                    "tests/test_test.py", "w", encoding="utf-8"
                )
                mock_file().write.assert_called_once_with("test content")

    def test_write_test_file_error(self):
        """Test writing test file with error."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("builtins.open", side_effect=IOError("Write error")):
                # Should not raise exception
                generator._write_test_file("tests/test_test.py", "test content")

    def test_get_coverage_gaps(self):
        """Test getting coverage gaps."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 0
                mock_proc.stdout = "src/test.py:10:1: Not covered"
                mock_run.return_value = mock_proc

                gaps = generator._get_coverage_gaps(["src/test.py"])

                assert len(gaps) > 0

    def test_get_coverage_gaps_error(self):
        """Test getting coverage gaps with error."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run", side_effect=Exception("Command error")):
                gaps = generator._get_coverage_gaps(["src/test.py"])

                assert gaps == []

    def test_validate_generated_tests(self):
        """Test validating generated tests."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc

                result = generator._validate_generated_tests(["tests/test_test.py"])

                assert result is True

    def test_validate_generated_tests_failure(self):
        """Test validating generated tests with failure."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 1
                mock_run.return_value = mock_proc

                result = generator._validate_generated_tests(["tests/test_test.py"])

                assert result is False

    def test_validate_generated_tests_error(self):
        """Test validating generated tests with error."""
        config = TestGenConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=None
        ):
            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run", side_effect=Exception("Command error")):
                result = generator._validate_generated_tests(["tests/test_test.py"])

                assert result is False
