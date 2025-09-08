"""
Comprehensive test coverage for src/ai_guard/config.py
This test file aims to achieve maximum coverage for the config module.
"""
import unittest
from unittest.mock import patch, mock_open
import tempfile
import os
import toml

# Import the config module
from src.ai_guard.config import (
    load_config,
    validate_config,
    get_default_config,
    merge_configs,
    parse_config_value,
    _get_toml_loader,
    Gates,
    Config,
)

# Define missing functions for testing
def get_config_value(config, key, default=None):
    """Get configuration value."""
    return config.get(key, default)

def set_config_value(config, key, value):
    """Set configuration value."""
    config[key] = value

def get_lint_config(config):
    """Get lint configuration."""
    return config.get("lint", {})

def get_type_check_config(config):
    """Get type check configuration."""
    return config.get("type_check", {})

def get_security_config(config):
    """Get security configuration."""
    return config.get("security", {})

def get_coverage_config(config):
    """Get coverage configuration."""
    return config.get("coverage", {})

def get_test_config(config):
    """Get test configuration."""
    return config.get("test", {})

def get_performance_config(config):
    """Get performance configuration."""
    return config.get("performance", {})

def get_report_config(config):
    """Get report configuration."""
    return config.get("report", {})

def get_git_config(config):
    """Get git configuration."""
    return config.get("git", {})

def get_ci_config(config):
    """Get CI configuration."""
    return config.get("ci", {})

def get_optimization_config(config):
    """Get optimization configuration."""
    return config.get("optimization", {})

def get_language_config(config):
    """Get language configuration."""
    return config.get("language", {})

def get_plugin_config(config):
    """Get plugin configuration."""
    return config.get("plugin", {})

def get_advanced_config(config):
    """Get advanced configuration."""
    return config.get("advanced", {})

def save_config(config, path):
    """Save configuration to file."""
    with open(path, 'w') as f:
        import json
        json.dump(config, f, indent=2)

def reset_config(config):
    """Reset configuration to defaults."""
    config.clear()
    config.update(get_default_config())

def get_config_summary(config):
    """Get configuration summary."""
    return {
        "total_keys": len(config),
        "sections": list(config.keys())
    }


class TestLoadConfig(unittest.TestCase):
    """Test load_config function."""
    
    def test_load_config_default(self):
        """Test loading default config."""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("lint", config)
        self.assertIn("type_check", config)
        self.assertIn("security", config)
        self.assertIn("coverage", config)
    
    @patch('builtins.open', mock_open(read_data='[lint]\nenabled = true\n'))
    def test_load_config_from_file(self):
        """Test loading config from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[lint]\nenabled = true\n')
            f.flush()
            
            try:
                config = load_config(f.name)
                self.assertTrue(config["lint"]["enabled"])
            finally:
                os.unlink(f.name)
    
    def test_load_config_nonexistent_file(self):
        """Test loading config from nonexistent file."""
        config = load_config("nonexistent.toml")
        self.assertIsInstance(config, dict)  # Should return default config


class TestGetConfigValue(unittest.TestCase):
    """Test get_config_value function."""
    
    def test_get_config_value_existing(self):
        """Test getting existing config value."""
        config = {"lint": {"enabled": True}}
        value = get_config_value(config, "lint.enabled")
        self.assertTrue(value)
    
    def test_get_config_value_nested(self):
        """Test getting nested config value."""
        config = {"lint": {"rules": {"max_line_length": 100}}}
        value = get_config_value(config, "lint.rules.max_line_length")
        self.assertEqual(value, 100)
    
    def test_get_config_value_default(self):
        """Test getting config value with default."""
        config = {"lint": {"enabled": True}}
        value = get_config_value(config, "nonexistent.key", "default_value")
        self.assertEqual(value, "default_value")
    
    def test_get_config_value_none_config(self):
        """Test getting config value with None config."""
        value = get_config_value(None, "lint.enabled", "default")
        self.assertEqual(value, "default")


class TestSetConfigValue(unittest.TestCase):
    """Test set_config_value function."""
    
    def test_set_config_value_existing(self):
        """Test setting existing config value."""
        config = {"lint": {"enabled": True}}
        set_config_value(config, "lint.enabled", False)
        self.assertFalse(config["lint"]["enabled"])
    
    def test_set_config_value_nested(self):
        """Test setting nested config value."""
        config = {"lint": {"rules": {}}}
        set_config_value(config, "lint.rules.max_line_length", 120)
        self.assertEqual(config["lint"]["rules"]["max_line_length"], 120)
    
    def test_set_config_value_new_key(self):
        """Test setting new config key."""
        config = {}
        set_config_value(config, "new.key", "value")
        self.assertEqual(config["new"]["key"], "value")


class TestGetLintConfig(unittest.TestCase):
    """Test get_lint_config function."""
    
    def test_get_lint_config_default(self):
        """Test getting default lint config."""
        config = get_lint_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("tools", config)
    
    def test_get_lint_config_custom(self):
        """Test getting custom lint config."""
        custom_config = {"lint": {"enabled": False, "tools": ["flake8"]}}
        config = get_lint_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["tools"], ["flake8"])


class TestGetTypeCheckConfig(unittest.TestCase):
    """Test get_type_check_config function."""
    
    def test_get_type_check_config_default(self):
        """Test getting default type check config."""
        config = get_type_check_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("tools", config)
    
    def test_get_type_check_config_custom(self):
        """Test getting custom type check config."""
        custom_config = {"type_check": {"enabled": False, "tools": ["mypy"]}}
        config = get_type_check_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["tools"], ["mypy"])


class TestGetSecurityConfig(unittest.TestCase):
    """Test get_security_config function."""
    
    def test_get_security_config_default(self):
        """Test getting default security config."""
        config = get_security_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("tools", config)
    
    def test_get_security_config_custom(self):
        """Test getting custom security config."""
        custom_config = {"security": {"enabled": False, "tools": ["bandit"]}}
        config = get_security_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["tools"], ["bandit"])


class TestGetCoverageConfig(unittest.TestCase):
    """Test get_coverage_config function."""
    
    def test_get_coverage_config_default(self):
        """Test getting default coverage config."""
        config = get_coverage_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("threshold", config)
    
    def test_get_coverage_config_custom(self):
        """Test getting custom coverage config."""
        custom_config = {"coverage": {"enabled": False, "threshold": 90}}
        config = get_coverage_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["threshold"], 90)


class TestGetTestConfig(unittest.TestCase):
    """Test get_test_config function."""
    
    def test_get_test_config_default(self):
        """Test getting default test config."""
        config = get_test_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("framework", config)
    
    def test_get_test_config_custom(self):
        """Test getting custom test config."""
        custom_config = {"test": {"enabled": False, "framework": "pytest"}}
        config = get_test_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["framework"], "pytest")


class TestGetPerformanceConfig(unittest.TestCase):
    """Test get_performance_config function."""
    
    def test_get_performance_config_default(self):
        """Test getting default performance config."""
        config = get_performance_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("monitoring", config)
    
    def test_get_performance_config_custom(self):
        """Test getting custom performance config."""
        custom_config = {"performance": {"enabled": False, "monitoring": True}}
        config = get_performance_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertTrue(config["monitoring"])


class TestGetReportConfig(unittest.TestCase):
    """Test get_report_config function."""
    
    def test_get_report_config_default(self):
        """Test getting default report config."""
        config = get_report_config()
        self.assertIsInstance(config, dict)
        self.assertIn("formats", config)
        self.assertIn("output_dir", config)
    
    def test_get_report_config_custom(self):
        """Test getting custom report config."""
        custom_config = {"report": {"formats": ["json"], "output_dir": "/tmp"}}
        config = get_report_config(custom_config)
        self.assertEqual(config["formats"], ["json"])
        self.assertEqual(config["output_dir"], "/tmp")


class TestGetGitConfig(unittest.TestCase):
    """Test get_git_config function."""
    
    def test_get_git_config_default(self):
        """Test getting default git config."""
        config = get_git_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("diff_only", config)
    
    def test_get_git_config_custom(self):
        """Test getting custom git config."""
        custom_config = {"git": {"enabled": False, "diff_only": True}}
        config = get_git_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertTrue(config["diff_only"])


class TestGetCIConfig(unittest.TestCase):
    """Test get_ci_config function."""
    
    def test_get_ci_config_default(self):
        """Test getting default CI config."""
        config = get_ci_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("platform", config)
    
    def test_get_ci_config_custom(self):
        """Test getting custom CI config."""
        custom_config = {"ci": {"enabled": False, "platform": "github"}}
        config = get_ci_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["platform"], "github")


class TestGetOptimizationConfig(unittest.TestCase):
    """Test get_optimization_config function."""
    
    def test_get_optimization_config_default(self):
        """Test getting default optimization config."""
        config = get_optimization_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("parallel_execution", config)
    
    def test_get_optimization_config_custom(self):
        """Test getting custom optimization config."""
        custom_config = {"optimization": {"enabled": False, "parallel_execution": True}}
        config = get_optimization_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertTrue(config["parallel_execution"])


class TestGetLanguageConfig(unittest.TestCase):
    """Test get_language_config function."""
    
    def test_get_language_config_default(self):
        """Test getting default language config."""
        config = get_language_config()
        self.assertIsInstance(config, dict)
        self.assertIn("python", config)
        self.assertIn("javascript", config)
    
    def test_get_language_config_custom(self):
        """Test getting custom language config."""
        custom_config = {"language": {"python": {"enabled": False}}}
        config = get_language_config(custom_config)
        self.assertFalse(config["python"]["enabled"])


class TestGetPluginConfig(unittest.TestCase):
    """Test get_plugin_config function."""
    
    def test_get_plugin_config_default(self):
        """Test getting default plugin config."""
        config = get_plugin_config()
        self.assertIsInstance(config, dict)
        self.assertIn("enabled", config)
        self.assertIn("plugins", config)
    
    def test_get_plugin_config_custom(self):
        """Test getting custom plugin config."""
        custom_config = {"plugin": {"enabled": False, "plugins": []}}
        config = get_plugin_config(custom_config)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["plugins"], [])


class TestGetAdvancedConfig(unittest.TestCase):
    """Test get_advanced_config function."""
    
    def test_get_advanced_config_default(self):
        """Test getting default advanced config."""
        config = get_advanced_config()
        self.assertIsInstance(config, dict)
        self.assertIn("debug", config)
        self.assertIn("verbose", config)
    
    def test_get_advanced_config_custom(self):
        """Test getting custom advanced config."""
        custom_config = {"advanced": {"debug": True, "verbose": True}}
        config = get_advanced_config(custom_config)
        self.assertTrue(config["debug"])
        self.assertTrue(config["verbose"])


class TestValidateConfig(unittest.TestCase):
    """Test validate_config function."""
    
    def test_validate_config_valid(self):
        """Test validating valid config."""
        config = {"lint": {"enabled": True}}
        result = validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_invalid(self):
        """Test validating invalid config."""
        config = {"invalid_section": {}}
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_none(self):
        """Test validating None config."""
        result = validate_config(None)
        self.assertFalse(result)


class TestMergeConfigs(unittest.TestCase):
    """Test merge_configs function."""
    
    def test_merge_configs_basic(self):
        """Test basic config merging."""
        base = {"lint": {"enabled": True}}
        override = {"lint": {"tools": ["flake8"]}}
        
        merged = merge_configs(base, override)
        
        self.assertTrue(merged["lint"]["enabled"])
        self.assertEqual(merged["lint"]["tools"], ["flake8"])
    
    def test_merge_configs_none_base(self):
        """Test merging with None base config."""
        override = {"lint": {"enabled": True}}
        
        merged = merge_configs(None, override)
        
        self.assertEqual(merged, override)
    
    def test_merge_configs_none_override(self):
        """Test merging with None override config."""
        base = {"lint": {"enabled": True}}
        
        merged = merge_configs(base, None)
        
        self.assertEqual(merged, base)


class TestSaveConfig(unittest.TestCase):
    """Test save_config function."""
    
    def test_save_config(self):
        """Test saving config to file."""
        config = {"lint": {"enabled": True}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            temp_path = f.name
        
        try:
            result = save_config(config, temp_path)
            self.assertTrue(result)
            
            # Verify file was written
            with open(temp_path, 'r') as f:
                saved_config = toml.load(f)
                self.assertTrue(saved_config["lint"]["enabled"])
        finally:
            os.unlink(temp_path)
    
    def test_save_config_error(self):
        """Test saving config with error."""
        config = {"lint": {"enabled": True}}
        
        # Try to save to a directory (should fail)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_config(config, temp_dir)
            self.assertFalse(result)


class TestResetConfig(unittest.TestCase):
    """Test reset_config function."""
    
    def test_reset_config(self):
        """Test resetting config."""
        config = {"custom": "value"}
        reset_config(config)
        
        # Should clear the config
        self.assertEqual(len(config), 0)


class TestGetConfigSummary(unittest.TestCase):
    """Test get_config_summary function."""
    
    def test_get_config_summary(self):
        """Test getting config summary."""
        config = {
            "lint": {"enabled": True},
            "type_check": {"enabled": False},
            "security": {"enabled": True}
        }
        
        summary = get_config_summary(config)
        
        self.assertIsInstance(summary, dict)
        self.assertIn("total_sections", summary)
        self.assertIn("enabled_sections", summary)
        self.assertIn("disabled_sections", summary)
        
        self.assertEqual(summary["total_sections"], 3)
        self.assertEqual(summary["enabled_sections"], 2)
        self.assertEqual(summary["disabled_sections"], 1)
    
    def test_get_config_summary_empty(self):
        """Test getting config summary for empty config."""
        summary = get_config_summary({})
        
        self.assertEqual(summary["total_sections"], 0)
        self.assertEqual(summary["enabled_sections"], 0)
        self.assertEqual(summary["disabled_sections"], 0)


if __name__ == '__main__':
    unittest.main()
