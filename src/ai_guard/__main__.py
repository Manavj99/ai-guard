"""CLI entry points for ai-guard."""

import sys
import argparse

from .analyzer import main as run_analyzer


def main() -> None:
    """Main CLI entry point that parses arguments and calls the analyzer."""
    parser = argparse.ArgumentParser(
        description="AI-Guard: Smart Code Quality Gatekeeper"
    )
    parser.add_argument("--min-cov", type=int, help="Override min coverage percentage")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--event", type=str, help="Path to GitHub event JSON")
    parser.add_argument(
        "--report-format",
        choices=["sarif", "json", "html"],
        default="sarif",
        help="Output format for the final report",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        help="Path to write the report. Default depends on format",
    )
    parser.add_argument(
        "--sarif",
        type=str,
        help="(Deprecated) Output SARIF file path; use --report-format/--report-path",
    )

    args = parser.parse_args()

    # Handle deprecated --sarif argument
    if args.sarif and not args.report_path:
        print(
            "[warn] --sarif is deprecated. Use --report-format sarif --report-path PATH",
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

    # Build arguments for the analyzer
    analyzer_args = [
        "--report-format",
        args.report_format,
        "--report-path",
        args.report_path,
    ]

    if args.min_cov is not None:
        analyzer_args += ["--min-cov", str(args.min_cov)]
    if args.skip_tests:
        analyzer_args += ["--skip-tests"]
    if args.event:
        analyzer_args += ["--event", args.event]

    # Set sys.argv for the analyzer
    sys.argv = [sys.argv[0]] + analyzer_args
    run_analyzer()


if __name__ == "__main__":
    main()
