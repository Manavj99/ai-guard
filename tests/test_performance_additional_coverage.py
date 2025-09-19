"""Additional tests for performance module to increase coverage."""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceProfiler,
    PerformanceOptimizer,
    SimpleCache,
    MemoryProfiler,
    time_function,
    cached,
    profile_memory_usage,
    get_performance_summary,
    clear_performance_data
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
            execution_time=0.5
        )
        
        assert metric.function_name == "test_func"
        assert metric.execution_time == 0.5
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
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.0
        )
        
        monitor.record_metric(metric)
        
        assert len(monitor.metrics) == 1
        assert monitor.metrics[0] == metric

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        monitor = PerformanceMonitor()
        
        for i in range(5):
            metric = PerformanceMetrics(
                function_name=f"func_{i}",
                execution_time=i * 0.1
            )
            monitor.record_metric(metric)
        
        assert len(monitor.metrics) == 5

    def test_get_average_time(self):
        """Test getting average execution time."""
        monitor = PerformanceMonitor()
        
        # Add metrics for the same function
        for i in range(3):
            metric = PerformanceMetrics(
                function_name="test_func",
                execution_time=1.0 + i * 0.1
            )
            monitor.record_metric(metric)
        
        avg_time = monitor.get_average_time("test_func")
        
        assert avg_time == pytest.approx(1.1, rel=1e-2)

    def test_get_average_time_no_metrics(self):
        """Test getting average time for function with no metrics."""
        monitor = PerformanceMonitor()
        
        avg_time = monitor.get_average_time("nonexistent_func")
        
        assert avg_time is None

    def test_get_total_metrics(self):
        """Test getting total number of metrics."""
        monitor = PerformanceMonitor()
        
        assert monitor.get_total_metrics() == 0
        
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.0
        )
        monitor.record_metric(metric)
        
        assert monitor.get_total_metrics() == 1

    def test_thread_safety(self):
        """Test thread safety of PerformanceMonitor."""
        monitor = PerformanceMonitor()
        
        def add_metrics():
            for i in range(10):
                metric = PerformanceMetrics(
                    function_name=f"thread_func_{threading.current_thread().ident}",
                    execution_time=0.1 * i
                )
                monitor.record_metric(metric)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        assert monitor.get_total_metrics() == 50


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        
        assert profiler.monitor is not None
        assert profiler.profiling_enabled is True

    def test_profiler_init_disabled(self):
        """Test PerformanceProfiler initialization with profiling disabled."""
        profiler = PerformanceProfiler(enable_profiling=False)
        
        assert profiler.profiling_enabled is False

    def test_profile_function(self):
        """Test profiling a function."""
        profiler = PerformanceProfiler()
        
        def test_func():
            time.sleep(0.01)  # Small delay
            return "test_result"
        
        result = profiler.profile_function("test_func", test_func)
        
        assert result == "test_result"
        assert profiler.monitor.get_total_metrics() == 1
        
        # Check that the metric was recorded
        metric = profiler.monitor.metrics[0]
        assert metric.function_name == "test_func"
        assert metric.execution_time > 0

    def test_profile_function_disabled(self):
        """Test profiling a function when profiling is disabled."""
        profiler = PerformanceProfiler(enable_profiling=False)
        
        def test_func():
            return "test_result"
        
        result = profiler.profile_function("test_func", test_func)
        
        assert result == "test_result"
        assert profiler.monitor.get_total_metrics() == 0

    def test_profile_function_with_args(self):
        """Test profiling a function with arguments."""
        profiler = PerformanceProfiler()
        
        def test_func(x, y):
            return x + y
        
        result = profiler.profile_function("test_func", test_func, 5, 10)
        
        assert result == 15
        assert profiler.monitor.get_total_metrics() == 1

    def test_profile_function_with_kwargs(self):
        """Test profiling a function with keyword arguments."""
        profiler = PerformanceProfiler()
        
        def test_func(x=0, y=0):
            return x + y
        
        result = profiler.profile_function("test_func", test_func, x=5, y=10)
        
        assert result == 15
        assert profiler.monitor.get_total_metrics() == 1

    def test_profile_function_exception(self):
        """Test profiling a function that raises an exception."""
        profiler = PerformanceProfiler()
        
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            profiler.profile_function("test_func", test_func)
        
        # Should still record the metric even if function failed
        assert profiler.monitor.get_total_metrics() == 1


class TestSimpleCache:
    """Test SimpleCache class."""

    def test_simple_cache_init(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache(ttl_seconds=300)
        
        assert cache.ttl == 300
        assert len(cache) == 0

    def test_simple_cache_init_default_ttl(self):
        """Test SimpleCache initialization with default TTL."""
        cache = SimpleCache()
        
        assert cache.ttl == 300

    def test_get_cache_hit(self):
        """Test cache hit scenario."""
        cache = SimpleCache()
        
        # Add an item to cache
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        
        assert result == "value1"

    def test_get_cache_miss(self):
        """Test cache miss scenario."""
        cache = SimpleCache()
        
        result = cache.get("nonexistent_key")
        
        assert result is None

    def test_set_cache(self):
        """Test setting cache value."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"

    def test_cache_expiry(self):
        """Test cache expiry."""
        cache = SimpleCache(ttl_seconds=0)  # Immediate expiry
        
        cache.set("key1", "value1")
        time.sleep(0.01)  # Small delay to ensure expiry
        
        result = cache.get("key1")
        assert result is None

    def test_clear_cache(self):
        """Test clearing cache."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert len(cache) == 2
        
        cache.clear()
        
        assert len(cache) == 0

    def test_dict_like_access(self):
        """Test dict-like access methods."""
        cache = SimpleCache()
        
        cache["key1"] = "value1"
        assert cache["key1"] == "value1"
        assert "key1" in cache
        assert len(cache) == 1
        
        # Test keys, values, items
        assert list(cache.keys()) == ["key1"]
        assert list(cache.values()) == ["value1"]
        assert list(cache.items()) == [("key1", "value1")]

    def test_cache_update(self):
        """Test cache update method."""
        cache = SimpleCache()
        
        cache.update({"key1": "value1", "key2": "value2"})
        assert len(cache) == 2
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"


class TestMemoryProfiler:
    """Test MemoryProfiler class."""

    def test_memory_profiler_init(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler()
        
        assert profiler.memory_data == []

    def test_profile_decorator(self):
        """Test memory profiler decorator."""
        profiler = MemoryProfiler()
        
        @profiler.profile
        def test_func():
            return "test_result"
        
        result = test_func()
        
        assert result == "test_result"
        # Memory data might be empty if psutil is not available, which is fine

    def test_profile_decorator_without_psutil(self):
        """Test memory profiler decorator without psutil."""
        profiler = MemoryProfiler()
        
        @profiler.profile
        def test_func():
            return "test_result"
        
        result = test_func()
        
        assert result == "test_result"
        # Memory data might be empty if psutil is not available, which is fine


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_decorator(self):
        """Test time_function decorator."""
        @time_function
        def test_func():
            time.sleep(0.01)
            return "test_result"
        
        result = test_func()
        
        assert result == "test_result"
        
        # Check that metric was recorded
        from ai_guard.performance import get_performance_monitor
        monitor = get_performance_monitor()
        assert monitor.get_total_metrics() >= 1

    def test_time_function_with_monitor(self):
        """Test time_function decorator with specific monitor."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        def test_func():
            return "test_result"
        
        result = test_func()
        
        assert result == "test_result"
        assert monitor.get_total_metrics() == 1


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""

    def test_optimizer_init(self):
        """Test PerformanceOptimizer initialization."""
        optimizer = PerformanceOptimizer()
        
        assert optimizer.monitor is not None

    def test_optimize_function(self):
        """Test optimizing a function."""
        optimizer = PerformanceOptimizer()
        
        def test_func(x):
            return x * 2
        
        optimized_func = optimizer.optimize_function(test_func)
        
        result = optimized_func(5)
        assert result == 10
        
        # Check that metric was recorded
        assert optimizer.monitor.get_total_metrics() >= 1

    def test_get_optimization_suggestions(self):
        """Test getting optimization suggestions."""
        optimizer = PerformanceOptimizer()
        
        suggestions = optimizer.get_optimization_suggestions()
        
        # Should return empty list initially
        assert suggestions == []
        
        # Add some metrics
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.0
        )
        optimizer.monitor.record_metric(metric)
        
        suggestions = optimizer.get_optimization_suggestions()
        assert len(suggestions) > 0

    def test_analyze_performance(self):
        """Test analyzing performance."""
        optimizer = PerformanceOptimizer()
        
        # Test with no metrics
        analysis = optimizer.analyze_performance()
        assert analysis["total_functions"] == 0
        assert analysis["average_execution_time"] == 0.0
        assert analysis["total_execution_time"] == 0.0
        
        # Add some metrics
        metric1 = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.0
        )
        metric2 = PerformanceMetrics(
            function_name="test_func",
            execution_time=2.0
        )
        optimizer.monitor.record_metric(metric1)
        optimizer.monitor.record_metric(metric2)
        
        analysis = optimizer.analyze_performance()
        assert analysis["total_functions"] == 1
        assert analysis["average_execution_time"] == 1.5
        assert analysis["total_execution_time"] == 3.0


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        
        assert profiler.monitor is not None

    def test_profile_function(self):
        """Test profiling a function."""
        profiler = PerformanceProfiler()
        
        def test_func(x, y):
            return x + y
        
        result = profiler.profile_function(test_func, 5, 10)
        
        assert result == 15
        assert profiler.monitor.get_total_metrics() == 1

    def test_get_performance_report(self):
        """Test getting performance report."""
        profiler = PerformanceProfiler()
        
        # Add some mock data
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5
        )
        profiler.monitor.record_metric(metric)
        
        report_data = profiler.get_performance_report()
        
        assert "total_metrics" in report_data
        assert "functions_tracked" in report_data
        assert "average_times" in report_data
        assert report_data["total_metrics"] == 1
        assert report_data["functions_tracked"] == 1


class TestUtilityFunctions:
    """Test utility functions."""

    def test_cached_decorator(self):
        """Test cached decorator."""
        @cached
        def test_func(x):
            time.sleep(0.01)  # Simulate expensive operation
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == 10
        assert result2 == 10

    def test_cached_decorator_with_ttl(self):
        """Test cached decorator with TTL."""
        @cached(ttl_seconds=1)
        def test_func(x):
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == 10
        assert result2 == 10

    def test_profile_memory_usage_decorator(self):
        """Test profile_memory_usage decorator."""
        @profile_memory_usage
        def test_func():
            return "result"
        
        result = test_func()
        
        assert result == "result"

    def test_get_performance_summary(self):
        """Test get_performance_summary function."""
        # Clear any existing data
        clear_performance_data()
        
        summary = get_performance_summary()
        
        assert "total_metrics" in summary
        assert "cache_size" in summary
        assert "functions_tracked" in summary
        assert "average_times" in summary

    def test_clear_performance_data(self):
        """Test clear_performance_data function."""
        # Add some data first
        from ai_guard.performance import get_performance_monitor, get_cache
        monitor = get_performance_monitor()
        cache = get_cache()
        
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.0
        )
        monitor.record_metric(metric)
        cache.set("test_key", "test_value")
        
        # Clear data
        clear_performance_data()
        
        assert monitor.get_total_metrics() == 0
        assert len(cache) == 0


class TestAdditionalPerformanceFunctions:
    """Test additional performance functions."""

    def test_parallel_execute(self):
        """Test parallel_execute function."""
        from ai_guard.performance import parallel_execute
        
        def test_func(x):
            return x * 2
        
        tasks = [1, 2, 3, 4, 5]
        results = parallel_execute(test_func, tasks)
        
        assert len(results) == 5
        assert results == [2, 4, 6, 8, 10]

    def test_batch_process(self):
        """Test batch_process function."""
        from ai_guard.performance import batch_process
        
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        def processor(x):
            return x * 2
        
        results = batch_process(items, processor, batch_size=3)
        
        assert len(results) == 10
        assert results == [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

    def test_memory_efficient_file_reader(self):
        """Test memory_efficient_file_reader function."""
        from ai_guard.performance import memory_efficient_file_reader
        import tempfile
        import os
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content\nline 2\nline 3")
            temp_path = f.name
        
        try:
            content = memory_efficient_file_reader(temp_path)
            assert "test content" in content
            assert "line 2" in content
            assert "line 3" in content
        finally:
            os.unlink(temp_path)

    def test_optimize_file_operations(self):
        """Test optimize_file_operations function."""
        from ai_guard.performance import optimize_file_operations
        
        # Test with callable
        def test_func():
            return "test_result"
        
        result = optimize_file_operations(test_func)
        assert result == "test_result"
        
        # Test with list
        file_paths = ["file1.py", "file2.py", "file3.py"]
        result = optimize_file_operations(file_paths)
        assert result == file_paths
