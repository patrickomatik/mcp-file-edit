#!/usr/bin/env python3
"""
Test script for enhanced search functionality
"""
import asyncio
import sys
sys.path.insert(0, '.')

from server import mcp, search_files, list_files, replace_in_files, BASE_DIR

async def test_search():
    print("Testing search_files with depth limit...")
    
    # Test 1: Search with max_depth=1
    result = await search_files(
        pattern="def",
        path=".",
        file_pattern="*.py",
        recursive=True,
        max_depth=1,
        timeout=5.0
    )
    
    print(f"Search completed: {result['completed']}")
    print(f"Files searched: {result['files_searched']}")
    print(f"Timeout occurred: {result['timeout_occurred']}")
    if result['error']:
        print(f"Error: {result['error']}")
    print(f"Found {len(result['results'])} files with matches")
    
    # Test 2: Test timeout (using current directory with very short timeout)
    print("\nTesting search with very short timeout...")
    result = await search_files(
        pattern="import",
        path="../",  # Parent directory
        file_pattern="*.py",
        recursive=True,
        max_depth=2,
        timeout=0.01  # Very short timeout
    )
    
    print(f"Search completed: {result['completed']}")
    print(f"Timeout occurred: {result['timeout_occurred']}")
    if result['error']:
        print(f"Error: {result['error']}")

async def test_list():
    print("\n\nTesting list_files with depth limit...")
    
    result = await list_files(
        path=".",
        pattern="*.py",
        recursive=True,
        max_depth=2
    )
    
    print(f"Found {len(result)} files")
    for file_info in result[:5]:  # Show first 5
        print(f"  - {file_info['name']} ({file_info['type']})")

async def test_replace():
    print("\n\nTesting replace_in_files with timeout...")
    
    # Create a test file
    with open('test_replace.txt', 'w') as f:
        f.write('This is a test file.\nReplace this test.\nAnother test line.')
    
    result = await replace_in_files(
        search="test",
        replace="example",
        path="test_replace.txt",
        timeout=5.0
    )
    
    print(f"Replace completed: {result['completed']}")
    print(f"Files processed: {result['files_processed']}")
    if result['results']:
        print(f"Replacements made: {result['results'][0]['replacements']}")
    
    # Clean up
    import os
    os.remove('test_replace.txt')

if __name__ == "__main__":
    asyncio.run(test_search())
    asyncio.run(test_list())
    asyncio.run(test_replace())
