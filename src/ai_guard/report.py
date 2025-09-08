"""Reporting and result aggregation for AI-Guard."""

from dataclasses import dataclass
from typing import List


@dataclass
class GateResult:
    """Result of a quality gate check."""

    name: str
    passed: bool
    details: str = ""
    exit_code: int = 0


def summarize(results: List[GateResult]) -> int:
    """Summarize all gate results and return overall exit code.

    Args:
        results: List of gate results

    Returns:
        0 if all gates passed, 1 if any failed
    """
    failed = [r for r in results if not r.passed]

    print("\n" + "=" * 50)
    print("AI-Guard Quality Gates Summary")
    print("=" * 50)

    for result in results:
        prefix = "✅" if result.passed else "❌"
        status = "PASSED" if result.passed else "FAILED"
        details = f" - {result.details}" if result.details else ""
        print(f"{prefix} {result.name}: {status}{details}")

    print("=" * 50)

    if failed:
        print(f"❌ {len(failed)} gate(s) failed")
        return 1
    else:
        print("✅ All gates passed!")
        return 0


class ReportGenerator:
    """Report generator for AI-Guard quality gate results."""

    def __init__(self) -> None:
        """Initialize the report generator."""

    def generate_summary(self, results: List[GateResult]) -> str:
        """Generate a summary report from gate results.

        Args:
            results: List of gate results

        Returns:
            Summary report as string
        """
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        summary = "Quality Gates Summary:\n"
        summary += f"Total: {len(results)}\n"
        summary += f"Passed: {len(passed)}\n"
        summary += f"Failed: {len(failed)}\n"

        if failed:
            summary += "\nFailed Gates:\n"
            for result in failed:
                summary += f"- {result.name}: {result.details}\n"

        return summary

    def generate_detailed_report(self, results: List[GateResult]) -> str:
        """Generate a detailed report from gate results.

        Args:
            results: List of gate results

        Returns:
            Detailed report as string
        """
        report = "AI-Guard Quality Gates Detailed Report\n"
        report += "=" * 50 + "\n\n"

        for result in results:
            status = "PASSED" if result.passed else "FAILED"
            report += f"Gate: {result.name}\n"
            report += f"Status: {status}\n"
            if result.details:
                report += f"Details: {result.details}\n"
            report += f"Exit Code: {result.exit_code}\n"
            report += "-" * 30 + "\n"

        return report
