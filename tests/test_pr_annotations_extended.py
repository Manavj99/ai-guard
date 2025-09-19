"""Extended tests for PR annotations to improve coverage."""

import pytest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from src.ai_guard.pr_annotations import (
    AnnotationLevel,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
    create_pr_annotations,
    parse_lint_output,
    parse_bandit_output,
    parse_mypy_output,
    format_annotation_message,
    write_annotations_file,
    AnnotationFormatter,
    PRAnnotationManager,
    create_pr_annotation,
    get_annotation_level,
    create_quality_gate_annotation,
    create_coverage_annotation,
    create_security_annotation,
    create_performance_annotation,
    create_test_annotation,
    create_github_annotation,
    format_annotation_message_from_issue
)


class TestAnnotationLevelExtended:
    """Extended tests for AnnotationLevel enum."""

    def test_annotation_level_values(self):
        """Test AnnotationLevel enum values."""
        assert AnnotationLevel.NOTICE.value == "notice"
        assert AnnotationLevel.WARNING.value == "warning"
        assert AnnotationLevel.ERROR.value == "error"

    def test_annotation_level_membership(self):
        """Test AnnotationLevel membership."""
        assert AnnotationLevel.NOTICE in AnnotationLevel
        assert AnnotationLevel.WARNING in AnnotationLevel
        assert AnnotationLevel.ERROR in AnnotationLevel


class TestCodeIssueExtended:
    """Extended tests for CodeIssue dataclass."""

    def test_code_issue_creation(self):
        """Test creating CodeIssue object."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            rule_id="E123",
            suggestion="Fix this issue",
            fix_code="corrected_code()"
        )
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.rule_id == "E123"
        assert issue.suggestion == "Fix this issue"
        assert issue.fix_code == "corrected_code()"

    def test_code_issue_minimal(self):
        """Test creating CodeIssue with minimal data."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=1,
            column=0,
            severity="warning",
            message="Test warning",
            rule_id="W001"
        )
        assert issue.file_path == "test.py"
        assert issue.suggestion is None
        assert issue.fix_code is None

    def test_code_issue_to_dict(self):
        """Test converting CodeIssue to dictionary."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E123",
            suggestion="Fix it",
            fix_code="fixed_code()"
        )
        
        issue_dict = issue.to_dict()
        
        assert isinstance(issue_dict, dict)
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 10
        assert issue_dict["column"] == 5
        assert issue_dict["severity"] == "error"
        assert issue_dict["message"] == "Test error"
        assert issue_dict["rule_id"] == "E123"
        assert issue_dict["suggestion"] == "Fix it"
        assert issue_dict["fix_code"] == "fixed_code()"


class TestPRAnnotationExtended:
    """Extended tests for PRAnnotation dataclass."""

    def test_pr_annotation_creation(self):
        """Test creating PRAnnotation object."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test annotation message",
            annotation_level="error",
            title="Test Title",
            raw_details="Raw details",
            start_line=10,
            end_line=10,
            start_column=1,
            end_column=5
        )
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test annotation message"
        assert annotation.annotation_level == "error"
        assert annotation.title == "Test Title"
        assert annotation.raw_details == "Raw details"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 1
        assert annotation.end_column == 5

    def test_pr_annotation_minimal(self):
        """Test creating PRAnnotation with minimal data."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=1,
            message="Minimal annotation",
            annotation_level="notice"
        )
        assert annotation.file_path == "test.py"
        assert annotation.title is None
        assert annotation.raw_details is None
        assert annotation.start_line is None
        assert annotation.end_line is None
        assert annotation.start_column is None
        assert annotation.end_column is None


class TestPRReviewSummaryExtended:
    """Extended tests for PRReviewSummary dataclass."""

    def test_pr_review_summary_creation(self):
        """Test creating PRReviewSummary object."""
        annotations = [
            PRAnnotation("test.py", 1, "Test", "notice")
        ]
        suggestions = ["Test suggestion"]
        
        summary = PRReviewSummary(
            overall_status="approved",
            summary="All checks passed",
            annotations=annotations,
            suggestions=suggestions,
            quality_score=0.95,
            coverage_info={"coverage": 85.0},
            security_issues=["No issues found"]
        )
        
        assert summary.overall_status == "approved"
        assert summary.summary == "All checks passed"
        assert len(summary.annotations) == 1
        assert len(summary.suggestions) == 1
        assert summary.quality_score == 0.95
        assert summary.coverage_info["coverage"] == 85.0
        assert summary.security_issues[0] == "No issues found"


class TestPRAnnotatorExtended:
    """Extended tests for PRAnnotator class."""

    def test_pr_annotator_init(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_init_with_params(self):
        """Test PRAnnotator initialization with parameters."""
        annotator = PRAnnotator(github_token="token", repo="owner/repo")
        assert annotator.github_token == "token"
        assert annotator.repo == "owner/repo"

    def test_add_issue(self):
        """Test adding a code issue."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E123"
        )
        
        annotator.add_issue(issue)
        
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1

    def test_add_lint_issues(self):
        """Test adding lint issues."""
        annotator = PRAnnotator()
        lint_results = [
            {
                "file": "test.py",
                "line": 10,
                "column": 5,
                "severity": "error",
                "message": "Test error",
                "rule": "E123"
            }
        ]
        
        annotator.add_lint_issues(lint_results)
        
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1

    def test_add_coverage_annotation(self):
        """Test adding coverage annotation."""
        annotator = PRAnnotator()
        coverage_data = {
            "coverage": 75.0,
            "uncovered_lines": [10, 15, 20]
        }
        
        annotator.add_coverage_annotation("test.py", coverage_data)
        
        assert len(annotator.annotations) >= 1

    def test_add_security_annotation(self):
        """Test adding security annotation."""
        annotator = PRAnnotator()
        security_issues = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "high",
                "message": "Security vulnerability",
                "rule": "B001"
            }
        ]
        
        annotator.add_security_annotation(security_issues)
        
        assert len(annotator.annotations) == 1

    def test_generate_review_summary(self):
        """Test generating review summary."""
        annotator = PRAnnotator()
        
        # Add some issues
        issue1 = CodeIssue("test.py", 10, 5, "error", "Error", "E123")
        issue2 = CodeIssue("test.py", 15, 3, "warning", "Warning", "W001")
        annotator.add_issue(issue1)
        annotator.add_issue(issue2)
        
        summary = annotator.generate_review_summary()
        
        assert isinstance(summary, PRReviewSummary)
        assert summary.overall_status in ["approved", "changes_requested", "commented"]
        assert summary.quality_score >= 0.0
        assert summary.quality_score <= 1.0

    def test_create_github_annotations(self):
        """Test creating GitHub annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test error", "E123")
        annotator.add_issue(issue)
        
        github_annotations = annotator.create_github_annotations()
        
        assert isinstance(github_annotations, list)
        assert len(github_annotations) == 1
        assert github_annotations[0]["path"] == "test.py"

    def test_create_review_comment(self):
        """Test creating review comment."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test error", "E123")
        annotator.add_issue(issue)
        
        summary = annotator.generate_review_summary()
        comment = annotator.create_review_comment(summary)
        
        assert isinstance(comment, str)
        assert "AI-Guard Quality Review" in comment

    def test_save_annotations(self):
        """Test saving annotations to file."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test error", "E123")
        annotator.add_issue(issue)
        
        with patch('builtins.open', mock_open()) as mock_file:
            annotator.save_annotations("test_output.json")
            mock_file.assert_called_once_with("test_output.json", "w", encoding="utf-8")

    def test_clear_annotations(self):
        """Test clearing annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test error", "E123")
        annotator.add_issue(issue)
        
        annotator.clear_annotations()
        
        assert len(annotator.annotations) == 0
        assert len(annotator.issues) == 0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_pr_annotation(self):
        """Test create_pr_annotation function."""
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="error",
            message="Test message",
            title="Test Title"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "failure"
        assert annotation["message"] == "Test message"
        assert annotation["title"] == "Test Title"

    def test_get_annotation_level(self):
        """Test get_annotation_level function."""
        assert get_annotation_level("error") == "failure"
        assert get_annotation_level("warning") == "warning"
        assert get_annotation_level("info") == "notice"
        assert get_annotation_level("unknown") == "notice"

    def test_create_quality_gate_annotation(self):
        """Test create_quality_gate_annotation function."""
        annotation = create_quality_gate_annotation(
            path="test.py",
            line=10,
            gate_name="coverage",
            status="passed",
            message="Coverage threshold met"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "notice"
        assert "coverage" in annotation["message"]

    def test_create_coverage_annotation(self):
        """Test create_coverage_annotation function."""
        annotation = create_coverage_annotation(
            path="test.py",
            coverage_percent=85.0,
            threshold=80.0
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 1
        assert annotation["annotation_level"] == "notice"
        assert "85.0%" in annotation["message"]

    def test_create_security_annotation(self):
        """Test create_security_annotation function."""
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

    def test_create_performance_annotation(self):
        """Test create_performance_annotation function."""
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

    def test_create_test_annotation(self):
        """Test create_test_annotation function."""
        annotation = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="failed",
            duration=0.5,
            error_message="AssertionError"
        )
        
        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "failure"
        assert "test_function" in annotation["message"]

    def test_create_github_annotation(self):
        """Test create_github_annotation function."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E123"
        )
        
        annotation = create_github_annotation(issue)
        
        assert annotation["path"] == "test.py"
        assert annotation["start_line"] == 10
        assert annotation["end_line"] == 10
        assert annotation["annotation_level"] == "failure"

    def test_format_annotation_message(self):
        """Test format_annotation_message function."""
        message = format_annotation_message(
            message="Test message",
            details="Additional details",
            suggestion="Try this fix",
            code_example="fixed_code()"
        )
        
        assert "Test message" in message
        assert "Additional details" in message
        assert "Try this fix" in message
        assert "fixed_code()" in message

    def test_format_annotation_message_from_issue(self):
        """Test format_annotation_message_from_issue function."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E123",
            suggestion="Fix this",
            fix_code="corrected_code()"
        )
        
        message = format_annotation_message_from_issue(issue)
        
        assert "Test error" in message
        assert "Fix this" in message
        assert "corrected_code()" in message


class TestParsingFunctions:
    """Test parsing functions."""

    def test_parse_lint_output(self):
        """Test parsing lint output."""
        lint_output = "test.py:10:5: E123: Test error message"
        issues = parse_lint_output(lint_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].severity == "error"

    def test_parse_lint_output_empty(self):
        """Test parsing empty lint output."""
        issues = parse_lint_output("")
        assert len(issues) == 0

    def test_parse_lint_output_none(self):
        """Test parsing None lint output."""
        issues = parse_lint_output(None)
        assert len(issues) == 0

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = "test.py:10: error: Incompatible types"
        issues = parse_mypy_output(mypy_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].severity == "error"
        assert issues[0].rule_id == "mypy"

    def test_parse_bandit_output(self):
        """Test parsing bandit output."""
        bandit_output = "test.py:10:1: B001: Test security issue"
        issues = parse_bandit_output(bandit_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].severity == "medium"
        assert issues[0].rule_id == "B001"


class TestPRAnnotationManager:
    """Test PRAnnotationManager class."""

    def test_manager_init(self):
        """Test PRAnnotationManager initialization."""
        manager = PRAnnotationManager(max_annotations=10)
        assert manager.max_annotations == 10
        assert manager.annotations == []

    def test_add_annotation(self):
        """Test adding annotation."""
        manager = PRAnnotationManager(max_annotations=5)
        annotation = {"path": "test.py", "line": 10, "message": "Test"}
        
        manager.add_annotation(annotation)
        
        assert len(manager.annotations) == 1

    def test_add_annotation_max_limit(self):
        """Test adding annotation with max limit."""
        manager = PRAnnotationManager(max_annotations=2)
        
        for i in range(5):
            manager.add_annotation({"path": f"test{i}.py", "line": i, "message": f"Test {i}"})
        
        assert len(manager.annotations) == 2

    def test_get_annotations_by_level(self):
        """Test getting annotations by level."""
        manager = PRAnnotationManager()
        manager.add_annotation({"path": "test.py", "line": 10, "annotation_level": "error"})
        manager.add_annotation({"path": "test.py", "line": 15, "annotation_level": "warning"})
        
        error_annotations = manager.get_annotations_by_level("error")
        warning_annotations = manager.get_annotations_by_level("warning")
        
        assert len(error_annotations) == 1
        assert len(warning_annotations) == 1

    def test_get_annotations_by_path(self):
        """Test getting annotations by path."""
        manager = PRAnnotationManager()
        manager.add_annotation({"path": "test1.py", "line": 10, "message": "Test 1"})
        manager.add_annotation({"path": "test2.py", "line": 15, "message": "Test 2"})
        
        test1_annotations = manager.get_annotations_by_path("test1.py")
        test2_annotations = manager.get_annotations_by_path("test2.py")
        
        assert len(test1_annotations) == 1
        assert len(test2_annotations) == 1

    def test_clear_annotations(self):
        """Test clearing annotations."""
        manager = PRAnnotationManager()
        manager.add_annotation({"path": "test.py", "line": 10, "message": "Test"})
        
        manager.clear_annotations()
        
        assert len(manager.annotations) == 0

    def test_get_summary(self):
        """Test getting annotation summary."""
        manager = PRAnnotationManager()
        manager.add_annotation({"path": "test.py", "line": 10, "annotation_level": "failure"})
        manager.add_annotation({"path": "test.py", "line": 15, "annotation_level": "warning"})
        
        summary = manager.get_summary()
        
        assert summary["total"] == 2
        assert summary["failures"] == 1
        assert summary["warnings"] == 1


class TestAnnotationFormatter:
    """Test AnnotationFormatter class."""

    def test_formatter_init(self):
        """Test AnnotationFormatter initialization."""
        formatter = AnnotationFormatter(max_message_length=1000, include_timestamp=True)
        assert formatter.max_message_length == 1000
        assert formatter.include_timestamp is True

    def test_format_annotation(self):
        """Test formatting annotation."""
        formatter = AnnotationFormatter(max_message_length=100)
        annotation = {"message": "Short message"}
        
        formatted = formatter.format_annotation(annotation)
        
        assert formatted["message"] == "Short message"

    def test_format_annotation_long_message(self):
        """Test formatting annotation with long message."""
        formatter = AnnotationFormatter(max_message_length=10)
        annotation = {"message": "This is a very long message that should be truncated"}
        
        formatted = formatter.format_annotation(annotation)
        
        assert len(formatted["message"]) <= 10
        assert formatted["message"].endswith("...")

    def test_format_annotations(self):
        """Test formatting multiple annotations."""
        formatter = AnnotationFormatter()
        annotations = [
            {"message": "Message 1"},
            {"message": "Message 2"}
        ]
        
        formatted = formatter.format_annotations(annotations)
        
        assert len(formatted) == 2
        assert formatted[0]["message"] == "Message 1"
        assert formatted[1]["message"] == "Message 2"


class TestCreatePRAnnotations:
    """Test create_pr_annotations function."""

    def test_create_pr_annotations_with_lint(self):
        """Test creating PR annotations with lint output."""
        lint_output = "test.py:10:5: E123: Test error"
        
        annotations = create_pr_annotations(lint_output=lint_output)
        
        assert len(annotations) == 1
        assert annotations[0].file_path == "test.py"

    def test_create_pr_annotations_with_bandit(self):
        """Test creating PR annotations with bandit output."""
        bandit_output = "test.py:10:1: B001: Security issue"
        
        annotations = create_pr_annotations(bandit_output=bandit_output)
        
        assert len(annotations) == 1

    def test_create_pr_annotations_with_mypy(self):
        """Test creating PR annotations with mypy output."""
        mypy_output = "test.py:10: error: Type error"
        
        annotations = create_pr_annotations(mypy_output=mypy_output)
        
        assert len(annotations) == 1

    def test_create_pr_annotations_with_coverage(self):
        """Test creating PR annotations with coverage output."""
        coverage_output = "test.py 100 75 75% 10-15"
        
        annotations = create_pr_annotations(coverage_output=coverage_output)
        
        assert len(annotations) >= 1

    def test_create_pr_annotations_with_output_file(self):
        """Test creating PR annotations with output file."""
        lint_output = "test.py:10:5: E123: Test error"
        
        with patch('builtins.open', mock_open()) as mock_file:
            annotations = create_pr_annotations(
                lint_output=lint_output,
                output_file="test_output.json"
            )
            mock_file.assert_called_once()


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""

    def test_write_annotations_file_success(self):
        """Test writing annotations file successfully."""
        annotations = [
            {"path": "test.py", "line": 10, "message": "Test"}
        ]
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_annotations_file(annotations, "test.json")
            
            assert result is True
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")

    def test_write_annotations_file_failure(self):
        """Test writing annotations file with failure."""
        annotations = [{"path": "test.py", "line": 10, "message": "Test"}]
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = write_annotations_file(annotations, "test.json")
            
            assert result is False
