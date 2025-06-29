#!/usr/bin/env python3
"""
Test the code analysis functionality
"""
import asyncio
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_code_analysis():
    # Import the tools
    from server import (
        list_functions, get_function_at_line, 
        get_code_structure, search_functions,
        set_project_directory, create_file
    )
    
    # Create test files
    print("=== Testing Code Analysis Features ===\n")
    
    # Set up test directory
    await set_project_directory(".")
    
    # Create a test Python file
    test_py_content = '''"""Test module for code analysis"""
import os
import sys
from typing import List, Optional

def simple_function():
    """A simple function"""
    return 42

async def async_function(name: str) -> str:
    """An async function with type hints
    
    Args:
        name: The name to greet
        
    Returns:
        A greeting string
    """
    return f"Hello, {name}!"

class TestClass:
    """A test class"""
    
    def __init__(self, value: int = 0):
        self.value = value
    
    def method(self) -> int:
        """A class method"""
        return self.value * 2
    
    @staticmethod
    def static_method():
        """A static method"""
        return "static"

def function_with_decorators():
    """Function with decorators"""
    @property
    def inner():
        return "inner"
    return inner
'''
    
    await create_file("test_analysis.py", test_py_content)
    
    # Test 1: List all functions
    print("1. List all functions in test_analysis.py:")
    functions = await list_functions("test_analysis.py")
    for func in functions:
        print(f"   - {func['signature']} at line {func['line_start']}")
        if func.get('is_method'):
            print(f"     (method of {func['class_name']})")
    print()
    
    # Test 2: Get function at specific line
    print("2. Get function at line 15:")
    func = await get_function_at_line("test_analysis.py", 15)
    if func:
        print(f"   Found: {func['name']} ({func['line_start']}-{func['line_end']})")
        if func.get('docstring'):
            print(f"   Docstring: {func['docstring'][:50]}...")
    print()
    
    # Test 3: Get code structure
    print("3. Get code structure:")
    structure = await get_code_structure("test_analysis.py")
    print(f"   Language: {structure['language']}")
    print(f"   Lines: {structure['lines']}")
    print(f"   Imports: {len(structure.get('imports', []))}")
    print(f"   Classes: {len(structure.get('classes', []))}")
    print(f"   Functions: {len(structure.get('functions', []))}")
    
    if structure.get('classes'):
        for cls in structure['classes']:
            print(f"   - Class {cls['name']} with {len(cls['methods'])} methods")
    print()
    
    # Create another test file
    test_js_content = '''// JavaScript test file
function regularFunction(a, b) {
    return a + b;
}

const arrowFunction = (x) => x * 2;

async function asyncFunction() {
    return await Promise.resolve(42);
}

class MyClass {
    constructor() {
        this.value = 0;
    }
    
    method() {
        return this.value;
    }
}
'''
    
    await create_file("test_analysis.js", test_js_content)
    
    # Test 4: List JavaScript functions
    print("4. List functions in JavaScript file:")
    js_functions = await list_functions("test_analysis.js", "javascript")
    for func in js_functions:
        print(f"   - {func['name']} at line {func['line_start']}")
    print()
    
    # Test 5: Search for functions
    print("5. Search for functions matching 'function':")
    results = await search_functions("function", ".", "*.py", max_depth=2)
    print(f"   Found {results['total_functions']} matching functions in {results['files_searched']} files")
    for result in results['results']:
        print(f"   In {result['file']}:")
        for func in result['functions']:
            print(f"     - {func['name']}")
    print()
    
    # Test 6: Search with pattern
    print("6. Search for async functions:")
    results = await search_functions("async", ".", "*.py")
    for result in results['results']:
        for func in result['functions']:
            if func.get('is_async'):
                print(f"   - {func['name']} in {result['file']}")
    
    # Cleanup
    os.remove("test_analysis.py")
    os.remove("test_analysis.js")
    
    print("\n=== Code Analysis Tests Complete ===")
    print("Features tested:")
    print("- List all functions with signatures and line numbers")
    print("- Find function at specific line")
    print("- Extract complete code structure")
    print("- Support for Python and JavaScript")
    print("- Search functions by pattern")

if __name__ == "__main__":
    asyncio.run(test_code_analysis())
