"""Performance optimization utilities for AI-Guard."""

import time
import functools
import threading
import hashlib
import json
import gc
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import weakref
from contextlib import contextmanager


class MetricType(Enum):
    """Types of performance metrics."""

    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    THREAD_COUNT = "thread_count"
    FILE_OPERATION = "file_operation"
    NETWORK_OPERATION = "network_operation"


@dataclass
class PerformanceMetrics:
    """Enhanced performance metrics for tracking execution times."""

    function_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None
    cpu_usage: Optional[float] = None
    thread_count: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    metric_type: MetricType = MetricType.EXECUTION_TIME
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Cache statistics for monitoring performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 1000
    hit_rate: float = 0.0

    def update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        total = self.hits + self.misses
        self.hit_rate = (self.hits / total) if total > 0 else 0.0


@dataclass
class PerformanceProfile:
    """Comprehensive performance profile for a function."""

    function_name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    memory_peak: float = 0.0
    memory_avg: float = 0.0
    cache_hit_rate: float = 0.0
    error_count: int = 0
    last_called: float = 0.0

    def update_stats(self, metric: PerformanceMetrics) -> None:
        """Update profile statistics with new metric."""
        self.total_calls += 1
        self.total_time += metric.execution_time
        self.min_time = min(self.min_time, metric.execution_time)
        self.max_time = max(self.max_time, metric.execution_time)
        self.avg_time = self.total_time / self.total_calls
        self.last_called = metric.timestamp

        if metric.memory_usage:
            self.memory_peak = max(self.memory_peak, metric.memory_usage)
            self.memory_avg = (
                self.memory_avg * (self.total_calls - 1) + metric.memory_usage
            ) / self.total_calls


class AdvancedCache:
    """Advanced cache with LRU eviction, TTL, and statistics."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300) -> None:
        """Initialize advanced cache."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_order = deque()
        self.stats = CacheStats(max_size=max_size)
        self._lock = threading.RLock()

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else {},
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with LRU update."""
        with self._lock:
            if key not in self.cache:
                self.stats.misses += 1
                self.stats.update_hit_rate()
                return None

            value, timestamp = self.cache[key]
            current_time = time.time()

            # Check TTL
            if current_time - timestamp > self.ttl_seconds:
                del self.cache[key]
                self.access_order.remove(key)
                self.stats.misses += 1
                self.stats.update_hit_rate()
                return None

            # Update LRU order
            self.access_order.remove(key)
            self.access_order.append(key)

            self.stats.hits += 1
            self.stats.update_hit_rate()
            return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction."""
        with self._lock:
            current_time = time.time()

            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]
                self.stats.evictions += 1

            # Add/update entry
            self.cache[key] = (value, current_time)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            self.stats.size = len(self.cache)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.stats = CacheStats(max_size=self.max_size)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                size=self.stats.size,
                max_size=self.stats.max_size,
                hit_rate=self.stats.hit_rate,
            )


class PerformanceMonitor:
    """Enhanced monitor and track performance metrics."""

    def __init__(self, max_metrics: int = 10000) -> None:
        """Initialize the performance monitor."""
        self.metrics: List[PerformanceMetrics] = []
        self.profiles: Dict[str, PerformanceProfile] = defaultdict(
            lambda: PerformanceProfile(function_name="")
        )
        self._lock = threading.RLock()
        self.max_metrics = max_metrics
        self.start_time = time.time()

    def record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric with profile update."""
        with self._lock:
            # Add metric
            self.metrics.append(metric)

            # Update profile
            profile = self.profiles[metric.function_name]
            if profile.function_name == "":
                profile.function_name = metric.function_name
            profile.update_stats(metric)

            # Limit metrics size
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]

    def get_average_time(self, function_name: str) -> Optional[float]:
        """Get average execution time for a function."""
        with self._lock:
            profile = self.profiles.get(function_name)
            return profile.avg_time if profile else None

    def get_total_metrics(self) -> int:
        """Get total number of recorded metrics."""
        with self._lock:
            return len(self.metrics)

    def get_profile(self, function_name: str) -> Optional[PerformanceProfile]:
        """Get performance profile for a function."""
        with self._lock:
            return self.profiles.get(function_name)

    def get_all_profiles(self) -> Dict[str, PerformanceProfile]:
        """Get all performance profiles."""
        with self._lock:
            return dict(self.profiles)

    def get_top_slow_functions(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top slowest functions by average time."""
        with self._lock:
            sorted_profiles = sorted(
                self.profiles.items(), key=lambda x: x[1].avg_time, reverse=True
            )
            return [
                (name, profile.avg_time) for name, profile in sorted_profiles[:limit]
            ]

    def get_memory_hogs(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get functions with highest memory usage."""
        with self._lock:
            sorted_profiles = sorted(
                self.profiles.items(), key=lambda x: x[1].memory_peak, reverse=True
            )
            return [
                (name, profile.memory_peak) for name, profile in sorted_profiles[:limit]
            ]

    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        with self._lock:
            self.metrics.clear()
            self.profiles.clear()

    def get_runtime_stats(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        with self._lock:
            current_time = time.time()
            uptime = current_time - self.start_time

            return {
                "uptime_seconds": uptime,
                "total_metrics": len(self.metrics),
                "unique_functions": len(self.profiles),
                "metrics_per_second": len(self.metrics) / uptime if uptime > 0 else 0,
                "memory_usage_mb": self._get_memory_usage(),
                "thread_count": threading.active_count(),
            }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


# Global instances
_performance_monitor = PerformanceMonitor()
_advanced_cache = AdvancedCache()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor


def get_advanced_cache() -> AdvancedCache:
    """Get the global advanced cache instance."""
    return _advanced_cache


@contextmanager
def performance_context(name: str, monitor: Optional[PerformanceMonitor] = None):
    """Context manager for performance monitoring."""
    monitor = monitor or _performance_monitor
    start_time = time.time()
    start_memory = _get_memory_usage()

    try:
        yield
    finally:
        end_time = time.time()
        end_memory = _get_memory_usage()

        metric = PerformanceMetrics(
            function_name=name,
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            timestamp=end_time,
        )
        monitor.record_metric(metric)


def _get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def time_function(func_or_monitor: Any = None) -> Callable[..., Any]:
    """Enhanced decorator to time function execution with advanced metrics."""

    def decorator(
        func: Callable[..., Any], monitor_instance: Optional[PerformanceMonitor] = None
    ) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            start_memory = _get_memory_usage()
            start_threads = threading.active_count()

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Record error in metric
                end_time = time.time()
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=end_time - start_time,
                    memory_usage=_get_memory_usage() - start_memory,
                    thread_count=threading.active_count() - start_threads,
                    timestamp=end_time,
                    metadata={"error": str(e), "error_type": type(e).__name__},
                )
                monitor = monitor_instance or _performance_monitor
                monitor.record_metric(metric)
                raise
            finally:
                end_time = time.time()
                end_memory = _get_memory_usage()
                end_threads = threading.active_count()

                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=end_time - start_time,
                    memory_usage=end_memory - start_memory,
                    thread_count=end_threads - start_threads,
                    timestamp=end_time,
                )
                monitor = monitor_instance or _performance_monitor
                monitor.record_metric(metric)

        return wrapper

    if func_or_monitor is None:
        # Called without parameters: @time_function
        return lambda func: decorator(func, None)
    elif isinstance(func_or_monitor, PerformanceMonitor):
        # Called with monitor: @time_function(monitor)
        return lambda func: decorator(func, func_or_monitor)
    elif callable(func_or_monitor):
        # Called with function: @time_function
        return decorator(func_or_monitor, None)
    else:
        # Called with other type
        return lambda func: decorator(func, None)


def timed_function(monitor: Optional[PerformanceMonitor] = None) -> Callable[..., Any]:
    """Alternative decorator name for time_function."""
    if monitor is None:
        return lambda func: time_function(func)
    else:
        return lambda func: time_function(monitor)(func)


class SimpleCache:
    """Legacy simple cache for backward compatibility."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialize cache with TTL in seconds."""
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self.cache[key]
            return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()

    def size(self) -> int:
        """Get cache size."""
        with self._lock:
            return len(self.cache)

    def __getitem__(self, key: str) -> Any:
        """Support dict-like access."""
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dict-like assignment."""
        self.set(key, value)

    def __contains__(self, key: object) -> bool:
        """Support 'in' operator."""
        if isinstance(key, str):
            return self.get(key) is not None
        return False

    def __len__(self) -> int:
        """Support len() function."""
        return self.size()

    def keys(self) -> list[str]:
        """Return cache keys."""
        with self._lock:
            return list(self.cache.keys())

    def values(self) -> list[Any]:
        """Return cache values."""
        with self._lock:
            return [value for value, _ in self.cache.values()]

    def items(self) -> list[tuple[str, Any]]:
        """Return cache items."""
        with self._lock:
            return [(key, value) for key, (value, _) in self.cache.items()]

    def update(self, other: Any = None, **kwargs: Any) -> Any:
        """Update cache with other dict-like object."""
        if other is not None:
            if hasattr(other, "items"):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value


# Global cache instance for backward compatibility
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance for backward compatibility."""
    return _cache


def cached(
    func: Optional[Callable[..., Any]] = None,
    ttl_seconds: int = 300,
    max_size: int = 1000,
    cache_instance: Optional[AdvancedCache] = None,
) -> Callable[..., Any]:
    """Enhanced decorator to cache function results with advanced features."""

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        cache = cache_instance or _advanced_cache

        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            cache_key = cache._generate_key(f.__name__, args, kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return wrapper

    if func is None:
        # Called with parameters: @cached(ttl_seconds=300)
        return decorator
    else:
        # Called without parameters: @cached
        return decorator(func)


def cache_result(max_size: int = 100) -> Callable[..., Any]:
    """Enhanced decorator to cache function results with size limit."""

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        cache_dict: Dict[str, Any] = {}
        access_order = deque()
        _lock = threading.Lock()

        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            with _lock:
                # Try to get from cache
                if cache_key in cache_dict:
                    # Update LRU order
                    access_order.remove(cache_key)
                    access_order.append(cache_key)
                    return cache_dict[cache_key]

                # Execute function and cache result
                result = f(*args, **kwargs)

                # Manage cache size with LRU eviction
                if len(cache_dict) >= max_size:
                    # Remove oldest entry
                    oldest_key = access_order.popleft()
                    del cache_dict[oldest_key]

                cache_dict[cache_key] = result
                access_order.append(cache_key)
                return result

        return wrapper

    return decorator


def parallel_execute(
    func_or_functions: Any,
    tasks: Optional[List[Any]] = None,
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
    raise_exceptions: bool = True,
    use_processes: bool = False,
    monitor: Optional[PerformanceMonitor] = None,
) -> List[Any]:
    """Enhanced parallel execution with process support and monitoring."""
    monitor = monitor or _performance_monitor
    results = []
    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor

    # Handle both function + tasks and list of functions
    if tasks is not None:
        # Called as parallel_execute(func, tasks, max_workers=...)
        functions = [functools.partial(func_or_functions, task) for task in tasks]
    else:
        # Called as parallel_execute([func1, func2, ...], max_workers=...)
        functions = func_or_functions

    with executor_class(max_workers=max_workers) as executor:
        # Submit all functions with their index
        future_to_index = {}
        for i, func in enumerate(functions):
            future = executor.submit(func)
            future_to_index[future] = i

        # Initialize results list with None
        results = [None] * len(functions)

        # Collect results as they complete
        first_exception = None
        completed_count = 0
        start_time = time.time()

        for future in as_completed(future_to_index.keys(), timeout=timeout):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
                completed_count += 1
            except Exception as e:
                # Store the first exception we encounter
                if first_exception is None:
                    first_exception = e
                print(f"Error executing function at index {index}: {e}")
                results[index] = None
                completed_count += 1

        # Record parallel execution metrics
        end_time = time.time()
        metric = PerformanceMetrics(
            function_name="parallel_execute",
            execution_time=end_time - start_time,
            thread_count=max_workers or len(functions),
            timestamp=end_time,
            metadata={
                "total_tasks": len(functions),
                "completed_tasks": completed_count,
                "use_processes": use_processes,
                "timeout": timeout,
            },
        )
        monitor.record_metric(metric)

        # Handle exceptions based on raise_exceptions parameter
        if first_exception is not None and raise_exceptions:
            raise first_exception

    return results


def batch_process(
    items: List[Any],
    processor: Optional[Callable[..., Any]] = None,
    batch_size: int = 10,
    max_workers: Optional[int] = None,
    monitor: Optional[PerformanceMonitor] = None,
) -> List[Any]:
    """Enhanced batch processing with parallel execution and monitoring."""
    monitor = monitor or _performance_monitor
    results = []
    start_time = time.time()

    # Process items in batches
    for i in range(0, len(items), batch_size):
        batch = items[i: i + batch_size]
        batch_start = time.time()

        if processor:
            # Check if processor expects a single item or a batch
            func_name = getattr(processor, "__name__", "")
            if "batch" in func_name.lower():
                # Function name suggests it's a batch processor
                batch_result = processor(batch)
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)
            else:
                # Process items in parallel within batch
                if max_workers and max_workers > 1:
                    batch_functions = [
                        functools.partial(processor, item) for item in batch
                    ]
                    batch_results = parallel_execute(
                        batch_functions,
                        max_workers=min(max_workers, len(batch)),
                        monitor=monitor,
                    )
                    results.extend(batch_results)
                else:
                    # Sequential processing
                    batch_results = [processor(item) for item in batch]
                    results.extend(batch_results)
        else:
            results.extend(batch)

        # Record batch processing metrics
        batch_end = time.time()
        metric = PerformanceMetrics(
            function_name="batch_process",
            execution_time=batch_end - batch_start,
            timestamp=batch_end,
            metadata={
                "batch_size": len(batch),
                "batch_index": i // batch_size,
                "total_items": len(items),
                "max_workers": max_workers,
            },
        )
        monitor.record_metric(metric)

    # Record overall batch processing metrics
    end_time = time.time()
    total_metric = PerformanceMetrics(
        function_name="batch_process_total",
        execution_time=end_time - start_time,
        timestamp=end_time,
        metadata={
            "total_batches": (len(items) + batch_size - 1) // batch_size,
            "total_items": len(items),
            "batch_size": batch_size,
        },
    )
    monitor.record_metric(total_metric)

    return results


def optimize_file_operations(file_operation: Any) -> Any:
    """Enhanced file operations optimization with monitoring."""
    start_time = time.time()

    try:
        if callable(file_operation):
            result = file_operation()

            # Record file operation metrics
            metric = PerformanceMetrics(
                function_name="file_operation",
                execution_time=time.time() - start_time,
                timestamp=time.time(),
                metric_type=MetricType.FILE_OPERATION,
                metadata={"operation_type": "callable"},
            )
            _performance_monitor.record_metric(metric)

            return result
        elif isinstance(file_operation, list):
            # Handle list of file paths
            metric = PerformanceMetrics(
                function_name="file_operation",
                execution_time=time.time() - start_time,
                timestamp=time.time(),
                metric_type=MetricType.FILE_OPERATION,
                metadata={"operation_type": "list", "file_count": len(file_operation)},
            )
            _performance_monitor.record_metric(metric)

            return file_operation
        else:
            # Handle other types
            metric = PerformanceMetrics(
                function_name="file_operation",
                execution_time=time.time() - start_time,
                timestamp=time.time(),
                metric_type=MetricType.FILE_OPERATION,
                metadata={"operation_type": type(file_operation).__name__},
            )
            _performance_monitor.record_metric(metric)

            return file_operation
    except Exception as e:
        # Record error metric
        metric = PerformanceMetrics(
            function_name="file_operation",
            execution_time=time.time() - start_time,
            timestamp=time.time(),
            metric_type=MetricType.FILE_OPERATION,
            metadata={"error": str(e), "error_type": type(e).__name__},
        )
        _performance_monitor.record_metric(metric)
        raise


def memory_efficient_file_reader(file_path: str, chunk_size: int = 8192) -> str:
    """Enhanced memory-efficient file reader with monitoring."""
    start_time = time.time()
    start_memory = _get_memory_usage()
    content = []
    bytes_read = 0

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                content.append(chunk)
                bytes_read += len(chunk.encode("utf-8"))
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""
    finally:
        # Record file reading metrics
        end_time = time.time()
        end_memory = _get_memory_usage()

        metric = PerformanceMetrics(
            function_name="memory_efficient_file_reader",
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            timestamp=end_time,
            metadata={
                "file_path": file_path,
                "chunk_size": chunk_size,
                "bytes_read": bytes_read,
                "chunks_processed": len(content),
            },
        )
        _performance_monitor.record_metric(metric)

    return "".join(content)


def profile_memory_usage(func: Callable[..., Any]) -> Callable[..., Any]:
    """Enhanced decorator to profile memory usage of a function."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            import psutil
            import gc

            process = psutil.Process()

            # Force garbage collection before measurement
            gc.collect()

            # Get memory before execution
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            memory_percent_before = process.memory_percent()

            # Execute function
            result = func(*args, **kwargs)

            # Get memory after execution
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_percent_after = process.memory_percent()
            memory_used = memory_after - memory_before

            # Record metric with detailed memory usage
            metric = PerformanceMetrics(
                function_name=func.__name__,
                execution_time=0.0,  # Will be set by time_function if used together
                memory_usage=memory_used,
                timestamp=time.time(),
                metadata={
                    "memory_before_mb": memory_before,
                    "memory_after_mb": memory_after,
                    "memory_percent_before": memory_percent_before,
                    "memory_percent_after": memory_percent_after,
                    "cpu_percent": process.cpu_percent(),
                },
            )
            _performance_monitor.record_metric(metric)

            return result
        except ImportError:
            # psutil not available, just execute function without recording metrics
            return func(*args, **kwargs)

    return wrapper


def get_performance_summary() -> Dict[str, Any]:
    """Get a comprehensive summary of performance metrics."""
    monitor = get_performance_monitor()
    cache = get_advanced_cache()
    cache_stats = cache.get_stats()
    runtime_stats = monitor.get_runtime_stats()

    summary: Dict[str, Any] = {
        "runtime_stats": runtime_stats,
        "cache_stats": {
            "hits": cache_stats.hits,
            "misses": cache_stats.misses,
            "hit_rate": cache_stats.hit_rate,
            "evictions": cache_stats.evictions,
            "size": cache_stats.size,
            "max_size": cache_stats.max_size,
        },
        "performance_profiles": {},
        "top_slow_functions": monitor.get_top_slow_functions(5),
        "memory_hogs": monitor.get_memory_hogs(5),
        "total_metrics": monitor.get_total_metrics(),
        "functions_tracked": len(monitor.get_all_profiles()),
    }

    # Add detailed profiles for each function
    profiles = monitor.get_all_profiles()
    for func_name, profile in profiles.items():
        summary["performance_profiles"][func_name] = {
            "total_calls": profile.total_calls,
            "total_time": profile.total_time,
            "avg_time": profile.avg_time,
            "min_time": profile.min_time,
            "max_time": profile.max_time,
            "memory_peak": profile.memory_peak,
            "memory_avg": profile.memory_avg,
            "cache_hit_rate": profile.cache_hit_rate,
            "error_count": profile.error_count,
            "last_called": profile.last_called,
        }

    return summary


def clear_performance_data() -> None:
    """Clear all performance monitoring data."""
    _performance_monitor.clear_metrics()
    _advanced_cache.clear()
    _cache.clear()


def reset_global_monitor() -> None:
    """Reset the global performance monitor."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor()


def reset_global_cache() -> None:
    """Reset the global advanced cache."""
    global _advanced_cache
    _advanced_cache = AdvancedCache()


# Enhanced example usage and performance optimization functions
@time_function
@cached(ttl_seconds=600)
@profile_memory_usage
def expensive_operation(data: str) -> str:
    """Example of an expensive operation that benefits from caching and monitoring."""
    # Simulate expensive operation
    time.sleep(0.1)
    return f"processed_{data}"


@time_function
@profile_memory_usage
def process_large_file(file_path: str) -> List[str]:
    """Example of processing a large file with memory monitoring."""
    content = memory_efficient_file_reader(file_path)
    return content.split("\n")


@time_function
def optimize_quality_gates_execution(
    file_paths: List[str], quality_checks: List[Callable[..., Any]]
) -> Dict[str, Any]:
    """Enhanced optimization of quality gates execution on multiple files."""
    # Optimize file paths
    optimized_paths = optimize_file_operations(file_paths)

    # Process files in batches with parallel execution
    batch_size = min(10, len(optimized_paths)) if len(optimized_paths) > 0 else 1
    results = []

    # Create batches manually
    for i in range(0, len(optimized_paths), batch_size):
        batch = optimized_paths[i: i + batch_size]

        # Run quality checks in parallel for each batch
        batch_functions: List[Callable[..., Any]] = []
        for path in batch:
            for check in quality_checks:
                # Use functools.partial to properly capture the arguments
                batch_functions.append(functools.partial(check, path))

        batch_results = parallel_execute(
            batch_functions, max_workers=min(4, len(batch_functions))
        )
        results.extend(batch_results)

    return {
        "processed_files": len(optimized_paths),
        "total_checks": len(quality_checks),
        "results": results,
        "performance_summary": get_performance_summary(),
    }


# Additional functions for test compatibility
def _get_cache() -> SimpleCache:
    """Get the internal cache instance."""
    return _cache


def clear_cache() -> None:
    """Clear the global cache."""
    _cache.clear()


def _get_performance_summary() -> Dict[str, Any]:
    """Get internal performance summary."""
    return get_performance_summary()


def _clear_cache() -> None:
    """Clear the internal cache."""
    _cache.clear()


# Additional classes for test compatibility
# Additional enhanced classes for advanced performance monitoring
class MemoryProfiler:
    """Enhanced memory profiler for tracking memory usage."""

    def __init__(self):
        self.memory_data = []
        self.monitor = PerformanceMonitor()

    def profile(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Profile memory usage of a function with detailed tracking."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import psutil
                import gc

                process = psutil.Process()

                # Force garbage collection
                gc.collect()

                memory_before = process.memory_info().rss / 1024 / 1024
                memory_percent_before = process.memory_percent()

                result = func(*args, **kwargs)

                memory_after = process.memory_info().rss / 1024 / 1024
                memory_percent_after = process.memory_percent()
                memory_delta = memory_after - memory_before

                self.memory_data.append(memory_delta)

                # Record detailed memory metric
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=0.0,
                    memory_usage=memory_delta,
                    timestamp=time.time(),
                    metadata={
                        "memory_before_mb": memory_before,
                        "memory_after_mb": memory_after,
                        "memory_percent_before": memory_percent_before,
                        "memory_percent_after": memory_percent_after,
                        "cpu_percent": process.cpu_percent(),
                    },
                )
                self.monitor.record_metric(metric)

                return result
            except ImportError:
                return func(*args, **kwargs)

        return wrapper

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        if not self.memory_data:
            return {"total_samples": 0, "avg_memory": 0.0, "peak_memory": 0.0}

        return {
            "total_samples": len(self.memory_data),
            "avg_memory": sum(self.memory_data) / len(self.memory_data),
            "peak_memory": max(self.memory_data),
            "min_memory": min(self.memory_data),
            "total_memory": sum(self.memory_data),
        }


def memory_profiler(func_or_monitor: Any = None) -> Callable[..., Any]:
    """Enhanced decorator to profile memory usage."""

    def decorator(
        func: Callable[..., Any], monitor_instance: Optional[PerformanceMonitor] = None
    ) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import psutil
                import gc

                process = psutil.Process()

                # Force garbage collection
                gc.collect()

                memory_before = process.memory_info().rss / 1024 / 1024
                memory_percent_before = process.memory_percent()

                result = func(*args, **kwargs)

                memory_after = process.memory_info().rss / 1024 / 1024
                memory_percent_after = process.memory_percent()
                memory_used = memory_after - memory_before

                # Record metric with detailed memory usage
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=0.0,
                    memory_usage=memory_used,
                    timestamp=time.time(),
                    metadata={
                        "memory_before_mb": memory_before,
                        "memory_after_mb": memory_after,
                        "memory_percent_before": memory_percent_before,
                        "memory_percent_after": memory_percent_after,
                        "cpu_percent": process.cpu_percent(),
                    },
                )
                monitor = monitor_instance or _performance_monitor
                monitor.record_metric(metric)

                return result
            except ImportError:
                # psutil not available, just execute function without recording metrics
                return func(*args, **kwargs)

        return wrapper

    if func_or_monitor is None:
        # Called without parameters: @memory_profiler
        return lambda func: decorator(func, None)
    elif isinstance(func_or_monitor, PerformanceMonitor):
        # Called with monitor: @memory_profiler(monitor)
        return lambda func: decorator(func, func_or_monitor)
    elif callable(func_or_monitor):
        # Called with function: @memory_profiler
        return decorator(func_or_monitor, None)
    else:
        # Called with other type
        return lambda func: decorator(func, None)


class PerformanceProfiler:
    """Enhanced performance profiler for detailed analysis."""

    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.cache = AdvancedCache()

    def profile_function(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Profile a function with comprehensive monitoring."""
        profiled_func = time_function(self.monitor)(func)
        return profiled_func(*args, **kwargs)

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        summary: Dict[str, Any] = {
            "runtime_stats": self.monitor.get_runtime_stats(),
            "cache_stats": self.cache.get_stats(),
            "total_metrics": self.monitor.get_total_metrics(),
            "functions_tracked": len(self.monitor.get_all_profiles()),
            "top_slow_functions": self.monitor.get_top_slow_functions(10),
            "memory_hogs": self.monitor.get_memory_hogs(10),
        }

        # Add detailed profiles for each function
        profiles = self.monitor.get_all_profiles()
        summary["performance_profiles"] = {}
        for func_name, profile in profiles.items():
            summary["performance_profiles"][func_name] = {
                "total_calls": profile.total_calls,
                "total_time": profile.total_time,
                "avg_time": profile.avg_time,
                "min_time": profile.min_time,
                "max_time": profile.max_time,
                "memory_peak": profile.memory_peak,
                "memory_avg": profile.memory_avg,
                "cache_hit_rate": profile.cache_hit_rate,
                "error_count": profile.error_count,
                "last_called": profile.last_called,
            }

        return summary

    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on performance data."""
        recommendations = []
        profiles = self.monitor.get_all_profiles()

        for func_name, profile in profiles.items():
            if profile.avg_time > 1.0:  # Functions taking more than 1 second
                recommendations.append(
                    f"Consider optimizing {func_name} - avg time: {profile.avg_time:.2f}s"
                )

            if profile.memory_peak > 100:  # Functions using more than 100MB
                recommendations.append(
                    f"Consider memory optimization for {func_name} - peak: {profile.memory_peak:.2f}MB"
                )

            if profile.total_calls > 1000:  # Frequently called functions
                recommendations.append(
                    f"Consider caching for {func_name} - called {profile.total_calls} times"
                )

        return recommendations


class AsyncTaskManager:
    """Enhanced async task manager for concurrent operations."""

    def __init__(self, max_workers: Optional[int] = None):
        self.tasks = []
        self.executor = None
        self.max_workers = max_workers
        self.monitor = PerformanceMonitor()
        self.start_time = None

    def __enter__(self):
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            self.executor.shutdown()
            self.executor = None

            # Record task manager metrics
            if self.start_time:
                metric = PerformanceMetrics(
                    function_name="AsyncTaskManager",
                    execution_time=time.time() - self.start_time,
                    timestamp=time.time(),
                    metadata={
                        "total_tasks": len(self.tasks),
                        "max_workers": self.max_workers,
                    },
                )
                self.monitor.record_metric(metric)

    def submit_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Submit a task for execution with monitoring."""
        if not self.executor:
            raise RuntimeError("TaskManager not started")

        future = self.executor.submit(func, *args, **kwargs)
        self.tasks.append(future)
        return future

    def get_completed_tasks(self) -> List[Any]:
        """Get list of completed tasks."""
        completed = []
        for task in self.tasks:
            if task.done():
                completed.append(task)
        return completed

    def get_task_results(self) -> List[Any]:
        """Get results from completed tasks."""
        results = []
        for task in self.tasks:
            if task.done():
                try:
                    results.append(task.result())
                except Exception as e:
                    results.append(None)
        return results


class ResourceManager:
    """Enhanced resource manager for tracking resource usage."""

    def __init__(self):
        self.resources = {}
        self.resource_stats = defaultdict(
            lambda: {"acquired": 0, "released": 0, "active": 0}
        )
        self._lock = threading.RLock()
        self.monitor = PerformanceMonitor()

    def acquire_resource(self, resource_name: str) -> str:
        """Acquire a resource with monitoring."""
        with self._lock:
            self.resources[resource_name] = True
            self.resource_stats[resource_name]["acquired"] += 1
            self.resource_stats[resource_name]["active"] += 1

            # Record resource acquisition metric
            metric = PerformanceMetrics(
                function_name="acquire_resource",
                execution_time=0.0,
                timestamp=time.time(),
                metadata={
                    "resource_name": resource_name,
                    "total_resources": len(self.resources),
                    "action": "acquire",
                },
            )
            self.monitor.record_metric(metric)

        return resource_name

    def release_resource(self, resource_name: str) -> None:
        """Release a resource with monitoring."""
        with self._lock:
            if resource_name in self.resources:
                del self.resources[resource_name]
                self.resource_stats[resource_name]["released"] += 1
                self.resource_stats[resource_name]["active"] -= 1

                # Record resource release metric
                metric = PerformanceMetrics(
                    function_name="release_resource",
                    execution_time=0.0,
                    timestamp=time.time(),
                    metadata={
                        "resource_name": resource_name,
                        "total_resources": len(self.resources),
                        "action": "release",
                    },
                )
                self.monitor.record_metric(metric)

    def get_resource_status(self) -> Dict[str, bool]:
        """Get resource status."""
        with self._lock:
            return self.resources.copy()

    def get_resource_stats(self) -> Dict[str, Dict[str, int]]:
        """Get resource usage statistics."""
        with self._lock:
            return dict(self.resource_stats)

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource summary."""
        with self._lock:
            total_acquired = sum(
                stats["acquired"] for stats in self.resource_stats.values()
            )
            total_released = sum(
                stats["released"] for stats in self.resource_stats.values()
            )
            active_resources = len(self.resources)

            return {
                "active_resources": active_resources,
                "total_acquired": total_acquired,
                "total_released": total_released,
                "resource_stats": dict(self.resource_stats),
                "resource_status": dict(self.resources),
            }


class PerformanceOptimizer:
    """Enhanced performance optimizer for analyzing and optimizing functions."""

    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.cache = AdvancedCache()
        self.optimization_history = []

    def optimize_function(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Optimize a function with comprehensive monitoring."""
        optimized_func = time_function(self.monitor)(func)

        # Record optimization
        self.optimization_history.append(
            {
                "function_name": func.__name__,
                "timestamp": time.time(),
                "optimization_type": "timing_monitoring",
            }
        )

        return optimized_func

    def get_optimization_suggestions(self) -> List[str]:
        """Get comprehensive optimization suggestions."""
        suggestions = []
        profiles = self.monitor.get_all_profiles()

        if self.monitor.get_total_metrics() > 0:
            suggestions.append("Consider caching frequently called functions")
            suggestions.append("Profile memory usage for large operations")
            suggestions.append("Use parallel execution for independent tasks")

            # Analyze specific functions
            for func_name, profile in profiles.items():
                if profile.avg_time > 0.5:  # Functions taking more than 500ms
                    suggestions.append(
                        f"Optimize {func_name} - average time: {profile.avg_time:.2f}s"
                    )

                if profile.memory_peak > 50:  # Functions using more than 50MB
                    suggestions.append(
                        f"Consider memory optimization for {func_name} - peak: {profile.memory_peak:.2f}MB"
                    )

                if profile.total_calls > 100:  # Frequently called functions
                    suggestions.append(
                        f"Add caching to {func_name} - called {profile.total_calls} times"
                    )

        return suggestions

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics comprehensively."""
        total_metrics = self.monitor.get_total_metrics()
        if total_metrics == 0:
            return {
                "total_functions": 0,
                "average_execution_time": 0.0,
                "total_execution_time": 0.0,
                "memory_usage": 0.0,
                "cache_efficiency": 0.0,
            }

        profiles = self.monitor.get_all_profiles()
        total_time = sum(profile.total_time for profile in profiles.values())
        avg_time = total_time / total_metrics if total_metrics > 0 else 0

        # Calculate memory usage
        total_memory = sum(profile.memory_peak for profile in profiles.values())
        avg_memory = total_memory / len(profiles) if profiles else 0

        # Calculate cache efficiency
        cache_stats = self.cache.get_stats()
        cache_efficiency = cache_stats.hit_rate if cache_stats else 0

        return {
            "total_functions": len(profiles),
            "total_calls": sum(profile.total_calls for profile in profiles.values()),
            "average_execution_time": avg_time,
            "total_execution_time": total_time,
            "memory_usage": total_memory,
            "average_memory_per_function": avg_memory,
            "cache_efficiency": cache_efficiency,
            "optimization_history": len(self.optimization_history),
            "runtime_stats": self.monitor.get_runtime_stats(),
        }

    def get_performance_insights(self) -> Dict[str, Any]:
        """Get detailed performance insights and recommendations."""
        analysis = self.analyze_performance()
        suggestions = self.get_optimization_suggestions()

        insights = {
            "analysis": analysis,
            "suggestions": suggestions,
            "top_slow_functions": self.monitor.get_top_slow_functions(5),
            "memory_hogs": self.monitor.get_memory_hogs(5),
            "cache_stats": self.cache.get_stats(),
            "optimization_history": self.optimization_history,
        }

        return insights
