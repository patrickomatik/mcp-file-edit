#!/usr/bin/env python3
"""
Prepare the project for GitHub release
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return its output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    print("🚀 Preparing MCP File Edit for release...")
    
    # Check if we're in the right directory
    if not os.path.exists("server.py"):
        print("❌ Error: server.py not found. Run from project root.")
        sys.exit(1)
    
    # Clean up Python cache
    print("🧹 Cleaning up...")
    run_command("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true")
    run_command("find . -type f -name '*.pyc' -delete 2>/dev/null || true")
    run_command("find . -type f -name '*.backup_*' -delete 2>/dev/null || true")
    
    # Check Python syntax
    print("🐍 Checking Python syntax...")
    run_command("python -m py_compile server.py")
    
    # Update git
    print("📝 Checking git status...")
    status = run_command("git status --porcelain")
    if status:
        print("⚠️  Uncommitted changes found:")
        print(status)
        response = input("Do you want to commit all changes? (y/n): ")
        if response.lower() == 'y':
            message = input("Enter commit message: ")
            run_command("git add -A")
            run_command(f'git commit -m "{message}"')
    
    # Create a release tag
    print("🏷️  Creating release tag...")
    current_tag = run_command("git describe --tags --abbrev=0 2>/dev/null || echo 'v0.0.0'")
    print(f"Current tag: {current_tag}")
    new_tag = input("Enter new version tag (e.g., v1.0.0): ")
    
    if new_tag:
        tag_message = input("Enter tag message (or press Enter for default): ")
        if not tag_message:
            tag_message = f"Release {new_tag}"
        run_command(f'git tag -a {new_tag} -m "{tag_message}"')
        print(f"✅ Created tag: {new_tag}")
    
    # Create release branch if it doesn't exist
    print("🌿 Checking release branch...")
    branches = run_command("git branch -r")
    if "origin/release" not in branches:
        print("Creating release branch...")
        run_command("git checkout -b release")
        run_command("git push -u origin release")
        run_command("git checkout main")
    
    print("\n✅ Release preparation complete!")
    print("\n📋 Next steps:")
    print("1. Push to GitHub: git push origin main --tags")
    print("2. Go to https://github.com/patrickomatik/mcp-file-edit/releases")
    print("3. Click 'Create a new release'")
    print(f"4. Select tag '{new_tag}' and create release")
    print("\n💡 Tip: Include the CHANGELOG content in the release notes")

if __name__ == "__main__":
    main()
