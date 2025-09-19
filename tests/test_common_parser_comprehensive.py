"""Comprehensive tests for common parser module."""

import pytest
from src.ai_guard.parsers.common import (
    _extract_mypy_rule,
    _RULE_NORMALIZERS,
    normalize_rule
)


class TestExtractMypyRule:
    """Test _extract_mypy_rule function."""

    def test_extract_mypy_rule_with_brackets(self):
        """Test extracting rule from mypy error format with brackets."""
        result = _extract_mypy_rule("error[name-defined]")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_with_brackets_complex(self):
        """Test extracting rule from complex mypy error format."""
        result = _extract_mypy_rule("error[no-any-return]")
        assert result == "mypy:no-any-return"

    def test_extract_mypy_rule_with_brackets_multiple(self):
        """Test extracting rule with multiple brackets."""
        result = _extract_mypy_rule("error[unused-ignore]")
        assert result == "mypy:unused-ignore"

    def test_extract_mypy_rule_no_brackets(self):
        """Test with no brackets."""
        result = _extract_mypy_rule("error")
        assert result == "mypy:error"

    def test_extract_mypy_rule_already_prefixed(self):
        """Test with already prefixed rule."""
        result = _extract_mypy_rule("mypy:error")
        assert result == "mypy:error"

    def test_extract_mypy_rule_empty_string(self):
        """Test with empty string."""
        result = _extract_mypy_rule("")
        assert result == "mypy:"

    def test_extract_mypy_rule_malformed_brackets(self):
        """Test with malformed brackets."""
        result = _extract_mypy_rule("error[name-defined")
        assert result == "mypy:error[name-defined"

    def test_extract_mypy_rule_reverse_brackets(self):
        """Test with reverse brackets."""
        result = _extract_mypy_rule("error]name-defined[")
        assert result == "mypy:error]name-defined["

    def test_extract_mypy_rule_nested_brackets(self):
        """Test with nested brackets."""
        result = _extract_mypy_rule("error[name[defined]]")
        assert result == "mypy:name[defined]"

    def test_extract_mypy_rule_single_bracket(self):
        """Test with single bracket."""
        result = _extract_mypy_rule("error[name")
        assert result == "mypy:error[name"


class TestRuleNormalizers:
    """Test _RULE_NORMALIZERS dictionary."""

    def test_rule_normalizers_keys(self):
        """Test that all expected tools are in normalizers."""
        expected_tools = {"flake8", "mypy", "bandit", "eslint", "jest"}
        assert set(_RULE_NORMALIZERS.keys()) == expected_tools

    def test_flake8_normalizer(self):
        """Test flake8 normalizer."""
        normalizer = _RULE_NORMALIZERS["flake8"]
        assert normalizer("E501") == "flake8:E501"
        assert normalizer("flake8:E501") == "flake8:E501"
        assert normalizer("W292") == "flake8:W292"

    def test_mypy_normalizer(self):
        """Test mypy normalizer."""
        normalizer = _RULE_NORMALIZERS["mypy"]
        assert normalizer("error[name-defined]") == "mypy:name-defined"
        assert normalizer("mypy:error") == "mypy:error"

    def test_bandit_normalizer(self):
        """Test bandit normalizer."""
        normalizer = _RULE_NORMALIZERS["bandit"]
        assert normalizer("B101") == "bandit:B101"
        assert normalizer("bandit:B101") == "bandit:B101"
        assert normalizer("B602") == "bandit:B602"

    def test_eslint_normalizer(self):
        """Test eslint normalizer."""
        normalizer = _RULE_NORMALIZERS["eslint"]
        assert normalizer("no-unused") == "eslint:no-unused"
        assert normalizer("eslint:no-unused") == "eslint:no-unused"
        assert normalizer("no-console") == "eslint:no-console"

    def test_jest_normalizer(self):
        """Test jest normalizer."""
        normalizer = _RULE_NORMALIZERS["jest"]
        assert normalizer("test-failure") == "jest:test-failure"
        assert normalizer("jest:test-failure") == "jest:test-failure"
        assert normalizer("timeout") == "jest:timeout"


class TestNormalizeRule:
    """Test normalize_rule function."""

    def test_normalize_rule_flake8(self):
        """Test normalizing flake8 rule."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_flake8_already_normalized(self):
        """Test normalizing already normalized flake8 rule."""
        result = normalize_rule("flake8", "flake8:E501")
        assert result == "flake8:E501"

    def test_normalize_rule_mypy(self):
        """Test normalizing mypy rule."""
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"

    def test_normalize_rule_mypy_already_normalized(self):
        """Test normalizing already normalized mypy rule."""
        result = normalize_rule("mypy", "mypy:error")
        assert result == "mypy:error"

    def test_normalize_rule_bandit(self):
        """Test normalizing bandit rule."""
        result = normalize_rule("bandit", "B101")
        assert result == "bandit:B101"

    def test_normalize_rule_bandit_already_normalized(self):
        """Test normalizing already normalized bandit rule."""
        result = normalize_rule("bandit", "bandit:B101")
        assert result == "bandit:B101"

    def test_normalize_rule_eslint(self):
        """Test normalizing eslint rule."""
        result = normalize_rule("eslint", "no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_eslint_already_normalized(self):
        """Test normalizing already normalized eslint rule."""
        result = normalize_rule("eslint", "eslint:no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_jest(self):
        """Test normalizing jest rule."""
        result = normalize_rule("jest", "test-failure")
        assert result == "jest:test-failure"

    def test_normalize_rule_jest_already_normalized(self):
        """Test normalizing already normalized jest rule."""
        result = normalize_rule("jest", "jest:test-failure")
        assert result == "jest:test-failure"

    def test_normalize_rule_unknown_tool(self):
        """Test normalizing rule for unknown tool."""
        result = normalize_rule("unknown", "rule123")
        assert result == "unknown:rule123"

    def test_normalize_rule_case_insensitive(self):
        """Test normalizing rule with case insensitive tool name."""
        result = normalize_rule("FLAKE8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_none_tool(self):
        """Test normalizing rule with None tool."""
        result = normalize_rule(None, "rule123")
        assert result == "none:rule123"

    def test_normalize_rule_none_raw(self):
        """Test normalizing rule with None raw."""
        result = normalize_rule("flake8", None)
        assert result == "flake8:None"

    def test_normalize_rule_empty_raw(self):
        """Test normalizing rule with empty raw."""
        result = normalize_rule("flake8", "")
        assert result == "flake8:"

    def test_normalize_rule_numeric_raw(self):
        """Test normalizing rule with numeric raw."""
        result = normalize_rule("flake8", 123)
        assert result == "flake8:123"

    def test_normalize_rule_boolean_raw(self):
        """Test normalizing rule with boolean raw."""
        result = normalize_rule("flake8", True)
        assert result == "flake8:True"

    def test_normalize_rule_complex_mypy_rule(self):
        """Test normalizing complex mypy rule."""
        result = normalize_rule("mypy", "error[no-any-return]")
        assert result == "mypy:no-any-return"

    def test_normalize_rule_mypy_with_colon(self):
        """Test normalizing mypy rule that already has colon."""
        result = normalize_rule("mypy", "error:name-defined")
        assert result == "mypy:error:name-defined"

    def test_normalize_rule_flake8_with_colon(self):
        """Test normalizing flake8 rule that already has colon."""
        result = normalize_rule("flake8", "E501:line too long")
        assert result == "flake8:E501:line too long"

    def test_normalize_rule_eslint_with_colon(self):
        """Test normalizing eslint rule that already has colon."""
        result = normalize_rule("eslint", "no-unused:variable is unused")
        assert result == "eslint:no-unused:variable is unused"

    def test_normalize_rule_jest_with_colon(self):
        """Test normalizing jest rule that already has colon."""
        result = normalize_rule("jest", "test-failure:assertion failed")
        assert result == "jest:test-failure:assertion failed"

    def test_normalize_rule_bandit_with_colon(self):
        """Test normalizing bandit rule that already has colon."""
        result = normalize_rule("bandit", "B101:use of assert detected")
        assert result == "bandit:B101:use of assert detected"

    def test_normalize_rule_empty_tool(self):
        """Test normalizing rule with empty tool."""
        result = normalize_rule("", "rule123")
        assert result == ":rule123"

    def test_normalize_rule_whitespace_tool(self):
        """Test normalizing rule with whitespace tool."""
        result = normalize_rule("  flake8  ", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_whitespace_raw(self):
        """Test normalizing rule with whitespace raw."""
        result = normalize_rule("flake8", "  E501  ")
        assert result == "flake8:  E501  "

    def test_normalize_rule_special_characters(self):
        """Test normalizing rule with special characters."""
        result = normalize_rule("tool", "rule-with-special@chars#123")
        assert result == "tool:rule-with-special@chars#123"

    def test_normalize_rule_unicode(self):
        """Test normalizing rule with unicode characters."""
        result = normalize_rule("tool", "rülë-123")
        assert result == "tool:rülë-123"
