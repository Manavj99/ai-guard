"""Comprehensive tests for generator modules."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os

from src.ai_guard.generators.config_loader import (
    load_testgen_config, create_default_config, validate_config,
    TestGenerationConfig, _get_env_api_key
)


class TestConfigLoader:
    """Test configuration loader functionality."""

    def test_load_testgen_config_default(self):
        """Test loading test generation config with defaults."""
        with patch("os.path.exists", return_value=False):
            config = load_testgen_config()
            assert config.llm_provider == "openai"
            assert config.test_framework == "pytest"
            assert config.min_coverage_threshold == 80.0

    def test_load_testgen_config_custom_file(self):
        """Test loading test generation config from custom file."""
        with patch("os.path.exists", return_value=True):
            with patch("src.ai_guard.generators.config_loader._load_toml_config") as mock_load:
                mock_load.return_value = {
                    "llm": {"provider": "anthropic", "model": "claude-3"},
                    "test_generation": {"framework": "unittest", "max_tests_per_file": 20}
                }
                config = load_testgen_config("custom.toml")
                assert config.llm_provider == "anthropic"
                assert config.test_framework == "unittest"
                assert config.max_tests_per_file == 20

    def test_load_testgen_config_with_env_vars(self):
        """Test loading config with environment variables."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "AI_GUARD_LLM_PROVIDER": "openai",
            "AI_GUARD_LLM_MODEL": "gpt-3.5-turbo"
        }):
            with patch("os.path.exists", return_value=False):
                config = load_testgen_config()
                assert config.llm_api_key == "test-key"
                assert config.llm_provider == "openai"
                assert config.llm_model == "gpt-3.5-turbo"

    def test_get_env_api_key_openai(self):
        """Test getting OpenAI API key from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
            key = _get_env_api_key("openai")
            assert key == "test-openai-key"

    def test_get_env_api_key_anthropic(self):
        """Test getting Anthropic API key from environment."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"}):
            key = _get_env_api_key("anthropic")
            assert key == "test-anthropic-key"

    def test_get_env_api_key_generic(self):
        """Test getting generic AI Guard API key from environment."""
        with patch.dict(os.environ, {"AI_GUARD_API_KEY": "test-generic-key"}):
            key = _get_env_api_key()
            assert key == "test-generic-key"

    def test_get_env_api_key_none(self):
        """Test getting API key when none is set."""
        with patch.dict(os.environ, {}, clear=True):
            key = _get_env_api_key()
            assert key is None

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name

        try:
            create_default_config(temp_path)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "[llm]" in content
                assert "[test_generation]" in content
                assert "[coverage_analysis]" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = TestGenerationConfig(llm_api_key="test-key")
        assert validate_config(config) is True

    def test_validate_config_invalid_provider(self):
        """Test config validation with invalid provider."""
        config = TestGenerationConfig(llm_provider="invalid")
        assert validate_config(config) is False

    def test_validate_config_missing_api_key(self):
        """Test config validation with missing API key."""
        config = TestGenerationConfig(llm_provider="openai", llm_api_key="")
        assert validate_config(config) is False

    def test_validate_config_invalid_temperature(self):
        """Test config validation with invalid temperature."""
        config = TestGenerationConfig(llm_temperature=1.5)
        assert validate_config(config) is False

    def test_validate_config_invalid_framework(self):
        """Test config validation with invalid framework."""
        config = TestGenerationConfig(test_framework="invalid")
        assert validate_config(config) is False

    def test_validate_config_invalid_max_tests(self):
        """Test config validation with invalid max tests."""
        config = TestGenerationConfig(max_tests_per_file=0)
        assert validate_config(config) is False

    def test_validate_config_invalid_coverage_threshold(self):
        """Test config validation with invalid coverage threshold."""
        config = TestGenerationConfig(min_coverage_threshold=150.0)
        assert validate_config(config) is False

    def test_validate_config_empty_output_directory(self):
        """Test config validation with empty output directory."""
        config = TestGenerationConfig(output_directory="")
        assert validate_config(config) is False


class TestTestGenerationConfig:
    """Test TestGenerationConfig class."""

    def test_config_init_default(self):
        """Test config initialization with default values."""
        config = TestGenerationConfig()
        assert config.llm_provider == "openai"
        assert config.test_framework == "pytest"
        assert config.min_coverage_threshold == 80.0
        assert config.generate_mocks is True
        assert config.generate_parametrized_tests is True
        assert config.generate_edge_cases is True

    def test_config_init_custom(self):
        """Test config initialization with custom values."""
        config = TestGenerationConfig(
            llm_provider="anthropic",
            llm_model="claude-3",
            test_framework="unittest",
            min_coverage_threshold=90.0,
            generate_mocks=False,
            max_tests_per_file=15
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.test_framework == "unittest"
        assert config.min_coverage_threshold == 90.0
        assert config.generate_mocks is False
        assert config.max_tests_per_file == 15

    def test_config_to_dict(self):
        """Test config conversion to dictionary."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_model="gpt-4",
            test_framework="pytest"
        )
        config_dict = config.to_dict()
        assert config_dict["llm_provider"] == "openai"
        assert config_dict["llm_model"] == "gpt-4"
        assert config_dict["test_framework"] == "pytest"

    def test_config_from_dict(self):
        """Test config creation from dictionary."""
        config_dict = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3",
            "test_framework": "unittest",
            "min_coverage_threshold": 85.0
        }
        config = TestGenerationConfig.from_dict(config_dict)
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.test_framework == "unittest"
        assert config.min_coverage_threshold == 85.0

    def test_config_validation_method(self):
        """Test config validation method."""
        config = TestGenerationConfig(llm_api_key="test-key")
        assert config.validate() is True

        config.llm_provider = "invalid"
        assert config.validate() is False

    def test_config_str_representation(self):
        """Test config string representation."""
        config = TestGenerationConfig(llm_provider="openai")
        config_str = str(config)
        assert "TestGenConfig" in config_str
        assert "openai" in config_str

    def test_config_repr(self):
        """Test config repr method."""
        config = TestGenerationConfig(llm_provider="openai")
        config_repr = repr(config)
        assert "TestGenConfig" in config_repr
        assert "openai" in config_repr


class TestConfigLoaderIntegration:
    """Integration tests for config loader."""

    def test_full_config_loading_workflow(self):
        """Test complete config loading workflow."""
        config_content = """
[llm]
provider = "openai"
api_key = "test-key"
model = "gpt-4"
temperature = 0.1

[test_generation]
framework = "pytest"
generate_mocks = true
generate_parametrized_tests = true
generate_edge_cases = true
max_tests_per_file = 10
include_docstrings = true
include_type_hints = true

[coverage_analysis]
analyze_coverage_gaps = true
min_coverage_threshold = 80.0
include_coverage_suggestions = true

[output]
output_directory = "tests/unit"
test_file_suffix = "_test.py"
separate_files = false
include_imports = true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_testgen_config(temp_path)
            assert config.llm_provider == "openai"
            assert config.llm_api_key == "test-key"
            assert config.llm_model == "gpt-4"
            assert config.test_framework == "pytest"
            assert config.min_coverage_threshold == 80.0
            assert config.output_directory == "tests/unit"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_config_loading_with_environment_override(self):
        """Test config loading with environment variable overrides."""
        with patch.dict(os.environ, {
            "AI_GUARD_LLM_PROVIDER": "anthropic",
            "AI_GUARD_LLM_API_KEY": "env-key",
            "AI_GUARD_LLM_MODEL": "claude-3"
        }):
            with patch("os.path.exists", return_value=True):
                with patch("src.ai_guard.generators.config_loader._load_toml_config") as mock_load:
                    mock_load.return_value = {
                        "llm": {"provider": "openai", "api_key": "file-key", "model": "gpt-4"}
                    }
                    config = load_testgen_config("test.toml")
                    # Environment variables should override file values
                    assert config.llm_provider == "anthropic"
                    assert config.llm_api_key == "env-key"
                    assert config.llm_model == "claude-3"

    def test_config_validation_integration(self):
        """Test config validation in integration scenario."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            test_framework="pytest",
            min_coverage_threshold=80.0
        )
        
        # Should validate successfully
        assert config.validate() is True
        assert validate_config(config) is True
        
        # Convert to dict and back
        config_dict = config.to_dict()
        new_config = TestGenerationConfig.from_dict(config_dict)
        assert new_config.llm_provider == config.llm_provider
        assert new_config.llm_api_key == config.llm_api_key

    def test_config_error_handling(self):
        """Test config error handling and recovery."""
        # Test with invalid file path
        config = load_testgen_config("nonexistent.toml")
        assert config.llm_provider == "openai"  # Should use defaults

        # Test with malformed config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content")
            temp_path = f.name

        try:
            config = load_testgen_config(temp_path)
            assert config.llm_provider == "openai"  # Should use defaults
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_config_performance(self):
        """Test config loading performance."""
        # Test multiple config loading operations
        for i in range(100):
            config = load_testgen_config()
            assert config.llm_provider == "openai"
            assert config.test_framework == "pytest"
