#!/usr/bin/env python3
"""
Example demonstrating the patch_file functionality
"""

# The patch_file tool allows precise modifications to files
# This is especially useful for:
# - Updating configuration files
# - Modifying code at specific locations
# - Applying multiple changes atomically
# - Previewing changes before applying them

# Example 1: Update a specific line number
# patch_file(
#     path="config.json",
#     patches=[
#         {"line": 5, "content": '    "debug": true,'}
#     ]
# )

# Example 2: Replace a function definition
# patch_file(
#     path="mycode.py",
#     patches=[
#         {
#             "find": "def old_function(x):",
#             "replace": "def new_function(x, y=None):"
#         }
#     ]
# )

# Example 3: Multi-line replacement
# patch_file(
#     path="mycode.py",
#     patches=[
#         {
#             "start_line": 10,
#             "end_line": 15,
#             "content": "    # New implementation\n    return x * 2\n"
#         }
#     ]
# )

# Example 4: Context-based patching (safest for code that might move)
# patch_file(
#     path="mycode.py",
#     patches=[
#         {
#             "context": [
#                 "class MyClass:",
#                 "    def __init__(self):",
#                 "        self.value = 0"
#             ],
#             "replace": [
#                 "class MyClass:",
#                 "    def __init__(self, initial_value=0):",
#                 "        self.value = initial_value"
#             ]
#         }
#     ]
# )

# Example 5: Multiple patches with dry run
# patch_file(
#     path="important_file.py",
#     patches=[
#         {"line": 1, "content": "#!/usr/bin/env python3"},
#         {"find": "TODO", "replace": "DONE", "occurrence": 1},
#         {"find": "print\\((.*?)\\)", "replace": "logger.info(\\1)", "regex": true}
#     ],
#     dry_run=True  # Preview changes without applying
# )

# Example 6: Patch with backup
# patch_file(
#     path="production.conf",
#     patches=[
#         {"find": "localhost", "replace": "example.com"},
#         {"find": "debug=True", "replace": "debug=False"}
#     ],
#     backup=True  # Creates production.conf.backup_TIMESTAMP
# )

print("Patch file examples - see comments in this file for usage patterns")
print("\nKey features:")
print("- Line-based: Modify specific line numbers")
print("- Pattern-based: Find and replace with optional regex")
print("- Context-based: Safer patching using surrounding context")
print("- Multiple patches: Apply many changes atomically")
print("- Dry run: Preview changes before applying")
print("- Backup: Automatic backup before modifications")
