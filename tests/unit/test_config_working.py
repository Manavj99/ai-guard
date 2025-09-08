"""Working comprehensive tests for the config module."""

import os
import tempfile
from unittest.mock import patch, mock_open

from ai_guard.config import load_config


class TestConfigWorking:
    """Working comprehensive tests for config functionality."""

    def test_load_config_default(self):
        """Test load_config with default values."""
        config = load_config()

        assert config.min_coverage == 80
        assert config.skip_tests is False
        assert config.report_format == "sarif"
        assert config.report_path == "ai-guard.sarif"
        assert config.enhanced_testgen_enabled is False
        assert config.pr_annotations_enabled is False

    def test_load_config_from_file(self):
        """Test load_config loading from file."""
        config_data = """
[ai-guard]
min_coverage = 90
skip_tests = true
report_format = "json"
report_path = "custom-report.json"
enhanced_testgen_enabled = true
pr_annotations_enabled = true
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            f.write(config_data)
            config_path = f.name

        try:
            with patch("ai_guard.config.os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=config_data)):
                    config = load_config(config_path)

            assert config.min_coverage == 90
            assert config.skip_tests is True
            assert config.report_format == "json"
            assert config.report_path == "custom-report.json"
            assert config.enhanced_testgen_enabled is True
            assert config.pr_annotations_enabled is True
        finally:
            os.unlink(config_path)

    def test_load_config_file_not_found(self):
        """Test load_config when file doesn't exist."""
        with patch("ai_guard.config.os.path.exists", return_value=False):
            config = load_config("nonexistent.toml")

        # Should return default config
        assert config.min_coverage == 80
        assert config.skip_tests is False

    def test_load_config_invalid_toml(self):
        """Test load_config with invalid TOML."""
        invalid_toml = "invalid toml content ["

        with patch("ai_guard.config.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=invalid_toml)):
                config = load_config("invalid.toml")

        # Should return default config
        assert config.min_coverage == 80
        assert config.skip_tests is False

    def test_load_config_partial_config(self):
        """Test load_config with partial configuration."""
        config_data = """
[ai-guard]
min_coverage = 75
report_format = "html"
"""

        with patch("ai_guard.config.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_data)):
                config = load_config("partial.toml")

        assert config.min_coverage == 75
        assert config.report_format == "html"
        # Other values should be defaults
        assert config.skip_tests is False
        assert config.report_path == "ai-guard.html"
        assert config.enhanced_testgen_enabled is False
        assert config.pr_annotations_enabled is False

    def test_config_creation(self):
        """Test Config dataclass creation."""
        config = Config(
            min_coverage=85,
            skip_tests=True,
            report_format="json",
            report_path="test.json",
            enhanced_testgen_enabled=True,
            pr_annotations_enabled=True,
        )

        assert config.min_coverage == 85
        assert config.skip_tests is True
        assert config.report_format == "json"
        assert config.report_path == "test.json"
        assert config.enhanced_testgen_enabled is True
        assert config.pr_annotations_enabled is True

    def test_config_default_values(self):
        """Test Config with default values."""
        config = Config()

        assert config.min_coverage == 80
        assert config.skip_tests is False
        assert config.report_format == "sarif"
        assert config.report_path == "ai-guard.sarif"
        assert config.enhanced_testgen_enabled is False
        assert config.pr_annotations_enabled is False

    def test_load_config_environment_variables(self):
        """Test load_config with environment variables."""
        with patch.dict(
            os.environ,
            {
                "AI_GUARD_MIN_COVERAGE": "95",
                "AI_GUARD_SKIP_TESTS": "true",
                "AI_GUARD_REPORT_FORMAT": "html",
                "AI_GUARD_REPORT_PATH": "env-report.html",
                "AI_GUARD_ENHANCED_TESTGEN_ENABLED": "true",
                "AI_GUARD_PR_ANNOTATIONS_ENABLED": "true",
            },
        ):
            config = load_config()

        assert config.min_coverage == 95
        assert config.skip_tests is True
        assert config.report_format == "html"
        assert config.report_path == "env-report.html"
        assert config.enhanced_testgen_enabled is True
        assert config.pr_annotations_enabled is True

    def test_load_config_file_overrides_env(self):
        """Test that config file overrides environment variables."""
        config_data = """
[ai-guard]
min_coverage = 85
skip_tests = false
"""

        with patch.dict(
            os.environ, {"AI_GUARD_MIN_COVERAGE": "95", "AI_GUARD_SKIP_TESTS": "true"}
        ):
            with patch("ai_guard.config.os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=config_data)):
                    config = load_config("config.toml")

        # File values should override environment
        assert config.min_coverage == 85
        assert config.skip_tests is False

    def test_load_config_invalid_boolean_env(self):
        """Test load_config with invalid boolean environment variable."""
        with patch.dict(os.environ, {"AI_GUARD_SKIP_TESTS": "invalid_boolean"}):
            config = load_config()

        # Should use default value
        assert config.skip_tests is False

    def test_load_config_invalid_integer_env(self):
        """Test load_config with invalid integer environment variable."""
        with patch.dict(os.environ, {"AI_GUARD_MIN_COVERAGE": "not_a_number"}):
            config = load_config()

        # Should use default value
        assert config.min_coverage == 80

    def test_load_config_ai_guard_toml(self):
        """Test load_config loading from ai-guard.toml."""
        config_data = """
[ai-guard]
min_coverage = 88
"""

        with patch("ai_guard.config.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_data)):
                config = load_config()

        assert config.min_coverage == 88

    def test_load_config_pyproject_toml(self):
        """Test load_config loading from pyproject.toml."""
        config_data = """
[tool.ai-guard]
min_coverage = 92
"""

        with patch(
            "ai_guard.config.os.path.exists",
            side_effect=lambda x: x == "pyproject.toml",
        ):
            with patch("builtins.open", mock_open(read_data=config_data)):
                config = load_config()

        assert config.min_coverage == 92
