"""
Basic test coverage for src/ai_guard/generators/config_loader.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the config_loader module
from src.ai_guard.generators.config_loader import (
    _get_toml_loader,
    load_testgen_config,
    _load_toml_config,
    _load_env_config,
    _get_env_api_key
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


class TestLoadTestgenConfig(unittest.TestCase):
    """Test load_testgen_config function."""
    
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
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_with_path(self, mock_get_loader):
        """Test load_testgen_config with specific config path."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key"}
        }
        
        with open("test-config.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"')
        
        result = load_testgen_config("test-config.toml")
        self.assertEqual(result.llm_provider, "openai")
        self.assertEqual(result.llm_api_key, "test_key")
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_default_paths(self, mock_get_loader):
        """Test load_testgen_config with default config paths."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "anthropic", "api_key": "test_key"}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "anthropic"\napi_key = "test_key"')
        
        result = load_testgen_config()
        self.assertEqual(result.llm_provider, "anthropic")
        self.assertEqual(result.llm_api_key, "test_key")
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_hidden_file(self, mock_get_loader):
        """Test load_testgen_config with hidden config file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key"}
        }
        
        with open(".ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"')
        
        result = load_testgen_config()
        self.assertEqual(result.llm_provider, "openai")
        self.assertEqual(result.llm_api_key, "test_key")
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_no_file(self, mock_get_loader):
        """Test load_testgen_config with no config file."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.side_effect = Exception("File not found")
        
        result = load_testgen_config()
        self.assertEqual(result.llm_provider, "openai")  # Default value
        self.assertEqual(result.llm_api_key, "")  # Default value
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_override(self, mock_get_loader):
        """Test load_testgen_config with environment variable override."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key"}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_PROVIDER': 'anthropic'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "anthropic")
            self.assertEqual(result.llm_api_key, "test_key")
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_api_key(self, mock_get_loader):
        """Test load_testgen_config with environment API key."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key"}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_API_KEY': 'env_key'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "env_key")
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_model(self, mock_get_loader):
        """Test load_testgen_config with environment model."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "model": "gpt-4"}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nmodel = "gpt-4"')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_MODEL': 'gpt-3.5-turbo'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_model, "gpt-3.5-turbo")
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_temperature(self, mock_get_loader):
        """Test load_testgen_config with environment temperature."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "temperature": 0.7}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\ntemperature = 0.7')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_TEMPERATURE': '0.9'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_temperature, 0.9)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_max_tokens(self, mock_get_loader):
        """Test load_testgen_config with environment max_tokens."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "max_tokens": 1000}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nmax_tokens = 1000')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_MAX_TOKENS': '2000'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_max_tokens, 2000)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_timeout(self, mock_get_loader):
        """Test load_testgen_config with environment timeout."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "timeout": 30}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\ntimeout = 30')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_TIMEOUT': '60'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_timeout, 60)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retries(self, mock_get_loader):
        """Test load_testgen_config with environment retries."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retries": 3}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretries = 3')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRIES': '5'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retries, 5)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_delay(self, mock_get_loader):
        """Test load_testgen_config with environment retry_delay."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_delay": 1}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_delay = 1')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_DELAY': '2'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_delay, 2)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_backoff(self, mock_get_loader):
        """Test load_testgen_config with environment retry_backoff."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_backoff": 1.5}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_backoff = 1.5')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_BACKOFF': '2.0'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_backoff, 2.0)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_jitter(self, mock_get_loader):
        """Test load_testgen_config with environment retry_jitter."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_jitter": 0.1}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_jitter = 0.1')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_JITTER': '0.2'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_jitter, 0.2)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_max_delay(self, mock_get_loader):
        """Test load_testgen_config with environment retry_max_delay."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_max_delay": 60}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_max_delay = 60')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_MAX_DELAY': '120'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_max_delay, 120)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_exponential_base(self, mock_get_loader):
        """Test load_testgen_config with environment retry_exponential_base."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_exponential_base": 2}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_exponential_base = 2')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_EXPONENTIAL_BASE': '3'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_exponential_base, 3)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_exponential_max(self, mock_get_loader):
        """Test load_testgen_config with environment retry_exponential_max."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_exponential_max": 10}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_exponential_max = 10')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_EXPONENTIAL_MAX': '20'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_exponential_max, 20)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_exponential_min(self, mock_get_loader):
        """Test load_testgen_config with environment retry_exponential_min."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_exponential_min": 1}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_exponential_min = 1')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_EXPONENTIAL_MIN': '2'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_exponential_min, 2)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_exponential_max_attempts(self, mock_get_loader):
        """Test load_testgen_config with environment retry_exponential_max_attempts."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_exponential_max_attempts": 5}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_exponential_max_attempts = 5')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_EXPONENTIAL_MAX_ATTEMPTS': '10'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_exponential_max_attempts, 10)
    
    @patch('src.ai_guard.generators.config_loader._get_toml_loader')
    def test_load_testgen_config_environment_retry_exponential_max_attempts_invalid(self, mock_get_loader):
        """Test load_testgen_config with invalid environment retry_exponential_max_attempts."""
        mock_loader = MagicMock()
        mock_get_loader.return_value = mock_loader
        mock_loader.load.return_value = {
            "llm": {"provider": "openai", "api_key": "test_key", "retry_exponential_max_attempts": 5}
        }
        
        with open("ai-guard-testgen.toml", "w") as f:
            f.write('[llm]\nprovider = "openai"\napi_key = "test_key"\nretry_exponential_max_attempts = 5')
        
        with patch.dict(os.environ, {'AI_GUARD_LLM_RETRY_EXPONENTIAL_MAX_ATTEMPTS': 'invalid'}):
            result = load_testgen_config()
            self.assertEqual(result.llm_provider, "openai")
            self.assertEqual(result.llm_api_key, "test_key")
            self.assertEqual(result.llm_retry_exponential_max_attempts, 5)  # Should keep original value


if __name__ == '__main__':
    unittest.main()
