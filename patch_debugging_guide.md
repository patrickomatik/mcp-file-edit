# Why MCP File Edit Patches Fail - Common Issues and Solutions

## 1. Context Already Modified
**Issue**: The context you're looking for has already been changed by a previous edit.
**Solution**: Check the current file content first, or use a more unique context.

## 2. Context Not Found
**Issue**: The exact lines specified in context don't exist as continuous lines.
**Common Causes**:
- Extra or missing whitespace
- Different line endings
- Content has moved
- Partial match only

**Solutions**:
- Use `read_file` to check exact content first
- Use more specific, unique context
- Use line-based patches if you know the exact line numbers

## 3. Markdown Formatting Issues
**Issue**: Incorrect number of backticks in code blocks (e.g., 4 instead of 3)
**Solution**: Ensure markdown syntax is correct: ` ``` ` not ` ```` `

## 4. Multiple Matches
**Issue**: Context appears multiple times in the file
**Solution**: 
- Use more lines of context for uniqueness
- Specify `occurrence` parameter (1-based)
- Use pattern-based patches with `occurrence`

## 5. Special Characters
**Issue**: Regex special characters in find/replace patterns
**Solution**: 
- Escape special characters: `(`, `)`, `[`, `]`, etc.
- Use `regex: false` for literal matching (if supported)

## Debugging Tips

1. **Always check current content first**:
   ```python
   content = read_file("myfile.txt")
   # Verify your context exists
   ```

2. **Use specific context**:
   ```python
   # Bad - too generic
   {"context": ["", "## Tools"]}
   
   # Good - more specific
   {"context": ["specific line", "", "## Tools"]}
   ```

3. **Use line numbers when possible**:
   ```python
   # If you know the exact line
   {"line": 42, "content": "new content"}
   ```

4. **Test with dry_run**:
   ```python
   patch_file("file.txt", patches=[...], dry_run=True)
   ```

## Enhanced Error Messages

The improved patch function now provides:
- Exact search details
- Partial match locations
- Specific mismatch information
- Suggestions for fixes

## Example: Robust Patching

```python
# First, check what's there
content = read_file("config.py")

# Find unique context
search_results = search_files("specific_string", "config.py")

# Use robust context
patch_file("config.py", patches=[{
    "context": [
        "# Unique comment",
        "def my_function():",
        "    return old_value"
    ],
    "replace": [
        "# Unique comment", 
        "def my_function():",
        "    return new_value"
    ]
}])
```
