"""Comprehensive test suite to achieve 90%+ coverage for AI-Guard."""

import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock

# Import all modules to test
from ai_guard import __version__, __author__
from ai_guard.config import load_config, get_default_config, validate_config, Gates
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
from ai_guard.generators.enhanced_testgen import (
    EnhancedTestGenerator,
    TestGenerationConfig,
    TestTemplate,
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
            assert isinstance(config, Gates)
            assert config.min_coverage == 80

    def test_load_config_from_file(self):
        """Test loading config from file."""
        config_data = {"min_coverage": 90, "skip_tests": True, "report_format": "json"}

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(config_data))),
            patch("tomli.load", return_value=config_data),
        ):
            config = load_config()
            assert config.min_coverage == 90
            assert config.skip_tests is True
            assert config.report_format == "json"


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
        assert "3/3 gates passed" in summary
        assert "✅" in summary

    def test_summarize_failure(self):
        """Test summarize with failing gates."""
        results = [
            GateResult("Lint", True, "Passed"),
            GateResult("Type", False, "Failed"),
            GateResult("Security", True, "Passed"),
        ]
        summary = summarize(results)
        assert "2/3 gates passed" in summary
        assert "❌" in summary


class TestDiffParser:
    """Test diff parsing functionality."""

    def test_get_file_extensions(self):
        """Test file extension extraction."""
        files = ["test.py", "test.js", "test.ts", "README.md"]
        extensions = get_file_extensions(files)
        assert extensions == {".py", ".js", ".ts", ".md"}

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

    def test_parse_flake8_output(self):
        """Test parsing flake8 output."""
        flake8_output = "src/test.py:1:1: E111 indentation is not a multiple of four"
        results = _parse_flake8_output(flake8_output)
        assert len(results) == 1
        assert results[0].rule_id == "flake8:E111"
        assert "indentation" in results[0].message.text

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = "src/test.py:1: error: Incompatible types in assignment"
        results = _parse_mypy_output(mypy_output)
        assert len(results) == 1
        assert results[0].rule_id == "mypy:error"
        assert "Incompatible types" in results[0].message.text

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
            assert len(sarif) > 0

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
            assert len(sarif) > 0

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
            assert len(sarif) > 0

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


class TestSarifReport:
    """Test SARIF report functionality."""

    def test_sarif_run_creation(self):
        """Test SarifRun creation."""
        run = SarifRun()
        assert run.tool.driver.name == "ai-guard"
        assert run.tool.driver.version == "0.1.0"

    def test_sarif_result_creation(self):
        """Test SarifResult creation."""
        result = SarifResult(
            rule_id="test:rule",
            message="Test message",
            level="error",
            locations=[make_location("test.py", 1, 1)],
        )
        assert result.rule_id == "test:rule"
        assert result.message.text == "Test message"
        assert result.level == "error"

    def test_make_location(self):
        """Test location creation."""
        location = make_location("test.py", 10, 5)
        assert location.physical_location.artifact_location.uri == "test.py"
        assert location.physical_location.region.start_line == 10
        assert location.physical_location.region.start_column == 5

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


class TestReportFormats:
    """Test different report formats."""

    def test_write_json(self):
        """Test JSON report writing."""
        results = [GateResult("Test", True, "Passed")]

        with patch("builtins.open", mock_open()) as mock_file:
            write_json(results, "test.json")
            mock_file.assert_called_once_with("test.json", "w")

    def test_write_html(self):
        """Test HTML report writing."""
        results = [GateResult("Test", True, "Passed")]

        with patch("builtins.open", mock_open()) as mock_file:
            write_html(results, "test.html")
            mock_file.assert_called_once_with("test.html", "w")


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

    def test_run_safety_check(self):
        """Test safety check."""
        with patch("subprocess.call", return_value=0):
            result = run_safety_check()
            assert result == 0


class TestTestsRunner:
    """Test test runner functionality."""

    def test_run_pytest_with_coverage(self):
        """Test pytest run with coverage."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_pytest_with_coverage()
            assert result == 0


class TestPRAnnotations:
    """Test PR annotations functionality."""

    def test_code_issue_creation(self):
        """Test CodeIssue creation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="test:rule",
            message="Test message",
            level=AnnotationLevel.ERROR,
        )
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.rule_id == "test:rule"
        assert issue.severity == "error"

    def test_pr_annotator_creation(self):
        """Test PRAnnotator creation."""
        annotator = PRAnnotator()
        assert annotator is not None

    def test_format_annotation_message(self):
        """Test annotation message formatting."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="test:rule",
            message="Test message",
            level=AnnotationLevel.ERROR,
        )
        message = format_annotation_message(issue)
        assert "test:rule" in message
        assert "Test message" in message
        assert "test.py:10:5" in message


class TestEnhancedTestGen:
    """Test enhanced test generation functionality."""

    def test_test_generation_config(self):
        """Test TestGenerationConfig creation."""
        config = TestGenerationConfig()
        assert config.framework == "pytest"
        assert config.generate_mocks is True

    def test_test_template(self):
        """Test TestTemplate creation."""
        template = TestTemplate()
        assert template is not None

    def test_enhanced_test_generator(self):
        """Test EnhancedTestGenerator creation."""
        generator = EnhancedTestGenerator()
        assert generator is not None


class TestConfigLoader:
    """Test config loader functionality."""

    def test_get_env_api_key(self):
        """Test environment API key retrieval."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            key = _get_env_api_key()
            assert key == "test-key"

    def test_create_default_config(self):
        """Test default config creation."""
        with patch("builtins.open", mock_open()) as mock_file:
            create_default_config("test.toml")
            mock_file.assert_called_once_with("test.toml", "w")


class TestJSTSSupport:
    """Test JavaScript/TypeScript support functionality."""

    def test_check_node_installed(self):
        """Test Node.js installation check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = check_node_installed()
            assert result is True

    def test_check_npm_installed(self):
        """Test npm installation check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = check_npm_installed()
            assert result is True

    def test_run_eslint(self):
        """Test ESLint execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_eslint(["test.js"])
            assert result == 0

    def test_run_typescript_check(self):
        """Test TypeScript check execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_typescript_check(["test.ts"])
            assert result == 0

    def test_run_jest_tests(self):
        """Test Jest test execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_jest_tests()
            assert result == 0

    def test_run_prettier_check(self):
        """Test Prettier check execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_prettier_check(["test.js"])
            assert result == 0


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
        ):

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
        ):

            mock_lint.return_value = (GateResult("Lint", True, "OK"), [])
            mock_type.return_value = (GateResult("Type", True, "OK"), [])
            mock_sec.return_value = (GateResult("Security", True, "OK"), [])
            mock_cov.return_value = GateResult("Coverage", True, "OK")
            mock_annotator.return_value.generate_annotations.return_value = []

            main()

            mock_annotator.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
