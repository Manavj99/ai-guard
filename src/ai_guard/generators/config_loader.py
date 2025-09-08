"""Configuration loader for enhanced test generation."""

from .enhanced_testgen import TestGenerationConfig
import os
from typing import Optional, Dict, Any


def _get_toml_loader() -> Any:
    """Get the appropriate TOML loader."""
    try:
        import tomllib

        return tomllib
    except ModuleNotFoundError:
        import tomli

        return tomli


def load_testgen_config(config_path: Optional[str] = None) -> TestGenerationConfig:
    """Load test generation configuration from TOML file or environment variables.

    Args:
        config_path: Path to configuration file. If None, looks for:
                    1. ai-guard-testgen.toml in current directory
                    2. .ai-guard-testgen.toml in current directory
                    3. Environment variables

    Returns:
        TestGenerationConfig with loaded settings
    """
    config_data = {}

    # Try to load from TOML file
    if config_path and os.path.exists(config_path):
        config_data = _load_toml_config(config_path)
    else:
        # Try default config locations
        for default_path in ["ai-guard-testgen.toml", ".ai-guard-testgen.toml"]:
            if os.path.exists(default_path):
                config_data = _load_toml_config(default_path)
                break

    # Override with environment variables
    config_data.update(_load_env_config())

    # Create configuration object
    return TestGenerationConfig(
        llm_provider=config_data.get("llm", {}).get("provider", "openai"),
        llm_api_key=config_data.get("llm", {}).get("api_key") or _get_env_api_key(),
        llm_model=config_data.get("llm", {}).get("model", "gpt-4"),
        llm_temperature=float(config_data.get("llm", {}).get("temperature", 0.1)),
        test_framework=config_data.get("test_generation", {}).get(
            "framework", "pytest"
        ),
        generate_mocks=config_data.get("test_generation", {}).get(
            "generate_mocks", True
        ),
        generate_parametrized_tests=config_data.get("test_generation", {}).get(
            "generate_parametrized_tests", True
        ),
        generate_edge_cases=config_data.get("test_generation", {}).get(
            "generate_edge_cases", True
        ),
        max_tests_per_file=int(
            config_data.get("test_generation", {}).get("max_tests_per_file", 10)
        ),
        include_docstrings=config_data.get("test_generation", {}).get(
            "include_docstrings", True
        ),
        include_type_hints=config_data.get("test_generation", {}).get(
            "include_type_hints", True
        ),
        analyze_coverage_gaps=config_data.get("coverage_analysis", {}).get(
            "analyze_coverage_gaps", True
        ),
        min_coverage_threshold=float(
            config_data.get("coverage_analysis", {}).get("min_coverage_threshold", 80.0)
        ),
        output_directory=config_data.get("output", {}).get(
            "output_directory", "tests/unit"
        ),
        test_file_suffix=config_data.get("output", {}).get(
            "test_file_suffix", "_test.py"
        ),
    )


def _load_toml_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from TOML file."""
    try:
        with open(config_path, "rb") as f:
            return dict(_get_toml_loader().load(f))
    except Exception as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return {}


def _load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config: Dict[str, Any] = {}

    # LLM configuration
    if os.getenv("AI_GUARD_LLM_PROVIDER"):
        if "llm" not in config:
            config["llm"] = {}
        config["llm"]["provider"] = os.getenv("AI_GUARD_LLM_PROVIDER")

    if os.getenv("AI_GUARD_LLM_MODEL"):
        if "llm" not in config:
            config["llm"] = {}
        config["llm"]["model"] = os.getenv("AI_GUARD_LLM_MODEL")

    if os.getenv("AI_GUARD_LLM_TEMPERATURE"):
        if "llm" not in config:
            config["llm"] = {}
        try:
            config["llm"]["temperature"] = float(
                os.getenv("AI_GUARD_LLM_TEMPERATURE", "0.1")
            )
        except ValueError:
            # Use default if invalid temperature value
            config["llm"]["temperature"] = 0.1

    # Test generation configuration
    if os.getenv("AI_GUARD_TEST_FRAMEWORK"):
        if "test_generation" not in config:
            config["test_generation"] = {}
        config["test_generation"]["framework"] = os.getenv("AI_GUARD_TEST_FRAMEWORK")

    if os.getenv("AI_GUARD_GENERATE_MOCKS"):
        if "test_generation" not in config:
            config["test_generation"] = {}
        env_value = os.getenv("AI_GUARD_GENERATE_MOCKS")
        if env_value:
            config["test_generation"]["generate_mocks"] = env_value.lower() == "true"

    if os.getenv("AI_GUARD_GENERATE_EDGE_CASES"):
        if "test_generation" not in config:
            config["test_generation"] = {}
        env_value = os.getenv("AI_GUARD_GENERATE_EDGE_CASES")
        if env_value:
            config["test_generation"]["generate_edge_cases"] = (
                env_value.lower() == "true"
            )

    # Coverage configuration
    if os.getenv("AI_GUARD_ANALYZE_COVERAGE"):
        if "coverage_analysis" not in config:
            config["coverage_analysis"] = {}
        env_value = os.getenv("AI_GUARD_ANALYZE_COVERAGE")
        if env_value:
            config["coverage_analysis"]["analyze_coverage_gaps"] = (
                env_value.lower() == "true"
            )

    if os.getenv("AI_GUARD_MIN_COVERAGE"):
        if "coverage_analysis" not in config:
            config["coverage_analysis"] = {}
        try:
            config["coverage_analysis"]["min_coverage_threshold"] = float(
                os.getenv("AI_GUARD_MIN_COVERAGE", "80.0")
            )
        except ValueError:
            # Use default if invalid coverage value
            config["coverage_analysis"]["min_coverage_threshold"] = 80.0

    # Output configuration
    if os.getenv("AI_GUARD_OUTPUT_DIR"):
        if "output" not in config:
            config["output"] = {}
        config["output"]["output_directory"] = os.getenv("AI_GUARD_OUTPUT_DIR")

    return config


def _get_env_api_key() -> Optional[str]:
    """Get API key from environment variables."""
    # Try provider-specific environment variables first
    for provider in ["openai", "anthropic"]:
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if key:
            return key

    # Try generic AI-Guard API key
    return os.getenv("AI_GUARD_API_KEY")


def create_default_config(config_path: str = "ai-guard-testgen.toml") -> None:
    """Create a default configuration file."""
    default_config = """# AI-Guard Enhanced Test Generation Configuration
# This file contains settings for the enhanced test generation system

[llm]
# LLM provider: openai, anthropic, local
provider = "openai"
# API key (can also be set via environment variable OPENAI_API_KEY or ANTHROPIC_API_KEY)
api_key = ""
# Model to use
model = "gpt-4"
# Temperature for generation (0.0 = deterministic, 1.0 = creative)
temperature = 0.1
# Maximum tokens for generated tests
max_tokens = 1000

[test_generation]
# Test framework to use
framework = "pytest"
# Generate mocks for external dependencies
generate_mocks = true
# Generate parameterized tests
generate_parametrized_tests = true
# Generate edge case tests
generate_edge_cases = true
# Maximum number of tests per file
max_tests_per_file = 10
# Include docstrings in generated tests
include_docstrings = true
# Include type hints in generated tests
include_type_hints = true

[coverage_analysis]
# Analyze coverage gaps
analyze_coverage_gaps = true
# Minimum coverage threshold
min_coverage_threshold = 80.0
# Include coverage suggestions in generated tests
include_coverage_suggestions = true

[output]
# Output directory for generated tests
output_directory = "tests/unit"
# Suffix for generated test files
test_file_suffix = "_test.py"
# Generate separate test files per module
separate_files = false
# Include import statements
include_imports = true

[templates]
# Use built-in test templates
use_builtin_templates = true
# Path to custom template directory
custom_template_dir = ""
# Template to use for functions
function_template = "function_test"
# Template to use for classes
class_template = "class_test"
# Template to use for edge cases
edge_case_template = "edge_case_test"

[security]
# Validate generated code for security issues
validate_security = true
# Allow network calls in generated tests
allow_network_calls = false
# Allow file system operations in generated tests
allow_file_operations = false

[integration]
# Integrate with existing test suite
integrate_with_existing = true
# Update existing test files
update_existing = false
# Generate test discovery files
generate_discovery = true
"""

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(default_config)
        print(f"Created default configuration file: {config_path}")
        print("Please edit the file and add your API keys and preferences.")
    except Exception as e:
        print(f"Error creating configuration file: {e}")


def validate_config(config: TestGenerationConfig) -> bool:
    """Validate the configuration and print any issues."""
    issues = []

    # Check LLM configuration
    if config.llm_provider not in ["openai", "anthropic", "local"]:
        issues.append(f"Invalid LLM provider: {config.llm_provider}")

    if config.llm_provider in ["openai", "anthropic"] and not config.llm_api_key:
        issues.append(f"No API key provided for {config.llm_provider}")

    if config.llm_temperature < 0.0 or config.llm_temperature > 1.0:
        issues.append(
            f"Invalid temperature: {config.llm_temperature} (must be 0.0-1.0)"
        )

    # Check test generation configuration
    if config.test_framework not in ["pytest", "unittest"]:
        issues.append(f"Unsupported test framework: {config.test_framework}")

    if config.max_tests_per_file < 1:
        issues.append(f"Invalid max_tests_per_file: {config.max_tests_per_file}")

    # Check coverage configuration
    if config.min_coverage_threshold < 0.0 or config.min_coverage_threshold > 100.0:
        issues.append(f"Invalid coverage threshold: {config.min_coverage_threshold}%")

    # Check output configuration
    if not config.output_directory:
        issues.append("Output directory cannot be empty")

    if issues:
        print("Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    return True


if __name__ == "__main__":
    # Create default config if run directly
    create_default_config()
