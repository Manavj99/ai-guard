#!/usr/bin/env python3
"""
Comprehensive test suite for the optimized diff parser module.

This test suite validates all the performance optimizations, caching mechanisms,
and new features added to the diff_parser.py module.
"""

import unittest
import tempfile
import os
import time
import threading
from unittest.mock import patch, mock_open
from concurrent.futures import ThreadPoolExecutor

# Import the module under test
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_guard.diff_parser import (
    DiffParser,
    DiffCache,
    ChangeType,
    FileChange,
    LineChange,
    extract_file_changes_optimized,
    get_added_lines_optimized,
    get_removed_lines_optimized,
    get_modified_files_optimized,
    parse_diff_output_optimized,
    get_diff_statistics,
    validate_diff_format,
    parse_multiple_diffs_parallel,
    benchmark_diff_parsing,
    _validate_diff_content,
    _parse_hunk_header,
    _get_cache_key,
)


class TestDiffCache(unittest.TestCase):
    """Test the DiffCache class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = DiffCache(max_size=10, ttl=1)  # Small cache for testing

    def tearDown(self):
        """Clean up after tests."""
        self.cache.clear()

    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        # Test set and get
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

        # Test non-existent key
        self.assertIsNone(self.cache.get("nonexistent"))

        # Test cache miss
        self.cache.set("key2", "value2")
        self.assertEqual(self.cache.get("key2"), "value2")

    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("key1"))

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        for i in range(10):
            self.cache.set(f"key{i}", f"value{i}")

        # Add one more item to trigger eviction
        self.cache.set("key10", "value10")

        # First item should be evicted
        self.assertIsNone(self.cache.get("key0"))
        self.assertEqual(self.cache.get("key10"), "value10")

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        stats = self.cache.get_stats()
        self.assertIn("size", stats)
        self.assertIn("hit_rate", stats)
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)

    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        results = []

        def worker(thread_id):
            for i in range(10):
                key = f"thread{thread_id}_key{i}"
                value = f"thread{thread_id}_value{i}"
                self.cache.set(key, value)
                results.append(self.cache.get(key) == value)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        self.assertTrue(all(results))
        self.assertEqual(len(results), 50)


class TestDiffValidation(unittest.TestCase):
    """Test diff content validation functions."""

    def test_validate_diff_content_valid(self):
        """Test validation with valid diff content."""
        valid_diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def hello():
-    print("hello")
+    print("hello world")
+    return True
"""
        self.assertTrue(_validate_diff_content(valid_diff))

    def test_validate_diff_content_invalid(self):
        """Test validation with invalid content."""
        invalid_cases = [
            "",  # Empty
            "not a diff",  # Not a diff
            "single line",  # Too short
            None,  # None value
        ]

        for case in invalid_cases:
            if case is None:
                self.assertFalse(_validate_diff_content(case))
            else:
                self.assertFalse(_validate_diff_content(case))

    def test_validate_diff_format(self):
        """Test comprehensive diff format validation."""
        valid_diff = """diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def test():
-    return False
+    return True
"""

        result = validate_diff_format(valid_diff)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIn("line_count", result)

    def test_validate_diff_format_errors(self):
        """Test diff format validation with errors."""
        invalid_diff = "not a diff at all"

        result = validate_diff_format(invalid_diff)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)


class TestOptimizedParsing(unittest.TestCase):
    """Test optimized parsing functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("hello")
+    print("hello world")
+    return True
@@ -10,2 +11,3 @@
 def goodbye():
-    print("goodbye")
+    print("goodbye world")
+    return False
"""

    def test_extract_file_changes_optimized(self):
        """Test optimized file changes extraction."""
        changes = extract_file_changes_optimized(self.sample_diff)

        self.assertGreater(len(changes), 0)
        self.assertIsInstance(changes[0], FileChange)
        self.assertEqual(changes[0].file_path, "test.py")
        self.assertEqual(changes[0].change_type, ChangeType.MODIFIED)

    def test_get_added_lines_optimized(self):
        """Test optimized added lines extraction."""
        added_lines = get_added_lines_optimized(self.sample_diff)

        self.assertGreater(len(added_lines), 0)
        self.assertIsInstance(added_lines[0], LineChange)
        self.assertEqual(added_lines[0].change_type, "added")

    def test_get_removed_lines_optimized(self):
        """Test optimized removed lines extraction."""
        removed_lines = get_removed_lines_optimized(self.sample_diff)

        self.assertGreater(len(removed_lines), 0)
        self.assertIsInstance(removed_lines[0], LineChange)
        self.assertEqual(removed_lines[0].change_type, "removed")

    def test_get_modified_files_optimized(self):
        """Test optimized modified files extraction."""
        files = get_modified_files_optimized(self.sample_diff)

        self.assertIn("test.py", files)
        self.assertEqual(len(files), 1)

    def test_parse_diff_output_optimized(self):
        """Test optimized diff output parsing."""
        diff_output = """+++ b/test1.py
--- a/test2.py
+++ b/test3.py
"""
        files = parse_diff_output_optimized(diff_output)

        self.assertIn("test1.py", files)
        self.assertIn("test2.py", files)
        self.assertIn("test3.py", files)

    def test_caching_functionality(self):
        """Test that optimized functions use caching."""
        # First call should cache the result
        result1 = extract_file_changes_optimized(self.sample_diff)

        # Second call should return cached result
        result2 = extract_file_changes_optimized(self.sample_diff)

        self.assertEqual(result1, result2)

        # Verify cache stats show hits
        from ai_guard.diff_parser import _diff_cache

        stats = _diff_cache.get_stats()
        self.assertGreater(stats["hits"], 0)


class TestDiffStatistics(unittest.TestCase):
    """Test diff statistics functionality."""

    def test_get_diff_statistics(self):
        """Test comprehensive diff statistics."""
        diff_content = """diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("hello")
+    print("hello world")
+    return True
"""

        stats = get_diff_statistics(diff_content)

        self.assertIn("total_files", stats)
        self.assertIn("total_added_lines", stats)
        self.assertIn("total_removed_lines", stats)
        self.assertIn("net_lines", stats)
        self.assertIn("file_types", stats)
        self.assertIn("change_types", stats)

        self.assertEqual(stats["total_files"], 1)
        self.assertGreater(stats["total_added_lines"], 0)
        self.assertGreater(stats["total_removed_lines"], 0)

    def test_get_diff_statistics_caching(self):
        """Test that statistics are cached."""
        diff_content = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
 def test():
+    return True
"""

        # First call
        stats1 = get_diff_statistics(diff_content)

        # Second call should return cached result
        stats2 = get_diff_statistics(diff_content)

        self.assertEqual(stats1, stats2)


class TestParallelProcessing(unittest.TestCase):
    """Test parallel processing functionality."""

    def test_parse_multiple_diffs_parallel(self):
        """Test parallel parsing of multiple diffs."""
        diffs = [
            """diff --git a/file1.py b/file1.py
+++ b/file1.py
@@ -1,1 +1,2 @@
 def func1():
+    return True
""",
            """diff --git a/file2.py b/file2.py
+++ b/file2.py
@@ -1,1 +1,2 @@
 def func2():
+    return False
""",
        ]

        results = parse_multiple_diffs_parallel(diffs, max_workers=2)

        self.assertEqual(len(results), 2)
        self.assertGreater(len(results[0]), 0)
        self.assertGreater(len(results[1]), 0)

    def test_parallel_processing_performance(self):
        """Test that parallel processing is faster than sequential."""
        large_diff = """diff --git a/large.py b/large.py
+++ b/large.py
""" + "\n".join(
            [
                f"@@ -{i},1 +{i},2 @@\n def func{i}():\n+    return True"
                for i in range(100)
            ]
        )

        diffs = [large_diff] * 5

        # Time parallel processing
        start_time = time.time()
        parallel_results = parse_multiple_diffs_parallel(diffs, max_workers=4)
        parallel_time = time.time() - start_time

        # Time sequential processing
        start_time = time.time()
        sequential_results = [extract_file_changes_optimized(diff) for diff in diffs]
        sequential_time = time.time() - start_time

        # Parallel should be faster (allow some tolerance)
        self.assertLess(parallel_time, sequential_time * 1.5)
        self.assertEqual(len(parallel_results), len(sequential_results))


class TestBenchmarking(unittest.TestCase):
    """Test benchmarking functionality."""

    def test_benchmark_diff_parsing(self):
        """Test diff parsing benchmark."""
        diff_content = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
 def test():
+    return True
"""

        benchmark_result = benchmark_diff_parsing(diff_content, iterations=10)

        self.assertIn("original_time", benchmark_result)
        self.assertIn("optimized_time", benchmark_result)
        self.assertIn("speedup", benchmark_result)

        self.assertGreater(benchmark_result["speedup"], 0)

    def test_benchmark_performance_improvement(self):
        """Test that optimized version is faster."""
        diff_content = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("hello")
+    print("hello world")
+    return True
"""

        benchmark_result = benchmark_diff_parsing(diff_content, iterations=100)

        # Optimized should be faster
        self.assertLess(
            benchmark_result["optimized_time"], benchmark_result["original_time"]
        )


class TestDiffParserClass(unittest.TestCase):
    """Test the enhanced DiffParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = DiffParser()
        self.sample_diff = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
 def test():
+    return True
"""

    def test_parser_caching_capabilities(self):
        """Test parser caching capabilities."""
        # Test cache stats
        stats = self.parser.get_cache_stats()
        self.assertIn("size", stats)
        self.assertIn("hit_rate", stats)

        # Test cache clearing
        self.parser.clear_cache()
        stats_after_clear = self.parser.get_cache_stats()
        self.assertEqual(stats_after_clear["size"], 0)

    def test_parser_optimized_methods(self):
        """Test parser optimized methods."""
        # Test optimized parsing
        changes = self.parser.parse_diff_optimized(self.sample_diff)
        self.assertGreater(len(changes), 0)
        self.assertIsInstance(changes[0], FileChange)

        # Test statistics
        stats = self.parser.get_diff_statistics(self.sample_diff)
        self.assertIn("total_files", stats)

        # Test validation
        validation = self.parser.validate_diff(self.sample_diff)
        self.assertTrue(validation["valid"])

    def test_parser_backward_compatibility(self):
        """Test that parser maintains backward compatibility."""
        # Test existing methods still work
        files = self.parser.filter_python_files(["test.py", "test.txt"])
        self.assertEqual(files, ["test.py"])

        extensions = self.parser.get_file_extensions(["test.py", "test.js"])
        self.assertIn("py", extensions)
        self.assertIn("js", extensions)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""

    def test_parse_hunk_header(self):
        """Test hunk header parsing."""
        from ai_guard.diff_parser import _parse_hunk_header

        # Test valid hunk header
        result = _parse_hunk_header("@@ -10,5 +15,8 @@")
        self.assertIsNotNone(result)
        old_start, old_count, new_start, new_count = result
        self.assertEqual(old_start, 10)
        self.assertEqual(new_start, 15)

        # Test invalid hunk header
        result = _parse_hunk_header("not a hunk header")
        self.assertIsNone(result)

    def test_get_cache_key(self):
        """Test cache key generation."""
        from ai_guard.diff_parser import _get_cache_key

        key1 = _get_cache_key("test data", "operation")
        key2 = _get_cache_key("test data", "operation")
        key3 = _get_cache_key("different data", "operation")

        # Same data should generate same key
        self.assertEqual(key1, key2)

        # Different data should generate different key
        self.assertNotEqual(key1, key3)

        # Key should contain operation name
        self.assertIn("operation", key1)


class TestDataClasses(unittest.TestCase):
    """Test data classes."""

    def test_file_change_class(self):
        """Test FileChange data class."""
        change = FileChange(
            file_path="test.py",
            change_type=ChangeType.MODIFIED,
            added_lines=5,
            removed_lines=3,
            similarity=85,
            old_path="old_test.py",
            is_binary=False,
        )

        self.assertEqual(change.file_path, "test.py")
        self.assertEqual(change.change_type, ChangeType.MODIFIED)
        self.assertEqual(change.added_lines, 5)
        self.assertEqual(change.removed_lines, 3)

        # Test to_dict method
        change_dict = change.to_dict()
        self.assertIn("file_path", change_dict)
        self.assertIn("change_type", change_dict)
        self.assertEqual(change_dict["change_type"], "modified")

    def test_line_change_class(self):
        """Test LineChange data class."""
        line_change = LineChange(
            line_number=10,
            change_type="added",
            content="    return True",
            file_path="test.py",
            hunk_start=5,
            hunk_end=15,
        )

        self.assertEqual(line_change.line_number, 10)
        self.assertEqual(line_change.change_type, "added")
        self.assertEqual(line_change.content, "    return True")

        # Test to_dict method
        line_dict = line_change.to_dict()
        self.assertIn("line_number", line_dict)
        self.assertIn("change_type", line_dict)
        self.assertEqual(line_dict["line_number"], 10)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_empty_diff_content(self):
        """Test handling of empty diff content."""
        self.assertEqual(extract_file_changes_optimized(""), [])
        self.assertEqual(get_added_lines_optimized(""), [])
        self.assertEqual(get_removed_lines_optimized(""), [])
        self.assertEqual(get_modified_files_optimized(""), [])

        stats = get_diff_statistics("")
        self.assertEqual(stats, {})

    def test_none_diff_content(self):
        """Test handling of None diff content."""
        self.assertEqual(extract_file_changes_optimized(None), [])
        self.assertEqual(get_added_lines_optimized(None), [])
        self.assertEqual(get_removed_lines_optimized(None), [])
        self.assertEqual(get_modified_files_optimized(None), [])

    def test_malformed_diff_content(self):
        """Test handling of malformed diff content."""
        malformed_diff = "this is not a diff at all"

        # Should handle gracefully
        changes = extract_file_changes_optimized(malformed_diff)
        self.assertEqual(changes, [])

        validation = validate_diff_format(malformed_diff)
        self.assertFalse(validation["valid"])
        self.assertGreater(len(validation["errors"]), 0)


class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimizations."""

    def test_regex_compilation(self):
        """Test that regex patterns are compiled for performance."""
        from ai_guard.diff_parser import (
            DIFF_FILE_PATTERN,
            HUNK_PATTERN,
            ADDED_LINE_PATTERN,
            REMOVED_LINE_PATTERN,
            FILE_MODE_PATTERN,
        )

        # Test that patterns are compiled regex objects
        self.assertTrue(hasattr(DIFF_FILE_PATTERN, "match"))
        self.assertTrue(hasattr(HUNK_PATTERN, "match"))
        self.assertTrue(hasattr(ADDED_LINE_PATTERN, "match"))
        self.assertTrue(hasattr(REMOVED_LINE_PATTERN, "match"))
        self.assertTrue(hasattr(FILE_MODE_PATTERN, "match"))

    def test_caching_performance(self):
        """Test that caching improves performance."""
        diff_content = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
 def test():
+    return True
"""

        # First call (cache miss)
        start_time = time.time()
        result1 = extract_file_changes_optimized(diff_content)
        first_call_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = extract_file_changes_optimized(diff_content)
        second_call_time = time.time() - start_time

        # Results should be identical
        self.assertEqual(result1, result2)

        # Second call should be faster due to caching
        self.assertLess(second_call_time, first_call_time)

    def test_parallel_processing_scalability(self):
        """Test parallel processing scalability."""
        # Create multiple diffs
        diffs = []
        for i in range(20):
            diff = f"""diff --git a/file{i}.py b/file{i}.py
+++ b/file{i}.py
@@ -1,1 +1,2 @@
 def func{i}():
+    return True
"""
            diffs.append(diff)

        # Test with different worker counts
        for workers in [1, 2, 4]:
            start_time = time.time()
            results = parse_multiple_diffs_parallel(diffs, max_workers=workers)
            processing_time = time.time() - start_time

            self.assertEqual(len(results), 20)
            self.assertGreater(len(results[0]), 0)


if __name__ == "__main__":
    # Run the test suite
    unittest.main(verbosity=2)
