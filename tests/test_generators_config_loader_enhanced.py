"""Enhanced tests for generators/config_loader module to achieve 80%+ coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock

from src.ai_guard.generators.config_loader import (
    load_testgen_config,
    _get_toml_loader,
    _load_toml_config,
    _load_env_config,
    _get_env_api_key
)


class TestGetTomlLoader:
    """Test _get_toml_loader function."""

    def test_get_toml_loader_tomllib_available(self):
        """Test _get_toml_loader when tomllib is available."""
        with patch('src.ai_guard.generators.config_loader.tomllib') as mock_tomllib:
            with patch('src.ai_guard.generators.config_loader.tomli', side_effect=ImportError):
                result = _get_toml_loader()
                assert result == mock_tomllib

    def test_get_toml_loader_tomli_fallback(self):
        """Test _get_toml_loader falls back to tomli when tomllib not available."""
        with patch('src.ai_guard.generators.config_loader.tomllib', side_effect=ModuleNotFoundError):
            with patch('src.ai_guard.generators.config_loader.tomli') as mock_tomli:
                result = _get_toml_loader()
                assert result == mock_tomli

    def test_get_toml_loader_both_unavailable(self):
        """Test _get_toml_loader when both libraries are unavailable."""
        with patch('src.ai_guard.generators.config_loader.tomllib', side_effect=ModuleNotFoundError):
            with patch('src.ai_guard.generators.config_loader.tomli', side_effect=ModuleNotFoundError):
                with pytest.raises(ModuleNotFoundError):
                    _get_toml_loader()


class TestLoadTomlConfig:
    """Test _load_toml_config function."""

    def test_load_toml_config_success(self):
        """Test _load_toml_config with successful file loading."""
        toml_content = """
[llm]
provider = "openai"
api_key = "test-key"
model = "gpt-4"

[testgen]
max_tests_per_file = 15
generate_mocks = false
"""
        
        with patch('builtins.open', mock_open(read_data=toml_content)):
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.loads.return_value = {
                    "llm": {
                        "provider": "openai",
                        "api_key": "test-key",
                        "model": "gpt-4"
                    },
                    "testgen": {
                        "max_tests_per_file": 15,
                        "generate_mocks": False
                    }
                }
                
                result = _load_toml_config("test.toml")
                
                assert result["llm"]["provider"] == "openai"
                assert result["llm"]["api_key"] == "test-key"
                assert result["llm"]["model"] == "gpt-4"
                assert result["testgen"]["max_tests_per_file"] == 15
                assert result["testgen"]["generate_mocks"] is False

    def test_load_toml_config_file_not_found(self):
        """Test _load_toml_config with file not found."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = _load_toml_config("nonexistent.toml")
            assert result == {}

    def test_load_toml_config_parse_error(self):
        """Test _load_toml_config with parse error."""
        with patch('builtins.open', mock_open(read_data="invalid toml content")):
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.loads.side_effect = Exception("Parse error")
                result = _load_toml_config("test.toml")
                assert result == {}

    def test_load_toml_config_empty_file(self):
        """Test _load_toml_config with empty file."""
        with patch('builtins.open', mock_open(read_data="")):
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.loads.return_value = {}
                result = _load_toml_config("test.toml")
                assert result == {}


class TestLoadEnvConfig:
    """Test _load_env_config function."""

    def test_load_env_config_all_variables(self):
        """Test _load_env_config with all environment variables set."""
        env_vars = {
            'AI_GUARD_LLM_PROVIDER': 'anthropic',
            'AI_GUARD_LLM_API_KEY': 'env-key',
            'AI_GUARD_LLM_MODEL': 'claude-3',
            'AI_GUARD_LLM_TEMPERATURE': '0.2',
            'AI_GUARD_TESTGEN_FRAMEWORK': 'unittest',
            'AI_GUARD_TESTGEN_GENERATE_MOCKS': 'false',
            'AI_GUARD_TESTGEN_GENERATE_PARAMETRIZED_TESTS': 'true',
            'AI_GUARD_TESTGEN_GENERATE_EDGE_CASES': 'false',
            'AI_GUARD_TESTGEN_MAX_TESTS_PER_FILE': '20',
            'AI_GUARD_TESTGEN_ANALYZE_COVERAGE_GAPS': 'false',
            'AI_GUARD_TESTGEN_MIN_COVERAGE_THRESHOLD': '90.0',
            'AI_GUARD_TESTGEN_OUTPUT_DIRECTORY': 'custom/tests',
            'AI_GUARD_TESTGEN_TEST_FILE_SUFFIX': '_spec.py',
            'AI_GUARD_TESTGEN_INCLUDE_DOCSTRINGS': 'false',
            'AI_GUARD_TESTGEN_INCLUDE_TYPE_HINTS': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            result = _load_env_config()
            
            assert result["llm"]["provider"] == "anthropic"
            assert result["llm"]["api_key"] == "env-key"
            assert result["llm"]["model"] == "claude-3"
            assert result["llm"]["temperature"] == 0.2
            assert result["testgen"]["framework"] == "unittest"
            assert result["testgen"]["generate_mocks"] is False
            assert result["testgen"]["generate_parametrized_tests"] is True
            assert result["testgen"]["generate_edge_cases"] is False
            assert result["testgen"]["max_tests_per_file"] == 20
            assert result["testgen"]["analyze_coverage_gaps"] is False
            assert result["testgen"]["min_coverage_threshold"] == 90.0
            assert result["testgen"]["output_directory"] == "custom/tests"
            assert result["testgen"]["test_file_suffix"] == "_spec.py"
            assert result["testgen"]["include_docstrings"] is False
            assert result["testgen"]["include_type_hints"] is False

    def test_load_env_config_no_variables(self):
        """Test _load_env_config with no environment variables set."""
        with patch.dict(os.environ, {}, clear=True):
            result = _load_env_config()
            assert result == {}

    def test_load_env_config_partial_variables(self):
        """Test _load_env_config with only some variables set."""
        env_vars = {
            'AI_GUARD_LLM_PROVIDER': 'openai',
            'AI_GUARD_TESTGEN_MAX_TESTS_PER_FILE': '5'
        }
        
        with patch.dict(os.environ, env_vars):
            result = _load_env_config()
            
            assert result["llm"]["provider"] == "openai"
            assert result["testgen"]["max_tests_per_file"] == 5
            # Other values should not be present

    def test_load_env_config_invalid_boolean_values(self):
        """Test _load_env_config with invalid boolean values."""
        env_vars = {
            'AI_GUARD_TESTGEN_GENERATE_MOCKS': 'invalid',
            'AI_GUARD_TESTGEN_GENERATE_PARAMETRIZED_TESTS': 'yes',
            'AI_GUARD_TESTGEN_GENERATE_EDGE_CASES': '1',
            'AI_GUARD_TESTGEN_ANALYZE_COVERAGE_GAPS': '0',
            'AI_GUARD_TESTGEN_INCLUDE_DOCSTRINGS': 'true',
            'AI_GUARD_TESTGEN_INCLUDE_TYPE_HINTS': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            result = _load_env_config()
            
            # Invalid boolean should default to False
            assert result["testgen"]["generate_mocks"] is False
            # Valid boolean strings should be converted
            assert result["testgen"]["generate_parametrized_tests"] is True
            assert result["testgen"]["generate_edge_cases"] is True
            assert result["testgen"]["analyze_coverage_gaps"] is False
            assert result["testgen"]["include_docstrings"] is True
            assert result["testgen"]["include_type_hints"] is False

    def test_load_env_config_invalid_numeric_values(self):
        """Test _load_env_config with invalid numeric values."""
        env_vars = {
            'AI_GUARD_LLM_TEMPERATURE': 'invalid',
            'AI_GUARD_TESTGEN_MAX_TESTS_PER_FILE': 'not-a-number',
            'AI_GUARD_TESTGEN_MIN_COVERAGE_THRESHOLD': 'also-invalid'
        }
        
        with patch.dict(os.environ, env_vars):
            result = _load_env_config()
            
            # Invalid numeric values should not be included
            assert "temperature" not in result.get("llm", {})
            assert "max_tests_per_file" not in result.get("testgen", {})
            assert "min_coverage_threshold" not in result.get("testgen", {})


class TestGetEnvApiKey:
    """Test _get_env_api_key function."""

    def test_get_env_api_key_openai(self):
        """Test _get_env_api_key for OpenAI."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'}):
            result = _get_env_api_key("openai")
            assert result == "openai-key"

    def test_get_env_api_key_anthropic(self):
        """Test _get_env_api_key for Anthropic."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'anthropic-key'}):
            result = _get_env_api_key("anthropic")
            assert result == "anthropic-key"

    def test_get_env_api_key_unknown_provider(self):
        """Test _get_env_api_key for unknown provider."""
        result = _get_env_api_key("unknown")
        assert result is None

    def test_get_env_api_key_no_key_set(self):
        """Test _get_env_api_key when no key is set."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_env_api_key("openai")
            assert result is None

    def test_get_env_api_key_empty_key(self):
        """Test _get_env_api_key when key is empty."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            result = _get_env_api_key("openai")
            assert result is None


class TestLoadTestgenConfig:
    """Test load_testgen_config function."""

    def test_load_testgen_config_from_file(self):
        """Test loading config from specified file."""
        toml_content = """
[llm]
provider = "anthropic"
api_key = "file-key"
model = "claude-3"

[testgen]
max_tests_per_file = 25
generate_mocks = false
"""
        
        with patch('builtins.open', mock_open(read_data=toml_content)):
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.loads.return_value = {
                    "llm": {
                        "provider": "anthropic",
                        "api_key": "file-key",
                        "model": "claude-3"
                    },
                    "testgen": {
                        "max_tests_per_file": 25,
                        "generate_mocks": False
                    }
                }
                
                with patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}):
                    with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value=None):
                        config = load_testgen_config("test.toml")
                        
                        assert config.llm_provider == "anthropic"
                        assert config.llm_api_key == "file-key"
                        assert config.llm_model == "claude-3"
                        assert config.max_tests_per_file == 25
                        assert config.generate_mocks is False

    def test_load_testgen_config_default_files(self):
        """Test loading config from default file locations."""
        toml_content = """
[llm]
provider = "openai"
"""
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.side_effect = lambda path: path == "ai-guard-testgen.toml"
            
            with patch('builtins.open', mock_open(read_data=toml_content)):
                with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                    mock_loader.return_value.loads.return_value = {
                        "llm": {"provider": "openai"}
                    }
                    
                    with patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}):
                        with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value=None):
                            config = load_testgen_config()
                            
                            assert config.llm_provider == "openai"

    def test_load_testgen_config_env_override(self):
        """Test that environment variables override file config."""
        toml_content = """
[llm]
provider = "openai"
api_key = "file-key"
"""
        
        env_config = {
            "llm": {
                "provider": "anthropic",
                "api_key": "env-key"
            }
        }
        
        with patch('builtins.open', mock_open(read_data=toml_content)):
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.loads.return_value = {
                    "llm": {
                        "provider": "openai",
                        "api_key": "file-key"
                    }
                }
                
                with patch('src.ai_guard.generators.config_loader._load_env_config', return_value=env_config):
                    with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value=None):
                        config = load_testgen_config("test.toml")
                        
                        # Environment should override file
                        assert config.llm_provider == "anthropic"
                        assert config.llm_api_key == "env-key"

    def test_load_testgen_config_defaults(self):
        """Test loading config with all defaults."""
        with patch('os.path.exists', return_value=False):
            with patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}):
                with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value=None):
                    config = load_testgen_config()
                    
                    # Check default values
                    assert config.llm_provider == "openai"
                    assert config.llm_api_key is None
                    assert config.llm_model == "gpt-4"
                    assert config.llm_temperature == 0.1
                    assert config.test_framework == "pytest"
                    assert config.generate_mocks is True
                    assert config.generate_parametrized_tests is True
                    assert config.generate_edge_cases is True
                    assert config.max_tests_per_file == 10
                    assert config.analyze_coverage_gaps is True
                    assert config.min_coverage_threshold == 80.0
                    assert config.output_directory == "tests/unit"
                    assert config.test_file_suffix == "_test.py"
                    assert config.include_docstrings is True
                    assert config.include_type_hints is True

    def test_load_testgen_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}):
                with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value=None):
                    config = load_testgen_config("nonexistent.toml")
                    
                    # Should use defaults
                    assert config.llm_provider == "openai"

    def test_load_testgen_config_api_key_from_env(self):
        """Test loading API key from environment."""
        with patch('os.path.exists', return_value=False):
            with patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}):
                with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value="env-api-key"):
                    config = load_testgen_config()
                    
                    assert config.llm_api_key == "env-api-key"

    def test_load_testgen_config_mixed_sources(self):
        """Test loading config from mixed sources."""
        toml_content = """
[llm]
provider = "openai"
model = "gpt-3.5-turbo"

[testgen]
max_tests_per_file = 15
"""
        
        env_config = {
            "llm": {
                "api_key": "env-key"
            },
            "testgen": {
                "generate_mocks": False
            }
        }
        
        with patch('builtins.open', mock_open(read_data=toml_content)):
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.loads.return_value = {
                    "llm": {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo"
                    },
                    "testgen": {
                        "max_tests_per_file": 15
                    }
                }
                
                with patch('src.ai_guard.generators.config_loader._load_env_config', return_value=env_config):
                    with patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value=None):
                        config = load_testgen_config("test.toml")
                        
                        # File values
                        assert config.llm_provider == "openai"
                        assert config.llm_model == "gpt-3.5-turbo"
                        assert config.max_tests_per_file == 15
                        
                        # Environment overrides
                        assert config.llm_api_key == "env-key"
                        assert config.generate_mocks is False
                        
                        # Defaults for unspecified values
                        assert config.llm_temperature == 0.1
                        assert config.test_framework == "pytest"
