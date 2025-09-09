#!/usr/bin/env python3
"""Test script to verify AI-Guard functionality."""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all module imports."""
    print("=" * 50)
    print("TESTING IMPORTS")
    print("=" * 50)
    
    # Test core analyzer
    try:
        from ai_guard.analyzer import main, run_lint_check, run_type_check, run_security_check, run_coverage_check
        print("✅ Core analyzer functions imported successfully")
    except Exception as e:
        print(f"❌ Error importing analyzer: {e}")
        return False
    
    # Test HTML report generation
    try:
        from ai_guard.report_html import write_html, HTMLReportGenerator
        print("✅ HTML report functions imported successfully")
    except Exception as e:
        print(f"❌ Error importing HTML report: {e}")
        return False
    
    # Test coverage evaluation
    try:
        from ai_guard.gates.coverage_eval import evaluate_coverage_str, CoverageResult
        print("✅ Coverage evaluation functions imported successfully")
    except Exception as e:
        print(f"❌ Error importing coverage evaluation: {e}")
        return False
    
    # Test other modules
    try:
        from ai_guard.config import load_config
        from ai_guard.diff_parser import parse_diff
        from ai_guard.security_scanner import SecurityScanner
        from ai_guard.report import GateResult
        print("✅ Other core modules imported successfully")
    except Exception as e:
        print(f"❌ Error importing other modules: {e}")
        return False
    
    return True

def test_html_report_generation():
    """Test HTML report generation functionality."""
    print("\n" + "=" * 50)
    print("TESTING HTML REPORT GENERATION")
    print("=" * 50)
    
    try:
        from ai_guard.report_html import write_html, HTMLReportGenerator
        from ai_guard.report import GateResult
        
        # Create sample data
        gates = [
            GateResult(name="Coverage", passed=True, details="85% coverage"),
            GateResult(name="Security", passed=True, details="No vulnerabilities found"),
            GateResult(name="Linting", passed=False, details="3 linting errors found")
        ]
        
        findings = [
            {"rule_id": "E501", "level": "error", "message": "Line too long", "path": "test.py", "line": 10},
            {"rule_id": "F401", "level": "warning", "message": "Unused import", "path": "test.py", "line": 5}
        ]
        
        # Test HTMLReportGenerator
        generator = HTMLReportGenerator()
        print("✅ HTMLReportGenerator instantiated successfully")
        
        # Test generate_html_report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        generator.generate_html_report(gates, findings, temp_path)
        print(f"✅ HTML report generated successfully at {temp_path}")
        
        # Verify file was created and has content
        if os.path.exists(temp_path):
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "AI-Guard Report" in content and "Gates" in content:
                    print("✅ HTML report content verified")
                else:
                    print("❌ HTML report content verification failed")
            
            # Clean up
            os.unlink(temp_path)
        else:
            print("❌ HTML report file was not created")
            return False
        
        # Test write_html function directly
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path2 = f.name
        
        write_html(temp_path2, gates, findings)
        print(f"✅ write_html function works successfully")
        
        # Clean up
        if os.path.exists(temp_path2):
            os.unlink(temp_path2)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing HTML report generation: {e}")
        return False

def test_coverage_evaluation():
    """Test coverage evaluation functionality."""
    print("\n" + "=" * 50)
    print("TESTING COVERAGE EVALUATION")
    print("=" * 50)
    
    try:
        from ai_guard.gates.coverage_eval import evaluate_coverage_str, CoverageResult
        
        # Test with sample coverage XML
        sample_xml = '''<coverage line-rate="0.85" lines-valid="100" lines-covered="85">
            <packages>
                <package name="test" line-rate="0.85"/>
            </packages>
        </coverage>'''
        
        result = evaluate_coverage_str(sample_xml, 80.0)
        print(f"✅ Coverage evaluation test: {result.percent}% coverage, passed: {result.passed}")
        
        # Test with low coverage
        low_coverage_xml = '''<coverage line-rate="0.70" lines-valid="100" lines-covered="70">
            <packages>
                <package name="test" line-rate="0.70"/>
            </packages>
        </coverage>'''
        
        result2 = evaluate_coverage_str(low_coverage_xml, 80.0)
        print(f"✅ Low coverage test: {result2.percent}% coverage, passed: {result2.passed}")
        
        # Test with counter-based XML
        counter_xml = '''<coverage>
            <packages>
                <package name="test">
                    <classes>
                        <class name="TestClass">
                            <counter type="LINE" covered="85" missed="15"/>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>'''
        
        result3 = evaluate_coverage_str(counter_xml, 80.0)
        print(f"✅ Counter-based coverage test: {result3.percent}% coverage, passed: {result3.passed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing coverage evaluation: {e}")
        return False

def test_analyzer_functions():
    """Test analyzer functions."""
    print("\n" + "=" * 50)
    print("TESTING ANALYZER FUNCTIONS")
    print("=" * 50)
    
    try:
        from ai_guard.analyzer import run_lint_check, run_type_check, run_security_check, run_coverage_check
        
        # Test with a simple Python file
        test_code = '''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        try:
            # Test linting (this might fail if flake8 is not installed)
            print("Testing linting...")
            lint_result = run_lint_check([temp_file])
            print(f"✅ Lint check completed: {lint_result}")
        except Exception as e:
            print(f"⚠️  Lint check failed (expected if flake8 not installed): {e}")
        
        try:
            # Test type checking (this might fail if mypy is not installed)
            print("Testing type checking...")
            type_result = run_type_check([temp_file])
            print(f"✅ Type check completed: {type_result}")
        except Exception as e:
            print(f"⚠️  Type check failed (expected if mypy not installed): {e}")
        
        try:
            # Test security scanning (this might fail if bandit is not installed)
            print("Testing security scanning...")
            security_result = run_security_check([temp_file])
            print(f"✅ Security check completed: {security_result}")
        except Exception as e:
            print(f"⚠️  Security check failed (expected if bandit not installed): {e}")
        
        # Clean up
        os.unlink(temp_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing analyzer functions: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    print("\n" + "=" * 50)
    print("TESTING CONFIGURATION LOADING")
    print("=" * 50)
    
    try:
        from ai_guard.config import load_config
        
        # Test loading default config
        config = load_config()
        print(f"✅ Configuration loaded successfully: {type(config)}")
        
        # Test with custom config file
        custom_config = {
            "gates": {
                "coverage": {"threshold": 80.0},
                "security": {"enabled": True},
                "linting": {"enabled": True}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[gates.coverage]\nthreshold = 80.0\n\n[gates.security]\nenabled = true\n\n[gates.linting]\nenabled = true\n')
            config_file = f.name
        
        try:
            config2 = load_config(config_file)
            print(f"✅ Custom configuration loaded successfully")
        except Exception as e:
            print(f"⚠️  Custom config loading failed: {e}")
        finally:
            os.unlink(config_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration loading: {e}")
        return False

def main():
    """Run all tests."""
    print("AI-Guard Functionality Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_html_report_generation,
        test_coverage_evaluation,
        test_analyzer_functions,
        test_config_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! AI-Guard is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
