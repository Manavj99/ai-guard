"""Minimal SARIF v2.1.0 writer for AI-Guard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import json


@dataclass
class SarifResult:
    rule_id: str
    level: str  # "none" | "note" | "warning" | "error"
    message: str
    locations: List[Dict[str, Any]] | None = None


@dataclass
class SarifRun:
    tool_name: str
    results: List[SarifResult]


def write_sarif(path: str, run: SarifRun) -> None:
    sarif: Dict[str, Any] = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": run.tool_name}},
                "results": [
                    {
                        "ruleId": r.rule_id,
                        "level": r.level,
                        "message": {"text": r.message},
                        **({"locations": r.locations} if r.locations else {}),
                    }
                    for r in run.results
                ],
            }
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2)


def make_location(
    file_path: str, line: int | None = None, column: int | None = None
) -> Dict[str, Any]:
    # Normalize file path to use forward slashes for GitHub compatibility
    normalized_path = file_path.replace("\\", "/")

    region: Dict[str, Any] = {}
    if line is not None:
        region["startLine"] = line
    if column is not None:
        region["startColumn"] = column

    # Only include region if we have line or column information
    location: Dict[str, Any] = {
        "physicalLocation": {
            "artifactLocation": {"uri": normalized_path},
        }
    }

    # Add region only if it contains actual data
    if region:
        location["physicalLocation"]["region"] = region

    return location
