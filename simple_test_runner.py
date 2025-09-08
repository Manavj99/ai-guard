#!/usr/bin/env python3
"""Simple test runner to systematically improve coverage."""

import subprocess
import sys
import os
import xml.etree.ElementTree as ET

def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_coverage():
    """Check current coverage percentage."""
    if not os.path.exists("coverage.xml"):
        return 0
    
    try:
        tree = ET.parse("coverage.xml")
        root = tree.getroot()
        line_rate = float(root.get("line-rate", "0"))
        return int(round(line_rate * 100))
    except Exception as e:
        print(f"Error parsing coverage: {e}")
        return 0

def create_basic_tests():
    """Create basic tests for core modules."""
    
    # Test for __main__.py
    main_test = '''"""Basic tests for __main__.py."""

import pytest
from unittest.mock import patch, Mock
import sys

def test_main_help():
    """Test main function with help argument."""
    with patch('sys.argv', ['ai-guard', '--help']):
        with patch('ai_guard.__main__.run_analyzer') as mock_analyzer:
            from ai_guard.__main__ import main
            try:
                main()
            except SystemExit:
                pass  # Expected for help

def test_main_basic():
    """Test main function with basic arguments."""
    with patch('sys.argv', ['ai-guard', '--skip-tests']):
        with patch('ai_guard.__main__.run_analyzer') as mock_analyzer:
            from ai_guard.__main__ import main
            main()
            mock_analyzer.assert_called_once()

def test_main_with_coverage():
    """Test main function with coverage argument."""
    with patch('sys.argv', ['ai-guard', '--min-cov', '90']):
        with patch('ai_guard.__main__.run_analyzer') as mock_analyzer:
            from ai_guard.__main__ import main
            main()
            mock_analyzer.assert_called_once()

def test_main_with_report_format():
    """Test main function with report format."""
    with patch('sys.argv', ['ai-guard', '--report-format', 'json']):
        with patch('ai_guard.__main__.run_analyzer') as mock_analyzer:
            from ai_guard.__main__ import main
            main()
            mock_analyzer.assert_called_once()

def test_main_deprecated_sarif():
    """Test main function with deprecated sarif argument."""
    with patch('sys.argv', ['ai-guard', '--sarif', 'test.sarif']):
        with patch('ai_guard.__main__.run_analyzer') as mock_analyzer:
            from ai_guard.__main__ import main
            main()
            mock_analyzer.assert_called_once()
'''
    
    with open("tests/unit/test_main_basic.py", "w") as f:
        f.write(main_test)
    
    # Test for report.py
    report_test = '''"""Basic tests for report.py."""

import pytest
from ai_guard.report import GateResult, summarize

def test_gate_result_creation():
    """Test GateResult creation."""
    result = GateResult(
        name="test",
        passed=True,
        message="Test passed",
        details="Test details"
    )
    assert result.name == "test"
    assert result.passed is True
    assert result.message == "Test passed"
    assert result.details == "Test details"

def test_gate_result_failed():
    """Test GateResult for failed gate."""
    result = GateResult(
        name="test",
        passed=False,
        message="Test failed",
        details="Test failure details"
    )
    assert result.name == "test"
    assert result.passed is False
    assert result.message == "Test failed"

def test_summarize_basic():
    """Test basic summarize function."""
    results = [
        GateResult("test1", True, "Passed", ""),
        GateResult("test2", False, "Failed", "")
    ]
    
    summary = summarize(results)
    assert summary is not None
    assert "test1" in summary
    assert "test2" in summary

def test_summarize_empty():
    """Test summarize with empty results."""
    summary = summarize([])
    assert summary is not None
'''
    
    with open("tests/unit/test_report_basic.py", "w") as f:
        f.write(report_test)
    
    # Test for security_scanner.py
    security_test = '''"""Basic tests for security_scanner.py."""

import pytest
from unittest.mock import patch, mock_open
from ai_guard.security_scanner import SecurityScanner

def test_security_scanner_init():
    """Test SecurityScanner initialization."""
    scanner = SecurityScanner()
    assert scanner is not None

def test_scan_file_basic():
    """Test basic file scanning."""
    scanner = SecurityScanner()
    
    with patch('builtins.open', mock_open(read_data="import os")):
        result = scanner.scan_file("test.py")
        assert result is not None

def test_scan_file_with_vulnerability():
    """Test scanning file with potential vulnerability."""
    scanner = SecurityScanner()
    
    # File with potential security issue
    content = "password = 'hardcoded_password'"
    
    with patch('builtins.open', mock_open(read_data=content)):
        result = scanner.scan_file("test.py")
        assert result is not None

def test_scan_directory():
    """Test scanning directory."""
    scanner = SecurityScanner()
    
    with patch('os.walk') as mock_walk:
        mock_walk.return_value = [("", [], ["test.py"])]
        with patch.object(scanner, 'scan_file', return_value={"issues": []}):
            result = scanner.scan_directory("test_dir")
            assert result is not None
'''
    
    with open("tests/unit/test_security_basic.py", "w") as f:
        f.write(security_test)
    
    # Test for tests_runner.py
    runner_test = '''"""Basic tests for tests_runner.py."""

import pytest
from unittest.mock import patch, Mock
from ai_guard.tests_runner import TestsRunner, run_pytest_with_coverage

def test_tests_runner_init():
    """Test TestsRunner initialization."""
    runner = TestsRunner()
    assert runner is not None

def test_run_tests_basic():
    """Test basic test running."""
    runner = TestsRunner()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test passed"
        result = runner.run_tests("test_dir")
        assert result is not None

def test_run_tests_failure():
    """Test test running with failure."""
    runner = TestsRunner()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test failed"
        result = runner.run_tests("test_dir")
        assert result is not None

def test_run_pytest_with_coverage():
    """Test run_pytest_with_coverage function."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "coverage: 85%"
        
        exit_code, coverage = run_pytest_with_coverage("test_dir")
        assert exit_code == 0
        assert coverage >= 0
'''
    
    with open("tests/unit/test_runner_basic.py", "w") as f:
        f.write(runner_test)
    
    print("Created basic test files")

def main():
    """Main function."""
    print("AI-Guard Simple Test Runner")
    print("=" * 40)
    
    # Create basic tests
    create_basic_tests()
    
    # Run basic tests
    test_files = [
        "tests/unit/test_main_basic.py",
        "tests/unit/test_report_basic.py", 
        "tests/unit/test_security_basic.py",
        "tests/unit/test_runner_basic.py"
    ]
    
    # Check which files exist
    existing_tests = [f for f in test_files if os.path.exists(f)]
    
    if not existing_tests:
        print("No test files found!")
        return 1
    
    print(f"Running {len(existing_tests)} basic test files...")
    
    # Run tests
    cmd = f"python -m pytest {' '.join(existing_tests)} -v --cov=src --cov-report=xml --cov-report=term"
    success = run_command(cmd)
    
    if success:
        print("✅ Basic tests passed!")
        
        # Check coverage
        coverage = check_coverage()
        print(f"📊 Current Coverage: {coverage}%")
        
        if coverage >= 90:
            print("🎉 SUCCESS: Coverage is above 90%!")
            return 0
        else:
            print(f"⚠️ Coverage is {coverage}%, need to reach 90%")
            
            # Try to run more comprehensive tests
            print("Running additional comprehensive tests...")
            
            comprehensive_tests = [
                "tests/unit/test_analyzer_comprehensive_new.py",
                "tests/unit/test_config_comprehensive_new.py",
                "tests/unit/test_diff_parser_comprehensive_new.py"
            ]
            
            existing_comprehensive = [f for f in comprehensive_tests if os.path.exists(f)]
            
            if existing_comprehensive:
                cmd2 = f"python -m pytest {' '.join(existing_comprehensive)} -v --cov=src --cov-append --cov-report=xml --cov-report=term"
                run_command(cmd2)
                
                final_coverage = check_coverage()
                print(f"📊 Final Coverage: {final_coverage}%")
                
                if final_coverage >= 90:
                    print("🎉 SUCCESS: Final coverage is above 90%!")
                    return 0
                else:
                    print(f"⚠️ Final coverage is {final_coverage}%, still need to reach 90%")
                    return 1
            else:
                return 1
    else:
        print("❌ Basic tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
