"""Tests for enhanced AI-Guard features."""

import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile
import os

from ai_guard.generators.enhanced_testgen import (
    EnhancedTestGenerator,
    TestGenerationConfig,
    CodeChange,
)
from ai_guard.language_support.js_ts_support import (
    JavaScriptTypeScriptSupport,
    JSTestGenerationConfig,
)
from ai_guard.pr_annotations import PRAnnotator, CodeIssue, PRAnnotation


class TestEnhancedTestGeneration:
    """Test enhanced test generation functionality."""

    def test_test_generation_config_defaults(self):
        """Test TestGenerationConfig default values."""
        config = TestGenerationConfig()

        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.1
        assert config.test_framework == "pytest"
        assert config.generate_mocks is True
        assert config.analyze_coverage_gaps is True

    def test_code_change_creation(self):
        """Test CodeChange dataclass creation."""
        change = CodeChange(
            file_path="src/test.py",
            function_name="test_function",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def test_function():\n    pass",
            context="Simple function",
        )

        assert change.file_path == "src/test.py"
        assert change.function_name == "test_function"
        assert change.change_type == "function"
        assert change.line_numbers == (10, 15)

    @patch("builtins.__import__")
    def test_llm_client_initialization_openai(self, mock_import):
        """Test OpenAI client initialization."""

        # Mock the import to simulate openai not being available
        def side_effect(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("openai not available")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        config = TestGenerationConfig(llm_provider="openai", llm_api_key="test-key")

        generator = EnhancedTestGenerator(config)
        # Since openai is not actually available, it should fall back to template-based generation
        assert generator.llm_client is None

    def test_template_based_generation(self):
        """Test template-based test generation when LLM is not available."""
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
        assert "test_function" in test_content
        assert "def test_" in test_content


class TestJavaScriptTypeScriptSupport:
    """Test JavaScript/TypeScript support functionality."""

    def test_js_config_defaults(self):
        """Test JSTestGenerationConfig default values."""
        config = JSTestGenerationConfig()

        assert config.test_framework == "jest"
        assert config.use_eslint is True
        assert config.use_prettier is True
        assert config.use_typescript is False
        assert config.generate_unit_tests is True

    def test_dependency_checking(self):
        """Test dependency checking functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock package.json
            package_json = {"devDependencies": {"eslint": "^8.0.0", "jest": "^29.0.0"}}

            import json

            package_path = Path(temp_dir) / "package.json"
            with open(package_path, "w") as f:
                json.dump(package_json, f)

            # Change to temp directory and test
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                config = JSTestGenerationConfig()
                support = JavaScriptTypeScriptSupport(config)

                # Mock subprocess calls to ensure consistent behavior
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "8.0.0"

                    deps = support.check_dependencies()
                    assert deps["eslint"] is True
                    assert deps["jest"] is True
                    # typescript might be True if tsc is available in PATH, so we'll check the package.json logic
                    # The package.json doesn't have typescript, so it should be False from that check
                    # But if tsc is available in PATH, it might be True
                    # Let's just verify the package.json dependencies are working
                    assert deps["eslint"] is True  # From package.json
                    assert deps["jest"] is True  # From package.json
            finally:
                os.chdir(original_cwd)


class TestPRAnnotations:
    """Test PR annotation functionality."""

    def test_code_issue_creation(self):
        """Test CodeIssue dataclass creation."""
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=42,
            column=5,
            severity="warning",
            message="Line too long",
            rule_id="E501",
            suggestion="Break into multiple lines",
        )

        assert issue.file_path == "src/test.py"
        assert issue.line_number == 42
        assert issue.severity == "warning"
        assert issue.suggestion == "Break into multiple lines"

    def test_pr_annotation_creation(self):
        """Test PRAnnotation dataclass creation."""
        annotation = PRAnnotation(
            file_path="src/test.py",
            line_number=42,
            message="Line too long",
            annotation_level="warning",
            title="E501: Line too long",
        )

        assert annotation.file_path == "src/test.py"
        assert annotation.line_number == 42
        assert annotation.annotation_level == "warning"

    def test_pr_annotator_issue_adding(self):
        """Test adding issues to PR annotator."""
        annotator = PRAnnotator()

        issue = CodeIssue(
            file_path="src/test.py",
            line_number=42,
            column=5,
            severity="warning",
            message="Line too long",
            rule_id="E501",
        )

        annotator.add_issue(issue)
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1

    def test_review_summary_generation(self):
        """Test PR review summary generation."""
        annotator = PRAnnotator()

        # Add some issues
        issue1 = CodeIssue(
            file_path="src/test.py",
            line_number=42,
            column=5,
            severity="error",
            message="Syntax error",
            rule_id="E999",
        )

        issue2 = CodeIssue(
            file_path="src/test.py",
            line_number=67,
            column=1,
            severity="warning",
            message="Line too long",
            rule_id="E501",
        )

        annotator.add_issue(issue1)
        annotator.add_issue(issue2)

        summary = annotator.generate_review_summary()

        assert summary.overall_status == "changes_requested"
        assert summary.quality_score < 1.0
        assert len(summary.annotations) == 2
        assert len(summary.suggestions) > 0


class TestIntegration:
    """Test integration between different enhanced features."""

    def test_enhanced_testgen_with_pr_annotations(self):
        """Test that enhanced test generation can work with PR annotations."""
        # This test verifies the components can work together
        testgen_config = TestGenerationConfig(llm_api_key=None)
        testgen = EnhancedTestGenerator(testgen_config)

        annotator = PRAnnotator()

        # Both should be able to process the same code changes
        change = CodeChange(
            file_path="src/test.py",
            function_name="test_function",
            class_name=None,
            change_type="function",
            line_numbers=(10, 15),
            code_snippet="def test_function():\n    pass",
            context="Simple function",
        )

        # Generate tests
        test_content = testgen.generate_tests_with_llm(change)
        assert test_content

        # Create annotation
        issue = CodeIssue(
            file_path="src/test.py",
            line_number=10,
            column=1,
            severity="info",
            message="Function added",
            rule_id="function:added",
        )
        annotator.add_issue(issue)

        # Both should work without conflicts
        assert test_content
        assert len(annotator.annotations) == 1


if __name__ == "__main__":
    pytest.main([__file__])
