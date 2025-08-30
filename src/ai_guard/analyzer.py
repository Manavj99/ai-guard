"""Main analyzer that orchestrates all quality gate checks."""

import argparse
import subprocess
import re
import json
import sys
from typing import List

from .config import load_config
from .report import GateResult, summarize
from .diff_parser import changed_python_files
from .sarif_report import SarifRun, SarifResult, write_sarif, make_location
from .tests_runner import run_pytest_with_coverage
from .report_json import write_json
from .report_html import write_html


def cov_percent() -> int:
    """Parse coverage.xml and return percentage.

    Returns:
        Coverage percentage as integer
    """
    # Harden XML parsing against XML-based attacks
    from defusedxml import ElementTree as ET
    import os

    # Try multiple possible locations for coverage.xml
    coverage_paths = ["coverage.xml", "../coverage.xml"]

    for coverage_path in coverage_paths:
        try:
            if os.path.exists(coverage_path):
                tree = ET.parse(coverage_path)
                rate = float(tree.getroot().get("line-rate", "0"))
                return int(round(rate * 100))
        except Exception as e:
            print(f"Warning: Could not parse {coverage_path}: {e}")
            continue

    print("Warning: No coverage.xml file found")
    return 0


def _parse_flake8_output(output: str) -> List[SarifResult]:
    results: List[SarifResult] = []
    pattern = re.compile(
        (
            r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+): "
            r"(?P<code>[A-Z]\d{3,4}) (?P<msg>.*)$"
        )
    )
    for line in output.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        file_path = m.group("file")
        line_no = int(m.group("line"))
        col_no = int(m.group("col"))
        code = m.group("code")
        msg = m.group("msg")
        results.append(
            SarifResult(
                rule_id=f"flake8:{code}",
                level="warning",
                message=f"{code} {msg}",
                locations=[make_location(file_path, line_no, col_no)],
            )
        )
    return results


def _parse_mypy_output(output: str) -> List[SarifResult]:
    results: List[SarifResult] = []
    pattern = re.compile(
        (
            r"^(?P<file>.*?):(?P<line>\d+):(?:(?P<col>\d+):)? "
            r"(?P<level>error|note|warning): "
            r"(?P<msg>.*?)(?: \[(?P<code>[^\]]+)\])?$"
        )
    )
    for line in output.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        file_path = m.group("file")
        line_no = int(m.group("line"))
        col = m.group("col")
        col_no = int(col) if col else None
        level = m.group("level")
        msg = m.group("msg")
        code = m.group("code") or "mypy-error"
        sarif_level = (
            "error"
            if level == "error"
            else ("warning" if level == "warning" else "note")
        )
        results.append(
            SarifResult(
                rule_id=f"mypy:{code}",
                level=sarif_level,
                message=msg,
                locations=[make_location(file_path, line_no, col_no)],
            )
        )
    return results


def run_lint_check(
    paths: List[str] | None = None,
) -> tuple[GateResult, List[SarifResult]]:
    """Run flake8 linting check.

    Returns:
        GateResult for linting
    """
    try:
        cmd = ["flake8"]
        if paths:
            cmd.extend(paths)
        else:
            cmd.extend(["src", "tests"])
        proc = subprocess.run(cmd, text=True, capture_output=True)
        sarif = _parse_flake8_output(proc.stdout + "\n" + proc.stderr)
        return GateResult("Lint (flake8)", proc.returncode == 0), sarif
    except FileNotFoundError:
        return GateResult("Lint (flake8)", False, "flake8 not found"), []


def run_type_check(
    paths: List[str] | None = None,
) -> tuple[GateResult, List[SarifResult]]:
    """Run mypy type checking.

    Returns:
        GateResult for type checking
    """
    try:
        cmd = ["mypy", "--show-error-codes", "--no-color-output", "--no-error-summary"]
        if paths:
            cmd.extend(paths)
        else:
            cmd.append("src")
        proc = subprocess.run(cmd, text=True, capture_output=True)
        sarif = _parse_mypy_output(proc.stdout + "\n" + proc.stderr)
        return GateResult("Static types (mypy)", proc.returncode == 0), sarif
    except FileNotFoundError:
        return GateResult("Static types (mypy)", False, "mypy not found"), []


def _parse_bandit_json(output: str) -> List[SarifResult]:
    """Parse Bandit's JSON output into SARIF results."""
    results: List[SarifResult] = []
    try:
        data = json.loads(output or "{}")
    except json.JSONDecodeError:
        return results

    issues = data.get("results") or []
    for issue in issues:
        file_path = issue.get("filename") or issue.get("file_name") or ""
        line_no = issue.get("line_number")
        test_id = issue.get("test_id") or "bandit-issue"
        message = (
            issue.get("issue_text") or issue.get("issue_severity") or "Bandit issue"
        )
        sev = (issue.get("issue_severity") or "LOW").upper()
        level = "note"
        if sev == "MEDIUM":
            level = "warning"
        if sev == "HIGH":
            level = "error"
        location = make_location(
            file_path, int(line_no) if isinstance(line_no, int) else None, None
        )
        results.append(
            SarifResult(
                rule_id=f"bandit:{test_id}",
                level=level,
                message=message,
                locations=[location],
            )
        )
    return results


def run_security_check() -> tuple[GateResult, List[SarifResult]]:
    """Run bandit security scan.

    Returns:
        GateResult for security scanning
    """
    try:
        # Prefer JSON output for SARIF conversion
        proc = subprocess.run(
            ["bandit", "-r", "src", "-x", "tests", "-s", "B101", "-f", "json", "-q"],
            text=True,
            capture_output=True,
        )
        sarif = _parse_bandit_json(proc.stdout)
        # Treat HIGH severity as blocking; MEDIUM/LOW are warnings
        passed = not any(r.level == "error" for r in sarif)
        return GateResult("Security (bandit)", passed), sarif
    except FileNotFoundError:
        return GateResult("Security (bandit)", False, "bandit not found"), []


def _to_findings(sarif_results: List[SarifResult]) -> List[dict[str, str | int | None]]:
    """Convert SARIF results to neutral findings format for JSON/HTML reports.

    Args:
        sarif_results: List of SARIF results

    Returns:
        List of findings as dictionaries
    """
    out = []
    for r in sarif_results:
        # Extract location info if available
        path = "unknown"
        line = None
        if r.locations and len(r.locations) > 0:
            loc = r.locations[0]
            if ("physicalLocation" in loc
                    and "artifactLocation" in loc["physicalLocation"]):
                path = loc["physicalLocation"]["artifactLocation"].get("uri", "unknown")
            if ("physicalLocation" in loc
                    and "region" in loc["physicalLocation"]):
                line = loc["physicalLocation"]["region"].get("startLine")

        out.append({
            "rule_id": r.rule_id,
            "level": r.level,
            "message": r.message,
            "path": path,
            "line": line,
        })
    return out


def run_coverage_check(min_coverage: int) -> GateResult:
    """Run coverage check.

    Args:
        min_coverage: Minimum required coverage percentage

    Returns:
        GateResult for coverage
    """
    pct = cov_percent()
    passed = pct >= min_coverage
    details = f"{pct}% >= {min_coverage}%"
    return GateResult("Coverage", passed, details)


def main() -> None:
    """Main entry point for AI-Guard analyzer."""
    parser = argparse.ArgumentParser(description="AI-Guard Quality Gate Analyzer")
    default_gates = load_config()
    parser.add_argument(
        "--min-cov",
        type=int,
        default=default_gates.min_coverage,
        help=(
            f"Minimum coverage percentage "
            f"(default: {default_gates.min_coverage})"
        ),
    )
    parser.add_argument(
        "--skip-tests", action="store_true", help="Skip running tests (useful for CI)"
    )
    parser.add_argument(
        "--event",
        type=str,
        default=None,
        help="Path to GitHub event JSON to scope changed files",
    )
    parser.add_argument(
        "--report-format",
        choices=["sarif", "json", "html"],
        default="sarif",
        help="Output format for the final report"
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default=None,
        help="Path to write the report. Default depends on format"
    )
    # Back-compat:
    parser.add_argument(
        "--sarif", type=str, default=None,
        help=(
            "(Deprecated) Output SARIF file path; "
            "use --report-format/--report-path"
        )
    )
    args = parser.parse_args()

    # Handle deprecated --sarif argument
    if args.sarif and not args.report_path:
        print(
            "[warn] --sarif is deprecated. Use --report-format sarif "
            "--report-path PATH",
            file=sys.stderr
        )
        args.report_format = "sarif"
        args.report_path = args.sarif

    # Set default report path based on format
    if not args.report_path:
        args.report_path = {
            "sarif": "ai-guard.sarif",
            "json": "ai-guard.json",
            "html": "ai-guard.html",
        }[args.report_format]

    results: List[GateResult] = []
    sarif_diagnostics: List[SarifResult] = []

    # Determine changed Python files (for scoping)
    changed_py = changed_python_files(args.event)
    print(f"Changed Python files: {changed_py}")

    if args.event:
        print(f"GitHub event file: {args.event}")
        try:
            import os
            if os.path.exists(args.event):
                print(f"Event file exists, size: {os.path.getsize(args.event)} bytes")
            else:
                print("Event file does not exist")
        except Exception as e:
            print(f"Error checking event file: {e}")

    # Lint check (scoped to changed files if available)
    lint_scope = [p for p in changed_py if p.endswith(".py")] or None
    lint_gate, lint_sarif = run_lint_check(lint_scope)
    results.append(lint_gate)
    sarif_diagnostics.extend(lint_sarif)

    # Type check (scoped where possible)
    type_scope = [p for p in (lint_scope or []) if p.startswith("src/")] or None
    type_gate, mypy_sarif = run_type_check(type_scope)
    results.append(type_gate)
    sarif_diagnostics.extend(mypy_sarif)

    # Security check
    sec_gate, bandit_sarif = run_security_check()
    results.append(sec_gate)
    sarif_diagnostics.extend(bandit_sarif)

    # Coverage check
    results.append(run_coverage_check(args.min_cov))

    # Run tests if not skipped
    if not args.skip_tests:
        print("Running tests with coverage...")
        test_rc = run_pytest_with_coverage()
        results.append(GateResult("Tests", test_rc == 0))

    # Summarize
    exit_code = summarize(results)

    # Generate findings for JSON/HTML reports
    findings = _to_findings(sarif_diagnostics)

    # Generate report based on format
    if args.report_format == "sarif":
        # SARIF emission (basic run with results summary)
        # Compose SARIF run: include diagnostics plus overall gate statuses as notes
        gate_summaries: List[SarifResult] = [
            SarifResult(
                rule_id=f"gate:{r.name}",
                level=("note" if r.passed else "error"),
                message=r.details or r.name,
                locations=[make_location("README.md", 1)]  # Default location
            )
            for r in results
        ]
        write_sarif(
            args.report_path,
            SarifRun(tool_name="ai-guard", results=sarif_diagnostics + gate_summaries),
        )
    elif args.report_format == "json":
        write_json(args.report_path, results, findings)
    elif args.report_format == "html":
        write_html(args.report_path, results, findings)
    else:
        print(f"Unknown report format: {args.report_format}", file=sys.stderr)
        sys.exit(2)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
