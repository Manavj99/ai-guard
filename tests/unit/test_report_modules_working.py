"""Working comprehensive tests for report modules."""

import pytest
import json
import tempfile
from unittest.mock import patch

from ai_guard.report import GateResult, summarize
from ai_guard.report_json import write_json
from ai_guard.report_html import write_html


class TestReportModulesWorking:
    """Working comprehensive tests for report modules functionality."""

    def test_gate_result_creation(self):
        """Test GateResult dataclass creation."""
        result = GateResult(
            name="test-gate", passed=True, details="Test passed successfully"
        )

        assert result.name == "test-gate"
        assert result.passed is True
        assert result.details == "Test passed successfully"

    def test_gate_result_failed(self):
        """Test GateResult with failed status."""
        result = GateResult(
            name="test-gate", passed=False, details="Test failed with errors"
        )

        assert result.name == "test-gate"
        assert result.passed is False
        assert result.details == "Test failed with errors"

    def test_summarize_all_passed(self):
        """Test summarize with all gates passed."""
        gates = [
            GateResult("lint", True, "No linting issues"),
            GateResult("type", True, "No type errors"),
            GateResult("security", True, "No security issues"),
            GateResult("coverage", True, "Coverage: 85%"),
        ]

        summary = summarize(gates)

        assert summary.passed is True
        assert len(summary.gates) == 4
        assert all(gate.passed for gate in summary.gates)

    def test_summarize_some_failed(self):
        """Test summarize with some gates failed."""
        gates = [
            GateResult("lint", True, "No linting issues"),
            GateResult("type", False, "Type errors found"),
            GateResult("security", True, "No security issues"),
            GateResult("coverage", False, "Coverage: 75% (below 80%)"),
        ]

        summary = summarize(gates)

        assert summary.passed is False
        assert len(summary.gates) == 4
        assert summary.gates[0].passed is True
        assert summary.gates[1].passed is False
        assert summary.gates[2].passed is True
        assert summary.gates[3].passed is False

    def test_summarize_empty_gates(self):
        """Test summarize with empty gates list."""
        summary = summarize([])

        assert summary.passed is True
        assert len(summary.gates) == 0

    def test_write_json(self):
        """Test write_json function."""
        gates = [
            GateResult("lint", True, "No linting issues"),
            GateResult("coverage", False, "Coverage: 75%"),
        ]
        findings = [
            {
                "rule_id": "flake8:E302",
                "level": "warning",
                "message": "expected 2 blank lines",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            write_json(gates, findings, output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                written_data = json.load(f)
                assert written_data["version"] == "1.0"
                assert written_data["summary"]["passed"] is False
                assert len(written_data["summary"]["gates"]) == 2
                assert len(written_data["findings"]) == 1
        finally:
            import os

            os.unlink(output_path)

    def test_write_json_error(self):
        """Test write_json with write error."""
        gates = [GateResult("test", True, "Test")]
        findings = []

        with patch("builtins.open", side_effect=IOError("Write error")):
            with pytest.raises(IOError):
                write_json(gates, findings, "test.json")

    def test_write_html(self):
        """Test write_html function."""
        gates = [
            GateResult("lint", True, "No linting issues"),
            GateResult("coverage", False, "Coverage: 75%"),
        ]
        findings = [
            {
                "rule_id": "flake8:E302",
                "level": "warning",
                "message": "expected 2 blank lines",
                "path": "src/test.py",
                "line": 10,
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
            output_path = f.name

        try:
            write_html(gates, findings, output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "AI-Guard Report" in content
                assert "lint" in content
                assert "coverage" in content
                assert "flake8:E302" in content
        finally:
            import os

            os.unlink(output_path)

    def test_write_html_error(self):
        """Test write_html with write error."""
        gates = [GateResult("test", True, "Test")]
        findings = []

        with patch("builtins.open", side_effect=IOError("Write error")):
            with pytest.raises(IOError):
                write_html(gates, findings, "test.html")

    def test_write_json_empty_data(self):
        """Test write_json with empty data."""
        gates = []
        findings = []

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            write_json(gates, findings, output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                written_data = json.load(f)
                assert written_data["version"] == "1.0"
                assert written_data["summary"]["passed"] is True
                assert len(written_data["summary"]["gates"]) == 0
                assert len(written_data["findings"]) == 0
        finally:
            import os

            os.unlink(output_path)

    def test_write_html_empty_data(self):
        """Test write_html with empty data."""
        gates = []
        findings = []

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
            output_path = f.name

        try:
            write_html(gates, findings, output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "AI-Guard Report" in content
        finally:
            import os

            os.unlink(output_path)

    def test_write_json_large_findings(self):
        """Test write_json with large number of findings."""
        gates = [GateResult("test", True, "Test")]
        findings = [
            {
                "rule_id": f"rule-{i}",
                "level": "warning",
                "message": f"Message {i}",
                "path": f"src/file{i}.py",
                "line": i,
            }
            for i in range(100)
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            write_json(gates, findings, output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                written_data = json.load(f)
                assert len(written_data["findings"]) == 100
        finally:
            import os

            os.unlink(output_path)

    def test_write_html_large_findings(self):
        """Test write_html with large number of findings."""
        gates = [GateResult("test", True, "Test")]
        findings = [
            {
                "rule_id": f"rule-{i}",
                "level": "warning",
                "message": f"Message {i}",
                "path": f"src/file{i}.py",
                "line": i,
            }
            for i in range(50)
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
            output_path = f.name

        try:
            write_html(gates, findings, output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "rule-0" in content
                assert "rule-49" in content
        finally:
            import os

            os.unlink(output_path)
