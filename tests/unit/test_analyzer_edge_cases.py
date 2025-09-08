"""Edge case tests for analyzer module to improve coverage to 90%+."""

from unittest.mock import patch

from ai_guard.analyzer import (
    run_lint_check,
    run_type_check,
    run_security_check,
    run_coverage_check,
)


class TestAnalyzerEdgeCases:
    """Test edge cases and error handling in analyzer module."""

    @patch("subprocess.run")
    def test_run_lint_check_with_scope(self, mock_run):
        """Test lint check with file scope."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_lint_check(["src/test.py"])

        assert result.passed
        assert result.name == "Lint (flake8)"
        assert sarif == []

    @patch("subprocess.run")
    def test_run_lint_check_with_scope_none(self, mock_run):
        """Test lint check with no scope (None)."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_lint_check(None)

        assert result.passed
        assert result.name == "Lint (flake8)"

    @patch("subprocess.run")
    def test_run_lint_check_with_empty_scope(self, mock_run):
        """Test lint check with empty scope list."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_lint_check([])

        assert result.passed
        assert result.name == "Lint (flake8)"

    @patch("subprocess.run")
    def test_run_type_check_with_scope(self, mock_run):
        """Test type check with file scope."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_type_check(["src/test.py"])

        assert result.passed
        assert result.name == "Static types (mypy)"
        assert sarif == []

    @patch("subprocess.run")
    def test_run_type_check_with_scope_none(self, mock_run):
        """Test type check with no scope (None)."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_type_check(None)

        assert result.passed
        assert result.name == "Static types (mypy)"

    @patch("subprocess.run")
    def test_run_type_check_with_empty_scope(self, mock_run):
        """Test type check with empty scope list."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_type_check([])

        assert result.passed
        assert result.name == "Static types (mypy)"

    @patch("subprocess.run")
    def test_run_security_check_success(self, mock_run):
        """Test security check success."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result, sarif = run_security_check()

        assert result.passed
        assert result.name == "Security (bandit)"
        assert sarif == []

    @patch("subprocess.run")
    def test_run_coverage_check_with_min_cov(self, mock_run):
        """Test coverage check with minimum coverage requirement."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"TOTAL                   123    45    78    63%"

        result = run_coverage_check(80)

        assert not result.passed
        assert result.name == "Coverage"
        assert "63% >= 80%" in result.details

    @patch("subprocess.run")
    def test_run_coverage_check_without_min_cov(self, mock_run):
        """Test coverage check without minimum coverage requirement."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"TOTAL                   123    45    78    63%"

        result = run_coverage_check(None)

        assert result.passed
        assert result.name == "Coverage"
        assert "63%" in result.details

    @patch("subprocess.run")
    def test_run_coverage_check_exact_coverage(self, mock_run):
        """Test coverage check with exact coverage match."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"TOTAL                   100    0   100   100%"

        result = run_coverage_check(100)

        assert result.passed
        assert result.name == "Coverage"
        assert "100% >= 100%" in result.details

    @patch("subprocess.run")
    def test_run_coverage_check_above_threshold(self, mock_run):
        """Test coverage check above threshold."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"TOTAL                   100    10    90    90%"

        result = run_coverage_check(85)

        assert result.passed
        assert result.name == "Coverage"
        assert "90% >= 85%" in result.details

    @patch("subprocess.run")
    def test_run_coverage_check_subprocess_failure(self, mock_run):
        """Test coverage check when subprocess fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = b"Error running coverage"

        result = run_coverage_check(80)

        assert not result.passed
        assert result.name == "Coverage"
        assert "Error running coverage" in result.details

    @patch("subprocess.run")
    def test_run_lint_check_subprocess_failure(self, mock_run):
        """Test lint check when subprocess fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = b"flake8 error"

        result, sarif = run_lint_check(None)

        assert not result.passed
        assert result.name == "Lint (flake8)"
        assert "flake8 error" in result.details

    @patch("subprocess.run")
    def test_run_type_check_subprocess_failure(self, mock_run):
        """Test type check when subprocess fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = b"mypy error"

        result, sarif = run_type_check(None)

        assert not result.passed
        assert result.name == "Static types (mypy)"
        assert "mypy error" in result.details

    @patch("subprocess.run")
    def test_run_security_check_subprocess_failure(self, mock_run):
        """Test security check when subprocess fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = b"bandit error"

        result, sarif = run_security_check()

        assert not result.passed
        assert result.name == "Security (bandit)"
        assert "bandit error" in result.details

    @patch("subprocess.run")
    def test_run_lint_check_with_output_parsing(self, mock_run):
        """Test lint check with actual output parsing."""
        mock_output = b"""src/test.py:1:1: F401 'os' imported but unused
src/test.py:2:5: E302 expected 2 blank lines, found 1"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output

        result, sarif = run_lint_check(None)

        assert not result.passed
        assert result.name == "Lint (flake8)"
        assert "F401" in result.details
        assert "E302" in result.details
        assert len(sarif) == 2

    @patch("subprocess.run")
    def test_run_type_check_with_output_parsing(self, mock_run):
        """Test type check with actual output parsing."""
        mock_output = b"""src/test.py:1: error: Name 'undefined_var' is not defined
src/test.py:5: error: Argument 1 to 'len' has incompatible type"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output

        result, sarif = run_type_check(None)

        assert not result.passed
        assert result.name == "Static types (mypy)"
        assert "undefined_var" in result.details
        assert len(sarif) == 2

    @patch("subprocess.run")
    def test_run_security_check_with_output_parsing(self, mock_run):
        """Test security check with actual output parsing."""
        mock_output = b""">> Issue: [B101:assert_used] Use of assert detected. The assert statement is not reliable in production code.
   Severity: Low   Confidence: High
   Location: src/test.py:1:0"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output

        result, sarif = run_security_check()

        assert not result.passed
        assert result.name == "Security (bandit)"
        assert "B101" in result.details
        assert len(sarif) == 1

    @patch("subprocess.run")
    def test_run_coverage_check_with_complex_output(self, mock_run):
        """Test coverage check with complex coverage output."""
        mock_output = b"""Name                           Stmts   Miss  Cover
-------------------------------------------------------------------------
src/ai_guard/__init__.py             5      0   100%
src/ai_guard/analyzer.py           247     39    84%
src/ai_guard/config.py             33      0   100%
-------------------------------------------------------------------------
TOTAL                             285     39    86%"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output

        result = run_coverage_check(90)

        assert not result.passed
        assert result.name == "Coverage"
        assert "86% >= 90%" in result.details

    @patch("subprocess.run")
    def test_run_coverage_check_with_no_output(self, mock_run):
        """Test coverage check with no output."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b""

        result = run_coverage_check(80)

        assert not result.passed
        assert result.name == "Coverage"
        assert "No coverage data" in result.details

    @patch("subprocess.run")
    def test_run_lint_check_with_unicode_output(self, mock_run):
        """Test lint check with unicode output."""
        mock_output = "src/test.py:1:1: F401 'os' imported but unused".encode("utf-8")
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output

        result, sarif = run_lint_check(None)

        assert not result.passed
        assert result.name == "Lint (flake8)"
        assert "F401" in result.details

    @patch("subprocess.run")
    def test_run_type_check_with_unicode_output(self, mock_run):
        """Test type check with unicode output."""
        mock_output = (
            "src/test.py:1: error: Name 'undefined_var' is not defined".encode("utf-8")
        )
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output

        result, sarif = run_type_check(None)

        assert not result.passed
        assert result.name == "Static types (mypy)"
        assert "undefined_var" in result.details

    @patch("subprocess.run")
    def test_run_security_check_with_unicode_output(self, mock_run):
        """Test security check with unicode output."""
        mock_output = ">> Issue: [B101:assert_used] Use of assert detected".encode(
            "utf-8"
        )
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = mock_output

        result, sarif = run_security_check()

        assert not result.passed
        assert result.name == "Security (bandit)"
        assert "B101" in result.details

    @patch("subprocess.run")
    def test_run_coverage_check_with_unicode_output(self, mock_run):
        """Test coverage check with unicode output."""
        mock_output = "TOTAL                             285     39    86%".encode(
            "utf-8"
        )
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output

        result = run_coverage_check(90)

        assert not result.passed
        assert result.name == "Coverage"
        assert "86% >= 90%" in result.details
