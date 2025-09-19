"""Additional tests for PR annotations module."""

import pytest
from unittest.mock import patch, MagicMock
from ai_guard.pr_annotations import (
    create_pr_annotation,
    format_annotation_message,
    get_annotation_level,
    create_quality_gate_annotation,
    create_coverage_annotation,
    create_security_annotation,
    create_performance_annotation,
    create_test_annotation,
    PRAnnotationManager,
    AnnotationFormatter,
    QualityGateAnnotation,
    CoverageAnnotation,
    SecurityAnnotation,
    PerformanceAnnotation,
    TestAnnotation
)


class TestPRAnnotationCreation:
    """Test PR annotation creation functions."""

    def test_create_pr_annotation_success(self):
        """Test successful PR annotation creation."""
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="warning",
            message="Test warning",
            title="Test Title"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "warning"
        assert annotation["message"] == "Test warning"
        assert annotation["title"] == "Test Title"

    def test_create_pr_annotation_minimal(self):
        """Test PR annotation creation with minimal parameters."""
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="notice",
            message="Test message"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "notice"
        assert annotation["message"] == "Test message"
        assert annotation["title"] == "AI-Guard Analysis"

    def test_create_pr_annotation_invalid_level(self):
        """Test PR annotation creation with invalid level."""
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="invalid",
            message="Test message"
        )
        
        assert annotation["annotation_level"] == "notice"  # Should default to notice


class TestAnnotationFormatting:
    """Test annotation message formatting."""

    def test_format_annotation_message_simple(self):
        """Test simple annotation message formatting."""
        message = format_annotation_message("Simple message")
        
        assert message == "Simple message"

    def test_format_annotation_message_with_details(self):
        """Test annotation message formatting with details."""
        message = format_annotation_message(
            "Main message",
            details="Additional details",
            suggestion="Try this instead"
        )
        
        assert "Main message" in message
        assert "Additional details" in message
        assert "Try this instead" in message

    def test_format_annotation_message_with_code(self):
        """Test annotation message formatting with code."""
        message = format_annotation_message(
            "Code issue",
            code_example="print('hello')",
            suggestion="Use logging instead"
        )
        
        assert "Code issue" in message
        assert "print('hello')" in message
        assert "Use logging instead" in message


class TestAnnotationLevel:
    """Test annotation level functions."""

    def test_get_annotation_level_error(self):
        """Test getting error annotation level."""
        level = get_annotation_level("error")
        assert level == "failure"

    def test_get_annotation_level_warning(self):
        """Test getting warning annotation level."""
        level = get_annotation_level("warning")
        assert level == "warning"

    def test_get_annotation_level_info(self):
        """Test getting info annotation level."""
        level = get_annotation_level("info")
        assert level == "notice"

    def test_get_annotation_level_default(self):
        """Test getting default annotation level."""
        level = get_annotation_level("unknown")
        assert level == "notice"


class TestQualityGateAnnotation:
    """Test quality gate annotation creation."""

    def test_create_quality_gate_annotation_success(self):
        """Test successful quality gate annotation creation."""
        annotation = create_quality_gate_annotation(
            path="test.py",
            line=10,
            gate_name="test_gate",
            status="passed",
            message="Gate passed successfully"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "notice"
        assert "test_gate" in annotation["message"]
        assert "passed" in annotation["message"]

    def test_create_quality_gate_annotation_failed(self):
        """Test quality gate annotation creation for failed gate."""
        annotation = create_quality_gate_annotation(
            path="test.py",
            line=10,
            gate_name="test_gate",
            status="failed",
            message="Gate failed"
        )
        
        assert annotation["annotation_level"] == "failure"
        assert "failed" in annotation["message"]


class TestCoverageAnnotation:
    """Test coverage annotation creation."""

    def test_create_coverage_annotation_high(self):
        """Test coverage annotation for high coverage."""
        annotation = create_coverage_annotation(
            path="test.py",
            coverage_percent=95.5,
            threshold=80.0
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["annotation_level"] == "notice"
        assert "95.5%" in annotation["message"]

    def test_create_coverage_annotation_low(self):
        """Test coverage annotation for low coverage."""
        annotation = create_coverage_annotation(
            path="test.py",
            coverage_percent=65.0,
            threshold=80.0
        )
        
        assert annotation["annotation_level"] == "warning"
        assert "65.0%" in annotation["message"]
        assert "80.0%" in annotation["message"]


class TestSecurityAnnotation:
    """Test security annotation creation."""

    def test_create_security_annotation_high(self):
        """Test security annotation for high severity."""
        annotation = create_security_annotation(
            path="test.py",
            line=10,
            severity="high",
            vulnerability="SQL Injection",
            description="Potential SQL injection vulnerability"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "failure"
        assert "SQL Injection" in annotation["message"]

    def test_create_security_annotation_medium(self):
        """Test security annotation for medium severity."""
        annotation = create_security_annotation(
            path="test.py",
            line=10,
            severity="medium",
            vulnerability="XSS",
            description="Potential XSS vulnerability"
        )
        
        assert annotation["annotation_level"] == "warning"
        assert "XSS" in annotation["message"]

    def test_create_security_annotation_low(self):
        """Test security annotation for low severity."""
        annotation = create_security_annotation(
            path="test.py",
            line=10,
            severity="low",
            vulnerability="Info Disclosure",
            description="Information disclosure"
        )
        
        assert annotation["annotation_level"] == "notice"
        assert "Info Disclosure" in annotation["message"]


class TestPerformanceAnnotation:
    """Test performance annotation creation."""

    def test_create_performance_annotation_slow(self):
        """Test performance annotation for slow function."""
        annotation = create_performance_annotation(
            path="test.py",
            line=10,
            function_name="slow_function",
            execution_time=2.5,
            threshold=1.0
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "warning"
        assert "slow_function" in annotation["message"]
        assert "2.5s" in annotation["message"]

    def test_create_performance_annotation_fast(self):
        """Test performance annotation for fast function."""
        annotation = create_performance_annotation(
            path="test.py",
            line=10,
            function_name="fast_function",
            execution_time=0.5,
            threshold=1.0
        )
        
        assert annotation["annotation_level"] == "notice"
        assert "fast_function" in annotation["message"]


class TestTestAnnotation:
    """Test test annotation creation."""

    def test_create_test_annotation_passed(self):
        """Test test annotation for passed test."""
        annotation = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="passed",
            duration=0.1
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "notice"
        assert "test_function" in annotation["message"]
        assert "passed" in annotation["message"]

    def test_create_test_annotation_failed(self):
        """Test test annotation for failed test."""
        annotation = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="failed",
            duration=0.1,
            error_message="AssertionError: Expected 1, got 2"
        )
        
        assert annotation["annotation_level"] == "failure"
        assert "failed" in annotation["message"]
        assert "AssertionError" in annotation["message"]


class TestPRAnnotationManager:
    """Test PR annotation manager."""

    def test_manager_init(self):
        """Test annotation manager initialization."""
        manager = PRAnnotationManager()
        
        assert manager.annotations == []
        assert manager.max_annotations == 50

    def test_manager_init_custom_max(self):
        """Test annotation manager initialization with custom max."""
        manager = PRAnnotationManager(max_annotations=100)
        
        assert manager.max_annotations == 100

    def test_add_annotation(self):
        """Test adding annotation to manager."""
        manager = PRAnnotationManager()
        
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="warning",
            message="Test warning"
        )
        
        manager.add_annotation(annotation)
        
        assert len(manager.annotations) == 1
        assert manager.annotations[0] == annotation

    def test_add_annotation_max_limit(self):
        """Test adding annotation when at max limit."""
        manager = PRAnnotationManager(max_annotations=2)
        
        # Add two annotations
        for i in range(2):
            annotation = create_pr_annotation(
                path=f"test{i}.py",
                line=10,
                level="warning",
                message=f"Warning {i}"
            )
            manager.add_annotation(annotation)
        
        # Try to add third annotation
        annotation = create_pr_annotation(
            path="test3.py",
            line=10,
            level="warning",
            message="Warning 3"
        )
        
        manager.add_annotation(annotation)
        
        # Should still have only 2 annotations
        assert len(manager.annotations) == 2

    def test_get_annotations_by_level(self):
        """Test getting annotations by level."""
        manager = PRAnnotationManager()
        
        # Add annotations with different levels
        manager.add_annotation(create_pr_annotation("test1.py", 10, "failure", "Error"))
        manager.add_annotation(create_pr_annotation("test2.py", 10, "warning", "Warning"))
        manager.add_annotation(create_pr_annotation("test3.py", 10, "notice", "Info"))
        
        error_annotations = manager.get_annotations_by_level("failure")
        warning_annotations = manager.get_annotations_by_level("warning")
        notice_annotations = manager.get_annotations_by_level("notice")
        
        assert len(error_annotations) == 1
        assert len(warning_annotations) == 1
        assert len(notice_annotations) == 1

    def test_get_annotations_by_path(self):
        """Test getting annotations by path."""
        manager = PRAnnotationManager()
        
        # Add annotations for different paths
        manager.add_annotation(create_pr_annotation("test1.py", 10, "warning", "Warning 1"))
        manager.add_annotation(create_pr_annotation("test1.py", 20, "warning", "Warning 2"))
        manager.add_annotation(create_pr_annotation("test2.py", 10, "warning", "Warning 3"))
        
        test1_annotations = manager.get_annotations_by_path("test1.py")
        test2_annotations = manager.get_annotations_by_path("test2.py")
        
        assert len(test1_annotations) == 2
        assert len(test2_annotations) == 1

    def test_clear_annotations(self):
        """Test clearing all annotations."""
        manager = PRAnnotationManager()
        
        # Add some annotations
        manager.add_annotation(create_pr_annotation("test.py", 10, "warning", "Warning"))
        
        assert len(manager.annotations) == 1
        
        manager.clear_annotations()
        
        assert len(manager.annotations) == 0

    def test_get_summary(self):
        """Test getting annotation summary."""
        manager = PRAnnotationManager()
        
        # Add annotations with different levels
        manager.add_annotation(create_pr_annotation("test1.py", 10, "failure", "Error"))
        manager.add_annotation(create_pr_annotation("test2.py", 10, "warning", "Warning"))
        manager.add_annotation(create_pr_annotation("test3.py", 10, "notice", "Info"))
        
        summary = manager.get_summary()
        
        assert summary["total"] == 3
        assert summary["failures"] == 1
        assert summary["warnings"] == 1
        assert summary["notices"] == 1


class TestAnnotationFormatter:
    """Test annotation formatter."""

    def test_formatter_init(self):
        """Test formatter initialization."""
        formatter = AnnotationFormatter()
        
        assert formatter.max_message_length == 65535
        assert formatter.include_timestamp is True

    def test_formatter_init_custom(self):
        """Test formatter initialization with custom settings."""
        formatter = AnnotationFormatter(
            max_message_length=1000,
            include_timestamp=False
        )
        
        assert formatter.max_message_length == 1000
        assert formatter.include_timestamp is False

    def test_format_annotation(self):
        """Test formatting annotation."""
        formatter = AnnotationFormatter()
        
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="warning",
            message="Test warning"
        )
        
        formatted = formatter.format_annotation(annotation)
        
        assert formatted["path"] == "test.py"
        assert formatted["line"] == 10
        assert formatted["annotation_level"] == "warning"
        assert "Test warning" in formatted["message"]

    def test_format_annotation_long_message(self):
        """Test formatting annotation with long message."""
        formatter = AnnotationFormatter(max_message_length=100)
        
        long_message = "This is a very long message that should be truncated because it exceeds the maximum length allowed for annotation messages"
        
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="warning",
            message=long_message
        )
        
        formatted = formatter.format_annotation(annotation)
        
        assert len(formatted["message"]) <= 100
        assert "..." in formatted["message"]

    def test_format_annotations_batch(self):
        """Test formatting multiple annotations."""
        formatter = AnnotationFormatter()
        
        annotations = [
            create_pr_annotation("test1.py", 10, "warning", "Warning 1"),
            create_pr_annotation("test2.py", 20, "failure", "Error 1"),
            create_pr_annotation("test3.py", 30, "notice", "Info 1")
        ]
        
        formatted = formatter.format_annotations(annotations)
        
        assert len(formatted) == 3
        assert all("path" in ann for ann in formatted)
        assert all("message" in ann for ann in formatted)
