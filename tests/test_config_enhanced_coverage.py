"""Enhanced test coverage for config.py module to achieve 60%+ coverage."""

import pytest
import tempfile
import os
import json
import time
from unittest.mock import patch, mock_open, MagicMock

from src.ai_guard.config import (
    _get_toml_loader,
    _is_cache_valid,
    _cache_config,
    _get_cached_config,
    _clear_cache,
    _validate_coverage_value,
    _validate_boolean_value,
    _validate_report_format,
    _validate_llm_provider,
    _validate_file_path,
    _validate_config_section,
    _load_toml_config,
    _load_json_config,
    _load_yaml_config,
    _load_config_file,
    _merge_configs,
    _apply_env_overrides,
    _validate_config,
    load_config,
    save_config,
    get_config_value,
    set_config_value,
    reset_config,
    get_default_config,
    validate_config_file,
    _config_cache,
    _cache_lock,
    _cache_timestamps,
)


class TestGetTomlLoader:
    """Test _get_toml_loader function."""

    @patch("importlib.import_module")
    def test_get_toml_loader_tomllib(self, mock_import):
        """Test getting tomllib loader."""
        mock_tomllib = MagicMock()
        mock_import.side_effect = lambda x: mock_tomllib if x == "tomllib" else None

        loader = _get_toml_loader()
        assert loader == mock_tomllib

    @patch("importlib.import_module")
    def test_get_toml_loader_tomli(self, mock_import):
        """Test getting tomli loader when tomllib not available."""
        mock_tomli = MagicMock()
        mock_import.side_effect = lambda x: mock_tomli if x == "tomli" else None

        loader = _get_toml_loader()
        assert loader == mock_tomli

    @patch("importlib.import_module", side_effect=ImportError)
    def test_get_toml_loader_error(self, mock_import):
        """Test error when no TOML loader available."""
        with pytest.raises(ImportError):
            _get_toml_loader()


class TestCacheValid:
    """Test _is_cache_valid function."""

    def test_is_cache_valid_no_timestamp(self):
        """Test cache validity with no timestamp."""
        result = _is_cache_valid("nonexistent_file")
        assert result is False

    def test_is_cache_valid_ttl_expired(self):
        """Test cache validity with expired TTL."""
        with _cache_lock:
            _cache_timestamps["test_file"] = time.time() - 400  # 400 seconds ago

        result = _is_cache_valid("test_file")
        assert result is False

    def test_is_cache_valid_file_modified(self):
        """Test cache validity with modified file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            try:
                with _cache_lock:
                    _cache_timestamps[f.name] = time.time() - 10  # 10 seconds ago

                # Modify file
                with open(f.name, "w") as f2:
                    f2.write("modified content")

                result = _is_cache_valid(f.name)
                assert result is False
            finally:
                os.unlink(f.name)

    def test_is_cache_valid_valid(self):
        """Test cache validity when valid."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            try:
                with _cache_lock:
                    _cache_timestamps[f.name] = time.time()  # Now

                result = _is_cache_valid(f.name)
                assert result is True
            finally:
                os.unlink(f.name)

    def test_is_cache_valid_file_not_found(self):
        """Test cache validity with file not found."""
        with _cache_lock:
            _cache_timestamps["nonexistent"] = time.time()

        result = _is_cache_valid("nonexistent")
        assert result is False


class TestCacheConfig:
    """Test _cache_config function."""

    def test_cache_config(self):
        """Test caching configuration."""
        config = {"test": "value"}

        _cache_config("test_file", config)

        with _cache_lock:
            assert "test_file" in _config_cache
            assert "test_file" in _cache_timestamps
            assert _config_cache["test_file"] == config


class TestGetCachedConfig:
    """Test _get_cached_config function."""

    def test_get_cached_config_valid(self):
        """Test getting valid cached config."""
        config = {"test": "value"}

        with _cache_lock:
            _config_cache["test_file"] = config
            _cache_timestamps["test_file"] = time.time()

        result = _get_cached_config("test_file")
        assert result == config

    def test_get_cached_config_invalid(self):
        """Test getting invalid cached config."""
        with _cache_lock:
            _cache_timestamps["test_file"] = time.time() - 400

        result = _get_cached_config("test_file")
        assert result is None

    def test_get_cached_config_not_found(self):
        """Test getting non-existent cached config."""
        result = _get_cached_config("nonexistent")
        assert result is None


class TestClearCache:
    """Test _clear_cache function."""

    def test_clear_cache_specific_file(self):
        """Test clearing cache for specific file."""
        with _cache_lock:
            _config_cache["file1"] = {"test": "value"}
            _config_cache["file2"] = {"test2": "value2"}
            _cache_timestamps["file1"] = time.time()
            _cache_timestamps["file2"] = time.time()

        _clear_cache("file1")

        with _cache_lock:
            assert "file1" not in _config_cache
            assert "file1" not in _cache_timestamps
            assert "file2" in _config_cache

    def test_clear_cache_all(self):
        """Test clearing all cache."""
        with _cache_lock:
            _config_cache["file1"] = {"test": "value"}
            _cache_timestamps["file1"] = time.time()

        _clear_cache()

        with _cache_lock:
            assert len(_config_cache) == 0
            assert len(_cache_timestamps) == 0


class TestValidateCoverageValue:
    """Test _validate_coverage_value function."""

    def test_validate_coverage_value_int_valid(self):
        """Test validating valid integer coverage value."""
        assert _validate_coverage_value(85) is True

    def test_validate_coverage_value_int_invalid(self):
        """Test validating invalid integer coverage value."""
        assert _validate_coverage_value(150) is False
        assert _validate_coverage_value(-10) is False

    def test_validate_coverage_value_string_valid(self):
        """Test validating valid string coverage value."""
        assert _validate_coverage_value("85") is True

    def test_validate_coverage_value_string_invalid(self):
        """Test validating invalid string coverage value."""
        assert _validate_coverage_value("abc") is False
        assert _validate_coverage_value("150") is False

    def test_validate_coverage_value_invalid_type(self):
        """Test validating invalid type."""
        assert _validate_coverage_value(None) is False
        assert _validate_coverage_value([]) is False


class TestValidateBooleanValue:
    """Test _validate_boolean_value function."""

    def test_validate_boolean_value_bool(self):
        """Test validating boolean value."""
        assert _validate_boolean_value(True) is True
        assert _validate_boolean_value(False) is True

    def test_validate_boolean_value_string_true(self):
        """Test validating true string values."""
        assert _validate_boolean_value("true") is True
        assert _validate_boolean_value("TRUE") is True
        assert _validate_boolean_value("1") is True
        assert _validate_boolean_value("yes") is True
        assert _validate_boolean_value("YES") is True
        assert _validate_boolean_value("on") is True
        assert _validate_boolean_value("ON") is True

    def test_validate_boolean_value_string_false(self):
        """Test validating false string values."""
        assert _validate_boolean_value("false") is True
        assert _validate_boolean_value("FALSE") is True
        assert _validate_boolean_value("0") is True
        assert _validate_boolean_value("no") is True
        assert _validate_boolean_value("NO") is True

    def test_validate_boolean_value_invalid(self):
        """Test validating invalid boolean values."""
        assert _validate_boolean_value("invalid") is False
        assert _validate_boolean_value("maybe") is False
        assert _validate_boolean_value(123) is False


class TestValidateReportFormat:
    """Test _validate_report_format function."""

    def test_validate_report_format_valid(self):
        """Test validating valid report formats."""
        assert _validate_report_format("sarif") is True
        assert _validate_report_format("SARIF") is True
        assert _validate_report_format("json") is True
        assert _validate_report_format("JSON") is True
        assert _validate_report_format("html") is True
        assert _validate_report_format("HTML") is True

    def test_validate_report_format_invalid(self):
        """Test validating invalid report formats."""
        assert _validate_report_format("xml") is False
        assert _validate_report_format("pdf") is False
        assert _validate_report_format("invalid") is False


class TestValidateLlmProvider:
    """Test _validate_llm_provider function."""

    def test_validate_llm_provider_valid(self):
        """Test validating valid LLM providers."""
        assert _validate_llm_provider("openai") is True
        assert _validate_llm_provider("OPENAI") is True
        assert _validate_llm_provider("anthropic") is True
        assert _validate_llm_provider("ANTHROPIC") is True

    def test_validate_llm_provider_invalid(self):
        """Test validating invalid LLM providers."""
        assert _validate_llm_provider("google") is False
        assert _validate_llm_provider("invalid") is False


class TestValidateFilePath:
    """Test _validate_file_path function."""

    def test_validate_file_path_valid(self):
        """Test validating valid file paths."""
        assert _validate_file_path("test.py") is True
        assert _validate_file_path("path/to/file.py") is True
        assert _validate_file_path("file-name.txt") is True
        assert _validate_file_path("file_name.py") is True

    def test_validate_file_path_invalid(self):
        """Test validating invalid file paths."""
        assert _validate_file_path("file with spaces.py") is False
        assert _validate_file_path("file@special.py") is False
        assert _validate_file_path("file#hash.py") is False


class TestValidateConfigSection:
    """Test _validate_config_section function."""

    def test_validate_config_section_valid(self):
        """Test validating valid config section."""
        config = {
            "coverage_threshold": 80,
            "enable_security": True,
            "output_format": "json",
            "llm_provider": "openai",
            "config_file": "config.toml",
        }

        result, errors = _validate_config_section(config)
        assert result is True
        assert len(errors) == 0

    def test_validate_config_section_invalid(self):
        """Test validating invalid config section."""
        config = {
            "coverage_threshold": 150,
            "enable_security": "maybe",
            "output_format": "xml",
            "llm_provider": "google",
            "config_file": "file with spaces.toml",
        }

        result, errors = _validate_config_section(config)
        assert result is False
        assert len(errors) > 0


class TestLoadTomlConfig:
    """Test _load_toml_config function."""

    @patch("src.ai_guard.config._get_toml_loader")
    def test_load_toml_config_success(self, mock_get_loader):
        """Test successful TOML config loading."""
        mock_loader = MagicMock()
        mock_loader.load.return_value = {"test": "value"}
        mock_get_loader.return_value = mock_loader

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[test]\nvalue = "test"')
            f.flush()

            try:
                result = _load_toml_config(f.name)
                assert result == {"test": "value"}
            finally:
                os.unlink(f.name)

    @patch("src.ai_guard.config._get_toml_loader")
    def test_load_toml_config_error(self, mock_get_loader):
        """Test TOML config loading error."""
        mock_loader = MagicMock()
        mock_loader.load.side_effect = Exception("Parse error")
        mock_get_loader.return_value = mock_loader

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("invalid toml content")
            f.flush()

            try:
                result = _load_toml_config(f.name)
                assert result == {}
            finally:
                os.unlink(f.name)


class TestLoadJsonConfig:
    """Test _load_json_config function."""

    def test_load_json_config_success(self):
        """Test successful JSON config loading."""
        config_data = {"test": "value", "number": 42}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()

            try:
                result = _load_json_config(f.name)
                assert result == config_data
            finally:
                os.unlink(f.name)

    def test_load_json_config_error(self):
        """Test JSON config loading error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()

            try:
                result = _load_json_config(f.name)
                assert result == {}
            finally:
                os.unlink(f.name)


class TestLoadYamlConfig:
    """Test _load_yaml_config function."""

    @patch("yaml.safe_load")
    def test_load_yaml_config_success(self, mock_yaml_load):
        """Test successful YAML config loading."""
        mock_yaml_load.return_value = {"test": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test: value")
            f.flush()

            try:
                result = _load_yaml_config(f.name)
                assert result == {"test": "value"}
            finally:
                os.unlink(f.name)

    @patch("yaml.safe_load", side_effect=Exception("YAML error"))
    def test_load_yaml_config_error(self, mock_yaml_load):
        """Test YAML config loading error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            try:
                result = _load_yaml_config(f.name)
                assert result == {}
            finally:
                os.unlink(f.name)


class TestLoadConfigFile:
    """Test _load_config_file function."""

    def test_load_config_file_toml(self):
        """Test loading TOML config file."""
        with patch(
            "src.ai_guard.config._load_toml_config", return_value={"test": "value"}
        ):
            result = _load_config_file("config.toml")
            assert result == {"test": "value"}

    def test_load_config_file_json(self):
        """Test loading JSON config file."""
        with patch(
            "src.ai_guard.config._load_json_config", return_value={"test": "value"}
        ):
            result = _load_config_file("config.json")
            assert result == {"test": "value"}

    def test_load_config_file_yaml(self):
        """Test loading YAML config file."""
        with patch(
            "src.ai_guard.config._load_yaml_config", return_value={"test": "value"}
        ):
            result = _load_config_file("config.yaml")
            assert result == {"test": "value"}

    def test_load_config_file_unsupported(self):
        """Test loading unsupported config file."""
        result = _load_config_file("config.xml")
        assert result == {}


class TestMergeConfigs:
    """Test _merge_configs function."""

    def test_merge_configs_empty(self):
        """Test merging empty configs."""
        result = _merge_configs({}, {})
        assert result == {}

    def test_merge_configs_base_only(self):
        """Test merging with base config only."""
        base = {"key1": "value1", "key2": "value2"}
        result = _merge_configs(base, {})
        assert result == base

    def test_merge_configs_override_only(self):
        """Test merging with override config only."""
        override = {"key3": "value3", "key4": "value4"}
        result = _merge_configs({}, override)
        assert result == override

    def test_merge_configs_both(self):
        """Test merging both configs."""
        base = {"key1": "value1", "key2": "value2"}
        override = {"key2": "new_value2", "key3": "value3"}
        result = _merge_configs(base, override)

        expected = {"key1": "value1", "key2": "new_value2", "key3": "value3"}
        assert result == expected

    def test_merge_configs_nested(self):
        """Test merging nested configs."""
        base = {"section": {"key1": "value1"}}
        override = {"section": {"key2": "value2"}}
        result = _merge_configs(base, override)

        expected = {"section": {"key1": "value1", "key2": "value2"}}
        assert result == expected


class TestApplyEnvOverrides:
    """Test _apply_env_overrides function."""

    def test_apply_env_overrides_empty(self):
        """Test applying empty env overrides."""
        config = {"key1": "value1"}
        result = _apply_env_overrides(config, {})
        assert result == config

    def test_apply_env_overrides_simple(self):
        """Test applying simple env overrides."""
        config = {"key1": "value1"}
        env_vars = {"AI_GUARD_KEY1": "new_value1"}

        with patch.dict(os.environ, env_vars):
            result = _apply_env_overrides(config, env_vars)
            assert result["key1"] == "new_value1"

    def test_apply_env_overrides_nested(self):
        """Test applying nested env overrides."""
        config = {"section": {"key1": "value1"}}
        env_vars = {"AI_GUARD_SECTION_KEY1": "new_value1"}

        with patch.dict(os.environ, env_vars):
            result = _apply_env_overrides(config, env_vars)
            assert result["section"]["key1"] == "new_value1"

    def test_apply_env_overrides_boolean(self):
        """Test applying boolean env overrides."""
        config = {"enable_feature": False}
        env_vars = {"AI_GUARD_ENABLE_FEATURE": "true"}

        with patch.dict(os.environ, env_vars):
            result = _apply_env_overrides(config, env_vars)
            assert result["enable_feature"] is True

    def test_apply_env_overrides_integer(self):
        """Test applying integer env overrides."""
        config = {"threshold": 50}
        env_vars = {"AI_GUARD_THRESHOLD": "75"}

        with patch.dict(os.environ, env_vars):
            result = _apply_env_overrides(config, env_vars)
            assert result["threshold"] == 75


class TestValidateConfig:
    """Test _validate_config function."""

    def test_validate_config_valid(self):
        """Test validating valid config."""
        config = {
            "coverage_threshold": 80,
            "enable_security": True,
            "output_format": "json",
            "llm_provider": "openai",
            "config_file": "config.toml",
        }

        result, errors = _validate_config(config)
        assert result is True
        assert len(errors) == 0

    def test_validate_config_invalid(self):
        """Test validating invalid config."""
        config = {
            "coverage_threshold": 150,
            "enable_security": "maybe",
            "output_format": "xml",
            "llm_provider": "google",
            "config_file": "file with spaces.toml",
        }

        result, errors = _validate_config(config)
        assert result is False
        assert len(errors) > 0


class TestLoadConfig:
    """Test load_config function."""

    @patch("src.ai_guard.config._get_cached_config")
    @patch("src.ai_guard.config._load_config_file")
    def test_load_config_cached(self, mock_load_file, mock_get_cached):
        """Test loading cached config."""
        cached_config = {"test": "cached_value"}
        mock_get_cached.return_value = cached_config

        result = load_config("test.toml")

        assert result == cached_config
        mock_load_file.assert_not_called()

    @patch("src.ai_guard.config._get_cached_config")
    @patch("src.ai_guard.config._load_config_file")
    @patch("src.ai_guard.config._cache_config")
    def test_load_config_not_cached(self, mock_cache, mock_load_file, mock_get_cached):
        """Test loading non-cached config."""
        mock_get_cached.return_value = None
        file_config = {"test": "file_value"}
        mock_load_file.return_value = file_config

        result = load_config("test.toml")

        assert result == file_config
        mock_load_file.assert_called_once_with("test.toml")
        mock_cache.assert_called_once_with("test.toml", file_config)

    @patch("src.ai_guard.config._get_cached_config")
    @patch("src.ai_guard.config._load_config_file")
    def test_load_config_default(self, mock_load_file, mock_get_cached):
        """Test loading default config."""
        mock_get_cached.return_value = None
        mock_load_file.return_value = {}

        result = load_config("nonexistent.toml")

        assert result == {}

    def test_load_config_nonexistent_file(self):
        """Test loading nonexistent config file."""
        result = load_config("nonexistent.toml")
        assert result == {}


class TestSaveConfig:
    """Test save_config function."""

    def test_save_config_toml(self):
        """Test saving TOML config."""
        config = {"test": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.flush()

            try:
                result = save_config(config, f.name)
                assert result is True

                # Verify file was written
                with open(f.name, "r") as rf:
                    content = rf.read()
                    assert "test" in content
            finally:
                os.unlink(f.name)

    def test_save_config_json(self):
        """Test saving JSON config."""
        config = {"test": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.flush()

            try:
                result = save_config(config, f.name)
                assert result is True

                # Verify JSON was written
                with open(f.name, "r") as rf:
                    loaded = json.load(rf)
                    assert loaded == config
            finally:
                os.unlink(f.name)

    def test_save_config_error(self):
        """Test saving config with error."""
        config = {"test": "value"}

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = save_config(config, "invalid_path/config.toml")
            assert result is False


class TestGetConfigValue:
    """Test get_config_value function."""

    def test_get_config_value_simple(self):
        """Test getting simple config value."""
        config = {"key1": "value1", "key2": 42}

        assert get_config_value(config, "key1") == "value1"
        assert get_config_value(config, "key2") == 42
        assert get_config_value(config, "nonexistent") is None

    def test_get_config_value_nested(self):
        """Test getting nested config value."""
        config = {"section": {"subsection": {"key": "value"}}}

        assert get_config_value(config, "section.subsection.key") == "value"
        assert get_config_value(config, "section.subsection.nonexistent") is None
        assert get_config_value(config, "section.nonexistent.key") is None

    def test_get_config_value_default(self):
        """Test getting config value with default."""
        config = {"key1": "value1"}

        assert get_config_value(config, "key1", "default") == "value1"
        assert get_config_value(config, "nonexistent", "default") == "default"


class TestSetConfigValue:
    """Test set_config_value function."""

    def test_set_config_value_simple(self):
        """Test setting simple config value."""
        config = {"key1": "value1"}

        set_config_value(config, "key2", "value2")
        assert config["key2"] == "value2"

        set_config_value(config, "key1", "new_value1")
        assert config["key1"] == "new_value1"

    def test_set_config_value_nested(self):
        """Test setting nested config value."""
        config = {}

        set_config_value(config, "section.subsection.key", "value")
        assert config["section"]["subsection"]["key"] == "value"

    def test_set_config_value_existing_nested(self):
        """Test setting nested config value with existing structure."""
        config = {"section": {"existing": "value"}}

        set_config_value(config, "section.new", "new_value")
        assert config["section"]["existing"] == "value"
        assert config["section"]["new"] == "new_value"


class TestResetConfig:
    """Test reset_config function."""

    def test_reset_config(self):
        """Test resetting config."""
        # Add some test data
        with _cache_lock:
            _config_cache["test_file"] = {"test": "value"}
            _cache_timestamps["test_file"] = time.time()

        reset_config()

        with _cache_lock:
            assert len(_config_cache) == 0
            assert len(_cache_timestamps) == 0


class TestGetDefaultConfig:
    """Test get_default_config function."""

    def test_get_default_config(self):
        """Test getting default config."""
        config = get_default_config()

        assert "coverage_threshold" in config
        assert "enable_security" in config
        assert "enable_performance" in config
        assert "enable_quality" in config
        assert "output_format" in config
        assert "llm_provider" in config

        # Verify default values
        assert config["coverage_threshold"] == 80
        assert config["enable_security"] is True
        assert config["enable_performance"] is True
        assert config["enable_quality"] is True
        assert config["output_format"] == "json"
        assert config["llm_provider"] == "openai"


class TestValidateConfigFile:
    """Test validate_config_file function."""

    def test_validate_config_file_valid(self):
        """Test validating valid config file."""
        config_data = {
            "coverage_threshold": 80,
            "enable_security": True,
            "output_format": "json",
            "llm_provider": "openai",
            "config_file": "config.toml",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()

            try:
                result, errors = validate_config_file(f.name)
                assert result is True
                assert len(errors) == 0
            finally:
                os.unlink(f.name)

    def test_validate_config_file_invalid(self):
        """Test validating invalid config file."""
        config_data = {
            "coverage_threshold": 150,
            "enable_security": "maybe",
            "output_format": "xml",
            "llm_provider": "google",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()

            try:
                result, errors = validate_config_file(f.name)
                assert result is False
                assert len(errors) > 0
            finally:
                os.unlink(f.name)

    def test_validate_config_file_nonexistent(self):
        """Test validating nonexistent config file."""
        result, errors = validate_config_file("nonexistent.json")
        assert result is False
        assert len(errors) > 0

    def test_validate_config_file_invalid_format(self):
        """Test validating config file with invalid format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("invalid config format")
            f.flush()

            try:
                result, errors = validate_config_file(f.name)
                assert result is False
                assert len(errors) > 0
            finally:
                os.unlink(f.name)
