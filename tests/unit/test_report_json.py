"""Tests for JSON report module."""

import pytest  # noqa: F401
import json
import tempfile
import os
from src.ai_guard.report_json import write_json
from src.ai_guard.report import GateResult


class TestReportJson:
    """Test JSON report functionality."""

    def test_write_json_basic(self):
        """Test basic JSON report generation."""
        gates = [
            GateResult("Lint (flake8)", True, ""),
            GateResult("Static types (mypy)", False, "mypy not found"),
            GateResult("Coverage", True, "85% >= 80%")
        ]

        findings = [
            {
                "rule_id": "mypy:arg-type",
                "level": "error",
                "message": "Argument 1 to \"func\" has incompatible type",
                "path": "src/foo.py",
                "line": 42
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            write_json(temp_path, gates, findings)

            # Verify file was written
            assert os.path.exists(temp_path)

            # Verify content
            with open(temp_path, 'r') as f:
                content = json.load(f)

            assert content["version"] == "1.0"
            assert content["summary"]["passed"] is False  # One gate failed

            # Check gates
            assert len(content["summary"]["gates"]) == 3
            assert content["summary"]["gates"][0]["name"] == "Lint (flake8)"
            assert content["summary"]["gates"][0]["passed"] is True
            assert content["summary"]["gates"][1]["name"] == "Static types (mypy)"
            assert content["summary"]["gates"][1]["passed"] is False
            assert content["summary"]["gates"][1]["details"] == "mypy not found"

            # Check findings
            assert len(content["findings"]) == 1
            assert content["findings"][0]["rule_id"] == "mypy:arg-type"
            assert content["findings"][0]["level"] == "error"
            assert content["findings"][0]["path"] == "src/foo.py"
            assert content["findings"][0]["line"] == 42

        finally:
            os.unlink(temp_path)

    def test_write_json_all_passed(self):
        """Test JSON report when all gates pass."""
        gates = [
            GateResult("Lint (flake8)", True, ""),
            GateResult("Coverage", True, "90% >= 80%")
        ]

        findings = []  # No findings

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            write_json(temp_path, gates, findings)

            with open(temp_path, 'r') as f:
                content = json.load(f)

            assert content["summary"]["passed"] is True
            assert len(content["findings"]) == 0

        finally:
            os.unlink(temp_path)

    def test_write_json_empty_gates(self):
        """Test JSON report with no gates."""
        gates = []
        findings = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            write_json(temp_path, gates, findings)

            with open(temp_path, 'r') as f:
                content = json.load(f)

            assert content["summary"]["passed"] is True  # Empty list means all passed
            assert len(content["summary"]["gates"]) == 0
            assert len(content["findings"]) == 0

        finally:
            os.unlink(temp_path)
