"""Working comprehensive tests for the diff_parser module."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

from ai_guard.diff_parser import (
    changed_python_files,
    parse_diff_output,
    get_file_extensions,
    filter_python_files,
    parse_github_event,
    _git_ls_files,
    _git_changed_files,
    _get_base_head_from_event,
)


class TestDiffParserWorking:
    """Working comprehensive tests for diff parser functionality."""

    def test_get_file_extensions(self):
        """Test get_file_extensions function."""
        file_paths = ["src/test.py", "src/helper.js", "README.md", "src/utils.ts"]
        extensions = get_file_extensions(file_paths)

        assert extensions == [".py", ".js", ".md", ".ts"]

    def test_get_file_extensions_no_extension(self):
        """Test get_file_extensions with files without extensions."""
        file_paths = ["README", "Makefile", "Dockerfile"]
        extensions = get_file_extensions(file_paths)

        assert extensions == ["", "", ""]

    def test_filter_python_files(self):
        """Test filter_python_files function."""
        file_paths = ["src/test.py", "src/helper.js", "README.md", "src/utils.py"]
        python_files = filter_python_files(file_paths)

        assert python_files == ["src/test.py", "src/utils.py"]

    def test_filter_python_files_no_python(self):
        """Test filter_python_files with no Python files."""
        file_paths = ["src/helper.js", "README.md", "src/utils.ts"]
        python_files = filter_python_files(file_paths)

        assert python_files == []

    def test_parse_diff_output(self):
        """Test parse_diff_output function."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
"""

        changed_files = parse_diff_output(diff_output)

        assert "src/test.py" in changed_files

    def test_parse_diff_output_multiple_files(self):
        """Test parse_diff_output with multiple files."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")

diff --git a/src/helper.py b/src/helper.py
index 1234567..abcdefg 100644
--- a/src/helper.py
+++ b/src/helper.py
@@ -1,3 +1,4 @@
 def helper():
     return True
+    return False
"""

        changed_files = parse_diff_output(diff_output)

        assert "src/test.py" in changed_files
        assert "src/helper.py" in changed_files
        assert len(changed_files) == 2

    def test_parse_diff_output_no_files(self):
        """Test parse_diff_output with no files."""
        diff_output = """Some other output without diff headers"""

        changed_files = parse_diff_output(diff_output)

        assert changed_files == []

    @patch("ai_guard.diff_parser.subprocess.run")
    def test_git_ls_files(self, mock_run):
        """Test _git_ls_files function."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/test.py\nsrc/helper.py\nREADME.md\n"
        )

        files = _git_ls_files()

        assert files == ["src/test.py", "src/helper.py", "README.md"]

    @patch("ai_guard.diff_parser.subprocess.run")
    def test_git_changed_files(self, mock_run):
        """Test _git_changed_files function."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/test.py\nsrc/helper.py\n"
        )

        files = _git_changed_files("main", "feature")

        assert files == ["src/test.py", "src/helper.py"]

    def test_parse_github_event(self):
        """Test parse_github_event function."""
        event_data = {
            "pull_request": {"base": {"ref": "main"}, "head": {"ref": "feature"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            import json

            json.dump(event_data, f)
            event_path = f.name

        try:
            result = parse_github_event(event_path)
            assert result["base_ref"] == "main"
            assert result["head_ref"] == "feature"
        finally:
            os.unlink(event_path)

    def test_parse_github_event_invalid_file(self):
        """Test parse_github_event with invalid file."""
        with pytest.raises(Exception):
            parse_github_event("nonexistent.json")

    def test_get_base_head_from_event(self):
        """Test _get_base_head_from_event function."""
        event_data = {
            "pull_request": {"base": {"ref": "main"}, "head": {"ref": "feature"}}
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            import json

            json.dump(event_data, f)
            event_path = f.name

        try:
            result = _get_base_head_from_event(event_path)
            assert result == ("main", "feature")
        finally:
            os.unlink(event_path)

    def test_get_base_head_from_event_no_pr(self):
        """Test _get_base_head_from_event with no pull request."""
        event_data = {"some_other_event": True}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            import json

            json.dump(event_data, f)
            event_path = f.name

        try:
            result = _get_base_head_from_event(event_path)
            assert result is None
        finally:
            os.unlink(event_path)

    @patch("ai_guard.diff_parser._git_ls_files")
    def test_changed_python_files_no_event(self, mock_ls_files):
        """Test changed_python_files with no event file."""
        mock_ls_files.return_value = ["src/test.py", "src/helper.js", "README.md"]

        files = changed_python_files()

        assert files == ["src/test.py"]

    @patch("ai_guard.diff_parser._git_changed_files")
    def test_changed_python_files_with_event(self, mock_changed_files):
        """Test changed_python_files with event file."""
        mock_changed_files.return_value = ["src/test.py", "src/helper.js", "README.md"]

        files = changed_python_files("event.json")

        assert files == ["src/test.py"]

    @patch("ai_guard.diff_parser._git_ls_files")
    def test_changed_python_files_no_python(self, mock_ls_files):
        """Test changed_python_files with no Python files."""
        mock_ls_files.return_value = ["src/helper.js", "README.md", "src/utils.ts"]

        files = changed_python_files()

        assert files == []
