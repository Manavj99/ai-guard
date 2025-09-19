"""Additional tests for performance.py to improve coverage."""

import pytest
import time
import threading
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
        """Test creating performance metrics."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=1024.5,
            cache_hits=10,
            cache_misses=2
        )
        
        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.5
        assert metric.memory_usage == 1024.5
        assert metric.cache_hits == 10
        assert metric.cache_misses == 2
    
    def test_performance_metrics_minimal(self):
        """Test creating performance metrics with minimal data."""
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
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
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
        """Test recording multiple performance metrics."""
        monitor = PerformanceMonitor()
        
        for i in range(5):
            metric = PerformanceMetrics(
                function_name=f"test_func_{i}",
                execution_time=float(i)
            )
            monitor.record_metric(metric)
        
        assert len(monitor.metrics) == 5
    
    def test_get_average_time_existing_function(self):
        """Test getting average time for existing function."""
        monitor = PerformanceMonitor()
        
        # Add metrics for the same function
        for i in range(3):
            metric = PerformanceMetrics(
                function_name="test_func",
                execution_time=float(i + 1)
            )
            monitor.record_metric(metric)
        
        average = monitor.get_average_time("test_func")
        assert average == 2.0  # (1 + 2 + 3) / 3
    
    def test_get_average_time_nonexistent_function(self):
        """Test getting average time for non-existent function."""
        monitor = PerformanceMonitor()
        
        average = monitor.get_average_time("nonexistent")
        assert average is None
    
    def test_get_total_metrics(self):
        """Test getting total number of metrics."""
        monitor = PerformanceMonitor()
        
        assert monitor.get_total_metrics() == 0
        
        for i in range(3):
            metric = PerformanceMetrics(
                function_name=f"test_func_{i}",
                execution_time=1.0
            )
            monitor.record_metric(metric)
        
        assert monitor.get_total_metrics() == 3
    
    def test_thread_safety(self):
        """Test thread safety of performance monitor."""
        monitor = PerformanceMonitor()
        
        def record_metrics():
            for i in range(10):
                metric = PerformanceMetrics(
                    function_name=f"thread_func_{i}",
                    execution_time=1.0
                )
                monitor.record_metric(metric)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have 50 metrics total (5 threads * 10 metrics each)
        assert monitor.get_total_metrics() == 50


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""
    
    def test_performance_profiler_initialization(self):
        """Test performance profiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.start_time is None
        assert profiler.end_time is None
        assert profiler.memory_start is None
        assert profiler.memory_end is None
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_start_profiling(self, mock_process):
        """Test starting profiling."""
        mock_instance = Mock()
        mock_instance.memory_info.return_value = Mock(rss=1024)
        mock_process.return_value = mock_instance
        
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        
        assert profiler.start_time is not None
        assert profiler.memory_start == 1024
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_stop_profiling(self, mock_process):
        """Test stopping profiling."""
        mock_instance = Mock()
        mock_instance.memory_info.return_value = Mock(rss=2048)
        mock_process.return_value = mock_instance
        
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        time.sleep(0.01)  # Small delay
        profiler.stop_profiling()
        
        assert profiler.end_time is not None
        assert profiler.memory_end == 2048
        assert profiler.end_time > profiler.start_time
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_get_execution_time(self, mock_process):
        """Test getting execution time."""
        mock_instance = Mock()
        mock_instance.memory_info.return_value = Mock(rss=1024)
        mock_process.return_value = mock_instance
        
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        time.sleep(0.01)
        profiler.stop_profiling()
        
        execution_time = profiler.get_execution_time()
        assert execution_time > 0
        assert execution_time < 1.0  # Should be small
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_get_memory_usage(self, mock_process):
        """Test getting memory usage."""
        mock_instance = Mock()
        mock_instance.memory_info.side_effect = [
            Mock(rss=1024),  # start
            Mock(rss=2048)   # end
        ]
        mock_process.return_value = mock_instance
        
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        profiler.stop_profiling()
        
        memory_usage = profiler.get_memory_usage()
        assert memory_usage == 1024  # 2048 - 1024
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_get_memory_usage_no_profiling(self, mock_process):
        """Test getting memory usage without profiling."""
        profiler = PerformanceProfiler()
        
        memory_usage = profiler.get_memory_usage()
        assert memory_usage is None
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_get_memory_usage_import_error(self, mock_process):
        """Test getting memory usage with psutil import error."""
        mock_process.side_effect = ImportError("psutil not available")
        
        profiler = PerformanceProfiler()
        profiler.start_profiling()
        profiler.stop_profiling()
        
        memory_usage = profiler.get_memory_usage()
        assert memory_usage is None


class TestCacheManager:
    """Test CacheManager class."""
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(max_size=100)
        assert cache.max_size == 100
        assert cache.cache == {}
        assert cache.access_times == {}
        assert cache.hit_count == 0
        assert cache.miss_count == 0
    
    def test_cache_manager_default_max_size(self):
        """Test cache manager with default max size."""
        cache = CacheManager()
        assert cache.max_size == 1000
    
    def test_get_cache_hit(self):
        """Test getting cached value (hit)."""
        cache = CacheManager()
        cache.cache["key1"] = "value1"
        cache.access_times["key1"] = time.time()
        
        value = cache.get("key1")
        assert value == "value1"
        assert cache.hit_count == 1
        assert cache.miss_count == 0
    
    def test_get_cache_miss(self):
        """Test getting cached value (miss)."""
        cache = CacheManager()
        
        value = cache.get("nonexistent")
        assert value is None
        assert cache.hit_count == 0
        assert cache.miss_count == 1
    
    def test_set_cache_value(self):
        """Test setting cache value."""
        cache = CacheManager()
        
        cache.set("key1", "value1")
        assert cache.cache["key1"] == "value1"
        assert "key1" in cache.access_times
    
    def test_set_cache_value_with_max_size(self):
        """Test setting cache value when at max size."""
        cache = CacheManager(max_size=2)
        
        # Fill cache to max size
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Add one more - should evict oldest
        cache.set("key3", "value3")
        
        assert len(cache.cache) == 2
        assert "key1" not in cache.cache  # Should be evicted
        assert "key2" in cache.cache
        assert "key3" in cache.cache
    
    def test_clear_cache(self):
        """Test clearing cache."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        assert len(cache.cache) == 0
        assert len(cache.access_times) == 0
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        cache = CacheManager()
        
        # Generate some hits and misses
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss
        
        stats = cache.get_stats()
        assert stats["hit_count"] == 2
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 2/3
        assert stats["size"] == 1


class TestMemoryTracker:
    """Test MemoryTracker class."""
    
    def test_memory_tracker_initialization(self):
        """Test memory tracker initialization."""
        tracker = MemoryTracker()
        assert tracker.peak_memory == 0
        assert tracker.current_memory == 0
        assert tracker.memory_history == []
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_start_tracking(self, mock_process):
        """Test starting memory tracking."""
        mock_instance = Mock()
        mock_instance.memory_info.return_value = Mock(rss=1024)
        mock_process.return_value = mock_instance
        
        tracker = MemoryTracker()
        tracker.start_tracking()
        
        assert tracker.current_memory == 1024
        assert len(tracker.memory_history) == 1
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_update_memory(self, mock_process):
        """Test updating memory usage."""
        mock_instance = Mock()
        mock_instance.memory_info.return_value = Mock(rss=2048)
        mock_process.return_value = mock_instance
        
        tracker = MemoryTracker()
        tracker.start_tracking()
        tracker.update_memory()
        
        assert tracker.current_memory == 2048
        assert tracker.peak_memory == 2048
        assert len(tracker.memory_history) == 2
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_get_memory_stats(self, mock_process):
        """Test getting memory statistics."""
        mock_instance = Mock()
        mock_instance.memory_info.side_effect = [
            Mock(rss=1024),  # start
            Mock(rss=2048),  # update 1
            Mock(rss=1536)   # update 2
        ]
        mock_process.return_value = mock_instance
        
        tracker = MemoryTracker()
        tracker.start_tracking()
        tracker.update_memory()
        tracker.update_memory()
        
        stats = tracker.get_memory_stats()
        assert stats["current"] == 1536
        assert stats["peak"] == 2048
        assert stats["average"] == (1024 + 2048 + 1536) / 3
        assert stats["samples"] == 3
    
    @patch('src.ai_guard.performance.psutil.Process')
    def test_memory_tracking_import_error(self, mock_process):
        """Test memory tracking with psutil import error."""
        mock_process.side_effect = ImportError("psutil not available")
        
        tracker = MemoryTracker()
        tracker.start_tracking()
        tracker.update_memory()
        
        stats = tracker.get_memory_stats()
        assert stats["current"] == 0
        assert stats["peak"] == 0


class TestExecutionTimer:
    """Test ExecutionTimer class."""
    
    def test_execution_timer_initialization(self):
        """Test execution timer initialization."""
        timer = ExecutionTimer()
        assert timer.start_time is None
        assert timer.end_time is None
    
    def test_start_timer(self):
        """Test starting timer."""
        timer = ExecutionTimer()
        timer.start()
        
        assert timer.start_time is not None
        assert timer.end_time is None
    
    def test_stop_timer(self):
        """Test stopping timer."""
        timer = ExecutionTimer()
        timer.start()
        time.sleep(0.01)
        timer.stop()
        
        assert timer.end_time is not None
        assert timer.end_time > timer.start_time
    
    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        timer = ExecutionTimer()
        timer.start()
        time.sleep(0.01)
        timer.stop()
        
        elapsed = timer.get_elapsed_time()
        assert elapsed > 0
        assert elapsed < 1.0
    
    def test_get_elapsed_time_not_stopped(self):
        """Test getting elapsed time without stopping."""
        timer = ExecutionTimer()
        timer.start()
        time.sleep(0.01)
        
        elapsed = timer.get_elapsed_time()
        assert elapsed > 0
    
    def test_get_elapsed_time_not_started(self):
        """Test getting elapsed time without starting."""
        timer = ExecutionTimer()
        
        elapsed = timer.get_elapsed_time()
        assert elapsed is None
    
    def test_context_manager(self):
        """Test using timer as context manager."""
        with ExecutionTimer() as timer:
            time.sleep(0.01)
        
        assert timer.start_time is not None
        assert timer.end_time is not None
        assert timer.get_elapsed_time() > 0


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""
    
    def test_performance_optimizer_initialization(self):
        """Test performance optimizer initialization."""
        optimizer = PerformanceOptimizer()
        assert optimizer.optimizations == []
        assert optimizer.benchmark_results == {}
    
    def test_add_optimization(self):
        """Test adding optimization."""
        optimizer = PerformanceOptimizer()
        
        def test_optimization():
            return "optimized"
        
        optimizer.add_optimization("test", test_optimization)
        assert len(optimizer.optimizations) == 1
        assert optimizer.optimizations[0]["name"] == "test"
    
    def test_run_optimization(self):
        """Test running optimization."""
        optimizer = PerformanceOptimizer()
        
        def test_optimization():
            return "optimized"
        
        optimizer.add_optimization("test", test_optimization)
        result = optimizer.run_optimization("test")
        
        assert result == "optimized"
    
    def test_run_nonexistent_optimization(self):
        """Test running non-existent optimization."""
        optimizer = PerformanceOptimizer()
        
        result = optimizer.run_optimization("nonexistent")
        assert result is None
    
    def test_benchmark_optimization(self):
        """Test benchmarking optimization."""
        optimizer = PerformanceOptimizer()
        
        def test_optimization():
            time.sleep(0.01)
            return "optimized"
        
        optimizer.add_optimization("test", test_optimization)
        benchmark = optimizer.benchmark_optimization("test", iterations=3)
        
        assert benchmark["name"] == "test"
        assert benchmark["iterations"] == 3
        assert benchmark["total_time"] > 0
        assert benchmark["average_time"] > 0
        assert benchmark["results"] == ["optimized", "optimized", "optimized"]
    
    def test_benchmark_nonexistent_optimization(self):
        """Test benchmarking non-existent optimization."""
        optimizer = PerformanceOptimizer()
        
        benchmark = optimizer.benchmark_optimization("nonexistent")
        assert benchmark is None


class TestDecorators:
    """Test performance decorators."""
    
    def test_profile_function_decorator(self):
        """Test profile_function decorator."""
        @profile_function
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_cached_function_decorator(self):
        """Test cached_function decorator."""
        call_count = 0
        
        @cached_function
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
    
    def test_memory_monitor_decorator(self):
        """Test memory_monitor decorator."""
        @memory_monitor
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_time_execution_decorator(self):
        """Test time_execution decorator."""
        @time_execution
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_optimize_memory_usage(self):
        """Test optimize_memory_usage function."""
        # Test with list
        data = [1, 2, 3, 4, 5]
        optimized = optimize_memory_usage(data)
        assert optimized == data
        
        # Test with dict
        data = {"a": 1, "b": 2, "c": 3}
        optimized = optimize_memory_usage(data)
        assert optimized == data
    
    def test_parallel_execution(self):
        """Test parallel_execution function."""
        def test_func(x):
            return x * 2
        
        inputs = [1, 2, 3, 4, 5]
        results = parallel_execution(test_func, inputs, max_workers=2)
        
        assert results == [2, 4, 6, 8, 10]
    
    def test_batch_processing(self):
        """Test batch_processing function."""
        def test_func(batch):
            return [x * 2 for x in batch]
        
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        results = batch_processing(test_func, data, batch_size=3)
        
        # Should process in batches of 3
        expected = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        assert results == expected
    
    def test_batch_processing_empty_data(self):
        """Test batch_processing with empty data."""
        def test_func(batch):
            return [x * 2 for x in batch]
        
        results = batch_processing(test_func, [], batch_size=3)
        assert results == []
    
    def test_batch_processing_single_batch(self):
        """Test batch_processing with single batch."""
        def test_func(batch):
            return [x * 2 for x in batch]
        
        data = [1, 2]
        results = batch_processing(test_func, data, batch_size=5)
        assert results == [2, 4]
