"""Additional tests for performance module to improve coverage."""

import pytest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    time_function,
    timed_function,
    cached,
    cache_result,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    get_performance_summary,
    clear_performance_data,
    reset_global_monitor,
    MemoryProfiler,
    PerformanceProfiler,
    AsyncTaskManager,
    ResourceManager,
    PerformanceOptimizer,
    SimpleCache
)


class TestTimedFunction:
    """Test timed_function decorator."""

    def test_timed_function_basic(self):
        """Test basic timed_function decorator."""
        @timed_function()
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10

    def test_timed_function_with_monitor(self):
        """Test timed_function with custom monitor."""
        monitor = PerformanceMonitor()
        
        @timed_function(monitor)
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
        assert monitor.get_total_metrics() == 1


class TestCacheResult:
    """Test cache_result decorator."""

    def test_cache_result_basic(self):
        """Test basic cache_result functionality."""
        call_count = 0
        
        @cache_result(max_size=2)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First calls
        result1 = test_func(1)
        result2 = test_func(2)
        assert call_count == 2
        
        # Cache hits
        result3 = test_func(1)
        result4 = test_func(2)
        assert call_count == 2
        
        # This should evict the first entry
        result5 = test_func(3)
        assert call_count == 3


class TestBatchProcess:
    """Test batch_process function."""

    def test_batch_process_basic(self):
        """Test basic batch processing."""
        items = list(range(10))
        
        def processor(item):
            return item * 2
        
        results = batch_process(items, processor, batch_size=3)
        
        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_batch_process_batch_processor(self):
        """Test batch processing with batch processor."""
        items = list(range(10))
        
        def batch_processor(batch):
            return [x * 2 for x in batch]
        
        results = batch_process(items, batch_processor, batch_size=3)
        
        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_batch_process_no_processor(self):
        """Test batch processing without processor."""
        items = list(range(5))
        results = batch_process(items, batch_size=2)
        
        assert results == items


class TestOptimizeFileOperations:
    """Test optimize_file_operations function."""

    def test_optimize_file_operations_callable(self):
        """Test optimize_file_operations with callable."""
        def file_op():
            return "test_result"
        
        result = optimize_file_operations(file_op)
        assert result == "test_result"

    def test_optimize_file_operations_list(self):
        """Test optimize_file_operations with list."""
        file_paths = ["file1.py", "file2.py"]
        result = optimize_file_operations(file_paths)
        assert result == file_paths

    def test_optimize_file_operations_exception(self):
        """Test optimize_file_operations with exception."""
        def file_op():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            optimize_file_operations(file_op)


class TestMemoryEfficientFileReader:
    """Test memory_efficient_file_reader function."""

    def test_memory_efficient_file_reader_basic(self):
        """Test basic memory efficient file reading."""
        content = "line1\nline2\nline3"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            result = memory_efficient_file_reader(temp_file)
            assert result == content
        finally:
            os.unlink(temp_file)

    def test_memory_efficient_file_reader_nonexistent_file(self):
        """Test memory efficient file reading with non-existent file."""
        result = memory_efficient_file_reader("nonexistent.txt")
        assert result == ""


class TestMemoryProfiler:
    """Test MemoryProfiler class."""

    def test_memory_profiler_init(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.memory_data == []

    @patch('psutil.Process')
    def test_memory_profiler_profile(self, mock_process):
        """Test MemoryProfiler profile method."""
        mock_instance = MagicMock()
        mock_instance.memory_info.return_value.rss = 1024 * 1024
        mock_process.return_value = mock_instance
        
        profiler = MemoryProfiler()
        
        @profiler.profile
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"
        assert len(profiler.memory_data) == 1


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_performance_profiler_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        assert isinstance(profiler.monitor, PerformanceMonitor)

    def test_performance_profiler_profile_function(self):
        """Test PerformanceProfiler profile_function method."""
        profiler = PerformanceProfiler()
        
        def test_func(x):
            return x * 2
        
        result = profiler.profile_function(test_func, 5)
        assert result == 10
        assert profiler.monitor.get_total_metrics() == 1


class TestAsyncTaskManager:
    """Test AsyncTaskManager class."""

    def test_async_task_manager_init(self):
        """Test AsyncTaskManager initialization."""
        manager = AsyncTaskManager(max_workers=2)
        assert manager.max_workers == 2
        assert manager.tasks == []
        assert manager.executor is None

    def test_async_task_manager_context_manager(self):
        """Test AsyncTaskManager as context manager."""
        with AsyncTaskManager(max_workers=2) as manager:
            assert manager.executor is not None
            
            def test_func(x):
                return x * 2
            
            future = manager.submit_task(test_func, 5)
            result = future.result()
            assert result == 10


class TestResourceManager:
    """Test ResourceManager class."""

    def test_resource_manager_init(self):
        """Test ResourceManager initialization."""
        manager = ResourceManager()
        assert manager.resources == {}
        assert hasattr(manager, '_lock')

    def test_resource_manager_acquire_release(self):
        """Test ResourceManager acquire and release."""
        manager = ResourceManager()
        
        resource = manager.acquire_resource("test_resource")
        assert resource == "test_resource"
        assert manager.get_resource_status()["test_resource"] is True
        
        manager.release_resource("test_resource")
        assert manager.get_resource_status() == {}


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""

    def test_performance_optimizer_init(self):
        """Test PerformanceOptimizer initialization."""
        optimizer = PerformanceOptimizer()
        assert isinstance(optimizer.monitor, PerformanceMonitor)

    def test_performance_optimizer_optimize_function(self):
        """Test PerformanceOptimizer optimize_function method."""
        optimizer = PerformanceOptimizer()
        
        def test_func(x):
            return x * 2
        
        optimized_func = optimizer.optimize_function(test_func)
        result = optimized_func(5)
        assert result == 10
        assert optimizer.monitor.get_total_metrics() == 1


class TestUtilityFunctions:
    """Test additional utility functions."""

    def test_get_performance_summary(self):
        """Test get_performance_summary function."""
        summary = get_performance_summary()
        assert "total_metrics" in summary
        assert "cache_size" in summary
        assert "functions_tracked" in summary
        assert "average_times" in summary

    def test_clear_performance_data(self):
        """Test clear_performance_data function."""
        monitor = PerformanceMonitor()
        cache = SimpleCache()
        
        # Add some data
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        cache.set("test_key", "test_value")
        
        assert monitor.get_total_metrics() > 0
        assert cache.size() > 0
        
        clear_performance_data()
        
        # Check global instances are cleared
        global_monitor = PerformanceMonitor()
        global_cache = SimpleCache()
        assert global_monitor.get_total_metrics() == 0
        assert global_cache.size() == 0

    def test_reset_global_monitor(self):
        """Test reset_global_monitor function."""
        monitor1 = PerformanceMonitor()
        monitor1.record_metric(PerformanceMetrics("test_func", 1.0))
        
        assert monitor1.get_total_metrics() == 1
        
        reset_global_monitor()
        
        monitor2 = PerformanceMonitor()
        assert monitor2.get_total_metrics() == 0
        assert monitor2 is not monitor1


class TestSimpleCacheAdvanced:
    """Test advanced SimpleCache functionality."""

    def test_simple_cache_update(self):
        """Test SimpleCache update method."""
        cache = SimpleCache()
        
        # Update with dict
        cache.update({"key1": "value1", "key2": "value2"})
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Update with kwargs
        cache.update(key3="value3", key4="value4")
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_simple_cache_keyerror(self):
        """Test SimpleCache KeyError for missing keys."""
        cache = SimpleCache()
        
        with pytest.raises(KeyError):
            cache["nonexistent_key"]
