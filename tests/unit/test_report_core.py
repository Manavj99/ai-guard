"""Core tests for report module to improve coverage."""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any

from src.ai_guard.report import GateResult, summarize


class TestGateResult:
    """Test GateResult dataclass."""
    
    def test_gate_result_creation(self):
        """Test GateResult creation."""
        gate = GateResult(
            name="Test Gate",
            passed=True,
            details="All tests passed"
        )
        assert gate.name == "Test Gate"
        assert gate.passed is True
        assert gate.details == "All tests passed"
    
    def test_gate_result_failed(self):
        """Test GateResult with failure."""
        gate = GateResult(
            name="Test Gate",
            passed=False,
            details="Some tests failed"
        )
        assert gate.name == "Test Gate"
        assert gate.passed is False
        assert gate.details == "Some tests failed"
    
    def test_gate_result_empty_details(self):
        """Test GateResult with empty details."""
        gate = GateResult(
            name="Test Gate",
            passed=True,
            details=""
        )
        assert gate.name == "Test Gate"
        assert gate.passed is True
        assert gate.details == ""


class TestSummarize:
    """Test summarize function."""
    
    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        gates = [
            GateResult("Lint (flake8)", True, ""),
            GateResult("Static types (mypy)", True, ""),
            GateResult("Security (bandit)", True, ""),
            GateResult("Coverage", True, "85% >= 80%")
        ]
        
        result = summarize(gates)
        assert result["passed"] is True
        assert len(result["gates"]) == 4
        assert all(gate["passed"] for gate in result["gates"])
    
    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        gates = [
            GateResult("Lint (flake8)", False, "E501 line too long"),
            GateResult("Static types (mypy)", True, ""),
            GateResult("Security (bandit)", True, ""),
            GateResult("Coverage", False, "75% < 80%")
        ]
        
        result = summarize(gates)
        assert result["passed"] is False
        assert len(result["gates"]) == 4
        assert result["gates"][0]["passed"] is False
        assert result["gates"][1]["passed"] is True
        assert result["gates"][2]["passed"] is True
        assert result["gates"][3]["passed"] is False
    
    def test_summarize_all_failed(self):
        """Test summarize with all gates failed."""
        gates = [
            GateResult("Lint (flake8)", False, "Multiple errors"),
            GateResult("Static types (mypy)", False, "Type errors"),
            GateResult("Security (bandit)", False, "Security issues"),
            GateResult("Coverage", False, "Low coverage")
        ]
        
        result = summarize(gates)
        assert result["passed"] is False
        assert len(result["gates"]) == 4
        assert all(not gate["passed"] for gate in result["gates"])
    
    def test_summarize_empty_gates(self):
        """Test summarize with no gates."""
        gates = []
        
        result = summarize(gates)
        assert result["passed"] is True  # Empty gates should pass
        assert len(result["gates"]) == 0
    
    def test_summarize_single_gate(self):
        """Test summarize with single gate."""
        gates = [
            GateResult("Single Gate", True, "Passed")
        ]
        
        result = summarize(gates)
        assert result["passed"] is True
        assert len(result["gates"]) == 1
        assert result["gates"][0]["name"] == "Single Gate"
        assert result["gates"][0]["passed"] is True
        assert result["gates"][0]["details"] == "Passed"
    
    def test_summarize_mixed_results(self):
        """Test summarize with mixed results."""
        gates = [
            GateResult("Gate 1", True, "Passed"),
            GateResult("Gate 2", False, "Failed"),
            GateResult("Gate 3", True, "Passed"),
            GateResult("Gate 4", False, "Failed")
        ]
        
        result = summarize(gates)
        assert result["passed"] is False  # Any failure should make overall fail
        assert len(result["gates"]) == 4
        assert result["gates"][0]["passed"] is True
        assert result["gates"][1]["passed"] is False
        assert result["gates"][2]["passed"] is True
        assert result["gates"][3]["passed"] is False
    
    def test_summarize_gate_structure(self):
        """Test that summarize returns correct gate structure."""
        gates = [
            GateResult("Test Gate", True, "Test details")
        ]
        
        result = summarize(gates)
        gate = result["gates"][0]
        
        # Check that gate has expected structure
        assert "name" in gate
        assert "passed" in gate
        assert "details" in gate
        assert gate["name"] == "Test Gate"
        assert gate["passed"] is True
        assert gate["details"] == "Test details"
    
    def test_summarize_preserves_details(self):
        """Test that summarize preserves gate details."""
        gates = [
            GateResult("Gate 1", True, "Detail 1"),
            GateResult("Gate 2", False, "Detail 2 with special chars: !@#$%"),
            GateResult("Gate 3", True, "Detail 3 with\nnewlines")
        ]
        
        result = summarize(gates)
        assert result["gates"][0]["details"] == "Detail 1"
        assert result["gates"][1]["details"] == "Detail 2 with special chars: !@#$%"
        assert result["gates"][2]["details"] == "Detail 3 with\nnewlines"
