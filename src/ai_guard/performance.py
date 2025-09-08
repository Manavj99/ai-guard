"""Performance optimization utilities for AI-Guard."""

import time
import functools
import threading
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """Performance metrics for tracking execution times."""

    function_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self) -> None:
        """Initialize the performance monitor."""
        self.metrics: List[PerformanceMetrics] = []
        self._lock = threading.Lock()

    def record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)

    def get_average_time(self, function_name: str) -> Optional[float]:
        """Get average execution time for a function."""
        with self._lock:
            times = [
                m.execution_time
                for m in self.metrics
                if m.function_name == function_name
            ]
            return sum(times) / len(times) if times else None

    def get_total_metrics(self) -> int:
        """Get total number of recorded metrics."""
        with self._lock:
            return len(self.metrics)

    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        with self._lock:
            self.metrics.clear()


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor


def time_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to time function execution."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            metric = PerformanceMetrics(
                function_name=func.__name__, execution_time=execution_time
            )
            _performance_monitor.record_metric(metric)

    return wrapper


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 300):
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


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _cache


def cached(
    ttl_seconds: int = 300,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache function results."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


def parallel_execute(
    functions: List[Callable[..., Any]],
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
) -> List[Any]:
    """Execute multiple functions in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all functions
        future_to_func = {executor.submit(func): func for func in functions}

        # Collect results as they complete
        for future in as_completed(future_to_func, timeout=timeout):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Log error but continue with other functions
                print(f"Error executing function: {e}")
                results.append(None)

    return results


def batch_process(
    items: List[Any], batch_size: int = 10, processor: Optional[Callable[..., Any]] = None
) -> List[Any]:
    """Process items in batches for better memory management."""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i: i + batch_size]

        if processor:
            batch_results = [processor(item) for item in batch]
        else:
            batch_results = batch

        results.extend(batch_results)

    return results


def optimize_file_operations(file_paths: List[str]) -> List[str]:
    """Optimize file operations by grouping and sorting."""
    # Group by directory to minimize directory changes
    dir_groups: Dict[str, List[str]] = {}

    for path in file_paths:
        dir_path = str(Path(path).parent)
        if dir_path not in dir_groups:
            dir_groups[dir_path] = []
        dir_groups[dir_path].append(path)

    # Sort within each directory and flatten
    optimized_paths = []
    for dir_path in sorted(dir_groups.keys()):
        optimized_paths.extend(sorted(dir_groups[dir_path]))

    return optimized_paths


def memory_efficient_file_reader(file_path: str, chunk_size: int = 8192) -> str:
    """Read file in chunks to manage memory usage."""
    content = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                content.append(chunk)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

    return "".join(content)


def profile_memory_usage(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to profile memory usage of a function."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            import psutil

            process = psutil.Process()

            # Get memory before execution
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # Execute function
            result = func(*args, **kwargs)

            # Get memory after execution
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before

            # Record metric with memory usage
            metric = PerformanceMetrics(
                function_name=func.__name__,
                execution_time=0.0,  # Will be set by time_function if used together
                memory_usage=memory_used,
            )
            _performance_monitor.record_metric(metric)

            return result
        except ImportError:
            # psutil not available, just execute function
            return func(*args, **kwargs)

    return wrapper


def get_performance_summary() -> Dict[str, Any]:
    """Get a summary of performance metrics."""
    monitor = get_performance_monitor()
    cache = get_cache()

    summary: Dict[str, Any] = {
        "total_metrics": monitor.get_total_metrics(),
        "cache_size": cache.size(),
        "functions_tracked": len(set(m.function_name for m in monitor.metrics)),
    }

    # Add average times for each function
    function_times: Dict[str, List[float]] = {}
    for metric in monitor.metrics:
        if metric.function_name not in function_times:
            function_times[metric.function_name] = []
        function_times[metric.function_name].append(metric.execution_time)

    summary["average_times"] = {
        func: sum(times) / len(times) for func, times in function_times.items()
    }

    return summary


def clear_performance_data() -> None:
    """Clear all performance monitoring data."""
    _performance_monitor.clear_metrics()
    _cache.clear()


# Example usage and performance optimization functions
@time_function
@cached(ttl_seconds=600)
def expensive_operation(data: str) -> str:
    """Example of an expensive operation that benefits from caching."""
    # Simulate expensive operation
    time.sleep(0.1)
    return f"processed_{data}"


@time_function
@profile_memory_usage
def process_large_file(file_path: str) -> List[str]:
    """Example of processing a large file with memory monitoring."""
    content = memory_efficient_file_reader(file_path)
    return content.split("\n")


def optimize_quality_gates_execution(
    file_paths: List[str], quality_checks: List[Callable[..., Any]]
) -> Dict[str, Any]:
    """Optimize the execution of quality gates on multiple files."""
    # Optimize file paths
    optimized_paths = optimize_file_operations(file_paths)

    # Process files in batches (manually to avoid string iteration)
    batch_size = min(10, len(optimized_paths))
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

        batch_results = parallel_execute(batch_functions)
        results.extend(batch_results)

    return {
        "processed_files": len(optimized_paths),
        "total_checks": len(quality_checks),
        "results": results,
        "performance_summary": get_performance_summary(),
    }
