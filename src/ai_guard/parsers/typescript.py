from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .common import normalize_rule


def parse_eslint(output: str) -> List[Dict[str, Any]]:
    """
    Parse ESLint output.

    Priority:
      1) JSON format (eslint -f json)
      2) Stylish-like text lines: /path/file.ts:12:5  error  Message  rule-id
    """
    output = output or ""

    # Try JSON first
    try:
        data = json.loads(output)
        findings: List[Dict[str, Any]] = []
        for file_entry in data:
            file_path = file_entry.get("filePath")
            for msg in file_entry.get("messages", []):
                severity = "error" if (msg.get("severity") == 2) else "warning"
                findings.append(
                    {
                        "file": file_path,
                        "line": int(msg.get("line", 1) or 1),
                        "col": int(msg.get("column", 1) or 1),
                        "rule": normalize_rule("eslint", msg.get("ruleId") or "unknown"),
                        "message": msg.get("message", ""),
                        "severity": severity,
                    }
                )
        return findings
    except Exception:
        pass

    # Fallback: stylish-like
    findings_fallback: List[Dict[str, Any]] = []
    line_re = re.compile(
        r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+)\s+"
        r"(?P<sev>error|warning)\s+"
        r"(?P<msg>.+?)\s+"
        r"(?P<rule>[\w-]+)\s*$"
    )
    for line in output.splitlines():
        m = line_re.search(line.strip())
        if not m:
            continue
        findings_fallback.append(
            {
                "file": m.group("file"),
                "line": int(m.group("line")),
                "col": int(m.group("col")),
                "rule": normalize_rule("eslint", m.group("rule")),
                "message": m.group("msg"),
                "severity": m.group("sev"),
            }
        )
    return findings_fallback


def parse_jest(output: str) -> Dict[str, int]:
    """
    Parse human-readable Jest summary.

    Example line:
      'Tests:       1 failed, 12 passed, 13 total'
    """
    output = output or ""
    summary = {"tests": 0, "passed": 0, "failed": 0}

    m = re.search(
        r"Tests:\s+(?:(\d+)\s+failed,?\s*)?(?:(\d+)\s+passed,?\s*)?(?:(\d+)\s+total)",
        output,
    )
    if m:
        failed = int(m.group(1) or 0)
        passed = int(m.group(2) or 0)
        total = int(m.group(3) or (failed + passed))
        summary.update({"tests": total, "passed": passed, "failed": failed})
    return summary
