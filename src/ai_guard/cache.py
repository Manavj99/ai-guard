"""Caching system for AI Guard."""

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from functools import wraps


class CacheManager:
    """Manages caching for AI Guard operations."""

    def __init__(
        self, cache_dir: Optional[str] = None, default_ttl: int = 3600  # 1 hour
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir or os.path.join(os.getcwd(), ".ai_guard_cache"))
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache metadata
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}  # type: ignore[return-value]

    def _save_metadata(self) -> None:
        """Save cache metadata."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except IOError:
            pass

    def _get_cache_key(self, key: str) -> str:
        """Generate cache key."""
        return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path."""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.cache"

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.metadata:
            return True

        entry_time = self.metadata[key].get("timestamp", 0)
        ttl = self.metadata[key].get("ttl", self.default_ttl)

        return bool(time.time() - entry_time > ttl)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if self._is_expired(key):
            self.delete(key)
            return None

        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)  # nosec B301 - internal cache, trusted data
        except (pickle.PickleError, IOError):
            self.delete(key)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        ttl = ttl or self.default_ttl
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(value, f)

            # Update metadata
            self.metadata[key] = {
                "timestamp": time.time(),
                "ttl": ttl,
                "size": cache_path.stat().st_size,
            }
            self._save_metadata()
        except IOError:
            pass

    def delete(self, key: str) -> None:
        """Delete cache entry.

        Args:
            key: Cache key
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                cache_path.unlink()
            except IOError:
                pass

        if key in self.metadata:
            del self.metadata[key]
            self._save_metadata()

    def clear(self) -> None:
        """Clear all cache entries."""
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except IOError:
                pass

        self.metadata.clear()
        self._save_metadata()

    def cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        expired_keys = [key for key in self.metadata.keys() if self._is_expired(key)]

        for key in expired_keys:
            self.delete(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        total_size = sum(entry.get("size", 0) for entry in self.metadata.values())

        return {
            "total_entries": len(self.metadata),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }


# Global cache instance
_cache_manager = CacheManager()


def cached(
    ttl: Optional[int] = None, key_func: Optional[Callable[..., str]] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
        key_func: Function to generate cache key
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Create a more robust cache key that includes function name and arguments
                key_data = {
                    "func_name": func.__name__,
                    "args": args,
                    "kwargs": tuple(sorted(kwargs.items())) if kwargs else (),
                }
                cache_key = f"{func.__name__}:{hash(str(key_data))}"

            # Try to get from cache
            cached_result = _cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_key_from_args(*args: Any, **kwargs: Any) -> str:
    """Generate cache key from function arguments."""
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    return hashlib.md5(str(key_data).encode(), usedforsecurity=False).hexdigest()


def cache_key_from_file_path(file_path: str, config_hash: str = "") -> str:
    """Generate cache key from file path and config."""
    key_data = f"{file_path}:{config_hash}"
    return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()


class FileCache:
    """File-based cache for analysis results."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize file cache.

        Args:
            cache_dir: Cache directory
        """
        self.cache_dir = Path(cache_dir or ".ai_guard_file_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_file_hash(self, file_path: str) -> str:
        """Get file hash for cache key."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except IOError:
            return ""

    def get_cache_path(self, file_path: str, analysis_type: str) -> Path:
        """Get cache file path."""
        file_hash = self.get_file_hash(file_path)
        cache_key = f"{analysis_type}_{file_hash}"
        return self.cache_dir / f"{cache_key}.json"

    def get_analysis_result(
        self, file_path: str, analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached analysis result.

        Args:
            file_path: Path to analyzed file
            analysis_type: Type of analysis

        Returns:
            Cached result or None
        """
        cache_path = self.get_cache_path(file_path, analysis_type)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def set_analysis_result(
        self, file_path: str, analysis_type: str, result: Dict[str, Any]
    ) -> None:
        """Cache analysis result.

        Args:
            file_path: Path to analyzed file
            analysis_type: Type of analysis
            result: Analysis result
        """
        cache_path = self.get_cache_path(file_path, analysis_type)
        try:
            with open(cache_path, "w") as f:
                json.dump(result, f, indent=2)
        except IOError:
            pass

    def invalidate_file(self, file_path: str) -> None:
        """Invalidate all cache entries for a file.

        Args:
            file_path: Path to file
        """
        file_hash = self.get_file_hash(file_path)
        for cache_file in self.cache_dir.glob(f"*_{file_hash}.json"):
            try:
                cache_file.unlink()
            except IOError:
                pass


class MemoryCache:
    """In-memory cache with LRU eviction."""

    def __init__(self, max_size: int = 1000):
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self._access_counter = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            # Use counter to ensure proper LRU ordering
            self._access_counter += 1
            self.access_times[key] = self._access_counter
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[key] = value
        self._access_counter += 1
        self.access_times[key] = self._access_counter

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        # Find the key with the oldest access time
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_times.clear()
        self._access_counter = 0


# Global cache instances
file_cache = FileCache()
memory_cache = MemoryCache()


def get_cache_manager() -> CacheManager:
    """Get global cache manager."""
    return _cache_manager


def clear_all_caches() -> None:
    """Clear all caches."""
    _cache_manager.clear()
    if file_cache.cache_dir.exists():
        file_cache.cache_dir.rmdir()
    memory_cache.clear()
