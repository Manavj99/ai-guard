"""Comprehensive tests for pr_annotations.py to improve coverage."""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
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
)


class TestAnnotationLevel:
    """Test AnnotationLevel enum."""

    def test_level_values(self):
        """Test annotation level values."""
        assert AnnotationLevel.NOTICE == "notice"
        assert AnnotationLevel.WARNING == "warning"
        assert AnnotationLevel.FAILURE == "failure"


class TestCodeIssue:
    """Test CodeIssue class."""

    def test_initialization(self):
        """Test code issue initialization."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Test issue",
            rule_id="E501",
            severity="warning",
        )
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.message == "Test issue"
        assert issue.rule_id == "E501"
        assert issue.severity == "warning"

    def test_to_dict(self):
        """Test converting to dictionary."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Test issue",
            rule_id="E501",
            severity="warning",
        )
        issue_dict = issue.to_dict()
        assert isinstance(issue_dict, dict)
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 10
        assert issue_dict["column_number"] == 5
        assert issue_dict["message"] == "Test issue"
        assert issue_dict["rule_id"] == "E501"
        assert issue_dict["severity"] == "warning"

    def test_from_dict(self):
        """Test creating from dictionary."""
        issue_dict = {
            "file_path": "test.py",
            "line_number": 10,
            "column_number": 5,
            "message": "Test issue",
            "rule_id": "E501",
            "severity": "warning",
        }
        issue = CodeIssue.from_dict(issue_dict)
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.message == "Test issue"
        assert issue.rule_id == "E501"
        assert issue.severity == "warning"


class TestPRAnnotation:
    """Test PRAnnotation class."""

    def test_initialization(self):
        """Test PR annotation initialization."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            column_number=5,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
            title="Test Title",
        )
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.column_number == 5
        assert annotation.level == AnnotationLevel.WARNING
        assert annotation.message == "Test annotation"
        assert annotation.title == "Test Title"

    def test_to_dict(self):
        """Test converting to dictionary."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            column_number=5,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
            title="Test Title",
        )
        annotation_dict = annotation.to_dict()
        assert isinstance(annotation_dict, dict)
        assert annotation_dict["file_path"] == "test.py"
        assert annotation_dict["line_number"] == 10
        assert annotation_dict["column_number"] == 5
        assert annotation_dict["level"] == "warning"
        assert annotation_dict["message"] == "Test annotation"
        assert annotation_dict["title"] == "Test Title"


class TestPRReviewSummary:
    """Test PRReviewSummary class."""

    def test_initialization(self):
        """Test review summary initialization."""
        summary = PRReviewSummary(
            total_issues=10, critical_issues=2, warning_issues=5, info_issues=3
        )
        assert summary.total_issues == 10
        assert summary.critical_issues == 2
        assert summary.warning_issues == 5
        assert summary.info_issues == 3

    def test_to_dict(self):
        """Test converting to dictionary."""
        summary = PRReviewSummary(
            total_issues=10, critical_issues=2, warning_issues=5, info_issues=3
        )
        summary_dict = summary.to_dict()
        assert isinstance(summary_dict, dict)
        assert summary_dict["total_issues"] == 10
        assert summary_dict["critical_issues"] == 2
        assert summary_dict["warning_issues"] == 5
        assert summary_dict["info_issues"] == 3


class TestPRAnnotator:
    """Test PRAnnotator class."""

    def test_initialization(self):
        """Test annotator initialization."""
        annotator = PRAnnotator()
        assert annotator.annotations == []
        assert annotator.github_token is None
        assert annotator.repository is None
        assert annotator.pull_request_number is None

    def test_initialization_with_params(self):
        """Test annotator initialization with parameters."""
        annotator = PRAnnotator(
            github_token="test_token", repository="owner/repo", pull_request_number=123
        )
        assert annotator.github_token == "test_token"
        assert annotator.repository == "owner/repo"
        assert annotator.pull_request_number == 123

    def test_add_annotation(self):
        """Test adding annotation."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0] == annotation

    def test_add_annotations(self):
        """Test adding multiple annotations."""
        annotator = PRAnnotator()
        annotations = [
            PRAnnotation(
                file_path="test.py",
                line_number=10,
                level=AnnotationLevel.WARNING,
                message="Test annotation 1",
            ),
            PRAnnotation(
                file_path="test.py",
                line_number=20,
                level=AnnotationLevel.FAILURE,
                message="Test annotation 2",
            ),
        ]
        annotator.add_annotations(annotations)
        assert len(annotator.annotations) == 2

    def test_clear_annotations(self):
        """Test clearing annotations."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)
        annotator.clear_annotations()
        assert len(annotator.annotations) == 0

    def test_get_annotations_by_file(self):
        """Test getting annotations by file."""
        annotator = PRAnnotator()
        annotation1 = PRAnnotation(
            file_path="file1.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation 1",
        )
        annotation2 = PRAnnotation(
            file_path="file2.py",
            line_number=20,
            level=AnnotationLevel.FAILURE,
            message="Test annotation 2",
        )
        annotator.add_annotation(annotation1)
        annotator.add_annotation(annotation2)

        file1_annotations = annotator.get_annotations_by_file("file1.py")
        assert len(file1_annotations) == 1
        assert file1_annotations[0] == annotation1

        file2_annotations = annotator.get_annotations_by_file("file2.py")
        assert len(file2_annotations) == 1
        assert file2_annotations[0] == annotation2

    def test_get_annotations_by_level(self):
        """Test getting annotations by level."""
        annotator = PRAnnotator()
        annotation1 = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation 1",
        )
        annotation2 = PRAnnotation(
            file_path="test.py",
            line_number=20,
            level=AnnotationLevel.FAILURE,
            message="Test annotation 2",
        )
        annotator.add_annotation(annotation1)
        annotator.add_annotation(annotation2)

        warning_annotations = annotator.get_annotations_by_level(
            AnnotationLevel.WARNING
        )
        assert len(warning_annotations) == 1
        assert warning_annotations[0] == annotation1

        failure_annotations = annotator.get_annotations_by_level(
            AnnotationLevel.FAILURE
        )
        assert len(failure_annotations) == 1
        assert failure_annotations[0] == annotation2

    def test_get_summary(self):
        """Test getting summary."""
        annotator = PRAnnotator()
        annotation1 = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation 1",
        )
        annotation2 = PRAnnotation(
            file_path="test.py",
            line_number=20,
            level=AnnotationLevel.FAILURE,
            message="Test annotation 2",
        )
        annotator.add_annotation(annotation1)
        annotator.add_annotation(annotation2)

        summary = annotator.get_summary()
        assert summary["total_annotations"] == 2
        assert summary["by_level"]["warning"] == 1
        assert summary["by_level"]["failure"] == 1

    def test_export_annotations_json(self):
        """Test exporting annotations to JSON."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            annotator.export_annotations_json(temp_file)
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                data = json.load(f)
            assert "annotations" in data
            assert len(data["annotations"]) == 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_export_annotations_sarif(self):
        """Test exporting annotations to SARIF."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as f:
            temp_file = f.name

        try:
            annotator.export_annotations_sarif(temp_file)
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @patch("src.ai_guard.pr_annotations.requests.post")
    def test_post_annotations_to_github(self, mock_post):
        """Test posting annotations to GitHub."""
        annotator = PRAnnotator(
            github_token="test_token", repository="owner/repo", pull_request_number=123
        )
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)

        mock_post.return_value = Mock(status_code=200, json=lambda: {"id": 1})

        result = annotator.post_annotations_to_github()
        assert result is True
        mock_post.assert_called_once()

    @patch("src.ai_guard.pr_annotations.requests.post")
    def test_post_annotations_to_github_failure(self, mock_post):
        """Test posting annotations to GitHub with failure."""
        annotator = PRAnnotator(
            github_token="test_token", repository="owner/repo", pull_request_number=123
        )
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)

        mock_post.return_value = Mock(
            status_code=400, json=lambda: {"error": "Bad request"}
        )

        result = annotator.post_annotations_to_github()
        assert result is False

    def test_post_annotations_to_github_no_credentials(self):
        """Test posting annotations to GitHub without credentials."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        annotator.add_annotation(annotation)

        result = annotator.post_annotations_to_github()
        assert result is False


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_pr_annotations(self):
        """Test creating PR annotations."""
        annotations = create_pr_annotations(["test.py"])
        assert isinstance(annotations, list)

    def test_write_annotations_file(self):
        """Test writing annotations file."""
        annotations = [
            {
                "file_path": "test.py",
                "line_number": 10,
                "level": "warning",
                "message": "Test annotation",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            result = write_annotations_file(annotations, temp_file)
            assert result is True
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_parse_coverage_output(self):
        """Test parsing coverage output."""
        coverage_output = "Name                    Stmts   Miss  Cover\n----------------------------------------\ntest.py                   10      2    80%"
        result = _parse_coverage_output(coverage_output)
        assert isinstance(result, dict)

    def test_parse_lint_output(self):
        """Test parsing lint output."""
        lint_output = "test.py:10:1: E501 line too long (80 > 79 characters)"
        result = parse_lint_output(lint_output)
        assert isinstance(result, list)

    def test_parse_lint_output_none(self):
        """Test parsing None lint output."""
        result = parse_lint_output(None)
        assert result == []

    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = "test.py:10: error: Incompatible types in assignment"
        result = parse_mypy_output(mypy_output)
        assert isinstance(result, list)

    def test_parse_bandit_output(self):
        """Test parsing bandit output."""
        bandit_output = "test.py:10:1: B101: Use of assert detected"
        result = parse_bandit_output(bandit_output)
        assert isinstance(result, list)

    def test_create_pr_annotation(self):
        """Test creating PR annotation."""
        annotation = create_pr_annotation(
            file_path="test.py",
            line_number=10,
            level="warning",
            message="Test annotation",
        )
        assert isinstance(annotation, PRAnnotation)
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.level == AnnotationLevel.WARNING
        assert annotation.message == "Test annotation"

    def test_get_annotation_level(self):
        """Test getting annotation level."""
        level = get_annotation_level("warning")
        assert level == "warning"

        level = get_annotation_level("error")
        assert level == "failure"

        level = get_annotation_level("info")
        assert level == "notice"

    def test_create_quality_gate_annotation(self):
        """Test creating quality gate annotation."""
        annotation = create_quality_gate_annotation(
            file_path="test.py", line_number=10, message="Quality gate failed"
        )
        assert isinstance(annotation, PRAnnotation)
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Quality gate failed"

    def test_create_coverage_annotation(self):
        """Test creating coverage annotation."""
        annotation = create_coverage_annotation(
            file_path="test.py", line_number=10, coverage_percent=80.0
        )
        assert isinstance(annotation, PRAnnotation)
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert "80.0%" in annotation.message

    def test_create_security_annotation(self):
        """Test creating security annotation."""
        annotation = create_security_annotation(
            file_path="test.py", line_number=10, message="Security issue detected"
        )
        assert isinstance(annotation, PRAnnotation)
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Security issue detected"

    def test_create_performance_annotation(self):
        """Test creating performance annotation."""
        annotation = create_performance_annotation(
            file_path="test.py", line_number=10, message="Performance issue detected"
        )
        assert isinstance(annotation, PRAnnotation)
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Performance issue detected"

    def test_create_test_annotation(self):
        """Test creating test annotation."""
        annotation = create_test_annotation(
            file_path="test.py", line_number=10, message="Test issue detected"
        )
        assert isinstance(annotation, PRAnnotation)
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test issue detected"


class TestPRAnnotationManager:
    """Test PRAnnotationManager class."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = PRAnnotationManager()
        assert manager.annotations == []
        assert manager.summary is None

    def test_add_annotation(self):
        """Test adding annotation."""
        manager = PRAnnotationManager()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        manager.add_annotation(annotation)
        assert len(manager.annotations) == 1
        assert manager.annotations[0] == annotation

    def test_generate_summary(self):
        """Test generating summary."""
        manager = PRAnnotationManager()
        annotation1 = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation 1",
        )
        annotation2 = PRAnnotation(
            file_path="test.py",
            line_number=20,
            level=AnnotationLevel.FAILURE,
            message="Test annotation 2",
        )
        manager.add_annotation(annotation1)
        manager.add_annotation(annotation2)

        summary = manager.generate_summary()
        assert isinstance(summary, PRReviewSummary)
        assert summary.total_issues == 2
        assert summary.warning_issues == 1
        assert summary.critical_issues == 1

    def test_export_summary(self):
        """Test exporting summary."""
        manager = PRAnnotationManager()
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            level=AnnotationLevel.WARNING,
            message="Test annotation",
        )
        manager.add_annotation(annotation)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            result = manager.export_summary(temp_file)
            assert result is True
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
