#!/usr/bin/env python3
"""
Examples of using code analysis features in MCP File Edit
"""

# The code analysis features help you understand and navigate code files

# Example 1: List all functions in a file
# list_functions("src/main.py")
# Returns:
# [
#   {
#     "name": "main",
#     "line_start": 10,
#     "line_end": 25,
#     "signature": "main(args)",
#     "docstring": "Main entry point",
#     "is_async": false,
#     "decorators": []
#   },
#   {
#     "name": "process_data",
#     "line_start": 30,
#     "line_end": 45,
#     "signature": "process_data(data, options=...)",
#     "docstring": "Process input data",
#     "return_type": "Dict[str, Any]",
#     "param_types": {"data": "str", "options": "Optional[Dict]"}
#   }
# ]

# Example 2: Find which function contains a specific line
# get_function_at_line("src/utils.py", 42)
# Returns:
# {
#   "name": "validate_input",
#   "line_start": 35,
#   "line_end": 50,
#   "signature": "validate_input(value)"
# }

# Example 3: Get complete code structure
# get_code_structure("mymodule.py")
# Returns:
# {
#   "language": "python",
#   "file": "mymodule.py",
#   "lines": 250,
#   "imports": [
#     {"type": "import", "module": "os", "line": 1},
#     {"type": "from", "module": "typing", "name": "List", "line": 2}
#   ],
#   "classes": [
#     {
#       "name": "MyClass",
#       "line_start": 20,
#       "line_end": 80,
#       "methods": [
#         {"name": "__init__", "line": 22},
#         {"name": "process", "line": 30}
#       ],
#       "bases": ["BaseClass"]
#     }
#   ],
#   "functions": [
#     {"name": "helper", "line_start": 90, "line_end": 100}
#   ]
# }

# Example 4: Search for functions across files
# search_functions("test_.*", "tests/", "*.py", recursive=True)
# Returns:
# {
#   "results": [
#     {
#       "file": "tests/test_main.py",
#       "functions": [
#         {"name": "test_basic", "line_start": 10},
#         {"name": "test_advanced", "line_start": 20}
#       ]
#     }
#   ],
#   "files_searched": 5,
#   "total_functions": 12
# }

# Example 5: Working with JavaScript/TypeScript
# list_functions("app.js", language="javascript")
# Returns functions from JavaScript files

# Example 6: Find async functions
# search_functions("async", "src/", "*.py")
# Finds all async functions in Python files

print("Code Analysis Examples")
print("=====================")
print()
print("Features:")
print("- list_functions: Get all functions with line numbers and signatures")
print("- get_function_at_line: Find which function contains a line")
print("- get_code_structure: Extract imports, classes, and functions")
print("- search_functions: Search for functions by name pattern")
print()
print("Supported languages:")
print("- Python (.py)")
print("- JavaScript (.js)")
print("- TypeScript (.ts)")
print()
print("Use cases:")
print("- Navigate large codebases")
print("- Understand code structure")
print("- Find specific implementations")
print("- Extract documentation")
print("- Analyze code organization")
