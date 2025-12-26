"""Enhanced test coverage for cache.py module to achieve 60%+ coverage."""

import pytest
import tempfile
import os
import time
import threading
from unittest.mock import patch, MagicMock, call

from src.ai_guard.cache import (
    Cache,
    LRUCache,
    TTLCache,
    CacheManager,
    cache_result,
    get_cache_stats,
    clear_all_caches,
    _cache_instances,
    _cache_lock,
)


class TestCache:
    """Test Cache base class."""

    def test_cache_init(self):
        """Test Cache initialization."""
        cache = Cache(max_size=100)
        assert cache.max_size == 100
        assert cache.size == 0

    def test_cache_get_missing(self):
        """Test getting missing key from cache."""
        cache = Cache()
        result = cache.get("missing_key")
        assert result is None

    def test_cache_set_get(self):
        """Test setting and getting from cache."""
        cache = Cache()
        cache.set("key", "value")
        assert cache.get("key") == "value"
        assert cache.size == 1

    def test_cache_delete(self):
        """Test deleting from cache."""
        cache = Cache()
        cache.set("key", "value")
        assert cache.get("key") == "value"

        cache.delete("key")
        assert cache.get("key") is None
        assert cache.size == 0

    def test_cache_delete_missing(self):
        """Test deleting missing key from cache."""
        cache = Cache()
        cache.delete("missing_key")  # Should not raise exception
        assert cache.size == 0

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size == 2

        cache.clear()
        assert cache.size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_contains(self):
        """Test checking if key exists in cache."""
        cache = Cache()
        assert "key" not in cache

        cache.set("key", "value")
        assert "key" in cache

    def test_cache_len(self):
        """Test cache length."""
        cache = Cache()
        assert len(cache) == 0

        cache.set("key1", "value1")
        assert len(cache) == 1

        cache.set("key2", "value2")
        assert len(cache) == 2

    def test_cache_keys(self):
        """Test getting cache keys."""
        cache = Cache()
        assert list(cache.keys()) == []

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        keys = list(cache.keys())
        assert "key1" in keys
        assert "key2" in keys
        assert len(keys) == 2

    def test_cache_values(self):
        """Test getting cache values."""
        cache = Cache()
        assert list(cache.values()) == []

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        values = list(cache.values())
        assert "value1" in values
        assert "value2" in values
        assert len(values) == 2

    def test_cache_items(self):
        """Test getting cache items."""
        cache = Cache()
        assert list(cache.items()) == []

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        items = list(cache.items())
        assert ("key1", "value1") in items
        assert ("key2", "value2") in items
        assert len(items) == 2

    def test_cache_stats(self):
        """Test getting cache statistics."""
        cache = Cache()
        stats = cache.get_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "size" in stats
        assert "max_size" in stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0

    def test_cache_hit_miss_stats(self):
        """Test cache hit/miss statistics."""
        cache = Cache()

        # Test miss
        cache.get("missing")
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

        # Test hit
        cache.set("key", "value")
        cache.get("key")
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1


class TestLRUCache:
    """Test LRUCache class."""

    def test_lru_cache_init(self):
        """Test LRUCache initialization."""
        cache = LRUCache(max_size=3)
        assert cache.max_size == 3
        assert cache.size == 0

    def test_lru_cache_basic_operations(self):
        """Test basic LRU cache operations."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.size == 3

    def test_lru_cache_eviction(self):
        """Test LRU cache eviction."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Add fourth item - should evict key1 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # Should be evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
        assert cache.size == 3

    def test_lru_cache_access_updates_order(self):
        """Test that accessing updates LRU order."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add fourth item - should evict key2 (least recently used now)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Should still be there
        assert cache.get("key2") is None  # Should be evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_cache_update_existing_key(self):
        """Test updating existing key in LRU cache."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Update existing key
        cache.set("key1", "new_value1")

        assert cache.get("key1") == "new_value1"
        assert cache.get("key2") == "value2"
        assert cache.size == 2

    def test_lru_cache_delete(self):
        """Test deleting from LRU cache."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.delete("key2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.size == 2

    def test_lru_cache_clear(self):
        """Test clearing LRU cache."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_lru_cache_zero_max_size(self):
        """Test LRU cache with zero max size."""
        cache = LRUCache(max_size=0)

        cache.set("key", "value")
        assert cache.get("key") is None
        assert cache.size == 0

    def test_lru_cache_one_max_size(self):
        """Test LRU cache with max size of 1."""
        cache = LRUCache(max_size=1)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.set("key2", "value2")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"


class TestTTLCache:
    """Test TTLCache class."""

    def test_ttl_cache_init(self):
        """Test TTLCache initialization."""
        cache = TTLCache(max_size=100, ttl=60)
        assert cache.max_size == 100
        assert cache.ttl == 60
        assert cache.size == 0

    def test_ttl_cache_basic_operations(self):
        """Test basic TTL cache operations."""
        cache = TTLCache(max_size=100, ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.size == 2

    def test_ttl_cache_expiration(self):
        """Test TTL cache expiration."""
        cache = TTLCache(max_size=100, ttl=0.1)  # 100ms TTL

        cache.set("key", "value")
        assert cache.get("key") == "value"

        # Wait for expiration
        time.sleep(0.2)

        assert cache.get("key") is None
        assert cache.size == 0

    def test_ttl_cache_no_expiration(self):
        """Test TTL cache without expiration."""
        cache = TTLCache(max_size=100, ttl=None)

        cache.set("key", "value")

        # Wait a bit
        time.sleep(0.1)

        assert cache.get("key") == "value"
        assert cache.size == 1

    def test_ttl_cache_access_extends_ttl(self):
        """Test that accessing extends TTL."""
        cache = TTLCache(max_size=100, ttl=0.2)  # 200ms TTL

        cache.set("key", "value")

        # Wait 150ms
        time.sleep(0.15)

        # Access key - should extend TTL
        assert cache.get("key") == "value"

        # Wait another 150ms
        time.sleep(0.15)

        # Should still be there due to TTL extension
        assert cache.get("key") == "value"

    def test_ttl_cache_update_existing_key(self):
        """Test updating existing key in TTL cache."""
        cache = TTLCache(max_size=100, ttl=60)

        cache.set("key", "value1")
        assert cache.get("key") == "value1"

        cache.set("key", "value2")
        assert cache.get("key") == "value2"
        assert cache.size == 1

    def test_ttl_cache_delete(self):
        """Test deleting from TTL cache."""
        cache = TTLCache(max_size=100, ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.delete("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.size == 1

    def test_ttl_cache_clear(self):
        """Test clearing TTL cache."""
        cache = TTLCache(max_size=100, ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_ttl_cache_cleanup_expired(self):
        """Test TTL cache cleanup of expired items."""
        cache = TTLCache(max_size=100, ttl=0.1)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Wait for expiration
        time.sleep(0.2)

        # Access one key to trigger cleanup
        cache.get("key1")

        assert cache.size == 0

    def test_ttl_cache_stats(self):
        """Test TTL cache statistics."""
        cache = TTLCache(max_size=100, ttl=60)

        cache.set("key", "value")
        cache.get("key")
        cache.get("missing")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1


class TestCacheManager:
    """Test CacheManager class."""

    def test_cache_manager_init(self):
        """Test CacheManager initialization."""
        manager = CacheManager()
        assert manager.caches == {}

    def test_cache_manager_create_cache(self):
        """Test creating cache through manager."""
        manager = CacheManager()

        cache = manager.create_cache("test_cache", "lru", max_size=100)
        assert isinstance(cache, LRUCache)
        assert cache.max_size == 100
        assert "test_cache" in manager.caches

    def test_cache_manager_create_ttl_cache(self):
        """Test creating TTL cache through manager."""
        manager = CacheManager()

        cache = manager.create_cache("test_cache", "ttl", max_size=100, ttl=60)
        assert isinstance(cache, TTLCache)
        assert cache.max_size == 100
        assert cache.ttl == 60

    def test_cache_manager_create_unsupported_type(self):
        """Test creating unsupported cache type."""
        manager = CacheManager()

        with pytest.raises(ValueError):
            manager.create_cache("test_cache", "unsupported")

    def test_cache_manager_get_cache(self):
        """Test getting cache from manager."""
        manager = CacheManager()

        # Create cache
        cache1 = manager.create_cache("test_cache", "lru", max_size=100)

        # Get cache
        cache2 = manager.get_cache("test_cache")
        assert cache1 is cache2

    def test_cache_manager_get_missing_cache(self):
        """Test getting missing cache from manager."""
        manager = CacheManager()

        cache = manager.get_cache("missing_cache")
        assert cache is None

    def test_cache_manager_delete_cache(self):
        """Test deleting cache from manager."""
        manager = CacheManager()

        cache = manager.create_cache("test_cache", "lru", max_size=100)
        assert "test_cache" in manager.caches

        manager.delete_cache("test_cache")
        assert "test_cache" not in manager.caches

    def test_cache_manager_delete_missing_cache(self):
        """Test deleting missing cache from manager."""
        manager = CacheManager()

        # Should not raise exception
        manager.delete_cache("missing_cache")

    def test_cache_manager_clear_all_caches(self):
        """Test clearing all caches in manager."""
        manager = CacheManager()

        cache1 = manager.create_cache("cache1", "lru", max_size=100)
        cache2 = manager.create_cache("cache2", "lru", max_size=100)

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        manager.clear_all_caches()

        assert cache1.size == 0
        assert cache2.size == 0

    def test_cache_manager_get_stats(self):
        """Test getting stats from all caches."""
        manager = CacheManager()

        cache1 = manager.create_cache("cache1", "lru", max_size=100)
        cache2 = manager.create_cache("cache2", "lru", max_size=100)

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        stats = manager.get_stats()
        assert "cache1" in stats
        assert "cache2" in stats
        assert stats["cache1"]["size"] == 1
        assert stats["cache2"]["size"] == 1


class TestCacheResult:
    """Test cache_result decorator."""

    def test_cache_result_basic(self):
        """Test basic cache_result functionality."""
        call_count = 0

        @cache_result(cache_name="test_cache", ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should be cached
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

    def test_cache_result_different_args(self):
        """Test cache_result with different arguments."""
        call_count = 0

        @cache_result(cache_name="test_cache", ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Call with different args
        result1 = test_function(5)
        result2 = test_function(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2

    def test_cache_result_ttl_expiration(self):
        """Test cache_result with TTL expiration."""
        call_count = 0

        @cache_result(cache_name="test_cache", ttl=0.1)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Wait for expiration
        time.sleep(0.2)

        # Second call - should call function again
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 2

    def test_cache_result_no_cache(self):
        """Test cache_result with no caching."""
        call_count = 0

        @cache_result(cache_name="test_cache", ttl=None)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should call function again (no caching)
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 2

    def test_cache_result_exception(self):
        """Test cache_result with exceptions."""
        call_count = 0

        @cache_result(cache_name="test_cache", ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            if x < 0:
                raise ValueError("Negative value")
            return x * 2

        # Call with exception
        with pytest.raises(ValueError):
            test_function(-1)

        assert call_count == 1

        # Call again - should raise exception again (not cached)
        with pytest.raises(ValueError):
            test_function(-1)

        assert call_count == 2


class TestCacheStats:
    """Test get_cache_stats function."""

    def test_get_cache_stats_empty(self):
        """Test getting stats with no caches."""
        stats = get_cache_stats()
        assert stats == {}

    def test_get_cache_stats_with_caches(self):
        """Test getting stats with caches."""
        # Create some caches
        cache1 = CacheManager().create_cache("cache1", "lru", max_size=100)
        cache2 = CacheManager().create_cache("cache2", "lru", max_size=100)

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        stats = get_cache_stats()
        assert "cache1" in stats
        assert "cache2" in stats
        assert stats["cache1"]["size"] == 1
        assert stats["cache2"]["size"] == 1


class TestClearAllCaches:
    """Test clear_all_caches function."""

    def test_clear_all_caches(self):
        """Test clearing all caches."""
        # Create some caches
        cache1 = CacheManager().create_cache("cache1", "lru", max_size=100)
        cache2 = CacheManager().create_cache("cache2", "lru", max_size=100)

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        clear_all_caches()

        assert cache1.size == 0
        assert cache2.size == 0


class TestThreadSafety:
    """Test thread safety of cache operations."""

    def test_lru_cache_thread_safety(self):
        """Test LRU cache thread safety."""
        cache = LRUCache(max_size=100)

        def worker(thread_id):
            for i in range(100):
                key = f"key_{thread_id}_{i}"
                value = f"value_{thread_id}_{i}"
                cache.set(key, value)
                assert cache.get(key) == value

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify cache is in consistent state
        assert cache.size <= cache.max_size

    def test_ttl_cache_thread_safety(self):
        """Test TTL cache thread safety."""
        cache = TTLCache(max_size=100, ttl=60)

        def worker(thread_id):
            for i in range(50):
                key = f"key_{thread_id}_{i}"
                value = f"value_{thread_id}_{i}"
                cache.set(key, value)
                assert cache.get(key) == value

        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify cache is in consistent state
        assert cache.size <= cache.max_size

    def test_cache_manager_thread_safety(self):
        """Test CacheManager thread safety."""
        manager = CacheManager()

        def worker(thread_id):
            for i in range(50):
                cache_name = f"cache_{thread_id}"
                cache = manager.create_cache(cache_name, "lru", max_size=100)
                cache.set(f"key_{i}", f"value_{i}")
                assert cache.get(f"key_{i}") == f"value_{i}"

        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify manager is in consistent state
        assert len(manager.caches) >= 3
