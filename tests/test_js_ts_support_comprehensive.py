"""Comprehensive tests for js_ts_support module."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_typescript_check,
    run_jest_tests,
    run_prettier_check,
    JSTestGenerationConfig,
    JSFileChange,
    JavaScriptTypeScriptSupport
)


class TestCheckNodeInstalled:
    """Test check_node_installed function."""

    @patch('subprocess.run')
    def test_check_node_installed_success(self, mock_run):
        """Test successful Node.js check."""
        mock_run.return_value = MagicMock(returncode=0)
        result = check_node_installed()
        assert result is True

    @patch('subprocess.run')
    def test_check_node_installed_failure(self, mock_run):
        """Test failed Node.js check."""
        mock_run.return_value = MagicMock(returncode=1)
        result = check_node_installed()
        assert result is False

    @patch('subprocess.run')
    def test_check_node_installed_called_process_error(self, mock_run):
        """Test CalledProcessError."""
        mock_run.side_effect = Exception("Process error")
        result = check_node_installed()
        assert result is False

    @patch('subprocess.run')
    def test_check_node_installed_file_not_found(self, mock_run):
        """Test FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("Node not found")
        result = check_node_installed()
        assert result is False


class TestCheckNpmInstalled:
    """Test check_npm_installed function."""

    @patch('subprocess.run')
    def test_check_npm_installed_success(self, mock_run):
        """Test successful npm check."""
        mock_run.return_value = MagicMock(returncode=0)
        result = check_npm_installed()
        assert result is True

    @patch('subprocess.run')
    def test_check_npm_installed_failure(self, mock_run):
        """Test failed npm check."""
        mock_run.return_value = MagicMock(returncode=1)
        result = check_npm_installed()
        assert result is False

    @patch('subprocess.run')
    def test_check_npm_installed_called_process_error(self, mock_run):
        """Test CalledProcessError."""
        mock_run.side_effect = Exception("Process error")
        result = check_npm_installed()
        assert result is False

    @patch('subprocess.run')
    def test_check_npm_installed_file_not_found(self, mock_run):
        """Test FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("npm not found")
        result = check_npm_installed()
        assert result is False


class TestRunEslint:
    """Test run_eslint function."""

    @patch('subprocess.run')
    def test_run_eslint_success(self, mock_run):
        """Test successful ESLint run."""
        mock_run.return_value = MagicMock(returncode=0, stdout="No issues", stderr="")
        result = run_eslint(["test.js"])
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert result["output"] == "No issues"

    @patch('subprocess.run')
    def test_run_eslint_failure(self, mock_run):
        """Test failed ESLint run."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error found")
        result = run_eslint(["test.js"])
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert result["errors"] == "Error found"

    @patch('subprocess.run')
    def test_run_eslint_file_not_found(self, mock_run):
        """Test FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("ESLint not found")
        result = run_eslint(["test.js"])
        assert result["passed"] is False
        assert result["errors"] == "ESLint not found"
        assert result["returncode"] == 1


class TestRunTypescriptCheck:
    """Test run_typescript_check function."""

    @patch('subprocess.run')
    def test_run_typescript_check_success(self, mock_run):
        """Test successful TypeScript check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="No errors", stderr="")
        result = run_typescript_check(["test.ts"])
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert result["output"] == "No errors"

    @patch('subprocess.run')
    def test_run_typescript_check_failure(self, mock_run):
        """Test failed TypeScript check."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Type error")
        result = run_typescript_check(["test.ts"])
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert result["errors"] == "Type error"

    @patch('subprocess.run')
    def test_run_typescript_check_file_not_found(self, mock_run):
        """Test FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("TypeScript compiler not found")
        result = run_typescript_check(["test.ts"])
        assert result["passed"] is False
        assert result["errors"] == "TypeScript compiler not found"
        assert result["returncode"] == 1


class TestRunJestTests:
    """Test run_jest_tests function."""

    @patch('subprocess.run')
    def test_run_jest_tests_success(self, mock_run):
        """Test successful Jest run."""
        mock_run.return_value = MagicMock(returncode=0, stdout="All tests passed", stderr="")
        result = run_jest_tests()
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert result["output"] == "All tests passed"

    @patch('subprocess.run')
    def test_run_jest_tests_failure(self, mock_run):
        """Test failed Jest run."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Test failed")
        result = run_jest_tests()
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert result["errors"] == "Test failed"

    @patch('subprocess.run')
    def test_run_jest_tests_file_not_found(self, mock_run):
        """Test FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("Jest not found")
        result = run_jest_tests()
        assert result["passed"] is False
        assert result["errors"] == "Jest not found"
        assert result["returncode"] == 1


class TestRunPrettierCheck:
    """Test run_prettier_check function."""

    @patch('subprocess.run')
    def test_run_prettier_check_success(self, mock_run):
        """Test successful Prettier check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="All files formatted", stderr="")
        result = run_prettier_check(["test.js"])
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert result["output"] == "All files formatted"

    @patch('subprocess.run')
    def test_run_prettier_check_failure(self, mock_run):
        """Test failed Prettier check."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Formatting issues")
        result = run_prettier_check(["test.js"])
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert result["errors"] == "Formatting issues"

    @patch('subprocess.run')
    def test_run_prettier_check_file_not_found(self, mock_run):
        """Test FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("Prettier not found")
        result = run_prettier_check(["test.js"])
        assert result["passed"] is False
        assert result["errors"] == "Prettier not found"
        assert result["returncode"] == 1


class TestJSTestGenerationConfig:
    """Test JSTestGenerationConfig class."""

    def test_js_test_generation_config_init(self):
        """Test JSTestGenerationConfig initialization."""
        config = JSTestGenerationConfig()
        assert config.framework == "jest"
        assert config.coverage_threshold == 80.0
        assert config.test_directory == "tests"
        assert config.include_mocks is True

    def test_js_test_generation_config_custom_values(self):
        """Test JSTestGenerationConfig with custom values."""
        config = JSTestGenerationConfig(
            framework="mocha",
            coverage_threshold=90.0,
            test_directory="spec",
            include_mocks=False
        )
        assert config.framework == "mocha"
        assert config.coverage_threshold == 90.0
        assert config.test_directory == "spec"
        assert config.include_mocks is False


class TestJSFileChange:
    """Test JSFileChange class."""

    def test_js_file_change_init(self):
        """Test JSFileChange initialization."""
        change = JSFileChange(
            file_path="test.js",
            change_type="modified",
            lines_changed=[1, 2, 3]
        )
        assert change.file_path == "test.js"
        assert change.change_type == "modified"
        assert change.lines_changed == [1, 2, 3]

    def test_js_file_change_defaults(self):
        """Test JSFileChange with default values."""
        change = JSFileChange(file_path="test.js")
        assert change.file_path == "test.js"
        assert change.change_type == "unknown"
        assert change.lines_changed == []


class TestJavaScriptTypeScriptSupport:
    """Test JavaScriptTypeScriptSupport class."""

    def test_javascript_typescript_support_init(self):
        """Test JavaScriptTypeScriptSupport initialization."""
        support = JavaScriptTypeScriptSupport()
        assert support.language == "javascript"
        assert support.extensions == [".js", ".jsx", ".ts", ".tsx"]

    def test_check_dependencies(self):
        """Test check_dependencies method."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.check_node_installed') as mock_node:
            with patch('src.ai_guard.language_support.js_ts_support.check_npm_installed') as mock_npm:
                mock_node.return_value = True
                mock_npm.return_value = True
                result = support.check_dependencies()
                assert result["node_installed"] is True
                assert result["npm_installed"] is True

    def test_check_dependencies_node_missing(self):
        """Test check_dependencies with Node.js missing."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.check_node_installed') as mock_node:
            with patch('src.ai_guard.language_support.js_ts_support.check_npm_installed') as mock_npm:
                mock_node.return_value = False
                mock_npm.return_value = True
                result = support.check_dependencies()
                assert result["node_installed"] is False
                assert result["npm_installed"] is True

    def test_check_dependencies_npm_missing(self):
        """Test check_dependencies with npm missing."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.check_node_installed') as mock_node:
            with patch('src.ai_guard.language_support.js_ts_support.check_npm_installed') as mock_npm:
                mock_node.return_value = True
                mock_npm.return_value = False
                result = support.check_dependencies()
                assert result["node_installed"] is True
                assert result["npm_installed"] is False

    def test_run_linting(self):
        """Test run_linting method."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.run_eslint') as mock_eslint:
            mock_eslint.return_value = {"passed": True, "output": "No issues"}
            result = support.run_linting(["test.js"])
            assert result["passed"] is True
            assert result["output"] == "No issues"

    def test_run_type_checking(self):
        """Test run_type_checking method."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.run_typescript_check') as mock_tsc:
            mock_tsc.return_value = {"passed": True, "output": "No errors"}
            result = support.run_type_checking(["test.ts"])
            assert result["passed"] is True
            assert result["output"] == "No errors"

    def test_run_tests(self):
        """Test run_tests method."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.run_jest_tests') as mock_jest:
            mock_jest.return_value = {"passed": True, "output": "All tests passed"}
            result = support.run_tests()
            assert result["passed"] is True
            assert result["output"] == "All tests passed"

    def test_run_formatting_check(self):
        """Test run_formatting_check method."""
        support = JavaScriptTypeScriptSupport()
        
        with patch('src.ai_guard.language_support.js_ts_support.run_prettier_check') as mock_prettier:
            mock_prettier.return_value = {"passed": True, "output": "All files formatted"}
            result = support.run_formatting_check(["test.js"])
            assert result["passed"] is True
            assert result["output"] == "All files formatted"

    def test_generate_test_file(self):
        """Test generate_test_file method."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = os.path.join(temp_dir, "calculator.js")
            with open(source_file, 'w') as f:
                f.write("function add(a, b) { return a + b; }")
            
            test_file = support.generate_test_file(source_file, temp_dir)
            assert test_file is not None
            assert os.path.exists(test_file)

    def test_generate_test_file_typescript(self):
        """Test generate_test_file method for TypeScript."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = os.path.join(temp_dir, "calculator.ts")
            with open(source_file, 'w') as f:
                f.write("export function add(a: number, b: number): number { return a + b; }")
            
            test_file = support.generate_test_file(source_file, temp_dir)
            assert test_file is not None
            assert os.path.exists(test_file)

    def test_analyze_file_complexity(self):
        """Test analyze_file_complexity method."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = os.path.join(temp_dir, "complex.js")
            with open(source_file, 'w') as f:
                f.write("""
                function complexFunction(a, b, c) {
                    if (a > b) {
                        if (c > 0) {
                            return a + c;
                        } else {
                            return a - c;
                        }
                    } else {
                        return b;
                    }
                }
                """)
            
            result = support.analyze_file_complexity(source_file)
            assert result["complexity"] > 0
            assert result["lines_of_code"] > 0

    def test_get_file_dependencies(self):
        """Test get_file_dependencies method."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = os.path.join(temp_dir, "module.js")
            with open(source_file, 'w') as f:
                f.write("""
                const fs = require('fs');
                const path = require('path');
                import { helper } from './helper.js';
                """)
            
            result = support.get_file_dependencies(source_file)
            assert "fs" in result["node_modules"]
            assert "path" in result["node_modules"]
            assert "./helper.js" in result["local_modules"]

    def test_check_security_vulnerabilities(self):
        """Test check_security_vulnerabilities method."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = os.path.join(temp_dir, "vulnerable.js")
            with open(source_file, 'w') as f:
                f.write("""
                const userInput = req.query.input;
                eval(userInput);
                """)
            
            result = support.check_security_vulnerabilities(source_file)
            assert len(result["vulnerabilities"]) > 0

    def test_get_code_metrics(self):
        """Test get_code_metrics method."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = os.path.join(temp_dir, "metrics.js")
            with open(source_file, 'w') as f:
                f.write("""
                function example() {
                    console.log('Hello World');
                    return 42;
                }
                """)
            
            result = support.get_code_metrics(source_file)
            assert result["lines_of_code"] > 0
            assert result["functions"] > 0
            assert result["classes"] >= 0

    def test_validate_syntax(self):
        """Test validate_syntax method."""
        support = JavaScriptTypeScriptSupport()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid JavaScript
            valid_file = os.path.join(temp_dir, "valid.js")
            with open(valid_file, 'w') as f:
                f.write("function test() { return true; }")
            
            result = support.validate_syntax(valid_file)
            assert result["valid"] is True
            
            # Invalid JavaScript
            invalid_file = os.path.join(temp_dir, "invalid.js")
            with open(invalid_file, 'w') as f:
                f.write("function test() { return true; // missing closing brace")
            
            result = support.validate_syntax(invalid_file)
            assert result["valid"] is False

    def test_get_supported_extensions(self):
        """Test get_supported_extensions method."""
        support = JavaScriptTypeScriptSupport()
        extensions = support.get_supported_extensions()
        assert ".js" in extensions
        assert ".jsx" in extensions
        assert ".ts" in extensions
        assert ".tsx" in extensions

    def test_is_supported_file(self):
        """Test is_supported_file method."""
        support = JavaScriptTypeScriptSupport()
        
        assert support.is_supported_file("test.js") is True
        assert support.is_supported_file("component.jsx") is True
        assert support.is_supported_file("module.ts") is True
        assert support.is_supported_file("component.tsx") is True
        assert support.is_supported_file("test.py") is False
        assert support.is_supported_file("README.md") is False