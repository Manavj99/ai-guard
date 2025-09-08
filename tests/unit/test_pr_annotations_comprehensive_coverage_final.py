"""
Comprehensive test coverage for src/ai_guard/pr_annotations.py
This test file aims to achieve maximum coverage for the pr_annotations module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import os
from typing import List, Dict, Any

# Import the pr_annotations module
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
    create_github_annotation,
    format_annotation_message,
    main
)


class TestAnnotationLevel(unittest.TestCase):
    """Test AnnotationLevel enum."""
    
    def test_annotation_level_values(self):
        """Test AnnotationLevel enum values."""
        self.assertEqual(AnnotationLevel.NOTICE, "notice")
        self.assertEqual(AnnotationLevel.WARNING, "warning")
        self.assertEqual(AnnotationLevel.FAILURE, "failure")


class TestCodeIssue(unittest.TestCase):
    """Test CodeIssue class."""
    
    def test_code_issue_initialization(self):
        """Test CodeIssue initialization."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            severity="error"
        )
        
        self.assertEqual(issue.file_path, "test.py")
        self.assertEqual(issue.line_number, 10)
        self.assertEqual(issue.column_number, 5)
        self.assertEqual(issue.rule_id, "E501")
        self.assertEqual(issue.message, "line too long")
        self.assertEqual(issue.severity, "error")
    
    def test_code_issue_optional_parameters(self):
        """Test CodeIssue with optional parameters."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long"
        )
        
        self.assertEqual(issue.severity, "error")  # Default value
        self.assertIsNone(issue.end_line_number)
        self.assertIsNone(issue.end_column_number)
    
    def test_code_issue_with_end_positions(self):
        """Test CodeIssue with end line and column numbers."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            end_line_number=10,
            end_column_number=80
        )
        
        self.assertEqual(issue.end_line_number, 10)
        self.assertEqual(issue.end_column_number, 80)


class TestPRAnnotation(unittest.TestCase):
    """Test PRAnnotation class."""
    
    def test_pr_annotation_initialization(self):
        """Test PRAnnotation initialization."""
        annotation = PRAnnotation(
            file_path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=80,
            level=AnnotationLevel.WARNING,
            message="line too long",
            title="Line Length Violation"
        )
        
        self.assertEqual(annotation.file_path, "test.py")
        self.assertEqual(annotation.start_line, 10)
        self.assertEqual(annotation.end_line, 10)
        self.assertEqual(annotation.start_column, 5)
        self.assertEqual(annotation.end_column, 80)
        self.assertEqual(annotation.level, AnnotationLevel.WARNING)
        self.assertEqual(annotation.message, "line too long")
        self.assertEqual(annotation.title, "Line Length Violation")
    
    def test_pr_annotation_optional_parameters(self):
        """Test PRAnnotation with optional parameters."""
        annotation = PRAnnotation(
            file_path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=80,
            level=AnnotationLevel.WARNING,
            message="line too long"
        )
        
        self.assertIsNone(annotation.title)  # Default value


class TestPRReviewSummary(unittest.TestCase):
    """Test PRReviewSummary class."""
    
    def test_pr_review_summary_initialization(self):
        """Test PRReviewSummary initialization."""
        summary = PRReviewSummary(
            total_issues=5,
            error_count=2,
            warning_count=2,
            notice_count=1,
            files_affected=3
        )
        
        self.assertEqual(summary.total_issues, 5)
        self.assertEqual(summary.error_count, 2)
        self.assertEqual(summary.warning_count, 2)
        self.assertEqual(summary.notice_count, 1)
        self.assertEqual(summary.files_affected, 3)
    
    def test_pr_review_summary_optional_parameters(self):
        """Test PRReviewSummary with optional parameters."""
        summary = PRReviewSummary(total_issues=5)
        
        self.assertEqual(summary.error_count, 0)  # Default value
        self.assertEqual(summary.warning_count, 0)  # Default value
        self.assertEqual(summary.notice_count, 0)  # Default value
        self.assertEqual(summary.files_affected, 0)  # Default value


class TestPRAnnotator(unittest.TestCase):
    """Test PRAnnotator class."""
    
    def test_pr_annotator_initialization(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()
        
        self.assertIsInstance(annotator.annotations, list)
        self.assertEqual(len(annotator.annotations), 0)
        self.assertIsNone(annotator.summary)
    
    def test_add_annotation(self):
        """Test adding annotation."""
        annotator = PRAnnotator()
        annotation = PRAnnotation(
            file_path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=80,
            level=AnnotationLevel.WARNING,
            message="line too long"
        )
        
        annotator.add_annotation(annotation)
        
        self.assertEqual(len(annotator.annotations), 1)
        self.assertEqual(annotator.annotations[0], annotation)
    
    def test_add_issue(self):
        """Test adding issue."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long"
        )
        
        annotator.add_issue(issue)
        
        self.assertEqual(len(annotator.annotations), 1)
        annotation = annotator.annotations[0]
        self.assertEqual(annotation.file_path, "test.py")
        self.assertEqual(annotation.start_line, 10)
        self.assertEqual(annotation.level, AnnotationLevel.FAILURE)  # Default for error severity
    
    def test_add_issue_warning_severity(self):
        """Test adding issue with warning severity."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="W293",
            message="blank line contains whitespace",
            severity="warning"
        )
        
        annotator.add_issue(issue)
        
        annotation = annotator.annotations[0]
        self.assertEqual(annotation.level, AnnotationLevel.WARNING)
    
    def test_add_issue_notice_severity(self):
        """Test adding issue with notice severity."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="B101",
            message="Use of assert detected",
            severity="info"
        )
        
        annotator.add_issue(issue)
        
        annotation = annotator.annotations[0]
        self.assertEqual(annotation.level, AnnotationLevel.NOTICE)
    
    def test_generate_summary(self):
        """Test generating summary."""
        annotator = PRAnnotator()
        
        # Add some annotations
        annotation1 = PRAnnotation(
            file_path="test1.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=80,
            level=AnnotationLevel.FAILURE,
            message="error 1"
        )
        annotation2 = PRAnnotation(
            file_path="test2.py",
            start_line=20,
            end_line=20,
            start_column=1,
            end_column=50,
            level=AnnotationLevel.WARNING,
            message="warning 1"
        )
        annotation3 = PRAnnotation(
            file_path="test1.py",
            start_line=30,
            end_line=30,
            start_column=1,
            end_column=10,
            level=AnnotationLevel.NOTICE,
            message="notice 1"
        )
        
        annotator.add_annotation(annotation1)
        annotator.add_annotation(annotation2)
        annotator.add_annotation(annotation3)
        
        summary = annotator.generate_summary()
        
        self.assertEqual(summary.total_issues, 3)
        self.assertEqual(summary.error_count, 1)
        self.assertEqual(summary.warning_count, 1)
        self.assertEqual(summary.notice_count, 1)
        self.assertEqual(summary.files_affected, 2)  # test1.py and test2.py
    
    def test_clear_annotations(self):
        """Test clearing annotations."""
        annotator = PRAnnotator()
        
        # Add some annotations
        annotation = PRAnnotation(
            file_path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=80,
            level=AnnotationLevel.WARNING,
            message="line too long"
        )
        annotator.add_annotation(annotation)
        
        self.assertEqual(len(annotator.annotations), 1)
        
        annotator.clear_annotations()
        
        self.assertEqual(len(annotator.annotations), 0)
        self.assertIsNone(annotator.summary)
    
    def test_get_annotations_for_file(self):
        """Test getting annotations for specific file."""
        annotator = PRAnnotator()
        
        # Add annotations for different files
        annotation1 = PRAnnotation(
            file_path="test1.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=80,
            level=AnnotationLevel.WARNING,
            message="warning in test1.py"
        )
        annotation2 = PRAnnotation(
            file_path="test2.py",
            start_line=20,
            end_line=20,
            start_column=1,
            end_column=50,
            level=AnnotationLevel.FAILURE,
            message="error in test2.py"
        )
        annotation3 = PRAnnotation(
            file_path="test1.py",
            start_line=30,
            end_line=30,
            start_column=1,
            end_column=10,
            level=AnnotationLevel.NOTICE,
            message="notice in test1.py"
        )
        
        annotator.add_annotation(annotation1)
        annotator.add_annotation(annotation2)
        annotator.add_annotation(annotation3)
        
        # Get annotations for test1.py
        test1_annotations = annotator.get_annotations_for_file("test1.py")
        self.assertEqual(len(test1_annotations), 2)
        self.assertEqual(test1_annotations[0].file_path, "test1.py")
        self.assertEqual(test1_annotations[1].file_path, "test1.py")
        
        # Get annotations for test2.py
        test2_annotations = annotator.get_annotations_for_file("test2.py")
        self.assertEqual(len(test2_annotations), 1)
        self.assertEqual(test2_annotations[0].file_path, "test2.py")
        
        # Get annotations for nonexistent file
        nonexistent_annotations = annotator.get_annotations_for_file("nonexistent.py")
        self.assertEqual(len(nonexistent_annotations), 0)


class TestCreatePRAnnotations(unittest.TestCase):
    """Test create_pr_annotations function."""
    
    def test_create_pr_annotations_basic(self):
        """Test basic PR annotations creation."""
        issues = [
            CodeIssue(
                file_path="test.py",
                line_number=10,
                column_number=5,
                rule_id="E501",
                message="line too long",
                severity="error"
            ),
            CodeIssue(
                file_path="test.py",
                line_number=20,
                column_number=1,
                rule_id="W293",
                message="blank line contains whitespace",
                severity="warning"
            )
        ]
        
        annotations = create_pr_annotations(issues)
        
        self.assertEqual(len(annotations), 2)
        self.assertEqual(annotations[0].file_path, "test.py")
        self.assertEqual(annotations[0].start_line, 10)
        self.assertEqual(annotations[0].level, AnnotationLevel.FAILURE)
        self.assertEqual(annotations[1].level, AnnotationLevel.WARNING)
    
    def test_create_pr_annotations_empty(self):
        """Test PR annotations creation with empty issues list."""
        annotations = create_pr_annotations([])
        self.assertEqual(len(annotations), 0)
    
    def test_create_pr_annotations_with_end_positions(self):
        """Test PR annotations creation with end positions."""
        issues = [
            CodeIssue(
                file_path="test.py",
                line_number=10,
                column_number=5,
                rule_id="E501",
                message="line too long",
                severity="error",
                end_line_number=10,
                end_column_number=80
            )
        ]
        
        annotations = create_pr_annotations(issues)
        
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].end_line, 10)
        self.assertEqual(annotations[0].end_column, 80)


class TestWriteAnnotationsFile(unittest.TestCase):
    """Test write_annotations_file function."""
    
    def test_write_annotations_file(self):
        """Test writing annotations to file."""
        annotations = [
            {
                "file_path": "test.py",
                "start_line": 10,
                "end_line": 10,
                "start_column": 5,
                "end_column": 80,
                "level": "warning",
                "message": "line too long",
                "title": "Line Length Violation"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            result = write_annotations_file(annotations, temp_path)
            self.assertTrue(result)
            
            # Verify file was written
            with open(temp_path, 'r') as f:
                data = json.load(f)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]["file_path"], "test.py")
        finally:
            os.unlink(temp_path)
    
    def test_write_annotations_file_empty(self):
        """Test writing empty annotations to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            result = write_annotations_file([], temp_path)
            self.assertTrue(result)
            
            # Verify file was written
            with open(temp_path, 'r') as f:
                data = json.load(f)
                self.assertEqual(len(data), 0)
        finally:
            os.unlink(temp_path)
    
    def test_write_annotations_file_error(self):
        """Test writing annotations file with error."""
        annotations = [{"test": "data"}]
        
        # Try to write to a directory (should fail)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_annotations_file(annotations, temp_dir)
            self.assertFalse(result)


class TestParseCoverageOutput(unittest.TestCase):
    """Test _parse_coverage_output function."""
    
    def test_parse_coverage_output_valid(self):
        """Test parsing valid coverage output."""
        coverage_output = """Name                     Stmts   Miss  Cover   Missing
-----------------------------------------------------
test_module.py             10      2    80%   3, 7
other_module.py             5      0   100%
-----------------------------------------------------
TOTAL                      15      2    87%"""
        
        result = _parse_coverage_output(coverage_output)
        
        self.assertIn("test_module.py", result)
        self.assertIn("other_module.py", result)
        
        test_module = result["test_module.py"]
        self.assertEqual(test_module["statements"], 10)
        self.assertEqual(test_module["missing"], 2)
        self.assertEqual(test_module["coverage"], 80)
        self.assertEqual(test_module["missing_lines"], "3, 7")
        
        other_module = result["other_module.py"]
        self.assertEqual(other_module["statements"], 5)
        self.assertEqual(other_module["missing"], 0)
        self.assertEqual(other_module["coverage"], 100)
        self.assertEqual(other_module["missing_lines"], "")
    
    def test_parse_coverage_output_empty(self):
        """Test parsing empty coverage output."""
        result = _parse_coverage_output("")
        self.assertEqual(len(result), 0)
    
    def test_parse_coverage_output_malformed(self):
        """Test parsing malformed coverage output."""
        coverage_output = "invalid coverage output"
        result = _parse_coverage_output(coverage_output)
        self.assertEqual(len(result), 0)


class TestParseLintOutput(unittest.TestCase):
    """Test parse_lint_output function."""
    
    def test_parse_lint_output_valid(self):
        """Test parsing valid lint output."""
        lint_output = """test.py:1:1: E501 line too long (80 > 79 characters)
test.py:2:5: F401 'os' imported but unused
test.py:3:1: W293 blank line contains whitespace"""
        
        issues = parse_lint_output(lint_output)
        
        self.assertEqual(len(issues), 3)
        
        # Check first issue
        self.assertEqual(issues[0].file_path, "test.py")
        self.assertEqual(issues[0].line_number, 1)
        self.assertEqual(issues[0].column_number, 1)
        self.assertEqual(issues[0].rule_id, "E501")
        self.assertEqual(issues[0].message, "line too long (80 > 79 characters)")
        self.assertEqual(issues[0].severity, "error")
        
        # Check second issue
        self.assertEqual(issues[1].file_path, "test.py")
        self.assertEqual(issues[1].line_number, 2)
        self.assertEqual(issues[1].column_number, 5)
        self.assertEqual(issues[1].rule_id, "F401")
        self.assertEqual(issues[1].message, "'os' imported but unused")
        self.assertEqual(issues[1].severity, "error")
        
        # Check third issue
        self.assertEqual(issues[2].file_path, "test.py")
        self.assertEqual(issues[2].line_number, 3)
        self.assertEqual(issues[2].column_number, 1)
        self.assertEqual(issues[2].rule_id, "W293")
        self.assertEqual(issues[2].message, "blank line contains whitespace")
        self.assertEqual(issues[2].severity, "warning")
    
    def test_parse_lint_output_empty(self):
        """Test parsing empty lint output."""
        issues = parse_lint_output("")
        self.assertEqual(len(issues), 0)
    
    def test_parse_lint_output_malformed(self):
        """Test parsing malformed lint output."""
        lint_output = "invalid lint output"
        issues = parse_lint_output(lint_output)
        self.assertEqual(len(issues), 0)


class TestParseMypyOutput(unittest.TestCase):
    """Test parse_mypy_output function."""
    
    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        mypy_output = """test.py:1: error: Name 'x' is not defined  [name-defined]
test.py:2: error: Argument 1 to "func" has incompatible type "str"; expected "int"  [arg-type]
test.py:3: warning: Unused 'type: ignore' comment  [unused-ignore]"""
        
        issues = parse_mypy_output(mypy_output)
        
        self.assertEqual(len(issues), 3)
        
        # Check first issue
        self.assertEqual(issues[0].file_path, "test.py")
        self.assertEqual(issues[0].line_number, 1)
        self.assertEqual(issues[0].rule_id, "name-defined")
        self.assertEqual(issues[0].message, "Name 'x' is not defined")
        self.assertEqual(issues[0].severity, "error")
        
        # Check second issue
        self.assertEqual(issues[1].file_path, "test.py")
        self.assertEqual(issues[1].line_number, 2)
        self.assertEqual(issues[1].rule_id, "arg-type")
        self.assertEqual(issues[1].message, "Argument 1 to \"func\" has incompatible type \"str\"; expected \"int\"")
        self.assertEqual(issues[1].severity, "error")
        
        # Check third issue
        self.assertEqual(issues[2].file_path, "test.py")
        self.assertEqual(issues[2].line_number, 3)
        self.assertEqual(issues[2].rule_id, "unused-ignore")
        self.assertEqual(issues[2].message, "Unused 'type: ignore' comment")
        self.assertEqual(issues[2].severity, "warning")
    
    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        issues = parse_mypy_output("")
        self.assertEqual(len(issues), 0)
    
    def test_parse_mypy_output_malformed(self):
        """Test parsing malformed mypy output."""
        mypy_output = "invalid mypy output"
        issues = parse_mypy_output(mypy_output)
        self.assertEqual(len(issues), 0)


class TestParseBanditOutput(unittest.TestCase):
    """Test parse_bandit_output function."""
    
    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        bandit_output = """[main]  INFO    profile include tests: None
[main]  INFO    profile exclude tests: None
[main]  INFO    cli include tests: None
[main]  INFO    cli exclude tests: None
[main]  INFO    running on Python 3.11.3
test.py:1:1: B101: Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.
test.py:5:1: B105: Use of hardcoded password strings, use getpass or environment variables instead."""
        
        issues = parse_bandit_output(bandit_output)
        
        self.assertEqual(len(issues), 2)
        
        # Check first issue
        self.assertEqual(issues[0].file_path, "test.py")
        self.assertEqual(issues[0].line_number, 1)
        self.assertEqual(issues[0].column_number, 1)
        self.assertEqual(issues[0].rule_id, "B101")
        self.assertEqual(issues[0].message, "Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.")
        self.assertEqual(issues[0].severity, "info")
        
        # Check second issue
        self.assertEqual(issues[1].file_path, "test.py")
        self.assertEqual(issues[1].line_number, 5)
        self.assertEqual(issues[1].column_number, 1)
        self.assertEqual(issues[1].rule_id, "B105")
        self.assertEqual(issues[1].message, "Use of hardcoded password strings, use getpass or environment variables instead.")
        self.assertEqual(issues[1].severity, "info")
    
    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        issues = parse_bandit_output("")
        self.assertEqual(len(issues), 0)
    
    def test_parse_bandit_output_malformed(self):
        """Test parsing malformed bandit output."""
        bandit_output = "invalid bandit output"
        issues = parse_bandit_output(bandit_output)
        self.assertEqual(len(issues), 0)


class TestCreateGithubAnnotation(unittest.TestCase):
    """Test create_github_annotation function."""
    
    def test_create_github_annotation_basic(self):
        """Test creating basic GitHub annotation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            severity="error"
        )
        
        annotation = create_github_annotation(issue)
        
        self.assertEqual(annotation["path"], "test.py")
        self.assertEqual(annotation["start_line"], 10)
        self.assertEqual(annotation["end_line"], 10)
        self.assertEqual(annotation["start_column"], 5)
        self.assertEqual(annotation["end_column"], 5)
        self.assertEqual(annotation["annotation_level"], "failure")
        self.assertEqual(annotation["message"], "line too long")
        self.assertEqual(annotation["title"], "E501: line too long")
    
    def test_create_github_annotation_with_end_positions(self):
        """Test creating GitHub annotation with end positions."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            severity="error",
            end_line_number=10,
            end_column_number=80
        )
        
        annotation = create_github_annotation(issue)
        
        self.assertEqual(annotation["end_line"], 10)
        self.assertEqual(annotation["end_column"], 80)
    
    def test_create_github_annotation_warning_severity(self):
        """Test creating GitHub annotation with warning severity."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="W293",
            message="blank line contains whitespace",
            severity="warning"
        )
        
        annotation = create_github_annotation(issue)
        
        self.assertEqual(annotation["annotation_level"], "warning")
    
    def test_create_github_annotation_notice_severity(self):
        """Test creating GitHub annotation with notice severity."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="B101",
            message="Use of assert detected",
            severity="info"
        )
        
        annotation = create_github_annotation(issue)
        
        self.assertEqual(annotation["annotation_level"], "notice")


class TestFormatAnnotationMessage(unittest.TestCase):
    """Test format_annotation_message function."""
    
    def test_format_annotation_message_basic(self):
        """Test formatting basic annotation message."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            severity="error"
        )
        
        message = format_annotation_message(issue)
        
        expected = "E501: line too long"
        self.assertEqual(message, expected)
    
    def test_format_annotation_message_no_rule_id(self):
        """Test formatting annotation message without rule ID."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="",
            message="line too long",
            severity="error"
        )
        
        message = format_annotation_message(issue)
        
        expected = "line too long"
        self.assertEqual(message, expected)


class TestMain(unittest.TestCase):
    """Test main function."""
    
    @patch('src.ai_guard.pr_annotations.create_pr_annotations')
    @patch('src.ai_guard.pr_annotations.write_annotations_file')
    def test_main_success(self, mock_write_file, mock_create_annotations):
        """Test successful main execution."""
        mock_create_annotations.return_value = []
        mock_write_file.return_value = True
        
        with patch('sys.argv', ['pr_annotations', '--output', 'annotations.json']):
            main()
        
        mock_create_annotations.assert_called_once()
        mock_write_file.assert_called_once()
    
    @patch('src.ai_guard.pr_annotations.create_pr_annotations')
    @patch('src.ai_guard.pr_annotations.write_annotations_file')
    def test_main_write_error(self, mock_write_file, mock_create_annotations):
        """Test main execution with write error."""
        mock_create_annotations.return_value = []
        mock_write_file.return_value = False
        
        with patch('sys.argv', ['pr_annotations', '--output', 'annotations.json']):
            main()
        
        mock_create_annotations.assert_called_once()
        mock_write_file.assert_called_once()


if __name__ == '__main__':
    unittest.main()
