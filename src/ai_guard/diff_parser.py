"""Parse changed files from Git diffs or GitHub events."""

import json
import os
from typing import List


def changed_python_files(event_path: str | None = None) -> List[str]:
    """Get list of changed Python files.
    
    Args:
        event_path: Path to GitHub event JSON file
        
    Returns:
        List of Python file paths that have changed
    """
    # Conservative: just diff entire repo in initial version
    # Later you can parse event JSON or `git diff` range for precision
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
