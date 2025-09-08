from __future__ import annotations

import xml.etree.ElementTree as ET  # nosec B405 - trusted coverage XML input
from dataclasses import dataclass


@dataclass
class CoverageResult:
    passed: bool
    percent: float


def _percent_from_root(root: ET.Element) -> float:
    # Coverage.py XML uses either attributes line-rate / branch-rate
    # or counters (lines-valid, lines-covered).
    line_rate = root.attrib.get("line-rate")
    if line_rate is not None:
        try:
            return float(line_rate) * 100.0
        except ValueError:
            pass

    lines_valid = root.attrib.get("lines-valid")
    lines_covered = root.attrib.get("lines-covered")
    if lines_valid and lines_covered:
        try:
            valid = float(lines_valid)
            covered = float(lines_covered)
            if valid > 0:
                return (covered / valid) * 100.0
        except ValueError:
            pass

    # Fallback: sum over packages/classes if present
    total_cov = 0.0
    total_valid = 0.0
    for counter in root.iter("counter"):
        if counter.attrib.get("type") == "LINE":
            cov = float(counter.attrib.get("covered", 0))
            miss = float(counter.attrib.get("missed", 0))
            total_cov += cov
            total_valid += (cov + miss)

    if total_valid > 0:
        return (total_cov / total_valid) * 100.0

    return 0.0


def evaluate_coverage_str(xml_text: str, threshold: float = 80.0) -> CoverageResult:
    """
    Evaluate coverage percentage from a coverage XML string.

    Returns:
        CoverageResult(passed=<bool>, percent=<float>)
    """
    root = ET.fromstring(xml_text)  # nosec B314 - trusted coverage XML input
    pct = _percent_from_root(root)
    return CoverageResult(passed=(pct >= threshold), percent=pct)
