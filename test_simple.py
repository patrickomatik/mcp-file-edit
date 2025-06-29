#!/usr/bin/env python3
"""
Simple test to verify the MCP file server works
"""
import json

def test_list_files():
    import subprocess
    import sys
    
    test_code = '''
import sys
sys.path.insert(0, ".")
from server import mcp

# Get the list_files tool
list_files_tool = None
for tool in mcp._tools.values():
    if tool.name == "list_files":
        list_files_tool = tool
        break

# Call it with our new parameters
import asyncio
result = asyncio.run(list_files_tool.fn(path=".", pattern="*.py", recursive=True, max_depth=1))
print(f"Found {len(result)} files")
for f in result[:3]:
    print(f"  {f['name']} - {f['type']}")
'''
    
    result = subprocess.run([sys.executable, "-c", test_code], 
                          capture_output=True, text=True, cwd=".")
    print("List files test:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
def test_search_files():
    import subprocess
    import sys
    
    test_code = '''
import sys
sys.path.insert(0, ".")
from server import mcp

# Get the search_files tool  
search_files_tool = None
for tool in mcp._tools.values():
    if tool.name == "search_files":
        search_files_tool = tool
        break

# Call it with our new parameters
import asyncio
result = asyncio.run(search_files_tool.fn(
    pattern="def", 
    path=".", 
    file_pattern="*.py",
    recursive=True,
    max_depth=1,
    timeout=5.0
))
print(f"Search completed: {result['completed']}")
print(f"Files searched: {result['files_searched']}")
print(f"Results found: {len(result['results'])}")
'''
    
    result = subprocess.run([sys.executable, "-c", test_code], 
                          capture_output=True, text=True, cwd=".")
    print("\nSearch files test:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

if __name__ == "__main__":
    test_list_files()
    test_search_files()
