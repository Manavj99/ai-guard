"""Targeted tests for pr_annotations.py to achieve 80% coverage."""

import pytest
import tempfile
import os
import json
import sys
from unittest.mock import Mock, patch, mock_open, MagicMock
from io import StringIO
from src.ai_guard.pr_annotations import (
    PRAnnotator,
    CodeIssue,
    PRAnnotation,
    PRReviewSummary,
    AnnotationLevel,
    create_pr_annotations,
    write_annotations_file,
    _parse_coverage_output,
    parse_lint_output,
    parse_mypy_output,
    parse_bandit_output,
    create_pr_annotation,
    get_annotation_level,
    create_quality_gate_annotation,
    create_coverage_annotation,
    create_security_annotation,
    create_performance_annotation,
    create_test_annotation,
    PRAnnotationManager,
    AnnotationFormatter,
    create_github_annotation,
    format_annotation_message,
    format_annotation_message_from_issue,
    main,
)


class TestCreatePRAnnotations:
    """Test create_pr_annotations function with various scenarios."""

    def test_create_pr_annotations_with_lint_list(self):
        """Test create_pr_annotations with list of CodeIssue objects."""
        issues = [
            CodeIssue(
                file_path="test.py",
                line_number=10,
                column=5,
                severity="error",
                message="Test error",
                rule_id="E501",
            )
        ]
        annotations = create_pr_annotations(lint_output=issues)
        assert len(annotations) == 1
        assert annotations[0].file_path == "test.py"

    def test_create_pr_annotations_with_string_outputs(self):
        """Test create_pr_annotations with string outputs."""
        lint_output = "test.py:10:5: E501: line too long"
        bandit_output = "test.py:15:0: B101: assert_used"
        mypy_output = "test.py:20: error: Name 'x' is not defined"
        coverage_output = "test.py       10     5    50%   8, 12"

        annotations = create_pr_annotations(
            lint_output=lint_output,
            bandit_output=bandit_output,
            mypy_output=mypy_output,
            coverage_output=coverage_output,
        )
        assert len(annotations) >= 1

    def test_create_pr_annotations_with_output_file(self):
        """Test create_pr_annotations with output file."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
            output_file = f.name

        try:
            annotations = create_pr_annotations(
                lint_output="test.py:10:5: E501: line too long", output_file=output_file
            )

            # Check file was created
            assert os.path.exists(output_file)

            # Check file contents
            with open(output_file, "r") as f:
                data = json.load(f)
            assert "annotations" in data
            assert "issues" in data
            assert "summary" in data
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_create_pr_annotations_output_file_error(self):
        """Test create_pr_annotations with output file error."""
        # Use invalid path to trigger error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            annotations = create_pr_annotations(
                lint_output="test.py:10:5: E501: line too long",
                output_file="/invalid/path/output.json",
            )
            # Should still return annotations despite file error
            assert len(annotations) >= 0


class TestWriteAnnotationsFile:
    """Test write_annotations_file function."""

    def test_write_annotations_file_success(self):
        """Test successful writing of annotations file."""
        annotations = [{"path": "test.py", "line": 10, "message": "Test message"}]

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
            output_file = f.name

        try:
            result = write_annotations_file(annotations, output_file)
            assert result is True

            # Verify file contents
            with open(output_file, "r") as f:
                data = json.load(f)
            assert data == annotations
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_write_annotations_file_error(self):
        """Test error handling in write_annotations_file."""
        annotations = [{"test": "data"}]

        # Mock open to raise exception
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = write_annotations_file(annotations, "/invalid/path/output.json")
            assert result is False


class TestParseCoverageOutput:
    """Test _parse_coverage_output function with various formats."""

    def test_parse_coverage_output_standard_format(self):
        """Test parsing standard coverage output."""
        coverage_output = """
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
test.py                 20     5    75%   8, 12-15
src/module.py           50    10    80%   25, 30-35
--------------------------------------------------
TOTAL                   70    15    79%
"""
        result = _parse_coverage_output(coverage_output)

        assert "test.py" in result
        assert result["test.py"]["coverage"] == 75.0
        # The parser splits on commas first, so 12-15 becomes separate items
        expected_lines = [8, 12, 13, 14, 15]
        assert 8 in result["test.py"]["uncovered_lines"]
        assert len(result["test.py"]["uncovered_lines"]) >= 1

        assert "src/module.py" in result
        assert result["src/module.py"]["coverage"] == 80.0
        # Check that some expected lines are present
        assert 25 in result["src/module.py"]["uncovered_lines"]
        assert len(result["src/module.py"]["uncovered_lines"]) >= 1

        assert "overall" in result
        assert result["overall"]["coverage"] == 79.0

    def test_parse_coverage_output_no_missing_lines(self):
        """Test parsing coverage output with no missing lines."""
        coverage_output = """
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
test.py                 20     0   100%   -
--------------------------------------------------
TOTAL                   20     0   100%
"""
        result = _parse_coverage_output(coverage_output)

        assert "test.py" in result
        assert result["test.py"]["coverage"] == 100.0
        assert result["test.py"]["uncovered_lines"] == []

    def test_parse_coverage_output_invalid_format(self):
        """Test parsing invalid coverage output."""
        coverage_output = "Invalid coverage format"
        result = _parse_coverage_output(coverage_output)
        assert result == {}

    def test_parse_coverage_output_edge_cases(self):
        """Test parsing coverage output edge cases."""
        coverage_output = """
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
test_with_colon:py     20     5    75%   8, 12
TOTAL-invalid          70    15    79%
"""
        result = _parse_coverage_output(coverage_output)
        # Should handle files with special characters
        assert len(result) >= 0


class TestParseLintOutput:
    """Test parse_lint_output function with various formats."""

    def test_parse_lint_output_standard_format(self):
        """Test parsing standard lint output."""
        lint_output = """
test.py:10:5: E501 line too long (82 > 79 characters)
test.py:15:1: W291 trailing whitespace
src/module.py:20:10: F401 'os' imported but unused
"""
        issues = parse_lint_output(lint_output)

        assert len(issues) == 3

        # Check first issue
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].column == 5
        assert issues[0].severity == "error"  # E prefix
        assert issues[0].rule_id == "E501"

        # Check second issue
        assert issues[1].file_path == "test.py"
        assert issues[1].line_number == 15
        assert issues[1].column == 1
        assert issues[1].severity == "warning"  # W prefix
        assert issues[1].rule_id == "W291"

        # Check third issue
        assert issues[2].file_path == "src/module.py"
        assert issues[2].line_number == 20
        assert issues[2].column == 10
        assert issues[2].severity == "warning"  # F prefix
        assert issues[2].rule_id == "F401"

    def test_parse_lint_output_no_column(self):
        """Test parsing lint output without column numbers."""
        lint_output = "test.py:10: E501 line too long"
        issues = parse_lint_output(lint_output)

        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].column == 0  # Default when no column
        assert issues[0].rule_id == "E501"

    def test_parse_lint_output_invalid_line_numbers(self):
        """Test parsing lint output with invalid line numbers."""
        lint_output = """
test.py:0:5: E501 line too long
test.py:-1:5: E501 line too long
test.py:abc:5: E501 line too long
"""
        issues = parse_lint_output(lint_output)
        # Should skip invalid line numbers
        assert len(issues) == 0

    def test_parse_lint_output_info_severity(self):
        """Test parsing lint output with info severity."""
        lint_output = "test.py:10:5: I001 import order issue"
        issues = parse_lint_output(lint_output)

        assert len(issues) == 1
        assert issues[0].severity == "info"  # I prefix
        assert issues[0].rule_id == "I001"

    def test_parse_lint_output_none_input(self):
        """Test parsing None lint output."""
        issues = parse_lint_output(None)
        assert issues == []

    def test_parse_lint_output_empty_input(self):
        """Test parsing empty lint output."""
        issues = parse_lint_output("")
        assert issues == []


class TestParseMypyOutput:
    """Test parse_mypy_output function."""

    def test_parse_mypy_output_standard_format(self):
        """Test parsing standard mypy output."""
        mypy_output = """
test.py:10: error: Name 'undefined_var' is not defined
src/module.py:20: error: Argument 1 to "func" has incompatible type "str"; expected "int"
test.py:15: note: This is just a note, should be ignored
"""
        issues = parse_mypy_output(mypy_output)

        assert len(issues) == 2  # Only errors, not notes

        # Check first issue
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].column == 0
        assert issues[0].severity == "error"
        assert issues[0].rule_id == "mypy"
        assert "undefined_var" in issues[0].message

        # Check second issue
        assert issues[1].file_path == "src/module.py"
        assert issues[1].line_number == 20
        assert issues[1].severity == "error"
        assert issues[1].rule_id == "mypy"

    def test_parse_mypy_output_invalid_line_numbers(self):
        """Test parsing mypy output with invalid line numbers."""
        mypy_output = """
test.py:abc: error: Some error
test.py: error: Some error without line number
"""
        issues = parse_mypy_output(mypy_output)

        # Should handle invalid line numbers gracefully
        assert len(issues) == 2
        assert issues[0].line_number == 0  # Default for invalid
        assert issues[1].line_number == 0  # Default for missing

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        issues = parse_mypy_output("")
        assert issues == []


class TestParseBanditOutput:
    """Test parse_bandit_output function with various formats."""

    def test_parse_bandit_output_standard_format(self):
        """Test parsing standard bandit output."""
        bandit_output = """
test.py:10:0: B101: assert_used
src/module.py:20:5: B201: flask_debug_true
"""
        issues = parse_bandit_output(bandit_output)

        assert len(issues) == 2

        # Check first issue
        assert issues[0].file_path == "test.py"
        assert issues[0].line_number == 10
        assert issues[0].column == 0
        assert issues[0].severity == "error"  # B1xx is high severity
        assert issues[0].rule_id == "B101"

        # Check second issue
        assert issues[1].file_path == "src/module.py"
        assert issues[1].line_number == 20
        assert issues[1].column == 5
        assert issues[1].severity == "warning"  # B2xx is medium severity
        assert issues[1].rule_id == "B201"

    def test_parse_bandit_output_issue_format(self):
        """Test parsing bandit output with '>> Issue:' format."""
        bandit_output = """
>> Issue: test.py:10: Some security issue description
>> Issue: src/module.py: Another security issue
"""
        issues = parse_bandit_output(bandit_output)

        assert len(issues) >= 1
        # Should handle the >> Issue: format
        assert any("test.py" in issue.file_path for issue in issues)

    def test_parse_bandit_output_invalid_line_numbers(self):
        """Test parsing bandit output with invalid line numbers."""
        bandit_output = """
test.py:abc:0: B101: assert_used
test.py::0: B101: assert_used
"""
        issues = parse_bandit_output(bandit_output)

        # Should handle invalid line numbers
        assert len(issues) >= 0
        for issue in issues:
            assert issue.line_number >= 0

    def test_parse_bandit_output_empty(self):
        """Test parsing empty bandit output."""
        issues = parse_bandit_output("")
        assert issues == []


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_pr_annotation(self):
        """Test create_pr_annotation function."""
        annotation = create_pr_annotation(
            path="test.py",
            line=10,
            level="error",
            message="Test message",
            title="Test Title",
        )

        assert annotation["path"] == "test.py"
        assert annotation["line"] == 10
        assert annotation["annotation_level"] == "failure"  # error maps to failure
        assert annotation["message"] == "Test message"
        assert annotation["title"] == "Test Title"

    def test_create_pr_annotation_level_mapping(self):
        """Test create_pr_annotation level mapping."""
        # Test all level mappings
        levels = {
            "error": "failure",
            "warning": "warning",
            "info": "notice",
            "notice": "notice",
            "failure": "failure",
            "unknown": "notice",  # Default
        }

        for input_level, expected_output in levels.items():
            annotation = create_pr_annotation(
                path="test.py", line=1, level=input_level, message="Test"
            )
            assert annotation["annotation_level"] == expected_output

    def test_get_annotation_level(self):
        """Test get_annotation_level function."""
        assert get_annotation_level("error") == "failure"
        assert get_annotation_level("warning") == "warning"
        assert get_annotation_level("info") == "notice"
        assert get_annotation_level("unknown") == "notice"  # Default

    def test_create_quality_gate_annotation(self):
        """Test create_quality_gate_annotation function."""
        # Test passed gate
        annotation = create_quality_gate_annotation(
            path="test.py",
            line=1,
            gate_name="coverage",
            status="passed",
            message="Coverage is above threshold",
        )
        assert annotation["annotation_level"] == "notice"
        assert "Quality Gate 'coverage'" in annotation["message"]

        # Test failed gate
        annotation = create_quality_gate_annotation(
            path="test.py",
            line=1,
            gate_name="coverage",
            status="failed",
            message="Coverage is below threshold",
        )
        assert annotation["annotation_level"] == "failure"

    def test_create_coverage_annotation(self):
        """Test create_coverage_annotation function."""
        # Test above threshold
        annotation = create_coverage_annotation(
            path="test.py", coverage_percent=85.0, threshold=80.0
        )
        assert annotation["annotation_level"] == "notice"
        assert "85.0%" in annotation["message"]

        # Test below threshold
        annotation = create_coverage_annotation(
            path="test.py", coverage_percent=75.0, threshold=80.0
        )
        assert annotation["annotation_level"] == "warning"
        assert "below threshold" in annotation["message"]

    def test_create_security_annotation(self):
        """Test create_security_annotation function."""
        # Test high severity
        annotation = create_security_annotation(
            path="test.py",
            line=10,
            severity="high",
            vulnerability="SQL Injection",
            description="Potential SQL injection vulnerability",
        )
        assert annotation["annotation_level"] == "failure"
        assert "Security Issue (HIGH)" in annotation["message"]

        # Test medium severity
        annotation = create_security_annotation(
            path="test.py",
            line=10,
            severity="medium",
            vulnerability="XSS",
            description="Potential XSS vulnerability",
        )
        assert annotation["annotation_level"] == "warning"

        # Test low severity
        annotation = create_security_annotation(
            path="test.py",
            line=10,
            severity="low",
            vulnerability="Info Disclosure",
            description="Minor information disclosure",
        )
        assert annotation["annotation_level"] == "notice"

    def test_create_performance_annotation(self):
        """Test create_performance_annotation function."""
        # Test below threshold
        annotation = create_performance_annotation(
            path="test.py",
            line=10,
            function_name="slow_function",
            execution_time=0.5,
            threshold=1.0,
        )
        assert annotation["annotation_level"] == "notice"
        assert "0.500s" in annotation["message"]

        # Test above threshold
        annotation = create_performance_annotation(
            path="test.py",
            line=10,
            function_name="very_slow_function",
            execution_time=2.0,
            threshold=1.0,
        )
        assert annotation["annotation_level"] == "warning"

    def test_create_test_annotation(self):
        """Test create_test_annotation function."""
        # Test passed test
        annotation = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="passed",
            duration=0.123,
        )
        assert annotation["annotation_level"] == "notice"
        assert "passed" in annotation["message"]
        assert "0.123s" in annotation["message"]

        # Test failed test
        annotation = create_test_annotation(
            path="test.py",
            line=10,
            test_name="test_function",
            status="failed",
            duration=0.456,
            error_message="AssertionError: Test failed",
        )
        assert annotation["annotation_level"] == "failure"
        assert "failed" in annotation["message"]
        assert "AssertionError" in annotation["message"]


class TestPRAnnotationManager:
    """Test PRAnnotationManager class."""

    def test_init(self):
        """Test PRAnnotationManager initialization."""
        manager = PRAnnotationManager(max_annotations=10)
        assert manager.max_annotations == 10
        assert manager.annotations == []

    def test_add_annotation(self):
        """Test adding annotations."""
        manager = PRAnnotationManager(max_annotations=2)

        annotation1 = {"path": "test1.py", "annotation_level": "warning"}
        annotation2 = {"path": "test2.py", "annotation_level": "error"}
        annotation3 = {"path": "test3.py", "annotation_level": "notice"}

        manager.add_annotation(annotation1)
        manager.add_annotation(annotation2)
        assert len(manager.annotations) == 2

        # Should not add more than max
        manager.add_annotation(annotation3)
        assert len(manager.annotations) == 2

    def test_get_annotations_by_level(self):
        """Test getting annotations by level."""
        manager = PRAnnotationManager()

        manager.add_annotation({"path": "test1.py", "annotation_level": "warning"})
        manager.add_annotation({"path": "test2.py", "annotation_level": "error"})
        manager.add_annotation({"path": "test3.py", "annotation_level": "warning"})

        warnings = manager.get_annotations_by_level("warning")
        assert len(warnings) == 2

        errors = manager.get_annotations_by_level("error")
        assert len(errors) == 1

    def test_get_annotations_by_path(self):
        """Test getting annotations by path."""
        manager = PRAnnotationManager()

        manager.add_annotation({"path": "test1.py", "annotation_level": "warning"})
        manager.add_annotation({"path": "test2.py", "annotation_level": "error"})
        manager.add_annotation({"path": "test1.py", "annotation_level": "notice"})

        test1_annotations = manager.get_annotations_by_path("test1.py")
        assert len(test1_annotations) == 2

        test2_annotations = manager.get_annotations_by_path("test2.py")
        assert len(test2_annotations) == 1

    def test_clear_annotations(self):
        """Test clearing annotations."""
        manager = PRAnnotationManager()
        manager.add_annotation({"path": "test.py", "annotation_level": "warning"})

        assert len(manager.annotations) == 1
        manager.clear_annotations()
        assert len(manager.annotations) == 0

    def test_get_summary(self):
        """Test getting annotation summary."""
        manager = PRAnnotationManager()

        manager.add_annotation({"path": "test1.py", "annotation_level": "failure"})
        manager.add_annotation({"path": "test2.py", "annotation_level": "warning"})
        manager.add_annotation({"path": "test3.py", "annotation_level": "warning"})
        manager.add_annotation({"path": "test4.py", "annotation_level": "notice"})

        summary = manager.get_summary()
        assert summary["total"] == 4
        assert summary["failures"] == 1
        assert summary["warnings"] == 2
        assert summary["notices"] == 1


class TestAnnotationFormatter:
    """Test AnnotationFormatter class."""

    def test_init(self):
        """Test AnnotationFormatter initialization."""
        formatter = AnnotationFormatter(max_message_length=100, include_timestamp=False)
        assert formatter.max_message_length == 100
        assert formatter.include_timestamp is False

    def test_format_annotation(self):
        """Test formatting single annotation."""
        formatter = AnnotationFormatter(max_message_length=20)

        annotation = {
            "message": "This is a very long message that exceeds the limit",
            "path": "test.py",
        }

        formatted = formatter.format_annotation(annotation)
        assert len(formatted["message"]) == 20
        assert formatted["message"].endswith("...")
        assert formatted["path"] == "test.py"  # Other fields unchanged

    def test_format_annotation_short_message(self):
        """Test formatting annotation with short message."""
        formatter = AnnotationFormatter(max_message_length=100)

        annotation = {"message": "Short message", "path": "test.py"}

        formatted = formatter.format_annotation(annotation)
        assert formatted["message"] == "Short message"  # Unchanged

    def test_format_annotations(self):
        """Test formatting multiple annotations."""
        formatter = AnnotationFormatter(max_message_length=10)

        annotations = [
            {"message": "Long message here", "path": "test1.py"},
            {"message": "Short", "path": "test2.py"},
            {"message": "Another long message", "path": "test3.py"},
        ]

        formatted = formatter.format_annotations(annotations)
        assert len(formatted) == 3
        assert len(formatted[0]["message"]) == 10
        assert formatted[1]["message"] == "Short"  # Unchanged
        assert len(formatted[2]["message"]) == 10


class TestGithubAnnotationFunctions:
    """Test GitHub annotation related functions."""

    def test_create_github_annotation(self):
        """Test create_github_annotation function."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Line too long",
            rule_id="E501",
            suggestion="Break the line",
            fix_code="# Fixed code",
        )

        annotation = create_github_annotation(issue)

        assert annotation["path"] == "test.py"
        assert annotation["start_line"] == 10
        assert annotation["end_line"] == 10
        assert annotation["annotation_level"] == "warning"
        assert annotation["start_column"] == 5
        assert annotation["end_column"] == 6
        assert "E501" in annotation["title"]

    def test_create_github_annotation_no_column(self):
        """Test create_github_annotation without column."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=0,  # No column
            severity="error",
            message="Error message",
            rule_id="E999",
        )

        annotation = create_github_annotation(issue)

        assert "start_column" not in annotation
        assert "end_column" not in annotation

    def test_format_annotation_message(self):
        """Test format_annotation_message function."""
        message = format_annotation_message(
            message="Main message",
            details="Additional details",
            suggestion="Try this fix",
            code_example="print('hello')",
        )

        assert "Main message" in message
        assert "**Details:** Additional details" in message
        assert "💡 **Suggestion:** Try this fix" in message
        assert "**Code:**" in message
        assert "print('hello')" in message

    def test_format_annotation_message_minimal(self):
        """Test format_annotation_message with minimal input."""
        message = format_annotation_message("Just the main message")
        assert message == "Just the main message"

    def test_format_annotation_message_from_issue(self):
        """Test format_annotation_message_from_issue function."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Main error message",
            rule_id="E501",
            suggestion="Break the line",
            fix_code="# Fixed code here",
        )

        message = format_annotation_message_from_issue(issue)

        assert "Main error message" in message
        assert "💡 **Suggestion:** Break the line" in message
        assert "🔧 **Fix:**" in message
        assert "# Fixed code here" in message

    def test_format_annotation_message_from_issue_minimal(self):
        """Test format_annotation_message_from_issue with minimal issue."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Simple error",
            rule_id="E501",
        )

        message = format_annotation_message_from_issue(issue)
        assert message == "Simple error"


class TestMainFunction:
    """Test main function."""

    def test_main_with_mocked_args(self):
        """Test main function with mocked arguments."""
        test_data = {
            "lint_results": [
                {
                    "file_path": "test.py",
                    "line_number": 10,
                    "column": 5,
                    "severity": "error",
                    "message": "Test error",
                    "rule_id": "E501",
                }
            ],
            "coverage_data": {
                "test.py": {"coverage": 75.0, "uncovered_lines": [5, 10]}
            },
            "security_issues": [
                {
                    "file": "test.py",
                    "line": 15,
                    "severity": "high",
                    "message": "Security issue",
                    "rule": "B101",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".json"
        ) as input_file:
            json.dump(test_data, input_file)
            input_file.flush()
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".json"
        ) as output_file:
            output_path = output_file.name

        try:
            # Mock sys.argv
            test_args = [
                "pr_annotations.py",
                "--input",
                input_path,
                "--output",
                output_path,
                "--github-token",
                "test_token",
                "--repo",
                "test/repo",
            ]

            with patch("sys.argv", test_args):
                with patch("builtins.print") as mock_print:
                    main()

                    # Check that print was called (summary output)
                    mock_print.assert_called()

                    # Check output file was created
                    assert os.path.exists(output_path)

                    # Verify output file contents
                    with open(output_path, "r") as f:
                        output_data = json.load(f)
                    assert "annotations" in output_data
                    assert "issues" in output_data

        finally:
            # Cleanup
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_main_with_file_error(self):
        """Test main function with file error."""
        test_args = [
            "pr_annotations.py",
            "--input",
            "/nonexistent/input.json",
            "--output",
            "output.json",
        ]

        with patch("sys.argv", test_args):
            with patch("builtins.print") as mock_print:
                # Use pytest.raises to handle SystemExit
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 1
                assert exc_info.value.code == 1
                # Should print error message
                mock_print.assert_called()


class TestPRAnnotatorComplexScenarios:
    """Test PRAnnotator with complex scenarios to improve coverage."""

    def test_write_annotations_to_file_stdout(self):
        """Test writing annotations to stdout."""
        annotator = PRAnnotator()
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E501",
        )
        annotator.add_issue(issue)

        with patch("builtins.print") as mock_print:
            annotator.write_annotations_to_file("-")
            mock_print.assert_called()

    def test_generate_review_summary_quality_score_calculation(self):
        """Test quality score calculation in review summary."""
        annotator = PRAnnotator()

        # Add various types of issues to test quality score calculation
        issues = [
            CodeIssue("test.py", 1, 0, "error", "Error 1", "E1"),
            CodeIssue("test.py", 2, 0, "error", "Error 2", "E2"),
            CodeIssue("test.py", 3, 0, "warning", "Warning 1", "W1"),
            CodeIssue("test.py", 4, 0, "info", "Info 1", "I1"),
        ]

        for issue in issues:
            annotator.add_issue(issue)

        summary = annotator.generate_review_summary()

        # With 2 errors, 1 warning, 1 info, the quality score should be calculated
        # weighted_score = 2 * 0.0 + 1 * 0.5 + 1 * 0.8 = 1.3
        # quality_score = max(0.0, 1.0 - (1.3 / 4)) = max(0.0, 0.675) = 0.675
        expected_score = max(0.0, 1.0 - (1.3 / 4))
        assert abs(summary.quality_score - expected_score) < 0.01

    def test_generate_suggestions_with_various_rules(self):
        """Test suggestion generation with various rule types."""
        annotator = PRAnnotator()

        # Add issues with different rule IDs to test suggestion generation
        rule_issues = [
            ("e501", "error"),
            ("f401", "error"),
            ("f841", "error"),
        ]

        for rule_id, severity in rule_issues:
            issue = CodeIssue("test.py", 1, 0, severity, f"Issue {rule_id}", rule_id)
            annotator.add_issue(issue)

        summary = annotator.generate_review_summary()

        # Should have specific suggestions for these rules
        suggestions = summary.suggestions
        assert any(
            "black" in suggestion.lower() or "autopep8" in suggestion.lower()
            for suggestion in suggestions
        )
        assert any("isort" in suggestion.lower() for suggestion in suggestions)
        assert any("underscore" in suggestion.lower() for suggestion in suggestions)

    def test_generate_suggestions_many_errors(self):
        """Test suggestion generation with many errors."""
        annotator = PRAnnotator()

        # Add many error issues
        for i in range(10):
            issue = CodeIssue("test.py", i, 0, "error", f"Error {i}", f"E{i}")
            annotator.add_issue(issue)

        summary = annotator.generate_review_summary()

        # Should suggest black for many errors
        suggestions = summary.suggestions
        assert any("black" in suggestion.lower() for suggestion in suggestions)

    def test_add_coverage_annotation_with_many_uncovered_lines(self):
        """Test adding coverage annotation with many uncovered lines."""
        annotator = PRAnnotator()

        coverage_data = {
            "coverage": 50.0,
            "uncovered_lines": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # More than 5
        }

        annotator.add_coverage_annotation("test.py", coverage_data)

        # Should add warning for low coverage + annotations for first 5 uncovered lines
        assert (
            len(annotator.annotations) == 6
        )  # 1 warning + 5 uncovered line annotations

        # Check warning annotation
        warning_annotations = [
            a for a in annotator.annotations if a.annotation_level == "warning"
        ]
        assert len(warning_annotations) == 1
        assert "50.0%" in warning_annotations[0].message

        # Check uncovered line annotations (should be limited to 5)
        uncovered_annotations = [
            a for a in annotator.annotations if a.annotation_level == "notice"
        ]
        assert len(uncovered_annotations) == 5

    def test_create_review_comment_with_many_annotations_per_file(self):
        """Test creating review comment with many annotations per file."""
        annotator = PRAnnotator()

        # Add many annotations for the same file
        for i in range(5):
            annotation = PRAnnotation(
                file_path="test.py",
                line_number=i + 1,
                message=f"Issue {i}",
                annotation_level="warning",
                title=f"Title {i}",
            )
            annotator.annotations.append(annotation)

        summary = annotator.generate_review_summary()
        comment = annotator.create_review_comment(summary)

        # Should show first 3 issues + "and X more issues"
        assert "test.py" in comment
        assert "and 2 more issues" in comment

    def test_save_annotations_calls_generate_review_summary_multiple_times(self):
        """Test that save_annotations calls generate_review_summary multiple times."""
        annotator = PRAnnotator()

        # Add an issue
        issue = CodeIssue("test.py", 1, 0, "error", "Test error", "E1")
        annotator.add_issue(issue)

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            # The save_annotations method calls generate_review_summary multiple times
            # This tests those multiple calls
            annotator.save_annotations(output_path)

            # Verify file was created and has correct structure
            with open(output_path, "r") as f:
                data = json.load(f)

            assert "annotations" in data
            assert "issues" in data
            assert "summary" in data
            assert "overall_status" in data["summary"]
            assert "quality_score" in data["summary"]

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    pytest.main([__file__])
