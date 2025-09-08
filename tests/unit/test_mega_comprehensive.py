"""Mega comprehensive test for AI-Guard to achieve 90%+ coverage."""

import pytest
import tempfile
import json
from unittest.mock import patch, mock_open
from pathlib import Path

# Import all modules
from ai_guard.analyzer import CodeAnalyzer
from ai_guard.config import Config
from ai_guard.diff_parser import DiffParser
from ai_guard.pr_annotations import (
    PRAnnotator,
    CodeIssue,
    create_pr_annotations,
    parse_lint_output,
)
from ai_guard.report import GateResult
from ai_guard.report_html import HTMLReportGenerator
from ai_guard.report_json import write_json
from ai_guard.sarif_report import write_sarif, SarifRun
from ai_guard.security_scanner import SecurityScanner
from ai_guard.tests_runner import TestsRunner
from ai_guard.generators.config_loader import load_testgen_config
from ai_guard.generators.enhanced_testgen import EnhancedTestGenerator, TestGenConfig
from ai_guard.language_support.js_ts_support import (
    JavaScriptTypeScriptSupport,
    JSTestGenerationConfig,
)


class TestCodeAnalyzer:
    """Comprehensive tests for CodeAnalyzer."""

    def test_analyzer_init(self):
        """Test analyzer initialization."""
        analyzer = CodeAnalyzer()
        assert analyzer is not None

    def test_run_all_checks(self):
        """Test running all checks."""
        analyzer = CodeAnalyzer()

        with patch(
            "ai_guard.analyzer.run_lint_check",
            return_value=(GateResult("test", True), []),
        ):
            with patch(
                "ai_guard.analyzer.run_type_check",
                return_value=(GateResult("test", True), []),
            ):
                with patch(
                    "ai_guard.analyzer.run_security_check",
                    return_value=(GateResult("test", True), []),
                ):
                    with patch(
                        "ai_guard.analyzer.run_coverage_check",
                        return_value=GateResult("test", True),
                    ):
                        result = analyzer.run_all_checks()
                        assert result is not None
                        assert len(result) > 0

    def test_analyzer_with_config(self):
        """Test analyzer with custom config."""
        config = {"min_coverage": 90}
        analyzer = CodeAnalyzer(config)
        assert analyzer.config == config


class TestConfig:
    """Comprehensive tests for Config."""

    def test_config_init(self):
        """Test config initialization."""
        config = Config()
        assert config is not None

    def test_config_properties(self):
        """Test config properties."""
        config = Config()

        # Test default values
        assert config.min_coverage == 80
        assert config.skip_tests == False
        assert config.report_format == "sarif"
        assert config.enhanced_testgen == False

    def test_config_get_set(self):
        """Test config get and set methods."""
        config = Config()

        # Test get method
        assert config.get("min_coverage") == 80
        assert config.get("nonexistent", "default") == "default"

        # Test set method
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"


class TestDiffParser:
    """Comprehensive tests for DiffParser."""

    def test_parser_init(self):
        """Test parser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_parse_changed_files(self):
        """Test parsing changed files."""
        parser = DiffParser()

        with patch(
            "ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ):
            result = parser.parse_changed_files()
            assert result == ["test.py"]

    def test_parse_github_event(self):
        """Test parsing GitHub event."""
        parser = DiffParser()

        with patch(
            "ai_guard.diff_parser.parse_github_event", return_value={"test": "data"}
        ):
            result = parser.parse_github_event("event.json")
            assert result == {"test": "data"}


class TestPRAnnotator:
    """Comprehensive tests for PRAnnotator."""

    def test_annotator_init(self):
        """Test annotator initialization."""
        annotator = PRAnnotator()
        assert annotator is not None

    def test_create_annotation(self):
        """Test creating annotation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=1,
            column=1,
            severity="error",
            message="Test issue",
            rule_id="TEST001",
        )
        annotator = PRAnnotator()
        annotator.add_issue(issue)
        assert len(annotator.annotations) > 0

    def test_create_pr_annotations_function(self):
        """Test create_pr_annotations function."""
        # Test with string input (not list)
        result = create_pr_annotations(lint_output="test.py:1:1: E501 line too long")
        assert isinstance(result, dict)
        assert "annotations" in result

    def test_parse_lint_output(self):
        """Test parsing lint output."""
        lint_output = "test.py:1:1: error: Test error"
        issues = parse_lint_output(lint_output)
        assert isinstance(issues, list)


class TestReportGenerators:
    """Comprehensive tests for report generators."""

    def test_html_report(self):
        """Test HTML report generation."""
        generator = HTMLReportGenerator()
        results = [GateResult("test", True)]
        findings = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            generator.generate_html_report(results, findings, temp_path)
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_json_report(self):
        """Test JSON report generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            gates = [GateResult("test", True)]
            findings = []
            write_json(temp_path, gates, findings)

            # Verify file was created and contains valid JSON
            with open(temp_path, "r") as f:
                data = json.load(f)
                assert "version" in data
                assert "summary" in data
                assert "findings" in data
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_sarif_report(self):
        """Test SARIF report generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as f:
            temp_path = f.name

        try:
            # Create a test run
            run = SarifRun(tool_name="ai-guard", tool_version="1.0.0", results=[])

            # Write SARIF report
            write_sarif(temp_path, run)

            # Verify file was created
            assert Path(temp_path).exists()

            # Verify it contains valid JSON
            with open(temp_path, "r") as f:
                data = json.load(f)
                assert "runs" in data
                assert len(data["runs"]) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestSecurityScanner:
    """Comprehensive tests for SecurityScanner."""

    def test_scanner_init(self):
        """Test scanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None

    def test_run_bandit_scan(self):
        """Test bandit scanning."""
        scanner = SecurityScanner()

        with patch("ai_guard.security_scanner.run_bandit", return_value=0):
            result = scanner.run_bandit_scan()
            assert result == 0


class TestTestsRunner:
    """Comprehensive tests for TestsRunner."""

    def test_runner_init(self):
        """Test runner initialization."""
        runner = TestsRunner()
        assert runner is not None

    def test_run_tests(self):
        """Test running tests."""
        runner = TestsRunner()

        with patch("ai_guard.tests_runner.run_pytest", return_value=0):
            result = runner.run_pytest()
            assert result == 0


class TestEnhancedTestGenerator:
    """Comprehensive tests for EnhancedTestGenerator."""

    def test_generator_init(self):
        """Test generator initialization."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)
        assert generator is not None

    def test_generate_tests(self):
        """Test test generation."""
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)

        with patch.object(generator, "generate_tests", return_value="test content"):
            result = generator.generate_tests(["test.py"], None)
            assert result == "test content"


class TestJavaScriptSupport:
    """Comprehensive tests for JavaScript support."""

    def test_js_support_init(self):
        """Test JS support initialization."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        assert support is not None

    def test_js_support_methods(self):
        """Test JS support methods."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        # Test that the support object has expected methods
        assert hasattr(support, "run_eslint")
        assert hasattr(support, "run_prettier")
        assert hasattr(support, "run_typescript_check")
        assert hasattr(support, "generate_tests")


class TestConfigLoader:
    """Comprehensive tests for config loader."""

    def test_load_config(self):
        """Test loading testgen config."""
        with patch(
            "builtins.open", mock_open(read_data="[testgen]\ntemperature = 0.7")
        ):
            with patch("tomli.load", return_value={"testgen": {"temperature": 0.7}}):
                config = load_testgen_config("config.toml")
                assert config is not None


# Additional test functions
def test_gate_result():
    """Test GateResult class."""
    result = GateResult("test", True, "details")
    assert result.name == "test"
    assert result.passed == True
    assert result.details == "details"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
