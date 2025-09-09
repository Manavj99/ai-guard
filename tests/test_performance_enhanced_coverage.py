"""Enhanced tests for performance module to significantly improve coverage."""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock, call

from src.ai_guard.performance import (
    time_function,
    cached,
    get_performance_summary,
    get_cache,
    clear_performance_data,
    get_performance_monitor
)


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_success(self):
        """Test time_function with successful execution."""
        @time_function
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_time_function_with_args(self):
        """Test time_function with function arguments."""
        @time_function
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        assert result == 5

    def test_time_function_with_kwargs(self):
        """Test time_function with keyword arguments."""
        @time_function
        def test_func(x=0, y=0):
            return x + y
        
        result = test_func(x=2, y=3)
        assert result == 5

    def test_time_function_with_exception(self):
        """Test time_function with exception."""
        @time_function
        def test_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            test_func()

    def test_time_function_records_timing(self):
        """Test time_function records timing information."""
        @time_function
        def test_func():
            time.sleep(0.01)  # Small delay to ensure timing is recorded
            return "success"
        
        # Clear cache first
        clear_performance_data()
        
        test_func()
        
        # Check that timing was recorded
        summary = get_performance_summary()
        assert summary['total_metrics'] > 0
        assert 'test_func' in summary['average_times']

    def test_time_function_multiple_calls(self):
        """Test time_function with multiple calls."""
        @time_function
        def test_func():
            return "success"
        
        # Clear cache first
        clear_performance_data()
        
        # Make multiple calls
        for _ in range(3):
            test_func()
        
        # Check that timing was recorded for multiple calls
        summary = get_performance_summary()
        assert summary['total_metrics'] >= 3


class TestCached:
    """Test cached decorator."""

    def test_cached_success(self):
        """Test cached with successful execution."""
        @cached
        def test_func(x):
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == 10
        assert result2 == 10

    def test_cached_different_args(self):
        """Test cached with different arguments."""
        @cached
        def test_func(x):
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(10)
        
        assert result1 == 10
        assert result2 == 20

    def test_cached_with_kwargs(self):
        """Test cached with keyword arguments."""
        @cached
        def test_func(x=0, y=0):
            return x + y
        
        result1 = test_func(x=2, y=3)
        result2 = test_func(x=2, y=3)
        
        assert result1 == 5
        assert result2 == 5

    def test_cached_with_exception(self):
        """Test cached with exception."""
        @cached
        def test_func(x):
            if x < 0:
                raise ValueError("negative value")
            return x * 2
        
        # First call should raise exception
        with pytest.raises(ValueError):
            test_func(-1)
        
        # Second call should also raise exception (not cached)
        with pytest.raises(ValueError):
            test_func(-1)

    def test_cached_cache_hit(self):
        """Test cached returns cached result on second call."""
        call_count = 0
        
        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Clear cache first
        clear_performance_data()
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert call_count == 1  # Function should only be called once
        assert result1 == result2 == 10

    def test_cached_cache_miss(self):
        """Test cached calls function on cache miss."""
        call_count = 0
        
        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Clear cache first
        clear_performance_data()
        
        result1 = test_func(5)
        result2 = test_func(10)
        
        assert call_count == 2  # Function should be called twice
        assert result1 == 10
        assert result2 == 20


class TestCacheManagement:
    """Test cache management functions."""

    def test_get_cache(self):
        """Test get_cache function."""
        cache = get_cache()
        assert isinstance(cache, dict)

    def test_clear_performance_data(self):
        """Test clear_performance_data function."""
        # Add some data to cache
        cache = get_cache()
        cache['test_key'] = 'test_value'
        
        # Clear performance data
        clear_performance_data()
        
        # Check that cache is empty
        assert len(cache) == 0

    def test_get_performance_summary(self):
        """Test get_performance_summary function."""
        summary = get_performance_summary()
        
        assert isinstance(summary, dict)
        assert 'total_metrics' in summary
        assert 'cache_size' in summary
        assert 'functions_tracked' in summary
        assert 'average_times' in summary
        
        assert isinstance(summary['total_metrics'], int)
        assert isinstance(summary['cache_size'], int)
        assert isinstance(summary['functions_tracked'], int)
        assert isinstance(summary['average_times'], dict)

    def test_performance_summary_after_timing(self):
        """Test performance summary after recording timing data."""
        # Clear cache first
        clear_performance_data()
        
        @time_function
        def test_func():
            time.sleep(0.01)
            return "success"
        
        test_func()
        
        summary = get_performance_summary()
        assert summary['total_metrics'] > 0
        assert summary['functions_tracked'] > 0
        assert 'test_func' in summary['average_times']

    def test_performance_summary_after_caching(self):
        """Test performance summary after using cached functions."""
        # Clear cache first
        clear_performance_data()
        
        @cached
        def test_func(x):
            return x * 2
        
        test_func(5)
        test_func(10)
        
        summary = get_performance_summary()
        assert summary['cache_size'] > 0


class TestInternalFunctions:
    """Test internal functions."""

    def test_get_cache_internal(self):
        """Test _get_cache function."""
        cache = _get_cache()
        assert isinstance(cache, dict)

    def test_clear_cache_internal(self):
        """Test _clear_cache function."""
        # Add some data to cache
        cache = _get_cache()
        cache['test_key'] = 'test_value'
        
        # Clear cache
        _clear_cache()
        
        # Check that cache is empty
        assert len(cache) == 0

    def test_get_performance_summary_internal(self):
        """Test _get_performance_summary function."""
        summary = _get_performance_summary()
        
        assert isinstance(summary, dict)
        assert 'total_metrics' in summary
        assert 'cache_size' in summary
        assert 'functions_tracked' in summary
        assert 'average_times' in summary


class TestConcurrency:
    """Test concurrent access to cache and timing."""

    def test_concurrent_timing(self):
        """Test concurrent timing recording."""
        @time_function
        def test_func(delay):
            time.sleep(delay)
            return "success"
        
        # Clear cache first
        clear_cache()
        
        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=test_func, args=(0.01,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that timing was recorded
        summary = get_performance_summary()
        assert summary['total_metrics'] >= 3

    def test_concurrent_caching(self):
        """Test concurrent cache access."""
        @cached
        def test_func(x):
            return x * 2
        
        # Clear cache first
        clear_cache()
        
        # Run multiple threads with same argument
        results = []
        threads = []
        
        def worker():
            results.append(test_func(5))
        
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be the same
        assert all(result == 10 for result in results)
        
        # Check that cache was used
        summary = get_performance_summary()
        assert summary['cache_size'] > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_time_function_with_none_return(self):
        """Test time_function with function that returns None."""
        @time_function
        def test_func():
            return None
        
        result = test_func()
        assert result is None

    def test_cached_with_none_return(self):
        """Test cached with function that returns None."""
        @cached
        def test_func(x):
            return None
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 is None
        assert result2 is None

    def test_cached_with_mutable_arguments(self):
        """Test cached with mutable arguments."""
        @cached
        def test_func(lst):
            return lst.copy()
        
        # Clear cache first
        clear_cache()
        
        lst1 = [1, 2, 3]
        lst2 = [1, 2, 3]
        
        result1 = test_func(lst1)
        result2 = test_func(lst2)
        
        # Results should be equal but different objects
        assert result1 == result2
        assert result1 is not result2

    def test_performance_summary_empty_cache(self):
        """Test performance summary with empty cache."""
        # Clear cache first
        clear_performance_data()
        
        summary = get_performance_summary()
        assert summary['total_metrics'] == 0
        assert summary['cache_size'] == 0
        assert summary['functions_tracked'] == 0
        assert summary['average_times'] == {}
