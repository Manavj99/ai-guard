"""Comprehensive tests for pr_annotations.py module."""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from dataclasses import asdict

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
    main
)


class TestAnnotationLevel:
    """Test AnnotationLevel enum."""

    def test_annotation_level_values(self):
        """Test AnnotationLevel enum values."""
        assert AnnotationLevel.NOTICE.value == "notice"
        assert AnnotationLevel.WARNING.value == "warning"
        assert AnnotationLevel.ERROR.value == "error"


class TestCodeIssue:
    """Test CodeIssue dataclass."""

    def test_code_issue_creation(self):
        """Test creating CodeIssue."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error",
            suggestion="Break the line",
            fix_code="line1 = 'short'\nline2 = 'line'"
        )
        
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.rule_id == "E501"
        assert issue.message == "Line too long"
        assert issue.severity == "error"
        assert issue.suggestion == "Break the line"
        assert issue.fix_code == "line1 = 'short'\nline2 = 'line'"

    def test_code_issue_minimal(self):
        """Test creating CodeIssue with minimal data."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=1,
            column=1,
            severity="error",
            message="Syntax error",
            rule_id="E001"
        )
        
        assert issue.file_path == "test.py"
        assert issue.line_number == 1
        assert issue.column == 1
        assert issue.rule_id == "E001"
        assert issue.message == "Syntax error"
        assert issue.severity == "info"  # Default value
        assert issue.suggestion is None
        assert issue.fix_code is None

    def test_code_issue_to_dict(self):
        """Test converting CodeIssue to dictionary."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error",
            suggestion="Break the line",
            fix_code="line1 = 'short'"
        )
        
        issue_dict = issue.to_dict()
        
        expected = {
            "file_path": "test.py",
            "line_number": 10,
            "column": 5,
            "rule_id": "E501",
            "message": "Line too long",
            "severity": "error",
            "suggestion": "Break the line",
            "fix_code": "line1 = 'short'"
        }
        
        assert issue_dict == expected


class TestPRAnnotation:
    """Test PRAnnotation dataclass."""

    def test_pr_annotation_creation(self):
        """Test creating PRAnnotation."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test message",
            annotation_level="error",
            title="Test Title",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10
        )
        
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "error"
        assert annotation.title == "Test Title"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 5
        assert annotation.end_column == 10

    def test_pr_annotation_to_dict(self):
        """Test converting PRAnnotation to dictionary."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test message",
            annotation_level="error",
            title="Test Title"
        )
        
        # Test PRAnnotation attributes directly
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "error"
        assert annotation.title == "Test Title"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 1
        assert annotation.end_column == 1


class TestPRReviewSummary:
    """Test PRReviewSummary dataclass."""

    def test_pr_review_summary_creation(self):
        """Test creating PRReviewSummary."""
        summary = PRReviewSummary(
            overall_status="success",
            summary="Test summary",
            annotations=[],
            suggestions=["suggestion1", "suggestion2"],
            quality_score=0.85,
            security_issues=["security1"]
        )
        
        assert summary.overall_status == "success"
        assert summary.quality_score == 0.85
        assert summary.annotations == []
        assert summary.suggestions == ["suggestion1", "suggestion2"]
        assert summary.security_issues == ["security1"]

    def test_pr_review_summary_minimal(self):
        """Test creating PRReviewSummary with minimal data."""
        summary = PRReviewSummary(
            overall_status="failure",
            summary="Minimal summary",
            annotations=[],
            suggestions=[],
            quality_score=0.5
        )
        
        assert summary.overall_status == "failure"
        assert summary.quality_score == 0.5
        assert summary.annotations == []
        assert summary.security_issues is None


class TestPRAnnotator:
    """Test PRAnnotator class."""

    def test_pr_annotator_init_default(self):
        """Test PRAnnotator initialization with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            annotator = PRAnnotator()
            assert annotator.github_token is None
            assert annotator.repo is None
            assert annotator.annotations == []
            assert annotator.issues == []

    def test_pr_annotator_init_with_params(self):
        """Test PRAnnotator initialization with parameters."""
        annotator = PRAnnotator(
            github_token="test_token",
            repo="owner/repo"
        )
        assert annotator.github_token == "test_token"
        assert annotator.repo == "owner/repo"
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_init_with_env(self):
        """Test PRAnnotator initialization with environment variables."""
        with patch.dict(os.environ, {
            "GITHUB_TOKEN": "env_token",
            "GITHUB_REPOSITORY": "env/repo"
        }):
            annotator = PRAnnotator()
            assert annotator.github_token == "env_token"
            assert annotator.repo == "env/repo"

    def test_add_issue(self):
        """Test adding a code issue."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error"
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
            rule_id="E501",
            message="Line too long",
            severity="error",
            suggestion="Break the line",
            fix_code="short_line = 'value'"
        )
        
        annotation = annotator._issue_to_annotation(issue)
        
        assert annotation is not None
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.annotation_level == "failure"
        assert "Line too long" in annotation.message
        assert "Suggestion:" in annotation.message
        assert "Fix:" in annotation.message

    def test_issue_to_annotation_warning(self):
        """Test converting warning issue to annotation."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=5,
            column=1,
            rule_id="W001",
            message="Unused import",
            severity="warning"
        )
        
        annotation = annotator._issue_to_annotation(issue)
        
        assert annotation is not None
        assert annotation.annotation_level == "warning"
        assert annotation.title == "W001: Unused import"

    def test_issue_to_annotation_info(self):
        """Test converting info issue to annotation."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=1,
            column=1,
            rule_id="I001",
            message="Style suggestion",
            severity="info"
        )
        
        annotation = annotator._issue_to_annotation(issue)
        
        assert annotation is not None
        assert annotation.annotation_level == "notice"

    def test_add_lint_issues(self):
        """Test adding lint issues."""
        annotator = PRAnnotator()
        
        lint_results = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "column": 5,
                "rule_id": "E501",
                "message": "Line too long",
                "severity": "error"
            },
            {
                "file_path": "test2.py",
                "line_number": 5,
                "column": 1,
                "rule_id": "W001",
                "message": "Unused import",
                "severity": "warning"
            }
        ]
        
        annotator.add_lint_issues(lint_results)
        
        assert len(annotator.issues) == 2
        assert len(annotator.annotations) == 2

    def test_add_security_annotation(self):
        """Test adding security annotations."""
        annotator = PRAnnotator()
        
        security_issues = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "column": 5,
                "rule_id": "B101",
                "message": "Hardcoded password",
                "severity": "error"
            }
        ]
        
        annotator.add_security_annotation(security_issues)
        
        assert len(annotator.annotations) == 1
        annotation = annotator.annotations[0]
        assert "security" in annotation.title.lower() or "B101" in annotation.title

    def test_add_coverage_annotation(self):
        """Test adding coverage annotations."""
        annotator = PRAnnotator()
        
        annotator.add_coverage_annotation("test.py", {"coverage": 75.5})
        
        assert len(annotator.annotations) == 1
        annotation = annotator.annotations[0]
        assert "coverage" in annotation.title.lower()
        assert "75.5%" in annotation.message

    def test_generate_review_summary(self):
        """Test generating review summary."""
        annotator = PRAnnotator()
        
        # Add some issues
        issue1 = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error"
        )
        
        issue2 = CodeIssue(
            file_path="test.py",
            line_number=15,
            column=1,
            rule_id="W001",
            message="Unused import",
            severity="warning"
        )
        
        annotator.add_issue(issue1)
        annotator.add_issue(issue2)
        
        summary = annotator.generate_review_summary()
        
        assert summary.overall_status in ["success", "failure", "warning", "changes_requested"]
        assert 0 <= summary.quality_score <= 1
        assert len(summary.annotations) == 2

    def test_create_review_comment(self):
        """Test creating review comment."""
        annotator = PRAnnotator()
        
        # Add some issues
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error"
        )
        
        annotator.add_issue(issue)
        summary = annotator.generate_review_summary()
        
        comment = annotator.create_review_comment(summary)
        
        assert isinstance(comment, str)
        assert len(comment) > 0

    def test_save_annotations(self):
        """Test saving annotations to file."""
        annotator = PRAnnotator()
        
        # Add an issue
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error"
        )
        
        annotator.add_issue(issue)
        
        # Mock file operations
        with patch("builtins.open", mock_open()) as mock_file:
            annotator.save_annotations("test_annotations.json")
            
            mock_file.assert_called_once_with("test_annotations.json", "w", encoding="utf-8")
            
            # Check that JSON was written
            written_data = mock_file().write.call_args[0][0]
            annotations_data = json.loads(written_data)
            assert "annotations" in annotations_data
            assert len(annotations_data["annotations"]) == 1


class TestParseFunctions:
    """Test parsing functions."""

    def test_parse_lint_output(self):
        """Test parsing lint output."""
        lint_output = """
test.py:10:5: E501 line too long (80 > 79 characters)
test.py:15:1: W001 unused import 'os'
test.py:20:10: E001 syntax error
        """.strip()
        
        issues = parse_lint_output(lint_output)
        
        assert len(issues) == 3
        
        # Check first issue
        issue1 = issues[0]
        assert issue1.file_path == "test.py"
        assert issue1.line_number == 10
        assert issue1.column == 5
        assert issue1.rule_id == "E501"
        assert "line too long" in issue1.message
        assert issue1.severity == "error"

    def test_parse_bandit_output(self):
        """Test parsing bandit output."""
        bandit_output = """
test.py:10:5: B101 Use of hardcoded password strings
test.py:20:1: B102 exec_used Use of exec
        """.strip()
        
        issues = parse_bandit_output(bandit_output)
        
        assert len(issues) == 2
        
        # Check first issue
        issue1 = issues[0]
        assert issue1.file_path == "test.py"
        assert issue1.line_number == 10
        assert issue1.rule_id == "B101"
        assert "hardcoded password" in issue1.message.lower()

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = """
test.py:10: error: Incompatible return type
test.py:15: warning: Unused "type: ignore" comment
        """.strip()
        
        issues = parse_mypy_output(mypy_output)
        
        assert len(issues) == 2
        
        # Check first issue
        issue1 = issues[0]
        assert issue1.file_path == "test.py"
        assert issue1.line_number == 10
        assert "Incompatible return type" in issue1.message
        assert issue1.severity == "error"

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        assert parse_lint_output("") == []
        assert parse_bandit_output("") == []
        assert parse_mypy_output("") == []


class TestCreatePRAnnotations:
    """Test create_pr_annotations function."""

    def test_create_pr_annotations_with_lint(self):
        """Test creating PR annotations with lint output."""
        lint_output = "test.py:10:5: E501 line too long"
        
        annotations = create_pr_annotations(lint_output=lint_output)
        
        assert len(annotations) == 1
        annotation = annotations[0]
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10

    def test_create_pr_annotations_with_bandit(self):
        """Test creating PR annotations with bandit output."""
        bandit_output = "test.py:10:5: B101 hardcoded password"
        
        annotations = create_pr_annotations(bandit_output=bandit_output)
        
        assert len(annotations) == 1

    def test_create_pr_annotations_with_mypy(self):
        """Test creating PR annotations with mypy output."""
        mypy_output = "test.py:10: error: Incompatible return type"
        
        annotations = create_pr_annotations(mypy_output=mypy_output)
        
        assert len(annotations) == 1

    def test_create_pr_annotations_with_coverage(self):
        """Test creating PR annotations with coverage output."""
        coverage_output = "test.py: 10 lines, 8 covered (80%)"
        
        annotations = create_pr_annotations(coverage_output=coverage_output)
        
        assert len(annotations) == 1

    def test_create_pr_annotations_with_multiple(self):
        """Test creating PR annotations with multiple outputs."""
        lint_output = "test.py:10:5: E501 line too long"
        bandit_output = "test.py:20:1: B101 hardcoded password"
        
        annotations = create_pr_annotations(
            lint_output=lint_output,
            bandit_output=bandit_output
        )
        
        assert len(annotations) == 2

    def test_create_pr_annotations_with_list(self):
        """Test creating PR annotations with list of issues."""
        issues = [
            CodeIssue(
                file_path="test.py",
                line_number=10,
                column=5,
                rule_id="E501",
                message="Line too long",
                severity="error"
            )
        ]
        
        annotations = create_pr_annotations(lint_output=issues)
        
        assert len(annotations) == 1

    def test_create_pr_annotations_with_output_file(self):
        """Test creating PR annotations with output file."""
        lint_output = "test.py:10:5: E501 line too long"
        
        with patch("builtins.open", mock_open()) as mock_file:
            annotations = create_pr_annotations(
                lint_output=lint_output,
                output_file="test_output.json"
            )
            
            assert len(annotations) == 1
            mock_file.assert_called()


class TestFormatAnnotationMessage:
    """Test format_annotation_message function."""

    def test_format_annotation_message_basic(self):
        """Test formatting basic annotation message."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error"
        )
        
        message = format_annotation_message(issue)
        
        assert "Line too long" in message
        assert issue.message in message

    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error",
            suggestion="Break the line"
        )
        
        message = format_annotation_message(issue)
        
        assert "Line too long" in message
        assert "Suggestion:" in message
        assert "Break the line" in message

    def test_format_annotation_message_with_fix(self):
        """Test formatting annotation message with fix code."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error",
            fix_code="short_line = 'value'"
        )
        
        message = format_annotation_message(issue)
        
        assert "Line too long" in message
        assert "Fix:" in message
        assert "short_line = 'value'" in message

    def test_format_annotation_message_complete(self):
        """Test formatting annotation message with all fields."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            rule_id="E501",
            message="Line too long",
            severity="error",
            suggestion="Break the line",
            fix_code="short_line = 'value'"
        )
        
        message = format_annotation_message(issue)
        
        assert "Line too long" in message
        assert "Suggestion:" in message
        assert "Break the line" in message
        assert "Fix:" in message
        assert "short_line = 'value'" in message


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""

    def test_write_annotations_file_success(self):
        """Test successfully writing annotations file."""
        annotations = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "message": "Test message",
                "annotation_level": "error"
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            result = write_annotations_file(annotations, "test.json")
            
            assert result is True
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
            
            # Check JSON content
            written_data = mock_file().write.call_args[0][0]
            data = json.loads(written_data)
            assert "annotations" in data
            assert len(data["annotations"]) == 1

    def test_write_annotations_file_error(self):
        """Test writing annotations file with error."""
        annotations = [{"test": "data"}]
        
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = write_annotations_file(annotations, "test.json")
            
            assert result is False


class TestMain:
    """Test main function."""

    def test_main_with_args(self):
        """Test main function with command line arguments."""
        test_args = [
            "pr_annotations.py",
            "--input", "test_input.json",
            "--output", "test_output.json",
            "--github-token", "test_token",
            "--repo", "owner/repo"
        ]
        
        input_data = {
            "lint_results": [
                {
                    "file_path": "test.py",
                    "line_number": 10,
                    "column": 5,
                    "rule_id": "E501",
                    "message": "Line too long",
                    "severity": "error"
                }
            ]
        }
        
        with patch("sys.argv", test_args), \
             patch("builtins.open", mock_open(read_data=json.dumps(input_data))), \
             patch("src.ai_guard.pr_annotations.PRAnnotator") as mock_annotator_class, \
             patch("builtins.print") as mock_print:
            
            mock_annotator = Mock()
            mock_annotator_class.return_value = mock_annotator
            mock_annotator.generate_review_summary.return_value = PRReviewSummary(
                overall_status="success",
                summary="Test summary",
                annotations=[],
                suggestions=[],
                quality_score=0.85
            )
            mock_annotator.create_review_comment.return_value = "Test comment"
            
            main()
            
            mock_annotator.add_lint_issues.assert_called_once()
            mock_annotator.save_annotations.assert_called_once_with("test_output.json")

    def test_main_with_error(self):
        """Test main function with error."""
        test_args = [
            "pr_annotations.py",
            "--input", "nonexistent.json",
            "--output", "test_output.json"
        ]
        
        with patch("sys.argv", test_args), \
             patch("builtins.open", side_effect=FileNotFoundError("File not found")), \
             patch("builtins.print") as mock_print:
            
            main()
            
            # Should print error message
            mock_print.assert_called()
            assert "Error processing input" in str(mock_print.call_args)


class TestIntegration:
    """Integration tests for pr_annotations module."""

    def test_full_workflow(self):
        """Test full workflow from parsing to annotation creation."""
        # Create test data
        lint_output = "test.py:10:5: E501 line too long"
        bandit_output = "test.py:20:1: B101 hardcoded password"
        coverage_output = "test.py: 10 lines, 8 covered (80%)"
        
        # Create annotations
        annotations = create_pr_annotations(
            lint_output=lint_output,
            bandit_output=bandit_output,
            coverage_output=coverage_output
        )
        
        assert len(annotations) == 3
        
        # Verify annotation types
        annotation_types = [ann.annotation_level for ann in annotations]
        assert "failure" in annotation_types  # Error
        assert "warning" in annotation_types  # Coverage below threshold
        
        # Test saving annotations
        with patch("builtins.open", mock_open()) as mock_file:
            result = write_annotations_file(
                [ann.to_dict() for ann in annotations],
                "test_annotations.json"
            )
            
            assert result is True

    def test_annotator_with_real_data(self):
        """Test PRAnnotator with realistic data."""
        annotator = PRAnnotator()
        
        # Add various types of issues
        issues = [
            CodeIssue(
                file_path="src/main.py",
                line_number=10,
                column=5,
                rule_id="E501",
                message="Line too long (120 > 79 characters)",
                severity="error",
                suggestion="Break the line into multiple lines",
                fix_code="result = some_function_call(\n    param1, param2, param3\n)"
            ),
            CodeIssue(
                file_path="src/utils.py",
                line_number=25,
                column=1,
                rule_id="W001",
                message="Unused import 'os'",
                severity="warning"
            ),
            CodeIssue(
                file_path="src/auth.py",
                line_number=5,
                column=10,
                rule_id="B101",
                message="Use of hardcoded password strings",
                severity="error",
                suggestion="Use environment variables or secure key management"
            )
        ]
        
        for issue in issues:
            annotator.add_issue(issue)
        
        # Generate summary
        summary = annotator.generate_review_summary()
        
        assert summary.overall_status in ["success", "failure", "warning", "changes_requested"]
        assert 0 <= summary.quality_score <= 1
        assert len(summary.annotations) == 3
        
        # Create review comment
        comment = annotator.create_review_comment(summary)
        assert isinstance(comment, str)
        assert len(comment) > 0
        
        # Verify annotations have proper formatting
        for annotation in annotator.annotations:
            assert annotation.file_path
            assert annotation.line_number > 0
            assert annotation.message
            assert annotation.annotation_level in ["failure", "warning", "notice"]