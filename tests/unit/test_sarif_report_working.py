"""Working comprehensive tests for the SARIF report module."""

import pytest
import json
import tempfile
from unittest.mock import patch

from ai_guard.sarif_report import (
    SarifResult,
    SarifRun,
    create_sarif_report,
    write_sarif,
    make_location,
)


class TestSarifReportWorking:
    """Working comprehensive tests for SARIF report functionality."""

    def test_sarif_result_creation(self):
        """Test SarifResult dataclass creation."""
        result = SarifResult(
            rule_id="test-rule",
            level="warning",
            message="Test message",
            locations=[{"physicalLocation": {"artifactLocation": {"uri": "test.py"}}}],
        )

        assert result.rule_id == "test-rule"
        assert result.level == "warning"
        assert result.message == "Test message"
        assert len(result.locations) == 1

    def test_sarif_run_creation(self):
        """Test SarifRun dataclass creation."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun(tool_name="test-tool", results=[result], tool_version="1.0.0")

        assert run.tool_name == "test-tool"
        assert len(run.results) == 1
        assert run.tool_version == "1.0.0"

    def test_make_location(self):
        """Test make_location function."""
        location = make_location("src/test.py", 10, 5, 15, 10)

        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 5
        assert location["physicalLocation"]["region"]["endLine"] == 15
        assert location["physicalLocation"]["region"]["endColumn"] == 10

    def test_make_location_minimal(self):
        """Test make_location with minimal parameters."""
        location = make_location("src/test.py", 10)

        assert location["physicalLocation"]["artifactLocation"]["uri"] == "src/test.py"
        assert location["physicalLocation"]["region"]["startLine"] == 10
        assert location["physicalLocation"]["region"]["startColumn"] == 1
        assert location["physicalLocation"]["region"]["endLine"] == 10
        assert location["physicalLocation"]["region"]["endColumn"] == 1

    def test_create_sarif_report_basic(self):
        """Test create_sarif_report with basic data."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun("test-tool", [result])

        report = create_sarif_report([run])

        assert report["version"] == "2.1.0"
        assert report["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
        assert len(report["runs"]) == 1
        assert report["runs"][0]["tool"]["driver"]["name"] == "test-tool"
        assert len(report["runs"][0]["results"]) == 1

    def test_create_sarif_report_with_metadata(self):
        """Test create_sarif_report with metadata."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun("test-tool", [result])
        metadata = {"scan_time": "2023-01-01T00:00:00Z"}

        report = create_sarif_report([run], metadata)

        assert report["metadata"] == metadata

    def test_create_sarif_report_multiple_runs(self):
        """Test create_sarif_report with multiple runs."""
        result1 = SarifResult("rule1", "warning", "Message 1")
        result2 = SarifResult("rule2", "error", "Message 2")
        run1 = SarifRun("tool1", [result1])
        run2 = SarifRun("tool2", [result2])

        report = create_sarif_report([run1, run2])

        assert len(report["runs"]) == 2
        assert report["runs"][0]["tool"]["driver"]["name"] == "tool1"
        assert report["runs"][1]["tool"]["driver"]["name"] == "tool2"

    def test_create_sarif_report_empty_results(self):
        """Test create_sarif_report with empty results."""
        run = SarifRun("test-tool", [])

        report = create_sarif_report([run])

        assert len(report["runs"]) == 1
        assert len(report["runs"][0]["results"]) == 0

    def test_write_sarif(self):
        """Test write_sarif function."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun("test-tool", [result])

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sarif") as f:
            output_path = f.name

        try:
            write_sarif([run], output_path)

            # Verify file was written
            with open(output_path, "r") as f:
                written_data = json.load(f)
                assert written_data["version"] == "2.1.0"
                assert len(written_data["runs"]) == 1
        finally:
            import os

            os.unlink(output_path)

    def test_write_sarif_with_metadata(self):
        """Test write_sarif function with metadata."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun("test-tool", [result])
        metadata = {"scan_time": "2023-01-01T00:00:00Z"}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sarif") as f:
            output_path = f.name

        try:
            write_sarif([run], output_path, metadata)

            # Verify file was written with metadata
            with open(output_path, "r") as f:
                written_data = json.load(f)
                assert written_data["metadata"] == metadata
        finally:
            import os

            os.unlink(output_path)

    def test_write_sarif_error(self):
        """Test write_sarif with write error."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun("test-tool", [result])

        with patch("builtins.open", side_effect=IOError("Write error")):
            with pytest.raises(IOError):
                write_sarif([run], "test.sarif")

    def test_sarif_result_with_locations(self):
        """Test SarifResult with complex locations."""
        location1 = make_location("src/test1.py", 10, 5, 15, 10)
        location2 = make_location("src/test2.py", 20, 1, 25, 5)

        result = SarifResult(
            rule_id="test-rule",
            level="warning",
            message="Test message",
            locations=[location1, location2],
        )

        assert len(result.locations) == 2
        assert (
            result.locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test1.py"
        )
        assert (
            result.locations[1]["physicalLocation"]["artifactLocation"]["uri"]
            == "src/test2.py"
        )

    def test_sarif_result_without_locations(self):
        """Test SarifResult without locations."""
        result = SarifResult(
            rule_id="test-rule", level="warning", message="Test message"
        )

        assert result.locations is None

    def test_sarif_run_default_version(self):
        """Test SarifRun with default version."""
        result = SarifResult("test-rule", "warning", "Test message")
        run = SarifRun("test-tool", [result])

        assert run.tool_version == "unknown"
