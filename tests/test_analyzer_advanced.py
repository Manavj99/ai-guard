"""Advanced tests for analyzer.py module to improve coverage."""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.ai_guard.analyzer import (
    _normalize_rule_id,
    _norm,
    _parse_bandit_output,
    _write_reports,
    _run_tool,
    _get_git_diff,
    _get_changed_files,
    _parse_sarif_output,
    ArtifactLocation,
    Region,
    PhysicalLocation,
    Location,
    default_gates,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    analyze_files_parallel,
    benchmark_analyzer,
    analyze_code,
    analyze_security,
    analyze_performance,
    analyze_quality,
    analyze_coverage,
    run_analysis,
)
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestNormalizeRuleId:
    """Test _normalize_rule_id function."""

    def test_normalize_rule_id_with_prefix(self):
        """Test normalizing rule ID with tool prefix."""
        assert _normalize_rule_id("flake8:E501") == "E501"
        assert _normalize_rule_id("mypy:name-defined") == "name-defined"

    def test_normalize_rule_id_without_prefix(self):
        """Test normalizing rule ID without tool prefix."""
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

    def test_norm_invalid_bytes(self):
        """Test _norm with invalid bytes."""
        result = _norm(b"\xff\xfe")
        assert isinstance(result, str)


class TestParseBanditOutput:
    """Test _parse_bandit_output function."""

    def test_parse_bandit_output_with_bandit_keyword(self):
        """Test parsing bandit output with 'bandit' keyword."""
        output = "bandit found issues"
        results = _parse_bandit_output(output)
        assert len(results) == 1
        assert results[0].rule_id == "bandit:B101"
        assert results[0].message == "Sample bandit issue"

    def test_parse_bandit_output_without_bandit_keyword(self):
        """Test parsing bandit output without 'bandit' keyword."""
        output = "some other output"
        results = _parse_bandit_output(output)
        assert results == []


class TestWriteReports:
    """Test _write_reports function."""

    def test_write_reports_sarif_format(self):
        """Test writing SARIF format reports."""
        issues = [
            {
                "rule_id": "test-rule",
                "level": "warning",
                "message": "Test issue",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "sarif", "report_path": "test.sarif"}

        with patch("src.ai_guard.analyzer.write_sarif") as mock_write_sarif:
            _write_reports(issues, config)
            mock_write_sarif.assert_called_once()

    def test_write_reports_json_format(self):
        """Test writing JSON format reports."""
        issues = [
            {
                "rule_id": "test-rule",
                "level": "warning",
                "message": "Test issue",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "json", "report_path": "test.json"}

        with patch("src.ai_guard.analyzer.write_json") as mock_write_json:
            _write_reports(issues, config)
            mock_write_json.assert_called_once()

    def test_write_reports_html_format(self):
        """Test writing HTML format reports."""
        issues = [
            {
                "rule_id": "test-rule",
                "level": "warning",
                "message": "Test issue",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "html", "report_path": "test.html"}

        with patch("src.ai_guard.analyzer.write_html") as mock_write_html:
            _write_reports(issues, config)
            mock_write_html.assert_called_once()

    def test_write_reports_exception_handling(self):
        """Test _write_reports exception handling."""
        issues = []
        config = {"report_format": "unknown"}

        with patch("builtins.print") as mock_print:
            _write_reports(issues, config)
            # Should not raise exception, just print warning


class TestRunTool:
    """Test _run_tool function."""

    def test_run_tool_success(self):
        """Test successful tool execution."""
        with patch(
            "src.ai_guard.utils.subprocess_runner.run_cmd", return_value=(0, "output")
        ):
            result = _run_tool(["echo", "test"])
            assert result.returncode == 0
            assert result.stdout == "output"

    def test_run_tool_error(self):
        """Test tool execution error."""
        from src.ai_guard.utils.subprocess_runner import ToolExecutionError

        with patch(
            "src.ai_guard.utils.subprocess_runner.run_cmd",
            side_effect=ToolExecutionError("Tool error"),
        ):
            result = _run_tool(["invalid", "command"])
            assert result.returncode == 1
            assert "Tool error" in result.stderr


class TestGitFunctions:
    """Test git-related functions."""

    def test_get_git_diff_success(self):
        """Test successful git diff."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "diff output"
            result = _get_git_diff()
            assert result == "diff output"

    def test_get_git_diff_error(self):
        """Test git diff error."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            result = _get_git_diff()
            assert result == ""

    def test_get_changed_files_success(self):
        """Test successful git changed files."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "file1.py\nfile2.py\n"
            result = _get_changed_files()
            assert result == ["file1.py", "file2.py"]

    def test_get_changed_files_error(self):
        """Test git changed files error."""
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = _get_changed_files()
            assert result == []


class TestParseSarifOutput:
    """Test _parse_sarif_output function."""

    def test_parse_sarif_output_valid(self):
        """Test parsing valid SARIF output."""
        sarif_data = {
            "runs": [
                {
                    "results": [
                        {
                            "ruleId": "test-rule",
                            "message": {"text": "Test message"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "test.py"},
                                        "region": {"startLine": 10},
                                    }
                                }
                            ],
                        }
                    ]
                }
            ]
        }
        output = json.dumps(sarif_data)
        results = _parse_sarif_output(output)
        assert len(results) == 1
        assert results[0]["ruleId"] == "test-rule"

    def test_parse_sarif_output_invalid_json(self):
        """Test parsing invalid JSON."""
        output = "invalid json"
        results = _parse_sarif_output(output)
        assert results == []

    def test_parse_sarif_output_empty(self):
        """Test parsing empty SARIF output."""
        output = "{}"
        results = _parse_sarif_output(output)
        assert results == []


class TestDataclasses:
    """Test dataclass definitions."""

    def test_artifact_location(self):
        """Test ArtifactLocation dataclass."""
        location = ArtifactLocation(uri="test.py")
        assert location.uri == "test.py"

    def test_region(self):
        """Test Region dataclass."""
        region = Region(start_line=10, start_column=5, end_line=15, end_column=20)
        assert region.start_line == 10
        assert region.start_column == 5
        assert region.end_line == 15
        assert region.end_column == 20

    def test_physical_location(self):
        """Test PhysicalLocation dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        location = PhysicalLocation(artifact_location=artifact, region=region)
        assert location.artifact_location.uri == "test.py"
        assert location.region.start_line == 10

    def test_location(self):
        """Test Location dataclass."""
        artifact = ArtifactLocation(uri="test.py")
        region = Region(start_line=10)
        physical = PhysicalLocation(artifact_location=artifact, region=region)
        location = Location(physical_location=physical)
        assert location.physical_location.artifact_location.uri == "test.py"


class TestDefaultGates:
    """Test default gates configuration."""

    def test_default_gates(self):
        """Test default gates configuration."""
        assert "min_coverage" in default_gates
        assert default_gates["min_coverage"] == 80


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_security_analyzer_init(self):
        """Test SecurityAnalyzer initialization."""
        analyzer = SecurityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.rules == []
        assert hasattr(analyzer, "_cache")
        assert hasattr(analyzer, "_lock")

    def test_security_analyzer_load_rules(self):
        """Test loading security rules."""
        analyzer = SecurityAnalyzer()
        analyzer.load_rules()
        assert analyzer.rules == ["rule1", "rule2", "rule3"]

    def test_security_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = SecurityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_security_analyzer_analyze_file_with_issues(self):
        """Test analyzing file with security issues."""
        analyzer = SecurityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nos.system('ls')\neval('code')\n")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert len(result) > 0
            assert any("os.system" in issue for issue in result)
            assert any("eval()" in issue for issue in result)
        finally:
            os.unlink(temp_file)

    def test_security_analyzer_add_issue(self):
        """Test adding security issue."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "high")
        assert len(analyzer.issues) == 1
        assert analyzer.issues[0]["file"] == "test.py"
        assert analyzer.issues[0]["line"] == 10
        assert analyzer.issues[0]["message"] == "Test issue"
        assert analyzer.issues[0]["severity"] == "high"

    def test_security_analyzer_get_issues(self):
        """Test getting security issues."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "high")
        issues = analyzer.get_issues()
        assert len(issues) == 1

    def test_security_analyzer_clear_issues(self):
        """Test clearing security issues."""
        analyzer = SecurityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "high")
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    def test_performance_analyzer_init(self):
        """Test PerformanceAnalyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.issues == []
        assert analyzer.benchmarks == {}
        assert hasattr(analyzer, "_cache")
        assert hasattr(analyzer, "_lock")

    def test_performance_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_performance_analyzer_analyze_file_with_issues(self):
        """Test analyzing file with performance issues."""
        analyzer = PerformanceAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("for i in range(1000000):\n    pass\ntime.sleep(1)\n")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert len(result) > 0
            assert any("large range" in issue for issue in result)
            assert any("sleep" in issue for issue in result)
        finally:
            os.unlink(temp_file)

    def test_performance_analyzer_add_issue(self):
        """Test adding performance issue."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "medium")
        assert len(analyzer.issues) == 1

    def test_performance_analyzer_get_issues(self):
        """Test getting performance issues."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "medium")
        issues = analyzer.get_issues()
        assert len(issues) == 1

    def test_performance_analyzer_clear_issues(self):
        """Test clearing performance issues."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "medium")
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestQualityAnalyzer:
    """Test QualityAnalyzer class."""

    def test_quality_analyzer_init(self):
        """Test QualityAnalyzer initialization."""
        analyzer = QualityAnalyzer()
        assert analyzer.issues == []
        assert analyzer.metrics == {}
        assert hasattr(analyzer, "_cache")
        assert hasattr(analyzer, "_lock")

    def test_quality_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = QualityAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == []

    def test_quality_analyzer_analyze_file_with_issues(self):
        """Test analyzing file with quality issues."""
        analyzer = QualityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: Fix this\n# FIXME: Bad code\nprint('hello')\n")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert len(result) > 0
            assert any("TODO" in issue for issue in result)
            assert any("FIXME" in issue for issue in result)
        finally:
            os.unlink(temp_file)

    def test_quality_analyzer_add_issue(self):
        """Test adding quality issue."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "low")
        assert len(analyzer.issues) == 1

    def test_quality_analyzer_get_issues(self):
        """Test getting quality issues."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "low")
        issues = analyzer.get_issues()
        assert len(issues) == 1

    def test_quality_analyzer_clear_issues(self):
        """Test clearing quality issues."""
        analyzer = QualityAnalyzer()
        analyzer.add_issue("test.py", 10, "Test issue", "low")
        analyzer.clear_issues()
        assert analyzer.issues == []


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_coverage_analyzer_init(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.coverage_data == {}
        assert analyzer.threshold == 80.0
        assert hasattr(analyzer, "_cache")
        assert hasattr(analyzer, "_lock")

    def test_coverage_analyzer_analyze_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze_file("nonexistent.py")
        assert result == {}

    def test_coverage_analyzer_analyze_file_with_coverage(self):
        """Test analyzing file with coverage data."""
        analyzer = CoverageAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, dict)
            assert temp_file in result
        finally:
            os.unlink(temp_file)

    def test_coverage_analyzer_set_threshold(self):
        """Test setting coverage threshold."""
        analyzer = CoverageAnalyzer()
        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0

    def test_coverage_analyzer_get_coverage_data(self):
        """Test getting coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.0}
        data = analyzer.get_coverage_data()
        assert data == {"test.py": 85.0}

    def test_coverage_analyzer_clear_data(self):
        """Test clearing coverage data."""
        analyzer = CoverageAnalyzer()
        analyzer.coverage_data = {"test.py": 85.0}
        analyzer.clear_data()
        assert analyzer.coverage_data == {}


class TestCodeAnalyzerAdvanced:
    """Test advanced CodeAnalyzer functionality."""

    def test_code_analyzer_analyze_file_with_all_analyzers_disabled(self):
        """Test analyzing file with all analyzers disabled."""
        from src.ai_guard.analyzer import AnalysisConfig

        config = AnalysisConfig(
            enable_security_analysis=False,
            enable_performance_analysis=False,
            enable_quality_analysis=False,
            enable_coverage_analysis=False,
        )
        analyzer = CodeAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            result = analyzer.analyze_file(temp_file)
            assert result.security_issues == []
            assert result.performance_issues == []
            assert result.quality_issues == []
            assert result.coverage_data == {}
        finally:
            os.unlink(temp_file)

    def test_code_analyzer_get_performance_metrics(self):
        """Test getting performance metrics."""
        analyzer = CodeAnalyzer()
        metrics = analyzer.get_performance_metrics()
        assert isinstance(metrics, dict)

    def test_code_analyzer_clear_cache(self):
        """Test clearing cache."""
        analyzer = CodeAnalyzer()
        analyzer.clear_cache()
        # Should not raise exception

    def test_code_analyzer_get_cache_stats(self):
        """Test getting cache statistics."""
        analyzer = CodeAnalyzer()
        stats = analyzer.get_cache_stats()
        assert isinstance(stats, dict)
        assert "file_cache" in stats
        assert "security_cache" in stats
        assert "performance_cache" in stats
        assert "quality_cache" in stats
        assert "coverage_cache" in stats
        assert "total_cache" in stats


class TestAnalyzeFilesParallel:
    """Test analyze_files_parallel function."""

    def test_analyze_files_parallel_small_list(self):
        """Test analyzing small list of files (sequential)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            results = analyze_files_parallel([temp_file])
            assert len(results) == 1
            assert isinstance(results[0], type(analyze_code(temp_file)))
        finally:
            os.unlink(temp_file)

    def test_analyze_files_parallel_large_list(self):
        """Test analyzing large list of files (parallel)."""
        temp_files = []
        try:
            # Create multiple temp files
            for i in range(6):
                f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
                f.write(f"print('hello {i}')\n")
                f.close()
                temp_files.append(f.name)

            results = analyze_files_parallel(temp_files, max_workers=2)
            assert len(results) == 6
            assert all(
                isinstance(result, type(analyze_code(temp_files[0])))
                for result in results
            )
        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)

    def test_analyze_files_parallel_with_exception(self):
        """Test analyzing files with exception handling."""
        results = analyze_files_parallel(["nonexistent.py"], max_workers=1)
        assert len(results) == 1
        assert len(results[0].security_issues) > 0


class TestBenchmarkAnalyzer:
    """Test benchmark_analyzer function."""

    def test_benchmark_analyzer(self):
        """Test benchmarking analyzer performance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            results = benchmark_analyzer([temp_file], iterations=2)
            assert isinstance(results, dict)
            assert "sequential_time" in results
            assert "parallel_time" in results
            assert "speedup" in results
            assert "files_per_second_sequential" in results
            assert "files_per_second_parallel" in results
        finally:
            os.unlink(temp_file)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_analyze_code(self):
        """Test analyze_code function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            result = analyze_code(temp_file)
            assert hasattr(result, "security_issues")
            assert hasattr(result, "performance_issues")
            assert hasattr(result, "quality_issues")
            assert hasattr(result, "coverage_data")
        finally:
            os.unlink(temp_file)

    def test_analyze_security(self):
        """Test analyze_security function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nos.system('ls')\n")
            temp_file = f.name

        try:
            result = analyze_security(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_performance(self):
        """Test analyze_performance function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("for i in range(1000000):\n    pass\n")
            temp_file = f.name

        try:
            result = analyze_performance(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_quality(self):
        """Test analyze_quality function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: Fix this\nprint('hello')\n")
            temp_file = f.name

        try:
            result = analyze_quality(temp_file)
            assert isinstance(result, list)
        finally:
            os.unlink(temp_file)

    def test_analyze_coverage(self):
        """Test analyze_coverage function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            result = analyze_coverage(temp_file)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_file)

    def test_run_analysis(self):
        """Test run_analysis function."""
        from src.ai_guard.analyzer import AnalysisConfig

        config = AnalysisConfig()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name

        try:
            result = run_analysis([temp_file], config)
            assert hasattr(result, "security_issues")
            assert hasattr(result, "performance_issues")
            assert hasattr(result, "quality_issues")
            assert hasattr(result, "coverage_data")
        finally:
            os.unlink(temp_file)
