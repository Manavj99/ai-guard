"""Optimized analyzer that orchestrates all quality gate checks with performance improvements."""

import argparse
import os
import subprocess
import re
import json
import sys
import defusedxml.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Callable
from enum import Enum
import functools

from .config import load_config
from .report import GateResult, summarize
from .diff_parser import changed_python_files
from .sarif_report import SarifRun, SarifResult, write_sarif, make_location
from .tests_runner import run_pytest_with_coverage
from .report_json import write_json
from .report_html import write_html
from .generators.enhanced_testgen import EnhancedTestGenerator, TestGenConfig
from .pr_annotations import PRAnnotator
from .performance import (
    time_function,
    cached,
    parallel_execute,
    get_cache,
    get_performance_summary,
)


# Rule ID formatting helpers
class RuleIdStyle(str, Enum):
    BARE = "bare"  # "E501", "name-defined", "B101"
    TOOL = "tool"  # "flake8:E501", "mypy:name-defined", "bandit:B101"


@cached(ttl_seconds=300)  # Cache for 5 minutes
def _rule_style() -> RuleIdStyle:
    v = os.getenv("AI_GUARD_RULE_ID_STYLE", "bare").strip().lower()
    return RuleIdStyle.TOOL if v == "tool" else RuleIdStyle.BARE


def _make_rule_id(tool: str, code: str | None) -> str:
    code = (code or "").strip() or tool
    return f"{tool}:{code}" if _rule_style() == RuleIdStyle.TOOL else code


@cached(ttl_seconds=300)
def _strict_subprocess_fail() -> bool:
    return os.getenv("AI_GUARD_STRICT_SUBPROCESS_ERRORS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _to_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (bytes, bytearray)):
        return x.decode("utf-8", errors="replace")
    return str(x)


# Dataclasses for SARIF result objects
@dataclass
class ArtifactLocation:
    uri: str


@dataclass
class Region:
    start_line: Optional[int] = None
    start_column: Optional[int] = None


@dataclass
class PhysicalLocation:
    artifact_location: ArtifactLocation
    region: Optional[Region] = None


@dataclass
class Location:
    physical_location: PhysicalLocation


# Default gates configuration
default_gates = {"min_coverage": 80}


def _normalize_rule_id(rule_id: str) -> str:
    """Remove tool prefix from rule ID if present."""
    if ":" in rule_id:
        return rule_id.split(":", 1)[1]
    return rule_id


def _norm(s: str | bytes | None) -> str:
    """Normalize string/bytes to string."""
    if s is None:
        return ""
    if isinstance(s, (bytes, bytearray)):
        return s.decode("utf-8", errors="replace")
    return s


@time_function
@cached(ttl_seconds=60)  # Cache coverage results for 1 minute
def _coverage_percent_from_xml(xml_path: str | None = None) -> int | None:
    """Parse coverage.xml and return percentage.

    Args:
        xml_path: Optional path to coverage XML file

    Returns:
        Coverage percentage as integer, or None if parsing fails
    """
    try:
        # Try current dir then one level up (your tests use both)
        candidates = [xml_path] if xml_path else ["coverage.xml", "../coverage.xml"]
        for p in filter(None, candidates):
            if not os.path.exists(p):
                continue
            tree = ET.parse(p)
            root = tree.getroot()

            # Cobertura style: <coverage line-rate="0.86" ...>
            line_rate = root.attrib.get("line-rate")
            if line_rate is not None:
                try:
                    return round(float(line_rate) * 100)
                except ValueError:
                    pass

            # Alternative counters: <counter type="LINE" covered="xx" missed="yy" />
            total_covered = total_missed = 0
            for counter in root.findall(".//counter"):
                if counter.attrib.get("type", "").upper() == "LINE":
                    c = int(counter.attrib.get("covered", 0))
                    m = int(counter.attrib.get("missed", 0))
                    total_covered += c
                    total_missed += m
            total = total_covered + total_missed
            if total > 0:
                return round((total_covered / total) * 100)

        return None
    except Exception:
        return None


# Backward compatibility alias
def cov_percent() -> int:
    """Parse coverage.xml and return percentage.

    Returns:
        Coverage percentage as integer
    """
    result = _coverage_percent_from_xml()
    return int(result) if result is not None else 0


@time_function
def _parse_flake8_output(text: str) -> List[SarifResult]:
    """
    Parse Flake8 findings from text output and return a list of SarifResult objects.
    Format: file:line:col: CODE message...
    """
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return []

    results = []
    for ln in lines:
        m = re.match(
            r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s*"
            r"(?P<code>[A-Za-z]\w{2,5})\s+(?P<msg>.+)$",
            ln.strip(),
        )
        if not m:
            continue

        file = m["file"]
        line = int(m["line"])
        col = int(m["col"])
        code = m["code"]
        msg = m["msg"].strip()

        loc = {
            "physicalLocation": {
                "artifactLocation": {"uri": file},
                "region": {"startLine": line, "startColumn": col},
            }
        }
        results.append(
            SarifResult(
                rule_id=_make_rule_id("flake8", code),
                message=msg,
                locations=[loc],
                level="warning",
            )
        )

    return results


@time_function
def _parse_mypy_output(text: str) -> List[SarifResult]:
    """
    Parse MyPy errors from text output and return a list of SarifResult objects.
    Supports optional column and bracketed code [name-defined].
    """
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return []

    results = []
    for ln in lines:
        # file:line(:col)?: severity: message [code]
        pattern = (
            r"^(?P<file>[^:]+):(?P<line>\d+)(?::(?P<col>\d+))?:\s*"
            r"(?P<sev>\w+):\s*(?P<msg>.+?)(?:\s*\[(?P<code>[^\]]+)\])?$"
        )
        m = re.match(pattern, ln.strip())
        if not m:
            continue
        if m["sev"].lower() not in {"error", "note", "warning"}:
            continue
        code = (m["code"] or "").strip()
        file = m["file"]
        line = int(m["line"])
        col = int(m["col"]) if m["col"] else None
        msg = m["msg"].strip()
        severity = m["sev"].lower()

        # If there's a bracketed code, use it as the rule ID (bare format)
        # If no bracketed code, use "mypy-error" with tool prefix
        if code:
            rule_id = code  # Bare format for bracketed codes
        else:
            rule_id = _make_rule_id("mypy", "mypy-error")  # Tool format for no code

        loc = {
            "physicalLocation": {
                "artifactLocation": {"uri": file},
                "region": {"startLine": line, "startColumn": col},
            }
        }
        results.append(
            SarifResult(
                rule_id=rule_id,
                message=msg,
                locations=[loc],
                level=severity,
            )
        )

    return results


@time_function
def _run_subprocess_optimized(
    cmd: List[str], timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    """Run subprocess with timeout and error handling."""
    from .utils.subprocess_runner import run_cmd, ToolExecutionError

    try:
        returncode, output = run_cmd(cmd, timeout=timeout)
        # Create a CompletedProcess-like object for backward compatibility

        class SuccessProcessResult(subprocess.CompletedProcess[str]):
            def __init__(self, args: List[str], returncode: int, stdout: str, stderr: str = ""):
                super().__init__(args, returncode, stdout, stderr)

        return SuccessProcessResult(cmd, returncode, output)
    except ToolExecutionError as e:
        # Return a failed process result
        class ErrorProcessResult(subprocess.CompletedProcess[str]):
            def __init__(self, args: List[str], returncode: int, stdout: str, stderr: str = ""):
                super().__init__(args, returncode, stdout, stderr)

        return ErrorProcessResult(cmd, 1, "", str(e))


@time_function
def run_lint_check(paths: list[str] | None) -> tuple[GateResult, SarifResult | None]:
    cmd = ["flake8"] + (paths or [])
    proc = _run_subprocess_optimized(cmd)

    if proc.returncode == 127:  # Command not found
        return GateResult("Lint (flake8)", False, "flake8 not found", 0), None

    combined = _to_text(proc.stdout) + "\n" + _to_text(proc.stderr)

    sarif_results = _parse_flake8_output(combined)
    first_result = sarif_results[0] if sarif_results else None

    # If non-zero AND we did parse a finding → fail with the finding message.
    if proc.returncode != 0 and first_result is not None:
        return GateResult("Lint (flake8)", False, first_result.message, 0), first_result

    # If non-zero AND no parseable output → treat as tool error and show stderr.
    if proc.returncode != 0 and (first_result is None):
        details = ("flake8 error: " + _to_text(proc.stderr).strip()) or "flake8 error"
        return GateResult("Lint (flake8)", False, details, 0), None

    # Zero returncode → pass
    details = "No issues" if first_result is None else first_result.message
    return GateResult("Lint (flake8)", True, details, 0), first_result


@time_function
def run_type_check(paths: list[str] | None) -> tuple[GateResult, SarifResult | None]:
    cmd = ["mypy"] + (paths or [])
    proc = _run_subprocess_optimized(cmd, timeout=60)  # Longer timeout for mypy

    if proc.returncode == 127:  # Command not found
        return GateResult("Static types (mypy)", False, "mypy not found", 0), None

    combined = _to_text(proc.stdout) + "\n" + _to_text(proc.stderr)

    sarif_results = _parse_mypy_output(combined)
    first_result = sarif_results[0] if sarif_results else None

    if proc.returncode != 0 and first_result is not None:
        return (
            GateResult("Static types (mypy)", False, first_result.message, 0),
            first_result,
        )

    if proc.returncode != 0 and (first_result is None):
        details = ("mypy error: " + _to_text(proc.stderr).strip()) or "mypy error"
        return GateResult("Static types (mypy)", False, details, 0), None

    details = "No issues" if first_result is None else first_result.message
    return GateResult("Static types (mypy)", True, details, 0), first_result


@time_function
def _parse_bandit_json(output: Any) -> List[SarifResult]:
    """
    Parse Bandit results from JSON output (string/bytes/other) and return a list of
    SarifResult objects.
    """
    if isinstance(output, (bytes, bytearray)):
        output = output.decode("utf-8", errors="replace")
    elif not isinstance(output, str):
        output = str(output)

    try:
        data = json.loads(output or "{}")
    except Exception:
        return []

    results = (data or {}).get("results") or []
    if not results:
        return []

    sarif_results = []
    for r in results:
        file = r.get("filename", "unknown.py")
        line = int(r.get("line_number", 1))
        msg = r.get("issue_text", "").strip()
        code = (r.get("test_id") or r.get("test_name") or "bandit").strip()

        loc = {
            "physicalLocation": {
                "artifactLocation": {"uri": file},
                "region": {"startLine": line},
            }
        }
        sarif_results.append(
            SarifResult(
                rule_id=_make_rule_id("bandit", code),
                level="warning",
                message=msg,
                locations=[loc],
            )
        )

    return sarif_results


def _parse_bandit_output(output: str) -> List[SarifResult]:
    """Parse Bandit's output into SARIF results.

    This is an alias for _parse_bandit_json for backward compatibility.
    """
    return _parse_bandit_json(output)  # type: ignore[no-any-return]


@time_function
def run_security_check() -> tuple[GateResult, SarifResult | None]:
    cmd = ["bandit", "-q", "-r", "src", "-f", "json", "-c", ".bandit"]
    proc = _run_subprocess_optimized(cmd, timeout=45)  # Longer timeout for bandit

    if proc.returncode == 127:  # Command not found
        return GateResult("Security (bandit)", False, "bandit not found", 0), None

    stdout = _to_text(proc.stdout)
    stderr = _to_text(proc.stderr)

    sarif_results = _parse_bandit_json(stdout)
    first_result = sarif_results[0] if sarif_results else None

    if proc.returncode != 0 and first_result is not None:
        return (
            GateResult("Security (bandit)", False, first_result.message, 0),
            first_result,
        )

    if proc.returncode != 0 and (first_result is None):
        details = ("bandit error: " + stderr.strip()) or "bandit error"
        return GateResult("Security (bandit)", False, details, 0), None

    # If zero and no results, it's a pass
    details = "No issues" if first_result is None else first_result.message
    passed = first_result is None  # bandit zero typically means nothing found
    return GateResult("Security (bandit)", passed, details, 0), first_result


@time_function
def _to_findings(
    sarif_results: List[SarifResult],
) -> List[Dict[str, Union[str, int, None]]]:
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
            if isinstance(loc, dict) and "physicalLocation" in loc:
                if "artifactLocation" in loc["physicalLocation"]:
                    path = loc["physicalLocation"]["artifactLocation"].get(
                        "uri", "unknown"
                    )
                if "region" in loc["physicalLocation"]:
                    line = loc["physicalLocation"]["region"].get("startLine")
            elif hasattr(loc, "physical_location") and hasattr(
                loc.physical_location, "artifact_location"
            ):
                path = loc.physical_location.artifact_location.uri
                if (
                    hasattr(loc.physical_location, "region")
                    and loc.physical_location.region
                ):
                    line = loc.physical_location.region.start_line

        out.append(
            {
                "rule_id": r.rule_id,
                "level": r.level,
                "message": r.message,
                "path": path,
                "line": line,
            }
        )
    return out


@time_function
def run_coverage_check(
    min_coverage: int | None, xml_path: str | None = None
) -> GateResult:
    """Run coverage check.

    Args:
        min_coverage: Minimum required coverage percentage
        xml_path: Optional path to coverage XML file

    Returns:
        GateResult for coverage
    """
    # Use the backward compatibility function for existing tests
    pct = cov_percent()
    if pct is None:
        return GateResult(
            name="Coverage",
            passed=False if (min_coverage is not None and min_coverage > 0) else False,
            details="No coverage data",
            exit_code=0,
        )

    # If min_coverage is None, don't enforce a threshold—report informationally.
    if min_coverage is None:
        return GateResult(
            name="Coverage",
            passed=True,  # informational pass
            details=f"{pct}% (no minimum set)",
            exit_code=0,
        )

    passed = pct >= min_coverage
    return GateResult(
        name="Coverage",
        passed=passed,
        details=f"{pct}% >= {min_coverage}%",
        exit_code=0,
    )


def _run_quality_checks_parallel(
    changed_py: List[str],
) -> tuple[List[GateResult], List[SarifResult]]:
    """Run quality checks in parallel for better performance."""
    results = []
    sarif_diagnostics = []

    # Prepare functions for parallel execution
    functions_to_run: List[Callable[..., Any]] = []

    # Lint check (scoped to changed files if available)
    lint_scope = [p for p in changed_py if p.endswith(".py")] or None
    if lint_scope:
        functions_to_run.append(functools.partial(run_lint_check, lint_scope))

    # Type check (scoped where possible)
    type_scope = [p for p in (lint_scope or []) if p.startswith("src/")] or None
    if type_scope:
        functions_to_run.append(functools.partial(run_type_check, type_scope))

    # Security check (always run)
    functions_to_run.append(run_security_check)

    # Run functions in parallel
    parallel_results = parallel_execute(functions_to_run, max_workers=3, timeout=120)

    # Process results
    for i, result in enumerate(parallel_results):
        if result is None:
            continue

        if i < len(functions_to_run) - 1:  # Lint and type checks
            gate_result, sarif_result = result
            results.append(gate_result)
            if sarif_result:
                sarif_diagnostics.append(sarif_result)
        else:  # Security check
            gate_result, sarif_result = result
            results.append(gate_result)
            if sarif_result:
                sarif_diagnostics.append(sarif_result)

    return results, sarif_diagnostics


@time_function
def run(argv: list[str] | None = None) -> int:
    """Run the optimized analyzer with given arguments.

    Args:
        argv: Optional command line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="AI-Guard Quality Gate Analyzer (Optimized)"
    )
    config = load_config()
    parser.add_argument(
        "--min-cov",
        type=int,
        default=config.get("min_coverage", 80),
        help=(
            f"Minimum coverage percentage "
            f"(default: {config.get('min_coverage', 80)})"
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
        help="Output format for the final report",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default=None,
        help="Path to write the report. Default depends on format",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel execution of quality checks",
    )
    parser.add_argument(
        "--performance-report", action="store_true", help="Generate performance report"
    )
    # Back-compat:
    parser.add_argument(
        "--sarif",
        type=str,
        default=None,
        help=(
            "(Deprecated) Output SARIF file path; " "use --report-format/--report-path"
        ),
    )
    parser.add_argument(
        "--enhanced-testgen",
        action="store_true",
        help="Enable enhanced test generation with LLM integration",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic", "local"],
        default="openai",
        help="LLM provider for test generation",
    )
    parser.add_argument(
        "--llm-api-key", type=str, default=None, help="API key for LLM provider"
    )
    parser.add_argument(
        "--pr-annotations",
        action="store_true",
        help="Generate PR annotations for better GitHub integration",
    )
    parser.add_argument(
        "--annotations-output",
        type=str,
        default="annotations.json",
        help="Output file for PR annotations",
    )
    args = parser.parse_args(argv)

    # Handle deprecated --sarif argument
    if args.sarif and not args.report_path:
        print(
            "[warn] --sarif is deprecated. Use --report-format sarif "
            "--report-path PATH",
            file=sys.stderr,
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
            if os.path.exists(args.event):
                print(f"Event file exists, size: {os.path.getsize(args.event)} bytes")
            else:
                print("Event file does not exist")
        except Exception as e:
            print(f"Error checking event file: {e}")

    # Run quality checks (parallel or sequential)
    if args.parallel and changed_py:
        print("🚀 Running quality checks in parallel...")
        quality_results, quality_sarif = _run_quality_checks_parallel(changed_py)
        results.extend(quality_results)
        sarif_diagnostics.extend(quality_sarif)
    else:
        # Sequential execution (original behavior)
        # Lint check (scoped to changed files if available)
        lint_scope = [p for p in changed_py if p.endswith(".py")] or None
        lint_gate, lint_sarif = run_lint_check(lint_scope)
        results.append(lint_gate)
        if lint_sarif:
            sarif_diagnostics.append(lint_sarif)

        # Type check (scoped where possible)
        type_scope = [p for p in (lint_scope or []) if p.startswith("src/")] or None
        type_gate, mypy_sarif = run_type_check(type_scope)
        results.append(type_gate)
        if mypy_sarif:
            sarif_diagnostics.append(mypy_sarif)

        # Security check
        sec_gate, bandit_sarif = run_security_check()
        results.append(sec_gate)
        if bandit_sarif:
            sarif_diagnostics.append(bandit_sarif)

    # Coverage check
    results.append(run_coverage_check(args.min_cov))

    # Enhanced test generation (if enabled)
    if args.enhanced_testgen and changed_py:
        print("🔧 Running enhanced test generation...")
        try:
            # Initialize enhanced test generator
            testgen_config = TestGenConfig(
                llm_provider=args.llm_provider,
                llm_api_key=args.llm_api_key,
                llm_model=(
                    "gpt-4"
                    if args.llm_provider == "openai"
                    else "claude-3-sonnet-20240229"
                ),
            )

            testgen = EnhancedTestGenerator(testgen_config)

            # Generate tests for changed files
            test_content = testgen.generate_tests(changed_py, args.event)

            if test_content:
                # Write generated tests
                test_output_path = "tests/unit/test_generated_enhanced.py"

                Path(test_output_path).parent.mkdir(parents=True, exist_ok=True)

                with open(test_output_path, "w", encoding="utf-8") as f:
                    f.write(test_content)

                print(f"✅ Enhanced tests generated: {test_output_path}")
                results.append(
                    GateResult(
                        "Enhanced Test Generation",
                        True,
                        f"Generated tests for {len(changed_py)} files",
                    )
                )
            else:
                print("ℹ️ No enhanced tests generated")
                results.append(
                    GateResult("Enhanced Test Generation", True, "No tests needed")
                )

        except Exception as e:
            print(f"⚠️ Enhanced test generation failed: {e}")
            results.append(
                GateResult("Enhanced Test Generation", False, f"Generation failed: {e}")
            )

    # PR Annotations (if enabled)
    if args.pr_annotations:
        print("📝 Generating PR annotations...")
        try:
            # Initialize PR annotator
            annotator = PRAnnotator()

            # Add lint issues
            for sarif_result in sarif_diagnostics:
                if sarif_result.rule_id.startswith("flake8:"):
                    lint_issues = []
                    if sarif_result.locations and len(sarif_result.locations) > 0:
                        location = sarif_result.locations[0]
                        if (
                            isinstance(location, dict)
                            and "physicalLocation" in location
                        ):
                            lint_issues.append(
                                {
                                    "file": location["physicalLocation"][
                                        "artifactLocation"
                                    ]["uri"],
                                    "line": location["physicalLocation"]["region"].get(
                                        "startLine", 0
                                    ),
                                    "column": location["physicalLocation"][
                                        "region"
                                    ].get("startColumn", 0),
                                    "severity": sarif_result.level,
                                    "message": sarif_result.message,
                                    "rule": sarif_result.rule_id,
                                }
                            )
                    annotator.add_lint_issues(lint_issues)

            # Generate and save annotations
            summary = annotator.generate_review_summary()
            annotator.save_annotations(args.annotations_output)

            print(f"✅ PR annotations generated: {args.annotations_output}")
            print(f"📊 Review status: {summary.overall_status}")
            print(f"🎯 Quality score: {summary.quality_score:.1%}")

            results.append(
                GateResult(
                    "PR Annotations",
                    True,
                    f"Generated {len(summary.annotations)} annotations",
                )
            )

        except Exception as e:
            print(f"⚠️ PR annotation generation failed: {e}")
            results.append(
                GateResult("PR Annotations", False, f"Generation failed: {e}")
            )

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
                locations=[make_location("README.md", 1)],  # Default location
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

    # Generate performance report if requested
    if args.performance_report:
        perf_summary = get_performance_summary()
        print("\n📊 Performance Summary:")
        print(f"  Total metrics recorded: {perf_summary['total_metrics']}")
        print(f"  Cache size: {perf_summary['cache_size']}")
        print(f"  Functions tracked: {perf_summary['functions_tracked']}")
        if perf_summary["average_times"]:
            print("  Average execution times:")
            for func, avg_time in perf_summary["average_times"].items():
                print(f"    {func}: {avg_time:.3f}s")

    return exit_code


def main() -> None:
    """Main entry point for AI-Guard optimized analyzer."""
    import sys

    sys.exit(run())


class OptimizedCodeAnalyzer:
    """Optimized code analyzer class for orchestrating quality gate checks."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the optimized code analyzer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or load_config()

    @time_function
    def run_all_checks(
        self, paths: Optional[List[str]] = None, parallel: bool = True
    ) -> List[GateResult]:
        """Run all quality gate checks with optional parallel execution.

        Args:
            paths: Optional list of paths to check
            parallel: Whether to run checks in parallel

        Returns:
            List of gate results
        """
        results = []

        if parallel and paths:
            # Run checks in parallel
            quality_results, _ = _run_quality_checks_parallel(paths)
            results.extend(quality_results)
        else:
            # Sequential execution
            # Run lint check
            lint_result, _ = run_lint_check(paths)
            results.append(lint_result)

            # Run type check
            type_result, _ = run_type_check(paths)
            results.append(type_result)

            # Run security check
            security_result, _ = run_security_check()
            results.append(security_result)

        # Run coverage check
        min_coverage = self.config.get("min_coverage", 80)
        coverage_result = run_coverage_check(min_coverage)
        results.append(coverage_result)

        return results

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the analyzer."""
        return get_performance_summary()

    def clear_cache(self) -> None:
        """Clear the performance cache."""
        get_cache().clear()


if __name__ == "__main__":
    main()
