"""Comprehensive tests for diff_parser.py module to achieve high coverage."""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
import json
import subprocess
from pathlib import Path

from src.ai_guard.diff_parser import (
    get_file_extensions,
    filter_python_files,
    parse_diff_output,
    changed_python_files,
    get_changed_files,
    parse_github_event,
    _get_base_head_from_event,
    _git_ls_files,
    _git_changed_files,
    DiffParser,
    parse_diff
)


class TestDiffParserComprehensive(unittest.TestCase):
    """Comprehensive tests for diff_parser module."""

    def test_get_file_extensions_basic(self):
        """Test getting file extensions from basic file paths."""
        file_paths = [
            "src/main.py",
            "tests/test.py",
            "README.md",
            "config.json",
            "setup.cfg"
        ]
        
        extensions = get_file_extensions(file_paths)
        expected = ["cfg", "json", "md", "py"]
        self.assertEqual(extensions, expected)

    def test_get_file_extensions_no_extensions(self):
        """Test getting file extensions when files have no extensions."""
        file_paths = [
            "README",
            "Makefile",
            "Dockerfile",
            "LICENSE"
        ]
        
        extensions = get_file_extensions(file_paths)
        self.assertEqual(extensions, [])

    def test_get_file_extensions_mixed(self):
        """Test getting file extensions from mixed file types."""
        file_paths = [
            "src/main.py",
            "README",
            "config.json",
            "tests/test.py",
            "docs/index.html",
            "scripts/build.sh"
        ]
        
        extensions = get_file_extensions(file_paths)
        expected = ["html", "json", "py", "sh"]
        self.assertEqual(extensions, expected)

    def test_get_file_extensions_empty_list(self):
        """Test getting file extensions from empty list."""
        extensions = get_file_extensions([])
        self.assertEqual(extensions, [])

    def test_get_file_extensions_special_chars(self):
        """Test getting file extensions with special characters."""
        file_paths = [
            "file.with.dots.py",
            "file-with-dashes.js",
            "file_with_underscores.ts",
            "file with spaces.txt"
        ]
        
        extensions = get_file_extensions(file_paths)
        expected = ["js", "py", "ts", "txt"]
        self.assertEqual(extensions, expected)

    def test_filter_python_files_basic(self):
        """Test filtering Python files from mixed file types."""
        file_paths = [
            "src/main.py",
            "tests/test.py",
            "README.md",
            "config.json",
            "scripts/run.py"
        ]
        
        python_files = filter_python_files(file_paths)
        expected = ["src/main.py", "tests/test.py", "scripts/run.py"]
        self.assertEqual(python_files, expected)

    def test_filter_python_files_no_python(self):
        """Test filtering when no Python files are present."""
        file_paths = [
            "README.md",
            "config.json",
            "setup.cfg"
        ]
        
        python_files = filter_python_files(file_paths)
        self.assertEqual(python_files, [])

    def test_filter_python_files_empty_list(self):
        """Test filtering from empty list."""
        python_files = filter_python_files([])
        self.assertEqual(python_files, [])

    def test_parse_diff_output_basic(self):
        """Test parsing basic git diff output."""
        diff_output = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
     print("Hello")
+    print("World")
 
diff --git a/tests/test.py b/tests/test.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/tests/test.py
@@ -0,0 +1,3 @@
+def test_main():
+    assert True
+"""
        
        files = parse_diff_output(diff_output)
        expected = ["src/main.py", "tests/test.py"]
        self.assertEqual(files, expected)

    def test_parse_diff_output_no_files(self):
        """Test parsing diff output with no file changes."""
        diff_output = "No changes found"
        files = parse_diff_output(diff_output)
        self.assertEqual(files, [])

    def test_parse_diff_output_empty(self):
        """Test parsing empty diff output."""
        files = parse_diff_output("")
        self.assertEqual(files, [])

    def test_parse_diff_output_renamed_files(self):
        """Test parsing diff output with renamed files."""
        diff_output = """diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
--- a/old_name.py
+++ b/new_name.py
"""
        files = parse_diff_output(diff_output)
        expected = ["old_name.py", "new_name.py"]
        self.assertEqual(files, expected)

    @patch('subprocess.check_output')
    def test_git_ls_files_basic(self, mock_check_output):
        """Test getting tracked files from git."""
        mock_check_output.return_value = "src/main.py\ntests/test.py\nREADME.md"
        
        files = _git_ls_files()
        self.assertEqual(files, ["src/main.py", "tests/test.py", "README.md"])

    @patch('subprocess.check_output')
    def test_git_ls_files_error(self, mock_check_output):
        """Test getting tracked files when git fails."""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")
        
        files = _git_ls_files()
        self.assertEqual(files, [])

    @patch('subprocess.check_call')
    @patch('subprocess.check_output')
    def test_git_changed_files_basic(self, mock_check_output, mock_check_call):
        """Test getting changed files between refs."""
        mock_check_output.return_value = "src/main.py\ntests/test.py"
        
        files = _git_changed_files("base_ref", "head_ref")
        self.assertEqual(files, ["src/main.py", "tests/test.py"])

    @patch('subprocess.check_call')
    def test_git_changed_files_error(self, mock_check_call):
        """Test getting changed files when git fails."""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "git")
        
        files = _git_changed_files("base_ref", "head_ref")
        self.assertEqual(files, [])

    def test_parse_github_event_basic(self):
        """Test parsing basic GitHub event JSON."""
        event_data = {
            "pull_request": {
                "head": {
                    "sha": "abc123"
                },
                "base": {
                    "sha": "def456"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            result = parse_github_event(event_file)
            self.assertEqual(result, event_data)
        finally:
            os.unlink(event_file)

    def test_parse_github_event_file_not_found(self):
        """Test parsing GitHub event from non-existent file."""
        result = parse_github_event("nonexistent.json")
        self.assertEqual(result, {})

    def test_parse_github_event_invalid_json(self):
        """Test parsing GitHub event from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            event_file = f.name
        
        try:
            result = parse_github_event(event_file)
            self.assertEqual(result, {})
        finally:
            os.unlink(event_file)

    def test_get_base_head_from_event_pull_request(self):
        """Test extracting base/head from pull request event."""
        event_data = {
            "pull_request": {
                "head": {"sha": "abc123"},
                "base": {"sha": "def456"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            result = _get_base_head_from_event(event_file)
            self.assertEqual(result, ("def456", "abc123"))
        finally:
            os.unlink(event_file)

    def test_get_base_head_from_event_push(self):
        """Test extracting base/head from push event."""
        event_data = {
            "before": "abc123",
            "after": "def456"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            result = _get_base_head_from_event(event_file)
            self.assertEqual(result, ("abc123", "def456"))
        finally:
            os.unlink(event_file)

    def test_get_base_head_from_event_workflow_dispatch(self):
        """Test extracting base/head from workflow dispatch event."""
        event_data = {
            "event_name": "workflow_dispatch"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            result = _get_base_head_from_event(event_file)
            self.assertIsNone(result)
        finally:
            os.unlink(event_file)

    def test_get_base_head_from_event_invalid(self):
        """Test extracting base/head from invalid event."""
        event_data = {"invalid": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            result = _get_base_head_from_event(event_file)
            self.assertIsNone(result)
        finally:
            os.unlink(event_file)

    def test_changed_python_files_with_event(self):
        """Test getting changed Python files with event."""
        event_data = {
            "pull_request": {
                "head": {"sha": "abc123"},
                "base": {"sha": "def456"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            with patch('src.ai_guard.diff_parser._git_changed_files') as mock_git_changed:
                mock_git_changed.return_value = ["src/main.py", "tests/test.py", "README.md"]
                
                files = changed_python_files(event_file)
                self.assertEqual(files, ["src/main.py", "tests/test.py"])
        finally:
            os.unlink(event_file)

    def test_changed_python_files_without_event(self):
        """Test getting changed Python files without event."""
        with patch('src.ai_guard.diff_parser._git_ls_files') as mock_git_ls:
            mock_git_ls.return_value = ["src/main.py", "tests/test.py", "README.md"]
            
            files = changed_python_files()
            self.assertEqual(files, ["src/main.py", "tests/test.py"])

    def test_changed_python_files_error(self):
        """Test getting changed Python files when git operations fail."""
        with patch('src.ai_guard.diff_parser._git_ls_files') as mock_git_ls:
            mock_git_ls.side_effect = Exception("Git error")
            
            files = changed_python_files()
            self.assertEqual(files, [])

    def test_get_changed_files_basic(self):
        """Test getting changed files."""
        with patch('src.ai_guard.diff_parser.changed_python_files') as mock_changed:
            mock_changed.return_value = ["src/main.py", "tests/test.py"]
            
            files = get_changed_files()
            self.assertEqual(files, ["src/main.py", "tests/test.py"])

    def test_parse_diff_basic(self):
        """Test parsing diff content."""
        diff_content = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
     print("Hello")
+    print("World")
"""
        
        files = parse_diff(diff_content)
        self.assertEqual(files, ["src/main.py"])

    def test_diff_parser_init(self):
        """Test DiffParser initialization."""
        parser = DiffParser()
        self.assertIsInstance(parser, DiffParser)

    def test_diff_parser_parse_changed_files(self):
        """Test DiffParser parse_changed_files method."""
        parser = DiffParser()
        
        with patch('src.ai_guard.diff_parser.changed_python_files') as mock_changed:
            mock_changed.return_value = ["src/main.py", "tests/test.py"]
            
            files = parser.parse_changed_files()
            self.assertEqual(files, ["src/main.py", "tests/test.py"])

    def test_diff_parser_parse_github_event(self):
        """Test DiffParser parse_github_event method."""
        parser = DiffParser()
        
        event_data = {"test": "data"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(event_data, f)
            event_file = f.name
        
        try:
            result = parser.parse_github_event(event_file)
            self.assertEqual(result, event_data)
        finally:
            os.unlink(event_file)

    def test_diff_parser_get_file_extensions(self):
        """Test DiffParser get_file_extensions method."""
        parser = DiffParser()
        
        file_paths = ["src/main.py", "tests/test.py", "README.md"]
        extensions = parser.get_file_extensions(file_paths)
        expected = ["md", "py"]
        self.assertEqual(extensions, expected)

    def test_diff_parser_filter_python_files(self):
        """Test DiffParser filter_python_files method."""
        parser = DiffParser()
        
        file_paths = ["src/main.py", "tests/test.py", "README.md"]
        python_files = parser.filter_python_files(file_paths)
        expected = ["src/main.py", "tests/test.py"]
        self.assertEqual(python_files, expected)


if __name__ == '__main__':
    unittest.main()
