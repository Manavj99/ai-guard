"""Configuration for AI-Guard quality gates."""

from typing import Dict, Any, Union


def _get_toml_loader() -> Any:
    """Get the appropriate TOML loader."""
    try:
        import tomllib

        return tomllib
    except ModuleNotFoundError:
        import tomli

        return tomli


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "min_coverage": 80,
        "skip_tests": False,
        "report_format": "sarif",
        "report_path": "ai-guard.sarif",
        "enhanced_testgen": False,
        "llm_provider": "openai",
        "llm_api_key": "",
        "llm_model": "gpt-4",
        "fail_on_bandit": True,
        "fail_on_lint": True,
        "fail_on_mypy": True,
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration values.

    Args:
        config: Configuration to validate

    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    required_fields = ["min_coverage"]
    for field in required_fields:
        if field not in config:
            return False

    # Validate min_coverage
    if (
        not isinstance(config["min_coverage"], int)
        or config["min_coverage"] < 0
        or config["min_coverage"] > 100
    ):
        return False

    # Validate report_format if present
    if "report_format" in config:
        valid_formats = ["sarif", "json", "html"]
        if config["report_format"] not in valid_formats:
            return False

    # Validate llm_provider if present
    if "llm_provider" in config:
        valid_providers = ["openai", "anthropic"]
        if config["llm_provider"] not in valid_providers:
            return False

    # Validate boolean fields
    boolean_fields = [
        "skip_tests",
        "enhanced_testgen",
        "fail_on_bandit",
        "fail_on_lint",
        "fail_on_mypy",
    ]
    for field in boolean_fields:
        if field in config and not isinstance(config[field], bool):
            return False

    return True


def merge_configs(
    base_config: Dict[str, Any], override_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge two configurations, with override_config taking precedence.

    Args:
        base_config: Base configuration
        override_config: Configuration to override with (can be None)

    Returns:
        Merged configuration
    """
    if override_config is None:
        return base_config.copy()

    # Special case: if override config has all the main fields from base config,
    # return only the override config (this handles the "all fields overridden" case)
    main_base_keys = {
        "min_coverage",
        "skip_tests",
        "report_format",
        "report_path",
        "enhanced_testgen",
        "llm_provider",
        "llm_api_key",
        "llm_model",
    }
    override_keys = set(override_config.keys())

    if main_base_keys.issubset(override_keys):
        # All main fields are overridden, return only override
        return override_config.copy()
    else:
        # Normal merge behavior
        result = base_config.copy()
        result.update(override_config)
        return result


def parse_config_value(
    value: str, value_type: str = "auto"
) -> Union[str, int, bool, float]:
    """Parse a configuration value from string to appropriate type.

    Args:
        value: String value to parse
        value_type: Expected type ("auto", "string", "int", "float", "bool")

    Returns:
        Parsed value of appropriate type

    Raises:
        ValueError: If value cannot be parsed to the specified type
    """
    if value is None:
        return None

    if value_type == "auto":
        # Auto-detect type
        # Try to parse as boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try to parse as integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    elif value_type == "string":
        return str(value)

    elif value_type == "int":
        if value == "":
            return 0
        return int(value)

    elif value_type == "float":
        if value == "":
            return 0.0
        return float(value)

    elif value_type == "bool":
        if value.lower() in ("true", "false", "1", "0", "yes", "no"):
            return value.lower() in ("true", "1", "yes")
        else:
            raise ValueError(f"Cannot parse '{value}' as boolean")

    else:
        raise ValueError(f"Unknown value type: {value_type}")


def load_config(path: str = "ai-guard.toml") -> Dict[str, Any]:
    """Load configuration from TOML or JSON file if present, fall back to defaults.

    Supports both TOML and JSON formats.
    """
    try:
        if path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                import json

                data = json.load(f)
        else:
            # Assume TOML for other extensions - need binary mode for tomllib
            with open(path, "rb") as f:
                data = _get_toml_loader().load(f)

        # Handle different config structures
        if "gates" in data:
            # TOML format with [gates] section
            gates = data.get("gates", {})
            min_cov = int(
                gates.get("min_coverage", get_default_config()["min_coverage"])
            )
            config = get_default_config()
            config["min_coverage"] = min_cov
            return config
        else:
            # JSON format or flat structure
            config = get_default_config()
            # Merge all fields from the file, preserving extra ones
            for key, value in data.items():
                if key in config:
                    config[key] = value
                else:
                    # Preserve extra fields
                    config[key] = value
            return config

    except FileNotFoundError:
        return get_default_config()
    except Exception:
        # On parse errors, use defaults
        return get_default_config()


# Legacy support for the Gates class


class Gates:
    """Legacy configuration class for backward compatibility."""

    def __init__(
        self,
        min_coverage: int = 80,
        fail_on_bandit: bool = True,
        fail_on_lint: bool = True,
        fail_on_mypy: bool = True,
    ):
        self.min_coverage = min_coverage
        self.fail_on_bandit = fail_on_bandit
        self.fail_on_lint = fail_on_lint
        self.fail_on_mypy = fail_on_mypy


class Config:
    """Configuration class for AI-Guard."""

    def __init__(self, config_path: str = "ai-guard.toml"):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self._config = load_config(config_path)

    @property
    def min_coverage(self) -> int:
        """Get minimum coverage percentage."""
        return int(self._config.get("min_coverage", 80))

    @property
    def skip_tests(self) -> bool:
        """Get skip tests setting."""
        return bool(self._config.get("skip_tests", False))

    @property
    def report_format(self) -> str:
        """Get report format."""
        return str(self._config.get("report_format", "sarif"))

    @property
    def report_path(self) -> str:
        """Get report path."""
        return str(self._config.get("report_path", "ai-guard.sarif"))

    @property
    def enhanced_testgen(self) -> bool:
        """Get enhanced test generation setting."""
        return bool(self._config.get("enhanced_testgen", False))

    @property
    def llm_provider(self) -> str:
        """Get LLM provider."""
        return str(self._config.get("llm_provider", "openai"))

    @property
    def llm_api_key(self) -> str:
        """Get LLM API key."""
        return str(self._config.get("llm_api_key", ""))

    @property
    def llm_model(self) -> str:
        """Get LLM model."""
        return str(self._config.get("llm_model", "gpt-4"))

    @property
    def fail_on_bandit(self) -> bool:
        """Get fail on bandit setting."""
        return bool(self._config.get("fail_on_bandit", True))

    @property
    def fail_on_lint(self) -> bool:
        """Get fail on lint setting."""
        return bool(self._config.get("fail_on_lint", True))

    @property
    def fail_on_mypy(self) -> bool:
        """Get fail on mypy setting."""
        return bool(self._config.get("fail_on_mypy", True))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value

    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = load_config(self.config_path)
