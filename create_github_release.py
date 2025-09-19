#!/usr/bin/env python3
"""
GitHub Release Creation Script for AI Guard v0.1.0-beta

This script helps create a GitHub release with the built packages.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def check_git_status():
    """Check if we're in a git repository and if there are uncommitted changes."""
    print("🔍 Checking git status...")
    
    # Check if we're in a git repo
    result = run_command("git status", check=False)
    if result.returncode != 0:
        print("❌ Not in a git repository. Please run this from the ai-guard directory.")
        sys.exit(1)
    
    # Check for uncommitted changes
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("⚠️  Warning: You have uncommitted changes.")
        print("Consider committing them before creating a release.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Release cancelled.")
            sys.exit(0)

def create_git_tag():
    """Create a git tag for the release."""
    print("🏷️  Creating git tag...")
    
    tag_name = "v0.1.0-beta"
    
    # Check if tag already exists
    result = run_command(f"git tag -l {tag_name}", check=False)
    if tag_name in result.stdout:
        print(f"⚠️  Tag {tag_name} already exists.")
        response = input("Delete and recreate? (y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d {tag_name}")
        else:
            print("Using existing tag.")
            return tag_name
    
    # Create the tag
    run_command(f"git tag -a {tag_name} -m 'Release {tag_name} - Beta version of AI Guard'")
    print(f"✅ Created tag: {tag_name}")
    return tag_name

def push_tag(tag_name):
    """Push the tag to GitHub."""
    print("📤 Pushing tag to GitHub...")
    
    # Check if we have a remote
    result = run_command("git remote -v", check=False)
    if not result.stdout.strip():
        print("❌ No git remotes found. Please add a GitHub remote.")
        sys.exit(1)
    
    # Push the tag
    run_command(f"git push origin {tag_name}")
    print(f"✅ Pushed tag {tag_name} to GitHub")

def check_packages():
    """Check if the release packages exist."""
    print("📦 Checking release packages...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ dist/ directory not found. Please run 'python -m build' first.")
        sys.exit(1)
    
    wheel_file = dist_dir / "smart_ai_guard-0.1.0-py3-none-any.whl"
    source_file = dist_dir / "smart_ai_guard-0.1.0.tar.gz"
    
    if not wheel_file.exists():
        print(f"❌ Wheel package not found: {wheel_file}")
        sys.exit(1)
    
    if not source_file.exists():
        print(f"❌ Source package not found: {source_file}")
        sys.exit(1)
    
    print("✅ Release packages found:")
    print(f"  - {wheel_file}")
    print(f"  - {source_file}")

def create_github_release():
    """Create the GitHub release using GitHub CLI or provide instructions."""
    print("🚀 Creating GitHub release...")
    
    # Check if GitHub CLI is available
    result = run_command("gh --version", check=False)
    if result.returncode == 0:
        print("✅ GitHub CLI found. Creating release...")
        
        # Read release notes
        with open("RELEASE_NOTES_v0.1.0-beta.md", "r", encoding="utf-8") as f:
            release_notes = f.read()
        
        # Create release
        cmd = f'''gh release create v0.1.0-beta \\
            --title "AI Guard v0.1.0-beta - Smart Code Quality Gatekeeper" \\
            --notes-file RELEASE_NOTES_v0.1.0-beta.md \\
            dist/smart_ai_guard-0.1.0-py3-none-any.whl \\
            dist/smart_ai_guard-0.1.0.tar.gz'''
        
        run_command(cmd)
        print("✅ GitHub release created successfully!")
        
    else:
        print("⚠️  GitHub CLI not found. Please create the release manually:")
        print("\n" + "="*60)
        print("MANUAL RELEASE INSTRUCTIONS")
        print("="*60)
        print("1. Go to: https://github.com/ai-guard/ai-guard/releases/new")
        print("2. Click 'Choose a tag' and select 'v0.1.0-beta'")
        print("3. Set release title: 'AI Guard v0.1.0-beta - Smart Code Quality Gatekeeper'")
        print("4. Copy the contents of RELEASE_NOTES_v0.1.0-beta.md as the description")
        print("5. Upload these files:")
        print("   - dist/smart_ai_guard-0.1.0-py3-none-any.whl")
        print("   - dist/smart_ai_guard-0.1.0.tar.gz")
        print("6. Check 'Set as the latest release' if this is your first release")
        print("7. Click 'Publish release'")
        print("="*60)

def main():
    """Main function to create the GitHub release."""
    print("🎉 AI Guard v0.1.0-beta Release Creation")
    print("=" * 50)
    
    # Check prerequisites
    check_git_status()
    check_packages()
    
    # Create and push tag
    tag_name = create_git_tag()
    push_tag(tag_name)
    
    # Create GitHub release
    create_github_release()
    
    print("\n🎉 Release process completed!")
    print("Check your GitHub repository for the new release.")

if __name__ == "__main__":
    main()
