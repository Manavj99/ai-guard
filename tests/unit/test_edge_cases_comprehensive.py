"""Comprehensive edge case tests for AI-Guard."""

import pytest
import os
import json
import subprocess
from unittest.mock import patch, mock_open, MagicMock

from ai_guard.config import load_config, get_default_config, validate_config
from ai_guard.report import GateResult, summarize
from ai_guard.diff_parser import (
    changed_python_files,
    parse_diff_output,
    get_file_extensions,
)
from ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
    main,
)
from ai_guard.sarif_report import SarifResult, write_sarif, make_location
from ai_guard.report_json import write_json
from ai_guard.report_html import write_html
from ai_guard.security_scanner import run_bandit, run_safety_check
from ai_guard.tests_runner import run_pytest_with_coverage
from ai_guard.pr_annotations import (
    CodeIssue,
    AnnotationLevel,
    format_annotation_message,
)
from ai_guard.generators.enhanced_testgen import (
    EnhancedTestGenerator,
    TestGenerationConfig,
)
from ai_guard.generators.config_loader import (
    create_default_config,
    _get_env_api_key,
)
from ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_typescript_check,
    run_jest_tests,
    run_prettier_check,
)


class TestConfigEdgeCases:
    """Test configuration edge cases."""

    def test_load_config_invalid_toml(self):
        """Test loading config with invalid TOML."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid toml content")),
            patch("tomli.load", side_effect=Exception("Invalid TOML")),
        ):
            config = load_config()
            # Should fall back to default
            assert config.min_coverage == 80

    def test_validate_config_edge_values(self):
        """Test config validation with edge values."""
        config = get_default_config()

        # Test boundary values
        config["min_coverage"] = 0
        assert validate_config(config) is True

        config["min_coverage"] = 100
        assert validate_config(config) is True

        config["min_coverage"] = 101
        assert validate_config(config) is False

    def test_validate_config_missing_keys(self):
        """Test config validation with missing keys."""
        config = {}
        assert validate_config(config) is False


class TestReportEdgeCases:
    """Test reporting edge cases."""

    def test_summarize_empty_results(self):
        """Test summarize with empty results."""
        summary = summarize([])
        assert "0/0 gates passed" in summary

    def test_summarize_mixed_results(self):
        """Test summarize with mixed results."""
        results = [
            GateResult("Gate1", True, "Passed"),
            GateResult("Gate2", False, "Failed"),
            GateResult("Gate3", True, "Passed"),
            GateResult("Gate4", False, "Failed"),
        ]
        summary = summarize(results)
        assert "2/4 gates passed" in summary


class TestDiffParserEdgeCases:
    """Test diff parser edge cases."""

    def test_get_file_extensions_empty(self):
        """Test file extension extraction with empty list."""
        extensions = get_file_extensions([])
        assert extensions == set()

    def test_get_file_extensions_no_extension(self):
        """Test file extension extraction with files without extensions."""
        files = ["README", "Makefile", "Dockerfile"]
        extensions = get_file_extensions(files)
        assert extensions == set()

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        files = parse_diff_output("")
        assert files == []

    def test_parse_diff_output_malformed(self):
        """Test parsing malformed diff output."""
        malformed_diff = "not a valid diff"
        files = parse_diff_output(malformed_diff)
        assert files == []

    def test_changed_python_files_git_error(self):
        """Test changed_python_files with git error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "git error"
            files = changed_python_files(None)
            assert files == []

    def test_changed_python_files_invalid_event(self):
        """Test changed_python_files with invalid event file."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid json")),
        ):
            files = changed_python_files("invalid.json")
            assert files == []


class TestAnalyzerEdgeCases:
    """Test analyzer edge cases."""

    def test_cov_percent_parse_error(self):
        """Test coverage percentage with parse error."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid xml")),
            patch("defusedxml.ElementTree.parse", side_effect=Exception("Parse error")),
        ):
            percent = cov_percent()
            assert percent == 0

    def test_cov_percent_missing_line_rate(self):
        """Test coverage percentage with missing line-rate attribute."""
        xml_content = '<?xml version="1.0"?><coverage></coverage>'

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=xml_content)),
            patch("defusedxml.ElementTree.parse") as mock_parse,
        ):
            mock_root = MagicMock()
            mock_root.get.return_value = None
            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree

            percent = cov_percent()
            assert percent == 0

    def test_parse_flake8_output_multiple_lines(self):
        """Test parsing flake8 output with multiple lines."""
        flake8_output = """src/test.py:1:1: E111 indentation is not a multiple of four
src/test.py:2:5: E501 line too long (120 > 100 characters)
src/test2.py:10:1: W293 blank line contains whitespace"""
        results = _parse_flake8_output(flake8_output)
        assert len(results) == 3
        assert results[0].rule_id == "flake8:E111"
        assert results[1].rule_id == "flake8:E501"
        assert results[2].rule_id == "flake8:W293"

    def test_parse_mypy_output_multiple_lines(self):
        """Test parsing mypy output with multiple lines."""
        mypy_output = """src/test.py:1: error: Incompatible types in assignment
src/test.py:5: note: Revealed type is 'str'
src/test2.py:10: warning: Unused 'type: ignore' comment"""
        results = _parse_mypy_output(mypy_output)
        assert len(results) == 3
        assert results[0].rule_id == "mypy:error"
        assert results[1].rule_id == "mypy:note"
        assert results[2].rule_id == "mypy:warning"

    def test_run_lint_check_subprocess_error(self):
        """Test lint check with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "flake8")
        ):
            result, sarif = run_lint_check()
            assert result.passed is False
            assert "Error running flake8" in result.details

    def test_run_type_check_subprocess_error(self):
        """Test type check with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "mypy")
        ):
            result, sarif = run_type_check()
            assert result.passed is False
            assert "Error running mypy" in result.details

    def test_run_security_check_subprocess_error(self):
        """Test security check with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "bandit")
        ):
            result, sarif = run_security_check()
            assert result.passed is False
            assert "Error running bandit" in result.details

    def test_run_coverage_check_boundary_values(self):
        """Test coverage check with boundary values."""
        # Test exact threshold
        with patch("ai_guard.analyzer.cov_percent", return_value=80):
            result = run_coverage_check(80)
            assert result.passed is True

        # Test just below threshold
        with patch("ai_guard.analyzer.cov_percent", return_value=79):
            result = run_coverage_check(80)
            assert result.passed is False

        # Test 100% coverage
        with patch("ai_guard.analyzer.cov_percent", return_value=100):
            result = run_coverage_check(80)
            assert result.passed is True


class TestSarifReportEdgeCases:
    """Test SARIF report edge cases."""

    def test_write_sarif_io_error(self):
        """Test SARIF writing with IO error."""
        results = [
            SarifResult(
                rule_id="test:rule",
                message="Test message",
                level="error",
                locations=[make_location("test.py", 1, 1)],
            )
        ]

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_sarif(results, "test.sarif")

    def test_make_location_edge_values(self):
        """Test location creation with edge values."""
        # Test with zero values
        location = make_location("test.py", 0, 0)
        assert location.physical_location.region.start_line == 0
        assert location.physical_location.region.start_column == 0

        # Test with large values
        location = make_location("test.py", 999999, 999999)
        assert location.physical_location.region.start_line == 999999
        assert location.physical_location.region.start_column == 999999


class TestReportFormatsEdgeCases:
    """Test report format edge cases."""

    def test_write_json_io_error(self):
        """Test JSON writing with IO error."""
        results = [GateResult("Test", True, "Passed")]

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_json(results, "test.json")

    def test_write_html_io_error(self):
        """Test HTML writing with IO error."""
        results = [GateResult("Test", True, "Passed")]

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_html(results, "test.html")


class TestSecurityScannerEdgeCases:
    """Test security scanner edge cases."""

    def test_run_bandit_subprocess_error(self):
        """Test bandit run with subprocess error."""
        with patch(
            "subprocess.call", side_effect=subprocess.CalledProcessError(1, "bandit")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_bandit()

    def test_run_safety_check_subprocess_error(self):
        """Test safety check with subprocess error."""
        with patch(
            "subprocess.call", side_effect=subprocess.CalledProcessError(1, "safety")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_safety_check()


class TestTestsRunnerEdgeCases:
    """Test test runner edge cases."""

    def test_run_pytest_with_coverage_subprocess_error(self):
        """Test pytest run with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "pytest")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_pytest_with_coverage()


class TestPRAnnotationsEdgeCases:
    """Test PR annotations edge cases."""

    def test_code_issue_edge_values(self):
        """Test CodeIssue with edge values."""
        issue = CodeIssue(
            file_path="",
            line_number=0,
            column_number=0,
            rule_id="",
            message="",
            level=AnnotationLevel.WARNING,
        )
        assert issue.file_path == ""
        assert issue.line_number == 0
        assert issue.column_number == 0
        assert issue.rule_id == ""
        assert issue.message == ""
        assert issue.level == AnnotationLevel.WARNING

    def test_format_annotation_message_empty(self):
        """Test annotation message formatting with empty values."""
        issue = CodeIssue(
            file_path="",
            line_number=0,
            column_number=0,
            rule_id="",
            message="",
            level=AnnotationLevel.WARNING,
        )
        message = format_annotation_message(issue)
        assert message is not None
        assert isinstance(message, str)


class TestEnhancedTestGenEdgeCases:
    """Test enhanced test generation edge cases."""

    def test_test_generation_config_edge_values(self):
        """Test TestGenerationConfig with edge values."""
        config = TestGenerationConfig()
        config.max_tests_per_file = 0
        config.temperature = 0.0
        assert config.max_tests_per_file == 0
        assert config.temperature == 0.0

    def test_enhanced_test_generator_with_invalid_config(self):
        """Test EnhancedTestGenerator with invalid config."""
        generator = EnhancedTestGenerator()
        # Test with invalid file path
        result = generator.generate_tests_for_file("nonexistent.py")
        assert result is None


class TestConfigLoaderEdgeCases:
    """Test config loader edge cases."""

    def test_get_env_api_key_missing(self):
        """Test environment API key retrieval when missing."""
        with patch.dict(os.environ, {}, clear=True):
            key = _get_env_api_key()
            assert key is None

    def test_create_default_config_io_error(self):
        """Test default config creation with IO error."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                create_default_config("test.toml")


class TestJSTSSupportEdgeCases:
    """Test JavaScript/TypeScript support edge cases."""

    def test_check_node_installed_not_found(self):
        """Test Node.js installation check when not found."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "node")
        ):
            result = check_node_installed()
            assert result is False

    def test_check_npm_installed_not_found(self):
        """Test npm installation check when not found."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "npm")
        ):
            result = check_npm_installed()
            assert result is False

    def test_run_eslint_subprocess_error(self):
        """Test ESLint execution with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "eslint")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_eslint(["test.js"])

    def test_run_typescript_check_subprocess_error(self):
        """Test TypeScript check execution with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "tsc")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_typescript_check(["test.ts"])

    def test_run_jest_tests_subprocess_error(self):
        """Test Jest test execution with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "jest")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_jest_tests()

    def test_run_prettier_check_subprocess_error(self):
        """Test Prettier check execution with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "prettier")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_prettier_check(["test.js"])


class TestMainIntegrationEdgeCases:
    """Test main integration edge cases."""

    def test_main_with_invalid_args(self):
        """Test main function with invalid arguments."""
        with (
            patch("sys.argv", ["ai-guard", "--invalid-arg"]),
            pytest.raises(SystemExit),
        ):
            main()

    def test_main_with_deprecated_sarif_arg(self):
        """Test main function with deprecated --sarif argument."""
        with (
            patch("sys.argv", ["ai-guard", "--sarif", "test.sarif", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")

            main()

            mock_write.assert_called_once()

    def test_main_with_event_file_processing(self):
        """Test main function with event file processing."""
        event_data = {
            "pull_request": {"head": {"sha": "abc123"}, "base": {"sha": "def456"}}
        }

        with (
            patch("sys.argv", ["ai-guard", "--event", "event.json", "--skip-tests"]),
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(event_data))),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
        ):

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")

            main()

            mock_lint.assert_called_once()
            mock_type.assert_called_once()
            mock_sec.assert_called_once()
            mock_write.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
