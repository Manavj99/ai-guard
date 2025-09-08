"""Final comprehensive test suite for coverage improvement."""

from unittest.mock import patch
import os
import json
from ai_guard.config import (
    load_config,
    Gates,
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
)
from ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_json,
)
from ai_guard.pr_annotations import (
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
    format_annotation_message,
    parse_lint_output,
    parse_mypy_output,
    parse_bandit_output,
)
from ai_guard.language_support.js_ts_support import (
    JSTestGenerationConfig,
    JSFileChange,
    JavaScriptTypeScriptSupport,
)
from ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    CodeChange,
    TestGenTemplate,
    EnhancedTestGenerator,
)


class TestConfigCoverage:
    """Test coverage for config module."""

    def test_gates_default_values(self):
        """Test Gates dataclass default values."""
        gates = Gates()

        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_custom_values(self):
        """Test Gates dataclass with custom values."""
        gates = Gates(
            min_coverage=90,
            fail_on_bandit=False,
            fail_on_lint=False,
            fail_on_mypy=False,
        )

        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is False

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()

        assert isinstance(config, dict)
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"

    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = {
            "min_coverage": 85,
            "report_format": "json",
            "llm_provider": "anthropic",
        }

        assert validate_config(config) is True

    def test_validate_config_invalid_coverage(self):
        """Test validating configuration with invalid coverage."""
        config = {
            "min_coverage": 150,  # Invalid: > 100
        }

        assert validate_config(config) is False

    def test_validate_config_missing_required_field(self):
        """Test validating configuration missing required fields."""
        config = {
            "report_format": "json"
            # Missing min_coverage
        }

        assert validate_config(config) is False

    def test_merge_configs(self):
        """Test merging configurations."""
        base_config = {
            "min_coverage": 80,
            "report_format": "sarif",
            "skip_tests": False,
        }

        override_config = {"min_coverage": 90, "report_format": "json"}

        result = merge_configs(base_config, override_config)

        assert result["min_coverage"] == 90
        assert result["report_format"] == "json"
        assert result["skip_tests"] is False

    def test_parse_config_value_int(self):
        """Test parsing integer config value."""
        result = parse_config_value("42", "int")
        assert result == 42

    def test_parse_config_value_float(self):
        """Test parsing float config value."""
        result = parse_config_value("3.14", "float")
        assert result == 3.14

    def test_parse_config_value_bool_true(self):
        """Test parsing boolean config value (true)."""
        result = parse_config_value("true", "bool")
        assert result is True

    def test_parse_config_value_bool_false(self):
        """Test parsing boolean config value (false)."""
        result = parse_config_value("false", "bool")
        assert result is False

    def test_parse_config_value_auto_int(self):
        """Test auto-parsing integer value."""
        result = parse_config_value("123", "auto")
        assert result == 123

    def test_parse_config_value_auto_float(self):
        """Test auto-parsing float value."""
        result = parse_config_value("1.23", "auto")
        assert result == 1.23

    def test_parse_config_value_auto_bool(self):
        """Test auto-parsing boolean value."""
        result = parse_config_value("true", "auto")
        assert result is True

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        result = load_config("nonexistent.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 80  # Default value


class TestAnalyzerCoverage:
    """Test coverage for analyzer module."""

    def test_cov_percent_file_not_found(self):
        """Test cov_percent when coverage.xml doesn't exist."""
        with patch("os.path.exists", return_value=False):
            result = cov_percent()
            assert result == 0

    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        flake8_output = """
src/test.py:10:1: E302 expected 2 blank lines, found 1
src/test.py:15:5: E111 indentation is not a multiple of four
"""

        results = _parse_flake8_output(flake8_output)

        assert len(results) == 2
        assert "E302" in results[0].rule_id
        assert "expected 2 blank lines" in results[0].message

    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        results = _parse_flake8_output("")
        assert results == []

    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        mypy_output = """
src/test.py:10: error: Incompatible return type
src/test.py:15: error: Argument 1 has incompatible type
"""

        results = _parse_mypy_output(mypy_output)

        assert len(results) == 2
        assert "Incompatible return type" in results[0].message

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        results = _parse_mypy_output("")
        assert results == []

    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON output."""
        bandit_json = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test issue",
                    "test_id": "B101",
                }
            ]
        }

        results = _parse_bandit_json(json.dumps(bandit_json))

        assert len(results) == 1
        assert "B101" in results[0].rule_id
        assert "Test issue" in results[0].message

    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON output."""
        bandit_json = {"results": []}

        results = _parse_bandit_json(json.dumps(bandit_json))

        assert results == []

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON output."""
        results = _parse_bandit_json("invalid json")
        assert results == []


class TestPRAnnotationsCoverage:
    """Test coverage for pr_annotations module."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            rule_id="E302",
            suggestion="Add blank lines",
            fix_code="\n\n",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.rule_id == "E302"
        assert issue.suggestion == "Add blank lines"
        assert issue.fix_code == "\n\n"

    def test_code_issue_minimal(self):
        """Test CodeIssue with minimal required fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W001",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "warning"
        assert issue.message == "Test warning"
        assert issue.rule_id == "W001"
        assert issue.suggestion is None
        assert issue.fix_code is None

    def test_pr_annotation_creation(self):
        """Test PRAnnotation dataclass creation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test annotation message",
            annotation_level="warning",
            title="Test Title",
            raw_details="Raw details",
            start_line=10,
            end_line=12,
            start_column=5,
            end_column=10,
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test annotation message"
        assert annotation.annotation_level == "warning"
        assert annotation.title == "Test Title"
        assert annotation.raw_details == "Raw details"
        assert annotation.start_line == 10
        assert annotation.end_line == 12
        assert annotation.start_column == 5
        assert annotation.end_column == 10

    def test_pr_annotation_minimal(self):
        """Test PRAnnotation with minimal required fields."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test message",
            annotation_level="notice",
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "notice"
        assert annotation.title is None
        assert annotation.raw_details is None
        assert annotation.start_line is None
        assert annotation.end_line is None
        assert annotation.start_column is None
        assert annotation.end_column is None

    def test_pr_review_summary_creation(self):
        """Test PRReviewSummary dataclass creation."""
        annotations = [
            PRAnnotation(
                file_path="src/test.py",
                line_number=10,
                message="Test message",
                annotation_level="warning",
            )
        ]

        summary = PRReviewSummary(
            overall_status="changes_requested",
            summary="Test summary",
            annotations=annotations,
            suggestions=["Fix line 10"],
            quality_score=0.8,
            coverage_info={"coverage": 85.0},
            security_issues=["Potential security issue"],
        )

        assert summary.overall_status == "changes_requested"
        assert summary.summary == "Test summary"
        assert len(summary.annotations) == 1
        assert summary.suggestions == ["Fix line 10"]
        assert summary.quality_score == 0.8
        assert summary.coverage_info == {"coverage": 85.0}
        assert summary.security_issues == ["Potential security issue"]

    def test_pr_annotator_init_with_token(self):
        """Test PRAnnotator initialization with token."""
        annotator = PRAnnotator(github_token="test_token", repo="test/repo")

        assert annotator.github_token == "test_token"
        assert annotator.repo == "test/repo"
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_init_with_env_vars(self):
        """Test PRAnnotator initialization with environment variables."""
        with patch.dict(
            os.environ, {"GITHUB_TOKEN": "env_token", "GITHUB_REPOSITORY": "env/repo"}
        ):
            annotator = PRAnnotator()

            assert annotator.github_token == "env_token"
            assert annotator.repo == "env/repo"
            assert annotator.annotations == []
            assert annotator.issues == []

    def test_add_issue_error_severity(self):
        """Test adding issue with error severity."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "failure"
        assert annotator.annotations[0].title == "E001: Test error"

    def test_add_issue_warning_severity(self):
        """Test adding issue with warning severity."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "warning"
        assert annotator.annotations[0].title == "W001: Test warning"

    def test_add_issue_info_severity(self):
        """Test adding issue with info severity."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="info",
            message="Test info",
            rule_id="I001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "notice"
        assert annotator.annotations[0].title == "I001: Test info"

    def test_format_annotation_message(self):
        """Test formatting annotation message."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Add blank lines",
            fix_code="\n\n",
        )

        message = format_annotation_message(issue)

        assert "Test error" in message
        assert "💡 **Suggestion:** Add blank lines" in message
        assert "🔧 **Fix:**" in message

    def test_parse_lint_output(self):
        """Test parsing lint output."""
        lint_output = "src/test.py:10:1: E302 expected 2 blank lines, found 1"

        issues = parse_lint_output(lint_output)

        assert len(issues) == 1
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].rule_id == "E302"
        assert "expected 2 blank lines" in issues[0].message

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = "src/test.py:10: error: Incompatible return type"

        issues = parse_mypy_output(mypy_output)

        assert len(issues) == 1
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert "Incompatible return type" in issues[0].message

    def test_parse_bandit_output(self):
        """Test parsing bandit output."""
        bandit_output = "src/test.py:10:1: >> Issue: B101: Use of assert detected"

        issues = parse_bandit_output(bandit_output)

        assert len(issues) == 1
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].rule_id == "security_scan"
        assert "B101: Use of assert detected" in issues[0].message


class TestJSTSSupportCoverage:
    """Test coverage for js_ts_support module."""

    def test_js_test_generation_config_defaults(self):
        """Test JSTestGenerationConfig default values."""
        config = JSTestGenerationConfig()

        assert config.test_framework == "jest"
        assert config.test_runner == "npm test"
        assert config.use_eslint is True
        assert config.use_prettier is True
        assert config.use_typescript is False
        assert config.generate_unit_tests is True
        assert config.generate_integration_tests is False
        assert config.generate_mocks is True
        assert config.generate_snapshots is True
        assert config.output_directory == "tests"
        assert config.test_file_suffix == ".test.js"
        assert config.include_types is True

    def test_js_test_generation_config_custom_values(self):
        """Test JSTestGenerationConfig with custom values."""
        config = JSTestGenerationConfig(
            test_framework="vitest",
            test_runner="npm run test:vitest",
            use_eslint=False,
            use_prettier=False,
            use_typescript=True,
            generate_unit_tests=False,
            generate_integration_tests=True,
            generate_mocks=False,
            generate_snapshots=False,
            output_directory="custom/tests",
            test_file_suffix=".spec.ts",
            include_types=False,
        )

        assert config.test_framework == "vitest"
        assert config.test_runner == "npm run test:vitest"
        assert config.use_eslint is False
        assert config.use_prettier is False
        assert config.use_typescript is True
        assert config.generate_unit_tests is False
        assert config.generate_integration_tests is True
        assert config.generate_mocks is False
        assert config.generate_snapshots is False
        assert config.output_directory == "custom/tests"
        assert config.test_file_suffix == ".spec.ts"
        assert config.include_types is False

    def test_js_file_change_creation(self):
        """Test JSFileChange dataclass creation."""
        change = JSFileChange(
            file_path="src/test.js",
            function_name="testFunction",
            class_name="TestClass",
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="function testFunction() { return true; }",
            context="Test context",
        )

        assert change.file_path == "src/test.js"
        assert change.function_name == "testFunction"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_numbers == (10, 15)
        assert change.code_snippet == "function testFunction() { return true; }"
        assert change.context == "Test context"

    def test_javascript_typescript_support_init(self):
        """Test JavaScriptTypeScriptSupport initialization."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        assert support.config == config


class TestEnhancedTestGenCoverage:
    """Test coverage for enhanced_testgen module."""

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
