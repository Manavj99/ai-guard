"""Comprehensive tests for performance.py to improve coverage."""

import pytest
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.ai_guard.performance import (
    time_function,
    cached,
    get_performance_summary,
    get_cache,
    PerformanceMetrics,
    PerformanceMonitor,
    clear_performance_data,
    reset_global_monitor,
    expensive_operation,
    process_large_file,
    get_performance_monitor,
    timed_function,
    SimpleCache,
    cache_result,
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    profile_memory_usage,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics.execution_times == []
        assert metrics.memory_usage == []
        assert metrics.cpu_usage == []
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_add_execution_time(self):
        """Test adding execution time."""
        metrics = PerformanceMetrics()
        metrics.add_execution_time(1.5)
        assert len(metrics.execution_times) == 1
        assert metrics.execution_times[0] == 1.5

    def test_add_memory_usage(self):
        """Test adding memory usage."""
        metrics = PerformanceMetrics()
        metrics.add_memory_usage(1024)
        assert len(metrics.memory_usage) == 1
        assert metrics.memory_usage[0] == 1024

    def test_add_cpu_usage(self):
        """Test adding CPU usage."""
        metrics = PerformanceMetrics()
        metrics.add_cpu_usage(50.0)
        assert len(metrics.cpu_usage) == 1
        assert metrics.cpu_usage[0] == 50.0

    def test_increment_cache_hits(self):
        """Test incrementing cache hits."""
        metrics = PerformanceMetrics()
        metrics.increment_cache_hits()
        assert metrics.cache_hits == 1

    def test_increment_cache_misses(self):
        """Test incrementing cache misses."""
        metrics = PerformanceMetrics()
        metrics.increment_cache_misses()
        assert metrics.cache_misses == 1

    def test_get_average_execution_time(self):
        """Test getting average execution time."""
        metrics = PerformanceMetrics()
        metrics.add_execution_time(1.0)
        metrics.add_execution_time(2.0)
        metrics.add_execution_time(3.0)

        avg_time = metrics.get_average_execution_time()
        assert avg_time == 2.0

    def test_get_average_execution_time_empty(self):
        """Test getting average execution time with no data."""
        metrics = PerformanceMetrics()
        avg_time = metrics.get_average_execution_time()
        assert avg_time == 0.0

    def test_get_average_memory_usage(self):
        """Test getting average memory usage."""
        metrics = PerformanceMetrics()
        metrics.add_memory_usage(1000)
        metrics.add_memory_usage(2000)
        metrics.add_memory_usage(3000)

        avg_memory = metrics.get_average_memory_usage()
        assert avg_memory == 2000.0

    def test_get_average_memory_usage_empty(self):
        """Test getting average memory usage with no data."""
        metrics = PerformanceMetrics()
        avg_memory = metrics.get_average_memory_usage()
        assert avg_memory == 0.0

    def test_get_average_cpu_usage(self):
        """Test getting average CPU usage."""
        metrics = PerformanceMetrics()
        metrics.add_cpu_usage(25.0)
        metrics.add_cpu_usage(50.0)
        metrics.add_cpu_usage(75.0)

        avg_cpu = metrics.get_average_cpu_usage()
        assert avg_cpu == 50.0

    def test_get_average_cpu_usage_empty(self):
        """Test getting average CPU usage with no data."""
        metrics = PerformanceMetrics()
        avg_cpu = metrics.get_average_cpu_usage()
        assert avg_cpu == 0.0

    def test_get_cache_hit_rate(self):
        """Test getting cache hit rate."""
        metrics = PerformanceMetrics()
        metrics.increment_cache_hits()
        metrics.increment_cache_hits()
        metrics.increment_cache_misses()

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 2 / 3

    def test_get_cache_hit_rate_no_requests(self):
        """Test getting cache hit rate with no requests."""
        metrics = PerformanceMetrics()
        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 0.0

    def test_clear_metrics(self):
        """Test clearing metrics."""
        metrics = PerformanceMetrics()
        metrics.add_execution_time(1.0)
        metrics.add_memory_usage(1000)
        metrics.add_cpu_usage(50.0)
        metrics.increment_cache_hits()
        metrics.increment_cache_misses()

        metrics.clear_metrics()
        assert len(metrics.execution_times) == 0
        assert len(metrics.memory_usage) == 0
        assert len(metrics.cpu_usage) == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_to_dict(self):
        """Test converting to dictionary."""
        metrics = PerformanceMetrics()
        metrics.add_execution_time(1.0)
        metrics.add_memory_usage(1000)
        metrics.add_cpu_usage(50.0)
        metrics.increment_cache_hits()
        metrics.increment_cache_misses()

        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert "execution_times" in metrics_dict
        assert "memory_usage" in metrics_dict
        assert "cpu_usage" in metrics_dict
        assert "cache_hits" in metrics_dict
        assert "cache_misses" in metrics_dict


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def test_initialization(self):
        """Test monitor initialization."""
        monitor = PerformanceMonitor()
        assert isinstance(monitor.metrics, PerformanceMetrics)

    def test_start_timing(self):
        """Test starting timing."""
        monitor = PerformanceMonitor()
        monitor.start_timing("test_operation")
        assert "test_operation" in monitor.active_timings

    def test_end_timing(self):
        """Test ending timing."""
        monitor = PerformanceMonitor()
        monitor.start_timing("test_operation")
        time.sleep(0.01)  # Small delay
        monitor.end_timing("test_operation")
        assert "test_operation" not in monitor.active_timings

    def test_record_execution_time(self):
        """Test recording execution time."""
        monitor = PerformanceMonitor()
        monitor.record_execution_time("test_operation", 1.5)
        assert len(monitor.metrics.execution_times) == 1
        assert monitor.metrics.execution_times[0] == 1.5

    def test_record_memory_usage(self):
        """Test recording memory usage."""
        monitor = PerformanceMonitor()
        monitor.record_memory_usage(1024)
        assert len(monitor.metrics.memory_usage) == 1
        assert monitor.metrics.memory_usage[0] == 1024

    def test_record_cpu_usage(self):
        """Test recording CPU usage."""
        monitor = PerformanceMonitor()
        monitor.record_cpu_usage(50.0)
        assert len(monitor.metrics.cpu_usage) == 1
        assert monitor.metrics.cpu_usage[0] == 50.0

    def test_get_metrics(self):
        """Test getting metrics."""
        monitor = PerformanceMonitor()
        metrics = monitor.get_metrics()
        assert isinstance(metrics, PerformanceMetrics)

    def test_clear_metrics(self):
        """Test clearing metrics."""
        monitor = PerformanceMonitor()
        monitor.record_execution_time("test", 1.0)
        monitor.clear_metrics()
        assert len(monitor.metrics.execution_times) == 0


class TestSimpleCache:
    """Test SimpleCache class."""

    def test_initialization(self):
        """Test cache initialization."""
        cache = SimpleCache()
        assert cache.cache == {}
        assert cache.max_size == 100

    def test_initialization_with_max_size(self):
        """Test cache initialization with max size."""
        cache = SimpleCache(max_size=50)
        assert cache.max_size == 50

    def test_get_nonexistent(self):
        """Test getting nonexistent key."""
        cache = SimpleCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_set_and_get(self):
        """Test setting and getting value."""
        cache = SimpleCache()
        cache.set("key", "value")
        result = cache.get("key")
        assert result == "value"

    def test_clear(self):
        """Test clearing cache."""
        cache = SimpleCache()
        cache.set("key", "value")
        cache.clear()
        assert len(cache.cache) == 0

    def test_size_limit(self):
        """Test cache size limit."""
        cache = SimpleCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # This should evict key1
        assert len(cache.cache) == 2
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"


class TestTimeFunctionDecorator:
    """Test time_function decorator."""

    def test_time_function_basic(self):
        """Test basic time_function decorator."""

        @time_function
        def test_func():
            time.sleep(0.01)
            return "test"

        result = test_func()
        assert result == "test"

    def test_time_function_with_args(self):
        """Test time_function decorator with arguments."""

        @time_function
        def test_func(x, y):
            return x + y

        result = test_func(1, 2)
        assert result == 3

    def test_time_function_with_kwargs(self):
        """Test time_function decorator with keyword arguments."""

        @time_function
        def test_func(x=0, y=0):
            return x + y

        result = test_func(x=1, y=2)
        assert result == 3

    def test_time_function_exception(self):
        """Test time_function decorator with exception."""

        @time_function
        def test_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            test_func()


class TestCachedDecorator:
    """Test cached decorator."""

    def test_cached_basic(self):
        """Test basic cached decorator."""
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

        # Second call (should be cached)
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

    def test_cached_different_args(self):
        """Test cached decorator with different arguments."""
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

        # Second call with different argument
        result2 = test_func(10)
        assert result2 == 20
        assert call_count == 2  # Should increment

    def test_cached_with_kwargs(self):
        """Test cached decorator with keyword arguments."""
        call_count = 0

        @cached
        def test_func(x, y=0):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call
        result1 = test_func(5, y=3)
        assert result1 == 8
        assert call_count == 1

        # Second call with same arguments
        result2 = test_func(5, y=3)
        assert result2 == 8
        assert call_count == 1  # Should be cached

    def test_cached_clear(self):
        """Test clearing cache."""
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

        # Clear cache
        test_func.cache_clear()

        # Second call (should not be cached)
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 2  # Should increment


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_performance_monitor(self):
        """Test getting performance monitor."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        summary = get_performance_summary()
        assert isinstance(summary, dict)

    def test_get_cache(self):
        """Test getting cache."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)

    def test_clear_performance_data(self):
        """Test clearing performance data."""
        clear_performance_data()
        # Should not raise an exception

    def test_reset_global_monitor(self):
        """Test resetting global monitor."""
        reset_global_monitor()
        # Should not raise an exception

    def test_expensive_operation(self):
        """Test expensive operation."""
        result = expensive_operation("test data")
        assert isinstance(result, str)
        assert "processed" in result

    def test_process_large_file(self):
        """Test processing large file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3")
            temp_file = f.name

        try:
            result = process_large_file(temp_file)
            assert isinstance(result, list)
            assert len(result) == 3
        finally:
            os.unlink(temp_file)

    def test_timed_function(self):
        """Test timed function decorator."""
        monitor = PerformanceMonitor()

        @timed_function(monitor)
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"

    def test_cache_result(self):
        """Test cache result decorator."""
        call_count = 0

        @cache_result(max_size=10)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (should be cached)
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1

    def test_parallel_execute(self):
        """Test parallel execution."""

        def test_func(x):
            return x * 2

        results = parallel_execute([test_func], [1, 2, 3])
        assert len(results) == 3
        assert results[0] == 2
        assert results[1] == 4
        assert results[2] == 6

    def test_batch_process(self):
        """Test batch processing."""

        def test_func(x):
            return x * 2

        results = batch_process([1, 2, 3], test_func, batch_size=2)
        assert len(results) == 3
        assert results[0] == 2
        assert results[1] == 4
        assert results[2] == 6

    def test_optimize_file_operations(self):
        """Test optimizing file operations."""

        def test_file_op(file_path):
            with open(file_path, "r") as f:
                return f.read()

        optimized_op = optimize_file_operations(test_file_op)
        assert callable(optimized_op)

    def test_memory_efficient_file_reader(self):
        """Test memory efficient file reader."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_file = f.name

        try:
            content = memory_efficient_file_reader(temp_file)
            assert content == "test content"
        finally:
            os.unlink(temp_file)

    def test_profile_memory_usage(self):
        """Test profiling memory usage."""

        @profile_memory_usage
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"


class TestResourceManager:
    """Test ResourceManager class."""

    def test_initialization(self):
        """Test ResourceManager initialization."""
        from src.ai_guard.performance import ResourceManager

        manager = ResourceManager()
        assert manager.resources == {}

    def test_acquire_resource(self):
        """Test acquiring a resource."""
        from src.ai_guard.performance import ResourceManager

        manager = ResourceManager()

        manager.acquire_resource("test_resource")
        assert manager.resources["test_resource"] is True

    def test_release_resource(self):
        """Test releasing a resource."""
        from src.ai_guard.performance import ResourceManager

        manager = ResourceManager()

        manager.acquire_resource("test_resource")
        manager.release_resource("test_resource")
        assert "test_resource" not in manager.resources

    def test_get_resource_status(self):
        """Test getting resource status."""
        from src.ai_guard.performance import ResourceManager

        manager = ResourceManager()

        manager.acquire_resource("test_resource")
        status = manager.get_resource_status()
        assert status["test_resource"] is True


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""

    def test_initialization(self):
        """Test PerformanceOptimizer initialization."""
        from src.ai_guard.performance import PerformanceOptimizer

        optimizer = PerformanceOptimizer()
        assert optimizer.monitor is not None

    def test_optimize_function(self):
        """Test optimizing a function."""
        from src.ai_guard.performance import PerformanceOptimizer

        optimizer = PerformanceOptimizer()

        def test_func():
            return "test"

        optimized_func = optimizer.optimize_function(test_func)
        assert callable(optimized_func)
        assert optimized_func() == "test"

    def test_get_optimization_suggestions_empty(self):
        """Test getting optimization suggestions with no metrics."""
        from src.ai_guard.performance import PerformanceOptimizer

        optimizer = PerformanceOptimizer()

        suggestions = optimizer.get_optimization_suggestions()
        assert suggestions == []

    def test_get_optimization_suggestions_with_metrics(self):
        """Test getting optimization suggestions with metrics."""
        from src.ai_guard.performance import PerformanceOptimizer, PerformanceMetrics

        optimizer = PerformanceOptimizer()

        # Add some metrics to trigger suggestions
        metric = PerformanceMetrics("test_func", 1.0)
        optimizer.monitor.metrics.append(metric)

        suggestions = optimizer.get_optimization_suggestions()
        assert len(suggestions) > 0
        assert "Consider caching frequently called functions" in suggestions

    def test_analyze_performance_empty(self):
        """Test analyzing performance with no metrics."""
        from src.ai_guard.performance import PerformanceOptimizer

        optimizer = PerformanceOptimizer()

        analysis = optimizer.analyze_performance()
        assert analysis["total_functions"] == 0
        assert analysis["average_execution_time"] == 0.0
        assert analysis["total_execution_time"] == 0.0

    def test_analyze_performance_with_metrics(self):
        """Test analyzing performance with metrics."""
        from src.ai_guard.performance import PerformanceOptimizer, PerformanceMetrics

        optimizer = PerformanceOptimizer()

        # Add some metrics
        metric1 = PerformanceMetrics("test_func1", 1.0)
        metric2 = PerformanceMetrics("test_func2", 2.0)
        optimizer.monitor.metrics.extend([metric1, metric2])

        analysis = optimizer.analyze_performance()
        assert analysis["total_functions"] == 2
        assert analysis["average_execution_time"] == 1.5
        assert analysis["total_execution_time"] == 3.0
