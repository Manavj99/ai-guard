"""Extended tests for performance module to improve coverage."""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock, mock_open
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    time_function,
    cache_result,
    parallel_execute,
    batch_process,
    PerformanceProfiler,
    MemoryProfiler,
    SimpleCache,
    AsyncTaskManager,
    ResourceManager,
    PerformanceOptimizer,
    get_performance_monitor,
    get_cache,
    cached,
    memory_efficient_file_reader,
    profile_memory_usage,
    get_performance_summary,
    clear_performance_data
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics object."""
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

    def test_performance_monitor_init(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.metrics == []
        assert monitor._lock is not None

    def test_record_metric(self):
        """Test recording a performance metric."""
        monitor = PerformanceMonitor()
        metric = PerformanceMetrics("test_func", 1.0)
        
        monitor.record_metric(metric)
        
        assert len(monitor.metrics) == 1
        assert monitor.metrics[0] == metric

    def test_get_average_time(self):
        """Test getting average execution time."""
        monitor = PerformanceMonitor()
        
        # Add multiple metrics for the same function
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        monitor.record_metric(PerformanceMetrics("test_func", 2.0))
        monitor.record_metric(PerformanceMetrics("other_func", 3.0))
        
        avg_time = monitor.get_average_time("test_func")
        assert avg_time == 1.5

    def test_get_average_time_no_data(self):
        """Test getting average time for non-existent function."""
        monitor = PerformanceMonitor()
        
        avg_time = monitor.get_average_time("nonexistent")
        assert avg_time is None

    def test_get_total_metrics(self):
        """Test getting total number of metrics."""
        monitor = PerformanceMonitor()
        
        assert monitor.get_total_metrics() == 0
        
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        monitor.record_metric(PerformanceMetrics("other_func", 2.0))
        
        assert monitor.get_total_metrics() == 2

    def test_clear_metrics(self):
        """Test clearing all metrics."""
        monitor = PerformanceMonitor()
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        
        monitor.clear_metrics()
        
        assert monitor.get_total_metrics() == 0


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_decorator(self):
        """Test time_function decorator."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        
        assert result == "result"
        assert monitor.get_total_metrics() == 1
        assert monitor.metrics[0].function_name == "test_func"
        assert monitor.metrics[0].execution_time > 0

    def test_time_function_global_monitor(self):
        """Test time_function with global monitor."""
        @time_function
        def test_func():
            return "result"
        
        result = test_func()
        
        assert result == "result"
        # Check global monitor was used
        global_monitor = get_performance_monitor()
        assert global_monitor.get_total_metrics() >= 1

    def test_time_function_with_exception(self):
        """Test time_function decorator with exception."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        def test_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            test_func()
        
        # Should still record the metric
        assert monitor.get_total_metrics() == 1


class TestCacheResult:
    """Test cache_result decorator."""

    def test_cache_result_decorator(self):
        """Test cache_result decorator."""
        @cache_result(max_size=2)
        def expensive_func(x):
            time.sleep(0.01)
            return x * 2
        
        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        
        # Second call should be cached
        result2 = expensive_func(5)
        assert result2 == 10
        
        # Different input
        result3 = expensive_func(3)
        assert result3 == 6

    def test_cache_result_size_limit(self):
        """Test cache_result with size limit."""
        @cache_result(max_size=2)
        def test_func(x):
            return x
        
        # Fill cache
        test_func(1)
        test_func(2)
        test_func(3)  # Should evict 1
        
        # 1 should be evicted
        result = test_func(1)  # Should recompute
        assert result == 1


class TestParallelExecute:
    """Test parallel_execute function."""

    def test_parallel_execute_functions(self):
        """Test parallel execution of functions."""
        def func1():
            time.sleep(0.01)
            return "result1"
        
        def func2():
            time.sleep(0.01)
            return "result2"
        
        results = parallel_execute([func1, func2])
        
        assert len(results) == 2
        assert "result1" in results
        assert "result2" in results

    def test_parallel_execute_with_tasks(self):
        """Test parallel execution with tasks."""
        def process_item(item):
            return item * 2
        
        tasks = [1, 2, 3]
        results = parallel_execute(process_item, tasks)
        
        assert len(results) == 3
        assert 2 in results
        assert 4 in results
        assert 6 in results

    def test_parallel_execute_with_exception(self):
        """Test parallel execution with exception."""
        def failing_func():
            raise ValueError("test error")
        
        def success_func():
            return "success"
        
        with pytest.raises(ValueError):
            parallel_execute([failing_func, success_func], raise_exceptions=True)

    def test_parallel_execute_without_exception(self):
        """Test parallel execution without raising exceptions."""
        def failing_func():
            raise ValueError("test error")
        
        def success_func():
            return "success"
        
        results = parallel_execute([failing_func, success_func], raise_exceptions=False)
        
        assert len(results) == 2
        assert None in results  # Failed function returns None
        assert "success" in results


class TestBatchProcess:
    """Test batch_process function."""

    def test_batch_process_with_processor(self):
        """Test batch processing with processor function."""
        def process_item(item):
            return item * 2
        
        items = list(range(10))
        results = batch_process(items, process_item, batch_size=3)
        
        assert len(results) == 10
        assert results[0] == 0
        assert results[1] == 2
        assert results[9] == 18

    def test_batch_process_without_processor(self):
        """Test batch processing without processor."""
        items = [1, 2, 3, 4, 5]
        results = batch_process(items, batch_size=2)
        
        assert results == items

    def test_batch_process_batch_processor(self):
        """Test batch processing with batch processor."""
        def batch_processor(batch):
            return [x * 2 for x in batch]
        
        items = list(range(6))
        results = batch_process(items, batch_processor, batch_size=2)
        
        assert len(results) == 6
        assert results[0] == 0
        assert results[1] == 2
        assert results[2] == 4


class TestSimpleCache:
    """Test SimpleCache class."""

    def test_cache_init(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache(ttl_seconds=300)
        assert cache.ttl == 300
        assert cache.size() == 0

    def test_cache_default_init(self):
        """Test SimpleCache initialization with defaults."""
        cache = SimpleCache()
        assert cache.ttl == 300

    def test_get_cache_hit(self):
        """Test cache hit."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        
        assert result == "value1"

    def test_get_cache_miss(self):
        """Test cache miss."""
        cache = SimpleCache()
        
        result = cache.get("nonexistent")
        
        assert result is None

    def test_set_cache_value(self):
        """Test setting cache value."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"

    def test_cache_size(self):
        """Test cache size."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.size() == 2

    def test_clear_cache(self):
        """Test clearing cache."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        
        cache.clear()
        
        assert cache.get("key1") is None

    def test_cache_keys_values_items(self):
        """Test cache keys, values, and items."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        keys = list(cache.keys())
        values = list(cache.values())
        items = list(cache.items())
        
        assert len(keys) == 2
        assert len(values) == 2
        assert len(items) == 2

    def test_cache_dict_access(self):
        """Test dict-like access to cache."""
        cache = SimpleCache()
        
        cache["key1"] = "value1"
        assert cache["key1"] == "value1"
        
        assert "key1" in cache
        assert len(cache) == 1

    def test_cache_update(self):
        """Test cache update method."""
        cache = SimpleCache()
        
        cache.update({"key1": "value1", "key2": "value2"})
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"


class TestAsyncTaskManager:
    """Test AsyncTaskManager class."""

    def test_task_manager_init(self):
        """Test AsyncTaskManager initialization."""
        manager = AsyncTaskManager(max_workers=4)
        assert manager.max_workers == 4
        assert manager.tasks == []
        assert manager.executor is None

    def test_task_manager_context(self):
        """Test AsyncTaskManager as context manager."""
        with AsyncTaskManager(max_workers=2) as manager:
            assert manager.executor is not None
            
            def test_task():
                return "result"
            
            future = manager.submit_task(test_task)
            assert future is not None

    def test_submit_task_without_context(self):
        """Test submitting task without context."""
        manager = AsyncTaskManager()
        
        with pytest.raises(RuntimeError):
            manager.submit_task(lambda: "test")


class TestResourceManager:
    """Test ResourceManager class."""

    def test_resource_manager_init(self):
        """Test ResourceManager initialization."""
        manager = ResourceManager()
        assert manager.resources == {}
        assert manager._lock is not None

    def test_acquire_resource(self):
        """Test acquiring a resource."""
        manager = ResourceManager()
        
        resource = manager.acquire_resource("resource1")
        
        assert resource == "resource1"
        assert manager.get_resource_status()["resource1"] is True

    def test_release_resource(self):
        """Test releasing a resource."""
        manager = ResourceManager()
        manager.acquire_resource("resource1")
        
        manager.release_resource("resource1")
        
        assert manager.get_resource_status() == {}

    def test_get_resource_status(self):
        """Test getting resource status."""
        manager = ResourceManager()
        manager.acquire_resource("resource1")
        manager.acquire_resource("resource2")
        
        status = manager.get_resource_status()
        
        assert len(status) == 2
        assert status["resource1"] is True
        assert status["resource2"] is True


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""

    def test_optimizer_init(self):
        """Test PerformanceOptimizer initialization."""
        optimizer = PerformanceOptimizer()
        assert optimizer.monitor is not None

    def test_optimize_function(self):
        """Test optimizing a function."""
        optimizer = PerformanceOptimizer()
        
        def test_func():
            return "result"
        
        optimized_func = optimizer.optimize_function(test_func)
        result = optimized_func()
        
        assert result == "result"
        assert optimizer.monitor.get_total_metrics() == 1

    def test_get_optimization_suggestions(self):
        """Test getting optimization suggestions."""
        optimizer = PerformanceOptimizer()
        
        suggestions = optimizer.get_optimization_suggestions()
        
        assert isinstance(suggestions, list)

    def test_analyze_performance(self):
        """Test analyzing performance."""
        optimizer = PerformanceOptimizer()
        
        analysis = optimizer.analyze_performance()
        
        assert isinstance(analysis, dict)
        assert "total_functions" in analysis
        assert "average_execution_time" in analysis
        assert "total_execution_time" in analysis


class TestGlobalFunctions:
    """Test global functions."""

    def test_get_performance_monitor(self):
        """Test getting performance monitor."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

    def test_get_cache(self):
        """Test getting cache."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)

    def test_cached_decorator(self):
        """Test cached decorator."""
        @cached(ttl_seconds=600)
        def test_func(x):
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == 10
        assert result2 == 10

    def test_memory_efficient_file_reader(self):
        """Test memory efficient file reader."""
        with patch('builtins.open', mock_open(read_data='test content')):
            content = memory_efficient_file_reader('test.txt')
            assert content == 'test content'

    def test_profile_memory_usage(self):
        """Test profile_memory_usage decorator."""
        @profile_memory_usage
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        summary = get_performance_summary()
        assert isinstance(summary, dict)
        assert "total_metrics" in summary
        assert "cache_size" in summary

    def test_clear_performance_data(self):
        """Test clearing performance data."""
        clear_performance_data()
        
        monitor = get_performance_monitor()
        cache = get_cache()
        
        assert monitor.get_total_metrics() == 0
        assert cache.size() == 0


class TestMemoryProfiler:
    """Test MemoryProfiler class."""

    def test_memory_profiler_init(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.memory_data == []

    def test_profile_decorator(self):
        """Test profile decorator."""
        profiler = MemoryProfiler()
        
        @profiler.profile
        def test_func():
            return "result"
        
        result = test_func()
        
        assert result == "result"
        # Memory data might be empty if psutil is not available
        assert isinstance(profiler.memory_data, list)


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.monitor is not None

    def test_profile_function(self):
        """Test profiling a function."""
        profiler = PerformanceProfiler()
        
        def test_func():
            return "result"
        
        result = profiler.profile_function(test_func)
        
        assert result == "result"
        assert profiler.monitor.get_total_metrics() == 1

    def test_get_performance_report(self):
        """Test getting performance report."""
        profiler = PerformanceProfiler()
        
        report = profiler.get_performance_report()
        
        assert isinstance(report, dict)
        assert "total_metrics" in report
        assert "functions_tracked" in report
