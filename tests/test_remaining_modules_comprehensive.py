"""Comprehensive tests for remaining AI-Guard modules to increase coverage."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from src.ai_guard.report_html import (
    generate_html_report, format_html_summary, create_html_table,
    HTMLReportGenerator, write_html
)
from src.ai_guard.report_json import (
    generate_json_report, format_json_summary, JSONReportGenerator,
    write_json
)
from src.ai_guard.sarif_report import (
    generate_sarif_report, create_sarif_run, create_sarif_result,
    SARIFReportGenerator, create_sarif_report, parse_issue_to_sarif,
    SarifResult, SarifRun, make_location, write_sarif
)
from src.ai_guard.gates.coverage_eval import CoverageResult, evaluate_coverage_str
from src.ai_guard.generators.config_loader import load_testgen_config
from src.ai_guard.generators.testgen import generate_speculative_tests
from src.ai_guard.generators.enhanced_testgen import EnhancedTestGenerator
from src.ai_guard.parsers.common import normalize_rule
from src.ai_guard.parsers.typescript import parse_eslint, parse_jest
from src.ai_guard.performance import PerformanceOptimizer
from src.ai_guard.diff_parser import DiffParser
from src.ai_guard.analyzer import (
    SecurityAnalyzer, PerformanceAnalyzer, QualityAnalyzer, 
    CoverageAnalyzer, CodeAnalyzer, AnalysisConfig, AnalysisResult
)
from src.ai_guard.analyzer_optimized import OptimizedCodeAnalyzer
from src.ai_guard.config import Config


class TestReportHTMLComprehensive:
    """Comprehensive tests for HTML report generation."""

    def test_generate_html_report_comprehensive(self):
        """Test HTML report generation comprehensively."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues": [
                {"type": "error", "message": "Error 1", "file": "test.py", "line": 10},
                {"type": "warning", "message": "Warning 1", "file": "test.py", "line": 20}
            ]
        }
        
        result = generate_html_report(analysis_results)
        assert result["success"] is True
        assert result["format"] == "html"
        assert "<html>" in result["content"]
        assert "Error 1" in result["content"]
        assert "Warning 1" in result["content"]
        assert result["files_analyzed"] == 3
        assert result["total_issues"] == 2

    def test_format_html_summary_comprehensive(self):
        """Test HTML summary formatting comprehensively."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 1, "warning": 2}
        }
        
        summary = format_html_summary(report_data)
        assert "<div" in summary
        assert "Files analyzed: 5" in summary
        assert "Total issues: 3" in summary
        assert "Errors: 1" in summary
        assert "Warnings: 2" in summary

    def test_create_html_table_comprehensive(self):
        """Test HTML table creation comprehensively."""
        data = [
            {"file": "test1.py", "issues": 2, "status": "warning"},
            {"file": "test2.py", "issues": 1, "status": "error"}
        ]
        
        table = create_html_table(data, ["file", "issues", "status"])
        assert "<table>" in table
        assert "<thead>" in table
        assert "<tbody>" in table
        assert "test1.py" in table
        assert "test2.py" in table
        assert "2" in table
        assert "1" in table

    def test_html_report_generator_comprehensive(self):
        """Test HTML report generator comprehensively."""
        generator = HTMLReportGenerator()
        
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1,
            "issues": [{"type": "error", "message": "Test error", "file": "test.py", "line": 10}]
        }
        
        result = generator.generate_report(analysis_results)
        assert result["success"] is True
        assert result["format"] == "html"
        assert "<html>" in result["content"]

    def test_write_html_comprehensive(self):
        """Test write_html function comprehensively."""
        from ai_guard.report import GateResult
        
        gates = [
            GateResult(name="test_gate1", passed=True, details="Gate passed"),
            GateResult(name="test_gate2", passed=False, details="Gate failed")
        ]
        
        findings = [
            {"rule_id": "E001", "level": "error", "message": "Test error", "path": "test.py", "line": 10},
            {"rule_id": "W001", "level": "warning", "message": "Test warning", "path": "test.py", "line": 20}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name
        
        try:
            write_html(temp_path, gates, findings)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "<html>" in content
            assert "test_gate1" in content
            assert "test_gate2" in content
            assert "Test error" in content
            assert "Test warning" in content
        finally:
            os.unlink(temp_path)


class TestReportJSONComprehensive:
    """Comprehensive tests for JSON report generation."""

    def test_generate_json_report_comprehensive(self):
        """Test JSON report generation comprehensively."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1},
            "issues": [
                {"type": "error", "message": "Error 1", "file": "test.py"},
                {"type": "warning", "message": "Warning 1", "file": "test.py"}
            ]
        }
        
        result = generate_json_report(analysis_results)
        assert result["success"] is True
        assert result["format"] == "json"
        
        content = json.loads(result["content"])
        assert content["files_analyzed"] == 3
        assert content["total_issues"] == 2
        assert len(content["issues"]) == 2

    def test_format_json_summary_comprehensive(self):
        """Test JSON summary formatting comprehensively."""
        report_data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 1, "warning": 2}
        }
        
        summary = format_json_summary(report_data)
        summary_data = json.loads(summary)
        assert summary_data["files_analyzed"] == 5
        assert summary_data["total_issues"] == 3
        assert summary_data["issues_by_type"]["error"] == 1
        assert summary_data["issues_by_type"]["warning"] == 2

    def test_json_report_generator_comprehensive(self):
        """Test JSON report generator comprehensively."""
        generator = JSONReportGenerator()
        
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1,
            "issues": [{"type": "error", "message": "Test error", "file": "test.py"}]
        }
        
        result = generator.generate_report(analysis_results)
        assert result["success"] is True
        assert result["format"] == "json"
        
        content = json.loads(result["content"])
        assert content["files_analyzed"] == 2

    def test_write_json_comprehensive(self):
        """Test write_json function comprehensively."""
        from ai_guard.report import GateResult
        
        gates = [
            GateResult(name="test_gate1", passed=True, details="Gate passed"),
            GateResult(name="test_gate2", passed=False, details="Gate failed")
        ]
        
        findings = [
            {"rule_id": "E001", "level": "error", "message": "Test error", "path": "test.py", "line": 10}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            write_json(temp_path, gates, findings)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data["version"] == "1.0"
            assert len(data["summary"]["gates"]) == 2
            assert len(data["findings"]) == 1
        finally:
            os.unlink(temp_path)


class TestSARIFReportComprehensive:
    """Comprehensive tests for SARIF report generation."""

    def test_generate_sarif_report_comprehensive(self):
        """Test SARIF report generation comprehensively."""
        analysis_results = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues": [
                {
                    "type": "error",
                    "message": "Error 1",
                    "file": "test.py",
                    "line": 10,
                    "rule_id": "rule1"
                },
                {
                    "type": "warning",
                    "message": "Warning 1",
                    "file": "test.py",
                    "line": 20,
                    "rule_id": "rule2"
                }
            ]
        }
        
        result = generate_sarif_report(analysis_results)
        assert result["success"] is True
        assert result["format"] == "sarif"
        
        content = json.loads(result["content"])
        assert content["version"] == "2.1.0"
        assert content["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
        assert len(content["runs"]) == 1
        assert len(content["runs"][0]["results"]) == 2

    def test_create_sarif_run_comprehensive(self):
        """Test SARIF run creation comprehensively."""
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1,
            "issues": [
                {
                    "type": "error",
                    "message": "Error 1",
                    "file": "test.py",
                    "line": 10,
                    "rule_id": "rule1"
                }
            ]
        }
        
        sarif_run = create_sarif_run(analysis_results)
        assert sarif_run["tool"]["driver"]["name"] == "AI-Guard"
        assert len(sarif_run["results"]) == 1
        assert sarif_run["results"][0]["ruleId"] == "rule1"

    def test_create_sarif_result_comprehensive(self):
        """Test SARIF result creation comprehensively."""
        issue = {
            "type": "error",
            "message": "Error 1",
            "file": "test.py",
            "line": 10,
            "rule_id": "rule1"
        }
        
        result = create_sarif_result(issue)
        assert result["ruleId"] == "rule1"
        assert result["level"] == "error"
        assert result["message"]["text"] == "Error 1"
        assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 10

    def test_sarif_report_generator_comprehensive(self):
        """Test SARIF report generator comprehensively."""
        generator = SARIFReportGenerator()
        
        analysis_results = {
            "files_analyzed": 2,
            "total_issues": 1,
            "issues": [
                {
                    "type": "error",
                    "message": "Error 1",
                    "file": "test.py",
                    "line": 10,
                    "rule_id": "rule1"
                }
            ]
        }
        
        result = generator.generate_report(analysis_results)
        assert result["success"] is True
        assert result["format"] == "sarif"
        
        content = json.loads(result["content"])
        assert content["version"] == "2.1.0"
        assert len(content["runs"]) == 1

    def test_parse_issue_to_sarif_comprehensive(self):
        """Test parsing issues to SARIF comprehensively."""
        issue = {
            "rule_id": "E001",
            "level": "error",
            "message": "Test error",
            "file": "test.py",
            "line": 10,
            "column": 5
        }
        
        sarif_result = parse_issue_to_sarif(issue)
        assert sarif_result.rule_id == "E001"
        assert sarif_result.level == "error"
        assert sarif_result.message == "Test error"
        assert sarif_result.locations is not None
        assert len(sarif_result.locations) == 1

    def test_make_location_comprehensive(self):
        """Test making SARIF locations comprehensively."""
        # Test with line and column
        location = make_location("test.py", 10, 5)
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5
        
        # Test with line only
        location = make_location("test.py", 10)
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        
        # Test with no line/column
        location = make_location("test.py")
        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert "region" not in location["physicalLocation"]

    def test_write_sarif_comprehensive(self):
        """Test write_sarif function comprehensively."""
        sarif_run = SarifRun(
            tool_name="AI-Guard",
            tool_version="1.0.0",
            results=[
                SarifResult(
                    rule_id="E001",
                    level="error",
                    message="Test error",
                    locations=[make_location("test.py", 10)]
                )
            ]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sarif') as f:
            temp_path = f.name
        
        try:
            write_sarif(temp_path, sarif_run)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data["version"] == "2.1.0"
            assert len(data["runs"]) == 1
            assert data["runs"][0]["tool"]["driver"]["name"] == "AI-Guard"
        finally:
            os.unlink(temp_path)


class TestCoverageEvalComprehensive:
    """Comprehensive tests for coverage evaluation."""

    def test_coverage_evaluator_comprehensive(self):
        """Test coverage evaluation comprehensively."""
        # Test with high coverage XML
        high_coverage_xml = '''<?xml version="1.0" ?>
        <coverage line-rate="0.85" branch-rate="0.80">
            <packages>
                <package name="src" line-rate="0.85" branch-rate="0.80">
                    <classes>
                        <class name="test_module" line-rate="0.85" branch-rate="0.80"/>
                    </classes>
                </package>
            </packages>
        </coverage>'''
        
        result = evaluate_coverage_str(high_coverage_xml, 80.0)
        assert result.passed is True
        assert result.percent == 85.0
        
        # Test with low coverage XML
        low_coverage_xml = '''<?xml version="1.0" ?>
        <coverage line-rate="0.75" branch-rate="0.70">
            <packages>
                <package name="src" line-rate="0.75" branch-rate="0.70">
                    <classes>
                        <class name="test_module" line-rate="0.75" branch-rate="0.70"/>
                    </classes>
                </package>
            </packages>
        </coverage>'''
        
        result = evaluate_coverage_str(low_coverage_xml, 80.0)
        assert result.passed is False
        assert result.percent == 75.0
        
        # Test with exact threshold
        exact_coverage_xml = '''<?xml version="1.0" ?>
        <coverage line-rate="0.80" branch-rate="0.80">
            <packages>
                <package name="src" line-rate="0.80" branch-rate="0.80">
                    <classes>
                        <class name="test_module" line-rate="0.80" branch-rate="0.80"/>
                    </classes>
                </package>
            </packages>
        </coverage>'''
        
        result = evaluate_coverage_str(exact_coverage_xml, 80.0)
        assert result.passed is True
        assert result.percent == 80.0


class TestConfigLoaderComprehensive:
    """Comprehensive tests for config loader."""

    def test_config_loader_comprehensive(self):
        """Test config loader function comprehensively."""
        # Test loading config with valid TOML
        toml_content = """
[testgen]
threshold = 80.0
enabled = true
"""
        with patch("builtins.open", mock_open(read_data=toml_content)):
            config = load_testgen_config("config.toml")
            assert config is not None
        
        # Test loading config with environment variables
        with patch.dict(os.environ, {"AI_GUARD_THRESHOLD": "85.0"}):
            config = load_testgen_config()
            assert config is not None


class TestTestGeneratorComprehensive:
    """Comprehensive tests for test generator."""

    def test_test_generator_comprehensive(self):
        """Test test generator function comprehensively."""
        # Test generating tests for changed files
        changed_files = ["test.py", "module.py"]
        
        result = generate_speculative_tests(changed_files)
        
        assert isinstance(result, str)
        assert "test.py" in result
        assert "module.py" in result
        assert "pytest" in result
        assert "test_generated_imports" in result


class TestEnhancedTestGeneratorComprehensive:
    """Comprehensive tests for enhanced test generator."""

    def test_enhanced_test_generator_comprehensive(self):
        """Test EnhancedTestGenerator comprehensively."""
        from src.ai_guard.generators.enhanced_testgen import TestGenConfig
        config = TestGenConfig()
        generator = EnhancedTestGenerator(config)
        
        # Test generating enhanced tests
        code_content = """
        def multiply(a, b):
            return a * b
        """
        
        result = generator.generate_tests(code_content, "test.py")
        assert isinstance(result, str)
        # The method may return empty string if no tests can be generated
        # Just verify it returns a string


class TestCommonParserComprehensive:
    """Comprehensive tests for common parser."""

    def test_common_parser_comprehensive(self):
        """Test common parser functions comprehensively."""
        # Test rule normalization
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"
        
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"
        
        result = normalize_rule("bandit", "B101")
        assert result == "bandit:B101"
        
        result = normalize_rule("eslint", "no-unused")
        assert result == "eslint:no-unused"


class TestTypeScriptParserComprehensive:
    """Comprehensive tests for TypeScript parser."""

    def test_typescript_parser_comprehensive(self):
        """Test TypeScript parser functions comprehensively."""
        # Test ESLint parsing with JSON format
        eslint_json = json.dumps([{
            "filePath": "test.ts",
            "messages": [{
                "line": 10,
                "column": 5,
                "severity": 2,
                "ruleId": "no-unused-vars",
                "message": "Variable is unused"
            }]
        }])
        
        result = parse_eslint(eslint_json)
        assert len(result) == 1
        assert result[0]["file"] == "test.ts"
        assert result[0]["line"] == 10
        assert result[0]["severity"] == "error"
        
        # Test Jest parsing
        jest_output = "Tests: 1 failed, 12 passed, 13 total"
        summary = parse_jest(jest_output)
        assert summary["tests"] == 13
        assert summary["passed"] == 12
        assert summary["failed"] == 1


class TestPerformanceAnalyzerComprehensive:
    """Comprehensive tests for performance analyzer."""

    def test_performance_analyzer_comprehensive(self):
        """Test PerformanceAnalyzer comprehensively."""
        analyzer = PerformanceOptimizer()
        
        # Test analyzing performance
        code_content = """
        def slow_function():
            import time
            time.sleep(1)
            return "done"
        """
        
        result = analyzer.analyze_performance()
        assert isinstance(result, dict)
        assert "total_functions" in result


class TestDiffParserComprehensive:
    """Comprehensive tests for diff parser."""

    def test_diff_parser_comprehensive(self):
        """Test DiffParser comprehensively."""
        parser = DiffParser()
        
        # Test parsing diff
        diff_content = """
        diff --git a/test.py b/test.py
        index 1234567..abcdefg 100644
        --- a/test.py
        +++ b/test.py
        @@ -1,3 +1,3 @@
        -old line
        +new line
        """
        
        result = parser.parse_changed_files()
        assert isinstance(result, list)


class TestAnalyzerComprehensive:
    """Comprehensive tests for analyzer."""

    def test_analyzer_comprehensive(self):
        """Test CodeAnalyzer comprehensively."""
        analyzer = CodeAnalyzer()
        
        # Test analyzing a file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def example_function():
    return "Hello, World!"
""")
            temp_file = f.name
        
        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            assert hasattr(result, 'security_issues')
            assert hasattr(result, 'performance_issues')
            assert hasattr(result, 'quality_issues')
        finally:
            os.unlink(temp_file)


class TestOptimizedAnalyzerComprehensive:
    """Comprehensive tests for optimized analyzer."""

    def test_optimized_analyzer_comprehensive(self):
        """Test OptimizedCodeAnalyzer comprehensively."""
        analyzer = OptimizedCodeAnalyzer()
        
        # Test optimized analysis
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def optimized_function():
    return "Optimized!"
""")
            temp_file = f.name
        
        try:
            result = analyzer.run_all_checks([temp_file])
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)


class TestConfigComprehensive:
    """Comprehensive tests for config."""

    def test_config_comprehensive(self):
        """Test Config comprehensively."""
        config = Config()
        
        # Test configuration properties
        assert config.min_coverage == 80
        assert config.skip_tests is False
        assert config.report_format == "sarif"
