"""Standardized error message formatting across AI-Guard modules."""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(str, Enum):
    """Standard error severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Standard error categories."""

    CONFIGURATION = "configuration"
    EXECUTION = "execution"
    PARSING = "parsing"
    VALIDATION = "validation"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COVERAGE = "coverage"
    TESTING = "testing"
    LINT = "lint"
    TYPE = "type"
    LOGIC = "logic"
    SYNTAX = "syntax"
    STYLE = "style"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error formatting."""

    module: str
    function: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    tool: Optional[str] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    fix_code: Optional[str] = None


class ErrorFormatter:
    """Standardized error message formatter."""

    def __init__(self, include_context: bool = True, include_emoji: bool = True):
        """Initialize the error formatter.

        Args:
            include_context: Whether to include context information
            include_emoji: Whether to include emoji in messages
        """
        self.include_context = include_context
        self.include_emoji = include_emoji

        # Emoji mapping for different severities
        self.emoji_map = {
            ErrorSeverity.DEBUG: "🔍",
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨",
        }

        # Category-specific prefixes
        self.category_prefixes = {
            ErrorCategory.CONFIGURATION: "Config",
            ErrorCategory.EXECUTION: "Execution",
            ErrorCategory.PARSING: "Parsing",
            ErrorCategory.VALIDATION: "Validation",
            ErrorCategory.NETWORK: "Network",
            ErrorCategory.FILE_SYSTEM: "FileSystem",
            ErrorCategory.SECURITY: "Security",
            ErrorCategory.PERFORMANCE: "Performance",
            ErrorCategory.COVERAGE: "Coverage",
            ErrorCategory.TESTING: "Testing",
            ErrorCategory.LINT: "Lint",
            ErrorCategory.TYPE: "Type",
            ErrorCategory.LOGIC: "Logic",
            ErrorCategory.SYNTAX: "Syntax",
            ErrorCategory.STYLE: "Style",
            ErrorCategory.UNKNOWN: "Unknown",
        }

    def format_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.EXECUTION,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format an error message with standardized structure.

        Args:
            message: The main error message
            severity: Error severity level
            category: Error category
            context: Optional context information
            details: Optional additional details

        Returns:
            Formatted error message
        """
        parts = []

        # Add emoji if enabled
        if self.include_emoji:
            emoji = self.emoji_map.get(severity, "")
            if emoji:
                parts.append(emoji)

        # Add category prefix
        category_prefix = self.category_prefixes.get(category, "Error")
        parts.append(f"[{category_prefix}]")

        # Add severity
        parts.append(f"({severity.value.upper()})")

        # Add main message
        parts.append(message)

        # Add context if provided
        if self.include_context and context:
            context_parts = []

            if context.module:
                context_parts.append(f"module={context.module}")

            if context.function:
                context_parts.append(f"function={context.function}")

            if context.file_path:
                context_parts.append(f"file={context.file_path}")

            if context.line_number:
                context_parts.append(f"line={context.line_number}")

            if context.column:
                context_parts.append(f"col={context.column}")

            if context.tool:
                context_parts.append(f"tool={context.tool}")

            if context.rule_id:
                context_parts.append(f"rule={context.rule_id}")

            if context_parts:
                parts.append(f"{{{', '.join(context_parts)}}}")

        # Add details if provided
        if details:
            detail_parts = []
            for key, value in details.items():
                if isinstance(value, (str, int, float, bool)):
                    detail_parts.append(f"{key}={value}")
                else:
                    detail_parts.append(f"{key}={type(value).__name__}")

            if detail_parts:
                parts.append(f"Details: {', '.join(detail_parts)}")

        return " ".join(parts)

    def format_annotation_message(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        context: Optional[ErrorContext] = None,
    ) -> str:
        """Format a message for PR annotations.

        Args:
            message: The main message
            severity: Error severity level
            context: Optional context information

        Returns:
            Formatted annotation message
        """
        parts = [message]

        # Add suggestion if available
        if context and context.suggestion:
            parts.append(f"\n💡 **Suggestion:** {context.suggestion}")

        # Add fix code if available
        if context and context.fix_code:
            parts.append(f"\n🔧 **Fix:**\n```\n{context.fix_code}\n```")

        return "\n".join(parts)

    def format_log_message(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.INFO,
        category: ErrorCategory = ErrorCategory.EXECUTION,
        context: Optional[ErrorContext] = None,
    ) -> str:
        """Format a message for logging.

        Args:
            message: The main message
            severity: Error severity level
            category: Error category
            context: Optional context information

        Returns:
            Formatted log message
        """
        return self.format_error(
            message=message,
            severity=severity,
            category=category,
            context=context,
        )

    def format_gate_result_message(
        self,
        gate_name: str,
        passed: bool,
        details: str,
        context: Optional[ErrorContext] = None,
    ) -> str:
        """Format a gate result message.

        Args:
            gate_name: Name of the gate
            passed: Whether the gate passed
            details: Details about the result
            context: Optional context information

        Returns:
            Formatted gate result message
        """
        status = "PASSED" if passed else "FAILED"
        emoji = "✅" if passed else "❌"

        parts = [f"{emoji} {gate_name}: {status}"]

        if details:
            parts.append(f"- {details}")

        if context and context.tool:
            parts.append(f"(via {context.tool})")

        return " ".join(parts)

    def format_coverage_message(
        self,
        current_coverage: float,
        target_coverage: float,
        file_path: Optional[str] = None,
    ) -> str:
        """Format a coverage message.

        Args:
            current_coverage: Current coverage percentage
            target_coverage: Target coverage percentage
            file_path: Optional file path

        Returns:
            Formatted coverage message
        """
        status = "PASSED" if current_coverage >= target_coverage else "FAILED"
        emoji = "✅" if current_coverage >= target_coverage else "❌"

        message = f"{emoji} Coverage: {current_coverage:.1f}% >= {target_coverage:.1f}% ({status})"

        if file_path:
            message += f" for {file_path}"

        return message

    def format_security_message(
        self,
        issue_count: int,
        severity: str = "medium",
        tool: str = "bandit",
    ) -> str:
        """Format a security message.

        Args:
            issue_count: Number of security issues found
            severity: Severity level of issues
            tool: Security tool used

        Returns:
            Formatted security message
        """
        if issue_count == 0:
            return f"✅ Security: No issues found (via {tool})"

        emoji = "🚨" if severity == "high" else "⚠️"
        return f"{emoji} Security: {issue_count} {severity} issues found (via {tool})"

    def format_performance_message(
        self,
        function_name: str,
        execution_time: float,
        threshold: float = 1.0,
    ) -> str:
        """Format a performance message.

        Args:
            function_name: Name of the function
            execution_time: Execution time in seconds
            threshold: Performance threshold in seconds

        Returns:
            Formatted performance message
        """
        status = "PASSED" if execution_time < threshold else "FAILED"
        emoji = "✅" if execution_time < threshold else "⚠️"

        return (
            f"{emoji} Performance: {function_name} took {execution_time:.3f}s "
            f"(threshold: {threshold}s) - {status}"
        )


# Global error formatter instance
error_formatter = ErrorFormatter()

# Convenience functions for common error formatting


def format_error(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    category: ErrorCategory = ErrorCategory.EXECUTION,
    context: Optional[ErrorContext] = None,
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """Format an error message using the global formatter."""
    return error_formatter.format_error(message, severity, category, context, details)


def format_log_message(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.INFO,
    category: ErrorCategory = ErrorCategory.EXECUTION,
    context: Optional[ErrorContext] = None,
) -> str:
    """Format a log message using the global formatter."""
    return error_formatter.format_log_message(message, severity, category, context)


def format_annotation_message(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.WARNING,
    context: Optional[ErrorContext] = None,
) -> str:
    """Format an annotation message using the global formatter."""
    return error_formatter.format_annotation_message(message, severity, context)


def format_gate_result_message(
    gate_name: str,
    passed: bool,
    details: str,
    context: Optional[ErrorContext] = None,
) -> str:
    """Format a gate result message using the global formatter."""
    return error_formatter.format_gate_result_message(
        gate_name, passed, details, context
    )


def format_coverage_message(
    current_coverage: float,
    target_coverage: float,
    file_path: Optional[str] = None,
) -> str:
    """Format a coverage message using the global formatter."""
    return error_formatter.format_coverage_message(
        current_coverage, target_coverage, file_path
    )


def format_security_message(
    issue_count: int,
    severity: str = "medium",
    tool: str = "bandit",
) -> str:
    """Format a security message using the global formatter."""
    return error_formatter.format_security_message(issue_count, severity, tool)


def format_performance_message(
    function_name: str,
    execution_time: float,
    threshold: float = 1.0,
) -> str:
    """Format a performance message using the global formatter."""
    return error_formatter.format_performance_message(
        function_name, execution_time, threshold
    )


def format_error_message(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
    severity: str = "error",
) -> str:
    """Format an error message with context and suggestion.

    Args:
        message: Main error message
        context: Optional context dictionary
        suggestion: Optional suggestion
        severity: Error severity level

    Returns:
        Formatted error message
    """
    parts = [message]

    if context:
        context_parts = []
        for key, value in context.items():
            context_parts.append(f"{key}={value}")
        if context_parts:
            parts.append(f"Context: {', '.join(context_parts)}")

    if suggestion:
        parts.append(f"Suggestion: {suggestion}")

    if severity:
        parts.insert(0, f"[{severity.upper()}]")

    return " | ".join(parts)


def format_exception(exception: Exception, include_traceback: bool = False) -> str:
    """Format an exception with optional traceback.

    Args:
        exception: Exception to format
        include_traceback: Whether to include traceback

    Returns:
        Formatted exception message
    """
    parts = [f"{type(exception).__name__}: {str(exception)}"]

    if include_traceback:
        import traceback

        tb = traceback.format_exc()
        parts.append(f"Traceback:\n{tb}")

    return "\n".join(parts)


def format_traceback(traceback_str: str) -> str:
    """Format a traceback string.

    Args:
        traceback_str: Raw traceback string

    Returns:
        Formatted traceback
    """
    return f"Traceback:\n{traceback_str}"


class ExceptionFormatter:
    """Formatter for exceptions."""

    def __init__(self, include_traceback: bool = True, max_traceback_lines: int = 10):
        """Initialize the exception formatter.

        Args:
            include_traceback: Whether to include traceback
            max_traceback_lines: Maximum traceback lines
        """
        self.include_traceback = include_traceback
        self.max_traceback_lines = max_traceback_lines

    def format_exception(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format an exception.

        Args:
            exception: Exception to format
            context: Optional context

        Returns:
            Formatted exception message
        """
        parts = [f"{type(exception).__name__}: {str(exception)}"]

        if context:
            context_parts = []
            for key, value in context.items():
                context_parts.append(f"{key}={value}")
            if context_parts:
                parts.append(f"Context: {', '.join(context_parts)}")

        if self.include_traceback:
            import traceback

            tb_lines = traceback.format_exc().split("\n")
            if len(tb_lines) > self.max_traceback_lines:
                tb_lines = tb_lines[: self.max_traceback_lines] + ["..."]
            parts.append("Traceback:\n" + "\n".join(tb_lines))

        return "\n".join(parts)


class TracebackFormatter:
    """Formatter for tracebacks."""

    def __init__(self, max_lines: int = 20, include_locals: bool = False):
        """Initialize the traceback formatter.

        Args:
            max_lines: Maximum lines to include
            include_locals: Whether to include local variables
        """
        self.max_lines = max_lines
        self.include_locals = include_locals

    def format_traceback(self, traceback_str: str) -> str:
        """Format a traceback string.

        Args:
            traceback_str: Raw traceback string

        Returns:
            Formatted traceback
        """
        lines = traceback_str.split("\n")
        if len(lines) > self.max_lines:
            lines = lines[: self.max_lines] + ["..."]

        return "\n".join(lines)
