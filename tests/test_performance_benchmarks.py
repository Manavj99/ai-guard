"""Performance benchmarks and optimization tests."""

import pytest
import tempfile
import os
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from src.ai_guard.analyzer import (
    run_analysis,
    AnalysisConfig,
    CodeAnalyzer,
    analyze_files_parallel,
    benchmark_analyzer,
)
from src.ai_guard.cache import LRUCache, TTLCache, CacheManager
from src.ai_guard.config import load_config, _get_cached_config, _cache_config
from src.ai_guard.security_scanner import scan_file, scan_code_string
from src.ai_guard.analytics import AnalyticsSystem, MetricsCollector


class TestAnalyzerPerformance:
    """Test analyzer performance benchmarks."""

    def test_single_file_analysis_performance(self):
        """Benchmark single file analysis performance."""
        # Create test file
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

def test_function(x):
    return x * 2 + fibonacci(10) + factorial(5)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                config = AnalysisConfig()

                # Measure performance
                times = []
                for _ in range(5):
                    start_time = time.time()
                    result = run_analysis([f.name], config)
                    end_time = time.time()
                    times.append(end_time - start_time)

                avg_time = statistics.mean(times)
                max_time = max(times)
                min_time = min(times)

                # Performance assertions
                assert avg_time < 10.0  # Should complete within 10 seconds
                assert max_time < 15.0  # Worst case should be under 15 seconds
                assert min_time > 0.0  # Should take some time

                # Verify result quality
                assert result is not None
                assert result.execution_time > 0

            finally:
                os.unlink(f.name)

    def test_large_file_analysis_performance(self):
        """Benchmark large file analysis performance."""
        # Create large test file (1000+ lines)
        large_code = []
        for i in range(1000):
            large_code.append(
                f"""
def function_{i}(x):
    # Function {i} with some logic
    result = x * {i}
    if result > 100:
        return result * 2
    else:
        return result + 1
"""
            )

        test_code = "\n".join(large_code)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                config = AnalysisConfig()

                start_time = time.time()
                result = run_analysis([f.name], config)
                end_time = time.time()

                execution_time = end_time - start_time

                # Performance assertions for large file
                assert execution_time < 60.0  # Should complete within 60 seconds
                assert result is not None
                assert result.execution_time > 0

                # File size should be reasonable
                file_size = os.path.getsize(f.name)
                assert file_size > 50000  # Should be substantial size

            finally:
                os.unlink(f.name)

    def test_multiple_files_parallel_performance(self):
        """Benchmark parallel analysis of multiple files."""
        # Create multiple test files
        test_files = []
        for i in range(10):
            test_code = f"""
def function_{i}(x):
    return x * {i}

def helper_{i}(y):
    return y + {i}
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_code)
                f.flush()
                test_files.append(f.name)

        try:
            config = AnalysisConfig()

            # Test parallel analysis
            start_time = time.time()
            results = analyze_files_parallel(test_files, config, max_workers=4)
            end_time = time.time()

            parallel_time = end_time - start_time

            # Test sequential analysis for comparison
            start_time = time.time()
            sequential_results = []
            for file_path in test_files:
                result = run_analysis([file_path], config)
                sequential_results.append(result)
            end_time = time.time()

            sequential_time = end_time - start_time

            # Verify results
            assert len(results) == len(test_files)
            assert len(sequential_results) == len(test_files)

            # Parallel should be faster (or at least not significantly slower)
            # Allow some tolerance for overhead
            assert parallel_time <= sequential_time * 1.5

            # Both should complete in reasonable time
            assert parallel_time < 30.0
            assert sequential_time < 60.0

        finally:
            for file_path in test_files:
                os.unlink(file_path)

    def test_analyzer_benchmark_function(self):
        """Test the built-in benchmark function."""
        # Create test file
        test_code = """
def test_function(x):
    return x * 2

def another_function(y):
    return y + 1
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # Run benchmark
                stats = benchmark_analyzer([f.name], iterations=3)

                # Verify benchmark results
                assert "avg_execution_time" in stats
                assert "min_execution_time" in stats
                assert "max_execution_time" in stats
                assert "std_execution_time" in stats

                assert stats["avg_execution_time"] > 0
                assert stats["min_execution_time"] > 0
                assert stats["max_execution_time"] > 0
                assert stats["std_execution_time"] >= 0

                # Min should be <= avg <= max
                assert stats["min_execution_time"] <= stats["avg_execution_time"]
                assert stats["avg_execution_time"] <= stats["max_execution_time"]

            finally:
                os.unlink(f.name)


class TestCachePerformance:
    """Test cache performance benchmarks."""

    def test_lru_cache_performance(self):
        """Benchmark LRU cache performance."""
        cache = LRUCache(max_size=1000)

        # Test cache insertion performance
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        end_time = time.time()

        insertion_time = end_time - start_time
        assert insertion_time < 1.0  # Should be very fast

        # Test cache retrieval performance
        start_time = time.time()
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        end_time = time.time()

        retrieval_time = end_time - start_time
        assert retrieval_time < 1.0  # Should be very fast

        # Test cache eviction performance
        start_time = time.time()
        for i in range(1000, 2000):
            cache.set(f"key_{i}", f"value_{i}")
        end_time = time.time()

        eviction_time = end_time - start_time
        assert eviction_time < 1.0  # Should handle eviction efficiently

    def test_ttl_cache_performance(self):
        """Benchmark TTL cache performance."""
        cache = TTLCache(max_size=1000, ttl=60)

        # Test cache operations with TTL
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        end_time = time.time()

        insertion_time = end_time - start_time
        assert insertion_time < 1.0

        # Test retrieval with TTL checking
        start_time = time.time()
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        end_time = time.time()

        retrieval_time = end_time - start_time
        assert retrieval_time < 1.0

    def test_cache_thread_safety_performance(self):
        """Benchmark cache performance under concurrent access."""
        cache = LRUCache(max_size=1000)

        def worker(thread_id, num_operations):
            for i in range(num_operations):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                cache.set(key, value)
                retrieved = cache.get(key)
                assert retrieved == value

        # Test with multiple threads
        num_threads = 4
        operations_per_thread = 250

        start_time = time.time()
        threads = []

        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i, operations_per_thread))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        total_time = end_time - start_time
        total_operations = num_threads * operations_per_thread * 2  # set + get

        operations_per_second = total_operations / total_time

        # Should handle thousands of operations per second
        assert operations_per_second > 1000

    def test_cache_memory_usage(self):
        """Test cache memory usage efficiency."""
        cache = LRUCache(max_size=10000)

        # Add items to cache
        for i in range(10000):
            cache.set(f"key_{i}", f"value_{i}")

        # Cache should be at max size
        assert cache.size == 10000

        # Add more items to trigger eviction
        for i in range(10000, 20000):
            cache.set(f"key_{i}", f"value_{i}")

        # Cache should still be at max size
        assert cache.size == 10000

        # Should have evicted old items
        assert cache.get("key_0") is None
        assert cache.get("key_19999") is not None


class TestConfigPerformance:
    """Test configuration system performance."""

    def test_config_caching_performance(self):
        """Benchmark configuration caching performance."""
        config_data = {
            "coverage_threshold": 80,
            "enable_security": True,
            "enable_performance": True,
            "enable_quality": True,
            "output_format": "json",
            "llm_provider": "openai",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(config_data, f)
            f.flush()

            try:
                # First load (should populate cache)
                start_time = time.time()
                config1 = load_config(f.name)
                first_load_time = time.time() - start_time

                # Second load (should use cache)
                start_time = time.time()
                config2 = load_config(f.name)
                second_load_time = time.time() - start_time

                # Verify results are the same
                assert config1 == config2

                # Cached load should be faster
                assert second_load_time < first_load_time

                # Both should be reasonably fast
                assert first_load_time < 1.0
                assert second_load_time < 0.1

            finally:
                os.unlink(f.name)

    def test_config_validation_performance(self):
        """Benchmark configuration validation performance."""
        # Create large config
        large_config = {}
        for i in range(1000):
            large_config[f"key_{i}"] = f"value_{i}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(large_config, f)
            f.flush()

            try:
                # Measure config loading and validation time
                start_time = time.time()
                config = load_config(f.name)
                end_time = time.time()

                load_time = end_time - start_time

                # Should handle large configs efficiently
                assert load_time < 2.0
                assert len(config) == 1000

            finally:
                os.unlink(f.name)


class TestSecurityScannerPerformance:
    """Test security scanner performance benchmarks."""

    def test_security_scan_performance(self):
        """Benchmark security scanning performance."""
        # Create test file with various patterns
        test_code = """
import os
import subprocess

# Various security patterns
password = 'hardcoded_password'
api_key = 'hardcoded_api_key'
secret_token = 'secret_token_value'

def dangerous_function():
    # SQL injection pattern
    query = "SELECT * FROM users WHERE id = " + user_id
    
    # Command injection pattern
    os.system("echo " + user_input)
    
    # Path traversal pattern
    file_path = "../../../etc/passwd"
    
    return query

def crypto_function():
    # Weak crypto patterns
    import hashlib
    hash_value = hashlib.md5(data).hexdigest()
    
    # Insecure random
    import random
    random_value = random.randint(1, 100)
    
    return hash_value, random_value
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                # Measure security scan performance
                start_time = time.time()
                result = scan_file(f.name)
                end_time = time.time()

                scan_time = end_time - start_time

                # Should complete quickly
                assert scan_time < 5.0
                assert result["total_issues"] > 0  # Should find issues
                assert result["files_scanned"] == 1

            finally:
                os.unlink(f.name)

    def test_large_file_security_scan_performance(self):
        """Benchmark security scanning of large files."""
        # Create large file with security patterns
        large_code = []
        for i in range(500):
            large_code.append(
                f"""
def function_{i}(x):
    # Security pattern in each function
    password_{i} = 'password_{i}'
    api_key_{i} = 'api_key_{i}'
    
    # Some computation
    result = x * {i}
    
    # More patterns
    secret_{i} = 'secret_{i}'
    
    return result
"""
            )

        test_code = "\n".join(large_code)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            try:
                start_time = time.time()
                result = scan_file(f.name)
                end_time = time.time()

                scan_time = end_time - start_time

                # Should handle large files efficiently
                assert scan_time < 10.0
                assert result["files_scanned"] == 1
                assert result["total_issues"] > 0

            finally:
                os.unlink(f.name)

    def test_security_scan_concurrent_performance(self):
        """Benchmark concurrent security scanning."""
        # Create multiple test files
        test_files = []
        for i in range(10):
            test_code = f"""
password_{i} = 'password_{i}'
api_key_{i} = 'api_key_{i}'

def function_{i}(x):
    return x * {i}
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_code)
                f.flush()
                test_files.append(f.name)

        try:
            # Test concurrent scanning
            def scan_file_wrapper(file_path):
                return scan_file(file_path)

            start_time = time.time()
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(scan_file_wrapper, file_path)
                    for file_path in test_files
                ]
                results = [future.result() for future in as_completed(futures)]
            end_time = time.time()

            concurrent_time = end_time - start_time

            # Test sequential scanning
            start_time = time.time()
            sequential_results = [scan_file(file_path) for file_path in test_files]
            end_time = time.time()

            sequential_time = end_time - start_time

            # Verify results
            assert len(results) == len(test_files)
            assert len(sequential_results) == len(test_files)

            # Concurrent should be faster
            assert concurrent_time <= sequential_time * 1.5

            # Both should complete in reasonable time
            assert concurrent_time < 15.0
            assert sequential_time < 30.0

        finally:
            for file_path in test_files:
                os.unlink(file_path)


class TestAnalyticsPerformance:
    """Test analytics system performance benchmarks."""

    def test_metrics_collection_performance(self):
        """Benchmark metrics collection performance."""
        analytics = AnalyticsSystem()

        # Test adding many metrics quickly
        start_time = time.time()
        for i in range(1000):
            analytics.metrics_collector.add_metric(
                name=f"metric_{i}",
                value=i,
                metric_type=analytics.metrics_collector.MetricType.GAUGE,
                tags={"iteration": str(i)},
            )
        end_time = time.time()

        metrics_time = end_time - start_time
        assert metrics_time < 2.0  # Should be fast

        # Test retrieving metrics
        start_time = time.time()
        metrics = analytics.metrics_collector.get_metrics()
        end_time = time.time()

        retrieval_time = end_time - start_time
        assert retrieval_time < 1.0  # Should be very fast
        assert len(metrics) == 1000

    def test_report_generation_performance(self):
        """Benchmark report generation performance."""
        analytics = AnalyticsSystem()

        # Add some test data
        for i in range(100):
            analytics.metrics_collector.add_metric(
                name="test_metric",
                value=i,
                metric_type=analytics.metrics_collector.MetricType.GAUGE,
            )

        # Test report generation performance
        start_time = time.time()
        report = analytics.generate_executive_report()
        end_time = time.time()

        report_time = end_time - start_time
        assert report_time < 1.0  # Should be fast
        assert report is not None

    def test_concurrent_metrics_performance(self):
        """Benchmark concurrent metrics collection."""
        analytics = AnalyticsSystem()

        def add_metrics(thread_id, num_metrics):
            for i in range(num_metrics):
                analytics.metrics_collector.add_metric(
                    name=f"thread_{thread_id}_metric_{i}",
                    value=i,
                    metric_type=analytics.metrics_collector.MetricType.GAUGE,
                    tags={"thread": str(thread_id)},
                )

        # Test with multiple threads
        num_threads = 4
        metrics_per_thread = 250

        start_time = time.time()
        threads = []

        for i in range(num_threads):
            thread = threading.Thread(target=add_metrics, args=(i, metrics_per_thread))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        total_time = end_time - start_time
        total_metrics = num_threads * metrics_per_thread

        operations_per_second = total_metrics / total_time

        # Should handle thousands of metrics per second
        assert operations_per_second > 1000

        # Verify all metrics were collected
        all_metrics = analytics.metrics_collector.get_metrics()
        assert len(all_metrics) == total_metrics


class TestMemoryUsage:
    """Test memory usage and optimization."""

    def test_analyzer_memory_usage(self):
        """Test analyzer memory usage with large files."""
        # Create large test file
        large_code = "def test_function(x):\n    return x * 2\n" * 10000

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(large_code)
            f.flush()

            try:
                config = AnalysisConfig()

                # Monitor memory usage (basic check)
                import psutil
                import os

                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss

                # Run analysis
                result = run_analysis([f.name], config)

                memory_after = process.memory_info().rss
                memory_increase = memory_after - memory_before

                # Memory increase should be reasonable (less than 100MB)
                assert memory_increase < 100 * 1024 * 1024

                # Result should still be valid
                assert result is not None

            finally:
                os.unlink(f.name)

    def test_cache_memory_efficiency(self):
        """Test cache memory efficiency."""
        # Test with large cache
        cache = LRUCache(max_size=10000)

        # Add large values
        large_value = "x" * 1000  # 1KB per value

        for i in range(10000):
            cache.set(f"key_{i}", f"{large_value}_{i}")

        # Cache should be at max size
        assert cache.size == 10000

        # Add more to test eviction
        for i in range(10000, 15000):
            cache.set(f"key_{i}", f"{large_value}_{i}")

        # Should still be at max size
        assert cache.size == 10000

        # Should have evicted old items
        assert cache.get("key_0") is None
        assert cache.get("key_14999") is not None
