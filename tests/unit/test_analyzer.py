"""Tests for analyzer module."""

import pytest  # noqa: F401
from unittest.mock import patch, Mock, mock_open  # noqa: F401
import subprocess  # noqa: F401
from ai_guard.analyzer import (
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    _parse_bandit_json,
    _parse_flake8_output,
    _parse_mypy_output,
    _to_findings,
    main,
)
from ai_guard.report import GateResult  # noqa: F401


class TestAnalyzer:
    """Test analyzer functionality."""

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_lint_check(None)

        assert result.name == "Lint (flake8)"
        assert result.passed is True
        assert sarif is None  # No issues found

    @patch("src.ai_guard.analyzer.subprocess.run")
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
        assert sarif is None  # No issues found
        # Verify the command included the paths
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]  # First positional argument
        assert call_args[0] == "flake8"
        assert "src/ai_guard/analyzer.py" in call_args

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_lint_check_failure(self, mock_run):
        """Test lint check failure."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = "src/ai_guard/example.py:10:5: E999 SyntaxError"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_lint_check(None)

        assert result.name == "Lint (flake8)"
        assert result.passed is False
        assert sarif is not None  # Should have a SarifResult object

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_lint_check_file_not_found(self, mock_run):
        """Test lint check when flake8 is not found."""
        mock_run.side_effect = FileNotFoundError("flake8: command not found")

        result, sarif = run_lint_check(None)

        assert result.name == "Lint (flake8)"
        assert result.passed is False
        assert "Tool not found" in result.details
        assert sarif is None

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_type_check(None)

        assert result.name == "Static types (mypy)"
        assert result.passed is True
        assert sarif is None  # No issues found

    @patch("src.ai_guard.analyzer.subprocess.run")
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

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_type_check_failure(self, mock_run):
        """Test type check failure."""
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stdout = (
            "src/ai_guard/example.py:10: error: Name 'undefined_var' is not defined"
        )
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_type_check(None)

        assert result.name == "Static types (mypy)"
        assert result.passed is False
        assert sarif is not None  # Should have a SarifResult object

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_type_check_file_not_found(self, mock_run):
        """Test type check when mypy is not found."""
        mock_run.side_effect = FileNotFoundError("mypy: command not found")

        result, sarif = run_type_check(None)

        assert result.name == "Static types (mypy)"
        assert result.passed is False
        assert "Tool not found" in result.details
        assert sarif is None

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"results": []}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_security_check()

        assert result.name == "Security (bandit)"
        assert result.passed is True
        assert sarif is None  # No issues means no SarifResult

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_security_check_with_high_severity(self, mock_run):
        """Test security check with high severity issues."""
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stdout = """{
            "results": [
                {
                    "filename": "src/ai_guard/example.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "Use of assert detected",
                    "issue_severity": "HIGH"
                }
            ]
        }"""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result, sarif = run_security_check()

        assert result.name == "Security (bandit)"
        assert result.passed is False
        assert sarif is not None  # Should have a SarifResult object
        assert sarif.level == "warning"  # Check the level

    @patch("src.ai_guard.analyzer.subprocess.run")
    def test_run_security_check_file_not_found(self, mock_run):
        """Test security check when bandit is not found."""
        mock_run.side_effect = FileNotFoundError("bandit: command not found")

        result, sarif = run_security_check()

        assert result.name == "Security (bandit)"
        assert result.passed is False
        assert "Tool not found" in result.details
        assert sarif is None

    def test_run_coverage_check_passed(self):
        """Test coverage check that passes."""
        with patch("ai_guard.analyzer.cov_percent", return_value=85):
            result, sarif = run_coverage_check(80)
            assert result.name == "Coverage"
            assert result.passed is True
            assert "85.0% >= 80.0%" in result.details
            assert sarif is None

    def test_run_coverage_check_failed(self):
        """Test coverage check that fails."""
        with patch("ai_guard.analyzer.cov_percent", return_value=75):
            result, sarif = run_coverage_check(80)
            assert result.name == "Coverage"
            assert result.passed is False
            assert "75.0% >= 80.0%" in result.details
            assert sarif is None

    def test_parse_flake8_output(self):
        """Test parsing flake8 output."""
        output = (
            "src/ai_guard/example.py:10:5: E501 line too long (120 > 79 characters)"
        )
        results = _parse_flake8_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "E501"
        assert result.level == "error"
        assert "line too long" in result.message

    def test_parse_flake8_output_no_match(self):
        """Test parsing flake8 output with no matching lines."""
        output = "This is not a flake8 output line"
        results = _parse_flake8_output(output)

        assert len(results) == 0

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        output = "src/ai_guard/example.py:10: error: Name 'undefined_var' is not defined [name-defined]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "name-defined"
        assert result.level == "error"
        assert "Name 'undefined_var' is not defined" in result.message

    def test_parse_mypy_output_with_column(self):
        """Test parsing mypy output with column information."""
        output = "src/ai_guard/example.py:10:5: error: Name 'undefined_var' is not defined [name-defined]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "name-defined"
        assert result.level == "error"

    def test_parse_mypy_output_warning(self):
        """Test parsing mypy warning output."""
        output = (
            "src/ai_guard/example.py:10: warning: Unused import 'os' [unused-import]"
        )
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "unused-import"
        assert result.level == "warning"

    def test_parse_mypy_output_note(self):
        """Test parsing mypy note output."""
        output = "src/ai_guard/example.py:10: note: Use '-> None' if function does not return a value"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "mypy-error"
        assert result.level == "note"

    def test_parse_mypy_output_no_code(self):
        """Test parsing mypy output without error code."""
        output = (
            "src/ai_guard/example.py:10: error: Name 'undefined_var' is not defined"
        )
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "mypy-error"
        assert result.level == "error"

    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON output."""
        output = """{
            "results": [
                {
                    "filename": "src/ai_guard/example.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "Use of assert detected",
                    "issue_severity": "MEDIUM"
                }
            ]
        }"""
        results = _parse_bandit_json(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "B101"
        assert result.level == "warning"
        assert "Use of assert detected" in result.message

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON output."""
        output = "invalid json"
        results = _parse_bandit_json(output)

        assert len(results) == 0

    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON output."""
        output = "{}"
        results = _parse_bandit_json(output)

        assert len(results) == 0

    def test_parse_bandit_json_no_results(self):
        """Test parsing bandit JSON output with no results."""
        output = '{"results": []}'
        results = _parse_bandit_json(output)

        assert len(results) == 0

    def test_parse_bandit_json_missing_fields(self):
        """Test parsing bandit JSON output with missing fields."""
        output = """{
            "results": [
                {
                    "filename": "src/ai_guard/example.py",
                    "line_number": 10
                }
            ]
        }"""
        results = _parse_bandit_json(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "bandit"
        assert result.level == "warning"

    def test_to_findings_with_locations(self):
        """Test converting SARIF results to findings with location info."""
        from ai_guard.sarif_report import SarifResult, make_location

        sarif_results = [
            SarifResult(
                rule_id="rule1",
                level="warning",
                message="Test message",
                locations=[make_location("src/test.py", 10, 5)],
            )
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 1
        finding = findings[0]
        assert finding["rule_id"] == "rule1"
        assert finding["level"] == "warning"
        assert finding["path"] == "src/test.py"
        assert finding["line"] == 10

    def test_to_findings_without_locations(self):
        """Test converting SARIF results to findings without location info."""
        from ai_guard.sarif_report import SarifResult

        sarif_results = [
            SarifResult(
                rule_id="rule1", level="warning", message="Test message", locations=[]
            )
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 1
        finding = findings[0]
        assert finding["rule_id"] == "rule1"
        assert finding["level"] == "warning"
        assert finding["path"] == "unknown"
        assert finding["line"] is None

    @patch("ai_guard.analyzer.cov_percent")
    def test_cov_percent_success(self, mock_cov):
        """Test successful coverage percentage parsing."""
        mock_cov.return_value = 85
        from ai_guard.analyzer import cov_percent

        result = cov_percent()
        assert result == 85

    @patch("os.path.exists")
    def test_cov_percent_fallback(self, mock_exists):
        """Test coverage percentage fallback when parsing fails."""
        from ai_guard.analyzer import cov_percent

        # Mock that no coverage files exist
        mock_exists.return_value = False
        result = cov_percent()
        assert result == 0

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_basic_flow(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test basic main function flow."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = []
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Test with basic arguments
        with patch("sys.argv", ["ai-guard", "--min-cov", "80"]):
            with pytest.raises(SystemExit):
                main()

        # Verify all the expected calls were made
        mock_lint_check.assert_called_once()
        mock_type_check.assert_called_once()
        mock_sec_check.assert_called_once()
        mock_cov_check.assert_called_once_with(80)
        mock_run_tests.assert_called_once()
        mock_summarize.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_with_enhanced_testgen(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with enhanced test generation enabled."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Mock the enhanced test generation
        with patch("ai_guard.analyzer.EnhancedTestGenerator") as mock_testgen_class:
            mock_testgen = Mock()
            mock_testgen_class.return_value = mock_testgen
            mock_testgen.generate_tests.return_value = "def test_example(): pass"

            # Test with enhanced test generation enabled
            with patch("sys.argv", ["ai-guard", "--enhanced-testgen"]):
                with pytest.raises(SystemExit):
                    main()

            # Verify enhanced test generation was called
            mock_testgen_class.assert_called_once()
            mock_testgen.generate_tests.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_with_pr_annotations(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with PR annotations enabled."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Mock the PR annotator
        with patch("ai_guard.analyzer.PRAnnotator") as mock_annotator_class:
            mock_annotator = Mock()
            mock_annotator_class.return_value = mock_annotator
            mock_annotator.generate_review_summary.return_value = Mock(
                overall_status="approved", quality_score=0.95, annotations=[]
            )

            # Test with PR annotations enabled
            with patch("sys.argv", ["ai-guard", "--pr-annotations"]):
                with pytest.raises(SystemExit):
                    main()

            # Verify PR annotations were generated
            mock_annotator_class.assert_called_once()
            mock_annotator.save_annotations.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_json")
    def test_main_json_format(
        self,
        mock_write_json,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with JSON report format."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = []
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Test with JSON format
        with patch("sys.argv", ["ai-guard", "--report-format", "json"]):
            with pytest.raises(SystemExit):
                main()

        # Verify JSON report was written
        mock_write_json.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_html")
    def test_main_html_format(
        self,
        mock_write_html,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with HTML report format."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = []
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Test with HTML format
        with patch("sys.argv", ["ai-guard", "--report-format", "html"]):
            with pytest.raises(SystemExit):
                main()

        # Verify HTML report was written
        mock_write_html.assert_called_once()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_unknown_format(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with unknown report format."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = []
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Test with unknown format
        with patch("sys.argv", ["ai-guard", "--report-format", "unknown"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_skip_tests(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with tests skipped."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = []
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_summarize.return_value = 0

        # Test with tests skipped
        with patch("sys.argv", ["ai-guard", "--skip-tests"]):
            with pytest.raises(SystemExit):
                main()

        # Verify tests were not run
        mock_run_tests.assert_not_called()

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_with_event_file(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with GitHub event file."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = ["src/test.py"]
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Mock file operations
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", return_value=1024):
                # Test with event file
                with patch("sys.argv", ["ai-guard", "--event", "event.json"]):
                    with pytest.raises(SystemExit):
                        main()

                # Verify changed files were processed
                mock_changed_files.assert_called_once_with("event.json")

    @patch("ai_guard.analyzer.load_config")
    @patch("ai_guard.analyzer.changed_python_files")
    @patch("ai_guard.analyzer.run_lint_check")
    @patch("ai_guard.analyzer.run_type_check")
    @patch("ai_guard.analyzer.run_security_check")
    @patch("ai_guard.analyzer.run_coverage_check")
    @patch("ai_guard.analyzer.run_pytest_with_coverage")
    @patch("ai_guard.analyzer.summarize")
    @patch("ai_guard.analyzer.write_sarif")
    def test_main_deprecated_sarif_arg(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_run_tests,
        mock_cov_check,
        mock_sec_check,
        mock_type_check,
        mock_lint_check,
        mock_changed_files,
        mock_load_config,
    ):
        """Test main function with deprecated --sarif argument."""
        # Mock all the dependencies
        mock_load_config.return_value = Mock(min_coverage=80)
        mock_changed_files.return_value = []
        mock_lint_check.return_value = (Mock(name="Lint", passed=True), [])
        mock_type_check.return_value = (Mock(name="Types", passed=True), [])
        mock_sec_check.return_value = (Mock(name="Security", passed=True), [])
        mock_cov_check.return_value = (Mock(name="Coverage", passed=True), None)
        mock_run_tests.return_value = 0
        mock_summarize.return_value = 0

        # Test with deprecated --sarif argument
        with patch("sys.argv", ["ai-guard", "--sarif", "output.sarif"]):
            with patch("sys.stderr") as mock_stderr:
                with pytest.raises(SystemExit):
                    main()

                # Verify deprecation warning was printed
                mock_stderr.write.assert_called()
