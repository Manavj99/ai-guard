"""Basic tests for __main__.py."""

from unittest.mock import patch


def test_main_help():
    """Test main function with help argument."""
    with patch("sys.argv", ["ai-guard", "--help"]):
        with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
            from ai_guard.__main__ import main

            try:
                main()
            except SystemExit:
                pass  # Expected for help


def test_main_basic():
    """Test main function with basic arguments."""
    with patch("sys.argv", ["ai-guard", "--skip-tests"]):
        with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
            from ai_guard.__main__ import main

            main()
            mock_analyzer.assert_called_once()


def test_main_with_coverage():
    """Test main function with coverage argument."""
    with patch("sys.argv", ["ai-guard", "--min-cov", "90"]):
        with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
            from ai_guard.__main__ import main

            main()
            mock_analyzer.assert_called_once()


def test_main_with_report_format():
    """Test main function with report format."""
    with patch("sys.argv", ["ai-guard", "--report-format", "json"]):
        with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
            from ai_guard.__main__ import main

            main()
            mock_analyzer.assert_called_once()


def test_main_deprecated_sarif():
    """Test main function with deprecated sarif argument."""
    with patch("sys.argv", ["ai-guard", "--sarif", "test.sarif"]):
        with patch("ai_guard.__main__.run_analyzer") as mock_analyzer:
            from ai_guard.__main__ import main

            main()
            mock_analyzer.assert_called_once()
