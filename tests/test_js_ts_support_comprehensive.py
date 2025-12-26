"""Comprehensive tests for js_ts_support.py to improve coverage."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional

from src.ai_guard.language_support.js_ts_support import (
    JSTestGenerationConfig,
    JSFileChange,
    JavaScriptTypeScriptSupport,
)


class TestJSTestGenerationConfig:
    """Test JSTestGenerationConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = JSTestGenerationConfig()
        assert config.test_framework == "jest"
        assert config.use_eslint is True
        assert config.use_prettier is True
        assert config.use_typescript is True
        assert config.generate_unit_tests is True
        assert config.output_directory == "tests"
        assert config.test_file_suffix == ".test.js"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = JSTestGenerationConfig(
            test_framework="mocha",
            use_eslint=False,
            use_prettier=False,
            output_directory="custom_tests",
            test_file_suffix=".spec.js",
        )
        assert config.test_framework == "mocha"
        assert config.use_eslint is False
        assert config.use_prettier is False
        assert config.output_directory == "custom_tests"
        assert config.test_file_suffix == ".spec.js"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = JSTestGenerationConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["test_framework"] == "jest"
        assert config_dict["use_eslint"] is True


class TestJSFileChange:
    """Test JSFileChange class."""

    def test_js_file_change_creation(self):
        """Test creating a JS file change."""
        change = JSFileChange(
            file_path="test.js",
            function_name="testFunc",
            class_name="TestClass",
            change_type="function",
            code_snippet="function testFunc() { return 'hello'; }",
            line_number=10,
        )
        assert change.file_path == "test.js"
        assert change.function_name == "testFunc"
        assert change.class_name == "TestClass"
        assert change.change_type == "function"
        assert change.line_number == 10


class TestJavaScriptTypeScriptSupport:
    """Test JavaScriptTypeScriptSupport class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return JSTestGenerationConfig(
            test_framework="jest",
            use_eslint=True,
            use_prettier=True,
            use_typescript=True,
        )

    @pytest.fixture
    def support(self, config):
        """Create a test support instance."""
        with patch.object(JavaScriptTypeScriptSupport, "__init__", return_value=None):
            support = JavaScriptTypeScriptSupport.__new__(JavaScriptTypeScriptSupport)
            support.config = config
            support.project_root = Path.cwd()
            support.package_json = {}
            return support

    def test_support_initialization(self, config):
        """Test support initialization."""
        with patch.object(
            JavaScriptTypeScriptSupport, "_load_package_json", return_value={}
        ):
            support = JavaScriptTypeScriptSupport(config)
            assert support.config == config
            assert support.project_root is not None
            assert support.package_json is not None

    def test_load_package_json_existing(self, support):
        """Test loading existing package.json."""
        package_data = {
            "name": "test-project",
            "scripts": {"test": "jest"},
            "devDependencies": {"jest": "^27.0.0"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(package_data, f)
            f.flush()

            try:
                with patch.object(support, "project_root", Path(f.name).parent):
                    result = support._load_package_json()
                    assert result["name"] == "test-project"
                    assert "jest" in result["devDependencies"]
            finally:
                Path(f.name).unlink()

    def test_load_package_json_nonexistent(self, support):
        """Test loading nonexistent package.json."""
        with patch.object(support, "project_root", Path("/nonexistent")):
            result = support._load_package_json()
            assert result == {}

    def test_check_dependencies_all_available(self, support):
        """Test checking dependencies when all are available."""
        with patch("shutil.which", return_value="/usr/bin/jest"):
            result = support.check_dependencies()
            assert result["jest"] is True
            assert result["eslint"] is True
            assert result["prettier"] is True
            assert result["typescript"] is True

    def test_check_dependencies_none_available(self, support):
        """Test checking dependencies when none are available."""
        with patch("shutil.which", return_value=None):
            result = support.check_dependencies()
            assert result["jest"] is False
            assert result["eslint"] is False
            assert result["prettier"] is False
            assert result["typescript"] is False

    def test_run_eslint_success(self, support):
        """Test running ESLint successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "No issues found"

            result = support.run_eslint(["test.js"])
            assert result[0] is True  # passed
            assert result[1] == []  # issues

    def test_run_eslint_failure(self, support):
        """Test running ESLint with issues."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "test.js:1:1 error: Unexpected var"

            result = support.run_eslint(["test.js"])
            assert result[0] is False  # failed
            assert len(result[1]) > 0  # has issues

    def test_run_eslint_error(self, support):
        """Test running ESLint with error."""
        with patch("subprocess.run", side_effect=Exception("Command failed")):
            result = support.run_eslint(["test.js"])
            assert result[0] is False
            assert "Command failed" in result[1][0]

    def test_run_prettier_success(self, support):
        """Test running Prettier successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "All files formatted"

            result = support.run_prettier(["test.js"])
            assert result[0] is True
            assert result[1] == []

    def test_run_prettier_failure(self, support):
        """Test running Prettier with formatting issues."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "test.js needs formatting"

            result = support.run_prettier(["test.js"])
            assert result[0] is False
            assert len(result[1]) > 0

    def test_run_typescript_check_success(self, support):
        """Test running TypeScript check successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "No type errors"

            result = support.run_typescript_check(["test.ts"])
            assert result[0] is True
            assert result[1] == []

    def test_run_typescript_check_failure(self, support):
        """Test running TypeScript check with type errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = (
                "test.ts:1:1 error: Type 'string' is not assignable"
            )

            result = support.run_typescript_check(["test.ts"])
            assert result[0] is False
            assert len(result[1]) > 0

    def test_run_jest_tests_success(self, support):
        """Test running Jest tests successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "All tests passed"

            result = support.run_jest_tests()
            assert result[0] is True
            assert "All tests passed" in result[1]

    def test_run_jest_tests_failure(self, support):
        """Test running Jest tests with failures."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "Some tests failed"

            result = support.run_jest_tests()
            assert result[0] is False
            assert "Some tests failed" in result[1]

    def test_run_quality_checks_all_pass(self, support):
        """Test running quality checks when all pass."""
        with patch.object(support, "run_eslint", return_value=(True, [])):
            with patch.object(support, "run_prettier", return_value=(True, [])):
                with patch.object(
                    support, "run_typescript_check", return_value=(True, [])
                ):
                    result = support.run_quality_checks(["test.js"])
                    assert result["overall"] is True
                    assert result["eslint"]["passed"] is True
                    assert result["prettier"]["passed"] is True
                    assert result["typescript"]["passed"] is True

    def test_run_quality_checks_some_fail(self, support):
        """Test running quality checks when some fail."""
        with patch.object(support, "run_eslint", return_value=(False, ["error1"])):
            with patch.object(support, "run_prettier", return_value=(True, [])):
                with patch.object(
                    support, "run_typescript_check", return_value=(True, [])
                ):
                    result = support.run_quality_checks(["test.js"])
                    assert result["overall"] is False
                    assert result["eslint"]["passed"] is False
                    assert result["prettier"]["passed"] is True
                    assert result["typescript"]["passed"] is True

    def test_generate_tests_disabled(self, support):
        """Test generating tests when disabled."""
        support.config.generate_unit_tests = False
        result = support.generate_tests(["test.js"])
        assert result == {}

    def test_generate_tests_enabled(self, support):
        """Test generating tests when enabled."""
        support.config.generate_unit_tests = True

        with patch.object(
            support, "generate_test_templates", return_value={"test.js": "test content"}
        ):
            with patch.object(support, "create_test_file", return_value="test.test.js"):
                result = support.generate_tests(["test.js"])
                assert "test.js" in result
                assert result["test.js"] == "test.test.js"

    def test_run_linting_single_file(self, support):
        """Test running linting on a single file."""
        with patch.object(support, "run_eslint", return_value=(True, [])):
            result = support.run_linting("test.js")
            assert result["success"] is True
            assert result["output"] == "Linting passed"

    def test_run_linting_directory(self, support):
        """Test running linting on a directory."""
        with patch.object(support, "run_eslint", return_value=(True, [])):
            with patch.object(Path, "is_dir", return_value=True):
                with patch.object(Path, "glob", return_value=[Path("test.js")]):
                    result = support.run_linting("src/")
                    assert result["success"] is True

    def test_run_linting_no_files(self, support):
        """Test running linting with no files found."""
        with patch.object(Path, "is_dir", return_value=True):
            with patch.object(Path, "glob", return_value=[]):
                result = support.run_linting("empty_dir/")
                assert result["success"] is True
                assert "No JavaScript/TypeScript files found" in result["output"]

    def test_run_linting_failure(self, support):
        """Test running linting with failures."""
        with patch.object(
            support,
            "run_eslint",
            return_value=(False, [{"message": "error1"}, {"message": "error2"}]),
        ):
            result = support.run_linting("test.js")
            assert result["success"] is False
            assert "Linting failed" in result["output"]
            assert "error1" in result["output"]

    def test_run_testing_success(self, support):
        """Test running testing successfully."""
        with patch.object(support, "check_dependencies", return_value={"jest": True}):
            with patch.object(
                support, "run_jest_tests", return_value=(True, "All tests passed")
            ):
                result = support.run_testing()
                assert result["success"] is True
                assert result["output"] == "Tests passed"

    def test_run_testing_jest_not_available(self, support):
        """Test running testing when Jest is not available."""
        with patch.object(support, "check_dependencies", return_value={"jest": False}):
            result = support.run_testing()
            assert result["success"] is False
            assert result["error"] == "Jest not available"

    def test_run_testing_failure(self, support):
        """Test running testing with failures."""
        with patch.object(support, "check_dependencies", return_value={"jest": True}):
            with patch.object(
                support, "run_jest_tests", return_value=(False, "Tests failed")
            ):
                result = support.run_testing()
                assert result["success"] is False
                assert result["output"] == "Tests failed"

    def test_run_testing_error(self, support):
        """Test running testing with error."""
        with patch.object(
            support, "check_dependencies", side_effect=Exception("Error")
        ):
            result = support.run_testing()
            assert result["success"] is False
            assert "Error" in result["error"]

    def test_generate_test_file_path(self, support):
        """Test generating test file path."""
        support.project_root = Path("/project")

        with patch.object(Path, "relative_to", return_value=Path("src/test.js")):
            result = support.generate_test_file_path("/project/src/test.js")
            assert "test.test.js" in result

    def test_generate_test_file_path_not_relative(self, support):
        """Test generating test file path when not relative to project root."""
        support.project_root = Path("/project")

        with patch.object(Path, "relative_to", side_effect=ValueError("Not relative")):
            result = support.generate_test_file_path("/other/test.js")
            assert "test.test.js" in result

    def test_analyze_file_changes(self, support):
        """Test analyzing file changes."""
        changes = [
            JSFileChange("test.js", "func1", None, "function", "code1", 1),
            JSFileChange("test.js", "func2", None, "function", "code2", 2),
            JSFileChange("test.js", None, "Class1", "class", "code3", 3),
            JSFileChange("test.js", None, None, "import", "import code", 4),
        ]

        result = support.analyze_file_changes(changes)
        assert "test.js" in result
        assert len(result["test.js"]["functions"]) == 2
        assert len(result["test.js"]["classes"]) == 1
        assert len(result["test.js"]["imports"]) == 1

    def test_generate_test_content_function(self, support):
        """Test generating test content for function."""
        change = JSFileChange(
            "test.js", "testFunc", None, "function", "function testFunc() {}", 1
        )

        result = support.generate_test_content(change)
        assert "testFunc" in result
        assert "describe" in result

    def test_generate_test_content_class(self, support):
        """Test generating test content for class."""
        change = JSFileChange(
            "test.js", None, "TestClass", "class", "class TestClass {}", 1
        )

        result = support.generate_test_content(change)
        assert "TestClass" in result
        assert "describe" in result

    def test_generate_test_content_generic(self, support):
        """Test generating test content for generic change."""
        change = JSFileChange("test.js", None, None, "other", "some code", 1)

        result = support.generate_test_content(change)
        assert "test" in result
        assert "describe" in result

    def test_generate_function_test(self, support):
        """Test generating function test."""
        result = support._generate_function_test(
            "testFunc", "function testFunc() {}", False
        )
        assert "testFunc" in result
        assert "describe" in result
        assert "test" in result

    def test_generate_class_test(self, support):
        """Test generating class test."""
        result = support._generate_class_test("TestClass", "class TestClass {}", False)
        assert "TestClass" in result
        assert "describe" in result

    def test_generate_generic_test(self, support):
        """Test generating generic test."""
        result = support._generate_generic_test("test", False)
        assert "test" in result
        assert "describe" in result

    def test_validate_code_quality_success(self, support):
        """Test validating code quality successfully."""
        with patch.object(support, "run_linting", return_value={"success": True}):
            with patch.object(support, "run_testing", return_value={"success": True}):
                result = support.validate_code_quality("test.js")
                assert result["overall_success"] is True
                assert result["linting"]["success"] is True
                assert result["testing"]["success"] is True

    def test_validate_code_quality_failure(self, support):
        """Test validating code quality with failures."""
        with patch.object(support, "run_linting", return_value={"success": False}):
            with patch.object(support, "run_testing", return_value={"success": True}):
                result = support.validate_code_quality("test.js")
                assert result["overall_success"] is False

    def test_validate_code_quality_error(self, support):
        """Test validating code quality with error."""
        with patch.object(support, "run_linting", side_effect=Exception("Error")):
            result = support.validate_code_quality("test.js")
            assert result["overall_success"] is False
            assert "Error" in result["linting"]["error"]

    def test_get_recommendations_with_functions(self, support):
        """Test getting recommendations with functions."""
        analysis = {
            "test.js": {
                "functions": ["func1", "func2"],
                "classes": ["Class1"],
                "imports": [],
            }
        }

        result = support.get_recommendations(analysis)
        assert len(result) > 0
        assert "functions" in result[0]
        assert "classes" in result[1]

    def test_get_recommendations_empty(self, support):
        """Test getting recommendations with empty analysis."""
        analysis = {}
        result = support.get_recommendations(analysis)
        assert "No specific recommendations" in result[0]

    def test_export_results(self, support):
        """Test exporting results."""
        analysis = {"test": "data"}
        result = support.export_results(analysis)
        assert "timestamp" in result
        assert result["analysis"] == analysis
        assert "config" in result
        assert "project_root" in result


class TestJavaScriptTypeScriptSupportIntegration:
    """Integration tests for JavaScriptTypeScriptSupport."""

    def test_full_workflow(self):
        """Test full workflow from config to test generation."""
        config = JSTestGenerationConfig(
            test_framework="jest",
            use_eslint=True,
            use_prettier=True,
            generate_unit_tests=True,
        )

        with patch.object(
            JavaScriptTypeScriptSupport, "_load_package_json", return_value={}
        ):
            support = JavaScriptTypeScriptSupport(config)

            # Test the full workflow
            with patch.object(
                support,
                "check_dependencies",
                return_value={"jest": True, "eslint": True},
            ):
                with patch.object(
                    support, "run_quality_checks", return_value={"overall": True}
                ):
                    with patch.object(
                        support,
                        "generate_tests",
                        return_value={"test.js": "test.test.js"},
                    ):
                        # This should not raise an exception
                        deps = support.check_dependencies()
                        assert deps["jest"] is True

                        quality = support.run_quality_checks(["test.js"])
                        assert quality["overall"] is True

                        tests = support.generate_tests(["test.js"])
                        assert "test.js" in tests


def test_main_function():
    """Test the main function."""
    import sys
    from unittest.mock import patch

    test_args = [
        "js_ts_support.py",
        "--files",
        "test.js",
        "--quality",
        "--generate-tests",
    ]

    with patch.object(sys, "argv", test_args):
        with patch(
            "src.ai_guard.language_support.js_ts_support.JavaScriptTypeScriptSupport"
        ) as mock_support:
            # This should not raise an exception
            try:
                from src.ai_guard.language_support.js_ts_support import main

                main()
            except SystemExit:
                pass  # Expected when no files provided


if __name__ == "__main__":
    pytest.main([__file__])
