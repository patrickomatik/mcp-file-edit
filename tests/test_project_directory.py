#!/usr/bin/env python3
"""
Test the project directory functionality
"""
import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_project_directory():
    # Import from the new server
    from server_with_project import (
        set_project_directory, get_project_directory,
        list_files, read_file, write_file, create_file,
        search_files, patch_file, BASE_DIR
    )
    
    # Create a test project within BASE_DIR
    project_dir = BASE_DIR / "test_project_temp"
    
    try:
        # Clean up if exists
        if project_dir.exists():
            shutil.rmtree(project_dir)
            
        project_dir.mkdir()
        
        # Create project structure
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "docs").mkdir()
        
        # Create some files
        (project_dir / "README.md").write_text("# Test Project\nThis is a test.")
        (project_dir / "src" / "main.py").write_text("def main():\n    print('Hello')")
        (project_dir / "src" / "utils.py").write_text("def helper():\n    return 42")
        (project_dir / "tests" / "test_main.py").write_text("def test_main():\n    pass")
        
        print("=== Testing Project Directory Functionality ===\n")
        
        # Test 1: Get project directory when not set
        print("1. Get project directory (not set):")
        result = await get_project_directory()
        print(f"   Result: {result}")
        print()
        
        # Test 2: Set project directory
        print("2. Set project directory:")
        result = await set_project_directory("test_project_temp")
        print(f"   Project directory: {result['project_directory']}")
        print(f"   Relative to base: {result['relative_to_base']}")
        print()
        
        # Test 3: Get project directory after setting
        print("3. Get project directory (after setting):")
        result = await get_project_directory()
        print(f"   Project directory: {result['project_directory']}")
        print()
        
        # Test 4: List files with relative path
        print("4. List files in 'src' (relative path):")
        files = await list_files(path="src", pattern="*.py")
        for f in files:
            print(f"   - {f['name']}")
        print()
        
        # Test 5: Read file with relative path
        print("5. Read file 'src/main.py' (relative path):")
        result = await read_file(path="src/main.py")
        print(f"   Content: {result['content'][:30]}...")
        print()
        
        # Test 6: Create file with relative path
        print("6. Create file 'src/new_file.py' (relative path):")
        await create_file(path="src/new_file.py", content="# New file")
        files = await list_files(path="src", pattern="new_file.py")
        print(f"   Created: {files[0]['name'] if files else 'Failed'}")
        print()
        
        # Test 7: Search files with relative path
        print("7. Search for 'def' in project (relative path '.'):")
        result = await search_files(pattern="def", path=".", recursive=True)
        print(f"   Found matches in {len(result['results'])} files")
        for r in result['results']:
            print(f"   - {r['file']}: {len(r['matches'])} matches")
        print()
        
        # Test 8: Patch file with relative path
        print("8. Patch file 'src/main.py' (relative path):")
        result = await patch_file(
            path="src/main.py",
            patches=[
                {"line": 2, "content": "    print('Hello, World!')"}
            ]
        )
        print(f"   Success: {result['success']}")
        print(f"   Patches applied: {result['patches_applied']}")
        print()
        
        # Test 9: Write file with relative path
        print("9. Write file 'docs/notes.txt' (relative path):")
        await write_file(path="docs/notes.txt", content="Project notes here")
        result = await read_file(path="docs/notes.txt")
        print(f"   Written content: {result['content']}")
        print()
        
        # Test 10: Try to use absolute path (should still work)
        print("10. Use absolute path:")
        abs_path = str(project_dir / "absolute_test.txt")
        await write_file(path=abs_path, content="Absolute path test")
        result = await read_file(path=abs_path)
        print(f"   Absolute path works: {result['content']}")
        
        print("\n=== Test Complete ===")
        print("Project directory feature allows:")
        print("- Setting a project context with set_project_directory")
        print("- All relative paths are resolved from project directory")
        print("- Absolute paths still work as before")
        print("- Simplifies working within a specific project")
        
    finally:
        # Cleanup
        if project_dir.exists():
            shutil.rmtree(project_dir)

if __name__ == "__main__":
    asyncio.run(test_project_directory())
