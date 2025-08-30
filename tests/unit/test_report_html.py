"""Tests for HTML report module."""

import pytest  # noqa: F401
import tempfile
import os
from src.ai_guard.report_html import write_html
from src.ai_guard.report import GateResult


class TestReportHtml:
    """Test HTML report functionality."""

    def test_write_html_basic(self):
        """Test basic HTML report generation."""
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

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            # Verify file was written
            assert os.path.exists(temp_path)

            # Verify content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check basic structure
            assert "<!doctype html>" in content
            assert "<title>AI-Guard Report</title>" in content
            assert "<h1>AI-Guard Report</h1>" in content

            # Check status (should show GATES FAILED since one gate failed)
            assert "GATES FAILED" in content
            assert "badge fail" in content

            # Check gates table
            assert "<h2>Gates</h2>" in content
            assert "<th>Gate</th>" in content
            assert "<th>Status</th>" in content
            assert "<th>Details</th>" in content

            # Check specific gate content
            assert "Lint (flake8)" in content
            assert "Static types (mypy)" in content
            assert "mypy not found" in content

            # Check findings table
            assert "<h2>Findings</h2>" in content
            assert "<th>Location</th>" in content
            assert "<th>Level</th>" in content
            assert "<th>Rule</th>" in content
            assert "<th>Message</th>" in content

            # Check specific finding content
            assert "mypy:arg-type" in content
            assert "src/foo.py:42" in content
            assert "Argument 1 to &quot;func&quot; has incompatible type" in content

        finally:
            os.unlink(temp_path)

    def test_write_html_all_passed(self):
        """Test HTML report when all gates pass."""
        gates = [
            GateResult("Lint (flake8)", True, ""),
            GateResult("Coverage", True, "90% >= 80%")
        ]

        findings = []  # No findings

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should show ALL GATES PASSED
            assert "ALL GATES PASSED" in content
            assert "badge pass" in content

            # Should show "No findings 🎉" in findings table
            assert "No findings 🎉" in content

        finally:
            os.unlink(temp_path)

    def test_write_html_empty_gates(self):
        """Test HTML report with no gates."""
        gates = []
        findings = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Empty gates should still show ALL GATES PASSED
            assert "ALL GATES PASSED" in content
            assert "No findings 🎉" in content

        finally:
            os.unlink(temp_path)

    def test_write_html_escaping(self):
        """Test that HTML special characters are properly escaped."""
        gates = [
            GateResult("Test & Gate", True, "Details < 100%"),
            GateResult("Another 'Gate'", False, "Error: \"quoted\" message")
        ]

        findings = [
            {
                "rule_id": "test:rule<id>",
                "level": "error",
                "message": "Error with <script> tags & quotes",
                "path": "src/file<>.py",
                "line": 10
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            write_html(temp_path, gates, findings)

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check that special characters are escaped
            assert "Test &amp; Gate" in content
            assert "Details &lt; 100%" in content
            assert "Another &#x27;Gate&#x27;" in content
            assert "Error: &quot;quoted&quot; message" in content
            assert "test:rule&lt;id&gt;" in content
            assert "Error with &lt;script&gt; tags &amp; quotes" in content
            assert "src/file&lt;&gt;.py" in content

        finally:
            os.unlink(temp_path)
