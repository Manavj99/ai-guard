"""Tests for JavaScript/TypeScript language support module."""

from ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_prettier_check,
    run_typescript_check,
    run_jest_tests,
    JavaScriptTypeScriptSupport,
    JSTestGenerationConfig,
    JSFileChange,
)
import pytest
import json
import subprocess
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestNodeNpmChecks:
    """Test Node.js and npm installation checks."""

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_node_installed_success(self, mock_run):
        """Test checking Node.js installation when it's available."""
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0")

        result = check_node_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["node", "--version"], capture_output=True, text=True, check=True
        )

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_node_installed_failure(self, mock_run):
        """Test checking Node.js installation when it's not available."""
        mock_run.side_effect = FileNotFoundError()

        result = check_node_installed()

        assert result is False

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_node_installed_error(self, mock_run):
        """Test checking Node.js installation with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "node")

        result = check_node_installed()

        assert result is False

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_npm_installed_success(self, mock_run):
        """Test checking npm installation when it's available."""
        mock_run.return_value = Mock(returncode=0, stdout="8.0.0")

        result = check_npm_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["npm", "--version"], capture_output=True, text=True, check=True
        )

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_npm_installed_failure(self, mock_run):
        """Test checking npm installation when it's not available."""
        mock_run.side_effect = FileNotFoundError()

        result = check_npm_installed()

        assert result is False


class TestESLint:
    """Test ESLint functionality."""

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_eslint_success(self, mock_run):
        """Test running ESLint successfully."""
        mock_output = {
            "results": [
                {
                    "filePath": "test.js",
                    "messages": [
                        {
                            "ruleId": "no-console",
                            "severity": 1,
                            "message": "Unexpected console statement",
                            "line": 5,
                            "column": 1,
                        }
                    ],
                }
            ]
        }

        mock_run.return_value = Mock(
            returncode=0, stdout=json.dumps(mock_output), stderr=""
        )

        result = run_eslint(["test.js"])

        assert result["success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["filePath"] == "test.js"
        assert len(result["results"][0]["messages"]) == 1

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_eslint_failure(self, mock_run):
        """Test running ESLint with errors."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "eslint")

        result = run_eslint(["test.js"])

        assert result["success"] is False
        assert "error" in result["error"].lower()

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_eslint_invalid_json(self, mock_run):
        """Test running ESLint with invalid JSON output."""
        mock_run.return_value = Mock(returncode=0, stdout="invalid json", stderr="")

        result = run_eslint(["test.js"])

        assert result["success"] is False
        assert "error" in result["error"].lower()


class TestPrettier:
    """Test Prettier functionality."""

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_prettier_success(self, mock_run):
        """Test running Prettier successfully."""
        mock_run.return_value = Mock(returncode=0, stdout="formatted code", stderr="")

        result = run_prettier_check(["test.js"])

        assert result["success"] is True
        assert result["formatted_files"] == ["test.js"]

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_prettier_failure(self, mock_run):
        """Test running Prettier with errors."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "prettier")

        result = run_prettier_check(["test.js"])

        assert result["success"] is False
        assert "error" in result["error"].lower()


class TestTypeScriptCheck:
    """Test TypeScript checking functionality."""

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_typescript_check_success(self, mock_run):
        """Test running TypeScript check successfully."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = run_typescript_check(["test.ts"])

        assert result["success"] is True
        assert result["errors"] == []

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_typescript_check_with_errors(self, mock_run):
        """Test running TypeScript check with errors."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="test.ts(5,1): error TS2304: Cannot find name 'undefined'",
        )

        result = run_typescript_check(["test.ts"])

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "TS2304" in result["errors"][0]


class TestJestTests:
    """Test Jest test functionality."""

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_jest_tests_success(self, mock_run):
        """Test running Jest tests successfully."""
        mock_run.return_value = Mock(
            returncode=0, stdout="Tests: 5 passed, 5 total", stderr=""
        )

        result = run_jest_tests()

        assert result["success"] is True
        assert result["passed"] is True
        assert "5 passed" in result["output"]

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_jest_tests_failure(self, mock_run):
        """Test running Jest tests with failures."""
        mock_run.return_value = Mock(
            returncode=1, stdout="Tests: 3 passed, 2 failed, 5 total", stderr=""
        )

        result = run_jest_tests()

        assert result["success"] is True
        assert result["passed"] is False
        assert "2 failed" in result["output"]

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_jest_tests_error(self, mock_run):
        """Test running Jest tests with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "jest")

        result = run_jest_tests()

        assert result["success"] is False
        assert result["passed"] is False
        assert "error" in result["error"].lower()


class TestGenerateJestTests:
    """Test Jest test generation functionality."""

    def test_generate_jest_tests_function(self):
        """Test generating Jest tests for a function."""
        code_change = JSFileChange(
            change_type="function",
            function_name="add",
            file_path="math.js",
            line_number=10,
            content="function add(a, b) { return a + b; }",
        )

        support = JavaScriptTypeScriptSupport()
        tests = support.generate_tests(code_change)

        assert "describe('add'" in tests
        assert "test('should add two numbers'" in tests
        assert "expect(add(2, 3)).toBe(5)" in tests

    def test_generate_jest_tests_class(self):
        """Test generating Jest tests for a class."""
        code_change = JSFileChange(
            change_type="class",
            class_name="Calculator",
            file_path="calculator.js",
            line_number=5,
            content="class Calculator { add(a, b) { return a + b; } }",
        )

        support = JavaScriptTypeScriptSupport()
        tests = support.generate_tests(code_change)

        assert "describe('Calculator'" in tests
        assert "test('should create instance'" in tests
        assert "new Calculator()" in tests

    def test_generate_jest_tests_unknown_type(self):
        """Test generating Jest tests for unknown change type."""
        code_change = JSFileChange(
            change_type="unknown",
            file_path="test.js",
            line_number=1,
            content="some code",
        )

        support = JavaScriptTypeScriptSupport()
        tests = support.generate_tests(code_change)

        assert "describe('unknown'" in tests
        assert "test('should work'" in tests


class TestJavaScriptTypeScriptSupport:
    """Test JavaScriptTypeScriptSupport class."""

    def test_init(self):
        """Test initializing JavaScriptTypeScriptSupport."""
        support = JavaScriptTypeScriptSupport()
        assert support is not None

    @patch("ai_guard.language_support.js_ts_support.check_node_installed")
    @patch("ai_guard.language_support.js_ts_support.check_npm_installed")
    def test_check_environment(self, mock_npm, mock_node):
        """Test checking JavaScript/TypeScript environment."""
        mock_node.return_value = True
        mock_npm.return_value = True

        support = JavaScriptTypeScriptSupport()
        result = support.check_environment()

        assert result["node_installed"] is True
        assert result["npm_installed"] is True
        assert result["ready"] is True

    @patch("ai_guard.language_support.js_ts_support.check_node_installed")
    @patch("ai_guard.language_support.js_ts_support.check_npm_installed")
    def test_check_environment_missing_node(self, mock_npm, mock_node):
        """Test checking environment when Node.js is missing."""
        mock_node.return_value = False
        mock_npm.return_value = True

        support = JavaScriptTypeScriptSupport()
        result = support.check_environment()

        assert result["node_installed"] is False
        assert result["npm_installed"] is True
        assert result["ready"] is False

    @patch("ai_guard.language_support.js_ts_support.run_eslint")
    def test_run_lint_check(self, mock_eslint):
        """Test running lint check."""
        mock_eslint.return_value = {"success": True, "results": []}

        support = JavaScriptTypeScriptSupport()
        result = support.run_lint_check(["test.js"])

        assert result["success"] is True
        mock_eslint.assert_called_once_with(["test.js"])

    @patch("ai_guard.language_support.js_ts_support.run_prettier_check")
    def test_run_format_check(self, mock_prettier):
        """Test running format check."""
        mock_prettier.return_value = {"success": True, "formatted_files": []}

        support = JavaScriptTypeScriptSupport()
        result = support.run_format_check(["test.js"])

        assert result["success"] is True
        mock_prettier.assert_called_once_with(["test.js"])

    @patch("ai_guard.language_support.js_ts_support.run_typescript_check")
    def test_run_type_check(self, mock_tsc):
        """Test running type check."""
        mock_tsc.return_value = {"success": True, "errors": []}

        support = JavaScriptTypeScriptSupport()
        result = support.run_type_check(["test.ts"])

        assert result["success"] is True
        mock_tsc.assert_called_once_with(["test.ts"])

    @patch("ai_guard.language_support.js_ts_support.run_jest_tests")
    def test_run_tests(self, mock_jest):
        """Test running tests."""
        mock_jest.return_value = {
            "success": True,
            "passed": True,
            "output": "All tests passed",
        }

        support = JavaScriptTypeScriptSupport()
        result = support.run_tests()

        assert result["success"] is True
        assert result["passed"] is True
        mock_jest.assert_called_once()

    def test_generate_tests(self):
        """Test generating tests."""
        code_change = JSFileChange(
            change_type="function",
            function_name="multiply",
            file_path="math.js",
            line_number=15,
            content="function multiply(a, b) { return a * b; }",
        )

        support = JavaScriptTypeScriptSupport()
        tests = support.generate_tests(code_change)

        assert "describe('multiply'" in tests
        assert "test('should multiply two numbers'" in tests


class TestJSFileChange:
    """Test JSFileChange dataclass."""

    def test_js_file_change_creation(self):
        """Test creating JSFileChange instance."""
        change = JSFileChange(
            change_type="function",
            function_name="test_func",
            file_path="test.js",
            line_number=10,
            content="function test_func() { return true; }",
        )

        assert change.change_type == "function"
        assert change.function_name == "test_func"
        assert change.file_path == "test.js"
        assert change.line_number == 10
        assert change.content == "function test_func() { return true; }"
        assert change.class_name is None

    def test_js_file_change_with_class(self):
        """Test creating JSFileChange instance with class."""
        change = JSFileChange(
            change_type="class",
            class_name="TestClass",
            file_path="test.js",
            line_number=5,
            content="class TestClass { constructor() {} }",
        )

        assert change.change_type == "class"
        assert change.class_name == "TestClass"
        assert change.function_name is None


class TestJSTestGenerationConfig:
    """Test JSTestGenerationConfig dataclass."""

    def test_js_test_generation_config_creation(self):
        """Test creating JSTestGenerationConfig instance."""
        config = JSTestGenerationConfig(max_tests_per_file=10, include_comments=True)

        assert config.max_tests_per_file == 10
        assert config.include_comments is True


class TestIntegration:
    """Test integration scenarios."""

    @patch("ai_guard.language_support.js_ts_support.check_node_installed")
    @patch("ai_guard.language_support.js_ts_support.check_npm_installed")
    @patch("ai_guard.language_support.js_ts_support.run_eslint")
    @patch("ai_guard.language_support.js_ts_support.run_jest_tests")
    def test_full_workflow(self, mock_jest, mock_eslint, mock_npm, mock_node):
        """Test full JavaScript/TypeScript workflow."""
        mock_node.return_value = True
        mock_npm.return_value = True
        mock_eslint.return_value = {"success": True, "results": []}
        mock_jest.return_value = {
            "success": True,
            "passed": True,
            "output": "All tests passed",
        }

        support = JavaScriptTypeScriptSupport()

        # Check environment
        env_result = support.check_environment()
        assert env_result["ready"] is True

        # Run lint check
        lint_result = support.run_lint_check(["test.js"])
        assert lint_result["success"] is True

        # Run tests
        test_result = support.run_tests()
        assert test_result["success"] is True
        assert test_result["passed"] is True


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_eslint_timeout(self, mock_run):
        """Test ESLint timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("eslint", 30)

        result = run_eslint(["test.js"])

        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_prettier_permission_error(self, mock_run):
        """Test Prettier permission error handling."""
        mock_run.side_effect = PermissionError("Permission denied")

        result = run_prettier_check(["test.js"])

        assert result["success"] is False
        assert "permission" in result["error"].lower()

    def test_generate_tests_invalid_change(self):
        """Test generating tests with invalid code change."""
        code_change = JSFileChange(
            change_type="", file_path="", line_number=0, content=""
        )

        support = JavaScriptTypeScriptSupport()
        tests = support.generate_tests(code_change)

        # Should still generate some basic tests
        assert "describe" in tests
        assert "test" in tests


if __name__ == "__main__":
    pytest.main([__file__])
