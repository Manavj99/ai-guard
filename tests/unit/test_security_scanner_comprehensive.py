"""Comprehensive tests for security scanner module."""

from unittest.mock import patch

from ai_guard.security_scanner import run_bandit, run_safety_check


class TestSecurityScannerComprehensive:
    """Comprehensive tests for security scanner functionality."""

    def test_run_bandit_success(self):
        """Test successful bandit run."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 0

            result = run_bandit()

            assert result == 0
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "bandit" in call_args
            assert "-r" in call_args
            assert "src" in call_args

    def test_run_bandit_with_extra_args(self):
        """Test bandit run with extra arguments."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 1

            result = run_bandit(["-f", "json"])

            assert result == 1
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "-f" in call_args
            assert "json" in call_args

    def test_run_bandit_with_config_file(self):
        """Test bandit run with config file."""
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.call") as mock_call:
                mock_call.return_value = 0

                result = run_bandit()

                assert result == 0
                call_args = mock_call.call_args[0][0]
                assert "-c" in call_args
                assert ".bandit" in call_args

    def test_run_bandit_without_config_file(self):
        """Test bandit run without config file."""
        with patch("os.path.exists", return_value=False):
            with patch("subprocess.call") as mock_call:
                mock_call.return_value = 0

                result = run_bandit()

                assert result == 0
                call_args = mock_call.call_args[0][0]
                assert "-f" in call_args
                assert "json" in call_args
                assert "-ll" in call_args

    def test_run_safety_check_success(self):
        """Test successful safety check."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 0

            result = run_safety_check()

            assert result == 0
            mock_call.assert_called_once_with(["safety", "check"])

    def test_run_safety_check_not_found(self):
        """Test safety check when safety is not installed."""
        with patch("subprocess.call", side_effect=FileNotFoundError):
            with patch("builtins.print") as mock_print:
                result = run_safety_check()

                assert result == 0
                mock_print.assert_called_once()
                warning_call = mock_print.call_args[0][0]
                assert "Warning: safety not installed" in warning_call

    def test_run_safety_check_with_vulnerabilities(self):
        """Test safety check with vulnerabilities found."""
        with patch("subprocess.call") as mock_call:
            mock_call.return_value = 1

            result = run_safety_check()

            assert result == 1
            mock_call.assert_called_once_with(["safety", "check"])
