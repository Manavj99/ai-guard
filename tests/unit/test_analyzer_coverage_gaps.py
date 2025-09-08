"""Tests for analyzer module coverage gaps."""

from unittest.mock import patch, Mock, mock_open
from ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_json,
    _to_findings,
    run_coverage_check,
)
from ai_guard.sarif_report import SarifResult, make_location


class TestAnalyzerCoverageGaps:
    """Test coverage gaps in analyzer module."""

    def test_cov_percent_with_coverage_xml(self):
        """Test cov_percent with valid coverage.xml file."""
        xml_content = '<?xml version="1.0"?><coverage line-rate="0.85"></coverage>'

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=xml_content)):
                with patch("ai_guard.analyzer.ET") as mock_et:
                    mock_tree = Mock()
                    mock_root = Mock()
                    mock_root.get.return_value = "0.85"
                    mock_tree.getroot.return_value = mock_root
                    mock_et.parse.return_value = mock_tree

                    result = cov_percent()
                    assert result == 85

    def test_cov_percent_with_relative_path(self):
        """Test cov_percent with relative path coverage.xml."""
        xml_content = '<?xml version="1.0"?><coverage line-rate="0.75"></coverage>'

        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = [False, True]
            with patch("builtins.open", mock_open(read_data=xml_content)):
                with patch("ai_guard.analyzer.ET") as mock_et:
                    mock_tree = Mock()
                    mock_root = Mock()
                    mock_root.get.return_value = "0.75"
                    mock_tree.getroot.return_value = mock_root
                    mock_et.parse.return_value = mock_tree

                    result = cov_percent()
                    assert result == 75

    def test_cov_percent_parse_error(self):
        """Test cov_percent with XML parse error."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid xml")):
                with patch("ai_guard.analyzer.ET") as mock_et:
                    mock_et.parse.side_effect = Exception("Parse error")

                    result = cov_percent()
                    assert result == 0

    def test_cov_percent_no_file_found(self):
        """Test cov_percent when no coverage file is found."""
        with patch("os.path.exists", return_value=False):
            result = cov_percent()
            assert result == 0

    def test_parse_flake8_output_multiple_lines(self):
        """Test parsing multiple flake8 output lines."""
        output = """src/test.py:10:5: E501 line too long (120 > 79 characters)
src/test.py:15:1: F401 'os' imported but unused
src/test.py:20:10: W293 blank line contains whitespace"""

        results = _parse_flake8_output(output)

        assert len(results) == 3
        assert results[0].rule_id == "flake8:E501"
        assert results[1].rule_id == "flake8:F401"
        assert results[2].rule_id == "flake8:W293"

    def test_parse_mypy_output_multiple_errors(self):
        """Test parsing multiple mypy errors."""
        output = """src/test.py:10: error: Name 'undefined_var' is not defined [name-defined]
src/test.py:15: warning: Unused import 'os' [unused-import]
src/test.py:20: note: Use '-> None' if function does not return a value"""

        results = _parse_mypy_output(output)

        assert len(results) == 3
        assert results[0].rule_id == "mypy:name-defined"
        assert results[0].level == "error"
        assert results[1].rule_id == "mypy:unused-import"
        assert results[1].level == "warning"
        assert results[2].rule_id == "mypy:mypy-error"
        assert results[2].level == "note"

    def test_parse_bandit_json_multiple_results(self):
        """Test parsing bandit JSON with multiple results."""
        output = """{
            "results": [
                {
                    "filename": "src/test1.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "Use of assert detected",
                    "issue_severity": "HIGH"
                },
                {
                    "filename": "src/test2.py",
                    "line_number": 20,
                    "test_id": "B102",
                    "issue_text": "Use of exec detected",
                    "issue_severity": "MEDIUM"
                }
            ]
        }"""

        results = _parse_bandit_json(output)

        assert len(results) == 2
        assert results[0].rule_id == "bandit:B101"
        assert results[0].level == "error"
        assert results[1].rule_id == "bandit:B102"
        assert results[1].level == "warning"

    def test_parse_bandit_json_missing_severity(self):
        """Test parsing bandit JSON with missing severity."""
        output = """{
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "Use of assert detected"
                }
            ]
        }"""

        results = _parse_bandit_json(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "bandit:B101"
        assert result.level == "note"

    def test_to_findings_empty_list(self):
        """Test _to_findings with empty list."""
        findings = _to_findings([])
        assert findings == []

    def test_to_findings_multiple_results(self):
        """Test _to_findings with multiple SARIF results."""
        sarif_results = [
            SarifResult(
                rule_id="test:rule1",
                level="warning",
                message="Test message 1",
                locations=[make_location("src/test1.py", 10, 5)],
            ),
            SarifResult(
                rule_id="test:rule2",
                level="error",
                message="Test message 2",
                locations=[make_location("src/test2.py", 20, 10)],
            ),
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 2
        assert findings[0]["rule_id"] == "test:rule1"
        assert findings[0]["path"] == "src/test1.py"
        assert findings[0]["line"] == 10
        assert findings[1]["rule_id"] == "test:rule2"
        assert findings[1]["path"] == "src/test2.py"
        assert findings[1]["line"] == 20

    def test_run_coverage_check_passed(self):
        """Test coverage check that passes."""
        with patch("ai_guard.analyzer.cov_percent", return_value=85):
            result = run_coverage_check(80)
            assert result.name == "Coverage"
            assert result.passed is True
            assert "85% >= 80%" in result.details

    def test_run_coverage_check_failed(self):
        """Test coverage check that fails."""
        with patch("ai_guard.analyzer.cov_percent", return_value=75):
            result = run_coverage_check(80)
            assert result.name == "Coverage"
            assert result.passed is False
            assert "75% >= 80%" in result.details
