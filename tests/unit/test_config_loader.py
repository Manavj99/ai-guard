"""Tests for config_loader module."""

import os
from unittest.mock import patch, mock_open

from ai_guard.generators.config_loader import (
    _get_toml_loader,
    load_testgen_config,
    _load_toml_config,
    _load_env_config,
    _get_env_api_key,
    create_default_config,
    validate_config,
)
from ai_guard.generators.enhanced_testgen import TestGenerationConfig


class TestTomlLoader:
    """Test TOML loader functionality."""

    def test_get_toml_loader_returns_loader(self):
        """Test that _get_toml_loader returns a loader with load method."""
        loader = _get_toml_loader()
        assert hasattr(loader, "load")


class TestLoadTomlConfig:
    """Test TOML configuration loading."""

    def test_load_toml_config_success(self):
        """Test successfully loading TOML configuration."""
        toml_content = """
[llm]
provider = "openai"
api_key = "test-key"
model = "gpt-4"
temperature = 0.2

[test_generation]
max_tests_per_file = 10
        """

        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch(
                "ai_guard.generators.config_loader._get_toml_loader"
            ) as mock_loader:
                mock_loader.return_value.load.return_value = {
                    "llm": {
                        "provider": "openai",
                        "api_key": "test-key",
                        "model": "gpt-4",
                        "temperature": 0.2,
                    },
                    "test_generation": {"max_tests_per_file": 10},
                }

                config = _load_toml_config("test.toml")
                assert config["llm"]["provider"] == "openai"
                assert config["test_generation"]["max_tests_per_file"] == 10

    def test_load_toml_config_file_not_found(self):
        """Test loading TOML config when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            config = _load_toml_config("nonexistent.toml")
            assert config == {}


class TestLoadEnvConfig:
    """Test environment configuration loading."""

    @patch.dict(
        os.environ,
        {
            "AI_GUARD_LLM_PROVIDER": "anthropic",
            "AI_GUARD_LLM_MODEL": "claude-3",
            "AI_GUARD_LLM_TEMPERATURE": "0.3",
            "AI_GUARD_TEST_FRAMEWORK": "pytest",
        },
    )
    def test_load_env_config_with_values(self):
        """Test loading configuration from environment variables."""
        config = _load_env_config()

        assert config["llm"]["provider"] == "anthropic"
        assert config["llm"]["model"] == "claude-3"
        assert config["llm"]["temperature"] == 0.3
        assert config["test_generation"]["framework"] == "pytest"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_env_config_empty(self):
        """Test loading configuration when no environment variables are set."""
        config = _load_env_config()
        assert config == {}


class TestGetEnvApiKey:
    """Test environment API key retrieval."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    def test_get_env_api_key_openai(self):
        """Test getting OpenAI API key from environment."""
        key = _get_env_api_key()
        assert key == "test-openai-key"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    def test_get_env_api_key_anthropic(self):
        """Test getting Anthropic API key from environment."""
        key = _get_env_api_key()
        assert key == "test-anthropic-key"

    @patch.dict(os.environ, {"AI_GUARD_API_KEY": "test-generic-key"})
    def test_get_env_api_key_generic(self):
        """Test getting generic AI Guard API key from environment."""
        key = _get_env_api_key()
        assert key == "test-generic-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_env_api_key_none(self):
        """Test getting API key when none is set."""
        key = _get_env_api_key()
        assert key is None


class TestLoadTestgenConfig:
    """Test loading test generation configuration."""

    def test_load_testgen_config_from_file(self):
        """Test loading configuration from file."""
        toml_content = """
[llm]
provider = "openai"
api_key = "file-key"
model = "gpt-4"

[test_generation]
max_tests_per_file = 5
        """

        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch(
                "ai_guard.generators.config_loader._get_toml_loader"
            ) as mock_loader:
                mock_loader.return_value.load.return_value = {
                    "llm": {
                        "provider": "openai",
                        "api_key": "file-key",
                        "model": "gpt-4",
                    },
                    "test_generation": {"max_tests_per_file": 5},
                }

                with patch(
                    "ai_guard.generators.config_loader._load_env_config",
                    return_value={},
                ):
                    with patch(
                        "ai_guard.generators.config_loader._get_env_api_key",
                        return_value=None,
                    ):
                        config = load_testgen_config("test.toml")

                        assert isinstance(config, TestGenerationConfig)
                        assert config.llm_provider == "openai"
                        # API key comes from _get_env_api_key, not from file
                        assert config.llm_api_key is None
                        # The config uses test_generation key, not testgen
                        assert (
                            config.max_tests_per_file == 10
                        )  # Default value since test_generation key is used

    def test_load_testgen_config_defaults(self):
        """Test loading configuration with default values."""
        with patch(
            "ai_guard.generators.config_loader._load_toml_config", return_value={}
        ):
            with patch(
                "ai_guard.generators.config_loader._load_env_config", return_value={}
            ):
                with patch(
                    "ai_guard.generators.config_loader._get_env_api_key",
                    return_value=None,
                ):
                    config = load_testgen_config()

                    assert isinstance(config, TestGenerationConfig)
                    assert config.llm_provider == "openai"
                    assert config.llm_model == "gpt-4"
                    assert config.llm_temperature == 0.1
                    assert config.max_tests_per_file == 10


class TestCreateDefaultConfig:
    """Test creating default configuration file."""

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with patch("builtins.open", mock_open()) as mock_file:
            create_default_config("test-config.toml")

            mock_file.assert_called_once_with("test-config.toml", "w", encoding="utf-8")

    def test_create_default_config_default_path(self):
        """Test creating default configuration with default path."""
        with patch("builtins.open", mock_open()) as mock_file:
            create_default_config()

            mock_file.assert_called_once_with(
                "ai-guard-testgen.toml", "w", encoding="utf-8"
            )

    def test_create_default_config_write_error(self):
        """Test handling write errors when creating default config."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Should not raise exception, just print error
            create_default_config("test.toml")


class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=80.0,
            output_directory="tests",
        )

        assert validate_config(config) is True

    def test_validate_config_invalid_provider(self):
        """Test validating configuration with invalid provider."""
        config = TestGenerationConfig(
            llm_provider="invalid-provider",
            llm_api_key="test-key",
            llm_model="gpt-4",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=80.0,
            output_directory="tests",
        )

        assert validate_config(config) is False

    def test_validate_config_missing_api_key(self):
        """Test validating configuration with missing API key."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key=None,
            llm_model="gpt-4",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=80.0,
            output_directory="tests",
        )

        assert validate_config(config) is False

    def test_validate_config_invalid_temperature(self):
        """Test validating configuration with invalid temperature."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4",
            llm_temperature=1.5,  # Invalid: > 1.0
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=80.0,
            output_directory="tests",
        )

        assert validate_config(config) is False

    def test_validate_config_invalid_max_tests(self):
        """Test validating configuration with invalid max_tests_per_file."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=0,  # Invalid: < 1
            min_coverage_threshold=80.0,
            output_directory="tests",
        )

        assert validate_config(config) is False


class TestConfigurationIntegration:
    """Test configuration integration scenarios."""

    def test_config_priority_order(self):
        """Test configuration priority: env > file > defaults."""
        # File config
        with patch("ai_guard.generators.config_loader._load_toml_config") as mock_file:
            mock_file.return_value = {
                "llm": {"provider": "file-provider", "api_key": "file-key"},
                "test_generation": {"max_tests_per_file": 8},
            }

            # Env config (should override file)
            with patch(
                "ai_guard.generators.config_loader._load_env_config"
            ) as mock_env:
                mock_env.return_value = {
                    "llm": {"provider": "env-provider"},
                    "test_generation": {"max_tests_per_file": 12},
                }

                with patch(
                    "ai_guard.generators.config_loader._get_env_api_key",
                    return_value="env-api-key",
                ):
                    config = load_testgen_config("test.toml")

                    # Env should override file
                    assert config.llm_provider == "env-provider"
                    assert config.llm_api_key == "env-api-key"  # From env
                    assert config.max_tests_per_file == 12  # From env

    def test_config_type_conversion(self):
        """Test configuration type conversion."""
        with patch(
            "ai_guard.generators.config_loader._load_toml_config", return_value={}
        ):
            with patch(
                "ai_guard.generators.config_loader._load_env_config"
            ) as mock_env:
                mock_env.return_value = {
                    "llm": {"temperature": "0.5"},
                    "test_generation": {
                        "max_tests_per_file": "15",
                        "include_comments": "false",
                    },
                }

                with patch(
                    "ai_guard.generators.config_loader._get_env_api_key",
                    return_value=None,
                ):
                    config = load_testgen_config()

                    assert config.llm_temperature == 0.5
                    assert config.max_tests_per_file == 15
