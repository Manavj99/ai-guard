"""Comprehensive tests for performance module."""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    time_function,
    cached,
    get_performance_summary,
    profile_memory_usage,
    memory_profiler,
    PerformanceProfiler,
    MemoryProfiler,
    PerformanceOptimizer,
    AsyncTaskManager,
    ResourceManager,
    SimpleCache,
    get_cache,
    clear_cache,
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    get_performance_monitor,
    clear_performance_data
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_init(self):
        """Test PerformanceMetrics initialization."""
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
        """Test PerformanceMetrics with minimal parameters."""
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

    def test_get_average_time_existing_function(self):
        """Test getting average time for existing function."""
        monitor = PerformanceMonitor()
        
        # Add multiple metrics for same function
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        monitor.record_metric(PerformanceMetrics("test_func", 2.0))
        monitor.record_metric(PerformanceMetrics("test_func", 3.0))
        
        avg_time = monitor.get_average_time("test_func")
        assert avg_time == 2.0

    def test_get_average_time_nonexistent_function(self):
        """Test getting average time for nonexistent function."""
        monitor = PerformanceMonitor()
        avg_time = monitor.get_average_time("nonexistent_func")
        assert avg_time is None

    def test_get_total_metrics(self):
        """Test getting total number of metrics."""
        monitor = PerformanceMonitor()
        assert monitor.get_total_metrics() == 0
        
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        monitor.record_metric(PerformanceMetrics("func2", 2.0))
        assert monitor.get_total_metrics() == 2


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_basic(self):
        """Test basic time_function decorator."""
        @time_function
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        assert result == "result"

    def test_time_function_with_monitor(self):
        """Test time_function with custom monitor."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor=monitor)
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        assert result == "result"
        assert monitor.get_total_metrics() == 1
        assert monitor.metrics[0].function_name == "test_func"

    def test_time_function_with_args(self):
        """Test time_function with function arguments."""
        @time_function
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        assert result == 3

    def test_time_function_with_kwargs(self):
        """Test time_function with keyword arguments."""
        @time_function
        def test_func(x=1, y=2):
            return x + y
        
        result = test_func(x=3, y=4)
        assert result == 7


class TestCached:
    """Test cached decorator."""

    def test_cached_basic(self):
        """Test basic cached decorator."""
        call_count = 0
        
        @cached
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count == 1

    def test_cached_different_args(self):
        """Test cached decorator with different arguments."""
        call_count = 0
        
        @cached
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_func(5)
        result2 = expensive_func(10)
        assert result1 == 10
        assert result2 == 20
        assert call_count == 2

    def test_cached_with_ttl(self):
        """Test cached decorator with TTL."""
        call_count = 0
        
        @cached(ttl=0.1)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Second call should not use cache
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count == 2


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""

    def test_get_performance_summary_empty(self):
        """Test performance summary with empty metrics."""
        monitor = PerformanceMonitor()
        summary = get_performance_summary(monitor)
        
        assert summary["total_functions"] == 0
        assert summary["total_execution_time"] == 0.0
        assert summary["average_execution_time"] == 0.0

    def test_get_performance_summary_with_data(self):
        """Test performance summary with data."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        monitor.record_metric(PerformanceMetrics("func2", 2.0))
        monitor.record_metric(PerformanceMetrics("func1", 1.5))
        
        summary = get_performance_summary(monitor)
        
        assert summary["total_functions"] == 2
        assert summary["total_execution_time"] == 4.5
        assert summary["average_execution_time"] == 1.5
        assert "func1" in summary["function_stats"]
        assert "func2" in summary["function_stats"]


class TestMeasureMemoryUsage:
    """Test measure_memory_usage function."""

    def test_measure_memory_usage_basic(self):
        """Test basic memory usage measurement."""
        def test_func():
            data = [1] * 1000
            return len(data)
        
        memory_usage = measure_memory_usage(test_func)
        assert memory_usage > 0
        assert isinstance(memory_usage, float)

    def test_measure_memory_usage_with_args(self):
        """Test memory usage measurement with arguments."""
        def test_func(size):
            data = [1] * size
            return len(data)
        
        memory_usage = measure_memory_usage(test_func, 1000)
        assert memory_usage > 0


class TestBenchmarkFunction:
    """Test benchmark_function function."""

    def test_benchmark_function_basic(self):
        """Test basic function benchmarking."""
        def test_func():
            time.sleep(0.01)
            return "result"
        
        results = benchmark_function(test_func, iterations=3)
        
        assert len(results) == 3
        assert all(result > 0 for result in results)
        assert all(isinstance(result, float) for result in results)

    def test_benchmark_function_with_args(self):
        """Test function benchmarking with arguments."""
        def test_func(x):
            time.sleep(0.01)
            return x * 2
        
        results = benchmark_function(test_func, 5, iterations=2)
        
        assert len(results) == 2
        assert all(result > 0 for result in results)


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_performance_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.monitor is not None
        assert profiler.start_time is None

    def test_start_profiling(self):
        """Test starting profiling."""
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        assert profiler.start_time is not None

    def test_stop_profiling(self):
        """Test stopping profiling."""
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        time.sleep(0.01)
        profiler.stop_profiling()
        
        assert profiler.start_time is not None
        assert profiler.end_time is not None
        assert profiler.total_time > 0

    def test_get_profile_report(self):
        """Test getting profile report."""
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        time.sleep(0.01)
        profiler.stop_profiling()
        
        report = profiler.get_profile_report()
        assert "total_time" in report
        assert "metrics_count" in report
        assert report["total_time"] > 0


class TestCacheManager:
    """Test CacheManager class."""

    def test_cache_manager_init(self):
        """Test CacheManager initialization."""
        cache = CacheManager()
        assert cache._cache == {}
        assert cache._lock is not None

    def test_get_set_cache(self):
        """Test getting and setting cache values."""
        cache = CacheManager()
        
        # Set value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Get nonexistent key
        assert cache.get("nonexistent") is None

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert len(cache._cache) == 2
        cache.clear()
        assert len(cache._cache) == 0

    def test_cache_size(self):
        """Test getting cache size."""
        cache = CacheManager()
        assert cache.size() == 0
        
        cache.set("key1", "value1")
        assert cache.size() == 1
        
        cache.set("key2", "value2")
        assert cache.size() == 2


class TestThreadSafeCounter:
    """Test ThreadSafeCounter class."""

    def test_thread_safe_counter_init(self):
        """Test ThreadSafeCounter initialization."""
        counter = ThreadSafeCounter()
        assert counter.value == 0

    def test_increment(self):
        """Test counter increment."""
        counter = ThreadSafeCounter()
        counter.increment()
        assert counter.value == 1
        
        counter.increment(5)
        assert counter.value == 6

    def test_decrement(self):
        """Test counter decrement."""
        counter = ThreadSafeCounter()
        counter.increment(10)
        counter.decrement()
        assert counter.value == 9
        
        counter.decrement(3)
        assert counter.value == 6

    def test_reset(self):
        """Test counter reset."""
        counter = ThreadSafeCounter()
        counter.increment(5)
        counter.reset()
        assert counter.value == 0


class TestResourceMonitor:
    """Test ResourceMonitor class."""

    def test_resource_monitor_init(self):
        """Test ResourceMonitor initialization."""
        monitor = ResourceMonitor()
        assert monitor.cpu_usage == 0.0
        assert monitor.memory_usage == 0.0

    def test_update_metrics(self):
        """Test updating resource metrics."""
        monitor = ResourceMonitor()
        monitor.update_metrics()
        
        # Metrics should be updated (may be 0 on some systems)
        assert isinstance(monitor.cpu_usage, float)
        assert isinstance(monitor.memory_usage, float)

    def test_get_resource_summary(self):
        """Test getting resource summary."""
        monitor = ResourceMonitor()
        monitor.update_metrics()
        
        summary = monitor.get_resource_summary()
        assert "cpu_usage" in summary
        assert "memory_usage" in summary
        assert "timestamp" in summary


class TestPerformanceConfig:
    """Test PerformanceConfig dataclass."""

    def test_performance_config_init(self):
        """Test PerformanceConfig initialization."""
        config = PerformanceConfig(
            enable_profiling=True,
            cache_ttl=300,
            max_cache_size=1000,
            enable_memory_monitoring=True
        )
        assert config.enable_profiling is True
        assert config.cache_ttl == 300
        assert config.max_cache_size == 1000
        assert config.enable_memory_monitoring is True

    def test_performance_config_defaults(self):
        """Test PerformanceConfig with default values."""
        config = PerformanceConfig()
        assert config.enable_profiling is False
        assert config.cache_ttl == 60
        assert config.max_cache_size == 100
        assert config.enable_memory_monitoring is False


class TestOptimizeFunctionCalls:
    """Test optimize_function_calls function."""

    def test_optimize_function_calls_basic(self):
        """Test basic function call optimization."""
        def test_func(x):
            return x * 2
        
        optimized_func = optimize_function_calls(test_func)
        result = optimized_func(5)
        assert result == 10

    def test_optimize_function_calls_with_cache(self):
        """Test function call optimization with caching."""
        call_count = 0
        
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        optimized_func = optimize_function_calls(test_func, enable_caching=True)
        
        # First call
        result1 = optimized_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = optimized_func(5)
        assert result2 == 10
        assert call_count == 1


class TestGetSystemInfo:
    """Test get_system_info function."""

    def test_get_system_info(self):
        """Test getting system information."""
        info = get_system_info()
        
        assert "platform" in info
        assert "python_version" in info
        assert "cpu_count" in info
        assert "memory_total" in info
        assert isinstance(info["cpu_count"], int)
        assert isinstance(info["memory_total"], (int, float))


class TestLogPerformanceMetrics:
    """Test log_performance_metrics function."""

    def test_log_performance_metrics(self):
        """Test logging performance metrics."""
        monitor = PerformanceMonitor()
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        
        # This should not raise an exception
        log_performance_metrics(monitor)
        
        # Test with custom logger
        with patch('src.ai_guard.performance.logger') as mock_logger:
            log_performance_metrics(monitor)
            mock_logger.info.assert_called()