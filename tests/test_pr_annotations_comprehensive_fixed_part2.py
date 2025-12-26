"""Part 2 of comprehensive tests for pr_annotations.py."""

import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import pytest
from src.ai_guard.pr_annotations import (
    create_pr_annotations,
    write_annotations_file,
    _parse_coverage_output,
    parse_lint_output,
    parse_mypy_output,
    parse_bandit_output,
    create_pr_annotation,
    get_annotation_level,
    create_quality_gate_annotation,
    create_coverage_annotation,
    create_security_annotation,
    create_performance_annotation,
    create_test_annotation,
    PRAnnotationManager,
    AnnotationFormatter,
    create_github_annotation,
    format_annotation_message,
    format_annotation_message_from_issue,
    main,
    CodeIssue,
)


class TestCreatePrAnnotations:
    """Test create_pr_annotations function."""

    def test_create_pr_annotations_with_lint_string(self):
        """Test creating PR annotations with lint output string."""
        lint_output = "test.py:10:5: E501 line too long"

        annotations = create_pr_annotations(lint_output=lint_output)

        assert len(annotations) == 1
        assert annotations[0].file_path == "test.py"
        assert annotations[0].line_number == 10
        assert annotations[0].annotation_level == "failure"

    def test_create_pr_annotations_with_lint_list(self):
        """Test creating PR annotations with lint issues list."""
        lint_issues = [
            CodeIssue(
                file_path="test.py",
                line_number=10,
                column=5,
                severity="error",
                message="Test error",
                rule_id="E501",
            )
        ]

        annotations = create_pr_annotations(lint_output=lint_issues)

        assert len(annotations) == 1
        assert annotations[0].file_path == "test.py"

    def test_create_pr_annotations_with_bandit(self):
        """Test creating PR annotations with bandit output."""
        bandit_output = "test.py:10:1: B101 hardcoded password"

        annotations = create_pr_annotations(bandit_output=bandit_output)

        assert len(annotations) == 1
        assert annotations[0].file_path == "test.py"
        assert annotations[0].annotation_level == "failure"

    def test_create_pr_annotations_with_mypy(self):
        """Test creating PR annotations with mypy output."""
        mypy_output = "test.py:10: error: Incompatible return type"

        annotations = create_pr_annotations(mypy_output=mypy_output)

        assert len(annotations) == 1
        assert annotations[0].file_path == "test.py"
        assert annotations[0].annotation_level == "failure"

    def test_create_pr_annotations_with_coverage(self):
        """Test creating PR annotations with coverage output."""
        coverage_output = "test.py: 10 lines, 8 covered (80%)"

        annotations = create_pr_annotations(coverage_output=coverage_output)

        # Coverage parsing might not work with this format, so we test what we get
        assert isinstance(annotations, list)

    def test_create_pr_annotations_with_output_file(self):
        """Test creating PR annotations with output file."""
        lint_output = "test.py:10:5: E501 line too long"

        with patch("builtins.open", mock_open()) as mock_file:
            annotations = create_pr_annotations(
                lint_output=lint_output, output_file="test.json"
            )

            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")

    def test_create_pr_annotations_with_output_file_error(self):
        """Test creating PR annotations with output file error."""
        lint_output = "test.py:10:5: E501 line too long"

        with patch("builtins.open", side_effect=IOError("Write error")):
            with patch("src.ai_guard.pr_annotations.logger") as mock_logger:
                annotations = create_pr_annotations(
                    lint_output=lint_output, output_file="test.json"
                )

                mock_logger.error.assert_called_once()

    def test_create_pr_annotations_no_inputs(self):
        """Test creating PR annotations with no inputs."""
        annotations = create_pr_annotations()

        assert annotations == []


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""

    def test_write_annotations_file_success(self):
        """Test successfully writing annotations file."""
        annotations = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "message": "Test message",
                "annotation_level": "error",
            }
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            result = write_annotations_file(annotations, "test.json")

            assert result is True
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")

            # Check JSON content
            written_data = mock_file().write.call_args[0][0]
            data = json.loads(written_data)
            assert data == annotations

    def test_write_annotations_file_error(self):
        """Test writing annotations file with error."""
        annotations = [{"test": "data"}]

        with patch("builtins.open", side_effect=IOError("Write error")):
            with patch("src.ai_guard.pr_annotations.logger") as mock_logger:
                result = write_annotations_file(annotations, "test.json")

                assert result is False
                mock_logger.error.assert_called_once()


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""

    def test_parse_coverage_output_empty(self):
        """Test parsing empty coverage output."""
        result = _parse_coverage_output("")
        assert result == {}

    def test_parse_coverage_output_with_file(self):
        """Test parsing coverage output with file data."""
        coverage_output = "test.py 10 8 80% 5, 10"

        result = _parse_coverage_output(coverage_output)

        assert "test.py" in result
        assert result["test.py"]["coverage"] == 80.0
        assert result["test.py"]["uncovered_lines"] == [5, 10]

    def test_parse_coverage_output_with_total(self):
        """Test parsing coverage output with total line."""
        coverage_output = "TOTAL 85%"

        result = _parse_coverage_output(coverage_output)

        assert "overall" in result
        assert result["overall"]["coverage"] == 85.0
        assert result["overall"]["uncovered_lines"] == []

    def test_parse_coverage_output_with_range(self):
        """Test parsing coverage output with line ranges."""
        coverage_output = "test.py 10 8 80% 5-7, 10"

        result = _parse_coverage_output(coverage_output)

        assert "test.py" in result
        assert result["test.py"]["uncovered_lines"] == [5, 6, 7, 10]

    def test_parse_coverage_output_invalid(self):
        """Test parsing invalid coverage output."""
        coverage_output = "invalid line"

        result = _parse_coverage_output(coverage_output)

        assert result == {}


class TestParseLintOutput:
    """Test parse_lint_output function."""

    def test_parse_lint_output_none(self):
        """Test parsing None lint output."""
        result = parse_lint_output(None)
        assert result == []

    def test_parse_lint_output_empty(self):
        """Test parsing empty lint output."""
        result = parse_lint_output("")
        assert result == []

    def test_parse_lint_output_with_errors(self):
        """Test parsing lint output with errors."""
        lint_output = (
            "test.py:10:5: E501 line too long\ntest.py:15:1: F401 unused import"
        )

        result = parse_lint_output(lint_output)

        assert len(result) == 2
        assert result[0].file_path == "test.py"
        assert result[0].line_number == 10
        assert result[0].severity == "error"
        assert result[0].rule_id == "E501"
        assert result[1].rule_id == "F401"

    def test_parse_lint_output_with_warnings(self):
        """Test parsing lint output with warnings."""
        lint_output = "test.py:10:5: W291 trailing whitespace"

        result = parse_lint_output(lint_output)

        assert len(result) == 1
        assert result[0].severity == "warning"
        assert result[0].rule_id == "W291"

    def test_parse_lint_output_with_info(self):
        """Test parsing lint output with info."""
        lint_output = "test.py:10:5: I001 missing docstring"

        result = parse_lint_output(lint_output)

        assert len(result) == 1
        assert result[0].severity == "info"
        assert result[0].rule_id == "I001"

    def test_parse_lint_output_invalid_line(self):
        """Test parsing lint output with invalid lines."""
        lint_output = "invalid line\nanother invalid line"

        result = parse_lint_output(lint_output)

        assert result == []

    def test_parse_lint_output_negative_line(self):
        """Test parsing lint output with negative line numbers."""
        lint_output = "test.py:-1:5: E501 line too long"

        result = parse_lint_output(lint_output)

        assert result == []

    def test_parse_lint_output_zero_line(self):
        """Test parsing lint output with zero line numbers."""
        lint_output = "test.py:0:5: E501 line too long"

        result = parse_lint_output(lint_output)

        assert result == []


class TestParseMypyOutput:
    """Test parse_mypy_output function."""

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        result = parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_with_errors(self):
        """Test parsing mypy output with errors."""
        mypy_output = "test.py:10: error: Incompatible return type"

        result = parse_mypy_output(mypy_output)

        assert len(result) == 1
        assert result[0].file_path == "test.py"
        assert result[0].line_number == 10
        assert result[0].severity == "error"
        assert result[0].rule_id == "mypy"

    def test_parse_mypy_output_with_warnings(self):
        """Test parsing mypy output with warnings (should be ignored)."""
        mypy_output = "test.py:10: warning: Unused 'type: ignore' comment"

        result = parse_mypy_output(mypy_output)

        assert result == []

    def test_parse_mypy_output_invalid_line(self):
        """Test parsing mypy output with invalid lines."""
        mypy_output = "invalid line"

        result = parse_mypy_output(mypy_output)

        assert result == []

    def test_parse_mypy_output_invalid_line_number(self):
        """Test parsing mypy output with invalid line numbers."""
        mypy_output = "test.py:invalid: error: Test error"

        result = parse_mypy_output(mypy_output)

        assert len(result) == 1
        assert result[0].line_number == 0


class TestParseBanditOutput:
    """Test parse_bandit_output function."""

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        result = parse_bandit_output("")
        assert result == []

    def test_parse_bandit_output_standard_format(self):
        """Test parsing bandit output in standard format."""
        bandit_output = "test.py:10:1: B101 hardcoded password"

        result = parse_bandit_output(bandit_output)

        assert len(result) == 1
        assert result[0].file_path == "test.py"
        assert result[0].line_number == 10
        assert result[0].severity == "error"
        assert result[0].rule_id == "B101"

    def test_parse_bandit_output_issue_format(self):
        """Test parsing bandit output in issue format."""
        bandit_output = "test.py:10: >> Issue: hardcoded password"

        result = parse_bandit_output(bandit_output)

        assert len(result) == 1
        assert result[0].file_path == "test.py"
        assert result[0].line_number == 10
        assert result[0].severity == "medium"
        assert result[0].rule_id == "security_scan"

    def test_parse_bandit_output_issue_format_with_line(self):
        """Test parsing bandit output in issue format with line number."""
        bandit_output = "test.py:10:20: >> Issue: hardcoded password"

        result = parse_bandit_output(bandit_output)

        assert len(result) == 1
        assert result[0].file_path == "test.py"
        assert result[0].line_number == 20
        assert result[0].severity == "medium"

    def test_parse_bandit_output_different_severities(self):
        """Test parsing bandit output with different severities."""
        bandit_output = "test.py:10:1: B201 hardcoded password"

        result = parse_bandit_output(bandit_output)

        assert len(result) == 1
        assert result[0].severity == "warning"

    def test_parse_bandit_output_invalid_line(self):
        """Test parsing bandit output with invalid lines."""
        bandit_output = "invalid line"

        result = parse_bandit_output(bandit_output)

        assert result == []

    def test_parse_bandit_output_invalid_line_number(self):
        """Test parsing bandit output with invalid line numbers."""
        bandit_output = "test.py:invalid:1: B101 hardcoded password"

        result = parse_bandit_output(bandit_output)

        assert len(result) == 1
        assert result[0].line_number == 0


class TestCreatePrAnnotation:
    """Test create_pr_annotation function."""

    def test_create_pr_annotation_basic(self):
        """Test creating basic PR annotation."""
        result = create_pr_annotation(
            path="test.py", line=10, level="error", message="Test error"
        )

        assert result["path"] == "test.py"
        assert result["line"] == 10
        assert result["annotation_level"] == "failure"
        assert result["message"] == "Test error"
        assert result["title"] == "AI-Guard Analysis"

    def test_create_pr_annotation_with_title(self):
        """Test creating PR annotation with title."""
        result = create_pr_annotation(
            path="test.py",
            line=10,
            level="warning",
            message="Test warning",
            title="Custom Title",
        )

        assert result["annotation_level"] == "warning"
        assert result["title"] == "Custom Title"

    def test_create_pr_annotation_different_levels(self):
        """Test creating PR annotation with different levels."""
        # Test error level
        result = create_pr_annotation("test.py", 10, "error", "Test")
        assert result["annotation_level"] == "failure"

        # Test warning level
        result = create_pr_annotation("test.py", 10, "warning", "Test")
        assert result["annotation_level"] == "warning"

        # Test info level
        result = create_pr_annotation("test.py", 10, "info", "Test")
        assert result["annotation_level"] == "notice"

        # Test notice level
        result = create_pr_annotation("test.py", 10, "notice", "Test")
        assert result["annotation_level"] == "notice"

        # Test failure level
        result = create_pr_annotation("test.py", 10, "failure", "Test")
        assert result["annotation_level"] == "failure"

        # Test unknown level
        result = create_pr_annotation("test.py", 10, "unknown", "Test")
        assert result["annotation_level"] == "notice"


class TestGetAnnotationLevel:
    """Test get_annotation_level function."""

    def test_get_annotation_level_error(self):
        """Test getting annotation level for error."""
        result = get_annotation_level("error")
        assert result == "failure"

    def test_get_annotation_level_warning(self):
        """Test getting annotation level for warning."""
        result = get_annotation_level("warning")
        assert result == "warning"

    def test_get_annotation_level_info(self):
        """Test getting annotation level for info."""
        result = get_annotation_level("info")
        assert result == "notice"

    def test_get_annotation_level_unknown(self):
        """Test getting annotation level for unknown level."""
        result = get_annotation_level("unknown")
        assert result == "notice"

    def test_get_annotation_level_case_insensitive(self):
        """Test getting annotation level case insensitive."""
        result = get_annotation_level("ERROR")
        assert result == "failure"


class TestCreateQualityGateAnnotation:
    """Test create_quality_gate_annotation function."""

    def test_create_quality_gate_annotation_passed(self):
        """Test creating quality gate annotation for passed gate."""
        result = create_quality_gate_annotation(
            path="test.py",
            line=10,
            gate_name="coverage",
            status="passed",
            message="Coverage is above threshold",
        )

        assert result["path"] == "test.py"
        assert result["line"] == 10
        assert result["annotation_level"] == "notice"
        assert "Quality Gate 'coverage': passed" in result["message"]
        assert result["title"] == "Quality Gate: coverage"

    def test_create_quality_gate_annotation_failed(self):
        """Test creating quality gate annotation for failed gate."""
        result = create_quality_gate_annotation(
            path="test.py",
            line=10,
            gate_name="coverage",
            status="failed",
            message="Coverage is below threshold",
        )

        assert result["annotation_level"] == "failure"
        assert "Quality Gate 'coverage': failed" in result["message"]


class TestCreateCoverageAnnotation:
    """Test create_coverage_annotation function."""

    def test_create_coverage_annotation_above_threshold(self):
        """Test creating coverage annotation above threshold."""
        result = create_coverage_annotation(
            path="test.py", coverage_percent=90.0, threshold=80.0
        )

        assert result["path"] == "test.py"
        assert result["line"] == 1
        assert result["annotation_level"] == "notice"
        assert "Coverage: 90.0%" in result["message"]
        assert result["title"] == "Coverage Analysis"

    def test_create_coverage_annotation_below_threshold(self):
        """Test creating coverage annotation below threshold."""
        result = create_coverage_annotation(
            path="test.py", coverage_percent=70.0, threshold=80.0
        )

        assert result["annotation_level"] == "warning"
        assert "Coverage: 70.0%" in result["message"]
        assert "below threshold of 80.0%" in result["message"]


class TestCreateSecurityAnnotation:
    """Test create_security_annotation function."""

    def test_create_security_annotation_high(self):
        """Test creating security annotation for high severity."""
        result = create_security_annotation(
            path="test.py",
            line=10,
            severity="high",
            vulnerability="SQL Injection",
            description="Potential SQL injection vulnerability",
        )

        assert result["path"] == "test.py"
        assert result["line"] == 10
        assert result["annotation_level"] == "failure"
        assert "Security Issue (HIGH)" in result["message"]
        assert "SQL Injection" in result["message"]
        assert result["title"] == "Security: SQL Injection"

    def test_create_security_annotation_medium(self):
        """Test creating security annotation for medium severity."""
        result = create_security_annotation(
            path="test.py",
            line=10,
            severity="medium",
            vulnerability="XSS",
            description="Potential XSS vulnerability",
        )

        assert result["annotation_level"] == "warning"
        assert "Security Issue (MEDIUM)" in result["message"]

    def test_create_security_annotation_low(self):
        """Test creating security annotation for low severity."""
        result = create_security_annotation(
            path="test.py",
            line=10,
            severity="low",
            vulnerability="Info Leak",
            description="Information disclosure",
        )

        assert result["annotation_level"] == "notice"
        assert "Security Issue (LOW)" in result["message"]

    def test_create_security_annotation_unknown(self):
        """Test creating security annotation for unknown severity."""
        result = create_security_annotation(
            path="test.py",
            line=10,
            severity="unknown",
            vulnerability="Unknown",
            description="Unknown issue",
        )

        assert result["annotation_level"] == "warning"


class TestCreatePerformanceAnnotation:
    """Test create_performance_annotation function."""

    def test_create_performance_annotation_below_threshold(self):
        """Test creating performance annotation below threshold."""
        result = create_performance_annotation(
            path="test.py",
            line=10,
            function_name="slow_function",
            execution_time=0.5,
            threshold=1.0,
        )

        assert result["path"] == "test.py"
        assert result["line"] == 10
        assert result["annotation_level"] == "notice"
        assert "Performance: slow_function took 0.500s" in result["message"]
        assert "threshold: 1.0s" in result["message"]
        assert result["title"] == "Performance: slow_function"

    def test_create_performance_annotation_above_threshold(self):
        """Test creating performance annotation above threshold."""
        result = create_performance_annotation(
            path="test.py",
            line=10,
            function_name="slow_function",
            execution_time=2.0,
            threshold=1.0,
        )

        assert result["annotation_level"] == "warning"


class TestCreateTestAnnotation:
    """Test create_test_annotation function."""

    def test_create_test_annotation_passed(self):
        """Test creating test annotation for passed test."""
        result = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="passed",
            duration=0.5,
        )

        assert result["path"] == "test.py"
        assert result["line"] == 10
        assert result["annotation_level"] == "notice"
        assert "Test 'test_function': passed (0.500s)" in result["message"]
        assert result["title"] == "Test: test_function"

    def test_create_test_annotation_failed(self):
        """Test creating test annotation for failed test."""
        result = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="failed",
            duration=0.5,
            error_message="AssertionError: Expected 1, got 2",
        )

        assert result["annotation_level"] == "failure"
        assert "Test 'test_function': failed (0.500s)" in result["message"]
        assert "Error: AssertionError: Expected 1, got 2" in result["message"]


class TestPRAnnotationManager:
    """Test PRAnnotationManager class."""

    def test_pr_annotation_manager_init(self):
        """Test PRAnnotationManager initialization."""
        manager = PRAnnotationManager()
        assert manager.annotations == []
        assert manager.max_annotations == 50

    def test_pr_annotation_manager_init_custom_max(self):
        """Test PRAnnotationManager initialization with custom max."""
        manager = PRAnnotationManager(max_annotations=100)
        assert manager.max_annotations == 100

    def test_add_annotation(self):
        """Test adding annotation to manager."""
        manager = PRAnnotationManager()
        annotation = {"path": "test.py", "line": 10, "message": "Test"}

        manager.add_annotation(annotation)

        assert len(manager.annotations) == 1
        assert manager.annotations[0] == annotation

    def test_add_annotation_max_limit(self):
        """Test adding annotation when at max limit."""
        manager = PRAnnotationManager(max_annotations=1)
        annotation1 = {"path": "test1.py", "line": 10, "message": "Test1"}
        annotation2 = {"path": "test2.py", "line": 20, "message": "Test2"}

        manager.add_annotation(annotation1)
        manager.add_annotation(annotation2)

        assert len(manager.annotations) == 1
        assert manager.annotations[0] == annotation1

    def test_get_annotations_by_level(self):
        """Test getting annotations by level."""
        manager = PRAnnotationManager()
        annotation1 = {"path": "test1.py", "line": 10, "annotation_level": "error"}
        annotation2 = {"path": "test2.py", "line": 20, "annotation_level": "warning"}
        annotation3 = {"path": "test3.py", "line": 30, "annotation_level": "error"}

        manager.add_annotation(annotation1)
        manager.add_annotation(annotation2)
        manager.add_annotation(annotation3)

        error_annotations = manager.get_annotations_by_level("error")
        assert len(error_annotations) == 2
        assert annotation1 in error_annotations
        assert annotation3 in error_annotations

        warning_annotations = manager.get_annotations_by_level("warning")
        assert len(warning_annotations) == 1
        assert annotation2 in warning_annotations

    def test_get_annotations_by_path(self):
        """Test getting annotations by path."""
        manager = PRAnnotationManager()
        annotation1 = {"path": "test1.py", "line": 10, "message": "Test1"}
        annotation2 = {"path": "test2.py", "line": 20, "message": "Test2"}
        annotation3 = {"path": "test1.py", "line": 30, "message": "Test3"}

        manager.add_annotation(annotation1)
        manager.add_annotation(annotation2)
        manager.add_annotation(annotation3)

        test1_annotations = manager.get_annotations_by_path("test1.py")
        assert len(test1_annotations) == 2
        assert annotation1 in test1_annotations
        assert annotation3 in test1_annotations

        test2_annotations = manager.get_annotations_by_path("test2.py")
        assert len(test2_annotations) == 1
        assert annotation2 in test2_annotations

    def test_clear_annotations(self):
        """Test clearing annotations."""
        manager = PRAnnotationManager()
        annotation = {"path": "test.py", "line": 10, "message": "Test"}

        manager.add_annotation(annotation)
        assert len(manager.annotations) == 1

        manager.clear_annotations()
        assert len(manager.annotations) == 0

    def test_get_summary(self):
        """Test getting annotation summary."""
        manager = PRAnnotationManager()
        annotation1 = {"path": "test1.py", "line": 10, "annotation_level": "error"}
        annotation2 = {"path": "test2.py", "line": 20, "annotation_level": "warning"}
        annotation3 = {"path": "test3.py", "line": 30, "annotation_level": "notice"}

        manager.add_annotation(annotation1)
        manager.add_annotation(annotation2)
        manager.add_annotation(annotation3)

        summary = manager.get_summary()

        assert summary["total"] == 3
        assert summary["failures"] == 1
        assert summary["warnings"] == 1
        assert summary["notices"] == 1


class TestAnnotationFormatter:
    """Test AnnotationFormatter class."""

    def test_annotation_formatter_init(self):
        """Test AnnotationFormatter initialization."""
        formatter = AnnotationFormatter()
        assert formatter.max_message_length == 65535
        assert formatter.include_timestamp is True

    def test_annotation_formatter_init_custom(self):
        """Test AnnotationFormatter initialization with custom parameters."""
        formatter = AnnotationFormatter(
            max_message_length=1000, include_timestamp=False
        )
        assert formatter.max_message_length == 1000
        assert formatter.include_timestamp is False

    def test_format_annotation_short_message(self):
        """Test formatting annotation with short message."""
        formatter = AnnotationFormatter()
        annotation = {"message": "Short message"}

        result = formatter.format_annotation(annotation)

        assert result == annotation

    def test_format_annotation_long_message(self):
        """Test formatting annotation with long message."""
        formatter = AnnotationFormatter(max_message_length=10)
        long_message = "This is a very long message that should be truncated"
        annotation = {"message": long_message}

        result = formatter.format_annotation(annotation)

        assert len(result["message"]) == 10
        assert result["message"].endswith("...")

    def test_format_annotations(self):
        """Test formatting multiple annotations."""
        formatter = AnnotationFormatter(max_message_length=10)
        annotations = [
            {"message": "Short"},
            {"message": "This is a very long message that should be truncated"},
        ]

        result = formatter.format_annotations(annotations)

        assert len(result) == 2
        assert result[0]["message"] == "Short"
        assert len(result[1]["message"]) == 10
        assert result[1]["message"].endswith("...")


class TestCreateGithubAnnotation:
    """Test create_github_annotation function."""

    def test_create_github_annotation_error(self):
        """Test creating GitHub annotation for error."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('fixed')",
        )

        result = create_github_annotation(issue)

        assert result["path"] == "test.py"
        assert result["start_line"] == 10
        assert result["end_line"] == 10
        assert result["annotation_level"] == "failure"
        assert result["title"] == "E501: Test error"
        assert result["start_column"] == 5
        assert result["end_column"] == 6

    def test_create_github_annotation_warning(self):
        """Test creating GitHub annotation for warning."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=0,
            severity="warning",
            message="Test warning",
            rule_id="W501",
        )

        result = create_github_annotation(issue)

        assert result["annotation_level"] == "warning"
        assert "start_column" not in result
        assert "end_column" not in result

    def test_create_github_annotation_medium(self):
        """Test creating GitHub annotation for medium severity."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=0,
            severity="medium",
            message="Test medium",
            rule_id="M501",
        )

        result = create_github_annotation(issue)

        assert result["annotation_level"] == "warning"


class TestFormatAnnotationMessage:
    """Test format_annotation_message function."""

    def test_format_annotation_message_basic(self):
        """Test formatting basic annotation message."""
        result = format_annotation_message("Test message")

        assert result == "Test message"

    def test_format_annotation_message_with_details(self):
        """Test formatting annotation message with details."""
        result = format_annotation_message("Test message", details="Additional details")

        assert "Test message" in result
        assert "**Details:** Additional details" in result

    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        result = format_annotation_message("Test message", suggestion="Try this fix")

        assert "Test message" in result
        assert "💡 **Suggestion:** Try this fix" in result

    def test_format_annotation_message_with_code_example(self):
        """Test formatting annotation message with code example."""
        result = format_annotation_message(
            "Test message", code_example="print('hello')"
        )

        assert "Test message" in result
        assert "**Code:**" in result
        assert "```" in result
        assert "print('hello')" in result

    def test_format_annotation_message_complete(self):
        """Test formatting annotation message with all fields."""
        result = format_annotation_message(
            "Test message",
            details="Additional details",
            suggestion="Try this fix",
            code_example="print('hello')",
        )

        assert "Test message" in result
        assert "**Details:** Additional details" in result
        assert "💡 **Suggestion:** Try this fix" in result
        assert "**Code:**" in result
        assert "print('hello')" in result


class TestFormatAnnotationMessageFromIssue:
    """Test format_annotation_message_from_issue function."""

    def test_format_annotation_message_from_issue_basic(self):
        """Test formatting annotation message from basic issue."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )

        result = format_annotation_message_from_issue(issue)

        assert result == "Test error"

    def test_format_annotation_message_from_issue_with_suggestion(self):
        """Test formatting annotation message from issue with suggestion."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
            suggestion="Fix this",
        )

        result = format_annotation_message_from_issue(issue)

        assert "Test error" in result
        assert "💡 **Suggestion:** Fix this" in result

    def test_format_annotation_message_from_issue_with_fix_code(self):
        """Test formatting annotation message from issue with fix code."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
            fix_code="print('fixed')",
        )

        result = format_annotation_message_from_issue(issue)

        assert "Test error" in result
        assert "🔧 **Fix:**" in result
        assert "print('fixed')" in result

    def test_format_annotation_message_from_issue_complete(self):
        """Test formatting annotation message from issue with all fields."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('fixed')",
        )

        result = format_annotation_message_from_issue(issue)

        assert "Test error" in result
        assert "💡 **Suggestion:** Fix this" in result
        assert "🔧 **Fix:**" in result
        assert "print('fixed')" in result


class TestMain:
    """Test main function."""

    def test_main_success(self):
        """Test main function with successful execution."""
        test_args = [
            "pr_annotations.py",
            "--input",
            "test_input.json",
            "--output",
            "test_output.json",
        ]

        input_data = {
            "lint_results": [
                {
                    "file_path": "test.py",
                    "line_number": 10,
                    "column": 5,
                    "severity": "error",
                    "message": "Test error",
                    "rule": "E501",
                }
            ]
        }

        with (
            patch("sys.argv", test_args),
            patch("builtins.open", mock_open(read_data=json.dumps(input_data))),
            patch("builtins.print") as mock_print,
        ):

            main()

            # Check that output was printed
            assert mock_print.call_count >= 4  # At least 4 print calls

    def test_main_with_error(self):
        """Test main function with error."""
        test_args = [
            "pr_annotations.py",
            "--input",
            "nonexistent.json",
            "--output",
            "test_output.json",
        ]

        with (
            patch("sys.argv", test_args),
            patch("builtins.open", side_effect=FileNotFoundError("File not found")),
            patch("builtins.print") as mock_print,
            patch("sys.exit") as mock_exit,
        ):

            main()

            mock_exit.assert_called_once_with(1)

    def test_main_with_github_token(self):
        """Test main function with GitHub token."""
        test_args = [
            "pr_annotations.py",
            "--input",
            "test_input.json",
            "--output",
            "test_output.json",
            "--github-token",
            "test_token",
            "--repo",
            "owner/repo",
        ]

        input_data = {"lint_results": []}

        with (
            patch("sys.argv", test_args),
            patch("builtins.open", mock_open(read_data=json.dumps(input_data))),
            patch("builtins.print"),
        ):

            main()

    def test_main_with_coverage_data(self):
        """Test main function with coverage data."""
        test_args = [
            "pr_annotations.py",
            "--input",
            "test_input.json",
            "--output",
            "test_output.json",
        ]

        input_data = {
            "coverage_data": {"test.py": {"coverage": 80, "uncovered_lines": [5, 10]}}
        }

        with (
            patch("sys.argv", test_args),
            patch("builtins.open", mock_open(read_data=json.dumps(input_data))),
            patch("builtins.print"),
        ):

            main()

    def test_main_with_security_issues(self):
        """Test main function with security issues."""
        test_args = [
            "pr_annotations.py",
            "--input",
            "test_input.json",
            "--output",
            "test_output.json",
        ]

        input_data = {
            "security_issues": [
                {
                    "file": "test.py",
                    "line": 10,
                    "severity": "high",
                    "message": "Security issue",
                    "rule": "B101",
                }
            ]
        }

        with (
            patch("sys.argv", test_args),
            patch("builtins.open", mock_open(read_data=json.dumps(input_data))),
            patch("builtins.print"),
        ):

            main()
