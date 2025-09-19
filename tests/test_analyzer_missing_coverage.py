"""Additional tests for analyzer.py to improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock, Mock
from pathlib import Path

from src.ai_guard.analyzer import (
    RuleIdStyle, _rule_style, _make_rule_id, _strict_subprocess_fail,
    _to_text, ArtifactLocation, Region, PhysicalLocation, Location,
    _normalize_rule_id, _norm, _coverage_percent_from_xml, cov_percent,
    _parse_flake8_output, _parse_mypy_output, run_lint_check, run_type_check,
    _parse_bandit_json, _parse_bandit_output,
    AnalysisConfig, AnalysisResult, SecurityAnalyzer, PerformanceAnalyzer,
    QualityAnalyzer, CoverageAnalyzer, CodeAnalyzer,
    analyze_code, analyze_security, analyze_performance, analyze_quality,
    analyze_coverage, generate_report, run_analysis
)


class TestAnalysisConfig:
    """Test AnalysisConfig class."""
    
    def test_analysis_config_initialization(self):
        """Test analysis config initialization."""
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True
        assert config.output_format == "json"
        assert config.verbose is False
    
    def test_analysis_config_custom_values(self):
        """Test analysis config with custom values."""
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
    
    def test_analysis_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AnalysisConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["enable_security_analysis"] is True
        assert config_dict["enable_performance_analysis"] is True
        assert config_dict["enable_quality_analysis"] is True
        assert config_dict["enable_coverage_analysis"] is True
        assert config_dict["output_format"] == "json"
        assert config_dict["verbose"] is False
    
    def test_analysis_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "enable_security_analysis": False,
            "enable_performance_analysis": True,
            "enable_quality_analysis": False,
            "enable_coverage_analysis": True,
            "output_format": "xml",
            "verbose": True
        }
        
        config = AnalysisConfig.from_dict(config_dict)
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is False
        assert config.enable_coverage_analysis is True
        assert config.output_format == "xml"
        assert config.verbose is True


class TestAnalysisResult:
    """Test AnalysisResult class."""
    
    def test_analysis_result_initialization(self):
        """Test analysis result initialization."""
        result = AnalysisResult()
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.summary == {}
        assert result.execution_time == 0.0
    
    def test_analysis_result_with_data(self):
        """Test analysis result with data."""
        result = AnalysisResult()
        result.security_issues = ["issue1", "issue2"]
        result.performance_issues = ["perf1"]
        result.quality_issues = ["quality1", "quality2", "quality3"]
        result.coverage_data = {"file1.py": 85.5}
        result.summary = {"total_issues": 6}
        result.execution_time = 1.5
        
        assert len(result.security_issues) == 2
        assert len(result.performance_issues) == 1
        assert len(result.quality_issues) == 3
        assert result.coverage_data["file1.py"] == 85.5
        assert result.summary["total_issues"] == 6
        assert result.execution_time == 1.5
    
    def test_analysis_result_get_total_issues(self):
        """Test getting total issues count."""
        result = AnalysisResult()
        result.security_issues = ["issue1", "issue2"]
        result.performance_issues = ["perf1"]
        result.quality_issues = ["quality1"]
        
        total = result.get_total_issues()
        assert total == 4
    
    def test_analysis_result_get_total_issues_empty(self):
        """Test getting total issues count when empty."""
        result = AnalysisResult()
        total = result.get_total_issues()
        assert total == 0
    
    def test_analysis_result_to_dict(self):
        """Test converting result to dictionary."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        result.performance_issues = ["perf1"]
        result.quality_issues = ["quality1"]
        result.coverage_data = {"file1.py": 85.5}
        result.summary = {"total_issues": 3}
        result.execution_time = 1.5
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["security_issues"] == ["issue1"]
        assert result_dict["performance_issues"] == ["perf1"]
        assert result_dict["quality_issues"] == ["quality1"]
        assert result_dict["coverage_data"] == {"file1.py": 85.5}
        assert result_dict["summary"] == {"total_issues": 3}
        assert result_dict["execution_time"] == 1.5


class TestCodeAnalyzer:
    """Test CodeAnalyzer class."""
    
    def test_code_analyzer_initialization(self):
        """Test code analyzer initialization."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        assert analyzer.config == config
        assert analyzer.security_analyzer is not None
        assert analyzer.performance_analyzer is not None
        assert analyzer.quality_analyzer is not None
        assert analyzer.coverage_analyzer is not None
    
    def test_code_analyzer_analyze_file(self):
        """Test analyzing a single file."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            assert result.execution_time >= 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_code_analyzer_analyze_file_nonexistent(self):
        """Test analyzing non-existent file."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        result = analyzer.analyze_file("nonexistent.py")
        assert isinstance(result, AnalysisResult)
        assert result.get_total_issues() > 0  # Should have file not found issues
    
    def test_code_analyzer_analyze_directory(self):
        """Test analyzing a directory."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = os.path.join(temp_dir, "test1.py")
            test_file2 = os.path.join(temp_dir, "test2.py")
            
            with open(test_file1, 'w') as f:
                f.write("def func1():\n    return True\n")
            
            with open(test_file2, 'w') as f:
                f.write("def func2():\n    return False\n")
            
            results = analyzer.analyze_directory(temp_dir)
            assert len(results) == 2
            assert all(isinstance(r, AnalysisResult) for r in results)
    
    def test_code_analyzer_analyze_directory_empty(self):
        """Test analyzing empty directory."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            results = analyzer.analyze_directory(temp_dir)
            assert results == []
    
    def test_code_analyzer_analyze_directory_nonexistent(self):
        """Test analyzing non-existent directory."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        results = analyzer.analyze_directory("nonexistent_dir")
        assert results == []
    
    def test_code_analyzer_generate_summary(self):
        """Test generating analysis summary."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)
        
        # Create mock results
        result1 = AnalysisResult()
        result1.security_issues = ["issue1", "issue2"]
        result1.performance_issues = ["perf1"]
        result1.execution_time = 1.0
        
        result2 = AnalysisResult()
        result2.security_issues = ["issue3"]
        result2.quality_issues = ["quality1"]
        result2.execution_time = 0.5
        
        results = [result1, result2]
        summary = analyzer.generate_summary(results)
        
        assert summary["total_files"] == 2
        assert summary["total_security_issues"] == 3
        assert summary["total_performance_issues"] == 1
        assert summary["total_quality_issues"] == 1
        assert summary["total_coverage_issues"] == 0
        assert summary["total_issues"] == 5
        assert summary["average_execution_time"] == 0.75


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""
    
    def test_security_analyzer_initialization(self):
        """Test security analyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.rules == []
    
    def test_security_analyzer_load_rules(self):
        """Test loading security rules."""
        analyzer = SecurityAnalyzer()
        analyzer.load_rules()
        assert len(analyzer.rules) > 0
    
    def test_security_analyzer_analyze_file(self):
        """Test analyzing file for security issues."""
        analyzer = SecurityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nos.system('rm -rf /')\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert isinstance(issues, list)
            # Should detect dangerous os.system call
            assert len(issues) > 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_security_analyzer_analyze_file_safe_code(self):
        """Test analyzing file with safe code."""
        analyzer = SecurityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def safe_func():\n    return 'safe'\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert isinstance(issues, list)
            # Should have no security issues
            assert len(issues) == 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_security_analyzer_analyze_file_nonexistent(self):
        """Test analyzing non-existent file."""
        analyzer = SecurityAnalyzer()
        
        issues = analyzer.analyze_file("nonexistent.py")
        assert isinstance(issues, list)
        assert len(issues) > 0  # Should have file not found issue
    
    def test_security_analyzer_add_issue(self):
        """Test adding security issue."""
        analyzer = SecurityAnalyzer()
        
        analyzer.add_issue("test.py", 10, "Dangerous function call", "HIGH")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["file"] == "test.py"
        assert analyzer.issues[0]["line"] == 10
        assert analyzer.issues[0]["message"] == "Dangerous function call"
        assert analyzer.issues[0]["severity"] == "HIGH"
    
    def test_security_analyzer_get_issues(self):
        """Test getting security issues."""
        analyzer = SecurityAnalyzer()
        
        analyzer.add_issue("test1.py", 10, "Issue 1", "HIGH")
        analyzer.add_issue("test2.py", 20, "Issue 2", "MEDIUM")
        
        issues = analyzer.get_issues()
        assert len(issues) == 2
    
    def test_security_analyzer_clear_issues(self):
        """Test clearing security issues."""
        analyzer = SecurityAnalyzer()
        
        analyzer.add_issue("test.py", 10, "Issue", "HIGH")
        assert len(analyzer.issues) == 1
        
        analyzer.clear_issues()
        assert len(analyzer.issues) == 0


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""
    
    def test_performance_analyzer_initialization(self):
        """Test performance analyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.issues == []
        assert analyzer.benchmarks == {}
    
    def test_performance_analyzer_analyze_file(self):
        """Test analyzing file for performance issues."""
        analyzer = PerformanceAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def slow_func():\n    for i in range(1000000):\n        pass\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert isinstance(issues, list)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_performance_analyzer_analyze_file_nonexistent(self):
        """Test analyzing non-existent file."""
        analyzer = PerformanceAnalyzer()
        
        issues = analyzer.analyze_file("nonexistent.py")
        assert isinstance(issues, list)
        assert len(issues) > 0  # Should have file not found issue
    
    def test_performance_analyzer_add_issue(self):
        """Test adding performance issue."""
        analyzer = PerformanceAnalyzer()
        
        analyzer.add_issue("test.py", 10, "Slow operation", "MEDIUM")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["file"] == "test.py"
        assert analyzer.issues[0]["line"] == 10
        assert analyzer.issues[0]["message"] == "Slow operation"
        assert analyzer.issues[0]["severity"] == "MEDIUM"
    
    def test_performance_analyzer_get_issues(self):
        """Test getting performance issues."""
        analyzer = PerformanceAnalyzer()
        
        analyzer.add_issue("test1.py", 10, "Issue 1", "HIGH")
        analyzer.add_issue("test2.py", 20, "Issue 2", "LOW")
        
        issues = analyzer.get_issues()
        assert len(issues) == 2
    
    def test_performance_analyzer_clear_issues(self):
        """Test clearing performance issues."""
        analyzer = PerformanceAnalyzer()
        
        analyzer.add_issue("test.py", 10, "Issue", "HIGH")
        assert len(analyzer.issues) == 1
        
        analyzer.clear_issues()
        assert len(analyzer.issues) == 0


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""
    
    def test_quality_analyzer_initialization(self):
        """Test quality analyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.metrics == {}
    
    def test_quality_analyzer_analyze_file(self):
        """Test analyzing file for quality issues."""
        analyzer = QualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def func():\n    x = 1\n    y = 2\n    return x + y\n")
            temp_file = f.name
        
        try:
            issues = analyzer.analyze_file(temp_file)
            assert isinstance(issues, list)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_quality_analyzer_analyze_file_nonexistent(self):
        """Test analyzing non-existent file."""
        analyzer = QualityAnalyzer()
        
        issues = analyzer.analyze_file("nonexistent.py")
        assert isinstance(issues, list)
        assert len(issues) > 0  # Should have file not found issue
    
    def test_quality_analyzer_add_issue(self):
        """Test adding quality issue."""
        analyzer = QualityAnalyzer()
        
        analyzer.add_issue("test.py", 10, "Code style issue", "LOW")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["file"] == "test.py"
        assert analyzer.issues[0]["line"] == 10
        assert analyzer.issues[0]["message"] == "Code style issue"
        assert analyzer.issues[0]["severity"] == "LOW"
    
    def test_quality_analyzer_get_issues(self):
        """Test getting quality issues."""
        analyzer = QualityAnalyzer()
        
        analyzer.add_issue("test1.py", 10, "Issue 1", "HIGH")
        analyzer.add_issue("test2.py", 20, "Issue 2", "MEDIUM")
        
        issues = analyzer.get_issues()
        assert len(issues) == 2
    
    def test_quality_analyzer_clear_issues(self):
        """Test clearing quality issues."""
        analyzer = QualityAnalyzer()
        
        analyzer.add_issue("test.py", 10, "Issue", "HIGH")
        assert len(analyzer.issues) == 1
        
        analyzer.clear_issues()
        assert len(analyzer.issues) == 0


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""
    
    def test_coverage_analyzer_initialization(self):
        """Test coverage analyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}
        assert analyzer.threshold == 80.0
    
    def test_coverage_analyzer_analyze_file(self):
        """Test analyzing file for coverage."""
        analyzer = CoverageAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def func():\n    return True\n")
            temp_file = f.name
        
        try:
            coverage = analyzer.analyze_file(temp_file)
            assert isinstance(coverage, dict)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_coverage_analyzer_analyze_file_nonexistent(self):
        """Test analyzing non-existent file."""
        analyzer = CoverageAnalyzer()
        
        coverage = analyzer.analyze_file("nonexistent.py")
        assert isinstance(coverage, dict)
        assert coverage == {}
    
    def test_coverage_analyzer_set_threshold(self):
        """Test setting coverage threshold."""
        analyzer = CoverageAnalyzer()
        
        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0
    
    def test_coverage_analyzer_get_coverage_data(self):
        """Test getting coverage data."""
        analyzer = CoverageAnalyzer()
        
        analyzer.coverage_data = {"file1.py": 85.5, "file2.py": 92.0}
        data = analyzer.get_coverage_data()
        assert data == {"file1.py": 85.5, "file2.py": 92.0}
    
    def test_coverage_analyzer_clear_data(self):
        """Test clearing coverage data."""
        analyzer = CoverageAnalyzer()
        
        analyzer.coverage_data = {"file1.py": 85.5}
        assert len(analyzer.coverage_data) == 1
        
        analyzer.clear_data()
        assert len(analyzer.coverage_data) == 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            result = analyze_code(temp_file)
            assert isinstance(result, AnalysisResult)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            issues = analyze_security(temp_file)
            assert isinstance(issues, list)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            issues = analyze_performance(temp_file)
            assert isinstance(issues, list)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            issues = analyze_quality(temp_file)
            assert isinstance(issues, list)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            coverage = analyze_coverage(temp_file)
            assert isinstance(coverage, dict)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_generate_report(self):
        """Test generate_report function."""
        result = AnalysisResult()
        result.security_issues = ["issue1"]
        result.performance_issues = ["perf1"]
        result.quality_issues = ["quality1"]
        
        report = generate_report(result, "json")
        assert isinstance(report, str)
        
        report = generate_report(result, "html")
        assert isinstance(report, str)
        
        report = generate_report(result, "xml")
        assert isinstance(report, str)
    
    def test_run_analysis(self):
        """Test run_analysis function."""
        config = AnalysisConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    return True\n")
            temp_file = f.name
        
        try:
            result = run_analysis([temp_file], config)
            assert isinstance(result, AnalysisResult)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
