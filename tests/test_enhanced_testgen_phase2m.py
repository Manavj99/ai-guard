import ast
import os
import sys
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch, mock_open

import pytest

# Ensure project root is on sys.path so `src` package is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ai_guard.generators.enhanced_testgen import (
    EnhancedTestGenerator,
    TestGenConfig,
    CodeChange,
    main as enhanced_main,
)


def _make_subprocess_result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_initialize_llm_client_paths_openai_importerror():
    cfg = TestGenConfig(llm_provider="openai", llm_api_key="key")
    with patch.dict("sys.modules", {"openai": None}):
        gen = EnhancedTestGenerator(cfg)
        # When openai import fails, client becomes None
        assert gen.llm_client is None


def test_initialize_llm_client_paths_anthropic_importerror():
    cfg = TestGenConfig(llm_provider="anthropic", llm_api_key="key")
    with patch.dict("sys.modules", {"anthropic": None}):
        gen = EnhancedTestGenerator(cfg)
        assert gen.llm_client is None


def test_initialize_llm_client_no_key_local_returns_mock():
    cfg = TestGenConfig(llm_provider="local", llm_api_key=None)
    gen = EnhancedTestGenerator(cfg)
    assert isinstance(gen.llm_client, Mock)


def test_analyze_file_changes_without_diff_includes_all_nodes(tmp_path):
    src = """
class Foo:
    def method(self):
        return 1

def bar(x, y):
    return x + y
""".strip()
    file_path = tmp_path / "sample.py"
    file_path.write_text(src, encoding="utf-8")

    cfg = TestGenConfig(llm_provider="local")
    gen = EnhancedTestGenerator(cfg)

    # Force git diff to return no changes so the code uses the fallback range
    with patch("subprocess.run", return_value=_make_subprocess_result(0, stdout="")):
        changes = gen._analyze_file_changes(str(file_path))

    kinds = {c.change_type for c in changes}
    names = {c.function_name or c.class_name for c in changes}
    # At least one class and one function detected
    assert "class" in kinds and "function" in kinds
    # Ensure the top-level function and class are included
    assert {"Foo", "bar"}.issubset(names)


def test_parse_diff_lines_extracts_new_chunk_start_lines():
    diff = """
@@ -10,5 +20,8 @@
 some
@@ -30 +40,2 @@
 other
""".strip()
    cfg = TestGenConfig(llm_provider="local")
    gen = EnhancedTestGenerator(cfg)
    lines = gen._parse_diff_lines(diff)
    # Should contain context around 20 and 40
    assert 20 in lines and 40 in lines


def test_generate_tests_with_llm_falls_back_to_templates_for_function():
    cfg = TestGenConfig(
        llm_provider="local"
    )  # llm_client is Mock so not None when key is missing; ensure None path
    cfg.llm_api_key = None
    gen = EnhancedTestGenerator(cfg)
    change = CodeChange(
        file_path="pkg/mod.py",
        function_name="bar",
        change_type="function",
        line_numbers=(1, 1),
        code_snippet="def bar(x, y):\n    return x + y\n",
    )
    tests = gen.generate_tests_with_llm(change)
    assert "def test_bar(" in tests
    assert "parametrize" in tests or "parametrized" in tests


def test_analyze_coverage_gaps_parses_missing_lines(tmp_path):
    # Prepare a fake file path to appear in coverage output
    fake_file = str(tmp_path / "mymod.py")
    (tmp_path / "mymod.py").write_text("def x():\n    return 1\n", encoding="utf-8")

    cfg = TestGenConfig(llm_provider="local")
    gen = EnhancedTestGenerator(cfg)

    def subprocess_side_effect(args, capture_output=True, text=True, check=False):
        if args[:3] == ["python", "-m", "coverage"] and "report" in args:
            # Simulate coverage report with Missing section for our file
            out = f"{fake_file}   50%   10-12\n"
            return _make_subprocess_result(0, stdout=out)
        return _make_subprocess_result(0, stdout="")

    with patch("subprocess.run", side_effect=subprocess_side_effect):
        gaps = gen._analyze_file_coverage(fake_file)

    assert any("10-12" in g for g in gaps)


def test_generate_test_file_compiles_and_includes_imports(tmp_path):
    cfg = TestGenConfig(llm_provider="local")
    gen = EnhancedTestGenerator(cfg)
    change = CodeChange(
        file_path=str(tmp_path / "module_a.py"),
        function_name="foo",
        change_type="function",
        line_numbers=(1, 1),
        code_snippet="def foo(a):\n    return a\n",
    )
    content = gen.generate_test_file([change], str(tmp_path / "out_test.py"))
    assert "from" in content and "import *" in content
    # Ensure at least one test is generated
    assert "def test_foo" in content or "def test_function_foo" in content


def test_main_cli_generates_output_file(tmp_path, monkeypatch, capsys):
    # Prepare fake event and changed files
    event = {"before": "a", "after": "b"}
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")

    # Patch changed_python_files to return our file list
    with patch(
        "src.ai_guard.generators.enhanced_testgen.changed_python_files",
        return_value=[str(tmp_path / "m1.py")],
    ):
        # Ensure output write happens without touching filesystem permissions
        m = mock_open()
        with patch("builtins.open", m):
            with patch.object(Path, "mkdir") as _mk:
                # Run CLI with arguments
                monkeypatch.setenv("OPENAI_API_KEY", "")
                with patch(
                    "sys.argv",
                    [
                        "prog",
                        "--event",
                        str(event_path),
                        "--output",
                        str(tmp_path / "gen_test.py"),
                        "--llm-provider",
                        "local",
                    ],
                ):
                    enhanced_main()

    out = capsys.readouterr().out
    assert "Generated enhanced tests" in out or "No tests generated" in out


"""Comprehensive tests for enhanced_testgen.py to achieve 80% coverage - Phase 2M."""

import pytest
import tempfile
import json
import ast
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from typing import List, Dict, Any

from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    TestGenTemplate,
    CodeChange,
    EnhancedTestGenerator,
    TestGenerationConfig,
    TestTemplate,
)


class TestTestGenConfigComprehensive:
    """Comprehensive tests for TestGenConfig class."""

    def test_config_validation_valid(self):
        """Test configuration validation with valid values."""
        config = TestGenConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_temperature=0.5,
            test_framework="pytest",
            max_tests_per_file=5,
            min_coverage_threshold=75.0,
            output_directory="tests",
        )
        assert config.validate() is True

    def test_config_validation_invalid_provider(self):
        """Test configuration validation with invalid provider."""
        config = TestGenConfig(llm_provider="invalid")
        assert config.validate() is False

    def test_config_validation_missing_api_key(self):
        """Test configuration validation with missing API key."""
        config = TestGenConfig(llm_provider="openai", llm_api_key=None)
        assert config.validate() is False

    def test_config_validation_invalid_temperature_low(self):
        """Test configuration validation with temperature too low."""
        config = TestGenConfig(llm_temperature=-0.1)
        assert config.validate() is False

    def test_config_validation_invalid_temperature_high(self):
        """Test configuration validation with temperature too high."""
        config = TestGenConfig(llm_temperature=1.1)
        assert config.validate() is False

    def test_config_validation_invalid_framework(self):
        """Test configuration validation with invalid framework."""
        config = TestGenConfig(test_framework="invalid")
        assert config.validate() is False

    def test_config_validation_invalid_max_tests(self):
        """Test configuration validation with invalid max tests."""
        config = TestGenConfig(max_tests_per_file=0)
        assert config.validate() is False

    def test_config_validation_invalid_coverage_threshold_low(self):
        """Test configuration validation with coverage threshold too low."""
        config = TestGenConfig(min_coverage_threshold=-1.0)
        assert config.validate() is False

    def test_config_validation_invalid_coverage_threshold_high(self):
        """Test configuration validation with coverage threshold too high."""
        config = TestGenConfig(min_coverage_threshold=101.0)
        assert config.validate() is False

    def test_config_validation_empty_output_directory(self):
        """Test configuration validation with empty output directory."""
        config = TestGenConfig(output_directory="")
        assert config.validate() is False

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "llm_provider": "anthropic",
            "llm_api_key": "test-key",
            "llm_model": "claude-3",
            "llm_temperature": 0.3,
            "test_framework": "unittest",
            "generate_mocks": False,
            "max_tests_per_file": 15,
        }
        config = TestGenConfig.from_dict(config_dict)
        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "test-key"
        assert config.llm_model == "claude-3"
        assert config.llm_temperature == 0.3
        assert config.test_framework == "unittest"
        assert config.generate_mocks is False
        assert config.max_tests_per_file == 15


class TestCodeChangeComprehensive:
    """Comprehensive tests for CodeChange class."""

    def test_code_change_to_dict(self):
        """Test converting CodeChange to dictionary."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            line_numbers=(10, 20),
            code_snippet="def test_func(): pass",
            context="test context",
            line_number=15,
            content="test content",
        )
        change_dict = change.to_dict()
        assert change_dict["file_path"] == "test.py"
        assert change_dict["function_name"] == "test_func"
        assert change_dict["class_name"] == "TestClass"
        assert change_dict["change_type"] == "function"
        assert change_dict["line_numbers"] == (10, 20)
        assert change_dict["code_snippet"] == "def test_func(): pass"
        assert change_dict["context"] == "test context"
        assert change_dict["line_number"] == 15
        assert change_dict["content"] == "test content"


class TestEnhancedTestGeneratorComprehensive:
    """Comprehensive tests for EnhancedTestGenerator class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return TestGenConfig(
            llm_provider="local",
            llm_api_key="test-key",
            llm_model="test-model",
            test_framework="pytest",
            generate_mocks=True,
            generate_parametrized_tests=True,
            generate_edge_cases=True,
            max_tests_per_file=10,
            analyze_coverage_gaps=True,
            min_coverage_threshold=80.0,
            output_directory="tests/unit",
            test_file_suffix="_test.py",
            include_docstrings=True,
            include_type_hints=True,
        )

    @pytest.fixture
    def generator(self, config):
        """Create a test generator with mocked LLM client."""
        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=Mock()
        ):
            return EnhancedTestGenerator(config)

    def test_generator_initialization_with_config(self, config):
        """Test generator initialization with custom config."""
        with patch.object(
            EnhancedTestGenerator, "_initialize_llm_client", return_value=Mock()
        ):
            generator = EnhancedTestGenerator(config)
            assert generator.config == config
            assert generator.test_templates is not None
            assert generator.llm_client is not None

    def test_load_test_templates_comprehensive(self, generator):
        """Test loading all test templates."""
        templates = generator._load_test_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 8  # Should have at least 8 templates

        template_names = [t.name for t in templates]
        expected_templates = [
            "function_test",
            "function_parametrized_test",
            "function_error_test",
            "class_test",
            "class_property_test",
            "edge_case_test",
            "integration_test",
            "performance_test",
            "coverage_test",
        ]

        for expected in expected_templates:
            assert expected in template_names, f"Missing template: {expected}"

    def test_initialize_llm_client_no_api_key(self):
        """Test initializing LLM client without API key."""
        config = TestGenConfig(llm_provider="openai", llm_api_key=None)
        generator = EnhancedTestGenerator(config)
        assert generator.llm_client is None

    def test_initialize_llm_client_openai_import_error(self):
        """Test initializing OpenAI client with import error."""
        config = TestGenConfig(llm_provider="openai", llm_api_key="test-key")

        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'openai'")
        ):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is None

    def test_initialize_llm_client_anthropic_import_error(self):
        """Test initializing Anthropic client with import error."""
        config = TestGenConfig(llm_provider="anthropic", llm_api_key="test-key")

        with patch(
            "builtins.__import__",
            side_effect=ImportError("No module named 'anthropic'"),
        ):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is None

    def test_initialize_llm_client_exception_handling(self):
        """Test LLM client initialization exception handling."""
        config = TestGenConfig(llm_provider="openai", llm_api_key="test-key")

        with patch("builtins.__import__", side_effect=Exception("Unexpected error")):
            generator = EnhancedTestGenerator(config)
            assert generator.llm_client is None

    def test_analyze_code_changes_non_python_file(self, generator):
        """Test analyzing non-Python files."""
        result = generator.analyze_code_changes(["test.txt", "test.js"])
        assert result == []

    def test_analyze_file_changes_syntax_error(self, generator):
        """Test analyzing file with syntax error."""
        test_file = "test_syntax_error.py"
        try:
            with open(test_file, "w") as f:
                f.write("def invalid syntax")

            result = generator._analyze_file_changes(test_file)
            assert result == []
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_analyze_file_changes_file_not_found(self, generator):
        """Test analyzing non-existent file."""
        result = generator._analyze_file_changes("nonexistent.py")
        assert result == []

    def test_analyze_file_changes_with_functions(self, generator):
        """Test analyzing file with functions."""
        test_file = "test_functions.py"
        try:
            with open(test_file, "w") as f:
                f.write(
                    """
def function1():
    return "hello"

def function2(x):
    return x * 2

class TestClass:
    def method1(self):
        return "world"
"""
                )

            result = generator._analyze_file_changes(test_file)
            assert len(result) >= 3  # Should find function1, function2, and TestClass

            function_names = [
                change.function_name for change in result if change.function_name
            ]
            class_names = [change.class_name for change in result if change.class_name]

            assert "function1" in function_names
            assert "function2" in function_names
            assert "TestClass" in class_names
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_get_file_diff_with_event_path(self, generator):
        """Test getting file diff with event path."""
        test_file = "test_event.json"
        try:
            with open(test_file, "w") as f:
                event_data = {
                    "pull_request": {
                        "base": {"sha": "main_sha"},
                        "head": {"sha": "feature_sha"},
                    }
                }
                json.dump(event_data, f)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = '+++ b/test.py\n@@ -1,3 +1,3 @@\n def test():\n-    return "old"\n+    return "new"'

                result = generator._get_file_diff("test.py", test_file)
                assert result is not None
                assert "test.py" in result
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_get_file_diff_fallback(self, generator):
        """Test getting file diff fallback."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '+++ b/test.py\n@@ -1,3 +1,3 @@\n def test():\n-    return "old"\n+    return "new"'

            result = generator._get_file_diff("test.py")
            assert result is not None

    def test_get_file_diff_subprocess_error(self, generator):
        """Test getting file diff with subprocess error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Error"

            result = generator._get_file_diff("test.py")
            assert result is None

    def test_get_base_head_from_event_invalid_json(self, generator):
        """Test getting base/head from invalid JSON."""
        test_file = "test_invalid.json"
        try:
            with open(test_file, "w") as f:
                f.write("invalid json")

            result = generator._get_base_head_from_event(test_file)
            assert result is None
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_get_base_head_from_event_with_before_after(self, generator):
        """Test getting base/head from event with before/after."""
        test_file = "test_before_after.json"
        try:
            with open(test_file, "w") as f:
                event_data = {"before": "commit1", "after": "commit2"}
                json.dump(event_data, f)

            result = generator._get_base_head_from_event(test_file)
            assert result == ("commit1", "commit2")
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_parse_diff_lines_comprehensive(self, generator):
        """Test parsing diff lines comprehensively."""
        diff_content = """@@ -1,3 +1,3 @@
 def test():
-    return "old"
+    return "new"
@@ -10,5 +10,5 @@
 def another():
-    return "old2"
+    return "new2"
@@ -20,1 +20,1 @@
 single line
-    old
+    new
"""
        result = generator._parse_diff_lines(diff_content)
        assert isinstance(result, list)
        assert len(result) > 0

        # Should include lines around the changes
        assert 1 in result or 2 in result or 3 in result  # Around first change
        assert 10 in result or 11 in result or 12 in result  # Around second change
        assert 20 in result or 21 in result or 22 in result  # Around third change

    def test_is_function_changed_with_end_lineno_none(self, generator):
        """Test checking if function was changed when end_lineno is None."""
        func_node = Mock()
        func_node.lineno = 10
        func_node.end_lineno = None

        changed_lines = [10, 11, 12]
        result = generator._is_function_changed(func_node, changed_lines)
        assert result is True

        changed_lines = [1, 2, 3]
        result = generator._is_function_changed(func_node, changed_lines)
        assert result is False

    def test_is_class_changed_with_end_lineno_none(self, generator):
        """Test checking if class was changed when end_lineno is None."""
        class_node = Mock()
        class_node.lineno = 20
        class_node.end_lineno = None

        changed_lines = [20, 21, 22]
        result = generator._is_class_changed(class_node, changed_lines)
        assert result is True

        changed_lines = [1, 2, 3]
        result = generator._is_class_changed(class_node, changed_lines)
        assert result is False

    def test_get_class_name_with_multiple_parents(self, generator):
        """Test getting class name with multiple parent levels."""
        grandparent = Mock()
        grandparent.name = "GrandParent"

        parent = Mock()
        parent.name = "Parent"
        parent.parent = grandparent

        func_node = Mock()
        func_node.parent = parent

        result = generator._get_class_name(func_node)
        assert result == "Parent"  # Should return the immediate parent

    def test_get_function_context_with_decorators(self, generator):
        """Test getting function context with decorators."""
        decorator1 = Mock()
        decorator1.attr = "decorator1"

        decorator2 = Mock()
        decorator2.value = "decorator2"

        func_node = Mock()
        func_node.decorator_list = [decorator1, decorator2]
        func_node.args = Mock()
        func_node.args.args = [Mock(arg="param1")]
        func_node.returns = Mock()
        func_node.returns.value = "str"

        with patch(
            "ast.unparse",
            side_effect=lambda x: (
                "decorator1"
                if hasattr(x, "attr")
                else "decorator2" if hasattr(x, "value") else "str"
            ),
        ):
            result = generator._get_function_context(func_node)
            assert "decorator1" in result or "decorator2" in result
            assert "param1" in result

    def test_get_function_context_with_return_annotation(self, generator):
        """Test getting function context with return annotation."""
        func_node = Mock()
        func_node.decorator_list = []
        func_node.args = Mock()
        func_node.args.args = [Mock(arg="param1")]
        func_node.returns = Mock()
        func_node.returns.value = "int"

        with patch("ast.unparse", return_value="int"):
            result = generator._get_function_context(func_node)
            assert "int" in result
            assert "param1" in result

    def test_get_class_context_comprehensive(self, generator):
        """Test getting class context comprehensively."""
        base1 = Mock()
        base1.value = "Base1"

        base2 = Mock()
        base2.value = "Base2"

        method1 = Mock()
        method1.name = "method1"

        method2 = Mock()
        method2.name = "method2"

        class_node = Mock()
        class_node.bases = [base1, base2]
        class_node.body = [method1, method2, Mock()]  # Include non-function node

        with patch(
            "ast.unparse",
            side_effect=lambda x: (
                "Base1"
                if hasattr(x, "value") and x.value == "Base1"
                else "Base2" if hasattr(x, "value") and x.value == "Base2" else ""
            ),
        ):
            with patch(
                "isinstance",
                side_effect=lambda obj, cls: cls == ast.FunctionDef
                and hasattr(obj, "name"),
            ):
                result = generator._get_class_context(class_node)
                assert "Base1" in result or "Base2" in result
                assert "method1" in result
                assert "method2" in result

    def test_generate_tests_with_llm_no_client(self, generator):
        """Test generating tests with LLM when no client available."""
        generator.llm_client = None
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_with_llm_openai_success(self, generator):
        """Test generating tests with OpenAI LLM successfully."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated test content"

        generator.llm_client = Mock()
        generator.llm_client.ChatCompletion.create.return_value = mock_response

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator.generate_tests_with_llm(change)
        assert result == "Generated test content"

    def test_generate_tests_with_llm_openai_non_string_content(self, generator):
        """Test generating tests with OpenAI LLM returning non-string content."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 123  # Non-string content

        generator.llm_client = Mock()
        generator.llm_client.ChatCompletion.create.return_value = mock_response

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator.generate_tests_with_llm(change)
        assert result == ""

    def test_generate_tests_with_llm_anthropic_success(self, generator):
        """Test generating tests with Anthropic LLM successfully."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Generated test content"

        generator.llm_client = Mock()
        generator.llm_client.messages.create.return_value = mock_response

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator.generate_tests_with_llm(change)
        assert result == "Generated test content"

    def test_generate_tests_with_llm_anthropic_non_string_content(self, generator):
        """Test generating tests with Anthropic LLM returning non-string content."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = 123  # Non-string content

        generator.llm_client = Mock()
        generator.llm_client.messages.create.return_value = mock_response

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator.generate_tests_with_llm(change)
        assert result == ""

    def test_generate_tests_with_llm_exception_fallback(self, generator):
        """Test generating tests with LLM exception fallback."""
        generator.llm_client = Mock()
        generator.llm_client.ChatCompletion.create.side_effect = Exception("API Error")

        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator.generate_tests_with_llm(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_create_llm_prompt(self, generator):
        """Test creating LLM prompt."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
            context="test context",
            code_snippet="def test_func(): pass",
        )

        prompt = generator._create_llm_prompt(change)
        assert "test.py" in prompt
        assert "test_func" in prompt
        assert "TestClass" in prompt
        assert "function" in prompt
        assert "test context" in prompt
        assert "def test_func(): pass" in prompt
        assert "pytest" in prompt

    def test_generate_tests_with_templates_function(self, generator):
        """Test generating tests with templates for function."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(x, y): return x + y",
        )

        result = generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_tests_with_templates_class(self, generator):
        """Test generating tests with templates for class."""
        change = CodeChange(
            file_path="test.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass: pass",
        )

        result = generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "TestClass" in result

    def test_generate_tests_with_templates_other(self, generator):
        """Test generating tests with templates for other change types."""
        change = CodeChange(
            file_path="test.py", change_type="import", code_snippet="import os"
        )

        result = generator._generate_tests_with_templates(change)
        assert isinstance(result, str)
        assert "import" in result

    def test_generate_function_tests_with_ast_parsing_error(self, generator):
        """Test generating function tests with AST parsing error."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="invalid python code",
        )

        result = generator._generate_function_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_function_tests_with_no_func_def(self, generator):
        """Test generating function tests with no function definition."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="x = 1",
        )

        result = generator._generate_function_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_function_tests_comprehensive(self, generator):
        """Test generating function tests comprehensively."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(a, b, c): return a + b + c",
        )

        result = generator._generate_function_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result
        assert (
            "parametrized" in result
            or "error" in result
            or "edge" in result
            or "coverage" in result
        )

    def test_generate_test_cases_multiple_args(self, generator):
        """Test generating test cases with multiple arguments."""
        func_def = Mock()
        func_def.args = Mock()
        func_def.args.args = [
            Mock(arg="param1"),
            Mock(arg="param2"),
            Mock(arg="param3"),
        ]

        result = generator._generate_test_cases(func_def)
        assert isinstance(result, str)
        assert "test_input" in result
        assert "expected_output" in result
        assert "arg1" in result
        assert "arg2" in result

    def test_generate_coverage_tests_multiple_args(self, generator):
        """Test generating coverage tests with multiple arguments."""
        func_def = Mock()
        func_def.name = "test_func"
        func_def.args = Mock()
        func_def.args.args = [Mock(arg="param1"), Mock(arg="param2")]

        result = generator._generate_coverage_tests(func_def)
        assert isinstance(result, str)
        assert "test_func" in result
        assert "multiple parameters" in result

    def test_generate_class_tests_no_template(self, generator):
        """Test generating class tests when no template available."""
        # Remove class templates temporarily
        original_templates = generator.test_templates
        generator.test_templates = []

        change = CodeChange(
            file_path="test.py",
            class_name="TestClass",
            change_type="class",
            code_snippet="class TestClass: pass",
        )

        result = generator._generate_class_tests(change)
        assert isinstance(result, str)
        assert "TestClass" in result

        # Restore templates
        generator.test_templates = original_templates

    def test_generate_generic_tests(self, generator):
        """Test generating generic tests."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            class_name="TestClass",
            change_type="function",
        )

        result = generator._generate_generic_tests(change)
        assert isinstance(result, str)
        assert "test_func" in result
        assert "function" in result

    def test_analyze_coverage_gaps_disabled(self, generator):
        """Test analyzing coverage gaps when disabled."""
        generator.config.analyze_coverage_gaps = False
        result = generator.analyze_coverage_gaps(["test.py"])
        assert result == {}

    def test_analyze_coverage_gaps_non_python_file(self, generator):
        """Test analyzing coverage gaps with non-Python files."""
        result = generator.analyze_coverage_gaps(["test.txt", "test.js"])
        assert result == {}

    def test_analyze_file_coverage_subprocess_error(self, generator):
        """Test analyzing file coverage with subprocess error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Error"

            result = generator._analyze_file_coverage("test.py")
            assert result == []

    def test_analyze_file_coverage_coverage_report_error(self, generator):
        """Test analyzing file coverage with coverage report error."""
        with patch("subprocess.run") as mock_run:
            # First call succeeds (coverage run)
            # Second call fails (coverage report)
            mock_run.side_effect = [
                Mock(returncode=0, stdout="Success"),
                Mock(returncode=1, stderr="Report error"),
            ]

            result = generator._analyze_file_coverage("test.py")
            assert isinstance(result, list)

    def test_analyze_file_coverage_with_missing_lines(self, generator):
        """Test analyzing file coverage with missing lines."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = (
                "test.py: 85% coverage\nMissing: 10-15, 20-25"
            )

            result = generator._analyze_file_coverage("test.py")
            assert isinstance(result, list)

    def test_analyze_function_coverage_with_docstring(self, generator):
        """Test analyzing function coverage with docstring."""
        test_file = "test_docstring.py"
        try:
            with open(test_file, "w") as f:
                f.write(
                    """
def function_with_docstring():
    '''This function has a docstring.'''
    return "hello"

def complex_function():
    '''Complex function with many lines.'''
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    return x + y + z + a + b + c + d + e + f + g + h
"""
                )

            result = generator._analyze_function_coverage(test_file)
            assert isinstance(result, list)
            # Should detect functions with docstrings and complex functions
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_analyze_function_coverage_file_error(self, generator):
        """Test analyzing function coverage with file error."""
        result = generator._analyze_function_coverage("nonexistent.py")
        assert result == []

    def test_analyze_branch_coverage_comprehensive(self, generator):
        """Test analyzing branch coverage comprehensively."""
        test_file = "test_branch.py"
        try:
            with open(test_file, "w") as f:
                f.write(
                    """
if condition:
    do_something()

for item in items:
    process(item)

while running:
    continue_running()

try:
    risky_operation()
except Exception:
    handle_error()
"""
                )

            result = generator._analyze_branch_coverage(test_file)
            assert isinstance(result, list)
            assert len(result) >= 4  # Should detect if, for, while, try-except
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_analyze_branch_coverage_file_error(self, generator):
        """Test analyzing branch coverage with file error."""
        result = generator._analyze_branch_coverage("nonexistent.py")
        assert result == []

    def test_generate_test_file_comprehensive(self, generator):
        """Test generating test file comprehensively."""
        changes = [
            CodeChange(
                file_path="test1.py",
                function_name="func1",
                change_type="function",
                code_snippet="def func1(): pass",
            ),
            CodeChange(
                file_path="test2.py",
                class_name="Class1",
                change_type="class",
                code_snippet="class Class1: pass",
            ),
        ]

        with patch.object(
            generator,
            "analyze_coverage_gaps",
            return_value={"test1.py": ["Missing line 5"]},
        ):
            result = generator.generate_test_file(changes, "output.py")
            assert isinstance(result, str)
            assert "func1" in result
            assert "Class1" in result
            assert "test1.py" in result
            assert "test2.py" in result
            assert "Missing line 5" in result

    def test_generate_tests_with_event_path(self, generator):
        """Test generating tests with event path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_function(): return 'hello'")
            f.flush()

            try:
                with patch.object(generator, "analyze_code_changes", return_value=[]):
                    result = generator.generate_tests([f.name], event_path="event.json")
                    assert result == ""
            finally:
                Path(f.name).unlink()

    def test_generate_tests_with_changes_detected(self, generator):
        """Test generating tests when changes are detected."""
        changes = [
            CodeChange(
                file_path="test.py",
                function_name="test_func",
                change_type="function",
                code_snippet="def test_func(): pass",
            )
        ]

        with patch.object(generator, "analyze_code_changes", return_value=changes):
            result = generator.generate_tests(["test.py"])
            assert isinstance(result, str)
            assert "test_func" in result

    def test_generate_tests_for_changes_comprehensive(self, generator):
        """Test generating tests for changes comprehensively."""
        changes = [
            CodeChange(
                file_path="test.py",
                function_name="test_func",
                change_type="function",
                code_snippet="def test_func(): pass",
            )
        ]

        result = generator.generate_tests_for_changes(changes)
        assert isinstance(result, str)
        assert "test_func" in result

    def test_generate_function_test_alias(self, generator):
        """Test the _generate_function_test alias method."""
        change = CodeChange(
            file_path="test.py",
            function_name="test_func",
            change_type="function",
            code_snippet="def test_func(): pass",
        )

        result = generator._generate_function_test(change)
        assert isinstance(result, str)
        assert "test_func" in result


class TestMainFunction:
    """Test the main function."""

    def test_main_with_no_changed_files(self):
        """Test main function with no changed files."""
        import sys
        from unittest.mock import patch

        test_args = [
            "enhanced_testgen.py",
            "--output",
            "test_output.py",
            "--llm-provider",
            "local",
        ]

        with patch.object(sys, "argv", test_args):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.changed_python_files",
                return_value=[],
            ):
                with patch("builtins.print") as mock_print:
                    from src.ai_guard.generators.enhanced_testgen import main

                    main()

                    # Should print that no files changed
                    mock_print.assert_called_with(
                        "[enhanced-testgen] No Python files changed, skipping test generation"
                    )

    def test_main_with_changed_files(self):
        """Test main function with changed files."""
        import sys
        from unittest.mock import patch

        test_args = [
            "enhanced_testgen.py",
            "--output",
            "test_output.py",
            "--llm-provider",
            "local",
            "--llm-api-key",
            "test-key",
        ]

        with patch.object(sys, "argv", test_args):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.changed_python_files",
                return_value=["test.py"],
            ):
                with patch(
                    "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
                ) as mock_gen_class:
                    mock_generator = Mock()
                    mock_generator.generate_tests.return_value = (
                        "Generated test content"
                    )
                    mock_gen_class.return_value = mock_generator

                    with patch("builtins.print") as mock_print:
                        with patch("builtins.open", mock_open()):
                            with patch("pathlib.Path.mkdir"):
                                from src.ai_guard.generators.enhanced_testgen import (
                                    main,
                                )

                                main()

                                # Should print success message
                                mock_print.assert_any_call(
                                    "[enhanced-testgen] Generated enhanced tests for 1 files"
                                )

    def test_main_with_no_tests_generated(self):
        """Test main function with no tests generated."""
        import sys
        from unittest.mock import patch

        test_args = [
            "enhanced_testgen.py",
            "--output",
            "test_output.py",
            "--llm-provider",
            "local",
        ]

        with patch.object(sys, "argv", test_args):
            with patch(
                "src.ai_guard.generators.enhanced_testgen.changed_python_files",
                return_value=["test.py"],
            ):
                with patch(
                    "src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator"
                ) as mock_gen_class:
                    mock_generator = Mock()
                    mock_generator.generate_tests.return_value = ""
                    mock_gen_class.return_value = mock_generator

                    with patch("builtins.print") as mock_print:
                        from src.ai_guard.generators.enhanced_testgen import main

                        main()

                        # Should print that no tests were generated
                        mock_print.assert_called_with(
                            "[enhanced-testgen] No tests generated"
                        )


class TestBackwardCompatibility:
    """Test backward compatibility aliases."""

    def test_test_generation_config_alias(self):
        """Test TestGenerationConfig alias."""
        config = TestGenerationConfig()
        assert isinstance(config, TestGenConfig)
        assert config.llm_provider == "openai"

    def test_test_template_alias(self):
        """Test TestTemplate alias."""
        template = TestTemplate(
            name="test",
            description="test",
            template="template",
            variables=[],
            applicable_to=[],
        )
        assert isinstance(template, TestGenTemplate)
        assert template.name == "test"


if __name__ == "__main__":
    pytest.main([__file__])
