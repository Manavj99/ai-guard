"""
Comprehensive test coverage for src/ai_guard/performance.py
"""
import unittest
from unittest.mock import patch, MagicMock
import time
import functools
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable
import threading
import queue

# Import the performance module
from src.ai_guard.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    time_function,
    cached
)


class TestPerformanceMetrics(unittest.TestCase):
    """Test PerformanceMetrics dataclass."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics with all fields."""
        metrics = PerformanceMetrics(
            function_name="test_func",
            execution_time=1.5,
            memory_usage=1024,
            cache_hits=5,
            cache_misses=2
        )
        
        self.assertEqual(metrics.function_name, "test_func")
        self.assertEqual(metrics.execution_time, 1.5)
        self.assertEqual(metrics.memory_usage, 1024)
        self.assertEqual(metrics.cache_hits, 5)
        self.assertEqual(metrics.cache_misses, 2)
    
    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metrics = PerformanceMetrics(function_name="test_func")
        
        self.assertEqual(metrics.function_name, "test_func")
        self.assertEqual(metrics.execution_time, 0.0)
        self.assertEqual(metrics.memory_usage, 0)
        self.assertEqual(metrics.cache_hits, 0)
        self.assertEqual(metrics.cache_misses, 0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        self.assertEqual(self.monitor.metrics, {})
        self.assertEqual(self.monitor.start_times, {})
    
    def test_start_timing(self):
        """Test starting timing for a function."""
        self.monitor.start_timing("test_func")
        
        self.assertIn("test_func", self.monitor.start_times)
        self.assertIsInstance(self.monitor.start_times["test_func"], float)
    
    def test_end_timing(self):
        """Test ending timing and recording metrics."""
        # Start timing
        self.monitor.start_timing("test_func")
        time.sleep(0.01)  # Small delay to ensure measurable time
        
        # End timing
        self.monitor.end_timing("test_func", memory_usage=512)
        
        # Check metrics were recorded
        self.assertIn("test_func", self.monitor.metrics)
        metrics = self.monitor.metrics["test_func"]
        self.assertEqual(metrics.function_name, "test_func")
        self.assertGreater(metrics.execution_time, 0)
        self.assertEqual(metrics.memory_usage, 512)
    
    def test_end_timing_without_start(self):
        """Test ending timing without starting first."""
        # Should not raise an error, just return None
        result = self.monitor.end_timing("nonexistent_func")
        self.assertIsNone(result)
    
    def test_get_metrics(self):
        """Test getting metrics for a function."""
        # Record some metrics
        self.monitor.start_timing("test_func")
        time.sleep(0.01)
        self.monitor.end_timing("test_func", memory_usage=256)
        
        # Get metrics
        metrics = self.monitor.get_metrics("test_func")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.function_name, "test_func")
        self.assertGreater(metrics.execution_time, 0)
        self.assertEqual(metrics.memory_usage, 256)
    
    def test_get_metrics_nonexistent(self):
        """Test getting metrics for nonexistent function."""
        metrics = self.monitor.get_metrics("nonexistent_func")
        self.assertIsNone(metrics)
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        # Record metrics for multiple functions
        self.monitor.start_timing("func1")
        time.sleep(0.01)
        self.monitor.end_timing("func1", memory_usage=100)
        
        self.monitor.start_timing("func2")
        time.sleep(0.01)
        self.monitor.end_timing("func2", memory_usage=200)
        
        # Get all metrics
        all_metrics = self.monitor.get_all_metrics()
        self.assertEqual(len(all_metrics), 2)
        self.assertIn("func1", all_metrics)
        self.assertIn("func2", all_metrics)
    
    def test_clear_metrics(self):
        """Test clearing all metrics."""
        # Record some metrics
        self.monitor.start_timing("test_func")
        time.sleep(0.01)
        self.monitor.end_timing("test_func", memory_usage=128)
        
        # Clear metrics
        self.monitor.clear_metrics()
        
        # Check metrics are cleared
        self.assertEqual(self.monitor.metrics, {})
        self.assertEqual(self.monitor.start_times, {})
    
    def test_get_summary(self):
        """Test getting performance summary."""
        # Record metrics for multiple functions
        self.monitor.start_timing("func1")
        time.sleep(0.01)
        self.monitor.end_timing("func1", memory_usage=100)
        
        self.monitor.start_timing("func2")
        time.sleep(0.01)
        self.monitor.end_timing("func2", memory_usage=200)
        
        # Get summary
        summary = self.monitor.get_summary()
        
        self.assertIn("total_functions", summary)
        self.assertIn("total_execution_time", summary)
        self.assertIn("total_memory_usage", summary)
        self.assertIn("average_execution_time", summary)
        self.assertIn("average_memory_usage", summary)
        
        self.assertEqual(summary["total_functions"], 2)
        self.assertGreater(summary["total_execution_time"], 0)
        self.assertEqual(summary["total_memory_usage"], 300)
        self.assertGreater(summary["average_execution_time"], 0)
        self.assertEqual(summary["average_memory_usage"], 150)


class TestTimeFunctionDecorator(unittest.TestCase):
    """Test time_function decorator."""
    
    def test_time_function_decorator(self):
        """Test time_function decorator functionality."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        def test_function(x, y):
            time.sleep(0.01)
            return x + y
        
        # Call the decorated function
        result = test_function(2, 3)
        
        # Check result
        self.assertEqual(result, 5)
        
        # Check metrics were recorded
        metrics = monitor.get_metrics("test_function")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.function_name, "test_function")
        self.assertGreater(metrics.execution_time, 0)
    
    def test_time_function_with_memory_tracking(self):
        """Test time_function with memory tracking."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor, track_memory=True)
        def memory_function():
            # Create some data to use memory
            data = [i for i in range(1000)]
            return len(data)
        
        result = memory_function()
        self.assertEqual(result, 1000)
        
        # Check metrics
        metrics = monitor.get_metrics("memory_function")
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.memory_usage, 0)
    
    def test_time_function_without_monitor(self):
        """Test time_function without monitor (should still work)."""
        @time_function()
        def simple_function():
            return "test"
        
        result = simple_function()
        self.assertEqual(result, "test")
    
    def test_time_function_with_exception(self):
        """Test time_function when function raises exception."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        def failing_function():
            raise ValueError("Test error")
        
        # Should still record timing even if function fails
        with self.assertRaises(ValueError):
            failing_function()
        
        # Check that timing was still recorded
        metrics = monitor.get_metrics("failing_function")
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.execution_time, 0)


class TestCachedDecorator(unittest.TestCase):
    """Test cached decorator."""
    
    def test_cached_decorator_basic(self):
        """Test basic caching functionality."""
        call_count = 0
        
        @cached(maxsize=2)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        # Second call with same argument (should use cache)
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # Should not increment
        
        # Call with different argument
        result3 = expensive_function(3)
        self.assertEqual(result3, 6)
        self.assertEqual(call_count, 2)
    
    def test_cached_decorator_with_ttl(self):
        """Test cached decorator with TTL."""
        call_count = 0
        
        @cached(maxsize=10, ttl=0.1)  # 100ms TTL
        def ttl_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3
        
        # First call
        result1 = ttl_function(4)
        self.assertEqual(result1, 12)
        self.assertEqual(call_count, 1)
        
        # Immediate second call (should use cache)
        result2 = ttl_function(4)
        self.assertEqual(result2, 12)
        self.assertEqual(call_count, 1)
        
        # Wait for TTL to expire
        time.sleep(0.15)
        
        # Call after TTL expired (should not use cache)
        result3 = ttl_function(4)
        self.assertEqual(result3, 12)
        self.assertEqual(call_count, 2)
    
    def test_cached_decorator_maxsize(self):
        """Test cached decorator with maxsize limit."""
        call_count = 0
        
        @cached(maxsize=2)
        def limited_function(x):
            nonlocal call_count
            call_count += 1
            return x * 4
        
        # Fill cache
        limited_function(1)  # call_count = 1
        limited_function(2)  # call_count = 2
        
        # Call first function again (should use cache)
        limited_function(1)
        self.assertEqual(call_count, 2)
        
        # Add third function (should evict first)
        limited_function(3)  # call_count = 3
        
        # Call first function again (should not use cache, was evicted)
        limited_function(1)
        self.assertEqual(call_count, 4)
    
    def test_cached_decorator_with_key_function(self):
        """Test cached decorator with custom key function."""
        call_count = 0
        
        def custom_key(*args, **kwargs):
            # Only use first argument as key
            return args[0] if args else None
        
        @cached(maxsize=10, key=custom_key)
        def key_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call
        result1 = key_function(5, 10)
        self.assertEqual(result1, 15)
        self.assertEqual(call_count, 1)
        
        # Second call with same first arg, different second arg
        result2 = key_function(5, 20)
        self.assertEqual(result2, 15)  # Should return cached result
        self.assertEqual(call_count, 1)  # Should not increment
    
    def test_cached_decorator_with_exception(self):
        """Test cached decorator when function raises exception."""
        call_count = 0
        
        @cached(maxsize=5)
        def error_function(x):
            nonlocal call_count
            call_count += 1
            if x == 0:
                raise ValueError("Division by zero")
            return 10 / x
        
        # Call with valid argument
        result1 = error_function(2)
        self.assertEqual(result1, 5.0)
        self.assertEqual(call_count, 1)
        
        # Call with same argument (should use cache)
        result2 = error_function(2)
        self.assertEqual(result2, 5.0)
        self.assertEqual(call_count, 1)
        
        # Call with error argument
        with self.assertRaises(ValueError):
            error_function(0)
        self.assertEqual(call_count, 2)
        
        # Call with error argument again (should not use cache for exceptions)
        with self.assertRaises(ValueError):
            error_function(0)
        self.assertEqual(call_count, 3)
    
    def test_cached_decorator_clear_cache(self):
        """Test clearing cache."""
        call_count = 0
        
        @cached(maxsize=5)
        def clearable_function(x):
            nonlocal call_count
            call_count += 1
            return x * 5
        
        # First call
        result1 = clearable_function(3)
        self.assertEqual(result1, 15)
        self.assertEqual(call_count, 1)
        
        # Clear cache
        clearable_function.cache_clear()
        
        # Call again (should not use cache)
        result2 = clearable_function(3)
        self.assertEqual(result2, 15)
        self.assertEqual(call_count, 2)
    
    def test_cached_decorator_cache_info(self):
        """Test cache info functionality."""
        @cached(maxsize=3)
        def info_function(x):
            return x * 6
        
        # Get initial cache info
        info = info_function.cache_info()
        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 0)
        self.assertEqual(info.currsize, 0)
        self.assertEqual(info.maxsize, 3)
        
        # Make some calls
        info_function(1)  # miss
        info_function(1)  # hit
        info_function(2)  # miss
        
        # Get updated cache info
        info = info_function.cache_info()
        self.assertEqual(info.hits, 1)
        self.assertEqual(info.misses, 2)
        self.assertEqual(info.currsize, 2)
        self.assertEqual(info.maxsize, 3)


class TestPerformanceIntegration(unittest.TestCase):
    """Integration tests for performance monitoring."""
    
    def test_monitor_with_multiple_decorators(self):
        """Test using monitor with multiple decorated functions."""
        monitor = PerformanceMonitor()
        
        @time_function(monitor)
        @cached(maxsize=5)
        def complex_function(x):
            time.sleep(0.01)
            return x * x
        
        # First call
        result1 = complex_function(4)
        self.assertEqual(result1, 16)
        
        # Second call (should use cache)
        result2 = complex_function(4)
        self.assertEqual(result2, 16)
        
        # Check metrics
        metrics = monitor.get_metrics("complex_function")
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.execution_time, 0)
    
    def test_thread_safety(self):
        """Test thread safety of performance monitoring."""
        monitor = PerformanceMonitor()
        results = []
        
        @time_function(monitor)
        def thread_function(thread_id):
            time.sleep(0.01)
            return thread_id * 10
        
        def worker(thread_id):
            result = thread_function(thread_id)
            results.append(result)
        
        # Create and start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(results), 5)
        self.assertEqual(set(results), {0, 10, 20, 30, 40})
        
        # Check metrics were recorded for all threads
        all_metrics = monitor.get_all_metrics()
        self.assertIn("thread_function", all_metrics)


if __name__ == '__main__':
    unittest.main()