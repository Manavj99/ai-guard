"""Main analyzer that orchestrates all quality gate checks."""

import argparse
import subprocess
import sys
from typing import List

from .config import Gates
from .report import GateResult, summarize
from .tests_runner import run_pytest_with_coverage
from .security_scanner import run_bandit


def cov_percent() -> int:
    """Parse coverage.xml and return percentage.
    
    Returns:
        Coverage percentage as integer
    """
    import xml.etree.ElementTree as ET
    
    try:
        tree = ET.parse("coverage.xml")
        rate = float(tree.getroot().attrib.get("line-rate", "0"))
        return int(round(rate * 100))
    except Exception:
        return 0


def run_lint_check() -> GateResult:
    """Run flake8 linting check.
    
    Returns:
        GateResult for linting
    """
    try:
        rc = subprocess.call(["flake8", "src", "tests"])
        return GateResult("Lint (flake8)", rc == 0)
    except FileNotFoundError:
        return GateResult("Lint (flake8)", False, "flake8 not found")


def run_type_check() -> GateResult:
    """Run mypy type checking.
    
    Returns:
        GateResult for type checking
    """
    try:
        rc = subprocess.call(["mypy", "src"])
        return GateResult("Static types (mypy)", rc == 0)
    except FileNotFoundError:
        return GateResult("Static types (mypy)", False, "mypy not found")


def run_security_check() -> GateResult:
    """Run bandit security scan.
    
    Returns:
        GateResult for security scanning
    """
    try:
        rc = run_bandit()
        return GateResult("Security (bandit)", rc == 0)
    except FileNotFoundError:
        return GateResult("Security (bandit)", False, "bandit not found")


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
    parser.add_argument("--min-cov", type=int, default=Gates().min_coverage,
                       help=f"Minimum coverage percentage (default: {Gates().min_coverage})")
    parser.add_argument("--skip-tests", action="store_true",
                       help="Skip running tests (useful for CI)")
    args = parser.parse_args()

    results: List[GateResult] = []

    # Lint check
    results.append(run_lint_check())

    # Type check
    results.append(run_type_check())

    # Security check
    results.append(run_security_check())

    # Coverage check
    results.append(run_coverage_check(args.min_cov))

    # Run tests if not skipped
    if not args.skip_tests:
        print("Running tests with coverage...")
        test_rc = run_pytest_with_coverage()
        results.append(GateResult("Tests", test_rc == 0))

    # Summarize and exit
    exit_code = summarize(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
