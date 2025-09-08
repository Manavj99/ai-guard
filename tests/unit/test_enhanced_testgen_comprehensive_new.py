"""Comprehensive tests for enhanced_testgen module."""

from unittest.mock import patch, Mock, mock_open
from ai_guard.generators.enhanced_testgen import (
    TestGenerationConfig,
    CodeChange,
    TestTemplate,
    EnhancedTestGenerator,
)


class TestEnhancedTestGenComprehensive:
    """Comprehensive test coverage for enhanced_testgen module."""

    def test_test_generation_config_defaults(self):
        """Test TestGenerationConfig default values."""
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

    def test_test_generation_config_custom_values(self):
        """Test TestGenerationConfig with custom values."""
        config = TestGenerationConfig(
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model="claude-3-sonnet",
            llm_temperature=0.5,
            test_framework="unittest",
            generate_mocks=False,
            generate_parametrized_tests=False,
            generate_edge_cases=False,
            max_tests_per_file=5,
            analyze_coverage_gaps=False,
            min_coverage_threshold=90.0,
            output_directory="custom/tests",
            test_file_suffix=".spec.py",
            include_docstrings=False,
            include_type_hints=False,
        )

        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "test-key"
        assert config.llm_model == "claude-3-sonnet"
        assert config.llm_temperature == 0.5
        assert config.test_framework == "unittest"
        assert config.generate_mocks is False
        assert config.generate_parametrized_tests is False
        assert config.generate_edge_cases is False
        assert config.max_tests_per_file == 5
        assert config.analyze_coverage_gaps is False
        assert config.min_coverage_threshold == 90.0
        assert config.output_directory == "custom/tests"
        assert config.test_file_suffix == ".spec.py"
        assert config.include_docstrings is False
        assert config.include_type_hints is False

    def test_code_change_creation(self):
        """Test CodeChange dataclass creation."""
        change = CodeChange(
            file_path="src/test.py",
            change_type="function",
            function_name="test_function",
            class_name="TestClass",
            line_number=10,
            content="def test_function(): pass",
        )

        assert change.file_path == "src/test.py"
        assert change.change_type == "function"
        assert change.function_name == "test_function"
        assert change.class_name == "TestClass"
        assert change.line_number == 10
        assert change.content == "def test_function(): pass"

    def test_test_template_creation(self):
        """Test TestTemplate dataclass creation."""
        template = TestTemplate(
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

    def test_enhanced_test_generator_init(self):
        """Test EnhancedTestGenerator initialization."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            assert generator.config == config
            assert len(generator.test_templates) > 0
            assert generator.llm_client is not None

    def test_load_test_templates(self):
        """Test loading of built-in test templates."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)
            templates = generator._load_test_templates()

            assert len(templates) >= 3  # function_test, class_test, edge_case_test
            template_names = [t.name for t in templates]
            assert "function_test" in template_names
            assert "class_test" in template_names
            assert "edge_case_test" in template_names

    def test_initialize_llm_client_openai(self):
        """Test LLM client initialization for OpenAI."""
        config = TestGenerationConfig(llm_provider="openai", llm_api_key="test-key")

        with patch("ai_guard.generators.enhanced_testgen.openai") as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            generator = EnhancedTestGenerator(config)

            assert generator.llm_client == mock_client
            mock_openai.OpenAI.assert_called_once_with(api_key="test-key")

    def test_initialize_llm_client_anthropic(self):
        """Test LLM client initialization for Anthropic."""
        config = TestGenerationConfig(llm_provider="anthropic", llm_api_key="test-key")

        with patch("ai_guard.generators.enhanced_testgen.anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            generator = EnhancedTestGenerator(config)

            assert generator.llm_client == mock_client
            mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")

    def test_initialize_llm_client_local(self):
        """Test LLM client initialization for local provider."""
        config = TestGenerationConfig(llm_provider="local")

        with patch("ai_guard.generators.enhanced_testgen.requests") as mock_requests:
            generator = EnhancedTestGenerator(config)

            assert generator.llm_client is not None
            # Local client should be a mock or simple implementation

    def test_initialize_llm_client_no_api_key(self):
        """Test LLM client initialization without API key."""
        config = TestGenerationConfig(llm_provider="openai", llm_api_key=None)

        with patch("ai_guard.generators.enhanced_testgen.openai") as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            generator = EnhancedTestGenerator(config)

            assert generator.llm_client == mock_client
            mock_openai.OpenAI.assert_called_once_with(api_key=None)

    def test_analyze_code_changes_empty_files(self):
        """Test analyzing code changes with empty file list."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)
            changes = generator.analyze_code_changes([])

            assert changes == []

    def test_analyze_code_changes_with_files(self):
        """Test analyzing code changes with file list."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch(
                "builtins.open", mock_open(read_data="def test_function(): pass")
            ):
                with patch("os.path.exists", return_value=True):
                    changes = generator.analyze_code_changes(["src/test.py"])

                    assert len(changes) > 0
                    assert all(isinstance(change, CodeChange) for change in changes)

    def test_analyze_code_changes_file_not_found(self):
        """Test analyzing code changes when file doesn't exist."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch("os.path.exists", return_value=False):
                changes = generator.analyze_code_changes(["nonexistent.py"])

                assert changes == []

    def test_analyze_code_changes_parse_error(self):
        """Test analyzing code changes with parse error."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch("builtins.open", mock_open(read_data="invalid python code")):
                with patch("os.path.exists", return_value=True):
                    with patch("ast.parse", side_effect=SyntaxError("Invalid syntax")):
                        changes = generator.analyze_code_changes(["src/test.py"])

                        assert changes == []

    def test_generate_function_tests(self):
        """Test generating tests for functions."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            code_change = CodeChange(
                file_path="src/test.py",
                change_type="function",
                function_name="test_function",
                class_name=None,
                line_number=10,
                content="def test_function(): pass",
            )

            result = generator._generate_function_tests(code_change)

            assert "def test_test_function" in result
            assert "test_function" in result

    def test_generate_class_tests(self):
        """Test generating tests for classes."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            code_change = CodeChange(
                file_path="src/test.py",
                change_type="class",
                function_name=None,
                class_name="TestClass",
                line_number=10,
                content="class TestClass: pass",
            )

            result = generator._generate_class_tests(code_change)

            assert "class TestTestClass" in result
            assert "TestClass" in result

    def test_generate_generic_tests(self):
        """Test generating generic tests."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            code_change = CodeChange(
                file_path="src/test.py",
                change_type="unknown",
                function_name="test_function",
                class_name=None,
                line_number=10,
                content="some code",
            )

            result = generator._generate_generic_tests(code_change)

            assert "def test_unknown_test_function" in result
            assert "assert True" in result

    def test_analyze_coverage_gaps_disabled(self):
        """Test coverage gap analysis when disabled."""
        config = TestGenerationConfig(analyze_coverage_gaps=False)

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)
            gaps = generator.analyze_coverage_gaps(["src/test.py"])

            assert gaps == {}

    def test_analyze_coverage_gaps_enabled(self):
        """Test coverage gap analysis when enabled."""
        config = TestGenerationConfig(analyze_coverage_gaps=True)

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch.object(generator, "_analyze_file_coverage") as mock_analyze:
                mock_analyze.return_value = ["line 10", "line 20"]

                gaps = generator.analyze_coverage_gaps(["src/test.py"])

                assert "src/test.py" in gaps
                assert gaps["src/test.py"] == ["line 10", "line 20"]

    def test_analyze_file_coverage(self):
        """Test analyzing coverage for a specific file."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 0
                mock_proc.stdout = "src/test.py:10: uncovered line"
                mock_run.return_value = mock_proc

                gaps = generator._analyze_file_coverage("src/test.py")

                assert len(gaps) > 0
                assert "line 10" in gaps[0]

    def test_analyze_file_coverage_error(self):
        """Test analyzing coverage with error."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch("subprocess.run", side_effect=Exception("Coverage error")):
                gaps = generator._analyze_file_coverage("src/test.py")

                assert gaps == []

    def test_generate_test_file(self):
        """Test generating test file content."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            code_changes = [
                CodeChange(
                    file_path="src/test.py",
                    change_type="function",
                    function_name="test_function",
                    class_name=None,
                    line_number=10,
                    content="def test_function(): pass",
                )
            ]

            with patch.object(generator, "analyze_coverage_gaps") as mock_analyze:
                mock_analyze.return_value = {}

                result = generator.generate_test_file(code_changes, "test_output.py")

                assert "def test_test_function" in result
                assert "import pytest" in result
                assert "Auto-generated test file" in result

    def test_generate_tests_no_files(self):
        """Test generating tests with no changed files."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)
            result = generator.generate_tests([])

            assert result == ""

    def test_generate_tests_with_files(self):
        """Test generating tests with changed files."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch.object(generator, "analyze_code_changes") as mock_analyze:
                mock_analyze.return_value = [
                    CodeChange(
                        file_path="src/test.py",
                        change_type="function",
                        function_name="test_function",
                        class_name=None,
                        line_number=10,
                        content="def test_function(): pass",
                    )
                ]

                with patch.object(generator, "generate_test_file") as mock_generate:
                    mock_generate.return_value = "def test_example(): pass"

                    result = generator.generate_tests(["src/test.py"])

                    assert result == "def test_example(): pass"
                    mock_analyze.assert_called_once_with(["src/test.py"], None)
                    mock_generate.assert_called_once()

    def test_generate_tests_no_changes(self):
        """Test generating tests when no code changes detected."""
        config = TestGenerationConfig()

        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client"
        ) as mock_init_llm:
            mock_init_llm.return_value = Mock()

            generator = EnhancedTestGenerator(config)

            with patch.object(generator, "analyze_code_changes") as mock_analyze:
                mock_analyze.return_value = []

                result = generator.generate_tests(["src/test.py"])

                assert result == ""
