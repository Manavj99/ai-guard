"""Minimal SARIF v2.1.0 writer for AI-Guard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
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
    tool_version: str = "unknown"


def create_sarif_report(
    runs: List[SarifRun], metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a complete SARIF report.

    Args:
        runs: List of SARIF runs
        metadata: Optional metadata to include

    Returns:
        Complete SARIF report dictionary
    """
    sarif: Dict[str, Any] = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [],
    }

    # Add metadata if provided
    if metadata:
        sarif["metadata"] = metadata

    # Process each run
    for run in runs:
        run_data: Dict[str, Any] = {
            "tool": {"driver": {"name": run.tool_name}},
            "results": [],
        }

        for result in run.results:
            result_data: Dict[str, Any] = {
                "ruleId": result.rule_id,
                "level": result.level,
                "message": {"text": result.message},
            }

            if result.locations:
                result_data["locations"] = result.locations

            run_data["results"].append(result_data)

        sarif["runs"].append(run_data)

    return sarif


def parse_issue_to_sarif(issue: Dict[str, Any]) -> SarifResult:
    """Convert a generic issue dictionary to a SARIF result.

    Args:
        issue: Issue dictionary with keys like 'rule_id', 'level', 'message', 'file', 'line'

    Returns:
        SARIF result object
    """
    rule_id = issue.get("rule_id", "unknown")
    level = issue.get("level", "warning")
    message = issue.get("message", "No message provided")

    # Create location if file and line information is available
    locations = None
    if "file" in issue and "line" in issue:
        file_path = issue["file"]
        line = issue["line"]
        column = issue.get("column")

        location = make_location(file_path, line, column)
        locations = [location]

    return SarifResult(
        rule_id=rule_id, level=level, message=message, locations=locations
    )


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
