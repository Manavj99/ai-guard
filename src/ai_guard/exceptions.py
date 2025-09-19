"""Custom exceptions for AI Guard."""

from typing import Optional, Dict, Any


class AIGuardError(Exception):
    """Base exception class for all AI Guard errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize AI Guard error.

        Args:
            message: Error message
            error_code: Optional error code
            details: Optional additional details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(AIGuardError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize configuration error.

        Args:
            message: Error message
            config_path: Path to configuration file
            details: Optional additional details
        """
        super().__init__(message, "CONFIG_ERROR", details)
        self.config_path = config_path


class AnalysisError(AIGuardError):
    """Raised when analysis fails due to code issues."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize analysis error.

        Args:
            message: Error message
            file_path: Path to file with issues
            line_number: Line number with issues
            details: Optional additional details
        """
        super().__init__(message, "ANALYSIS_ERROR", details)
        self.file_path = file_path
        self.line_number = line_number


class SecurityError(AIGuardError):
    """Raised when security analysis encounters critical issues."""

    def __init__(
        self,
        message: str,
        vulnerability_type: Optional[str] = None,
        severity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize security error.

        Args:
            message: Error message
            vulnerability_type: Type of vulnerability
            severity: Severity level
            details: Optional additional details
        """
        super().__init__(message, "SECURITY_ERROR", details)
        self.vulnerability_type = vulnerability_type
        self.severity = severity


class PerformanceError(AIGuardError):
    """Raised when performance analysis fails."""

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        threshold: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize performance error.

        Args:
            message: Error message
            metric_name: Name of performance metric
            threshold: Performance threshold
            details: Optional additional details
        """
        super().__init__(message, "PERFORMANCE_ERROR", details)
        self.metric_name = metric_name
        self.threshold = threshold


class TestGenerationError(AIGuardError):
    """Raised when test generation fails."""

    def __init__(
        self,
        message: str,
        target_file: Optional[str] = None,
        generation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize test generation error.

        Args:
            message: Error message
            target_file: File being tested
            generation_type: Type of test generation
            details: Optional additional details
        """
        super().__init__(message, "TEST_GENERATION_ERROR", details)
        self.target_file = target_file
        self.generation_type = generation_type


class ReportGenerationError(AIGuardError):
    """Raised when report generation fails."""

    def __init__(
        self,
        message: str,
        report_format: Optional[str] = None,
        output_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize report generation error.

        Args:
            message: Error message
            report_format: Format of report
            output_path: Output path for report
            details: Optional additional details
        """
        super().__init__(message, "REPORT_GENERATION_ERROR", details)
        self.report_format = report_format
        self.output_path = output_path


class DependencyError(AIGuardError):
    """Raised when dependency analysis fails."""

    def __init__(
        self,
        message: str,
        package_name: Optional[str] = None,
        version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize dependency error.

        Args:
            message: Error message
            package_name: Name of package
            version: Package version
            details: Optional additional details
        """
        super().__init__(message, "DEPENDENCY_ERROR", details)
        self.package_name = package_name
        self.version = version


class ToolExecutionError(AIGuardError):
    """Raised when external tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize tool execution error.

        Args:
            message: Error message
            tool_name: Name of tool
            command: Command that failed
            exit_code: Exit code of command
            details: Optional additional details
        """
        super().__init__(message, "TOOL_EXECUTION_ERROR", details)
        self.tool_name = tool_name
        self.command = command
        self.exit_code = exit_code


class ValidationError(AIGuardError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field_name: Name of field that failed validation
            value: Value that failed validation
            details: Optional additional details
        """
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field_name = field_name
        self.value = value


class TimeoutError(AIGuardError):
    """Raised when operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[int] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Timeout in seconds
            operation: Operation that timed out
            details: Optional additional details
        """
        super().__init__(message, "TIMEOUT_ERROR", details)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class FileSystemError(AIGuardError):
    """Raised when file system operations fail."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize file system error.

        Args:
            message: Error message
            file_path: Path to file
            operation: File system operation
            details: Optional additional details
        """
        super().__init__(message, "FILESYSTEM_ERROR", details)
        self.file_path = file_path
        self.operation = operation


class NetworkError(AIGuardError):
    """Raised when network operations fail."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize network error.

        Args:
            message: Error message
            url: URL that failed
            status_code: HTTP status code
            details: Optional additional details
        """
        super().__init__(message, "NETWORK_ERROR", details)
        self.url = url
        self.status_code = status_code
