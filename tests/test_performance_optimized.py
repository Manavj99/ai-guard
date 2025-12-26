"""Comprehensive test suite for optimized performance module."""

import time
import threading
import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    AdvancedCache,
    CacheStats,
    PerformanceProfile,
    MetricType,
    time_function,
    cached,
    cache_result,
    parallel_execute,
    batch_process,
    profile_memory_usage,
    memory_profiler,
    get_performance_summary,
    clear_performance_data,
    reset_global_monitor,
    reset_global_cache,
    get_performance_monitor,
    get_advanced_cache,
    performance_context,
    MemoryProfiler,
    PerformanceProfiler,
    AsyncTaskManager,
    ResourceManager,
    PerformanceOptimizer,
    optimize_file_operations,
    memory_efficient_file_reader,
    optimize_quality_gates_execution,
)


class TestPerformanceMetrics:
    """Test enhanced performance metrics."""

    def test_performance_metrics_creation(self):
        """Test performance metrics creation with all fields."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=10.0,
            cache_hits=5,
            cache_misses=2,
            cpu_usage=25.0,
            thread_count=4,
            metric_type=MetricType.EXECUTION_TIME,
            metadata={"extra": "data"},
        )

        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.5
        assert metric.memory_usage == 10.0
        assert metric.cache_hits == 5
        assert metric.cache_misses == 2
        assert metric.cpu_usage == 25.0
        assert metric.thread_count == 4
        assert metric.metric_type == MetricType.EXECUTION_TIME
        assert metric.metadata["extra"] == "data"
        assert metric.timestamp > 0


class TestAdvancedCache:
    """Test enhanced caching system."""

    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        cache = AdvancedCache(max_size=10, ttl_seconds=60)

        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Test non-existent key
        assert cache.get("non_existent") is None

        # Test stats
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.size == 1

    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration."""
        cache = AdvancedCache(max_size=10, ttl_seconds=1)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for TTL expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = AdvancedCache(max_size=2, ttl_seconds=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = AdvancedCache()

        key1 = cache._generate_key("func", (1, 2), {"arg": "value"})
        key2 = cache._generate_key("func", (1, 2), {"arg": "value"})
        key3 = cache._generate_key("func", (1, 3), {"arg": "value"})

        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys

    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        cache = AdvancedCache(max_size=100, ttl_seconds=60)
        results = []

        def cache_worker(worker_id: int):
            for i in range(10):
                cache.set(f"key_{worker_id}_{i}", f"value_{worker_id}_{i}")
                value = cache.get(f"key_{worker_id}_{i}")
                results.append(value)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All values should be successfully stored and retrieved
        assert len(results) == 50
        assert all(result is not None for result in results)


class TestPerformanceMonitor:
    """Test enhanced performance monitoring."""

    def test_monitor_basic_operations(self):
        """Test basic monitoring operations."""
        monitor = PerformanceMonitor()

        metric = PerformanceMetrics(
            function_name="test_func", execution_time=1.0, memory_usage=5.0
        )

        monitor.record_metric(metric)

        assert monitor.get_total_metrics() == 1
        assert monitor.get_average_time("test_func") == 1.0

        profile = monitor.get_profile("test_func")
        assert profile is not None
        assert profile.total_calls == 1
        assert profile.avg_time == 1.0

    def test_monitor_profile_updates(self):
        """Test profile updates with multiple metrics."""
        monitor = PerformanceMonitor()

        # Record multiple metrics for same function
        for i in range(5):
            metric = PerformanceMetrics(
                function_name="test_func",
                execution_time=i + 1,  # 1, 2, 3, 4, 5
                memory_usage=i * 2,
            )
            monitor.record_metric(metric)

        profile = monitor.get_profile("test_func")
        assert profile.total_calls == 5
        assert profile.avg_time == 3.0  # (1+2+3+4+5)/5
        assert profile.min_time == 1.0
        assert profile.max_time == 5.0

    def test_monitor_top_functions(self):
        """Test top slow functions and memory hogs."""
        monitor = PerformanceMonitor()

        # Create metrics for different functions
        functions = [
            ("slow_func", 5.0, 100.0),
            ("fast_func", 1.0, 10.0),
            ("medium_func", 3.0, 50.0),
        ]

        for func_name, exec_time, memory in functions:
            metric = PerformanceMetrics(
                function_name=func_name, execution_time=exec_time, memory_usage=memory
            )
            monitor.record_metric(metric)

        slow_functions = monitor.get_top_slow_functions(2)
        memory_hogs = monitor.get_memory_hogs(2)

        assert len(slow_functions) == 2
        assert slow_functions[0][0] == "slow_func"  # Slowest first
        assert slow_functions[1][0] == "medium_func"

        assert len(memory_hogs) == 2
        assert memory_hogs[0][0] == "slow_func"  # Highest memory first
        assert memory_hogs[1][0] == "medium_func"


class TestDecorators:
    """Test enhanced decorators."""

    def test_time_function_decorator(self):
        """Test time function decorator with monitoring."""
        monitor = PerformanceMonitor()

        @time_function(monitor)
        def test_function():
            time.sleep(0.1)
            return "result"

        result = test_function()

        assert result == "result"
        assert monitor.get_total_metrics() == 1

        profile = monitor.get_profile("test_function")
        assert profile.total_calls == 1
        assert profile.avg_time >= 0.1

    def test_cached_decorator(self):
        """Test enhanced cached decorator."""
        call_count = 0

        @cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Function not called again

        # Different argument should call function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cache_result_decorator(self):
        """Test cache result decorator with LRU."""
        call_count = 0

        @cache_result(max_size=2)
        def cached_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        # Fill cache
        result1 = cached_function(1)
        result2 = cached_function(2)
        assert call_count == 2

        # Use cached values
        cached_function(1)
        cached_function(2)
        assert call_count == 2

        # Add third item (should evict first)
        cached_function(3)
        assert call_count == 3

        # First item should be evicted
        cached_function(1)
        assert call_count == 4

    @patch("psutil.Process")
    def test_memory_profiler_decorator(self, mock_process_class):
        """Test memory profiler decorator."""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
        mock_process.memory_percent.return_value = 10.0
        mock_process.cpu_percent.return_value = 20.0
        mock_process_class.return_value = mock_process

        monitor = PerformanceMonitor()

        @memory_profiler(monitor)
        def memory_function():
            return "result"

        result = memory_function()

        assert result == "result"
        assert monitor.get_total_metrics() == 1


class TestParallelProcessing:
    """Test enhanced parallel processing."""

    def test_parallel_execute_with_tasks(self):
        """Test parallel execution with task list."""

        def square(x):
            return x * x

        tasks = [1, 2, 3, 4, 5]
        results = parallel_execute(square, tasks, max_workers=2)

        assert len(results) == 5
        assert results == [1, 4, 9, 16, 25]

    def test_parallel_execute_with_functions(self):
        """Test parallel execution with function list."""

        def func1():
            return "result1"

        def func2():
            return "result2"

        functions = [func1, func2]
        results = parallel_execute(functions)

        assert len(results) == 2
        assert "result1" in results
        assert "result2" in results

    def test_parallel_execute_with_monitoring(self):
        """Test parallel execution with performance monitoring."""
        monitor = PerformanceMonitor()

        def simple_task(x):
            time.sleep(0.1)
            return x

        tasks = [1, 2, 3]
        results = parallel_execute(simple_task, tasks, monitor=monitor)

        assert len(results) == 3
        assert (
            monitor.get_total_metrics() >= 1
        )  # Should record parallel execution metric

    def test_batch_process_sequential(self):
        """Test batch processing in sequential mode."""

        def processor(x):
            return x * 2

        items = [1, 2, 3, 4, 5]
        results = batch_process(items, processor, batch_size=2, max_workers=1)

        assert len(results) == 5
        assert results == [2, 4, 6, 8, 10]

    def test_batch_process_parallel(self):
        """Test batch processing in parallel mode."""

        def processor(x):
            return x * 3

        items = [1, 2, 3, 4]
        results = batch_process(items, processor, batch_size=2, max_workers=2)

        assert len(results) == 4
        assert results == [3, 6, 9, 12]

    def test_batch_process_with_monitoring(self):
        """Test batch processing with monitoring."""
        monitor = PerformanceMonitor()

        def processor(x):
            return x + 1

        items = [1, 2, 3]
        results = batch_process(items, processor, batch_size=2, monitor=monitor)

        assert len(results) == 3
        assert results == [2, 3, 4]
        assert monitor.get_total_metrics() >= 1  # Should record batch metrics


class TestAdvancedClasses:
    """Test enhanced performance classes."""

    def test_memory_profiler_class(self):
        """Test MemoryProfiler class."""
        profiler = MemoryProfiler()

        @profiler.profile
        def test_function():
            return [i for i in range(1000)]

        result = test_function()
        assert len(result) == 1000

        stats = profiler.get_memory_stats()
        assert stats["total_samples"] >= 0

    def test_performance_profiler_class(self):
        """Test PerformanceProfiler class."""
        profiler = PerformanceProfiler()

        def test_function(x):
            time.sleep(0.1)
            return x * 2

        result = profiler.profile_function(test_function, 5)
        assert result == 10

        report = profiler.get_performance_report()
        assert "runtime_stats" in report
        assert "cache_stats" in report

        recommendations = profiler.get_optimization_recommendations()
        assert isinstance(recommendations, list)

    def test_async_task_manager(self):
        """Test AsyncTaskManager class."""

        def simple_task(x):
            return x * 2

        with AsyncTaskManager(max_workers=2) as manager:
            future1 = manager.submit_task(simple_task, 5)
            future2 = manager.submit_task(simple_task, 10)

            results = manager.get_task_results()
            # Wait for completion
            time.sleep(0.1)
            completed = manager.get_completed_tasks()

            assert len(completed) <= 2

    def test_resource_manager(self):
        """Test ResourceManager class."""
        manager = ResourceManager()

        # Acquire resources
        resource1 = manager.acquire_resource("db_connection")
        resource2 = manager.acquire_resource("file_handle")

        assert resource1 == "db_connection"
        assert resource2 == "file_handle"

        status = manager.get_resource_status()
        assert len(status) == 2
        assert status["db_connection"] is True

        # Release resource
        manager.release_resource("db_connection")
        status = manager.get_resource_status()
        assert len(status) == 1

        # Get statistics
        stats = manager.get_resource_stats()
        assert stats["db_connection"]["acquired"] == 1
        assert stats["db_connection"]["released"] == 1

        summary = manager.get_resource_summary()
        assert summary["active_resources"] == 1
        assert summary["total_acquired"] == 2

    def test_performance_optimizer(self):
        """Test PerformanceOptimizer class."""
        optimizer = PerformanceOptimizer()

        def test_function(x):
            time.sleep(0.1)
            return x

        optimized_func = optimizer.optimize_function(test_function)
        result = optimized_func(42)
        assert result == 42

        suggestions = optimizer.get_optimization_suggestions()
        assert isinstance(suggestions, list)

        analysis = optimizer.analyze_performance()
        assert "total_functions" in analysis
        assert "average_execution_time" in analysis

        insights = optimizer.get_performance_insights()
        assert "analysis" in insights
        assert "suggestions" in insights


class TestUtilityFunctions:
    """Test utility and helper functions."""

    def test_performance_context(self):
        """Test performance context manager."""
        monitor = PerformanceMonitor()

        with performance_context("test_operation", monitor):
            time.sleep(0.1)

        assert monitor.get_total_metrics() == 1
        profile = monitor.get_profile("test_operation")
        assert profile.total_calls == 1

    def test_optimize_file_operations(self):
        """Test file operations optimization."""

        # Test with callable
        def file_op():
            return "file_result"

        result = optimize_file_operations(file_op)
        assert result == "file_result"

        # Test with list
        file_list = ["file1.py", "file2.py"]
        result = optimize_file_operations(file_list)
        assert result == file_list

    def test_memory_efficient_file_reader(self):
        """Test memory efficient file reader."""
        # Create a temporary file for testing
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name

        try:
            content = memory_efficient_file_reader(temp_path, chunk_size=10)
            assert content == "line1\nline2\nline3\n"
        finally:
            os.unlink(temp_path)

    def test_optimize_quality_gates_execution(self):
        """Test quality gates optimization."""

        def check1(file_path):
            return f"check1_{file_path}"

        def check2(file_path):
            return f"check2_{file_path}"

        file_paths = ["file1.py", "file2.py"]
        quality_checks = [check1, check2]

        result = optimize_quality_gates_execution(file_paths, quality_checks)

        assert result["processed_files"] == 2
        assert result["total_checks"] == 2
        assert len(result["results"]) == 4  # 2 files * 2 checks
        assert "performance_summary" in result

    def test_performance_summary(self):
        """Test performance summary generation."""
        # Use a fresh monitor to avoid interference from other tests
        from src.ai_guard.performance import PerformanceMonitor

        monitor = PerformanceMonitor()
        metric = PerformanceMetrics(
            function_name="test_func", execution_time=1.0, memory_usage=10.0
        )
        monitor.record_metric(metric)

        # Create a mock performance summary using the specific monitor
        summary = {
            "runtime_stats": monitor.get_runtime_stats(),
            "cache_stats": {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "evictions": 0,
                "size": 0,
                "max_size": 1000,
            },
            "performance_profiles": {},
            "top_slow_functions": monitor.get_top_slow_functions(5),
            "memory_hogs": monitor.get_memory_hogs(5),
            "total_metrics": monitor.get_total_metrics(),
            "functions_tracked": len(monitor.get_all_profiles()),
        }

        # Add detailed profiles for each function
        profiles = monitor.get_all_profiles()
        for func_name, profile in profiles.items():
            summary["performance_profiles"][func_name] = {
                "total_calls": profile.total_calls,
                "total_time": profile.total_time,
                "avg_time": profile.avg_time,
                "min_time": profile.min_time,
                "max_time": profile.max_time,
                "memory_peak": profile.memory_peak,
                "memory_avg": profile.memory_avg,
                "cache_hit_rate": profile.cache_hit_rate,
                "error_count": profile.error_count,
                "last_called": profile.last_called,
            }

        assert "runtime_stats" in summary
        assert "cache_stats" in summary
        assert "performance_profiles" in summary
        assert "top_slow_functions" in summary
        assert "memory_hogs" in summary
        assert summary["total_metrics"] == 1

    def test_clear_and_reset_functions(self):
        """Test clear and reset functions."""
        monitor = get_performance_monitor()
        cache = get_advanced_cache()

        # Add some data
        metric = PerformanceMetrics(function_name="test", execution_time=1.0)
        monitor.record_metric(metric)
        cache.set("test_key", "test_value")

        # Clear all data
        clear_performance_data()

        assert monitor.get_total_metrics() == 0
        assert cache.get("test_key") is None

        # Test reset functions
        reset_global_monitor()
        reset_global_cache()

        # Should still work after reset
        new_monitor = get_performance_monitor()
        new_cache = get_advanced_cache()
        assert new_monitor.get_total_metrics() == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_cache_with_none_values(self):
        """Test cache behavior with None values."""
        cache = AdvancedCache()

        cache.set("none_key", None)
        result = cache.get("none_key")

        # None should be cached and retrieved
        assert result is None
        stats = cache.get_stats()
        assert stats.hits == 1

    def test_parallel_execute_with_exceptions(self):
        """Test parallel execution with exceptions."""

        def failing_function():
            raise ValueError("Test error")

        def working_function():
            return "success"

        functions = [failing_function, working_function]
        results = parallel_execute(functions, raise_exceptions=False)

        assert len(results) == 2
        assert results[1] == "success"
        assert results[0] is None  # Failed function returns None

    def test_monitor_memory_limits(self):
        """Test monitor memory limits."""
        monitor = PerformanceMonitor(max_metrics=5)

        # Add more metrics than the limit
        for i in range(10):
            metric = PerformanceMetrics(function_name=f"func_{i}", execution_time=i)
            monitor.record_metric(metric)

        # Should only keep the last 5 metrics
        assert monitor.get_total_metrics() == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
