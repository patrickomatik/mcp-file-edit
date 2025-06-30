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
- 📤 **SSH Transfer**: Upload/download files and efficient rsync synchronization
- 📤 **SSH Upload/Download**: Transfer files between local and remote filesystems
- 🔀 **Git Operations**: Full git support for both local and remote repositories

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

#### SSH File Transfer Operations

Transfer files between local and remote filesystems:

```python
# First, establish SSH connection
set_project_directory(
    path="/remote/project",
    connection_type="ssh",
    ssh_host="example.com",
    ssh_username="user"
)

# Upload a single file
result = ssh_upload(
    local_path="/local/file.txt",
    remote_path="uploads/file.txt"
)

# Upload a directory recursively
result = ssh_upload(
    local_path="/local/project",
    remote_path="/remote/backup",
    recursive=True,
    overwrite=True
)

# Download a file
result = ssh_download(
    remote_path="data/report.pdf",
    local_path="/local/downloads/report.pdf"
)

# Download a directory
result = ssh_download(
    remote_path="/remote/logs",
    local_path="/local/logs_backup",
    recursive=True
)

# Sync directories using rsync for efficiency
result = ssh_sync(
    local_path="/local/source",
    remote_path="/remote/mirror",
    direction="upload",       # or "download"
    delete=False,             # Don't delete extra files in destination
    update_only=True,         # Only update if source is newer (default)
    show_progress=True,       # Show rsync progress output (default)
    exclude_patterns=[        # Patterns to exclude from sync
        "*.log",
        "*.tmp",
        "node_modules/",
        ".git/"
    ]
)

**Transfer Features:**
- Efficient rsync-based synchronization with compression
- Single file or recursive directory transfers
- Smart updates - only transfer files if source is newer
- Automatic directory creation
- Overwrite control with update_only option
- Real-time progress tracking with rsync --progress
- Exclude patterns for filtering files
- Delete option for true mirror synchronization
- Error handling with detailed error reports
- Supports both absolute and relative paths

**SSH Features:**
- Key-based authentication (no password prompts)
- All file operations work transparently over SSH
- No tools required on the remote server
- Efficient operations using SFTP protocol
- Automatic reconnection on connection loss
- Upload/download files between local and remote systems
- Recursive directory transfers
- Sync operations with conflict handling

## Examples
=======
=======
### Git Operations

The file editor provides comprehensive git support for both local and remote repositories:

```python
# Check git status
status = git_status()
# Shows: branch, staged files, modified files, untracked files

# Initialize a new repository
git_init()

# Clone a repository
git_clone("https://github.com/user/repo.git", branch="main")

# Stage files
git_add("file.txt")  # Single file
git_add(["*.py", "docs/"])  # Multiple files/patterns

# Commit changes
git_commit("feat: Add new feature")

# Push to remote
git_push("origin", "main", set_upstream=True)

# Pull changes
git_pull("origin", "main")

# View commit history
logs = git_log(limit=20, oneline=False)

# Branch operations
git_branch(create="feature/new-feature")  # Create branch
git_checkout("feature/new-feature")  # Switch branch
branches = git_branch()  # List branches
git_branch(delete="old-branch")  # Delete branch

# View differences
diff = git_diff()  # Working directory changes
diff = git_diff(cached=True)  # Staged changes

# Remote management
remotes = git_remote()  # List remotes
git_remote(action="add", name="upstream", url="https://github.com/upstream/repo.git")
git_remote(action="remove", name="old-remote")
```

#### Git on Remote Servers

Git operations work seamlessly on remote servers via SSH:

```python
# Connect to remote server
set_project_directory(
    path="/home/user/project",
    connection_type="ssh",
    ssh_host="server.example.com",
    ssh_username="user"
)

# All git operations now work on the remote server
status = git_status()  # Check remote repository status
git_add("*.js")  # Stage files on remote
git_commit("fix: Update configuration")  # Commit on remote
git_push()  # Push from remote to its origin
```

**Git Features:**
- Full git command support (status, add, commit, push, pull, etc.)
- Works identically on local and remote repositories
- Branch management (create, switch, delete)
- Remote repository management
- Commit history with detailed information
- Diff viewing for changes
- No git installation needed on Claude's side

>>>>>>> 55f824a (feat: Add comprehensive git operations support)
## Practical Claude Desktop Examples

### Example 1: Analyzing and Refactoring a Python Project

**User**: "Can you help me refactor this Python project in /Users/me/projects/webapp?"

**Claude**:
```python
# First, I'll set the project directory to work with your files
set_project_directory("/Users/me/projects/webapp")

# Let me explore the project structure
files = list_files(recursive=True, pattern="*.py")
# Found: app.py, models.py, utils.py, tests/test_app.py, etc.

# Let's look at the main application file
content = read_file("app.py")
# I can see this is a Flask application with some issues...

# Let me check the code structure
structure = get_code_structure("app.py")
# Found 15 functions, 3 classes, various imports

# Search for potential issues
results = search_files("TODO|FIXME|XXX", pattern="*.py")
# Found 8 TODOs across different files

# Let's refactor the database connection function
patch_file(
    "app.py",
    patches=[{
        "find": "def get_db():\n    return sqlite3.connect('database.db')",
        "replace": "def get_db():\n    \"\"\"Get database connection with proper error handling.\"\"\"\n    try:\n        conn = sqlite3.connect('database.db')\n        conn.row_factory = sqlite3.Row\n        return conn\n    except sqlite3.Error as e:\n        current_app.logger.error(f'Database connection failed: {e}')\n        raise"
    }]
)

# Create a new configuration file
create_file(
    "config.py",
    content='''"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
'''
)
```

### Example 2: Deploying a Web Application to a Remote Server

**User**: "I need to deploy my React app to my VPS at server.example.com"

**Claude**:
```python
# First, let's connect to your remote server
set_project_directory(
    path="/var/www/myapp",
    connection_type="ssh",
    ssh_host="server.example.com",
    ssh_username="deploy",
    ssh_port=22
)

# Check what's currently on the server
files = list_files()
# I see there's an old version deployed...

# Create a backup of the current deployment
create_file("backup_timestamp.txt", datetime.now().isoformat())
move_file("current", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# Now let's upload your built React app
# First, let me check your local build
set_project_directory("/Users/you/projects/react-app", connection_type="local")

# Make sure you have a fresh build
local_files = list_files("build", recursive=True)
# Good, I can see the build directory with all assets

# Switch back to SSH and upload
set_project_directory(
    "ssh://deploy@server.example.com/var/www/myapp",
    connection_type="ssh"
)

# Upload the entire build directory
result = ssh_upload(
    local_path="/Users/you/projects/react-app/build",
    remote_path="current",
    recursive=True,
    overwrite=True
)
# Uploaded 156 files successfully

# Set proper permissions
for html_file in list_files("current", pattern="*.html"):
    # Note: You might need to run chmod via SSH separately
    pass

# Create/update the nginx configuration
config_content = read_file("/etc/nginx/sites-available/myapp")
# Let me update the configuration...
```

### Example 3: Analyzing Logs Across Multiple Servers

**User**: "I need to investigate an issue that happened yesterday across our three web servers"

**Claude**:
```python
# I'll help you gather and analyze logs from all three servers

# Server 1 - Web Frontend
set_project_directory(
    "ssh://admin@web1.example.com/var/log",
    connection_type="ssh"
)

# Search for errors in yesterday's logs
error_logs = search_files(
    "ERROR|CRITICAL|Exception",
    pattern="*.log",
    recursive=True
)
# Found 45 matches in nginx/error.log and app/production.log

# Download yesterday's logs for detailed analysis
result = ssh_download(
    remote_path="nginx/access.log.1",
    local_path="/tmp/analysis/web1_access.log"
)

# Server 2 - API Backend
set_project_directory(
    "ssh://admin@api.example.com/var/log",
    connection_type="ssh"
)

# Check for database connection errors
db_errors = search_files(
    "connection refused|timeout|Connection reset",
    pattern="postgresql*.log"
)
# Found 12 connection timeout errors between 14:30-14:45

# Download the specific time range
result = ssh_download(
    remote_path="app/api.log",
    local_path="/tmp/analysis/api.log"
)

# Server 3 - Background Workers
set_project_directory(
    "ssh://admin@worker.example.com/var/log",
    connection_type="ssh"
)

# Check for job failures
job_failures = search_files(
    "Job.*failed|Task.*error",
    pattern="worker*.log"
)

# Now analyze locally
set_project_directory("/tmp/analysis", connection_type="local")

# Correlate timestamps across all logs
all_logs = list_files(pattern="*.log")
for log_file in all_logs:
    content = read_file(log_file['name'])
    # ... analyze and correlate events
```

### Example 4: Maintaining Configuration Files Across Environments

**User**: "I need to update configuration files across dev, staging, and production environments"

**Claude**:
```python
# Let's create a systematic approach to managing your configurations

# First, let's work with your configuration templates locally
set_project_directory("/Users/you/configs", connection_type="local")

# Create a base configuration template
create_file(
    "base_config.yaml",
    content="""# Base configuration for all environments
app:
  name: MyApplication
  version: 2.1.0
  
logging:
  level: INFO
  format: json
  
metrics:
  enabled: true
  port: 9090
"""
)

# Create environment-specific overrides
environments = ["dev", "staging", "prod"]
for env in environments:
    create_file(
        f"{env}_config.yaml",
        content=f"""# {env.title()} environment configuration
env: {env}
database:
  host: {env}-db.internal
  pool_size: {'5' if env == 'dev' else '20'}
  
api:
  rate_limit: {'100' if env == 'dev' else '1000'}
  debug: {'true' if env == 'dev' else 'false'}
"""
    )

# Now deploy to each environment
servers = {
    "dev": "dev.example.com",
    "staging": "staging.example.com",
    "prod": "prod1.example.com"
}

for env, host in servers.items():
    # Connect to the server
    set_project_directory(
        f"ssh://deploy@{host}/etc/myapp",
        connection_type="ssh"
    )
    
    # Backup existing configuration
    if await file_exists("config.yaml"):
        copy_file("config.yaml", f"config.yaml.backup.{datetime.now().strftime('%Y%m%d')}")
    
    # Upload the new configuration
    result = ssh_upload(
        local_path=f"/Users/you/configs/{env}_config.yaml",
        remote_path="config.yaml"
    )
    
    # Verify the upload
    content = read_file("config.yaml")
    print(f"✓ Updated configuration on {env} server")
```

### Example 5: Collaborative Code Review and Fixes

**User**: "Can you review my code and fix any security issues you find?"

**Claude**:
```python
# Let's do a comprehensive security review of your codebase
set_project_directory("/Users/you/projects/webapp")

# First, let's search for common security issues

# 1. Check for hardcoded secrets
secrets_search = search_files(
    "password.*=.*['\"]|api_key.*=.*['\"]|secret.*=.*['\"]|token.*=.*['\"]",
    pattern="*.py,*.js,*.env*"
)
# Found potential hardcoded secrets in config.py and test_api.py

# 2. Look for SQL injection vulnerabilities
sql_issues = search_files(
    "execute\(.*%.*%|execute\(.*format\(|execute\(.*\+.*",
    pattern="*.py"
)
# Found 3 potential SQL injection points

# Let's fix the SQL injection in user.py
patch_file(
    "models/user.py",
    patches=[{
        "find": 'cursor.execute(f"SELECT * FROM users WHERE email = \'{email}\'")',
        "replace": 'cursor.execute("SELECT * FROM users WHERE email = %s", (email,))'
    }]
)

# 3. Check for missing input validation
validation_check = list_functions("routes.py")
# I'll examine each route handler...

# Fix missing validation in the user registration endpoint
patch_file(
    "routes.py",
    patches=[{
        "find": "@app.route('/register', methods=['POST'])\ndef register():\n    email = request.form['email']\n    password = request.form['password']",
        "replace": "@app.route('/register', methods=['POST'])\ndef register():\n    email = request.form.get('email', '').strip()\n    password = request.form.get('password', '')\n    \n    # Validate input\n    if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):\n        return jsonify({'error': 'Invalid email address'}), 400\n    if len(password) < 8:\n        return jsonify({'error': 'Password must be at least 8 characters'}), 400"
    }]
)

# 4. Create a security configuration file
create_file(
    "security.py",
    content='''"""Security configuration and utilities."""
import os
from functools import wraps
from flask import request, jsonify
import secrets

# Security headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
}

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600  # 1 hour

def generate_secure_token():
    """Generate a cryptographically secure token."""
    return secrets.token_urlsafe(32)

def require_api_key(f):
    """Decorator to require API key for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function
'''
)

# 5. Create a security audit report
report = f"""# Security Audit Report
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Issues Found and Fixed:
1. SQL Injection: Fixed {len(sql_issues['results'])} vulnerable queries
2. Hardcoded Secrets: Found {len(secrets_search['results'])} instances
3. Input Validation: Added validation to user registration
4. Security Headers: Created security configuration file

## Recommendations:
- Move all secrets to environment variables
- Implement rate limiting on all endpoints  
- Add CSRF protection to forms
- Enable security headers in production
- Regular dependency updates
"""

create_file("SECURITY_AUDIT.md", report)
```

### More Practical Claude Desktop Interactions

#### Quick File Operations

**User**: "List files in the current directory"

**Claude**:
```python
# I'll list the files in your current directory
files = list_files()
# Here are the files I found:
# - README.md (2.5 KB)
# - app.py (10.2 KB) 
# - requirements.txt (456 bytes)
# - tests/ (directory)
# - static/ (directory)
```

**User**: "Show me what's in the tests folder"

**Claude**:
```python
test_files = list_files("tests", recursive=True)
# Found in tests/:
# - test_app.py (3.2 KB)
# - test_models.py (2.8 KB)
# - test_utils.py (1.5 KB)
# - fixtures/test_data.json (890 bytes)
```

#### Remote Server Management

**User**: "Use the remote server user@foo.example.com, set remote working directory to /home/user/project_a and upload the file readme.txt"

**Claude**:
```python
# I'll connect to your remote server and upload the file
set_project_directory(
    path="/home/user/project_a",
    connection_type="ssh",
    ssh_host="foo.example.com",
    ssh_username="user"
)
# Connected to foo.example.com as user

# Now uploading readme.txt from your local directory
result = ssh_upload(
    local_path="readme.txt",
    remote_path="readme.txt"
)
# Successfully uploaded readme.txt (1,234 bytes)
```

**User**: "Check if the file was uploaded correctly and show me what files are on the server"

**Claude**:
```python
# Let me verify the upload and show you the directory contents
files = list_files()
# Files in /home/user/project_a:
# - readme.txt (1,234 bytes) - just uploaded
# - config.json (456 bytes)
# - src/ (directory)
# - logs/ (directory)

# Let's verify the content matches
content = read_file("readme.txt")
# The file contains your project documentation and was uploaded successfully
```

#### Editing Configuration Files

**User**: "I need to update the database connection string in my config file"

**Claude**:
```python
# I'll help you update the database configuration
# First, let me read the current config
config_content = read_file("config.json")

# I'll update the database connection string
patch_file(
    "config.json",
    patches=[{
        "find": "\"database_url\": \"postgresql://localhost/myapp\"",
        "replace": "\"database_url\": \"postgresql://db.example.com:5432/myapp_prod\""
    }]
)
# Configuration updated successfully
```

#### Searching Across Files

**User**: "Find all TODO comments in my Python files"

**Claude**:
```python
# I'll search for TODO comments across all Python files
todos = search_files(
    pattern="TODO|FIXME|XXX",
    file_pattern="*.py",
    recursive=True
)

# Found 12 TODOs:
# app.py:45 - TODO: Add error handling for database connection
# app.py:89 - TODO: Implement rate limiting
# models.py:23 - FIXME: This query is not optimized
# utils.py:67 - TODO: Add unit tests for this function
# ...
```

#### Backing Up and Restoring

**User**: "Create a backup of my entire project directory"

**Claude**:
```python
# I'll create a timestamped backup of your project
from datetime import datetime

backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Create backup directory
create_file(f"../{backup_name}/.backup_info", f"Backup created at {datetime.now()}")

# Copy all files
files = list_files(recursive=True)
for file in files:
    if file['type'] == 'file':
        content = read_file(file['name'])
        write_file(f"../{backup_name}/{file['name']}", content)
        
# Backup created successfully at ../{backup_name}/
```

#### Working with Multiple Files

**User**: "Replace all instances of 'http://' with 'https://' in all my config files"

**Claude**:
```python
# I'll update all config files to use HTTPS
result = replace_in_files(
    search="http://",
    replace="https://",
    file_pattern="*.conf,*.json,*.yaml,*.yml",
    recursive=True
)

# Updated 8 files:
# - config.json: 3 replacements
# - app.conf: 2 replacements  
# - settings.yaml: 1 replacement
# ...
# Total: 15 replacements across 8 files
```

#### Analyzing Code Structure

**User**: "Show me all the functions in my main.py file"

**Claude**:
```python
# I'll analyze the code structure of main.py
functions = list_functions("main.py")

# Found 12 functions in main.py:
# 1. initialize_app() - Line 10-25: Sets up the application
# 2. connect_database() - Line 28-45: Establishes database connection
# 3. authenticate_user() - Line 48-72: Handles user authentication
# 4. process_request() - Line 75-95: Main request handler
# ...

# Let me also show you the overall structure
structure = get_code_structure("main.py")
# File structure:
# - Imports: 8 (flask, sqlalchemy, ...)
# - Classes: 3 (App, Database, UserAuth)
# - Functions: 12
# - Total lines: 450
```

#### Git Version Control

**User**: "Initialize git for this project and make the first commit"

**Claude**:
```python
# I'll initialize git and create your first commit

# Initialize the repository
result = git_init()
# Initialized empty Git repository in /Users/you/project/.git/

# Check current status
status = git_status()
# Untracked files: app.py, README.md, requirements.txt, config.json

# Create a .gitignore file
create_file(".gitignore", '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
''')

# Add all files
git_add(".")
# Added 5 files to staging area

# Make the first commit
commit_result = git_commit("Initial commit: Project setup")
# Created commit 7a8b9c1: Initial commit: Project setup
```

**User**: "Create a new feature branch and push it to GitHub"

**Claude**:
```python
# I'll create a feature branch and set up the GitHub remote

# First, let's add the GitHub remote
git_remote(
    action="add",
    name="origin",
    url="https://github.com/yourusername/project.git"
)
# Added remote 'origin'

# Create and switch to a new feature branch
git_branch(create="feature/user-authentication")
git_checkout("feature/user-authentication")
# Switched to new branch 'feature/user-authentication'

# Make some changes for the feature
create_file("auth.py", '''"""User authentication module."""
import hashlib
import secrets

class UserAuth:
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        self.users[username] = {
            "salt": salt,
            "password_hash": password_hash
        }
        return True
''')

# Stage and commit the changes
git_add("auth.py")
git_commit("feat: Add user authentication module")

# Push the branch to GitHub
git_push("origin", "feature/user-authentication", set_upstream=True)
# Branch 'feature/user-authentication' set up to track 'origin/feature/user-authentication'
# Successfully pushed to GitHub
```

#### Creating Project Templates

**User**: "Create a basic Flask project structure for me"

**Claude**:
```python
# I'll create a basic Flask project structure

# Create main application file
create_file("app.py", '''from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
''')

# Create configuration
create_file("config.py", '''import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
''')

# Create requirements file
create_file("requirements.txt", '''Flask==2.3.2
SQLAlchemy==2.0.19
python-dotenv==1.0.0
''')

# Create directory structure
create_file("templates/index.html", '''<!DOCTYPE html>
<html>
<head>
    <title>My Flask App</title>
</head>
<body>
    <h1>Welcome to Flask!</h1>
</body>
</html>
''')

create_file("static/style.css", '''body {
    font-family: Arial, sans-serif;
    margin: 40px;
}
''')

create_file(".env.example", '''SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
''')

# Flask project structure created successfully!
```

## Code Examples

See the `examples/` directory for detailed usage examples:
- `example_usage.py` - Basic file operations
- `enhanced_features_examples.py` - Advanced search and depth control
- `patch_examples.py` - Various patching techniques
- `project_directory_examples.py` - Project directory usage
- `ssh_transfer_examples.py` - SSH upload/download operations

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
