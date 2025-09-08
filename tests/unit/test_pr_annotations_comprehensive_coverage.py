"""
Comprehensive test coverage for src/ai_guard/pr_annotations.py
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

# Import the pr_annotations module
from src.ai_guard.pr_annotations import (
    AnnotationLevel,
    CodeIssue,
    PRAnnotation,
    PRAnnotator
)


class TestAnnotationLevel(unittest.TestCase):
    """Test AnnotationLevel enum."""
    
    def test_annotation_level_values(self):
        """Test AnnotationLevel enum values."""
        self.assertEqual(AnnotationLevel.NOTICE.value, "notice")
        self.assertEqual(AnnotationLevel.WARNING.value, "warning")
        self.assertEqual(AnnotationLevel.FAILURE.value, "failure")
    
    def test_annotation_level_enumeration(self):
        """Test AnnotationLevel enumeration."""
        levels = list(AnnotationLevel)
        self.assertEqual(len(levels), 3)
        self.assertIn(AnnotationLevel.NOTICE, levels)
        self.assertIn(AnnotationLevel.WARNING, levels)
        self.assertIn(AnnotationLevel.FAILURE, levels)


class TestCodeIssue(unittest.TestCase):
    """Test CodeIssue dataclass."""
    
    def test_code_issue_creation(self):
        """Test creating CodeIssue with all fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=42,
            column=10,
            message="Test issue",
            severity="error",
            rule_id="TEST001"
        )
        
        self.assertEqual(issue.file_path, "src/test.py")
        self.assertEqual(issue.line_number, 42)
        self.assertEqual(issue.column, 10)
        self.assertEqual(issue.message, "Test issue")
        self.assertEqual(issue.severity, "error")
        self.assertEqual(issue.rule_id, "TEST001")
    
    def test_code_issue_defaults(self):
        """Test CodeIssue with default values."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=0,
            message="Test issue",
            severity="info",
            rule_id=""
        )
        
        self.assertEqual(issue.file_path, "src/test.py")
        self.assertEqual(issue.line_number, 10)
        self.assertEqual(issue.column, 0)
        self.assertEqual(issue.message, "Test issue")
        self.assertEqual(issue.severity, "info")
        self.assertEqual(issue.rule_id, "")
    
    def test_code_issue_to_dict(self):
        """Test converting CodeIssue to dictionary."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=15,
            column=5,
            message="Test issue",
            severity="warning",
            rule_id="TEST002"
        )
        
        issue_dict = issue.to_dict()
        
        expected = {
            "file_path": "src/test.py",
            "line_number": 15,
            "column": 5,
            "message": "Test issue",
            "severity": "warning",
            "rule_id": "TEST002",
            "suggestion": None,
            "fix_code": None
        }
        
        self.assertEqual(issue_dict, expected)


class TestPRAnnotation(unittest.TestCase):
    """Test PRAnnotation dataclass."""
    
    def test_pr_annotation_creation(self):
        """Test creating PRAnnotation with all fields."""
        annotation = PRAnnotation(
            path="src/test.py",
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=10,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation",
            title="Test Title",
            raw_details="Raw details here"
        )
        
        self.assertEqual(annotation.path, "src/test.py")
        self.assertEqual(annotation.start_line, 10)
        self.assertEqual(annotation.end_line, 15)
        self.assertEqual(annotation.start_column, 5)
        self.assertEqual(annotation.end_column, 10)
        self.assertEqual(annotation.annotation_level, AnnotationLevel.WARNING)
        self.assertEqual(annotation.message, "Test annotation")
        self.assertEqual(annotation.title, "Test Title")
        self.assertEqual(annotation.raw_details, "Raw details here")
    
    def test_pr_annotation_defaults(self):
        """Test PRAnnotation with default values."""
        annotation = PRAnnotation(
            path="src/test.py",
            start_line=20,
            annotation_level=AnnotationLevel.NOTICE,
            message="Test annotation"
        )
        
        self.assertEqual(annotation.path, "src/test.py")
        self.assertEqual(annotation.start_line, 20)
        self.assertEqual(annotation.end_line, 20)
        self.assertEqual(annotation.start_column, 0)
        self.assertEqual(annotation.end_column, 0)
        self.assertEqual(annotation.annotation_level, AnnotationLevel.NOTICE)
        self.assertEqual(annotation.message, "Test annotation")
        self.assertEqual(annotation.title, "")
        self.assertEqual(annotation.raw_details, "")
    
    def test_pr_annotation_to_dict(self):
        """Test converting PRAnnotation to dictionary."""
        annotation = PRAnnotation(
            path="src/test.py",
            start_line=25,
            end_line=30,
            start_column=10,
            end_column=15,
            annotation_level=AnnotationLevel.FAILURE,
            message="Test annotation",
            title="Test Title",
            raw_details="Raw details"
        )
        
        annotation_dict = annotation.to_dict()
        
        expected = {
            "path": "src/test.py",
            "start_line": 25,
            "end_line": 30,
            "start_column": 10,
            "end_column": 15,
            "annotation_level": "failure",
            "message": "Test annotation",
            "title": "Test Title",
            "raw_details": "Raw details"
        }
        
        self.assertEqual(annotation_dict, expected)


class TestPRAnnotator(unittest.TestCase):
    """Test PRAnnotator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.annotator = PRAnnotator()
    
    def test_pr_annotator_initialization(self):
        """Test PRAnnotator initialization."""
        self.assertEqual(self.annotator.annotations, [])
        self.assertEqual(self.annotator.max_annotations, 50)
    
    def test_pr_annotator_with_max_annotations(self):
        """Test PRAnnotator with custom max_annotations."""
        annotator = PRAnnotator(max_annotations=100)
        self.assertEqual(annotator.max_annotations, 100)
    
    def test_add_annotation(self):
        """Test adding annotation to annotator."""
        annotation = PRAnnotation(
            path="src/test.py",
            start_line=10,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation"
        )
        
        self.annotator.add_annotation(annotation)
        
        self.assertEqual(len(self.annotator.annotations), 1)
        self.assertEqual(self.annotator.annotations[0], annotation)
    
    def test_add_annotation_max_limit(self):
        """Test adding annotations up to max limit."""
        # Set a small max limit for testing
        annotator = PRAnnotator(max_annotations=3)
        
        for i in range(5):
            annotation = PRAnnotation(
                path=f"src/test{i}.py",
                start_line=i,
                annotation_level=AnnotationLevel.WARNING,
                message=f"Test annotation {i}"
            )
            annotator.add_annotation(annotation)
        
        # Should only have 3 annotations (max limit)
        self.assertEqual(len(annotator.annotations), 3)
    
    def test_add_annotation_from_issue(self):
        """Test adding annotation from CodeIssue."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=15,
            column_number=5,
            message="Test issue",
            severity="error",
            rule_id="TEST001",
            tool_name="test_tool"
        )
        
        self.annotator.add_annotation_from_issue(issue)
        
        self.assertEqual(len(self.annotator.annotations), 1)
        annotation = self.annotator.annotations[0]
        self.assertEqual(annotation.path, "src/test.py")
        self.assertEqual(annotation.start_line, 15)
        self.assertEqual(annotation.start_column, 5)
        self.assertEqual(annotation.annotation_level, AnnotationLevel.FAILURE)
        self.assertIn("Test issue", annotation.message)
        self.assertIn("TEST001", annotation.message)
        self.assertIn("test_tool", annotation.message)
    
    def test_add_annotation_from_issue_warning_severity(self):
        """Test adding annotation from CodeIssue with warning severity."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=20,
            message="Warning issue",
            severity="warning"
        )
        
        self.annotator.add_annotation_from_issue(issue)
        
        annotation = self.annotator.annotations[0]
        self.assertEqual(annotation.annotation_level, AnnotationLevel.WARNING)
    
    def test_add_annotation_from_issue_info_severity(self):
        """Test adding annotation from CodeIssue with info severity."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=25,
            message="Info issue",
            severity="info"
        )
        
        self.annotator.add_annotation_from_issue(issue)
        
        annotation = self.annotator.annotations[0]
        self.assertEqual(annotation.annotation_level, AnnotationLevel.NOTICE)
    
    def test_get_annotations(self):
        """Test getting all annotations."""
        # Add some annotations
        for i in range(3):
            annotation = PRAnnotation(
                path=f"src/test{i}.py",
                start_line=i,
                annotation_level=AnnotationLevel.WARNING,
                message=f"Test annotation {i}"
            )
            self.annotator.add_annotation(annotation)
        
        annotations = self.annotator.get_annotations()
        self.assertEqual(len(annotations), 3)
    
    def test_clear_annotations(self):
        """Test clearing all annotations."""
        # Add some annotations
        for i in range(3):
            annotation = PRAnnotation(
                path=f"src/test{i}.py",
                start_line=i,
                annotation_level=AnnotationLevel.WARNING,
                message=f"Test annotation {i}"
            )
            self.annotator.add_annotation(annotation)
        
        # Clear annotations
        self.annotator.clear_annotations()
        
        self.assertEqual(len(self.annotator.annotations), 0)
    
    def test_get_annotation_summary(self):
        """Test getting annotation summary."""
        # Add annotations with different levels
        notice_annotation = PRAnnotation(
            path="src/test1.py",
            start_line=10,
            annotation_level=AnnotationLevel.NOTICE,
            message="Notice"
        )
        warning_annotation = PRAnnotation(
            path="src/test2.py",
            start_line=20,
            annotation_level=AnnotationLevel.WARNING,
            message="Warning"
        )
        failure_annotation = PRAnnotation(
            path="src/test3.py",
            start_line=30,
            annotation_level=AnnotationLevel.FAILURE,
            message="Failure"
        )
        
        self.annotator.add_annotation(notice_annotation)
        self.annotator.add_annotation(warning_annotation)
        self.annotator.add_annotation(failure_annotation)
        
        summary = self.annotator.get_annotation_summary()
        
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["notice"], 1)
        self.assertEqual(summary["warning"], 1)
        self.assertEqual(summary["failure"], 1)
    
    def test_get_annotations_by_level(self):
        """Test getting annotations by level."""
        # Add annotations with different levels
        notice_annotation = PRAnnotation(
            path="src/test1.py",
            start_line=10,
            annotation_level=AnnotationLevel.NOTICE,
            message="Notice"
        )
        warning_annotation = PRAnnotation(
            path="src/test2.py",
            start_line=20,
            annotation_level=AnnotationLevel.WARNING,
            message="Warning"
        )
        
        self.annotator.add_annotation(notice_annotation)
        self.annotator.add_annotation(warning_annotation)
        
        # Get warnings only
        warnings = self.annotator.get_annotations_by_level(AnnotationLevel.WARNING)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], warning_annotation)
        
        # Get notices only
        notices = self.annotator.get_annotations_by_level(AnnotationLevel.NOTICE)
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0], notice_annotation)
    
    def test_get_annotations_by_file(self):
        """Test getting annotations by file path."""
        # Add annotations for different files
        annotation1 = PRAnnotation(
            path="src/test1.py",
            start_line=10,
            annotation_level=AnnotationLevel.WARNING,
            message="Warning 1"
        )
        annotation2 = PRAnnotation(
            path="src/test2.py",
            start_line=20,
            annotation_level=AnnotationLevel.WARNING,
            message="Warning 2"
        )
        annotation3 = PRAnnotation(
            path="src/test1.py",
            start_line=30,
            annotation_level=AnnotationLevel.WARNING,
            message="Warning 3"
        )
        
        self.annotator.add_annotation(annotation1)
        self.annotator.add_annotation(annotation2)
        self.annotator.add_annotation(annotation3)
        
        # Get annotations for test1.py
        test1_annotations = self.annotator.get_annotations_by_file("src/test1.py")
        self.assertEqual(len(test1_annotations), 2)
        self.assertIn(annotation1, test1_annotations)
        self.assertIn(annotation3, test1_annotations)
        
        # Get annotations for test2.py
        test2_annotations = self.annotator.get_annotations_by_file("src/test2.py")
        self.assertEqual(len(test2_annotations), 1)
        self.assertIn(annotation2, test2_annotations)


# Note: Utility functions like create_annotation, create_annotations_from_issues, 
# delete_annotations, and format_annotation_message are not available in the current
# implementation, so these tests are removed.


class TestPRAnnotatorIntegration(unittest.TestCase):
    """Integration tests for PRAnnotator."""
    
    def test_full_workflow(self):
        """Test complete annotation workflow."""
        annotator = PRAnnotator(max_annotations=10)
        
        # Create issues
        issues = [
            CodeIssue(
                file_path="src/test1.py",
                line_number=10,
                message="Error issue",
                severity="error",
                rule_id="ERR001"
            ),
            CodeIssue(
                file_path="src/test2.py",
                line_number=20,
                message="Warning issue",
                severity="warning",
                rule_id="WARN001"
            ),
            CodeIssue(
                file_path="src/test3.py",
                line_number=30,
                message="Info issue",
                severity="info",
                rule_id="INFO001"
            )
        ]
        
        # Add annotations from issues
        for issue in issues:
            annotator.add_annotation_from_issue(issue)
        
        # Check annotations were added
        self.assertEqual(len(annotator.annotations), 3)
        
        # Get summary
        summary = annotator.get_annotation_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["failure"], 1)
        self.assertEqual(summary["warning"], 1)
        self.assertEqual(summary["notice"], 1)
        
        # Get annotations by level
        failures = annotator.get_annotations_by_level(AnnotationLevel.FAILURE)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].path, "src/test1.py")
        
        # Get annotations by file
        test1_annotations = annotator.get_annotations_by_file("src/test1.py")
        self.assertEqual(len(test1_annotations), 1)
        
        # Clear annotations
        annotator.clear_annotations()
        self.assertEqual(len(annotator.annotations), 0)
    
    def test_annotation_limits(self):
        """Test annotation limits and overflow handling."""
        annotator = PRAnnotator(max_annotations=2)
        
        # Add more annotations than the limit
        for i in range(5):
            issue = CodeIssue(
                file_path=f"src/test{i}.py",
                line_number=i,
                message=f"Issue {i}",
                severity="error"
            )
            annotator.add_annotation_from_issue(issue)
        
        # Should only have 2 annotations (the limit)
        self.assertEqual(len(annotator.annotations), 2)
        
        # Should have the last 2 annotations
        paths = [ann.path for ann in annotator.annotations]
        self.assertIn("src/test3.py", paths)
        self.assertIn("src/test4.py", paths)


if __name__ == '__main__':
    unittest.main()