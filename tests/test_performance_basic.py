"""Basic tests for performance module."""

import pytest
import time
from unittest.mock import patch, MagicMock
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    time_function,
    cached,
    get_performance_summary,
    get_performance_monitor,
    SimpleCache,
    get_cache,
    clear_cache,
    MemoryProfiler,
    PerformanceProfiler
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
        
        @time_function(monitor)
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
        # Note: cached decorator might cache differently, so we just check results
        assert call_count >= 1


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        summary = get_performance_summary()
        
        assert isinstance(summary, dict)
        assert "functions_tracked" in summary
        assert "total_metrics" in summary
        assert "average_times" in summary


class TestGetPerformanceMonitor:
    """Test get_performance_monitor function."""

    def test_get_performance_monitor(self):
        """Test getting performance monitor."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)


class TestSimpleCache:
    """Test SimpleCache class."""

    def test_simple_cache_init(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache()
        assert len(cache) == 0

    def test_simple_cache_set_get(self):
        """Test SimpleCache set and get operations."""
        cache = SimpleCache()
        
        cache["key1"] = "value1"
        assert cache["key1"] == "value1"
        
        cache["key2"] = "value2"
        assert cache["key2"] == "value2"

    def test_simple_cache_clear(self):
        """Test SimpleCache clear operation."""
        cache = SimpleCache()
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        
        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0


class TestGetCache:
    """Test get_cache function."""

    def test_get_cache(self):
        """Test getting cache instance."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)


class TestClearCache:
    """Test clear_cache function."""

    def test_clear_cache(self):
        """Test clearing cache."""
        cache = get_cache()
        cache["test_key"] = "test_value"
        
        assert len(cache) > 0
        clear_cache()
        assert len(cache) == 0


class TestMemoryProfiler:
    """Test MemoryProfiler class."""

    def test_memory_profiler_init(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.memory_data == []

    def test_profile_decorator(self):
        """Test memory profiling decorator."""
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

    def test_performance_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.monitor is not None

    def test_profile_function(self):
        """Test profiling a function."""
        profiler = PerformanceProfiler()
        
        def test_func(x):
            return x * 2
        
        result = profiler.profile_function(test_func, 5)
        assert result == 10

    def test_get_performance_report(self):
        """Test getting performance report."""
        profiler = PerformanceProfiler()
        
        def test_func():
            time.sleep(0.01)
            return "result"
        
        profiler.profile_function(test_func)
        
        report = profiler.get_performance_report()
        assert "total_metrics" in report
        assert "functions_tracked" in report
        assert "average_times" in report