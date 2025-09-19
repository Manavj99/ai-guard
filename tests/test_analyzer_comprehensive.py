"""Comprehensive tests for analyzer.py - the main orchestrator."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.ai_guard.analyzer import (
    RuleIdStyle,
    _rule_style,
    _make_rule_id,
    _strict_subprocess_fail,
    _to_text,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    _normalize_rule_id,
    _norm,
    _coverage_percent_from_xml,
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    run_lint_check,
    run_type_check,
    _parse_bandit_json,
    _parse_bandit_output,
    run_security_check,
    _to_findings,
    _run_tool,
    _write_reports,
    _should_skip_file,
    _parse_coverage_output,
    _parse_sarif_output,
    _get_git_diff,
    _get_changed_files,
    run_coverage_check,
    AnalysisConfig,
    AnalysisResult,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    analyze_code,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    generate_report,
    run_analysis
)


class TestRuleIdStyle:
    """Test RuleIdStyle enum and related functions."""

    def test_rule_style_bare_default(self):
        """Test default rule style is BARE."""
        with patch.dict(os.environ, {}, clear=True):
            style = _rule_style()
            assert style == RuleIdStyle.BARE

    def test_rule_style_tool(self):
        """Test tool rule style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            style = _rule_style()
            assert style == RuleIdStyle.TOOL

    def test_rule_style_invalid(self):
        """Test invalid rule style defaults to BARE."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "invalid"}):
            style = _rule_style()
            assert style == RuleIdStyle.BARE

    def test_make_rule_id_bare(self):
        """Test rule ID creation in BARE style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "bare"}):
            rule_id = _make_rule_id("flake8", "E501")
            assert rule_id == "E501"

    def test_make_rule_id_tool(self):
        """Test rule ID creation in TOOL style."""
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            rule_id = _make_rule_id("flake8", "E501")
            assert rule_id == "flake8:E501"

    def test_make_rule_id_no_code(self):
        """Test rule ID creation without code."""
        rule_id = _make_rule_id("flake8", None)
        assert rule_id == "flake8"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_strict_subprocess_fail_default(self):
        """Test strict subprocess fail default."""
        with patch.dict(os.environ, {}, clear=True):
            assert _strict_subprocess_fail() is False

    def test_strict_subprocess_fail_true(self):
        """Test strict subprocess fail enabled."""
        with patch.dict(os.environ, {"AI_GUARD_STRICT_SUBPROCESS_ERRORS": "true"}):
            assert _strict_subprocess_fail() is True
    
    def test_to_text_string(self):
        """Test _to_text with string input."""
        result = _to_text("test string")
        assert result == "test string"
    
    def test_to_text_bytes(self):
        """Test _to_text with bytes input."""
        result = _to_text(b"test bytes")
        assert result == "test bytes"
    
    def test_to_text_none(self):
        """Test _to_text with None input."""
        result = _to_text(None)
        assert result == ""

    def test_to_text_other(self):
        """Test _to_text with other types."""
        result = _to_text(123)
        assert result == "123"

    def test_normalize_rule_id(self):
        """Test rule ID normalization."""
        assert _normalize_rule_id("E501") == "E501"
        assert _normalize_rule_id("flake8:E501") == "E501"
        assert _normalize_rule_id("mypy:name-defined") == "name-defined"

    def test_norm_string(self):
        """Test _norm with string input."""
        assert _norm("test") == "test"

    def test_norm_bytes(self):
        """Test _norm with bytes input."""
        assert _norm(b"test") == "test"

    def test_norm_none(self):
        """Test _norm with None input."""
        assert _norm(None) == ""


class TestLocationClasses:
    """Test location-related classes."""

    def test_artifact_location(self):
        """Test ArtifactLocation class."""
        location = ArtifactLocation(uri="file://test.py")
        assert location.uri == "file://test.py"

    def test_region(self):
        """Test Region class."""
        region = Region(start_line=10, end_line=15)
        assert region.start_line == 10
        assert region.end_line == 15

    def test_physical_location(self):
        """Test PhysicalLocation class."""
        artifact = ArtifactLocation(uri="file://test.py")
        region = Region(start_line=10, end_line=15)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        
        assert location.artifact_location == artifact
        assert location.region == region

    def test_location(self):
        """Test Location class."""
        artifact = ArtifactLocation(uri="file://test.py")
        region = Region(start_line=10, end_line=15)
        physical_location = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical_location)
        
        assert location.physical_location == physical_location


class TestCoverageFunctions:
    """Test coverage-related functions."""

    def test_coverage_percent_from_xml_none(self):
        """Test coverage from XML with None input."""
        result = _coverage_percent_from_xml(None)
        assert result is None
    
    def test_coverage_percent_from_xml_invalid_file(self):
        """Test coverage from XML with invalid file."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None
    
    def test_coverage_percent_from_xml_valid(self):
        """Test coverage from XML with valid file."""
        xml_content = '''<?xml version="1.0" ?>
        <coverage version="1.0">
            <packages>
                <package name="test" line-rate="0.8" branch-rate="0.7">
                </package>
            </packages>
        </coverage>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = f.name
        
        try:
            result = _coverage_percent_from_xml(xml_path)
            assert result == 80
        finally:
            os.unlink(xml_path)

    def test_cov_percent(self):
        """Test cov_percent function."""
        with patch('src.ai_guard.analyzer._coverage_percent_from_xml') as mock_cov:
            mock_cov.return_value = 85
            result = cov_percent()
            assert result == 85
    

class TestOutputParsing:
    """Test output parsing functions."""

    def test_parse_flake8_output(self):
        """Test flake8 output parsing."""
        flake8_output = """test.py:10:1: E501 line too long (80 > 79 characters)
test.py:15:5: F401 'os' imported but unused
test.py:20:1: W292 no newline at end of file"""
        
        results = _parse_flake8_output(flake8_output)
        assert len(results) == 3
        
        # Check first result
        first_result = results[0]
        assert first_result.rule_id == "E501"
        assert first_result.level == "error"
        assert "line too long" in first_result.message

    def test_parse_mypy_output(self):
        """Test mypy output parsing."""
        mypy_output = """test.py:10: error: Name "undefined_var" is not defined
test.py:15: note: Use "-> None" if function does not return a value"""
        
        results = _parse_mypy_output(mypy_output)
        assert len(results) >= 1
        
        # Check first result
        first_result = results[0]
        assert first_result.rule_id == "mypy-error"
        assert first_result.level == "error"
        assert "not defined" in first_result.message

    def test_parse_bandit_json(self):
        """Test bandit JSON output parsing."""
        bandit_json = json.dumps({
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test issue",
                    "filename": "test.py",
                    "line_number": 10,
                    "test_id": "B101"
                }
            ]
        })
        
        results = _parse_bandit_json(bandit_json)
        assert len(results) == 1
        
        first_result = results[0]
        assert first_result.rule_id == "B101"
        assert first_result.level == "warning"
        assert "Test issue" in first_result.message

    def test_parse_bandit_output(self):
        """Test bandit text output parsing."""
        bandit_output = """bandit test.py:10:1: B101: Test issue [HIGH]"""
        
        results = _parse_bandit_output(bandit_output)
        assert len(results) == 1
        
        first_result = results[0]
        assert first_result.rule_id == "bandit:B101"
        assert first_result.level == "warning"

    def test_parse_coverage_output(self):
        """Test coverage output parsing."""
        coverage_output = """Name                    Stmts   Miss  Cover
----------------------------------------
test.py                    10      2    80%
----------------------------------------
TOTAL 80%"""
        
        result = _parse_coverage_output(coverage_output)
        assert result == 80

    def test_parse_sarif_output(self):
        """Test SARIF output parsing."""
        sarif_output = """{
            "runs": [{
                "results": [{
                    "ruleId": "test-rule",
                    "level": "error",
                    "message": {"text": "Test message"},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": "test.py"},
                            "region": {"startLine": 10}
                        }
                    }]
                }]
            }]
        }"""
        
        results = _parse_sarif_output(sarif_output)
        assert len(results) == 1
        assert results[0]["ruleId"] == "test-rule"


class TestToolExecution:
    """Test tool execution functions."""

    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_success(self, mock_run_cmd):
        """Test successful tool execution."""
        mock_run_cmd.return_value = (0, "success output")
        
        result = _run_tool(["test", "command"])
        assert result.returncode == 0
        assert result.stdout == "success output"
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_failure(self, mock_run_cmd):
        """Test failed tool execution."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError
        mock_run_cmd.side_effect = ToolExecutionError("error output")
        
        result = _run_tool(["test", "command"])
        assert result.returncode == 1
        assert result.stderr == "error output"
    
    @patch('src.ai_guard.utils.subprocess_runner.run_cmd')
    def test_run_tool_timeout(self, mock_run_cmd):
        """Test tool execution timeout."""
        mock_run_cmd.side_effect = subprocess.TimeoutExpired("test", 30)
        
        with pytest.raises(subprocess.TimeoutExpired):
            _run_tool(["test", "command"])


class TestFileFiltering:
    """Test file filtering functions."""

    def test_should_skip_file_python(self):
        """Test that Python files are not skipped."""
        assert _should_skip_file("test.py") is False
        assert _should_skip_file("src/module.py") is False

    def test_should_skip_file_non_python(self):
        """Test that non-Python files are skipped."""
        assert _should_skip_file("test.txt") is True
        assert _should_skip_file("README.md") is True

    def test_should_skip_file_test_files(self):
        """Test that test files are skipped."""
        assert _should_skip_file("test_test.py") is True
        assert _should_skip_file("tests/test_module.py") is True

    def test_should_skip_file_hidden(self):
        """Test that hidden files are skipped."""
        assert _should_skip_file(".hidden.py") is True
        assert _should_skip_file("__pycache__/module.py") is True


class TestGitIntegration:
    """Test Git integration functions."""
    
    @patch('subprocess.run')
    def test_get_git_diff(self, mock_run):
        """Test Git diff retrieval."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="diff content",
            stderr=""
        )
        
        result = _get_git_diff()
        assert result == "diff content"
    
    @patch('subprocess.run')
    def test_get_git_diff_failure(self, mock_run):
        """Test Git diff retrieval failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="error"
        )
        
        result = _get_git_diff()
        assert result == ""

    @patch('subprocess.run')
    def test_get_changed_files(self, mock_run):
        """Test changed files retrieval."""
        mock_run.return_value = Mock(
            stdout="test.py\nsrc/module.py\n",
            returncode=0
        )

        result = _get_changed_files()
        assert result == ["test.py", "src/module.py"]


class TestGateChecks:
    """Test gate check functions."""

    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="test.py:10:1: E501 line too long",
            stderr=""
        )
        
        gate_result, sarif_result = run_lint_check(["test.py"])
        assert gate_result.passed is True
        assert sarif_result is not None

    @patch('subprocess.run')
    def test_run_lint_check_failure(self, mock_run):
        """Test failed lint check."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="test.py:10:1: E501 line too long",
            stderr=""
        )
        
        gate_result, sarif_result = run_lint_check(["test.py"])
        assert gate_result.passed is False
        assert sarif_result is not None

    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test successful type check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success: no issues found",
            stderr=""
        )
        
        gate_result, sarif_result = run_type_check(["test.py"])
        assert gate_result.passed is True

    @patch('subprocess.run')
    def test_run_security_check_success(self, mock_run):
        """Test successful security check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"results": []}',
            stderr=""
        )
        
        gate_result, sarif_result = run_security_check()
        assert gate_result.passed is True

    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_run_coverage_check_success(self, mock_cov_xml):
        """Test successful coverage check."""
        mock_cov_xml.return_value = 85
        
        gate_result, sarif_result = run_coverage_check(min_coverage=80)
        assert gate_result.passed is True


class TestAnalysisClasses:
    """Test analysis classes."""

    def test_analysis_config(self):
        """Test AnalysisConfig class."""
        config = AnalysisConfig()
        
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True
        assert config.output_format == "json"
        assert config.verbose is False

    def test_analysis_result(self):
        """Test AnalysisResult class."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["perf1"],
            quality_issues=["quality1"],
            coverage_data={"test.py": 85.0}
        )
        
        assert result.security_issues == ["issue1"]
        assert result.performance_issues == ["perf1"]
        assert result.quality_issues == ["quality1"]
        assert result.coverage_data == {"test.py": 85.0}

    def test_security_analyzer(self):
        """Test SecurityAnalyzer class."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.rules == []

    def test_performance_analyzer(self):
        """Test PerformanceAnalyzer class."""
        analyzer = PerformanceAnalyzer()
        assert hasattr(analyzer, 'issues')

    def test_quality_analyzer(self):
        """Test QualityAnalyzer class."""
        analyzer = QualityAnalyzer()
        assert hasattr(analyzer, 'issues')

    def test_coverage_analyzer(self):
        """Test CoverageAnalyzer class."""
        analyzer = CoverageAnalyzer()
        assert hasattr(analyzer, 'coverage_data')
        assert hasattr(analyzer, 'threshold')

    def test_code_analyzer(self):
        """Test CodeAnalyzer class."""
        analyzer = CodeAnalyzer()
        assert hasattr(analyzer, 'config')
        assert hasattr(analyzer, 'security_analyzer')
        assert hasattr(analyzer, 'performance_analyzer')
        assert hasattr(analyzer, 'quality_analyzer')
        assert hasattr(analyzer, 'coverage_analyzer')


class TestAnalysisFunctions:
    """Test analysis functions."""

    @patch('src.ai_guard.analyzer.CodeAnalyzer')
    def test_analyze_code(self, mock_analyzer_class):
        """Test analyze_code function."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_file.return_value = AnalysisResult(
            security_issues=[],
            performance_issues=[],
            quality_issues=[],
            coverage_data={"test.py": 85.0}
        )
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_code("test.py")
        assert isinstance(result, AnalysisResult)
        assert result.coverage_data == {"test.py": 85.0}

    @patch('src.ai_guard.analyzer.SecurityAnalyzer')
    def test_analyze_security(self, mock_analyzer_class):
        """Test analyze_security function."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_file.return_value = ["issue1", "issue2"]
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_security("test.py")
        assert result == ["issue1", "issue2"]

    @patch('src.ai_guard.analyzer.PerformanceAnalyzer')
    def test_analyze_performance(self, mock_analyzer_class):
        """Test analyze_performance function."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_file.return_value = ["perf1", "perf2"]
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_performance("test.py")
        assert result == ["perf1", "perf2"]

    @patch('src.ai_guard.analyzer.QualityAnalyzer')
    def test_analyze_quality(self, mock_analyzer_class):
        """Test analyze_quality function."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_file.return_value = ["quality1", "quality2"]
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_quality("test.py")
        assert result == ["quality1", "quality2"]

    @patch('src.ai_guard.analyzer.CoverageAnalyzer')
    def test_analyze_coverage(self, mock_analyzer_class):
        """Test analyze_coverage function."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_file.return_value = {"test.py": 85.0}
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_coverage("test.py")
        assert result == {"test.py": 85.0}

    def test_generate_report_json(self):
        """Test report generation in JSON format."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["perf1"],
            quality_issues=["quality1"],
            coverage_data={"test.py": 85.0}
        )
        
        report = generate_report(result, "json")
        assert isinstance(report, str)
        report_data = json.loads(report)
        assert report_data["security_issues"] == ["issue1"]
        assert report_data["coverage_data"] == {"test.py": 85.0}

    def test_generate_report_html(self):
        """Test report generation in HTML format."""
        result = AnalysisResult(
            security_issues=[],
            performance_issues=[],
            quality_issues=[],
            coverage_data={"test.py": 85.0}
        )
        
        report = generate_report(result, "html")
        assert isinstance(report, str)
        assert "<html>" in report.lower()

    def test_generate_report_unknown_format(self):
        """Test report generation with unknown format."""
        result = AnalysisResult(
            security_issues=[],
            performance_issues=[],
            quality_issues=[],
            coverage_data={"test.py": 85.0}
        )
        
        report = generate_report(result, "unknown")
        assert isinstance(report, str)
        assert "test.py" in report
        assert "85.0" in report

    @patch('src.ai_guard.analyzer.CodeAnalyzer')
    def test_run_analysis(self, mock_analyzer_class):
        """Test run_analysis function."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_file.return_value = AnalysisResult(
            security_issues=[],
            performance_issues=[],
            quality_issues=[],
            coverage_data={"test.py": 85.0}
        )
        mock_analyzer_class.return_value = mock_analyzer
        
        config = AnalysisConfig()
        files = ["test.py"]
        
        result = run_analysis(files, config)
        assert isinstance(result, AnalysisResult)
        assert result.coverage_data == {"test.py": 85.0}


class TestIntegration:
    """Integration tests for analyzer."""

    def test_end_to_end_analysis(self):
        """Test end-to-end analysis workflow."""
        config = AnalysisConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_function(x, y):
    return x + y

class TestClass:
    def method(self):
        return "test"
""")
            test_file = f.name
        
        try:
            # This would normally run the full analysis
            # For now, just test that the function can be called
            result = run_analysis([test_file], config)
            assert isinstance(result, AnalysisResult)
        finally:
            os.unlink(test_file)

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid config
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        
        # Test with different values
        config.enable_security_analysis = False
        assert config.enable_security_analysis is False