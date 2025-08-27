"""CLI entry points for ai-guard."""

from typing import Optional
import sys
import typer

from .analyzer import main as run_analyzer


app = typer.Typer(help="AI-Guard: Smart Code Quality Gatekeeper")


@app.callback()
def callback() -> None:
    """ai-guard CLI."""


@app.command("check")
def check(
    min_cov: Optional[int] = typer.Option(None, help="Override min coverage %"),
    skip_tests: bool = typer.Option(False, help="Skip running tests"),
    event: Optional[str] = typer.Option(None, help="Path to GitHub event JSON"),
    sarif: str = typer.Option("ai-guard.sarif", help="Output SARIF path"),
) -> None:
    """Run quality gates using analyzer with optional overrides."""
    args = ["--sarif", sarif]
    if min_cov is not None:
        args += ["--min-cov", str(min_cov)]
    if skip_tests:
        args += ["--skip-tests"]
    if event:
        args += ["--event", event]

    sys.argv = [sys.argv[0]] + args
    run_analyzer()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
