"""Core tests for diff_parser module to improve coverage."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from src.ai_guard.diff_parser import (
    _git_ls_files, _git_changed_files, 
    changed_python_files, parse_diff
)


class TestGitLsFiles:
    """Test _git_ls_files function."""
    
    @patch('subprocess.check_output')
    def test_git_ls_files_success(self, mock_check_output):
        """Test _git_ls_files with successful git command."""
        mock_check_output.return_value = "file1.py\nfile2.py\nfile3.js\n"
        
        files = _git_ls_files()
        assert files == ["file1.py", "file2.py", "file3.js"]
        mock_check_output.assert_called_once_with(["git", "ls-files"], text=True)
    
    @patch('subprocess.check_output')
    def test_git_ls_files_empty(self, mock_check_output):
        """Test _git_ls_files with empty output."""
        mock_check_output.return_value = ""
        
        files = _git_ls_files()
        assert files == []
    
    @patch('subprocess.check_output')
    def test_git_ls_files_with_whitespace(self, mock_check_output):
        """Test _git_ls_files with whitespace in output."""
        mock_check_output.return_value = "file1.py\n  \nfile2.py\n\n"
        
        files = _git_ls_files()
        assert files == ["file1.py", "file2.py"]
    
    @patch('subprocess.check_output')
    def test_git_ls_files_git_error(self, mock_check_output):
        """Test _git_ls_files with git error."""
        mock_check_output.side_effect = FileNotFoundError("git not found")
        
        files = _git_ls_files()
        assert files == []


class TestGitChangedFiles:
    """Test _git_changed_files function."""
    
    @patch('subprocess.check_call')
    @patch('subprocess.check_output')
    def test_git_changed_files_success(self, mock_check_output, mock_check_call):
        """Test _git_changed_files with successful git commands."""
        mock_check_output.return_value = "file1.py\nfile2.py\n"
        
        files = _git_changed_files("main", "feature")
        assert files == ["file1.py", "file2.py"]
        
        # Verify git commands were called
        assert mock_check_call.call_count == 2  # Two rev-parse calls
        mock_check_output.assert_called_once()
    
    @patch('subprocess.check_call')
    @patch('subprocess.check_output')
    def test_git_changed_files_invalid_refs(self, mock_check_output, mock_check_call):
        """Test _git_changed_files with invalid refs."""
        mock_check_call.side_effect = FileNotFoundError("git not found")
        
        files = _git_changed_files("invalid", "ref")
        assert files == []
    
    @patch('subprocess.check_call')
    @patch('subprocess.check_output')
    def test_git_changed_files_no_changes(self, mock_check_output, mock_check_call):
        """Test _git_changed_files with no changes."""
        mock_check_output.return_value = ""
        
        files = _git_changed_files("main", "feature")
        assert files == []
    
    @patch('subprocess.check_call')
    @patch('subprocess.check_output')
    def test_git_changed_files_git_diff_error(self, mock_check_output, mock_check_call):
        """Test _git_changed_files with git diff error."""
        mock_check_output.side_effect = FileNotFoundError("git not found")
        
        files = _git_changed_files("main", "feature")
        assert files == []


class TestChangedPythonFiles:
    """Test changed_python_files function."""
    
    def test_changed_python_files_success(self):
        """Test changed_python_files with Python files."""
        with patch('src.ai_guard.diff_parser._git_changed_files') as mock_get_changed:
            mock_get_changed.return_value = [
                "src/file1.py",
                "src/file2.py", 
                "docs/readme.md",
                "tests/test_file.py"
            ]
            
            files = changed_python_files("main", "feature")
            assert files == ["src/file1.py", "src/file2.py", "tests/test_file.py"]
    
    def test_changed_python_files_no_python(self):
        """Test changed_python_files with no Python files."""
        with patch('src.ai_guard.diff_parser._git_changed_files') as mock_get_changed:
            mock_get_changed.return_value = [
                "docs/readme.md",
                "config.json",
                "Dockerfile"
            ]
            
            files = changed_python_files("main", "feature")
            assert files == []
    
    def test_changed_python_files_empty(self):
        """Test changed_python_files with no changes."""
        with patch('src.ai_guard.diff_parser._git_changed_files') as mock_get_changed:
            mock_get_changed.return_value = []
            
            files = changed_python_files("main", "feature")
            assert files == []
    
    def test_changed_python_files_error(self):
        """Test changed_python_files with error."""
        with patch('src.ai_guard.diff_parser._git_changed_files') as mock_get_changed:
            mock_get_changed.side_effect = Exception("Git error")
            
            files = changed_python_files("main", "feature")
            assert files == []


class TestParseDiff:
    """Test parse_diff function."""
    
    def test_parse_diff_empty(self):
        """Test parse_diff with empty diff."""
        result = parse_diff("")
        assert result == []
    
    def test_parse_diff_simple(self):
        """Test parse_diff with simple diff."""
        diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,3 @@
 def func():
-    return "old"
+    return "new"
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "file1.py"
    
    def test_parse_diff_multiple_files(self):
        """Test parse_diff with multiple files."""
        diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-old
+new

diff --git a/file2.py b/file2.py
index 1234567..abcdefg 100644
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-old2
+new2
"""
        result = parse_diff(diff)
        assert len(result) == 2
        assert "file1.py" in result
        assert "file2.py" in result
    
    def test_parse_diff_new_file(self):
        """Test parse_diff with new file."""
        diff = """diff --git a/newfile.py b/newfile.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/newfile.py
@@ -0,0 +1,3 @@
+def new_func():
+    return "new"
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "newfile.py"
    
    def test_parse_diff_deleted_file(self):
        """Test parse_diff with deleted file."""
        diff = """diff --git a/oldfile.py b/oldfile.py
deleted file mode 100644
index 1234567..0000000
--- a/oldfile.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_func():
-    return "old"
"""
        result = parse_diff(diff)
        assert len(result) == 1
        assert result[0] == "oldfile.py"
