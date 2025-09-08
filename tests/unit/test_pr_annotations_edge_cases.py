"""Edge case tests for PR annotations module to improve coverage to 90%+."""

from unittest.mock import patch, mock_open

from ai_guard.pr_annotations import (
    CodeIssue,
    create_pr_annotations,
    write_annotations_file,
    parse_lint_output,
    parse_mypy_output,
    parse_bandit_output,
    create_github_annotation,
    format_annotation_message,
)


class TestPRAnnotationsEdgeCases:
    """Test edge cases and error handling in PR annotations module."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation with all fields."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=42,
            column=10,
            rule_id="E501",
            message="Line too long",
            severity="warning",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 42
        assert issue.column == 10
        assert issue.rule_id == "E501"
        assert issue.message == "Line too long"
        assert issue.severity == "warning"

    def test_code_issue_defaults(self):
        """Test CodeIssue creation with default values."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=1,
            column=1,
            rule_id="F401",
            message="Import unused",
        )

        assert issue.severity == "warning"  # default value
        assert issue.file_path == "src/test.py"

    @patch("builtins.open", new_callable=mock_open)
    def test_write_annotations_file_success(self, mock_file):
        """Test successful writing of annotations file."""
        issues = [
            CodeIssue("src/test.py", 1, 1, "F401", "Import unused"),
            CodeIssue("src/test.py", 2, 5, "E302", "Expected 2 blank lines"),
        ]

        result = write_annotations_file(issues, "annotations.json")

        assert result is True
        mock_file.assert_called_once_with("annotations.json", "w", encoding="utf-8")

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_write_annotations_file_permission_error(self, mock_file):
        """Test writing annotations file with permission error."""
        issues = [CodeIssue("src/test.py", 1, 1, "F401", "Import unused")]

        result = write_annotations_file(issues, "/root/annotations.json")

        assert result is False

    @patch("builtins.open", side_effect=OSError("Disk full"))
    def test_write_annotations_file_os_error(self, mock_file):
        """Test writing annotations file with OS error."""
        issues = [CodeIssue("src/test.py", 1, 1, "F401", "Import unused")]

        result = write_annotations_file(issues, "annotations.json")

        assert result is False

    def test_parse_lint_output_empty(self):
        """Test parsing empty lint output."""
        result = parse_lint_output("")

        assert result == []

    def test_parse_lint_output_single_line(self):
        """Test parsing single line lint output."""
        output = "src/test.py:1:1: F401 'os' imported but unused"

        result = parse_lint_output(output)

        assert len(result) == 1
        assert result[0].file_path == "src/test.py"
        assert result[0].line_number == 1
        assert result[0].column == 1
        assert result[0].rule_id == "F401"
        assert result[0].message == "'os' imported but unused"

    def test_parse_lint_output_multiple_lines(self):
        """Test parsing multiple lines of lint output."""
        output = """src/test.py:1:1: F401 'os' imported but unused
src/test.py:2:5: E302 expected 2 blank lines, found 1
src/test.py:10:80: E501 line too long (120 > 100 characters)"""

        result = parse_lint_output(output)

        assert len(result) == 3
        assert result[0].rule_id == "F401"
        assert result[1].rule_id == "E302"
        assert result[2].rule_id == "E501"

    def test_parse_lint_output_malformed_line(self):
        """Test parsing malformed lint output line."""
        output = "src/test.py:invalid:1: F401 'os' imported but unused"

        result = parse_lint_output(output)

        assert result == []

    def test_parse_lint_output_with_column(self):
        """Test parsing lint output with column information."""
        output = "src/test.py:1:5: F401 'os' imported but unused"

        result = parse_lint_output(output)

        assert len(result) == 1
        assert result[0].column == 5

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        result = parse_mypy_output("")

        assert result == []

    def test_parse_mypy_output_single_line(self):
        """Test parsing single line mypy output."""
        output = "src/test.py:1: error: Name 'undefined_var' is not defined"

        result = parse_mypy_output(output)

        assert len(result) == 1
        assert result[0].file_path == "src/test.py"
        assert result[0].line_number == 1
        assert result[0].column == 1
        assert result[0].rule_id == "mypy"
        assert "undefined_var" in result[0].message

    def test_parse_mypy_output_multiple_lines(self):
        """Test parsing multiple lines of mypy output."""
        output = """src/test.py:1: error: Name 'undefined_var' is not defined
src/test.py:5: error: Argument 1 to 'len' has incompatible type 'None' (got 'str')
src/test.py:10: error: Incompatible types in assignment (expression has type 'int', variable has type 'str')"""

        result = parse_mypy_output(output)

        assert len(result) == 3
        assert all(issue.rule_id == "mypy" for issue in result)

    def test_parse_mypy_output_malformed_line(self):
        """Test parsing malformed mypy output line."""
        output = "src/test.py:invalid: error: Name 'undefined_var' is not defined"

        result = parse_mypy_output(output)

        assert result == []

    def test_parse_mypy_output_with_note(self):
        """Test parsing mypy output with note lines."""
        output = """src/test.py:1: error: Name 'undefined_var' is not defined
src/test.py: note: 'undefined_var' is defined here"""

        result = parse_mypy_output(output)

        assert len(result) == 1  # Note lines should be ignored

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        result = parse_bandit_output("")

        assert result == []

    def test_parse_bandit_output_single_issue(self):
        """Test parsing single bandit issue."""
        output = """>> Issue: [B101:assert_used] Use of assert detected. The assert statement is not reliable in production code.
   Severity: Low   Confidence: High
   Location: src/test.py:1:0"""

        result = parse_bandit_output(output)

        assert len(result) == 1
        assert result[0].file_path == "src/test.py"
        assert result[0].line_number == 1
        assert result[0].column == 1
        assert result[0].rule_id == "B101"
        assert "assert detected" in result[0].message

    def test_parse_bandit_output_multiple_issues(self):
        """Test parsing multiple bandit issues."""
        output = """>> Issue: [B101:assert_used] Use of assert detected
   Severity: Low   Confidence: High
   Location: src/test.py:1:0
>> Issue: [B102:exec_used] Use of exec detected
   Severity: High   Confidence: Medium
   Location: src/test.py:5:0"""

        result = parse_bandit_output(output)

        assert len(result) == 2
        assert result[0].rule_id == "B101"
        assert result[1].rule_id == "B102"

    def test_parse_bandit_output_malformed(self):
        """Test parsing malformed bandit output."""
        output = ">> Issue: [B101:assert_used] Use of assert detected"

        result = parse_bandit_output(output)

        assert result == []

    def test_parse_bandit_output_with_extra_lines(self):
        """Test parsing bandit output with extra lines."""
        output = """>> Issue: [B101:assert_used] Use of assert detected
   Severity: Low   Confidence: High
   Location: src/test.py:1:0
   Extra information here
   More details"""

        result = parse_bandit_output(output)

        assert len(result) == 1
        assert result[0].rule_id == "B101"

    def test_create_github_annotation_success(self):
        """Test successful creation of GitHub annotation."""
        issue = CodeIssue("src/test.py", 42, 10, "E501", "Line too long")

        annotation = create_github_annotation(issue)

        assert annotation["path"] == "src/test.py"
        assert annotation["start_line"] == 42
        assert annotation["end_line"] == 42
        assert annotation["start_column"] == 10
        assert annotation["end_column"] == 10
        assert annotation["annotation_level"] == "warning"
        assert "Line too long" in annotation["message"]

    def test_create_github_annotation_error_severity(self):
        """Test GitHub annotation creation with error severity."""
        issue = CodeIssue("src/test.py", 1, 1, "F401", "Import unused", "error")

        annotation = create_github_annotation(issue)

        assert annotation["annotation_level"] == "failure"

    def test_create_github_annotation_note_severity(self):
        """Test GitHub annotation creation with note severity."""
        issue = CodeIssue("src/test.py", 1, 1, "F401", "Import unused", "note")

        annotation = create_github_annotation(issue)

        assert annotation["annotation_level"] == "notice"

    def test_format_annotation_message_basic(self):
        """Test basic annotation message formatting."""
        issue = CodeIssue("src/test.py", 1, 1, "F401", "Import unused")

        message = format_annotation_message(issue)

        assert "F401" in message
        assert "Import unused" in message
        assert "src/test.py:1" in message

    def test_format_annotation_message_with_severity(self):
        """Test annotation message formatting with severity."""
        issue = CodeIssue("src/test.py", 1, 1, "F401", "Import unused", "error")

        message = format_annotation_message(issue)

        assert "[ERROR]" in message
        assert "F401" in message

    def test_format_annotation_message_long_message(self):
        """Test annotation message formatting with long message."""
        long_message = "This is a very long message that should be truncated to fit within reasonable limits for GitHub annotations"
        issue = CodeIssue("src/test.py", 1, 1, "F401", long_message)

        message = format_annotation_message(issue)

        assert len(message) <= 200  # GitHub annotation limit
        assert "F401" in message

    @patch("ai_guard.pr_annotations.parse_lint_output")
    @patch("ai_guard.pr_annotations.parse_mypy_output")
    @patch("ai_guard.pr_annotations.parse_bandit_output")
    def test_create_pr_annotations_with_all_sources(
        self, mock_bandit, mock_mypy, mock_lint
    ):
        """Test creating PR annotations from all sources."""
        mock_lint.return_value = [
            CodeIssue("src/test.py", 1, 1, "F401", "Import unused")
        ]
        mock_mypy.return_value = [CodeIssue("src/test.py", 5, 1, "mypy", "Type error")]
        mock_bandit.return_value = [
            CodeIssue("src/test.py", 10, 1, "B101", "Assert used")
        ]

        annotations = create_pr_annotations(
            lint_output="lint output",
            mypy_output="mypy output",
            bandit_output="bandit output",
        )

        assert len(annotations) == 3
        assert mock_lint.called
        assert mock_mypy.called
        assert mock_bandit.called

    @patch("ai_guard.pr_annotations.parse_lint_output")
    def test_create_pr_annotations_lint_only(self, mock_lint):
        """Test creating PR annotations from lint output only."""
        mock_lint.return_value = [
            CodeIssue("src/test.py", 1, 1, "F401", "Import unused")
        ]

        annotations = create_pr_annotations(lint_output="lint output")

        assert len(annotations) == 1
        assert mock_lint.called

    def test_create_pr_annotations_no_outputs(self):
        """Test creating PR annotations with no outputs."""
        annotations = create_pr_annotations()

        assert annotations == []

    @patch("ai_guard.pr_annotations.write_annotations_file")
    def test_create_pr_annotations_with_file_write(self, mock_write):
        """Test creating PR annotations and writing to file."""
        mock_write.return_value = True

        result = create_pr_annotations(
            lint_output="src/test.py:1:1: F401 'os' imported but unused",
            output_file="annotations.json",
        )

        assert result is True
        mock_write.assert_called_once()

    @patch("ai_guard.pr_annotations.write_annotations_file")
    def test_create_pr_annotations_file_write_failure(self, mock_write):
        """Test creating PR annotations with file write failure."""
        mock_write.return_value = False

        result = create_pr_annotations(
            lint_output="src/test.py:1:1: F401 'os' imported but unused",
            output_file="annotations.json",
        )

        assert result is False

    def test_parse_lint_output_with_tabs(self):
        """Test parsing lint output with tab characters."""
        output = "src/test.py:1:1:\tF401 'os' imported but unused"

        result = parse_lint_output(output)

        assert len(result) == 1
        assert result[0].rule_id == "F401"

    def test_parse_mypy_output_with_colons_in_message(self):
        """Test parsing mypy output with colons in the message."""
        output = "src/test.py:1: error: Argument 1 to 'func' has incompatible type 'str'; expected 'int'"

        result = parse_mypy_output(output)

        assert len(result) == 1
        assert "incompatible type" in result[0].message

    def test_parse_bandit_output_with_special_characters(self):
        """Test parsing bandit output with special characters."""
        output = """>> Issue: [B101:assert_used] Use of assert detected (line contains 'assert x == y')
   Severity: Low   Confidence: High
   Location: src/test.py:1:0"""

        result = parse_bandit_output(output)

        assert len(result) == 1
        assert "assert detected" in result[0].message
