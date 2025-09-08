"""Comprehensive tests for js_ts_support module."""

from unittest.mock import patch, Mock, mock_open
import json
from ai_guard.language_support.js_ts_support import (
    JSTestGenerationConfig,
    JSFileChange,
    JavaScriptTypeScriptSupport,
)


class TestJSTSSupportComprehensive:
    """Comprehensive test coverage for js_ts_support module."""

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
            change_type="function",
            function_name="testFunction",
            class_name="TestClass",
            line_number=10,
            content="function testFunction() { return true; }",
        )

        assert change.file_path == "src/test.js"
        assert change.change_type == "function"
        assert change.function_name == "testFunction"
        assert change.class_name == "TestClass"
        assert change.line_number == 10
        assert change.content == "function testFunction() { return true; }"

    def test_javascript_typescript_support_init(self):
        """Test JavaScriptTypeScriptSupport initialization."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        assert support.config == config

    def test_check_dependencies_all_available(self):
        """Test checking dependencies when all are available."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_run.return_value = mock_proc

            deps = support.check_dependencies()

            assert deps["node"] is True
            assert deps["npm"] is True
            assert deps["jest"] is True
            assert deps["eslint"] is True
            assert deps["prettier"] is True

    def test_check_dependencies_some_missing(self):
        """Test checking dependencies when some are missing."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run") as mock_run:

            def side_effect(*args, **kwargs):
                mock_proc = Mock()
                if "node" in args[0] or "npm" in args[0]:
                    mock_proc.returncode = 0
                else:
                    mock_proc.returncode = 1
                return mock_proc

            mock_run.side_effect = side_effect

            deps = support.check_dependencies()

            assert deps["node"] is True
            assert deps["npm"] is True
            assert deps["jest"] is False
            assert deps["eslint"] is False
            assert deps["prettier"] is False

    def test_check_dependencies_error(self):
        """Test checking dependencies with error."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run", side_effect=Exception("Command error")):
            deps = support.check_dependencies()

            assert deps["node"] is False
            assert deps["npm"] is False
            assert deps["jest"] is False
            assert deps["eslint"] is False
            assert deps["prettier"] is False

    def test_analyze_package_json_valid(self):
        """Test analyzing valid package.json."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "scripts": {
                "test": "jest",
                "lint": "eslint .",
                "format": "prettier --write .",
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0",
                "prettier": "^2.0.0",
            },
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(package_json))):
            with patch("os.path.exists", return_value=True):
                result = support.analyze_package_json("package.json")

                assert result["name"] == "test-project"
                assert result["version"] == "1.0.0"
                assert "test" in result["scripts"]
                assert "jest" in result["devDependencies"]

    def test_analyze_package_json_file_not_found(self):
        """Test analyzing package.json when file doesn't exist."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("os.path.exists", return_value=False):
            result = support.analyze_package_json("package.json")

            assert result == {}

    def test_analyze_package_json_invalid_json(self):
        """Test analyzing package.json with invalid JSON."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists", return_value=True):
                result = support.analyze_package_json("package.json")

                assert result == {}

    def test_analyze_package_json_parse_error(self):
        """Test analyzing package.json with parse error."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("os.path.exists", return_value=True):
                with patch("json.load", side_effect=json.JSONDecodeError("", "", 0)):
                    result = support.analyze_package_json("package.json")

                    assert result == {}

    def test_generate_test_templates_empty_files(self):
        """Test generating test templates with empty file list."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        templates = support.generate_test_templates([])

        assert templates == {}

    def test_generate_test_templates_with_files(self):
        """Test generating test templates with file list."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch(
            "builtins.open",
            mock_open(read_data="function testFunction() { return true; }"),
        ):
            with patch("os.path.exists", return_value=True):
                templates = support.generate_test_templates(["src/test.js"])

                assert "src/test.js" in templates
                assert "Auto-generated test file" in templates["src/test.js"]
                assert "testFunction" in templates["src/test.js"]

    def test_generate_test_templates_typescript(self):
        """Test generating test templates for TypeScript files."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch(
            "builtins.open",
            mock_open(read_data="function testFunction(): boolean { return true; }"),
        ):
            with patch("os.path.exists", return_value=True):
                templates = support.generate_test_templates(["src/test.ts"])

                assert "src/test.ts" in templates
                assert "import { testFunction }" in templates["src/test.ts"]

    def test_generate_test_templates_file_not_found(self):
        """Test generating test templates when file doesn't exist."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("os.path.exists", return_value=False):
            templates = support.generate_test_templates(["nonexistent.js"])

            assert templates == {}

    def test_generate_test_templates_read_error(self):
        """Test generating test templates with read error."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Read error")):
                templates = support.generate_test_templates(["src/test.js"])

                assert templates == {}

    def test_create_test_template_jest(self):
        """Test creating test template for Jest framework."""
        config = JSTestGenerationConfig(test_framework="jest")
        support = JavaScriptTypeScriptSupport(config)

        template = support._create_test_template(
            "src/test.js", "function testFunction() { return true; }"
        )

        assert "Auto-generated test file" in template
        assert "describe('test', () => {" in template
        assert "test('should render without crashing'" in template
        assert "expect(true).toBe(true)" in template

    def test_create_test_template_vitest(self):
        """Test creating test template for Vitest framework."""
        config = JSTestGenerationConfig(test_framework="vitest")
        support = JavaScriptTypeScriptSupport(config)

        template = support._create_test_template(
            "src/test.js", "function testFunction() { return true; }"
        )

        assert "Auto-generated test file" in template
        assert (
            "TODO: Implement tests using your preferred testing framework" in template
        )

    def test_create_test_template_typescript(self):
        """Test creating test template for TypeScript files."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        template = support._create_test_template(
            "src/test.ts", "function testFunction(): boolean { return true; }"
        )

        assert "import { testFunction }" in template
        assert "from './test'" in template

    def test_create_test_file(self):
        """Test creating test file path and content."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        test_file = support.create_test_file("src/test.js", "test content")

        assert test_file == "tests/test.test.js"

    def test_create_test_file_custom_output_dir(self):
        """Test creating test file with custom output directory."""
        config = JSTestGenerationConfig(output_directory="custom/tests")
        support = JavaScriptTypeScriptSupport(config)

        test_file = support.create_test_file("src/test.js", "test content")

        assert test_file == "custom/tests/test.test.js"

    def test_create_test_file_custom_suffix(self):
        """Test creating test file with custom suffix."""
        config = JSTestGenerationConfig(test_file_suffix=".spec.js")
        support = JavaScriptTypeScriptSupport(config)

        test_file = support.create_test_file("src/test.js", "test content")

        assert test_file == "tests/test.spec.js"

    def test_run_quality_checks_eslint(self):
        """Test running quality checks with ESLint."""
        config = JSTestGenerationConfig(use_eslint=True)
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = "No issues found"
            mock_run.return_value = mock_proc

            results = support.run_quality_checks(["src/test.js"])

            assert "eslint" in results
            assert results["eslint"]["passed"] is True
            assert results["eslint"]["output"] == "No issues found"

    def test_run_quality_checks_prettier(self):
        """Test running quality checks with Prettier."""
        config = JSTestGenerationConfig(use_prettier=True)
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = "All files formatted"
            mock_run.return_value = mock_proc

            results = support.run_quality_checks(["src/test.js"])

            assert "prettier" in results
            assert results["prettier"]["passed"] is True
            assert results["prettier"]["issues"] == []

    def test_run_quality_checks_typescript(self):
        """Test running quality checks with TypeScript."""
        config = JSTestGenerationConfig(use_typescript=True)
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = "No type errors"
            mock_run.return_value = mock_proc

            results = support.run_quality_checks(["src/test.ts"])

            assert "typescript" in results
            assert results["typescript"]["passed"] is True
            assert results["typescript"]["issues"] == []

    def test_run_quality_checks_error(self):
        """Test running quality checks with error."""
        config = JSTestGenerationConfig(use_eslint=True)
        support = JavaScriptTypeScriptSupport(config)

        with patch("subprocess.run", side_effect=Exception("Command error")):
            results = support.run_quality_checks(["src/test.js"])

            assert "eslint" in results
            assert results["eslint"]["passed"] is False
            assert len(results["eslint"]["issues"]) > 0

    def test_generate_tests_disabled(self):
        """Test generating tests when disabled."""
        config = JSTestGenerationConfig(generate_unit_tests=False)
        support = JavaScriptTypeScriptSupport(config)

        result = support.generate_tests(["src/test.js"])

        assert result == {}

    def test_generate_tests_enabled(self):
        """Test generating tests when enabled."""
        config = JSTestGenerationConfig(generate_unit_tests=True)
        support = JavaScriptTypeScriptSupport(config)

        with patch.object(support, "generate_test_templates") as mock_templates:
            mock_templates.return_value = {"src/test.js": "test content"}

            with patch.object(support, "create_test_file") as mock_create:
                mock_create.return_value = "tests/test.test.js"

                result = support.generate_tests(["src/test.js"])

                assert "src/test.js" in result
                assert result["src/test.js"] == "tests/test.test.js"
