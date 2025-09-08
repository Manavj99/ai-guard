"""Working comprehensive tests for other modules."""

from unittest.mock import patch, MagicMock

from ai_guard.tests_runner import run_pytest_with_coverage
from ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_typescript_check,
    run_jest_tests,
)


class TestOtherModulesWorking:
    """Working comprehensive tests for other modules functionality."""

    @patch("ai_guard.tests_runner.subprocess.run")
    def test_run_pytest_with_coverage(self, mock_run):
        """Test run_pytest_with_coverage function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = run_pytest_with_coverage(["src/test.py"])

        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("ai_guard.tests_runner.subprocess.run")
    def test_run_pytest_with_coverage_failure(self, mock_run):
        """Test run_pytest_with_coverage with test failures."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Test failed")

        result = run_pytest_with_coverage(["src/test.py"])

        assert result.returncode == 1

    @patch("ai_guard.security_scanner.subprocess.run")
    def test_run_bandit_scan(self, mock_run):
        """Test run_bandit_scan function."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"results": []}', stderr=""
        )

        result = run_bandit_scan(["src/test.py"])

        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("ai_guard.security_scanner.subprocess.run")
    def test_run_bandit_scan_with_issues(self, mock_run):
        """Test run_bandit_scan with security issues."""
        bandit_output = {
            "results": [
                {
                    "test_id": "B101",
                    "test_name": "Test for use of assert detected",
                    "filename": "src/test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test for use of assert detected",
                }
            ]
        }

        mock_run.return_value = MagicMock(
            returncode=1, stdout=str(bandit_output), stderr=""
        )

        result = run_bandit_scan(["src/test.py"])

        assert result.returncode == 1

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_node_installed(self, mock_run):
        """Test check_node_installed function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="v18.0.0")

        result = check_node_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["node", "--version"], capture_output=True, text=True
        )

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_node_installed_not_found(self, mock_run):
        """Test check_node_installed when node is not installed."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="node: command not found"
        )

        result = check_node_installed()

        assert result is False

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_npm_installed(self, mock_run):
        """Test check_npm_installed function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="8.0.0")

        result = check_npm_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["npm", "--version"], capture_output=True, text=True
        )

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_check_npm_installed_not_found(self, mock_run):
        """Test check_npm_installed when npm is not installed."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="npm: command not found"
        )

        result = check_npm_installed()

        assert result is False

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_eslint(self, mock_run):
        """Test run_eslint function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = run_eslint(["src/test.js"])

        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_eslint_with_issues(self, mock_run):
        """Test run_eslint with linting issues."""
        eslint_output = """src/test.js
  1:1  error  'console' is not defined  no-undef
  2:5  warning  Missing semicolon  semi

2 problems (1 error, 1 warning)
"""

        mock_run.return_value = MagicMock(returncode=1, stdout=eslint_output, stderr="")

        result = run_eslint(["src/test.js"])

        assert result.returncode == 1

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_typescript_check(self, mock_run):
        """Test run_typescript_check function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = run_typescript_check(["src/test.ts"])

        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_typescript_check_with_errors(self, mock_run):
        """Test run_typescript_check with type errors."""
        tsc_output = """src/test.ts(1,1): error TS2304: Cannot find name 'console'.
src/test.ts(2,5): error TS2304: Cannot find name 'process'.
"""

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr=tsc_output)

        result = run_typescript_check(["src/test.ts"])

        assert result.returncode == 1

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_jest_tests(self, mock_run):
        """Test run_jest_tests function."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = run_jest_tests()

        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("ai_guard.language_support.js_ts_support.subprocess.run")
    def test_run_jest_tests_with_failures(self, mock_run):
        """Test run_jest_tests with test failures."""
        jest_output = """FAIL src/test.test.js
  ● Test suite failed to run

    Cannot find module 'some-module' from 'src/test.test.js'
"""

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr=jest_output)

        result = run_jest_tests()

        assert result.returncode == 1

    def test_run_pytest_with_coverage_no_files(self):
        """Test run_pytest_with_coverage with no files."""
        result = run_pytest_with_coverage([])

        # Should still run pytest even with no specific files
        assert hasattr(result, "returncode")

    def test_run_bandit_scan_no_files(self):
        """Test run_bandit_scan with no files."""
        with patch("ai_guard.security_scanner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='{"results": []}', stderr=""
            )

            result = run_bandit_scan([])

            assert result.returncode == 0

    def test_run_eslint_no_files(self):
        """Test run_eslint with no files."""
        with patch(
            "ai_guard.language_support.js_ts_support.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = run_eslint([])

            assert result.returncode == 0

    def test_run_typescript_check_no_files(self):
        """Test run_typescript_check with no files."""
        with patch(
            "ai_guard.language_support.js_ts_support.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = run_typescript_check([])

            assert result.returncode == 0
