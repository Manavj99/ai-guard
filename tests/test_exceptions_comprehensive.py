"""Comprehensive tests for exceptions module."""

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

    def test_basic_error_creation(self):
        """Test basic error creation."""
        error = AIGuardError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.details == {}

    def test_error_with_code(self):
        """Test error with error code."""
        error = AIGuardError("Test error", error_code="TEST_ERROR")
        assert str(error) == "[TEST_ERROR] Test error"
        assert error.error_code == "TEST_ERROR"

    def test_error_with_details(self):
        """Test error with details."""
        details = {"file": "test.py", "line": 10}
        error = AIGuardError("Test error", details=details)
        assert error.details == details

    def test_error_with_code_and_details(self):
        """Test error with both code and details."""
        details = {"file": "test.py"}
        error = AIGuardError("Test error", error_code="TEST_ERROR", details=details)
        assert str(error) == "[TEST_ERROR] Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == details

    def test_error_inheritance(self):
        """Test that AIGuardError inherits from Exception."""
        error = AIGuardError("Test error")
        assert isinstance(error, Exception)

    def test_error_with_none_details(self):
        """Test error with None details."""
        error = AIGuardError("Test error", details=None)
        assert error.details == {}


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_configuration_error_creation(self):
        """Test configuration error creation."""
        error = ConfigurationError("Config error")
        assert str(error) == "[CONFIG_ERROR] Config error"
        assert error.error_code == "CONFIG_ERROR"
        assert error.config_path is None

    def test_configuration_error_with_path(self):
        """Test configuration error with path."""
        error = ConfigurationError("Config error", config_path="/path/to/config.toml")
        assert error.config_path == "/path/to/config.toml"

    def test_configuration_error_with_details(self):
        """Test configuration error with details."""
        details = {"missing_key": "required_field"}
        error = ConfigurationError("Config error", details=details)
        assert error.details == details

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from AIGuardError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, AIGuardError)


class TestAnalysisError:
    """Test AnalysisError class."""

    def test_analysis_error_creation(self):
        """Test analysis error creation."""
        error = AnalysisError("Analysis error")
        assert str(error) == "[ANALYSIS_ERROR] Analysis error"
        assert error.error_code == "ANALYSIS_ERROR"
        assert error.file_path is None
        assert error.line_number is None

    def test_analysis_error_with_file_path(self):
        """Test analysis error with file path."""
        error = AnalysisError("Analysis error", file_path="test.py")
        assert error.file_path == "test.py"

    def test_analysis_error_with_line_number(self):
        """Test analysis error with line number."""
        error = AnalysisError("Analysis error", line_number=42)
        assert error.line_number == 42

    def test_analysis_error_with_both(self):
        """Test analysis error with both file path and line number."""
        error = AnalysisError("Analysis error", file_path="test.py", line_number=42)
        assert error.file_path == "test.py"
        assert error.line_number == 42

    def test_analysis_error_inheritance(self):
        """Test that AnalysisError inherits from AIGuardError."""
        error = AnalysisError("Analysis error")
        assert isinstance(error, AIGuardError)


class TestSecurityError:
    """Test SecurityError class."""

    def test_security_error_creation(self):
        """Test security error creation."""
        error = SecurityError("Security error")
        assert str(error) == "[SECURITY_ERROR] Security error"
        assert error.error_code == "SECURITY_ERROR"
        assert error.vulnerability_type is None
        assert error.severity is None

    def test_security_error_with_vulnerability_type(self):
        """Test security error with vulnerability type."""
        error = SecurityError("Security error", vulnerability_type="SQL_INJECTION")
        assert error.vulnerability_type == "SQL_INJECTION"

    def test_security_error_with_severity(self):
        """Test security error with severity."""
        error = SecurityError("Security error", severity="HIGH")
        assert error.severity == "HIGH"

    def test_security_error_with_both(self):
        """Test security error with both vulnerability type and severity."""
        error = SecurityError("Security error", vulnerability_type="XSS", severity="CRITICAL")
        assert error.vulnerability_type == "XSS"
        assert error.severity == "CRITICAL"

    def test_security_error_inheritance(self):
        """Test that SecurityError inherits from AIGuardError."""
        error = SecurityError("Security error")
        assert isinstance(error, AIGuardError)


class TestPerformanceError:
    """Test PerformanceError class."""

    def test_performance_error_creation(self):
        """Test performance error creation."""
        error = PerformanceError("Performance error")
        assert str(error) == "[PERFORMANCE_ERROR] Performance error"
        assert error.error_code == "PERFORMANCE_ERROR"
        assert error.metric_name is None
        assert error.threshold is None

    def test_performance_error_with_metric_name(self):
        """Test performance error with metric name."""
        error = PerformanceError("Performance error", metric_name="execution_time")
        assert error.metric_name == "execution_time"

    def test_performance_error_with_threshold(self):
        """Test performance error with threshold."""
        error = PerformanceError("Performance error", threshold=5.0)
        assert error.threshold == 5.0

    def test_performance_error_with_both(self):
        """Test performance error with both metric name and threshold."""
        error = PerformanceError("Performance error", metric_name="memory_usage", threshold=100.0)
        assert error.metric_name == "memory_usage"
        assert error.threshold == 100.0

    def test_performance_error_inheritance(self):
        """Test that PerformanceError inherits from AIGuardError."""
        error = PerformanceError("Performance error")
        assert isinstance(error, AIGuardError)


class TestTestGenerationError:
    """Test TestGenerationError class."""

    def test_test_generation_error_creation(self):
        """Test test generation error creation."""
        error = TestGenerationError("Test generation error")
        assert str(error) == "[TEST_GENERATION_ERROR] Test generation error"
        assert error.error_code == "TEST_GENERATION_ERROR"
        assert error.target_file is None
        assert error.generation_type is None

    def test_test_generation_error_with_target_file(self):
        """Test test generation error with target file."""
        error = TestGenerationError("Test generation error", target_file="test_module.py")
        assert error.target_file == "test_module.py"

    def test_test_generation_error_with_generation_type(self):
        """Test test generation error with generation type."""
        error = TestGenerationError("Test generation error", generation_type="unit_tests")
        assert error.generation_type == "unit_tests"

    def test_test_generation_error_with_both(self):
        """Test test generation error with both target file and generation type."""
        error = TestGenerationError("Test generation error", target_file="test_module.py", generation_type="integration_tests")
        assert error.target_file == "test_module.py"
        assert error.generation_type == "integration_tests"

    def test_test_generation_error_inheritance(self):
        """Test that TestGenerationError inherits from AIGuardError."""
        error = TestGenerationError("Test generation error")
        assert isinstance(error, AIGuardError)


class TestReportGenerationError:
    """Test ReportGenerationError class."""

    def test_report_generation_error_creation(self):
        """Test report generation error creation."""
        error = ReportGenerationError("Report generation error")
        assert str(error) == "[REPORT_GENERATION_ERROR] Report generation error"
        assert error.error_code == "REPORT_GENERATION_ERROR"
        assert error.report_format is None
        assert error.output_path is None

    def test_report_generation_error_with_format(self):
        """Test report generation error with format."""
        error = ReportGenerationError("Report generation error", report_format="HTML")
        assert error.report_format == "HTML"

    def test_report_generation_error_with_output_path(self):
        """Test report generation error with output path."""
        error = ReportGenerationError("Report generation error", output_path="/path/to/report.html")
        assert error.output_path == "/path/to/report.html"

    def test_report_generation_error_with_both(self):
        """Test report generation error with both format and output path."""
        error = ReportGenerationError("Report generation error", report_format="SARIF", output_path="/path/to/report.sarif")
        assert error.report_format == "SARIF"
        assert error.output_path == "/path/to/report.sarif"

    def test_report_generation_error_inheritance(self):
        """Test that ReportGenerationError inherits from AIGuardError."""
        error = ReportGenerationError("Report generation error")
        assert isinstance(error, AIGuardError)


class TestDependencyError:
    """Test DependencyError class."""

    def test_dependency_error_creation(self):
        """Test dependency error creation."""
        error = DependencyError("Dependency error")
        assert str(error) == "[DEPENDENCY_ERROR] Dependency error"
        assert error.error_code == "DEPENDENCY_ERROR"
        assert error.package_name is None
        assert error.version is None

    def test_dependency_error_with_package_name(self):
        """Test dependency error with package name."""
        error = DependencyError("Dependency error", package_name="requests")
        assert error.package_name == "requests"

    def test_dependency_error_with_version(self):
        """Test dependency error with version."""
        error = DependencyError("Dependency error", version="2.28.0")
        assert error.version == "2.28.0"

    def test_dependency_error_with_both(self):
        """Test dependency error with both package name and version."""
        error = DependencyError("Dependency error", package_name="requests", version="2.28.0")
        assert error.package_name == "requests"
        assert error.version == "2.28.0"

    def test_dependency_error_inheritance(self):
        """Test that DependencyError inherits from AIGuardError."""
        error = DependencyError("Dependency error")
        assert isinstance(error, AIGuardError)


class TestToolExecutionError:
    """Test ToolExecutionError class."""

    def test_tool_execution_error_creation(self):
        """Test tool execution error creation."""
        error = ToolExecutionError("Tool execution error")
        assert str(error) == "[TOOL_EXECUTION_ERROR] Tool execution error"
        assert error.error_code == "TOOL_EXECUTION_ERROR"
        assert error.tool_name is None
        assert error.command is None
        assert error.exit_code is None

    def test_tool_execution_error_with_tool_name(self):
        """Test tool execution error with tool name."""
        error = ToolExecutionError("Tool execution error", tool_name="flake8")
        assert error.tool_name == "flake8"

    def test_tool_execution_error_with_command(self):
        """Test tool execution error with command."""
        error = ToolExecutionError("Tool execution error", command="flake8 src/")
        assert error.command == "flake8 src/"

    def test_tool_execution_error_with_exit_code(self):
        """Test tool execution error with exit code."""
        error = ToolExecutionError("Tool execution error", exit_code=1)
        assert error.exit_code == 1

    def test_tool_execution_error_with_all(self):
        """Test tool execution error with all parameters."""
        error = ToolExecutionError("Tool execution error", tool_name="flake8", command="flake8 src/", exit_code=1)
        assert error.tool_name == "flake8"
        assert error.command == "flake8 src/"
        assert error.exit_code == 1

    def test_tool_execution_error_inheritance(self):
        """Test that ToolExecutionError inherits from AIGuardError."""
        error = ToolExecutionError("Tool execution error")
        assert isinstance(error, AIGuardError)


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_creation(self):
        """Test validation error creation."""
        error = ValidationError("Validation error")
        assert str(error) == "[VALIDATION_ERROR] Validation error"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field_name is None
        assert error.value is None

    def test_validation_error_with_field_name(self):
        """Test validation error with field name."""
        error = ValidationError("Validation error", field_name="min_coverage")
        assert error.field_name == "min_coverage"

    def test_validation_error_with_value(self):
        """Test validation error with value."""
        error = ValidationError("Validation error", value=150)
        assert error.value == 150

    def test_validation_error_with_both(self):
        """Test validation error with both field name and value."""
        error = ValidationError("Validation error", field_name="min_coverage", value=150)
        assert error.field_name == "min_coverage"
        assert error.value == 150

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from AIGuardError."""
        error = ValidationError("Validation error")
        assert isinstance(error, AIGuardError)


class TestTimeoutError:
    """Test TimeoutError class."""

    def test_timeout_error_creation(self):
        """Test timeout error creation."""
        error = TimeoutError("Timeout error")
        assert str(error) == "[TIMEOUT_ERROR] Timeout error"
        assert error.error_code == "TIMEOUT_ERROR"
        assert error.timeout_seconds is None
        assert error.operation is None

    def test_timeout_error_with_timeout_seconds(self):
        """Test timeout error with timeout seconds."""
        error = TimeoutError("Timeout error", timeout_seconds=30)
        assert error.timeout_seconds == 30

    def test_timeout_error_with_operation(self):
        """Test timeout error with operation."""
        error = TimeoutError("Timeout error", operation="test_execution")
        assert error.operation == "test_execution"

    def test_timeout_error_with_both(self):
        """Test timeout error with both timeout seconds and operation."""
        error = TimeoutError("Timeout error", timeout_seconds=60, operation="analysis")
        assert error.timeout_seconds == 60
        assert error.operation == "analysis"

    def test_timeout_error_inheritance(self):
        """Test that TimeoutError inherits from AIGuardError."""
        error = TimeoutError("Timeout error")
        assert isinstance(error, AIGuardError)


class TestFileSystemError:
    """Test FileSystemError class."""

    def test_file_system_error_creation(self):
        """Test file system error creation."""
        error = FileSystemError("File system error")
        assert str(error) == "[FILESYSTEM_ERROR] File system error"
        assert error.error_code == "FILESYSTEM_ERROR"
        assert error.file_path is None
        assert error.operation is None

    def test_file_system_error_with_file_path(self):
        """Test file system error with file path."""
        error = FileSystemError("File system error", file_path="/path/to/file.py")
        assert error.file_path == "/path/to/file.py"

    def test_file_system_error_with_operation(self):
        """Test file system error with operation."""
        error = FileSystemError("File system error", operation="read")
        assert error.operation == "read"

    def test_file_system_error_with_both(self):
        """Test file system error with both file path and operation."""
        error = FileSystemError("File system error", file_path="/path/to/file.py", operation="write")
        assert error.file_path == "/path/to/file.py"
        assert error.operation == "write"

    def test_file_system_error_inheritance(self):
        """Test that FileSystemError inherits from AIGuardError."""
        error = FileSystemError("File system error")
        assert isinstance(error, AIGuardError)


class TestNetworkError:
    """Test NetworkError class."""

    def test_network_error_creation(self):
        """Test network error creation."""
        error = NetworkError("Network error")
        assert str(error) == "[NETWORK_ERROR] Network error"
        assert error.error_code == "NETWORK_ERROR"
        assert error.url is None
        assert error.status_code is None

    def test_network_error_with_url(self):
        """Test network error with URL."""
        error = NetworkError("Network error", url="https://api.example.com")
        assert error.url == "https://api.example.com"

    def test_network_error_with_status_code(self):
        """Test network error with status code."""
        error = NetworkError("Network error", status_code=404)
        assert error.status_code == 404

    def test_network_error_with_both(self):
        """Test network error with both URL and status code."""
        error = NetworkError("Network error", url="https://api.example.com", status_code=500)
        assert error.url == "https://api.example.com"
        assert error.status_code == 500

    def test_network_error_inheritance(self):
        """Test that NetworkError inherits from AIGuardError."""
        error = NetworkError("Network error")
        assert isinstance(error, AIGuardError)


class TestErrorChaining:
    """Test error chaining and exception handling."""

    def test_error_as_exception(self):
        """Test that errors can be raised as exceptions."""
        with pytest.raises(AIGuardError) as exc_info:
            raise AIGuardError("Test error")
        
        assert str(exc_info.value) == "Test error"

    def test_specific_error_as_exception(self):
        """Test that specific errors can be raised as exceptions."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Config error")
        
        assert str(exc_info.value) == "[CONFIG_ERROR] Config error"

    def test_error_with_complex_details(self):
        """Test error with complex details structure."""
        details = {
            "files": ["test1.py", "test2.py"],
            "metrics": {"coverage": 85.5, "complexity": 10},
            "nested": {"key": "value"}
        }
        error = AIGuardError("Complex error", details=details)
        assert error.details == details

    def test_error_string_representation(self):
        """Test error string representation."""
        error = AIGuardError("Test error", error_code="TEST_ERROR")
        # The repr shows the original message, not the formatted string
        assert repr(error) == "AIGuardError('Test error')"

    def test_error_equality(self):
        """Test error equality."""
        error1 = AIGuardError("Test error")
        error2 = AIGuardError("Test error")
        error3 = AIGuardError("Different error")
        
        # Errors with same message should be equal
        assert str(error1) == str(error2)
        assert str(error1) != str(error3)

    def test_error_with_empty_string_message(self):
        """Test error with empty string message."""
        error = AIGuardError("")
        assert str(error) == ""
        assert error.message == ""

    def test_error_with_unicode_message(self):
        """Test error with Unicode message."""
        error = AIGuardError("测试错误")
        assert str(error) == "测试错误"
        assert error.message == "测试错误"
