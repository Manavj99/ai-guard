#!/usr/bin/env python3
"""Script to check test coverage improvements."""

import subprocess
import sys
import os

def run_coverage_check():
    """Run coverage analysis on the new test files."""
    print("Running coverage analysis...")
    
    # Test files we created
    test_files = [
        "tests/unit/test_analyzer_coverage_gaps.py",
        "tests/unit/test_enhanced_testgen_comprehensive_new.py", 
        "tests/unit/test_js_ts_support_comprehensive_new.py",
        "tests/unit/test_config_comprehensive_new.py",
        "tests/unit/test_pr_annotations_simple.py"
    ]
    
    # Check which files exist
    existing_files = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_files.append(test_file)
            print(f"✓ Found: {test_file}")
        else:
            print(f"✗ Missing: {test_file}")
    
    if not existing_files:
        print("No test files found!")
        return False
    
    # Run coverage
    cmd = [
        "python", "-m", "pytest"
    ] + existing_files + [
        "--cov=src/ai_guard",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v"
    ]
    
    print(f"\nRunning: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        print("\n" + "="*50)
        print("COVERAGE RESULTS:")
        print("="*50)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nExit code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Test execution timed out!")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_coverage_check()
    sys.exit(0 if success else 1)
