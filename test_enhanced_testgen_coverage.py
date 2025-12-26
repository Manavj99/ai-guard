#!/usr/bin/env python3
"""Comprehensive test for enhanced_testgen.py to improve coverage."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    EnhancedTestGenerator,
    CodeChange,
    TestGenTemplate,
)


class TestTestGenConfigCoverage:
    """Test TestGenConfig class for better coverage."""
    
    def test_to_dict_comprehensive(self):
        """Test to_dict method with all fields."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model="claude-3",
            llm_temperature=0.5,
            test_framework="unittest",
            generate_mocks=False,
            generate_parametrized_tests=False,
            generate_edge_cases=False,
            max_tests_per_file=5,
            analyze_coverage_gaps=False,
            min_coverage_threshold=90.0,
            output_directory="custom_tests",
            test_file_suffix="_spec.py",
            include_docstrings=False,
            include_type_hints=False
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["llm_provider"] == "anthropic"
        assert config_dict["llm_api_key"] == "test-key"
        assert config_dict["llm_model"] == "claude-3"
        assert config_dict["llm_temperature"] == 0.5
        assert config_dict["test_framework"] == "unittest"
        assert config_dict["generate_mocks"] is False
        assert config_dict["generate_parametrized_tests"] is False
        assert config_dict["generate_edge_cases"] is False
        assert config_dict["max_tests_per_file"] == 5
        assert config_dict["analyze_coverage_gaps"] is False
        assert config_dict["min_coverage_threshold"] == 90.0
        assert config_dict["output_directory"] == "custom_tests"
        assert config_dict["test_file_suffix"] == "_spec.py"
        assert config_dict["include_docstrings"] is False
        assert config_dict["include_type_hints"] is False
    
    def test_from_dict_comprehensive(self):
        """Test from_dict method with all fields."""
        config_dict = {
            "llm_provider": "local",
            "llm_api_key": None,
            "llm_model": "local-model",
            "llm_temperature": 0.3,
            "test_framework": "pytest",
            "generate_mocks": True,
            "generate_parametrized_tests": True,
            "generate_edge_cases": True,
            "max_tests_per_file": 15,
            "analyze_coverage_gaps": True,
            "min_coverage_threshold": 75.0,
            "output_directory": "test_dir",
            "test_file_suffix": "_test.py",
            "include_docstrings": True,
            "include_type_hints": True
        }
        
        config = TestGenConfig.from_dict(config_dict)
        
        assert config.llm_provider == "local"
        assert config.llm_api_key is None
        assert config.llm_model == "local-model"
        assert config.llm_temperature == 0.3
        assert config.test_framework == "pytest"
        assert config.generate_mocks is True
        assert config.generate_parametrized_tests is True
        assert config.generate_edge_cases is True
        assert config.max_tests_per_file == 15
        assert config.analyze_coverage_gaps is True
        assert config.min_coverage_threshold == 75.0
        assert config.output_directory == "test_dir"
        assert config.test_file_suffix == "_test.py"
        assert config.include_docstrings is True
        assert config.include_type_hints is True
    
    def test_validate_all_conditions(self):
        """Test all validation conditions."""
        # Test valid config
        config = TestGenConfig(llm_api_key="test-key")
        assert config.validate() is True
        
        # Test invalid LLM provider
        config = TestGenConfig(llm_provider="invalid")
        assert config.validate() is False
        
        # Test missing API key for openai
        config = TestGenConfig(llm_provider="openai", llm_api_key=None)
        assert config.validate() is False
        
        # Test missing API key for anthropic
        config = TestGenConfig(llm_provider="anthropic", llm_api_key=None)
        assert config.validate() is False
        
        # Test local provider without API key (should be valid)
        config = TestGenConfig(llm_provider="local", llm_api_key=None)
        assert config.validate() is True
        
        # Test invalid temperature - too high
        config = TestGenConfig(llm_temperature=1.1)
        assert config.validate() is False
        
        # Test invalid temperature - too low
        config = TestGenConfig(llm_temperature=-0.1)
        assert config.validate() is False
        
        # Test invalid test framework
        config = TestGenConfig(test_framework="invalid")
        assert config.validate() is False
        
        # Test invalid max tests per file
        config = TestGenConfig(max_tests_per_file=0)
        assert config.validate() is False
        
        # Test invalid coverage threshold - too high
        config = TestGenConfig(min_coverage_threshold=101.0)
        assert config.validate() is False
        
        # Test invalid coverage threshold - too low
        config = TestGenConfig(min_coverage_threshold=-1.0)
        assert config.validate() is False
        
        # Test empty output directory
        config = TestGenConfig(output_directory="")
        assert config.validate() is False


class TestCodeChangeCoverage:
    """Test CodeChange class for better coverage."""
    
    def test_code_change_creation_minimal(self):
        """Test CodeChange creation with minimal data."""
        change = CodeChange(
            file_path="test.py",
            change_type="function",
            function_name="test_func"
        )
        
        assert change.file_path == "test.py"
        assert change.change_type == "function"
        assert change.function_name == "test_func"
        assert change.class_name is None
        assert change.code_snippet == ""  # Default value is empty string, not None
        assert change.line_number is None
        assert change.context == ""  # Default value is empty string, not None
    
    def test_code_change_creation_full(self):
        """Test CodeChange creation with all data."""
        change = CodeChange(
            file_path="test.py",
            change_type="class",
            function_name="test_method",
            class_name="TestClass",
            code_snippet="def test_method(): pass",
            line_number=42,
            context="class TestClass:"
        )
        
        assert change.file_path == "test.py"
        assert change.change_type == "class"
        assert change.function_name == "test_method"
        assert change.class_name == "TestClass"
        assert change.code_snippet == "def test_method(): pass"
        assert change.line_number == 42
        assert change.context == "class TestClass:"
    
    def test_code_change_to_dict(self):
        """Test CodeChange to_dict method."""
        change = CodeChange(
            file_path="test.py",
            change_type="function",
            function_name="test_func",
            code_snippet="def test_func(): pass"
        )
        
        change_dict = change.to_dict()
        
        assert change_dict["file_path"] == "test.py"
        assert change_dict["change_type"] == "function"
        assert change_dict["function_name"] == "test_func"
        assert change_dict["code_snippet"] == "def test_func(): pass"


class TestTestGenTemplateCoverage:
    """Test TestGenTemplate class for better coverage."""
    
    def test_template_creation(self):
        """Test TestGenTemplate creation."""
        template = TestGenTemplate(
            name="function_test",
            template="def test_{function_name}(): pass",
            description="Basic function test template",
            variables=["function_name"],
            applicable_to=["function"]
        )
        
        assert template.name == "function_test"
        assert template.template == "def test_{function_name}(): pass"
        assert template.description == "Basic function test template"
        assert template.variables == ["function_name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGeneratorCoverage:
    """Test EnhancedTestGenerator class for better coverage."""
    
    def test_init_with_config(self):
        """Test EnhancedTestGenerator initialization with config."""
        config = TestGenConfig(llm_api_key="test-key")
        generator = EnhancedTestGenerator(config)
        
        assert generator.config == config
        assert generator.test_templates is not None
    
    def test_load_test_templates(self):
        """Test loading test templates."""
        config = TestGenConfig(llm_api_key="test-key")
        generator = EnhancedTestGenerator(config)
        
        templates = generator._load_test_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all(isinstance(t, TestGenTemplate) for t in templates)
    
    @patch('src.ai_guard.generators.enhanced_testgen.openai')
    def test_initialize_llm_client_openai(self, mock_openai):
        """Test LLM client initialization for OpenAI."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4"
        )
        generator = EnhancedTestGenerator(config)
        
        client = generator._initialize_llm_client()
        
        assert client is not None
        assert mock_openai.api_key == "test-key"
    
    @patch('src.ai_guard.generators.enhanced_testgen.anthropic')
    def test_initialize_llm_client_anthropic(self, mock_anthropic):
        """Test LLM client initialization for Anthropic."""
        mock_anthropic.Anthropic.return_value = Mock()
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model="claude-3"
        )
        generator = EnhancedTestGenerator(config)
        
        client = generator._initialize_llm_client()
        
        assert client is not None
        mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")
    
    def test_initialize_llm_client_local(self):
        """Test LLM client initialization for local provider."""
        config = TestGenConfig(llm_provider="local")
        generator = EnhancedTestGenerator(config)
        
        client = generator._initialize_llm_client()
        
        assert client is not None
        assert hasattr(client, 'generate_tests')
    
    def test_initialize_llm_client_invalid(self):
        """Test LLM client initialization with invalid provider."""
        config = TestGenConfig(llm_provider="invalid")
        generator = EnhancedTestGenerator(config)
        
        client = generator._initialize_llm_client()
        assert client is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
