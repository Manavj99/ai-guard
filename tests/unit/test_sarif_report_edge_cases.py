"""Edge case tests for SARIF report module to improve coverage to 90%+."""

from unittest.mock import patch, mock_open

from ai_guard.sarif_report import (
    SarifRun,
    SarifResult,
    write_sarif,
    make_location,
    create_sarif_report,
    parse_issue_to_sarif,
)


class TestSARIFReportEdgeCases:
    """Test edge cases and error handling in SARIF report module."""

    def test_sarif_run_creation(self):
        """Test SarifRun creation with all fields."""
        run = SarifRun(
            tool_name="flake8", tool_version="3.9.2", results=[{"id": "test"}]
        )

        assert run.tool_name == "flake8"
        assert run.tool_version == "3.9.2"
        assert run.results == [{"id": "test"}]

    def test_sarif_run_defaults(self):
        """Test SarifRun creation with default values."""
        run = SarifRun(tool_name="flake8")

        assert run.tool_version == "unknown"
        assert run.results == []

    def test_sarif_result_creation(self):
        """Test SarifResult creation with all fields."""
        result = SarifResult(
            rule_id="E501",
            message="Line too long",
            level="warning",
            locations=[{"uri": "src/test.py", "start_line": 42}],
        )

        assert result.rule_id == "E501"
        assert result.message == "Line too long"
        assert result.level == "warning"
        assert len(result.locations) == 1

    def test_sarif_result_defaults(self):
        """Test SarifResult creation with default values."""
        result = SarifResult(rule_id="E501", message="Line too long")

        assert result.level == "warning"
        assert result.locations == []

    def test_make_location_basic(self):
        """Test basic location creation."""
        location = make_location("src/test.py", 42, 10)

        assert location["uri"] == "src/test.py"
        assert location["start_line"] == 42
        assert location["start_column"] == 10
        assert location["end_line"] == 42
        assert location["end_column"] == 10

    def test_make_location_with_end_position(self):
        """Test location creation with end position."""
        location = make_location("src/test.py", 42, 10, 42, 50)

        assert location["start_line"] == 42
        assert location["start_column"] == 10
        assert location["end_line"] == 42
        assert location["end_column"] == 50

    def test_make_location_with_relative_path(self):
        """Test location creation with relative path."""
        location = make_location("./src/test.py", 1, 1)

        assert location["uri"] == "./src/test.py"

    def test_make_location_with_absolute_path(self):
        """Test location creation with absolute path."""
        location = make_location("/absolute/path/test.py", 1, 1)

        assert location["uri"] == "/absolute/path/test.py"

    def test_make_location_with_unicode_path(self):
        """Test location creation with unicode path."""
        location = make_location("src/тест.py", 1, 1)

        assert location["uri"] == "src/тест.py"

    def test_make_location_with_special_characters(self):
        """Test location creation with special characters in path."""
        location = make_location("src/test file.py", 1, 1)

        assert location["uri"] == "src/test file.py"

    def test_parse_issue_to_sarif_basic(self):
        """Test basic issue parsing to SARIF."""
        issue = {
            "file_path": "src/test.py",
            "line_number": 42,
            "column": 10,
            "rule_id": "E501",
            "message": "Line too long",
        }

        result = parse_issue_to_sarif(issue)

        assert result["rule_id"] == "E501"
        assert result["message"]["text"] == "Line too long"
        assert len(result["locations"]) == 1
        assert result["locations"][0]["uri"] == "src/test.py"

    def test_parse_issue_to_sarif_with_severity(self):
        """Test issue parsing with severity information."""
        issue = {
            "file_path": "src/test.py",
            "line_number": 1,
            "column": 1,
            "rule_id": "F401",
            "message": "Import unused",
            "severity": "error",
        }

        result = parse_issue_to_sarif(issue)

        assert result["level"] == "error"

    def test_parse_issue_to_sarif_without_column(self):
        """Test issue parsing without column information."""
        issue = {
            "file_path": "src/test.py",
            "line_number": 42,
            "rule_id": "E501",
            "message": "Line too long",
        }

        result = parse_issue_to_sarif(issue)

        assert result["locations"][0]["start_column"] == 1
        assert result["locations"][0]["end_column"] == 1

    def test_parse_issue_to_sarif_without_line_number(self):
        """Test issue parsing without line number."""
        issue = {
            "file_path": "src/test.py",
            "rule_id": "E501",
            "message": "Line too long",
        }

        result = parse_issue_to_sarif(issue)

        assert result["locations"][0]["start_line"] == 1
        assert result["locations"][0]["end_line"] == 1

    def test_parse_issue_to_sarif_without_file_path(self):
        """Test issue parsing without file path."""
        issue = {"line_number": 42, "rule_id": "E501", "message": "Line too long"}

        result = parse_issue_to_sarif(issue)

        assert result["locations"][0]["uri"] == "unknown"

    def test_parse_issue_to_sarif_without_rule_id(self):
        """Test issue parsing without rule ID."""
        issue = {
            "file_path": "src/test.py",
            "line_number": 42,
            "message": "Line too long",
        }

        result = parse_issue_to_sarif(issue)

        assert result["rule_id"] == "unknown"

    def test_parse_issue_to_sarif_without_message(self):
        """Test issue parsing without message."""
        issue = {"file_path": "src/test.py", "line_number": 42, "rule_id": "E501"}

        result = parse_issue_to_sarif(issue)

        assert result["message"]["text"] == "No message provided"

    def test_parse_issue_to_sarif_with_long_message(self):
        """Test issue parsing with long message."""
        long_message = "This is a very long message that should be handled properly by the SARIF parser without any issues or truncation"
        issue = {
            "file_path": "src/test.py",
            "line_number": 42,
            "rule_id": "E501",
            "message": long_message,
        }

        result = parse_issue_to_sarif(issue)

        assert result["message"]["text"] == long_message

    def test_parse_issue_to_sarif_with_special_characters(self):
        """Test issue parsing with special characters in message."""
        special_message = "Message with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        issue = {
            "file_path": "src/test.py",
            "line_number": 42,
            "rule_id": "E501",
            "message": special_message,
        }

        result = parse_issue_to_sarif(issue)

        assert result["message"]["text"] == special_message

    def test_parse_issue_to_sarif_with_unicode_message(self):
        """Test issue parsing with unicode message."""
        unicode_message = "Сообщение с русскими символами"
        issue = {
            "file_path": "src/test.py",
            "line_number": 42,
            "rule_id": "E501",
            "message": unicode_message,
        }

        result = parse_issue_to_sarif(issue)

        assert result["message"]["text"] == unicode_message

    def test_create_sarif_report_basic(self):
        """Test basic SARIF report creation."""
        runs = [
            SarifRun("flake8", "3.9.2", [{"id": "test1"}]),
            SarifRun("mypy", "0.991", [{"id": "test2"}]),
        ]

        report = create_sarif_report(runs)

        assert report["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
        assert report["version"] == "2.1.0"
        assert len(report["runs"]) == 2

    def test_create_sarif_report_empty_runs(self):
        """Test SARIF report creation with empty runs."""
        report = create_sarif_report([])

        assert report["runs"] == []

    def test_create_sarif_report_single_run(self):
        """Test SARIF report creation with single run."""
        runs = [SarifRun("flake8", "3.9.2", [{"id": "test"}])]

        report = create_sarif_report(runs)

        assert len(report["runs"]) == 1
        assert report["runs"][0]["tool"]["driver"]["name"] == "flake8"

    def test_create_sarif_report_with_metadata(self):
        """Test SARIF report creation with additional metadata."""
        runs = [SarifRun("flake8", "3.9.2", [{"id": "test"}])]

        report = create_sarif_report(runs, metadata={"custom": "value"})

        assert report["custom"] == "value"

    @patch("builtins.open", new_callable=mock_open)
    def test_write_sarif_success(self, mock_file):
        """Test successful SARIF file writing."""
        runs = [SarifRun("flake8", "3.9.2", [{"id": "test"}])]

        result = write_sarif(runs, "test.sarif")

        assert result is True
        mock_file.assert_called_once_with("test.sarif", "w", encoding="utf-8")

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_write_sarif_permission_error(self, mock_file):
        """Test SARIF file writing with permission error."""
        runs = [SarifRun("flake8", "3.9.2", [{"id": "test"}])]

        result = write_sarif(runs, "/root/test.sarif")

        assert result is False

    @patch("builtins.open", side_effect=OSError("Disk full"))
    def test_write_sarif_os_error(self, mock_file):
        """Test SARIF file writing with OS error."""
        runs = [SarifRun("flake8", "3.9.2", [{"id": "test"}])]

        result = write_sarif(runs, "test.sarif")

        assert result is False

    @patch(
        "builtins.open", side_effect=UnicodeEncodeError("utf-8", "test", 0, 1, "reason")
    )
    def test_write_sarif_unicode_error(self, mock_file):
        """Test SARIF file writing with unicode error."""
        runs = [SarifRun("flake8", "3.9.2", [{"id": "test"}])]

        result = write_sarif(runs, "test.sarif")

        assert result is False

    def test_write_sarif_with_empty_runs(self):
        """Test SARIF file writing with empty runs."""
        result = write_sarif([], "test.sarif")

        assert result is True

    def test_write_sarif_with_complex_data(self):
        """Test SARIF file writing with complex data structures."""
        complex_result = {
            "rule_id": "E501",
            "message": {"text": "Line too long"},
            "locations": [
                {
                    "uri": "src/test.py",
                    "start_line": 42,
                    "start_column": 1,
                    "end_line": 42,
                    "end_column": 100,
                }
            ],
            "level": "warning",
        }

        runs = [SarifRun("flake8", "3.9.2", [complex_result])]

        with patch("builtins.open", new_callable=mock_open) as mock_file:
            result = write_sarif(runs, "test.sarif")

            assert result is True
            mock_file.assert_called_once()

    def test_sarif_run_to_dict(self):
        """Test SarifRun conversion to dictionary."""
        run = SarifRun("flake8", "3.9.2", [{"id": "test"}])

        run_dict = run.to_dict()

        assert run_dict["tool"]["driver"]["name"] == "flake8"
        assert run_dict["tool"]["driver"]["version"] == "3.9.2"
        assert run_dict["results"] == [{"id": "test"}]

    def test_sarif_result_to_dict(self):
        """Test SarifResult conversion to dictionary."""
        result = SarifResult(
            rule_id="E501",
            message="Line too long",
            level="warning",
            locations=[{"uri": "src/test.py", "start_line": 42}],
        )

        result_dict = result.to_dict()

        assert result_dict["rule_id"] == "E501"
        assert result_dict["message"]["text"] == "Line too long"
        assert result_dict["level"] == "warning"
        assert len(result_dict["locations"]) == 1

    def test_sarif_result_without_optional_fields(self):
        """Test SarifResult without optional fields."""
        result = SarifResult(rule_id="E501", message="Line too long")

        result_dict = result.to_dict()

        assert result_dict["rule_id"] == "E501"
        assert result_dict["message"]["text"] == "Line too long"
        assert "level" not in result_dict
        assert result_dict["locations"] == []

    def test_make_location_with_zero_values(self):
        """Test location creation with zero values."""
        location = make_location("src/test.py", 0, 0)

        assert location["start_line"] == 0
        assert location["start_column"] == 0
        assert location["end_line"] == 0
        assert location["end_column"] == 0

    def test_make_location_with_negative_values(self):
        """Test location creation with negative values."""
        location = make_location("src/test.py", -1, -1)

        assert location["start_line"] == -1
        assert location["start_column"] == -1
        assert location["end_line"] == -1
        assert location["end_column"] == -1

    def test_make_location_with_large_values(self):
        """Test location creation with large values."""
        location = make_location("src/test.py", 999999, 999999)

        assert location["start_line"] == 999999
        assert location["start_column"] == 999999
        assert location["end_line"] == 999999
        assert location["end_column"] == 999999

    def test_parse_issue_to_sarif_with_none_values(self):
        """Test issue parsing with None values."""
        issue = {
            "file_path": None,
            "line_number": None,
            "column": None,
            "rule_id": None,
            "message": None,
        }

        result = parse_issue_to_sarif(issue)

        assert result["rule_id"] == "unknown"
        assert result["message"]["text"] == "No message provided"
        assert result["locations"][0]["uri"] == "unknown"
        assert result["locations"][0]["start_line"] == 1
        assert result["locations"][0]["start_column"] == 1
