"""Working comprehensive tests for the PR annotations module."""

import json
import os
import tempfile
from unittest.mock import patch, mock_open

from ai_guard.pr_annotations import (
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
    create_pr_annotations,
    write_annotations_file,
    parse_lint_output,
    parse_mypy_output,
    parse_bandit_output,
    _parse_coverage_output,
    create_github_annotation,
    format_annotation_message,
)


class TestPRAnnotationsWorking:
    """Working comprehensive tests for PR annotations functionality."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column_number=5,
            rule_id="flake8:E302",
            message="expected 2 blank lines, found 1",
            severity="warning",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.rule_id == "flake8:E302"
        assert issue.message == "expected 2 blank lines, found 1"
        assert issue.severity == "warning"

    def test_pr_annotation_creation(self):
        """Test PRAnnotation dataclass creation."""
        annotation = PRAnnotation(
            path="src/test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=10,
            annotation_level="warning",
            message="expected 2 blank lines, found 1",
            title="flake8:E302",
        )

        assert annotation.path == "src/test.py"
        assert annotation.start_line == 10
        assert annotation.end_line == 10
        assert annotation.start_column == 5
        assert annotation.end_column == 10
        assert annotation.annotation_level == "warning"
        assert annotation.message == "expected 2 blank lines, found 1"
        assert annotation.title == "flake8:E302"

    def test_pr_review_summary_creation(self):
        """Test PRReviewSummary dataclass creation."""
        summary = PRReviewSummary(
            body="Code quality review completed", event="COMMENT", comments=[]
        )

        assert summary.body == "Code quality review completed"
        assert summary.event == "COMMENT"
        assert summary.comments == []

    def test_pr_annotator_creation(self):
        """Test PRAnnotator class creation."""
        annotator = PRAnnotator(
            repo_owner="test-owner",
            repo_name="test-repo",
            pr_number=123,
            github_token="test-token",
        )

        assert annotator.repo_owner == "test-owner"
        assert annotator.repo_name == "test-repo"
        assert annotator.pr_number == 123
        assert annotator.github_token == "test-token"

    def test_parse_lint_output(self):
        """Test parse_lint_output function."""
        lint_output = """src/test.py:10:1: E302 expected 2 blank lines, found 1
src/test.py:15:5: E111 indentation is not a multiple of four
src/test.py:20:1: F401 'os' imported but unused"""

        issues = parse_lint_output(lint_output)

        assert len(issues) == 3

        # Check first issue
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].column_number == 1
        assert issues[0].rule_id == "flake8:E302"
        assert "expected 2 blank lines" in issues[0].message
        assert issues[0].severity == "warning"

    def test_parse_lint_output_empty(self):
        """Test parse_lint_output with empty output."""
        issues = parse_lint_output("")
        assert issues == []

    def test_parse_mypy_output(self):
        """Test parse_mypy_output function."""
        mypy_output = """src/test.py:10: error: Incompatible return type
src/test.py:15: note: Revealed type is 'builtins.int'
src/test.py:20: warning: Unused 'type: ignore' comment"""

        issues = parse_mypy_output(mypy_output)

        assert len(issues) == 3

        # Check first issue (error)
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].rule_id == "mypy:error"
        assert "Incompatible return type" in issues[0].message
        assert issues[0].severity == "error"

    def test_parse_bandit_output(self):
        """Test parse_bandit_output function."""
        bandit_output = """src/test.py:10:1: B101: Test for use of assert detected
src/test.py:15:5: B602: subprocess call with shell=True"""

        issues = parse_bandit_output(bandit_output)

        assert len(issues) == 2

        # Check first issue
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].column_number == 1
        assert issues[0].rule_id == "bandit:B101"
        assert "Test for use of assert detected" in issues[0].message
        assert issues[0].severity == "note"

    def test_parse_coverage_output(self):
        """Test _parse_coverage_output function."""
        coverage_output = """Name                    Stmts   Miss  Cover   Missing
----------------------------------------------------
src/test.py                10      2    80%   8, 12
src/helper.py               5      0   100%
----------------------------------------------------
TOTAL                      15      2    87%"""

        coverage_data = _parse_coverage_output(coverage_output)

        assert "src/test.py" in coverage_data
        assert "src/helper.py" in coverage_data
        assert coverage_data["src/test.py"]["coverage"] == 80
        assert coverage_data["src/helper.py"]["coverage"] == 100

    def test_create_github_annotation(self):
        """Test create_github_annotation function."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column_number=5,
            rule_id="flake8:E302",
            message="expected 2 blank lines, found 1",
            severity="warning",
        )

        annotation = create_github_annotation(issue)

        assert annotation["path"] == "src/test.py"
        assert annotation["start_line"] == 10
        assert annotation["end_line"] == 10
        assert annotation["start_column"] == 5
        assert annotation["end_column"] == 10
        assert annotation["annotation_level"] == "warning"
        assert "expected 2 blank lines" in annotation["message"]
        assert annotation["title"] == "flake8:E302"

    def test_format_annotation_message(self):
        """Test format_annotation_message function."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column_number=5,
            rule_id="flake8:E302",
            message="expected 2 blank lines, found 1",
            severity="warning",
        )

        message = format_annotation_message(issue)

        assert "flake8:E302" in message
        assert "expected 2 blank lines" in message
        assert "src/test.py:10:5" in message

    def test_write_annotations_file(self):
        """Test write_annotations_file function."""
        annotations = [
            {
                "path": "src/test.py",
                "start_line": 10,
                "end_line": 10,
                "annotation_level": "warning",
                "message": "Test message",
                "title": "Test Title",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            result = write_annotations_file(annotations, output_path)
            assert result is True

            # Verify file was written
            with open(output_path, "r") as f:
                written_data = json.load(f)
                assert written_data == annotations
        finally:
            os.unlink(output_path)

    def test_write_annotations_file_error(self):
        """Test write_annotations_file with write error."""
        annotations = [{"test": "data"}]

        with patch("builtins.open", side_effect=IOError("Write error")):
            result = write_annotations_file(annotations, "test.json")
            assert result is False

    @patch("ai_guard.pr_annotations.parse_lint_output")
    @patch("ai_guard.pr_annotations.parse_mypy_output")
    @patch("ai_guard.pr_annotations.parse_bandit_output")
    @patch("ai_guard.pr_annotations._parse_coverage_output")
    def test_create_pr_annotations(
        self, mock_coverage, mock_bandit, mock_mypy, mock_lint
    ):
        """Test create_pr_annotations function."""
        # Setup mocks
        mock_lint.return_value = [
            CodeIssue("src/test.py", 10, 1, "flake8:E302", "Test message", "warning")
        ]
        mock_mypy.return_value = []
        mock_bandit.return_value = []
        mock_coverage.return_value = {"src/test.py": {"coverage": 80}}

        # Mock file operations
        with patch("builtins.open", mock_open(read_data="test output")):
            with patch("os.path.exists", return_value=True):
                annotations = create_pr_annotations(
                    repo_owner="test-owner",
                    repo_name="test-repo",
                    pr_number=123,
                    github_token="test-token",
                )

        assert len(annotations) == 1
        assert annotations[0]["path"] == "src/test.py"
        assert annotations[0]["annotation_level"] == "warning"

    def test_create_pr_annotations_no_files(self):
        """Test create_pr_annotations with no output files."""
        with patch("os.path.exists", return_value=False):
            annotations = create_pr_annotations(
                repo_owner="test-owner",
                repo_name="test-repo",
                pr_number=123,
                github_token="test-token",
            )

        assert annotations == []
