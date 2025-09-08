"""Core tests for analyzer module to improve coverage."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.ai_guard.analyzer import (
    RuleIdStyle, _rule_style, _make_rule_id, 
    run_lint_check, run_type_check
)


class TestRuleIdStyle:
    """Test RuleIdStyle enum and related functions."""
    
    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"
    
    def test_rule_style_tool(self):
        """Test rule style returns tool format."""
        with patch.dict('os.environ', {'AI_GUARD_RULE_STYLE': 'tool'}):
            assert _rule_style() == RuleIdStyle.TOOL
    
    def test_rule_style_bare(self):
        """Test rule style returns bare format."""
        with patch.dict('os.environ', {'AI_GUARD_RULE_STYLE': 'bare'}):
            assert _rule_style() == RuleIdStyle.BARE
    
    def test_rule_style_default(self):
        """Test rule style default value."""
        with patch.dict('os.environ', {}, clear=True):
            assert _rule_style() == RuleIdStyle.TOOL
    
    @patch('src.ai_guard.analyzer._rule_style')
    def test_make_rule_id_tool_style(self, mock_rule_style):
        """Test _make_rule_id with tool style."""
        mock_rule_style.return_value = RuleIdStyle.TOOL
        assert _make_rule_id("flake8", "E501") == "flake8:E501"
    
    @patch('src.ai_guard.analyzer._rule_style')
    def test_make_rule_id_bare_style(self, mock_rule_style):
        """Test _make_rule_id with bare style."""
        mock_rule_style.return_value = RuleIdStyle.BARE
        assert _make_rule_id("flake8", "E501") == "E501"


class TestLinters:
    """Test linter functions."""
    
    def test_run_lint_check_success(self):
        """Test run_lint_check with successful execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')\n")
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="",
                    stderr=""
                )
                
                gate_result, sarif_result = run_lint_check([str(test_file)])
                assert gate_result.passed is True
    
    def test_run_lint_check_with_errors(self):
        """Test run_lint_check with linting errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')  # line too long\n")
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,
                    stdout="test.py:1:1: E501 line too long",
                    stderr=""
                )
                
                gate_result, sarif_result = run_lint_check([str(test_file)])
                assert gate_result.passed is False
                assert "E501" in gate_result.details
    
    def test_run_type_check_success(self):
        """Test run_type_check with successful execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def func() -> int:\n    return 42\n")
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="Success: no issues found",
                    stderr=""
                )
                
                gate_result, sarif_result = run_type_check([str(test_file)])
                assert gate_result.passed is True


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_run_lint_check_file_not_found(self):
        """Test run_lint_check with non-existent file."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("flake8 not found")
            
            gate_result, sarif_result = run_lint_check(["nonexistent.py"])
            assert gate_result.passed is False
            assert "flake8 not found" in gate_result.details
    
    def test_run_type_check_file_not_found(self):
        """Test run_type_check with non-existent file."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("mypy not found")
            
            gate_result, sarif_result = run_type_check(["nonexistent.py"])
            assert gate_result.passed is False
            assert "mypy not found" in gate_result.details
