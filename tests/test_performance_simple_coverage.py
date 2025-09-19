"""Simple comprehensive tests for performance.py to achieve 80+ coverage."""

import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
import tempfile
import os

from src.ai_guard.performance import (
    time_function, cached, get_performance_summary, PerformanceMonitor,
    PerformanceMetrics, get_performance_monitor, timed_function,
    SimpleCache, get_cache, cache_result, parallel_execute, batch_process,
    optimize_file_operations, memory_efficient_file_reader, profile_memory_usage,
    clear_performance_data, reset_global_monitor, expensive_operation,
    process_large_file, optimize_quality_gates_execution, clear_cache,
    MemoryProfiler, memory_profiler, PerformanceProfiler, AsyncTaskManager,
    ResourceManager
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""
    
    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics.execution_times == {}
        assert metrics.memory_usage == {}
        assert metrics.function_calls == {}
    
    def test_performance_metrics_record_execution_time(self):
        """Test PerformanceMetrics record_execution_time."""
        metrics = PerformanceMetrics()
        metrics.record_execution_time("test_func", 0.1)
        
        assert "test_func" in metrics.execution_times
        assert metrics.execution_times["test_func"] == [0.1]
    
    def test_performance_metrics_record_memory_usage(self):
        """Test PerformanceMetrics record_memory_usage."""
        metrics = PerformanceMetrics()
        metrics.record_memory_usage("test_func", 1024)
        
        assert "test_func" in metrics.memory_usage
        assert metrics.memory_usage["test_func"] == [1024]
    
    def test_performance_metrics_increment_function_calls(self):
        """Test PerformanceMetrics increment_function_calls."""
        metrics = PerformanceMetrics()
        metrics.increment_function_calls("test_func")
        metrics.increment_function_calls("test_func")
        
        assert metrics.function_calls["test_func"] == 2
    
    def test_performance_metrics_get_summary(self):
        """Test PerformanceMetrics get_summary."""
        metrics = PerformanceMetrics()
        metrics.record_execution_time("test_func", 0.1)
        metrics.record_memory_usage("test_func", 1024)
        metrics.increment_function_calls("test_func")
        
        summary = metrics.get_summary()
        assert isinstance(summary, dict)
        assert "execution_times" in summary
        assert "memory_usage" in summary
        assert "function_calls" in summary


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.metrics is not None
        assert isinstance(monitor.metrics, PerformanceMetrics)
    
    def test_performance_monitor_start_monitoring(self):
        """Test PerformanceMonitor start_monitoring."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        assert monitor.is_monitoring is True
    
    def test_performance_monitor_stop_monitoring(self):
        """Test PerformanceMonitor stop_monitoring."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        monitor.stop_monitoring()
        assert monitor.is_monitoring is False
    
    def test_performance_monitor_record_function(self):
        """Test PerformanceMonitor record_function."""
        monitor = PerformanceMonitor()
        
        @monitor.record_function
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
        assert "test_func" in monitor.metrics.function_calls


class TestTimeFunction:
    """Test time_function decorator."""
    
    def test_time_function_decorator(self):
        """Test time_function decorator functionality."""
        @time_function
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        assert result == "result"
        assert hasattr(test_func, '_execution_time')
        assert test_func._execution_time > 0
    
    def test_time_function_with_args(self):
        """Test time_function decorator with arguments."""
        @time_function
        def test_func_with_args(x, y=10):
            return x + y
        
        result = test_func_with_args(5, y=15)
        assert result == 20
        assert hasattr(test_func_with_args, '_execution_time')
    
    def test_time_function_with_exception(self):
        """Test time_function decorator with exception."""
        @time_function
        def test_func_exception():
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError):
            test_func_exception()
        
        assert hasattr(test_func_exception, '_execution_time')


class TestCached:
    """Test cached decorator."""
    
    def test_cached_decorator_basic(self):
        """Test cached decorator basic functionality."""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
    
    def test_cached_decorator_different_args(self):
        """Test cached decorator with different arguments."""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Different arguments should not use cache
        result1 = expensive_function(5)
        result2 = expensive_function(10)
        
        assert result1 == 10
        assert result2 == 20
        assert call_count == 2


class TestSimpleCache:
    """Test SimpleCache class."""
    
    def test_simple_cache_initialization(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache()
        assert len(cache) == 0
        assert cache.max_size == 100
        assert cache.ttl == 3600
    
    def test_simple_cache_set_get(self):
        """Test SimpleCache set and get methods."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
    
    def test_simple_cache_max_size(self):
        """Test SimpleCache max_size behavior."""
        cache = SimpleCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_simple_cache_clear(self):
        """Test SimpleCache clear method."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.clear()
        
        assert len(cache) == 0
        assert cache.get("key1") is None


class TestGetPerformanceMonitor:
    """Test get_performance_monitor function."""
    
    def test_get_performance_monitor(self):
        """Test get_performance_monitor function."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)


class TestTimedFunction:
    """Test timed_function decorator."""
    
    def test_timed_function_decorator(self):
        """Test timed_function decorator."""
        monitor = PerformanceMonitor()
        
        @timed_function(monitor)
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10


class TestGetCache:
    """Test get_cache function."""
    
    def test_get_cache(self):
        """Test get_cache function."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)


class TestCacheResult:
    """Test cache_result decorator."""
    
    def test_cache_result_decorator(self):
        """Test cache_result decorator."""
        call_count = 0
        
        @cache_result(max_size=10)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment


class TestParallelExecute:
    """Test parallel_execute function."""
    
    def test_parallel_execute(self):
        """Test parallel_execute function."""
        def test_func(x):
            return x * 2
        
        results = parallel_execute([test_func], [5])
        assert results == [10]
    
    def test_parallel_execute_multiple(self):
        """Test parallel_execute with multiple functions."""
        def func1(x):
            return x * 2
        
        def func2(x):
            return x + 1
        
        results = parallel_execute([func1, func2], [5, 5])
        assert results == [10, 6]


class TestBatchProcess:
    """Test batch_process function."""
    
    def test_batch_process(self):
        """Test batch_process function."""
        def process_item(item):
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = batch_process(items, process_item, batch_size=2)
        assert results == [2, 4, 6, 8, 10]


class TestOptimizeFileOperations:
    """Test optimize_file_operations function."""
    
    def test_optimize_file_operations(self):
        """Test optimize_file_operations function."""
        def file_operation(file_path):
            return f"processed {file_path}"
        
        optimized = optimize_file_operations(file_operation)
        assert optimized is not None


class TestMemoryEfficientFileReader:
    """Test memory_efficient_file_reader function."""
    
    def test_memory_efficient_file_reader(self):
        """Test memory_efficient_file_reader function."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            
            try:
                content = memory_efficient_file_reader(f.name)
                assert content == "test content"
            finally:
                os.unlink(f.name)
    
    def test_memory_efficient_file_reader_chunk_size(self):
        """Test memory_efficient_file_reader with custom chunk size."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            
            try:
                content = memory_efficient_file_reader(f.name, chunk_size=4)
                assert content == "test content"
            finally:
                os.unlink(f.name)


class TestProfileMemoryUsage:
    """Test profile_memory_usage decorator."""
    
    def test_profile_memory_usage_decorator(self):
        """Test profile_memory_usage decorator."""
        @profile_memory_usage
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""
    
    def test_get_performance_summary(self):
        """Test get_performance_summary function."""
        summary = get_performance_summary()
        assert isinstance(summary, dict)
        assert "execution_times" in summary
        assert "memory_usage" in summary
        assert "function_calls" in summary


class TestClearPerformanceData:
    """Test clear_performance_data function."""
    
    def test_clear_performance_data(self):
        """Test clear_performance_data function."""
        clear_performance_data()
        # Should not raise any exceptions


class TestResetGlobalMonitor:
    """Test reset_global_monitor function."""
    
    def test_reset_global_monitor(self):
        """Test reset_global_monitor function."""
        reset_global_monitor()
        # Should not raise any exceptions


class TestExpensiveOperation:
    """Test expensive_operation function."""
    
    def test_expensive_operation(self):
        """Test expensive_operation function."""
        result = expensive_operation("test")
        assert isinstance(result, str)
        assert result == "test"


class TestProcessLargeFile:
    """Test process_large_file function."""
    
    def test_process_large_file(self):
        """Test process_large_file function."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("line1\nline2\nline3")
            f.flush()
            
            try:
                lines = process_large_file(f.name)
                assert isinstance(lines, list)
                assert len(lines) == 3
            finally:
                os.unlink(f.name)


class TestOptimizeQualityGatesExecution:
    """Test optimize_quality_gates_execution function."""
    
    def test_optimize_quality_gates_execution(self):
        """Test optimize_quality_gates_execution function."""
        def quality_gate_func():
            return True
        
        optimized = optimize_quality_gates_execution(quality_gate_func)
        assert optimized is not None


class TestClearCache:
    """Test clear_cache function."""
    
    def test_clear_cache(self):
        """Test clear_cache function."""
        clear_cache()
        # Should not raise any exceptions


class TestMemoryProfiler:
    """Test MemoryProfiler class."""
    
    def test_memory_profiler_initialization(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.memory_data == {}
    
    def test_memory_profiler_profile(self):
        """Test MemoryProfiler profile method."""
        profiler = MemoryProfiler()
        
        @profiler.profile
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
        assert "test_func" in profiler.memory_data


class TestMemoryProfilerDecorator:
    """Test memory_profiler decorator."""
    
    def test_memory_profiler_decorator(self):
        """Test memory_profiler decorator."""
        @memory_profiler
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""
    
    def test_performance_profiler_initialization(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.profile_data == {}
    
    def test_performance_profiler_profile(self):
        """Test PerformanceProfiler profile method."""
        profiler = PerformanceProfiler()
        
        @profiler.profile
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
        assert "test_func" in profiler.profile_data


class TestAsyncTaskManager:
    """Test AsyncTaskManager class."""
    
    def test_async_task_manager_initialization(self):
        """Test AsyncTaskManager initialization."""
        manager = AsyncTaskManager()
        assert manager.tasks == []
        assert manager.is_running is False
    
    def test_async_task_manager_add_task(self):
        """Test AsyncTaskManager add_task method."""
        manager = AsyncTaskManager()
        
        def task_func():
            return "task result"
        
        manager.add_task(task_func)
        assert len(manager.tasks) == 1
    
    def test_async_task_manager_start_stop(self):
        """Test AsyncTaskManager start and stop methods."""
        manager = AsyncTaskManager()
        
        manager.start()
        assert manager.is_running is True
        
        manager.stop()
        assert manager.is_running is False


class TestResourceManager:
    """Test ResourceManager class."""
    
    def test_resource_manager_initialization(self):
        """Test ResourceManager initialization."""
        manager = ResourceManager()
        assert manager.resources == {}
        assert manager.max_resources == 10
    
    def test_resource_manager_acquire_release(self):
        """Test ResourceManager acquire and release methods."""
        manager = ResourceManager()
        
        resource = manager.acquire("resource1")
        assert resource is not None
        assert "resource1" in manager.resources
        
        manager.release("resource1")
        assert "resource1" not in manager.resources
    
    def test_resource_manager_max_resources(self):
        """Test ResourceManager max_resources behavior."""
        manager = ResourceManager(max_resources=1)
        
        resource1 = manager.acquire("resource1")
        assert resource1 is not None
        
        resource2 = manager.acquire("resource2")
        assert resource2 is None  # Should be None due to max_resources limit
