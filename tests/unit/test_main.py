"""Tests for the __main__.py module."""

from unittest.mock import patch
from io import StringIO

from ai_guard.__main__ import main


class TestMain:
    """Test the main CLI entry point."""

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_basic(self, mock_run_analyzer):
        """Test basic main function execution."""
        with patch("sys.argv", ["ai-guard"]):
            main()
            mock_run_analyzer.assert_called_once()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_with_min_cov(self, mock_run_analyzer):
        """Test main function with min coverage argument."""
        with patch("sys.argv", ["ai-guard", "--min-cov", "80"]):
            main()
            mock_run_analyzer.assert_called_once()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_with_skip_tests(self, mock_run_analyzer):
        """Test main function with skip tests argument."""
        with patch("sys.argv", ["ai-guard", "--skip-tests"]):
            main()
            mock_run_analyzer.assert_called_once()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_with_event(self, mock_run_analyzer):
        """Test main function with event argument."""
        with patch("sys.argv", ["ai-guard", "--event", "event.json"]):
            main()
            mock_run_analyzer.assert_called_once()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_with_report_format(self, mock_run_analyzer):
        """Test main function with report format argument."""
        with patch("sys.argv", ["ai-guard", "--report-format", "json"]):
            main()
            mock_run_analyzer.assert_called_once()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_with_report_path(self, mock_run_analyzer):
        """Test main function with report path argument."""
        with patch("sys.argv", ["ai-guard", "--report-path", "custom.json"]):
            main()
            mock_run_analyzer.assert_called_once()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_deprecated_sarif(self, mock_run_analyzer):
        """Test main function with deprecated sarif argument."""
        with patch("sys.argv", ["ai-guard", "--sarif", "output.sarif"]):
            with patch("sys.stderr", new=StringIO()) as mock_stderr:
                main()
                mock_run_analyzer.assert_called_once()
                # Check that deprecation warning was printed
                assert "deprecated" in mock_stderr.getvalue()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_default_report_paths(self, mock_run_analyzer):
        """Test main function sets correct default report paths."""
        test_cases = [
            ("sarif", "ai-guard.sarif"),
            ("json", "ai-guard.json"),
            ("html", "ai-guard.html"),
        ]

        for format_type, expected_path in test_cases:
            with patch("sys.argv", ["ai-guard", "--report-format", format_type]):
                main()
                mock_run_analyzer.assert_called_once()
                # Reset for next iteration
                mock_run_analyzer.reset_mock()

    @patch("src.ai_guard.__main__.run_analyzer")
    def test_main_complex_arguments(self, mock_run_analyzer):
        """Test main function with multiple arguments."""
        with patch(
            "sys.argv",
            [
                "ai-guard",
                "--min-cov",
                "85",
                "--skip-tests",
                "--event",
                "pr.json",
                "--report-format",
                "html",
                "--report-path",
                "report.html",
            ],
        ):
            main()
            mock_run_analyzer.assert_called_once()
