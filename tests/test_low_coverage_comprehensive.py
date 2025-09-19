"""Comprehensive tests for low-coverage files to improve overall coverage."""

import pytest
import subprocess
import os
from unittest.mock import patch, mock_open, MagicMock
from dataclasses import dataclass

from src.ai_guard.utils.subprocess_runner import (
    run_cmd, run_command, _format_command_output, ToolExecutionError
)
from src.ai_guard.security_scanner import (
    run_bandit, run_safety_check, SecurityScanner
)
from src.ai_guard.report import (
    GateResult, summarize, ReportGenerator
)
from src.ai_guard.report_html import HTMLReportGenerator
from src.ai_guard.sarif_report import SarifResult, SarifRun
from src.ai_guard.tests_runner import TestsRunner


class TestSubprocessRunner:
    """Test subprocess_runner module."""

    def test_run_cmd_success(self):
        """Test run_cmd with successful command."""
        returncode, output = run_cmd(["python", "-c", "print('test')"])
        assert returncode == 0
        assert "test" in output

    def test_run_cmd_failure(self):
        """Test run_cmd with failing command."""
        with pytest.raises(ToolExecutionError):
            run_cmd(["python", "-c", "exit(1)"])

    def test_run_cmd_empty_command(self):
        """Test run_cmd with empty command."""
        with pytest.raises(ToolExecutionError, match="Empty or None command"):
            run_cmd([])

    def test_run_cmd_none_command(self):
        """Test run_cmd with None command."""
        with pytest.raises(ToolExecutionError, match="Empty or None command"):
            run_cmd(None)

    def test_run_cmd_timeout(self):
        """Test run_cmd with timeout."""
        with pytest.raises(ToolExecutionError):
            run_cmd(["sleep", "2"], timeout=1)

    def test_run_cmd_with_cwd(self):
        """Test run_cmd with custom working directory."""
        returncode, output = run_cmd(["python", "-c", "import os; print(os.getcwd())"], cwd=".")
        assert returncode == 0

    def test_run_command_none(self):
        """Test run_command with None."""
        returncode, output = run_command(None)
        assert returncode == 1
        assert "No command provided" in output

    def test_run_command_empty(self):
        """Test run_command with empty command."""
        returncode, output = run_command([])
        assert returncode == 1
        assert "Empty command" in output

    def test_run_command_valid(self):
        """Test run_command with valid command."""
        returncode, output = run_command(["python", "-c", "print('test')"])
        assert returncode == 0
        assert "test" in output

    def test_format_command_output_both(self):
        """Test _format_command_output with both stdout and stderr."""
        result = _format_command_output("stdout", "stderr")
        assert result == "stdout\nstderr"

    def test_format_command_output_stdout_only(self):
        """Test _format_command_output with stdout only."""
        result = _format_command_output("stdout", "")
        assert result == "stdout"

    def test_format_command_output_stderr_only(self):
        """Test _format_command_output with stderr only."""
        result = _format_command_output("", "stderr")
        assert result == "stderr"

    def test_format_command_output_neither(self):
        """Test _format_command_output with neither stdout nor stderr."""
        result = _format_command_output("", "")
        assert result == "No output"


class TestSecurityScanner:
    """Test security_scanner module."""

    def test_run_bandit_no_config(self):
        """Test run_bandit without config file."""
        with patch('os.path.exists', return_value=False):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 0
                result = run_bandit()
                mock_call.assert_called_once()
                # Check that default args were used
                args = mock_call.call_args[0][0]
                assert "bandit" in args
                assert "-f" in args
                assert "json" in args
                assert "-ll" in args

    def test_run_bandit_with_config(self):
        """Test run_bandit with config file."""
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 0
                result = run_bandit()
                mock_call.assert_called_once()
                args = mock_call.call_args[0][0]
                assert "-c" in args
                assert ".bandit" in args

    def test_run_bandit_with_extra_args(self):
        """Test run_bandit with extra arguments."""
        with patch('os.path.exists', return_value=False):
            with patch('subprocess.call') as mock_call:
                mock_call.return_value = 0
                result = run_bandit(["-v", "-r", "custom_dir"])
                mock_call.assert_called_once()
                args = mock_call.call_args[0][0]
                assert "-v" in args
                assert "custom_dir" in args

    def test_run_safety_check_success(self):
        """Test run_safety_check success."""
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            result = run_safety_check()
            assert result == 0
            mock_call.assert_called_once_with(["safety", "check"])

    def test_run_safety_check_not_found(self):
        """Test run_safety_check when safety is not installed."""
        with patch('subprocess.call', side_effect=FileNotFoundError()):
            with patch('builtins.print') as mock_print:
                result = run_safety_check()
                assert result == 0
                mock_print.assert_called_once()
                assert "Warning: safety not installed" in mock_print.call_args[0][0]

    def test_run_safety_check_exception(self):
        """Test run_safety_check with other exception."""
        with patch('subprocess.call', side_effect=Exception("Test error")):
            with patch('builtins.print') as mock_print:
                result = run_safety_check()
                assert result == 0
                mock_print.assert_called_once()
                assert "Warning: Error running safety check" in mock_print.call_args[0][0]

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    def test_security_scanner_run_bandit_scan(self):
        """Test SecurityScanner.run_bandit_scan."""
        scanner = SecurityScanner()
        with patch('src.ai_guard.security_scanner.run_bandit') as mock_run_bandit:
            mock_run_bandit.return_value = 0
            result = scanner.run_bandit_scan()
            assert result == 0
            mock_run_bandit.assert_called_once_with(None)

    def test_security_scanner_run_bandit_scan_with_args(self):
        """Test SecurityScanner.run_bandit_scan with extra args."""
        scanner = SecurityScanner()
        with patch('src.ai_guard.security_scanner.run_bandit') as mock_run_bandit:
            mock_run_bandit.return_value = 0
            result = scanner.run_bandit_scan(["-v"])
            assert result == 0
            mock_run_bandit.assert_called_once_with(["-v"])

    def test_security_scanner_run_safety_scan(self):
        """Test SecurityScanner.run_safety_scan."""
        scanner = SecurityScanner()
        with patch('src.ai_guard.security_scanner.run_safety_check') as mock_run_safety:
            mock_run_safety.return_value = 0
            result = scanner.run_safety_scan()
            assert result == 0
            mock_run_safety.assert_called_once()

    def test_security_scanner_run_all_security_checks_both_pass(self):
        """Test SecurityScanner.run_all_security_checks when both pass."""
        scanner = SecurityScanner()
        with patch.object(scanner, 'run_bandit_scan', return_value=0):
            with patch.object(scanner, 'run_safety_scan', return_value=0):
                result = scanner.run_all_security_checks()
                assert result == 0

    def test_security_scanner_run_all_security_checks_bandit_fails(self):
        """Test SecurityScanner.run_all_security_checks when bandit fails."""
        scanner = SecurityScanner()
        with patch.object(scanner, 'run_bandit_scan', return_value=1):
            with patch.object(scanner, 'run_safety_scan', return_value=0):
                result = scanner.run_all_security_checks()
                assert result == 1

    def test_security_scanner_run_all_security_checks_safety_fails(self):
        """Test SecurityScanner.run_all_security_checks when safety fails."""
        scanner = SecurityScanner()
        with patch.object(scanner, 'run_bandit_scan', return_value=0):
            with patch.object(scanner, 'run_safety_scan', return_value=1):
                result = scanner.run_all_security_checks()
                assert result == 1

    def test_security_scanner_run_all_security_checks_both_fail(self):
        """Test SecurityScanner.run_all_security_checks when both fail."""
        scanner = SecurityScanner()
        with patch.object(scanner, 'run_bandit_scan', return_value=1):
            with patch.object(scanner, 'run_safety_scan', return_value=1):
                result = scanner.run_all_security_checks()
                assert result == 1


class TestReport:
    """Test report module."""

    def test_gate_result_creation(self):
        """Test GateResult creation."""
        result = GateResult("test_gate", True, "All good", 0)
        assert result.name == "test_gate"
        assert result.passed is True
        assert result.details == "All good"
        assert result.exit_code == 0

    def test_gate_result_defaults(self):
        """Test GateResult with defaults."""
        result = GateResult("test_gate", False)
        assert result.name == "test_gate"
        assert result.passed is False
        assert result.details == ""
        assert result.exit_code == 0

    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed"),
        ]
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            assert exit_code == 0
            # Check that success message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("All gates passed!" in call for call in print_calls)

    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            assert exit_code == 1
            # Check that failure message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("1 gate(s) failed" in call for call in print_calls)

    def test_summarize_empty_results(self):
        """Test summarize with empty results."""
        results = []
        with patch('builtins.print') as mock_print:
            exit_code = summarize(results)
            assert exit_code == 0

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_report_generator_generate_summary_all_passed(self):
        """Test ReportGenerator.generate_summary with all passed."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", True, "Also passed"),
        ]
        summary = generator.generate_summary(results)
        assert "Total: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary
        assert "Failed Gates:" not in summary

    def test_report_generator_generate_summary_some_failed(self):
        """Test ReportGenerator.generate_summary with some failed."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed"),
            GateResult("gate2", False, "Failed"),
        ]
        summary = generator.generate_summary(results)
        assert "Total: 2" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary
        assert "Failed Gates:" in summary
        assert "gate2: Failed" in summary

    def test_report_generator_generate_detailed_report(self):
        """Test ReportGenerator.generate_detailed_report."""
        generator = ReportGenerator()
        results = [
            GateResult("gate1", True, "Passed", 0),
            GateResult("gate2", False, "Failed", 1),
        ]
        report = generator.generate_detailed_report(results)
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate: gate1" in report
        assert "Gate: gate2" in report
        assert "Status: PASSED" in report
        assert "Status: FAILED" in report
        assert "Exit Code: 0" in report
        assert "Exit Code: 1" in report

    def test_report_generator_generate_detailed_report_empty(self):
        """Test ReportGenerator.generate_detailed_report with empty results."""
        generator = ReportGenerator()
        results = []
        report = generator.generate_detailed_report(results)
        assert "AI-Guard Quality Gates Detailed Report" in report
        assert "Gate:" not in report


class TestHTMLReport:
    """Test HTMLReport module."""

    def test_html_report_init(self):
        """Test HTMLReportGenerator initialization."""
        html_report = HTMLReportGenerator()
        assert html_report is not None


class TestSARIFReport:
    """Test SARIFReport module."""

    def test_sarif_report_init(self):
        """Test SARIF report initialization."""
        sarif_result = SarifResult("test", "error", "test message")
        assert sarif_result.rule_id == "test"


class TestTestsRunner:
    """Test TestsRunner module."""

    def test_tests_runner_init(self):
        """Test TestsRunner initialization."""
        runner = TestsRunner()
        assert runner is not None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_run_cmd_command_with_spaces(self):
        """Test run_cmd with command containing spaces."""
        returncode, output = run_cmd(["python", "-c", "print('hello world')"])
        assert returncode == 0
        assert "hello world" in output

    def test_run_cmd_long_running_command(self):
        """Test run_cmd with long running command."""
        returncode, output = run_cmd(["python", "-c", "import time; time.sleep(0.1)"])
        assert returncode == 0

    def test_format_command_output_unicode(self):
        """Test _format_command_output with unicode characters."""
        result = _format_command_output("测试", "错误")
        assert result == "测试\n错误"

    def test_gate_result_unicode_details(self):
        """Test GateResult with unicode details."""
        result = GateResult("test_gate", True, "测试详情", 0)
        assert result.details == "测试详情"

    def test_summarize_unicode_details(self):
        """Test summarize with unicode details."""
        results = [GateResult("gate1", False, "测试失败")]
        with patch('builtins.print'):
            exit_code = summarize(results)
            assert exit_code == 1
