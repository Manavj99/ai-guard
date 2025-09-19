"""Tests for utility modules."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.ai_guard.utils.error_formatter import (
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    format_error,
    format_coverage_message,
)


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_error_context_init(self):
        """Test ErrorContext initialization."""
        context = ErrorContext(
            module="test_module",
            function="test_func",
            file_path="test.py",
            line_number=10,
            column=5
        )
        assert context.module == "test_module"
        assert context.function == "test_func"
        assert context.file_path == "test.py"
        assert context.line_number == 10
        assert context.column == 5

    def test_error_context_minimal(self):
        """Test ErrorContext with minimal parameters."""
        context = ErrorContext(module="test_module", function="test_func")
        assert context.module == "test_module"
        assert context.function == "test_func"
        assert context.file_path is None
        assert context.line_number is None
        assert context.column is None


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.DEBUG == "debug"
        assert ErrorSeverity.INFO == "info"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.CRITICAL == "critical"


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_error_category_values(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.SECURITY == "security"
        assert ErrorCategory.PERFORMANCE == "performance"
        assert ErrorCategory.COVERAGE == "coverage"
        assert ErrorCategory.STYLE == "style"
        assert ErrorCategory.CONFIGURATION == "configuration"


class TestFormatError:
    """Test format_error function."""

    def test_format_error_basic(self):
        """Test basic error formatting."""
        context = ErrorContext(module="test_module", function="test_func", file_path="test.py", line_number=10)
        formatted = format_error(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SECURITY,
            context=context
        )
        
        assert "Test error" in formatted
        assert "test.py" in formatted
        assert "line 10" in formatted
        assert "ERROR" in formatted
        assert "SECURITY" in formatted

    def test_format_error_no_context(self):
        """Test error formatting without context."""
        formatted = format_error(
            message="Test error",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STYLE
        )
        
        assert "Test error" in formatted
        assert "WARNING" in formatted
        assert "STYLE" in formatted

    def test_format_error_minimal(self):
        """Test error formatting with minimal parameters."""
        formatted = format_error("Simple error")
        
        assert "Simple error" in formatted


class TestFormatCoverageMessage:
    """Test format_coverage_message function."""

    def test_format_coverage_message_passing(self):
        """Test formatting passing coverage message."""
        message = format_coverage_message(
            current_coverage=85.5,
            passed=True
        )
        
        assert "85.5%" in message
        assert "passed" in message.lower()

    def test_format_coverage_message_failing(self):
        """Test formatting failing coverage message."""
        message = format_coverage_message(
            current_coverage=75.0,
            passed=False
        )
        
        assert "75.0%" in message
        assert "failed" in message.lower()

    def test_format_coverage_message_exact_threshold(self):
        """Test formatting coverage message at exact threshold."""
        message = format_coverage_message(
            current_coverage=80.0,
            passed=True
        )
        
        assert "80.0%" in message
        assert "passed" in message.lower()
