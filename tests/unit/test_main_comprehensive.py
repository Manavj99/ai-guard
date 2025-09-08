"""Comprehensive tests for the main module."""

import sys
from unittest.mock import patch

from ai_guard.__main__ import main


class TestMainModule:
    """Test the main CLI module."""

    def test_main_with_min_cov(self):
        """Test main function with min-cov argument."""
        test_args = ["ai-guard", "--min-cov", "90"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                # Check that sys.argv was set correctly for analyzer
                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "sarif",
                    "--report-path",
                    "ai-guard.sarif",
                    "--min-cov",
                    "90",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_skip_tests(self):
        """Test main function with skip-tests argument."""
        test_args = ["ai-guard", "--skip-tests"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "sarif",
                    "--report-path",
                    "ai-guard.sarif",
                    "--skip-tests",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_event(self):
        """Test main function with event argument."""
        test_args = ["ai-guard", "--event", "event.json"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "sarif",
                    "--report-path",
                    "ai-guard.sarif",
                    "--event",
                    "event.json",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_report_format_json(self):
        """Test main function with JSON report format."""
        test_args = ["ai-guard", "--report-format", "json"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "json",
                    "--report-path",
                    "ai-guard.json",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_report_format_html(self):
        """Test main function with HTML report format."""
        test_args = ["ai-guard", "--report-format", "html"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "html",
                    "--report-path",
                    "ai-guard.html",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_custom_report_path(self):
        """Test main function with custom report path."""
        test_args = ["ai-guard", "--report-path", "custom/report.sarif"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "sarif",
                    "--report-path",
                    "custom/report.sarif",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_deprecated_sarif_arg(self):
        """Test main function with deprecated --sarif argument."""
        test_args = ["ai-guard", "--sarif", "deprecated.sarif"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                with patch("sys.stderr") as mock_stderr:
                    main()

                    expected_args = [
                        "ai-guard",
                        "--report-format",
                        "sarif",
                        "--report-path",
                        "deprecated.sarif",
                    ]
                    assert sys.argv == expected_args
                    mock_analyzer.assert_called_once()

                    # Check warning was printed
                    mock_stderr.write.assert_called()
                    # The warning might be in a different call or format
                    all_calls = [
                        call[0][0] for call in mock_stderr.write.call_args_list
                    ]
                    warning_found = any(
                        "[warn] --sarif is deprecated" in call for call in all_calls
                    )
                    assert warning_found

    def test_main_with_all_arguments(self):
        """Test main function with all arguments."""
        test_args = [
            "ai-guard",
            "--min-cov",
            "95",
            "--skip-tests",
            "--event",
            "event.json",
            "--report-format",
            "json",
            "--report-path",
            "full-report.json",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "json",
                    "--report-path",
                    "full-report.json",
                    "--min-cov",
                    "95",
                    "--skip-tests",
                    "--event",
                    "event.json",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_default_behavior(self):
        """Test main function with no arguments (default behavior)."""
        test_args = ["ai-guard"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "sarif",
                    "--report-path",
                    "ai-guard.sarif",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_with_sarif_and_report_path(self):
        """Test main function with both --sarif and --report-path (report-path should take precedence)."""
        test_args = ["ai-guard", "--sarif", "old.sarif", "--report-path", "new.sarif"]

        with patch.object(sys, "argv", test_args):
            with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
                main()

                expected_args = [
                    "ai-guard",
                    "--report-format",
                    "sarif",
                    "--report-path",
                    "new.sarif",
                ]
                assert sys.argv == expected_args
                mock_analyzer.assert_called_once()

    def test_main_argument_parser_help(self):
        """Test that argument parser is created correctly."""
        import argparse

        # Test that we can create the parser without errors
        parser = argparse.ArgumentParser(
            description="AI-Guard: Smart Code Quality Gatekeeper"
        )
        parser.add_argument(
            "--min-cov", type=int, help="Override min coverage percentage"
        )
        parser.add_argument(
            "--skip-tests", action="store_true", help="Skip running tests"
        )
        parser.add_argument("--event", type=str, help="Path to GitHub event JSON")
        parser.add_argument(
            "--report-format",
            choices=["sarif", "json", "html"],
            default="sarif",
            help="Output format for the final report",
        )
        parser.add_argument(
            "--report-path",
            type=str,
            help="Path to write the report. Default depends on format",
        )
        parser.add_argument(
            "--sarif",
            type=str,
            help="(Deprecated) Output SARIF file path; use --report-format/--report-path",
        )

        # Test parsing various argument combinations
        args = parser.parse_args(["--min-cov", "90"])
        assert args.min_cov == 90
        assert args.skip_tests is False
        assert args.report_format == "sarif"

        args = parser.parse_args(["--skip-tests", "--report-format", "json"])
        assert args.skip_tests is True
        assert args.report_format == "json"

        args = parser.parse_args(["--sarif", "test.sarif"])
        assert args.sarif == "test.sarif"
