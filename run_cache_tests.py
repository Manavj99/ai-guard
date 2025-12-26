#!/usr/bin/env python
"""Quick test runner for cache tests."""

import subprocess
import sys

def run_tests():
    """Run cache tests and show results."""
    print("Running cache comprehensive tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/test_cache_comprehensive_new.py", 
         "-v", "--tb=short", "-x"],
        capture_output=True,
        text=True
    )
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
    
    return result.returncode == 0

def check_coverage():
    """Check test coverage."""
    print("\n\nChecking coverage...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_cache_comprehensive_new.py",
         "--cov=src.ai_guard.cache",
         "--cov-report=term-missing",
         "--cov-report=term"],
        capture_output=True,
        text=True
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    # Extract coverage percentage
    lines = result.stdout.split('\n')
    for line in lines:
        if 'cache.py' in line and '%' in line:
            print(f"\nCoverage line: {line}")
        if 'TOTAL' in line and '%' in line:
            print(f"\nTotal coverage: {line}")

if __name__ == "__main__":
    print("=" * 60)
    print("Step 1: Running tests")
    print("=" * 60)
    success = run_tests()
    
    print("\n" + "=" * 60)
    print("Step 2: Checking coverage")
    print("=" * 60)
    check_coverage()
    
    sys.exit(0 if success else 1)


