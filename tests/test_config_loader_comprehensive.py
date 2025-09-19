"""Comprehensive tests for config_loader module."""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.ai_guard.generators.config_loader import (
    load_testgen_config,
    _load_toml_config,
    _load_env_config,
    _get_env_api_key,
    create_default_config,
    validate_config,
    _get_toml_loader,
    TestGenerationConfig
)


class TestGetTomlLoader:
    """Test _get_toml_loader function."""
    
    def test_get_toml_loader_with_tomllib(self):
        """Test _get_toml_loader when tomllib is available."""
        with patch('src.ai_guard.generators.config_loader.TOML_LIBRARY', 'tomllib'):
            result = _get_toml_loader()
            assert result == 'tomllib'
    
    def test_get_toml_loader_with_tomli(self):
        """Test _get_toml_loader when tomli is available."""
        with patch('src.ai_guard.generators.config_loader.TOML_LIBRARY', 'tomli'):
            result = _get_toml_loader()
            assert result == 'tomli'
    
    def test_get_toml_loader_none_available(self):
        """Test _get_toml_loader when no TOML library is available."""
        with patch('src.ai_guard.generators.config_loader.TOML_LIBRARY', None):
            with pytest.raises(ModuleNotFoundError, match="Neither tomllib nor tomli is available"):
                _get_toml_loader()


class TestLoadTomlConfig:
    """Test _load_toml_config function."""
    
    def test_load_toml_config_success(self):
        """Test successful TOML config loading."""
        config_content = """
[llm]
provider = "openai"
api_key = "test-key"
model = "gpt-4"

[test_generation]
framework = "pytest"
generate_mocks = true
"""
        
        with patch('builtins.open', mock_open(read_data=config_content)), \
             patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
            mock_loader.return_value.load.return_value = {
                'llm': {'provider': 'openai', 'api_key': 'test-key', 'model': 'gpt-4'},
                'test_generation': {'framework': 'pytest', 'generate_mocks': True}
            }
            
            result = _load_toml_config("test.toml")
            assert result['llm']['provider'] == 'openai'
            assert result['llm']['api_key'] == 'test-key'
            assert result['test_generation']['framework'] == 'pytest'
    
    def test_load_toml_config_file_not_found(self):
        """Test TOML config loading when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = _load_toml_config("nonexistent.toml")
            assert result == {}
    
    def test_load_toml_config_parse_error(self):
        """Test TOML config loading with parse error."""
        with patch('builtins.open', mock_open(read_data="invalid toml content")), \
             patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
            mock_loader.return_value.load.side_effect = Exception("Parse error")
            
            result = _load_toml_config("test.toml")
            assert result == {}


class TestLoadEnvConfig:
    """Test _load_env_config function."""
    
    def test_load_env_config_empty(self):
        """Test loading environment config with no variables set."""
        with patch.dict(os.environ, {}, clear=True):
            result = _load_env_config()
            assert result == {}
    
    def test_load_env_config_llm_provider(self):
        """Test loading LLM provider from environment."""
        with patch.dict(os.environ, {'AI_GUARD_LLM_PROVIDER': 'anthropic'}):
            result = _load_env_config()
            assert result['llm']['provider'] == 'anthropic'
    
    def test_load_env_config_llm_api_key(self):
        """Test loading LLM API key from environment."""
        with patch.dict(os.environ, {'AI_GUARD_LLM_API_KEY': 'test-key'}):
            result = _load_env_config()
            assert result['llm']['api_key'] == 'test-key'
    
    def test_load_env_config_llm_model(self):
        """Test loading LLM model from environment."""
        with patch.dict(os.environ, {'AI_GUARD_LLM_MODEL': 'claude-3'}):
            result = _load_env_config()
            assert result['llm']['model'] == 'claude-3'
    
    def test_load_env_config_llm_temperature(self):
        """Test loading LLM temperature from environment."""
        with patch.dict(os.environ, {'AI_GUARD_LLM_TEMPERATURE': '0.5'}):
            result = _load_env_config()
            assert result['llm']['temperature'] == 0.5
    
    def test_load_env_config_llm_temperature_invalid(self):
        """Test loading invalid LLM temperature from environment."""
        with patch.dict(os.environ, {'AI_GUARD_LLM_TEMPERATURE': 'invalid'}):
            result = _load_env_config()
            assert 'llm' not in result or 'temperature' not in result.get('llm', {})
    
    def test_load_env_config_test_framework(self):
        """Test loading test framework from environment."""
        with patch.dict(os.environ, {'AI_GUARD_TEST_FRAMEWORK': 'unittest'}):
            result = _load_env_config()
            assert result['test_generation']['framework'] == 'unittest'
    
    def test_load_env_config_testgen_framework(self):
        """Test loading test framework from TESTGEN environment variable."""
        with patch.dict(os.environ, {'AI_GUARD_TESTGEN_FRAMEWORK': 'unittest'}):
            result = _load_env_config()
            assert result['test_generation']['framework'] == 'unittest'
    
    def test_load_env_config_generate_mocks_true(self):
        """Test loading generate_mocks=true from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_MOCKS': 'true'}):
            result = _load_env_config()
            assert result['test_generation']['generate_mocks'] is True
    
    def test_load_env_config_generate_mocks_false(self):
        """Test loading generate_mocks=false from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_MOCKS': 'false'}):
            result = _load_env_config()
            assert result['test_generation']['generate_mocks'] is False
    
    def test_load_env_config_generate_mocks_yes(self):
        """Test loading generate_mocks=yes from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_MOCKS': 'yes'}):
            result = _load_env_config()
            assert result['test_generation']['generate_mocks'] is True
    
    def test_load_env_config_generate_mocks_1(self):
        """Test loading generate_mocks=1 from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_MOCKS': '1'}):
            result = _load_env_config()
            assert result['test_generation']['generate_mocks'] is True
    
    def test_load_env_config_generate_mocks_on(self):
        """Test loading generate_mocks=on from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_MOCKS': 'on'}):
            result = _load_env_config()
            assert result['test_generation']['generate_mocks'] is True
    
    def test_load_env_config_generate_mocks_empty(self):
        """Test loading generate_mocks with empty value from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_MOCKS': ''}):
            result = _load_env_config()
            # Empty value should not create the test_generation section
            assert 'test_generation' not in result
    
    def test_load_env_config_generate_parametrized_tests(self):
        """Test loading generate_parametrized_tests from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_PARAMETRIZED_TESTS': 'true'}):
            result = _load_env_config()
            assert result['test_generation']['generate_parametrized_tests'] is True
    
    def test_load_env_config_generate_edge_cases(self):
        """Test loading generate_edge_cases from environment."""
        with patch.dict(os.environ, {'AI_GUARD_GENERATE_EDGE_CASES': 'true'}):
            result = _load_env_config()
            assert result['test_generation']['generate_edge_cases'] is True
    
    def test_load_env_config_max_tests_per_file(self):
        """Test loading max_tests_per_file from environment."""
        with patch.dict(os.environ, {'AI_GUARD_TESTGEN_MAX_TESTS_PER_FILE': '15'}):
            result = _load_env_config()
            assert result['test_generation']['max_tests_per_file'] == 15
    
    def test_load_env_config_max_tests_per_file_invalid(self):
        """Test loading invalid max_tests_per_file from environment."""
        with patch.dict(os.environ, {'AI_GUARD_TESTGEN_MAX_TESTS_PER_FILE': 'invalid'}):
            result = _load_env_config()
            assert 'test_generation' not in result or 'max_tests_per_file' not in result.get('test_generation', {})
    
    def test_load_env_config_include_docstrings(self):
        """Test loading include_docstrings from environment."""
        with patch.dict(os.environ, {'AI_GUARD_TESTGEN_INCLUDE_DOCSTRINGS': 'true'}):
            result = _load_env_config()
            assert result['test_generation']['include_docstrings'] is True
    
    def test_load_env_config_include_type_hints(self):
        """Test loading include_type_hints from environment."""
        with patch.dict(os.environ, {'AI_GUARD_TESTGEN_INCLUDE_TYPE_HINTS': 'true'}):
            result = _load_env_config()
            assert result['test_generation']['include_type_hints'] is True
    
    def test_load_env_config_analyze_coverage_gaps(self):
        """Test loading analyze_coverage_gaps from environment."""
        with patch.dict(os.environ, {'AI_GUARD_ANALYZE_COVERAGE': 'true'}):
            result = _load_env_config()
            assert result['coverage_analysis']['analyze_coverage_gaps'] is True
    
    def test_load_env_config_min_coverage_threshold(self):
        """Test loading min_coverage_threshold from environment."""
        with patch.dict(os.environ, {'AI_GUARD_MIN_COVERAGE': '85.5'}):
            result = _load_env_config()
            assert result['coverage_analysis']['min_coverage_threshold'] == 85.5
    
    def test_load_env_config_min_coverage_threshold_invalid(self):
        """Test loading invalid min_coverage_threshold from environment."""
        with patch.dict(os.environ, {'AI_GUARD_MIN_COVERAGE': 'invalid'}):
            result = _load_env_config()
            assert 'coverage_analysis' not in result or 'min_coverage_threshold' not in result.get('coverage_analysis', {})
    
    def test_load_env_config_output_directory(self):
        """Test loading output_directory from environment."""
        with patch.dict(os.environ, {'AI_GUARD_OUTPUT_DIR': '/custom/tests'}):
            result = _load_env_config()
            assert result['output']['output_directory'] == '/custom/tests'
    
    def test_load_env_config_test_file_suffix(self):
        """Test loading test_file_suffix from environment."""
        with patch.dict(os.environ, {'AI_GUARD_TESTGEN_TEST_FILE_SUFFIX': '_spec.py'}):
            result = _load_env_config()
            assert result['output']['test_file_suffix'] == '_spec.py'


class TestGetEnvApiKey:
    """Test _get_env_api_key function."""
    
    def test_get_env_api_key_openai(self):
        """Test getting OpenAI API key from environment."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'}):
            result = _get_env_api_key('openai')
            assert result == 'openai-key'
    
    def test_get_env_api_key_anthropic(self):
        """Test getting Anthropic API key from environment."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'anthropic-key'}):
            result = _get_env_api_key('anthropic')
            assert result == 'anthropic-key'
    
    def test_get_env_api_key_generic_fallback(self):
        """Test getting generic API key as fallback."""
        with patch.dict(os.environ, {'AI_GUARD_API_KEY': 'generic-key'}):
            result = _get_env_api_key('openai')
            assert result == 'generic-key'
    
    def test_get_env_api_key_no_provider(self):
        """Test getting API key without specifying provider."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'}):
            result = _get_env_api_key(None)
            assert result == 'openai-key'
    
    def test_get_env_api_key_anthropic_preference(self):
        """Test getting Anthropic API key when both are available."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'openai-key',
            'ANTHROPIC_API_KEY': 'anthropic-key'
        }):
            result = _get_env_api_key(None)
            assert result == 'openai-key'  # First in the loop
    
    def test_get_env_api_key_none_found(self):
        """Test getting API key when none are found."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_env_api_key('openai')
            assert result is None


class TestLoadTestgenConfig:
    """Test load_testgen_config function."""
    
    def test_load_testgen_config_default(self):
        """Test loading default configuration."""
        with patch('src.ai_guard.generators.config_loader._load_toml_config', return_value={}), \
             patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}):
            
            config = load_testgen_config()
            assert config.llm_provider == 'openai'
            assert config.llm_model == 'gpt-4'
            assert config.llm_temperature == 0.1
            assert config.test_framework == 'pytest'
            assert config.generate_mocks is True
            assert config.generate_parametrized_tests is True
            assert config.generate_edge_cases is True
            assert config.max_tests_per_file == 10
            assert config.include_docstrings is True
            assert config.include_type_hints is True
            assert config.analyze_coverage_gaps is True
            assert config.min_coverage_threshold == 80.0
            assert config.output_directory == 'tests/unit'
            assert config.test_file_suffix == '_test.py'
    
    def test_load_testgen_config_with_file(self):
        """Test loading configuration from file."""
        config_data = {
            'llm': {'provider': 'anthropic', 'model': 'claude-3'},
            'test_generation': {'framework': 'unittest', 'generate_mocks': False}
        }
        
        with patch('src.ai_guard.generators.config_loader._load_toml_config', return_value=config_data), \
             patch('src.ai_guard.generators.config_loader._load_env_config', return_value={}), \
             patch('src.ai_guard.generators.config_loader._get_env_api_key', return_value='test-key'), \
             patch('os.path.exists', return_value=True):
            
            config = load_testgen_config('test.toml')
            assert config.llm_provider == 'anthropic'
            assert config.llm_model == 'claude-3'
            assert config.test_framework == 'unittest'
            assert config.generate_mocks is False
    
    def test_load_testgen_config_env_override(self):
        """Test environment variables overriding file config."""
        file_data = {
            'llm': {'provider': 'openai', 'model': 'gpt-4'},
            'test_generation': {'framework': 'pytest'}
        }
        env_data = {
            'llm': {'provider': 'anthropic'},
            'test_generation': {'framework': 'unittest'}
        }
        
        with patch('src.ai_guard.generators.config_loader._load_toml_config', return_value=file_data), \
             patch('src.ai_guard.generators.config_loader._load_env_config', return_value=env_data):
            
            config = load_testgen_config('test.toml')
            assert config.llm_provider == 'anthropic'  # Overridden by env
            assert config.llm_model == 'gpt-4'  # From file
            assert config.test_framework == 'unittest'  # Overridden by env
    
    def test_load_testgen_config_env_merge_nested(self):
        """Test environment variables merging with nested file config."""
        file_data = {
            'llm': {'provider': 'openai', 'model': 'gpt-4'},
            'test_generation': {'framework': 'pytest', 'generate_mocks': True}
        }
        env_data = {
            'llm': {'temperature': 0.5},
            'test_generation': {'generate_mocks': False}
        }
        
        with patch('src.ai_guard.generators.config_loader._load_toml_config', return_value=file_data), \
             patch('src.ai_guard.generators.config_loader._load_env_config', return_value=env_data):
            
            config = load_testgen_config('test.toml')
            assert config.llm_provider == 'openai'  # From file
            assert config.llm_model == 'gpt-4'  # From file
            assert config.llm_temperature == 0.5  # From env
            assert config.test_framework == 'pytest'  # From file
            assert config.generate_mocks is False  # Overridden by env


class TestCreateDefaultConfig:
    """Test create_default_config function."""
    
    def test_create_default_config_success(self):
        """Test successful creation of default config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml') as f:
            config_path = f.name
        
        try:
            with patch('builtins.open', mock_open()) as mock_file:
                create_default_config(config_path)
                mock_file.assert_called_once_with(config_path, 'w', encoding='utf-8')
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_create_default_config_error(self):
        """Test error handling in default config creation."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should not raise exception, just print error
            create_default_config("test.toml")


class TestValidateConfig:
    """Test validate_config function."""
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='pytest',
            max_tests_per_file=10,
            min_coverage_threshold=80.0,
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is True
    
    def test_validate_config_invalid_provider(self):
        """Test validation with invalid LLM provider."""
        config = TestGenerationConfig(
            llm_provider='invalid-provider',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='pytest',
            max_tests_per_file=10,
            min_coverage_threshold=80.0,
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is False
    
    def test_validate_config_missing_api_key(self):
        """Test validation with missing API key."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key=None,
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='pytest',
            max_tests_per_file=10,
            min_coverage_threshold=80.0,
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is False
    
    def test_validate_config_invalid_temperature(self):
        """Test validation with invalid temperature."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=1.5,  # Invalid: > 1.0
            test_framework='pytest',
            max_tests_per_file=10,
            min_coverage_threshold=80.0,
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is False
    
    def test_validate_config_invalid_framework(self):
        """Test validation with invalid test framework."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='invalid-framework',
            max_tests_per_file=10,
            min_coverage_threshold=80.0,
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is False
    
    def test_validate_config_invalid_max_tests(self):
        """Test validation with invalid max_tests_per_file."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='pytest',
            max_tests_per_file=0,  # Invalid: < 1
            min_coverage_threshold=80.0,
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is False
    
    def test_validate_config_invalid_coverage_threshold(self):
        """Test validation with invalid coverage threshold."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='pytest',
            max_tests_per_file=10,
            min_coverage_threshold=150.0,  # Invalid: > 100
            output_directory='tests/unit'
        )
        
        result = validate_config(config)
        assert result is False
    
    def test_validate_config_empty_output_directory(self):
        """Test validation with empty output directory."""
        config = TestGenerationConfig(
            llm_provider='openai',
            llm_api_key='test-key',
            llm_model='gpt-4',
            llm_temperature=0.1,
            test_framework='pytest',
            max_tests_per_file=10,
            min_coverage_threshold=80.0,
            output_directory=''  # Invalid: empty
        )
        
        result = validate_config(config)
        assert result is False


class TestConfigLoaderIntegration:
    """Integration tests for config_loader module."""
    
    def test_full_config_loading_workflow(self):
        """Test complete configuration loading workflow."""
        # Create a temporary config file
        config_content = """
[llm]
provider = "anthropic"
api_key = "test-key"
model = "claude-3"
temperature = 0.2

[test_generation]
framework = "unittest"
generate_mocks = false
generate_parametrized_tests = true
generate_edge_cases = false
max_tests_per_file = 15
include_docstrings = false
include_type_hints = true

[coverage_analysis]
analyze_coverage_gaps = false
min_coverage_threshold = 90.0

[output]
output_directory = "custom_tests"
test_file_suffix = "_spec.py"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml') as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            with patch('src.ai_guard.generators.config_loader._get_toml_loader') as mock_loader:
                mock_loader.return_value.load.return_value = {
                    'llm': {
                        'provider': 'anthropic',
                        'api_key': 'test-key',
                        'model': 'claude-3',
                        'temperature': 0.2
                    },
                    'test_generation': {
                        'framework': 'unittest',
                        'generate_mocks': False,
                        'generate_parametrized_tests': True,
                        'generate_edge_cases': False,
                        'max_tests_per_file': 15,
                        'include_docstrings': False,
                        'include_type_hints': True
                    },
                    'coverage_analysis': {
                        'analyze_coverage_gaps': False,
                        'min_coverage_threshold': 90.0
                    },
                    'output': {
                        'output_directory': 'custom_tests',
                        'test_file_suffix': '_spec.py'
                    }
                }
                
                config = load_testgen_config(config_path)
                
                # Verify all values are loaded correctly
                assert config.llm_provider == 'anthropic'
                assert config.llm_api_key == 'test-key'
                assert config.llm_model == 'claude-3'
                assert config.llm_temperature == 0.2
                assert config.test_framework == 'unittest'
                assert config.generate_mocks is False
                assert config.generate_parametrized_tests is True
                assert config.generate_edge_cases is False
                assert config.max_tests_per_file == 15
                assert config.include_docstrings is False
                assert config.include_type_hints is True
                assert config.analyze_coverage_gaps is False
                assert config.min_coverage_threshold == 90.0
                assert config.output_directory == 'custom_tests'
                assert config.test_file_suffix == '_spec.py'
                
                # Validate the configuration
                assert validate_config(config) is True
                
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)