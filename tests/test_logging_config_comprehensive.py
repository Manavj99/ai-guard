"""Comprehensive tests for logging_config module."""

import logging
import tempfile
import os
import time
from unittest.mock import patch, MagicMock
import pytest
from src.ai_guard.logging_config import (
    AIGuardFormatter,
    AIGuardLogger,
    setup_logging,
    get_logger,
    LogContext,
    log_function_call,
    log_performance,
    StructuredLogger
)


class TestAIGuardFormatter:
    """Test AIGuardFormatter class."""

    def test_formatter_with_timestamp(self):
        """Test formatter with timestamp."""
        formatter = AIGuardFormatter(include_timestamp=True)
        assert formatter.include_timestamp is True
        assert "%(asctime)s" in formatter._fmt

    def test_formatter_without_timestamp(self):
        """Test formatter without timestamp."""
        formatter = AIGuardFormatter(include_timestamp=False)
        assert formatter.include_timestamp is False
        assert "%(asctime)s" not in formatter._fmt

    def test_formatter_format_record(self):
        """Test formatter formatting a log record."""
        formatter = AIGuardFormatter(include_timestamp=True)
        
        # Create a mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "test_logger" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted

    def test_formatter_format_record_without_timestamp(self):
        """Test formatter formatting without timestamp."""
        formatter = AIGuardFormatter(include_timestamp=False)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "test_logger" in formatted
        assert "ERROR" in formatted
        assert "Error message" in formatted
        # Should not contain timestamp
        assert ":" not in formatted or formatted.count(":") <= 2


class TestAIGuardLogger:
    """Test AIGuardLogger class."""

    def test_logger_initialization_default(self):
        """Test logger initialization with default parameters."""
        logger_config = AIGuardLogger()
        logger = logger_config.get_logger()
        
        assert logger.name == "ai_guard"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1  # Only console handler

    def test_logger_initialization_custom_name(self):
        """Test logger initialization with custom name."""
        logger_config = AIGuardLogger(name="custom_logger")
        logger = logger_config.get_logger()
        
        assert logger.name == "custom_logger"

    def test_logger_initialization_custom_level(self):
        """Test logger initialization with custom level."""
        logger_config = AIGuardLogger(level="DEBUG")
        logger = logger_config.get_logger()
        
        assert logger.level == logging.DEBUG

    def test_logger_initialization_with_file(self):
        """Test logger initialization with log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            logger_config = AIGuardLogger(log_file=temp_path)
            logger = logger_config.get_logger()
            
            assert len(logger.handlers) == 2  # Console and file handlers
            
            # Test logging to file
            logger.info("Test message")
            
            # Close handlers to release file
            for handler in logger.handlers:
                handler.close()
            
            # Check if message was written to file
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # File might still be in use

    def test_logger_initialization_without_timestamp(self):
        """Test logger initialization without timestamp."""
        logger_config = AIGuardLogger(include_timestamp=False)
        logger = logger_config.get_logger()
        
        # Check that formatter doesn't include timestamp
        handler = logger.handlers[0]
        formatter = handler.formatter
        assert not formatter.include_timestamp

    def test_logger_handlers_cleared(self):
        """Test that existing handlers are cleared."""
        logger = logging.getLogger("test_clear")
        logger.addHandler(logging.StreamHandler())
        
        # Create new logger config
        logger_config = AIGuardLogger(name="test_clear")
        logger = logger_config.get_logger()
        
        # Should have only one handler (console)
        assert len(logger.handlers) == 1

    def test_logger_different_levels(self):
        """Test logger with different levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in levels:
            logger_config = AIGuardLogger(level=level)
            logger = logger_config.get_logger()
            assert logger.level == getattr(logging, level)


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        logger = setup_logging()
        
        assert logger.name == "ai_guard"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom level."""
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self):
        """Test setup_logging with log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            logger = setup_logging(log_file=temp_path)
            assert len(logger.handlers) == 2
            
            # Test logging
            logger.info("Test message")
            
            # Close handlers to release file
            for handler in logger.handlers:
                handler.close()
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # File might still be in use

    def test_setup_logging_without_timestamp(self):
        """Test setup_logging without timestamp."""
        logger = setup_logging(include_timestamp=False)
        
        handler = logger.handlers[0]
        formatter = handler.formatter
        assert not formatter.include_timestamp


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_default(self):
        """Test get_logger with default name."""
        logger = get_logger()
        assert logger.name == "ai_guard"

    def test_get_logger_custom_name(self):
        """Test get_logger with custom name."""
        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"

    def test_get_logger_same_instance(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        assert logger1 is logger2


class TestLogContext:
    """Test LogContext class."""

    def test_log_context_initialization(self):
        """Test LogContext initialization."""
        logger = get_logger("test_context")
        context = LogContext(logger, "test_operation")
        
        assert context.logger == logger
        assert context.operation == "test_operation"
        assert context.level == logging.INFO

    def test_log_context_custom_level(self):
        """Test LogContext with custom level."""
        logger = get_logger("test_context")
        context = LogContext(logger, "test_operation", level=logging.DEBUG)
        
        assert context.level == logging.DEBUG

    def test_log_context_success(self):
        """Test LogContext with successful operation."""
        logger = get_logger("test_context")
        
        with patch.object(logger, 'log') as mock_log:
            with LogContext(logger, "test_operation"):
                time.sleep(0.01)  # Small delay to test timing
            
            # Should log start and completion
            assert mock_log.call_count == 2
            assert "Starting test_operation" in str(mock_log.call_args_list[0])
            assert "Completed test_operation" in str(mock_log.call_args_list[1])

    def test_log_context_exception(self):
        """Test LogContext with exception."""
        logger = get_logger("test_context")
        
        with patch.object(logger, 'log') as mock_log, \
             patch.object(logger, 'error') as mock_error:
            
            try:
                with LogContext(logger, "test_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Should log start and error
            assert mock_log.call_count == 1
            assert mock_error.call_count == 1
            assert "Starting test_operation" in str(mock_log.call_args_list[0])
            assert "Failed test_operation" in str(mock_error.call_args_list[0])

    def test_log_context_timing(self):
        """Test LogContext timing functionality."""
        logger = get_logger("test_context")
        
        with patch.object(logger, 'log') as mock_log:
            with LogContext(logger, "test_operation"):
                time.sleep(0.1)
            
            # Check that timing is included in completion message
            completion_call = mock_log.call_args_list[1]
            assert "in" in str(completion_call)
            assert "s" in str(completion_call)


class TestLogFunctionCall:
    """Test log_function_call decorator."""

    def test_log_function_call_success(self):
        """Test log_function_call decorator with successful function."""
        @log_function_call
        def test_function(x, y):
            return x + y
        
        # Test that function works correctly
        result = test_function(2, 3)
        assert result == 5

    def test_log_function_call_exception(self):
        """Test log_function_call decorator with exception."""
        @log_function_call
        def test_function():
            raise ValueError("Test error")
        
        # Test that exception is properly raised
        with pytest.raises(ValueError):
            test_function()

    def test_log_function_call_with_args(self):
        """Test log_function_call decorator with function arguments."""
        @log_function_call
        def test_function(a, b, c=None):
            return a + b + (c or 0)
        
        # Test that function works with arguments
        result = test_function(1, 2, c=3)
        assert result == 6


class TestLogPerformance:
    """Test log_performance decorator."""

    def test_log_performance_success(self):
        """Test log_performance decorator with successful function."""
        @log_performance
        def test_function(x):
            time.sleep(0.01)
            return x * 2
        
        # Test that function works correctly
        result = test_function(5)
        assert result == 10

    def test_log_performance_exception(self):
        """Test log_performance decorator with exception."""
        @log_performance
        def test_function():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        # Test that exception is properly raised
        with pytest.raises(ValueError):
            test_function()

    def test_log_performance_timing(self):
        """Test log_performance decorator timing."""
        @log_performance
        def test_function():
            time.sleep(0.1)
            return "done"
        
        # Test that function works correctly
        result = test_function()
        assert result == "done"


class TestStructuredLogger:
    """Test StructuredLogger class."""

    def test_structured_logger_initialization(self):
        """Test StructuredLogger initialization."""
        logger = get_logger("test_structured")
        structured_logger = StructuredLogger(logger)
        
        assert structured_logger.logger == logger

    def test_log_analysis_start(self):
        """Test log_analysis_start method."""
        logger = get_logger("test_structured")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            config = {"min_coverage": 80, "timeout": 30}
            structured_logger.log_analysis_start("/path/to/project", config)
            
            assert mock_info.call_count == 1
            call_args = mock_info.call_args_list[0]
            assert "Analysis started" in str(call_args)
            assert "analysis_start" in str(call_args)

    def test_log_analysis_complete(self):
        """Test log_analysis_complete method."""
        logger = get_logger("test_structured")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            metrics = {"coverage": 85.5, "files_analyzed": 10}
            structured_logger.log_analysis_complete("/path/to/project", True, 5.2, metrics)
            
            assert mock_info.call_count == 1
            call_args = mock_info.call_args_list[0]
            assert "Analysis completed" in str(call_args)
            assert "analysis_complete" in str(call_args)

    def test_log_security_scan(self):
        """Test log_security_scan method."""
        logger = get_logger("test_structured")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            severity_counts = {"HIGH": 2, "MEDIUM": 5, "LOW": 1}
            structured_logger.log_security_scan("/path/to/project", 8, severity_counts)
            
            assert mock_info.call_count == 1
            call_args = mock_info.call_args_list[0]
            assert "Security scan completed" in str(call_args)
            assert "security_scan" in str(call_args)

    def test_log_performance_metrics(self):
        """Test log_performance_metrics method."""
        logger = get_logger("test_structured")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            metrics = {"execution_time": 2.5, "memory_usage": 100.0}
            structured_logger.log_performance_metrics("/path/to/project", metrics)
            
            assert mock_info.call_count == 1
            call_args = mock_info.call_args_list[0]
            assert "Performance metrics collected" in str(call_args)
            assert "performance_metrics" in str(call_args)

    def test_log_test_generation(self):
        """Test log_test_generation method."""
        logger = get_logger("test_structured")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_test_generation("/path/to/project", 15, 12.5)
            
            assert mock_info.call_count == 1
            call_args = mock_info.call_args_list[0]
            assert "Test generation completed" in str(call_args)
            assert "test_generation" in str(call_args)


class TestIntegration:
    """Test integration scenarios."""

    def test_full_logging_setup(self):
        """Test complete logging setup."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Setup logging
            logger = setup_logging(level="DEBUG", log_file=temp_path)
            
            # Test different log levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Close handlers to release file
            for handler in logger.handlers:
                handler.close()
            
            # Check file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Debug message" in content
                assert "Info message" in content
                assert "Warning message" in content
                assert "Error message" in content
        
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # File might still be in use

    def test_decorator_combination(self):
        """Test combining decorators."""
        @log_function_call
        @log_performance
        def combined_function(x):
            time.sleep(0.01)
            return x * 2
        
        # Test that combined decorators work correctly
        result = combined_function(5)
        assert result == 10

    def test_structured_logging_integration(self):
        """Test structured logging integration."""
        logger = setup_logging(level="INFO")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            # Simulate analysis workflow
            structured_logger.log_analysis_start("/project", {"coverage": 80})
            structured_logger.log_security_scan("/project", 0, {})
            structured_logger.log_performance_metrics("/project", {"time": 1.0})
            structured_logger.log_analysis_complete("/project", True, 2.0, {"coverage": 85})
            
            assert mock_info.call_count == 4

    def test_logger_isolation(self):
        """Test that different loggers are isolated."""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")
        
        assert logger1 is not logger2
        assert logger1.name == "logger1"
        assert logger2.name == "logger2"

    def test_handler_cleanup(self):
        """Test that handlers are properly cleaned up."""
        logger_name = "test_cleanup"
        
        # Create first logger
        logger_config1 = AIGuardLogger(name=logger_name)
        logger1 = logger_config1.get_logger()
        initial_handlers = len(logger1.handlers)
        
        # Create second logger with same name
        logger_config2 = AIGuardLogger(name=logger_name)
        logger2 = logger_config2.get_logger()
        
        # Should have same number of handlers (cleared and recreated)
        assert len(logger2.handlers) == initial_handlers
