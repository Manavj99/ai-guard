"""Tests for the performance module."""

import time
import threading
from unittest.mock import patch, MagicMock
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    time_function,
    SimpleCache,
    cached,
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    profile_memory_usage,
    get_performance_summary,
    clear_performance_data,
    get_performance_monitor,
    get_cache,
    expensive_operation,
    process_large_file,
    optimize_quality_gates_execution,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating performance metrics."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=10.5,
            cache_hits=5,
            cache_misses=2,
        )

        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.5
        assert metric.memory_usage == 10.5
        assert metric.cache_hits == 5
        assert metric.cache_misses == 2


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def setup_method(self):
        """Set up test method."""
        self.monitor = PerformanceMonitor()

    def test_record_metric(self):
        """Test recording a metric."""
        metric = PerformanceMetrics("test_func", 1.0)
        self.monitor.record_metric(metric)

        assert self.monitor.get_total_metrics() == 1

    def test_get_average_time(self):
        """Test getting average execution time."""
        # Record multiple metrics for the same function
        self.monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        self.monitor.record_metric(PerformanceMetrics("test_func", 2.0))
        self.monitor.record_metric(PerformanceMetrics("test_func", 3.0))

        average = self.monitor.get_average_time("test_func")
        assert average == 2.0

    def test_get_average_time_nonexistent(self):
        """Test getting average time for nonexistent function."""
        average = self.monitor.get_average_time("nonexistent")
        assert average is None

    def test_clear_metrics(self):
        """Test clearing metrics."""
        self.monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        assert self.monitor.get_total_metrics() == 1

        self.monitor.clear_metrics()
        assert self.monitor.get_total_metrics() == 0

    def test_thread_safety(self):
        """Test thread safety of performance monitor."""

        def record_metrics():
            for i in range(10):
                metric = PerformanceMetrics(f"func_{i}", i * 0.1)
                self.monitor.record_metric(metric)

        # Create multiple threads
        threads = [threading.Thread(target=record_metrics) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have 50 metrics total
        assert self.monitor.get_total_metrics() == 50


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_decorator(self):
        """Test that time_function decorator works correctly."""

        @time_function
        def test_func():
            time.sleep(0.01)  # Small delay to ensure measurable time
            return "test_result"

        result = test_func()
        assert result == "test_result"

        # Check that metric was recorded
        monitor = get_performance_monitor()
        assert monitor.get_total_metrics() >= 1

        # Check that the function name is recorded
        metrics = [m for m in monitor.metrics if m.function_name == "test_func"]
        assert len(metrics) >= 1
        assert metrics[0].execution_time > 0


class TestSimpleCache:
    """Test SimpleCache class."""

    def setup_method(self):
        """Set up test method."""
        self.cache = SimpleCache(ttl_seconds=1)

    def test_cache_set_get(self):
        """Test setting and getting cache values."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_cache_expiration(self):
        """Test cache expiration."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert self.cache.get("key1") is None

    def test_cache_clear(self):
        """Test clearing cache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        assert self.cache.size() == 2

        self.cache.clear()
        assert self.cache.size() == 0

    def test_cache_size(self):
        """Test cache size tracking."""
        assert self.cache.size() == 0

        self.cache.set("key1", "value1")
        assert self.cache.size() == 1

        self.cache.set("key2", "value2")
        assert self.cache.size() == 2


class TestCachedDecorator:
    """Test cached decorator."""

    def setup_method(self):
        """Set up test method."""
        # Clear cache before each test
        get_cache().clear()

    def test_cached_decorator(self):
        """Test that cached decorator works correctly."""
        call_count = 0

        @cached(ttl_seconds=60)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call should execute function
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

    def test_cached_different_args(self):
        """Test cached decorator with different arguments."""
        call_count = 0

        @cached(ttl_seconds=60)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Different arguments should cause separate cache entries
        result1 = test_func(5)
        result2 = test_func(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2


class TestParallelExecute:
    """Test parallel_execute function."""

    def test_parallel_execute_success(self):
        """Test successful parallel execution."""

        def func1():
            return "result1"

        def func2():
            return "result2"

        def func3():
            return "result3"

        results = parallel_execute([func1, func2, func3])

        assert len(results) == 3
        assert "result1" in results
        assert "result2" in results
        assert "result3" in results

    def test_parallel_execute_with_errors(self):
        """Test parallel execution with some functions failing."""

        def func1():
            return "result1"

        def func2():
            raise ValueError("Test error")

        def func3():
            return "result3"

        results = parallel_execute([func1, func2, func3])

        assert len(results) == 3
        assert "result1" in results
        assert "result3" in results
        assert None in results  # Failed function returns None

    def test_parallel_execute_with_timeout(self):
        """Test parallel execution with timeout."""

        def slow_func():
            time.sleep(2)
            return "slow_result"

        def fast_func():
            return "fast_result"

        # Should timeout and return partial results
        try:
            results = parallel_execute([slow_func, fast_func], timeout=0.5)
            # If no timeout occurs, we should have both results
            assert len(results) == 2
        except TimeoutError:
            # Timeout is expected behavior
            pass


class TestBatchProcess:
    """Test batch_process function."""

    def test_batch_process_with_processor(self):
        """Test batch processing with a processor function."""
        items = list(range(10))

        def processor(x):
            return x * 2

        results = batch_process(items, batch_size=3, processor=processor)

        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_batch_process_without_processor(self):
        """Test batch processing without a processor."""
        items = list(range(10))

        results = batch_process(items, batch_size=3)

        assert len(results) == 10
        assert results == items

    def test_batch_process_single_batch(self):
        """Test batch processing with all items in one batch."""
        items = list(range(5))

        def processor(x):
            return x * 2

        results = batch_process(items, batch_size=10, processor=processor)

        assert len(results) == 5
        assert results == [0, 2, 4, 6, 8]


class TestOptimizeFileOperations:
    """Test optimize_file_operations function."""

    def test_optimize_file_operations(self):
        """Test file operations optimization."""
        file_paths = [
            "/path/to/file1.py",
            "/path/to/file2.py",
            "/other/path/file3.py",
            "/path/to/file4.py",
            "/other/path/file5.py",
        ]

        optimized = optimize_file_operations(file_paths)

        # Should be sorted and grouped by directory
        assert len(optimized) == 5
        assert optimized[0] == "/other/path/file3.py"
        assert optimized[1] == "/other/path/file5.py"
        assert optimized[2] == "/path/to/file1.py"
        assert optimized[3] == "/path/to/file2.py"
        assert optimized[4] == "/path/to/file4.py"


class TestMemoryEfficientFileReader:
    """Test memory_efficient_file_reader function."""

    def test_memory_efficient_file_reader_success(self, tmp_path):
        """Test successful file reading."""
        test_file = tmp_path / "test.txt"
        test_content = "Line 1\nLine 2\nLine 3"
        test_file.write_text(test_content)

        result = memory_efficient_file_reader(str(test_file))
        assert result == test_content

    def test_memory_efficient_file_reader_nonexistent(self):
        """Test reading nonexistent file."""
        result = memory_efficient_file_reader("/nonexistent/file.txt")
        assert result == ""

    def test_memory_efficient_file_reader_chunk_size(self, tmp_path):
        """Test file reading with specific chunk size."""
        test_file = tmp_path / "test.txt"
        test_content = "A" * 1000  # 1000 characters
        test_file.write_text(test_content)

        result = memory_efficient_file_reader(str(test_file), chunk_size=100)
        assert result == test_content


class TestProfileMemoryUsage:
    """Test profile_memory_usage decorator."""

    @patch("psutil.Process")
    def test_profile_memory_usage_with_psutil(self, mock_process_class):
        """Test memory profiling with psutil available."""
        # Mock psutil Process
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024  # 1MB
        mock_process_class.return_value = mock_process

        @profile_memory_usage
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"

        # Check that memory metric was recorded
        monitor = get_performance_monitor()
        memory_metrics = [m for m in monitor.metrics if m.memory_usage is not None]
        assert len(memory_metrics) >= 1

    def test_profile_memory_usage_without_psutil(self):
        """Test memory profiling without psutil."""

        @profile_memory_usage
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""

    def setup_method(self):
        """Set up test method."""
        clear_performance_data()

    def test_get_performance_summary_empty(self):
        """Test performance summary with no data."""
        summary = get_performance_summary()

        assert summary["total_metrics"] == 0
        assert summary["cache_size"] == 0
        assert summary["functions_tracked"] == 0
        assert summary["average_times"] == {}

    def test_get_performance_summary_with_data(self):
        """Test performance summary with data."""
        # Add some metrics
        monitor = get_performance_monitor()
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        monitor.record_metric(PerformanceMetrics("func1", 2.0))
        monitor.record_metric(PerformanceMetrics("func2", 3.0))

        # Add some cache data
        cache = get_cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        summary = get_performance_summary()

        assert summary["total_metrics"] == 3
        assert summary["cache_size"] == 2
        assert summary["functions_tracked"] == 2
        assert "func1" in summary["average_times"]
        assert "func2" in summary["average_times"]
        assert summary["average_times"]["func1"] == 1.5
        assert summary["average_times"]["func2"] == 3.0


class TestClearPerformanceData:
    """Test clear_performance_data function."""

    def test_clear_performance_data(self):
        """Test clearing all performance data."""
        # Clear any existing data first
        clear_performance_data()

        # Add some data
        monitor = get_performance_monitor()
        monitor.record_metric(PerformanceMetrics("func1", 1.0))

        cache = get_cache()
        cache.set("key1", "value1")

        # Verify data exists
        assert monitor.get_total_metrics() == 1
        assert cache.size() == 1

        # Clear data
        clear_performance_data()

        # Verify data is cleared
        assert monitor.get_total_metrics() == 0
        assert cache.size() == 0


class TestExampleFunctions:
    """Test example functions in the performance module."""

    def setup_method(self):
        """Set up test method."""
        clear_performance_data()

    def test_expensive_operation(self):
        """Test expensive_operation function."""
        # First call should execute
        result1 = expensive_operation("test")
        assert result1 == "processed_test"

        # Second call should use cache
        result2 = expensive_operation("test")
        assert result2 == "processed_test"

    def test_process_large_file(self, tmp_path):
        """Test process_large_file function."""
        test_file = tmp_path / "test.txt"
        test_content = "Line 1\nLine 2\nLine 3"
        test_file.write_text(test_content)

        result = process_large_file(str(test_file))
        assert result == ["Line 1", "Line 2", "Line 3"]

    def test_optimize_quality_gates_execution(self):
        """Test optimize_quality_gates_execution function."""
        file_paths = ["file1.py", "file2.py", "file3.py"]

        def mock_check(file_path):
            return f"checked_{file_path}"

        quality_checks = [mock_check]

        result = optimize_quality_gates_execution(file_paths, quality_checks)

        assert result["processed_files"] == 3
        assert result["total_checks"] == 1
        # Results should be 3 files * 1 check = 3 results
        assert len(result["results"]) == 3
        assert "performance_summary" in result

        # Verify the results contain the expected file paths
        expected_results = ["checked_file1.py", "checked_file2.py", "checked_file3.py"]
        for expected in expected_results:
            assert expected in result["results"]


class TestGlobalInstances:
    """Test global instance functions."""

    def test_get_performance_monitor(self):
        """Test get_performance_monitor function."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

    def test_get_cache(self):
        """Test get_cache function."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)
