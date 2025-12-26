"""Comprehensive tests for the optimized analyzer module."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import time

from src.ai_guard.analyzer import (
    CodeAnalyzer,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    analyze_files_parallel,
    benchmark_analyzer,
)


class TestOptimizedAnalyzer(unittest.TestCase):
    """Test the optimized analyzer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.py")

        # Create test Python file
        with open(self.test_file, "w") as f:
            f.write(
                """
import os
import time

def test_function():
    # TODO: Add more tests
    password = "secret123"  # FIXME: Remove hardcoded password
    for i in range(1000000):  # Performance issue
        time.sleep(0.001)
    os.system("echo hello")  # Security issue
    eval("print('hello')")  # Security issue
    return "done"
"""
            )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_security_analyzer_optimized(self):
        """Test optimized security analyzer."""
        analyzer = SecurityAnalyzer()

        # Test file analysis
        issues = analyzer.analyze_file(self.test_file)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

        # Test caching
        issues2 = analyzer.analyze_file(self.test_file)
        self.assertEqual(issues, issues2)

        # Test cache stats
        with analyzer._lock:
            cache_size = len(analyzer._cache)
        self.assertGreater(cache_size, 0)

    def test_performance_analyzer_optimized(self):
        """Test optimized performance analyzer."""
        analyzer = PerformanceAnalyzer()

        # Test file analysis
        issues = analyzer.analyze_file(self.test_file)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

        # Test caching
        issues2 = analyzer.analyze_file(self.test_file)
        self.assertEqual(issues, issues2)

    def test_quality_analyzer_optimized(self):
        """Test optimized quality analyzer."""
        analyzer = QualityAnalyzer()

        # Test file analysis
        issues = analyzer.analyze_file(self.test_file)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

        # Test caching
        issues2 = analyzer.analyze_file(self.test_file)
        self.assertEqual(issues, issues2)

    def test_coverage_analyzer_optimized(self):
        """Test optimized coverage analyzer."""
        analyzer = CoverageAnalyzer()

        # Test file analysis
        coverage_data = analyzer.analyze_file(self.test_file)
        self.assertIsInstance(coverage_data, dict)
        self.assertIn(self.test_file, coverage_data)

        # Test caching
        coverage_data2 = analyzer.analyze_file(self.test_file)
        self.assertEqual(coverage_data, coverage_data2)

    def test_code_analyzer_optimized(self):
        """Test optimized code analyzer."""
        config = AnalysisConfig(
            enable_security_analysis=True,
            enable_performance_analysis=True,
            enable_quality_analysis=True,
            enable_coverage_analysis=True,
        )
        analyzer = CodeAnalyzer(config)

        # Test file analysis
        result = analyzer.analyze_file(self.test_file)
        self.assertIsInstance(result, AnalysisResult)
        self.assertGreater(len(result.security_issues), 0)
        self.assertGreater(len(result.performance_issues), 0)
        self.assertGreater(len(result.quality_issues), 0)
        self.assertIn(self.test_file, result.coverage_data)

        # Test caching
        result2 = analyzer.analyze_file(self.test_file)
        self.assertEqual(result.security_issues, result2.security_issues)
        self.assertEqual(result.performance_issues, result2.performance_issues)
        self.assertEqual(result.quality_issues, result2.quality_issues)

    def test_analyze_directory_parallel(self):
        """Test parallel directory analysis."""
        # Create multiple test files
        test_files = []
        for i in range(5):
            test_file = os.path.join(self.temp_dir, f"test_{i}.py")
            with open(test_file, "w") as f:
                f.write(
                    f"""
def test_function_{i}():
    # TODO: Test {i}
    password = "secret{i}"
    for j in range(1000):
        pass
    return "done_{i}"
"""
                )
            test_files.append(test_file)

        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)

        # Test parallel analysis
        results = analyzer.analyze_directory(self.temp_dir, max_workers=2)
        self.assertEqual(len(results), 6)  # 5 new files + 1 original

        # Verify all results are AnalysisResult instances
        for result in results:
            self.assertIsInstance(result, AnalysisResult)

    def test_run_all_checks_parallel(self):
        """Test parallel execution of all checks."""
        config = AnalysisConfig()
        analyzer = CodeAnalyzer(config)

        # Test parallel execution
        results = analyzer.run_all_checks([self.test_file], parallel=True)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # Verify all results are GateResult instances
        from src.ai_guard.report import GateResult

        for result in results:
            self.assertIsInstance(result, GateResult)

    def test_analyze_files_parallel_function(self):
        """Test the analyze_files_parallel utility function."""
        test_files = [self.test_file]

        # Test parallel analysis
        results = analyze_files_parallel(test_files, max_workers=2)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], AnalysisResult)

    def test_benchmark_analyzer(self):
        """Test analyzer benchmarking."""
        test_files = [self.test_file]

        # Run benchmark
        benchmark_results = benchmark_analyzer(test_files, iterations=2)

        self.assertIn("sequential_time", benchmark_results)
        self.assertIn("parallel_time", benchmark_results)
        self.assertIn("speedup", benchmark_results)
        self.assertIn("files_per_second_sequential", benchmark_results)
        self.assertIn("files_per_second_parallel", benchmark_results)

        # Verify benchmark results are reasonable
        self.assertGreater(benchmark_results["sequential_time"], 0)
        self.assertGreater(benchmark_results["parallel_time"], 0)
        self.assertGreaterEqual(benchmark_results["speedup"], 1.0)

    def test_cache_functionality(self):
        """Test cache functionality."""
        analyzer = CodeAnalyzer()

        # Analyze file first time
        result1 = analyzer.analyze_file(self.test_file)

        # Get cache stats
        cache_stats = analyzer.get_cache_stats()
        self.assertGreater(cache_stats["total_cache"], 0)

        # Analyze file second time (should use cache)
        result2 = analyzer.analyze_file(self.test_file)

        # Results should be identical
        self.assertEqual(result1.security_issues, result2.security_issues)
        self.assertEqual(result1.performance_issues, result2.performance_issues)
        self.assertEqual(result1.quality_issues, result2.quality_issues)

        # Clear cache
        analyzer.clear_cache()

        # Cache should be empty
        cache_stats_after = analyzer.get_cache_stats()
        self.assertEqual(cache_stats_after["total_cache"], 0)

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        analyzer = CodeAnalyzer()

        # Analyze some files to generate metrics
        analyzer.analyze_file(self.test_file)

        # Get performance metrics
        metrics = analyzer.get_performance_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_metrics", metrics)

    def test_error_handling(self):
        """Test error handling in optimized analyzers."""
        analyzer = CodeAnalyzer()

        # Test with non-existent file
        result = analyzer.analyze_file("non_existent_file.py")
        self.assertIsInstance(result, AnalysisResult)
        self.assertGreater(len(result.security_issues), 0)

        # Test with invalid directory
        results = analyzer.analyze_directory("non_existent_directory")
        self.assertEqual(len(results), 0)

    def test_thread_safety(self):
        """Test thread safety of analyzers."""
        import threading
        import time

        analyzer = CodeAnalyzer()
        results = []
        errors = []

        def analyze_file():
            try:
                result = analyzer.analyze_file(self.test_file)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=analyze_file)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)

        # Verify all results are identical (cached)
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(first_result.security_issues, result.security_issues)
            self.assertEqual(first_result.performance_issues, result.performance_issues)
            self.assertEqual(first_result.quality_issues, result.quality_issues)

    def test_compiled_patterns(self):
        """Test compiled regex patterns."""
        analyzer = SecurityAnalyzer()

        # Verify patterns are compiled
        self.assertIsInstance(analyzer._compiled_patterns, dict)
        self.assertGreater(len(analyzer._compiled_patterns), 0)

        # Test specific patterns
        self.assertIn("os_system", analyzer._compiled_patterns)
        self.assertIn("eval_call", analyzer._compiled_patterns)
        self.assertIn("hardcoded_password", analyzer._compiled_patterns)

        # Verify patterns are compiled regex objects
        for pattern_name, pattern in analyzer._compiled_patterns.items():
            self.assertTrue(hasattr(pattern, "findall"))

    def test_coverage_xml_caching(self):
        """Test coverage XML caching."""
        analyzer = CoverageAnalyzer()

        # Test XML caching
        coverage_percent = analyzer._get_coverage_from_xml_cached()

        # Should return a value if coverage.xml exists, None otherwise
        # This test just verifies the caching mechanism works
        self.assertIsInstance(coverage_percent, (int, type(None)))

        # Test cache functionality
        with analyzer._lock:
            self.assertIn("coverage.xml", analyzer._xml_cache)

    def test_analysis_config_optimization(self):
        """Test analysis configuration optimization."""
        # Test with different configurations
        configs = [
            AnalysisConfig(
                enable_security_analysis=True, enable_performance_analysis=False
            ),
            AnalysisConfig(
                enable_security_analysis=False, enable_performance_analysis=True
            ),
            AnalysisConfig(
                enable_quality_analysis=False, enable_coverage_analysis=True
            ),
        ]

        for config in configs:
            analyzer = CodeAnalyzer(config)
            result = analyzer.analyze_file(self.test_file)

            # Verify only enabled analyzers run
            if config.enable_security_analysis:
                self.assertGreater(len(result.security_issues), 0)
            else:
                self.assertEqual(len(result.security_issues), 0)

            if config.enable_performance_analysis:
                self.assertGreater(len(result.performance_issues), 0)
            else:
                self.assertEqual(len(result.performance_issues), 0)


if __name__ == "__main__":
    unittest.main()
