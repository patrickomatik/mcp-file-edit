# MCP File Editor

A Model Context Protocol (MCP) server built with FastMCP that provides comprehensive file system operations.

## Features

- **File Operations**: Read, write, create, delete, move, and copy files
- **Directory Operations**: List files, create directories, recursive operations
- **Search**: Search for patterns in files using regex
- **Replace**: Find and replace text across multiple files
- **File Information**: Get detailed metadata about files and directories
- **Safety**: Built-in path traversal protection
- **Binary Support**: Handle both text and binary files

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-file-editor.git
cd mcp-file-editor

# Install dependencies using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Usage

### Running the server

```bash
# Using uv
uv run mcp run server.py

# Or directly with Python
python server.py
```

### Integration with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "file-editor": {
      "command": "/path/to/your/python",
      "args": ["/path/to/mcp_file_editor/server.py"]
    }
  }
}
```

Or if using uv:

```json
{
  "mcpServers": {
    "file-editor": {
      "command": "uv",
      "args": ["run", "mcp", "run", "/path/to/mcp_file_editor/server.py"]
    }
  }
}
```

## Available Tools

### list_files
List files and directories with optional filtering and depth control.

**Parameters:**
- `path` (str, optional): Directory path (default: current directory)
- `pattern` (str, optional): Glob pattern for filtering (default: \"*\")
- `recursive` (bool, optional): List recursively (default: False)
- `include_hidden` (bool, optional): Include hidden files (default: False)
- `max_depth` (int, optional): Maximum depth for recursive listing (default: None for unlimited)

### read_file
Read the contents of a file.

**Parameters:**
- `path` (str): File path
- `encoding` (str, optional): File encoding (default: "utf-8")
- `start_line` (int, optional): Starting line number (1-based)
- `end_line` (int, optional): Ending line number (inclusive)

### write_file
Write content to a file.

**Parameters:**
- `path` (str): File path
- `content` (str): Content to write
- `encoding` (str, optional): File encoding (default: "utf-8", or "base64" for binary)
- `create_dirs` (bool, optional): Create parent directories if needed (default: False)

### create_file
Create a new file with optional initial content.

**Parameters:**
- `path` (str): File path
- `content` (str, optional): Initial content (default: "")
- `create_dirs` (bool, optional): Create parent directories if needed (default: False)

### delete_file
Delete a file or directory.

**Parameters:**
- `path` (str): File or directory path
- `recursive` (bool, optional): Delete directories recursively (default: False)

### move_file
Move or rename a file.

**Parameters:**
- `source` (str): Source path
- `destination` (str): Destination path
- `overwrite` (bool, optional): Overwrite if exists (default: False)

### copy_file
Copy a file or directory.

**Parameters:**
- `source` (str): Source path
- `destination` (str): Destination path
- `overwrite` (bool, optional): Overwrite if exists (default: False)

### search_files
Search for patterns in files with timeout and depth control.

**Parameters:**
- `pattern` (str): Search pattern (regex)
- `path` (str, optional): Directory to search in (default: \".\")
- `file_pattern` (str, optional): File name pattern (default: \"*\")
- `recursive` (bool, optional): Search recursively (default: True)
- `max_depth` (int, optional): Maximum depth for recursive search (default: None for unlimited)
- `timeout` (float, optional): Maximum time in seconds for search operation (default: 30.0)

**Returns:**
Dictionary containing:
- `results`: List of files with matches
- `completed`: Whether search completed fully
- `files_searched`: Number of files searched
- `timeout_occurred`: Whether search timed out
- `error`: Any error message

### replace_in_files
Replace text in files with timeout and depth control.

**Parameters:**
- `search` (str): Search pattern (regex)
- `replace` (str): Replacement text
- `path` (str, optional): Directory or file path (default: \".\")
- `file_pattern` (str, optional): File name pattern (default: \"*\")
- `recursive` (bool, optional): Search recursively (default: True)
- `max_depth` (int, optional): Maximum depth for recursive search (default: None for unlimited)
- `timeout` (float, optional): Maximum time in seconds for operation (default: 30.0)

**Returns:**
Dictionary containing:
- `results`: List of files with replacement counts
- `completed`: Whether operation completed fully
- `files_processed`: Number of files processed
- `timeout_occurred`: Whether operation timed out
- `error`: Any error message

### get_file_info
Get detailed information about a file.

**Parameters:**
- `path` (str): File path

## Security

- All file paths are validated to prevent directory traversal attacks
- Operations are restricted to the server's working directory and subdirectories
- Binary files are handled safely with base64 encoding

## Development

### Running tests

```bash
python test_mcp_server.py
```

### Example usage

```python
# See example_usage.py for more examples
```

## License

MIT License - see LICENSE file for details
