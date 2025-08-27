"""Basic smoke tests for AI-Guard."""

import pytest


def test_smoke():
    """Basic smoke test."""
    assert True


def test_imports():
    """Test that main modules can be imported."""
    from src.ai_guard.config import Gates
    from src.ai_guard.report import GateResult, summarize
    from src.ai_guard.analyzer import main
    
    # Test Gates instantiation
    gates = Gates()
    assert gates.min_coverage == 80
    assert gates.fail_on_bandit is True
    
    # Test GateResult
    result = GateResult("test", True, "test details")
    assert result.name == "test"
    assert result.passed is True
    assert result.details == "test details"
