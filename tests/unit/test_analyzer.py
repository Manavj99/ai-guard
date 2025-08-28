"""Tests for analyzer module."""

import pytest  # noqa: F401
from unittest.mock import patch, Mock, mock_open  # noqa: F401
import subprocess  # noqa: F401
from src.ai_guard.analyzer import (
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    _parse_bandit_json,
    main
)
from src.ai_guard.report import GateResult  # noqa: F401


class TestAnalyzer:
    """Test analyzer functionality."""

    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_lint_check()

        assert result.name == "Lint (flake8)"
        assert result.passed is True
        assert isinstance(sarif, list)

    @patch('subprocess.run')
    def test_run_lint_check_with_paths(self, mock_run):
        """Test lint check with specific paths."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        paths = ["src/ai_guard/analyzer.py"]
        result, sarif = run_lint_check(paths)

        assert result.name == "Lint (flake8)"
        assert result.passed is True
        # Verify the command included the paths
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]  # First positional argument
        assert call_args[0] == "flake8"
        assert "src/ai_guard/analyzer.py" in call_args

    @patch('subprocess.run')
    def test_run_lint_check_failure(self, mock_run):
        """Test lint check failure."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = "src/ai_guard/example.py:10:5: E999 SyntaxError"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_lint_check()

        assert result.name == "Lint (flake8)"
        assert result.passed is False
        assert len(sarif) > 0

    @patch('subprocess.run')
    def test_run_lint_check_file_not_found(self, mock_run):
        """Test lint check when flake8 is not found."""
        mock_run.side_effect = FileNotFoundError("flake8: command not found")

        result, sarif = run_lint_check()

        assert result.name == "Lint (flake8)"
        assert result.passed is False
        assert "flake8 not found" in result.details
        assert sarif == []

    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_type_check()

        assert result.name == "Static types (mypy)"
        assert result.passed is True
        assert isinstance(sarif, list)

    @patch('subprocess.run')
    def test_run_type_check_with_paths(self, mock_run):
        """Test type check with specific paths."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        paths = ["src/ai_guard/analyzer.py"]
        result, sarif = run_type_check(paths)

        assert result.name == "Static types (mypy)"
        assert result.passed is True
        # Verify the command included the paths
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]  # First positional argument
        assert call_args[0] == "mypy"
        assert "src/ai_guard/analyzer.py" in call_args

    @patch('subprocess.run')
    def test_run_type_check_failure(self, mock_run):
        """Test type check failure."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = "src/ai_guard/example.py:12: error: Incompatible return value type"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_type_check()

        assert result.name == "Static types (mypy)"
        assert result.passed is False
        assert len(sarif) > 0

    @patch('subprocess.run')
    def test_run_type_check_file_not_found(self, mock_run):
        """Test type check when mypy is not found."""
        mock_run.side_effect = FileNotFoundError("mypy: command not found")

        result, sarif = run_type_check()

        assert result.name == "Static types (mypy)"
        assert result.passed is False
        assert "mypy not found" in result.details
        assert sarif == []

    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON output."""
        bandit_json = {
            "results": [
                {
                    "filename": "src/ai_guard/secret.py",
                    "line_number": 8,
                    "issue_severity": "HIGH",
                    "issue_text": "Use of insecure function",
                    "test_id": "B102",
                },
                {
                    "filename": "src/ai_guard/mid.py",
                    "line_number": 20,
                    "issue_severity": "MEDIUM",
                    "issue_text": "Potential vulnerability",
                    "test_id": "B301",
                },
                {
                    "filename": "src/ai_guard/low.py",
                    "line_number": 15,
                    "issue_severity": "LOW",
                    "issue_text": "Minor issue",
                    "test_id": "B401",
                }
            ]
        }

        import json
        results = _parse_bandit_json(json.dumps(bandit_json))

        assert len(results) == 3

        # Check HIGH severity
        high = results[0]
        assert high.rule_id == "bandit:B102"
        assert high.level == "error"
        assert high.message == "Use of insecure function"

        # Check MEDIUM severity
        med = results[1]
        assert med.rule_id == "bandit:B301"
        assert med.level == "warning"
        assert med.message == "Potential vulnerability"

        # Check LOW severity
        low = results[2]
        assert low.rule_id == "bandit:B401"
        assert low.level == "note"
        assert low.message == "Minor issue"

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON output."""
        results = _parse_bandit_json("invalid json")
        assert results == []

    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON output."""
        results = _parse_bandit_json("{}")
        assert results == []

    @patch('subprocess.run')
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"results": []}'
        mock_run.return_value = mock_proc

        result, sarif = run_security_check()

        assert result.name == "Security (bandit)"
        assert result.passed is True
        assert sarif == []

    @patch('subprocess.run')
    def test_run_security_check_with_high_severity(self, mock_run):
        """Test security check with high severity issues."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = (
            '{"results": [{"filename": "test.py", "line_number": 10, "issue_severity": "HIGH"}]}'
        )
        mock_run.return_value = mock_proc

        result, sarif = run_security_check()

        assert result.name == "Security (bandit)"
        assert result.passed is False
        assert len(sarif) == 1
        assert sarif[0].level == "error"

    @patch('subprocess.run')
    def test_run_security_check_file_not_found(self, mock_run):
        """Test security check when bandit is not found."""
        mock_run.side_effect = FileNotFoundError("bandit: command not found")

        result, sarif = run_security_check()

        assert result.name == "Security (bandit)"
        assert result.passed is False
        assert "bandit not found" in result.details
        assert sarif == []

    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_passed(self, mock_cov_percent):
        """Test coverage check that passes."""
        mock_cov_percent.return_value = 85

        result = run_coverage_check(80)

        assert result.name == "Coverage"
        assert result.passed is True
        assert "85% >= 80%" in result.details

    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_failed(self, mock_cov_percent):
        """Test coverage check that fails."""
        mock_cov_percent.return_value = 75

        result = run_coverage_check(80)

        assert result.name == "Coverage"
        assert result.passed is False
        assert "75% >= 80%" in result.details

    @patch('argparse.ArgumentParser.parse_args')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.summarize')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('builtins.print')
    def test_main_basic_flow(
        self, mock_print, mock_write_sarif, mock_summarize,
        mock_coverage, mock_security, mock_type, mock_lint,
        mock_changed_files, mock_parse_args
    ):
        """Test main function basic flow."""
        # Mock command line arguments
        mock_args = Mock()
        mock_args.min_cov = 80
        mock_args.skip_tests = True
        mock_args.event = None
        mock_args.sarif = "test.sarif"
        mock_parse_args.return_value = mock_args

        # Mock function returns
        mock_changed_files.return_value = []
        mock_lint.return_value = (Mock(name="Lint", passed=True), [])
        mock_type.return_value = (Mock(name="Types", passed=True), [])
        mock_security.return_value = (Mock(name="Security", passed=True), [])
        mock_coverage.return_value = Mock(name="Coverage", passed=True)
        mock_summarize.return_value = 0

        # Mock sys.exit to prevent actual exit
        with patch('sys.exit') as mock_exit:
            main()

        # Verify all functions were called
        mock_changed_files.assert_called_once_with(None)
        mock_lint.assert_called_once_with(None)
        mock_type.assert_called_once_with(None)
        mock_security.assert_called_once()
        mock_coverage.assert_called_once_with(80)
        mock_summarize.assert_called_once()
        mock_write_sarif.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.run_pytest_with_coverage')
    @patch('src.ai_guard.analyzer.summarize')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('builtins.print')
    def test_main_with_tests(
        self, mock_print, mock_write_sarif, mock_summarize,
        mock_pytest, mock_coverage, mock_security, mock_type,
        mock_lint, mock_changed_files, mock_parse_args
    ):
        """Test main function with tests enabled."""
        # Mock command line arguments
        mock_args = Mock()
        mock_args.min_cov = 85
        mock_args.skip_tests = False
        mock_args.event = "event.json"
        mock_args.sarif = "test.sarif"
        mock_parse_args.return_value = mock_args

        # Mock function returns
        mock_changed_files.return_value = ["src/ai_guard/analyzer.py"]
        mock_lint.return_value = (Mock(name="Lint", passed=True), [])
        mock_type.return_value = (Mock(name="Types", passed=True), [])
        mock_security.return_value = (Mock(name="Security", passed=True), [])
        mock_coverage.return_value = Mock(name="Coverage", passed=True)
        mock_pytest.return_value = 0
        mock_summarize.return_value = 0

        # Mock os.path.exists
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=1024):
                with patch('sys.exit') as mock_exit:
                    main()

        # Verify tests were run
        mock_pytest.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('src.ai_guard.analyzer.changed_python_files')
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    @patch('src.ai_guard.analyzer.summarize')
    @patch('src.ai_guard.analyzer.write_sarif')
    @patch('builtins.print')
    def test_main_with_event_file_error(
        self, mock_print, mock_write_sarif, mock_summarize,
        mock_coverage, mock_security, mock_type,
        mock_lint, mock_changed_files, mock_parse_args
    ):
        """Test main function with event file error."""
        # Mock command line arguments
        mock_args = Mock()
        mock_args.min_cov = 80
        mock_args.skip_tests = True
        mock_args.event = "event.json"
        mock_args.sarif = "test.sarif"
        mock_parse_args.return_value = mock_args

        # Mock function returns
        mock_changed_files.return_value = []
        mock_lint.return_value = (Mock(name="Lint", passed=True), [])
        mock_type.return_value = (Mock(name="Types", passed=True), [])
        mock_security.return_value = (Mock(name="Security", passed=True), [])
        mock_coverage.return_value = Mock(name="Coverage", passed=True)
        mock_summarize.return_value = 0

        # Mock sys.exit to prevent actual exit
        with patch('sys.exit') as mock_exit:
            main()

        # Verify the function completed successfully
        mock_exit.assert_called_once_with(0)
