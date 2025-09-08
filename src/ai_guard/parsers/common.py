from __future__ import annotations

from typing import Any, Callable


def _extract_mypy_rule(raw: str) -> str:
    """Extract rule from mypy error format like 'error[name-defined]'."""
    # Simple pattern to match error[rule] format
    if '[' in raw and ']' in raw:
        start = raw.find('[')
        end = raw.find(']')
        if start != -1 and end != -1 and end > start:
            rule = raw[start + 1:end]
            return f"mypy:{rule}"
    return f"mypy:{raw}" if not raw.startswith("mypy:") else raw


# Individual normalizers keep each tool stable and easy to extend.
_RULE_NORMALIZERS: dict[str, Callable[[str], str]] = {
    "flake8": lambda r: r if ":" in r else f"flake8:{r}",
    "mypy": _extract_mypy_rule,
    "bandit": lambda r: r if r.startswith("bandit:") else f"bandit:{r}",
    "eslint": lambda r: r if ":" in r else f"eslint:{r}",
    "jest": lambda r: r if ":" in r else f"jest:{r}",
}


def normalize_rule(tool: str, raw: str) -> str:
    """
    Normalize a tool-specific rule/code into 'tool:rule' form.

    Examples:
      flake8 + 'E501'         -> 'flake8:E501'
      mypy   + 'error[name]'  -> 'mypy:name'
      bandit + 'B101'         -> 'bandit:B101'
      eslint + 'no-unused'    -> 'eslint:no-unused'
    """
    tool_l = (tool or "").lower()
    raw = raw or "unknown"
    norm = _RULE_NORMALIZERS.get(tool_l)
    if norm:
        return norm(raw)
    return f"{tool_l}:{raw}"
