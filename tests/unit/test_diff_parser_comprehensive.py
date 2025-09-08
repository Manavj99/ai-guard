"""Comprehensive tests for diff_parser module."""

from unittest.mock import patch, MagicMock

from ai_guard.diff_parser import (
    changed_python_files,
    parse_diff_output,
    filter_python_files,
)


class TestDiffParserComprehensive:
    """Comprehensive tests for diff parser functionality."""

    def test_changed_python_files_with_git_diff(self):
        """Test changed_python_files with git diff output."""
        git_diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
+    print("Hello, world!")
     return True

diff --git a/src/other.py b/src/other.py
index 1234567..abcdefg 100644
--- a/src/other.py
+++ b/src/other.py
@@ -1,2 +1,3 @@
 class Test:
+    def method(self):
     pass
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            files = changed_python_files()

            assert "src/test.py" in files
            assert "src/other.py" in files
            assert len(files) == 2

    def test_changed_python_files_git_error(self):
        """Test changed_python_files when git command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="fatal: not a git repository"
            )

            files = changed_python_files()

            assert files == []

    def test_changed_python_files_no_python_files(self):
        """Test changed_python_files with no Python files in diff."""
        git_diff_output = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Test
+New line
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            files = changed_python_files()

            assert files == []

    def test_changed_python_files_with_non_python_extensions(self):
        """Test changed_python_files with mixed file types."""
        git_diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True

diff --git a/src/test.js b/src/test.js
index 1234567..abcdefg 100644
--- a/src/test.js
+++ b/src/test.js
@@ -1,2 +1,3 @@
 function hello() {
+    console.log("Hello");
     return true;
 }
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            files = changed_python_files()

            assert "src/test.py" in files
            assert "src/test.js" not in files
            assert len(files) == 1

    def test_parse_unified_diff(self):
        """Test parsing unified diff format."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
+    print("Hello, world!")
     return True
"""

        file_paths = parse_diff_output(diff_output)

        assert "src/test.py" in file_paths
        assert len(file_paths) == 1

    def test_parse_unified_diff_multiple_files(self):
        """Test parsing unified diff with multiple files."""
        diff_output = """diff --git a/src/test1.py b/src/test1.py
index 1234567..abcdefg 100644
--- a/src/test1.py
+++ b/src/test1.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True

diff --git a/src/test2.py b/src/test2.py
index 1234567..abcdefg 100644
--- a/src/test2.py
+++ b/src/test2.py
@@ -1,2 +1,3 @@
 def world():
+    print("World")
     return False
"""

        file_paths = parse_diff_output(diff_output)

        assert "src/test1.py" in file_paths
        assert "src/test2.py" in file_paths
        assert len(file_paths) == 2

    def test_parse_unified_diff_empty(self):
        """Test parsing empty diff."""
        file_paths = parse_diff_output("")
        assert file_paths == []

    def test_parse_unified_diff_malformed(self):
        """Test parsing malformed diff."""
        malformed_diff = """not a proper diff
some random text
diff --git a/src/test.py b/src/test.py
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True
"""

        file_paths = parse_diff_output(malformed_diff)

        # Should still extract valid file paths
        assert "src/test.py" in file_paths

    def test_extract_file_paths(self):
        """Test extracting file paths from diff lines."""
        diff_lines = [
            "diff --git a/src/test.py b/src/test.py",
            "diff --git a/src/other.py b/src/other.py",
            "index 1234567..abcdefg 100644",
            "--- a/src/test.py",
            "+++ b/src/test.py",
        ]

        file_paths = parse_diff_output("\n".join(diff_lines))

        assert "src/test.py" in file_paths
        assert "src/other.py" in file_paths
        assert len(file_paths) == 2

    def test_extract_file_paths_no_diff_lines(self):
        """Test extracting file paths with no diff lines."""
        diff_lines = [
            "index 1234567..abcdefg 100644",
            "--- a/src/test.py",
            "+++ b/src/test.py",
        ]

        file_paths = parse_diff_output("\n".join(diff_lines))

        assert file_paths == []

    def test_is_python_file(self):
        """Test Python file detection."""
        assert "test.py" in filter_python_files(["test.py"])
        assert "test.pyi" in filter_python_files(["test.pyi"])
        assert "test.pyx" in filter_python_files(["test.pyx"])
        assert "test.pyw" in filter_python_files(["test.pyw"])
        assert "test.js" not in filter_python_files(["test.js"])
        assert "test.txt" not in filter_python_files(["test.txt"])
        assert "test" not in filter_python_files(["test"])
        assert "" not in filter_python_files([""])

    def test_is_python_file_with_paths(self):
        """Test Python file detection with full paths."""
        assert "src/test.py" in filter_python_files(["src/test.py"])
        assert "/path/to/test.py" in filter_python_files(["/path/to/test.py"])
        assert "src/test.js" not in filter_python_files(["src/test.js"])
        assert "src/test.py.bak" not in filter_python_files(["src/test.py.bak"])

    def test_get_file_changes(self):
        """Test getting file changes from diff."""
        diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,4 @@
 def hello():
+    print("Hello, world!")
     return True
"""

        changes = parse_diff_output(diff_output)

        assert "src/test.py" in changes
        assert changes["src/test.py"]["added_lines"] > 0
        assert changes["src/test.py"]["removed_lines"] >= 0

    def test_get_file_changes_multiple_files(self):
        """Test getting file changes for multiple files."""
        diff_output = """diff --git a/src/test1.py b/src/test1.py
index 1234567..abcdefg 100644
--- a/src/test1.py
+++ b/src/test1.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True

diff --git a/src/test2.py b/src/test2.py
index 1234567..abcdefg 100644
--- a/src/test2.py
+++ b/src/test2.py
@@ -1,2 +1,3 @@
 def world():
+    print("World")
     return False
"""

        changes = parse_diff_output(diff_output)

        assert "src/test1.py" in changes
        assert "src/test2.py" in changes
        assert len(changes) == 2

    def test_get_file_changes_empty(self):
        """Test getting file changes from empty diff."""
        changes = parse_diff_output("")
        assert changes == {}

    def test_changed_python_files_with_custom_git_command(self):
        """Test changed_python_files with custom git command."""
        git_diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            # Test with custom git command
            files = changed_python_files(git_command="git diff --cached")

            assert "src/test.py" in files
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "git diff --cached" in " ".join(call_args)

    def test_changed_python_files_with_working_directory(self):
        """Test changed_python_files with specific working directory."""
        git_diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            # Test with working directory
            files = changed_python_files(working_dir="/path/to/repo")

            assert "src/test.py" in files
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get("cwd") == "/path/to/repo"

    def test_changed_python_files_with_encoding_issues(self):
        """Test changed_python_files with encoding issues in diff."""
        git_diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello, 世界!")
     return True
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            files = changed_python_files()

            assert "src/test.py" in files
            assert len(files) == 1

    def test_changed_python_files_with_binary_files(self):
        """Test changed_python_files with binary files in diff."""
        git_diff_output = """diff --git a/src/test.py b/src/test.py
index 1234567..abcdefg 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,2 +1,3 @@
 def hello():
+    print("Hello")
     return True

diff --git a/binary_file.bin b/binary_file.bin
index 1234567..abcdefg 100644
Binary files a/binary_file.bin and b/binary_file.bin differ
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=git_diff_output, stderr=""
            )

            files = changed_python_files()

            assert "src/test.py" in files
            assert "binary_file.bin" not in files
            assert len(files) == 1
