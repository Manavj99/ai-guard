"""Parse changed files from Git diffs or GitHub events."""

import json
from typing import List, Tuple, Dict, Any, Optional


def get_file_extensions(file_paths: Optional[List[str]]) -> List[str]:
    """Extract file extensions from a list of file paths.

    Args:
        file_paths: List of file paths

    Returns:
        List of unique file extensions (without the dot)
    """
    if file_paths is None:
        return []
    extensions = set()
    for file_path in file_paths:
        if "." in file_path:
            # Split by dot and get the last part
            parts = file_path.split(".")
            if len(parts) > 1:
                ext = parts[-1].lower()
                # Only add if extension is alphanumeric and not a backup/temp file
                if (
                    ext
                    and ext.isalnum()
                    and not ext.endswith(("~", "bak", "tmp", "temp"))
                ):
                    extensions.add(ext)
    return sorted(list(extensions))


def filter_python_files(file_paths: Optional[List[str]]) -> List[str]:
    """Filter a list of file paths to only include Python files.

    Args:
        file_paths: List of file paths

    Returns:
        List of Python file paths only
    """
    if file_paths is None:
        return []
    return [f for f in file_paths if f.endswith(".py")]


def parse_diff_output(diff_output: Optional[str]) -> List[str]:
    """Parse git diff output to extract changed file paths.

    Args:
        diff_output: Output from git diff command

    Returns:
        List of changed file paths
    """
    if diff_output is None:
        return []
    files = []
    lines = diff_output.split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            # Extract file path from diff output
            file_path = line[6:]  # Remove '+++ b/' or '--- a/' prefix
            if file_path not in files:
                files.append(file_path)

    return files


def changed_python_files(event_path: str | List[str] | None = None) -> List[str]:
    """Get list of changed Python files.

    Args:
        event_path: Path to GitHub event JSON file, or list of files to filter

    Returns:
        List of Python file paths that have changed
    """
    # If a list of files is provided, filter for Python files
    if isinstance(event_path, list):
        return [f for f in event_path if f and f.endswith(".py")]

    # If GitHub event is provided and has base/head, use precise diff
    if event_path is not None:
        try:
            base_head = _get_base_head_from_event(event_path)
            if base_head is not None:
                base, head = base_head
                files = _git_changed_files(base, head)
                if files:  # Only return diff if we successfully got files
                    return [p for p in files if p.endswith(".py")]
        except Exception as e:
            print(f"Warning: Error parsing GitHub event: {e}")

    # Fallback: all tracked Python files (including when event_path is None)
    try:
        return [p for p in _git_ls_files() if p.endswith(".py")]
    except Exception as e:
        print(f"Warning: Error getting tracked files: {e}")
        return []


def _git_ls_files() -> List[str]:
    """Get all tracked files from Git that still exist."""
    import subprocess
    import os

    try:
        out = subprocess.check_output(["git", "ls-files"], text=True)
        tracked_files = [line.strip() for line in out.splitlines() if line.strip()]
        # Filter out deleted files - only return files that still exist
        # Also filter out empty lines and whitespace-only lines
        existing_files = []
        for f in tracked_files:
            if f and os.path.exists(f):
                existing_files.append(f)
        return existing_files
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback if git is not available
        return []


def _git_changed_files(base_ref: str, head_ref: str) -> List[str]:
    """Get changed files between base and head refs.

    Uses `git diff --name-only base...head` to include merge-base.
    Only returns files that still exist (not deleted).
    """
    import subprocess
    import os

    try:
        # Validate that the refs exist in the repository
        subprocess.check_call(
            ["git", "rev-parse", "--verify", base_ref],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.check_call(
            ["git", "rev-parse", "--verify", head_ref],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Get the diff
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"], text=True
        )
        # Filter out deleted files - only return files that still exist
        changed_files = [line.strip() for line in out.splitlines() if line.strip()]
        return [f for f in changed_files if os.path.exists(f)]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If Git operations fail, return empty list instead of crashing
        print(f"Warning: Could not get diff between {base_ref} and {head_ref}")
        return []


def parse_github_event(event_path: str) -> Dict[str, Any]:
    """Parse GitHub event JSON file.

    Args:
        event_path: Path to the event JSON file

    Returns:
        Parsed event data
    """
    try:
        with open(event_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _get_base_head_from_event(event_path: str) -> Tuple[str, str] | None:
    """Extract base and head SHA or refs from a GitHub event file.

    Supports pull_request events.
    """
    event = parse_github_event(event_path)
    if not event:
        return None

    # Handle pull_request events
    pr = event.get("pull_request")
    if isinstance(pr, dict):
        base = pr.get("base", {})
        head = pr.get("head", {})
        if isinstance(base, dict) and isinstance(head, dict):
            base_sha = base.get("sha")
            head_sha = head.get("sha")
            if isinstance(base_sha, str) and isinstance(head_sha, str):
                return base_sha, head_sha

    # Handle push events
    if event.get("before") and event.get("after"):
        before_sha = event.get("before")
        after_sha = event.get("after")
        if isinstance(before_sha, str) and isinstance(after_sha, str):
            return before_sha, after_sha

    # Handle workflow_dispatch events (no specific commits)
    if event.get("event_name") == "workflow_dispatch":
        return None

    return None


class DiffParser:
    """Parser for Git diffs and GitHub events."""

    def __init__(self) -> None:
        """Initialize the diff parser."""

    def parse_changed_files(self, event_path: Optional[str] = None) -> List[str]:
        """Parse changed files from Git diffs or GitHub events.

        Args:
            event_path: Optional path to GitHub event JSON file

        Returns:
            List of changed file paths
        """
        return changed_python_files(event_path)

    def parse_github_event(self, event_path: str) -> Dict[str, Any]:
        """Parse GitHub event JSON file.

        Args:
            event_path: Path to the event JSON file

        Returns:
            Parsed event data
        """
        return parse_github_event(event_path)

    def get_file_extensions(self, file_paths: List[str]) -> List[str]:
        """Extract file extensions from a list of file paths.

        Args:
            file_paths: List of file paths

        Returns:
            List of unique file extensions (without the dot)
        """
        return get_file_extensions(file_paths)

    def filter_python_files(self, file_paths: List[str]) -> List[str]:
        """Filter a list of file paths to only include Python files.

        Args:
            file_paths: List of file paths

        Returns:
            List of Python file paths only
        """
        return filter_python_files(file_paths)


def parse_diff(diff_content: Optional[str]) -> List[str]:
    """Parse diff content to extract changed file paths.

    Args:
        diff_content: Raw diff content

    Returns:
        List of changed file paths
    """
    return parse_diff_output(diff_content)


def get_changed_files(event_path: Optional[str] = None) -> List[str]:
    """Get list of changed files.

    Args:
        event_path: Optional path to GitHub event JSON file

    Returns:
        List of changed file paths
    """
    return changed_python_files(event_path)
