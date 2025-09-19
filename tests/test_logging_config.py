"""Tests for AI Guard logging configuration."""

import logging
import tempfile
import os
from pathlib import Path
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
    """Test AIGuardFormatter."""

    def test_formatter_with_timestamp(self):
        """Test formatter with timestamp."""
        formatter = AIGuardFormatter(include_timestamp=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "test - INFO - Test message" in formatted
        assert "-" in formatted  # Should include timestamp

    def test_formatter_without_timestamp(self):
        """Test formatter without timestamp."""
        formatter = AIGuardFormatter(include_timestamp=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert formatted == "test - INFO - Test message"


class TestAIGuardLogger:
    """Test AIGuardLogger."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger_config = AIGuardLogger("test_logger", "DEBUG")
        logger = logger_config.get_logger()
        
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1  # Console handler

    def test_logger_with_file(self):
        """Test logger with file handler."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            logger_config = AIGuardLogger("test_logger", "INFO", temp_path)
            logger = logger_config.get_logger()
            
            assert len(logger.handlers) == 2  # Console + file handler
            
            logger.info("Test message")
            
            # Check if message was written to file
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        
        finally:
            os.unlink(temp_path)


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        logger = setup_logging()
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ai_guard"
        assert logger.level == logging.INFO

    def test_setup_logging_with_file(self):
        """Test setup_logging with log file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            logger = setup_logging(log_file=temp_path)
            
            logger.info("Test message")
            
            # Check if message was written to file
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        
        finally:
            os.unlink(temp_path)


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


class TestLogContext:
    """Test LogContext context manager."""

    def test_log_context_success(self):
        """Test LogContext with successful operation."""
        logger = get_logger("test")
        
        with patch.object(logger, 'log') as mock_log:
            with LogContext(logger, "test_operation"):
                pass
            
            # Should log start and completion
            assert mock_log.call_count == 2
            mock_log.assert_any_call(logging.INFO, "Starting test_operation")
            mock_log.assert_any_call(logging.INFO, "Completed test_operation in")

    def test_log_context_exception(self):
        """Test LogContext with exception."""
        logger = get_logger("test")
        
        with patch.object(logger, 'log') as mock_log:
            try:
                with LogContext(logger, "test_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Should log start and failure
            assert mock_log.call_count == 2
            mock_log.assert_any_call(logging.INFO, "Starting test_operation")
            mock_log.assert_any_call(logging.ERROR, "Failed test_operation after")


class TestLogFunctionCall:
    """Test log_function_call decorator."""

    def test_log_function_call_success(self):
        """Test log_function_call decorator with successful function."""
        logger = get_logger("test")
        
        @log_function_call
        def test_function():
            return "success"
        
        with patch.object(logger, 'log') as mock_log:
            result = test_function()
            
            assert result == "success"
            # Should log start, completion, and debug
            assert mock_log.call_count >= 2

    def test_log_function_call_exception(self):
        """Test log_function_call decorator with exception."""
        logger = get_logger("test")
        
        @log_function_call
        def test_function():
            raise ValueError("Test error")
        
        with patch.object(logger, 'log') as mock_log:
            with pytest.raises(ValueError):
                test_function()
            
            # Should log start and error
            assert mock_log.call_count >= 2


class TestLogPerformance:
    """Test log_performance decorator."""

    def test_log_performance_success(self):
        """Test log_performance decorator with successful function."""
        logger = get_logger("test")
        
        @log_performance
        def test_function():
            return "success"
        
        with patch.object(logger, 'info') as mock_info:
            result = test_function()
            
            assert result == "success"
            mock_info.assert_called_once()
            assert "took" in mock_info.call_args[0][0]

    def test_log_performance_exception(self):
        """Test log_performance decorator with exception."""
        logger = get_logger("test")
        
        @log_performance
        def test_function():
            raise ValueError("Test error")
        
        with patch.object(logger, 'error') as mock_error:
            with pytest.raises(ValueError):
                test_function()
            
            mock_error.assert_called_once()
            assert "failed after" in mock_error.call_args[0][0]


class TestStructuredLogger:
    """Test StructuredLogger."""

    def test_structured_logger_initialization(self):
        """Test StructuredLogger initialization."""
        logger = get_logger("test")
        structured_logger = StructuredLogger(logger)
        
        assert structured_logger.logger == logger

    def test_log_analysis_start(self):
        """Test log_analysis_start."""
        logger = get_logger("test")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_analysis_start("src/", {"min_coverage": 80})
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Analysis started"
            assert "event" in call_args[1]["extra"]
            assert call_args[1]["extra"]["event"] == "analysis_start"

    def test_log_analysis_complete(self):
        """Test log_analysis_complete."""
        logger = get_logger("test")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_analysis_complete(
                "src/", True, 1.5, {"coverage": 85}
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Analysis completed"
            assert call_args[1]["extra"]["success"] is True
            assert call_args[1]["extra"]["duration"] == 1.5

    def test_log_security_scan(self):
        """Test log_security_scan."""
        logger = get_logger("test")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_security_scan(
                "src/", 5, {"high": 2, "medium": 3}
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Security scan completed"
            assert call_args[1]["extra"]["vulnerabilities"] == 5

    def test_log_performance_metrics(self):
        """Test log_performance_metrics."""
        logger = get_logger("test")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_performance_metrics(
                "src/", {"memory": 100, "cpu": 50}
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Performance metrics collected"
            assert call_args[1]["extra"]["metrics"]["memory"] == 100

    def test_log_test_generation(self):
        """Test log_test_generation."""
        logger = get_logger("test")
        structured_logger = StructuredLogger(logger)
        
        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_test_generation(
                "src/", 10, 15.5
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Test generation completed"
            assert call_args[1]["extra"]["tests_generated"] == 10
            assert call_args[1]["extra"]["coverage_improvement"] == 15.5
