"""Simple tests for __main__.py to achieve maximum coverage."""

import pytest
from unittest.mock import patch
from ai_guard.__main__ import main


class TestMain:
    """Test main function."""

    def test_main_with_help(self):
        """Test main function with --help argument."""
        with patch("sys.argv", ["ai-guard", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_with_version(self):
        """Test main function with --version argument."""
        with patch("sys.argv", ["ai-guard", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_with_invalid_args(self):
        """Test main function with invalid arguments."""
        with patch("sys.argv", ["ai-guard", "--invalid-arg"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_main_with_no_args(self):
        """Test main function with no arguments."""
        with patch("sys.argv", ["ai-guard"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_paths(self):
        """Test main function with specific paths."""
        with patch("sys.argv", ["ai-guard", "src/", "tests/"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once_with(["src/", "tests/"])

    def test_main_with_config_file(self):
        """Test main function with config file."""
        with patch("sys.argv", ["ai-guard", "--config", "config.toml"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_output_file(self):
        """Test main function with output file."""
        with patch("sys.argv", ["ai-guard", "--output", "report.json"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_format(self):
        """Test main function with format option."""
        with patch("sys.argv", ["ai-guard", "--format", "html"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_verbose(self):
        """Test main function with verbose option."""
        with patch("sys.argv", ["ai-guard", "--verbose"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_quiet(self):
        """Test main function with quiet option."""
        with patch("sys.argv", ["ai-guard", "--quiet"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_multiple_options(self):
        """Test main function with multiple options."""
        with patch(
            "sys.argv",
            [
                "ai-guard",
                "--config",
                "config.toml",
                "--output",
                "report.json",
                "--verbose",
            ],
        ):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_analyzer_returns_error(self):
        """Test main function when analyzer returns error."""
        with patch("sys.argv", ["ai-guard"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 1
                result = main()
                assert result == 1
                mock_run.assert_called_once()

    def test_main_analyzer_raises_exception(self):
        """Test main function when analyzer raises exception."""
        with patch("sys.argv", ["ai-guard"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.side_effect = Exception("Test exception")
                with pytest.raises(Exception, match="Test exception"):
                    main()

    def test_main_with_github_event(self):
        """Test main function with GitHub event file."""
        with patch("sys.argv", ["ai-guard", "--github-event", "event.json"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_github_diff(self):
        """Test main function with GitHub diff file."""
        with patch("sys.argv", ["ai-guard", "--github-diff", "diff.txt"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_github_base(self):
        """Test main function with GitHub base ref."""
        with patch("sys.argv", ["ai-guard", "--github-base", "main"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_github_head(self):
        """Test main function with GitHub head ref."""
        with patch("sys.argv", ["ai-guard", "--github-head", "feature-branch"]):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_all_github_options(self):
        """Test main function with all GitHub options."""
        with patch(
            "sys.argv",
            [
                "ai-guard",
                "--github-event",
                "event.json",
                "--github-diff",
                "diff.txt",
                "--github-base",
                "main",
                "--github-head",
                "feature-branch",
            ],
        ):
            with patch("ai_guard.analyzer.run_analyzer") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
