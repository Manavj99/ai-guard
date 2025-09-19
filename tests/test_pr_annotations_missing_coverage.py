"""Additional tests for pr_annotations.py to improve coverage."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock, Mock
from pathlib import Path

from src.ai_guard.pr_annotations import (
    AnnotationLevel, CodeIssue, PRAnnotation, PRReviewSummary, PRAnnotator,
    create_pr_annotations, write_annotations_file, parse_lint_output,
    parse_mypy_output, parse_bandit_output, create_github_annotation,
    format_annotation_message, _parse_coverage_output
)


class TestPRAnnotatorAdvanced:
    """Test advanced PRAnnotator functionality."""
    
    def test_pr_annotator_with_custom_config(self):
        """Test PRAnnotator with custom configuration."""
        config = {
            "max_annotations": 50,
            "group_by_file": True,
            "include_suggestions": True,
            "severity_threshold": "warning",
            "output_format": "json"
        }
        
        annotator = PRAnnotator(config)
        assert annotator.config["max_annotations"] == 50
        assert annotator.config["group_by_file"] is True
        assert annotator.config["include_suggestions"] is True
        assert annotator.config["severity_threshold"] == "warning"
        assert annotator.config["output_format"] == "json"
    
    def test_pr_annotator_with_invalid_config(self):
        """Test PRAnnotator with invalid configuration."""
        config = {
            "max_annotations": "invalid",
            "group_by_file": "invalid",
            "include_suggestions": "invalid",
            "severity_threshold": "invalid",
            "output_format": "invalid"
        }
        
        annotator = PRAnnotator(config)
        # Should use defaults for invalid values
        assert annotator.config["max_annotations"] == 100
        assert annotator.config["group_by_file"] is True
        assert annotator.config["include_suggestions"] is True
        assert annotator.config["severity_threshold"] == "info"
        assert annotator.config["output_format"] == "github"
    
    def test_add_annotation_with_custom_severity(self):
        """Test adding annotation with custom severity."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="critical",
            message="Critical error",
            rule_id="C001",
            suggestion="Fix immediately"
        )
        
        annotator.add_annotation(issue)
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].severity == "critical"
    
    def test_add_annotation_with_fix_code(self):
        """Test adding annotation with fix code."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Error message",
            rule_id="E001",
            suggestion="Fix this",
            fix_code="fixed_code()"
        )
        
        annotator.add_annotation(issue)
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].fix_code == "fixed_code()"
    
    def test_add_annotation_with_none_values(self):
        """Test adding annotation with None values."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Warning message",
            rule_id="W001"
        )
        
        annotator.add_annotation(issue)
        assert len(annotator.annotations) == 1
        assert annotator.annotations[0].suggestion is None
        assert annotator.annotations[0].fix_code is None
    
    def test_add_annotation_exceeds_max(self):
        """Test adding annotation when exceeding max annotations."""
        config = {"max_annotations": 2}
        annotator = PRAnnotator(config)
        
        # Add 3 annotations
        for i in range(3):
            issue = CodeIssue(
                file_path=f"test{i}.py",
                line_number=10,
                column=5,
                severity="error",
                message=f"Error {i}",
                rule_id=f"E00{i}"
            )
            annotator.add_annotation(issue)
        
        # Should only keep the first 2
        assert len(annotator.annotations) == 2
    
    def test_get_annotations_by_severity(self):
        """Test getting annotations by severity."""
        annotator = PRAnnotator()
        
        # Add annotations with different severities
        severities = ["error", "warning", "info", "error", "warning"]
        for i, severity in enumerate(severities):
            issue = CodeIssue(
                file_path=f"test{i}.py",
                line_number=10,
                column=5,
                severity=severity,
                message=f"Message {i}",
                rule_id=f"R00{i}"
            )
            annotator.add_annotation(issue)
        
        error_annotations = annotator.get_annotations_by_severity("error")
        assert len(error_annotations) == 2
        
        warning_annotations = annotator.get_annotations_by_severity("warning")
        assert len(warning_annotations) == 2
        
        info_annotations = annotator.get_annotations_by_severity("info")
        assert len(info_annotations) == 1
    
    def test_get_annotations_by_file(self):
        """Test getting annotations by file."""
        annotator = PRAnnotator()
        
        # Add annotations for different files
        files = ["test1.py", "test2.py", "test1.py", "test3.py"]
        for i, file_path in enumerate(files):
            issue = CodeIssue(
                file_path=file_path,
                line_number=10,
                column=5,
                severity="error",
                message=f"Message {i}",
                rule_id=f"R00{i}"
            )
            annotator.add_annotation(issue)
        
        test1_annotations = annotator.get_annotations_by_file("test1.py")
        assert len(test1_annotations) == 2
        
        test2_annotations = annotator.get_annotations_by_file("test2.py")
        assert len(test2_annotations) == 1
        
        test3_annotations = annotator.get_annotations_by_file("test3.py")
        assert len(test3_annotations) == 1
    
    def test_get_annotation_summary(self):
        """Test getting annotation summary."""
        annotator = PRAnnotator()
        
        # Add annotations with different severities
        severities = ["error", "warning", "info", "error", "warning", "info"]
        for i, severity in enumerate(severities):
            issue = CodeIssue(
                file_path=f"test{i}.py",
                line_number=10,
                column=5,
                severity=severity,
                message=f"Message {i}",
                rule_id=f"R00{i}"
            )
            annotator.add_annotation(issue)
        
        summary = annotator.get_annotation_summary()
        assert summary["total"] == 6
        assert summary["error"] == 2
        assert summary["warning"] == 2
        assert summary["info"] == 2
        assert summary["files_affected"] == 6
    
    def test_clear_annotations(self):
        """Test clearing annotations."""
        annotator = PRAnnotator()
        
        # Add some annotations
        for i in range(3):
            issue = CodeIssue(
                file_path=f"test{i}.py",
                line_number=10,
                column=5,
                severity="error",
                message=f"Message {i}",
                rule_id=f"R00{i}"
            )
            annotator.add_annotation(issue)
        
        assert len(annotator.annotations) == 3
        
        annotator.clear_annotations()
        assert len(annotator.annotations) == 0
    
    def test_export_annotations_json(self):
        """Test exporting annotations to JSON."""
        annotator = PRAnnotator()
        
        # Add some annotations
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix this"
        )
        annotator.add_annotation(issue)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            annotator.export_annotations(temp_file, "json")
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            assert "annotations" in data
            assert len(data["annotations"]) == 1
            assert data["annotations"][0]["file_path"] == "test.py"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_export_annotations_csv(self):
        """Test exporting annotations to CSV."""
        annotator = PRAnnotator()
        
        # Add some annotations
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix this"
        )
        annotator.add_annotation(issue)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            annotator.export_annotations(temp_file, "csv")
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            assert "test.py" in content
            assert "Test error" in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_export_annotations_markdown(self):
        """Test exporting annotations to Markdown."""
        annotator = PRAnnotator()
        
        # Add some annotations
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix this"
        )
        annotator.add_annotation(issue)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_file = f.name
        
        try:
            annotator.export_annotations(temp_file, "markdown")
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            assert "# Annotations Report" in content
            assert "test.py" in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_export_annotations_invalid_format(self):
        """Test exporting annotations with invalid format."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        annotator.add_annotation(issue)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            annotator.export_annotations(temp_file, "invalid")
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_parse_lint_output_flake8(self):
        """Test parsing flake8 output."""
        flake8_output = """test.py:1:1: E501 line too long (80 > 79 characters)
test.py:2:5: W292 no newline at end of file
test.py:3:10: F401 'os' imported but unused"""
        
        issues = parse_lint_output(flake8_output, "flake8")
        assert len(issues) == 3
        assert issues[0].rule_id == "E501"
        assert issues[1].rule_id == "W292"
        assert issues[2].rule_id == "F401"
    
    def test_parse_lint_output_pylint(self):
        """Test parsing pylint output."""
        pylint_output = """test.py:1:0: C0114: Missing module docstring (missing-module-docstring)
test.py:5:4: W0612: Unused variable 'x' (unused-variable)
test.py:10:0: E1121: Too many positional arguments for function call (too-many-function-args)"""
        
        issues = parse_lint_output(pylint_output, "pylint")
        assert len(issues) == 3
        assert issues[0].rule_id == "C0114"
        assert issues[1].rule_id == "W0612"
        assert issues[2].rule_id == "E1121"
    
    def test_parse_lint_output_black(self):
        """Test parsing black output."""
        black_output = """would reformat test.py
All done! ✨ 🍰 ✨
1 file would be reformatted."""
        
        issues = parse_lint_output(black_output, "black")
        assert len(issues) == 1
        assert issues[0].rule_id == "black"
        assert "would reformat" in issues[0].message
    
    def test_parse_lint_output_unknown_tool(self):
        """Test parsing output from unknown tool."""
        output = "Some unknown output format"
        
        issues = parse_lint_output(output, "unknown_tool")
        assert len(issues) == 0
    
    def test_parse_mypy_output(self):
        """Test parsing mypy output."""
        mypy_output = """test.py:5: error: Argument 1 to "func" has incompatible type "str"; expected "int"
test.py:10: note: Revealed type is 'builtins.str'
test.py:15: warning: unused "type: ignore" comment"""
        
        issues = parse_mypy_output(mypy_output)
        assert len(issues) == 2  # error and warning, but not note
        assert issues[0].severity == "error"
        assert issues[1].severity == "warning"
    
    def test_parse_bandit_output(self):
        """Test parsing bandit output."""
        bandit_output = """[main]  INFO    profile include tests: None
[main]  INFO    profile exclude tests: None
[main]  INFO    cli include tests: None
[main]  INFO    cli exclude tests: None
[main]  INFO    running on Python 3.11.3
Run started:2025-01-17 12:00:00.000000

Test results:
>> Issue: [B101:test_assert_used] Use of assert detected. The enclosed code will be removed when compiling to optimized byte code.
   Severity: Low   Confidence: High
   Location: test.py:5:5
   More Info: https://bandit.readthedocs.io/en/1.7.5/plugins/b101_test_assert_used.html"""
        
        issues = parse_bandit_output(bandit_output)
        assert len(issues) == 1
        assert issues[0].rule_id == "B101"
        assert issues[0].severity == "warning"  # Low severity maps to warning
        assert issues[0].line_number == 5
    
    def test_create_github_annotation(self):
        """Test creating GitHub annotation."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix this"
        )
        
        annotation = create_github_annotation(issue)
        assert annotation["path"] == "test.py"
        assert annotation["start_line"] == 10
        assert annotation["end_line"] == 10
        assert annotation["annotation_level"] == "failure"
        assert "Test error" in annotation["message"]
    
    def test_create_github_annotation_warning(self):
        """Test creating GitHub annotation for warning."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="warning",
            message="Test warning",
            rule_id="W001"
        )
        
        annotation = create_github_annotation(issue)
        assert annotation["annotation_level"] == "warning"
    
    def test_create_github_annotation_notice(self):
        """Test creating GitHub annotation for notice."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="info",
            message="Test info",
            rule_id="I001"
        )
        
        annotation = create_github_annotation(issue)
        assert annotation["annotation_level"] == "notice"
    
    def test_format_annotation_message_with_suggestion(self):
        """Test formatting annotation message with suggestion."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001",
            suggestion="Fix this"
        )
        
        message = format_annotation_message(issue)
        assert "Test error" in message
        assert "Fix this" in message
        assert "E001" in message
    
    def test_format_annotation_message_without_suggestion(self):
        """Test formatting annotation message without suggestion."""
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        
        message = format_annotation_message(issue)
        assert "Test error" in message
        assert "E001" in message
        assert "Suggestion:" not in message
    
    def test_parse_coverage_output(self):
        """Test parsing coverage output."""
        coverage_output = """Name                     Stmts   Miss  Cover   Missing
-----------------------------------------------------
test.py                     10      2    80%   3-4, 8
test2.py                     5      0   100%
-----------------------------------------------------
TOTAL                       15      2    87%"""
        
        gaps = _parse_coverage_output(coverage_output)
        assert len(gaps) == 1  # Only test.py has gaps
        assert gaps[0].file_path == "test.py"
        assert gaps[0].line_number == 3  # First missing line
        assert gaps[0].severity == "warning"
    
    def test_parse_test_results(self):
        """Test parsing test results."""
        test_output = """test_basic_function ... ok
test_edge_cases ... FAIL
test_error_handling ... ERROR
test_performance ... SKIP

======================================================================
FAIL: test_edge_cases
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test.py", line 10, in test_edge_cases
    assert result == expected
AssertionError: 1 != 2

======================================================================
ERROR: test_error_handling
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test.py", line 15, in test_error_handling
    raise ValueError("Test error")
ValueError: Test error

Ran 4 tests in 0.001s

FAILED (failures=1, errors=1)"""
        
        results = _parse_test_results(test_output)
        assert len(results) == 2  # Only failures and errors
        assert results[0].severity == "error"  # FAIL
        assert results[1].severity == "error"  # ERROR


class TestPRAnnotatorMethods:
    """Test PRAnnotator methods that need more coverage."""
    
    def test_pr_annotator_run_method(self):
        """Test PRAnnotator run method."""
        config = {"max_annotations": 10}
        annotator = PRAnnotator(config)
        
        # Add some annotations
        for i in range(5):
            issue = CodeIssue(
                file_path=f"test{i}.py",
                line_number=10,
                column=5,
                severity="error",
                message=f"Error {i}",
                rule_id=f"E00{i}"
            )
            annotator.add_annotation(issue)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            result = annotator.run(temp_file)
            assert result is True
            assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_pr_annotator_run_method_no_annotations(self):
        """Test PRAnnotator run method with no annotations."""
        annotator = PRAnnotator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            result = annotator.run(temp_file)
            assert result is False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_pr_annotator_run_method_invalid_path(self):
        """Test PRAnnotator run method with invalid path."""
        annotator = PRAnnotator()
        
        issue = CodeIssue(
            file_path="test.py",
            line_number=10,
            column=5,
            severity="error",
            message="Test error",
            rule_id="E001"
        )
        annotator.add_annotation(issue)
        
        result = annotator.run("/invalid/path/file.json")
        assert result is False
