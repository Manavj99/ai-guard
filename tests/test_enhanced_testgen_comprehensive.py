"""Comprehensive tests for EnhancedTestGenerator."""

import ast
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.ai_guard.generators.enhanced_testgen import (
    EnhancedTestGenerator,
    TestGenConfig,
    CodeChange,
    TestGenTemplate
)


class TestTestGenConfig:
    """Test TestGenConfig class."""

    def test_config_creation(self):
        """Test basic configuration creation."""
        config = TestGenConfig()
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.test_framework == "pytest"
        assert config.generate_mocks is True
        assert config.max_tests_per_file == 10

    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_model="claude-3",
            test_framework="unittest"
        )
        config_dict = config.to_dict()
        
        assert config_dict["llm_provider"] == "anthropic"
        assert config_dict["llm_model"] == "claude-3"
        assert config_dict["test_framework"] == "unittest"

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "llm_provider": "local",
            "llm_model": "llama-2",
            "test_framework": "pytest",
            "generate_mocks": False
        }
        config = TestGenConfig.from_dict(config_dict)
        
        assert config.llm_provider == "local"
        assert config.llm_model == "llama-2"
        assert config.test_framework == "pytest"
        assert config.generate_mocks is False

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config with API key
        config = TestGenConfig(llm_api_key="test-key")
        assert config.validate() is True

        # Invalid LLM provider
        config.llm_provider = "invalid"
        assert config.validate() is False

        # Invalid test framework
        config.llm_provider = "openai"
        config.test_framework = "invalid"
        assert config.validate() is False
        
        # Missing API key for OpenAI
        config.test_framework = "pytest"
        config.llm_api_key = None
        assert config.validate() is False


class TestCodeChange:
    """Test CodeChange class."""

    def test_code_change_creation(self):
        """Test basic code change creation."""
        change = CodeChange(
            change_type="function",
            function_name="test_func",
            file_path="test.py",
            line_number=10
        )
        
        assert change.change_type == "function"
        assert change.function_name == "test_func"
        assert change.file_path == "test.py"
        assert change.line_number == 10

    def test_code_change_to_dict(self):
        """Test code change to dictionary conversion."""
        change = CodeChange(
            change_type="class",
            class_name="TestClass",
            file_path="test.py",
            line_number=5,
            context="class definition"
        )
        
        change_dict = change.to_dict()
        assert change_dict["change_type"] == "class"
        assert change_dict["class_name"] == "TestClass"
        assert change_dict["file_path"] == "test.py"
        assert change_dict["line_number"] == 5
        assert change_dict["context"] == "class definition"


class TestTestGenTemplate:
    """Test TestGenTemplate class."""

    def test_template_creation(self):
        """Test template creation."""
        template = TestGenTemplate(
            name="test_template",
            description="A test template",
            template="def test_{name}(): pass",
            variables=["name"],
            applicable_to=["function"]
        )
        
        assert template.name == "test_template"
        assert template.description == "A test template"
        assert template.template == "def test_{name}(): pass"
        assert template.variables == ["name"]
        assert template.applicable_to == ["function"]


class TestEnhancedTestGenerator:
    """Test EnhancedTestGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            test_framework="pytest"
        )
        self.generator = EnhancedTestGenerator(self.config)

    def test_generator_initialization(self):
        """Test generator initialization."""
        assert self.generator.config == self.config
        assert isinstance(self.generator.test_templates, list)
        assert len(self.generator.test_templates) > 0

    def test_load_test_templates(self):
        """Test loading of test templates."""
        templates = self.generator._load_test_templates()
        
        assert len(templates) > 0
        assert all(isinstance(t, TestGenTemplate) for t in templates)
        
        # Check for specific templates
        template_names = [t.name for t in templates]
        assert "function_test" in template_names
        assert "function_parametrized_test" in template_names
        assert "function_error_test" in template_names

    @patch('src.ai_guard.generators.enhanced_testgen.subprocess.run')
    def test_initialize_llm_client_openai(self, mock_run):
        """Test LLM client initialization for OpenAI."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test-key"
        )
        generator = EnhancedTestGenerator(config)
        
        # Should not raise an exception
        assert generator.llm_client is not None

    def test_initialize_llm_client_no_key(self):
        """Test LLM client initialization without API key."""
        config = TestGenConfig(llm_provider="openai")
        generator = EnhancedTestGenerator(config)
        
        assert generator.llm_client is None

    def test_parse_diff_lines(self):
        """Test parsing diff content for changed lines."""
        diff_content = """@@ -10,5 +10,5 @@ def test_function():
-    old_line = "old"
+    new_line = "new"
@@ -20,3 +20,3 @@ class TestClass:
-    def old_method(self):
+    def new_method(self):
"""
        
        changed_lines = self.generator._parse_diff_lines(diff_content)
        assert len(changed_lines) > 0
        assert all(isinstance(line, int) for line in changed_lines)

    def test_is_function_changed(self):
        """Test function change detection."""
        # Create a mock function node
        func_node = Mock()
        func_node.lineno = 10
        func_node.end_lineno = 15
        
        changed_lines = [10, 12, 14]
        assert self.generator._is_function_changed(func_node, changed_lines) is True
        
        changed_lines = [20, 25]
        assert self.generator._is_function_changed(func_node, changed_lines) is False

    def test_is_class_changed(self):
        """Test class change detection."""
        # Create a mock class node
        class_node = Mock()
        class_node.lineno = 5
        class_node.end_lineno = 20
        
        changed_lines = [10, 15]
        assert self.generator._is_class_changed(class_node, changed_lines) is True
        
        changed_lines = [25, 30]
        assert self.generator._is_class_changed(class_node, changed_lines) is False

    def test_get_function_context(self):
        """Test function context extraction."""
        # Create a mock function node
        func_node = Mock()
        func_node.name = "test_function"
        func_node.args = Mock()
        func_node.args.args = [Mock(arg="param1"), Mock(arg="param2")]
        func_node.returns = None
        func_node.decorator_list = []
        
        context = self.generator._get_function_context(func_node)
        assert "param1" in context
        assert "param2" in context
        assert "Arguments:" in context

    def test_get_class_context(self):
        """Test class context extraction."""
        # Create a mock class node
        class_node = Mock()
        class_node.name = "TestClass"
        class_node.bases = []
        class_node.decorator_list = []
        class_node.body = []  # Add empty body
        
        context = self.generator._get_class_context(class_node)
        assert isinstance(context, str)

    def test_generate_function_tests(self):
        """Test function test generation."""
        code_change = CodeChange(
            change_type="function",
            function_name="test_func",
            file_path="test.py",
            line_number=10,
            context="def test_func(param1, param2): return param1 + param2"
        )
        
        tests = self.generator._generate_function_tests(code_change)
        assert isinstance(tests, str)
        assert "test_func" in tests
        assert "def test_" in tests

    def test_generate_test_cases(self):
        """Test test case generation for parametrized tests."""
        # Create a mock function definition
        func_def = Mock()
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="param1"), Mock(arg="param2")]
        
        test_cases = self.generator._generate_test_cases(func_def)
        assert isinstance(test_cases, str)
        assert "test_input" in test_cases
        assert "expected_output" in test_cases

    def test_generate_class_tests(self):
        """Test class test generation."""
        code_change = CodeChange(
            change_type="class",
            class_name="TestClass",
            file_path="test.py",
            line_number=5,
            context="class TestClass: pass"
        )
        
        tests = self.generator._generate_class_tests(code_change)
        assert isinstance(tests, str)
        assert "TestClass" in tests
        assert "class Test" in tests

    def test_generate_generic_tests(self):
        """Test generic test generation."""
        code_change = CodeChange(
            change_type="unknown",
            function_name="unknown_func",
            file_path="test.py",
            line_number=1
        )
        
        tests = self.generator._generate_generic_tests(code_change)
        assert isinstance(tests, str)
        assert "unknown_func" in tests

    def test_analyze_coverage_gaps_disabled(self):
        """Test coverage gap analysis when disabled."""
        config = TestGenConfig(analyze_coverage_gaps=False)
        generator = EnhancedTestGenerator(config)
        
        gaps = generator.analyze_coverage_gaps(["test.py"])
        assert gaps == {}

    @patch('src.ai_guard.generators.enhanced_testgen.subprocess.run')
    def test_analyze_file_coverage(self, mock_run):
        """Test file coverage analysis."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"test.py": {"lines": {"1": 1, "2": 0, "3": 1}}}'
        )
        
        gaps = self.generator._analyze_file_coverage("test.py")
        assert isinstance(gaps, list)

    def test_generate_tests_for_changes_empty(self):
        """Test test generation for empty changes list."""
        tests = self.generator.generate_tests_for_changes([])
        assert tests == ""

    def test_generate_tests_for_changes(self):
        """Test test generation for changes."""
        changes = [
            CodeChange(
                change_type="function",
                function_name="test_func",
                file_path="test.py",
                line_number=10
            )
        ]
        
        tests = self.generator.generate_tests_for_changes(changes)
        assert isinstance(tests, str)
        assert "test_func" in tests

    def test_generate_function_test(self):
        """Test individual function test generation."""
        change = CodeChange(
            change_type="function",
            function_name="test_func",
            file_path="test.py",
                line_number=10
            )
        
        test = self.generator._generate_function_test(change)
        assert isinstance(test, str)
        assert "test_func" in test

    @patch('src.ai_guard.generators.enhanced_testgen.changed_python_files')
    def test_analyze_code_changes(self, mock_changed_files):
        """Test code changes analysis."""
        mock_changed_files.return_value = ["test.py"]
        
        with patch.object(self.generator, '_analyze_file_changes') as mock_analyze:
            mock_analyze.return_value = [
                CodeChange(
                    change_type="function",
                    function_name="test_func",
                    file_path="test.py",
                    line_number=10
                )
            ]
            
            changes = self.generator.analyze_code_changes(["test.py"])
            assert len(changes) == 1
            assert changes[0].function_name == "test_func"

    @patch('src.ai_guard.generators.enhanced_testgen.subprocess.run')
    def test_get_file_diff(self, mock_run):
        """Test file diff retrieval."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="diff content"
        )
        
        diff = self.generator._get_file_diff("test.py")
        assert diff == "diff content"

    def test_get_file_diff_no_event(self):
        """Test file diff retrieval without event path."""
        with patch('src.ai_guard.generators.enhanced_testgen.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="diff content"
            )
            
            diff = self.generator._get_file_diff("test.py")
            assert diff == "diff content"

    def test_get_base_head_from_event(self):
        """Test base and head extraction from GitHub event."""
        event_data = {
            "pull_request": {
                "base": {"sha": "base-sha"},
                "head": {"sha": "head-sha"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(event_data, f)
            event_path = f.name
        
        try:
            base, head = self.generator._get_base_head_from_event(event_path)
            assert base == "base-sha"
            assert head == "head-sha"
        finally:
            os.unlink(event_path)

    def test_get_base_head_from_event_invalid(self):
        """Test base and head extraction from invalid event."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("invalid json")
            event_path = f.name
        
        try:
            result = self.generator._get_base_head_from_event(event_path)
            assert result is None
        finally:
            os.unlink(event_path)

    def test_generate_tests_with_llm_no_client(self):
        """Test LLM test generation without client."""
        config = TestGenConfig(llm_provider="openai")  # No API key
        generator = EnhancedTestGenerator(config)
        
        code_change = CodeChange(
            change_type="function",
            function_name="test_func",
            file_path="test.py",
            line_number=10
        )
        
        tests = generator.generate_tests_with_llm(code_change)
        assert isinstance(tests, str)
        assert "test_func" in tests

    def test_create_llm_prompt(self):
        """Test LLM prompt creation."""
        code_change = CodeChange(
            change_type="function",
            function_name="test_func",
            file_path="test.py",
            line_number=10,
            context="def test_func(x): return x * 2"
        )
        
        prompt = self.generator._create_llm_prompt(code_change)
        assert isinstance(prompt, str)
        assert "test_func" in prompt
        assert "function" in prompt

    def test_generate_tests_with_templates(self):
        """Test test generation using templates."""
        code_change = CodeChange(
            change_type="function",
            function_name="test_func",
            file_path="test.py",
            line_number=10
        )
        
        tests = self.generator._generate_tests_with_templates(code_change)
        assert isinstance(tests, str)
        assert "test_func" in tests

    def test_generate_coverage_tests(self):
        """Test coverage-specific test generation."""
        func_def = Mock()
        func_def.name = "test_func"
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="param")]
        
        tests = self.generator._generate_coverage_tests(func_def)
        assert isinstance(tests, str)
        assert "test_func" in tests

    def test_generate_test_file(self):
        """Test test file generation."""
        changes = [
            CodeChange(
                change_type="function",
                function_name="test_func",
                file_path="test.py",
                line_number=10
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_generated.py")
            result = self.generator.generate_test_file(changes, output_path)
            
            assert isinstance(result, str)
            assert "test_func" in result
            assert "Auto-generated tests" in result

    @patch('src.ai_guard.generators.enhanced_testgen.changed_python_files')
    def test_generate_tests(self, mock_changed_files):
        """Test main test generation method."""
        mock_changed_files.return_value = ["test.py"]
        
        with patch.object(self.generator, 'analyze_code_changes') as mock_analyze:
            mock_analyze.return_value = [
                CodeChange(
                    change_type="function",
                    function_name="test_func",
                    file_path="test.py",
                    line_number=10
                )
            ]
            
            with patch.object(self.generator, 'generate_test_file') as mock_generate:
                mock_generate.return_value = "test_output.py"
                
                result = self.generator.generate_tests(["test.py"], "output.py")
                assert result == "test_output.py"


class TestIntegration:
    """Integration tests for EnhancedTestGenerator."""

    def test_end_to_end_test_generation(self):
        """Test end-to-end test generation workflow."""
        config = TestGenConfig(
            llm_provider="openai",
            test_framework="pytest",
            generate_mocks=True
        )
        generator = EnhancedTestGenerator(config)
        
        # Create a simple test file
        test_code = """
def add_numbers(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write(test_code)
            test_file = f.name
        
        try:
            # Analyze changes
            changes = generator.analyze_code_changes([test_file])
            
            # Generate tests
            if changes:
                tests = generator.generate_tests_for_changes(changes)
                assert isinstance(tests, str)
                assert len(tests) > 0
        finally:
            os.unlink(test_file)

    def test_configuration_persistence(self):
        """Test configuration persistence and loading."""
        config = TestGenConfig(
            llm_provider="anthropic",
            llm_model="claude-3",
            test_framework="unittest",
            generate_mocks=False
        )
        
        # Convert to dict and back
        config_dict = config.to_dict()
        loaded_config = TestGenConfig.from_dict(config_dict)
        
        assert loaded_config.llm_provider == config.llm_provider
        assert loaded_config.llm_model == config.llm_model
        assert loaded_config.test_framework == config.test_framework
        assert loaded_config.generate_mocks == config.generate_mocks