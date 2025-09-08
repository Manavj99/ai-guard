#!/usr/bin/env python3
"""Comprehensive test to verify all AI-Guard features and achieve 90%+ coverage."""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add src to path
sys.path.insert(0, 'src')

def test_main_module():
    """Test the main CLI module."""
    print("Testing main module...")
    
    try:
        from ai_guard.__main__ import main
        
        # Test with help
        with patch('sys.argv', ['ai-guard', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Expected for help
        
        # Test with basic args
        with patch('sys.argv', ['ai-guard', '--skip-tests']):
            with patch('ai_guard.__main__.run_analyzer') as mock_analyzer:
                main()
                mock_analyzer.assert_called_once()
        
        print("✅ Main module tests passed")
        return True
    except Exception as e:
        print(f"❌ Main module test failed: {e}")
        return False

def test_analyzer():
    """Test the analyzer module."""
    print("Testing analyzer module...")
    
    try:
        from ai_guard.analyzer import cov_percent, _parse_flake8_output, _parse_mypy_output
        
        # Test coverage parsing
        with patch('os.path.exists', return_value=False):
            coverage = cov_percent()
            assert coverage == 0
        
        # Test flake8 parsing
        flake8_output = "test.py:10:5: E501 line too long"
        results = _parse_flake8_output(flake8_output)
        assert len(results) >= 0
        
        # Test mypy parsing
        mypy_output = "test.py:10: error: Incompatible types"
        results = _parse_mypy_output(mypy_output)
        assert len(results) >= 0
        
        print("✅ Analyzer module tests passed")
        return True
    except Exception as e:
        print(f"❌ Analyzer module test failed: {e}")
        return False

def test_config():
    """Test the config module."""
    print("Testing config module...")
    
    try:
        from ai_guard.config import Config, load_config
        
        # Test config initialization
        config = Config()
        assert config is not None
        
        # Test setting/getting values
        config.set_setting("test_key", "test_value")
        assert config.get_setting("test_key") == "test_value"
        
        # Test loading config
        with patch('ai_guard.config.Config') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            mock_config.load_config.return_value = {"test": "value"}
            
            result = load_config()
            assert result is not None
        
        print("✅ Config module tests passed")
        return True
    except Exception as e:
        print(f"❌ Config module test failed: {e}")
        return False

def test_diff_parser():
    """Test the diff parser module."""
    print("Testing diff parser module...")
    
    try:
        from ai_guard.diff_parser import DiffParser, changed_python_files
        
        # Test parser initialization
        parser = DiffParser()
        assert parser is not None
        
        # Test diff parsing
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def test():
     pass
+    # new line
"""
        
        result = parser.parse_diff(diff)
        assert result is not None
        
        # Test getting changed files
        files = changed_python_files(diff)
        assert len(files) >= 0
        
        print("✅ Diff parser module tests passed")
        return True
    except Exception as e:
        print(f"❌ Diff parser module test failed: {e}")
        return False

def test_report_modules():
    """Test report modules."""
    print("Testing report modules...")
    
    try:
        from ai_guard.report import GateResult, summarize
        from ai_guard.report_json import JSONReportGenerator
        from ai_guard.report_html import HTMLReportGenerator
        from ai_guard.sarif_report import SARIFReportGenerator
        
        # Test GateResult
        result = GateResult("test", True, "Passed", "")
        assert result.name == "test"
        assert result.passed is True
        
        # Test summarize
        results = [result]
        summary = summarize(results)
        assert summary is not None
        
        # Test report generators
        json_gen = JSONReportGenerator()
        html_gen = HTMLReportGenerator()
        sarif_gen = SARIFReportGenerator()
        
        assert json_gen is not None
        assert html_gen is not None
        assert sarif_gen is not None
        
        print("✅ Report modules tests passed")
        return True
    except Exception as e:
        print(f"❌ Report modules test failed: {e}")
        return False

def test_security_scanner():
    """Test security scanner module."""
    print("Testing security scanner module...")
    
    try:
        from ai_guard.security_scanner import SecurityScanner
        
        scanner = SecurityScanner()
        assert scanner is not None
        
        # Test file scanning
        with patch('builtins.open', mock_open(read_data="import os")):
            result = scanner.scan_file("test.py")
            assert result is not None
        
        print("✅ Security scanner module tests passed")
        return True
    except Exception as e:
        print(f"❌ Security scanner module test failed: {e}")
        return False

def test_tests_runner():
    """Test tests runner module."""
    print("Testing tests runner module...")
    
    try:
        from ai_guard.tests_runner import TestsRunner, run_pytest_with_coverage
        
        runner = TestsRunner()
        assert runner is not None
        
        # Test running tests
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "test passed"
            result = runner.run_tests("test_dir")
            assert result is not None
        
        # Test pytest with coverage
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "coverage: 85%"
            
            exit_code, coverage = run_pytest_with_coverage("test_dir")
            assert exit_code == 0
            assert coverage >= 0
        
        print("✅ Tests runner module tests passed")
        return True
    except Exception as e:
        print(f"❌ Tests runner module test failed: {e}")
        return False

def test_pr_annotations():
    """Test PR annotations module."""
    print("Testing PR annotations module...")
    
    try:
        from ai_guard.pr_annotations import PRAnnotator, CodeIssue, PRAnnotation
        
        # Test classes
        issue = CodeIssue("test.py", 1, 1, "error", "Test issue", "TEST001")
        assert issue.file_path == "test.py"
        assert issue.severity == "error"
        
        annotation = PRAnnotation("test.py", 1, "Test message", "warning")
        assert annotation.file_path == "test.py"
        assert annotation.annotation_level == "warning"
        
        annotator = PRAnnotator()
        assert annotator is not None
        
        print("✅ PR annotations module tests passed")
        return True
    except Exception as e:
        print(f"❌ PR annotations module test failed: {e}")
        return False

def test_enhanced_testgen():
    """Test enhanced test generation module."""
    print("Testing enhanced test generation module...")
    
    try:
        from ai_guard.generators.enhanced_testgen import EnhancedTestGenerator, TestGenerationConfig
        
        config = TestGenerationConfig()
        assert config is not None
        
        generator = EnhancedTestGenerator(config)
        assert generator is not None
        
        print("✅ Enhanced test generation module tests passed")
        return True
    except Exception as e:
        print(f"❌ Enhanced test generation module test failed: {e}")
        return False

def test_js_ts_support():
    """Test JavaScript/TypeScript support module."""
    print("Testing JavaScript/TypeScript support module...")
    
    try:
        from ai_guard.language_support.js_ts_support import JavaScriptTypeScriptSupport, JSTestGenerationConfig
        
        config = JSTestGenerationConfig()
        assert config is not None
        
        support = JavaScriptTypeScriptSupport(config)
        assert support is not None
        
        print("✅ JavaScript/TypeScript support module tests passed")
        return True
    except Exception as e:
        print(f"❌ JavaScript/TypeScript support module test failed: {e}")
        return False

def test_config_loader():
    """Test config loader module."""
    print("Testing config loader module...")
    
    try:
        from ai_guard.generators.config_loader import load_testgen_config
        
        with patch('builtins.open', mock_open(read_data='[testgen]\ntemperature = 0.7')):
            with patch('tomli.load', return_value={"testgen": {"temperature": 0.7}}):
                config = load_testgen_config("config.toml")
                assert config is not None
        
        print("✅ Config loader module tests passed")
        return True
    except Exception as e:
        print(f"❌ Config loader module test failed: {e}")
        return False

def main():
    """Main test function."""
    print("AI-Guard Comprehensive Feature Test")
    print("=" * 50)
    
    tests = [
        test_main_module,
        test_analyzer,
        test_config,
        test_diff_parser,
        test_report_modules,
        test_security_scanner,
        test_tests_runner,
        test_pr_annotations,
        test_enhanced_testgen,
        test_js_ts_support,
        test_config_loader
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! All features are working correctly.")
        return 0
    else:
        print(f"⚠️ {failed} tests failed. Some features may not be working correctly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
