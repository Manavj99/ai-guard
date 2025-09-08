"""Comprehensive tests for analyzer.py to achieve high coverage."""

import pytest
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from ai_guard.analyzer import (
    cov_percent,
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_output,
    main as analyzer_main,
)


class TestCoverageParsing:
    """Test coverage percentage parsing."""

    def test_cov_percent_with_valid_xml(self):
        """Test parsing valid coverage XML."""
        xml_content = """<?xml version="1.0" ?>
<coverage version="7.10.5" line-rate="0.85">
    <packages>
        <package name="test" line-rate="0.85">
        </package>
    </packages>
</coverage>"""

        with patch("builtins.open", mock_open(read_data=xml_content)):
            with patch("os.path.exists", return_value=True):
                with patch("defusedxml.ElementTree.parse") as mock_parse:
                    mock_tree = Mock()
                    mock_root = Mock()
                    mock_root.get.return_value = "0.85"
                    mock_tree.getroot.return_value = mock_root
                    mock_parse.return_value = mock_tree

                    result = cov_percent()
                    assert result == 85

    def test_cov_percent_no_file(self):
        """Test when no coverage file exists."""
        with patch("os.path.exists", return_value=False):
            result = cov_percent()
            assert result == 0

    def test_cov_percent_parse_error(self):
        """Test handling parse errors."""
        with patch("os.path.exists", return_value=True):
            with patch(
                "defusedxml.ElementTree.parse", side_effect=Exception("Parse error")
            ):
                result = cov_percent()
                assert result == 0


class TestFlake8Parsing:
    """Test flake8 output parsing."""

    def test_parse_flake8_output_valid(self):
        """Test parsing valid flake8 output."""
        output = "test.py:10:5: E501 line too long (80 > 79 characters)"
        results = _parse_flake8_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "flake8:E501"
        assert result.level == "warning"
        assert "line too long" in result.message
        assert len(result.locations) == 1
        assert (
            result.locations[0]["physicalLocation"]["artifactLocation"]["uri"]
            == "test.py"
        )
        assert result.locations[0]["physicalLocation"]["region"]["startLine"] == 10

    def test_parse_flake8_output_multiple(self):
        """Test parsing multiple flake8 issues."""
        output = """test.py:10:5: E501 line too long
test.py:15:1: F401 'os' imported but unused
test.py:20:10: W292 no newline at end of file"""

        results = _parse_flake8_output(output)
        assert len(results) == 3

    def test_parse_flake8_output_invalid(self):
        """Test parsing invalid flake8 output."""
        output = "This is not a valid flake8 line"
        results = _parse_flake8_output(output)
        assert len(results) == 0

    def test_parse_flake8_output_empty(self):
        """Test parsing empty output."""
        results = _parse_flake8_output("")
        assert len(results) == 0


class TestMyPyParsing:
    """Test mypy output parsing."""

    def test_parse_mypy_output_error(self):
        """Test parsing mypy error output."""
        output = "test.py:10: error: Incompatible types in assignment"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "mypy:mypy-error"
        assert result.level == "error"
        assert "Incompatible types" in result.message

    def test_parse_mypy_output_warning(self):
        """Test parsing mypy warning output."""
        output = "test.py:15: warning: Unused 'type: ignore' comment"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.level == "warning"

    def test_parse_mypy_output_with_code(self):
        """Test parsing mypy output with error code."""
        output = "test.py:20: error: Need type annotation for 'x' [var-annotated]"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "var-annotated"

    def test_parse_mypy_output_with_column(self):
        """Test parsing mypy output with column number."""
        output = "test.py:25:10: error: Missing return type annotation"
        results = _parse_mypy_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.locations[0].physical_location.region.start_column == 10


class TestBanditParsing:
    """Test bandit output parsing."""

    def test_parse_bandit_output_valid(self):
        """Test parsing valid bandit output."""
        output = """{
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Use of hard coded passwords",
                    "test_id": "B105"
                }
            ]
        }"""

        results = _parse_bandit_output(output)

        assert len(results) == 1
        result = results[0]
        assert result.rule_id == "bandit:B105"
        assert result.level == "error"
        assert "hard coded passwords" in result.message
        assert result.locations[0].physical_location.artifact_location.uri == "test.py"
        assert result.locations[0].physical_location.region.start_line == 10

    def test_parse_bandit_output_multiple(self):
        """Test parsing multiple bandit issues."""
        output = """{
            "results": [
                {
                    "filename": "test1.py",
                    "line_number": 5,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Issue 1",
                    "test_id": "B001"
                },
                {
                    "filename": "test2.py",
                    "line_number": 15,
                    "issue_severity": "MEDIUM",
                    "issue_confidence": "LOW",
                    "issue_text": "Issue 2",
                    "test_id": "B002"
                }
            ]
        }"""

        results = _parse_bandit_output(output)
        assert len(results) == 2

    def test_parse_bandit_output_invalid_json(self):
        """Test parsing invalid JSON."""
        output = "This is not valid JSON"
        results = _parse_bandit_output(output)
        assert len(results) == 0

    def test_parse_bandit_output_empty_results(self):
        """Test parsing empty results."""
        output = '{"results": []}'
        results = _parse_bandit_output(output)
        assert len(results) == 0


class TestAnalyzerMain:
    """Test the main analyzer function."""

    def test_analyzer_main_basic(self):
        """Test basic analyzer main function."""
        with patch("sys.argv", ["analyzer.py", "--skip-tests"]):
            with patch("ai_guard.analyzer.load_config") as mock_config:
                with patch("ai_guard.analyzer.changed_python_files") as mock_files:
                    with patch(
                        "ai_guard.analyzer.run_pytest_with_coverage"
                    ) as mock_pytest:
                        with patch(
                            "ai_guard.analyzer.subprocess.run"
                        ) as mock_subprocess:
                            with patch("ai_guard.analyzer.write_sarif") as mock_sarif:

                                # Setup mocks
                                mock_config.return_value = {"min_cov": 80}
                                mock_files.return_value = ["test.py"]
                                mock_pytest.return_value = (0, 85)
                                mock_subprocess.return_value.stdout = ""
                                mock_subprocess.return_value.returncode = 0

                                # Run analyzer
                                analyzer_main()

                                # Verify calls
                                mock_config.assert_called_once()
                                mock_files.assert_called_once()
                                mock_pytest.assert_called_once()
                                mock_sarif.assert_called_once()

    def test_analyzer_main_with_enhanced_testgen(self):
        """Test analyzer with enhanced test generation."""
        with patch("sys.argv", ["analyzer.py", "--enhanced-testgen", "--skip-tests"]):
            with patch("ai_guard.analyzer.load_config") as mock_config:
                with patch("ai_guard.analyzer.changed_python_files") as mock_files:
                    with patch(
                        "ai_guard.analyzer.run_pytest_with_coverage"
                    ) as mock_pytest:
                        with patch(
                            "ai_guard.analyzer.subprocess.run"
                        ) as mock_subprocess:
                            with patch("ai_guard.analyzer.write_sarif") as mock_sarif:
                                with patch(
                                    "ai_guard.analyzer.EnhancedTestGenerator"
                                ) as mock_generator:

                                    # Setup mocks
                                    mock_config.return_value = {"min_cov": 80}
                                    mock_files.return_value = ["test.py"]
                                    mock_pytest.return_value = (0, 85)
                                    mock_subprocess.return_value.stdout = ""
                                    mock_subprocess.return_value.returncode = 0
                                    mock_gen_instance = Mock()
                                    mock_generator.return_value = mock_gen_instance

                                    # Run analyzer
                                    analyzer_main()

                                    # Verify enhanced test generator was called
                                    mock_generator.assert_called_once()
                                    mock_gen_instance.generate_tests.assert_called_once()

    def test_analyzer_main_with_pr_annotations(self):
        """Test analyzer with PR annotations."""
        with patch("sys.argv", ["analyzer.py", "--pr-annotations", "--skip-tests"]):
            with patch("ai_guard.analyzer.load_config") as mock_config:
                with patch("ai_guard.analyzer.changed_python_files") as mock_files:
                    with patch(
                        "ai_guard.analyzer.run_pytest_with_coverage"
                    ) as mock_pytest:
                        with patch(
                            "ai_guard.analyzer.subprocess.run"
                        ) as mock_subprocess:
                            with patch("ai_guard.analyzer.write_sarif") as mock_sarif:
                                with patch(
                                    "ai_guard.analyzer.PRAnnotator"
                                ) as mock_annotator:

                                    # Setup mocks
                                    mock_config.return_value = {"min_cov": 80}
                                    mock_files.return_value = ["test.py"]
                                    mock_pytest.return_value = (0, 85)
                                    mock_subprocess.return_value.stdout = ""
                                    mock_subprocess.return_value.returncode = 0
                                    mock_annotator_instance = Mock()
                                    mock_annotator.return_value = (
                                        mock_annotator_instance
                                    )

                                    # Run analyzer
                                    analyzer_main()

                                    # Verify PR annotator was called
                                    mock_annotator.assert_called_once()
                                    mock_annotator_instance.create_annotations.assert_called_once()

    def test_analyzer_main_coverage_failure(self):
        """Test analyzer when coverage is below threshold."""
        with patch("sys.argv", ["analyzer.py", "--min-cov", "90", "--skip-tests"]):
            with patch("ai_guard.analyzer.load_config") as mock_config:
                with patch("ai_guard.analyzer.changed_python_files") as mock_files:
                    with patch(
                        "ai_guard.analyzer.run_pytest_with_coverage"
                    ) as mock_pytest:
                        with patch(
                            "ai_guard.analyzer.subprocess.run"
                        ) as mock_subprocess:
                            with patch("ai_guard.analyzer.write_sarif") as mock_sarif:

                                # Setup mocks - coverage below threshold
                                mock_config.return_value = {"min_cov": 90}
                                mock_files.return_value = ["test.py"]
                                mock_pytest.return_value = (
                                    0,
                                    85,
                                )  # 85% coverage, below 90%
                                mock_subprocess.return_value.stdout = ""
                                mock_subprocess.return_value.returncode = 0

                                # Run analyzer
                                with pytest.raises(SystemExit) as exc_info:
                                    analyzer_main()

                                # Should exit with error code
                                assert exc_info.value.code == 1

    def test_analyzer_main_tests_failure(self):
        """Test analyzer when tests fail."""
        with patch("sys.argv", ["analyzer.py"]):
            with patch("ai_guard.analyzer.load_config") as mock_config:
                with patch("ai_guard.analyzer.changed_python_files") as mock_files:
                    with patch(
                        "ai_guard.analyzer.run_pytest_with_coverage"
                    ) as mock_pytest:
                        with patch(
                            "ai_guard.analyzer.subprocess.run"
                        ) as mock_subprocess:
                            with patch("ai_guard.analyzer.write_sarif") as mock_sarif:

                                # Setup mocks - tests fail
                                mock_config.return_value = {"min_cov": 80}
                                mock_files.return_value = ["test.py"]
                                mock_pytest.return_value = (
                                    1,
                                    85,
                                )  # Tests fail (exit code 1)
                                mock_subprocess.return_value.stdout = ""
                                mock_subprocess.return_value.returncode = 0

                                # Run analyzer
                                with pytest.raises(SystemExit) as exc_info:
                                    analyzer_main()

                                # Should exit with error code
                                assert exc_info.value.code == 1


class TestAnalyzerIntegration:
    """Integration tests for analyzer."""

    def test_analyzer_with_real_files(self):
        """Test analyzer with real file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def test_function():\n    pass")

            with patch("sys.argv", ["analyzer.py", "--skip-tests"]):
                with patch("ai_guard.analyzer.load_config") as mock_config:
                    with patch("ai_guard.analyzer.changed_python_files") as mock_files:
                        with patch(
                            "ai_guard.analyzer.run_pytest_with_coverage"
                        ) as mock_pytest:
                            with patch(
                                "ai_guard.analyzer.subprocess.run"
                            ) as mock_subprocess:
                                with patch(
                                    "ai_guard.analyzer.write_sarif"
                                ) as mock_sarif:

                                    # Setup mocks
                                    mock_config.return_value = {"min_cov": 80}
                                    mock_files.return_value = [str(test_file)]
                                    mock_pytest.return_value = (0, 85)
                                    mock_subprocess.return_value.stdout = ""
                                    mock_subprocess.return_value.returncode = 0

                                    # Run analyzer
                                    analyzer_main()

                                    # Verify it processed the test file
                                    mock_files.assert_called_once()
                                    mock_sarif.assert_called_once()
