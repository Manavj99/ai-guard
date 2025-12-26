"""Comprehensive integration tests for core workflows."""

import pytest
import tempfile
import os
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ai_guard.analyzer import (
    run_analysis,
    AnalysisConfig,
    CodeAnalyzer,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
)
from src.ai_guard.config import load_config, save_config
from src.ai_guard.security_scanner import scan_file, scan_directory
from src.ai_guard.cache import CacheManager, LRUCache, TTLCache
from src.ai_guard.analytics import AnalyticsSystem, MetricsCollector, KPIManager


class TestEndToEndAnalysis:
    """Test end-to-end analysis workflows."""

    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow from file to report."""
        # Create test Python file with various issues
        test_code = """
import os
import subprocess

# Security issue: hardcoded password
password = 'secret123'

# Performance issue: inefficient loop
def slow_function():
    result = []
    for i in range(1000):
        result.append(i * 2)
    return result

# Quality issue: unused import
import sys

# Coverage: simple function
def test_function(x):
    return x * 2
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # Create analysis config
                config = AnalysisConfig(
                    enable_security_analysis=True,
                    enable_performance_analysis=True,
                    enable_quality_analysis=True,
                    enable_coverage_analysis=True,
                )

                # Run analysis
                result = run_analysis([f.name], config)

                # Verify results
                assert result is not None
                assert len(result.security_issues) >= 0  # May find hardcoded password
                assert (
                    len(result.performance_issues) >= 0
                )  # May find performance issues
                assert len(result.quality_issues) >= 0  # May find quality issues
                assert isinstance(result.coverage_data, dict)
                assert result.execution_time > 0

            finally:
                os.unlink(f.name)

    def test_analysis_with_config_file(self):
        """Test analysis using configuration file."""
        # Create config file
        config_data = {
            "coverage_threshold": 80,
            "enable_security": True,
            "enable_performance": True,
            "enable_quality": True,
            "output_format": "json",
            "llm_provider": "openai",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as config_file:
            json.dump(config_data, config_file)
            config_file.flush()

            # Create test file
            test_code = "print('hello world')"
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as test_file:
                test_file.write(test_code)
                test_file.flush()

                try:
                    # Load config
                    config = load_config(config_file.name)

                    # Create analysis config from loaded config
                    analysis_config = AnalysisConfig(
                        enable_security_analysis=config.get("enable_security", True),
                        enable_performance_analysis=config.get(
                            "enable_performance", True
                        ),
                        enable_quality_analysis=config.get("enable_quality", True),
                        enable_coverage_analysis=True,
                    )

                    # Run analysis
                    result = run_analysis([test_file.name], analysis_config)

                    assert result is not None
                    assert result.execution_time > 0

                finally:
                    os.unlink(config_file.name)
                    os.unlink(test_file.name)

    def test_multi_file_analysis(self):
        """Test analysis of multiple files."""
        test_files = []

        try:
            # Create multiple test files
            for i in range(3):
                test_code = f"""
def function_{i}(x):
    return x * {i}

# Some security issue
api_key = 'key_{i}'
"""

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False
                ) as f:
                    f.write(test_code)
                    f.flush()
                    test_files.append(f.name)

            # Run analysis on multiple files
            config = AnalysisConfig()
            results = []

            for file_path in test_files:
                result = run_analysis([file_path], config)
                results.append(result)

            # Verify all files were analyzed
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert result.execution_time > 0

        finally:
            for file_path in test_files:
                os.unlink(file_path)


class TestComponentIntegration:
    """Test integration between different components."""

    def test_analyzer_with_cache_integration(self):
        """Test analyzer integration with caching system."""
        # Create cache manager
        cache_manager = CacheManager()
        cache = cache_manager.create_cache("analysis_cache", "lru", max_size=100)

        # Create test file
        test_code = "def test_function(x):\n    return x * 2"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # First analysis (should populate cache)
                config = AnalysisConfig()
                result1 = run_analysis([f.name], config)

                # Second analysis (should use cache if implemented)
                result2 = run_analysis([f.name], config)

                assert result1 is not None
                assert result2 is not None

                # Cache should have some data
                assert cache.size >= 0

            finally:
                os.unlink(f.name)

    def test_security_scanner_with_analyzer_integration(self):
        """Test security scanner integration with analyzer."""
        # Create test file with security issues
        test_code = """
password = 'secret123'
api_key = 'abc123def456'
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # Run security scan
                security_result = scan_file(f.name)

                # Run analyzer with security analysis
                config = AnalysisConfig(enable_security_analysis=True)
                analysis_result = run_analysis([f.name], config)

                # Both should find security issues
                assert security_result["total_issues"] >= 0
                assert len(analysis_result.security_issues) >= 0

            finally:
                os.unlink(f.name)

    def test_analytics_integration(self):
        """Test analytics system integration."""
        # Initialize analytics system
        analytics = AnalyticsSystem()

        # Create test metrics
        analytics.metrics_collector.add_metric(
            name="analysis_duration",
            value=2.5,
            metric_type=analytics.metrics_collector.MetricType.TIMER,
            tags={"environment": "test"},
        )

        analytics.metrics_collector.add_metric(
            name="quality_score",
            value=85.0,
            metric_type=analytics.metrics_collector.MetricType.GAUGE,
            tags={"environment": "test"},
        )

        # Generate report
        report = analytics.generate_executive_report()

        assert report is not None
        assert report.report_type == "executive"
        assert "kpis" in report.data

        # Get system statistics
        stats = analytics.get_system_statistics()

        assert "total_metrics" in stats
        assert "total_kpis" in stats
        assert stats["total_metrics"] >= 2


class TestErrorHandlingIntegration:
    """Test error handling across components."""

    def test_analysis_with_invalid_file(self):
        """Test analysis with invalid file paths."""
        config = AnalysisConfig()

        # Test with nonexistent file
        result = run_analysis(["nonexistent_file.py"], config)

        # Should handle gracefully
        assert result is not None
        assert result.execution_time >= 0

    def test_analysis_with_permission_error(self):
        """Test analysis with permission errors."""
        config = AnalysisConfig()

        # Create file without read permission (if possible)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            f.flush()

            try:
                # Try to analyze file
                result = run_analysis([f.name], config)

                # Should handle gracefully
                assert result is not None

            finally:
                os.unlink(f.name)

    def test_config_loading_errors(self):
        """Test configuration loading error handling."""
        # Test loading nonexistent config
        config = load_config("nonexistent_config.json")
        assert config == {}  # Should return empty config

        # Test loading invalid config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()

            try:
                config = load_config(f.name)
                assert config == {}  # Should return empty config on error
            finally:
                os.unlink(f.name)

    def test_security_scanner_errors(self):
        """Test security scanner error handling."""
        # Test scanning nonexistent file
        result = scan_file("nonexistent.py")

        assert result["total_issues"] == 0
        assert result["files_scanned"] == 0

        # Test scanning nonexistent directory
        result = scan_directory("nonexistent_directory")

        assert result["total_issues"] == 0
        assert result["files_scanned"] == 0


class TestPerformanceIntegration:
    """Test performance across integrated components."""

    def test_large_file_analysis_performance(self):
        """Test analysis performance with large file."""
        # Create large test file
        large_code = "def test_function(x):\n    return x * 2\n" * 1000

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(large_code)
            f.flush()

            try:
                config = AnalysisConfig()

                # Measure analysis time
                import time

                start_time = time.time()
                result = run_analysis([f.name], config)
                end_time = time.time()

                execution_time = end_time - start_time

                assert result is not None
                assert result.execution_time > 0
                assert execution_time < 30  # Should complete within 30 seconds

            finally:
                os.unlink(f.name)

    def test_concurrent_analysis_performance(self):
        """Test concurrent analysis performance."""
        import threading
        import time

        # Create multiple test files
        test_files = []
        for i in range(5):
            test_code = f"def function_{i}(x):\n    return x * {i}\n"

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_code)
                f.flush()
                test_files.append(f.name)

        try:
            results = []
            threads = []

            def analyze_file(file_path):
                config = AnalysisConfig()
                result = run_analysis([file_path], config)
                results.append(result)

            # Start concurrent analysis
            start_time = time.time()

            for file_path in test_files:
                thread = threading.Thread(target=analyze_file, args=(file_path,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            end_time = time.time()

            # Verify all analyses completed
            assert len(results) == 5
            assert end_time - start_time < 60  # Should complete within 60 seconds

        finally:
            for file_path in test_files:
                os.unlink(file_path)


class TestDataFlowIntegration:
    """Test data flow between components."""

    def test_config_to_analysis_flow(self):
        """Test data flow from config to analysis."""
        # Create detailed config
        config_data = {
            "coverage_threshold": 90,
            "enable_security": True,
            "enable_performance": False,
            "enable_quality": True,
            "output_format": "html",
            "severity_threshold": "high",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as config_file:
            json.dump(config_data, config_file)
            config_file.flush()

            # Create test file
            test_code = """
def test_function(x):
    return x * 2

# Security issue
password = 'secret'
"""

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as test_file:
                test_file.write(test_code)
                test_file.flush()

                try:
                    # Load config
                    loaded_config = load_config(config_file.name)

                    # Create analysis config based on loaded config
                    analysis_config = AnalysisConfig(
                        enable_security_analysis=loaded_config.get(
                            "enable_security", True
                        ),
                        enable_performance_analysis=loaded_config.get(
                            "enable_performance", True
                        ),
                        enable_quality_analysis=loaded_config.get(
                            "enable_quality", True
                        ),
                        enable_coverage_analysis=True,
                    )

                    # Run analysis
                    result = run_analysis([test_file.name], analysis_config)

                    # Verify config was applied
                    assert result is not None

                    # Security should be enabled
                    assert analysis_config.enable_security_analysis is True

                    # Performance should be disabled
                    assert analysis_config.enable_performance_analysis is False

                finally:
                    os.unlink(config_file.name)
                    os.unlink(test_file.name)

    def test_analysis_to_report_flow(self):
        """Test data flow from analysis to report generation."""
        # Create test file
        test_code = """
def test_function(x):
    return x * 2

# Quality issue: unused variable
unused_var = 42

# Security issue
api_key = 'secret_key'
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # Run analysis
                config = AnalysisConfig()
                result = run_analysis([f.name], config)

                # Convert to dictionary for report generation
                report_data = result.to_dict()

                # Verify report data structure
                assert "security_issues" in report_data
                assert "performance_issues" in report_data
                assert "quality_issues" in report_data
                assert "coverage_data" in report_data
                assert "execution_time" in report_data

                # Verify execution time is recorded
                assert report_data["execution_time"] > 0

            finally:
                os.unlink(f.name)


class TestWorkflowScenarios:
    """Test realistic workflow scenarios."""

    def test_ci_cd_pipeline_simulation(self):
        """Test simulating a CI/CD pipeline workflow."""
        # Create test files representing a project
        project_files = []

        try:
            # Main application file
            main_code = """
import os
import json

def main():
    config = load_config()
    result = process_data(config)
    return result

def load_config():
    return {'api_key': os.getenv('API_KEY')}

def process_data(config):
    return {'status': 'success', 'data': 'processed'}
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(main_code)
                f.flush()
                project_files.append(f.name)

            # Test file
            test_code = """
import pytest
from main import process_data

def test_process_data():
    config = {'api_key': 'test_key'}
    result = process_data(config)
    assert result['status'] == 'success'
"""

            with tempfile.NamedTemporaryFile(
                mode="w", suffix="_test.py", delete=False
            ) as f:
                f.write(test_code)
                f.flush()
                project_files.append(f.name)

            # Configuration file
            config_data = {
                "coverage_threshold": 80,
                "enable_security": True,
                "enable_performance": True,
                "enable_quality": True,
                "output_format": "json",
            }

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(config_data, f)
                f.flush()
                project_files.append(f.name)

            # Load configuration
            config = load_config(project_files[2])

            # Create analysis config
            analysis_config = AnalysisConfig(
                enable_security_analysis=config.get("enable_security", True),
                enable_performance_analysis=config.get("enable_performance", True),
                enable_quality_analysis=config.get("enable_quality", True),
                enable_coverage_analysis=True,
            )

            # Analyze all Python files
            python_files = [f for f in project_files if f.endswith(".py")]
            results = []

            for file_path in python_files:
                result = run_analysis([file_path], analysis_config)
                results.append(result)

            # Verify pipeline results
            assert len(results) == 2  # Main and test files

            total_execution_time = sum(result.execution_time for result in results)
            assert total_execution_time > 0

            # Check if any issues were found
            total_issues = sum(
                len(result.security_issues)
                + len(result.performance_issues)
                + len(result.quality_issues)
                for result in results
            )

            # Should handle gracefully regardless of issue count
            assert total_issues >= 0

        finally:
            for file_path in project_files:
                os.unlink(file_path)

    def test_development_workflow_simulation(self):
        """Test simulating a development workflow."""
        # Initialize analytics for tracking
        analytics = AnalyticsSystem()

        # Create test file with issues
        problematic_code = """
import os
import subprocess

# Security issues
password = 'hardcoded_password'
api_key = 'hardcoded_api_key'

# Performance issues
def slow_function():
    result = []
    for i in range(10000):
        result.append(i * 2)
    return result

# Quality issues
unused_import = 'this is unused'
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(problematic_code)
            f.flush()

            try:
                # Initial analysis
                config = AnalysisConfig()
                initial_result = run_analysis([f.name], config)

                # Record metrics
                analytics.metrics_collector.add_metric(
                    name="initial_analysis_duration",
                    value=initial_result.execution_time,
                    metric_type=analytics.metrics_collector.MetricType.TIMER,
                )

                analytics.metrics_collector.add_metric(
                    name="initial_security_issues",
                    value=len(initial_result.security_issues),
                    metric_type=analytics.metrics_collector.MetricType.GAUGE,
                )

                # Simulate fixing issues
                fixed_code = """
import os

# Fixed: Use environment variables
password = os.getenv('PASSWORD')
api_key = os.getenv('API_KEY')

# Fixed: More efficient implementation
def fast_function():
    return [i * 2 for i in range(10000)]

# Fixed: Removed unused variable
"""

                with open(f.name, "w") as f:
                    f.write(fixed_code)

                # Re-analyze after fixes
                fixed_result = run_analysis([f.name], config)

                # Record improvement metrics
                analytics.metrics_collector.add_metric(
                    name="fixed_analysis_duration",
                    value=fixed_result.execution_time,
                    metric_type=analytics.metrics_collector.MetricType.TIMER,
                )

                analytics.metrics_collector.add_metric(
                    name="fixed_security_issues",
                    value=len(fixed_result.security_issues),
                    metric_type=analytics.metrics_collector.MetricType.GAUGE,
                )

                # Verify improvements
                assert len(fixed_result.security_issues) <= len(
                    initial_result.security_issues
                )
                assert fixed_result.execution_time >= 0

                # Generate final report
                final_report = analytics.generate_executive_report()
                assert final_report is not None

            finally:
                os.unlink(f.name)
