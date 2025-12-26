"""Performance utility function tests - parallel_execute, file operations, etc."""

import time
import tempfile
import os
import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.performance import (
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    get_performance_summary,
    _get_performance_summary,
    clear_performance_data,
    expensive_operation,
    process_large_file,
    optimize_quality_gates_execution,
)


class TestParallelExecute:
    """Test parallel_execute function."""

    def test_parallel_execute_with_function_and_tasks(self):
        """Test parallel_execute with function and tasks."""

        def multiply_by_two(x):
            time.sleep(0.01)
            return x * 2

        tasks = [1, 2, 3, 4, 5]
        results = parallel_execute(multiply_by_two, tasks)

        assert len(results) == 5
        assert results == [2, 4, 6, 8, 10]

    def test_parallel_execute_with_function_list(self):
        """Test parallel_execute with list of functions."""

        def func1():
            time.sleep(0.01)
            return "result1"

        def func2():
            time.sleep(0.01)
            return "result2"

        def func3():
            time.sleep(0.01)
            return "result3"

        functions = [func1, func2, func3]
        results = parallel_execute(functions)

        assert len(results) == 3
        assert set(results) == {"result1", "result2", "result3"}

    def test_parallel_execute_with_max_workers(self):
        """Test parallel_execute with max_workers parameter."""

        def slow_func(x):
            time.sleep(0.1)
            return x * 2

        tasks = [1, 2, 3]
        start_time = time.time()
        results = parallel_execute(slow_func, tasks, max_workers=2)
        execution_time = time.time() - start_time

        assert len(results) == 3
        assert results == [2, 4, 6]
        # Should be faster than sequential execution (0.3s) but slower than full parallel (0.1s)
        assert 0.1 < execution_time < 0.3

    def test_parallel_execute_with_timeout(self):
        """Test parallel_execute with timeout."""

        def slow_func(x):
            time.sleep(0.2)
            return x * 2

        tasks = [1, 2, 3]

        with pytest.raises(Exception):  # Should timeout
            parallel_execute(slow_func, tasks, timeout=0.1)

    def test_parallel_execute_with_exceptions_raise_true(self):
        """Test parallel_execute with exceptions and raise_exceptions=True."""

        def failing_func(x):
            if x == 2:
                raise ValueError("test error")
            return x * 2

        tasks = [1, 2, 3]

        with pytest.raises(ValueError, match="test error"):
            parallel_execute(failing_func, tasks, raise_exceptions=True)

    def test_parallel_execute_with_exceptions_raise_false(self):
        """Test parallel_execute with exceptions and raise_exceptions=False."""

        def failing_func(x):
            if x == 2:
                raise ValueError("test error")
            return x * 2

        tasks = [1, 2, 3]
        results = parallel_execute(failing_func, tasks, raise_exceptions=False)

        assert len(results) == 3
        assert results[0] == 2  # func(1)
        assert results[1] is None  # func(2) failed
        assert results[2] == 6  # func(3)

    def test_parallel_execute_empty_tasks(self):
        """Test parallel_execute with empty tasks."""

        def test_func(x):
            return x * 2

        results = parallel_execute(test_func, [])
        assert results == []

    def test_parallel_execute_empty_functions(self):
        """Test parallel_execute with empty function list."""
        results = parallel_execute([])
        assert results == []


class TestBatchProcess:
    """Test batch_process function."""

    def test_batch_process_without_processor(self):
        """Test batch_process without processor function."""
        items = [1, 2, 3, 4, 5]
        results = batch_process(items, batch_size=2)

        assert results == [1, 2, 3, 4, 5]

    def test_batch_process_with_item_processor(self):
        """Test batch_process with item processor function."""

        def multiply_by_two(x):
            return x * 2

        items = [1, 2, 3, 4, 5]
        results = batch_process(items, multiply_by_two, batch_size=2)

        assert results == [2, 4, 6, 8, 10]

    def test_batch_process_with_batch_processor(self):
        """Test batch_process with batch processor function."""

        def batch_processor(batch):
            return [x * 2 for x in batch]

        items = [1, 2, 3, 4, 5]
        results = batch_process(items, batch_processor, batch_size=2)

        assert results == [2, 4, 6, 8, 10]

    def test_batch_process_with_batch_processor_non_list_result(self):
        """Test batch_process with batch processor returning non-list."""

        def batch_processor(batch):
            return sum(batch)

        items = [1, 2, 3, 4, 5]
        results = batch_process(items, batch_processor, batch_size=2)

        assert results == [3, 7, 5]  # [1+2, 3+4, 5]

    def test_batch_process_batch_size_larger_than_items(self):
        """Test batch_process with batch size larger than number of items."""

        def multiply_by_two(x):
            return x * 2

        items = [1, 2, 3]
        results = batch_process(items, multiply_by_two, batch_size=10)

        assert results == [2, 4, 6]

    def test_batch_process_empty_items(self):
        """Test batch_process with empty items list."""

        def multiply_by_two(x):
            return x * 2

        results = batch_process([], multiply_by_two, batch_size=2)
        assert results == []


class TestOptimizeFileOperations:
    """Test optimize_file_operations function."""

    def test_optimize_file_operations_with_callable(self):
        """Test optimize_file_operations with callable."""

        def file_op():
            return "file_content"

        result = optimize_file_operations(file_op)
        assert result == "file_content"

    def test_optimize_file_operations_with_callable_exception(self):
        """Test optimize_file_operations with callable that raises exception."""

        def file_op():
            raise FileNotFoundError("file not found")

        with pytest.raises(FileNotFoundError):
            optimize_file_operations(file_op)

    def test_optimize_file_operations_with_list(self):
        """Test optimize_file_operations with list of file paths."""
        file_paths = ["file1.txt", "file2.txt", "file3.txt"]
        result = optimize_file_operations(file_paths)
        assert result == file_paths

    def test_optimize_file_operations_with_other_type(self):
        """Test optimize_file_operations with other types."""
        result = optimize_file_operations("not_a_list_or_callable")
        assert result == "not_a_list_or_callable"

        result = optimize_file_operations(123)
        assert result == 123


class TestMemoryEfficientFileReader:
    """Test memory_efficient_file_reader function."""

    def test_memory_efficient_file_reader_basic(self):
        """Test basic file reading functionality."""
        content = "Line 1\nLine 2\nLine 3\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_file = f.name

        try:
            result = memory_efficient_file_reader(temp_file)
            assert result == content
        finally:
            os.unlink(temp_file)

    def test_memory_efficient_file_reader_with_chunk_size(self):
        """Test file reading with custom chunk size."""
        content = "A" * 1000  # 1000 characters

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_file = f.name

        try:
            result = memory_efficient_file_reader(temp_file, chunk_size=100)
            assert result == content
        finally:
            os.unlink(temp_file)

    def test_memory_efficient_file_reader_file_not_found(self):
        """Test file reading with non-existent file."""
        result = memory_efficient_file_reader("nonexistent_file.txt")
        assert result == ""

    def test_memory_efficient_file_reader_empty_file(self):
        """Test file reading with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            temp_file = f.name

        try:
            result = memory_efficient_file_reader(temp_file)
            assert result == ""
        finally:
            os.unlink(temp_file)


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""

    def test_get_performance_summary_empty(self):
        """Test performance summary with no metrics."""
        clear_performance_data()

        summary = get_performance_summary()

        assert summary["total_metrics"] == 0
        assert summary["cache_size"] == 0
        assert summary["functions_tracked"] == 0
        assert summary["average_times"] == {}

    def test_get_performance_summary_with_metrics(self):
        """Test performance summary with metrics."""
        from src.ai_guard.performance import get_performance_monitor, PerformanceMetrics

        clear_performance_data()

        monitor = get_performance_monitor()
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        monitor.record_metric(PerformanceMetrics("func1", 2.0))
        monitor.record_metric(PerformanceMetrics("func2", 3.0))

        summary = get_performance_summary()

        assert summary["total_metrics"] == 3
        assert summary["cache_size"] == 0
        assert summary["functions_tracked"] == 2
        assert "func1" in summary["average_times"]
        assert "func2" in summary["average_times"]
        assert summary["average_times"]["func1"] == 1.5  # (1.0 + 2.0) / 2
        assert summary["average_times"]["func2"] == 3.0

    def test_get_performance_summary_internal(self):
        """Test internal performance summary function."""
        clear_performance_data()

        summary = _get_performance_summary()

        assert summary["total_metrics"] == 0
        assert summary["cache_size"] == 0
        assert summary["functions_tracked"] == 0


class TestExampleFunctions:
    """Test example functions in performance module."""

    def test_expensive_operation(self):
        """Test expensive_operation example function."""
        from src.ai_guard.performance import get_cache, get_performance_monitor

        cache = get_cache()
        cache.clear()
        monitor = get_performance_monitor()
        monitor.clear_metrics()

        # First call
        result1 = expensive_operation("test_data")
        assert result1 == "processed_test_data"
        assert monitor.get_total_metrics() == 1

        # Second call - should use cache
        result2 = expensive_operation("test_data")
        assert result2 == "processed_test_data"
        assert monitor.get_total_metrics() == 2  # Still records timing

    def test_process_large_file(self):
        """Test process_large_file example function."""
        content = "Line 1\nLine 2\nLine 3\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_file = f.name

        try:
            result = process_large_file(temp_file)
            assert result == [
                "Line 1",
                "Line 2",
                "Line 3",
                "",
            ]  # split includes empty string
        finally:
            os.unlink(temp_file)

    def test_optimize_quality_gates_execution(self):
        """Test optimize_quality_gates_execution function."""

        def mock_quality_check(file_path):
            return f"checked_{file_path}"

        file_paths = ["file1.txt", "file2.txt", "file3.txt"]
        quality_checks = [mock_quality_check]

        result = optimize_quality_gates_execution(file_paths, quality_checks)

        assert result["processed_files"] == 3
        assert result["total_checks"] == 1
        assert len(result["results"]) == 3
        assert "performance_summary" in result

        # Check that all files were processed
        expected_results = [
            "checked_file1.txt",
            "checked_file2.txt",
            "checked_file3.txt",
        ]
        assert set(result["results"]) == set(expected_results)

    def test_optimize_quality_gates_execution_empty_files(self):
        """Test optimize_quality_gates_execution with empty file list."""

        def mock_quality_check(file_path):
            return f"checked_{file_path}"

        result = optimize_quality_gates_execution([], [mock_quality_check])

        assert result["processed_files"] == 0
        assert result["total_checks"] == 1
        assert result["results"] == []

    def test_optimize_quality_gates_execution_multiple_checks(self):
        """Test optimize_quality_gates_execution with multiple quality checks."""

        def check1(file_path):
            return f"check1_{file_path}"

        def check2(file_path):
            return f"check2_{file_path}"

        file_paths = ["file1.txt"]
        quality_checks = [check1, check2]

        result = optimize_quality_gates_execution(file_paths, quality_checks)

        assert result["processed_files"] == 1
        assert result["total_checks"] == 2
        assert len(result["results"]) == 2
        assert "check1_file1.txt" in result["results"]
        assert "check2_file1.txt" in result["results"]

    def test_optimize_quality_gates_execution_large_batch(self):
        """Test optimize_quality_gates_execution with large number of files."""

        def mock_quality_check(file_path):
            return f"checked_{file_path}"

        # Create 25 files to test batching (batch_size=10)
        file_paths = [f"file{i}.txt" for i in range(25)]
        quality_checks = [mock_quality_check]

        result = optimize_quality_gates_execution(file_paths, quality_checks)

        assert result["processed_files"] == 25
        assert result["total_checks"] == 1
        assert len(result["results"]) == 25
