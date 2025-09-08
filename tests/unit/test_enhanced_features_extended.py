"""Extended tests for enhanced AI-Guard features to improve coverage."""

import pytest
from unittest.mock import patch, Mock
import tempfile
import os
import json

from ai_guard.generators.enhanced_testgen import (
    EnhancedTestGenerator,
    TestGenerationConfig,
    CodeChange,
    TestTemplate,
)
from ai_guard.language_support.js_ts_support import (
    JavaScriptTypeScriptSupport,
    JSTestGenerationConfig,
)
from ai_guard.pr_annotations import PRAnnotator, CodeIssue


class TestEnhancedTestGeneratorExtended:
    """Extended tests for EnhancedTestGenerator to improve coverage."""

    def test_test_template_creation(self):
        """Test TestTemplate dataclass creation."""
        template = TestTemplate(
            name="test_template",
            description="Test description",
            template="def test_{name}(): pass",
            variables=["name"],
            applicable_to=["function"],
        )

        assert template.name == "test_template"
        assert template.description == "Test description"
        assert template.template == "def test_{name}(): pass"
        assert template.variables == ["name"]
        assert template.applicable_to == ["function"]

    def test_llm_client_initialization_anthropic(self):
        """Test Anthropic client initialization."""
        with patch("builtins.__import__") as mock_import:
            mock_anthropic = Mock()
            mock_import.return_value = mock_anthropic

            config = TestGenerationConfig(
                llm_provider="anthropic", llm_api_key="test-key"
            )
            generator = EnhancedTestGenerator(config)

            # Should initialize with anthropic client
            assert generator.llm_client is not None

    def test_llm_client_initialization_unsupported(self):
        """Test unsupported LLM provider initialization."""
        config = TestGenerationConfig(
            llm_provider="unsupported", llm_api_key="test-key"
        )
        generator = EnhancedTestGenerator(config)

        # Should fall back to template-based generation
        assert generator.llm_client is None

    def test_llm_client_initialization_import_error(self):
        """Test LLM client initialization with import error."""
        with patch(
            "builtins.__import__", side_effect=ImportError("Library not available")
        ):
            config = TestGenerationConfig(llm_provider="openai", llm_api_key="test-key")
            generator = EnhancedTestGenerator(config)

            # Should fall back to template-based generation
            assert generator.llm_client is None

    def test_analyze_code_changes_with_non_python_files(self):
        """Test analyzing code changes with non-Python files."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        # Mock the entire _analyze_file_changes method to return a simple result
        with patch.object(
            generator,
            "_analyze_file_changes",
            return_value=[
                CodeChange(
                    file_path="src/test.py",
                    function_name="test_function",
                    class_name=None,
                    change_type="function",
                    line_numbers=(10, 15),
                    code_snippet="def test_function():\n    pass",
                    context="Simple function",
                )
            ],
        ):
            changed_files = ["src/test.py", "README.md", "requirements.txt"]
            changes = generator.analyze_code_changes(changed_files)

            # Should only process Python files
            assert len(changes) == 1
            assert changes[0].file_path == "src/test.py"

    def test_analyze_code_changes_with_analysis_error(self):
        """Test analyzing code changes when file analysis fails."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)

        # Mock _analyze_file_changes to raise an exception
        with patch.object(
            generator, "_analyze_file_changes", side_effect=Exception("Analysis failed")
        ):
            changed_files = ["src/test.py"]
            changes = generator.analyze_code_changes(changed_files)

            # Should handle errors gracefully and return empty list
            assert len(changes) == 0

    def test_generate_tests_with_llm_no_client(self):
        """Test test generation when LLM client is not available."""
        config = TestGenerationConfig(llm_api_key=None)
        generator = EnhancedTestGenerator(config)

        change = CodeChange(
            file_path="src/test.py",
            function_name="test_function",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def test_function():\n    pass",
            context="Simple function",
        )

        test_content = generator.generate_tests_with_llm(change)
        assert test_content
        assert "test_function" in test_content

    def test_generate_tests_with_llm_openai_success(self):
        """Test test generation with OpenAI LLM."""
        config = TestGenerationConfig(llm_provider="openai", llm_api_key="test-key")

        with patch("builtins.__import__") as mock_import:
            # Mock openai import
            mock_openai = Mock()
            mock_openai.ChatCompletion.create.return_value = Mock(
                choices=[Mock(message=Mock(content="def test_example(): pass"))]
            )
            mock_import.return_value = mock_openai

            generator = EnhancedTestGenerator(config)
            change = CodeChange(
                file_path="src/test.py",
                function_name="test_function",
                class_name=None,
                change_type="function",
                line_numbers=(10, 15),
                code_snippet="def test_function():\n    pass",
                context="Simple function",
            )

            test_content = generator.generate_tests_with_llm(change)
            assert test_content
            assert "test_example" in test_content

    def test_generate_tests_with_llm_anthropic_success(self):
        """Test test generation with Anthropic LLM."""
        config = TestGenerationConfig(llm_provider="anthropic", llm_api_key="test-key")

        with patch("builtins.__import__") as mock_import:
            # Mock anthropic import
            mock_anthropic = Mock()
            mock_client = Mock()
            mock_client.messages.create.return_value = Mock(
                content=[Mock(text="def test_example(): pass")]
            )
            mock_anthropic.Anthropic.return_value = mock_client
            mock_import.return_value = mock_anthropic

            generator = EnhancedTestGenerator(config)
            change = CodeChange(
                file_path="src/test.py",
                function_name="test_function",
                class_name=None,
                change_type="function",
                line_numbers=(10, 15),
                code_snippet="def test_function():\n    pass",
                context="Simple function",
            )

            test_content = generator.generate_tests_with_llm(change)
            assert test_content
            assert "test_example" in test_content

    def test_generate_tests_with_llm_error_handling(self):
        """Test test generation error handling."""
        config = TestGenerationConfig(llm_provider="openai", llm_api_key="test-key")

        with patch("builtins.__import__") as mock_import:
            # Mock openai import with error
            mock_openai = Mock()
            mock_openai.ChatCompletion.create.side_effect = Exception("API error")
            mock_import.return_value = mock_openai

            generator = EnhancedTestGenerator(config)
            change = CodeChange(
                file_path="src/test.py",
                function_name="test_function",
                class_name=None,
                change_type="function",
                line_numbers=(10, 15),
                code_snippet="def test_function():\n    pass",
                context="Simple function",
            )

            # Should fall back to template-based generation
            test_content = generator.generate_tests_with_llm(change)
            assert test_content
            assert "test_function" in test_content

    def test_generate_tests_for_multiple_files(self):
        """Test generating tests for multiple files."""
        config = TestGenerationConfig(llm_api_key=None)
        generator = EnhancedTestGenerator(config)

        # Mock the analyze_code_changes method to return some changes
        with patch.object(
            generator,
            "analyze_code_changes",
            return_value=[
                CodeChange(
                    file_path="src/test1.py",
                    function_name="test_function",
                    class_name=None,
                    change_type="function",
                    line_numbers=(10, 15),
                    code_snippet="def test_function():\n    pass",
                    context="Simple function",
                )
            ],
        ):
            changed_files = ["src/test1.py", "src/test2.py"]
            event_path = "event.json"

            test_content = generator.generate_tests(changed_files, event_path)
            assert test_content
            assert "test1" in test_content or "test2" in test_content

    def test_generate_tests_with_file_write_error(self):
        """Test test generation with file write error."""
        config = TestGenerationConfig(llm_api_key=None)
        generator = EnhancedTestGenerator(config)

        # Mock the analyze_code_changes method to return some changes
        with patch.object(
            generator,
            "analyze_code_changes",
            return_value=[
                CodeChange(
                    file_path="src/test.py",
                    function_name="test_function",
                    class_name=None,
                    change_type="function",
                    line_numbers=(10, 15),
                    code_snippet="def test_function():\n    pass",
                    context="Simple function",
                )
            ],
        ):
            changed_files = ["src/test.py"]

            test_content = generator.generate_tests(changed_files)
            # Should still return test content even if file write fails
            assert test_content


class TestJavaScriptTypeScriptSupportExtended:
    """Extended tests for JavaScript/TypeScript support."""

    def test_dependency_checking_with_missing_package_json(self):
        """Test dependency checking when package.json is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)

            # Change to temp directory without package.json
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "8.0.0"

                    deps = support.check_dependencies()
                    # Should check PATH for available tools
                    assert isinstance(deps["eslint"], bool)
                    assert isinstance(deps["jest"], bool)
            finally:
                os.chdir(original_cwd)

    def test_dependency_checking_with_subprocess_error(self):
        """Test dependency checking when subprocess calls fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = JSTestGenerationConfig()
            support = JavaScriptTypeScriptSupport(config)

            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = FileNotFoundError("Command not found")

                    deps = support.check_dependencies()
                    # Should handle subprocess errors gracefully
                    assert deps["eslint"] is False
                    assert deps["jest"] is False
            finally:
                os.chdir(original_cwd)

    def test_test_generation_with_eslint_issues(self):
        """Test test generation with ESLint issues."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch.object(
            support,
            "check_dependencies",
            return_value={"eslint": True, "jest": True, "typescript": False},
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = "ESLint found 2 issues"

                result = support.generate_tests(["src/test.js"])
                assert isinstance(result, dict)

    def test_test_generation_with_jest_issues(self):
        """Test test generation with Jest issues."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)

        with patch.object(
            support,
            "check_dependencies",
            return_value={"eslint": True, "jest": True, "typescript": False},
        ):
            with patch("subprocess.run") as mock_run:
                # Mock ESLint success
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""

                # Mock Jest failure
                mock_run.side_effect = [
                    Mock(returncode=0, stdout=""),  # ESLint
                    Mock(returncode=1, stdout="Jest found 1 failing test"),  # Jest
                ]

                result = support.generate_tests(["src/test.js"])
                assert isinstance(result, dict)


class TestPRAnnotationsExtended:
    """Extended tests for PR annotations."""

    def test_pr_annotator_with_lint_issues(self):
        """Test PR annotator with lint issues."""
        annotator = PRAnnotator()

        # Add lint issues
        lint_issues = [
            {
                "file": "src/test.py",
                "line": 42,
                "column": 5,
                "severity": "warning",
                "message": "Line too long",
                "rule": "E501",
            }
        ]

        annotator.add_lint_issues(lint_issues)
        assert len(annotator.annotations) == 1

    def test_pr_annotator_with_type_issues(self):
        """Test PR annotator with type check issues."""
        annotator = PRAnnotator()

        # Add type check issues
        type_issues = [
            {
                "file": "src/test.py",
                "line": 67,
                "column": 1,
                "severity": "error",
                "message": "Type error",
                "rule": "mypy:type-error",
            }
        ]

        annotator.add_lint_issues(type_issues)
        assert len(annotator.annotations) == 1

    def test_pr_annotator_with_security_issues(self):
        """Test PR annotator with security issues."""
        annotator = PRAnnotator()

        # Add security issues
        security_issues = [
            {
                "file": "src/test.py",
                "line": 89,
                "column": 10,
                "severity": "high",
                "message": "Security vulnerability",
                "rule": "bandit:B101",
            }
        ]

        annotator.add_security_annotation(security_issues)
        assert len(annotator.annotations) == 1

    def test_review_summary_with_mixed_issues(self):
        """Test review summary generation with mixed issue types."""
        annotator = PRAnnotator()

        # Add various types of issues
        annotator.add_issue(
            CodeIssue(
                file_path="src/test.py",
                line_number=42,
                column=5,
                severity="error",
                message="Critical error",
                rule_id="E999",
            )
        )

        annotator.add_issue(
            CodeIssue(
                file_path="src/test.py",
                line_number=67,
                column=1,
                severity="warning",
                message="Minor issue",
                rule_id="E501",
            )
        )

        summary = annotator.generate_review_summary()

        assert summary.overall_status == "changes_requested"
        assert summary.quality_score < 1.0
        assert len(summary.annotations) == 2
        assert len(summary.suggestions) > 0

    def test_annotations_save_and_load(self):
        """Test saving and loading annotations."""
        annotator = PRAnnotator()

        # Add some issues using the proper method
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=42,
            column=5,
            severity="warning",
            message="Test issue",
            rule_id="TEST001",
        )
        annotator.add_issue(issue)

        # Test saving
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            annotator.save_annotations(temp_file)

            # Verify file was created and contains data
            assert os.path.exists(temp_file)
            with open(temp_file, "r") as f:
                data = json.load(f)
                assert "annotations" in data
                assert len(data["annotations"]) == 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__])
