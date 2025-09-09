"""Enhanced tests for parsers/common module to achieve 80%+ coverage."""

import pytest

from src.ai_guard.parsers.common import (
    normalize_rule,
    _extract_mypy_rule,
    _RULE_NORMALIZERS
)


class TestExtractMypyRule:
    """Test _extract_mypy_rule function."""

    def test_extract_mypy_rule_with_brackets(self):
        """Test extracting rule from mypy error format with brackets."""
        result = _extract_mypy_rule("error[name-defined]")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_with_brackets_multiple(self):
        """Test extracting rule with multiple bracket pairs."""
        result = _extract_mypy_rule("error[unused-import]")
        assert result == "mypy:unused-import"

    def test_extract_mypy_rule_with_brackets_complex(self):
        """Test extracting rule with complex bracket content."""
        result = _extract_mypy_rule("error[attr-defined,no-any-return]")
        assert result == "mypy:attr-defined,no-any-return"

    def test_extract_mypy_rule_no_brackets(self):
        """Test extracting rule without brackets."""
        result = _extract_mypy_rule("name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_already_prefixed(self):
        """Test extracting rule already prefixed with mypy:."""
        result = _extract_mypy_rule("mypy:name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_empty_string(self):
        """Test extracting rule from empty string."""
        result = _extract_mypy_rule("")
        assert result == "mypy:"

    def test_extract_mypy_rule_malformed_brackets(self):
        """Test extracting rule with malformed brackets."""
        result = _extract_mypy_rule("error[name-defined")
        assert result == "mypy:error[name-defined"

    def test_extract_mypy_rule_reverse_brackets(self):
        """Test extracting rule with reverse bracket order."""
        result = _extract_mypy_rule("error]name-defined[")
        assert result == "mypy:error]name-defined["

    def test_extract_mypy_rule_only_brackets(self):
        """Test extracting rule with only brackets."""
        result = _extract_mypy_rule("[]")
        assert result == "mypy:"

    def test_extract_mypy_rule_nested_brackets(self):
        """Test extracting rule with nested brackets."""
        result = _extract_mypy_rule("error[[name-defined]]")
        assert result == "mypy:[name-defined"


class TestRuleNormalizers:
    """Test _RULE_NORMALIZERS dictionary."""

    def test_rule_normalizers_keys(self):
        """Test that all expected normalizers are present."""
        expected_tools = ["flake8", "mypy", "bandit", "eslint", "jest"]
        for tool in expected_tools:
            assert tool in _RULE_NORMALIZERS

    def test_rule_normalizers_are_callable(self):
        """Test that all normalizers are callable."""
        for normalizer in _RULE_NORMALIZERS.values():
            assert callable(normalizer)

    def test_flake8_normalizer_with_colon(self):
        """Test flake8 normalizer with existing colon."""
        normalizer = _RULE_NORMALIZERS["flake8"]
        result = normalizer("flake8:E501")
        assert result == "flake8:E501"

    def test_flake8_normalizer_without_colon(self):
        """Test flake8 normalizer without colon."""
        normalizer = _RULE_NORMALIZERS["flake8"]
        result = normalizer("E501")
        assert result == "flake8:E501"

    def test_bandit_normalizer_with_prefix(self):
        """Test bandit normalizer with existing bandit: prefix."""
        normalizer = _RULE_NORMALIZERS["bandit"]
        result = normalizer("bandit:B101")
        assert result == "bandit:B101"

    def test_bandit_normalizer_without_prefix(self):
        """Test bandit normalizer without prefix."""
        normalizer = _RULE_NORMALIZERS["bandit"]
        result = normalizer("B101")
        assert result == "bandit:B101"

    def test_eslint_normalizer_with_colon(self):
        """Test eslint normalizer with existing colon."""
        normalizer = _RULE_NORMALIZERS["eslint"]
        result = normalizer("eslint:no-unused")
        assert result == "eslint:no-unused"

    def test_eslint_normalizer_without_colon(self):
        """Test eslint normalizer without colon."""
        normalizer = _RULE_NORMALIZERS["eslint"]
        result = normalizer("no-unused")
        assert result == "eslint:no-unused"

    def test_jest_normalizer_with_colon(self):
        """Test jest normalizer with existing colon."""
        normalizer = _RULE_NORMALIZERS["jest"]
        result = normalizer("jest:test-name")
        assert result == "jest:test-name"

    def test_jest_normalizer_without_colon(self):
        """Test jest normalizer without colon."""
        normalizer = _RULE_NORMALIZERS["jest"]
        result = normalizer("test-name")
        assert result == "jest:test-name"


class TestNormalizeRule:
    """Test normalize_rule function."""

    def test_normalize_rule_known_tool(self):
        """Test normalizing rule for known tool."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_unknown_tool(self):
        """Test normalizing rule for unknown tool."""
        result = normalize_rule("unknown", "rule123")
        assert result == "unknown:rule123"

    def test_normalize_rule_none_tool(self):
        """Test normalizing rule with None tool."""
        result = normalize_rule(None, "rule123")
        assert result == "none:rule123"

    def test_normalize_rule_empty_tool(self):
        """Test normalizing rule with empty tool."""
        result = normalize_rule("", "rule123")
        assert result == "none:rule123"

    def test_normalize_rule_none_raw(self):
        """Test normalizing rule with None raw value."""
        result = normalize_rule("flake8", None)
        assert result == "flake8:None"

    def test_normalize_rule_empty_raw(self):
        """Test normalizing rule with empty raw value."""
        result = normalize_rule("flake8", "")
        assert result == "flake8:"

    def test_normalize_rule_string_raw(self):
        """Test normalizing rule with string raw value."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_numeric_raw(self):
        """Test normalizing rule with numeric raw value."""
        result = normalize_rule("flake8", 501)
        assert result == "flake8:501"

    def test_normalize_rule_case_insensitive_tool(self):
        """Test normalizing rule with case insensitive tool."""
        result = normalize_rule("FLAKE8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_mypy_special_case(self):
        """Test normalizing rule for mypy special case."""
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"

    def test_normalize_rule_bandit_special_case(self):
        """Test normalizing rule for bandit special case."""
        result = normalize_rule("bandit", "B101")
        assert result == "bandit:B101"

    def test_normalize_rule_eslint_special_case(self):
        """Test normalizing rule for eslint special case."""
        result = normalize_rule("eslint", "no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_jest_special_case(self):
        """Test normalizing rule for jest special case."""
        result = normalize_rule("jest", "test-name")
        assert result == "jest:test-name"

    def test_normalize_rule_complex_raw_value(self):
        """Test normalizing rule with complex raw value."""
        result = normalize_rule("custom", "complex-rule-123")
        assert result == "custom:complex-rule-123"

    def test_normalize_rule_whitespace_handling(self):
        """Test normalizing rule with whitespace in values."""
        result = normalize_rule("  flake8  ", "  E501  ")
        assert result == "  flake8  :  E501  "

    def test_normalize_rule_special_characters(self):
        """Test normalizing rule with special characters."""
        result = normalize_rule("tool", "rule-with-special-chars!@#$%")
        assert result == "tool:rule-with-special-chars!@#$%"

    def test_normalize_rule_unicode_characters(self):
        """Test normalizing rule with unicode characters."""
        result = normalize_rule("tool", "rule-with-unicode-ñáéíóú")
        assert result == "tool:rule-with-unicode-ñáéíóú"
