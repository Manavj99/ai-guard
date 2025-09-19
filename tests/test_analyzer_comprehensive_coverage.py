"""Comprehensive tests for analyzer.py to achieve 80+ coverage."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, mock_open, MagicMock, Mock, call
from pathlib import Path
import xml.etree.ElementTree as ET


def safe_unlink(file_path):
    """Safely unlink a file, handling Windows permission errors."""
    try:
        os.unlink(file_path)
    except PermissionError:
        # On Windows, sometimes the file is still locked
        pass

from src.ai_guard.analyzer import (
    RuleIdStyle, _rule_style, _make_rule_id, _strict_subprocess_fail,
    _to_text, ArtifactLocation, Region, PhysicalLocation, Location,
    _normalize_rule_id, _norm, _coverage_percent_from_xml, cov_percent,
    _parse_flake8_output, _parse_mypy_output, run_lint_check, run_type_check,
    _parse_bandit_json, _parse_bandit_output, run_security_check,
    _parse_coverage_output, run_coverage_check,
    AnalysisConfig, AnalysisResult, SecurityAnalyzer, PerformanceAnalyzer,
    QualityAnalyzer, CoverageAnalyzer, CodeAnalyzer,
    analyze_code, analyze_security, analyze_performance, analyze_quality,
    analyze_coverage, generate_report, run_analysis
)


class TestRuleIdHelpers:
    """Test rule ID helper functions."""
    
    def test_rule_style_default(self):
        """Test default rule style."""
        with patch.dict(os.environ, {}, clear=True):
            assert _rule_style() == RuleIdStyle.BARE
    
    def test_rule_style_tool(self):
        """Test tool rule style."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'tool'}):
            assert _rule_style() == RuleIdStyle.TOOL
    
    def test_rule_style_case_insensitive(self):
        """Test rule style is case insensitive."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'TOOL'}):
            assert _rule_style() == RuleIdStyle.TOOL
    
    def test_make_rule_id_bare_style(self):
        """Test making rule ID with bare style."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'bare'}):
            assert _make_rule_id("flake8", "E501") == "E501"
            assert _make_rule_id("mypy", None) == "mypy"
            assert _make_rule_id("bandit", "") == "bandit"
    
    def test_make_rule_id_tool_style(self):
        """Test making rule ID with tool style."""
        with patch.dict(os.environ, {'AI_GUARD_RULE_ID_STYLE': 'tool'}):
            assert _make_rule_id("flake8", "E501") == "flake8:E501"
            assert _make_rule_id("mypy", None) == "mypy:mypy"
            assert _make_rule_id("bandit", "") == "bandit:bandit"


class TestStrictSubprocessFail:
    """Test strict subprocess fail function."""
    
    def test_strict_subprocess_fail_default(self):
        """Test default strict subprocess fail behavior."""
        with patch.dict(os.environ, {}, clear=True):
            assert _strict_subprocess_fail() is False
    
    def test_strict_subprocess_fail_enabled_variants(self):
        """Test strict subprocess fail enabled variants."""
        for value in ["1", "true", "yes", "on"]:
            with patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': value}):
                assert _strict_subprocess_fail() is True
    
    def test_strict_subprocess_fail_disabled_variants(self):
        """Test strict subprocess fail disabled variants."""
        for value in ["0", "false", "no", "off", "disabled"]:
            with patch.dict(os.environ, {'AI_GUARD_STRICT_SUBPROCESS_ERRORS': value}):
                assert _strict_subprocess_fail() is False


class TestToText:
    """Test _to_text function."""
    
    def test_to_text_none(self):
        """Test _to_text with None."""
        assert _to_text(None) == ""
    
    def test_to_text_string(self):
        """Test _to_text with string."""
        assert _to_text("hello") == "hello"
    
    def test_to_text_bytes_utf8(self):
        """Test _to_text with valid UTF-8 bytes."""
        assert _to_text(b"hello") == "hello"
    
    def test_to_text_bytes_with_replacement_char(self):
        """Test _to_text with bytes containing replacement characters."""
        # Create bytes that would decode to contain replacement characters
        invalid_bytes = b'\xff\xfe'
        assert _to_text(invalid_bytes) == ""
    
    def test_to_text_bytes_unicode_decode_error(self):
        """Test _to_text with bytes that cause UnicodeDecodeError."""
        # This should return empty string for invalid bytes
        invalid_bytes = b'\x80\x81\x82'
        assert _to_text(invalid_bytes) == ""
    
    def test_to_text_bytearray(self):
        """Test _to_text with bytearray."""
        assert _to_text(bytearray(b"hello")) == "hello"


class TestDataclasses:
    """Test dataclass definitions."""
    
    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="file://test.py")
        assert location.uri == "file://test.py"
    
    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=1, start_column=1, end_line=10, end_column=20)
        assert region.start_line == 1
        assert region.start_column == 1
        assert region.end_line == 10
        assert region.end_column == 20
    
    def test_region_defaults(self):
        """Test Region dataclass with defaults."""
        region = Region()
        assert region.start_line is None
        assert region.start_column is None
        assert region.end_line is None
        assert region.end_column is None
    
    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="file://test.py")
        region = Region(start_line=1, end_line=10)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        assert location.artifact_location == artifact
        assert location.region == region
    
    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="file://test.py")
        region = Region(start_line=1, end_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        assert location.physical_location == physical


class TestNormalizeRuleId:
    """Test _normalize_rule_id function."""
    
    def test_normalize_rule_id_with_colon(self):
        """Test normalizing rule ID with colon."""
        assert _normalize_rule_id("flake8:E501") == "E501"
        assert _normalize_rule_id("mypy:name-defined") == "name-defined"
    
    def test_normalize_rule_id_without_colon(self):
        """Test normalizing rule ID without colon."""
        assert _normalize_rule_id("E501") == "E501"
        assert _normalize_rule_id("name-defined") == "name-defined"


class TestNorm:
    """Test _norm function."""
    
    def test_norm_none(self):
        """Test _norm with None."""
        assert _norm(None) == ""
    
    def test_norm_string(self):
        """Test _norm with string."""
        assert _norm("hello") == "hello"
    
    def test_norm_bytes(self):
        """Test _norm with bytes."""
        assert _norm(b"hello") == "hello"
    
    def test_norm_bytearray(self):
        """Test _norm with bytearray."""
        assert _norm(bytearray(b"hello")) == "hello"


class TestCoveragePercentFromXml:
    """Test _coverage_percent_from_xml function."""
    
    def test_coverage_percent_from_xml_none_test_mode(self):
        """Test coverage percent from XML with None path in test mode."""
        with patch.dict(os.environ, {'AI_GUARD_TEST_MODE': '1'}):
            result = _coverage_percent_from_xml(None)
            assert result is None
    
    def test_coverage_percent_from_xml_none_production_mode(self):
        """Test coverage percent from XML with None path in production mode."""
        with patch.dict(os.environ, {}, clear=True):
            result = _coverage_percent_from_xml(None)
            assert result is None
    
    def test_coverage_percent_from_xml_file_not_found(self):
        """Test coverage percent from XML with file not found."""
        result = _coverage_percent_from_xml("nonexistent.xml")
        assert result is None
    
    def test_coverage_percent_from_xml_valid_file(self):
        """Test coverage percent from XML with valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            # Create a minimal valid coverage XML
            xml_content = '''<?xml version="1.0" ?>
            <coverage version="5.0" timestamp="1234567890">
                <packages>
                    <package name="test" line-rate="0.85" branch-rate="0.75">
                    </package>
                </packages>
            </coverage>'''
            f.write(xml_content)
            f.flush()
            
            try:
                result = _coverage_percent_from_xml(f.name)
                assert result == 85
            finally:
                safe_unlink(f.name)
    
    def test_coverage_percent_from_xml_invalid_xml(self):
        """Test coverage percent from XML with invalid XML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("invalid xml content")
            f.flush()
            
            try:
                result = _coverage_percent_from_xml(f.name)
                assert result is None
            finally:
                safe_unlink(f.name)


class TestCovPercent:
    """Test cov_percent function."""
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_with_xml_path(self, mock_coverage):
        """Test cov_percent with XML path."""
        mock_coverage.return_value = 85
        result = cov_percent()
        assert result == 85
        mock_coverage.assert_called_once()
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_default_paths(self, mock_coverage):
        """Test cov_percent with default paths."""
        mock_coverage.side_effect = [None, None, 75]
        
        result = cov_percent()
        assert result == 75
        
        expected_calls = [
            call("coverage.xml"),
            call("htmlcov/coverage.xml"),
            call("tests/coverage.xml")
        ]
        mock_coverage.assert_has_calls(expected_calls)
    
    @patch('src.ai_guard.analyzer._coverage_percent_from_xml')
    def test_cov_percent_no_coverage_found(self, mock_coverage):
        """Test cov_percent when no coverage is found."""
        mock_coverage.return_value = None
        
        result = cov_percent()
        assert result is None


class TestParseFlake8Output:
    """Test _parse_flake8_output function."""
    
    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        result = _parse_flake8_output("")
        assert result == []
    
    def test_parse_flake8_output_valid_lines(self):
        """Test parsing valid flake8 output lines."""
        output = """test.py:1:1: E501 line too long (80 > 79 characters)
test.py:2:5: F401 'os' imported but unused
test.py:3:1: W292 no newline at end of file"""
        
        result = _parse_flake8_output(output)
        assert len(result) == 3
        
        # Check first issue - SarifResult object
        assert result[0].rule_id == "E501"
        assert result[0].message == "line too long (80 > 79 characters)"
        assert result[0].locations[0]['physicalLocation']['artifactLocation']['uri'] == "test.py"
        assert result[0].locations[0]['physicalLocation']['region']['startLine'] == 1
    
    def test_parse_flake8_output_invalid_lines(self):
        """Test parsing flake8 output with invalid lines."""
        output = """test.py:1:1: E501 line too long
invalid line format
test.py:3:1: W292 no newline at end of file"""
        
        result = _parse_flake8_output(output)
        assert len(result) == 2  # Only valid lines should be parsed


class TestParseMypyOutput:
    """Test _parse_mypy_output function."""
    
    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        result = _parse_mypy_output("")
        assert result == []
    
    def test_parse_mypy_output_valid_lines(self):
        """Test parsing valid mypy output lines."""
        output = """test.py:5: error: Incompatible return type [return-value]
test.py:10: note: Revealed type is 'builtins.str'
test.py:15: warning: Missing type annotation [type-arg]"""
        
        result = _parse_mypy_output(output)
        assert len(result) == 3
        
        # Check first issue - SarifResult object
        assert result[0].rule_id == "return-value"
        assert result[0].message == "Incompatible return type"
        assert result[0].locations[0]['physicalLocation']['artifactLocation']['uri'] == "test.py"
        assert result[0].locations[0]['physicalLocation']['region']['startLine'] == 5
    
    def test_parse_mypy_output_invalid_lines(self):
        """Test parsing mypy output with invalid lines."""
        output = """test.py:5: error: Incompatible return type [return-value]
invalid line format
test.py:15: warning: Missing type annotation [type-arg]"""
        
        result = _parse_mypy_output(output)
        assert len(result) == 2  # Only valid lines should be parsed


class TestParseBanditJson:
    """Test _parse_bandit_json function."""
    
    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON."""
        result = _parse_bandit_json("")
        assert result == []
    
    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test of bandit_blacklist_calls",
                    "test_id": "B101"
                }
            ]
        }
        
        result = _parse_bandit_json(json.dumps(json_data))
        assert len(result) == 1
        assert result[0].rule_id == "B101"
        assert result[0].message == "Test of bandit_blacklist_calls"
        assert result[0].locations[0]['physicalLocation']['artifactLocation']['uri'] == "test.py"
        assert result[0].locations[0]['physicalLocation']['region']['startLine'] == 10
    
    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON."""
        result = _parse_bandit_json("invalid json")
        assert result == []


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""
    
    def test_parse_bandit_output_json(self):
        """Test parsing bandit output as JSON."""
        json_data = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test issue",
                    "test_id": "B101"
                }
            ]
        }
        
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _parse_bandit_output(json.dumps(json_data))
            assert len(result) == 1
            assert result[0].rule_id == "bandit:B101"
    
    def test_parse_bandit_output_text(self):
        """Test parsing bandit output as text."""
        text_output = """Issue: [B101:test_blacklist_calls] Use of insecure MD2 hash algorithm.
   Severity: Medium   Confidence: High
   Location: test.py:10
   More Info: https://bandit.readthedocs.io/en/1.7.5/blacklists/blacklist_calls.html#b101-md2"""
        
        with patch.dict(os.environ, {"AI_GUARD_RULE_ID_STYLE": "tool"}):
            result = _parse_bandit_output(text_output)
            assert len(result) == 1
            assert result[0].rule_id == "bandit:B101"
            assert result[0].locations[0]['physicalLocation']['artifactLocation']['uri'] == "test.py"
            assert result[0].locations[0]['physicalLocation']['region']['startLine'] == 1


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""
    
    def test_parse_coverage_output_valid(self):
        """Test parsing valid coverage output."""
        output = "Total coverage: 85%"
        result = _parse_coverage_output(output)
        assert result == 85
    
    def test_parse_coverage_output_no_coverage(self):
        """Test parsing coverage output with no coverage."""
        output = "No coverage data found"
        result = _parse_coverage_output(output)
        assert result is None
    
    def test_parse_coverage_output_invalid(self):
        """Test parsing invalid coverage output."""
        output = "invalid output"
        result = _parse_coverage_output(output)
        assert result is None


class TestAnalysisConfig:
    """Test AnalysisConfig class."""
    
    def test_analysis_config_defaults(self):
        """Test AnalysisConfig with default values."""
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True
        assert config.output_format == "json"
        assert config.verbose is False
    
    def test_analysis_config_custom(self):
        """Test AnalysisConfig with custom values."""
        config = AnalysisConfig(
            enable_security_analysis=False,
            enable_performance_analysis=False,
            output_format="html",
            verbose=True
        )
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is False
        assert config.output_format == "html"
        assert config.verbose is True


class TestAnalysisResult:
    """Test AnalysisResult class."""
    
    def test_analysis_result_initialization(self):
        """Test AnalysisResult initialization."""
        result = AnalysisResult()
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.execution_time == 0.0


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""
    
    def test_security_analyzer_initialization(self):
        """Test SecurityAnalyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []
    
    def test_security_analyzer_analyze_file(self):
        """Test SecurityAnalyzer analyze_file method."""
        analyzer = SecurityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nprint('test')")
            f.flush()
            
            try:
                issues = analyzer.analyze_file(f.name)
                assert isinstance(issues, list)
            finally:
                safe_unlink(f.name)
    
    def test_security_analyzer_clear_issues(self):
        """Test SecurityAnalyzer clear_issues method."""
        analyzer = SecurityAnalyzer()
        analyzer.issues = ["issue1", "issue2"]
        
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""
    
    def test_performance_analyzer_initialization(self):
        """Test PerformanceAnalyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.issues == []
    
    def test_performance_analyzer_analyze_file(self):
        """Test PerformanceAnalyzer analyze_file method."""
        analyzer = PerformanceAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                issues = analyzer.analyze_file(f.name)
                assert isinstance(issues, list)
            finally:
                safe_unlink(f.name)
    
    def test_performance_analyzer_clear_issues(self):
        """Test PerformanceAnalyzer clear_issues method."""
        analyzer = PerformanceAnalyzer()
        analyzer.issues = ["issue1", "issue2"]
        
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""
    
    def test_quality_analyzer_initialization(self):
        """Test QualityAnalyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.issues == []
    
    def test_quality_analyzer_analyze_file(self):
        """Test QualityAnalyzer analyze_file method."""
        analyzer = QualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                issues = analyzer.analyze_file(f.name)
                assert isinstance(issues, list)
            finally:
                safe_unlink(f.name)
    
    def test_quality_analyzer_clear_issues(self):
        """Test QualityAnalyzer clear_issues method."""
        analyzer = QualityAnalyzer()
        analyzer.issues = ["issue1", "issue2"]
        
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""
    
    def test_coverage_analyzer_initialization(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}
        assert analyzer.threshold == 80.0
    
    def test_coverage_analyzer_set_threshold(self):
        """Test CoverageAnalyzer set_threshold method."""
        analyzer = CoverageAnalyzer()
        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0
    
    def test_coverage_analyzer_analyze_file_existing(self):
        """Test CoverageAnalyzer analyze_file with existing file."""
        analyzer = CoverageAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyzer.analyze_file(f.name)
                assert isinstance(result, dict)
                assert f.name in result
                assert result[f.name] == 85.5  # Mock value
            finally:
                safe_unlink(f.name)
    
    def test_coverage_analyzer_analyze_file_nonexistent(self):
        """Test CoverageAnalyzer analyze_file with nonexistent file."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == {}
    
    def test_coverage_analyzer_get_coverage_data(self):
        """Test CoverageAnalyzer get_coverage_data method."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.5}
        
        result = analyzer.get_coverage_data()
        assert result == {"test.py": 85.5}
    
    def test_coverage_analyzer_clear_data(self):
        """Test CoverageAnalyzer clear_data method."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.5}
        
        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""
    
    def test_code_analyzer_initialization_default(self):
        """Test CodeAnalyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        assert isinstance(analyzer.config, AnalysisConfig)
        assert isinstance(analyzer.security_analyzer, SecurityAnalyzer)
        assert isinstance(analyzer.performance_analyzer, PerformanceAnalyzer)
        assert isinstance(analyzer.quality_analyzer, QualityAnalyzer)
        assert isinstance(analyzer.coverage_analyzer, CoverageAnalyzer)
    
    def test_code_analyzer_initialization_custom(self):
        """Test CodeAnalyzer initialization with custom config."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        assert analyzer.config == config
    
    def test_code_analyzer_analyze_file_all_enabled(self):
        """Test CodeAnalyzer analyze_file with all analysis enabled."""
        analyzer = CodeAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyzer.analyze_file(f.name)
                assert isinstance(result, AnalysisResult)
                assert isinstance(result.security_issues, list)
                assert isinstance(result.performance_issues, list)
                assert isinstance(result.quality_issues, list)
                assert isinstance(result.coverage_data, dict)
            finally:
                safe_unlink(f.name)
    
    def test_code_analyzer_analyze_file_security_disabled(self):
        """Test CodeAnalyzer analyze_file with security analysis disabled."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyzer.analyze_file(f.name)
                assert isinstance(result, AnalysisResult)
                # Security issues should be empty when disabled
                assert result.security_issues == []
            finally:
                safe_unlink(f.name)
    
    def test_code_analyzer_analyze_directory_nonexistent(self):
        """Test CodeAnalyzer analyze_directory with nonexistent directory."""
        analyzer = CodeAnalyzer()
        results = analyzer.analyze_directory("nonexistent_directory")
        assert results == []
    
    def test_code_analyzer_analyze_directory_existing(self):
        """Test CodeAnalyzer analyze_directory with existing directory."""
        analyzer = CodeAnalyzer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def test_func():\n    pass")
            
            results = analyzer.analyze_directory(temp_dir)
            assert len(results) == 1
            assert isinstance(results[0], AnalysisResult)
    
    def test_code_analyzer_generate_summary_empty(self):
        """Test CodeAnalyzer generate_summary with empty results."""
        analyzer = CodeAnalyzer()
        summary = analyzer.generate_summary([])
        
        assert summary["total_files"] == 0
        assert summary["total_security_issues"] == 0
        assert summary["total_performance_issues"] == 0
        assert summary["total_quality_issues"] == 0
        assert summary["total_coverage_issues"] == 0
        assert summary["total_issues"] == 0
        assert summary["average_execution_time"] == 0
    
    def test_code_analyzer_generate_summary_with_results(self):
        """Test CodeAnalyzer generate_summary with results."""
        analyzer = CodeAnalyzer()
        
        # Create mock results
        result1 = AnalysisResult()
        result1.security_issues = ["issue1", "issue2"]
        result1.performance_issues = ["perf1"]
        result1.quality_issues = ["qual1"]
        result1.coverage_data = {"file1.py": 85.0}
        result1.execution_time = 1.5
        
        result2 = AnalysisResult()
        result2.security_issues = ["issue3"]
        result2.performance_issues = []
        result2.quality_issues = ["qual2", "qual3"]
        result2.coverage_data = {"file2.py": 90.0}
        result2.execution_time = 2.5
        
        summary = analyzer.generate_summary([result1, result2])
        
        assert summary["total_files"] == 2
        assert summary["total_security_issues"] == 3
        assert summary["total_performance_issues"] == 1
        assert summary["total_quality_issues"] == 3
        assert summary["total_coverage_issues"] == 2
        assert summary["total_issues"] == 7
        assert summary["average_execution_time"] == 2.0  # (1.5 + 2.5) / 2
    
    @patch('src.ai_guard.analyzer.run_lint_check')
    @patch('src.ai_guard.analyzer.run_type_check')
    @patch('src.ai_guard.analyzer.run_security_check')
    @patch('src.ai_guard.analyzer.run_coverage_check')
    def test_code_analyzer_run_all_checks(self, mock_coverage, mock_security, mock_type, mock_lint):
        """Test CodeAnalyzer run_all_checks method."""
        # Setup mocks
        mock_lint.return_value = (Mock(), None)
        mock_type.return_value = (Mock(), None)
        mock_security.return_value = (Mock(), None)
        mock_coverage.return_value = (Mock(), None)
        
        analyzer = CodeAnalyzer()
        results = analyzer.run_all_checks(["test.py"])
        
        assert len(results) == 4
        mock_lint.assert_called_once_with(["test.py"])
        mock_type.assert_called_once_with(["test.py"])
        mock_security.assert_called_once()
        mock_coverage.assert_called_once_with(80)  # Default min_coverage


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyze_code(f.name)
                assert isinstance(result, AnalysisResult)
            finally:
                safe_unlink(f.name)
    
    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyze_security(f.name)
                assert isinstance(result, list)
            finally:
                safe_unlink(f.name)
    
    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyze_performance(f.name)
                assert isinstance(result, list)
            finally:
                safe_unlink(f.name)
    
    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyze_quality(f.name)
                assert isinstance(result, list)
            finally:
                safe_unlink(f.name)
    
    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass")
            f.flush()
            
            try:
                result = analyze_coverage(f.name)
                assert isinstance(result, dict)
            finally:
                safe_unlink(f.name)




class TestRunLintCheck:
    """Test run_lint_check function."""
    
    @patch('subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test run_lint_check with successful execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        result, sarif = run_lint_check(["test.py"])
        assert result is not None
        assert sarif is None
    
    @patch('subprocess.run')
    def test_run_lint_check_with_issues(self, mock_run):
        """Test run_lint_check with linting issues."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "test.py:1:1: E501 line too long"
        mock_run.return_value = mock_process
        
        result, sarif = run_lint_check(["test.py"])
        assert result is not None
        assert hasattr(result, 'passed')


class TestRunTypeCheck:
    """Test run_type_check function."""
    
    @patch('subprocess.run')
    def test_run_type_check_success(self, mock_run):
        """Test run_type_check with successful execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        result, sarif = run_type_check(["test.py"])
        assert result is not None
        assert sarif is None
    
    @patch('subprocess.run')
    def test_run_type_check_with_issues(self, mock_run):
        """Test run_type_check with type issues."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "test.py:5: error: Incompatible return type"
        mock_run.return_value = mock_process
        
        result, sarif = run_type_check(["test.py"])
        assert result is not None
        assert hasattr(result, 'passed')


class TestRunSecurityCheck:
    """Test run_security_check function."""
    
    @patch('subprocess.run')
    def test_run_security_check_success(self, mock_run):
        """Test run_security_check with successful execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        result, sarif = run_security_check()
        assert result is not None
        assert sarif is None
    
    @patch('subprocess.run')
    def test_run_security_check_with_issues(self, mock_run):
        """Test run_security_check with security issues."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = '{"results": [{"filename": "test.py", "line_number": 10, "issue_severity": "HIGH", "issue_confidence": "MEDIUM", "issue_text": "Test issue", "test_id": "B101"}]}'
        mock_run.return_value = mock_process
        
        result, sarif = run_security_check()
        assert result is not None
        assert hasattr(result, 'passed')


class TestRunCoverageCheck:
    """Test run_coverage_check function."""
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_success(self, mock_cov_percent):
        """Test run_coverage_check with sufficient coverage."""
        mock_cov_percent.return_value = 85
        
        result, sarif = run_coverage_check(80)
        assert result is not None
        assert result.passed is True
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_failure(self, mock_cov_percent):
        """Test run_coverage_check with insufficient coverage."""
        mock_cov_percent.return_value = 75
        
        result, sarif = run_coverage_check(80)
        assert result is not None
        assert result.passed is False
    
    @patch('src.ai_guard.analyzer.cov_percent')
    def test_run_coverage_check_no_coverage(self, mock_cov_percent):
        """Test run_coverage_check with no coverage data."""
        mock_cov_percent.return_value = None
        
        result, sarif = run_coverage_check(80)
        assert result is not None
        assert result.passed is False


class TestGenerateReport:
    """Test generate_report function."""
    
    def test_generate_report_json(self):
        """Test generate_report with JSON format."""
        # Create a mock AnalysisResult
        mock_result = Mock()
        mock_result.to_dict.return_value = {"issues": 5}
        mock_result.get_total_issues.return_value = 5
        
        result = generate_report(mock_result, "json")
        assert "issues" in result
        assert "5" in result
    
    def test_generate_report_html(self):
        """Test generate_report with HTML format."""
        # Create a mock AnalysisResult
        mock_result = Mock()
        mock_result.get_total_issues.return_value = 3
        
        result = generate_report(mock_result, "html")
        assert "<html>" in result
        assert "3" in result
    
    def test_generate_report_sarif(self):
        """Test generate_report with SARIF format."""
        # Create a mock AnalysisResult
        mock_result = Mock()
        mock_result.get_total_issues.return_value = 2
        
        result = generate_report(mock_result, "xml")
        assert "<report>" in result
        assert "2" in result


class TestRunAnalysis:
    """Test run_analysis function."""
    
    @patch('src.ai_guard.analyzer.CodeAnalyzer')
    def test_run_analysis(self, mock_analyzer_class):
        """Test run_analysis function."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create a proper mock result
        mock_result = Mock()
        mock_result.security_issues = []
        mock_result.performance_issues = []
        mock_result.quality_issues = []
        mock_result.coverage_data = {}
        mock_result.execution_time = 0
        mock_analyzer.analyze_file.return_value = mock_result
        
        # Create a mock config
        mock_config = Mock()
        
        results = run_analysis(["test.py"], mock_config)
        assert hasattr(results, 'security_issues')  # Should return AnalysisResult
        mock_analyzer.analyze_file.assert_called_once_with("test.py")
