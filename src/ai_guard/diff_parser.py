"""Parse changed files from Git diffs or GitHub events."""

import json
import os
from typing import List, Tuple


def changed_python_files(event_path: str | None = None) -> List[str]:
    """Get list of changed Python files.
    
    Args:
        event_path: Path to GitHub event JSON file
        
    Returns:
        List of Python file paths that have changed
    """
    # If GitHub event is provided and has base/head, use precise diff
    if event_path:
        base_head = _get_base_head_from_event(event_path)
        if base_head is not None:
            base, head = base_head
            files = _git_changed_files(base, head)
            return [p for p in files if p.endswith(".py")]
    # Fallback: all tracked Python files
    return [p for p in _git_ls_files() if p.endswith(".py")]


def _git_ls_files() -> List[str]:
    """Get all tracked files from Git."""
    import subprocess
    
    try:
        out = subprocess.check_output(["git", "ls-files"], text=True)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback if git is not available
        return []


def _git_changed_files(base_ref: str, head_ref: str) -> List[str]:
    """Get changed files between base and head refs.
    
    Uses `git diff --name-only base...head` to include merge-base.
    """
    import subprocess
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", f"{base_ref}...{head_ref}"], text=True)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def parse_github_event(event_path: str) -> dict:
    """Parse GitHub event JSON file.
    
    Args:
        event_path: Path to the event JSON file
        
    Returns:
        Parsed event data
    """
    try:
        with open(event_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _get_base_head_from_event(event_path: str) -> Tuple[str, str] | None:
    """Extract base and head SHA or refs from a GitHub event file.
    
    Supports pull_request events.
    """
    event = parse_github_event(event_path)
    if not event:
        return None
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        return None
    base_sha = pr.get("base", {}).get("sha") or pr.get("base", {}).get("ref")
    head_sha = pr.get("head", {}).get("sha") or pr.get("head", {}).get("ref")
    if isinstance(base_sha, str) and isinstance(head_sha, str):
        return base_sha, head_sha
    return None
