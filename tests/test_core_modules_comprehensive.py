"""Comprehensive tests for core AI-Guard modules to increase coverage."""

import pytest
import json
import tempfile
import os
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from ai_guard.pr_annotations import (
    create_pr_annotation, format_annotation_message, get_annotation_level,
    create_quality_gate_annotation, create_coverage_annotation,
    create_security_annotation, create_performance_annotation,
    create_test_annotation, PRAnnotationManager, AnnotationFormatter,
    PRAnnotator, CodeIssue, PRAnnotation, PRReviewSummary
)
from ai_guard.report import (
    generate_report, format_report_summary, save_report_to_file,
    load_report_from_file, ReportGeneratorV2 as ReportGenerator, ReportFormatter, GateResult
)
from ai_guard.security_scanner import (
    scan_for_vulnerabilities, check_dependencies, analyze_security_patterns,
    SecurityScanner, VulnerabilityChecker, DependencyAnalyzer,
    SecurityPatternAnalyzer
)
from ai_guard.tests_runner import (
    run_tests, discover_test_files, execute_test_suite,
    TestRunner, TestDiscoverer, TestExecutor
)
from ai_guard.utils.error_formatter import (
    format_error_message, format_exception, format_traceback,
    ErrorFormatter, ExceptionFormatter, TracebackFormatter,
    ErrorSeverity, ErrorCategory, ErrorContext
)
from ai_guard.utils.subprocess_runner import (
    run_command, run_command_dict, run_command_with_output, run_command_safe,
    SubprocessRunner, CommandExecutor, SafeCommandRunner
)


class TestPRAnnotationsComprehensive:
    """Comprehensive tests for PR annotations."""

    def test_create_pr_annotation_all_levels(self):
        """Test creating PR annotations with all levels."""
        for level in ["notice", "warning", "failure", "error", "info"]:
            annotation = create_pr_annotation(
                path="test.py", line=10, level=level, message="Test message"
            )
            assert annotation["path"] == "test.py"
            assert annotation["line"] == 10
            assert annotation["message"] == "Test message"

    def test_format_annotation_message_all_options(self):
        """Test formatting annotation messages with all options."""
        message = format_annotation_message(
            "Main message",
            details="Additional details",
            suggestion="Try this instead",
            code_example="print('hello')"
        )
        assert "Main message" in message
        assert "Additional details" in message
        assert "Try this instead" in message
        assert "print('hello')" in message

    def test_get_annotation_level_all_inputs(self):
        """Test getting annotation levels for all inputs."""
        assert get_annotation_level("error") == "failure"
        assert get_annotation_level("warning") == "warning"
        assert get_annotation_level("info") == "notice"
        assert get_annotation_level("unknown") == "notice"

    def test_create_quality_gate_annotation_all_statuses(self):
        """Test creating quality gate annotations for all statuses."""
        for status in ["passed", "failed"]:
            annotation = create_quality_gate_annotation(
                path="test.py", line=10, gate_name="test_gate",
                status=status, message=f"Gate {status}"
            )
            assert annotation["path"] == "test.py"
            assert annotation["line"] == 10
            assert status in annotation["message"]

    def test_create_coverage_annotation_all_scenarios(self):
        """Test creating coverage annotations for all scenarios."""
        # High coverage
        annotation = create_coverage_annotation("test.py", 95.0, 80.0)
        assert annotation["annotation_level"] == "notice"
        
        # Low coverage
        annotation = create_coverage_annotation("test.py", 65.0, 80.0)
        assert annotation["annotation_level"] == "warning"

    def test_create_security_annotation_all_severities(self):
        """Test creating security annotations for all severities."""
        severities = ["high", "medium", "low"]
        for severity in severities:
            annotation = create_security_annotation(
                path="test.py", line=10, severity=severity,
                vulnerability="Test Vuln", description="Test description"
            )
            assert annotation["path"] == "test.py"
            assert annotation["line"] == 10
            assert severity.upper() in annotation["message"]

    def test_create_performance_annotation_all_scenarios(self):
        """Test creating performance annotations for all scenarios."""
        # Fast function
        annotation = create_performance_annotation(
            "test.py", 10, "fast_func", 0.5, 1.0
        )
        assert annotation["annotation_level"] == "notice"
        
        # Slow function
        annotation = create_performance_annotation(
            "test.py", 10, "slow_func", 2.0, 1.0
        )
        assert annotation["annotation_level"] == "warning"

    def test_create_test_annotation_all_statuses(self):
        """Test creating test annotations for all statuses."""
        # Passed test
        annotation = create_test_annotation(
            "test.py", 10, "test_func", "passed", 0.1
        )
        assert annotation["annotation_level"] == "notice"
        
        # Failed test
        annotation = create_test_annotation(
            "test.py", 10, "test_func", "failed", 0.1, "Test failed"
        )
        assert annotation["annotation_level"] == "failure"

    def test_pr_annotation_manager_comprehensive(self):
        """Test PR annotation manager comprehensively."""
        manager = PRAnnotationManager(max_annotations=3)
        
        # Add annotations
        for i in range(3):
            annotation = create_pr_annotation(f"test{i}.py", 10, "warning", f"Warning {i}")
            manager.add_annotation(annotation)
        
        # Test max limit
        extra_annotation = create_pr_annotation("test4.py", 10, "warning", "Extra")
        manager.add_annotation(extra_annotation)
        assert len(manager.annotations) == 3
        
        # Test filtering
        warning_annotations = manager.get_annotations_by_level("warning")
        assert len(warning_annotations) == 3
        
        test0_annotations = manager.get_annotations_by_path("test0.py")
        assert len(test0_annotations) == 1
        
        # Test summary
        summary = manager.get_summary()
        assert summary["total"] == 3
        assert summary["warnings"] == 3
        
        # Test clear
        manager.clear_annotations()
        assert len(manager.annotations) == 0

    def test_annotation_formatter_comprehensive(self):
        """Test annotation formatter comprehensively."""
        formatter = AnnotationFormatter(max_message_length=50, include_timestamp=False)
        
        # Test formatting
        annotation = create_pr_annotation("test.py", 10, "warning", "Test message")
        formatted = formatter.format_annotation(annotation)
        assert formatted["path"] == "test.py"
        
        # Test long message truncation
        long_message = "This is a very long message that should be truncated"
        annotation = create_pr_annotation("test.py", 10, "warning", long_message)
        formatted = formatter.format_annotation(annotation)
        assert len(formatted["message"]) <= 50
        assert "..." in formatted["message"]
        
        # Test batch formatting
        annotations = [
            create_pr_annotation("test1.py", 10, "warning", "Warning 1"),
            create_pr_annotation("test2.py", 10, "error", "Error 1")
        ]
        formatted = formatter.format_annotations(annotations)
        assert len(formatted) == 2

    def test_pr_annotator_comprehensive(self):
        """Test PR annotator comprehensively."""
        annotator = PRAnnotator()
        
        # Test adding issues
        issue = CodeIssue(
            file_path="test.py", line_number=10, column=5,
            severity="error", message="Test error", rule_id="E001"
        )
        annotator.add_issue(issue)
        assert len(annotator.issues) == 1
        assert len(annotator.annotations) == 1
        
        # Test lint issues
        lint_results = [
            {"file": "test.py", "line": 10, "column": 5, "severity": "warning", 
             "message": "Test warning", "rule": "W001"}
        ]
        annotator.add_lint_issues(lint_results)
        assert len(annotator.issues) == 2
        
        # Test coverage annotation
        coverage_data = {"coverage": 75.0, "uncovered_lines": [10, 20]}
        annotator.add_coverage_annotation("test.py", coverage_data)
        assert len(annotator.annotations) >= 2
        
        # Test security annotation
        security_issues = [
            {"file": "test.py", "line": 10, "severity": "high", 
             "message": "Security issue", "rule": "S001"}
        ]
        annotator.add_security_annotation(security_issues)
        assert len(annotator.annotations) >= 3
        
        # Test review summary
        summary = annotator.generate_review_summary()
        assert summary.overall_status in ["approved", "commented", "changes_requested"]
        assert summary.quality_score >= 0.0
        assert summary.quality_score <= 1.0
        
        # Test GitHub annotations
        github_annotations = annotator.create_github_annotations()
        assert len(github_annotations) >= 3
        
        # Test review comment
        comment = annotator.create_review_comment(summary)
        assert "AI-Guard Quality Review" in comment
        
        # Test save annotations
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            annotator.save_annotations(temp_path)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert "annotations" in data
            assert "issues" in data
            assert "summary" in data
        finally:
            os.unlink(temp_path)


class TestReportComprehensive:
    """Comprehensive tests for report module."""

    def test_generate_report_all_scenarios(self):
        """Test generating reports for all scenarios."""
        # Normal results
        results = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 1, "warning": 2}
        }
        report = generate_report(results)
        assert report["success"] is True
        assert report["files_analyzed"] == 5
        assert report["total_issues"] == 3
        
        # Empty results
        empty_results = {"files_analyzed": 0, "total_issues": 0, "issues_by_type": {}}
        report = generate_report(empty_results)
        assert report["success"] is True
        assert report["files_analyzed"] == 0

    def test_format_report_summary_all_scenarios(self):
        """Test formatting report summaries for all scenarios."""
        # Normal summary
        data = {
            "files_analyzed": 10,
            "total_issues": 5,
            "issues_by_type": {"error": 2, "warning": 3}
        }
        summary = format_report_summary(data)
        assert "10 files analyzed" in summary
        assert "5 total issues" in summary
        assert "2 errors" in summary
        assert "3 warnings" in summary
        
        # Empty summary
        empty_data = {"files_analyzed": 0, "total_issues": 0, "issues_by_type": {}}
        summary = format_report_summary(empty_data)
        assert "0 files analyzed" in summary

    def test_save_load_report_comprehensive(self):
        """Test saving and loading reports comprehensively."""
        report_data = {
            "files_analyzed": 3,
            "total_issues": 2,
            "issues_by_type": {"error": 1, "warning": 1}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Test save success
            result = save_report_to_file(report_data, temp_path)
            assert result["success"] is True
            
            # Test load success
            result = load_report_from_file(temp_path)
            assert result["success"] is True
            assert result["data"] == report_data
            
            # Test load non-existent file
            result = load_report_from_file("nonexistent.json")
            assert result["success"] is False
            assert "File not found" in result["error"]
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_report_generator_comprehensive(self):
        """Test report generator comprehensively."""
        # Test JSON format
        generator = ReportGenerator(report_format="json")
        results = {"files_analyzed": 3, "total_issues": 2}
        report = generator.generate_report(results)
        assert report["success"] is True
        assert report["format"] == "json"
        
        # Test HTML format
        generator = ReportGenerator(report_format="html")
        report = generator.generate_report(results)
        assert report["success"] is True
        assert report["format"] == "html"
        assert "<html>" in report["content"]
        
        # Test unsupported format
        generator = ReportGenerator(report_format="xml")
        report = generator.generate_report(results)
        assert report["success"] is False
        assert "error" in report

    def test_report_formatter_comprehensive(self):
        """Test report formatter comprehensively."""
        formatter = ReportFormatter()
        
        # Test summary formatting
        data = {
            "files_analyzed": 5,
            "total_issues": 3,
            "issues_by_type": {"error": 1, "warning": 2}
        }
        summary = formatter.format_summary(data)
        assert "5 files analyzed" in summary
        
        # Test issues list formatting
        issues = [
            {"type": "error", "message": "Error 1", "file": "test1.py"},
            {"type": "warning", "message": "Warning 1", "file": "test2.py"}
        ]
        formatted = formatter.format_issues_list(issues)
        assert "Error 1" in formatted
        assert "Warning 1" in formatted
        assert "test1.py" in formatted
        
        # Test empty issues
        formatted = formatter.format_issues_list([])
        assert "No issues found" in formatted


class TestSecurityScannerComprehensive:
    """Comprehensive tests for security scanner."""

    @patch('subprocess.run')
    def test_scan_for_vulnerabilities_comprehensive(self, mock_run):
        """Test vulnerability scanning comprehensively."""
        # Test success
        mock_output = json.dumps([
            {"vulnerability": "SQL Injection", "severity": "high", "file": "test.py", "line": 10}
        ])
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr="")
        
        result = scan_for_vulnerabilities(["test.py"])
        assert result["success"] is True
        assert "vulnerabilities" in result
        assert "files_scanned" in result
        assert result["files_scanned"] == 1
        
        # Test failure
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        result = scan_for_vulnerabilities(["test.py"])
        assert result["success"] is True  # Function always returns success=True

    @patch('subprocess.call')
    def test_check_dependencies_comprehensive(self, mock_call):
        """Test dependency checking comprehensively."""
        # Test success
        mock_call.return_value = 0
        
        result = check_dependencies()
        assert result["success"] is True
        assert "safety_check" in result
        
        # Test failure
        mock_call.return_value = 1
        result = check_dependencies()
        assert result["success"] is False

    def test_analyze_security_patterns_comprehensive(self):
        """Test security pattern analysis comprehensively."""
        # Test with SQL injection
        code_with_sql = """
        user_input = input("Enter name: ")
        query = f"SELECT * FROM users WHERE name = '{user_input}'"
        cursor.execute(query)
        """
        result = analyze_security_patterns(code_with_sql, "test.py")
        assert result["success"] is True
        assert len(result["patterns"]) > 0
        
        # Test with hardcoded password
        code_with_password = """
        password = "admin123"
        """
        result = analyze_security_patterns(code_with_password, "test.py")
        assert result["success"] is True
        
        # Test with dangerous functions
        code_with_dangerous = """
        import os
        os.system("rm -rf /")
        eval("malicious_code()")
        """
        result = analyze_security_patterns(code_with_dangerous, "test.py")
        assert result["success"] is True
        
        # Test clean code
        clean_code = """
        def safe_function():
            return "Hello World"
        """
        result = analyze_security_patterns(clean_code, "test.py")
        assert result["success"] is True

    def test_security_scanner_class_comprehensive(self):
        """Test SecurityScanner class comprehensively."""
        scanner = SecurityScanner()
        
        # Test bandit scan
        result = scanner.run_bandit_scan()
        assert isinstance(result, int)
        
        # Test safety scan
        result = scanner.run_safety_scan()
        assert isinstance(result, int)
        
        # Test all security checks
        result = scanner.run_all_security_checks()
        assert isinstance(result, int)

    def test_vulnerability_checker_comprehensive(self):
        """Test VulnerabilityChecker comprehensively."""
        checker = VulnerabilityChecker()
        
        # Test vulnerability patterns
        code = "password = 'admin123'"
        result = checker.check_vulnerability_patterns(code, "test.py")
        assert result["success"] is True
        
        # Test SQL injection patterns
        code = "query = f'SELECT * FROM users WHERE name = {user_input}'"
        result = checker.check_sql_injection_patterns(code, "test.py")
        assert result["success"] is True
        
        # Test XSS patterns
        code = "html = f'<div>{user_input}</div>'"
        result = checker.check_xss_patterns(code, "test.py")
        assert result["success"] is True

    def test_dependency_analyzer_comprehensive(self):
        """Test DependencyAnalyzer comprehensively."""
        analyzer = DependencyAnalyzer()
        
        # Test requirements file analysis
        requirements_content = "requests==2.25.1\ndjango==3.2.0"
        with patch("builtins.open", mock_open(read_data=requirements_content)):
            result = analyzer.analyze_requirements_file("requirements.txt")
        assert result["success"] is True
        assert len(result["packages"]) == 2
        
        # Test file not found
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = analyzer.analyze_requirements_file("nonexistent.txt")
        assert result["success"] is False
        
        # Test package vulnerability checking
        packages = [{"name": "requests", "version": "2.25.1"}]
        result = analyzer.check_package_vulnerabilities(packages)
        assert result["success"] is True

    def test_security_pattern_analyzer_comprehensive(self):
        """Test SecurityPatternAnalyzer comprehensively."""
        analyzer = SecurityPatternAnalyzer()
        
        # Test code pattern analysis
        code = "os.system('rm -rf /')"
        result = analyzer.analyze_code_patterns(code, "test.py")
        assert result["success"] is True
        
        # Test hardcoded secrets
        code = "api_key = 'sk-1234567890abcdef'"
        result = analyzer.check_hardcoded_secrets(code, "test.py")
        assert result["success"] is True
        
        # Test dangerous functions
        code = "eval('malicious_code()')"
        result = analyzer.check_dangerous_functions(code, "test.py")
        assert result["success"] is True


class TestTestsRunnerComprehensive:
    """Comprehensive tests for tests runner."""

    @patch('subprocess.run')
    def test_run_tests_comprehensive(self, mock_run):
        """Test running tests comprehensively."""
        # Test success
        mock_output = "test_file.py::test_function PASSED [100%]"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr="")
        
        result = run_tests(["test_file.py"])
        assert result["success"] is True
        assert result["passed"] == 1
        assert result["failed"] == 0
        
        # Test failure
        mock_output = "test_file.py::test_function FAILED [100%]"
        mock_run.return_value = MagicMock(returncode=1, stdout=mock_output, stderr="")
        
        result = run_tests(["test_file.py"])
        assert result["success"] is False
        assert result["failed"] == 1

    @patch('os.listdir')
    def test_discover_test_files_comprehensive(self, mock_listdir):
        """Test discovering test files comprehensively."""
        # Test with test files
        mock_listdir.return_value = ["test_file1.py", "test_file2.py", "other_file.py"]
        result = discover_test_files("test_dir")
        assert result["success"] is True
        assert len(result["test_files"]) == 2
        
        # Test with no test files
        mock_listdir.return_value = ["other_file.py", "not_test.txt"]
        result = discover_test_files("test_dir")
        assert result["success"] is True
        assert len(result["test_files"]) == 0

    def test_execute_test_suite_comprehensive(self):
        """Test executing test suite comprehensively."""
        with patch('ai_guard.tests_runner.run_tests') as mock_run_tests:
            mock_run_tests.return_value = {
                "success": True, "passed": 5, "failed": 0, "total": 5
            }
            
            result = execute_test_suite(["test_file1.py", "test_file2.py"])
            assert result["success"] is True
            assert result["passed"] == 5

    def test_test_runner_class_comprehensive(self):
        """Test TestRunner class comprehensively."""
        runner = TestRunner()
        
        with patch.object(runner, '_execute_test_command') as mock_execute:
            mock_execute.return_value = {
                "success": True, "passed": 3, "failed": 0, "total": 3
            }
            
            # Test single file
            result = runner.run_test_file("test_file.py")
            assert result["success"] is True
            
            # Test directory
            with patch.object(runner, 'discover_test_files') as mock_discover:
                mock_discover.return_value = {
                    "success": True, "test_files": ["test_file1.py", "test_file2.py"]
                }
                result = runner.run_test_directory("test_dir")
                assert result["success"] is True

    def test_test_discoverer_comprehensive(self):
        """Test TestDiscoverer comprehensively."""
        discoverer = TestDiscoverer()
        
        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = ["test_file1.py", "test_file2.py", "other_file.py"]
            result = discoverer.discover_test_files("test_dir")
            assert result["success"] is True
            assert len(result["test_files"]) == 2
        
        with patch("os.walk") as mock_walk:
            mock_walk.return_value = [
                ("test_dir", [], ["test_file1.py", "other_file.py"]),
                ("test_dir/subdir", [], ["test_file2.py"])
            ]
            result = discoverer.discover_test_files("test_dir", recursive=True)
            assert result["success"] is True
            assert len(result["test_files"]) == 2

    def test_test_executor_comprehensive(self):
        """Test TestExecutor comprehensively."""
        executor = TestExecutor(timeout=300)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test_file1.py::test_function1 PASSED\ntest_file1.py::test_function2 PASSED\ntest_file1.py::test_function3 PASSED\ntest_file1.py::test_function4 PASSED\ntest_file1.py::test_function5 PASSED\ntest_file1.py::test_function6 FAILED"
            mock_run.return_value = mock_result
            
            result = executor.execute_tests(["test_file1.py", "test_file2.py"])
            assert result["success"] is True
            assert result["passed"] == 5
            assert result["failed"] == 1


class TestErrorFormatterComprehensive:
    """Comprehensive tests for error formatter."""

    def test_format_error_message_comprehensive(self):
        """Test formatting error messages comprehensively."""
        # Simple message
        result = format_error_message("Simple error")
        assert result == "[ERROR] | Simple error"
        
        # With context
        context = {"file": "test.py", "line": 10}
        result = format_error_message("Error with context", context=context)
        assert "test.py" in result
        assert "10" in result
        
        # With suggestion
        result = format_error_message("Error with suggestion", suggestion="Try this")
        assert "Try this" in result
        
        # With severity
        result = format_error_message("Warning message", severity="warning")
        assert "[WARNING]" in result

    def test_format_exception_comprehensive(self):
        """Test formatting exceptions comprehensively."""
        # Basic exception
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = format_exception(e)
            assert "ValueError" in result
            assert "Test error" in result
        
        # With traceback
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = format_exception(e, include_traceback=True)
            assert "ValueError" in result
            assert "Traceback" in result

    def test_format_traceback_comprehensive(self):
        """Test formatting tracebacks comprehensively."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            result = format_traceback(tb)
            assert "ValueError" in result
            assert "Test error" in result

    def test_error_formatter_class_comprehensive(self):
        """Test ErrorFormatter class comprehensively."""
        formatter = ErrorFormatter(include_context=True, include_emoji=True)
        
        # Test error formatting
        context = ErrorContext(
            module="test_module", function="test_function",
            file_path="test.py", line_number=10
        )
        result = formatter.format_error(
            "Test error", ErrorSeverity.ERROR, ErrorCategory.EXECUTION, context
        )
        assert "Test error" in result
        assert "test_module" in result
        assert "test_function" in result
        
        # Test annotation message formatting
        result = formatter.format_annotation_message("Test message", ErrorSeverity.WARNING, context)
        assert "Test message" in result
        
        # Test log message formatting
        result = formatter.format_log_message("Test log", ErrorSeverity.INFO, ErrorCategory.EXECUTION, context)
        assert "Test log" in result
        
        # Test gate result message formatting
        result = formatter.format_gate_result_message("test_gate", True, "Gate passed", context)
        assert "test_gate" in result
        assert "PASSED" in result
        
        # Test coverage message formatting
        result = formatter.format_coverage_message(85.0, 80.0, "test.py")
        assert "85.0%" in result
        assert "80.0%" in result
        
        # Test security message formatting
        result = formatter.format_security_message(3, "high", "bandit")
        assert "3" in result
        assert "high" in result
        
        # Test performance message formatting
        result = formatter.format_performance_message("slow_func", 2.5, 1.0)    
        assert "slow_func" in result
        assert "2.500s" in result

    def test_exception_formatter_comprehensive(self):
        """Test ExceptionFormatter comprehensively."""
        formatter = ExceptionFormatter(include_traceback=True, max_traceback_lines=5)
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            context = {"operation": "test", "file": "test.py"}
            result = formatter.format_exception(e, context=context)
            assert "ValueError" in result
            assert "test" in result
        
        # Test without traceback
        formatter_no_tb = ExceptionFormatter(include_traceback=False)
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = formatter_no_tb.format_exception(e)
            assert "ValueError" in result
            assert "Traceback" not in result

    def test_traceback_formatter_comprehensive(self):
        """Test TracebackFormatter comprehensively."""
        formatter = TracebackFormatter(max_lines=5, include_locals=False)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            result = formatter.format_traceback(tb)
            assert "ValueError" in result
        
        # Test with locals
        formatter_with_locals = TracebackFormatter(include_locals=True)
        try:
            local_var = "test_value"
            raise ValueError("Test error")
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            result = formatter_with_locals.format_traceback(tb)
            assert "ValueError" in result


class TestSubprocessRunnerComprehensive:
    """Comprehensive tests for subprocess runner."""

    @patch('subprocess.run')
    def test_run_command_comprehensive(self, mock_run):
        """Test running commands comprehensively."""
        # Test success
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = run_command_dict(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        
        # Test failure
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        result = run_command_dict(["false"])
        assert result["success"] is False
        assert result["returncode"] == 1
        
        # Test exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "command")
        result = run_command_dict(["invalid_command"])
        assert result["success"] is False
        assert "error" in result

    @patch('subprocess.run')
    def test_run_command_with_output_comprehensive(self, mock_run):
        """Test running commands with output comprehensively."""
        # Test success
        mock_run.return_value = MagicMock(returncode=0, stdout="Hello", stderr="")
        result = run_command_with_output(["echo", "Hello"])
        assert result["success"] is True
        assert result["stdout"] == "Hello"
        
        # Test failure
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        result = run_command_with_output(["false"])
        assert result["success"] is False
        assert result["stderr"] == "Error"

    @patch('subprocess.run')
    def test_run_command_safe_comprehensive(self, mock_run):
        """Test safe command running comprehensively."""
        # Test success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_command_safe(["echo", "hello"])
        assert result["success"] is True
        
        # Test failure
        mock_run.side_effect = subprocess.CalledProcessError(1, "invalid_command")
        result = run_command_safe(["invalid_command"])
        assert result["success"] is False
        assert "error" in result
        
        # Test timeout
        mock_run.side_effect = subprocess.TimeoutExpired("sleep", 1)
        result = run_command_safe(["sleep", "10"], timeout=1)
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @patch('subprocess.run')
    def test_subprocess_runner_class_comprehensive(self, mock_run):
        """Test SubprocessRunner class comprehensively."""
        runner = SubprocessRunner(timeout=30, capture_output=True)
        
        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test execute command
        result = runner.execute_command(["echo", "hello"])
        assert result["success"] is True
        
        # Test execute command with output
        result = runner.execute_command_with_output(["echo", "hello"])
        assert result["success"] is True
        
        # Test execute command safe
        result = runner.execute_command_safe(["echo", "hello"])
        assert result["success"] is True

    @patch('subprocess.run')
    def test_command_executor_comprehensive(self, mock_run):
        """Test CommandExecutor comprehensively."""
        executor = CommandExecutor()
        
        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test execute command
        result = executor.execute_command(["echo", "hello"])
        assert result["success"] is True
        
        # Test execute multiple commands
        commands = [["echo", "hello"], ["echo", "world"]]
        results = executor.execute_multiple_commands(commands)
        assert len(results) == 2
        assert all(result["success"] for result in results)

    @patch('subprocess.run')
    def test_safe_command_runner_comprehensive(self, mock_run):
        """Test SafeCommandRunner comprehensively."""
        runner = SafeCommandRunner(max_retries=3)
        
        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test run command safe
        result = runner.run_command_safe(["echo", "hello"])
        assert result["success"] is True
        assert result["attempts"] == 1
        
        # Test with validation
        def validate_output(result):
            return "hello" in result.get("stdout", "")
        
        result = runner.run_command_safe(["echo", "hello"], validation_func=validate_output)
        assert result["success"] is True
        assert result["validated"] is True
        
        # Test validation failure
        def validate_failure(result):
            return "world" in result.get("stdout", "")
        
        result = runner.run_command_safe(["echo", "hello"], validation_func=validate_failure)
        assert result["success"] is True
        assert result["validated"] is False
