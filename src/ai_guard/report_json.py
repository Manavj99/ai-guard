"""JSON report writer for AI-Guard."""

from typing import List, Dict, Any
import json
from .report import GateResult


def write_json(
    report_path: str,
    gates: List[GateResult],
    findings: List[dict[str, str | int | None]],
) -> None:
    """Write a JSON report with gate summaries and findings.

    Args:
        report_path: Path to write the JSON file
        gates: List of gate results
        findings: List of findings as dictionaries with rule_id, level,
                 message, path, line
    """
    payload: Dict[str, Any] = {
        "version": "1.0",
        "summary": {
            "passed": all(g.passed for g in gates),
            "gates": [
                {"name": g.name, "passed": g.passed, "details": g.details or ""}
                for g in gates
            ],
        },
        "findings": findings,  # list of dicts: {rule_id, level, message, path, line}
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
