"""Tests for performance.py module."""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.ai_guard.performance import (
    time_function,
    cached,
    get_performance_summary,
)


class TestTimeFunction:
    """Test time_function decorator."""

    def test_time_function_basic(self):
        """Test basic time_function usage."""
        @time_function
        def test_func():
            time.sleep(0.01)  # Small delay to ensure measurable time
            return "test"
        
        result = test_func()
        assert result == "test"
        # The function should have been timed (we can't easily test the timing itself)

    def test_time_function_with_args(self):
        """Test time_function with arguments."""
        @time_function
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        assert result == 3

    def test_time_function_with_kwargs(self):
        """Test time_function with keyword arguments."""
        @time_function
        def test_func(x=0, y=0):
            return x + y
        
        result = test_func(x=1, y=2)
        assert result == 3

    def test_time_function_exception(self):
        """Test time_function with exception."""
        @time_function
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func()


class TestCached:
    """Test cached decorator."""

    def test_cached_basic(self):
        """Test basic cached functionality."""
        call_count = 0
        
        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

    def test_cached_different_args(self):
        """Test cached with different arguments."""
        call_count = 0
        
        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Different arguments should cause new function calls
        result1 = test_func(5)
        result2 = test_func(10)
        
        assert result1 == 10
        assert result2 == 20
        assert call_count == 2

    def test_cached_with_kwargs(self):
        """Test cached with keyword arguments."""
        call_count = 0
        
        @cached
        def test_func(x, y=0):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # Same positional and keyword args should be cached
        result1 = test_func(5, y=2)
        result2 = test_func(5, y=2)
        
        assert result1 == 7
        assert result2 == 7
        assert call_count == 1

    def test_cached_exception(self):
        """Test cached with exception."""
        call_count = 0
        
        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            if x < 0:
                raise ValueError("Negative number")
            return x * 2
        
        # Exception should not be cached
        with pytest.raises(ValueError):
            test_func(-1)
        
        with pytest.raises(ValueError):
            test_func(-1)
        
        assert call_count == 2  # Should call function twice

    def test_cached_clear_cache(self):
        """Test clearing cache."""
        call_count = 0
        
        @cached
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = test_func(5)
        assert call_count == 1
        
        # Second call (cached)
        result2 = test_func(5)
        assert call_count == 1
        
        # Clear cache
        test_func.cache_clear()
        
        # Third call (should execute function again)
        result3 = test_func(5)
        assert call_count == 2


class TestGetPerformanceSummary:
    """Test get_performance_summary function."""

    def test_get_performance_summary_empty(self):
        """Test performance summary with no data."""
        summary = get_performance_summary()
        
        assert isinstance(summary, dict)
        # Check for actual keys that exist in the implementation
        assert "average_times" in summary

    def test_get_performance_summary_with_data(self):
        """Test performance summary with some data."""
        # Mock some performance data
        with patch('src.ai_guard.performance._performance_data', {
            'test_func1': [0.1, 0.2, 0.15],
            'test_func2': [0.05, 0.08]
        }):
            summary = get_performance_summary()
            
            assert isinstance(summary, dict)
            assert "average_times" in summary

    def test_get_performance_summary_single_function(self):
        """Test performance summary with single function."""
        with patch('src.ai_guard.performance._performance_data', {
            'test_func': [0.1, 0.2, 0.15, 0.12]
        }):
            summary = get_performance_summary()
            
            assert isinstance(summary, dict)
            assert "average_times" in summary
