"""Focused tests for pr_annotations.py module to improve coverage."""

import json
import unittest
from unittest.mock import patch, mock_open

from src.ai_guard.pr_annotations import (
    AnnotationLevel,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
    format_annotation_message,
)


class TestCodeIssue(unittest.TestCase):
    """Test CodeIssue dataclass."""

    def test_code_issue_creation(self):
        """Test creating a CodeIssue instance."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        
        self.assertEqual(issue.file_path, "test.py")
        self.assertEqual(issue.line_number, 10)
        self.assertEqual(issue.severity, "error")

    def test_code_issue_to_dict(self):
        """Test converting CodeIssue to dictionary."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        
        result = issue.to_dict()
        self.assertIn("file_path", result)
        self.assertEqual(result["file_path"], "test.py")


class TestPRAnnotation(unittest.TestCase):
    """Test PRAnnotation dataclass."""

    def test_pr_annotation_creation(self):
        """Test creating a PRAnnotation instance."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test annotation",
            annotation_level="failure",
            title="Test Title"
        )
        
        self.assertEqual(annotation.file_path, "test.py")
        self.assertEqual(annotation.annotation_level, "failure")

    def test_pr_annotation_optional_fields(self):
        """Test PRAnnotation with optional fields."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test annotation",
            annotation_level="warning",
            start_line=10,
            end_line=12,
            start_column=5,
            end_column=10
        )
        
        self.assertEqual(annotation.start_line, 10)
        self.assertEqual(annotation.end_line, 12)
        self.assertEqual(annotation.start_column, 5)
        self.assertEqual(annotation.end_column, 10)


class TestPRAnnotator(unittest.TestCase):
    """Test PRAnnotator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.annotator = PRAnnotator()

    def test_add_issue(self):
        """Test adding an issue."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        
        self.annotator.add_issue(issue)
        self.assertEqual(len(self.annotator.annotations), 1)
        self.assertEqual(len(self.annotator.issues), 1)

    def test_add_lint_issues(self):
        """Test adding lint issues."""
        lint_output = [
            {
                "file": "test.py",
                "line": 10,
                "column": 5,
                "severity": "warning",
                "message": "line too long",
                "rule": "E501"
            }
        ]
        
        self.annotator.add_lint_issues(lint_output)
        self.assertEqual(len(self.annotator.annotations), 1)
        self.assertEqual(len(self.annotator.issues), 1)

    def test_issue_to_annotation_conversion(self):
        """Test converting issue to annotation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix this",
            fix_code="fixed_code()"
        )
        
        annotation = self.annotator._issue_to_annotation(issue)
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.file_path, "test.py")
        self.assertEqual(annotation.annotation_level, "failure")
        self.assertIn("Test error", annotation.message)
        self.assertIn("Fix this", annotation.message)
        self.assertIn("fixed_code()", annotation.message)

    def test_issue_to_annotation_warning(self):
        """Test converting warning issue to annotation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=15,
            column=3,
            severity="warning",
            message="Test warning",
            rule_id="W001"
        )
        
        annotation = self.annotator._issue_to_annotation(issue)
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.annotation_level, "warning")

    def test_issue_to_annotation_info(self):
        """Test converting info issue to annotation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=20,
            column=1,
            severity="info",
            message="Test info",
            rule_id="I001"
        )
        
        annotation = self.annotator._issue_to_annotation(issue)
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.annotation_level, "notice")


if __name__ == "__main__":
    unittest.main()
