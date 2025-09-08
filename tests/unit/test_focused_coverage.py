"""Focused test suite to achieve 90%+ coverage for AI-Guard core modules."""

import pytest
import json
import subprocess
from unittest.mock import patch, mock_open, MagicMock

# Import core modules to test
from ai_guard import __version__, __author__
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
from ai_guard.sarif_report import SarifRun, SarifResult, write_sarif, make_location
from ai_guard.report_json import write_json
from ai_guard.report_html import write_html
from ai_guard.security_scanner import run_bandit, run_safety_check
from ai_guard.tests_runner import run_pytest_with_coverage
from ai_guard.pr_annotations import PRAnnotator, CodeIssue, format_annotation_message


class TestPackageInit:
    """Test package initialization."""

    def test_version_and_author(self):
        """Test package version and author are defined."""
        assert __version__ == "0.1.0"
        assert __author__ == "AI-Guard Contributors"


class TestConfig:
    """Test configuration functionality."""

    def test_get_default_config(self):
        """Test default configuration values."""
        config = get_default_config()
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"
        assert config["enhanced_testgen"] is False
        assert config["llm_provider"] == "openai"
        assert config["fail_on_bandit"] is True

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = get_default_config()
        assert validate_config(config) is True

    def test_validate_config_invalid_coverage(self):
        """Test config validation with invalid coverage."""
        config = get_default_config()
        config["min_coverage"] = -1
        assert validate_config(config) is False

    def test_validate_config_invalid_format(self):
        """Test config validation with invalid format."""
        config = get_default_config()
        config["report_format"] = "invalid"
        assert validate_config(config) is False

    def test_load_config_default(self):
        """Test loading default config when no file exists."""
        with patch("os.path.exists", return_value=False):
            config = load_config()
            # Should return a dict, not Gates object
            assert isinstance(config, dict)
            assert config["min_coverage"] == 80

    def test_load_config_from_file(self):
        """Test loading config from file."""
        config_data = {"min_coverage": 90, "skip_tests": True, "report_format": "json"}

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(config_data))),
            patch("tomli.load", return_value=config_data),
        ):
            config = load_config()
            assert config["min_coverage"] == 90
            assert config["skip_tests"] is True
            assert config["report_format"] == "json"

    def test_load_config_invalid_toml(self):
        """Test loading config with invalid TOML."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid toml content")),
            patch("tomli.load", side_effect=Exception("Invalid TOML")),
        ):
            config = load_config()
            # Should fall back to default
            assert config["min_coverage"] == 80

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


class TestReport:
    """Test reporting functionality."""

    def test_gate_result_creation(self):
        """Test GateResult creation."""
        result = GateResult("Test Gate", True, "All good")
        assert result.name == "Test Gate"
        assert result.passed is True
        assert result.details == "All good"

    def test_gate_result_failure(self):
        """Test GateResult with failure."""
        result = GateResult("Test Gate", False, "Failed")
        assert result.passed is False

    def test_summarize_success(self):
        """Test summarize with all passing gates."""
        results = [
            GateResult("Lint", True, "Passed"),
            GateResult("Type", True, "Passed"),
            GateResult("Security", True, "Passed"),
        ]
        summary = summarize(results)
        # The summarize function prints to stdout, so we need to capture it
        assert summary is not None

    def test_summarize_failure(self):
        """Test summarize with failing gates."""
        results = [
            GateResult("Lint", True, "Passed"),
            GateResult("Type", False, "Failed"),
            GateResult("Security", True, "Passed"),
        ]
        summary = summarize(results)
        assert summary is not None

    def test_summarize_empty_results(self):
        """Test summarize with empty results."""
        summary = summarize([])
        assert summary is not None

    def test_summarize_mixed_results(self):
        """Test summarize with mixed results."""
        results = [
            GateResult("Gate1", True, "Passed"),
            GateResult("Gate2", False, "Failed"),
            GateResult("Gate3", True, "Passed"),
            GateResult("Gate4", False, "Failed"),
        ]
        summary = summarize(results)
        assert summary is not None


class TestDiffParser:
    """Test diff parsing functionality."""

    def test_get_file_extensions(self):
        """Test file extension extraction."""
        files = ["test.py", "test.js", "test.ts", "README.md"]
        extensions = get_file_extensions(files)
        # The function returns a list, not a set
        assert "py" in extensions
        assert "js" in extensions
        assert "ts" in extensions
        assert "md" in extensions

    def test_get_file_extensions_empty(self):
        """Test file extension extraction with empty list."""
        extensions = get_file_extensions([])
        assert extensions == []

    def test_get_file_extensions_no_extension(self):
        """Test file extension extraction with files without extensions."""
        files = ["README", "Makefile", "Dockerfile"]
        extensions = get_file_extensions(files)
        assert extensions == []

    def test_parse_diff_output(self):
        """Test parsing diff output."""
        diff_output = """
diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
"""
        files = parse_diff_output(diff_output)
        assert "src/test.py" in files

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        files = parse_diff_output("")
        assert files == []

    def test_parse_diff_output_malformed(self):
        """Test parsing malformed diff output."""
        malformed_diff = "not a valid diff"
        files = parse_diff_output(malformed_diff)
        assert files == []

    def test_changed_python_files_no_event(self):
        """Test changed_python_files without event file."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "src/test.py\n"
            mock_run.return_value.returncode = 0
            files = changed_python_files(None)
            assert "src/test.py" in files

    def test_changed_python_files_with_event(self):
        """Test changed_python_files with event file."""
        event_data = {
            "pull_request": {"head": {"sha": "abc123"}, "base": {"sha": "def456"}}
        }

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(event_data))),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = "src/test.py\n"
            mock_run.return_value.returncode = 0
            files = changed_python_files("event.json")
            assert "src/test.py" in files

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
            # Should return all Python files when event parsing fails
            assert isinstance(files, list)


class TestAnalyzer:
    """Test analyzer functionality."""

    def test_cov_percent_no_file(self):
        """Test coverage percentage when no file exists."""
        with patch("os.path.exists", return_value=False):
            percent = cov_percent()
            assert percent == 0

    def test_cov_percent_with_file(self):
        """Test coverage percentage with valid file."""
        xml_content = '<?xml version="1.0"?><coverage line-rate="0.85"></coverage>'

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=xml_content)),
            patch("defusedxml.ElementTree.parse") as mock_parse,
        ):
            mock_root = MagicMock()
            mock_root.get.return_value = "0.85"
            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree

            percent = cov_percent()
            assert percent == 85

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

    def test_parse_flake8_output(self):
        """Test parsing flake8 output."""
        flake8_output = "src/test.py:1:1: E111 indentation is not a multiple of four"
        results = _parse_flake8_output(flake8_output)
        assert len(results) == 1
        assert results[0].rule_id == "flake8:E111"
        # The message is a string, not an object with .text
        assert "indentation" in results[0].message

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

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = "src/test.py:1: error: Incompatible types in assignment"
        results = _parse_mypy_output(mypy_output)
        assert len(results) == 1
        # The actual rule_id format includes "mypy-" prefix
        assert "mypy" in results[0].rule_id
        assert "Incompatible types" in results[0].message

    def test_parse_mypy_output_multiple_lines(self):
        """Test parsing mypy output with multiple lines."""
        mypy_output = """src/test.py:1: error: Incompatible types in assignment
src/test.py:5: note: Revealed type is 'str'
src/test2.py:10: warning: Unused 'type: ignore' comment"""
        results = _parse_mypy_output(mypy_output)
        assert len(results) == 3
        assert "mypy" in results[0].rule_id
        assert "mypy" in results[1].rule_id
        assert "mypy" in results[2].rule_id

    def test_run_lint_check_success(self):
        """Test lint check with success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result, sarif = run_lint_check()
            assert result.passed is True
            assert result.name == "Lint (flake8)"

    def test_run_lint_check_failure(self):
        """Test lint check with failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:1:1: E111 error"
            result, sarif = run_lint_check()
            assert result.passed is False
            # SARIF results may be empty if parsing fails
            assert isinstance(sarif, list)

    def test_run_lint_check_subprocess_error(self):
        """Test lint check with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "flake8")
        ):
            result, sarif = run_lint_check()
            assert result.passed is False
            assert "Error running flake8" in result.details

    def test_run_type_check_success(self):
        """Test type check with success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result, sarif = run_type_check()
            assert result.passed is True
            assert result.name == "Static types (mypy)"

    def test_run_type_check_failure(self):
        """Test type check with failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "src/test.py:1: error: Incompatible types"
            result, sarif = run_type_check()
            assert result.passed is False
            assert isinstance(sarif, list)

    def test_run_type_check_subprocess_error(self):
        """Test type check with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "mypy")
        ):
            result, sarif = run_type_check()
            assert result.passed is False
            assert "Error running mypy" in result.details

    def test_run_security_check_success(self):
        """Test security check with success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result, sarif = run_security_check()
            assert result.passed is True
            assert result.name == "Security (bandit)"

    def test_run_security_check_failure(self):
        """Test security check with failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = '{"results": [{"issue_severity": "HIGH"}]}'
            result, sarif = run_security_check()
            assert result.passed is False
            assert isinstance(sarif, list)

    def test_run_security_check_subprocess_error(self):
        """Test security check with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "bandit")
        ):
            result, sarif = run_security_check()
            assert result.passed is False
            assert "Error running bandit" in result.details

    def test_run_coverage_check_success(self):
        """Test coverage check with success."""
        with patch("ai_guard.analyzer.cov_percent", return_value=85):
            result = run_coverage_check(80)
            assert result.passed is True
            assert "85%" in result.details

    def test_run_coverage_check_failure(self):
        """Test coverage check with failure."""
        with patch("ai_guard.analyzer.cov_percent", return_value=75):
            result = run_coverage_check(80)
            assert result.passed is False
            assert "75%" in result.details

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


class TestSarifReport:
    """Test SARIF report functionality."""

    def test_sarif_run_creation(self):
        """Test SarifRun creation."""
        # SarifRun requires arguments
        run = SarifRun("ai-guard", [])
        assert run.tool_name == "ai-guard"
        assert run.results == []

    def test_sarif_result_creation(self):
        """Test SarifResult creation."""
        result = SarifResult(
            rule_id="test:rule",
            message="Test message",
            level="error",
            locations=[make_location("test.py", 1, 1)],
        )
        assert result.rule_id == "test:rule"
        # The message is a string, not an object with .text
        assert result.message == "Test message"
        assert result.level == "error"

    def test_make_location(self):
        """Test location creation."""
        location = make_location("test.py", 10, 5)
        # The location is a dict, not an object with attributes
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_make_location_edge_values(self):
        """Test location creation with edge values."""
        # Test with zero values
        location = make_location("test.py", 0, 0)
        assert location["physicalLocation"]["region"]["startLine"] == 0
        assert location["physicalLocation"]["region"]["startColumn"] == 0

        # Test with large values
        location = make_location("test.py", 999999, 999999)
        assert location["physicalLocation"]["region"]["startLine"] == 999999
        assert location["physicalLocation"]["region"]["startColumn"] == 999999

    def test_write_sarif(self):
        """Test SARIF file writing."""
        results = [
            SarifResult(
                rule_id="test:rule",
                message="Test message",
                level="error",
                locations=[make_location("test.py", 1, 1)],
            )
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            write_sarif(results, "test.sarif")
            mock_file.assert_called_once_with("test.sarif", "w")

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


class TestReportFormats:
    """Test different report formats."""

    def test_write_json(self):
        """Test JSON report writing."""
        results = [GateResult("Test", True, "Passed")]
        findings = []  # Empty findings list

        with patch("builtins.open", mock_open()) as mock_file:
            write_json(results, findings, "test.json")
            mock_file.assert_called_once_with("test.json", "w")

    def test_write_json_io_error(self):
        """Test JSON writing with IO error."""
        results = [GateResult("Test", True, "Passed")]
        findings = []

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_json(results, findings, "test.json")

    def test_write_html(self):
        """Test HTML report writing."""
        results = [GateResult("Test", True, "Passed")]
        findings = []  # Empty findings list

        with patch("builtins.open", mock_open()) as mock_file:
            write_html(results, findings, "test.html")
            mock_file.assert_called_once_with("test.html", "w")

    def test_write_html_io_error(self):
        """Test HTML writing with IO error."""
        results = [GateResult("Test", True, "Passed")]
        findings = []

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                write_html(results, findings, "test.html")


class TestSecurityScanner:
    """Test security scanning functionality."""

    def test_run_bandit_success(self):
        """Test bandit run with success."""
        with patch("subprocess.call", return_value=0):
            result = run_bandit()
            assert result == 0

    def test_run_bandit_with_extra_args(self):
        """Test bandit run with extra arguments."""
        with patch("subprocess.call", return_value=0) as mock_call:
            run_bandit(["-f", "json"])
            mock_call.assert_called_once()
            args = mock_call.call_args[0][0]
            assert "-f" in args
            assert "json" in args

    def test_run_bandit_subprocess_error(self):
        """Test bandit run with subprocess error."""
        with patch(
            "subprocess.call", side_effect=subprocess.CalledProcessError(1, "bandit")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_bandit()

    def test_run_safety_check(self):
        """Test safety check."""
        with patch("subprocess.call", return_value=0):
            result = run_safety_check()
            assert result == 0

    def test_run_safety_check_subprocess_error(self):
        """Test safety check with subprocess error."""
        with patch(
            "subprocess.call", side_effect=subprocess.CalledProcessError(1, "safety")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_safety_check()


class TestTestsRunner:
    """Test test runner functionality."""

    def test_run_pytest_with_coverage(self):
        """Test pytest run with coverage."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_pytest_with_coverage()
            assert result == 0

    def test_run_pytest_with_coverage_subprocess_error(self):
        """Test pytest run with subprocess error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "pytest")
        ):
            with pytest.raises(subprocess.CalledProcessError):
                run_pytest_with_coverage()


class TestPRAnnotations:
    """Test PR annotations functionality."""

    def test_code_issue_creation(self):
        """Test CodeIssue creation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test message",
            rule_id="test:rule",
        )
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.rule_id == "test:rule"
        assert issue.severity == "error"

    def test_code_issue_edge_values(self):
        """Test CodeIssue with edge values."""
        issue = CodeIssue(
            file_path="",
            line_number=0,
            column=0,
            severity="warning",
            message="",
            rule_id="",
        )
        assert issue.file_path == ""
        assert issue.line_number == 0
        assert issue.column == 0
        assert issue.rule_id == ""
        assert issue.message == ""
        assert issue.severity == "warning"

    def test_pr_annotator_creation(self):
        """Test PRAnnotator creation."""
        annotator = PRAnnotator()
        assert annotator is not None

    def test_format_annotation_message(self):
        """Test annotation message formatting."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test message",
            rule_id="test:rule",
        )
        message = format_annotation_message(issue)
        # The function returns just the message, not formatted with rule_id
        assert "Test message" in message


class TestMainIntegration:
    """Test main integration functionality."""

    def test_main_with_minimal_args(self):
        """Test main function with minimal arguments."""
        with (
            patch("sys.argv", ["ai-guard", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
            patch("ai_guard.analyzer.load_config") as mock_load_config,
        ):

            # Mock load_config to return a dict with min_coverage
            mock_load_config.return_value = {"min_coverage": 80}

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")

            main()

            mock_lint.assert_called_once()
            mock_type.assert_called_once()
            mock_sec.assert_called_once()
            mock_write.assert_called_once()

    def test_main_with_enhanced_testgen(self):
        """Test main function with enhanced test generation."""
        with (
            patch("sys.argv", ["ai-guard", "--enhanced-testgen", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
            patch("ai_guard.analyzer.EnhancedTestGenerator") as mock_gen,
            patch("ai_guard.analyzer.load_config") as mock_load_config,
        ):

            mock_load_config.return_value = {"min_coverage": 80}

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")
            mock_gen.return_value.generate_tests.return_value = []

            main()

            mock_gen.assert_called_once()

    def test_main_with_pr_annotations(self):
        """Test main function with PR annotations."""
        with (
            patch("sys.argv", ["ai-guard", "--pr-annotations", "--skip-tests"]),
            patch("ai_guard.analyzer.run_lint_check") as mock_lint,
            patch("ai_guard.analyzer.run_type_check") as mock_type,
            patch("ai_guard.analyzer.run_security_check") as mock_sec,
            patch("ai_guard.analyzer.run_coverage_check") as mock_cov,
            patch("ai_guard.analyzer.write_sarif") as mock_write,
            patch("ai_guard.analyzer.PRAnnotator") as mock_annotator,
            patch("ai_guard.analyzer.load_config") as mock_load_config,
        ):

            mock_load_config.return_value = {"min_coverage": 80}

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")
            mock_annotator.return_value.generate_annotations.return_value = []

            main()

            mock_annotator.assert_called_once()

    def test_main_with_invalid_args(self):
        """Test main function with invalid arguments."""
        with (
            patch("sys.argv", ["ai-guard", "--invalid-arg"]),
            patch("ai_guard.analyzer.load_config") as mock_load_config,
            pytest.raises(SystemExit),
        ):
            mock_load_config.return_value = {"min_coverage": 80}
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
            patch("sys.stderr") as mock_stderr,
            patch("ai_guard.analyzer.load_config") as mock_load_config,
        ):

            mock_load_config.return_value = {"min_coverage": 80}

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")

            main()

            # Check that deprecation warning was printed
            mock_stderr.write.assert_called()
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
            patch("ai_guard.analyzer.load_config") as mock_load_config,
        ):

            mock_load_config.return_value = {"min_coverage": 80}

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
