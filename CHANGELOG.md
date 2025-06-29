# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-06-29

### Added
- Code analysis features for understanding code structure:  - `list_functions` - Extract all functions with signatures and line numbers  - `get_function_at_line` - Find function containing a specific line  - `get_code_structure` - Extract imports, classes, and functions  - `search_functions` - Search for functions by name pattern- Support for Python and JavaScript code analysis- Function signature extraction with type hints- Docstring extraction and parsing## [1.0.0] - 2025-06-29### Added- Initial release of MCP File Edit server
- Comprehensive file operations (read, write, create, delete, move, copy)
- Directory operations with recursive support
- Pattern-based file search with regex support
- Find and replace across multiple files
- Advanced patch functionality with multiple patch types:
  - Line-based patches for specific line modifications
  - Pattern-based patches for find/replace operations
  - Context-based patches for safer modifications
- Project directory support for simplified relative paths
- Depth limiting for recursive operations
- Timeout handling for long-running operations
- Binary file support with base64 encoding
- Path traversal protection
- Automatic backup creation before modifications
- Dry-run mode for previewing changes
- Comprehensive error handling and status reporting

### Security
- Built-in path traversal protection
- All operations restricted to base directory
- Safe handling of symbolic links
- Input validation for all file operations

[1.0.0]: https://github.com/patrickomatik/mcp-file-edit/releases/tag/v1.0.0
