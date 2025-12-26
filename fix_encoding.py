#!/usr/bin/env python3
"""Fix encoding issues in Phase 8 files."""

import os
import glob
import shutil

def fix_file_encoding(filepath):
    """Fix encoding issues in a file."""
    try:
        # Create backup
        backup_path = filepath + '.backup'
        shutil.copy2(filepath, backup_path)
        
        # Try different encodings to read the file
        encodings = ['utf-8', 'utf-16', 'utf-32', 'latin-1', 'cp1252']
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                used_encoding = encoding
                print(f"Successfully read {filepath} with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"❌ Could not read {filepath} with any encoding")
            return False
        
        # Clean the content (remove any remaining null bytes or BOM)
        content = content.replace('\x00', '')
        if content.startswith('\ufeff'):
            content = content[1:]  # Remove BOM
        
        # Write back with UTF-8 encoding
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed encoding for {filepath} (was {used_encoding})")
        
        # Remove backup if successful
        os.remove(backup_path)
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        # Restore backup if it exists
        if os.path.exists(backup_path):
            shutil.move(backup_path, filepath)
        return False

def main():
    """Fix encoding for all Phase 8 Python files."""
    print("🔧 Fixing encoding issues in Phase 8 files...")
    print("=" * 50)
    
    # Get all Python files in src/ai_guard
    python_files = glob.glob("src/ai_guard/*.py")
    
    fixed_count = 0
    total_count = len(python_files)
    
    for filepath in python_files:
        if fix_file_encoding(filepath):
            fixed_count += 1
    
    print("\n" + "=" * 50)
    print(f"Encoding fix complete: {fixed_count}/{total_count} files fixed")
    
    if fixed_count > 0:
        print("🎉 Encoding issues resolved successfully!")
    else:
        print("✅ No files needed encoding fixes")

if __name__ == "__main__":
    main()
