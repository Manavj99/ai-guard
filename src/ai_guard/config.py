"""Configuration for AI-Guard quality gates."""

from typing import Dict, Any, Union


def _get_toml_loader() -> Any:
    """Get the appropriate TOML loader."""
    try:
        import tomllib

        return tomllib
    except (ModuleNotFoundError, ImportError):
        try:
            import tomli

            return tomli
        except (ModuleNotFoundError, ImportError):
            raise ImportError("Neither tomllib nor tomli is available")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "gates": {
            "min_coverage": 80,
            "fail_on_bandit": True,
            "fail_on_lint": True,
            "fail_on_mypy": True,
        },
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
    if config is None or not isinstance(config, dict):
        return False

    # Empty dict is valid (will use defaults)
    if not config:
        return True

    # Check for required fields only if config has some content
    # Empty dict is valid (will use defaults)
    if len(config) > 0:
        # If config has content, it should have at least some basic structure
        # But be lenient - only require fields if they're explicitly set
        # This is intentionally left empty as we validate specific fields below
        pass

    # Check min_coverage validation - prioritize top-level over gates
    min_coverage_value = None
    if "min_coverage" in config:
        min_coverage_value = config["min_coverage"]
    elif (
        "gates" in config
        and isinstance(config["gates"], dict)
        and "min_coverage" in config["gates"]
    ):
        min_coverage_value = config["gates"]["min_coverage"]

    # Only validate min_coverage if it's present
    if min_coverage_value is not None:
        if (
            not isinstance(min_coverage_value, int)
            or min_coverage_value < 0
            or min_coverage_value > 100
        ):
            return False

    # Handle gates structure validation
    if "gates" in config:
        if not isinstance(config["gates"], dict):
            return False  # gates must be a dict if present
        gates = config["gates"]
        # Validate boolean fields in gates (allow None for edge cases)
        boolean_fields = ["fail_on_bandit", "fail_on_lint", "fail_on_mypy"]
        for field in boolean_fields:
            if (
                field in gates
                and gates[field] is not None
                and not isinstance(gates[field], bool)
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

    # Validate boolean fields at top level (allow None for edge cases)
    boolean_fields = [
        "skip_tests",
        "enhanced_testgen",
        "fail_on_bandit",
        "fail_on_lint",
        "fail_on_mypy",
    ]
    for field in boolean_fields:
        if (
            field in config
            and config[field] is not None
            and not isinstance(config[field], bool)
        ):
            return False

    return True


def _validate_config(config: Dict[str, Any]) -> bool:
    """Internal validation function for backward compatibility."""
    return validate_config(config)


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
    if base_config is None:
        base_config = {}
    if override_config is None:
        return base_config.copy()

    # Start with a copy of base config
    result = base_config.copy()

    # Handle gates merging
    if "gates" in override_config and isinstance(override_config["gates"], dict):
        if "gates" not in result:
            result["gates"] = {}
        result["gates"].update(override_config["gates"])

    # Handle top-level merging
    for key, value in override_config.items():
        if key != "gates":  # gates already handled above
            result[key] = value

    return result


def _merge_configs(
    base_config: Dict[str, Any], override_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Internal merge function for backward compatibility."""
    return merge_configs(base_config, override_config)


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
            # Continue to try float parsing
            pass

        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            # Return as string if both int and float parsing fail
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
        config = get_default_config()

        # Update gates section first if present
        if "gates" in data:
            gates = data.get("gates", {})
            if "gates" in config:
                config["gates"].update(gates)

        # Special handling: if min_coverage is in gates, copy it to top level
        # for backward compatibility
        # This ensures gates.min_coverage takes priority over the default
        if "gates" in config and "min_coverage" in config["gates"]:
            config["min_coverage"] = config["gates"]["min_coverage"]

        # Update top-level fields (these take priority over gates)
        for key, value in data.items():
            if key != "gates":
                config[key] = value

        # Handle fields that might be incorrectly placed in gates section
        # Move them to top level if they don't belong in gates
        if "gates" in config:
            fields_to_move = [
                "skip_tests",
                "report_format",
                "report_path",
                "enhanced_testgen",
                "llm_provider",
                "llm_api_key",
                "llm_model",
            ]
            for field in fields_to_move:
                if field in config["gates"] and field not in config:
                    config[field] = config["gates"][field]
                    del config["gates"][field]

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

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return getattr(self, key, default)


class Config:
    """Configuration class for AI-Guard."""

    def __init__(self, config_path: str = "ai-guard.toml", **kwargs):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file
            **kwargs: Configuration values to override defaults
        """
        self.config_path = config_path
        self._config = load_config(config_path)

        # Override with provided kwargs
        for key, value in kwargs.items():
            self._config[key] = value

        # Create gates object for backward compatibility
        gates_config = self._config.get("gates", {})
        self.gates = Gates(
            min_coverage=gates_config.get(
                "min_coverage", self._config.get("min_coverage", 80)
            ),
            fail_on_bandit=gates_config.get(
                "fail_on_bandit", self._config.get("fail_on_bandit", True)
            ),
            fail_on_lint=gates_config.get(
                "fail_on_lint", self._config.get("fail_on_lint", True)
            ),
            fail_on_mypy=gates_config.get(
                "fail_on_mypy", self._config.get("fail_on_mypy", True)
            ),
        )

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

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create Config instance from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Config instance
        """
        instance = cls()
        instance._config.update(config_dict)

        # Update gates object to reflect the new config
        gates_config = instance._config.get("gates", {})
        instance.gates = Gates(
            min_coverage=gates_config.get(
                "min_coverage", instance._config.get("min_coverage", 80)
            ),
            fail_on_bandit=gates_config.get(
                "fail_on_bandit", instance._config.get("fail_on_bandit", True)
            ),
            fail_on_lint=gates_config.get(
                "fail_on_lint", instance._config.get("fail_on_lint", True)
            ),
            fail_on_mypy=gates_config.get(
                "fail_on_mypy", instance._config.get("fail_on_mypy", True)
            ),
        )
        return instance

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return self._config.copy()

    def validate(self) -> bool:
        """Validate the current configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Use the raw stored config values for validation
        return validate_config(self._config)
