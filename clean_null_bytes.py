#!/usr/bin/env python3
"""Clean null bytes from Phase 8 files."""

import os
import glob

def clean_file(filepath):
    """Clean null bytes from a file."""
    try:
        # Read file in binary mode
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Check if null bytes exist
        if b'\x00' in data:
            print(f"Cleaning null bytes from {filepath}...")
            # Remove null bytes
            cleaned_data = data.replace(b'\x00', b'')
            
            # Write back cleaned data
            with open(filepath, 'wb') as f:
                f.write(cleaned_data)
            
            print(f"✅ Cleaned {filepath}")
            return True
        else:
            print(f"✅ {filepath} - No null bytes found")
            return False
            
    except Exception as e:
        print(f"❌ Error cleaning {filepath}: {e}")
        return False

def main():
    """Clean all Phase 8 Python files."""
    print("🧹 Cleaning null bytes from Phase 8 files...")
    print("=" * 50)
    
    # Get all Python files in src/ai_guard
    python_files = glob.glob("src/ai_guard/*.py")
    
    cleaned_count = 0
    total_count = len(python_files)
    
    for filepath in python_files:
        if clean_file(filepath):
            cleaned_count += 1
    
    print("\n" + "=" * 50)
    print(f"Cleaning complete: {cleaned_count}/{total_count} files cleaned")
    
    if cleaned_count > 0:
        print("🎉 Null bytes removed successfully!")
    else:
        print("✅ No files needed cleaning")

if __name__ == "__main__":
    main()
