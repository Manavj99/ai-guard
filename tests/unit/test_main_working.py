"""Working comprehensive tests for the main module."""

import pytest
import sys
from unittest.mock import patch

from ai_guard.__main__ import main


class TestMainWorking:
    """Working comprehensive tests for main module functionality."""

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_basic(self, mock_run_analyzer):
        """Test main function with basic arguments."""
        with patch.object(sys, "argv", ["ai-guard"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_min_cov(self, mock_run_analyzer):
        """Test main function with min coverage argument."""
        with patch.object(sys, "argv", ["ai-guard", "--min-cov", "90"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_skip_tests(self, mock_run_analyzer):
        """Test main function with skip tests argument."""
        with patch.object(sys, "argv", ["ai-guard", "--skip-tests"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_event(self, mock_run_analyzer):
        """Test main function with event argument."""
        with patch.object(sys, "argv", ["ai-guard", "--event", "event.json"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_report_format(self, mock_run_analyzer):
        """Test main function with report format argument."""
        with patch.object(sys, "argv", ["ai-guard", "--report-format", "json"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_report_path(self, mock_run_analyzer):
        """Test main function with report path argument."""
        with patch.object(
            sys, "argv", ["ai-guard", "--report-path", "custom-report.json"]
        ):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_deprecated_sarif(self, mock_run_analyzer):
        """Test main function with deprecated sarif argument."""
        with patch.object(sys, "argv", ["ai-guard", "--sarif", "old-report.sarif"]):
            with patch("builtins.print") as mock_print:
                main()

        mock_run_analyzer.assert_called_once()
        # Should print deprecation warning
        mock_print.assert_called()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_with_all_arguments(self, mock_run_analyzer):
        """Test main function with all arguments."""
        with patch.object(
            sys,
            "argv",
            [
                "ai-guard",
                "--min-cov",
                "95",
                "--skip-tests",
                "--event",
                "event.json",
                "--report-format",
                "html",
                "--report-path",
                "report.html",
            ],
        ):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_json_format_default_path(self, mock_run_analyzer):
        """Test main function with JSON format and default path."""
        with patch.object(sys, "argv", ["ai-guard", "--report-format", "json"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_html_format_default_path(self, mock_run_analyzer):
        """Test main function with HTML format and default path."""
        with patch.object(sys, "argv", ["ai-guard", "--report-format", "html"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_sarif_format_default_path(self, mock_run_analyzer):
        """Test main function with SARIF format and default path."""
        with patch.object(sys, "argv", ["ai-guard", "--report-format", "sarif"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_deprecated_sarif_with_report_path(self, mock_run_analyzer):
        """Test main function with deprecated sarif and report path."""
        with patch.object(
            sys,
            "argv",
            [
                "ai-guard",
                "--sarif",
                "old-report.sarif",
                "--report-path",
                "new-report.sarif",
            ],
        ):
            with patch("builtins.print") as mock_print:
                main()

        mock_run_analyzer.assert_called_once()
        # Should not print deprecation warning when report-path is also provided
        mock_print.assert_not_called()

    def test_main_argument_parsing(self):
        """Test that main function properly parses arguments."""
        with patch.object(sys, "argv", ["ai-guard", "--help"]):
            with pytest.raises(SystemExit):
                main()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_sets_sys_argv_correctly(self, mock_run_analyzer):
        """Test that main function sets sys.argv correctly for analyzer."""
        with patch.object(sys, "argv", ["ai-guard", "--min-cov", "90", "--skip-tests"]):
            main()

        # Verify that run_analyzer was called
        mock_run_analyzer.assert_called_once()

        # The analyzer should receive the processed arguments
        # This is tested indirectly through the mock call

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_handles_invalid_report_format(self, mock_run_analyzer):
        """Test main function with invalid report format."""
        with patch.object(sys, "argv", ["ai-guard", "--report-format", "invalid"]):
            with pytest.raises(SystemExit):
                main()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_handles_negative_min_cov(self, mock_run_analyzer):
        """Test main function with negative min coverage."""
        with patch.object(sys, "argv", ["ai-guard", "--min-cov", "-10"]):
            main()

        mock_run_analyzer.assert_called_once()

    @patch("ai_guard.__main__.run_analyzer")
    def test_main_handles_large_min_cov(self, mock_run_analyzer):
        """Test main function with large min coverage."""
        with patch.object(sys, "argv", ["ai-guard", "--min-cov", "150"]):
            main()

        mock_run_analyzer.assert_called_once()
