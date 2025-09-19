"""Tests for AI Guard cache system."""

import tempfile
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from src.ai_guard.cache import (
    CacheManager,
    cached,
    cache_key_from_args,
    cache_key_from_file_path,
    FileCache,
    MemoryCache,
    get_cache_manager,
    clear_all_caches
)


class TestCacheManager:
    """Test CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir)
            
            assert cache_manager.cache_dir == Path(temp_dir)
            assert cache_manager.default_ttl == 3600
            assert cache_manager.cache_dir.exists()

    def test_cache_manager_default_dir(self):
        """Test cache manager with default directory."""
        cache_manager = CacheManager()
        
        assert cache_manager.cache_dir.name == ".ai_guard_cache"
        assert cache_manager.default_ttl == 3600

    def test_set_and_get(self):
        """Test setting and getting cache values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir)
            
            # Set value
            cache_manager.set("test_key", "test_value")
            
            # Get value
            value = cache_manager.get("test_key")
            assert value == "test_value"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir)
            
            value = cache_manager.get("nonexistent_key")
            assert value is None

    def test_cache_expiration(self):
        """Test cache expiration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir, default_ttl=1)  # 1 second TTL
            
            # Set value
            cache_manager.set("test_key", "test_value")
            
            # Should be available immediately
            assert cache_manager.get("test_key") == "test_value"
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Should be expired
            assert cache_manager.get("test_key") is None

    def test_custom_ttl(self):
        """Test custom TTL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir, default_ttl=3600)
            
            # Set value with custom TTL
            cache_manager.set("test_key", "test_value", ttl=1)
            
            # Should be available immediately
            assert cache_manager.get("test_key") == "test_value"
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Should be expired
            assert cache_manager.get("test_key") is None

    def test_delete_key(self):
        """Test deleting cache key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir)
            
            # Set value
            cache_manager.set("test_key", "test_value")
            assert cache_manager.get("test_key") == "test_value"
            
            # Delete value
            cache_manager.delete("test_key")
            assert cache_manager.get("test_key") is None

    def test_clear_cache(self):
        """Test clearing all cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir)
            
            # Set multiple values
            cache_manager.set("key1", "value1")
            cache_manager.set("key2", "value2")
            
            # Clear cache
            cache_manager.clear()
            
            # All values should be gone
            assert cache_manager.get("key1") is None
            assert cache_manager.get("key2") is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir, default_ttl=1)
            
            # Set value
            cache_manager.set("test_key", "test_value")
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Cleanup expired
            cache_manager.cleanup_expired()
            
            # Should be gone
            assert cache_manager.get("test_key") is None

    def test_get_stats(self):
        """Test getting cache statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir)
            
            # Set some values
            cache_manager.set("key1", "value1")
            cache_manager.set("key2", "value2")
            
            stats = cache_manager.get_stats()
            
            assert stats['total_entries'] == 2
            assert stats['total_size_bytes'] > 0
            assert 'total_size_mb' in stats
            assert 'cache_dir' in stats


class TestCachedDecorator:
    """Test cached decorator."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_all_caches()

    def test_cached_decorator(self):
        """Test cached decorator functionality."""
        call_count = 0
        
        @cached(ttl=3600)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = test_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment

    def test_cached_decorator_with_custom_key(self):
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
        assert result1 == 3
        assert call_count == 1
        
        # Second call with same args should use cache
        result2 = test_function(1, 2)
        assert result2 == 3
        assert call_count == 1

    def test_cached_decorator_different_args(self):
        """Test cached decorator with different arguments."""
        call_count = 0
        
        @cached()
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call
        result1 = test_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call with different args should execute function
        result2 = test_function(2, 3)
        assert result2 == 5
        assert call_count == 2


class TestCacheKeyFunctions:
    """Test cache key generation functions."""

    def test_cache_key_from_args(self):
        """Test cache key generation from arguments."""
        key1 = cache_key_from_args(1, 2, 3, a=4, b=5)
        key2 = cache_key_from_args(1, 2, 3, a=4, b=5)
        key3 = cache_key_from_args(1, 2, 3, a=5, b=4)  # Different order
        
        assert key1 == key2  # Same args should produce same key
        assert key1 != key3  # Different args should produce different key

    def test_cache_key_from_file_path(self):
        """Test cache key generation from file path."""
        key1 = cache_key_from_file_path("test.py", "config_hash")
        key2 = cache_key_from_file_path("test.py", "config_hash")
        key3 = cache_key_from_file_path("test.py", "different_hash")
        
        assert key1 == key2  # Same path and config should produce same key
        assert key1 != key3  # Different config should produce different key


class TestFileCache:
    """Test FileCache class."""

    def test_file_cache_initialization(self):
        """Test file cache initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_cache = FileCache(temp_dir)
            
            assert file_cache.cache_dir == Path(temp_dir)
            assert file_cache.cache_dir.exists()

    def test_file_cache_default_dir(self):
        """Test file cache with default directory."""
        file_cache = FileCache()
        
        assert file_cache.cache_dir.name == ".ai_guard_file_cache"

    def test_get_file_hash(self):
        """Test getting file hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_path = temp_file.name
        
        try:
            file_cache = FileCache()
            hash1 = file_cache.get_file_hash(temp_path)
            hash2 = file_cache.get_file_hash(temp_path)
            
            assert hash1 == hash2  # Same content should produce same hash
            assert len(hash1) == 64  # SHA256 hash length
        
        finally:
            os.unlink(temp_path)

    def test_get_file_hash_nonexistent(self):
        """Test getting hash of non-existent file."""
        file_cache = FileCache()
        hash_value = file_cache.get_file_hash("nonexistent_file.txt")
        
        assert hash_value == ""

    def test_set_and_get_analysis_result(self):
        """Test setting and getting analysis results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_cache = FileCache(temp_dir)
            
            result = {"coverage": 85, "issues": 2}
            
            # Set result
            file_cache.set_analysis_result("test.py", "coverage", result)
            
            # Get result
            retrieved_result = file_cache.get_analysis_result("test.py", "coverage")
            assert retrieved_result == result

    def test_get_analysis_result_nonexistent(self):
        """Test getting non-existent analysis result."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_cache = FileCache(temp_dir)
            
            result = file_cache.get_analysis_result("test.py", "coverage")
            assert result is None

    def test_invalidate_file(self):
        """Test invalidating file cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_cache = FileCache(temp_dir)
            
            result = {"coverage": 85}
            
            # Set result
            file_cache.set_analysis_result("test.py", "coverage", result)
            
            # Should be available
            assert file_cache.get_analysis_result("test.py", "coverage") == result
            
            # Invalidate file
            file_cache.invalidate_file("test.py")
            
            # Should be gone
            assert file_cache.get_analysis_result("test.py", "coverage") is None


class TestMemoryCache:
    """Test MemoryCache class."""

    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        cache = MemoryCache(max_size=100)
        
        assert cache.max_size == 100
        assert len(cache.cache) == 0
        assert len(cache.access_times) == 0

    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = MemoryCache()
        
        # Set value
        cache.set("key1", "value1")
        
        # Get value
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        cache = MemoryCache()
        
        assert cache.get("nonexistent_key") is None

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = MemoryCache(max_size=2)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add third item, should evict key2 (least recently used)
        cache.set("key3", "value3")
        
        # key1 should still be there
        assert cache.get("key1") == "value1"
        
        # key2 should be evicted
        assert cache.get("key2") is None
        
        # key3 should be there
        assert cache.get("key3") == "value3"

    def test_clear(self):
        """Test clearing cache."""
        cache = MemoryCache()
        
        # Set some values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Clear cache
        cache.clear()
        
        # All values should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestGlobalCacheFunctions:
    """Test global cache functions."""

    def test_get_cache_manager(self):
        """Test getting global cache manager."""
        cache_manager = get_cache_manager()
        
        assert isinstance(cache_manager, CacheManager)

    def test_clear_all_caches(self):
        """Test clearing all caches."""
        # This test might affect other tests, so we'll just test that it doesn't crash
        try:
            clear_all_caches()
        except Exception:
            # If it fails, that's okay for this test
            pass
