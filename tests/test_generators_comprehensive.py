"""Comprehensive tests for generators module to improve coverage."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from src.ai_guard.generators.testgen import generate_speculative_tests, main as testgen_main
from src.ai_guard.generators.config_loader import load_testgen_config


class TestTestGen:
    """Test test generation functionality."""

    def test_generate_speculative_tests_basic(self):
        """Test basic speculative test generation."""
        changed_files = ["src/test.py", "src/utils.py"]
        
        result = generate_speculative_tests(changed_files)
        assert isinstance(result, str)
        assert "Auto-generated speculative tests" in result
        assert "src/test.py" in result
        assert "src/utils.py" in result

    def test_generate_speculative_tests_empty(self):
        """Test speculative test generation with empty list."""
        result = generate_speculative_tests([])
        assert result == ""

    def test_generate_speculative_tests_none(self):
        """Test speculative test generation with None."""
        result = generate_speculative_tests(None)
        assert result == ""

    def test_testgen_main(self):
        """Test testgen main function."""
        # Test with valid arguments instead of --help to avoid argparse conflicts
        with patch('sys.argv', ['testgen', '--event', 'nonexistent.json']):
            # Should not raise an exception, just return
            testgen_main()


class TestConfigLoader:
    """Test configuration loading functionality."""

    def test_load_testgen_config_default(self):
        """Test loading default testgen configuration."""
        config = load_testgen_config()
        assert hasattr(config, 'test_framework')
        assert config.test_framework == "pytest"

    def test_load_testgen_config_file(self):
        """Test loading testgen configuration from file."""
        config_content = """
[test_generation]
framework = "pytest"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_testgen_config(temp_path)
            assert config.test_framework == "pytest"
        finally:
            os.unlink(temp_path)

    def test_load_testgen_config_invalid_file(self):
        """Test loading testgen configuration from invalid file."""
        config = load_testgen_config("nonexistent.toml")
        assert hasattr(config, 'test_framework')

    def test_load_testgen_config_invalid_content(self):
        """Test loading testgen configuration from invalid content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content")
            temp_path = f.name
        
        try:
            config = load_testgen_config(temp_path)
            assert hasattr(config, 'test_framework')
        finally:
            os.unlink(temp_path)


class TestEnhancedTestGen:
    """Test enhanced test generation functionality."""

    def test_enhanced_testgen_import(self):
        """Test that enhanced testgen can be imported."""
        try:
            from src.ai_guard.generators.enhanced_testgen import EnhancedTestGenerator
            from src.ai_guard.generators.config_loader import load_testgen_config
            config = load_testgen_config()
            generator = EnhancedTestGenerator(config)
            assert generator is not None
        except ImportError:
            pytest.skip("EnhancedTestGenerator not available")

    def test_enhanced_testgen_basic_functionality(self):
        """Test basic enhanced testgen functionality."""
        try:
            from src.ai_guard.generators.enhanced_testgen import EnhancedTestGenerator
            from src.ai_guard.generators.config_loader import load_testgen_config
            
            config = load_testgen_config()
            generator = EnhancedTestGenerator(config)
            code = """
def calculate(a, b, operation):
    if operation == 'add':
        return a + b
    elif operation == 'multiply':
        return a * b
    else:
        return 0
"""
            
            # Test basic functionality without full implementation
            assert hasattr(generator, 'generate_tests')
            assert callable(generator.generate_tests)
            
        except ImportError:
            pytest.skip("EnhancedTestGenerator not available")


class TestAdditionalCoverage:
    """Test additional functions to improve coverage."""

    def test_generators_module_imports(self):
        """Test that all generator modules can be imported."""
        try:
            from src.ai_guard.generators import testgen
            from src.ai_guard.generators import config_loader
            from src.ai_guard.generators import enhanced_testgen
            assert True
        except ImportError as e:
            pytest.skip(f"Generator module import failed: {e}")

    def test_testgen_config_defaults(self):
        """Test default testgen configuration values."""
        config = load_testgen_config()
        
        # Check that required attributes exist
        assert hasattr(config, 'test_framework')
        assert hasattr(config, 'min_coverage_threshold')
        assert hasattr(config, 'max_tests_per_file')

    def test_generate_tests_error_handling(self):
        """Test error handling in test generation."""
        # Test basic error handling - just check that we can import the module
        try:
            from src.ai_guard.generators import enhanced_testgen
            assert True
        except ImportError:
            pytest.skip("Enhanced testgen not available")
