"""Tests for main CodeAnalyzer class and functions."""

import pytest
import tempfile
import os

from src.ai_guard.analyzer import (
    CodeAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    run_analysis,
    generate_report,
)


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""

    def test_code_analyzer_init_default(self):
        """Test CodeAnalyzer initialization with default config."""
        analyzer = CodeAnalyzer()
        assert isinstance(analyzer.config, AnalysisConfig)
        assert analyzer.security_analyzer is not None
        assert analyzer.performance_analyzer is not None
        assert analyzer.quality_analyzer is not None
        assert analyzer.coverage_analyzer is not None

    def test_code_analyzer_init_custom(self):
        """Test CodeAnalyzer initialization with custom config."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        assert analyzer.config.enable_security_analysis is False

    def test_code_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        
        assert isinstance(result, AnalysisResult)
        assert result.security_issues == ["File not found: nonexistent.py"]
        assert result.performance_issues == ["File not found: nonexistent.py"]
        assert result.quality_issues == ["File not found: nonexistent.py"]
        assert result.coverage_data == {}

    def test_code_analyzer_analyze_file_with_security_disabled(self):
        """Test analyzing file with security analysis disabled."""
        config = AnalysisConfig(enable_security_analysis=False)
        analyzer = CodeAnalyzer(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nos.system('ls')\n")
            temp_file = f.name
        
        try:
            result = analyzer.analyze_file(temp_file)
            assert result.security_issues == []
            # Performance analyzer should still run but may not find issues in this simple case
            assert isinstance(result.performance_issues, list)
        finally:
            os.unlink(temp_file)

    def test_code_analyzer_analyze_directory_not_found(self):
        """Test analyzing non-existent directory."""
        analyzer = CodeAnalyzer()
        results = analyzer.analyze_directory("nonexistent_dir")
        assert results == []

    def test_code_analyzer_analyze_directory(self):
        """Test analyzing directory."""
        analyzer = CodeAnalyzer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("print('Hello World')\n")
            
            results = analyzer.analyze_directory(temp_dir)
            assert len(results) == 1
            assert isinstance(results[0], AnalysisResult)

    def test_code_analyzer_generate_summary(self):
        """Test generating summary from results."""
        analyzer = CodeAnalyzer()
        
        # Create mock results
        result1 = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.0
        )
        
        result2 = AnalysisResult(
            security_issues=["issue4"],
            performance_issues=["issue5"],
            quality_issues=["issue6"],
            coverage_data={"file2": 90.0},
            execution_time=2.0
        )
        
        summary = analyzer.generate_summary([result1, result2])
        
        assert summary["total_files"] == 2
        assert summary["total_security_issues"] == 2
        assert summary["total_performance_issues"] == 2
        assert summary["total_quality_issues"] == 2
        assert summary["average_execution_time"] == 1.5
        assert summary["total_coverage_issues"] == 2


class TestRunAnalysis:
    """Test run_analysis function."""

    def test_run_analysis_empty_files(self):
        """Test running analysis on empty file list."""
        config = AnalysisConfig()
        result = run_analysis([], config)
        
        assert isinstance(result, AnalysisResult)
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.execution_time == 0.0

    def test_run_analysis_with_files(self):
        """Test running analysis on files."""
        config = AnalysisConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello World')\n")
            temp_file = f.name
        
        try:
            result = run_analysis([temp_file], config)
            assert isinstance(result, AnalysisResult)
        finally:
            os.unlink(temp_file)


class TestGenerateReport:
    """Test generate_report function."""

    def test_generate_report_json(self):
        """Test generating JSON report."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5
        )
        
        report = generate_report(result, "json")
        assert isinstance(report, str)
        assert "issue1" in report

    def test_generate_report_dict(self):
        """Test generating dictionary report."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5
        )
        
        report = generate_report(result, "dict")
        assert isinstance(report, str)  # generate_report returns string representation
        assert "issue1" in report

    def test_generate_report_unknown_format(self):
        """Test generating report with unknown format."""
        result = AnalysisResult()
        report = generate_report(result, "unknown")
        assert isinstance(report, str)
