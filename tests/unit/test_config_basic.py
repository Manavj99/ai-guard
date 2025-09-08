"""
Basic test coverage for src/ai_guard/config.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import json

# Import the config module
from src.ai_guard.config import (
    _get_toml_loader,
    get_default_config,
    validate_config,
    merge_configs,
    load_config
)


class TestGetTomlLoader(unittest.TestCase):
    """Test _get_toml_loader function."""
    
    @patch('importlib.import_module')
    def test_get_toml_loader_tomllib(self, mock_import):
        """Test _get_toml_loader with tomllib available."""
        mock_tomllib = MagicMock()
        mock_import.side_effect = lambda name: mock_tomllib if name == 'tomllib' else ModuleNotFoundError()
        
        result = _get_toml_loader()
        self.assertEqual(result, mock_tomllib)
    
    @patch('importlib.import_module')
    def test_get_toml_loader_tomli(self, mock_import):
        """Test _get_toml_loader with tomli fallback."""
        mock_tomli = MagicMock()
        mock_import.side_effect = lambda name: (
            ModuleNotFoundError() if name == 'tomllib' else mock_tomli
        )
        
        result = _get_toml_loader()
        self.assertEqual(result, mock_tomli)
    
    @patch('importlib.import_module')
    def test_get_toml_loader_no_toml(self, mock_import):
        """Test _get_toml_loader with no TOML library available."""
        mock_import.side_effect = ModuleNotFoundError()
        
        with self.assertRaises(ModuleNotFoundError):
            _get_toml_loader()


class TestGetDefaultConfig(unittest.TestCase):
    """Test get_default_config function."""
    
    def test_get_default_config(self):
        """Test get_default_config returns correct default values."""
        config = get_default_config()
        
        self.assertEqual(config["min_coverage"], 80)
        self.assertFalse(config["skip_tests"])
        self.assertEqual(config["report_format"], "sarif")
        self.assertEqual(config["report_path"], "ai-guard.sarif")
        self.assertFalse(config["enhanced_testgen"])
        self.assertEqual(config["llm_provider"], "openai")
        self.assertEqual(config["llm_api_key"], "")
        self.assertEqual(config["llm_model"], "gpt-4")
        self.assertTrue(config["fail_on_bandit"])
        self.assertTrue(config["fail_on_lint"])
        self.assertTrue(config["fail_on_mypy"])


class TestValidateConfig(unittest.TestCase):
    """Test validate_config function."""
    
    def test_validate_config_valid(self):
        """Test validate_config with valid configuration."""
        config = {
            "min_coverage": 80,
            "report_format": "sarif",
            "llm_provider": "openai",
            "skip_tests": False,
            "enhanced_testgen": True,
            "fail_on_bandit": True,
            "fail_on_lint": True,
            "fail_on_mypy": True
        }
        
        result = validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_required_field(self):
        """Test validate_config with missing required field."""
        config = {
            "report_format": "sarif"
        }
        
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_min_coverage_type(self):
        """Test validate_config with invalid min_coverage type."""
        config = {
            "min_coverage": "80"
        }
        
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_min_coverage_negative(self):
        """Test validate_config with negative min_coverage."""
        config = {
            "min_coverage": -1
        }
        
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_min_coverage_over_100(self):
        """Test validate_config with min_coverage over 100."""
        config = {
            "min_coverage": 101
        }
        
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_report_format(self):
        """Test validate_config with invalid report_format."""
        config = {
            "min_coverage": 80,
            "report_format": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_llm_provider(self):
        """Test validate_config with invalid llm_provider."""
        config = {
            "min_coverage": 80,
            "llm_provider": "invalid"
        }
        
        result = validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_boolean_field(self):
        """Test validate_config with invalid boolean field."""
        config = {
            "min_coverage": 80,
            "skip_tests": "true"
        }
        
        result = validate_config(config)
        self.assertFalse(result)


class TestMergeConfigs(unittest.TestCase):
    """Test merge_configs function."""
    
    def test_merge_configs_override_none(self):
        """Test merge_configs with None override config."""
        base_config = {"min_coverage": 80, "report_format": "sarif"}
        override_config = None
        
        result = merge_configs(base_config, override_config)
        self.assertEqual(result, base_config)
        self.assertIsNot(result, base_config)  # Should be a copy
    
    def test_merge_configs_override_empty(self):
        """Test merge_configs with empty override config."""
        base_config = {"min_coverage": 80, "report_format": "sarif"}
        override_config = {}
        
        result = merge_configs(base_config, override_config)
        self.assertEqual(result, base_config)
    
    def test_merge_configs_override_values(self):
        """Test merge_configs with override values."""
        base_config = {"min_coverage": 80, "report_format": "sarif"}
        override_config = {"min_coverage": 90, "report_format": "json"}
        
        result = merge_configs(base_config, override_config)
        self.assertEqual(result["min_coverage"], 90)
        self.assertEqual(result["report_format"], "json")
    
    def test_merge_configs_override_new_field(self):
        """Test merge_configs with new field in override."""
        base_config = {"min_coverage": 80}
        override_config = {"new_field": "value"}
        
        result = merge_configs(base_config, override_config)
        self.assertEqual(result["min_coverage"], 80)
        self.assertEqual(result["new_field"], "value")
    
    def test_merge_configs_nested_override(self):
        """Test merge_configs with nested override."""
        base_config = {
            "min_coverage": 80,
            "llm": {"provider": "openai", "model": "gpt-4"}
        }
        override_config = {
            "llm": {"provider": "anthropic"}
        }
        
        result = merge_configs(base_config, override_config)
        self.assertEqual(result["min_coverage"], 80)
        self.assertEqual(result["llm"]["provider"], "anthropic")
        self.assertEqual(result["llm"]["model"], "gpt-4")


class TestLoadConfig(unittest.TestCase):
    """Test load_config function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_toml_file(self, mock_get_loader):
        """Test load_config with TOML file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {"min_coverage": 90}
        
        with open("ai-guard.toml", "w") as f:
            f.write('min_coverage = 90')
        
        result = load_config()
        self.assertEqual(result["min_coverage"], 90)
        mock_loader.load.assert_called_once()
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_json_file(self, mock_get_loader):
        """Test load_config with JSON file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.side_effect = Exception("Not TOML")
        
        with open("ai-guard.json", "w") as f:
            json.dump({"min_coverage": 85}, f)
        
        result = load_config()
        self.assertEqual(result["min_coverage"], 85)
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_no_file(self, mock_get_loader):
        """Test load_config with no config file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.side_effect = Exception("Not TOML")
        
        result = load_config()
        self.assertEqual(result["min_coverage"], 80)  # Default value
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_invalid_toml(self, mock_get_loader):
        """Test load_config with invalid TOML file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.side_effect = Exception("Invalid TOML")
        
        with open("ai-guard.toml", "w") as f:
            f.write('invalid toml content')
        
        result = load_config()
        self.assertEqual(result["min_coverage"], 80)  # Default value
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_invalid_json(self, mock_get_loader):
        """Test load_config with invalid JSON file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.side_effect = Exception("Not TOML")
        
        with open("ai-guard.json", "w") as f:
            f.write('invalid json content')
        
        result = load_config()
        self.assertEqual(result["min_coverage"], 80)  # Default value
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override(self, mock_get_loader):
        """Test load_config with environment variable override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {"min_coverage": 90}
        
        with open("ai-guard.toml", "w") as f:
            f.write('min_coverage = 90')
        
        with patch.dict(os.environ, {'AI_GUARD_MIN_COVERAGE': '95'}):
            result = load_config()
            self.assertEqual(result["min_coverage"], 95)
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override_boolean(self, mock_get_loader):
        """Test load_config with boolean environment variable override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {"skip_tests": False}
        
        with open("ai-guard.toml", "w") as f:
            f.write('skip_tests = false')
        
        with patch.dict(os.environ, {'AI_GUARD_SKIP_TESTS': 'true'}):
            result = load_config()
            self.assertTrue(result["skip_tests"])
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override_nested(self, mock_get_loader):
        """Test load_config with nested environment variable override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "model": "gpt-4"}
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\nmodel = "gpt-4"')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_PROVIDER': 'anthropic'}):
            result = load_config()
            self.assertEqual(result["llm"]["provider"], "anthropic")
            self.assertEqual(result["llm"]["model"], "gpt-4")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override_new_field(self, mock_get_loader):
        """Test load_config with new field from environment."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {"min_coverage": 80}
        
        with open("ai-guard.toml", "w") as f:
            f.write('min_coverage = 80')
        
        with patch.dict(os.environ, {'AI_GUARD_NEW_FIELD': 'value'}):
            result = load_config()
            self.assertEqual(result["min_coverage"], 80)
            self.assertEqual(result["new_field"], "value")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override_invalid_type(self, mock_get_loader):
        """Test load_config with invalid type from environment."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {"min_coverage": 80}
        
        with open("ai-guard.toml", "w") as f:
            f.write('min_coverage = 80')
        
        with patch.dict(os.environ, {'AI_GUARD_MIN_COVERAGE': 'invalid'}):
            result = load_config()
            self.assertEqual(result["min_coverage"], 80)  # Should keep original value
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override_boolean_invalid(self, mock_get_loader):
        """Test load_config with invalid boolean from environment."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {"skip_tests": False}
        
        with open("ai-guard.toml", "w") as f:
            f.write('skip_tests = false')
        
        with patch.dict(os.environ, {'AI_GUARD_SKIP_TESTS': 'invalid'}):
            result = load_config()
            self.assertFalse(result["skip_tests"])  # Should keep original value


if __name__ == '__main__':
    unittest.main()
