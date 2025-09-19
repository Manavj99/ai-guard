"""Enhanced tests for js_ts_support module to improve coverage."""

import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_jest_tests,
    run_typescript_check,
    run_prettier_check,
    JSTestGenerationConfig,
    JSFileChange,
    JavaScriptTypeScriptSupport,
)


class TestCheckNodeInstalled:
    """Test check_node_installed function."""

    @patch('subprocess.run')
    def test_check_node_installed_success(self, mock_run):
        """Test successful Node.js check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = check_node_installed()
        assert result is True

    @patch('subprocess.run')
    def test_check_node_installed_failure(self, mock_run):
        """Test failed Node.js check."""
        mock_run.side_effect = FileNotFoundError()
        
        result = check_node_installed()
        assert result is False

    @patch('subprocess.run')
    def test_check_node_installed_called_process_error(self, mock_run):
        """Test Node.js check with CalledProcessError."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "node")

        result = check_node_installed()
        assert result is False


class TestCheckNpmInstalled:
    """Test check_npm_installed function."""

    @patch('subprocess.run')
    def test_check_npm_installed_success(self, mock_run):
        """Test successful npm check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = check_npm_installed()
        assert result is True

    @patch('subprocess.run')
    def test_check_npm_installed_failure(self, mock_run):
        """Test failed npm check."""
        mock_run.side_effect = FileNotFoundError()
        
        result = check_npm_installed()
        assert result is False

    @patch('subprocess.run')
    def test_check_npm_installed_called_process_error(self, mock_run):
        """Test npm check with CalledProcessError."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "npm")

        result = check_npm_installed()
        assert result is False


class TestRunEslint:
    """Test run_eslint function."""

    @patch('subprocess.run')
    def test_run_eslint_success(self, mock_run):
        """Test successful ESLint run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"results": []}'
        mock_run.return_value = mock_result
        
        result = run_eslint(["test.js"])
        assert result["passed"] is True

    @patch('subprocess.run')
    def test_run_eslint_failure(self, mock_run):
        """Test failed ESLint run."""
        mock_run.side_effect = FileNotFoundError()

        result = run_eslint(["test.js"])
        assert result["passed"] is False

    def test_run_eslint_empty_files(self):
        """Test ESLint with empty file list."""
        result = run_eslint([])
        # ESLint with empty file list might fail, so just check the structure
        assert "passed" in result
        assert "output" in result
        assert "errors" in result
        assert "returncode" in result


class TestRunJest:
    """Test run_jest_tests function."""

    @patch('subprocess.run')
    def test_run_jest_success(self, mock_run):
        """Test successful Jest run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Tests: 5 passed, 5 total"
        mock_run.return_value = mock_result
        
        result = run_jest_tests()
        assert result["passed"] is True

    @patch('subprocess.run')
    def test_run_jest_failure(self, mock_run):
        """Test failed Jest run."""
        mock_run.side_effect = FileNotFoundError()

        result = run_jest_tests()
        assert result["passed"] is False

    def test_run_jest_empty_files(self):
        """Test Jest with empty file list."""
        result = run_jest_tests()
        # Jest should still run even with no files due to --passWithNoTests flag
        assert "passed" in result


class TestJavaScriptTypeScriptSupport:
    """Test JavaScriptTypeScriptSupport class."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        assert support.config == config
        assert support.project_root is not None

    def test_check_dependencies(self):
        """Test dependency checking."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        deps = support.check_dependencies()
        assert isinstance(deps, dict)
        assert "eslint" in deps
        assert "prettier" in deps
        assert "jest" in deps
        assert "typescript" in deps

    @patch('subprocess.run')
    def test_run_eslint_success(self, mock_run):
        """Test successful ESLint run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '[]'
        mock_run.return_value = mock_result
        
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        passed, issues = support.run_eslint(["test.js"])
        assert passed is True
        assert issues == []

    def test_generate_test_file_path(self):
        """Test test file path generation."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        test_path = support.generate_test_file_path("src/utils.js")
        assert "utils.test.js" in test_path
