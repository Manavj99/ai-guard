"""Parse changed files from Git diffs or GitHub events."""

import json
from typing import List, Tuple, Dict, Any


def changed_python_files(event_path: str | None = None) -> List[str]:
    """Get list of changed Python files.

    Args:
        event_path: Path to GitHub event JSON file

    Returns:
        List of Python file paths that have changed
    """
    # If GitHub event is provided and has base/head, use precise diff
    if event_path:
        try:
            base_head = _get_base_head_from_event(event_path)
            if base_head is not None:
                base, head = base_head
                files = _git_changed_files(base, head)
                if files:  # Only return diff if we successfully got files
                    return [p for p in files if p.endswith(".py")]
        except Exception as e:
            print(f"Warning: Error parsing GitHub event: {e}")
    
    # Fallback: all tracked Python files
    try:
        return [p for p in _git_ls_files() if p.endswith(".py")]
    except Exception as e:
        print(f"Warning: Error getting tracked files: {e}")
        return []


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
        # Validate that the refs exist in the repository
        subprocess.check_call(["git", "rev-parse", "--verify", base_ref], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(["git", "rev-parse", "--verify", head_ref], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Get the diff
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"], text=True
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
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
        base_sha = pr.get("base", {}).get("sha")
        head_sha = pr.get("head", {}).get("sha")
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
