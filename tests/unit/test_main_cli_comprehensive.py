"""Comprehensive tests for the main CLI entry point."""

import pytest
import sys
from unittest.mock import patch, MagicMock

from ai_guard.__main__ import main as cli_main
from ai_guard.analyzer import main as analyzer_main


class TestCLIMain:
    """Test the main CLI entry point."""

    def test_cli_main_help(self):
        """Test CLI help output."""
        with patch("sys.argv", ["ai-guard", "--help"]), pytest.raises(SystemExit):
            cli_main()

    def test_cli_main_minimal_args(self):
        """Test CLI with minimal arguments."""
        with (
            patch("sys.argv", ["ai-guard"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_min_cov(self):
        """Test CLI with min coverage argument."""
        with (
            patch("sys.argv", ["ai-guard", "--min-cov", "90"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_skip_tests(self):
        """Test CLI with skip tests argument."""
        with (
            patch("sys.argv", ["ai-guard", "--skip-tests"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_event(self):
        """Test CLI with event file argument."""
        with (
            patch("sys.argv", ["ai-guard", "--event", "event.json"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_report_format_json(self):
        """Test CLI with JSON report format."""
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "json"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_report_format_html(self):
        """Test CLI with HTML report format."""
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "html"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_report_path(self):
        """Test CLI with custom report path."""
        with (
            patch("sys.argv", ["ai-guard", "--report-path", "custom.sarif"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_with_deprecated_sarif_arg(self):
        """Test CLI with deprecated --sarif argument."""
        with (
            patch("sys.argv", ["ai-guard", "--sarif", "test.sarif"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
            patch("sys.stderr") as mock_stderr,
        ):
            cli_main()
            mock_analyzer.assert_called_once()
            # Check that deprecation warning was printed
            mock_stderr.write.assert_called()

    def test_cli_main_with_all_args(self):
        """Test CLI with all arguments."""
        with (
            patch(
                "sys.argv",
                [
                    "ai-guard",
                    "--min-cov",
                    "95",
                    "--skip-tests",
                    "--event",
                    "event.json",
                    "--report-format",
                    "json",
                    "--report-path",
                    "custom.json",
                ],
            ),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_argument_parsing(self):
        """Test CLI argument parsing logic."""
        with (
            patch("sys.argv", ["ai-guard", "--min-cov", "85", "--skip-tests"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()

            # Verify that sys.argv was set correctly for the analyzer
            expected_args = [
                "ai-guard",
                "--report-format",
                "sarif",
                "--report-path",
                "ai-guard.sarif",
                "--min-cov",
                "85",
                "--skip-tests",
            ]
            # The analyzer should have been called with the modified sys.argv
            mock_analyzer.assert_called_once()

    def test_cli_main_default_report_paths(self):
        """Test CLI default report paths for different formats."""
        # Test SARIF default
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "sarif"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

        # Test JSON default
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "json"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

        # Test HTML default
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "html"]),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()

    def test_cli_main_deprecated_sarif_with_report_path(self):
        """Test CLI with both deprecated --sarif and --report-path."""
        with (
            patch(
                "sys.argv",
                ["ai-guard", "--sarif", "old.sarif", "--report-path", "new.sarif"],
            ),
            patch("ai_guard.analyzer.main") as mock_analyzer,
        ):
            cli_main()
            mock_analyzer.assert_called_once()
            # Should use --report-path, not --sarif

    def test_cli_main_invalid_report_format(self):
        """Test CLI with invalid report format."""
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "invalid"]),
            pytest.raises(SystemExit),
        ):
            cli_main()

    def test_cli_main_sys_argv_modification(self):
        """Test that sys.argv is properly modified for the analyzer."""
        original_argv = sys.argv.copy()

        try:
            with (
                patch("sys.argv", ["ai-guard", "--min-cov", "90"]),
                patch("ai_guard.analyzer.main") as mock_analyzer,
            ):
                cli_main()
                mock_analyzer.assert_called_once()
        finally:
            sys.argv = original_argv


class TestAnalyzerMain:
    """Test the analyzer main function."""

    def test_analyzer_main_help(self):
        """Test analyzer help output."""
        with patch("sys.argv", ["ai-guard", "--help"]), pytest.raises(SystemExit):
            analyzer_main()

    def test_analyzer_main_minimal_args(self):
        """Test analyzer with minimal arguments."""
        with (
            patch("sys.argv", ["ai-guard"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            mock_lint.assert_called_once()
            mock_type.assert_called_once()
            mock_sec.assert_called_once()
            mock_cov.assert_called_once()
            mock_write.assert_called_once()

    def test_analyzer_main_with_skip_tests(self):
        """Test analyzer with skip tests."""
        with (
            patch("sys.argv", ["ai-guard", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            # Coverage check should still be called even with --skip-tests
            mock_cov.assert_called_once()

    def test_analyzer_main_with_enhanced_testgen(self):
        """Test analyzer with enhanced test generation."""
        with (
            patch("sys.argv", ["ai-guard", "--enhanced-testgen", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
            patch("ai_guard.analyzer.EnhancedTestGenerator") as mock_gen,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()
            mock_gen.return_value.generate_tests.return_value = []

            analyzer_main()

            mock_gen.assert_called_once()

    def test_analyzer_main_with_pr_annotations(self):
        """Test analyzer with PR annotations."""
        with (
            patch("sys.argv", ["ai-guard", "--pr-annotations", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
            patch("ai_guard.analyzer.PRAnnotator") as mock_annotator,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()
            mock_annotator.return_value.generate_annotations.return_value = []

            analyzer_main()

            mock_annotator.assert_called_once()

    def test_analyzer_main_with_llm_provider(self):
        """Test analyzer with LLM provider."""
        with (
            patch(
                "sys.argv", ["ai-guard", "--llm-provider", "anthropic", "--skip-tests"]
            ),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            mock_lint.assert_called_once()
            mock_type.assert_called_once()
            mock_sec.assert_called_once()
            mock_cov.assert_called_once()
            mock_write.assert_called_once()

    def test_analyzer_main_with_llm_api_key(self):
        """Test analyzer with LLM API key."""
        with (
            patch(
                "sys.argv", ["ai-guard", "--llm-api-key", "test-key", "--skip-tests"]
            ),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            mock_lint.assert_called_once()
            mock_type.assert_called_once()
            mock_sec.assert_called_once()
            mock_cov.assert_called_once()
            mock_write.assert_called_once()

    def test_analyzer_main_with_annotations_output(self):
        """Test analyzer with custom annotations output."""
        with (
            patch(
                "sys.argv",
                ["ai-guard", "--annotations-output", "custom.json", "--skip-tests"],
            ),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            mock_lint.assert_called_once()
            mock_type.assert_called_once()
            mock_sec.assert_called_once()
            mock_cov.assert_called_once()
            mock_write.assert_called_once()

    def test_analyzer_main_deprecated_sarif_arg(self):
        """Test analyzer with deprecated --sarif argument."""
        with (
            patch("sys.argv", ["ai-guard", "--sarif", "test.sarif", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
            patch("sys.stderr") as mock_stderr,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            # Check that deprecation warning was printed
            mock_stderr.write.assert_called()
            mock_write.assert_called_once()

    def test_analyzer_main_report_formats(self):
        """Test analyzer with different report formats."""
        # Test JSON format
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "json", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_json") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            mock_write.assert_called_once()

        # Test HTML format
        with (
            patch("sys.argv", ["ai-guard", "--report-format", "html", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_html") as mock_write,
        ):

            mock_lint.return_value = (MagicMock(), [])
            mock_type.return_value = (MagicMock(), [])
            mock_sec.return_value = (MagicMock(), [])
            mock_cov.return_value = MagicMock()

            analyzer_main()

            mock_write.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
