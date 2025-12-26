"""Comprehensive tests for pr_annotations.py with fixes for existing issues."""

import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import pytest
from src.ai_guard.pr_annotations import (
    AnnotationLevel,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
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
)


class TestAnnotationLevel:
    """Test AnnotationLevel enum."""

    def test_annotation_level_values(self):
        """Test annotation level enum values."""
        assert AnnotationLevel.NOTICE.value == "notice"
        assert AnnotationLevel.WARNING.value == "warning"
        assert AnnotationLevel.ERROR.value == "error"


class TestCodeIssue:
    """Test CodeIssue dataclass."""

    def test_code_issue_creation(self):
        """Test creating CodeIssue with all fields."""
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

        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error"
        assert issue.rule_id == "E501"
        assert issue.suggestion == "Fix this"
        assert issue.fix_code == "print('fixed')"

    def test_code_issue_minimal(self):
        """Test creating CodeIssue with minimal fields."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=1,
            column=1,
            severity="error",
            message="Syntax error",
            rule_id="E001",
        )

        assert issue.file_path == "test.py"
        assert issue.line_number == 1
        assert issue.column == 1
        assert issue.severity == "error"
        assert issue.message == "Syntax error"
        assert issue.rule_id == "E001"
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
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('fixed')",
        )

        result = issue.to_dict()

        expected = {
            "file_path": "test.py",
            "line_number": 10,
            "column": 5,
            "severity": "error",
            "message": "Test error",
            "rule_id": "E501",
            "suggestion": "Fix this",
            "fix_code": "print('fixed')",
        }

        assert result == expected


class TestPRAnnotation:
    """Test PRAnnotation dataclass."""

    def test_pr_annotation_creation(self):
        """Test creating PRAnnotation with all fields."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test message",
            annotation_level="error",
            title="Test Title",
            raw_details="Details",
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=10,
        )

        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "error"
        assert annotation.title == "Test Title"
        assert annotation.raw_details == "Details"
        assert annotation.start_line == 10
        assert annotation.end_line == 15
        assert annotation.start_column == 5
        assert annotation.end_column == 10

    def test_pr_annotation_minimal(self):
        """Test creating PRAnnotation with minimal fields."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test message",
            annotation_level="error",
        )

        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "error"
        assert annotation.title is None
        assert annotation.raw_details is None
        assert annotation.start_line is None
        assert annotation.end_line is None
        assert annotation.start_column is None
        assert annotation.end_column is None


class TestPRReviewSummary:
    """Test PRReviewSummary dataclass."""

    def test_pr_review_summary_creation(self):
        """Test creating PRReviewSummary."""
        annotations = [PRAnnotation("test.py", 10, "Test", "error")]
        suggestions = ["Fix this"]

        summary = PRReviewSummary(
            overall_status="changes_requested",
            summary="Test summary",
            annotations=annotations,
            suggestions=suggestions,
            quality_score=0.8,
            coverage_info={"test.py": {"coverage": 80}},
            security_issues=["Security issue"],
        )

        assert summary.overall_status == "changes_requested"
        assert summary.summary == "Test summary"
        assert summary.annotations == annotations
        assert summary.suggestions == suggestions
        assert summary.quality_score == 0.8
        assert summary.coverage_info == {"test.py": {"coverage": 80}}
        assert summary.security_issues == ["Security issue"]


class TestPRAnnotator:
    """Test PRAnnotator class."""

    def test_pr_annotator_init(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()
        assert annotator.github_token is None
        assert annotator.repo is None
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_init_with_params(self):
        """Test PRAnnotator initialization with parameters."""
        annotator = PRAnnotator(github_token="token", repo="owner/repo")
        assert annotator.github_token == "token"
        assert annotator.repo == "owner/repo"
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_init_with_env(self):
        """Test PRAnnotator initialization with environment variables."""
        with patch.dict(
            os.environ, {"GITHUB_TOKEN": "env_token", "GITHUB_REPOSITORY": "env/repo"}
        ):
            annotator = PRAnnotator()
            assert annotator.github_token == "env_token"
            assert annotator.repo == "env/repo"

    def test_add_issue(self):
        """Test adding an issue."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.issues[0] == issue

    def test_issue_to_annotation_error(self):
        """Test converting error issue to annotation."""
        annotator = PRAnnotator()
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

        annotation = annotator._issue_to_annotation(issue)

        assert annotation is not None
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.annotation_level == "failure"
        assert annotation.title == "E501: Test error"
        assert "Test error" in annotation.message
        assert "💡 **Suggestion:** Fix this" in annotation.message
        assert "🔧 **Fix:**" in annotation.message
        assert "print('fixed')" in annotation.message

    def test_issue_to_annotation_warning(self):
        """Test converting warning issue to annotation."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W501",
        )

        annotation = annotator._issue_to_annotation(issue)

        assert annotation is not None
        assert annotation.annotation_level == "warning"
        assert annotation.title == "W501: Test warning"

    def test_issue_to_annotation_info(self):
        """Test converting info issue to annotation."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="info",
            message="Test info",
            rule_id="I501",
        )

        annotation = annotator._issue_to_annotation(issue)

        assert annotation is not None
        assert annotation.annotation_level == "notice"
        assert annotation.title == "I501: Test info"

    def test_add_lint_issues(self):
        """Test adding lint issues."""
        annotator = PRAnnotator()
        lint_results = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "column": 5,
                "severity": "error",
                "message": "Test error",
                "rule": "E501",
            }
        ]

        annotator.add_lint_issues(lint_results)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1

    def test_generate_lint_suggestion(self):
        """Test generating lint suggestions."""
        annotator = PRAnnotator()

        # Test E501 suggestion
        result = {"rule": "E501"}
        suggestion = annotator._generate_lint_suggestion(result)
        assert "breaking this long line" in suggestion

        # Test F401 suggestion
        result = {"rule": "F401"}
        suggestion = annotator._generate_lint_suggestion(result)
        assert "Remove unused import" in suggestion

        # Test unknown rule
        result = {"rule": "UNKNOWN"}
        suggestion = annotator._generate_lint_suggestion(result)
        assert suggestion is None

    def test_add_coverage_annotation_low_coverage(self):
        """Test adding coverage annotation for low coverage."""
        annotator = PRAnnotator()
        coverage_data = {"coverage": 70, "uncovered_lines": [5, 10, 15]}

        annotator.add_coverage_annotation("test.py", coverage_data)

        assert len(annotator.annotations) == 4  # 1 warning + 3 uncovered lines
        assert any(
            "Low Coverage Warning" in ann.message for ann in annotator.annotations
        )

    def test_add_coverage_annotation_high_coverage(self):
        """Test adding coverage annotation for high coverage."""
        annotator = PRAnnotator()
        coverage_data = {"coverage": 90, "uncovered_lines": [5]}

        annotator.add_coverage_annotation("test.py", coverage_data)

        assert len(annotator.annotations) == 1  # Only uncovered line
        assert not any(
            "Low Coverage Warning" in ann.message for ann in annotator.annotations
        )

    def test_add_coverage_annotation_empty(self):
        """Test adding coverage annotation with empty data."""
        annotator = PRAnnotator()

        annotator.add_coverage_annotation("test.py", {})

        assert len(annotator.annotations) == 0

    def test_add_security_annotation(self):
        """Test adding security annotations."""
        annotator = PRAnnotator()
        security_issues = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "high",
                "message": "Hardcoded password",
                "rule": "B101",
            },
            {
                "file": "test.py",
                "line": 20,
                "severity": "medium",
                "message": "Weak encryption",
                "rule": "B102",
            },
        ]

        annotator.add_security_annotation(security_issues)

        assert len(annotator.annotations) == 2
        assert any(
            "Security Issue (HIGH)" in ann.message for ann in annotator.annotations
        )
        assert any(
            "Security Issue (MEDIUM)" in ann.message for ann in annotator.annotations
        )

    def test_generate_review_summary_no_issues(self):
        """Test generating review summary with no issues."""
        annotator = PRAnnotator()
        summary = annotator.generate_review_summary()

        assert summary.overall_status == "approved"
        assert summary.quality_score == 1.0
        assert "All quality checks passed" in summary.summary

    def test_generate_review_summary_with_errors(self):
        """Test generating review summary with errors."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)
        summary = annotator.generate_review_summary()

        assert summary.overall_status == "changes_requested"
        assert summary.quality_score == 0.0  # 1 error: 1.0 - (1*0.0)/1 = 0.0
        assert "1 error" in summary.summary

    def test_generate_review_summary_with_warnings(self):
        """Test generating review summary with warnings."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W501",
        )
        annotator.add_issue(issue)
        summary = annotator.generate_review_summary()

        assert summary.overall_status == "commented"
        assert summary.quality_score == 0.5  # 1 warning: 1.0 - (1*0.5)/1 = 0.5
        assert "1 warning" in summary.summary

    def test_generate_review_summary_many_warnings(self):
        """Test generating review summary with many warnings."""
        annotator = PRAnnotator()
        for i in range(10):
            issue = CodeIssue(
                file_path="test.py",
                line_number=i,
                column=5,
                severity="warning",
                message="Test warning",
                rule_id="W501",
            )
            annotator.add_issue(issue)

        summary = annotator.generate_review_summary()

        assert summary.overall_status == "changes_requested"
        assert summary.quality_score == 0.5

    def test_generate_suggestions(self):
        """Test generating suggestions."""
        annotator = PRAnnotator()

        # Add E501 error
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Line too long",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        suggestions = annotator._generate_suggestions()

        assert any("line length formatter" in suggestion for suggestion in suggestions)

    def test_create_github_annotations(self):
        """Test creating GitHub annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        github_annotations = annotator.create_github_annotations()

        assert len(github_annotations) == 1
        assert github_annotations[0]["path"] == "test.py"
        assert github_annotations[0]["start_line"] == 10
        assert github_annotations[0]["annotation_level"] == "failure"

    def test_create_review_comment(self):
        """Test creating review comment."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        summary = annotator.generate_review_summary()
        comment = annotator.create_review_comment(summary)

        assert "AI-Guard Quality Review" in comment
        assert "Status:" in comment
        assert "Quality Score:" in comment
        assert "Summary" in comment
        assert "Issues Found" in comment

    def test_save_annotations(self):
        """Test saving annotations to file."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with patch("builtins.open", mock_open()) as mock_file:
            annotator.save_annotations("test_annotations.json")

            mock_file.assert_called_once_with(
                "test_annotations.json", "w", encoding="utf-8"
            )

            # Check that JSON was written
            written_data = mock_file().write.call_args[0][0]
            annotations_data = json.loads(written_data)

            assert "annotations" in annotations_data
            assert "issues" in annotations_data
            assert "summary" in annotations_data

    def test_generate_annotations_summary(self):
        """Test generating annotations summary."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        summary = annotator.generate_annotations_summary()

        assert "1 issues found" in summary
        assert "1 error" in summary

    def test_write_annotations_to_file_stdout(self):
        """Test writing annotations to stdout."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with patch("builtins.print") as mock_print:
            annotator.write_annotations_to_file("-")

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "AI-Guard Quality Review" in call_args

    def test_write_annotations_to_file_path(self):
        """Test writing annotations to file path."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with patch("builtins.open", mock_open()) as mock_file:
            annotator.write_annotations_to_file("test.json")

            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")

    def test_clear_annotations(self):
        """Test clearing annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        assert len(annotator.annotations) == 1
        assert len(annotator.issues) == 1

        annotator.clear_annotations()

        assert len(annotator.annotations) == 0
        assert len(annotator.issues) == 0

    def test_annotation_to_dict(self):
        """Test converting annotation to dictionary."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test message",
            annotation_level="error",
            title="Test Title",
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=10,
        )

        result = annotator._annotation_to_dict(annotation)

        expected = {
            "file_path": "test.py",
            "line_number": 10,
            "message": "Test message",
            "annotation_level": "error",
            "title": "Test Title",
            "start_line": 10,
            "end_line": 15,
            "start_column": 5,
            "end_column": 10,
        }

        assert result == expected

    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        annotator = PRAnnotator()
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

        result = annotator._issue_to_dict(issue)

        expected = {
            "file_path": "test.py",
            "line_number": 10,
            "column": 5,
            "severity": "error",
            "message": "Test error",
            "rule_id": "E501",
            "suggestion": "Fix this",
            "fix_code": "print('fixed')",
        }

        assert result == expected
