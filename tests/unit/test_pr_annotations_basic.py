"""
Basic test coverage for src/ai_guard/pr_annotations.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import json

# Import the pr_annotations module
from src.ai_guard.pr_annotations import (
    create_pr_annotations,
    write_annotations_file,
    _parse_coverage_output,
    parse_lint_output,
    parse_mypy_output,
    parse_bandit_output,
    create_github_annotation,
    format_annotation_message,
    AnnotationLevel,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
)


class TestCreatePrAnnotation(unittest.TestCase):
    """Test create_pr_annotation function."""
    
    def test_create_pr_annotation_success(self):
        """Test create_pr_annotation with successful result."""
        result = {
            "passed": True,
            "exit_code": 0,
            "command": "flake8 src",
            "output": "No issues found"
        }
        
        annotation = create_pr_annotation("lint", result, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(annotation["path"], "src/ai_guard/analyzer.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 20)
        self.assertEqual(annotation["annotation_level"], "notice")
        self.assertEqual(annotation["title"], "Lint Check Passed")
        self.assertIn("No issues found", annotation["message"])
    
    def test_create_pr_annotation_failure(self):
        """Test create_pr_annotation with failed result."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "flake8 src",
            "output": "E501 line too long (120 > 79 characters)",
            "error": "Lint check failed"
        }
        
        annotation = create_pr_annotation("lint", result, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(annotation["path"], "src/ai_guard/analyzer.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 20)
        self.assertEqual(annotation["annotation_level"], "failure")
        self.assertEqual(annotation["title"], "Lint Check Failed")
        self.assertIn("E501 line too long", annotation["message"])
        self.assertIn("Lint check failed", annotation["message"])
    
    def test_create_pr_annotation_static_types(self):
        """Test create_pr_annotation with static types result."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "mypy src",
            "output": "error: Argument 1 to \"func\" has incompatible type \"str\"; expected \"int\"",
            "error": "Static type check failed"
        }
        
        annotation = create_pr_annotation("static_types", result, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(annotation["path"], "src/ai_guard/analyzer.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 20)
        self.assertEqual(annotation["annotation_level"], "failure")
        self.assertEqual(annotation["title"], "Static Type Check Failed")
        self.assertIn("Argument 1 to \"func\"", annotation["message"])
        self.assertIn("Static type check failed", annotation["message"])
    
    def test_create_pr_annotation_security(self):
        """Test create_pr_annotation with security result."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "bandit src",
            "output": "Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True",
            "error": "Security check failed"
        }
        
        annotation = create_pr_annotation("security", result, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(annotation["path"], "src/ai_guard/analyzer.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 20)
        self.assertEqual(annotation["annotation_level"], "failure")
        self.assertEqual(annotation["title"], "Security Check Failed")
        self.assertIn("subprocess call with shell=True", annotation["message"])
        self.assertIn("Security check failed", annotation["message"])
    
    def test_create_pr_annotation_coverage(self):
        """Test create_pr_annotation with coverage result."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "pytest --cov=src",
            "output": "Coverage is 45.2%, which is below the required 90%",
            "error": "Coverage check failed"
        }
        
        annotation = create_pr_annotation("coverage", result, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(annotation["path"], "src/ai_guard/analyzer.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 20)
        self.assertEqual(annotation["annotation_level"], "failure")
        self.assertEqual(annotation["title"], "Coverage Check Failed")
        self.assertIn("Coverage is 45.2%", annotation["message"])
        self.assertIn("Coverage check failed", annotation["message"])
    
    def test_create_pr_annotation_unknown_check(self):
        """Test create_pr_annotation with unknown check type."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "unknown-check src",
            "output": "Unknown check failed",
            "error": "Unknown check error"
        }
        
        annotation = create_pr_annotation("unknown", result, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(annotation["path"], "src/ai_guard/analyzer.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 20)
        self.assertEqual(annotation["annotation_level"], "failure")
        self.assertEqual(annotation["title"], "Unknown Check Failed")
        self.assertIn("Unknown check failed", annotation["message"])
        self.assertIn("Unknown check error", annotation["message"])


class TestCreatePrAnnotationsFromResults(unittest.TestCase):
    """Test create_pr_annotations_from_results function."""
    
    def test_create_pr_annotations_from_results_success(self):
        """Test create_pr_annotations_from_results with successful results."""
        results = {
            "lint": {
                "passed": True,
                "exit_code": 0,
                "command": "flake8 src",
                "output": "No issues found"
            },
            "static_types": {
                "passed": True,
                "exit_code": 0,
                "command": "mypy src",
                "output": "No type errors found"
            },
            "security": {
                "passed": True,
                "exit_code": 0,
                "command": "bandit src",
                "output": "No security issues found"
            },
            "coverage": {
                "passed": True,
                "exit_code": 0,
                "command": "pytest --cov=src",
                "output": "Coverage is 95.2%"
            }
        }
        
        annotations = create_pr_annotations_from_results(results, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(len(annotations), 4)
        
        # Check that all annotations are present
        check_types = [ann["title"].split()[0] for ann in annotations]
        self.assertIn("Lint", check_types)
        self.assertIn("Static", check_types)
        self.assertIn("Security", check_types)
        self.assertIn("Coverage", check_types)
        
        # Check that all annotations have correct level
        for annotation in annotations:
            self.assertEqual(annotation["annotation_level"], "notice")
    
    def test_create_pr_annotations_from_results_failure(self):
        """Test create_pr_annotations_from_results with failed results."""
        results = {
            "lint": {
                "passed": False,
                "exit_code": 1,
                "command": "flake8 src",
                "output": "E501 line too long",
                "error": "Lint check failed"
            },
            "static_types": {
                "passed": False,
                "exit_code": 1,
                "command": "mypy src",
                "output": "Type error found",
                "error": "Static type check failed"
            },
            "security": {
                "passed": False,
                "exit_code": 1,
                "command": "bandit src",
                "output": "Security issue found",
                "error": "Security check failed"
            },
            "coverage": {
                "passed": False,
                "exit_code": 1,
                "command": "pytest --cov=src",
                "output": "Coverage is 45.2%",
                "error": "Coverage check failed"
            }
        }
        
        annotations = create_pr_annotations_from_results(results, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(len(annotations), 4)
        
        # Check that all annotations are present
        check_types = [ann["title"].split()[0] for ann in annotations]
        self.assertIn("Lint", check_types)
        self.assertIn("Static", check_types)
        self.assertIn("Security", check_types)
        self.assertIn("Coverage", check_types)
        
        # Check that all annotations have correct level
        for annotation in annotations:
            self.assertEqual(annotation["annotation_level"], "failure")
    
    def test_create_pr_annotations_from_results_mixed(self):
        """Test create_pr_annotations_from_results with mixed results."""
        results = {
            "lint": {
                "passed": True,
                "exit_code": 0,
                "command": "flake8 src",
                "output": "No issues found"
            },
            "static_types": {
                "passed": False,
                "exit_code": 1,
                "command": "mypy src",
                "output": "Type error found",
                "error": "Static type check failed"
            },
            "security": {
                "passed": True,
                "exit_code": 0,
                "command": "bandit src",
                "output": "No security issues found"
            },
            "coverage": {
                "passed": False,
                "exit_code": 1,
                "command": "pytest --cov=src",
                "output": "Coverage is 45.2%",
                "error": "Coverage check failed"
            }
        }
        
        annotations = create_pr_annotations_from_results(results, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(len(annotations), 4)
        
        # Check that all annotations are present
        check_types = [ann["title"].split()[0] for ann in annotations]
        self.assertIn("Lint", check_types)
        self.assertIn("Static", check_types)
        self.assertIn("Security", check_types)
        self.assertIn("Coverage", check_types)
        
        # Check that annotations have correct levels
        for annotation in annotations:
            if "Lint" in annotation["title"] or "Security" in annotation["title"]:
                self.assertEqual(annotation["annotation_level"], "notice")
            else:
                self.assertEqual(annotation["annotation_level"], "failure")
    
    def test_create_pr_annotations_from_results_empty(self):
        """Test create_pr_annotations_from_results with empty results."""
        results = {}
        
        annotations = create_pr_annotations_from_results(results, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(len(annotations), 0)
    
    def test_create_pr_annotations_from_results_partial(self):
        """Test create_pr_annotations_from_results with partial results."""
        results = {
            "lint": {
                "passed": True,
                "exit_code": 0,
                "command": "flake8 src",
                "output": "No issues found"
            },
            "coverage": {
                "passed": False,
                "exit_code": 1,
                "command": "pytest --cov=src",
                "output": "Coverage is 45.2%",
                "error": "Coverage check failed"
            }
        }
        
        annotations = create_pr_annotations_from_results(results, "src/ai_guard/analyzer.py", 10, 20)
        
        self.assertEqual(len(annotations), 2)
        
        # Check that only present annotations are created
        check_types = [ann["title"].split()[0] for ann in annotations]
        self.assertIn("Lint", check_types)
        self.assertIn("Coverage", check_types)
        self.assertNotIn("Static", check_types)
        self.assertNotIn("Security", check_types)


class TestFormatAnnotationMessage(unittest.TestCase):
    """Test format_annotation_message function."""
    
    def test_format_annotation_message_success(self):
        """Test format_annotation_message with successful result."""
        result = {
            "passed": True,
            "exit_code": 0,
            "command": "flake8 src",
            "output": "No issues found"
        }
        
        message = format_annotation_message("lint", result)
        
        self.assertIn("Lint check passed", message)
        self.assertIn("No issues found", message)
        self.assertIn("flake8 src", message)
    
    def test_format_annotation_message_failure(self):
        """Test format_annotation_message with failed result."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "flake8 src",
            "output": "E501 line too long",
            "error": "Lint check failed"
        }
        
        message = format_annotation_message("lint", result)
        
        self.assertIn("Lint check failed", message)
        self.assertIn("E501 line too long", message)
        self.assertIn("Lint check failed", message)
        self.assertIn("flake8 src", message)
    
    def test_format_annotation_message_no_output(self):
        """Test format_annotation_message with no output."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "flake8 src",
            "error": "Lint check failed"
        }
        
        message = format_annotation_message("lint", result)
        
        self.assertIn("Lint check failed", message)
        self.assertIn("Lint check failed", message)
        self.assertIn("flake8 src", message)
    
    def test_format_annotation_message_no_error(self):
        """Test format_annotation_message with no error."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "flake8 src",
            "output": "E501 line too long"
        }
        
        message = format_annotation_message("lint", result)
        
        self.assertIn("Lint check failed", message)
        self.assertIn("E501 line too long", message)
        self.assertIn("flake8 src", message)
    
    def test_format_annotation_message_unknown_check(self):
        """Test format_annotation_message with unknown check type."""
        result = {
            "passed": False,
            "exit_code": 1,
            "command": "unknown-check src",
            "output": "Unknown check failed",
            "error": "Unknown check error"
        }
        
        message = format_annotation_message("unknown", result)
        
        self.assertIn("Unknown check failed", message)
        self.assertIn("Unknown check failed", message)
        self.assertIn("Unknown check error", message)
        self.assertIn("unknown-check src", message)


class TestGetAnnotationLevel(unittest.TestCase):
    """Test get_annotation_level function."""
    
    def test_get_annotation_level_success(self):
        """Test get_annotation_level with successful result."""
        result = {
            "passed": True,
            "exit_code": 0
        }
        
        level = get_annotation_level(result)
        
        self.assertEqual(level, "notice")
    
    def test_get_annotation_level_failure(self):
        """Test get_annotation_level with failed result."""
        result = {
            "passed": False,
            "exit_code": 1
        }
        
        level = get_annotation_level(result)
        
        self.assertEqual(level, "failure")
    
    def test_get_annotation_level_exception(self):
        """Test get_annotation_level with exception result."""
        result = {
            "passed": False,
            "exit_code": -1,
            "error": "Exception occurred"
        }
        
        level = get_annotation_level(result)
        
        self.assertEqual(level, "failure")


class TestGetAnnotationTitle(unittest.TestCase):
    """Test get_annotation_title function."""
    
    def test_get_annotation_title_lint_success(self):
        """Test get_annotation_title with successful lint check."""
        result = {
            "passed": True,
            "exit_code": 0
        }
        
        title = get_annotation_title("lint", result)
        
        self.assertEqual(title, "Lint Check Passed")
    
    def test_get_annotation_title_lint_failure(self):
        """Test get_annotation_title with failed lint check."""
        result = {
            "passed": False,
            "exit_code": 1
        }
        
        title = get_annotation_title("lint", result)
        
        self.assertEqual(title, "Lint Check Failed")
    
    def test_get_annotation_title_static_types_success(self):
        """Test get_annotation_title with successful static types check."""
        result = {
            "passed": True,
            "exit_code": 0
        }
        
        title = get_annotation_title("static_types", result)
        
        self.assertEqual(title, "Static Type Check Passed")
    
    def test_get_annotation_title_static_types_failure(self):
        """Test get_annotation_title with failed static types check."""
        result = {
            "passed": False,
            "exit_code": 1
        }
        
        title = get_annotation_title("static_types", result)
        
        self.assertEqual(title, "Static Type Check Failed")
    
    def test_get_annotation_title_security_success(self):
        """Test get_annotation_title with successful security check."""
        result = {
            "passed": True,
            "exit_code": 0
        }
        
        title = get_annotation_title("security", result)
        
        self.assertEqual(title, "Security Check Passed")
    
    def test_get_annotation_title_security_failure(self):
        """Test get_annotation_title with failed security check."""
        result = {
            "passed": False,
            "exit_code": 1
        }
        
        title = get_annotation_title("security", result)
        
        self.assertEqual(title, "Security Check Failed")
    
    def test_get_annotation_title_coverage_success(self):
        """Test get_annotation_title with successful coverage check."""
        result = {
            "passed": True,
            "exit_code": 0
        }
        
        title = get_annotation_title("coverage", result)
        
        self.assertEqual(title, "Coverage Check Passed")
    
    def test_get_annotation_title_coverage_failure(self):
        """Test get_annotation_title with failed coverage check."""
        result = {
            "passed": False,
            "exit_code": 1
        }
        
        title = get_annotation_title("coverage", result)
        
        self.assertEqual(title, "Coverage Check Failed")
    
    def test_get_annotation_title_unknown_success(self):
        """Test get_annotation_title with successful unknown check."""
        result = {
            "passed": True,
            "exit_code": 0
        }
        
        title = get_annotation_title("unknown", result)
        
        self.assertEqual(title, "Unknown Check Passed")
    
    def test_get_annotation_title_unknown_failure(self):
        """Test get_annotation_title with failed unknown check."""
        result = {
            "passed": False,
            "exit_code": 1
        }
        
        title = get_annotation_title("unknown", result)
        
        self.assertEqual(title, "Unknown Check Failed")


if __name__ == '__main__':
    unittest.main()
