"""Focused tests for performance.py to achieve high coverage."""

import time
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    get_performance_monitor,
    time_function,
    timed_function,
    SimpleCache,
    get_cache,
    cached,
    cache_result,
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    profile_memory_usage,
    get_performance_summary,
    clear_performance_data,
    reset_global_monitor,
    expensive_operation,
    process_large_file,
    optimize_quality_gates_execution,
    clear_cache,
    MemoryProfiler,
    memory_profiler,
    PerformanceProfiler,
    AsyncTaskManager,
    ResourceManager,
    PerformanceOptimizer,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_performance_metrics_init(self):
        """Test PerformanceMetrics initialization."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=100.0,
            cache_hits=5,
            cache_misses=2,
        )
        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.5
        assert metric.memory_usage == 100.0
        assert metric.cache_hits == 5
        assert metric.cache_misses == 2

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metric = PerformanceMetrics(function_name="test_func", execution_time=1.0)
        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.0
        assert metric.memory_usage is None
        assert metric.cache_hits is None
        assert metric.cache_misses is None


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def test_performance_monitor_init(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.metrics == []
        assert monitor.get_total_metrics() == 0

    def test_record_metric(self):
        """Test recording a metric."""
        monitor = PerformanceMonitor()
        metric = PerformanceMetrics("test_func", 1.5)
        monitor.record_metric(metric)
        assert monitor.get_total_metrics() == 1

    def test_get_average_time(self):
        """Test getting average execution time."""
        monitor = PerformanceMonitor()

        # Test with no metrics
        assert monitor.get_average_time("test_func") is None

        # Add some metrics
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        monitor.record_metric(PerformanceMetrics("test_func", 3.0))
        monitor.record_metric(PerformanceMetrics("other_func", 2.0))

        assert monitor.get_average_time("test_func") == 2.0
        assert monitor.get_average_time("other_func") == 2.0
        assert monitor.get_average_time("nonexistent") is None

    def test_clear_metrics(self):
        """Test clearing metrics."""
        monitor = PerformanceMonitor()
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        assert monitor.get_total_metrics() == 1

        monitor.clear_metrics()
        assert monitor.get_total_metrics() == 0


class TestGetPerformanceMonitor:
    """Test get_performance_monitor function."""

    def test_get_performance_monitor(self):
        """Test getting the global performance monitor."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_decorator(self):
        """Test time_function as decorator."""

        @time_function
        def test_func():
            time.sleep(0.01)  # Small delay to ensure measurable time
            return "test"

        result = test_func()
        assert result == "test"

        # Check that metric was recorded
        monitor = get_performance_monitor()
        assert monitor.get_total_metrics() > 0

    def test_time_function_with_monitor(self):
        """Test time_function with custom monitor."""
        custom_monitor = PerformanceMonitor()

        @time_function(custom_monitor)
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"

        # Check that metric was recorded in custom monitor
        assert custom_monitor.get_total_metrics() == 1

    def test_time_function_direct_call(self):
        """Test time_function called directly on function."""

        def test_func():
            return "test"

        wrapped_func = time_function(test_func)
        result = wrapped_func()
        assert result == "test"


class TestTimedFunction:
    """Test timed_function decorator."""

    def test_timed_function(self):
        """Test timed_function decorator."""

        @timed_function()
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"

    def test_timed_function_with_monitor(self):
        """Test timed_function with monitor."""
        monitor = PerformanceMonitor()

        @timed_function(monitor)
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"


class TestSimpleCache:
    """Test SimpleCache class."""

    def test_simple_cache_init(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache()
        assert cache.cache == {}
        assert cache.max_size == 1000

    def test_simple_cache_with_max_size(self):
        """Test SimpleCache with custom max size."""
        cache = SimpleCache(max_size=100)
        assert cache.max_size == 100

    def test_get_set(self):
        """Test getting and setting cache values."""
        cache = SimpleCache()

        # Test setting and getting
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Test getting non-existent key
        assert cache.get("nonexistent") is None

    def test_clear(self):
        """Test clearing cache."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.clear()
        assert cache.get("key1") is None

    def test_size(self):
        """Test getting cache size."""
        cache = SimpleCache()
        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_max_size_limit(self):
        """Test max size limit behavior."""
        cache = SimpleCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # This should trigger cleanup

        assert cache.size() <= 2


class TestGetCache:
    """Test get_cache function."""

    def test_get_cache(self):
        """Test getting the global cache."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)


class TestCached:
    """Test cached decorator."""

    def test_cached_basic(self):
        """Test basic caching functionality."""
        call_count = 0

        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args (should use cache)
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

        # Call with different args
        result3 = test_func(3)
        assert result3 == 6
        assert call_count == 2

    def test_cached_different_args(self):
        """Test cached with different arguments."""

        @cached
        def test_func(x, y):
            return x + y

        assert test_func(1, 2) == 3
        assert test_func(2, 3) == 5
        assert test_func(1, 2) == 3  # Should use cache


class TestCacheResult:
    """Test cache_result decorator."""

    def test_cache_result_basic(self):
        """Test basic cache_result functionality."""
        call_count = 0

        @cache_result()
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (should use cache)
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1

    def test_cache_result_with_max_size(self):
        """Test cache_result with custom max size."""

        @cache_result(max_size=2)
        def test_func(x):
            return x * 2

        assert test_func(1) == 2
        assert test_func(2) == 4
        assert test_func(3) == 6  # Should trigger cleanup


class TestParallelExecute:
    """Test parallel_execute function."""

    def test_parallel_execute_basic(self):
        """Test basic parallel execution."""

        def square(x):
            return x * x

        results = parallel_execute([square], [(2,), (3,), (4,)])
        assert results == [4, 9, 16]

    def test_parallel_execute_multiple_functions(self):
        """Test parallel execution with multiple functions."""

        def add_one(x):
            return x + 1

        def multiply_two(x):
            return x * 2

        results = parallel_execute([add_one, multiply_two], [(1,), (2,)])
        assert results == [2, 4]


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
        import tempfile
        import os

        # Create a temporary file with content
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3")
            temp_path = f.name

        try:
            content = memory_efficient_file_reader(temp_path)
            assert "Line 1" in content
            assert "Line 2" in content
            assert "Line 3" in content
        finally:
            os.unlink(temp_path)


class TestProfileMemoryUsage:
    """Test profile_memory_usage decorator."""

    def test_profile_memory_usage(self):
        """Test memory profiling decorator."""

        @profile_memory_usage
        def test_func():
            data = [i for i in range(1000)]
            return len(data)

        result = test_func()
        assert result == 1000


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        summary = get_performance_summary()
        assert isinstance(summary, dict)
        assert "total_functions" in summary
        assert "average_time" in summary
        assert "total_executions" in summary


class TestClearPerformanceData:
    """Test clear_performance_data function."""

    def test_clear_performance_data(self):
        """Test clearing performance data."""
        # Add some data first
        monitor = get_performance_monitor()
        monitor.record_metric(PerformanceMetrics("test", 1.0))

        clear_performance_data()
        assert monitor.get_total_metrics() == 0


class TestResetGlobalMonitor:
    """Test reset_global_monitor function."""

    def test_reset_global_monitor(self):
        """Test resetting global monitor."""
        reset_global_monitor()
        monitor = get_performance_monitor()
        assert monitor.get_total_metrics() == 0


class TestExpensiveOperation:
    """Test expensive_operation function."""

    def test_expensive_operation(self):
        """Test expensive operation."""
        result = expensive_operation("test")
        assert result == "processed_test"


class TestProcessLargeFile:
    """Test process_large_file function."""

    def test_process_large_file(self):
        """Test processing large file."""
        import tempfile
        import os

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3")
            temp_path = f.name

        try:
            results = process_large_file(temp_path)
            assert isinstance(results, list)
        finally:
            os.unlink(temp_path)


class TestOptimizeQualityGatesExecution:
    """Test optimize_quality_gates_execution function."""

    def test_optimize_quality_gates_execution(self):
        """Test quality gates optimization."""

        def gate_func():
            return True

        optimized_func = optimize_quality_gates_execution(gate_func)
        result = optimized_func()
        assert result is True


class TestClearCache:
    """Test clear_cache function."""

    def test_clear_cache(self):
        """Test clearing cache."""
        cache = get_cache()
        cache.set("test", "value")
        assert cache.get("test") == "value"

        clear_cache()
        assert cache.get("test") is None


class TestMemoryProfiler:
    """Test MemoryProfiler class."""

    def test_memory_profiler_init(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.monitor is not None
        assert profiler.start_time is None

    def test_start_profiling(self):
        """Test starting profiling."""
        profiler = MemoryProfiler()
        profiler.start_profiling()
        assert profiler.start_time is not None

    def test_stop_profiling(self):
        """Test stopping profiling."""
        profiler = MemoryProfiler()
        profiler.start_profiling()
        profiler.stop_profiling()
        assert profiler.start_time is not None

    def test_get_profile_report(self):
        """Test getting profile report."""
        profiler = MemoryProfiler()
        profiler.start_profiling()
        profiler.stop_profiling()
        report = profiler.get_profile_report()
        assert isinstance(report, dict)


class TestMemoryProfilerDecorator:
    """Test memory_profiler decorator."""

    def test_memory_profiler_decorator(self):
        """Test memory_profiler decorator."""

        @memory_profiler
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_performance_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.monitor is not None

    def test_start_profiling(self):
        """Test starting profiling."""
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        assert profiler.start_time is not None

    def test_stop_profiling(self):
        """Test stopping profiling."""
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        profiler.stop_profiling()
        assert profiler.start_time is not None

    def test_get_profile_report(self):
        """Test getting profile report."""
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        profiler.stop_profiling()
        report = profiler.get_profile_report()
        assert isinstance(report, dict)


class TestAsyncTaskManager:
    """Test AsyncTaskManager class."""

    def test_async_task_manager_init(self):
        """Test AsyncTaskManager initialization."""
        manager = AsyncTaskManager()
        assert manager.tasks == {}
        assert manager.results == {}

    def test_add_task(self):
        """Test adding a task."""
        manager = AsyncTaskManager()

        def test_task():
            return "result"

        task_id = manager.add_task(test_task)
        assert task_id in manager.tasks

    def test_get_result(self):
        """Test getting task result."""
        manager = AsyncTaskManager()

        def test_task():
            return "result"

        task_id = manager.add_task(test_task)
        result = manager.get_result(task_id)
        assert result == "result"


class TestResourceManager:
    """Test ResourceManager class."""

    def test_resource_manager_init(self):
        """Test ResourceManager initialization."""
        manager = ResourceManager()
        assert manager.resources == {}
        assert manager.usage == {}

    def test_allocate_resource(self):
        """Test allocating a resource."""
        manager = ResourceManager()
        resource_id = manager.allocate_resource("memory", 100)
        assert resource_id in manager.resources
        assert manager.resources[resource_id]["type"] == "memory"
        assert manager.resources[resource_id]["size"] == 100

    def test_deallocate_resource(self):
        """Test deallocating a resource."""
        manager = ResourceManager()
        resource_id = manager.allocate_resource("memory", 100)
        manager.deallocate_resource(resource_id)
        assert resource_id not in manager.resources


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""

    def test_performance_optimizer_init(self):
        """Test PerformanceOptimizer initialization."""
        optimizer = PerformanceOptimizer()
        assert optimizer.monitor is not None
        assert optimizer.cache is not None

    def test_optimize_function(self):
        """Test optimizing a function."""
        optimizer = PerformanceOptimizer()

        def test_func(x):
            return x * 2

        optimized_func = optimizer.optimize_function(test_func)
        result = optimized_func(5)
        assert result == 10
