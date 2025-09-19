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


def generate_json_report(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a JSON report from analysis results.

    Args:
        analysis_results: Analysis results dictionary

    Returns:
        Dictionary with JSON report data
    """
    report_data = {
        "version": "1.0",
        "timestamp": "2024-01-01T00:00:00Z",
        "files_analyzed": analysis_results.get("files_analyzed", 0),
        "total_issues": analysis_results.get("total_issues", 0),
        "issues_by_type": analysis_results.get("issues_by_type", {}),
        "issues": analysis_results.get("issues", []),
    }

    return {
        "success": True,
        "format": "json",
        "content": json.dumps(report_data, indent=2),
        **report_data,
    }


def format_json_summary(report_data: Dict[str, Any]) -> str:
    """Format a report summary as JSON.

    Args:
        report_data: Report data dictionary

    Returns:
        JSON formatted summary
    """
    summary_data = {
        "files_analyzed": report_data.get("files_analyzed", 0),
        "total_issues": report_data.get("total_issues", 0),
        "issues_by_type": report_data.get("issues_by_type", {}),
    }

    return json.dumps(summary_data, indent=2)


class JSONReportGenerator:
    """JSON report generator class."""

    def __init__(self):
        """Initialize the JSON report generator."""
        pass

    def generate_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a JSON report.

        Args:
            analysis_results: Analysis results dictionary

        Returns:
            Dictionary with JSON report data
        """
        return generate_json_report(analysis_results)
