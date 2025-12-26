"""Comprehensive tests for diff_parser.py to improve coverage."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional

from src.ai_guard.diff_parser import (
    filter_python_files,
    parse_diff_output,
    changed_python_files,
    parse_github_event,
    get_file_extensions,
    _get_base_head_from_event,
    DiffParser,
    parse_diff,
    get_changed_files,
)


class TestFilterPythonFiles:
    """Test filter_python_files function."""

    def test_filter_python_files_none(self):
        """Test filtering with None input."""
        result = filter_python_files(None)
        assert result == []

    def test_filter_python_files_empty(self):
        """Test filtering with empty list."""
        result = filter_python_files([])
        assert result == []

    def test_filter_python_files_mixed(self):
        """Test filtering with mixed file types."""
        files = ["test.py", "test.js", "test.txt", "another.py"]
        result = filter_python_files(files)
        assert result == ["test.py", "another.py"]

    def test_filter_python_files_no_python(self):
        """Test filtering with no Python files."""
        files = ["test.js", "test.txt", "test.md"]
        result = filter_python_files(files)
        assert result == []

    def test_filter_python_files_all_python(self):
        """Test filtering with all Python files."""
        files = ["test1.py", "test2.py", "module.py"]
        result = filter_python_files(files)
        assert result == files


class TestParseDiffOutput:
    """Test parse_diff_output function."""

    def test_parse_diff_output_none(self):
        """Test parsing with None input."""
        result = parse_diff_output(None)
        assert result == []

    def test_parse_diff_output_empty(self):
        """Test parsing with empty string."""
        result = parse_diff_output("")
        assert result == []

    def test_parse_diff_output_standard_format(self):
        """Test parsing standard diff format."""
        diff_output = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    return "old"
+    return "new"
"""
        result = parse_diff_output(diff_output)
        assert "test.py" in result

    def test_parse_diff_output_multiple_files(self):
        """Test parsing diff with multiple files."""
        diff_output = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-change1
+change1_new

diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-change2
+change2_new
"""
        result = parse_diff_output(diff_output)
        assert "file1.py" in result
        assert "file2.py" in result
        assert len(result) == 2

    def test_parse_diff_output_no_files(self):
        """Test parsing diff with no file changes."""
        diff_output = """Some other content
that doesn't contain
file paths
"""
        result = parse_diff_output(diff_output)
        assert result == []


class TestParseGithubEvent:
    """Test parse_github_event function."""

    def test_parse_github_event_nonexistent_file(self):
        """Test parsing nonexistent event file."""
        result = parse_github_event("nonexistent.json")
        assert result is None

    def test_parse_github_event_valid_file(self):
        """Test parsing valid event file."""
        event_data = {
            "pull_request": {
                "head": {"ref": "feature"},
                "base": {"ref": "main"},
                "number": 123,
            },
            "repository": {"name": "test-repo", "full_name": "user/test-repo"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                result = parse_github_event(f.name)
                assert result is not None
                assert result["pull_request"]["number"] == 123
                assert result["repository"]["name"] == "test-repo"
            finally:
                Path(f.name).unlink()

    def test_parse_github_event_invalid_json(self):
        """Test parsing invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()

            try:
                result = parse_github_event(f.name)
                assert result is None
            finally:
                Path(f.name).unlink()


class TestGetFileExtensions:
    """Test get_file_extensions function."""

    def test_get_file_extensions_empty(self):
        """Test getting extensions from empty list."""
        result = get_file_extensions([])
        assert result == []

    def test_get_file_extensions_with_extensions(self):
        """Test getting extensions from file list."""
        files = ["test.py", "module.js", "data.txt", "config.json"]
        result = get_file_extensions(files)
        assert "py" in result
        assert "js" in result
        assert "txt" in result
        assert "json" in result

    def test_get_file_extensions_no_extensions(self):
        """Test getting extensions from files without extensions."""
        files = ["README", "Makefile", "LICENSE"]
        result = get_file_extensions(files)
        assert result == []

    def test_get_file_extensions_duplicates(self):
        """Test getting extensions with duplicates."""
        files = ["test.py", "another.py", "module.js", "another.js"]
        result = get_file_extensions(files)
        assert len(result) == 2  # Should be unique
        assert "py" in result
        assert "js" in result


class TestGetBaseHeadFromEvent:
    """Test _get_base_head_from_event function."""

    def test_get_base_head_nonexistent_file(self):
        """Test getting base/head from nonexistent file."""
        result = _get_base_head_from_event("nonexistent.json")
        assert result is None

    def test_get_base_head_valid_pull_request(self):
        """Test getting base/head from valid pull request event."""
        event_data = {
            "pull_request": {"head": {"ref": "feature-branch"}, "base": {"ref": "main"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                result = _get_base_head_from_event(f.name)
                assert result == ("main", "feature-branch")
            finally:
                Path(f.name).unlink()

    def test_get_base_head_push_event(self):
        """Test getting base/head from push event."""
        event_data = {
            "ref": "refs/heads/main",
            "before": "old-commit",
            "after": "new-commit",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                result = _get_base_head_from_event(f.name)
                assert result == ("old-commit", "new-commit")
            finally:
                Path(f.name).unlink()

    def test_get_base_head_invalid_event(self):
        """Test getting base/head from invalid event."""
        event_data = {"some": "other", "data": "here"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                result = _get_base_head_from_event(f.name)
                assert result is None
            finally:
                Path(f.name).unlink()


class TestChangedPythonFiles:
    """Test changed_python_files function."""

    def test_changed_python_files_no_event(self):
        """Test getting changed files without event."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "+++ b/test.py\n--- a/test.py"

            result = changed_python_files()
            assert isinstance(result, list)

    def test_changed_python_files_with_event(self):
        """Test getting changed files with event."""
        event_data = {
            "pull_request": {"head": {"ref": "feature"}, "base": {"ref": "main"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "+++ b/test.py\n--- a/test.py"

                    result = changed_python_files(f.name)
                    assert isinstance(result, list)
            finally:
                Path(f.name).unlink()

    def test_changed_python_files_with_list(self):
        """Test getting changed files with file list."""
        files = ["test1.py", "test2.py", "test3.js"]
        result = changed_python_files(files)
        assert result == ["test1.py", "test2.py"]

    def test_changed_python_files_git_error(self):
        """Test handling git command error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "git error"

            result = changed_python_files()
            assert result == []


class TestDiffParser:
    """Test DiffParser class."""

    def test_diff_parser_init(self):
        """Test DiffParser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_parse_changed_files(self):
        """Test parsing changed files."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = parser.parse_changed_files()
            assert result == ["test.py"]
            mock_func.assert_called_once_with(None)

    def test_parse_changed_files_with_event(self):
        """Test parsing changed files with event."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = parser.parse_changed_files("event.json")
            assert result == ["test.py"]
            mock_func.assert_called_once_with("event.json")

    def test_parse_github_event(self):
        """Test parsing GitHub event."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.parse_github_event", return_value={"test": "data"}
        ) as mock_func:
            result = parser.parse_github_event("event.json")
            assert result == {"test": "data"}
            mock_func.assert_called_once_with("event.json")

    def test_get_file_extensions(self):
        """Test getting file extensions."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.get_file_extensions", return_value=["py", "js"]
        ) as mock_func:
            result = parser.get_file_extensions(["test.py", "test.js"])
            assert result == ["py", "js"]
            mock_func.assert_called_once_with(["test.py", "test.js"])

    def test_filter_python_files(self):
        """Test filtering Python files."""
        parser = DiffParser()

        with patch(
            "src.ai_guard.diff_parser.filter_python_files", return_value=["test.py"]
        ) as mock_func:
            result = parser.filter_python_files(["test.py", "test.js"])
            assert result == ["test.py"]
            mock_func.assert_called_once_with(["test.py", "test.js"])


class TestParseDiff:
    """Test parse_diff function."""

    def test_parse_diff_none(self):
        """Test parsing diff with None content."""
        result = parse_diff(None)
        assert result == []

    def test_parse_diff_empty(self):
        """Test parsing diff with empty content."""
        result = parse_diff("")
        assert result == []

    def test_parse_diff_valid(self):
        """Test parsing diff with valid content."""
        diff_content = """--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old
+new
"""
        result = parse_diff(diff_content)
        assert isinstance(result, list)

    def test_parse_diff_multiple_files(self):
        """Test parsing diff with multiple files."""
        diff_content = """--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-change1
+change1_new

--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-change2
+change2_new
"""
        result = parse_diff(diff_content)
        assert isinstance(result, list)


class TestGetChangedFiles:
    """Test get_changed_files function."""

    def test_get_changed_files_no_event(self):
        """Test getting changed files without event."""
        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = get_changed_files()
            assert result == ["test.py"]
            mock_func.assert_called_once_with(None)

    def test_get_changed_files_with_event(self):
        """Test getting changed files with event."""
        with patch(
            "src.ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ) as mock_func:
            result = get_changed_files("event.json")
            assert result == ["test.py"]
            mock_func.assert_called_once_with("event.json")


class TestDiffParserIntegration:
    """Integration tests for DiffParser."""

    def test_full_workflow(self):
        """Test full workflow from event to file list."""
        # Create a mock event file
        event_data = {
            "pull_request": {"head": {"ref": "feature"}, "base": {"ref": "main"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                parser = DiffParser()

                # Mock the git command
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "+++ b/test.py\n--- a/test.py"

                    # Test the full workflow
                    changed_files = parser.parse_changed_files(f.name)
                    assert isinstance(changed_files, list)

                    # Test filtering
                    python_files = parser.filter_python_files(changed_files)
                    assert isinstance(python_files, list)

                    # Test getting extensions
                    extensions = parser.get_file_extensions(python_files)
                    assert isinstance(extensions, list)

            finally:
                Path(f.name).unlink()

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        parser = DiffParser()

        # Test with invalid event file
        with patch("src.ai_guard.diff_parser.changed_python_files", return_value=[]):
            result = parser.parse_changed_files("nonexistent.json")
            assert result == []

        # Test with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            f.flush()

            try:
                result = parser.parse_github_event(f.name)
                assert result is None
            finally:
                Path(f.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
