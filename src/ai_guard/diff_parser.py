"""Parse changed files from Git diffs or GitHub events."""

import json
import re
import os
import hashlib
import time
from typing import List, Tuple, Dict, Any, Optional, Set, Union
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)


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


# Compiled regex patterns for better performance
DIFF_FILE_PATTERN = re.compile(r"^diff --git a/(.+) b/(.+)$")
HUNK_PATTERN = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
ADDED_LINE_PATTERN = re.compile(r"^\+")
REMOVED_LINE_PATTERN = re.compile(r"^-")
FILE_MODE_PATTERN = re.compile(r"^(new|deleted) file mode")
BINARY_FILE_PATTERN = re.compile(r"^Binary files")
INDEX_PATTERN = re.compile(r"^index [a-f0-9]+\.\.[a-f0-9]+")
SIMILARITY_PATTERN = re.compile(r"^similarity index (\d+)%")
RENAME_PATTERN = re.compile(r"^rename from (.+)$")
RENAME_TO_PATTERN = re.compile(r"^rename to (.+)$")

# Thread-local storage for thread safety
_thread_local = threading.local()

# Global cache for parsed diffs and file operations
_cache = {}
_cache_lock = threading.RLock()
_cache_stats = {"hits": 0, "misses": 0, "evictions": 0, "size": 0}

# Cache configuration
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 1000
CACHE_CLEANUP_INTERVAL = 60  # 1 minute


class ChangeType(Enum):
    """Enumeration for different types of file changes."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    BINARY = "binary"


@dataclass
class FileChange:
    """Represents a file change in a diff."""

    file_path: str
    change_type: ChangeType
    added_lines: int = 0
    removed_lines: int = 0
    similarity: Optional[int] = None
    old_path: Optional[str] = None
    is_binary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "change_type": self.change_type.value,
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
            "similarity": self.similarity,
            "old_path": self.old_path,
            "is_binary": self.is_binary,
        }


@dataclass
class LineChange:
    """Represents a line change in a diff."""

    line_number: int
    change_type: str
    content: str
    file_path: str
    hunk_start: Optional[int] = None
    hunk_end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "line_number": self.line_number,
            "change_type": self.change_type,
            "content": self.content,
            "file_path": self.file_path,
            "hunk_start": self.hunk_start,
            "hunk_end": self.hunk_end,
        }


class DiffCache:
    """Thread-safe cache for diff parsing results."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE, ttl: int = CACHE_TTL):
        """Initialize the cache.

        Args:
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache = {}
        self._access_times = {}
        self._lock = threading.RLock()
        self._last_cleanup = time.time()

    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        if current_time - self._last_cleanup < CACHE_CLEANUP_INTERVAL:
            return

        expired_keys = []
        with self._lock:
            for key, (_, timestamp) in self._cache.items():
                if current_time - timestamp > self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                self._cache.pop(key, None)
                self._access_times.pop(key, None)
                _cache_stats["evictions"] += 1

            self._last_cleanup = current_time

    def _evict_lru(self):
        """Evict least recently used item."""
        if not self._access_times:
            return

        lru_key = min(self._access_times, key=self._access_times.get)
        self._cache.pop(lru_key, None)
        self._access_times.pop(lru_key, None)
        _cache_stats["evictions"] += 1

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        self._cleanup_expired()

        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp <= self.ttl:
                    self._access_times[key] = time.time()
                    _cache_stats["hits"] += 1
                    return value
                else:
                    # Expired
                    self._cache.pop(key, None)
                    self._access_times.pop(key, None)
                    _cache_stats["evictions"] += 1

            _cache_stats["misses"] += 1
            return None

    def set(self, key: str, value: Any):
        """Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cleanup_expired()

        with self._lock:
            # Remove if already exists
            if key in self._cache:
                self._cache.pop(key, None)
                self._access_times.pop(key, None)

            # Evict LRU if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            # Add new item
            current_time = time.time()
            self._cache[key] = (value, current_time)
            self._access_times[key] = current_time
            _cache_stats["size"] = len(self._cache)

    def clear(self):
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            _cache_stats["size"] = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hit_rate": (
                    _cache_stats["hits"]
                    / (_cache_stats["hits"] + _cache_stats["misses"])
                    if (_cache_stats["hits"] + _cache_stats["misses"]) > 0
                    else 0
                ),
                **{k: v for k, v in _cache_stats.items() if k != "size"},
            }


# Global cache instance
_diff_cache = DiffCache()


def _get_cache_key(data: str, operation: str) -> str:
    """Generate cache key for data and operation.

    Args:
        data: Input data
        operation: Operation type

    Returns:
        Cache key string
    """
    content_hash = hashlib.md5(data.encode("utf-8")).hexdigest()
    return f"{operation}:{content_hash}"


def _validate_diff_content(diff_content: str) -> bool:
    """Validate diff content format.

    Args:
        diff_content: Diff content to validate

    Returns:
        True if valid, False otherwise
    """
    if not diff_content or not isinstance(diff_content, str):
        return False

    lines = diff_content.split("\n")
    if len(lines) < 2:
        return False

    # Check for common diff markers
    has_diff_marker = any(line.startswith("diff --git") for line in lines[:10])
    has_file_marker = any(
        line.startswith("+++") or line.startswith("---") for line in lines[:10]
    )

    return has_diff_marker or has_file_marker


def _parse_hunk_header(hunk_line: str) -> Optional[Tuple[int, int, int, int]]:
    """Parse hunk header to extract line numbers.

    Args:
        hunk_line: Hunk header line

    Returns:
        Tuple of (old_start, old_count, new_start, new_count) or None
    """
    match = HUNK_PATTERN.match(hunk_line)
    if match:
        old_start = int(match.group(1))
        new_start = int(match.group(2))
        # Extract counts if present
        old_count = 1
        new_count = 1
        if "," in match.group(0):
            parts = match.group(0).split(",")
            if len(parts) >= 2:
                old_count = (
                    int(parts[1].split()[0]) if parts[1].split()[0].isdigit() else 1
                )
        return old_start, old_count, new_start, new_count
    return None


def _extract_file_path_from_diff_line(line: str) -> Optional[str]:
    """Extract file path from diff line.

    Args:
        line: Diff line

    Returns:
        File path or None
    """
    match = DIFF_FILE_PATTERN.match(line)
    if match:
        return match.group(2)  # b/ path
    return None


def _get_thread_local_data():
    """Get thread-local data storage."""
    if not hasattr(_thread_local, "data"):
        _thread_local.data = {}
    return _thread_local.data


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


def parse_diff_output_optimized(diff_output: Optional[str]) -> List[str]:
    """Optimized version of parse_diff_output using compiled regex.

    Args:
        diff_output: Output from git diff command

    Returns:
        List of changed file paths
    """
    if not diff_output:
        return []

    # Check cache first
    cache_key = _get_cache_key(diff_output, "parse_diff_output")
    cached_result = _diff_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    files = set()  # Use set for O(1) lookups
    lines = diff_output.split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            # Extract file path from diff output
            file_path = line[6:]  # Remove '+++ b/' or '--- a/' prefix
            files.add(file_path)

    result = list(files)
    _diff_cache.set(cache_key, result)
    return result


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
        self.cache = _diff_cache

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

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_stats()

    def clear_cache(self):
        """Clear the diff cache."""
        self.cache.clear()

    def parse_diff_optimized(self, diff_content: str) -> List[FileChange]:
        """Parse diff content with optimizations.

        Args:
            diff_content: Raw diff content

        Returns:
            List of FileChange objects
        """
        return extract_file_changes_optimized(diff_content)

    def get_diff_statistics(self, diff_content: str) -> Dict[str, Any]:
        """Get comprehensive statistics about a diff.

        Args:
            diff_content: Raw diff content

        Returns:
            Dictionary with diff statistics
        """
        return get_diff_statistics(diff_content)

    def validate_diff(self, diff_content: str) -> Dict[str, Any]:
        """Validate diff format.

        Args:
            diff_content: Raw diff content

        Returns:
            Dictionary with validation results
        """
        return validate_diff_format(diff_content)


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


def extract_file_changes(diff_content: Optional[str]) -> List[Dict[str, Any]]:
    """Extract file changes from diff content.

    Args:
        diff_content: Raw diff content

    Returns:
        List of file change dictionaries
    """
    if not diff_content:
        return []

    changes = []
    lines = diff_content.split("\n")
    current_file = None

    for line in lines:
        line = line.strip()
        match = DIFF_FILE_PATTERN.match(line)
        if match:
            # Extract file path from diff header
            file_path = match.group(2)  # b/ path
            current_file = file_path
            changes.append(
                {
                    "file_path": file_path,
                    "change_type": "modified",
                    "added_lines": 0,
                    "removed_lines": 0,
                }
            )
        elif FILE_MODE_PATTERN.match(line):
            if current_file and changes:
                mode_match = FILE_MODE_PATTERN.match(line)
                if mode_match:
                    mode = mode_match.group(1)
                    changes[-1]["change_type"] = mode

    return changes


def extract_file_changes_optimized(diff_content: Optional[str]) -> List[FileChange]:
    """Optimized version using compiled regex and better data structures.

    Args:
        diff_content: Raw diff content

    Returns:
        List of FileChange objects
    """
    if not diff_content or not _validate_diff_content(diff_content):
        return []

    # Check cache first
    cache_key = _get_cache_key(diff_content, "extract_file_changes")
    cached_result = _diff_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    changes = []
    lines = diff_content.split("\n")
    current_file = None
    current_change = None
    added_lines = 0
    removed_lines = 0
    similarity = None
    old_path = None
    is_binary = False

    for line in lines:
        line = line.strip()

        # File diff header
        match = DIFF_FILE_PATTERN.match(line)
        if match:
            # Save previous change if exists
            if current_change:
                current_change.added_lines = added_lines
                current_change.removed_lines = removed_lines
                current_change.similarity = similarity
                current_change.old_path = old_path
                current_change.is_binary = is_binary
                changes.append(current_change)

            # Start new file
            file_path = match.group(2)  # b/ path
            current_file = file_path
            current_change = FileChange(
                file_path=file_path, change_type=ChangeType.MODIFIED
            )
            added_lines = 0
            removed_lines = 0
            similarity = None
            old_path = None
            is_binary = False

        # File mode changes
        elif FILE_MODE_PATTERN.match(line):
            if current_change:
                mode_match = FILE_MODE_PATTERN.match(line)
                if mode_match:
                    mode = mode_match.group(1)
                    if mode == "new":
                        current_change.change_type = ChangeType.ADDED
                    elif mode == "deleted":
                        current_change.change_type = ChangeType.DELETED

        # Binary file detection
        elif BINARY_FILE_PATTERN.match(line):
            is_binary = True

        # Similarity index for renames
        elif SIMILARITY_PATTERN.match(line):
            sim_match = SIMILARITY_PATTERN.match(line)
            if sim_match:
                similarity = int(sim_match.group(1))

        # Rename from
        elif RENAME_PATTERN.match(line):
            rename_match = RENAME_PATTERN.match(line)
            if rename_match:
                old_path = rename_match.group(1)
                if current_change:
                    current_change.change_type = ChangeType.RENAMED

        # Hunk lines
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines += 1

    # Save last change
    if current_change:
        current_change.added_lines = added_lines
        current_change.removed_lines = removed_lines
        current_change.similarity = similarity
        current_change.old_path = old_path
        current_change.is_binary = is_binary
        changes.append(current_change)

    _diff_cache.set(cache_key, changes)
    return changes


def get_added_lines(diff_content: Optional[str]) -> List[Dict[str, Any]]:
    """Extract added lines from diff content.

    Args:
        diff_content: Raw diff content

    Returns:
        List of added line dictionaries
    """
    if not diff_content:
        return []

    added_lines = []
    lines = diff_content.split("\n")
    current_file = None
    line_number = 0

    for line in lines:
        line = line.strip()
        if line.startswith("diff --git"):
            # Reset for new file
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3].replace("b/", "")
                line_number = 0
        elif line.startswith("@@"):
            # Parse hunk header to get line numbers
            try:
                # Extract line number from hunk header
                parts = line.split()
                if len(parts) >= 2:
                    line_info = parts[1].split(",")[0].replace("+", "")
                    line_number = int(line_info) - 1
            except (ValueError, IndexError):
                pass
        elif line.startswith("+") and not line.startswith("+++"):
            # This is an added line
            line_number += 1
            added_lines.append(
                {
                    "file_path": current_file,
                    "line_number": line_number,
                    "content": line[1:],  # Remove the + prefix
                    "change_type": "added",
                }
            )
        elif not line.startswith("-") and not line.startswith("@"):
            # Regular line (not a hunk header or diff marker)
            line_number += 1

    return added_lines


def get_added_lines_optimized(diff_content: Optional[str]) -> List[LineChange]:
    """Optimized version using compiled regex patterns.

    Args:
        diff_content: Raw diff content

    Returns:
        List of LineChange objects
    """
    if not diff_content or not _validate_diff_content(diff_content):
        return []

    # Check cache first
    cache_key = _get_cache_key(diff_content, "get_added_lines")
    cached_result = _diff_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    added_lines = []
    lines = diff_content.split("\n")
    current_file = None
    line_number = 0
    hunk_start = None
    hunk_end = None

    for line in lines:
        line = line.strip()
        match = DIFF_FILE_PATTERN.match(line)
        if match:
            # Reset for new file
            current_file = match.group(2)  # b/ path
            line_number = 0
            hunk_start = None
            hunk_end = None
        elif HUNK_PATTERN.match(line):
            # Parse hunk header to get line numbers
            hunk_info = _parse_hunk_header(line)
            if hunk_info:
                _, _, new_start, new_count = hunk_info
                line_number = new_start - 1
                hunk_start = new_start
                hunk_end = new_start + new_count - 1
        elif ADDED_LINE_PATTERN.match(line) and not line.startswith("+++"):
            # This is an added line
            line_number += 1
            added_lines.append(
                LineChange(
                    line_number=line_number,
                    change_type="added",
                    content=line[1:],  # Remove the + prefix
                    file_path=current_file,
                    hunk_start=hunk_start,
                    hunk_end=hunk_end,
                )
            )
        elif not REMOVED_LINE_PATTERN.match(line) and not line.startswith("@"):
            # Regular line (not a hunk header or diff marker)
            line_number += 1

    _diff_cache.set(cache_key, added_lines)
    return added_lines


def get_removed_lines(diff_content: Optional[str]) -> List[Dict[str, Any]]:
    """Extract removed lines from diff content.

    Args:
        diff_content: Raw diff content

    Returns:
        List of removed line dictionaries
    """
    if not diff_content:
        return []

    removed_lines = []
    lines = diff_content.split("\n")
    current_file = None
    line_number = 0

    for line in lines:
        line = line.strip()
        if line.startswith("diff --git"):
            # Reset for new file
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3].replace("b/", "")
                line_number = 0
        elif line.startswith("@@"):
            # Parse hunk header to get line numbers
            try:
                # Extract line number from hunk header
                parts = line.split()
                if len(parts) >= 2:
                    line_info = parts[1].split(",")[0].replace("-", "")
                    line_number = int(line_info) - 1
            except (ValueError, IndexError):
                pass
        elif line.startswith("-") and not line.startswith("---"):
            # This is a removed line
            line_number += 1
            removed_lines.append(
                {
                    "file_path": current_file,
                    "line_number": line_number,
                    "content": line[1:],  # Remove the - prefix
                    "change_type": "removed",
                }
            )
        elif not line.startswith("+") and not line.startswith("@"):
            # Regular line (not a hunk header or diff marker)
            line_number += 1

    return removed_lines


def get_removed_lines_optimized(diff_content: Optional[str]) -> List[LineChange]:
    """Optimized version using compiled regex patterns.

    Args:
        diff_content: Raw diff content

    Returns:
        List of LineChange objects
    """
    if not diff_content or not _validate_diff_content(diff_content):
        return []

    # Check cache first
    cache_key = _get_cache_key(diff_content, "get_removed_lines")
    cached_result = _diff_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    removed_lines = []
    lines = diff_content.split("\n")
    current_file = None
    line_number = 0
    hunk_start = None
    hunk_end = None

    for line in lines:
        line = line.strip()
        match = DIFF_FILE_PATTERN.match(line)
        if match:
            # Reset for new file
            current_file = match.group(2)  # b/ path
            line_number = 0
            hunk_start = None
            hunk_end = None
        elif HUNK_PATTERN.match(line):
            # Parse hunk header to get line numbers
            hunk_info = _parse_hunk_header(line)
            if hunk_info:
                old_start, old_count, _, _ = hunk_info
                line_number = old_start - 1
                hunk_start = old_start
                hunk_end = old_start + old_count - 1
        elif REMOVED_LINE_PATTERN.match(line) and not line.startswith("---"):
            # This is a removed line
            line_number += 1
            removed_lines.append(
                LineChange(
                    line_number=line_number,
                    change_type="removed",
                    content=line[1:],  # Remove the - prefix
                    file_path=current_file,
                    hunk_start=hunk_start,
                    hunk_end=hunk_end,
                )
            )
        elif not ADDED_LINE_PATTERN.match(line) and not line.startswith("@"):
            # Regular line (not a hunk header or diff marker)
            line_number += 1

    _diff_cache.set(cache_key, removed_lines)
    return removed_lines


def get_modified_files(diff_content: Optional[str]) -> List[str]:
    """Extract modified file paths from diff content.

    Args:
        diff_content: Raw diff content

    Returns:
        List of modified file paths
    """
    if not diff_content:
        return []

    files = []
    lines = diff_content.split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("diff --git"):
            # Extract file path from diff header
            parts = line.split()
            if len(parts) >= 4:
                file_path = parts[3].replace("b/", "")
                if file_path not in files:
                    files.append(file_path)

    return files


def get_modified_files_optimized(diff_content: Optional[str]) -> List[str]:
    """Optimized version using compiled regex patterns.

    Args:
        diff_content: Raw diff content

    Returns:
        List of modified file paths
    """
    if not diff_content or not _validate_diff_content(diff_content):
        return []

    # Check cache first
    cache_key = _get_cache_key(diff_content, "get_modified_files")
    cached_result = _diff_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    files = set()
    lines = diff_content.split("\n")

    for line in lines:
        line = line.strip()
        match = DIFF_FILE_PATTERN.match(line)
        if match:
            file_path = match.group(2)  # b/ path
            files.add(file_path)

    result = list(files)
    _diff_cache.set(cache_key, result)
    return result


def parse_multiple_diffs_parallel(
    diff_contents: List[str], max_workers: int = 4
) -> List[List[Dict[str, Any]]]:
    """Parse multiple diff contents in parallel for better performance.

    Args:
        diff_contents: List of diff content strings
        max_workers: Maximum number of worker threads

    Returns:
        List of parsed diff results
    """
    if not diff_contents:
        return []

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all parsing tasks
        future_to_diff = {
            executor.submit(extract_file_changes_optimized, diff): diff
            for diff in diff_contents
        }

        # Collect results as they complete
        for future in as_completed(future_to_diff):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Log error and append empty result
                print(f"Error parsing diff: {e}")
                results.append([])

    return results


def benchmark_diff_parsing(
    diff_content: str, iterations: int = 1000
) -> Dict[str, float]:
    """Benchmark different diff parsing approaches.

    Args:
        diff_content: Sample diff content to parse
        iterations: Number of iterations to run

    Returns:
        Dictionary with timing results
    """
    import time

    # Benchmark original function
    start_time = time.time()
    for _ in range(iterations):
        extract_file_changes(diff_content)
    original_time = time.time() - start_time

    # Benchmark optimized function
    start_time = time.time()
    for _ in range(iterations):
        extract_file_changes_optimized(diff_content)
    optimized_time = time.time() - start_time

    return {
        "original_time": original_time,
        "optimized_time": optimized_time,
        "speedup": original_time / optimized_time if optimized_time > 0 else 0,
    }


def get_diff_statistics(diff_content: str) -> Dict[str, Any]:
    """Get comprehensive statistics about a diff.

    Args:
        diff_content: Raw diff content

    Returns:
        Dictionary with diff statistics
    """
    if not diff_content or not _validate_diff_content(diff_content):
        return {}

    # Check cache first
    cache_key = _get_cache_key(diff_content, "diff_statistics")
    cached_result = _diff_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    changes = extract_file_changes_optimized(diff_content)
    added_lines = get_added_lines_optimized(diff_content)
    removed_lines = get_removed_lines_optimized(diff_content)

    # Calculate statistics
    total_files = len(changes)
    total_added = sum(change.added_lines for change in changes)
    total_removed = sum(change.removed_lines for change in changes)

    file_types = {}
    for change in changes:
        ext = os.path.splitext(change.file_path)[1]
        file_types[ext] = file_types.get(ext, 0) + 1

    change_types = {}
    for change in changes:
        change_types[change.change_type.value] = (
            change_types.get(change.change_type.value, 0) + 1
        )

    stats = {
        "total_files": total_files,
        "total_added_lines": total_added,
        "total_removed_lines": total_removed,
        "net_lines": total_added - total_removed,
        "file_types": file_types,
        "change_types": change_types,
        "added_line_details": len(added_lines),
        "removed_line_details": len(removed_lines),
        "has_binary_files": any(change.is_binary for change in changes),
        "has_renames": any(
            change.change_type == ChangeType.RENAMED for change in changes
        ),
    }

    _diff_cache.set(cache_key, stats)
    return stats


def validate_diff_format(diff_content: str) -> Dict[str, Any]:
    """Validate diff format and return validation results.

    Args:
        diff_content: Raw diff content

    Returns:
        Dictionary with validation results
    """
    if not diff_content:
        return {"valid": False, "errors": ["Empty diff content"]}

    errors = []
    warnings = []

    lines = diff_content.split("\n")

    # Check for basic structure
    has_diff_header = any(line.startswith("diff --git") for line in lines)
    has_file_headers = any(
        line.startswith("+++") or line.startswith("---") for line in lines
    )

    if not has_diff_header and not has_file_headers:
        errors.append("No diff headers found")

    # Check for malformed lines
    malformed_lines = []
    for i, line in enumerate(lines):
        if line.startswith("@@") and not HUNK_PATTERN.match(line):
            malformed_lines.append(i + 1)

    if malformed_lines:
        warnings.append(f"Malformed hunk headers at lines: {malformed_lines}")

    # Check for binary files
    has_binary = any(BINARY_FILE_PATTERN.match(line) for line in lines)
    if has_binary:
        warnings.append("Contains binary files")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "line_count": len(lines),
        "has_diff_headers": has_diff_header,
        "has_file_headers": has_file_headers,
        "has_binary_files": has_binary,
    }
