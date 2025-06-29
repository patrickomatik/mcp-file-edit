#!/usr/bin/env python3
"""
Simple example showing how to use the enhanced search features
"""

# Example 1: Search with depth limit
# This would be used through MCP protocol, but here's the concept:

# search_files(
#     pattern="TODO|FIXME",
#     path="./src",
#     recursive=True,
#     max_depth=3,      # Only search 3 levels deep
#     timeout=15.0      # 15 second timeout
# )

# Example 2: List files with depth control
# list_files(
#     path=".",
#     pattern="*.py",
#     recursive=True,
#     max_depth=2       # Only go 2 levels deep
# )

# Example 3: Replace with timeout protection
# replace_in_files(
#     search="old_function",
#     replace="new_function", 
#     path="./src",
#     file_pattern="*.py",
#     recursive=True,
#     max_depth=5,
#     timeout=30.0
# )

print("Enhanced MCP File Editor Features:")
print("- max_depth: Control how deep recursive operations go")
print("- timeout: Prevent operations from running too long")
print("- Enhanced returns: Get status info about operations")
print("- Partial results: Get some results even on timeout")
print("\nUse these features through your MCP client!")
