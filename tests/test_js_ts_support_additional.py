"""Additional tests for JavaScript/TypeScript language support."""

import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_prettier_check,
    run_typescript_check,
    run_jest_tests
)


class TestNodeNpmChecks:
    """Test Node.js and npm availability checks."""

    @patch('subprocess.run')
    def test_check_node_installed_success(self, mock_run):
        """Test successful Node.js check."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = check_node_installed()
        
        assert result is True
        mock_run.assert_called_once_with(
            ["node", "--version"], capture_output=True, text=True, check=True
        )

    @patch('subprocess.run')
    def test_check_node_installed_failure(self, mock_run):
        """Test failed Node.js check."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "node")
        
        result = check_node_installed()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_node_installed_not_found(self, mock_run):
        """Test Node.js not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = check_node_installed()
        
        assert result is False

    @patch('subprocess.run')
    def test_check_npm_installed_success(self, mock_run):
        """Test successful npm check."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = check_npm_installed()
        
        assert result is True
        mock_run.assert_called_once_with(
            ["npm", "--version"], capture_output=True, text=True, check=True
        )

    @patch('subprocess.run')
    def test_check_npm_installed_failure(self, mock_run):
        """Test failed npm check."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "npm")
        
        result = check_npm_installed()
        
        assert result is False


class TestESLintRunner:
    """Test ESLint functionality."""

    @patch('subprocess.run')
    def test_run_eslint_success(self, mock_run):
        """Test successful ESLint run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="No linting errors found",
            stderr=""
        )
        
        result = run_eslint(["test.js"])
        
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert "No linting errors found" in result["output"]

    @patch('subprocess.run')
    def test_run_eslint_failure(self, mock_run):
        """Test failed ESLint run."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="ESLint found errors"
        )
        
        result = run_eslint(["test.js"])
        
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert "ESLint found errors" in result["errors"]

    def test_run_eslint_not_found(self):
        """Test ESLint when not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = run_eslint(["test.js"])
        
        assert result["passed"] is False
        assert result["errors"] == "ESLint not found"
        assert result["returncode"] == 1


class TestPrettierRunner:
    """Test Prettier functionality."""

    @patch('subprocess.run')
    def test_run_prettier_check_success(self, mock_run):
        """Test successful Prettier check."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All files are formatted",
            stderr=""
        )
        
        result = run_prettier_check(["test.js"])
        
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert "All files are formatted" in result["output"]

    @patch('subprocess.run')
    def test_run_prettier_check_not_formatted(self, mock_run):
        """Test Prettier check with unformatted files."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Files need formatting"
        )
        
        result = run_prettier_check(["test.js"])
        
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert "Files need formatting" in result["errors"]

    def test_run_prettier_check_not_found(self):
        """Test Prettier check when not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = run_prettier_check(["test.js"])
        
        assert result["passed"] is False
        assert result["errors"] == "Prettier not found"
        assert result["returncode"] == 1


class TestTypeScriptChecker:
    """Test TypeScript checking functionality."""

    @patch('subprocess.run')
    def test_run_typescript_check_success(self, mock_run):
        """Test successful TypeScript check."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        result = run_typescript_check(["test.ts"])
        
        assert result["passed"] is True
        assert result["returncode"] == 0

    @patch('subprocess.run')
    def test_run_typescript_check_with_errors(self, mock_run):
        """Test TypeScript check with errors."""
        mock_run.return_value = MagicMock(
            returncode=2,
            stdout="",
            stderr="error TS2304: Cannot find name 'foo'"
        )
        
        result = run_typescript_check(["test.ts"])
        
        assert result["passed"] is False
        assert result["returncode"] == 2
        assert "TS2304" in result["errors"]

    def test_run_typescript_check_not_found(self):
        """Test TypeScript check when not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = run_typescript_check(["test.ts"])
        
        assert result["passed"] is False
        assert result["errors"] == "TypeScript compiler not found"
        assert result["returncode"] == 1


class TestJestRunner:
    """Test Jest test runner functionality."""

    @patch('subprocess.run')
    def test_run_jest_tests_success(self, mock_run):
        """Test successful Jest run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All tests passed",
            stderr=""
        )
        
        result = run_jest_tests()
        
        assert result["passed"] is True
        assert result["returncode"] == 0
        assert "All tests passed" in result["output"]

    @patch('subprocess.run')
    def test_run_jest_tests_failure(self, mock_run):
        """Test failed Jest run."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Some tests failed"
        )
        
        result = run_jest_tests()
        
        assert result["passed"] is False
        assert result["returncode"] == 1
        assert "Some tests failed" in result["errors"]

    def test_run_jest_tests_not_found(self):
        """Test Jest run when not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = run_jest_tests()
        
        assert result["passed"] is False
        assert result["errors"] == "Jest not found"
        assert result["returncode"] == 1


class TestAdditionalJSTSFunctions:
    """Test additional JavaScript/TypeScript functions."""

    def test_check_node_installed_integration(self):
        """Test Node.js check integration."""
        result = check_node_installed()
        
        # This will be True or False depending on system
        assert isinstance(result, bool)

    def test_check_npm_installed_integration(self):
        """Test npm check integration."""
        result = check_npm_installed()
        
        # This will be True or False depending on system
        assert isinstance(result, bool)

    def test_run_jest_tests_integration(self):
        """Test Jest tests integration."""
        result = run_jest_tests()
        
        # Should return a dictionary with expected keys
        assert isinstance(result, dict)
        assert "passed" in result
        assert "returncode" in result
        assert "output" in result
        assert "errors" in result
