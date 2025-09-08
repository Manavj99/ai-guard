"""Working tests for config module that match actual source code."""

from unittest.mock import patch, mock_open
from ai_guard.config import (
    load_config,
    Gates,
    get_default_config,
    validate_config,
    merge_configs,
    parse_config_value,
)


class TestConfigWorking:
    """Working test coverage for config module."""

    def test_gates_default_values(self):
        """Test Gates dataclass default values."""
        gates = Gates()

        assert gates.min_coverage == 80
        assert gates.fail_on_bandit is True
        assert gates.fail_on_lint is True
        assert gates.fail_on_mypy is True

    def test_gates_custom_values(self):
        """Test Gates dataclass with custom values."""
        gates = Gates(
            min_coverage=90,
            fail_on_bandit=False,
            fail_on_lint=False,
            fail_on_mypy=False,
        )

        assert gates.min_coverage == 90
        assert gates.fail_on_bandit is False
        assert gates.fail_on_lint is False
        assert gates.fail_on_mypy is False

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()

        assert isinstance(config, dict)
        assert config["min_coverage"] == 80
        assert config["skip_tests"] is False
        assert config["report_format"] == "sarif"
        assert config["report_path"] == "ai-guard.sarif"
        assert config["enhanced_testgen"] is False
        assert config["llm_provider"] == "openai"
        assert config["llm_api_key"] == ""
        assert config["llm_model"] == "gpt-4"
        assert config["fail_on_bandit"] is True
        assert config["fail_on_lint"] is True
        assert config["fail_on_mypy"] is True

    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = {
            "min_coverage": 85,
            "report_format": "json",
            "llm_provider": "anthropic",
        }

        assert validate_config(config) is True

    def test_validate_config_invalid_coverage(self):
        """Test validating configuration with invalid coverage."""
        config = {
            "min_coverage": 150,  # Invalid: > 100
        }

        assert validate_config(config) is False

    def test_validate_config_negative_coverage(self):
        """Test validating configuration with negative coverage."""
        config = {
            "min_coverage": -10,  # Invalid: < 0
        }

        assert validate_config(config) is False

    def test_validate_config_invalid_format(self):
        """Test validating configuration with invalid report format."""
        config = {"min_coverage": 80, "report_format": "invalid_format"}

        assert validate_config(config) is False

    def test_validate_config_invalid_llm_provider(self):
        """Test validating configuration with invalid LLM provider."""
        config = {"min_coverage": 80, "llm_provider": "invalid_provider"}

        assert validate_config(config) is False

    def test_validate_config_missing_required_field(self):
        """Test validating configuration missing required fields."""
        config = {
            "report_format": "json"
            # Missing min_coverage
        }

        assert validate_config(config) is False

    def test_merge_configs(self):
        """Test merging configurations."""
        base_config = {
            "min_coverage": 80,
            "report_format": "sarif",
            "skip_tests": False,
        }

        override_config = {"min_coverage": 90, "report_format": "json"}

        result = merge_configs(base_config, override_config)

        assert result["min_coverage"] == 90
        assert result["report_format"] == "json"
        assert result["skip_tests"] is False

    def test_merge_configs_empty_override(self):
        """Test merging configurations with empty override."""
        base_config = {"min_coverage": 80, "report_format": "sarif"}

        override_config = {}

        result = merge_configs(base_config, override_config)

        assert result == base_config

    def test_parse_config_value_string(self):
        """Test parsing string config value."""
        result = parse_config_value("test_string", "str")
        assert result == "test_string"

    def test_parse_config_value_int(self):
        """Test parsing integer config value."""
        result = parse_config_value("42", "int")
        assert result == 42

    def test_parse_config_value_float(self):
        """Test parsing float config value."""
        result = parse_config_value("3.14", "float")
        assert result == 3.14

    def test_parse_config_value_bool_true(self):
        """Test parsing boolean config value (true)."""
        result = parse_config_value("true", "bool")
        assert result is True

    def test_parse_config_value_bool_false(self):
        """Test parsing boolean config value (false)."""
        result = parse_config_value("false", "bool")
        assert result is False

    def test_parse_config_value_auto_string(self):
        """Test auto-parsing string value."""
        result = parse_config_value("hello", "auto")
        assert result == "hello"

    def test_parse_config_value_auto_int(self):
        """Test auto-parsing integer value."""
        result = parse_config_value("123", "auto")
        assert result == 123

    def test_parse_config_value_auto_float(self):
        """Test auto-parsing float value."""
        result = parse_config_value("1.23", "auto")
        assert result == 1.23

    def test_parse_config_value_auto_bool(self):
        """Test auto-parsing boolean value."""
        result = parse_config_value("true", "auto")
        assert result is True

    def test_parse_config_value_invalid_type(self):
        """Test parsing config value with invalid type."""
        result = parse_config_value("test", "invalid_type")
        assert result == "test"  # Should return original value

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        result = load_config("nonexistent.toml")

        assert isinstance(result, dict)
        assert result["min_coverage"] == 80  # Default value

    def test_load_config_valid_toml(self):
        """Test loading config from valid TOML file."""
        toml_content = """
[gates]
min_coverage = 95
fail_on_bandit = false
fail_on_lint = true
fail_on_mypy = false

[enhanced_testgen]
enabled = true
llm_provider = "anthropic"
llm_model = "claude-3"
"""

        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("os.path.exists", return_value=True):
                result = load_config("test.toml")

                assert result["min_coverage"] == 95
                assert result["fail_on_bandit"] is False
                assert result["fail_on_lint"] is True
                assert result["fail_on_mypy"] is False
                assert result["enhanced_testgen"] is True
                assert result["llm_provider"] == "anthropic"
                assert result["llm_model"] == "claude-3"

    def test_load_config_invalid_toml(self):
        """Test loading config from invalid TOML file."""
        invalid_toml = "invalid toml content ["

        with patch("builtins.open", mock_open(read_data=invalid_toml)):
            with patch("os.path.exists", return_value=True):
                result = load_config("invalid.toml")

                # Should return default config on error
                assert isinstance(result, dict)
                assert result["min_coverage"] == 80

    def test_load_config_read_error(self):
        """Test loading config with read error."""
        with patch("builtins.open", side_effect=IOError("Read error")):
            with patch("os.path.exists", return_value=True):
                result = load_config("error.toml")

                # Should return default config on error
                assert isinstance(result, dict)
                assert result["min_coverage"] == 80
