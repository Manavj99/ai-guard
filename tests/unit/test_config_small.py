"""
Small test coverage for src/ai_guard/config.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the config module
from src.ai_guard.config import (
    load_config,
    validate_config,
    merge_configs
)


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
    def test_load_config_with_path(self, mock_get_loader):
        """Test load_config with specific config path."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("test-config.toml", "w") as f:
            f.write('[quality_gates]\nlint = {enabled = true, command = "flake8"}')
        
        result = load_config("test-config.toml")
        self.assertIn("quality_gates", result)
        self.assertTrue(result["quality_gates"]["lint"]["enabled"])
        self.assertEqual(result["quality_gates"]["lint"]["command"], "flake8")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_default_paths(self, mock_get_loader):
        """Test load_config with default config paths."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[quality_gates]\nlint = {enabled = true, command = "flake8"}')
        
        result = load_config()
        self.assertIn("quality_gates", result)
        self.assertTrue(result["quality_gates"]["lint"]["enabled"])
        self.assertEqual(result["quality_gates"]["lint"]["command"], "flake8")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_hidden_file(self, mock_get_loader):
        """Test load_config with hidden config file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open(".ai-guard.toml", "w") as f:
            f.write('[quality_gates]\nlint = {enabled = true, command = "flake8"}')
        
        result = load_config()
        self.assertIn("quality_gates", result)
        self.assertTrue(result["quality_gates"]["lint"]["enabled"])
        self.assertEqual(result["quality_gates"]["lint"]["command"], "flake8")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_no_file(self, mock_get_loader):
        """Test load_config with no config file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.side_effect = Exception("File not found")
        
        result = load_config()
        self.assertEqual(result, {})
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_override(self, mock_get_loader):
        """Test load_config with environment variable override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[quality_gates]\nlint = {enabled = true, command = "flake8"}')
        
        with patch.dict(os.environ, {'AI_GUARD_QUALITY_GATES_LINT_ENABLED': 'false'}):
            result = load_config()
            self.assertIn("quality_gates", result)
            self.assertFalse(result["quality_gates"]["lint"]["enabled"])
            self.assertEqual(result["quality_gates"]["lint"]["command"], "flake8")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_command_override(self, mock_get_loader):
        """Test load_config with environment command override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[quality_gates]\nlint = {enabled = true, command = "flake8"}')
        
        with patch.dict(os.environ, {'AI_GUARD_QUALITY_GATES_LINT_COMMAND': 'custom-flake8'}):
            result = load_config()
            self.assertIn("quality_gates", result)
            self.assertTrue(result["quality_gates"]["lint"]["enabled"])
            self.assertEqual(result["quality_gates"]["lint"]["command"], "custom-flake8")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_static_types_override(self, mock_get_loader):
        """Test load_config with environment static_types override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[quality_gates]\nstatic_types = {enabled = true, command = "mypy"}')
        
        with patch.dict(os.environ, {'AI_GUARD_QUALITY_GATES_STATIC_TYPES_ENABLED': 'false'}):
            result = load_config()
            self.assertIn("quality_gates", result)
            self.assertFalse(result["quality_gates"]["static_types"]["enabled"])
            self.assertEqual(result["quality_gates"]["static_types"]["command"], "mypy")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_security_override(self, mock_get_loader):
        """Test load_config with environment security override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[quality_gates]\nsecurity = {enabled = true, command = "bandit"}')
        
        with patch.dict(os.environ, {'AI_GUARD_QUALITY_GATES_SECURITY_ENABLED': 'false'}):
            result = load_config()
            self.assertIn("quality_gates", result)
            self.assertFalse(result["quality_gates"]["security"]["enabled"])
            self.assertEqual(result["quality_gates"]["security"]["command"], "bandit")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_coverage_override(self, mock_get_loader):
        """Test load_config with environment coverage override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "quality_gates": {
                "lint": {"enabled": True, "command": "flake8"},
                "static_types": {"enabled": True, "command": "mypy"},
                "security": {"enabled": True, "command": "bandit"},
                "coverage": {"enabled": True, "command": "pytest"}
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[quality_gates]\ncoverage = {enabled = true, command = "pytest"}')
        
        with patch.dict(os.environ, {'AI_GUARD_QUALITY_GATES_COVERAGE_ENABLED': 'false'}):
            result = load_config()
            self.assertIn("quality_gates", result)
            self.assertFalse(result["quality_gates"]["coverage"]["enabled"])
            self.assertEqual(result["quality_gates"]["coverage"]["command"], "pytest")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_override(self, mock_get_loader):
        """Test load_config with environment SARIF override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_ENABLED': 'false'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertFalse(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_output_file_override(self, mock_get_loader):
        """Test load_config with environment SARIF output_file override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_OUTPUT_FILE': 'custom_output.sarif'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "custom_output.sarif")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_format_override(self, mock_get_loader):
        """Test load_config with environment SARIF format override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_FORMAT': 'sarif-2.0.0'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.0.0")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_version_override(self, mock_get_loader):
        """Test load_config with environment SARIF version override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0",
                "version": "2.1.0"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"\nversion = "2.1.0"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_VERSION': '2.0.0'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.1.0")
            self.assertEqual(result["sarif"]["version"], "2.0.0")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_tool_name_override(self, mock_get_loader):
        """Test load_config with environment SARIF tool_name override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0",
                "version": "2.1.0",
                "tool_name": "ai-guard"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"\nversion = "2.1.0"\ntool_name = "ai-guard"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_TOOL_NAME': 'custom-ai-guard'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.1.0")
            self.assertEqual(result["sarif"]["version"], "2.1.0")
            self.assertEqual(result["sarif"]["tool_name"], "custom-ai-guard")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_tool_version_override(self, mock_get_loader):
        """Test load_config with environment SARIF tool_version override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0",
                "version": "2.1.0",
                "tool_name": "ai-guard",
                "tool_version": "1.0.0"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"\nversion = "2.1.0"\ntool_name = "ai-guard"\ntool_version = "1.0.0"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_TOOL_VERSION': '2.0.0'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.1.0")
            self.assertEqual(result["sarif"]["version"], "2.1.0")
            self.assertEqual(result["sarif"]["tool_name"], "ai-guard")
            self.assertEqual(result["sarif"]["tool_version"], "2.0.0")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_tool_vendor_override(self, mock_get_loader):
        """Test load_config with environment SARIF tool_vendor override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0",
                "version": "2.1.0",
                "tool_name": "ai-guard",
                "tool_version": "1.0.0",
                "tool_vendor": "ai-guard-team"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"\nversion = "2.1.0"\ntool_name = "ai-guard"\ntool_version = "1.0.0"\ntool_vendor = "ai-guard-team"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_TOOL_VENDOR': 'custom-vendor'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.1.0")
            self.assertEqual(result["sarif"]["version"], "2.1.0")
            self.assertEqual(result["sarif"]["tool_name"], "ai-guard")
            self.assertEqual(result["sarif"]["tool_version"], "1.0.0")
            self.assertEqual(result["sarif"]["tool_vendor"], "custom-vendor")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_tool_vendor_url_override(self, mock_get_loader):
        """Test load_config with environment SARIF tool_vendor_url override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0",
                "version": "2.1.0",
                "tool_name": "ai-guard",
                "tool_version": "1.0.0",
                "tool_vendor": "ai-guard-team",
                "tool_vendor_url": "https://github.com/ai-guard-team/ai-guard"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"\nversion = "2.1.0"\ntool_name = "ai-guard"\ntool_version = "1.0.0"\ntool_vendor = "ai-guard-team"\ntool_vendor_url = "https://github.com/ai-guard-team/ai-guard"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_TOOL_VENDOR_URL': 'https://custom-vendor.com'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.1.0")
            self.assertEqual(result["sarif"]["version"], "2.1.0")
            self.assertEqual(result["sarif"]["tool_name"], "ai-guard")
            self.assertEqual(result["sarif"]["tool_version"], "1.0.0")
            self.assertEqual(result["sarif"]["tool_vendor"], "ai-guard-team")
            self.assertEqual(result["sarif"]["tool_vendor_url"], "https://custom-vendor.com")
    
    @patch('src.ai_guard.config._get_toml_loader')
    def test_load_config_environment_sarif_tool_vendor_url_invalid(self, mock_get_loader):
        """Test load_config with invalid environment SARIF tool_vendor_url override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "sarif": {
                "enabled": True,
                "output_file": "output.sarif",
                "format": "sarif-2.1.0",
                "version": "2.1.0",
                "tool_name": "ai-guard",
                "tool_version": "1.0.0",
                "tool_vendor": "ai-guard-team",
                "tool_vendor_url": "https://github.com/ai-guard-team/ai-guard"
            }
        }
        
        with open("ai-guard.toml", "w") as f:
            f.write('[sarif]\nenabled = true\noutput_file = "output.sarif"\nformat = "sarif-2.1.0"\nversion = "2.1.0"\ntool_name = "ai-guard"\ntool_version = "1.0.0"\ntool_vendor = "ai-guard-team"\ntool_vendor_url = "https://github.com/ai-guard-team/ai-guard"')
        
        with patch.dict(os.environ, {'AI_GUARD_SARIF_TOOL_VENDOR_URL': 'invalid-url'}):
            result = load_config()
            self.assertIn("sarif", result)
            self.assertTrue(result["sarif"]["enabled"])
            self.assertEqual(result["sarif"]["output_file"], "output.sarif")
            self.assertEqual(result["sarif"]["format"], "sarif-2.1.0")
            self.assertEqual(result["sarif"]["version"], "2.1.0")
            self.assertEqual(result["sarif"]["tool_name"], "ai-guard")
            self.assertEqual(result["sarif"]["tool_version"], "1.0.0")
            self.assertEqual(result["sarif"]["tool_vendor"], "ai-guard-team")
            self.assertEqual(result["sarif"]["tool_vendor_url"], "https://github.com/ai-guard-team/ai-guard")  # Should keep original value


if __name__ == '__main__':
    unittest.main()
