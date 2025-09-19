"""Simple comprehensive tests for pr_annotations.py to achieve 80+ coverage."""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, mock_open, MagicMock, Mock
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from src.ai_guard.pr_annotations import (
    AnnotationLevel, CodeIssue, PRAnnotation, PRReviewSummary, PRAnnotator,
    create_pr_annotations, write_annotations_file, _parse_coverage_output,
    parse_lint_output, parse_mypy_output, parse_bandit_output,
    create_github_annotation, format_annotation_message, main
)


class TestAnnotationLevel:
    """Test AnnotationLevel enum."""
    
    def test_annotation_level_values(self):
        """Test AnnotationLevel enum values."""
        assert AnnotationLevel.NOTICE == "notice"
        assert AnnotationLevel.WARNING == "warning"
        assert AnnotationLevel.FAILURE == "failure"


class TestCodeIssue:
    """Test CodeIssue class."""
    
    def test_code_issue_creation(self):
        """Test CodeIssue creation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long"
        )
        
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.rule_id == "E501"
        assert issue.message == "line too long"
    
    def test_code_issue_with_optional_fields(self):
        """Test CodeIssue with optional fields."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            severity="warning",
            category="style",
            context="def test_func():"
        )
        
        assert issue.severity == "warning"
        assert issue.category == "style"
        assert issue.context == "def test_func():"


class TestPRAnnotation:
    """Test PRAnnotation class."""
    
    def test_pr_annotation_creation(self):
        """Test PRAnnotation creation."""
        annotation = PRAnnotation(
            path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation",
            title="Test Title"
        )
        
        assert annotation.path == "test.py"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 5
        assert annotation.end_column == 10
        assert annotation.annotation_level == AnnotationLevel.WARNING
        assert annotation.message == "Test annotation"
        assert annotation.title == "Test Title"


class TestPRReviewSummary:
    """Test PRReviewSummary class."""
    
    def test_pr_review_summary_creation(self):
        """Test PRReviewSummary creation."""
        summary = PRReviewSummary(
            total_issues=5,
            issues_by_severity={"warning": 3, "error": 2},
            files_affected=["test1.py", "test2.py"],
            coverage_percentage=85.5
        )
        
        assert summary.total_issues == 5
        assert summary.issues_by_severity == {"warning": 3, "error": 2}
        assert summary.files_affected == ["test1.py", "test2.py"]
        assert summary.coverage_percentage == 85.5


class TestPRAnnotator:
    """Test PRAnnotator class."""
    
    def test_pr_annotator_initialization(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()
        assert annotator.annotations == []
        assert annotator.summary is None
    
    def test_pr_annotator_add_annotation(self):
        """Test PRAnnotator add_annotation."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long"
        )
        
        annotation = PRAnnotation(
            path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation"
        )
        
        annotator.add_annotation(annotation)
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0] == annotation
    
    def test_pr_annotator_add_annotations(self):
        """Test PRAnnotator add_annotations."""
        annotator = PRAnnotator()
        
        annotation1 = PRAnnotation(
            path="test1.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation 1"
        )
        
        annotation2 = PRAnnotation(
            path="test2.py",
            start_line=2,
            end_line=2,
            start_column=2,
            end_column=2,
            annotation_level=AnnotationLevel.ERROR,
            message="Test annotation 2"
        )
        
        annotator.add_annotations([annotation1, annotation2])
        assert len(annotator.annotations) == 2
    
    def test_pr_annotator_clear_annotations(self):
        """Test PRAnnotator clear_annotations."""
        annotator = PRAnnotator()
        
        annotation = PRAnnotation(
            path="test.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation"
        )
        
        annotator.add_annotation(annotation)
        assert len(annotator.annotations) == 1
        
        annotator.clear_annotations()
        assert len(annotator.annotations) == 0
    
    def test_pr_annotator_get_annotations_by_file(self):
        """Test PRAnnotator get_annotations_by_file."""
        annotator = PRAnnotator()
        
        annotation1 = PRAnnotation(
            path="test1.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation 1"
        )
        
        annotation2 = PRAnnotation(
            path="test1.py",
            start_line=2,
            end_line=2,
            start_column=2,
            end_column=2,
            annotation_level=AnnotationLevel.ERROR,
            message="Test annotation 2"
        )
        
        annotation3 = PRAnnotation(
            path="test2.py",
            start_line=3,
            end_line=3,
            start_column=3,
            end_column=3,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation 3"
        )
        
        annotator.add_annotations([annotation1, annotation2, annotation3])
        
        test1_annotations = annotator.get_annotations_by_file("test1.py")
        test2_annotations = annotator.get_annotations_by_file("test2.py")
        
        assert len(test1_annotations) == 2
        assert len(test2_annotations) == 1
    
    def test_pr_annotator_get_annotations_by_level(self):
        """Test PRAnnotator get_annotations_by_level."""
        annotator = PRAnnotator()
        
        annotation1 = PRAnnotation(
            path="test1.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation 1"
        )
        
        annotation2 = PRAnnotation(
            path="test2.py",
            start_line=2,
            end_line=2,
            start_column=2,
            end_column=2,
            annotation_level=AnnotationLevel.ERROR,
            message="Test annotation 2"
        )
        
        annotator.add_annotations([annotation1, annotation2])
        
        warning_annotations = annotator.get_annotations_by_level(AnnotationLevel.WARNING)
        error_annotations = annotator.get_annotations_by_level(AnnotationLevel.ERROR)
        
        assert len(warning_annotations) == 1
        assert len(error_annotations) == 1
    
    def test_pr_annotator_generate_summary(self):
        """Test PRAnnotator generate_summary."""
        annotator = PRAnnotator()
        
        annotation1 = PRAnnotation(
            path="test1.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation 1"
        )
        
        annotation2 = PRAnnotation(
            path="test2.py",
            start_line=2,
            end_line=2,
            start_column=2,
            end_column=2,
            annotation_level=AnnotationLevel.ERROR,
            message="Test annotation 2"
        )
        
        annotator.add_annotations([annotation1, annotation2])
        
        summary = annotator.generate_summary()
        assert isinstance(summary, PRReviewSummary)
        assert summary.total_issues == 2
        assert summary.issues_by_severity["warning"] == 1
        assert summary.issues_by_severity["error"] == 1
        assert len(summary.files_affected) == 2
    
    def test_pr_annotator_export_annotations(self):
        """Test PRAnnotator export_annotations."""
        annotator = PRAnnotator()
        
        annotation = PRAnnotation(
            path="test.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation"
        )
        
        annotator.add_annotation(annotation)
        
        exported = annotator.export_annotations("json")
        assert isinstance(exported, str)
        
        exported_dict = json.loads(exported)
        assert len(exported_dict) == 1
    
    def test_pr_annotator_validate_annotations(self):
        """Test PRAnnotator validate_annotations."""
        annotator = PRAnnotator()
        
        annotation = PRAnnotation(
            path="test.py",
            start_line=1,
            end_line=1,
            start_column=1,
            end_column=1,
            annotation_level=AnnotationLevel.WARNING,
            message="Test annotation"
        )
        
        annotator.add_annotation(annotation)
        
        validation_result = annotator.validate_annotations()
        assert isinstance(validation_result, dict)
        assert "valid" in validation_result
        assert "errors" in validation_result


class TestCreatePrAnnotations:
    """Test create_pr_annotations function."""
    
    def test_create_pr_annotations_empty_list(self):
        """Test create_pr_annotations with empty list."""
        result = create_pr_annotations([])
        assert result == []
    
    def test_create_pr_annotations_with_issues(self):
        """Test create_pr_annotations with issues."""
        issues = [
            CodeIssue(
                file_path="test.py",
                line_number=10,
                column_number=5,
                rule_id="E501",
                message="line too long"
            )
        ]
        
        annotations = create_pr_annotations(issues)
        assert len(annotations) == 1
        assert annotations[0].path == "test.py"
        assert annotations[0].start_line == 10


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""
    
    def test_write_annotations_file_success(self):
        """Test write_annotations_file with successful write."""
        annotations = [
            {
                "path": "test.py",
                "start_line": 10,
                "message": "Test annotation"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.close()
            
            try:
                result = write_annotations_file(annotations, f.name)
                assert result is True
                
                # Verify file was created and contains annotations
                with open(f.name, 'r') as saved_file:
                    content = json.load(saved_file)
                    assert len(content) == 1
                    assert content[0]["path"] == "test.py"
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)
    
    def test_write_annotations_file_error(self):
        """Test write_annotations_file with error."""
        annotations = [{"test": "data"}]
        
        with patch('builtins.open', side_effect=OSError):
            result = write_annotations_file(annotations, "test.json")
            assert result is False


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""
    
    def test_parse_coverage_output_valid(self):
        """Test _parse_coverage_output with valid output."""
        coverage_output = "test.py: 85% coverage"
        result = _parse_coverage_output(coverage_output)
        
        assert isinstance(result, dict)
        assert "test.py" in result
        assert result["test.py"]["coverage"] == 85
    
    def test_parse_coverage_output_empty(self):
        """Test _parse_coverage_output with empty output."""
        result = _parse_coverage_output("")
        assert result == {}


class TestParseLintOutput:
    """Test parse_lint_output function."""
    
    def test_parse_lint_output_valid(self):
        """Test parse_lint_output with valid output."""
        lint_output = "test.py:10:5: E501 line too long (80 > 79 characters)"
        issues = parse_lint_output(lint_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].column_number == 5
        assert issues[0].rule_id == "E501"
        assert "line too long" in issues[0].message
    
    def test_parse_lint_output_none(self):
        """Test parse_lint_output with None input."""
        issues = parse_lint_output(None)
        assert issues == []
    
    def test_parse_lint_output_empty(self):
        """Test parse_lint_output with empty input."""
        issues = parse_lint_output("")
        assert issues == []


class TestParseMypyOutput:
    """Test parse_mypy_output function."""
    
    def test_parse_mypy_output_valid(self):
        """Test parse_mypy_output with valid output."""
        mypy_output = "test.py:10: error: Incompatible return type [return-value]"
        issues = parse_mypy_output(mypy_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].rule_id == "return-value"
        assert "Incompatible return type" in issues[0].message
    
    def test_parse_mypy_output_empty(self):
        """Test parse_mypy_output with empty input."""
        issues = parse_mypy_output("")
        assert issues == []


class TestParseBanditOutput:
    """Test parse_bandit_output function."""
    
    def test_parse_bandit_output_valid(self):
        """Test parse_bandit_output with valid output."""
        bandit_output = "test.py:10: B101 Use of insecure MD2 hash algorithm"
        issues = parse_bandit_output(bandit_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].rule_id == "B101"
        assert "Use of insecure MD2 hash algorithm" in issues[0].message
    
    def test_parse_bandit_output_empty(self):
        """Test parse_bandit_output with empty input."""
        issues = parse_bandit_output("")
        assert issues == []


class TestCreateGithubAnnotation:
    """Test create_github_annotation function."""
    
    def test_create_github_annotation(self):
        """Test create_github_annotation function."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long"
        )
        
        annotation = create_github_annotation(issue)
        
        assert isinstance(annotation, dict)
        assert annotation["path"] == "test.py"
        assert annotation["start_line"] == 10
        assert annotation["end_line"] == 10
        assert "E501" in annotation["message"]
        assert "line too long" in annotation["message"]


class TestFormatAnnotationMessage:
    """Test format_annotation_message function."""
    
    def test_format_annotation_message_basic(self):
        """Test format_annotation_message basic functionality."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long"
        )
        
        message = format_annotation_message(issue)
        assert isinstance(message, str)
        assert "E501" in message
        assert "line too long" in message
    
    def test_format_annotation_message_with_context(self):
        """Test format_annotation_message with context."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            rule_id="E501",
            message="line too long",
            context="def very_long_function_name_that_exceeds_line_length():"
        )
        
        message = format_annotation_message(issue)
        assert "def very_long_function_name_that_exceeds_line_length():" in message


class TestMain:
    """Test main function."""
    
    @patch('sys.argv', ['pr_annotations.py', '--help'])
    def test_main_help(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit):
            main()
    
    @patch('sys.argv', ['pr_annotations.py'])
    def test_main_no_args(self):
        """Test main function with no arguments."""
        with pytest.raises(SystemExit):
            main()
    
    @patch('sys.argv', ['pr_annotations.py', '--input', 'test.json'])
    @patch('builtins.open', mock_open(read_data='[]'))
    def test_main_with_input(self, mock_open):
        """Test main function with input file."""
        with patch('src.ai_guard.pr_annotations.PRAnnotator') as mock_annotator:
            mock_instance = Mock()
            mock_annotator.return_value = mock_instance
            
            main()
            mock_instance.process_issues.assert_called_once()
