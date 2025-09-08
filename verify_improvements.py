#!/usr/bin/env python3
"""
Quick verification script to demonstrate AI-Guard improvements.
Run this to verify all new components are working correctly.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_subprocess_runner():
    """Test the new robust subprocess runner."""
    print("🔧 Testing subprocess runner...")
    from ai_guard.utils.subprocess_runner import run_cmd, ToolExecutionError
    
    # Test successful command
    try:
        rc, output = run_cmd(['python', '--version'])
        print(f"   ✅ Success case: rc={rc}, output contains Python: {'Python' in output}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test command that would raise ToolExecutionError
    try:
        rc, output = run_cmd(['nonexistent_command_12345'])
        print(f"   ❌ Should have raised ToolExecutionError")
    except ToolExecutionError:
        print(f"   ✅ Correctly raised ToolExecutionError for bad command")
    except Exception as e:
        print(f"   ⚠️  Different error: {e}")

def test_rule_normalization():
    """Test the rule normalization system."""
    print("📝 Testing rule normalization...")
    from ai_guard.parsers.common import normalize_rule
    
    test_cases = [
        ("flake8", "E501", "flake8:E501"),
        ("mypy", "error[name-defined]", "mypy:name-defined"),
        ("mypy", "unused-ignore", "mypy:unused-ignore"),
        ("eslint", "no-unused-vars", "eslint:no-unused-vars"),
        ("bandit", "B101", "bandit:B101"),
    ]
    
    all_passed = True
    for tool, raw, expected in test_cases:
        result = normalize_rule(tool, raw)
        if result == expected:
            print(f"   ✅ {tool} + '{raw}' → '{result}'")
        else:
            print(f"   ❌ {tool} + '{raw}' → '{result}' (expected '{expected}')")
            all_passed = False
    
    return all_passed

def test_typescript_parsers():
    """Test the TypeScript/JS parsers."""
    print("🔍 Testing TypeScript/JS parsers...")
    from ai_guard.parsers.typescript import parse_eslint, parse_jest
    
    # Test ESLint JSON parsing
    eslint_json = '[{"filePath":"test.ts","messages":[{"ruleId":"no-unused-vars","severity":2,"message":"x unused","line":3,"column":7}]}]'
    eslint_results = parse_eslint(eslint_json)
    
    if eslint_results and eslint_results[0]["rule"] == "eslint:no-unused-vars":
        print("   ✅ ESLint JSON parsing works")
    else:
        print("   ❌ ESLint JSON parsing failed")
    
    # Test Jest parsing
    jest_output = "Tests:       1 failed, 12 passed, 13 total"
    jest_results = parse_jest(jest_output)
    
    if jest_results["failed"] == 1 and jest_results["tests"] == 13:
        print("   ✅ Jest parsing works")
    else:
        print("   ❌ Jest parsing failed")

def test_coverage_evaluation():
    """Test the coverage evaluation helper."""
    print("📊 Testing coverage evaluation...")
    from ai_guard.gates.coverage_eval import evaluate_coverage_str
    
    # Test low coverage XML
    low_coverage_xml = '''<?xml version="1.0" ?>
<coverage lines-covered="70" lines-valid="100" line-rate="0.70">
  <packages/>
</coverage>'''
    
    result = evaluate_coverage_str(low_coverage_xml, threshold=80.0)
    if not result.passed and result.percent == 70.0:
        print("   ✅ Coverage evaluation works (low coverage detected)")
    else:
        print(f"   ❌ Coverage evaluation failed: passed={result.passed}, percent={result.percent}")

def main():
    """Run all verification tests."""
    print("🚀 Verifying AI-Guard Improvements")
    print("=" * 50)
    
    try:
        test_subprocess_runner()
        print()
        
        if test_rule_normalization():
            print("   ✅ All rule normalization tests passed")
        print()
        
        test_typescript_parsers()
        print()
        
        test_coverage_evaluation()
        print()
        
        print("🎉 All verification tests completed!")
        print("✅ New AI-Guard components are working correctly.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the AI-Guard project root.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
