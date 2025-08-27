"""Configuration for AI-Guard quality gates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Gates:
    """Configuration for quality gates."""
    
    min_coverage: int = 80
    fail_on_bandit: bool = True
    fail_on_lint: bool = True
    fail_on_mypy: bool = True
