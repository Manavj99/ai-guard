"""Comprehensive tests for enhanced cache module."""

import json
import os
import pickle
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_guard.cache import (
    CacheManager,
    CacheConfig,
    CacheStrategy,
    CompressionType,
    CacheEntry,
    CacheStats,
    FileCache,
    MemoryCache,
    DistributedCache,
    RedisDistributedCache,
    MultiTierCache,
    CacheWarmer,
    CachePerformanceMonitor,
    cached,
    async_cached,
    setup_distributed_cache,
    get_cache_manager,
    clear_all_caches,
    get_cache_analytics,
    optimize_all_caches,
    warm_all_caches,
    start_cache_monitoring,
    stop_cache_monitoring,
    get_cache_performance_summary,
    register_cache_alert_callback,
    cache_key_from_args,
    cache_key_from_file_path,
    cache_key_from_object,
)


class TestCacheConfig(unittest.TestCase):
    """Test cache configuration."""

    def test_cache_config_defaults(self):
        """Test cache config default values."""
        config = CacheConfig()
        self.assertEqual(config.max_size, 1000)
        self.assertEqual(config.max_memory_mb, 100)
        self.assertEqual(config.default_ttl, 3600)
        self.assertEqual(config.strategy, CacheStrategy.LRU)
        self.assertTrue(config.compression_enabled)
        self.assertTrue(config.enable_analytics)

    def test_cache_config_custom(self):
        """Test cache config with custom values."""
        config = CacheConfig(
            max_size=500,
            max_memory_mb=50,
            default_ttl=1800,
            strategy=CacheStrategy.LFU,
            compression_enabled=False,
            enable_analytics=False,
        )
        self.assertEqual(config.max_size, 500)
        self.assertEqual(config.max_memory_mb, 50)
        self.assertEqual(config.default_ttl, 1800)
        self.assertEqual(config.strategy, CacheStrategy.LFU)
        self.assertFalse(config.compression_enabled)
        self.assertFalse(config.enable_analytics)


class TestCacheEntry(unittest.TestCase):
    """Test cache entry functionality."""

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry("test_key", "test_value", ttl=300)
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.value, "test_value")
        self.assertEqual(entry.ttl, 300)
        self.assertGreater(entry.created_at, 0)
        self.assertGreater(entry.size_bytes, 0)

    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        entry = CacheEntry("test_key", "test_value", ttl=1)
        self.assertFalse(entry.is_expired())

        time.sleep(1.1)
        self.assertTrue(entry.is_expired())

    def test_cache_entry_touch(self):
        """Test cache entry touch functionality."""
        entry = CacheEntry("test_key", "test_value")
        initial_access = entry.last_accessed
        initial_count = entry.access_count

        time.sleep(0.01)
        entry.touch()

        self.assertGreater(entry.last_accessed, initial_access)
        self.assertEqual(entry.access_count, initial_count + 1)

    def test_cache_entry_age_calculation(self):
        """Test cache entry age calculation."""
        entry = CacheEntry("test_key", "test_value")
        initial_age = entry.get_age()

        time.sleep(0.1)
        self.assertGreater(entry.get_age(), initial_age)


class TestCacheManager(unittest.TestCase):
    """Test enhanced cache manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            cache_dir=self.temp_dir,
            config=CacheConfig(
                max_size=10,
                max_memory_mb=1,
                default_ttl=1,
                cleanup_interval=0,  # Disable background cleanup
                warm_cache_on_start=False,
            ),
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.cache_manager.shutdown()
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        self.assertIsNotNone(self.cache_manager.cache_dir)
        self.assertEqual(self.cache_manager.default_ttl, 1)
        self.assertIsInstance(self.cache_manager.stats, CacheStats)

    def test_basic_cache_operations(self):
        """Test basic cache operations."""
        # Set and get
        self.cache_manager.set("key1", "value1")
        result = self.cache_manager.get("key1")
        self.assertEqual(result, "value1")

        # Check stats
        stats = self.cache_manager.get_stats()
        self.assertGreater(stats["hits"], 0)

    def test_cache_expiration(self):
        """Test cache expiration."""
        self.cache_manager.set("key1", "value1", ttl=1)
        self.assertEqual(self.cache_manager.get("key1"), "value1")

        time.sleep(1.1)
        self.assertIsNone(self.cache_manager.get("key1"))

    def test_cache_deletion(self):
        """Test cache deletion."""
        self.cache_manager.set("key1", "value1")
        self.assertEqual(self.cache_manager.get("key1"), "value1")

        self.cache_manager.delete("key1")
        self.assertIsNone(self.cache_manager.get("key1"))

    def test_cache_clear(self):
        """Test cache clearing."""
        self.cache_manager.set("key1", "value1")
        self.cache_manager.set("key2", "value2")

        self.cache_manager.clear()

        self.assertIsNone(self.cache_manager.get("key1"))
        self.assertIsNone(self.cache_manager.get("key2"))

    def test_cache_compression(self):
        """Test cache compression."""
        large_value = "x" * 2000  # Large enough to trigger compression

        self.cache_manager.set("large_key", large_value, compress=True)
        result = self.cache_manager.get("large_key")
        self.assertEqual(result, large_value)

    def test_cache_eviction_lru(self):
        """Test LRU cache eviction."""
        self.cache_manager.config.strategy = CacheStrategy.LRU

        # Fill cache beyond capacity
        for i in range(15):
            self.cache_manager.set(f"key{i}", f"value{i}")

        # First key should be evicted (LRU)
        stats = self.cache_manager.get_stats()
        self.assertLessEqual(stats["memory_entries"], 10)

    def test_cache_eviction_lfu(self):
        """Test LFU cache eviction."""
        self.cache_manager.config.strategy = CacheStrategy.LFU

        # Fill cache and access some keys more frequently
        for i in range(15):
            self.cache_manager.set(f"key{i}", f"value{i}")

        # Access some keys multiple times
        for _ in range(5):
            self.cache_manager.get("key5")
            self.cache_manager.get("key6")

        # Fill cache again
        for i in range(15, 25):
            self.cache_manager.set(f"key{i}", f"value{i}")

        stats = self.cache_manager.get_stats()
        self.assertLessEqual(stats["memory_entries"], 10)

    def test_cache_analytics(self):
        """Test cache analytics."""
        # Generate some cache activity
        for i in range(5):
            self.cache_manager.set(f"key{i}", f"value{i}")
            self.cache_manager.get(f"key{i}")

        analytics = self.cache_manager.get_analytics()
        self.assertIn("cache_efficiency", analytics)
        self.assertIn("memory_usage", analytics)

    def test_cache_optimization(self):
        """Test cache optimization."""
        # Fill cache with old entries
        for i in range(8):
            self.cache_manager.set(f"key{i}", f"value{i}")

        optimization = self.cache_manager.optimize_cache()
        self.assertIn("actions_taken", optimization)
        self.assertIn("recommendations", optimization)

    def test_cache_warming(self):
        """Test cache warming."""
        # Set some entries on disk
        for i in range(3):
            self.cache_manager.set(f"key{i}", f"value{i}")

        # Clear memory cache
        self.cache_manager._cache.clear()

        # Warm cache
        warm_keys = [f"key{i}" for i in range(3)]
        self.cache_manager.warm_cache(warm_keys)

        # Check if entries are back in memory
        for i in range(3):
            result = self.cache_manager.get(f"key{i}")
            self.assertEqual(result, f"value{i}")

    def test_thread_safety(self):
        """Test cache thread safety."""
        results = []
        errors = []

        def worker(thread_id):
            try:
                for i in range(10):
                    key = f"thread{thread_id}_key{i}"
                    value = f"thread{thread_id}_value{i}"
                    self.cache_manager.set(key, value)
                    result = self.cache_manager.get(key)
                    results.append(result == value)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
        self.assertEqual(len(results), 50)
        self.assertTrue(all(results))


class TestFileCache(unittest.TestCase):
    """Test enhanced file cache."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_cache = FileCache(cache_dir=self.temp_dir, max_size=5)
        self.test_file = os.path.join(self.temp_dir, "test.py")

        # Create test file
        with open(self.test_file, "w") as f:
            f.write("print('Hello, World!')")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_cache_initialization(self):
        """Test file cache initialization."""
        self.assertIsNotNone(self.file_cache.cache_dir)
        self.assertEqual(self.file_cache.max_size, 5)

    def test_file_hash_generation(self):
        """Test file hash generation."""
        hash1 = self.file_cache.get_file_hash(self.test_file)
        hash2 = self.file_cache.get_file_hash(self.test_file)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, "")

        # Modify file and check hash changes
        with open(self.test_file, "w") as f:
            f.write("print('Modified!')")

        hash3 = self.file_cache.get_file_hash(self.test_file)
        self.assertNotEqual(hash1, hash3)

    def test_file_cache_operations(self):
        """Test file cache operations."""
        result_data = {"issues": [], "metrics": {"lines": 10}}

        # Set analysis result
        self.file_cache.set_analysis_result(
            self.test_file, "test_analysis", result_data
        )

        # Get analysis result
        cached_result = self.file_cache.get_analysis_result(
            self.test_file, "test_analysis"
        )

        self.assertEqual(cached_result, result_data)

    def test_file_cache_invalidation(self):
        """Test file cache invalidation."""
        result_data = {"issues": [], "metrics": {"lines": 10}}

        # Set analysis result
        self.file_cache.set_analysis_result(
            self.test_file, "test_analysis", result_data
        )

        # Verify it's cached
        cached_result = self.file_cache.get_analysis_result(
            self.test_file, "test_analysis"
        )
        self.assertEqual(cached_result, result_data)

        # Invalidate file
        self.file_cache.invalidate_file(self.test_file)

        # Verify it's no longer cached
        cached_result = self.file_cache.get_analysis_result(
            self.test_file, "test_analysis"
        )
        self.assertIsNone(cached_result)

    def test_file_cache_size_limits(self):
        """Test file cache size limits."""
        # Fill cache beyond capacity
        for i in range(10):
            test_file = os.path.join(self.temp_dir, f"test{i}.py")
            with open(test_file, "w") as f:
                f.write(f"print('Test {i}')")

            result_data = {"issues": [], "metrics": {"lines": i}}
            self.file_cache.set_analysis_result(test_file, "test_analysis", result_data)

        # Check that size limit is respected
        stats = self.file_cache.get_stats()
        self.assertLessEqual(stats["total_entries"], 5)

    def test_file_cache_cleanup(self):
        """Test file cache cleanup."""
        # Set some entries
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f"test{i}.py")
            with open(test_file, "w") as f:
                f.write(f"print('Test {i}')")

            result_data = {"issues": [], "metrics": {"lines": i}}
            self.file_cache.set_analysis_result(test_file, "test_analysis", result_data)

        # Clean up old entries
        cleaned = self.file_cache.cleanup_old_entries(max_age_hours=0)
        self.assertEqual(cleaned, 3)

        # Verify entries are cleaned
        stats = self.file_cache.get_stats()
        self.assertEqual(stats["total_entries"], 0)


class TestMemoryCache(unittest.TestCase):
    """Test enhanced memory cache."""

    def setUp(self):
        """Set up test fixtures."""
        self.memory_cache = MemoryCache(max_size=5, strategy=CacheStrategy.LRU)

    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        self.assertEqual(self.memory_cache.max_size, 5)
        self.assertEqual(self.memory_cache.strategy, CacheStrategy.LRU)

    def test_memory_cache_operations(self):
        """Test memory cache operations."""
        # Set and get
        self.memory_cache.set("key1", "value1")
        result = self.memory_cache.get("key1")
        self.assertEqual(result, "value1")

        # Check stats
        stats = self.memory_cache.get_stats()
        self.assertGreater(stats["hits"], 0)
        self.assertEqual(stats["entries"], 1)

    def test_memory_cache_eviction_lru(self):
        """Test LRU eviction in memory cache."""
        self.memory_cache.strategy = CacheStrategy.LRU

        # Fill cache
        for i in range(7):
            self.memory_cache.set(f"key{i}", f"value{i}")

        # Check size limit
        stats = self.memory_cache.get_stats()
        self.assertLessEqual(stats["entries"], 5)

    def test_memory_cache_eviction_lfu(self):
        """Test LFU eviction in memory cache."""
        self.memory_cache.strategy = CacheStrategy.LFU

        # Fill cache
        for i in range(7):
            self.memory_cache.set(f"key{i}", f"value{i}")

        # Access some keys more frequently
        for _ in range(3):
            self.memory_cache.get("key0")
            self.memory_cache.get("key1")

        # Add more entries
        for i in range(7, 12):
            self.memory_cache.set(f"key{i}", f"value{i}")

        # Check that frequently used keys are still there
        self.assertIsNotNone(self.memory_cache.get("key0"))
        self.assertIsNotNone(self.memory_cache.get("key1"))

    def test_memory_cache_optimization(self):
        """Test memory cache optimization."""
        # Fill cache with some entries
        for i in range(4):
            self.memory_cache.set(f"key{i}", f"value{i}")

        optimization = self.memory_cache.optimize()
        self.assertIn("actions_taken", optimization)
        self.assertIn("recommendations", optimization)

    def test_memory_cache_clear(self):
        """Test memory cache clearing."""
        # Add some entries
        for i in range(3):
            self.memory_cache.set(f"key{i}", f"value{i}")

        # Clear cache
        self.memory_cache.clear()

        # Verify empty
        stats = self.memory_cache.get_stats()
        self.assertEqual(stats["entries"], 0)
        self.assertEqual(stats["hits"], 0)


class TestDistributedCache(unittest.TestCase):
    """Test distributed cache functionality."""

    def test_redis_cache_initialization_no_redis(self):
        """Test Redis cache initialization without Redis available."""
        # Mock redis import failure
        with patch.dict("sys.modules", {"redis": None}):
            redis_cache = RedisDistributedCache()
            self.assertIsNone(redis_cache.redis_client)

    @patch("redis.Redis")
    def test_redis_cache_operations(self, mock_redis):
        """Test Redis cache operations with mocked Redis."""
        # Mock Redis client
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        redis_cache = RedisDistributedCache()

        # Test set operation
        test_value = {"test": "data"}
        redis_cache.set("test_key", test_value, ttl=3600)
        mock_client.setex.assert_called_once()

        # Test get operation
        mock_client.get.return_value = pickle.dumps(test_value)
        result = redis_cache.get("test_key")
        self.assertEqual(result, test_value)

        # Test delete operation
        redis_cache.delete("test_key")
        mock_client.delete.assert_called_once_with("test_key")

        # Test exists operation
        mock_client.exists.return_value = 1
        self.assertTrue(redis_cache.exists("test_key"))

    def test_multi_tier_cache(self):
        """Test multi-tier cache functionality."""
        # Create cache manager and multi-tier cache
        cache_manager = CacheManager()
        multi_tier = MultiTierCache(cache_manager)

        # Test operations
        multi_tier.set("test_key", "test_value")
        result = multi_tier.get("test_key")
        self.assertEqual(result, "test_value")

        # Test stats
        stats = multi_tier.get_stats()
        self.assertIn("l1_stats", stats)
        self.assertIn("tier_stats", stats)


class TestCacheDecorators(unittest.TestCase):
    """Test cache decorators."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cached_decorator(self):
        """Test cached decorator."""
        call_count = 0

        @cached(ttl=3600)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call should execute function
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)

        # Second call should use cache
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # Should not increment

    def test_cached_decorator_with_key_func(self):
        """Test cached decorator with custom key function."""
        call_count = 0

        def custom_key_func(x, y):
            return f"custom_{x}_{y}"

        @cached(key_func=custom_key_func)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call
        result1 = test_function(1, 2)
        self.assertEqual(result1, 3)
        self.assertEqual(call_count, 1)

        # Second call with same args should use cache
        result2 = test_function(1, 2)
        self.assertEqual(result2, 3)
        self.assertEqual(call_count, 1)

    def test_async_cached_decorator(self):
        """Test async cached decorator."""
        call_count = 0

        @async_cached(ttl=3600)
        async def async_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        async def run_test():
            # First call
            result1 = await async_function(4)
            self.assertEqual(result1, 12)
            self.assertEqual(call_count, 1)

            # Second call should use cache
            result2 = await async_function(4)
            self.assertEqual(result2, 12)
            self.assertEqual(call_count, 1)

        import asyncio

        asyncio.run(run_test())


class TestCacheUtilities(unittest.TestCase):
    """Test cache utility functions."""

    def test_cache_key_generation(self):
        """Test cache key generation functions."""
        # Test cache_key_from_args
        key1 = cache_key_from_args(1, 2, 3, a=4, b=5)
        key2 = cache_key_from_args(1, 2, 3, a=4, b=5)
        key3 = cache_key_from_args(1, 2, 3, a=4, b=6)

        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)

        # Test cache_key_from_file_path
        file_key1 = cache_key_from_file_path("/path/to/file.py", "config_hash")
        file_key2 = cache_key_from_file_path("/path/to/file.py", "config_hash")
        file_key3 = cache_key_from_file_path("/path/to/file.py", "different_hash")

        self.assertEqual(file_key1, file_key2)
        self.assertNotEqual(file_key1, file_key3)

        # Test cache_key_from_object
        obj = {"test": "object"}
        obj_key1 = cache_key_from_object(obj, "prefix")
        obj_key2 = cache_key_from_object(obj, "prefix")
        obj_key3 = cache_key_from_object(obj, "different_prefix")

        self.assertEqual(obj_key1, obj_key2)
        self.assertNotEqual(obj_key1, obj_key3)

    def test_global_cache_functions(self):
        """Test global cache functions."""
        # Test get_cache_manager
        cache_manager = get_cache_manager()
        self.assertIsNotNone(cache_manager)

        # Test get_cache_analytics
        analytics = get_cache_analytics()
        self.assertIn("main_cache", analytics)
        self.assertIn("file_cache", analytics)
        self.assertIn("memory_cache", analytics)

        # Test optimize_all_caches
        optimizations = optimize_all_caches()
        self.assertIn("main_cache", optimizations)
        self.assertIn("memory_cache", optimizations)
        self.assertIn("file_cache", optimizations)

        # Test warm_all_caches
        warming = warm_all_caches()
        self.assertIn("main_cache", warming)
        self.assertIn("file_cache", warming)

    def test_clear_all_caches(self):
        """Test clearing all caches."""
        # Add some data to caches
        cache_manager = get_cache_manager()
        cache_manager.set("test_key", "test_value")

        # Clear all caches
        clear_all_caches()

        # Verify cache is cleared
        result = cache_manager.get("test_key")
        self.assertIsNone(result)


class TestCachePerformanceMonitor(unittest.TestCase):
    """Test cache performance monitoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = CachePerformanceMonitor()

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertTrue(self.monitor.monitoring_enabled)
        self.assertEqual(len(self.monitor.metrics_history), 0)
        self.assertEqual(len(self.monitor.alert_callbacks), 0)

    def test_collect_metrics(self):
        """Test metrics collection."""
        metrics = self.monitor.collect_metrics()

        self.assertIn("timestamp", metrics)
        self.assertIn("main_cache", metrics)
        self.assertIn("memory_cache", metrics)
        self.assertIn("file_cache", metrics)
        self.assertIn("system_memory", metrics)

    def test_check_alerts(self):
        """Test alert checking."""
        # Create mock metrics with low hit rate
        mock_metrics = {
            "main_cache": {"hit_rate": 0.2},  # Low hit rate
            "memory_cache": {"utilization": 0.95},  # High utilization
            "file_cache": {"total_size_mb": 1500},  # Large file cache
        }

        alerts = self.monitor.check_alerts(mock_metrics)

        self.assertGreater(len(alerts), 0)
        self.assertIn("type", alerts[0])
        self.assertIn("severity", alerts[0])
        self.assertIn("message", alerts[0])

    def test_alert_callbacks(self):
        """Test alert callback functionality."""
        callback_called = []

        def test_callback(alert):
            callback_called.append(alert)

        self.monitor.register_alert_callback(test_callback)

        # Trigger an alert
        mock_metrics = {
            "main_cache": {"hit_rate": 0.2},
            "memory_cache": {"utilization": 0.5},
            "file_cache": {"total_size_mb": 500},
        }

        alerts = self.monitor.check_alerts(mock_metrics)
        for alert in alerts:
            self.monitor._trigger_alert_callbacks(alert)

        self.assertGreater(len(callback_called), 0)

    def test_performance_summary(self):
        """Test performance summary generation."""
        # Add some mock metrics
        current_time = time.time()
        self.monitor.metrics_history = [
            {
                "timestamp": current_time - 3600,
                "main_cache": {"hit_rate": 0.7},
                "memory_cache": {"utilization": 0.6},
            },
            {
                "timestamp": current_time - 1800,
                "main_cache": {"hit_rate": 0.8},
                "memory_cache": {"utilization": 0.7},
            },
            {
                "timestamp": current_time,
                "main_cache": {"hit_rate": 0.9},
                "memory_cache": {"utilization": 0.8},
            },
        ]

        summary = self.monitor.get_performance_summary(hours=2)

        self.assertIn("period_hours", summary)
        self.assertIn("data_points", summary)
        self.assertIn("average_hit_rate", summary)
        self.assertIn("average_memory_usage", summary)
        self.assertIn("hit_rate_trend", summary)
        self.assertIn("memory_usage_trend", summary)


class TestCacheWarmer(unittest.TestCase):
    """Test cache warming functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            cache_dir=self.temp_dir,
            config=CacheConfig(
                max_size=10, cleanup_interval=0, warm_cache_on_start=False
            ),
        )
        self.cache_warmer = CacheWarmer(self.cache_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        self.cache_manager.shutdown()
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_warmer_initialization(self):
        """Test cache warmer initialization."""
        self.assertIsNotNone(self.cache_warmer.cache_manager)
        self.assertIn("frequent", self.cache_warmer.warming_strategies)
        self.assertIn("recent", self.cache_warmer.warming_strategies)
        self.assertIn("large", self.cache_warmer.warming_strategies)
        self.assertIn("expiring", self.cache_warmer.warming_strategies)

    def test_frequent_keys_warming(self):
        """Test frequent keys warming strategy."""
        # Add some cache entries with different access patterns
        for i in range(5):
            self.cache_manager.set(f"key{i}", f"value{i}")
            # Access some keys more frequently
            if i < 3:
                for _ in range(i + 1):
                    self.cache_manager.get(f"key{i}")

        # Test frequent keys warming
        result = self.cache_warmer.warm_cache("frequent", limit=3)

        self.assertIn("strategy", result)
        self.assertIn("keys_attempted", result)
        self.assertIn("keys_warmed", result)
        self.assertIn("success_rate", result)

    def test_custom_warming_strategy(self):
        """Test custom warming strategy registration."""

        def custom_strategy(limit=10):
            return ["custom_key1", "custom_key2"]

        self.cache_warmer.register_strategy("custom", custom_strategy)

        self.assertIn("custom", self.cache_warmer.warming_strategies)

        result = self.cache_warmer.warm_cache("custom")
        self.assertEqual(result["strategy"], "custom")


class TestCacheIntegration(unittest.TestCase):
    """Test cache system integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_cache_workflow(self):
        """Test complete cache workflow."""
        # Setup distributed cache (will fail gracefully if Redis not available)
        setup_distributed_cache("redis", host="localhost", port=6379)

        # Get cache manager
        cache_manager = get_cache_manager()

        # Test basic operations
        cache_manager.set("integration_test", "test_value")
        result = cache_manager.get("integration_test")
        self.assertEqual(result, "test_value")

        # Test analytics
        analytics = get_cache_analytics()
        self.assertIsInstance(analytics, dict)

        # Test optimization
        optimizations = optimize_all_caches()
        self.assertIsInstance(optimizations, dict)

        # Test warming
        warming = warm_all_caches()
        self.assertIsInstance(warming, dict)

        # Test monitoring
        start_cache_monitoring(interval_seconds=1)
        time.sleep(1.1)  # Wait for one monitoring cycle

        summary = get_cache_performance_summary(hours=1)
        self.assertIsInstance(summary, dict)

        stop_cache_monitoring()

    def test_cache_performance_under_load(self):
        """Test cache performance under concurrent load."""
        cache_manager = CacheManager(
            cache_dir=self.temp_dir,
            config=CacheConfig(
                max_size=100, cleanup_interval=0, warm_cache_on_start=False
            ),
        )

        results = []
        errors = []

        def worker(worker_id, iterations=50):
            try:
                for i in range(iterations):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"

                    # Set value
                    cache_manager.set(key, value)

                    # Get value
                    result = cache_manager.get(key)
                    results.append(result == value)

                    # Sometimes delete
                    if i % 10 == 0:
                        cache_manager.delete(key)

            except Exception as e:
                errors.append(e)

        # Run multiple workers concurrently
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker, args=(worker_id, 20))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors and all operations succeeded
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        self.assertTrue(all(results), "Some cache operations failed")

        # Verify final state
        stats = cache_manager.get_stats()
        self.assertGreater(stats["hits"], 0)
        self.assertGreater(stats["misses"], 0)

        cache_manager.shutdown()


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
