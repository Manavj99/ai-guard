"""Focused coverage tests for analyzer.py to achieve 80% coverage."""

import json
import os
import subprocess
import tempfile
from unittest.mock import Mock, patch
import pytest

# Direct imports to ensure the module is actually imported and covered
import src.ai_guard.analyzer as analyzer
from src.ai_guard.analyzer import (
    run,
    main,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    AnalysisResult,
    AnalysisConfig,
    _write_reports,
    _to_findings,
    _parse_coverage_output,
    _get_git_diff,
    _get_changed_files,
)
from src.ai_guard.report import GateResult
from src.ai_guard.sarif_report import SarifResult


class TestMainFunction:
    """Test the main run() function."""

    @patch("src.ai_guard.analyzer.load_config")
    @patch("src.ai_guard.analyzer.changed_python_files")
    @patch("src.ai_guard.analyzer.run_lint_check")
    @patch("src.ai_guard.analyzer.run_type_check")
    @patch("src.ai_guard.analyzer.run_security_check")
    @patch("src.ai_guard.analyzer.run_coverage_check")
    @patch("src.ai_guard.analyzer.summarize")
    @patch("src.ai_guard.analyzer.write_sarif")
    def test_run_function_complete(
        self,
        mock_write_sarif,
        mock_summarize,
        mock_coverage,
        mock_security,
        mock_type,
        mock_lint,
        mock_changed,
        mock_config,
    ):
        """Test complete run function workflow."""
        mock_config.return_value = {"min_coverage": 80}
        mock_changed.return_value = ["test.py"]

        gate_result = GateResult("Test", True, "Success", 0)
        mock_lint.return_value = (gate_result, None)
        mock_type.return_value = (gate_result, None)
        mock_security.return_value = (gate_result, None)
        mock_coverage.return_value = (gate_result, None)
        mock_summarize.return_value = 0

        result = run(["--min-cov", "80", "--skip-tests"])
        assert result == 0

    @patch("sys.exit")
    def test_main_function(self, mock_exit):
        """Test main function."""
        with patch("src.ai_guard.analyzer.run") as mock_run:
            mock_run.return_value = 1
            main()
            mock_exit.assert_called_once_with(1)


class TestAnalyzerClasses:
    """Test analyzer classes."""

    def test_security_analyzer(self):
        """Test SecurityAnalyzer complete functionality."""
        analyzer = SecurityAnalyzer()

        # Test load_rules
        analyzer.load_rules()
        assert analyzer.rules == ["rule1", "rule2", "rule3"]

        # Test with file containing security issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('import os\nos.system("test")\neval("bad")')
            test_file = f.name

        try:
            result = analyzer.analyze_file(test_file)
            assert len(result) >= 2
        finally:
            os.unlink(test_file)

        # Test add_issue and clear_issues
        analyzer.add_issue("test.py", 10, "Test issue", "HIGH")
        assert len(analyzer.get_issues()) == 1
        analyzer.clear_issues()
        assert len(analyzer.get_issues()) == 0

    def test_performance_analyzer(self):
        """Test PerformanceAnalyzer."""
        analyzer = PerformanceAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import time\ntime.sleep(1)\nfor i in range(1000000):\n    pass")
            test_file = f.name

        try:
            result = analyzer.analyze_file(test_file)
            assert len(result) >= 2
        finally:
            os.unlink(test_file)

        analyzer.add_issue("test.py", 5, "Performance issue", "MEDIUM")
        analyzer.clear_issues()

    def test_quality_analyzer(self):
        """Test QualityAnalyzer."""
        analyzer = QualityAnalyzer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# TODO: fix\n# FIXME: broken\npass")
            test_file = f.name

        try:
            result = analyzer.analyze_file(test_file)
            assert len(result) >= 2
        finally:
            os.unlink(test_file)

    def test_coverage_analyzer(self):
        """Test CoverageAnalyzer."""
        analyzer = CoverageAnalyzer()

        analyzer.set_threshold(90.0)
        assert analyzer.threshold == 90.0

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test():\n    pass")
            test_file = f.name

        try:
            result = analyzer.analyze_file(test_file)
            assert isinstance(result, dict)
        finally:
            os.unlink(test_file)

        analyzer.clear_data()


class TestAnalysisResult:
    """Test AnalysisResult functionality."""

    def test_analysis_result_methods(self):
        """Test all AnalysisResult methods."""
        result = AnalysisResult()

        # Test add methods
        result.add_security_issue("security issue")
        result.add_performance_issue("performance issue")
        result.add_quality_issue("quality issue")

        assert result.get_total_issues() == 3
        assert result.has_issues() is True

        summary = result.get_issues_summary()
        assert summary["total"] == 3

        result.set_coverage_data({"test.py": 85.0})
        result.set_execution_time(2.5)

        data = result.to_dict()
        assert data["execution_time"] == 2.5

        result.clear_issues()
        assert result.get_total_issues() == 0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_git_diff(self):
        """Test _get_git_diff."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="diff content")
            result = _get_git_diff()
            assert result == "diff content"

            mock_run.side_effect = FileNotFoundError()
            result = _get_git_diff()
            assert result == ""

    def test_get_changed_files(self):
        """Test _get_changed_files."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="file1.py\nfile2.py\n")
            result = _get_changed_files()
            assert result == ["file1.py", "file2.py"]

    def test_parse_coverage_output(self):
        """Test _parse_coverage_output."""
        output = "TOTAL 85%"
        result = _parse_coverage_output(output)
        assert result == 85

        output = "No coverage info"
        result = _parse_coverage_output(output)
        assert result is None

    def test_write_reports(self):
        """Test _write_reports."""
        issues = [
            {
                "rule_id": "E501",
                "level": "error",
                "message": "Test",
                "path": "test.py",
                "line": 10,
            }
        ]
        config = {"report_format": "sarif", "report_path": "test.sarif"}

        with patch("src.ai_guard.analyzer.write_sarif") as mock_write:
            _write_reports(issues, config)
            mock_write.assert_called_once()

    def test_to_findings(self):
        """Test _to_findings."""
        sarif_results = [
            SarifResult(
                rule_id="E501",
                level="error",
                message="Test",
                locations=[
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": "test.py"},
                            "region": {"startLine": 10},
                        }
                    }
                ],
            )
        ]

        findings = _to_findings(sarif_results)
        assert len(findings) == 1
        assert findings[0]["path"] == "test.py"


class TestAnalysisConfig:
    """Test AnalysisConfig."""

    def test_analysis_config_methods(self):
        """Test AnalysisConfig methods."""
        config = AnalysisConfig(output_format="xml", verbose=True)

        data = config.to_dict()
        assert data["output_format"] == "xml"
        assert data["verbose"] is True

        config2 = AnalysisConfig.from_dict(data)
        assert config2.output_format == "xml"
        assert config2.verbose is True
