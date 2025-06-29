#!/usr/bin/env python3
"""
Example: Using Project Directory Feature
"""

# The project directory feature simplifies file operations within a project
# Instead of specifying full paths every time, you can work with relative paths

# IMPORTANT: When using the MCP File Editor, always set the project directory first!

# Example 1: Set project directory
# set_project_directory("/Users/name/projects/my-app")
# or relative to current directory:
# set_project_directory("my-app")

# Example 2: Check current project directory
# get_project_directory()
# Returns: {
#   "project_directory": "/Users/name/projects/my-app",
#   "relative_to_base": "my-app",
#   "absolute_path": "/Users/name/projects/my-app"
# }

# Example 3: Work with project files using relative paths
# After setting project directory to "/Users/name/projects/my-app":

# Read a file (resolves to /Users/name/projects/my-app/src/main.py)
# read_file("src/main.py")

# List files in a directory (resolves to /Users/name/projects/my-app/tests)
# list_files("tests", pattern="*.py")

# Create a new file (creates /Users/name/projects/my-app/docs/README.md)
# create_file("docs/README.md", content="# Project Documentation")

# Search within project (searches in /Users/name/projects/my-app)
# search_files("TODO", path=".", recursive=True)

# Patch a file (patches /Users/name/projects/my-app/config.json)
# patch_file("config.json", patches=[
#     {"line": 5, "content": '  "debug": true,'}
# ])

# Example 4: Absolute paths still work
# write_file("/tmp/outside-project.txt", content="This works too")

print("Project Directory Usage Examples")
print("================================")
print()
print("Key benefits:")
print("1. Simplifies file paths - use relative paths from project root")
print("2. Reduces errors - no need to type long absolute paths")
print("3. Context-aware - all operations default to project directory")
print("4. Flexible - absolute paths still work when needed")
print()
print("Best practice for LLMs:")
print("- ALWAYS call set_project_directory() first when starting work")
print("- Use get_project_directory() to verify the context")
print("- Use relative paths for all project files")
print("- Document the project directory in conversations")
