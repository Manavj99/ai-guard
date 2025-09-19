"""Basic tests for js_ts_support.py module."""

import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

from src.ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_typescript_check,
    run_jest_tests,
    run_prettier_check,
    JSTestGenerationConfig,
    JSFileChange,
    JavaScriptTypeScriptSupport,
    main
)


class TestCheckFunctions:
    """Test utility check functions."""

    def test_check_node_installed_success(self):
        """Test check_node_installed when Node.js is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = check_node_installed()
            assert result is True
            mock_run.assert_called_once_with(
                ["node", "--version"], capture_output=True, text=True, check=True
            )

    def test_check_node_installed_failure(self):
        """Test check_node_installed when Node.js is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = check_node_installed()
            assert result is False

    def test_check_npm_installed_success(self):
        """Test check_npm_installed when npm is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = check_npm_installed()
            assert result is True
            mock_run.assert_called_once_with(
                ["npm", "--version"], capture_output=True, text=True, check=True
            )

    def test_check_npm_installed_failure(self):
        """Test check_npm_installed when npm is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = check_npm_installed()
            assert result is False


class TestRunFunctions:
    """Test run functions for various tools."""

    def test_run_eslint_success(self):
        """Test run_eslint with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="No issues found",
                stderr=""
            )
            
            result = run_eslint(["test.js"])
            
            assert result["passed"] is True
            assert result["returncode"] == 0
            assert result["output"] == "No issues found"
            assert result["errors"] == ""

    def test_run_eslint_failure(self):
        """Test run_eslint with linting errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="test.js:1:1: error: Unexpected var",
                stderr=""
            )
            
            result = run_eslint(["test.js"])
            
            assert result["passed"] is False
            assert result["returncode"] == 1
            assert "Unexpected var" in result["output"]

    def test_run_eslint_not_found(self):
        """Test run_eslint when ESLint is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = run_eslint(["test.js"])
            
            assert result["passed"] is False
            assert result["errors"] == "ESLint not found"
            assert result["returncode"] == 1

    def test_run_typescript_check_success(self):
        """Test run_typescript_check with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="",
                stderr=""
            )
            
            result = run_typescript_check(["test.ts"])
            
            assert result["passed"] is True
            assert result["returncode"] == 0

    def test_run_jest_tests_success(self):
        """Test run_jest_tests with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="All tests passed",
                stderr=""
            )
            
            result = run_jest_tests()
            
            assert result["passed"] is True
            assert result["returncode"] == 0
            assert result["output"] == "All tests passed"

    def test_run_prettier_check_success(self):
        """Test run_prettier_check with successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="",
                stderr=""
            )
            
            result = run_prettier_check(["test.js"])
            
            assert result["passed"] is True
            assert result["returncode"] == 0


class TestJSTestGenerationConfig:
    """Test JSTestGenerationConfig dataclass."""

    def test_config_defaults(self):
        """Test JSTestGenerationConfig with default values."""
        config = JSTestGenerationConfig()
        
        assert config.test_framework == "jest"
        assert config.test_runner == "npm test"
        assert config.use_eslint is True
        assert config.use_prettier is True
        assert config.use_typescript is False
        assert config.generate_unit_tests is True
        assert config.output_directory == "tests"
        assert config.test_file_suffix == ".test.js"

    def test_config_custom_values(self):
        """Test JSTestGenerationConfig with custom values."""
        config = JSTestGenerationConfig(
            test_framework="vitest",
            use_typescript=True,
            output_directory="custom_tests",
            test_file_suffix=".spec.ts"
        )
        
        assert config.test_framework == "vitest"
        assert config.use_typescript is True
        assert config.output_directory == "custom_tests"
        assert config.test_file_suffix == ".spec.ts"


class TestJSFileChange:
    """Test JSFileChange dataclass."""

    def test_js_file_change_creation(self):
        """Test creating JSFileChange."""
        change = JSFileChange(
            file_path="src/utils.js",
            function_name="calculateSum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="function calculateSum(a, b) { return a + b; }",
            context="Added new utility function"
        )
        
        assert change.file_path == "src/utils.js"
        assert change.function_name == "calculateSum"
        assert change.class_name is None
        assert change.change_type == "function"
        assert change.line_numbers == (10, 15)
        assert "calculateSum" in change.code_snippet
        assert change.context == "Added new utility function"

    def test_js_file_change_class(self):
        """Test creating JSFileChange for class."""
        change = JSFileChange(
            file_path="src/User.ts",
            function_name=None,
            class_name="User",
            change_type="class",
            line_numbers=(5, 20),
            code_snippet="class User { constructor(name) { this.name = name; } }",
            context="Added User class"
        )
        
        assert change.file_path == "src/User.ts"
        assert change.function_name is None
        assert change.class_name == "User"
        assert change.change_type == "class"


class TestJavaScriptTypeScriptSupport:
    """Test JavaScriptTypeScriptSupport class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        with patch("pathlib.Path.cwd") as mock_cwd, \
             patch("pathlib.Path.exists") as mock_exists, \
             patch("builtins.open", mock_open(read_data='{"name": "test-project"}')) as mock_file:
            
            mock_cwd.return_value = Path("/test/project")
            mock_exists.return_value = True
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            assert support.config == config
            assert support.project_root == Path("/test/project")
            assert support.package_json == {"name": "test-project"}

    def test_init_no_package_json(self):
        """Test initialization without package.json."""
        with patch("pathlib.Path.cwd") as mock_cwd, \
             patch("pathlib.Path.exists") as mock_exists:
            
            mock_cwd.return_value = Path("/test/project")
            mock_exists.return_value = False
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            assert support.package_json == {}

    def test_load_package_json_success(self):
        """Test loading package.json successfully."""
        package_data = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.0.0"
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0"
            }
        }
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(package_data))):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support._load_package_json()
            assert result == package_data

    def test_load_package_json_invalid_json(self):
        """Test loading invalid package.json."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="invalid json")):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support._load_package_json()
            assert result == {}

    def test_check_dependencies(self):
        """Test checking dependencies."""
        package_data = {
            "dependencies": {"react": "^18.0.0"},
            "devDependencies": {"jest": "^29.0.0", "eslint": "^8.0.0"}
        }
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(package_data))), \
             patch("subprocess.run") as mock_run:
            
            # Mock subprocess calls to return success
            mock_run.return_value = Mock(returncode=0)
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.check_dependencies()
            
            assert result["eslint"] is True
            assert result["prettier"] is True
            assert result["jest"] is True
            assert result["typescript"] is True

    def test_run_eslint_success(self):
        """Test running ESLint successfully."""
        eslint_output = [
            {
                "filePath": "test.js",
                "messages": []
            }
        ]
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(eslint_output),
                stderr=""
            )
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            passed, issues = support.run_eslint(["test.js"])
            
            assert passed is True
            assert issues == []

    def test_run_eslint_with_issues(self):
        """Test running ESLint with issues."""
        eslint_output = [
            {
                "filePath": "test.js",
                "messages": [
                    {
                        "line": 1,
                        "column": 1,
                        "severity": 2,
                        "message": "Unexpected var",
                        "ruleId": "no-var"
                    }
                ]
            }
        ]
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value = Mock(
                returncode=1,
                stdout=json.dumps(eslint_output),
                stderr=""
            )
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            passed, issues = support.run_eslint(["test.js"])
            
            assert passed is False
            assert len(issues) == 1
            assert issues[0]["message"] == "Unexpected var"
            assert issues[0]["rule"] == "no-var"

    def test_run_quality_checks(self):
        """Test running all quality checks."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch.object(JavaScriptTypeScriptSupport, 'run_eslint', return_value=(True, [])), \
             patch.object(JavaScriptTypeScriptSupport, 'run_prettier', return_value=(True, [])), \
             patch.object(JavaScriptTypeScriptSupport, 'run_typescript_check', return_value=(True, [])):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            results = support.run_quality_checks(["test.js"])
            
            assert results["eslint"]["passed"] is True
            assert results["prettier"]["passed"] is True
            assert results["typescript"]["passed"] is True
            assert results["overall"] is True

    def test_run_quality_checks_with_failures(self):
        """Test running quality checks with failures."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch.object(JavaScriptTypeScriptSupport, 'run_eslint', return_value=(False, [{"message": "Error"}])), \
             patch.object(JavaScriptTypeScriptSupport, 'run_prettier', return_value=(True, [])), \
             patch.object(JavaScriptTypeScriptSupport, 'run_typescript_check', return_value=(True, [])):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            results = support.run_quality_checks(["test.js"])
            
            assert results["eslint"]["passed"] is False
            assert results["prettier"]["passed"] is True
            assert results["overall"] is False

    def test_generate_test_templates(self):
        """Test generating test templates."""
        test_content = """
function calculateSum(a, b) {
    return a + b;
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
"""
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch("builtins.open", mock_open(read_data=test_content)) as mock_file_open:
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            templates = support.generate_test_templates(["test.js"])
            
            assert "test.js" in templates
            template_content = templates["test.js"]
            assert "Auto-generated test file" in template_content
            assert "describe" in template_content
            assert "test" in template_content

    def test_create_test_file(self):
        """Test creating test file."""
        test_content = "describe('test', () => { test('works', () => { expect(true).toBe(true); }); });"
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch("pathlib.Path.mkdir") as mock_mkdir, \
             patch("builtins.open", mock_open()) as mock_file_open:
            
            config = JSTestGenerationConfig(output_directory="tests")
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.create_test_file("src/utils.js", test_content)
            
            assert result.endswith("utils.test.js")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_file_open.assert_called_once()

    def test_run_linting_file(self):
        """Test running linting on single file."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch("pathlib.Path.is_dir", return_value=False), \
             patch.object(JavaScriptTypeScriptSupport, 'run_eslint', return_value=(True, [])):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.run_linting("test.js")
            
            assert result["success"] is True
            assert "Linting passed" in result["output"]

    def test_run_testing_success(self):
        """Test running tests successfully."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch.object(JavaScriptTypeScriptSupport, 'check_dependencies', return_value={"jest": True}), \
             patch.object(JavaScriptTypeScriptSupport, 'run_jest_tests', return_value=(True, {"message": "All tests passed"})):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.run_testing()
            
            assert result["success"] is True
            assert "Tests passed" in result["output"]

    def test_run_testing_no_jest(self):
        """Test running tests when Jest is not available."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch.object(JavaScriptTypeScriptSupport, 'check_dependencies', return_value={"jest": False}):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.run_testing()
            
            assert result["success"] is False
            assert "Jest not available" in result["error"]

    def test_analyze_file_changes(self):
        """Test analyzing file changes."""
        changes = [
            JSFileChange(
                file_path="src/utils.js",
                function_name="calculateSum",
                class_name=None,
                change_type="function",
                line_numbers=(10, 15),
                code_snippet="function calculateSum(a, b) { return a + b; }",
                context="Added function"
            ),
            JSFileChange(
                file_path="src/User.js",
                function_name=None,
                class_name="User",
                change_type="class",
                line_numbers=(5, 20),
                code_snippet="class User { constructor(name) { this.name = name; } }",
                context="Added class"
            )
        ]
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.analyze_file_changes(changes)
            
            assert "utils.js" in result
            assert "User.js" in result
            assert len(result["utils.js"]["functions"]) == 1
            assert len(result["User.js"]["classes"]) == 1

    def test_generate_test_content_function(self):
        """Test generating test content for function."""
        change = JSFileChange(
            file_path="src/utils.js",
            function_name="calculateSum",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="function calculateSum(a, b) { return a + b; }",
            context="Added function"
        )
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.generate_test_content(change)
            
            assert "calculateSum" in result
            assert "describe" in result
            assert "test" in result

    def test_validate_code_quality(self):
        """Test validating code quality."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')), \
             patch.object(JavaScriptTypeScriptSupport, 'run_linting', return_value={"success": True}), \
             patch.object(JavaScriptTypeScriptSupport, 'run_testing', return_value={"success": True}):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.validate_code_quality("test.js")
            
            assert result["overall_success"] is True
            assert result["linting"]["success"] is True
            assert result["testing"]["success"] is True

    def test_get_recommendations(self):
        """Test getting recommendations."""
        analysis = {
            "utils.js": {
                "functions": ["calculateSum", "calculateProduct"],
                "classes": [],
                "imports": []
            },
            "User.js": {
                "functions": [],
                "classes": ["User"],
                "imports": []
            }
        }
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.get_recommendations(analysis)
            
            assert len(result) == 2
            assert "2 functions in utils.js" in result[0]
            assert "1 classes in User.js" in result[1]

    def test_export_results(self):
        """Test exporting results."""
        analysis = {"test": "data"}
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data='{}')):
            
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)
            
            result = support.export_results(analysis)
            
            assert "timestamp" in result
            assert result["analysis"] == analysis
            assert "config" in result
            assert "project_root" in result
            assert "package_json" in result


class TestMain:
    """Test main function."""

    def test_main_check_deps(self):
        """Test main function with check-deps flag."""
        test_args = [
            "js_ts_support.py",
            "--check-deps"
        ]
        
        with patch("sys.argv", test_args), \
             patch("src.ai_guard.language_support.js_ts_support.JavaScriptTypeScriptSupport") as mock_support_class, \
             patch("builtins.print") as mock_print:
            
            mock_support = Mock()
            mock_support_class.return_value = mock_support
            mock_support.check_dependencies.return_value = {
                "eslint": True,
                "prettier": True,
                "jest": False,
                "typescript": True
            }
            
            main()
            
            mock_print.assert_called()
            # Check that dependencies were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Dependencies:" in call for call in print_calls)

    def test_main_quality_checks(self):
        """Test main function with quality checks."""
        test_args = [
            "js_ts_support.py",
            "--files", "test.js", "test2.js",
            "--quality"
        ]
        
        with patch("sys.argv", test_args), \
             patch("src.ai_guard.language_support.js_ts_support.JavaScriptTypeScriptSupport") as mock_support_class, \
             patch("builtins.print") as mock_print:
            
            mock_support = Mock()
            mock_support_class.return_value = mock_support
            mock_support.run_quality_checks.return_value = {
                "eslint": {"passed": True, "issues": []},
                "prettier": {"passed": False, "issues": ["test.js needs formatting"]},
                "typescript": {"passed": True, "issues": []},
                "overall": False
            }
            
            main()
            
            mock_print.assert_called()
            # Check that quality results were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Quality Check Results:" in call for call in print_calls)

    def test_main_generate_tests(self):
        """Test main function with test generation."""
        test_args = [
            "js_ts_support.py",
            "--files", "test.js",
            "--generate-tests",
            "--output-dir", "custom_tests"
        ]
        
        with patch("sys.argv", test_args), \
             patch("src.ai_guard.language_support.js_ts_support.JavaScriptTypeScriptSupport") as mock_support_class, \
             patch("builtins.print") as mock_print:
            
            mock_support = Mock()
            mock_support_class.return_value = mock_support
            mock_support.generate_tests.return_value = {
                "test.js": "custom_tests/test.test.js"
            }
            
            main()
            
            mock_print.assert_called()
            # Check that test generation results were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Generated Test Files:" in call for call in print_calls)
