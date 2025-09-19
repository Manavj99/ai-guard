"""Comprehensive tests for parsers.common module."""

import pytest

from src.ai_guard.parsers.common import (
    _extract_mypy_rule,
    normalize_rule,
    _RULE_NORMALIZERS,
)


class TestExtractMypyRule:
    """Test _extract_mypy_rule function."""

    def test_extract_mypy_rule_with_brackets(self):
        """Test extracting rule from mypy error format with brackets."""
        result = _extract_mypy_rule("error[name-defined]")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_with_brackets_multiple(self):
        """Test extracting rule with multiple brackets."""
        result = _extract_mypy_rule("error[type-arg]")
        assert result == "mypy:type-arg"

    def test_extract_mypy_rule_with_brackets_complex(self):
        """Test extracting rule with complex bracket content."""
        result = _extract_mypy_rule("error[attr-defined, name-defined]")
        assert result == "mypy:attr-defined, name-defined"

    def test_extract_mypy_rule_no_brackets(self):
        """Test with rule that has no brackets."""
        result = _extract_mypy_rule("name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_already_prefixed(self):
        """Test with rule already prefixed with mypy:."""
        result = _extract_mypy_rule("mypy:name-defined")
        assert result == "mypy:name-defined"

    def test_extract_mypy_rule_empty_string(self):
        """Test with empty string."""
        result = _extract_mypy_rule("")
        assert result == "mypy:"

    def test_extract_mypy_rule_only_brackets(self):
        """Test with only brackets."""
        result = _extract_mypy_rule("[]")
        assert result == "mypy:"

    def test_extract_mypy_rule_malformed_brackets(self):
        """Test with malformed brackets."""
        result = _extract_mypy_rule("error[name-defined")
        assert result == "mypy:error[name-defined"

    def test_extract_mypy_rule_reverse_brackets(self):
        """Test with brackets in reverse order."""
        result = _extract_mypy_rule("error]name-defined[")
        assert result == "mypy:error]name-defined["

    def test_extract_mypy_rule_multiple_bracket_pairs(self):
        """Test with multiple bracket pairs (should take first)."""
        result = _extract_mypy_rule("error[first] and [second]")
        assert result == "mypy:first"

    def test_extract_mypy_rule_nested_brackets(self):
        """Test with nested brackets."""
        result = _extract_mypy_rule("error[outer[inner]]")
        assert result == "mypy:outer[inner]"


class TestNormalizeRule:
    """Test normalize_rule function."""

    def test_normalize_rule_flake8_with_colon(self):
        """Test flake8 rule already with colon."""
        result = normalize_rule("flake8", "flake8:E501")
        assert result == "flake8:E501"

    def test_normalize_rule_flake8_without_colon(self):
        """Test flake8 rule without colon."""
        result = normalize_rule("flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_mypy_with_brackets(self):
        """Test mypy rule with brackets."""
        result = normalize_rule("mypy", "error[name-defined]")
        assert result == "mypy:name-defined"

    def test_normalize_rule_mypy_without_brackets(self):
        """Test mypy rule without brackets."""
        result = normalize_rule("mypy", "name-defined")
        assert result == "mypy:name-defined"

    def test_normalize_rule_bandit_with_prefix(self):
        """Test bandit rule with prefix."""
        result = normalize_rule("bandit", "bandit:B101")
        assert result == "bandit:B101"

    def test_normalize_rule_bandit_without_prefix(self):
        """Test bandit rule without prefix."""
        result = normalize_rule("bandit", "B101")
        assert result == "bandit:B101"

    def test_normalize_rule_eslint_with_colon(self):
        """Test eslint rule with colon."""
        result = normalize_rule("eslint", "eslint:no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_eslint_without_colon(self):
        """Test eslint rule without colon."""
        result = normalize_rule("eslint", "no-unused")
        assert result == "eslint:no-unused"

    def test_normalize_rule_jest_with_colon(self):
        """Test jest rule with colon."""
        result = normalize_rule("jest", "jest:test-failed")
        assert result == "jest:test-failed"

    def test_normalize_rule_jest_without_colon(self):
        """Test jest rule without colon."""
        result = normalize_rule("jest", "test-failed")
        assert result == "jest:test-failed"

    def test_normalize_rule_unknown_tool(self):
        """Test with unknown tool."""
        result = normalize_rule("unknown", "rule123")
        assert result == "unknown:rule123"

    def test_normalize_rule_none_tool(self):
        """Test with None tool."""
        result = normalize_rule(None, "rule123")
        assert result == "none:rule123"

    def test_normalize_rule_empty_tool(self):
        """Test with empty tool."""
        result = normalize_rule("", "rule123")
        assert result == ":rule123"

    def test_normalize_rule_none_raw(self):
        """Test with None raw rule."""
        result = normalize_rule("flake8", None)
        assert result == "flake8:None"

    def test_normalize_rule_empty_raw(self):
        """Test with empty raw rule."""
        result = normalize_rule("flake8", "")
        assert result == "flake8:"

    def test_normalize_rule_non_string_raw(self):
        """Test with non-string raw rule."""
        result = normalize_rule("flake8", 123)
        assert result == "flake8:123"

    def test_normalize_rule_case_insensitive_tool(self):
        """Test that tool name is case insensitive."""
        result = normalize_rule("FLAKE8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_mixed_case_tool(self):
        """Test with mixed case tool name."""
        result = normalize_rule("Flake8", "E501")
        assert result == "flake8:E501"

    def test_normalize_rule_special_characters(self):
        """Test with special characters in rule."""
        result = normalize_rule("eslint", "no-unused-vars")
        assert result == "eslint:no-unused-vars"

    def test_normalize_rule_unicode_characters(self):
        """Test with unicode characters in rule."""
        result = normalize_rule("eslint", "no-unicode-测试")
        assert result == "eslint:no-unicode-测试"


class TestRuleNormalizers:
    """Test _RULE_NORMALIZERS dictionary."""

    def test_rule_normalizers_contains_expected_tools(self):
        """Test that normalizers contain expected tools."""
        expected_tools = ["flake8", "mypy", "bandit", "eslint", "jest"]
        for tool in expected_tools:
            assert tool in _RULE_NORMALIZERS

    def test_rule_normalizers_flake8_function(self):
        """Test flake8 normalizer function."""
        normalizer = _RULE_NORMALIZERS["flake8"]
        
        # Test with colon
        result = normalizer("flake8:E501")
        assert result == "flake8:E501"
        
        # Test without colon
        result = normalizer("E501")
        assert result == "flake8:E501"

    def test_rule_normalizers_mypy_function(self):
        """Test mypy normalizer function."""
        normalizer = _RULE_NORMALIZERS["mypy"]
        
        # Test with brackets
        result = normalizer("error[name-defined]")
        assert result == "mypy:name-defined"
        
        # Test without brackets
        result = normalizer("name-defined")
        assert result == "mypy:name-defined"

    def test_rule_normalizers_bandit_function(self):
        """Test bandit normalizer function."""
        normalizer = _RULE_NORMALIZERS["bandit"]
        
        # Test with prefix
        result = normalizer("bandit:B101")
        assert result == "bandit:B101"
        
        # Test without prefix
        result = normalizer("B101")
        assert result == "bandit:B101"

    def test_rule_normalizers_eslint_function(self):
        """Test eslint normalizer function."""
        normalizer = _RULE_NORMALIZERS["eslint"]
        
        # Test with colon
        result = normalizer("eslint:no-unused")
        assert result == "eslint:no-unused"
        
        # Test without colon
        result = normalizer("no-unused")
        assert result == "eslint:no-unused"

    def test_rule_normalizers_jest_function(self):
        """Test jest normalizer function."""
        normalizer = _RULE_NORMALIZERS["jest"]
        
        # Test with colon
        result = normalizer("jest:test-failed")
        assert result == "jest:test-failed"
        
        # Test without colon
        result = normalizer("test-failed")
        assert result == "jest:test-failed"

    def test_rule_normalizers_edge_cases(self):
        """Test normalizers with edge cases."""
        # Test empty strings
        for tool, normalizer in _RULE_NORMALIZERS.items():
            if tool == "mypy":
                result = normalizer("")
                assert result == "mypy:"
            else:
                result = normalizer("")
                assert result == f"{tool}:"

    def test_rule_normalizers_none_input(self):
        """Test normalizers with None input."""
        for tool, normalizer in _RULE_NORMALIZERS.items():
            if tool == "mypy":
                result = normalizer(None)
                assert result == "mypy:None"
            else:
                result = normalizer(None)
                assert result == f"{tool}:None"