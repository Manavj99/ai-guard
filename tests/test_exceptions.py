"""Tests for AI Guard exceptions."""

import pytest
from src.ai_guard.exceptions import (
    AIGuardError,
    ConfigurationError,
    AnalysisError,
    SecurityError,
    PerformanceError,
    TestGenerationError,
    ReportGenerationError,
    DependencyError,
    ToolExecutionError,
    ValidationError,
    TimeoutError,
    FileSystemError,
    NetworkError
)


class TestAIGuardError:
    """Test AIGuardError base class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = AIGuardError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code is None
        assert error.details == {}

    def test_error_with_code(self):
        """Test error with error code."""
        error = AIGuardError("Test error", "TEST_CODE")
        assert str(error) == "[TEST_CODE] Test error"
        assert error.error_code == "TEST_CODE"

    def test_error_with_details(self):
        """Test error with details."""
        details = {"file": "test.py", "line": 10}
        error = AIGuardError("Test error", details=details)
        assert error.details == details


class TestConfigurationError:
    """Test ConfigurationError."""

    def test_configuration_error(self):
        """Test configuration error creation."""
        error = ConfigurationError("Invalid config", "config.toml")
        assert str(error) == "[CONFIG_ERROR] Invalid config"
        assert error.config_path == "config.toml"
        assert error.error_code == "CONFIG_ERROR"


class TestAnalysisError:
    """Test AnalysisError."""

    def test_analysis_error(self):
        """Test analysis error creation."""
        error = AnalysisError("Analysis failed", "test.py", 10)
        assert str(error) == "[ANALYSIS_ERROR] Analysis failed"
        assert error.file_path == "test.py"
        assert error.line_number == 10
        assert error.error_code == "ANALYSIS_ERROR"


class TestSecurityError:
    """Test SecurityError."""

    def test_security_error(self):
        """Test security error creation."""
        error = SecurityError("Security issue", "sql_injection", "high")
        assert str(error) == "[SECURITY_ERROR] Security issue"
        assert error.vulnerability_type == "sql_injection"
        assert error.severity == "high"
        assert error.error_code == "SECURITY_ERROR"


class TestPerformanceError:
    """Test PerformanceError."""

    def test_performance_error(self):
        """Test performance error creation."""
        error = PerformanceError("Performance issue", "memory", 100.0)
        assert str(error) == "[PERFORMANCE_ERROR] Performance issue"
        assert error.metric_name == "memory"
        assert error.threshold == 100.0
        assert error.error_code == "PERFORMANCE_ERROR"


class TestTestGenerationError:
    """Test TestGenerationError."""

    def test_test_generation_error(self):
        """Test test generation error creation."""
        error = TestGenerationError("Test generation failed", "test.py", "unit")
        assert str(error) == "[TEST_GENERATION_ERROR] Test generation failed"
        assert error.target_file == "test.py"
        assert error.generation_type == "unit"
        assert error.error_code == "TEST_GENERATION_ERROR"


class TestReportGenerationError:
    """Test ReportGenerationError."""

    def test_report_generation_error(self):
        """Test report generation error creation."""
        error = ReportGenerationError("Report failed", "html", "report.html")
        assert str(error) == "[REPORT_GENERATION_ERROR] Report failed"
        assert error.report_format == "html"
        assert error.output_path == "report.html"
        assert error.error_code == "REPORT_GENERATION_ERROR"


class TestDependencyError:
    """Test DependencyError."""

    def test_dependency_error(self):
        """Test dependency error creation."""
        error = DependencyError("Dependency issue", "requests", "2.25.0")
        assert str(error) == "[DEPENDENCY_ERROR] Dependency issue"
        assert error.package_name == "requests"
        assert error.version == "2.25.0"
        assert error.error_code == "DEPENDENCY_ERROR"


class TestToolExecutionError:
    """Test ToolExecutionError."""

    def test_tool_execution_error(self):
        """Test tool execution error creation."""
        error = ToolExecutionError("Tool failed", "flake8", "flake8 src/", 1)
        assert str(error) == "[TOOL_EXECUTION_ERROR] Tool failed"
        assert error.tool_name == "flake8"
        assert error.command == "flake8 src/"
        assert error.exit_code == 1
        assert error.error_code == "TOOL_EXECUTION_ERROR"


class TestValidationError:
    """Test ValidationError."""

    def test_validation_error(self):
        """Test validation error creation."""
        error = ValidationError("Validation failed", "coverage", 50)
        assert str(error) == "[VALIDATION_ERROR] Validation failed"
        assert error.field_name == "coverage"
        assert error.value == 50
        assert error.error_code == "VALIDATION_ERROR"


class TestTimeoutError:
    """Test TimeoutError."""

    def test_timeout_error(self):
        """Test timeout error creation."""
        error = TimeoutError("Operation timed out", 30, "analysis")
        assert str(error) == "[TIMEOUT_ERROR] Operation timed out"
        assert error.timeout_seconds == 30
        assert error.operation == "analysis"
        assert error.error_code == "TIMEOUT_ERROR"


class TestFileSystemError:
    """Test FileSystemError."""

    def test_filesystem_error(self):
        """Test file system error creation."""
        error = FileSystemError("File operation failed", "test.py", "read")
        assert str(error) == "[FILESYSTEM_ERROR] File operation failed"
        assert error.file_path == "test.py"
        assert error.operation == "read"
        assert error.error_code == "FILESYSTEM_ERROR"


class TestNetworkError:
    """Test NetworkError."""

    def test_network_error(self):
        """Test network error creation."""
        error = NetworkError("Network failed", "https://api.example.com", 500)
        assert str(error) == "[NETWORK_ERROR] Network failed"
        assert error.url == "https://api.example.com"
        assert error.status_code == 500
        assert error.error_code == "NETWORK_ERROR"


class TestExceptionInheritance:
    """Test exception inheritance."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all exceptions inherit from AIGuardError."""
        exceptions = [
            ConfigurationError,
            AnalysisError,
            SecurityError,
            PerformanceError,
            TestGenerationError,
            ReportGenerationError,
            DependencyError,
            ToolExecutionError,
            ValidationError,
            TimeoutError,
            FileSystemError,
            NetworkError
        ]
        
        for exception_class in exceptions:
            error = exception_class("Test message")
            assert isinstance(error, AIGuardError)
            assert isinstance(error, Exception)


class TestExceptionChaining:
    """Test exception chaining."""

    def test_exception_chaining(self):
        """Test exception chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise AIGuardError("Wrapped error") from e
        except AIGuardError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"
