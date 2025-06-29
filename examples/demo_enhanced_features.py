#!/usr/bin/env python3
"""
Demonstration of the enhanced search functionality with depth limits and timeouts
"""
import asyncio
import os
import sys
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def demonstrate_features():
    from server import search_files, list_files, replace_in_files
    
    print("=== MCP File Editor Enhanced Features Demo ===\n")
    
    # Demo 1: Search with depth limit
    print("1. Searching for 'def' in Python files (max depth = 1):")
    result = await search_files(
        pattern="def ",
        path=".",
        file_pattern="*.py",
        recursive=True,
        max_depth=1,
        timeout=10.0
    )
    
    print(f"   - Search completed: {result['completed']}")
    print(f"   - Files searched: {result['files_searched']}")
    print(f"   - Matches found: {len(result['results'])}")
    if result['results']:
        print(f"   - Example match: {result['results'][0]['file']}")
    print()
    
    # Demo 2: List files with depth limit
    print("2. Listing Python files (max depth = 2):")
    files = await list_files(
        path=".",
        pattern="*.py",
        recursive=True,
        max_depth=2
    )
    
    print(f"   - Found {len(files)} Python files")
    for f in files[:3]:
        print(f"   - {f['name']} ({f['size']} bytes)")
    print()
    
    # Demo 3: Demonstrate timeout handling
    print("3. Testing timeout handling (0.001 second timeout):")
    result = await search_files(
        pattern="import",
        path=".",
        file_pattern="*",
        recursive=True,
        max_depth=5,
        timeout=0.001  # Very short timeout to trigger timeout
    )
    
    print(f"   - Search completed: {result['completed']}")
    print(f"   - Timeout occurred: {result['timeout_occurred']}")
    if result['error']:
        print(f"   - Error message: {result['error']}")
    print(f"   - Partial results: {len(result['results'])} matches before timeout")
    
    print("\n=== Demo Complete ===")
    print("The enhanced features allow for:")
    print("- Controlled depth traversal to prevent deep recursion")
    print("- Timeout handling to prevent hanging operations")
    print("- Detailed status reporting for better error handling")
    print("- Partial results even when operations don't complete")

if __name__ == "__main__":
    asyncio.run(demonstrate_features())
