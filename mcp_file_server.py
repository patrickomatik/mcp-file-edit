#!/usr/bin/env python3
"""
MCP File Editor Server
A Model Context Protocol server for file system operations via stdio transport.
"""

import json
import sys
import os
import re
import stat
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import mimetypes
import base64

# MCP Protocol version
MCP_VERSION = "0.1.0"

# File type classifications
TEXT_EXTENSIONS = {
    '.txt', '.md', '.markdown', '.rst', '.log', '.csv', '.tsv',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.html', '.htm', '.xhtml', '.css', '.scss', '.sass',
    '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
    '.py', '.pyw', '.pyx', '.pyi', '.pyc',
    '.java', '.kt', '.scala', '.groovy',
    '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.c++',
    '.cs', '.fs', '.vb', '.swift', '.m', '.mm',
    '.go', '.rs', '.zig', '.nim', '.d',
    '.rb', '.php', '.pl', '.pm', '.lua',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    '.sql', '.r', '.R', '.jl', '.m', '.mat',
    '.tex', '.bib', '.cls', '.sty',
    '.Dockerfile', '.dockerignore', '.gitignore', '.env'
}

BINARY_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
    '.exe', '.dll', '.so', '.dylib', '.a', '.o',
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
    '.ttf', '.otf', '.woff', '.woff2', '.eot'
}

class MCPFileServer:
    """MCP File Editor Server implementation"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.request_id = 0
        
    def send_message(self, message: Dict[str, Any]):
        """Send a message following MCP stdio transport protocol"""
        json_str = json.dumps(message, separators=(',', ':'))
        sys.stdout.write(json_str + '\n')
        sys.stdout.flush()
        
    def send_error(self, id: Optional[int], code: int, message: str, data: Any = None):
        """Send an error response"""
        error = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": id
        }
        if data is not None:
            error["error"]["data"] = data
        self.send_message(error)
        
    def send_result(self, id: int, result: Any):
        """Send a successful result"""
        self.send_message({
            "jsonrpc": "2.0",
            "result": result,
            "id": id
        })
        
    def is_safe_path(self, path: Path) -> bool:
        """Check if a path is safe to access (no directory traversal)"""
        try:
            resolved = path.resolve()
            return resolved.is_relative_to(self.base_dir)
        except (ValueError, RuntimeError):
            return False
            
    def get_file_type(self, path: Path) -> str:
        """Determine file type"""
        suffix = path.suffix.lower()
        if suffix in TEXT_EXTENSIONS or path.name in TEXT_EXTENSIONS:
            return "text"
        elif suffix in BINARY_EXTENSIONS:
            return "binary"
        else:
            # Try to detect using mimetypes
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type:
                if mime_type.startswith('text/'):
                    return "text"
                elif mime_type.startswith(('image/', 'audio/', 'video/', 'application/')):
                    return "binary"
            return "unknown"
            
    def get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get detailed file information"""
        try:
            stat_info = path.stat()
            file_type = self.get_file_type(path)
            
            info = {
                "name": path.name,
                "path": str(path.relative_to(self.base_dir)),
                "absolute_path": str(path.absolute()),
                "type": "directory" if path.is_dir() else "file",
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "permissions": stat.filemode(stat_info.st_mode),
                "file_type": file_type
            }
            
            # Add line count for text files
            if file_type == "text" and path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        info["line_count"] = sum(1 for _ in f)
                except:
                    info["line_count"] = None
                    
            return info
        except Exception as e:
            return {
                "name": path.name,
                "error": str(e)
            }
            
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {
                    "list_files": {},
                    "read_file": {},
                    "write_file": {},
                    "create_file": {},
                    "delete_file": {},
                    "move_file": {},
                    "copy_file": {},
                    "search_files": {},
                    "replace_in_files": {},
                    "get_file_info": {}
                }
            },
            "serverInfo": {
                "name": "mcp-file-editor",
                "version": "1.0.0"
            }
        }
        
    def handle_list_tools(self) -> List[Dict[str, Any]]:
        """Return available tools"""
        return [
            {
                "name": "list_files",
                "description": "List files and directories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path (default: current directory)"},
                        "pattern": {"type": "string", "description": "Glob pattern for filtering"},
                        "recursive": {"type": "boolean", "description": "List recursively"},
                        "include_hidden": {"type": "boolean", "description": "Include hidden files"}
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read file contents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "encoding": {"type": "string", "description": "File encoding (default: utf-8)"},
                        "lines": {"type": "object", "properties": {
                            "start": {"type": "integer"},
                            "end": {"type": "integer"}
                        }}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Content to write"},
                        "encoding": {"type": "string", "description": "File encoding (default: utf-8)"},
                        "create_dirs": {"type": "boolean", "description": "Create parent directories if needed"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "create_file",
                "description": "Create a new file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Initial content"},
                        "create_dirs": {"type": "boolean", "description": "Create parent directories if needed"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "delete_file",
                "description": "Delete a file or directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File or directory path"},
                        "recursive": {"type": "boolean", "description": "Delete directories recursively"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "move_file",
                "description": "Move or rename a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "description": "Source path"},
                        "destination": {"type": "string", "description": "Destination path"},
                        "overwrite": {"type": "boolean", "description": "Overwrite if exists"}
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "copy_file",
                "description": "Copy a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "description": "Source path"},
                        "destination": {"type": "string", "description": "Destination path"},
                        "overwrite": {"type": "boolean", "description": "Overwrite if exists"}
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "search_files",
                "description": "Search for patterns in files",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory to search in"},
                        "pattern": {"type": "string", "description": "Search pattern (regex)"},
                        "file_pattern": {"type": "string", "description": "File name pattern"},
                        "recursive": {"type": "boolean", "description": "Search recursively"}
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "replace_in_files",
                "description": "Replace text in files",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory or file path"},
                        "search": {"type": "string", "description": "Search pattern (regex)"},
                        "replace": {"type": "string", "description": "Replacement text"},
                        "file_pattern": {"type": "string", "description": "File name pattern"},
                        "recursive": {"type": "boolean", "description": "Search recursively"}
                    },
                    "required": ["search", "replace"]
                }
            },
            {
                "name": "get_file_info",
                "description": "Get detailed file information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    },
                    "required": ["path"]
                }
            }
        ]
        
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle tool invocation"""
        handlers = {
            "list_files": self.tool_list_files,
            "read_file": self.tool_read_file,
            "write_file": self.tool_write_file,
            "create_file": self.tool_create_file,
            "delete_file": self.tool_delete_file,
            "move_file": self.tool_move_file,
            "copy_file": self.tool_copy_file,
            "search_files": self.tool_search_files,
            "replace_in_files": self.tool_replace_in_files,
            "get_file_info": self.tool_get_file_info
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        return handler(arguments)
        
    def tool_list_files(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List files in a directory"""
        path_str = args.get("path", ".")
        pattern = args.get("pattern", "*")
        recursive = args.get("recursive", False)
        include_hidden = args.get("include_hidden", False)
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        if not path.exists():
            raise ValueError(f"Path does not exist: {path_str}")
            
        results = []
        
        if recursive:
            for item in path.rglob(pattern):
                if not include_hidden and item.name.startswith('.'):
                    continue
                results.append(self.get_file_info(item))
        else:
            for item in path.glob(pattern):
                if not include_hidden and item.name.startswith('.'):
                    continue
                results.append(self.get_file_info(item))
                
        return results
        
    def tool_read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        path_str = args["path"]
        encoding = args.get("encoding", "utf-8")
        lines = args.get("lines")
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        if not path.exists():
            raise ValueError(f"File does not exist: {path_str}")
            
        if not path.is_file():
            raise ValueError(f"Not a file: {path_str}")
            
        file_type = self.get_file_type(path)
        
        if file_type == "binary":
            # Read binary file and encode as base64
            with open(path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
            return {
                "content": content,
                "encoding": "base64",
                "file_type": "binary"
            }
        else:
            # Read text file
            with open(path, 'r', encoding=encoding) as f:
                if lines:
                    start = lines.get("start", 1) - 1
                    end = lines.get("end")
                    file_lines = f.readlines()
                    if end:
                        content = ''.join(file_lines[start:end])
                    else:
                        content = ''.join(file_lines[start:])
                else:
                    content = f.read()
                    
            return {
                "content": content,
                "encoding": encoding,
                "file_type": "text"
            }
            
    def tool_write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file"""
        path_str = args["path"]
        content = args["content"]
        encoding = args.get("encoding", "utf-8")
        create_dirs = args.get("create_dirs", False)
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        # Check if content is base64 encoded
        if encoding == "base64":
            content_bytes = base64.b64decode(content)
            with open(path, 'wb') as f:
                f.write(content_bytes)
        else:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
                
        return {
            "path": str(path.relative_to(self.base_dir)),
            "size": path.stat().st_size
        }
        
    def tool_create_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file"""
        path_str = args["path"]
        content = args.get("content", "")
        create_dirs = args.get("create_dirs", False)
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        if path.exists():
            raise ValueError(f"File already exists: {path_str}")
            
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return self.get_file_info(path)
        
    def tool_delete_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file or directory"""
        path_str = args["path"]
        recursive = args.get("recursive", False)
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        if not path.exists():
            raise ValueError(f"Path does not exist: {path_str}")
            
        if path.is_dir():
            if recursive:
                import shutil
                shutil.rmtree(path)
            else:
                path.rmdir()
        else:
            path.unlink()
            
        return {"deleted": str(path.relative_to(self.base_dir))}
        
    def tool_move_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Move or rename a file"""
        source_str = args["source"]
        dest_str = args["destination"]
        overwrite = args.get("overwrite", False)
        
        source = self.base_dir / source_str
        dest = self.base_dir / dest_str
        
        if not self.is_safe_path(source) or not self.is_safe_path(dest):
            raise ValueError("Invalid path: directory traversal detected")
            
        if not source.exists():
            raise ValueError(f"Source does not exist: {source_str}")
            
        if dest.exists() and not overwrite:
            raise ValueError(f"Destination already exists: {dest_str}")
            
        source.rename(dest)
        
        return {
            "source": str(source.relative_to(self.base_dir)),
            "destination": str(dest.relative_to(self.base_dir))
        }
        
    def tool_copy_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Copy a file"""
        source_str = args["source"]
        dest_str = args["destination"]
        overwrite = args.get("overwrite", False)
        
        source = self.base_dir / source_str
        dest = self.base_dir / dest_str
        
        if not self.is_safe_path(source) or not self.is_safe_path(dest):
            raise ValueError("Invalid path: directory traversal detected")
            
        if not source.exists():
            raise ValueError(f"Source does not exist: {source_str}")
            
        if dest.exists() and not overwrite:
            raise ValueError(f"Destination already exists: {dest_str}")
            
        import shutil
        if source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=overwrite)
        else:
            shutil.copy2(source, dest)
            
        return {
            "source": str(source.relative_to(self.base_dir)),
            "destination": str(dest.relative_to(self.base_dir))
        }
        
    def tool_search_files(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for patterns in files"""
        path_str = args.get("path", ".")
        pattern = args["pattern"]
        file_pattern = args.get("file_pattern", "*")
        recursive = args.get("recursive", True)
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        regex = re.compile(pattern)
        results = []
        
        if path.is_file():
            files = [path]
        else:
            if recursive:
                files = path.rglob(file_pattern)
            else:
                files = path.glob(file_pattern)
                
        for file_path in files:
            if not file_path.is_file():
                continue
                
            file_type = self.get_file_type(file_path)
            if file_type != "text":
                continue
                
            matches = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append({
                                "line_number": line_num,
                                "line": line.rstrip(),
                                "column": regex.search(line).start()
                            })
            except Exception as e:
                continue
                
            if matches:
                results.append({
                    "file": str(file_path.relative_to(self.base_dir)),
                    "matches": matches
                })
                
        return results
        
    def tool_replace_in_files(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Replace text in files"""
        path_str = args.get("path", ".")
        search = args["search"]
        replace = args["replace"]
        file_pattern = args.get("file_pattern", "*")
        recursive = args.get("recursive", True)
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        regex = re.compile(search)
        results = []
        
        if path.is_file():
            files = [path]
        else:
            if recursive:
                files = path.rglob(file_pattern)
            else:
                files = path.glob(file_pattern)
                
        for file_path in files:
            if not file_path.is_file():
                continue
                
            file_type = self.get_file_type(file_path)
            if file_type != "text":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                new_content, count = regex.subn(replace, content)
                
                if count > 0:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
                    results.append({
                        "file": str(file_path.relative_to(self.base_dir)),
                        "replacements": count
                    })
            except Exception as e:
                continue
                
        return results
        
    def tool_get_file_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed file information"""
        path_str = args["path"]
        
        path = self.base_dir / path_str
        if not self.is_safe_path(path):
            raise ValueError("Invalid path: directory traversal detected")
            
        if not path.exists():
            raise ValueError(f"Path does not exist: {path_str}")
            
        return self.get_file_info(path)
        
    def handle_request(self, request: Dict[str, Any]):
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        id = request.get("id")
        
        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = {"tools": self.handle_list_tools()}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = self.handle_tool_call(tool_name, arguments)
            else:
                self.send_error(id, -32601, f"Method not found: {method}")
                return
                
            if id is not None:
                self.send_result(id, result)
                
        except Exception as e:
            self.send_error(
                id, 
                -32603, 
                f"Internal error: {str(e)}",
                {"traceback": traceback.format_exc()}
            )
            
    def run(self):
        """Main server loop"""
        # Send server info notification
        self.send_message({
            "jsonrpc": "2.0",
            "method": "server_info",
            "params": {
                "name": "mcp-file-editor",
                "version": "1.0.0",
                "protocol_version": MCP_VERSION
            }
        })
        
        # Read requests from stdin
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                self.handle_request(request)
            except json.JSONDecodeError as e:
                self.send_error(None, -32700, f"Parse error: {str(e)}")
            except Exception as e:
                self.send_error(None, -32603, f"Internal error: {str(e)}")

def main():
    """Entry point"""
    server = MCPFileServer()
    try:
        server.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
