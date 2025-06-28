# MCP File Editor

A Model Context Protocol (MCP) server that provides comprehensive file system operations through the stdio transport.

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

# Install in development mode
pip install -e .
```

## Usage

### As a standalone server

```bash
python mcp_file_server.py
```

### Integration with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "file-editor": {
      "command": "python",
      "args": ["/path/to/mcp_file_server.py"]
    }
  }
}
```

## Available Tools

### list_files
List files and directories with optional filtering.

```json
{
  "name": "list_files",
  "arguments": {
    "path": ".",
    "pattern": "*.py",
    "recursive": true,
    "include_hidden": false
  }
}
```

### read_file
Read the contents of a file.

```json
{
  "name": "read_file",
  "arguments": {
    "path": "example.txt",
    "encoding": "utf-8",
    "lines": {
      "start": 1,
      "end": 10
    }
  }
}
```

### write_file
Write content to a file.

```json
{
  "name": "write_file",
  "arguments": {
    "path": "output.txt",
    "content": "Hello, World!",
    "encoding": "utf-8",
    "create_dirs": true
  }
}
```

### create_file
Create a new file with optional initial content.

```json
{
  "name": "create_file",
  "arguments": {
    "path": "new_file.txt",
    "content": "Initial content",
    "create_dirs": true
  }
}
```

### delete_file
Delete a file or directory.

```json
{
  "name": "delete_file",
  "arguments": {
    "path": "old_file.txt",
    "recursive": false
  }
}
```

### move_file
Move or rename a file.

```json
{
  "name": "move_file",
  "arguments": {
    "source": "old_name.txt",
    "destination": "new_name.txt",
    "overwrite": false
  }
}
```

### copy_file
Copy a file or directory.

```json
{
  "name": "copy_file",
  "arguments": {
    "source": "original.txt",
    "destination": "copy.txt",
    "overwrite": false
  }
}
```

### search_files
Search for patterns in files.

```json
{
  "name": "search_files",
  "arguments": {
    "path": ".",
    "pattern": "TODO|FIXME",
    "file_pattern": "*.py",
    "recursive": true
  }
}
```

### replace_in_files
Replace text in files.

```json
{
  "name": "replace_in_files",
  "arguments": {
    "path": ".",
    "search": "old_text",
    "replace": "new_text",
    "file_pattern": "*.txt",
    "recursive": true
  }
}
```

### get_file_info
Get detailed information about a file.

```json
{
  "name": "get_file_info",
  "arguments": {
    "path": "example.txt"
  }
}
```

## Protocol

The server implements the Model Context Protocol using JSON-RPC 2.0 over stdio.

### Initialize

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {},
  "id": 1
}
```

### List Tools

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 2
}
```

### Call Tool

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "example.txt"
    }
  },
  "id": 3
}
```

## Security

- All file paths are validated to prevent directory traversal attacks
- Operations are restricted to the server's working directory and subdirectories
- Binary files are handled safely with base64 encoding

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
