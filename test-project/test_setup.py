#!/usr/bin/env python3
"""Test script to verify AI-Guard test project setup."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (missing)")
        return False


def main():
    """Main test function."""
    print("🧪 AI-Guard Test Project Setup Verification")
    print("=" * 50)

    # Check current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")

    # Check project structure
    print("\n📋 Checking project structure...")
    required_files = [
        ("src/sample_app/__init__.py", "Sample app init file"),
        ("src/sample_app/calculator.py", "Calculator module"),
        ("tests/test_calculator.py", "Calculator tests"),
        ("pyproject.toml", "Project configuration"),
        ("requirements.txt", "Dependencies file"),
        ("Makefile", "Build commands"),
        (".github/workflows/test-ai-guard.yml", "GitHub Actions workflow"),
        (".bandit", "Security config"),
        (".flake8", "Linting config"),
    ]

    structure_ok = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            structure_ok = False

    if not structure_ok:
        print("\n❌ Project structure verification failed!")
        return False

    print("\n✅ Project structure verification passed!")

    # Check Python environment
    print("\n🐍 Checking Python environment...")
    if not run_command("python --version", "Python version check"):
        return False

    # Check if we can import the sample app
    print("\n📦 Testing sample app import...")
    try:
        sys.path.insert(0, str(Path("src")))
        from sample_app.calculator import Calculator
        calc = Calculator()
        result = calc.add(2, 3)
        print(f"✅ Sample app import successful (2 + 3 = {result})")
    except ImportError as e:
        print(f"❌ Sample app import failed: {e}")
        return False

    # Check if development dependencies are available
    print("\n🔧 Checking development dependencies...")
    deps_to_check = ["pytest", "flake8", "mypy", "bandit"]
    deps_ok = True

    for dep in deps_to_check:
        try:
            result = subprocess.run(
                f"python -c 'import {dep}'",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {dep} available")
            else:
                print(f"⚠️ {dep} not available (run 'make install' to install)")
                deps_ok = False
        except Exception:
            print(f"⚠️ {dep} check failed")
            deps_ok = False

    # Check if AI-Guard is available
    print("\n🎯 Checking AI-Guard availability...")
    try:
        result = subprocess.run(
            "ai-guard --help",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ AI-Guard is available")
            ai_guard_available = True
        else:
            print("⚠️ AI-Guard not available (install it first)")
            ai_guard_available = False
    except Exception:
        print("⚠️ AI-Guard check failed")
        ai_guard_available = False

    # Run basic tests if dependencies are available
    if deps_ok:
        print("\n🧪 Running basic tests...")
        if not run_command("python -m pytest tests/ --collect-only", "Test discovery"):
            print("⚠️ Test discovery failed, but continuing...")

        if not run_command("flake8 src --count", "Linting check"):
            print("⚠️ Linting failed, but continuing...")

        if not run_command("mypy src --ignore-missing-imports", "Type checking"):
            print("⚠️ Type checking failed, but continuing...")

    # Test AI-Guard if available
    if ai_guard_available:
        print("\n🎯 Testing AI-Guard functionality...")
        if not run_command(
            "ai-guard check --skip-tests --report-format json --report-path test-setup.json",
            "AI-Guard quality gates"
        ):
            print("⚠️ AI-Guard test failed, but continuing...")

    # Final summary
    print("\n📊 Setup Verification Summary")
    print("=" * 50)
    print(f"✅ Project structure: {'PASS' if structure_ok else 'FAIL'}")
    print("✅ Python environment: PASS")
    print("✅ Sample app import: PASS")
    print(f"✅ Development deps: {'PASS' if deps_ok else 'PARTIAL'}")
    print(f"✅ AI-Guard: {'PASS' if ai_guard_available else 'NOT AVAILABLE'}")

    if structure_ok and deps_ok:
        print("\n🎉 Setup verification completed successfully!")
        print("\nNext steps:")
        print("1. Run 'make install' to install dependencies")
        print("2. Run 'make test' to run tests")
        print("3. Run 'make ai-guard-test' to test AI-Guard")
        print("4. Run 'make demo' to see the sample app in action")
        return True
    else:
        print("\n⚠️ Setup verification completed with issues.")
        print("Please resolve the issues above before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
