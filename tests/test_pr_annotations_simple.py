"""Simple tests for pr_annotations.py to achieve 80% coverage."""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from src.ai_guard.pr_annotations import (
    PRAnnotator,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    AnnotationLevel,
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

    def test_level_values(self):
        """Test annotation level values."""
        assert AnnotationLevel.NOTICE.value == "notice"
        assert AnnotationLevel.WARNING.value == "warning"
        assert AnnotationLevel.ERROR.value == "error"


class TestCodeIssue:
    """Test CodeIssue class."""

    def test_initialization(self):
        """Test code issue initialization."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "warning"
        assert issue.message == "Test issue"
        assert issue.rule_id == "E501"
        assert issue.suggestion is None
        assert issue.fix_code is None

    def test_initialization_with_optional_fields(self):
        """Test code issue initialization with optional fields."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test issue",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('hello')",
        )
        assert issue.suggestion == "Fix this"
        assert issue.fix_code == "print('hello')"

    def test_to_dict(self):
        """Test converting to dictionary."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('hello')",
        )
        issue_dict = issue.to_dict()
        assert isinstance(issue_dict, dict)
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 10
        assert issue_dict["column"] == 5
        assert issue_dict["severity"] == "warning"
        assert issue_dict["message"] == "Test issue"
        assert issue_dict["rule_id"] == "E501"
        assert issue_dict["suggestion"] == "Fix this"
        assert issue_dict["fix_code"] == "print('hello')"


class TestPRAnnotation:
    """Test PRAnnotation class."""

    def test_initialization(self):
        """Test PR annotation initialization."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test annotation",
            annotation_level="warning",
        )
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test annotation"
        assert annotation.annotation_level == "warning"
        assert annotation.title is None
        assert annotation.raw_details is None
        assert annotation.start_line is None
        assert annotation.end_line is None
        assert annotation.start_column is None
        assert annotation.end_column is None

    def test_initialization_with_optional_fields(self):
        """Test PR annotation initialization with optional fields."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test annotation",
            annotation_level="warning",
            title="Test Title",
            raw_details="Details",
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=10,
        )
        assert annotation.title == "Test Title"
        assert annotation.raw_details == "Details"
        assert annotation.start_line == 10
        assert annotation.end_line == 15
        assert annotation.start_column == 5
        assert annotation.end_column == 10


class TestPRReviewSummary:
    """Test PRReviewSummary class."""

    def test_initialization(self):
        """Test review summary initialization."""
        summary = PRReviewSummary(
            overall_status="approved",
            summary="All good",
            annotations=[],
            suggestions=[],
            quality_score=0.9,
        )
        assert summary.overall_status == "approved"
        assert summary.summary == "All good"
        assert summary.annotations == []
        assert summary.suggestions == []
        assert summary.quality_score == 0.9
        assert summary.coverage_info is None
        assert summary.security_issues is None

    def test_initialization_with_optional_fields(self):
        """Test review summary initialization with optional fields."""
        summary = PRReviewSummary(
            overall_status="changes_requested",
            summary="Issues found",
            annotations=[],
            suggestions=[],
            quality_score=0.5,
            coverage_info={"coverage": 80.0},
            security_issues=["SQL injection"],
        )
        assert summary.coverage_info == {"coverage": 80.0}
        assert summary.security_issues == ["SQL injection"]


class TestPRAnnotator:
    """Test PRAnnotator class."""

    def test_initialization(self):
        """Test annotator initialization."""
        annotator = PRAnnotator()
        assert annotator.annotations == []
        assert annotator.issues == []
        assert annotator.github_token is None
        assert annotator.repo is None

    def test_initialization_with_params(self):
        """Test annotator initialization with parameters."""
        annotator = PRAnnotator(github_token="test_token", repo="owner/repo")
        assert annotator.github_token == "test_token"
        assert annotator.repo == "owner/repo"

    def test_initialization_with_env_vars(self):
        """Test annotator initialization with environment variables."""
        with patch.dict(
            os.environ, {"GITHUB_TOKEN": "env_token", "GITHUB_REPOSITORY": "env/repo"}
        ):
            annotator = PRAnnotator()
            assert annotator.github_token == "env_token"
            assert annotator.repo == "env/repo"

    def test_add_issue(self):
        """Test adding issue."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.issues[0] == issue

    def test_add_issue_with_suggestion(self):
        """Test adding issue with suggestion."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test issue",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('hello')",
        )
        annotator.add_issue(issue)
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        annotation = annotator.annotations[0]
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.annotation_level == "failure"
        assert "Test issue" in annotation.message
        assert "Fix this" in annotation.message
        assert "print('hello')" in annotation.message

    def test_add_lint_issues(self):
        """Test adding lint issues."""
        annotator = PRAnnotator()
        lint_results = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "column": 5,
                "severity": "warning",
                "message": "Test issue",
                "rule_id": "E501",
            }
        ]
        annotator.add_lint_issues(lint_results)
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1

    def test_add_lint_issues_with_alternative_keys(self):
        """Test adding lint issues with alternative keys."""
        annotator = PRAnnotator()
        lint_results = [
            {
                "file": "test.py",
                "line": 10,
                "column": 5,
                "severity": "warning",
                "message": "Test issue",
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

    def test_add_coverage_annotation(self):
        """Test adding coverage annotation."""
        annotator = PRAnnotator()
        coverage_data = {"coverage": 70.0, "uncovered_lines": [10, 20, 30]}
        annotator.add_coverage_annotation("test.py", coverage_data)
        assert len(annotator.annotations) == 4  # 1 warning + 3 uncovered lines

    def test_add_coverage_annotation_high_coverage(self):
        """Test adding coverage annotation with high coverage."""
        annotator = PRAnnotator()
        coverage_data = {"coverage": 90.0, "uncovered_lines": [10, 20]}
        annotator.add_coverage_annotation("test.py", coverage_data)
        assert len(annotator.annotations) == 2  # Only uncovered lines

    def test_add_coverage_annotation_empty_data(self):
        """Test adding coverage annotation with empty data."""
        annotator = PRAnnotator()
        annotator.add_coverage_annotation("test.py", {})
        assert len(annotator.annotations) == 0

    def test_add_security_annotation(self):
        """Test adding security annotation."""
        annotator = PRAnnotator()
        security_issues = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "high",
                "message": "SQL injection",
                "rule": "B608",
            }
        ]
        annotator.add_security_annotation(security_issues)
        assert len(annotator.annotations) == 1
        annotation = annotator.annotations[0]
        assert annotation.annotation_level == "failure"
        assert "SQL injection" in annotation.message

    def test_add_security_annotation_medium_severity(self):
        """Test adding security annotation with medium severity."""
        annotator = PRAnnotator()
        security_issues = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "medium",
                "message": "Security issue",
                "rule": "B101",
            }
        ]
        annotator.add_security_annotation(security_issues)
        assert len(annotator.annotations) == 1
        annotation = annotator.annotations[0]
        assert annotation.annotation_level == "warning"

    def test_generate_review_summary_no_issues(self):
        """Test generating review summary with no issues."""
        annotator = PRAnnotator()
        summary = annotator.generate_review_summary()
        assert summary.overall_status == "approved"
        assert summary.quality_score == 1.0
        assert "All quality checks passed!" in summary.summary

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
        assert summary.quality_score < 1.0
        assert "1 error" in summary.summary

    def test_generate_review_summary_with_warnings(self):
        """Test generating review summary with warnings."""
        annotator = PRAnnotator()
        for i in range(3):
            issue = CodeIssue(
                file_path="test.py",
                line_number=10 + i,
                column=5,
                severity="warning",
                message=f"Test warning {i}",
                rule_id="E501",
            )
            annotator.add_issue(issue)
        summary = annotator.generate_review_summary()
        assert summary.overall_status == "commented"
        assert "3 warnings" in summary.summary

    def test_generate_review_summary_many_warnings(self):
        """Test generating review summary with many warnings."""
        annotator = PRAnnotator()
        for i in range(10):
            issue = CodeIssue(
                file_path="test.py",
                line_number=10 + i,
                column=5,
                severity="warning",
                message=f"Test warning {i}",
                rule_id="E501",
            )
            annotator.add_issue(issue)
        summary = annotator.generate_review_summary()
        assert summary.overall_status == "changes_requested"

    def test_generate_suggestions(self):
        """Test generating suggestions."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="e501",
        )
        annotator.add_issue(issue)
        suggestions = annotator._generate_suggestions()
        assert len(suggestions) > 0
        assert any("black" in suggestion.lower() for suggestion in suggestions)

    def test_generate_suggestions_f401(self):
        """Test generating suggestions for F401."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="f401",
        )
        annotator.add_issue(issue)
        suggestions = annotator._generate_suggestions()
        assert any("isort" in suggestion.lower() for suggestion in suggestions)

    def test_generate_suggestions_f841(self):
        """Test generating suggestions for F841."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="f841",
        )
        annotator.add_issue(issue)
        suggestions = annotator._generate_suggestions()
        assert any("underscore" in suggestion.lower() for suggestion in suggestions)

    def test_generate_suggestions_many_errors(self):
        """Test generating suggestions for many errors."""
        annotator = PRAnnotator()
        for i in range(10):
            issue = CodeIssue(
                file_path="test.py",
                line_number=10 + i,
                column=5,
                severity="error",
                message=f"Test error {i}",
                rule_id="e501",
            )
            annotator.add_issue(issue)
        suggestions = annotator._generate_suggestions()
        assert any("black" in suggestion.lower() for suggestion in suggestions)

    def test_generate_suggestions_no_errors(self):
        """Test generating suggestions with no errors."""
        annotator = PRAnnotator()
        suggestions = annotator._generate_suggestions()
        assert len(suggestions) == 1
        assert "Great job" in suggestions[0]

    def test_create_github_annotations(self):
        """Test creating GitHub annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)
        github_annotations = annotator.create_github_annotations()
        assert len(github_annotations) == 1
        assert github_annotations[0]["path"] == "test.py"
        assert github_annotations[0]["start_line"] == 10
        assert github_annotations[0]["annotation_level"] == "warning"

    def test_create_review_comment(self):
        """Test creating review comment."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)
        summary = annotator.generate_review_summary()
        comment = annotator.create_review_comment(summary)
        assert "AI-Guard Quality Review" in comment
        assert "test.py" in comment
        assert "Test issue" in comment

    def test_save_annotations(self):
        """Test saving annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            annotator.save_annotations(temp_file)
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                data = json.load(f)
            assert "annotations" in data
            assert "issues" in data
            assert "summary" in data
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_generate_annotations_summary(self):
        """Test generating annotations summary."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)
        summary = annotator.generate_annotations_summary()
        assert "1 issues found" in summary

    def test_write_annotations_to_file_stdout(self):
        """Test writing annotations to stdout."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with patch("builtins.print") as mock_print:
            annotator.write_annotations_to_file("-")
            mock_print.assert_called_once()

    def test_write_annotations_to_file_file(self):
        """Test writing annotations to file."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            annotator.write_annotations_to_file(temp_file)
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_clear_annotations(self):
        """Test clearing annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
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
            message="Test annotation",
            annotation_level="warning",
            title="Test Title",
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=10,
        )
        annotation_dict = annotator._annotation_to_dict(annotation)
        assert annotation_dict["file_path"] == "test.py"
        assert annotation_dict["line_number"] == 10
        assert annotation_dict["message"] == "Test annotation"
        assert annotation_dict["annotation_level"] == "warning"
        assert annotation_dict["title"] == "Test Title"
        assert annotation_dict["start_line"] == 10
        assert annotation_dict["end_line"] == 15
        assert annotation_dict["start_column"] == 5
        assert annotation_dict["end_column"] == 10

    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('hello')",
        )
        issue_dict = annotator._issue_to_dict(issue)
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 10
        assert issue_dict["column"] == 5
        assert issue_dict["severity"] == "warning"
        assert issue_dict["message"] == "Test issue"
        assert issue_dict["rule_id"] == "E501"
        assert issue_dict["suggestion"] == "Fix this"
        assert issue_dict["fix_code"] == "print('hello')"
