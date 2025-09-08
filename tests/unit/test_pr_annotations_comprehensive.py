"""Comprehensive tests for PR annotations module."""

import pytest
import json
from unittest.mock import patch, mock_open, MagicMock

from ai_guard.pr_annotations import (
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    PRAnnotator,
)


class TestPRAnnotationsComprehensive:
    """Comprehensive tests for PR annotations functionality."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            rule_id="E302",
            suggestion="Add two blank lines",
            fix_code="\n\n",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.rule_id == "E302"
        assert issue.suggestion == "Add two blank lines"
        assert issue.fix_code == "\n\n"

    def test_pr_annotation_creation(self):
        """Test PRAnnotation dataclass creation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=10,
            message="Test annotation message",
            annotation_level="warning",
            title="Code Quality Issue",
            raw_details="Detailed information",
            start_line=10,
            end_line=12,
            start_column=1,
            end_column=10,
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "Test annotation message"
        assert annotation.annotation_level == "warning"
        assert annotation.title == "Code Quality Issue"
        assert annotation.raw_details == "Detailed information"
        assert annotation.start_line == 10
        assert annotation.end_line == 12
        assert annotation.start_column == 1
        assert annotation.end_column == 10

    def test_pr_review_summary_creation(self):
        """Test PRReviewSummary dataclass creation."""
        annotations = [
            PRAnnotation("src/test.py", 10, "Error message", "failure"),
            PRAnnotation("src/test.py", 15, "Warning message", "warning"),
        ]
        suggestions = ["Fix the error", "Consider refactoring"]

        summary = PRReviewSummary(
            overall_status="changes_requested",
            summary="Found 2 issues that need attention",
            annotations=annotations,
            suggestions=suggestions,
            quality_score=0.7,
        )

        assert summary.overall_status == "changes_requested"
        assert summary.summary == "Found 2 issues that need attention"
        assert len(summary.annotations) == 2
        assert len(summary.suggestions) == 2
        assert summary.quality_score == 0.7

    def test_parse_sarif_results(self):
        """Test parsing SARIF results into CodeIssue objects."""
        sarif_results = [
            MagicMock(
                locations=[
                    MagicMock(
                        physicalLocation=MagicMock(
                            artifactLocation=MagicMock(uri="src/test.py"),
                            region=MagicMock(startLine=10, startColumn=5),
                        )
                    )
                ],
                message=MagicMock(text="E302: expected 2 blank lines"),
                ruleId="E302",
                level="error",
            ),
            MagicMock(
                locations=[
                    MagicMock(
                        physicalLocation=MagicMock(
                            artifactLocation=MagicMock(uri="src/test.py"),
                            region=MagicMock(startLine=15, startColumn=1),
                        )
                    )
                ],
                message=MagicMock(text="F401: 'os' imported but unused"),
                ruleId="F401",
                level="warning",
            ),
        ]

        issues = _parse_sarif_results(sarif_results)

        assert len(issues) == 2

        # Check first issue
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].column == 5
        assert issues[0].severity == "error"
        assert "E302" in issues[0].message
        assert issues[0].rule_id == "E302"

        # Check second issue
        assert issues[1].file_path == "src/test.py"
        assert issues[1].line_number == 15
        assert issues[1].column == 1
        assert issues[1].severity == "warning"
        assert "F401" in issues[1].message
        assert issues[1].rule_id == "F401"

    def test_parse_sarif_results_empty(self):
        """Test parsing empty SARIF results."""
        issues = _parse_sarif_results([])
        assert len(issues) == 0

    def test_parse_sarif_results_missing_fields(self):
        """Test parsing SARIF results with missing fields."""
        sarif_results = [
            MagicMock(
                locations=[
                    MagicMock(
                        physicalLocation=MagicMock(
                            artifactLocation=MagicMock(uri="src/test.py"),
                            region=MagicMock(startLine=10, startColumn=None),
                        )
                    )
                ],
                message=MagicMock(text="Test message"),
                ruleId=None,
                level="info",
            )
        ]

        issues = _parse_sarif_results(sarif_results)

        assert len(issues) == 1
        assert issues[0].file_path == "src/test.py"
        assert issues[0].line_number == 10
        assert issues[0].column == 0  # Default value
        assert issues[0].severity == "info"
        assert issues[0].rule_id == "unknown"

    def test_create_annotation_from_issue(self):
        """Test creating PRAnnotation from CodeIssue."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=5,
            severity="error",
            message="E302: expected 2 blank lines",
            rule_id="E302",
            suggestion="Add two blank lines before this function",
            fix_code="\n\n",
        )

        annotation = _create_annotation_from_issue(issue)

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 10
        assert annotation.message == "E302: expected 2 blank lines"
        assert annotation.annotation_level == "failure"
        assert annotation.title == "Code Quality Issue (E302)"
        assert "Add two blank lines" in annotation.raw_details
        assert annotation.start_line == 10
        assert annotation.start_column == 5

    def test_determine_annotation_level(self):
        """Test determining annotation level from severity."""
        assert _determine_annotation_level("error") == "failure"
        assert _determine_annotation_level("warning") == "warning"
        assert _determine_annotation_level("info") == "notice"
        assert _determine_annotation_level("unknown") == "notice"

    def test_calculate_quality_score(self):
        """Test calculating quality score from issues."""
        issues = [
            CodeIssue("src/test.py", 10, 1, "error", "Error 1", "E302"),
            CodeIssue("src/test.py", 15, 1, "warning", "Warning 1", "F401"),
            CodeIssue("src/test.py", 20, 1, "info", "Info 1", "I001"),
        ]

        score = _calculate_quality_score(issues)

        # Should be between 0 and 1, with errors weighted more heavily
        assert 0 <= score <= 1
        assert score < 1.0  # Should be less than perfect due to issues

    def test_calculate_quality_score_no_issues(self):
        """Test calculating quality score with no issues."""
        score = _calculate_quality_score([])
        assert score == 1.0

    def test_pr_annotator_initialization(self):
        """Test PRAnnotator initialization."""
        with patch("os.getenv", return_value="test-token"):
            annotator = PRAnnotator("test-repo", "test-token")

            assert annotator.repo_name == "test-repo"
            assert annotator.github_token == "test-token"

    def test_pr_annotator_initialization_from_env(self):
        """Test PRAnnotator initialization from environment variable."""
        with patch("os.getenv", return_value="env-token"):
            annotator = PRAnnotator("test-repo")

            assert annotator.repo_name == "test-repo"
            assert annotator.github_token == "env-token"

    def test_pr_annotator_initialization_no_token(self):
        """Test PRAnnotator initialization without token."""
        with patch("os.getenv", return_value=None):
            with pytest.raises(ValueError, match="GitHub token is required"):
                PRAnnotator("test-repo")

    def test_parse_github_event(self):
        """Test parsing GitHub event JSON."""
        event_data = {
            "pull_request": {
                "number": 123,
                "head": {"sha": "abc123", "ref": "feature-branch"},
                "base": {"sha": "def456", "ref": "main"},
            }
        }

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
                annotator = PRAnnotator("test-repo", "test-token")
                pr_info = annotator._parse_github_event("event.json")

                assert pr_info["number"] == 123
                assert pr_info["head_sha"] == "abc123"
                assert pr_info["head_ref"] == "feature-branch"
                assert pr_info["base_sha"] == "def456"
                assert pr_info["base_ref"] == "main"

    def test_parse_github_event_file_not_found(self):
        """Test parsing GitHub event when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            annotator = PRAnnotator("test-repo", "test-token")
            pr_info = annotator._parse_github_event("nonexistent.json")

            assert pr_info is None

    def test_parse_github_event_invalid_json(self):
        """Test parsing GitHub event with invalid JSON."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                annotator = PRAnnotator("test-repo", "test-token")
                pr_info = annotator._parse_github_event("event.json")

                assert pr_info is None

    def test_parse_github_event_missing_pull_request(self):
        """Test parsing GitHub event without pull_request section."""
        event_data = {"other": "data"}

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
                annotator = PRAnnotator("test-repo", "test-token")
                pr_info = annotator._parse_github_event("event.json")

                assert pr_info is None

    def test_create_github_client(self):
        """Test creating GitHub client."""
        with patch("ai_guard.pr_annotations.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client

            annotator = PRAnnotator("test-repo", "test-token")
            client = annotator._create_github_client()

            mock_github.assert_called_once_with("test-token")
            assert client == mock_client

    def test_get_pull_request(self):
        """Test getting pull request from GitHub."""
        with patch("ai_guard.pr_annotations.Github") as mock_github:
            mock_client = MagicMock()
            mock_repo = MagicMock()
            mock_pr = MagicMock()

            mock_github.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo
            mock_repo.get_pull.return_value = mock_pr

            annotator = PRAnnotator("test-repo", "test-token")
            pr = annotator._get_pull_request(123)

            mock_client.get_repo.assert_called_once_with("test-repo")
            mock_repo.get_pull.assert_called_once_with(123)
            assert pr == mock_pr

    def test_create_annotations_from_issues(self):
        """Test creating annotations from issues."""
        issues = [
            CodeIssue("src/test.py", 10, 1, "error", "Error message", "E302"),
            CodeIssue("src/test.py", 15, 1, "warning", "Warning message", "F401"),
        ]

        annotator = PRAnnotator("test-repo", "test-token")
        annotations = annotator._create_annotations_from_issues(issues)

        assert len(annotations) == 2
        assert annotations[0].annotation_level == "failure"
        assert annotations[1].annotation_level == "warning"

    def test_create_review_summary(self):
        """Test creating review summary."""
        issues = [
            CodeIssue("src/test.py", 10, 1, "error", "Error message", "E302"),
            CodeIssue("src/test.py", 15, 1, "warning", "Warning message", "F401"),
        ]

        annotator = PRAnnotator("test-repo", "test-token")
        summary = annotator._create_review_summary(issues)

        assert summary.overall_status == "changes_requested"
        assert len(summary.annotations) == 2
        assert len(summary.suggestions) > 0
        assert 0 <= summary.quality_score <= 1

    def test_create_review_summary_no_issues(self):
        """Test creating review summary with no issues."""
        annotator = PRAnnotator("test-repo", "test-token")
        summary = annotator._create_review_summary([])

        assert summary.overall_status == "approved"
        assert len(summary.annotations) == 0
        assert summary.quality_score == 1.0

    def test_submit_review(self):
        """Test submitting review to GitHub."""
        with patch("ai_guard.pr_annotations.Github") as mock_github:
            mock_client = MagicMock()
            mock_repo = MagicMock()
            mock_pr = MagicMock()

            mock_github.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo
            mock_repo.get_pull.return_value = mock_pr

            annotator = PRAnnotator("test-repo", "test-token")
            summary = PRReviewSummary(
                overall_status="changes_requested",
                summary="Test summary",
                annotations=[],
                suggestions=[],
                quality_score=0.8,
            )

            annotator._submit_review(123, summary)

            mock_pr.create_review.assert_called_once()
            call_args = mock_pr.create_review.call_args
            assert call_args[1]["event"] == "REQUEST_CHANGES"
            assert call_args[1]["body"] == "Test summary"

    def test_submit_review_approved(self):
        """Test submitting approved review to GitHub."""
        with patch("ai_guard.pr_annotations.Github") as mock_github:
            mock_client = MagicMock()
            mock_repo = MagicMock()
            mock_pr = MagicMock()

            mock_github.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo
            mock_repo.get_pull.return_value = mock_pr

            annotator = PRAnnotator("test-repo", "test-token")
            summary = PRReviewSummary(
                overall_status="approved",
                summary="All good!",
                annotations=[],
                suggestions=[],
                quality_score=1.0,
            )

            annotator._submit_review(123, summary)

            mock_pr.create_review.assert_called_once()
            call_args = mock_pr.create_review.call_args
            assert call_args[1]["event"] == "APPROVE"

    def test_annotate_pr_full_workflow(self):
        """Test full PR annotation workflow."""
        event_data = {
            "pull_request": {
                "number": 123,
                "head": {"sha": "abc123", "ref": "feature-branch"},
                "base": {"sha": "def456", "ref": "main"},
            }
        }

        sarif_results = [
            MagicMock(
                locations=[
                    MagicMock(
                        physicalLocation=MagicMock(
                            artifactLocation=MagicMock(uri="src/test.py"),
                            region=MagicMock(startLine=10, startColumn=1),
                        )
                    )
                ],
                message=MagicMock(text="E302: expected 2 blank lines"),
                ruleId="E302",
                level="error",
            )
        ]

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
                with patch("ai_guard.pr_annotations.Github") as mock_github:
                    mock_client = MagicMock()
                    mock_repo = MagicMock()
                    mock_pr = MagicMock()

                    mock_github.return_value = mock_client
                    mock_client.get_repo.return_value = mock_repo
                    mock_repo.get_pull.return_value = mock_pr

                    annotator = PRAnnotator("test-repo", "test-token")
                    result = annotator.annotate_pr(sarif_results, "event.json")

                    assert result is True
                    mock_pr.create_review.assert_called_once()

    def test_annotate_pr_no_event_file(self):
        """Test PR annotation without event file."""
        sarif_results = []

        with patch("os.path.exists", return_value=False):
            annotator = PRAnnotator("test-repo", "test-token")
            result = annotator.annotate_pr(sarif_results, "nonexistent.json")

            assert result is False

    def test_annotate_pr_github_error(self):
        """Test PR annotation with GitHub API error."""
        event_data = {
            "pull_request": {
                "number": 123,
                "head": {"sha": "abc123", "ref": "feature-branch"},
                "base": {"sha": "def456", "ref": "main"},
            }
        }

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
                with patch("ai_guard.pr_annotations.Github") as mock_github:
                    mock_github.side_effect = Exception("GitHub API error")

                    annotator = PRAnnotator("test-repo", "test-token")
                    result = annotator.annotate_pr([], "event.json")

                    assert result is False
