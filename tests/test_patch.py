#!/usr/bin/env python3
"""
Test the patch_file functionality
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_patch():
    from server import patch_file
    
    # Create a test file
    test_content = """line 1
line 2
def old_function():
    pass
line 5
line 6
line 7
"""
    
    with open('test_patch_file.py', 'w') as f:
        f.write(test_content)
    
    print("=== Testing Patch Functionality ===\n")
    
    # Test 1: Line-based patch
    print("1. Testing line-based patch (single line):")
    result = await patch_file(
        path="test_patch_file.py",
        patches=[
            {"line": 2, "content": "# This line was patched"}
        ],
        backup=True
    )
    print(f"   Success: {result['success']}")
    print(f"   Patches applied: {result['patches_applied']}/{result['patches_total']}")
    print(f"   Changes: {result['changes'][0]}")
    print()
    
    # Test 2: Multi-line patch
    print("2. Testing multi-line patch:")
    result = await patch_file(
        path="test_patch_file.py",
        patches=[
            {
                "start_line": 3,
                "end_line": 4,
                "content": "def new_function():\\n    # Updated function\\n    return True"
            }
        ]
    )
    print(f"   Success: {result['success']}")
    print(f"   Changes: {result['changes'][0]}")
    print()
    
    # Test 3: Pattern-based patch
    print("3. Testing pattern-based patch:")
    result = await patch_file(
        path="test_patch_file.py",
        patches=[
            {
                "find": "line 5",
                "replace": "# Line 5 was replaced"
            }
        ]
    )
    print(f"   Success: {result['success']}")
    print(f"   Changes: {result['changes'][0]}")
    print()
    
    # Test 4: Context-based patch
    print("4. Testing context-based patch:")
    result = await patch_file(
        path="test_patch_file.py",
        patches=[
            {
                "context": ["# Line 5 was replaced", "line 6", "line 7"],
                "replace": ["# Line 5 was replaced", "# Line 6 modified", "# Line 7 modified"]
            }
        ]
    )
    print(f"   Success: {result['success']}")
    print(f"   Changes: {result['changes'][0]}")
    print()
    
    # Test 5: Multiple patches in one call
    print("5. Testing multiple patches:")
    result = await patch_file(
        path="test_patch_file.py",
        patches=[
            {"line": 1, "content": "# First line changed"},
            {"find": "return True", "replace": "return False"},
            {"line": 7, "content": "# Last line"}
        ]
    )
    print(f"   Success: {result['success']}")
    print(f"   Patches applied: {result['patches_applied']}/{result['patches_total']}")
    print()
    
    # Test 6: Dry run
    print("6. Testing dry run:")
    result = await patch_file(
        path="test_patch_file.py",
        patches=[
            {"line": 1, "content": "# This won't be applied"}
        ],
        dry_run=True
    )
    print(f"   Dry run: {result['dry_run']}")
    print(f"   Would apply: {result['patches_applied']} patches")
    print()
    
    # Show final file content
    print("Final file content:")
    with open('test_patch_file.py', 'r') as f:
        print(f.read())
    
    # Cleanup
    os.remove('test_patch_file.py')
    # Remove backup files
    for f in os.listdir('.'):
        if f.startswith('test_patch_file.py.backup_'):
            os.remove(f)

if __name__ == "__main__":
    asyncio.run(test_patch())
