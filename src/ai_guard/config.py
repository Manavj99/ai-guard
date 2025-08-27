"""Configuration for AI-Guard quality gates."""

from dataclasses import dataclass
import tomli


def load_config(path: str = "ai-guard.toml") -> "Gates":
    """Load configuration from TOML if present, fall back to defaults.

    Only a minimal subset is supported: [gates].min_coverage
    """
    try:
        with open(path, "rb") as f:
            data = tomli.load(f)
        gates = data.get("gates", {})
        min_cov = int(gates.get("min_coverage", Gates().min_coverage))
        return Gates(min_coverage=min_cov)
    except FileNotFoundError:
        return Gates()
    except Exception:
        # On parse errors, use defaults
        return Gates()


@dataclass(frozen=True)
class Gates:
    """Configuration for quality gates."""

    min_coverage: int = 80
    fail_on_bandit: bool = True
    fail_on_lint: bool = True
    fail_on_mypy: bool = True
