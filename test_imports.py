#!/usr/bin/env python3
"""Test Phase 8 imports."""

import sys
import traceback

def test_import(module_name):
    """Test importing a module."""
    try:
        __import__(module_name)
        print(f"✅ {module_name}: Import successful")
        return True
    except Exception as e:
        print(f"❌ {module_name}: Import failed - {e}")
        traceback.print_exc()
        return False

def main():
    """Test all Phase 8 imports."""
    print("🚀 Testing Phase 8 Module Imports")
    print("=" * 50)
    
    modules = [
        "src.ai_guard.ml_integration",
        "src.ai_guard.monitoring", 
        "src.ai_guard.enterprise",
        "src.ai_guard.analytics",
        "src.ai_guard.cloud_integration",
        "src.ai_guard.advanced_security",
        "src.ai_guard.phase8_integration"
    ]
    
    success_count = 0
    for module in modules:
        if test_import(module):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Import Results: {success_count}/{len(modules)} successful")
    
    if success_count == len(modules):
        print("🎉 All Phase 8 modules imported successfully!")
        return True
    else:
        print("❌ Some modules failed to import. Check errors above.")
        return False

if __name__ == "__main__":
    main()
