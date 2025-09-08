"""Basic tests for report.py."""

from ai_guard.report import GateResult, summarize


def test_gate_result_creation():
    """Test GateResult creation."""
    result = GateResult(
        name="test", passed=True, message="Test passed", details="Test details"
    )
    assert result.name == "test"
    assert result.passed is True
    assert result.message == "Test passed"
    assert result.details == "Test details"


def test_gate_result_failed():
    """Test GateResult for failed gate."""
    result = GateResult(
        name="test", passed=False, message="Test failed", details="Test failure details"
    )
    assert result.name == "test"
    assert result.passed is False
    assert result.message == "Test failed"


def test_summarize_basic():
    """Test basic summarize function."""
    results = [
        GateResult("test1", True, "Passed", ""),
        GateResult("test2", False, "Failed", ""),
    ]

    summary = summarize(results)
    assert summary is not None
    assert "test1" in summary
    assert "test2" in summary


def test_summarize_empty():
    """Test summarize with empty results."""
    summary = summarize([])
    assert summary is not None
