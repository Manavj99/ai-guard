"""Logging configuration for AI Guard."""

import logging
import sys
from typing import Optional, Dict, Any, Callable


class AIGuardFormatter(logging.Formatter):
    """Custom formatter for AI Guard logs."""

    def __init__(self, include_timestamp: bool = True):
        """Initialize formatter.

        Args:
            include_timestamp: Whether to include timestamp in logs
        """
        if include_timestamp:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            fmt = "%(name)s - %(levelname)s - %(message)s"

        super().__init__(fmt)
        self.include_timestamp = include_timestamp


class AIGuardLogger:
    """AI Guard logger with configuration."""

    def __init__(
        self,
        name: str = "ai_guard",
        level: str = "INFO",
        log_file: Optional[str] = None,
        include_timestamp: bool = True,
    ):
        """Initialize logger.

        Args:
            name: Logger name
            level: Log level
            log_file: Optional log file path
            include_timestamp: Whether to include timestamp
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(AIGuardFormatter(include_timestamp))
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(AIGuardFormatter(include_timestamp))
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger


def setup_logging(
    level: str = "INFO", log_file: Optional[str] = None, include_timestamp: bool = True
) -> logging.Logger:
    """Set up logging for AI Guard.

    Args:
        level: Log level
        log_file: Optional log file path
        include_timestamp: Whether to include timestamp

    Returns:
        Configured logger
    """
    logger_config = AIGuardLogger(
        level=level, log_file=log_file, include_timestamp=include_timestamp
    )
    return logger_config.get_logger()


def get_logger(name: str = "ai_guard") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for logging operations."""

    def __init__(
        self, logger: logging.Logger, operation: str, level: int = logging.INFO
    ):
        """Initialize log context.

        Args:
            logger: Logger instance
            operation: Operation name
            level: Log level
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None

    def __enter__(self) -> "LogContext":
        """Enter context."""
        import time

        self.start_time = time.time()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context."""
        import time

        if self.start_time is not None:
            duration = time.time() - self.start_time

        if exc_type is None:
            self.logger.log(
                self.level, f"Completed {self.operation} in {duration:.2f}s"
            )
        else:
            self.logger.error(
                f"Failed {self.operation} after {duration:.2f}s: {exc_val}"
            )


def log_function_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to log function calls."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger()
        func_name = func.__name__

        with LogContext(logger, f"function {func_name}"):
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func_name} failed: {e}")
                raise

    return wrapper


def log_performance(func):
    """Decorator to log function performance."""

    def wrapper(*args, **kwargs):
        import time

        logger = get_logger()
        func_name = func.__name__

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func_name} took {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func_name} failed after {duration:.3f}s: {e}")
            raise

    return wrapper


class StructuredLogger:
    """Logger for structured logging."""

    def __init__(self, logger: logging.Logger):
        """Initialize structured logger.

        Args:
            logger: Base logger instance
        """
        self.logger = logger

    def log_analysis_start(self, path: str, config: Dict[str, Any]):
        """Log analysis start."""
        self.logger.info(
            "Analysis started",
            extra={"event": "analysis_start", "path": path, "config": config},
        )

    def log_analysis_complete(
        self, path: str, success: bool, duration: float, metrics: Dict[str, Any]
    ):
        """Log analysis completion."""
        self.logger.info(
            "Analysis completed",
            extra={
                "event": "analysis_complete",
                "path": path,
                "success": success,
                "duration": duration,
                "metrics": metrics,
            },
        )

    def log_security_scan(
        self, path: str, vulnerabilities: int, severity_counts: Dict[str, int]
    ):
        """Log security scan results."""
        self.logger.info(
            "Security scan completed",
            extra={
                "event": "security_scan",
                "path": path,
                "vulnerabilities": vulnerabilities,
                "severity_counts": severity_counts,
            },
        )

    def log_performance_metrics(self, path: str, metrics: Dict[str, float]):
        """Log performance metrics."""
        self.logger.info(
            "Performance metrics collected",
            extra={"event": "performance_metrics", "path": path, "metrics": metrics},
        )

    def log_test_generation(
        self, path: str, tests_generated: int, coverage_improvement: float
    ):
        """Log test generation results."""
        self.logger.info(
            "Test generation completed",
            extra={
                "event": "test_generation",
                "path": path,
                "tests_generated": tests_generated,
                "coverage_improvement": coverage_improvement,
            },
        )
