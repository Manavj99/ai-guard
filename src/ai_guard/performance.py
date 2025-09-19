"""Performance optimization utilities for AI-Guard."""

import time
import functools
import threading
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


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


def time_function(func_or_monitor: Any = None) -> Callable[..., Any]:
    """Decorator to time function execution."""

    def decorator(
        func: Callable[..., Any], monitor_instance: Optional[PerformanceMonitor] = None
    ) -> Callable[..., Any]:
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
                if monitor_instance:
                    monitor_instance.record_metric(metric)
                else:
                    _performance_monitor.record_metric(metric)

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
    """Simple in-memory cache with TTL support."""

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


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _cache


def cached(
    func: Optional[Callable[..., Any]] = None,
    ttl_seconds: int = 300,
) -> Callable[..., Any]:
    """Decorator to cache function results."""

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            if cache_key in _cache:
                return _cache[cache_key]

            # Execute function and cache result
            result = f(*args, **kwargs)
            _cache[cache_key] = result
            return result

        return wrapper

    if func is None:
        # Called with parameters: @cached(ttl_seconds=300)
        return decorator
    else:
        # Called without parameters: @cached
        return decorator(func)


def cache_result(max_size: int = 100) -> Callable[..., Any]:
    """Decorator to cache function results with size limit."""

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        cache_dict: Dict[str, Any] = {}

        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            if cache_key in cache_dict:
                return cache_dict[cache_key]

            # Execute function and cache result
            result = f(*args, **kwargs)

            # Manage cache size
            if len(cache_dict) >= max_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(cache_dict))
                del cache_dict[oldest_key]

            cache_dict[cache_key] = result
            return result

        return wrapper

    return decorator


def parallel_execute(
    func_or_functions: Any,
    tasks: Optional[List[Any]] = None,
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
    raise_exceptions: bool = True,
) -> List[Any]:
    """Execute multiple functions in parallel."""
    results = []

    # Handle both function + tasks and list of functions
    if tasks is not None:
        # Called as parallel_execute(func, tasks, max_workers=...)
        functions = [functools.partial(func_or_functions, task) for task in tasks]
        # Store original order for results
    else:
        # Called as parallel_execute([func1, func2, ...], max_workers=...)
        functions = func_or_functions

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all functions with their index
        future_to_index = {}
        for i, func in enumerate(functions):
            future = executor.submit(func)
            future_to_index[future] = i

        # Initialize results list with None
        results = [None] * len(functions)

        # Collect results as they complete
        first_exception = None
        for future in as_completed(future_to_index.keys(), timeout=timeout):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
            except Exception as e:
                # Store the first exception we encounter
                if first_exception is None:
                    first_exception = e
                print(f"Error executing function: {e}")
                results[index] = None

        # Handle exceptions based on raise_exceptions parameter
        if first_exception is not None and raise_exceptions:
            raise first_exception

    return results


def batch_process(
    items: List[Any],
    processor: Optional[Callable[..., Any]] = None,
    batch_size: int = 10,
) -> List[Any]:
    """Process items in batches for better memory management."""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]

        if processor:
            # Check if processor expects a single item or a batch
            # Use function name to determine if it's a batch processor
            func_name = getattr(processor, "__name__", "")
            if "batch" in func_name.lower():
                # Function name suggests it's a batch processor
                batch_result = processor(batch)
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)
            else:
                # Assume it's an item processor
                batch_results = [processor(item) for item in batch]
                results.extend(batch_results)
        else:
            results.extend(batch)

    return results


def optimize_file_operations(file_operation: Any) -> Any:
    """Optimize file operations by executing them efficiently."""
    if callable(file_operation):
        try:
            return file_operation()
        except Exception as e:
            raise e
    elif isinstance(file_operation, list):
        # Handle list of file paths - return the list as is
        return file_operation
    else:
        # Handle other types
        return file_operation


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


def reset_global_monitor() -> None:
    """Reset the global performance monitor."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor()


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
        batch = optimized_paths[i : i + batch_size]

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
class MemoryProfiler:
    """Memory profiler for tracking memory usage."""

    def __init__(self):
        self.memory_data = []

    def profile(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Profile memory usage of a function."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import psutil

                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024
                result = func(*args, **kwargs)
                memory_after = process.memory_info().rss / 1024 / 1024
                self.memory_data.append(memory_after - memory_before)
                return result
            except ImportError:
                return func(*args, **kwargs)

        return wrapper


def memory_profiler(func_or_monitor: Any = None) -> Callable[..., Any]:
    """Decorator to profile memory usage."""

    def decorator(
        func: Callable[..., Any], monitor_instance: Optional[PerformanceMonitor] = None
    ) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import psutil

                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024
                result = func(*args, **kwargs)
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_used = memory_after - memory_before

                # Record metric with memory usage
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=0.0,
                    memory_usage=memory_used,
                )
                if monitor_instance:
                    monitor_instance.record_metric(metric)
                else:
                    _performance_monitor.record_metric(metric)

                return result
            except ImportError:
                # psutil not available, just execute function
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
    """Performance profiler for detailed analysis."""

    def __init__(self):
        self.monitor = PerformanceMonitor()

    def profile_function(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Profile a function."""
        profiled_func = time_function(self.monitor)(func)
        return profiled_func(*args, **kwargs)

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report."""
        summary: Dict[str, Any] = {
            "total_metrics": self.monitor.get_total_metrics(),
            "functions_tracked": len(
                set(m.function_name for m in self.monitor.metrics)
            ),
        }

        # Add average times for each function
        function_times: Dict[str, List[float]] = {}
        for metric in self.monitor.metrics:
            if metric.function_name not in function_times:
                function_times[metric.function_name] = []
            function_times[metric.function_name].append(metric.execution_time)

        summary["average_times"] = {
            func: sum(times) / len(times) for func, times in function_times.items()
        }

        return summary


class AsyncTaskManager:
    """Async task manager for concurrent operations."""

    def __init__(self, max_workers: Optional[int] = None):
        self.tasks = []
        self.executor = None
        self.max_workers = max_workers

    def __enter__(self):
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            self.executor.shutdown()

    def submit_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Submit a task for execution."""
        if not self.executor:
            raise RuntimeError("TaskManager not started")
        future = self.executor.submit(func, *args, **kwargs)
        self.tasks.append(future)
        return future


class ResourceManager:
    """Resource manager for tracking resource usage."""

    def __init__(self):
        self.resources = {}
        self._lock = threading.Lock()

    def acquire_resource(self, resource_name: str) -> str:
        """Acquire a resource."""
        with self._lock:
            self.resources[resource_name] = True
        return resource_name

    def release_resource(self, resource_name: str) -> None:
        """Release a resource."""
        with self._lock:
            if resource_name in self.resources:
                del self.resources[resource_name]

    def get_resource_status(self) -> Dict[str, bool]:
        """Get resource status."""
        with self._lock:
            return self.resources.copy()


class PerformanceOptimizer:
    """Performance optimizer for analyzing and optimizing functions."""

    def __init__(self):
        self.monitor = PerformanceMonitor()

    def optimize_function(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Optimize a function with monitoring."""
        return time_function(self.monitor)(func)

    def get_optimization_suggestions(self) -> List[str]:
        """Get optimization suggestions."""
        suggestions = []
        if self.monitor.get_total_metrics() > 0:
            suggestions.append("Consider caching frequently called functions")
            suggestions.append("Profile memory usage for large operations")
            suggestions.append("Use parallel execution for independent tasks")
        return suggestions

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics."""
        total_metrics = self.monitor.get_total_metrics()
        if total_metrics == 0:
            return {
                "total_functions": 0,
                "average_execution_time": 0.0,
                "total_execution_time": 0.0,
            }

        total_time = sum(m.execution_time for m in self.monitor.metrics)
        avg_time = total_time / total_metrics

        return {
            "total_functions": len(set(m.function_name for m in self.monitor.metrics)),
            "average_execution_time": avg_time,
            "total_execution_time": total_time,
        }
