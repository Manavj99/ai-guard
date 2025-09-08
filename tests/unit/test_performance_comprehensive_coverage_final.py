"""
Comprehensive test coverage for src/ai_guard/performance.py
This test file aims to achieve maximum coverage for the performance module.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import time
import threading
import tempfile
import os
from typing import List, Dict, Any, Callable

# Import the performance module
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    get_performance_monitor,
    time_function,
    SimpleCache,
    get_cache,
    cached,
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    profile_memory_usage,
    get_performance_summary,
    clear_performance_data,
    expensive_operation,
    process_large_file,
    optimize_quality_gates_execution
)


class TestPerformanceMetrics(unittest.TestCase):
    """Test PerformanceMetrics class."""
    
    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        self.assertEqual(metrics.execution_time, 0.0)
        self.assertEqual(metrics.memory_usage, 0)
        self.assertEqual(metrics.cpu_usage, 0.0)
        self.assertEqual(metrics.cache_hits, 0)
        self.assertEqual(metrics.cache_misses, 0)
    
    def test_performance_metrics_set_values(self):
        """Test setting PerformanceMetrics values."""
        metrics = PerformanceMetrics()
        metrics.execution_time = 1.5
        metrics.memory_usage = 1024
        metrics.cpu_usage = 50.0
        metrics.cache_hits = 10
        metrics.cache_misses = 5
        
        self.assertEqual(metrics.execution_time, 1.5)
        self.assertEqual(metrics.memory_usage, 1024)
        self.assertEqual(metrics.cpu_usage, 50.0)
        self.assertEqual(metrics.cache_hits, 10)
        self.assertEqual(metrics.cache_misses, 5)


class TestPerformanceMonitor(unittest.TestCase):
    """Test PerformanceMonitor class."""
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        self.assertIsInstance(monitor.metrics, dict)
        self.assertEqual(len(monitor.metrics), 0)
    
    def test_record_execution_time(self):
        """Test recording execution time."""
        monitor = PerformanceMonitor()
        monitor.record_execution_time("test_func", 1.5)
        
        self.assertIn("test_func", monitor.metrics)
        self.assertEqual(monitor.metrics["test_func"].execution_time, 1.5)
    
    def test_record_memory_usage(self):
        """Test recording memory usage."""
        monitor = PerformanceMonitor()
        monitor.record_memory_usage("test_func", 1024)
        
        self.assertIn("test_func", monitor.metrics)
        self.assertEqual(monitor.metrics["test_func"].memory_usage, 1024)
    
    def test_record_cpu_usage(self):
        """Test recording CPU usage."""
        monitor = PerformanceMonitor()
        monitor.record_cpu_usage("test_func", 50.0)
        
        self.assertIn("test_func", monitor.metrics)
        self.assertEqual(monitor.metrics["test_func"].cpu_usage, 50.0)
    
    def test_record_cache_stats(self):
        """Test recording cache statistics."""
        monitor = PerformanceMonitor()
        monitor.record_cache_stats("test_func", 10, 5)
        
        self.assertIn("test_func", monitor.metrics)
        self.assertEqual(monitor.metrics["test_func"].cache_hits, 10)
        self.assertEqual(monitor.metrics["test_func"].cache_misses, 5)
    
    def test_get_metrics(self):
        """Test getting metrics."""
        monitor = PerformanceMonitor()
        monitor.record_execution_time("test_func", 1.5)
        
        metrics = monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.execution_time, 1.5)
    
    def test_get_metrics_nonexistent(self):
        """Test getting metrics for nonexistent function."""
        monitor = PerformanceMonitor()
        metrics = monitor.get_metrics("nonexistent")
        self.assertIsNone(metrics)
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        monitor = PerformanceMonitor()
        monitor.record_execution_time("test_func", 1.5)
        self.assertIn("test_func", monitor.metrics)
        
        monitor.clear_metrics()
        self.assertEqual(len(monitor.metrics), 0)


class TestGetPerformanceMonitor(unittest.TestCase):
    """Test get_performance_monitor function."""
    
    def test_get_performance_monitor_singleton(self):
        """Test that get_performance_monitor returns singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        self.assertIs(monitor1, monitor2)
        self.assertIsInstance(monitor1, PerformanceMonitor)


class TestTimeFunction(unittest.TestCase):
    """Test time_function decorator."""
    
    def test_time_function_decorator(self):
        """Test time_function decorator functionality."""
        @time_function
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        self.assertEqual(result, 10)
        
        # Check that metrics were recorded
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.execution_time, 0)
    
    def test_time_function_with_args(self):
        """Test time_function with arguments."""
        @time_function
        def test_func(a, b, c=10):
            return a + b + c
        
        result = test_func(1, 2, c=3)
        self.assertEqual(result, 6)
        
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)
    
    def test_time_function_exception(self):
        """Test time_function with exception."""
        @time_function
        def test_func():
            raise ValueError("test error")
        
        with self.assertRaises(ValueError):
            test_func()
        
        # Check that metrics were still recorded
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)


class TestSimpleCache(unittest.TestCase):
    """Test SimpleCache class."""
    
    def test_simple_cache_initialization(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache(max_size=100, ttl_seconds=300)
        self.assertEqual(cache.max_size, 100)
        self.assertEqual(cache.ttl_seconds, 300)
        self.assertEqual(len(cache._cache), 0)
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 0)
    
    def test_simple_cache_get_set(self):
        """Test cache get and set operations."""
        cache = SimpleCache()
        
        # Test setting and getting a value
        cache.set("key1", "value1")
        value = cache.get("key1")
        self.assertEqual(value, "value1")
        self.assertEqual(cache._hits, 1)
        self.assertEqual(cache._misses, 0)
    
    def test_simple_cache_miss(self):
        """Test cache miss."""
        cache = SimpleCache()
        
        value = cache.get("nonexistent")
        self.assertIsNone(value)
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 1)
    
    def test_simple_cache_max_size(self):
        """Test cache max size limit."""
        cache = SimpleCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # This should evict key1
        
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")
    
    def test_simple_cache_ttl_expired(self):
        """Test cache TTL expiration."""
        cache = SimpleCache(ttl_seconds=0.1)  # Very short TTL
        
        cache.set("key1", "value1")
        time.sleep(0.2)  # Wait for TTL to expire
        
        value = cache.get("key1")
        self.assertIsNone(value)
    
    def test_simple_cache_ttl_not_expired(self):
        """Test cache TTL not expired."""
        cache = SimpleCache(ttl_seconds=1.0)
        
        cache.set("key1", "value1")
        time.sleep(0.1)  # Short wait, TTL should not expire
        
        value = cache.get("key1")
        self.assertEqual(value, "value1")
    
    def test_simple_cache_clear(self):
        """Test cache clear."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.clear()
        
        self.assertEqual(len(cache._cache), 0)
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 0)
    
    def test_simple_cache_stats(self):
        """Test cache statistics."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["size"], 1)


class TestGetCache(unittest.TestCase):
    """Test get_cache function."""
    
    def test_get_cache_singleton(self):
        """Test that get_cache returns singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        
        self.assertIs(cache1, cache2)
        self.assertIsInstance(cache1, SimpleCache)


class TestCached(unittest.TestCase):
    """Test cached decorator."""
    
    def test_cached_decorator(self):
        """Test cached decorator functionality."""
        call_count = 0
        
        @cached(ttl_seconds=300)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = test_func(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        # Second call should use cache
        result2 = test_func(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # Should not increment
        
        # Different argument should execute function again
        result3 = test_func(10)
        self.assertEqual(result3, 20)
        self.assertEqual(call_count, 2)
    
    def test_cached_with_different_args(self):
        """Test cached decorator with different arguments."""
        call_count = 0
        
        @cached(ttl_seconds=300)
        def test_func(a, b, c=10):
            nonlocal call_count
            call_count += 1
            return a + b + c
        
        result1 = test_func(1, 2)
        self.assertEqual(result1, 13)
        self.assertEqual(call_count, 1)
        
        result2 = test_func(1, 2, c=5)
        self.assertEqual(result2, 8)
        self.assertEqual(call_count, 2)  # Different c value
    
    def test_cached_ttl_expiration(self):
        """Test cached decorator TTL expiration."""
        call_count = 0
        
        @cached(ttl_seconds=0.1)  # Very short TTL
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = test_func(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        time.sleep(0.2)  # Wait for TTL to expire
        
        result2 = test_func(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 2)  # Should execute again


class TestParallelExecute(unittest.TestCase):
    """Test parallel_execute function."""
    
    def test_parallel_execute_basic(self):
        """Test basic parallel execution."""
        def square(x):
            return x * x
        
        results = parallel_execute(square, [1, 2, 3, 4, 5])
        self.assertEqual(results, [1, 4, 9, 16, 25])
    
    def test_parallel_execute_empty_list(self):
        """Test parallel execution with empty list."""
        def square(x):
            return x * x
        
        results = parallel_execute(square, [])
        self.assertEqual(results, [])
    
    def test_parallel_execute_with_exception(self):
        """Test parallel execution with exception."""
        def divide(x):
            if x == 0:
                raise ValueError("Division by zero")
            return 10 / x
        
        with self.assertRaises(ValueError):
            parallel_execute(divide, [1, 0, 2])
    
    def test_parallel_execute_max_workers(self):
        """Test parallel execution with max_workers."""
        def square(x):
            return x * x
        
        results = parallel_execute(square, [1, 2, 3, 4, 5], max_workers=2)
        self.assertEqual(results, [1, 4, 9, 16, 25])


class TestBatchProcess(unittest.TestCase):
    """Test batch_process function."""
    
    def test_batch_process_basic(self):
        """Test basic batch processing."""
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        data = list(range(10))
        results = batch_process(process_batch, data, batch_size=3)
        expected = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        self.assertEqual(results, expected)
    
    def test_batch_process_empty_data(self):
        """Test batch processing with empty data."""
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        results = batch_process(process_batch, [], batch_size=3)
        self.assertEqual(results, [])
    
    def test_batch_process_single_batch(self):
        """Test batch processing with single batch."""
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        data = [1, 2, 3]
        results = batch_process(process_batch, data, batch_size=10)
        self.assertEqual(results, [2, 4, 6])
    
    def test_batch_process_custom_batch_size(self):
        """Test batch processing with custom batch size."""
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        data = list(range(7))
        results = batch_process(process_batch, data, batch_size=2)
        expected = [0, 2, 4, 6, 8, 10, 12]
        self.assertEqual(results, expected)


class TestOptimizeFileOperations(unittest.TestCase):
    """Test optimize_file_operations function."""
    
    def test_optimize_file_operations_basic(self):
        """Test basic file operations optimization."""
        file_paths = ["file1.py", "file2.py", "file3.py"]
        optimized = optimize_file_operations(file_paths)
        
        # Should return the same paths (basic implementation)
        self.assertEqual(optimized, file_paths)
    
    def test_optimize_file_operations_empty(self):
        """Test file operations optimization with empty list."""
        optimized = optimize_file_operations([])
        self.assertEqual(optimized, [])
    
    def test_optimize_file_operations_single_file(self):
        """Test file operations optimization with single file."""
        file_paths = ["single_file.py"]
        optimized = optimize_file_operations(file_paths)
        self.assertEqual(optimized, file_paths)


class TestMemoryEfficientFileReader(unittest.TestCase):
    """Test memory_efficient_file_reader function."""
    
    def test_memory_efficient_file_reader(self):
        """Test memory efficient file reader."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!\nThis is a test file.\nWith multiple lines.")
            f.flush()
            
            try:
                content = memory_efficient_file_reader(f.name)
                self.assertIn("Hello, World!", content)
                self.assertIn("This is a test file", content)
                self.assertIn("With multiple lines", content)
            finally:
                os.unlink(f.name)
    
    def test_memory_efficient_file_reader_nonexistent_file(self):
        """Test memory efficient file reader with nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            memory_efficient_file_reader("nonexistent_file.txt")
    
    def test_memory_efficient_file_reader_custom_chunk_size(self):
        """Test memory efficient file reader with custom chunk size."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            f.flush()
            
            try:
                content = memory_efficient_file_reader(f.name, chunk_size=5)
                self.assertEqual(content, "Test content")
            finally:
                os.unlink(f.name)


class TestProfileMemoryUsage(unittest.TestCase):
    """Test profile_memory_usage decorator."""
    
    def test_profile_memory_usage_decorator(self):
        """Test profile_memory_usage decorator functionality."""
        @profile_memory_usage
        def test_func(x):
            return [i for i in range(x)]
        
        result = test_func(1000)
        self.assertEqual(len(result), 1000)
        
        # Check that memory usage was recorded
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)
        self.assertGreaterEqual(metrics.memory_usage, 0)
    
    def test_profile_memory_usage_with_exception(self):
        """Test profile_memory_usage decorator with exception."""
        @profile_memory_usage
        def test_func():
            raise ValueError("test error")
        
        with self.assertRaises(ValueError):
            test_func()
        
        # Check that memory usage was still recorded
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)


class TestGetPerformanceSummary(unittest.TestCase):
    """Test get_performance_summary function."""
    
    def test_get_performance_summary(self):
        """Test getting performance summary."""
        # Record some metrics
        monitor = get_performance_monitor()
        monitor.record_execution_time("func1", 1.0)
        monitor.record_memory_usage("func1", 1024)
        monitor.record_execution_time("func2", 2.0)
        
        summary = get_performance_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn("total_functions", summary)
        self.assertIn("total_execution_time", summary)
        self.assertIn("total_memory_usage", summary)
        self.assertIn("functions", summary)
        
        self.assertEqual(summary["total_functions"], 2)
        self.assertEqual(summary["total_execution_time"], 3.0)
        self.assertEqual(summary["total_memory_usage"], 1024)


class TestClearPerformanceData(unittest.TestCase):
    """Test clear_performance_data function."""
    
    def test_clear_performance_data(self):
        """Test clearing performance data."""
        # Record some metrics
        monitor = get_performance_monitor()
        monitor.record_execution_time("func1", 1.0)
        self.assertGreater(len(monitor.metrics), 0)
        
        clear_performance_data()
        self.assertEqual(len(monitor.metrics), 0)


class TestExpensiveOperation(unittest.TestCase):
    """Test expensive_operation function."""
    
    def test_expensive_operation(self):
        """Test expensive operation function."""
        result = expensive_operation("test data")
        self.assertEqual(result, "Processed: test data")
    
    def test_expensive_operation_empty_string(self):
        """Test expensive operation with empty string."""
        result = expensive_operation("")
        self.assertEqual(result, "Processed: ")


class TestProcessLargeFile(unittest.TestCase):
    """Test process_large_file function."""
    
    def test_process_large_file(self):
        """Test processing large file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("line1\nline2\nline3\n")
            f.flush()
            
            try:
                result = process_large_file(f.name)
                self.assertEqual(len(result), 3)
                self.assertIn("line1", result)
                self.assertIn("line2", result)
                self.assertIn("line3", result)
            finally:
                os.unlink(f.name)
    
    def test_process_large_file_nonexistent(self):
        """Test processing nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            process_large_file("nonexistent.txt")


class TestOptimizeQualityGatesExecution(unittest.TestCase):
    """Test optimize_quality_gates_execution function."""
    
    def test_optimize_quality_gates_execution(self):
        """Test optimizing quality gates execution."""
        # Mock some quality gate functions
        def mock_lint_check():
            return True, None
        
        def mock_type_check():
            return True, None
        
        def mock_security_check():
            return True, None
        
        def mock_coverage_check():
            return True, None
        
        gates = [
            ("lint", mock_lint_check),
            ("type", mock_type_check),
            ("security", mock_security_check),
            ("coverage", mock_coverage_check)
        ]
        
        results = optimize_quality_gates_execution(gates)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 4)
        
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], bool)
    
    def test_optimize_quality_gates_execution_empty(self):
        """Test optimizing quality gates execution with empty list."""
        results = optimize_quality_gates_execution([])
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
