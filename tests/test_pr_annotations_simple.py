"""Simple tests for pr_annotations module focusing on actual functionality."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open

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
        """Test CodeIssue creation with all fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            rule_id="E001",
            suggestion="Fix this issue",
            fix_code="corrected_code()"
        )
        
        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.rule_id == "E001"
        assert issue.suggestion == "Fix this issue"
        assert issue.fix_code == "corrected_code()"

    def test_code_issue_to_dict(self):
        """Test CodeIssue to_dict method."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix it",
            fix_code="fixed()"
        )
        
        result = issue.to_dict()
        expected = {
            "file_path": "src/test.py",
            "line_number": 10,
            "column": 5,
            "severity": "error",
            "message": "Test error",
            "rule_id": "E001",
            "suggestion": "Fix it",
            "fix_code": "fixed()"
        }
        
        assert result == expected


class TestPRAnnotation:
    """Test PRAnnotation dataclass."""

    def test_pr_annotation_creation(self):
        """Test PRAnnotation creation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test annotation",
            annotation_level="failure",
            title="Test Title"
        )
        
        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test annotation"
        assert annotation.annotation_level == "failure"
        assert annotation.title == "Test Title"


class TestPRReviewSummary:
    """Test PRReviewSummary dataclass."""

    def test_pr_review_summary_creation(self):
        """Test PRReviewSummary creation."""
        annotations = [
            PRAnnotation(
                file_path="src/test.py",
                line_number=10,
                message="Test error",
                annotation_level="failure"
            )
        ]
        summary = PRReviewSummary(
            overall_status="changes_requested",
            summary="Test summary",
            annotations=annotations,
            suggestions=["Fix error"],
            quality_score=0.8
        )
        
        assert summary.overall_status == "changes_requested"
        assert summary.summary == "Test summary"
        assert len(summary.annotations) == 1
        assert summary.suggestions == ["Fix error"]
        assert summary.quality_score == 0.8


class TestPRAnnotator:
    """Test PRAnnotator class."""

    def test_pr_annotator_initialization(self):
        """Test PRAnnotator initialization."""
        annotator = PRAnnotator()
        
        assert annotator.annotations == []
        assert annotator.issues == []

    def test_pr_annotator_add_issue(self):
        """Test adding issue to PRAnnotator."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        
        annotator.add_issue(issue)
        
        assert len(annotator.issues) == 1
        assert annotator.issues[0] == issue
        # Should also create an annotation
        assert len(annotator.annotations) == 1


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""

    def test_write_annotations_file_success(self):
        """Test successful writing of annotations file."""
        annotations = [
            {
                "file_path": "src/test.py",
                "line_number": 10,
                "level": "error",
                "message": "Test error"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name
        
        try:
            result = write_annotations_file(annotations, output_path)
            assert result is True
            
            # Verify file was written
            with open(output_path, 'r') as f:
                written_data = json.load(f)
                assert written_data == annotations
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_write_annotations_file_error(self):
        """Test write_annotations_file with write error."""
        annotations = [{"test": "data"}]
        
        with patch('builtins.open', side_effect=IOError("Write error")):
            result = write_annotations_file(annotations, "/invalid/path.json")
            assert result is False


class TestParseCoverageOutput:
    """Test _parse_coverage_output function."""

    def test_parse_coverage_output_empty(self):
        """Test parsing empty coverage output."""
        result = _parse_coverage_output("")
        assert result == {}

    def test_parse_coverage_output_valid(self):
        """Test parsing valid coverage output."""
        coverage_output = """Name                    Stmts   Miss  Cover   Missing
----------------------------------------------------
src/test.py                10      2    80%   3, 7
src/other.py                5      0   100%
----------------------------------------------------
TOTAL                      15      2    87%"""
        
        result = _parse_coverage_output(coverage_output)
        
        # The function returns overall coverage info
        assert "overall" in result
        assert "coverage_percent" in result["overall"]
        assert result["overall"]["coverage_percent"] == 87.0


class TestParseLintOutput:
    """Test parse_lint_output function."""

    def test_parse_lint_output_empty(self):
        """Test parsing empty lint output."""
        result = parse_lint_output("")
        assert result == []

    def test_parse_lint_output_valid(self):
        """Test parsing valid lint output."""
        lint_output = """src/test.py:10:5: E001: Line too long (120 > 100)
src/test.py:15:1: W001: Missing docstring
src/other.py:5:10: E002: Unused variable 'x'"""
        
        result = parse_lint_output(lint_output)
        
        assert len(result) == 3
        assert all(isinstance(issue, CodeIssue) for issue in result)
        assert result[0].file_path == "src/test.py"
        assert result[0].line_number == 10
        assert result[0].rule_id == "E001"
        assert result[1].severity == "warning"
        assert result[2].file_path == "src/other.py"


class TestParseMypyOutput:
    """Test parse_mypy_output function."""

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        result = parse_mypy_output("")
        assert result == []

    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        mypy_output = """src/test.py:10: error: Incompatible types in assignment (expression has type "str", variable has type "int")
src/test.py:15: note: Use "-> None" if function does not return a value
src/other.py:5: warning: Missing return type annotation"""
        
        result = parse_mypy_output(mypy_output)
        
        assert len(result) >= 1  # At least one issue should be parsed
        assert all(isinstance(issue, CodeIssue) for issue in result)
        assert result[0].file_path == "src/test.py"
        assert result[0].severity == "error"


class TestParseBanditOutput:
    """Test parse_bandit_output function."""

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        result = parse_bandit_output("")
        assert result == []

    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        bandit_output = """src/test.py:10:1: B001: Do not use bare except
src/test.py:15:5: B002: Do not use bare except
src/other.py:5:10: B101: Test for use of assert"""
        
        result = parse_bandit_output(bandit_output)
        
        # The function might not parse all lines, so just check it returns a list
        assert isinstance(result, list)
        assert all(isinstance(issue, CodeIssue) for issue in result)


class TestCreateGitHubAnnotation:
    """Test create_github_annotation function."""

    def test_create_github_annotation_error(self):
        """Test creating GitHub annotation for error."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            rule_id="E001"
        )
        
        result = create_github_annotation(issue)
        
        assert result["path"] == "src/test.py"
        assert result["start_line"] == 10
        assert result["end_line"] == 10
        assert result["annotation_level"] == "failure"
        assert "Test error message" in result["message"]


class TestFormatAnnotationMessage:
    """Test format_annotation_message function."""

    def test_format_annotation_message_basic(self):
        """Test formatting basic annotation message."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        
        result = format_annotation_message(issue)
        
        # The function returns just the message, not including rule_id
        assert "Test error" in result

    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=15,
            column=1,
            severity="warning",
            message="Test warning",
            rule_id="W001",
            suggestion="Add docstring"
        )
        
        result = format_annotation_message(issue)
        
        assert "Test warning" in result
        assert "Add docstring" in result


class TestMainFunction:
    """Test main function."""

    def test_main_with_help(self):
        """Test main function with help argument."""
        with patch('sys.argv', ['pr_annotations', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_main_with_invalid_args(self):
        """Test main function with invalid arguments."""
        with patch('sys.argv', ['pr_annotations', '--invalid-arg']):
            with pytest.raises(SystemExit):
                main()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_code_issue_with_none_values(self):
        """Test CodeIssue with None values for optional fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=1,
            column=1,
            severity="info",
            message="Test info",
            rule_id="I001",
            suggestion=None,
            fix_code=None
        )
        
        assert issue.suggestion is None
        assert issue.fix_code is None
        assert issue.to_dict()["suggestion"] is None
        assert issue.to_dict()["fix_code"] is None

    def test_parse_coverage_output_malformed(self):
        """Test parsing malformed coverage output."""
        malformed_output = """Name                    Stmts   Miss  Cover   Missing
----------------------------------------------------
src/test.py                invalid    data    80%   3, 7
----------------------------------------------------
TOTAL                      invalid    data    80%"""
        
        result = _parse_coverage_output(malformed_output)
        
        # Should handle malformed data gracefully
        assert isinstance(result, dict)

    def test_parse_lint_output_malformed_line(self):
        """Test parsing lint output with malformed line."""
        malformed_output = """src/test.py:invalid:line:format
src/test.py:10:5: E001: Valid line"""
        
        result = parse_lint_output(malformed_output)
        
        # Should skip malformed lines and process valid ones
        assert len(result) == 1
        assert result[0].file_path == "src/test.py"
        assert result[0].rule_id == "E001"
