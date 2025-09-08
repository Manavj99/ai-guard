"""Simple tests for pr_annotations module focusing on existing functionality."""

from unittest.mock import Mock, patch, mock_open
from ai_guard.pr_annotations import (
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
    format_annotation_message,
)


class TestPRAnnotationsSimple:
    """Test class for pr_annotations module."""

    def test_code_issue_creation(self):
        """Test creating a CodeIssue."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning message",
            rule_id="test:rule1",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "warning"
        assert issue.message == "Test warning message"
        assert issue.rule_id == "test:rule1"

    def test_code_issue_with_optional_fields(self):
        """Test creating a CodeIssue with optional fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning message",
            rule_id="test:rule1",
            suggestion="Fix this",
            fix_code="print('fixed')",
        )

        assert issue.suggestion == "Fix this"
        assert issue.fix_code == "print('fixed')"

    def test_pr_annotation_creation(self):
        """Test creating a PRAnnotation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10,
            annotation_level="warning",
            message="Test annotation",
            title="Test Title",
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 5
        assert annotation.end_column == 10
        assert annotation.annotation_level == "warning"
        assert annotation.message == "Test annotation"
        assert annotation.title == "Test Title"

    def test_pr_review_summary_creation(self):
        """Test creating a PRReviewSummary."""
        summary = PRReviewSummary(
            overall_status="approved", quality_score=0.95, annotations=[]
        )

        assert summary.overall_status == "approved"
        assert summary.quality_score == 0.95
        assert summary.annotations == []

    def test_pr_annotator_initialization(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()

        assert annotator is not None
        assert hasattr(annotator, "add_issue")
        assert hasattr(annotator, "save_annotations")

    def test_pr_annotator_initialization_with_params(self):
        """Test PRAnnotator initialization with parameters."""
        annotator = PRAnnotator(github_token="test_token", repo="test/repo")

        assert annotator.github_token == "test_token"
        assert annotator.repo == "test/repo"

    def test_pr_annotator_add_issue(self):
        """Test adding an issue to the annotator."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning message",
            rule_id="test:rule1",
        )

        annotator.add_issue(issue)

        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.issues[0] == issue

    def test_format_annotation_message_basic(self):
        """Test formatting annotation message for basic message."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning message",
            rule_id="test:rule1",
        )

        message = format_annotation_message(issue)

        assert "Test warning message" in message

    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=20,
            column=10,
            severity="error",
            message="Test error message",
            rule_id="test:rule2",
            suggestion="Fix this issue",
        )

        message = format_annotation_message(issue)

        assert "Test error message" in message
        assert "💡 **Suggestion:** Fix this issue" in message

    def test_format_annotation_message_with_fix_code(self):
        """Test formatting annotation message with fix code."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=30,
            column=15,
            severity="info",
            message="Test note message",
            rule_id="test:rule3",
            fix_code="print('fixed')",
        )

        message = format_annotation_message(issue)

        assert "Test note message" in message
        assert "🔧 **Fix:**" in message
        assert "print('fixed')" in message

    def test_format_annotation_message_with_both_suggestion_and_fix(self):
        """Test formatting annotation message with both suggestion and fix."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=40,
            column=20,
            severity="unknown",
            message="Test unknown message",
            rule_id="test:rule4",
            suggestion="Consider this",
            fix_code="return True",
        )

        message = format_annotation_message(issue)

        assert "Test unknown message" in message
        assert "💡 **Suggestion:** Consider this" in message
        assert "🔧 **Fix:**" in message
        assert "return True" in message

    def test_pr_annotator_save_annotations(self):
        """Test saving annotations to file."""
        annotator = PRAnnotator()

        annotations = [
            PRAnnotation(
                file_path="src/test.py",
                start_line=10,
                end_line=10,
                start_column=5,
                end_column=10,
                annotation_level="warning",
                message="Test annotation",
                title="Test Title",
            )
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs"):
                annotator.save_annotations(annotations, "test-output.json")

                mock_file.assert_called_once_with(
                    "test-output.json", "w", encoding="utf-8"
                )

    def test_pr_annotator_save_annotations_default_path(self):
        """Test saving annotations with default path."""
        annotator = PRAnnotator()

        annotations = []

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs"):
                annotator.save_annotations(annotations)

                mock_file.assert_called_once_with(
                    "pr-annotations.json", "w", encoding="utf-8"
                )

    def test_pr_annotator_save_annotations_error(self):
        """Test saving annotations with error."""
        annotator = PRAnnotator()

        annotations = []

        with patch("builtins.open", side_effect=OSError("Write error")):
            with patch("os.makedirs"):
                # Should not raise exception
                annotator.save_annotations(annotations)

    def test_main_function_with_input(self):
        """Test main function with required input argument."""
        with patch("ai_guard.pr_annotations.PRAnnotator") as mock_annotator_class:
            mock_annotator = Mock()
            mock_annotator_class.return_value = mock_annotator
            mock_annotator.generate_review_summary.return_value = Mock(
                overall_status="approved", quality_score=0.95, annotations=[]
            )

            with patch("sys.argv", ["pr_annotations", "--input", "test.json"]):
                from ai_guard.pr_annotations import main

                main()

    def test_main_function_with_custom_output(self):
        """Test main function with custom output path."""
        with patch("ai_guard.pr_annotations.PRAnnotator") as mock_annotator_class:
            mock_annotator = Mock()
            mock_annotator_class.return_value = mock_annotator
            mock_annotator.generate_review_summary.return_value = Mock(
                overall_status="approved", quality_score=0.95, annotations=[]
            )

            with patch(
                "sys.argv",
                [
                    "pr_annotations",
                    "--input",
                    "test.json",
                    "--output",
                    "custom/output.json",
                ],
            ):
                from ai_guard.pr_annotations import main

                main()
