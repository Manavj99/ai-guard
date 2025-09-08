#!/usr/bin/env python3
"""Run comprehensive coverage improvement tests and measure results."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main function to run coverage improvement tests."""
    print("AI-Guard Coverage Improvement Test Runner")
    print("="*60)
    
    # List of new comprehensive test files
    new_test_files = [
        "tests/unit/test_main_comprehensive_coverage.py",
        "tests/unit/test_analyzer_comprehensive_coverage_new.py", 
        "tests/unit/test_diff_parser_comprehensive_coverage.py",
        "tests/unit/test_config_comprehensive_coverage_new.py",
        "tests/unit/test_report_comprehensive_coverage.py"
    ]
    
    # Check if test files exist
    missing_files = []
    for test_file in new_test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"Warning: Missing test files: {missing_files}")
        new_test_files = [f for f in new_test_files if f not in missing_files]
    
    if not new_test_files:
        print("No test files found to run!")
        return 1
    
    print(f"Found {len(new_test_files)} test files to run:")
    for test_file in new_test_files:
        print(f"  - {test_file}")
    
    # Run individual test files
    all_passed = True
    for test_file in new_test_files:
        cmd = f"python -m pytest {test_file} -v --tb=short"
        success = run_command(cmd, f"Testing {test_file}")
        if not success:
            all_passed = False
            print(f"❌ Tests failed for {test_file}")
        else:
            print(f"✅ Tests passed for {test_file}")
    
    # Run all new tests together
    if new_test_files:
        test_files_str = " ".join(new_test_files)
        cmd = f"python -m pytest {test_files_str} -v --tb=short"
        success = run_command(cmd, "Running all new comprehensive tests together")
        if not success:
            all_passed = False
            print("❌ Some tests failed when run together")
        else:
            print("✅ All new tests passed when run together")
    
    # Run coverage analysis
    print(f"\n{'='*60}")
    print("Running coverage analysis...")
    print('='*60)
    
    # Run coverage with the new tests
    coverage_cmd = f"python -m pytest {' '.join(new_test_files)} --cov=src/ai_guard --cov-report=term-missing --cov-report=xml"
    coverage_success = run_command(coverage_cmd, "Coverage analysis with new tests")
    
    if coverage_success:
        print("✅ Coverage analysis completed successfully")
        
        # Try to read and display coverage summary
        if Path("coverage.xml").exists():
            print("\nCoverage XML report generated: coverage.xml")
        
        # Display current coverage if available
        try:
            with open("coverage.xml", "r") as f:
                content = f.read()
                if 'line-rate=' in content:
                    import re
                    match = re.search(r'line-rate="([^"]+)"', content)
                    if match:
                        coverage_percent = float(match.group(1)) * 100
                        print(f"📊 Current coverage: {coverage_percent:.1f}%")
        except Exception as e:
            print(f"Could not parse coverage: {e}")
    else:
        print("❌ Coverage analysis failed")
        all_passed = False
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    if all_passed:
        print("✅ All tests passed successfully!")
        print("📈 Coverage should be significantly improved")
        print("\nNext steps:")
        print("1. Review the coverage.xml file for detailed coverage information")
        print("2. Run the full test suite to ensure no regressions")
        print("3. Consider adding more tests for any remaining uncovered areas")
    else:
        print("❌ Some tests failed")
        print("Please review the output above and fix any issues")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
