"""Basic performance module tests - PerformanceMetrics, PerformanceMonitor, SimpleCache."""

import time
import threading
import pytest
from unittest.mock import patch, MagicMock
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    SimpleCache,
    get_performance_monitor,
    get_cache,
    _get_cache,
    clear_cache,
    _clear_cache,
    reset_global_monitor,
    clear_performance_data,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metric = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=100.0,
            cache_hits=5,
            cache_misses=2,
        )

        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.5
        assert metric.memory_usage == 100.0
        assert metric.cache_hits == 5
        assert metric.cache_misses == 2

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metric = PerformanceMetrics(function_name="test_func", execution_time=1.0)

        assert metric.function_name == "test_func"
        assert metric.execution_time == 1.0
        assert metric.memory_usage is None
        assert metric.cache_hits is None
        assert metric.cache_misses is None


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()

        assert monitor.metrics == []
        assert hasattr(monitor._lock, "acquire")  # Check it's a lock-like object

    def test_record_metric(self):
        """Test recording a metric."""
        monitor = PerformanceMonitor()
        metric = PerformanceMetrics(function_name="test_func", execution_time=1.0)

        monitor.record_metric(metric)

        assert len(monitor.metrics) == 1
        assert monitor.metrics[0] == metric

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        monitor = PerformanceMonitor()

        metric1 = PerformanceMetrics("func1", 1.0)
        metric2 = PerformanceMetrics("func2", 2.0)
        metric3 = PerformanceMetrics("func1", 1.5)

        monitor.record_metric(metric1)
        monitor.record_metric(metric2)
        monitor.record_metric(metric3)

        assert len(monitor.metrics) == 3

    def test_get_average_time(self):
        """Test getting average execution time."""
        monitor = PerformanceMonitor()

        # Add metrics for func1
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        monitor.record_metric(PerformanceMetrics("func1", 2.0))
        monitor.record_metric(PerformanceMetrics("func1", 3.0))

        # Add metrics for func2
        monitor.record_metric(PerformanceMetrics("func2", 5.0))

        avg_time_func1 = monitor.get_average_time("func1")
        avg_time_func2 = monitor.get_average_time("func2")
        avg_time_nonexistent = monitor.get_average_time("nonexistent")

        assert avg_time_func1 == 2.0  # (1.0 + 2.0 + 3.0) / 3
        assert avg_time_func2 == 5.0
        assert avg_time_nonexistent is None

    def test_get_total_metrics(self):
        """Test getting total number of metrics."""
        monitor = PerformanceMonitor()

        assert monitor.get_total_metrics() == 0

        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        assert monitor.get_total_metrics() == 1

        monitor.record_metric(PerformanceMetrics("func2", 2.0))
        assert monitor.get_total_metrics() == 2

    def test_clear_metrics(self):
        """Test clearing all metrics."""
        monitor = PerformanceMonitor()

        # Add some metrics
        monitor.record_metric(PerformanceMetrics("func1", 1.0))
        monitor.record_metric(PerformanceMetrics("func2", 2.0))
        assert monitor.get_total_metrics() == 2

        # Clear metrics
        monitor.clear_metrics()
        assert monitor.get_total_metrics() == 0
        assert monitor.metrics == []

    def test_thread_safety(self):
        """Test thread safety of PerformanceMonitor."""
        monitor = PerformanceMonitor()
        results = []

        def record_metrics():
            for i in range(100):
                metric = PerformanceMetrics(f"func_{i}", i * 0.01)
                monitor.record_metric(metric)
                results.append(i)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all metrics were recorded
        assert monitor.get_total_metrics() == 500
        assert len(results) == 500


class TestSimpleCache:
    """Test SimpleCache class."""

    def test_cache_initialization(self):
        """Test SimpleCache initialization."""
        cache = SimpleCache(ttl_seconds=300)

        assert cache.cache == {}
        assert cache.ttl == 300
        assert hasattr(cache._lock, "acquire")  # Check it's a lock-like object

    def test_cache_default_ttl(self):
        """Test SimpleCache with default TTL."""
        cache = SimpleCache()
        assert cache.ttl == 300

    def test_cache_set_get(self):
        """Test setting and getting cache values."""
        cache = SimpleCache()

        cache.set("key1", "value1")
        cache.set("key2", {"nested": "value"})

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == {"nested": "value"}
        assert cache.get("nonexistent") is None

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = SimpleCache(ttl_seconds=1)  # 1 second TTL

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = SimpleCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None

    def test_cache_size(self):
        """Test getting cache size."""
        cache = SimpleCache()

        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

        # Set same key again (should not increase size)
        cache.set("key1", "new_value")
        assert cache.size() == 2

    def test_cache_dict_like_access(self):
        """Test dict-like access methods."""
        cache = SimpleCache()

        # Test __setitem__ and __getitem__
        cache["key1"] = "value1"
        assert cache["key1"] == "value1"

        # Test KeyError for missing key
        with pytest.raises(KeyError):
            _ = cache["nonexistent"]

        # Test __contains__
        assert "key1" in cache
        assert "nonexistent" not in cache

        # Test __len__
        assert len(cache) == 1

    def test_cache_keys_values_items(self):
        """Test cache keys, values, and items methods."""
        cache = SimpleCache()

        cache["key1"] = "value1"
        cache["key2"] = "value2"

        assert set(cache.keys()) == {"key1", "key2"}
        assert set(cache.values()) == {"value1", "value2"}
        assert set(cache.items()) == {("key1", "value1"), ("key2", "value2")}

    def test_cache_update_dict(self):
        """Test cache update with dict."""
        cache = SimpleCache()

        cache["key1"] = "value1"

        # Update with dict
        cache.update({"key2": "value2", "key3": "value3"})

        assert cache["key1"] == "value1"
        assert cache["key2"] == "value2"
        assert cache["key3"] == "value3"

    def test_cache_update_kwargs(self):
        """Test cache update with kwargs."""
        cache = SimpleCache()

        cache.update(key1="value1", key2="value2")

        assert cache["key1"] == "value1"
        assert cache["key2"] == "value2"

    def test_cache_update_iterable(self):
        """Test cache update with iterable."""
        cache = SimpleCache()

        cache.update([("key1", "value1"), ("key2", "value2")])

        assert cache["key1"] == "value1"
        assert cache["key2"] == "value2"

    def test_cache_thread_safety(self):
        """Test thread safety of SimpleCache."""
        cache = SimpleCache()
        results = []

        def cache_operations():
            for i in range(100):
                cache.set(f"key_{i}", f"value_{i}")
                value = cache.get(f"key_{i}")
                results.append(value)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_operations)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify cache operations were successful
        # Note: Cache size may be less than 500 due to key collisions in concurrent access
        assert cache.size() >= 100  # At least 100 unique keys
        assert len(results) == 500


class TestGlobalInstances:
    """Test global instances and utility functions."""

    def test_get_performance_monitor(self):
        """Test getting global performance monitor."""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

    def test_get_cache(self):
        """Test getting global cache."""
        cache = get_cache()
        assert isinstance(cache, SimpleCache)

    def test_get_cache_internal(self):
        """Test getting internal cache."""
        cache = _get_cache()
        assert isinstance(cache, SimpleCache)

    def test_clear_cache_functions(self):
        """Test cache clearing functions."""
        # Clear any existing cache state
        clear_cache()

        cache = get_cache()

        cache.set("key1", "value1")
        assert cache.size() == 1

        clear_cache()
        assert cache.size() == 0

        cache.set("key2", "value2")
        assert cache.size() == 1

        _clear_cache()
        assert cache.size() == 0

    def test_clear_performance_data(self):
        """Test clearing all performance data."""
        # Clear any existing state
        clear_performance_data()

        monitor = get_performance_monitor()
        cache = get_cache()

        # Add some data
        monitor.record_metric(PerformanceMetrics("test_func", 1.0))
        cache.set("test_key", "test_value")

        assert monitor.get_total_metrics() == 1
        assert cache.size() == 1

        # Clear all data
        clear_performance_data()

        assert monitor.get_total_metrics() == 0
        assert cache.size() == 0

    def test_reset_global_monitor(self):
        """Test resetting global monitor."""
        # Clear any existing state
        clear_performance_data()

        monitor1 = get_performance_monitor()

        # Add some metrics
        monitor1.record_metric(PerformanceMetrics("test_func", 1.0))
        assert monitor1.get_total_metrics() == 1

        # Reset global monitor
        reset_global_monitor()

        # Get new monitor instance
        monitor2 = get_performance_monitor()
        assert monitor2.get_total_metrics() == 0
        assert monitor2 is not monitor1
