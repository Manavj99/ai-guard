from __future__ import annotations

from typing import Callable


def _extract_mypy_rule(raw: str) -> str:
    """Extract rule from mypy error format like 'error[name-defined]'."""
    # Simple pattern to match error[rule] format
    if "[" in raw and "]" in raw:
        start = raw.find("[")
        end = raw.rfind("]")  # Use rfind to get the last closing bracket
        if start != -1 and end != -1 and end > start:
            rule = raw[start + 1 : end]
            return f"mypy:{rule}"
    return f"mypy:{raw}" if not raw.startswith("mypy:") else raw


# Individual normalizers keep each tool stable and easy to extend.
_RULE_NORMALIZERS: dict[str, Callable[[str], str]] = {
    "flake8": lambda r: r if r.startswith("flake8:") else f"flake8:{r}",
    "mypy": _extract_mypy_rule,
    "bandit": lambda r: r if r.startswith("bandit:") else f"bandit:{r}",
    "eslint": lambda r: r if r.startswith("eslint:") else f"eslint:{r}",
    "jest": lambda r: r if r.startswith("jest:") else f"jest:{r}",
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
    # Handle None, empty or whitespace tool
    if tool is None:
        tool_l = "none"
    elif not tool or not tool.strip():
        tool_l = ""
    else:
        tool_l = tool.strip().lower()

    if raw is None:
        raw = "None"
    elif not raw:
        raw = ""
    else:
        raw = str(raw)

    # If tool is empty string, return just the rule with colon prefix
    if tool_l == "":
        return f":{raw}"

    norm = _RULE_NORMALIZERS.get(tool_l)
    if norm:
        return norm(raw)
    return f"{tool_l}:{raw}"
