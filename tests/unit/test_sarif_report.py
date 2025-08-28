"""Tests for SARIF report module."""

import pytest  # noqa: F401
import json
import tempfile  # noqa: F401
import os  # noqa: F401
from src.ai_guard.sarif_report import (
    SarifResult,
    SarifRun,
    write_sarif,
    make_location
)


class TestSarifReport:
    """Test SARIF report functionality."""

    def test_sarif_result_creation(self):
        """Test SarifResult creation."""
        result = SarifResult(
            rule_id="test-rule",
            level="warning",
            message="Test message"
        )

        assert result.rule_id == "test-rule"
        assert result.level == "warning"
        assert result.message == "Test message"
        assert result.locations is None

    def test_sarif_result_with_locations(self):
        """Test SarifResult creation with locations."""
        locations = [{"test": "location"}]
        result = SarifResult(
            rule_id="test-rule",
            level="error",
            message="Test message",
            locations=locations
        )

        assert result.locations == locations

    def test_sarif_run_creation(self):
        """Test SarifRun creation."""
        results = [
            SarifResult("rule1", "warning", "Message 1"),
            SarifResult("rule2", "error", "Message 2")
        ]

        run = SarifRun(tool_name="test-tool", results=results)

        assert run.tool_name == "test-tool"
        assert run.results == results

    def test_make_location_file_only(self):
        """Test make_location with file path only."""
        location = make_location("test.py")

        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert "region" not in location["physicalLocation"]

    def test_make_location_with_line(self):
        """Test make_location with line number."""
        location = make_location("test.py", line=10)

        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert "startColumn" not in location["physicalLocation"]["region"]

    def test_make_location_with_line_and_column(self):
        """Test make_location with line and column numbers."""
        location = make_location("test.py", line=10, column=5)

        assert location["physicalLocation"]["artifactLocation"]["uri"] == "test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5

    def test_write_sarif(self):
        """Test write_sarif function."""
        results = [
            SarifResult("rule1", "warning", "Test warning"),
            SarifResult("rule2", "error", "Test error")
        ]
        run = SarifRun(tool_name="test-tool", results=results)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            temp_path = f.name

        try:
            write_sarif(temp_path, run)

            # Verify file was written
            assert os.path.exists(temp_path)

            # Verify content
            with open(temp_path, 'r') as f:
                content = json.load(f)

            assert content["version"] == "2.1.0"
            assert content["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
            assert len(content["runs"]) == 1
            assert content["runs"][0]["tool"]["driver"]["name"] == "test-tool"
            assert len(content["runs"][0]["results"]) == 2

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
