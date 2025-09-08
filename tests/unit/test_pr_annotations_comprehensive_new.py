"""Comprehensive tests for pr_annotations module."""

from unittest.mock import patch, Mock, mock_open
import json
from ai_guard.pr_annotations import (
    PRAnnotator,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    format_annotation_message,
    main,
)


class TestPRAnnotationsComprehensive:
    """Comprehensive test coverage for pr_annotations module."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test message",
            rule_id="test:rule1",
        )

        assert issue.rule_id == "test:rule1"
        assert issue.severity == "warning"
        assert issue.message == "Test message"
        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5

    def test_pr_annotation_creation(self):
        """Test PRAnnotation dataclass creation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test annotation",
            annotation_level="warning",
            title="Test Title",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10,
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 5
        assert annotation.end_column == 10
        assert annotation.annotation_level == "warning"
        assert annotation.message == "Test annotation"
        assert annotation.title == "Test Title"

    def test_review_summary_creation(self):
        """Test PRReviewSummary dataclass creation."""
        summary = PRReviewSummary(
            overall_status="approved",
            summary="Test summary",
            annotations=[],
            suggestions=[],
            quality_score=0.95,
        )

        assert summary.overall_status == "approved"
        assert summary.summary == "Test summary"
        assert summary.quality_score == 0.95
        assert summary.annotations == []
        assert summary.suggestions == []

    def test_pr_annotator_init(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()

        assert annotator is not None
        assert hasattr(annotator, "generate_review_summary")
        assert hasattr(annotator, "save_annotations")

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

    def test_pr_annotator_generate_review_summary_no_issues(self):
        """Test generating review summary with no issues."""
        annotator = PRAnnotator()

        with patch.object(annotator, "_load_findings") as mock_load:
            mock_load.return_value = []

            summary = annotator.generate_review_summary()

            assert summary.overall_status == "approved"
            assert summary.quality_score == 1.0
            assert len(summary.annotations) == 0

    def test_pr_annotator_generate_review_summary_with_issues(self):
        """Test generating review summary with issues."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": 10,
            },
            {
                "rule_id": "test:rule2",
                "level": "error",
                "message": "Test error",
                "path": "src/test.py",
                "line": 20,
            },
        ]

        with patch.object(annotator, "_load_findings") as mock_load:
            mock_load.return_value = findings

            summary = annotator.generate_review_summary()

            assert summary.overall_status == "changes_requested"
            assert summary.quality_score < 1.0
            assert len(summary.annotations) == 2

    def test_pr_annotator_generate_review_summary_mixed_issues(self):
        """Test generating review summary with mixed issue levels."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": 10,
            },
            {
                "rule_id": "test:rule2",
                "level": "note",
                "message": "Test note",
                "path": "src/test.py",
                "line": 20,
            },
        ]

        with patch.object(annotator, "_load_findings") as mock_load:
            mock_load.return_value = findings

            summary = annotator.generate_review_summary()

            assert summary.overall_status == "approved"
            assert summary.quality_score > 0.5
            assert len(summary.annotations) == 2

    def test_pr_annotator_load_findings_from_file(self):
        """Test loading findings from file."""
        annotator = PRAnnotator()

        findings_data = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        with patch("builtins.open", mock_open(read_data=json.dumps(findings_data))):
            with patch("os.path.exists", return_value=True):
                findings = annotator._load_findings()

                assert len(findings) == 1
                assert findings[0]["rule_id"] == "test:rule1"

    def test_pr_annotator_load_findings_file_not_found(self):
        """Test loading findings when file doesn't exist."""
        annotator = PRAnnotator()

        with patch("os.path.exists", return_value=False):
            findings = annotator._load_findings()

            assert findings == []

    def test_pr_annotator_load_findings_invalid_json(self):
        """Test loading findings with invalid JSON."""
        annotator = PRAnnotator()

        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists", return_value=True):
                findings = annotator._load_findings()

                assert findings == []

    def test_pr_annotator_load_findings_parse_error(self):
        """Test loading findings with parse error."""
        annotator = PRAnnotator()

        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("os.path.exists", return_value=True):
                with patch("json.load", side_effect=json.JSONDecodeError("", "", 0)):
                    findings = annotator._load_findings()

                    assert findings == []

    def test_pr_annotator_save_annotations(self):
        """Test saving annotations to file."""
        annotator = PRAnnotator()

        annotations = [
            PRAnnotation(
                path="src/test.py",
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
                annotator.save_annotations(annotations, "output.json")

                mock_file.assert_called_once_with("output.json", "w", encoding="utf-8")
                mock_file().write.assert_called_once()

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

        with patch("builtins.open", side_effect=IOError("Write error")):
            with patch("os.makedirs"):
                # Should not raise exception
                annotator.save_annotations(annotations)

    def test_pr_annotator_convert_findings_to_annotations(self):
        """Test converting findings to annotations."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        annotations = annotator._convert_findings_to_annotations(findings)

        assert len(annotations) == 1
        assert annotations[0].path == "src/test.py"
        assert annotations[0].start_line == 10
        assert annotations[0].annotation_level == "warning"
        assert annotations[0].message == "Test warning"

    def test_pr_annotator_convert_findings_to_annotations_no_line(self):
        """Test converting findings to annotations without line number."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": None,
            }
        ]

        annotations = annotator._convert_findings_to_annotations(findings)

        assert len(annotations) == 1
        assert annotations[0].path == "src/test.py"
        assert annotations[0].start_line == 1  # Default line
        assert annotations[0].annotation_level == "warning"

    def test_pr_annotator_calculate_quality_score_no_issues(self):
        """Test calculating quality score with no issues."""
        annotator = PRAnnotator()

        findings = []

        score = annotator._calculate_quality_score(findings)

        assert score == 1.0

    def test_pr_annotator_calculate_quality_score_with_issues(self):
        """Test calculating quality score with issues."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": 10,
            },
            {
                "rule_id": "test:rule2",
                "level": "error",
                "message": "Test error",
                "path": "src/test.py",
                "line": 20,
            },
        ]

        score = annotator._calculate_quality_score(findings)

        assert score < 1.0
        assert score > 0.0

    def test_pr_annotator_determine_overall_status_approved(self):
        """Test determining overall status as approved."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "note",
                "message": "Test note",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        status = annotator._determine_overall_status(findings)

        assert status == "approved"

    def test_pr_annotator_determine_overall_status_changes_requested(self):
        """Test determining overall status as changes requested."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "error",
                "message": "Test error",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        status = annotator._determine_overall_status(findings)

        assert status == "changes_requested"

    def test_pr_annotator_determine_overall_status_approved_with_warnings(self):
        """Test determining overall status as approved with warnings."""
        annotator = PRAnnotator()

        findings = [
            {
                "rule_id": "test:rule1",
                "level": "warning",
                "message": "Test warning",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        status = annotator._determine_overall_status(findings)

        assert status == "approved"

    def test_main_function(self):
        """Test main function."""
        with patch("ai_guard.pr_annotations.PRAnnotator") as mock_annotator_class:
            mock_annotator = Mock()
            mock_annotator_class.return_value = mock_annotator
            mock_annotator.generate_review_summary.return_value = Mock(
                overall_status="approved", quality_score=0.95, annotations=[]
            )

            with patch("sys.argv", ["pr_annotations"]):
                main()

                mock_annotator_class.assert_called_once()
                mock_annotator.generate_review_summary.assert_called_once()
                mock_annotator.save_annotations.assert_called_once()

    def test_main_function_with_custom_output(self):
        """Test main function with custom output path."""
        with patch("ai_guard.pr_annotations.PRAnnotator") as mock_annotator_class:
            mock_annotator = Mock()
            mock_annotator_class.return_value = mock_annotator
            mock_annotator.generate_review_summary.return_value = Mock(
                overall_status="approved", quality_score=0.95, annotations=[]
            )

            with patch(
                "sys.argv", ["pr_annotations", "--output", "custom/output.json"]
            ):
                main()

                mock_annotator_class.assert_called_once()
                mock_annotator.generate_review_summary.assert_called_once()
                mock_annotator.save_annotations.assert_called_once_with(
                    mock_annotator.generate_review_summary.return_value.annotations,
                    "custom/output.json",
                )
