"""Working tests for analyzer module that match actual source code."""

from unittest.mock import patch, Mock, mock_open
import json
from ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    run_lint_check,
    run_type_check,
    _parse_bandit_json,
    run_security_check,
    _to_findings,
    run_coverage_check,
    main,
)


class TestAnalyzerWorking:
    """Working test coverage for analyzer module."""

    def test_cov_percent_file_exists(self):
        """Test cov_percent when coverage.xml exists."""
        mock_xml = '<?xml version="1.0" ?><coverage line-rate="0.85"></coverage>'

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_xml)):
                with patch("ai_guard.analyzer.ET.parse") as mock_parse:
                    mock_root = Mock()
                    mock_root.get.return_value = "0.85"
                    mock_tree = Mock()
                    mock_tree.getroot.return_value = mock_root
                    mock_parse.return_value = mock_tree

                    result = cov_percent()
                    assert result == 85

    def test_cov_percent_file_not_found(self):
        """Test cov_percent when coverage.xml doesn't exist."""
        with patch("os.path.exists", return_value=False):
            result = cov_percent()
            assert result == 0

    def test_cov_percent_parse_error(self):
        """Test cov_percent with parse error."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid xml")):
                with patch(
                    "ai_guard.analyzer.ET.parse", side_effect=Exception("Parse error")
                ):
                    result = cov_percent()
                    assert result == 0

    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        flake8_output = """
src/test.py:10:1: E302 expected 2 blank lines, found 1
src/test.py:15:5: E111 indentation is not a multiple of four
"""

        results = _parse_flake8_output(flake8_output)

        assert len(results) == 2
        assert results[0].rule_id == "E302"
        assert results[0].message == "expected 2 blank lines, found 1"
        assert results[1].rule_id == "E111"
        assert results[1].message == "indentation is not a multiple of four"

    def test_parse_flake8_output_empty(self):
        """Test parsing empty flake8 output."""
        results = _parse_flake8_output("")
        assert results == []

    def test_parse_mypy_output_valid(self):
        """Test parsing valid mypy output."""
        mypy_output = """
src/test.py:10: error: Incompatible return type
src/test.py:15: error: Argument 1 has incompatible type
"""

        results = _parse_mypy_output(mypy_output)

        assert len(results) == 2
        assert "Incompatible return type" in results[0].message
        assert "Argument 1 has incompatible type" in results[1].message

    def test_parse_mypy_output_empty(self):
        """Test parsing empty mypy output."""
        results = _parse_mypy_output("")
        assert results == []

    def test_run_lint_check_success(self):
        """Test running lint check successfully."""
        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_run.return_value = mock_proc

            result, findings = run_lint_check(["src/test.py"])

            assert result.passed is True
            assert result.message == "Lint check passed"
            assert findings == []

    def test_run_lint_check_failure(self):
        """Test running lint check with failures."""
        flake8_output = "src/test.py:10:1: E302 expected 2 blank lines, found 1"

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 1
            mock_proc.stdout = flake8_output
            mock_run.return_value = mock_proc

            result, findings = run_lint_check(["src/test.py"])

            assert result.passed is False
            assert "Lint check failed" in result.message
            assert len(findings) == 1

    def test_run_lint_check_error(self):
        """Test running lint check with error."""
        with patch("subprocess.run", side_effect=Exception("Command error")):
            result, findings = run_lint_check(["src/test.py"])

            assert result.passed is False
            assert "Error running lint check" in result.message
            assert findings == []

    def test_run_type_check_success(self):
        """Test running type check successfully."""
        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_run.return_value = mock_proc

            result, findings = run_type_check(["src/test.py"])

            assert result.passed is True
            assert result.message == "Type check passed"
            assert findings == []

    def test_run_type_check_failure(self):
        """Test running type check with failures."""
        mypy_output = "src/test.py:10: error: Incompatible return type"

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 1
            mock_proc.stdout = mypy_output
            mock_run.return_value = mock_proc

            result, findings = run_type_check(["src/test.py"])

            assert result.passed is False
            assert "Type check failed" in result.message
            assert len(findings) == 1

    def test_run_type_check_error(self):
        """Test running type check with error."""
        with patch("subprocess.run", side_effect=Exception("Command error")):
            result, findings = run_type_check(["src/test.py"])

            assert result.passed is False
            assert "Error running type check" in result.message
            assert findings == []

    def test_parse_bandit_json_valid(self):
        """Test parsing valid bandit JSON output."""
        bandit_json = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test issue",
                    "test_id": "B101",
                }
            ]
        }

        results = _parse_bandit_json(json.dumps(bandit_json))

        assert len(results) == 1
        assert results[0].rule_id == "B101"
        assert "Test issue" in results[0].message

    def test_parse_bandit_json_empty(self):
        """Test parsing empty bandit JSON output."""
        bandit_json = {"results": []}

        results = _parse_bandit_json(json.dumps(bandit_json))

        assert results == []

    def test_parse_bandit_json_invalid(self):
        """Test parsing invalid bandit JSON output."""
        results = _parse_bandit_json("invalid json")
        assert results == []

    def test_run_security_check_success(self):
        """Test running security check successfully."""
        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = json.dumps({"results": []})
            mock_run.return_value = mock_proc

            result, findings = run_security_check()

            assert result.passed is True
            assert result.message == "Security check passed"
            assert findings == []

    def test_run_security_check_failure(self):
        """Test running security check with findings."""
        bandit_json = {
            "results": [
                {
                    "filename": "src/test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Test issue",
                    "test_id": "B101",
                }
            ]
        }

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 1
            mock_proc.stdout = json.dumps(bandit_json)
            mock_run.return_value = mock_proc

            result, findings = run_security_check()

            assert result.passed is False
            assert "Security check failed" in result.message
            assert len(findings) == 1

    def test_run_security_check_error(self):
        """Test running security check with error."""
        with patch("subprocess.run", side_effect=Exception("Command error")):
            result, findings = run_security_check()

            assert result.passed is False
            assert "Error running security check" in result.message
            assert findings == []

    def test_to_findings(self):
        """Test converting SARIF results to findings."""
        from ai_guard.sarif_report import SarifResult, make_location

        sarif_results = [
            SarifResult(
                rule_id="E302",
                message="Test message",
                level="error",
                locations=[make_location("src/test.py", 10, 1)],
            )
        ]

        findings = _to_findings(sarif_results)

        assert len(findings) == 1
        assert findings[0]["rule_id"] == "E302"
        assert findings[0]["message"] == "Test message"
        assert findings[0]["file"] == "src/test.py"
        assert findings[0]["line"] == 10

    def test_run_coverage_check_success(self):
        """Test running coverage check successfully."""
        with patch("ai_guard.analyzer.cov_percent", return_value=85):
            result = run_coverage_check(80)

            assert result.passed is True
            assert "Coverage check passed" in result.message
            assert "85%" in result.message

    def test_run_coverage_check_failure(self):
        """Test running coverage check with failure."""
        with patch("ai_guard.analyzer.cov_percent", return_value=75):
            result = run_coverage_check(80)

            assert result.passed is False
            assert "Coverage check failed" in result.message
            assert "75%" in result.message

    def test_main_with_args(self):
        """Test main function with arguments."""
        with patch("sys.argv", ["ai-guard", "--min-coverage", "90"]):
            with patch("ai_guard.analyzer.run_lint_check") as mock_lint:
                with patch("ai_guard.analyzer.run_type_check") as mock_type:
                    with patch("ai_guard.analyzer.run_security_check") as mock_security:
                        with patch(
                            "ai_guard.analyzer.run_coverage_check"
                        ) as mock_coverage:
                            from ai_guard.report import GateResult

                            mock_lint.return_value = (
                                GateResult(True, "Lint passed"),
                                [],
                            )
                            mock_type.return_value = (
                                GateResult(True, "Type passed"),
                                [],
                            )
                            mock_security.return_value = (
                                GateResult(True, "Security passed"),
                                [],
                            )
                            mock_coverage.return_value = GateResult(
                                True, "Coverage passed"
                            )

                            # This should not raise an exception
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected for argparse

    def test_main_without_args(self):
        """Test main function without arguments."""
        with patch("sys.argv", ["ai-guard"]):
            with patch("ai_guard.analyzer.run_lint_check") as mock_lint:
                with patch("ai_guard.analyzer.run_type_check") as mock_type:
                    with patch("ai_guard.analyzer.run_security_check") as mock_security:
                        with patch(
                            "ai_guard.analyzer.run_coverage_check"
                        ) as mock_coverage:
                            from ai_guard.report import GateResult

                            mock_lint.return_value = (
                                GateResult(True, "Lint passed"),
                                [],
                            )
                            mock_type.return_value = (
                                GateResult(True, "Type passed"),
                                [],
                            )
                            mock_security.return_value = (
                                GateResult(True, "Security passed"),
                                [],
                            )
                            mock_coverage.return_value = GateResult(
                                True, "Coverage passed"
                            )

                            # This should not raise an exception
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected for argparse
