"""Working tests for pr_annotations module that match actual source code."""

from unittest.mock import patch
import os
from ai_guard.pr_annotations import (
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
    format_annotation_message,
)


class TestPRAnnotationsWorking:
    """Working test coverage for pr_annotations module."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            rule_id="E302",
            suggestion="Add blank lines",
            fix_code="\n\n",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.rule_id == "E302"
        assert issue.suggestion == "Add blank lines"
        assert issue.fix_code == "\n\n"

    def test_code_issue_minimal(self):
        """Test CodeIssue with minimal required fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W001",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "warning"
        assert issue.message == "Test warning"
        assert issue.rule_id == "W001"
        assert issue.suggestion is None
        assert issue.fix_code is None

    def test_pr_annotation_creation(self):
        """Test PRAnnotation dataclass creation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test annotation message",
            annotation_level="warning",
            title="Test Title",
            raw_details="Raw details",
            start_line=10,
            end_line=12,
            start_column=5,
            end_column=10,
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test annotation message"
        assert annotation.annotation_level == "warning"
        assert annotation.title == "Test Title"
        assert annotation.raw_details == "Raw details"
        assert annotation.start_line == 10
        assert annotation.end_line == 12
        assert annotation.start_column == 5
        assert annotation.end_column == 10

    def test_pr_annotation_minimal(self):
        """Test PRAnnotation with minimal required fields."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test message",
            annotation_level="notice",
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "notice"
        assert annotation.title is None
        assert annotation.raw_details is None
        assert annotation.start_line is None
        assert annotation.end_line is None
        assert annotation.start_column is None
        assert annotation.end_column is None

    def test_pr_review_summary_creation(self):
        """Test PRReviewSummary dataclass creation."""
        annotations = [
            PRAnnotation(
                file_path="src/test.py",
                line_number=10,
                message="Test message",
                annotation_level="warning",
            )
        ]

        summary = PRReviewSummary(
            overall_status="changes_requested",
            summary="Test summary",
            annotations=annotations,
            suggestions=["Fix line 10"],
            quality_score=0.8,
            coverage_info={"coverage": 85.0},
            security_issues=["Potential security issue"],
        )

        assert summary.overall_status == "changes_requested"
        assert summary.summary == "Test summary"
        assert len(summary.annotations) == 1
        assert summary.suggestions == ["Fix line 10"]
        assert summary.quality_score == 0.8
        assert summary.coverage_info == {"coverage": 85.0}
        assert summary.security_issues == ["Potential security issue"]

    def test_pr_review_summary_minimal(self):
        """Test PRReviewSummary with minimal required fields."""
        summary = PRReviewSummary(
            overall_status="approved",
            summary="Test summary",
            annotations=[],
            suggestions=[],
            quality_score=1.0,
        )

        assert summary.overall_status == "approved"
        assert summary.summary == "Test summary"
        assert summary.annotations == []
        assert summary.suggestions == []
        assert summary.quality_score == 1.0
        assert summary.coverage_info is None
        assert summary.security_issues is None

    def test_pr_annotator_init_with_token(self):
        """Test PRAnnotator initialization with token."""
        annotator = PRAnnotator(github_token="test_token", repo="test/repo")

        assert annotator.github_token == "test_token"
        assert annotator.repo == "test/repo"
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_init_with_env_vars(self):
        """Test PRAnnotator initialization with environment variables."""
        with patch.dict(
            os.environ, {"GITHUB_TOKEN": "env_token", "GITHUB_REPOSITORY": "env/repo"}
        ):
            annotator = PRAnnotator()

            assert annotator.github_token == "env_token"
            assert annotator.repo == "env/repo"
            assert annotator.annotations == []
            assert annotator.issues == []

    def test_pr_annotator_init_without_env_vars(self):
        """Test PRAnnotator initialization without environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            annotator = PRAnnotator()

            assert annotator.github_token is None
            assert annotator.repo is None
            assert annotator.annotations == []
            assert annotator.issues == []

    def test_add_issue_error_severity(self):
        """Test adding issue with error severity."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "failure"
        assert annotator.annotations[0].title == "E001: Test error"

    def test_add_issue_warning_severity(self):
        """Test adding issue with warning severity."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "warning"
        assert annotator.annotations[0].title == "W001: Test warning"

    def test_add_issue_info_severity(self):
        """Test adding issue with info severity."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="info",
            message="Test info",
            rule_id="I001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "notice"
        assert annotator.annotations[0].title == "I001: Test info"

    def test_add_issue_with_suggestion(self):
        """Test adding issue with suggestion."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W001",
            suggestion="Add blank lines",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert "💡 **Suggestion:** Add blank lines" in annotator.annotations[0].message

    def test_add_issue_with_fix_code(self):
        """Test adding issue with fix code."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            fix_code="\n\n",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert "🔧 **Fix:**" in annotator.annotations[0].message
        assert "```" in annotator.annotations[0].message

    def test_add_issue_with_suggestion_and_fix(self):
        """Test adding issue with both suggestion and fix code."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Add blank lines",
            fix_code="\n\n",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        message = annotator.annotations[0].message
        assert "💡 **Suggestion:** Add blank lines" in message
        assert "🔧 **Fix:**" in message

    def test_format_annotation_message_simple(self):
        """Test formatting simple annotation message."""
        message = format_annotation_message("Test message")

        assert message == "Test message"

    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        message = format_annotation_message(
            "Test message", suggestion="Test suggestion"
        )

        assert "Test message" in message
        assert "💡 **Suggestion:** Test suggestion" in message

    def test_format_annotation_message_with_fix(self):
        """Test formatting annotation message with fix."""
        message = format_annotation_message("Test message", fix_code="test_fix()")

        assert "Test message" in message
        assert "🔧 **Fix:**" in message
        assert "```" in message
        assert "test_fix()" in message

    def test_format_annotation_message_with_both(self):
        """Test formatting annotation message with both suggestion and fix."""
        message = format_annotation_message(
            "Test message", suggestion="Test suggestion", fix_code="test_fix()"
        )

        assert "Test message" in message
        assert "💡 **Suggestion:** Test suggestion" in message
        assert "🔧 **Fix:**" in message
        assert "test_fix()" in message

    def test_get_annotations_by_file(self):
        """Test getting annotations grouped by file."""
        annotator = PRAnnotator()

        # Add issues for different files
        issue1 = CodeIssue(
            file_path="src/test1.py",
            line_number=10,
            column=5,
            severity="error",
            message="Error in test1",
            rule_id="E001",
        )

        issue2 = CodeIssue(
            file_path="src/test2.py",
            line_number=15,
            column=3,
            severity="warning",
            message="Warning in test2",
            rule_id="W001",
        )

        issue3 = CodeIssue(
            file_path="src/test1.py",
            line_number=20,
            column=7,
            severity="info",
            message="Info in test1",
            rule_id="I001",
        )

        annotator.add_issue(issue1)
        annotator.add_issue(issue2)
        annotator.add_issue(issue3)

        by_file = annotator.get_annotations_by_file()

        assert "src/test1.py" in by_file
        assert "src/test2.py" in by_file
        assert len(by_file["src/test1.py"]) == 2
        assert len(by_file["src/test2.py"]) == 1

    def test_get_annotations_by_file_empty(self):
        """Test getting annotations by file when no annotations exist."""
        annotator = PRAnnotator()

        by_file = annotator.get_annotations_by_file()

        assert by_file == {}

    def test_clear_annotations(self):
        """Test clearing all annotations and issues."""
        annotator = PRAnnotator()

        # Add some issues
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1

        annotator.clear_annotations()

        assert len(annotator.issues) == 0
        assert len(annotator.annotations) == 0

    def test_get_quality_score_high(self):
        """Test getting high quality score."""
        annotator = PRAnnotator()

        # Add mostly info issues
        for i in range(5):
            issue = CodeIssue(
                file_path=f"src/test{i}.py",
                line_number=10,
                column=5,
                severity="info",
                message=f"Info {i}",
                rule_id=f"I{i:03d}",
            )
            annotator.add_issue(issue)

        # Add one warning
        warning_issue = CodeIssue(
            file_path="src/warning.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Warning",
            rule_id="W001",
        )
        annotator.add_issue(warning_issue)

        score = annotator.get_quality_score()

        # Should be high since mostly info issues
        assert score > 0.7

    def test_get_quality_score_low(self):
        """Test getting low quality score."""
        annotator = PRAnnotator()

        # Add mostly error issues
        for i in range(5):
            issue = CodeIssue(
                file_path=f"src/test{i}.py",
                line_number=10,
                column=5,
                severity="error",
                message=f"Error {i}",
                rule_id=f"E{i:03d}",
            )
            annotator.add_issue(issue)

        score = annotator.get_quality_score()

        # Should be low since mostly error issues
        assert score < 0.5

    def test_get_quality_score_no_issues(self):
        """Test getting quality score with no issues."""
        annotator = PRAnnotator()

        score = annotator.get_quality_score()

        # Should be perfect score
        assert score == 1.0

    def test_generate_review_summary(self):
        """Test generating review summary."""
        annotator = PRAnnotator()

        # Add some issues
        issue1 = CodeIssue(
            file_path="src/test1.py",
            line_number=10,
            column=5,
            severity="error",
            message="Error in test1",
            rule_id="E001",
        )

        issue2 = CodeIssue(
            file_path="src/test2.py",
            line_number=15,
            column=3,
            severity="warning",
            message="Warning in test2",
            rule_id="W001",
        )

        annotator.add_issue(issue1)
        annotator.add_issue(issue2)

        summary = annotator.generate_review_summary()

        assert isinstance(summary, PRReviewSummary)
        assert summary.overall_status in ["approved", "changes_requested", "commented"]
        assert len(summary.annotations) == 2
        assert 0.0 <= summary.quality_score <= 1.0
