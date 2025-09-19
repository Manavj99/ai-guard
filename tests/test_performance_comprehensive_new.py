"""Comprehensive tests for performance.py to achieve high coverage."""

import pytest
import time
import threading
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from concurrent.futures import ThreadPoolExecutor

from src.ai_guard.performance import (
    PerformanceMetrics, PerformanceMonitor, get_performance_monitor,
    time_function, timed_function, SimpleCache, get_cache, cached,
    cache_result, parallel_execute, batch_process, optimize_file_operations,
    memory_efficient_file_reader, profile_memory_usage, get_performance_summary,
    clear_performance_data, reset_global_monitor, expensive_operation,
    process_large_file
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=1024.0,
            cache_hits=5,
            cache_misses=2
        )
        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.5
        assert metric.memory_usage == 1024.0
        assert metric.cache_hits == 5
        assert metric.cache_misses == 2
    
    def test_performance_metrics_minimal(self):
        """Test creating PerformanceMetrics with minimal data."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.0
        )
        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.0
        assert metric.memory_usage is None
        assert metric.cache_hits is None
        assert metric.cache_misses is None


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.metrics == []
        assert isinstance(monitor._lock, threading.Lock)
    
    def test_record_metric(self):
        """Test recording a metric."""
        monitor = PerformanceMonitor()
        metric = PerformanceMetrics("test_func", 1.0)
        
        monitor.record_metric(metric)
        assert len(monitor.metrics) == 1
        assert monitor.metrics[0] == metric
    
    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        monitor = PerformanceMonitor()
        metric1 = PerformanceMetrics("func1", 1.0)
        metric2 = PerformanceMetrics("func2", 2.0)
        
        monitor.record_metric(metric1)
        monitor.record_metric(metric2)
        assert len(monitor.metrics) == 2
    
    def test_get_average_time_existing_function(self):
        """Test getting average time for existing function."""
        monitor = PerformanceMonitor()
        metric1 = PerformanceMetrics("test_func", 1.0)
        metric2 = PerformanceMetrics("test_func", 3.0)
        
        monitor.record_metric(metric1)
        monitor.record_metric(metric2)
        
        avg_time = monitor.get_average_time("test_func")
        assert avg_time == 2.0
    
    def test_get_average_time_nonexistent_function(self):
        """Test getting average time for non-existent function."""
        monitor = PerformanceMonitor()
        avg_time = monitor.get_average_time("nonexistent")
        assert avg_time is None
    
    def test_get_total_metrics(self):
        """Test getting total metrics count."""
        monitor = PerformanceMonitor()
        assert monitor.get_total_metrics() == 0
        
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        assert monitor.get_total_metrics() == 1
        
        monitor.record_metric(PerformanceMetrics("func2", 2.0))
        assert monitor.get_total_metrics() == 2


class TestGetPerformanceMonitor:
    """Test get_performance_monitor function."""
    
    def test_get_performance_monitor_singleton(self):
        """Test that get_performance_monitor returns singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        assert monitor1 is monitor2


class TestTimeFunction:
    """Test time_function decorator."""
    
    def test_time_function_decorator(self):
        """Test time_function as decorator."""
        @time_function()
        def test_func():
            time.sleep(0.01)
            return "test"
        
        result = test_func()
        assert result == "test"
    
    def test_time_function_with_monitor(self):
        """Test time_function with specific monitor."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"
        assert monitor.get_total_metrics() == 1


class TestTimedFunction:
    """Test timed_function decorator."""
    
    def test_timed_function_decorator(self):
        """Test timed_function as decorator."""
        @timed_function()
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"
    
    def test_timed_function_with_monitor(self):
        """Test timed_function with specific monitor."""
        monitor = PerformanceMonitor()
        
        @timed_function(monitor)
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"


class TestSimpleCache:
    """Test SimpleCache class."""
    
    def test_simple_cache_initialization(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache()
        assert len(cache) == 0
        assert cache.max_size == 1000
    
    def test_simple_cache_with_max_size(self):
        """Test SimpleCache with custom max size."""
        cache = SimpleCache(max_size=5)
        assert cache.max_size == 5
    
    def test_simple_cache_set_get(self):
        """Test setting and getting cache values."""
        cache = SimpleCache()
        cache["key1"] = "value1"
        assert cache["key1"] == "value1"
    
    def test_simple_cache_max_size_eviction(self):
        """Test cache eviction when max size exceeded."""
        cache = SimpleCache(max_size=2)
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        cache["key3"] = "value3"  # Should evict key1
        
        assert "key1" not in cache
        assert cache["key2"] == "value2"
        assert cache["key3"] == "value3"


class TestGetCache:
    """Test get_cache function."""
    
    def test_get_cache_singleton(self):
        """Test that get_cache returns singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2


class TestCached:
    """Test cached decorator."""
    
    def test_cached_decorator(self):
        """Test cached decorator."""
        call_count = 0
        
        @cached()
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Function called only once
    
    def test_cached_with_cache(self):
        """Test cached decorator with specific cache."""
        cache = SimpleCache()
        call_count = 0
        
        @cached(cache=cache)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result = test_func(5)
        assert result == 10
        assert call_count == 1
        assert cache["test_func(5,)"] == 10


class TestCacheResult:
    """Test cache_result decorator."""
    
    def test_cache_result_decorator(self):
        """Test cache_result decorator."""
        call_count = 0
        
        @cache_result(max_size=5)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1


class TestParallelExecute:
    """Test parallel_execute function."""
    
    def test_parallel_execute_basic(self):
        """Test basic parallel execution."""
        def func(x):
            return x * 2
        
        results = parallel_execute([func], [1, 2, 3])
        assert results == [2, 4, 6]
    
    def test_parallel_execute_multiple_functions(self):
        """Test parallel execution with multiple functions."""
        def func1(x):
            return x * 2
        
        def func2(x):
            return x + 1
        
        results = parallel_execute([func1, func2], [1, 2])
        assert len(results) == 2
        assert results[0] == [2, 4]  # func1 results
        assert results[1] == [2, 3]  # func2 results


class TestBatchProcess:
    """Test batch_process function."""
    
    def test_batch_process_basic(self):
        """Test basic batch processing."""
        def process_item(item):
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = batch_process(items, process_item, batch_size=2)
        assert results == [2, 4, 6, 8, 10]
    
    def test_batch_process_single_batch(self):
        """Test batch processing with single batch."""
        def process_item(item):
            return item * 2
        
        items = [1, 2]
        results = batch_process(items, process_item, batch_size=5)
        assert results == [2, 4]


class TestOptimizeFileOperations:
    """Test optimize_file_operations function."""
    
    def test_optimize_file_operations(self):
        """Test file operations optimization."""
        def file_op(path):
            return f"processed_{path}"
        
        optimized_op = optimize_file_operations(file_op)
        result = optimized_op("test.txt")
        assert result == "processed_test.txt"


class TestMemoryEfficientFileReader:
    """Test memory_efficient_file_reader function."""
    
    def test_memory_efficient_file_reader(self):
        """Test memory efficient file reading."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello\nWorld\nTest")
            temp_path = f.name
        
        try:
            content = memory_efficient_file_reader(temp_path)
            assert "Hello" in content
            assert "World" in content
            assert "Test" in content
        finally:
            os.unlink(temp_path)
    
    def test_memory_efficient_file_reader_chunk_size(self):
        """Test memory efficient file reading with custom chunk size."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello World")
            temp_path = f.name
        
        try:
            content = memory_efficient_file_reader(temp_path, chunk_size=5)
            assert content == "Hello World"
        finally:
            os.unlink(temp_path)


class TestProfileMemoryUsage:
    """Test profile_memory_usage decorator."""
    
    def test_profile_memory_usage_decorator(self):
        """Test profile_memory_usage decorator."""
        @profile_memory_usage
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""
    
    def test_get_performance_summary(self):
        """Test getting performance summary."""
        summary = get_performance_summary()
        assert isinstance(summary, dict)
        assert "total_functions" in summary
        assert "average_execution_time" in summary


class TestClearPerformanceData:
    """Test clear_performance_data function."""
    
    def test_clear_performance_data(self):
        """Test clearing performance data."""
        clear_performance_data()
        # Should not raise any exceptions


class TestResetGlobalMonitor:
    """Test reset_global_monitor function."""
    
    def test_reset_global_monitor(self):
        """Test resetting global monitor."""
        reset_global_monitor()
        # Should not raise any exceptions


class TestExpensiveOperation:
    """Test expensive_operation function."""
    
    def test_expensive_operation(self):
        """Test expensive operation."""
        result = expensive_operation("test")
        assert isinstance(result, str)
        assert "test" in result


class TestProcessLargeFile:
    """Test process_large_file function."""
    
    def test_process_large_file(self):
        """Test processing large file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("line1\nline2\nline3")
            temp_path = f.name
        
        try:
            results = process_large_file(temp_path)
            assert isinstance(results, list)
            assert len(results) == 3
        finally:
            os.unlink(temp_path)