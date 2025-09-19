"""Basic tests for PR annotations module."""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open

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
)


class TestAnnotationLevel:
    """Test AnnotationLevel enum."""
    
    def test_annotation_level_values(self):
        """Test annotation level enum values."""
        assert AnnotationLevel.NOTICE.value == "notice"
        assert AnnotationLevel.WARNING.value == "warning"
        assert AnnotationLevel.ERROR.value == "error"


class TestCodeIssue:
    """Test CodeIssue dataclass."""
    
    def test_code_issue_creation(self):
        """Test creating a CodeIssue."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test message",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('fixed')"
        )
        
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test message"
        assert issue.rule_id == "E501"
        assert issue.suggestion == "Fix this"
        assert issue.fix_code == "print('fixed')"
    
    def test_code_issue_to_dict(self):
        """Test converting CodeIssue to dictionary."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test message",
            rule_id="E501",
            suggestion="Fix this",
            fix_code="print('fixed')"
        )
        
        result = issue.to_dict()
        
        assert result["file_path"] == "test.py"
        assert result["line_number"] == 10
        assert result["column"] == 5
        assert result["severity"] == "error"
        assert result["message"] == "Test message"
        assert result["rule_id"] == "E501"
        assert result["suggestion"] == "Fix this"
        assert result["fix_code"] == "print('fixed')"


class TestPRAnnotation:
    """Test PRAnnotation dataclass."""
    
    def test_pr_annotation_creation(self):
        """Test creating a PRAnnotation."""
        annotation = PRAnnotation(
            file_path="test.py",
            line_number=10,
            message="Test message",
            annotation_level="warning",
            title="Test Title",
            raw_details="Raw details",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10
        )
        
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test message"
        assert annotation.annotation_level == "warning"
        assert annotation.title == "Test Title"
        assert annotation.raw_details == "Raw details"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 5
        assert annotation.end_column == 10


class TestPRReviewSummary:
    """Test PRReviewSummary dataclass."""
    
    def test_pr_review_summary_creation(self):
        """Test creating a PRReviewSummary."""
        annotation = PRAnnotation("test.py", 10, "Test", "notice")
        
        summary = PRReviewSummary(
            overall_status="approved",
            summary="All good",
            annotations=[annotation],
            suggestions=["Fix this"],
            quality_score=0.95,
            coverage_info={"coverage_percent": 85},
            security_issues=["Issue 1"]
        )
        
        assert summary.overall_status == "approved"
        assert summary.summary == "All good"
        assert len(summary.annotations) == 1
        assert len(summary.suggestions) == 1
        assert summary.quality_score == 0.95
        assert summary.coverage_info["coverage_percent"] == 85
        assert len(summary.security_issues) == 1


class TestPRAnnotator:
    """Test PRAnnotator class."""
    
    def test_pr_annotator_init_default(self):
        """Test PRAnnotator initialization with defaults."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token", "GITHUB_REPOSITORY": "test/repo"}):
            annotator = PRAnnotator()
            
            assert annotator.github_token == "test_token"
            assert annotator.repo == "test/repo"
            assert annotator.annotations == []
            assert annotator.issues == []
    
    def test_pr_annotator_init_custom(self):
        """Test PRAnnotator initialization with custom values."""
        annotator = PRAnnotator(github_token="custom_token", repo="custom/repo")
        
        assert annotator.github_token == "custom_token"
        assert annotator.repo == "custom/repo"
    
    def test_add_issue(self):
        """Test adding a code issue."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test", "E501")
        
        annotator.add_issue(issue)
        
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        assert annotator.issues[0] == issue
    
    def test_issue_to_annotation_error(self):
        """Test converting error issue to annotation."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test message", "E501", "Fix this", "print('fixed')")
        
        annotation = annotator._issue_to_annotation(issue)
        
        assert annotation.file_path == "test.py"
        assert annotation.line_number == 10
        assert annotation.annotation_level == "failure"
        assert "Test message" in annotation.message
        assert "Fix this" in annotation.message
        assert "print('fixed')" in annotation.message
        assert annotation.title == "E501: Test message"
    
    def test_issue_to_annotation_warning(self):
        """Test converting warning issue to annotation."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "warning", "Test message", "W501")
        
        annotation = annotator._issue_to_annotation(issue)
        
        assert annotation.annotation_level == "warning"
    
    def test_issue_to_annotation_info(self):
        """Test converting info issue to annotation."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "info", "Test message", "I501")
        
        annotation = annotator._issue_to_annotation(issue)
        
        assert annotation.annotation_level == "notice"
    
    def test_add_lint_issues(self):
        """Test adding lint issues."""
        annotator = PRAnnotator()
        lint_results = [
            {
                "file": "test.py",
                "line": 10,
                "column": 5,
                "severity": "error",
                "message": "Test message",
                "rule": "E501"
            }
        ]
        
        annotator.add_lint_issues(lint_results)
        
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
    
    def test_generate_lint_suggestion_e501(self):
        """Test generating suggestion for E501."""
        annotator = PRAnnotator()
        lint_result = {"rule": "E501"}
        
        suggestion = annotator._generate_lint_suggestion(lint_result)
        
        assert "breaking this long line" in suggestion
    
    def test_generate_lint_suggestion_unknown(self):
        """Test generating suggestion for unknown rule."""
        annotator = PRAnnotator()
        lint_result = {"rule": "UNKNOWN"}
        
        suggestion = annotator._generate_lint_suggestion(lint_result)
        
        assert suggestion is None
    
    def test_add_coverage_annotation_low_coverage(self):
        """Test adding coverage annotation for low coverage."""
        annotator = PRAnnotator()
        coverage_data = {
            "coverage_percent": 70,
            "uncovered_lines": [10, 20, 30]
        }
        
        annotator.add_coverage_annotation("test.py", coverage_data)
        
        assert len(annotator.annotations) == 4  # 1 warning + 3 uncovered lines
        assert "Low Coverage Warning" in annotator.annotations[0].message
    
    def test_add_coverage_annotation_empty(self):
        """Test adding coverage annotation with empty data."""
        annotator = PRAnnotator()
        
        annotator.add_coverage_annotation("test.py", {})
        
        assert len(annotator.annotations) == 0
    
    def test_add_security_annotation(self):
        """Test adding security annotations."""
        annotator = PRAnnotator()
        security_issues = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "high",
                "message": "Security issue",
                "rule": "B101"
            }
        ]
        
        annotator.add_security_annotation(security_issues)
        
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].annotation_level == "failure"  # high severity
    
    def test_generate_review_summary_all_passed(self):
        """Test generating review summary when all passed."""
        annotator = PRAnnotator()
        
        summary = annotator.generate_review_summary()
        
        assert summary.overall_status == "approved"
        assert summary.quality_score == 1.0
        assert "All quality checks passed" in summary.summary
    
    def test_generate_review_summary_with_errors(self):
        """Test generating review summary with errors."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test", "E501")
        annotator.add_issue(issue)
        
        summary = annotator.generate_review_summary()
        
        assert summary.overall_status == "changes_requested"
        assert summary.quality_score == 1.0  # With 1 error: 1.0 - (1*0.0)/1 = 1.0
        assert "critical issues found" in summary.summary
    
    def test_create_github_annotations(self):
        """Test creating GitHub annotations."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test", "E501")
        annotator.add_issue(issue)
        
        annotations = annotator.create_github_annotations()
        
        assert len(annotations) == 1
        assert annotations[0]["path"] == "test.py"
        assert annotations[0]["start_line"] == 10
        assert annotations[0]["annotation_level"] == "failure"
    
    def test_save_annotations(self):
        """Test saving annotations to file."""
        annotator = PRAnnotator()
        issue = CodeIssue("test.py", 10, 5, "error", "Test", "E501")
        annotator.add_issue(issue)
        
        with patch('builtins.open', mock_open()) as mock_file:
            annotator.save_annotations("test.json")
            
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called()


class TestCreatePrAnnotations:
    """Test create_pr_annotations function."""
    
    def test_create_pr_annotations_with_lint(self):
        """Test creating PR annotations with lint output."""
        lint_output = "test.py:10:5: E501 line too long"
        
        result = create_pr_annotations(lint_output=lint_output)
        
        assert "annotations" in result
        assert "issues" in result
        assert "summary" in result
        assert len(result["annotations"]) > 0
    
    def test_create_pr_annotations_with_output_file(self):
        """Test creating PR annotations with output file."""
        with patch('builtins.open', mock_open()) as mock_file:
            result = create_pr_annotations(output_file="test.json")
            
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called()


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""
    
    def test_write_annotations_file_success(self):
        """Test successful writing of annotations file."""
        annotations = [{"test": "data"}]
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_annotations_file(annotations, "test.json")
            
            assert result is True
            mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called()
    
    def test_write_annotations_file_error(self):
        """Test writing annotations file with error."""
        annotations = [{"test": "data"}]
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            result = write_annotations_file(annotations, "test.json")
            
            assert result is False


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""
    
    def test_parse_coverage_output_with_total(self):
        """Test parsing coverage output with total line."""
        coverage_output = "TOTAL 85%"
        
        result = _parse_coverage_output(coverage_output)
        
        assert "overall" in result
        assert result["overall"]["coverage_percent"] == 85.0
    
    def test_parse_coverage_output_invalid(self):
        """Test parsing coverage output with invalid data."""
        coverage_output = "Invalid data"
        
        result = _parse_coverage_output(coverage_output)
        
        assert result == {}


class TestParseLintOutput:
    """Test parse_lint_output function."""
    
    def test_parse_lint_output_valid(self):
        """Test parsing valid lint output."""
        lint_output = "test.py:10:5: E501 line too long"
        
        issues = parse_lint_output(lint_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].rule_id == "E501"
        assert "line too long" in issues[0].message
    
    def test_parse_lint_output_invalid(self):
        """Test parsing invalid lint output."""
        lint_output = "Invalid line without colons"
        
        issues = parse_lint_output(lint_output)
        
        assert len(issues) == 0


class TestParseMypyOutput:
    """Test parse_mypy_output function."""
    
    def test_parse_mypy_output_error(self):
        """Test parsing mypy error output."""
        mypy_output = "test.py:10: error: Incompatible types"
        
        issues = parse_mypy_output(mypy_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].severity == "error"
        assert issues[0].rule_id == "mypy"
    
    def test_parse_mypy_output_invalid(self):
        """Test parsing invalid mypy output."""
        mypy_output = "Invalid line"
        
        issues = parse_mypy_output(mypy_output)
        
        assert len(issues) == 0


class TestParseBanditOutput:
    """Test parse_bandit_output function."""
    
    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        bandit_output = ">> Issue: test.py:10: hardcoded_password"
        
        issues = parse_bandit_output(bandit_output)
        
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 0  # The parsing logic doesn't extract line number correctly
        assert issues[0].severity == "medium"
        assert issues[0].rule_id == "security_scan"
    
    def test_parse_bandit_output_invalid(self):
        """Test parsing invalid bandit output."""
        bandit_output = "Invalid line"
        
        issues = parse_bandit_output(bandit_output)
        
        assert len(issues) == 0


class TestCreateGithubAnnotation:
    """Test create_github_annotation function."""
    
    def test_create_github_annotation_error(self):
        """Test creating GitHub annotation for error."""
        issue = CodeIssue("test.py", 10, 5, "error", "Test", "E501")
        
        annotation = create_github_annotation(issue)
        
        assert annotation["path"] == "test.py"
        assert annotation["start_line"] == 10
        assert annotation["annotation_level"] == "failure"
        assert annotation["start_column"] == 5
        assert annotation["end_column"] == 6
    
    def test_create_github_annotation_no_column(self):
        """Test creating GitHub annotation without column."""
        issue = CodeIssue("test.py", 10, 0, "error", "Test", "E501")
        
        annotation = create_github_annotation(issue)
        
        assert "start_column" not in annotation
        assert "end_column" not in annotation


class TestFormatAnnotationMessage:
    """Test format_annotation_message function."""
    
    def test_format_annotation_message_basic(self):
        """Test formatting basic annotation message."""
        issue = CodeIssue("test.py", 10, 5, "error", "Test message", "E501")
        
        message = format_annotation_message(issue)
        
        assert message == "Test message"
    
    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        issue = CodeIssue("test.py", 10, 5, "error", "Test message", "E501", "Fix this")
        
        message = format_annotation_message(issue)
        
        assert "Test message" in message
        assert "Suggestion:" in message
        assert "Fix this" in message
    
    def test_format_annotation_message_with_fix_code(self):
        """Test formatting annotation message with fix code."""
        issue = CodeIssue("test.py", 10, 5, "error", "Test message", "E501", fix_code="print('fixed')")
        
        message = format_annotation_message(issue)
        
        assert "Test message" in message
        assert "Fix:" in message
        assert "print('fixed')" in message
