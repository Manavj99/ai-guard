from unittest.mock import patch

from src.ai_guard.tests_runner import run_pytest, run_pytest_with_coverage
from src.ai_guard.security_scanner import run_bandit


def test_run_pytest_invocations():
    with patch("subprocess.call", return_value=0) as call:
        assert run_pytest() == 0
        assert run_pytest(["--maxfail=1"]) == 0
        # ensure subprocess.call was called
        assert call.call_count == 2


def test_run_pytest_with_coverage():
    with patch("subprocess.call", return_value=0) as call:
        assert run_pytest_with_coverage() == 0
        # ensure coverage flags passed
        args, kwargs = call.call_args
        cmd = args[0]
        assert "--cov=src" in cmd and "--cov-report=xml" in cmd


def test_run_bandit_wrapper():
    with patch("subprocess.call", return_value=0) as call:
        assert run_bandit(["-q"]) == 0
        args, kwargs = call.call_args
        assert args[0][0] == "bandit"
