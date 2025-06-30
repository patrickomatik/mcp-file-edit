# MCP File Edit

A simple Model Context Protocol (MCP) server that provides comprehensive file system operations including the ability to patch files and perform basic code analysis aimed at reducing Claude Desktop's token usage when compared to other similar tools. Built on FastMCP.

## Features

- 📁 **File Operations**: Read, write, create, delete, move, and copy files
- 📂 **Directory Management**: List files, create directories, recursive operations  
- 🔍 **Search**: Search for patterns in files using regex with depth control
- 🔄 **Replace**: Find and replace text across multiple files
- 🔧 **Patch**: Apply precise modifications using line, pattern, or context-based patches
- 📍 **Project Directory**: Set a working directory for simplified relative paths
- 🧬 **Code Analysis**: Extract functions, classes, and structure from code files
- 🛡️ **Safety**: Built-in path traversal protection and safe operations
- 💾 **Binary Support**: Handle both text and binary files with proper encoding
- 🌐 **SSH Support**: Seamlessly work with remote filesystems over SSH

## Installation

### Using uv (recommended)

```bash
git clone https://github.com/patrickomatik/mcp-file-edit.git
cd mcp-file-edit
uv pip install -e .
```

### Using pip

```bash
git clone https://github.com/patrickomatik/mcp-file-edit.git
cd mcp-file-edit
pip install -e .
```

## Quick Start

### 1. Configure Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "file-edit": {
      "command": "uv",
      "args": ["run", "mcp", "run", "/path/to/mcp-file-edit/server.py"]
    }
  }
}
```

Or with Python directly:

```json
{
  "mcpServers": {
    "file-edit": {
      "command": "/path/to/python",
      "args": ["/path/to/mcp-file-edit/server.py"]
    }
  }
}
```

### 2. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the MCP server.

## Usage Guide

### Project Directory (Recommended)

Set a project directory first to use relative paths:

```python
LLM chat session
>>> Use file-edit-mcp to set project directory to /User/fred/project
```


```python
# Set project directory
set_project_directory("/path/to/your/project")

# Now use simple relative paths
read_file("src/main.py")              # Reads from project/src/main.py
write_file("docs/README.md", content) # Writes to project/docs/README.md
list_files("tests")                   # Lists files in project/tests
```

### Basic File Operations


```python
LLM chat session
>>> Use file-edit-mcp to read the file example.txt
```

```python
# Read a file
content = read_file("example.txt")

# Write a file
write_file("output.txt", "Hello, World!")


```python
LLM chat session
>>> Use file-edit-mcp to write 'hello, world' to the file output.txt
```

# Create a new file
create_file("new_file.py", "# New Python file")


```python
LLM chat session
>>> Use file-edit-mcp to set create a file called new_file.py
```

# Delete a file
delete_file("old_file.txt")


```python
LLM chat session
>>> Use file-edit-mcp to delete the file old_file.txt
```

# Move/rename a file
move_file("old_name.txt", "new_name.txt")


```python
LLM chat session
>>> Use file-edit-mcp to rename old_name to new_name
```

# Copy a file
copy_file("source.txt", "destination.txt")
```


```python
LLM chat session
>>> Use file-edit-mcp to set copy the file source to destination
```

### Search and Replace

Claude should discover and use these functions as part of a wider remit, for example whilst writing new source code to your specification.
They can also be used for manual search and replace operations like this:

```python
LLM chat session
>>> Use file-edit-mcp to find all TODO occurrences and summarise here.
```

```python
# Search for patterns
results = search_files(
    pattern="TODO|FIXME",
    path="src",
    recursive=True,
    max_depth=3
)

# Replace across files
replace_in_files(
    search="old_function",
    replace="new_function",
    path=".",
    file_pattern="*.py"
)
```

### Advanced Patching

Claude should discover and use these functions as part of a wider remit, for example whilst amending source code to fix issues discovered in testing of it's own code.

```python
# Line-based patch
patch_file("config.json", patches=[
    {"line": 5, "content": '    "debug": true,'}
])

# Pattern-based patch
patch_file("main.py", patches=[
    {"find": "import old", "replace": "import new"}
])

# Context-based patch (safer)
patch_file("app.py", patches=[{
    "context": ["def process():", "    return None"],
    "replace": ["def process():", "    return result"]
}])
```

### Code Analysis

```python
# List all functions in a file
functions = list_functions("mycode.py")
# Returns function names, signatures, line numbers, docstrings

# Find function at specific line
func = get_function_at_line("mycode.py", 42)
# Returns the function containing line 42

# Get complete code structure
structure = get_code_structure("mycode.py")
# Returns imports, classes, functions, and more

# Search for functions by pattern
results = search_functions("test_.*", "tests/", "*.py")
# Finds all test functions

## Available Tools

### File Operations
- `read_file` - Read file contents with optional line range
- `write_file` - Write content to a file  
- `create_file` - Create a new file
- `delete_file` - Delete a file or directory
- `move_file` - Move or rename files
- `copy_file` - Copy files or directories

### Directory Operations
- `list_files` - List files with glob patterns and depth control
- `get_file_info` - Get detailed file metadata

### Search and Modification
- `search_files` - Search for patterns with regex support
- `replace_in_files` - Find and replace across multiple files
- `patch_file` - Apply precise modifications to files

### Project Management
- `set_project_directory` - Set the working directory context
- `get_project_directory` - Get current project directory

### Code Analysis- `list_functions` - List all functions in a code file with signatures and line numbers- `get_function_at_line` - Find which function contains a specific line- `get_code_structure` - Extract complete code structure (imports, classes, functions)- `search_functions` - Search for functions by name pattern across files

## Safety Features
- **Path Traversal Protection**: All paths are validated to prevent directory traversal attacks
- **Project Boundary Enforcement**: Operations are restricted to the base directory
- **Backup Creation**: Automatic backups before modifications (configurable)
- **Dry Run Mode**: Preview changes before applying them
- **Atomic Operations**: All-or-nothing patch applications

### SSH Support

The file editor now supports SSH connections for remote filesystem operations:

```python
# Connect to a remote server using SSH URL format
set_project_directory("ssh://user@example.com:22/home/user/project")

# Or specify SSH parameters explicitly
set_project_directory(
    path="/home/user/project",
    connection_type="ssh",
    ssh_host="example.com",
    ssh_username="user",
    ssh_port=22,
    ssh_key_filename="~/.ssh/id_rsa"  # Optional, defaults to ~/.ssh/id_rsa
)

# All file operations now work on the remote server
files = list_files("src")  # Lists files on remote server
content = read_file("config.json")  # Reads from remote server
write_file("output.txt", "Remote content")  # Writes to remote server

# Switch back to local filesystem
set_project_directory("/local/path", connection_type="local")
```

**SSH Features:**
- Key-based authentication (no password prompts)
- All file operations work transparently over SSH
- No tools required on the remote server
- Efficient operations using SFTP protocol
- Automatic reconnection on connection loss

## Examples
See the `examples/` directory for detailed usage examples:
- `example_usage.py` - Basic file operations
- `enhanced_features_examples.py` - Advanced search and depth control
- `patch_examples.py` - Various patching techniques
- `project_directory_examples.py` - Project directory usage

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_patch.py
```

### Project Structure

```
mcp-file-edit/
├── server.py              # Main MCP server implementation
├── pyproject.toml         # Project configuration
├── README.md              # This file
├── LICENSE                # MIT license
├── examples/              # Usage examples
│   ├── example_usage.py
│   ├── patch_examples.py
│   └── ...
└── tests/                 # Test files
    ├── test_patch.py
    ├── test_enhanced.py
    └── ...
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Implements the [Model Context Protocol](https://modelcontextprotocol.io) specification

## Support

For issues, questions, or suggestions, please open an issue on [GitHub](https://github.com/patrickomatik/mcp-file-edit/issues).
