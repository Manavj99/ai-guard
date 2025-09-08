"""Focused tests for config.py module to improve coverage."""

import unittest
from unittest.mock import patch, mock_open
import tempfile
import os

from src.ai_guard.config import (
    Gates,
    Config,
    load_config,
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
    _get_toml_loader
)


class TestGates(unittest.TestCase):
    """Test Gates dataclass."""

    def test_gates_creation(self):
        """Test creating Gates instance."""
        gates = Gates(
            min_coverage=85,
            fail_on_bandit=True,
            fail_on_lint=True,
            fail_on_mypy=True
        )
        
        self.assertEqual(gates.min_coverage, 85)
        self.assertTrue(gates.fail_on_bandit)
        self.assertTrue(gates.fail_on_lint)
        self.assertTrue(gates.fail_on_mypy)

    def test_gates_default_values(self):
        """Test Gates with default values."""
        gates = Gates()
        
        self.assertEqual(gates.min_coverage, 80)
        self.assertTrue(gates.fail_on_bandit)
        self.assertTrue(gates.fail_on_lint)
        self.assertTrue(gates.fail_on_mypy)


class TestConfigFunctions(unittest.TestCase):
    """Test config module functions."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        
        self.assertIsNotNone(config)
        self.assertIn("min_coverage", config)
        self.assertIn("skip_tests", config)
        self.assertIn("report_format", config)

    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        config = {
            "min_coverage": 80,
            "skip_tests": False,
            "report_format": "sarif"
        }
        
        result = validate_config(config)
        self.assertTrue(result)

    def test_validate_config_invalid(self):
        """Test validating an invalid configuration."""
        config = {
            "min_coverage": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_load_config_toml(self):
        """Test loading TOML configuration."""
        toml_content = """
[gates]
min_coverage = 85
"""
        
        with patch('builtins.open', mock_open(read_data=toml_content)):
            with patch('src.ai_guard.config._get_toml_loader') as mock_loader:
                mock_loader.return_value.load.return_value = {
                    "gates": {
                        "min_coverage": 85
                    }
                }
                config = load_config("config.toml")
                self.assertIsNotNone(config)
                self.assertEqual(config["min_coverage"], 85)

    def test_load_config_json(self):
        """Test loading JSON configuration."""
        json_content = """
{
    "min_coverage": 85,
    "skip_tests": true
}
"""
        
        with patch('builtins.open', mock_open(read_data=json_content)):
            with patch('json.load', return_value={
                "min_coverage": 85,
                "skip_tests": True
            }):
                config = load_config("config.json")
                self.assertIsNotNone(config)
                self.assertEqual(config["min_coverage"], 85)
                self.assertTrue(config["skip_tests"])

    def test_load_config_missing_file(self):
        """Test loading configuration from missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = load_config("missing.toml")
            # Should return default config when file is missing
            self.assertIsNotNone(config)
            self.assertIn("min_coverage", config)

    def test_load_config_invalid_format(self):
        """Test loading configuration with invalid format."""
        with patch('builtins.open', mock_open(read_data="invalid content")):
            with patch('src.ai_guard.config._get_toml_loader') as mock_loader:
                mock_loader.return_value.load.side_effect = Exception("Parse error")
                config = load_config("invalid.toml")
                # Should return default config on error
                self.assertIsNotNone(config)
                self.assertIn("min_coverage", config)

    def test_validate_config_missing_min_coverage(self):
        """Test validating configuration with missing min_coverage."""
        config = {
            "skip_tests": True
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_validate_config_invalid_coverage_threshold(self):
        """Test validating configuration with invalid coverage threshold."""
        config = {
            "min_coverage": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_validate_config_negative_coverage_threshold(self):
        """Test validating configuration with negative coverage threshold."""
        config = {
            "min_coverage": -10
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_validate_config_coverage_threshold_over_100(self):
        """Test validating configuration with coverage threshold over 100."""
        config = {
            "min_coverage": 150
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_validate_config_invalid_report_format(self):
        """Test validating configuration with invalid report format."""
        config = {
            "min_coverage": 80,
            "report_format": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_validate_config_invalid_llm_provider(self):
        """Test validating configuration with invalid LLM provider."""
        config = {
            "min_coverage": 80,
            "llm_provider": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)

    def test_validate_config_invalid_boolean_field(self):
        """Test validating configuration with invalid boolean field."""
        config = {
            "min_coverage": 80,
            "skip_tests": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)


class TestAdditionalConfigFunctions(unittest.TestCase):
    """Test additional config module functions."""

    def test_merge_configs_basic(self):
        """Test basic config merging."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {"skip_tests": True}
        
        result = merge_configs(base, override)
        self.assertEqual(result["min_coverage"], 80)
        self.assertTrue(result["skip_tests"])

    def test_merge_configs_none_override(self):
        """Test merging with None override."""
        base = {"min_coverage": 80}
        result = merge_configs(base, None)
        self.assertEqual(result, base)

    def test_merge_configs_all_override(self):
        """Test merging when all main fields are overridden."""
        base = {"min_coverage": 80, "skip_tests": False}
        override = {
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "test.sarif",
            "enhanced_testgen": True,
            "llm_provider": "openai",
            "llm_api_key": "test",
            "llm_model": "gpt-3.5"
        }
        
        result = merge_configs(base, override)
        self.assertEqual(result, override)

    def test_parse_config_value_auto_bool(self):
        """Test auto-parsing boolean values."""
        self.assertTrue(parse_config_value("true"))
        self.assertFalse(parse_config_value("false"))

    def test_parse_config_value_auto_int(self):
        """Test auto-parsing integer values."""
        self.assertEqual(parse_config_value("42"), 42)

    def test_parse_config_value_auto_float(self):
        """Test auto-parsing float values."""
        self.assertEqual(parse_config_value("3.14"), 3.14)

    def test_parse_config_value_auto_string(self):
        """Test auto-parsing string values."""
        self.assertEqual(parse_config_value("hello"), "hello")

    def test_parse_config_value_specific_types(self):
        """Test parsing with specific types."""
        self.assertEqual(parse_config_value("42", "int"), 42)
        self.assertEqual(parse_config_value("3.14", "float"), 3.14)
        self.assertEqual(parse_config_value("true", "bool"), True)
        self.assertEqual(parse_config_value("hello", "string"), "hello")

    def test_parse_config_value_none(self):
        """Test parsing None value."""
        self.assertIsNone(parse_config_value(None))

    def test_parse_config_value_invalid_type(self):
        """Test parsing with invalid type."""
        with self.assertRaises(ValueError):
            parse_config_value("hello", "invalid")

    def test_parse_config_value_invalid_bool(self):
        """Test parsing invalid boolean."""
        with self.assertRaises(ValueError):
            parse_config_value("maybe", "bool")

    def test_get_toml_loader(self):
        """Test TOML loader selection."""
        loader = _get_toml_loader()
        self.assertIsNotNone(loader)


class TestConfigClass(unittest.TestCase):
    """Test Config class."""

    def test_config_creation(self):
        """Test creating Config instance."""
        with patch('src.ai_guard.config.load_config', return_value={"min_coverage": 85}):
            config = Config("test.toml")
            self.assertEqual(config.min_coverage, 85)

    def test_config_properties(self):
        """Test Config properties."""
        test_config = {
            "min_coverage": 90,
            "skip_tests": True,
            "report_format": "json",
            "report_path": "test.sarif",
            "enhanced_testgen": True,
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3",
            "fail_on_bandit": False,
            "fail_on_lint": False,
            "fail_on_mypy": False
        }
        
        with patch('src.ai_guard.config.load_config', return_value=test_config):
            config = Config()
            self.assertEqual(config.min_coverage, 90)
            self.assertTrue(config.skip_tests)
            self.assertEqual(config.report_format, "json")
            self.assertEqual(config.report_path, "test.sarif")
            self.assertTrue(config.enhanced_testgen)
            self.assertEqual(config.llm_provider, "anthropic")
            self.assertEqual(config.llm_api_key, "test-key")
            self.assertEqual(config.llm_model, "claude-3")
            self.assertFalse(config.fail_on_bandit)
            self.assertFalse(config.fail_on_lint)
            self.assertFalse(config.fail_on_mypy)

    def test_config_get_set(self):
        """Test Config get and set methods."""
        with patch('src.ai_guard.config.load_config', return_value={"min_coverage": 80}):
            config = Config()
            self.assertEqual(config.get("min_coverage"), 80)
            self.assertEqual(config.get("nonexistent", "default"), "default")
            
            config.set("test_key", "test_value")
            self.assertEqual(config.get("test_key"), "test_value")

    def test_config_reload(self):
        """Test Config reload method."""
        with patch('src.ai_guard.config.load_config') as mock_load:
            mock_load.return_value = {"min_coverage": 80}
            config = Config()
            
            mock_load.return_value = {"min_coverage": 90}
            config.reload()
            self.assertEqual(config.min_coverage, 90)


if __name__ == "__main__":
    unittest.main()
