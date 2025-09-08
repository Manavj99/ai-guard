"""Simple tests for diff_parser.py to achieve maximum coverage."""

import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from ai_guard.diff_parser import (
    get_file_extensions,
    filter_python_files,
    parse_diff_output,
    changed_python_files,
    _git_ls_files,
    _git_changed_files,
    parse_github_event,
    _get_base_head_from_event,
    DiffParser,
    parse_diff,
    get_changed_files,
)


class TestFileExtensions:
    """Test file extension extraction functions."""

    def test_get_file_extensions_basic(self):
        """Test basic file extension extraction."""
        file_paths = ["test.py", "script.js", "style.css", "README.md"]
        extensions = get_file_extensions(file_paths)
        assert extensions == ["css", "js", "md", "py"]

    def test_get_file_extensions_no_extensions(self):
        """Test file paths without extensions."""
        file_paths = ["README", "Makefile", "Dockerfile"]
        extensions = get_file_extensions(file_paths)
        assert extensions == []

    def test_get_file_extensions_multiple_dots(self):
        """Test file paths with multiple dots."""
        file_paths = ["test.min.js", "config.prod.json", "backup.old.py"]
        extensions = get_file_extensions(file_paths)
        assert extensions == ["js", "json", "py"]

    def test_get_file_extensions_empty_list(self):
        """Test with empty file list."""
        extensions = get_file_extensions([])
        assert extensions == []

    def test_get_file_extensions_non_alphanumeric(self):
        """Test file paths with non-alphanumeric extensions."""
        file_paths = ["test.py~", "script.js.bak", "style.css.tmp"]
        extensions = get_file_extensions(file_paths)
        assert extensions == ["py", "js", "css"]  # Only alphanumeric extensions

    def test_get_file_extensions_case_insensitive(self):
        """Test that extensions are converted to lowercase."""
        file_paths = ["test.PY", "script.JS", "style.CSS"]
        extensions = get_file_extensions(file_paths)
        assert extensions == ["css", "js", "py"]

    def test_get_file_extensions_duplicates(self):
        """Test that duplicate extensions are removed."""
        file_paths = ["test1.py", "test2.py", "script1.js", "script2.js"]
        extensions = get_file_extensions(file_paths)
        assert extensions == ["js", "py"]

    def test_get_file_extensions_single_dot(self):
        """Test file paths with single dot (no extension)."""
        file_paths = ["test.", ".hidden", "file."]
        extensions = get_file_extensions(file_paths)
        assert extensions == []


class TestPythonFileFiltering:
    """Test Python file filtering functions."""

    def test_filter_python_files_basic(self):
        """Test basic Python file filtering."""
        file_paths = ["test.py", "script.js", "style.css", "module.py"]
        python_files = filter_python_files(file_paths)
        assert python_files == ["test.py", "module.py"]

    def test_filter_python_files_no_python(self):
        """Test filtering when no Python files exist."""
        file_paths = ["script.js", "style.css", "README.md"]
        python_files = filter_python_files(file_paths)
        assert python_files == []

    def test_filter_python_files_all_python(self):
        """Test filtering when all files are Python."""
        file_paths = ["test.py", "module.py", "script.py"]
        python_files = filter_python_files(file_paths)
        assert python_files == ["test.py", "module.py", "script.py"]

    def test_filter_python_files_empty_list(self):
        """Test filtering with empty list."""
        python_files = filter_python_files([])
        assert python_files == []

    def test_filter_python_files_case_sensitive(self):
        """Test that filtering is case sensitive."""
        file_paths = ["test.py", "script.PY", "module.Py"]
        python_files = filter_python_files(file_paths)
        assert python_files == ["test.py"]


class TestDiffParsing:
    """Test diff output parsing functions."""

    def test_parse_diff_output_basic(self):
        """Test basic diff output parsing."""
        diff_output = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
diff --git a/script.js b/script.js
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/script.js
@@ -0,0 +1,3 @@
+console.log("Hello");
+console.log("World");
"""
        files = parse_diff_output(diff_output)
        assert "test.py" in files
        assert "script.js" in files

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        files = parse_diff_output("")
        assert files == []

    def test_parse_diff_output_no_files(self):
        """Test parsing diff output with no file changes."""
        diff_output = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello")
+    print("Hi")
"""
        files = parse_diff_output(diff_output)
        assert files == []

    def test_parse_diff_output_renamed_files(self):
        """Test parsing diff output with renamed files."""
        diff_output = """diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
"""
        files = parse_diff_output(diff_output)
        assert "new_name.py" in files

    def test_parse_diff_output_deleted_files(self):
        """Test parsing diff output with deleted files."""
        diff_output = """diff --git a/deleted.py b/deleted.py
deleted file mode 100644
index 1234567..0000000
--- a/deleted.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def hello():
-    print("Hello")
-    return True
"""
        files = parse_diff_output(diff_output)
        assert "deleted.py" in files

    def test_parse_diff_output_binary_files(self):
        """Test parsing diff output with binary files."""
        diff_output = """diff --git a/image.png b/image.png
index 1234567..abcdefg 100644
Binary files a/image.png and b/image.png differ
"""
        files = parse_diff_output(diff_output)
        assert "image.png" in files


class TestGitFunctions:
    """Test git-related functions."""

    def test_git_ls_files_success(self):
        """Test successful git ls-files execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="file1.py\nfile2.js\nfile3.py\n"
            )

            files = _git_ls_files()
            assert files == ["file1.py", "file2.js", "file3.py"]

    def test_git_ls_files_failure(self):
        """Test git ls-files failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="fatal: not a git repository"
            )

            files = _git_ls_files()
            assert files == []

    def test_git_ls_files_exception(self):
        """Test git ls-files with exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            files = _git_ls_files()
            assert files == []

    def test_git_changed_files_success(self):
        """Test successful git diff execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="diff --git a/test.py b/test.py\nindex 123..456 100644\n--- a/test.py\n+++ b/test.py\n@@ -1,0 +1,1 @@\n+print('hello')",
            )

            files = _git_changed_files("abc123", "def456")
            assert "test.py" in files

    def test_git_changed_files_failure(self):
        """Test git diff failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="fatal: bad object"
            )

            files = _git_changed_files("abc123", "def456")
            assert files == []

    def test_git_changed_files_exception(self):
        """Test git diff with exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            files = _git_changed_files("abc123", "def456")
            assert files == []


class TestGitHubEventParsing:
    """Test GitHub event parsing functions."""

    def test_parse_github_event_push(self):
        """Test parsing push event."""
        event_data = {
            "ref": "refs/heads/main",
            "commits": [
                {
                    "added": ["new_file.py"],
                    "modified": ["existing.py"],
                    "removed": ["deleted.py"],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                files = parse_github_event(f.name)
                assert "new_file.py" in files
                assert "existing.py" in files
                assert "deleted.py" in files
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)

    def test_parse_github_event_pull_request(self):
        """Test parsing pull request event."""
        event_data = {
            "pull_request": {"head": {"sha": "abc123"}, "base": {"sha": "def456"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                with patch(
                    "ai_guard.diff_parser._git_changed_files", return_value=["test.py"]
                ):
                    files = parse_github_event(f.name)
                    assert "test.py" in files
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)

    def test_parse_github_event_workflow_run(self):
        """Test parsing workflow run event."""
        event_data = {
            "workflow_run": {"head_sha": "abc123", "head_branch": "feature-branch"}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                with patch(
                    "ai_guard.diff_parser._git_changed_files", return_value=["test.py"]
                ):
                    files = parse_github_event(f.name)
                    assert "test.py" in files
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)

    def test_parse_github_event_unknown_type(self):
        """Test parsing unknown event type."""
        event_data = {"unknown_event": {"data": "test"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                files = parse_github_event(f.name)
                assert files == []
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)

    def test_parse_github_event_file_not_found(self):
        """Test parsing non-existent event file."""
        files = parse_github_event("nonexistent.json")
        assert files == []

    def test_parse_github_event_invalid_json(self):
        """Test parsing invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()

            try:
                files = parse_github_event(f.name)
                assert files == []
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)


class TestGetBaseHeadFromEvent:
    """Test _get_base_head_from_event function."""

    def test_get_base_head_from_event_pull_request(self):
        """Test getting base and head from pull request event."""
        event_data = {
            "pull_request": {"head": {"sha": "abc123"}, "base": {"sha": "def456"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                result = _get_base_head_from_event(f.name)
                assert result == ("def456", "abc123")
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)

    def test_get_base_head_from_event_workflow_run(self):
        """Test getting base and head from workflow run event."""
        event_data = {
            "workflow_run": {"head_sha": "abc123", "head_branch": "feature-branch"}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                with patch(
                    "ai_guard.diff_parser._git_ls_files", return_value=["test.py"]
                ):
                    result = _get_base_head_from_event(f.name)
                    assert result == ("main", "abc123")
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)

    def test_get_base_head_from_event_no_match(self):
        """Test getting base and head from event with no matching type."""
        event_data = {"unknown": "data"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(event_data, f)
            f.flush()

            try:
                result = _get_base_head_from_event(f.name)
                assert result is None
            finally:
                if Path(f.name).exists():
                    Path(f.name).unlink(missing_ok=True)


class TestDiffParserClass:
    """Test DiffParser class."""

    def test_diff_parser_init(self):
        """Test DiffParser initialization."""
        parser = DiffParser()
        assert parser is not None

    def test_diff_parser_parse_changed_files(self):
        """Test DiffParser parse_changed_files method."""
        parser = DiffParser()

        with patch(
            "ai_guard.diff_parser.changed_python_files", return_value=["test.py"]
        ):
            result = parser.parse_changed_files()
            assert result == ["test.py"]

    def test_diff_parser_parse_github_event(self):
        """Test DiffParser parse_github_event method."""
        parser = DiffParser()

        with patch("ai_guard.diff_parser.parse_github_event", return_value=["test.py"]):
            result = parser.parse_github_event("event.json")
            assert result == ["test.py"]


class TestUtilityFunctions:
    """Test utility functions."""

    def test_parse_diff_basic(self):
        """Test parse_diff function."""
        diff_content = """diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1,0 +1,1 @@
+print('hello')
"""
        files = parse_diff(diff_content)
        assert "test.py" in files

    def test_parse_diff_empty(self):
        """Test parse_diff with empty content."""
        files = parse_diff("")
        assert files == []

    def test_get_changed_files_with_event(self):
        """Test get_changed_files with event path."""
        with patch("ai_guard.diff_parser.parse_github_event", return_value=["test.py"]):
            files = get_changed_files("event.json")
            assert files == ["test.py"]

    def test_get_changed_files_without_event(self):
        """Test get_changed_files without event path."""
        with patch(
            "ai_guard.diff_parser._git_ls_files", return_value=["test.py", "script.js"]
        ):
            files = get_changed_files()
            assert files == ["test.py", "script.js"]

    def test_changed_python_files_with_event(self):
        """Test changed_python_files with event path."""
        with patch(
            "ai_guard.diff_parser.parse_github_event",
            return_value=["test.py", "script.js"],
        ):
            files = changed_python_files("event.json")
            assert files == ["test.py"]

    def test_changed_python_files_without_event(self):
        """Test changed_python_files without event path."""
        with patch(
            "ai_guard.diff_parser._git_ls_files",
            return_value=["test.py", "script.js", "module.py"],
        ):
            files = changed_python_files()
            assert files == ["test.py", "module.py"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
