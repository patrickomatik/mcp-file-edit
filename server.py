#!/usr/bin/env python3
"""
MCP File Editor Server using FastMCP
Provides comprehensive file system operations through MCP
"""

import os
import re
import stat
import shutil
import base64
import mimetypes
import asyncio
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator, Tuple, AsyncIterator
from datetime import datetime

from code_analyzer import CodeAnalyzer, list_functions, get_function_at_line, get_code_structure, search_functions
from mcp.server.fastmcp import FastMCP
from file_operations import FileOperationsInterface, LocalFileOperations, SSHFileOperations
from ssh_manager import SSHConnectionManager
from git_operations import GitOperations, LocalGitOperations, SSHGitOperations

# Create the MCP server instance
mcp = FastMCP("file-editor")

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

# Global base directory (current working directory)
BASE_DIR = Path.cwd()

# Global project directory (optional, for project-relative paths)
PROJECT_DIR = None

# Global file operations backend and SSH manager
FILE_OPS: FileOperationsInterface = LocalFileOperations()
SSH_MANAGER = SSHConnectionManager()
CONNECTION_TYPE = "local"  # "local" or "ssh"
GIT_OPS: Optional[GitOperations] = None  # Initialized when needed

def is_safe_path(path: Path) -> bool:
    """Check if a path is safe to access (no directory traversal)"""
    try:
        resolved = path.resolve()
        return resolved.is_relative_to(BASE_DIR)
    except (ValueError, RuntimeError):
        return False


def get_git_operations() -> Optional[GitOperations]:
    """Get or initialize git operations based on current connection type."""
    global GIT_OPS
    
    if GIT_OPS is None and PROJECT_DIR is not None:
        if CONNECTION_TYPE == "ssh":
            git_backend = SSHGitOperations(SSH_MANAGER.connection, SSH_MANAGER.sftp)
        else:
            git_backend = LocalGitOperations()
        
        GIT_OPS = GitOperations(git_backend, FILE_OPS, PROJECT_DIR)
    
    return GIT_OPS


def resolve_path(path: str) -> Path:
    """
    Resolve a path relative to project directory if set, otherwise relative to BASE_DIR.
    
    Args:
        path: Input path (can be relative or absolute)
        
    Returns:
        Resolved Path object
    """
    path_obj = Path(path)
    
    # If path is absolute, return as-is
    if path_obj.is_absolute():
        return path_obj
    
    # If project directory is set, resolve relative to it
    if PROJECT_DIR:
        return PROJECT_DIR / path
    
    # Otherwise, resolve relative to BASE_DIR
    return BASE_DIR / path


def get_file_type(path: Path) -> str:
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

async def get_file_info_async(path: Path) -> Dict[str, Any]:
    """Get detailed file information using the current file operations backend"""
    try:
        stat_info = await FILE_OPS.stat(path)
        file_type = get_file_type(path)
        
        info = {
            "name": path.name,
            "path": str(path),
            "type": "directory" if await FILE_OPS.is_dir(path) else "file",
            "size": stat_info.st_size,
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "permissions": stat.filemode(stat_info.st_mode),
            "file_type": file_type
        }
        
        # Add absolute path for local connections
        if CONNECTION_TYPE == "local":
            info["absolute_path"] = str(path.absolute())
            try:
                info["relative_path"] = str(path.relative_to(BASE_DIR))
            except ValueError:
                info["relative_path"] = str(path)
        
        # Add line count for text files
        if file_type == "text" and not await FILE_OPS.is_dir(path):
            try:
                content = await FILE_OPS.read_file(path)
                info["line_count"] = len(content.splitlines())
            except:
                info["line_count"] = None
        
        return info
    except Exception as e:
        return {
            "name": path.name,
            "path": str(path),
            "type": "unknown",
            "error": str(e)
        }

def get_file_info_sync(path: Path) -> Dict[str, Any]:
    """Get detailed file information"""
    try:
        stat_info = path.stat()
        file_type = get_file_type(path)
        
        info = {
            "name": path.name,
            "path": str(path.relative_to(BASE_DIR)),
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

@mcp.tool()
async def list_files(
    path: str = ".",
    pattern: str = "*",
    recursive: bool = False,
    include_hidden: bool = False,
    max_depth: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    List files and directories.

    Args:
        path: Directory path (default: current directory)
        pattern: Glob pattern for filtering
        recursive: List recursively
        include_hidden: Include hidden files
        max_depth: Maximum depth for recursive listing (None for unlimited)

    Returns:
        List of file/directory information
    """
    target_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(target_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    # Check if path exists
    if not await FILE_OPS.exists(target_path):
        raise ValueError(f"Path does not exist: {path}")
    
    # Verify it's a directory
    if not await FILE_OPS.is_dir(target_path):
        raise ValueError(f"Path is not a directory: {path}")
    
    results = []
    
    if recursive:
        # Use async walk for recursive listing
        async for item in walk_with_depth_async(target_path, pattern, max_depth):
            if not include_hidden and item.name.startswith('.'):
                continue
            info = await get_file_info_async(item)
            results.append(info)
    else:
        # List directory contents
        entries = await FILE_OPS.listdir(target_path)
        import fnmatch
        
        for entry_name in entries:
            if not include_hidden and entry_name.startswith('.'):
                continue
            
            if fnmatch.fnmatch(entry_name, pattern):
                entry_path = target_path / entry_name
                info = await get_file_info_async(entry_path)
                results.append(info)
            
    return results

@mcp.tool()
async def read_file(
    path: str,
    encoding: str = "utf-8",
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read file contents.

    Args:
        path: File path
        encoding: File encoding (default: utf-8)
        start_line: Starting line number (1-based)
        end_line: Ending line number (inclusive)

    Returns:
        Dictionary with content, encoding, and file_type
    """
    file_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    # Check if file exists
    if not await FILE_OPS.exists(file_path):
        raise ValueError(f"File does not exist: {path}")
    
    # Verify it's a file
    if not await FILE_OPS.is_file(file_path):
        raise ValueError(f"Not a file: {path}")
    
    file_type = get_file_type(file_path)
    
    if file_type == "binary":
        # Read binary file and encode as base64
        content_bytes = await FILE_OPS.read_binary(file_path)
        content = base64.b64encode(content_bytes).decode('ascii')
        return {
            "content": content,
            "encoding": "base64",
            "file_type": "binary"
        }
    else:
        # Read text file
        content = await FILE_OPS.read_file(file_path, encoding=encoding)
        
        if start_line is not None or end_line is not None:
            lines = content.splitlines(keepends=True)
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else len(lines)
            content = ''.join(lines[start_idx:end_idx])
                
        return {
            "content": content,
            "encoding": encoding,
            "file_type": "text"
        }

@mcp.tool()
async def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = False
) -> Dict[str, Any]:
    """
    Write content to a file.

    Args:
        path: File path
        content: Content to write
        encoding: File encoding (default: utf-8, or 'base64' for binary)
        create_dirs: Create parent directories if needed

    Returns:
        Dictionary with path and size
    """
    file_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    # Create parent directories if requested
    if create_dirs:
        await FILE_OPS.makedirs(file_path.parent, exist_ok=True)
    
    # Write content
    if encoding == "base64":
        # Decode base64 and write as binary
        content_bytes = base64.b64decode(content)
        await FILE_OPS.write_file(file_path, content_bytes)
    else:
        # Write as text
        await FILE_OPS.write_file(file_path, content, encoding=encoding)
    
    # Get file info
    stat_info = await FILE_OPS.stat(file_path)
    
    result = {
        "path": str(file_path),
        "size": stat_info.st_size
    }
    
    # Add relative path for local connections
    if CONNECTION_TYPE == "local":
        try:
            result["relative_path"] = str(file_path.relative_to(BASE_DIR))
        except ValueError:
            result["relative_path"] = str(file_path)
    
    return result

@mcp.tool()
async def create_file(
    path: str,
    content: str = "",
    create_dirs: bool = False
) -> Dict[str, Any]:
    """
    Create a new file.

    Args:
        path: File path
        content: Initial content (supports multi-line strings)
        create_dirs: Create parent directories if needed

    Returns:
        File information
        
    Example:
        # Create a Python file with multi-line content
        create_file(
            path="file_operations.py",
            content=\"\"\"\nFile operations abstraction layer for local and SSH operations.
\"\"\"\n
import os
import stat
import shutil
...
\"\"\"
        )
    """
    file_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    # Check if file already exists
    if await FILE_OPS.exists(file_path):
        raise ValueError(f"File already exists: {path}")
    
    # Create parent directories if requested
    if create_dirs:
        await FILE_OPS.makedirs(file_path.parent, exist_ok=True)
    
    # Create the file with content
    await FILE_OPS.write_file(file_path, content, encoding='utf-8')
    
    # Return file info
    return await get_file_info_async(file_path)


@mcp.tool()
async def ssh_upload(
    local_path: str,
    remote_path: str,
    recursive: bool = False,
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Upload file(s) from local filesystem to remote SSH server.
    
    Args:
        local_path: Local file or directory path to upload
        remote_path: Remote destination path (on SSH server)
        recursive: Upload directories recursively
        overwrite: Overwrite existing files on remote
        
    Returns:
        Dictionary with upload results
    """
    if CONNECTION_TYPE != "ssh":
        raise ValueError("SSH connection not established. Use set_project_directory with connection_type='ssh' first")
    
    # Ensure we have local file operations for reading
    local_ops = LocalFileOperations()
    
    # Parse paths
    local_path_obj = Path(local_path).resolve()
    remote_path_obj = Path(remote_path)
    
    # If remote path is relative, make it relative to PROJECT_DIR
    if not remote_path_obj.is_absolute():
        remote_path_obj = PROJECT_DIR / remote_path_obj
    
    # Check if local path exists
    if not await local_ops.exists(local_path_obj):
        raise ValueError(f"Local path does not exist: {local_path}")
    
    uploaded_files = []
    errors = []
    
    try:
        if await local_ops.is_file(local_path_obj):
            # Upload single file
            try:
                # Check if remote path exists and is a directory
                remote_exists = await FILE_OPS.exists(remote_path_obj)
                if remote_exists and await FILE_OPS.is_dir(remote_path_obj):
                    # If remote is a directory, use same filename
                    remote_file_path = remote_path_obj / local_path_obj.name
                else:
                    # Use remote path as-is
                    remote_file_path = remote_path_obj
                
                # Check if should overwrite
                if await FILE_OPS.exists(remote_file_path) and not overwrite:
                    errors.append({
                        "file": str(local_path_obj),
                        "error": f"Remote file exists and overwrite=False: {remote_file_path}"
                    })
                else:
                    # Read local file
                    content = await local_ops.read(local_path_obj)
                    
                    # Write to remote
                    await FILE_OPS.write(remote_file_path, content)
                    
                    uploaded_files.append({
                        "local": str(local_path_obj),
                        "remote": str(remote_file_path),
                        "size": len(content)
                    })
            except Exception as e:
                errors.append({
                    "file": str(local_path_obj),
                    "error": str(e)
                })
        
        elif await local_ops.is_dir(local_path_obj):
            if not recursive:
                raise ValueError("Directory upload requires recursive=True")
            
            # Create remote directory if it doesn't exist
            if not await FILE_OPS.exists(remote_path_obj):
                await FILE_OPS.makedirs(remote_path_obj)
            
            # Walk through local directory
            for root, dirs, files in os.walk(local_path_obj):
                root_path = Path(root)
                rel_path = root_path.relative_to(local_path_obj)
                
                # Create directories on remote
                for dir_name in dirs:
                    remote_dir = remote_path_obj / rel_path / dir_name
                    try:
                        if not await FILE_OPS.exists(remote_dir):
                            await FILE_OPS.makedirs(remote_dir)
                    except Exception as e:
                        errors.append({
                            "file": str(root_path / dir_name),
                            "error": f"Failed to create remote directory: {e}"
                        })
                
                # Upload files
                for file_name in files:
                    local_file = root_path / file_name
                    remote_file = remote_path_obj / rel_path / file_name
                    
                    try:
                        if await FILE_OPS.exists(remote_file) and not overwrite:
                            errors.append({
                                "file": str(local_file),
                                "error": f"Remote file exists and overwrite=False: {remote_file}"
                            })
                            continue
                        
                        # Read local file
                        content = await local_ops.read(local_file)
                        
                        # Write to remote
                        await FILE_OPS.write(remote_file, content)
                        
                        uploaded_files.append({
                            "local": str(local_file),
                            "remote": str(remote_file),
                            "size": len(content)
                        })
                    except Exception as e:
                        errors.append({
                            "file": str(local_file),
                            "error": str(e)
                        })
    
    except Exception as e:
        raise ValueError(f"Upload failed: {str(e)}")
    
    return {
        "uploaded": len(uploaded_files),
        "errors": len(errors),
        "files": uploaded_files,
        "error_details": errors,
        "total_size": sum(f["size"] for f in uploaded_files)
    }


@mcp.tool()
async def ssh_download(
    remote_path: str,
    local_path: str,
    recursive: bool = False,
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Download file(s) from remote SSH server to local filesystem.
    
    Args:
        remote_path: Remote file or directory path to download (on SSH server)
        local_path: Local destination path
        recursive: Download directories recursively
        overwrite: Overwrite existing local files
        
    Returns:
        Dictionary with download results
    """
    if CONNECTION_TYPE != "ssh":
        raise ValueError("SSH connection not established. Use set_project_directory with connection_type='ssh' first")
    
    # Ensure we have local file operations for writing
    local_ops = LocalFileOperations()
    
    # Parse paths
    local_path_obj = Path(local_path).resolve()
    remote_path_obj = Path(remote_path)
    
    # If remote path is relative, make it relative to PROJECT_DIR
    if not remote_path_obj.is_absolute():
        remote_path_obj = PROJECT_DIR / remote_path_obj
    
    # Check if remote path exists
    if not await FILE_OPS.exists(remote_path_obj):
        raise ValueError(f"Remote path does not exist: {remote_path}")
    
    downloaded_files = []
    errors = []
    
    try:
        if await FILE_OPS.is_file(remote_path_obj):
            # Download single file
            try:
                # Check if local path exists and is a directory
                local_exists = await local_ops.exists(local_path_obj)
                if local_exists and await local_ops.is_dir(local_path_obj):
                    # If local is a directory, use same filename
                    local_file_path = local_path_obj / remote_path_obj.name
                else:
                    # Use local path as-is
                    local_file_path = local_path_obj
                
                # Check if should overwrite
                if await local_ops.exists(local_file_path) and not overwrite:
                    errors.append({
                        "file": str(remote_path_obj),
                        "error": f"Local file exists and overwrite=False: {local_file_path}"
                    })
                else:
                    # Ensure parent directory exists
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Read remote file
                    content = await FILE_OPS.read(remote_path_obj)
                    
                    # Write to local
                    await local_ops.write(local_file_path, content)
                    
                    downloaded_files.append({
                        "remote": str(remote_path_obj),
                        "local": str(local_file_path),
                        "size": len(content)
                    })
            except Exception as e:
                errors.append({
                    "file": str(remote_path_obj),
                    "error": str(e)
                })
        
        elif await FILE_OPS.is_dir(remote_path_obj):
            if not recursive:
                raise ValueError("Directory download requires recursive=True")
            
            # Create local directory if it doesn't exist
            local_path_obj.mkdir(parents=True, exist_ok=True)
            
            # List and download directory contents recursively
            async def download_dir(remote_dir: Path, local_dir: Path):
                # List remote directory contents
                entries = await FILE_OPS.listdir(remote_dir)
                
                for entry in entries:
                    remote_entry = remote_dir / entry
                    local_entry = local_dir / entry
                    
                    try:
                        if await FILE_OPS.is_dir(remote_entry):
                            # Create local directory
                            local_entry.mkdir(exist_ok=True)
                            # Recursively download subdirectory
                            await download_dir(remote_entry, local_entry)
                        else:
                            # Download file
                            if await local_ops.exists(local_entry) and not overwrite:
                                errors.append({
                                    "file": str(remote_entry),
                                    "error": f"Local file exists and overwrite=False: {local_entry}"
                                })
                                continue
                            
                            # Read remote file
                            content = await FILE_OPS.read(remote_entry)
                            
                            # Write to local
                            await local_ops.write(local_entry, content)
                            
                            downloaded_files.append({
                                "remote": str(remote_entry),
                                "local": str(local_entry),
                                "size": len(content)
                            })
                    except Exception as e:
                        errors.append({
                            "file": str(remote_entry),
                            "error": str(e)
                        })
            
            await download_dir(remote_path_obj, local_path_obj)
    
    except Exception as e:
        raise ValueError(f"Download failed: {str(e)}")
    
    return {
        "downloaded": len(downloaded_files),
        "errors": len(errors),
        "files": downloaded_files,
        "error_details": errors,
        "total_size": sum(f["size"] for f in downloaded_files)
    }


@mcp.tool()
async def ssh_sync(
    local_path: str,
    remote_path: str,
    direction: str = "upload",
    delete: bool = False,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Synchronize files between local and remote filesystems.
    
    Args:
        local_path: Local directory path
        remote_path: Remote directory path (on SSH server)
        direction: Sync direction - "upload" (local to remote) or "download" (remote to local)
        delete: Delete files in destination that don't exist in source
        exclude_patterns: List of glob patterns to exclude from sync
        
    Returns:
        Dictionary with sync results
    """
    if CONNECTION_TYPE != "ssh":
        raise ValueError("SSH connection not established. Use set_project_directory with connection_type='ssh' first")
    
    if direction not in ["upload", "download"]:
        raise ValueError("Direction must be 'upload' or 'download'")
    
    # For now, implement basic sync using upload/download
    # This is a simplified version - a full sync would compare timestamps and checksums
    if direction == "upload":
        result = await ssh_upload(
            local_path=local_path,
            remote_path=remote_path,
            recursive=True,
            overwrite=True
        )
    else:
        result = await ssh_download(
            remote_path=remote_path,
            local_path=local_path,
            recursive=True,
            overwrite=True
        )
    
    result["direction"] = direction
    result["sync_completed"] = True
    
    return result


# Git Operations Tools

@mcp.tool()
async def git_status(
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git repository status.
    
    Args:
        path: Path to check status (defaults to project directory)
        
    Returns:
        Dictionary with repository status information
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.status(work_path)


@mcp.tool()
async def git_init(
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize a new git repository.
    
    Args:
        path: Path to initialize repository (defaults to project directory)
        
    Returns:
        Dictionary with initialization result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.init(work_path)


@mcp.tool()
async def git_clone(
    url: str,
    path: Optional[str] = None,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clone a remote git repository.
    
    Args:
        url: Repository URL to clone
        path: Local path to clone into (defaults to project directory)
        branch: Specific branch to clone
        
    Returns:
        Dictionary with clone result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.clone(url, work_path, branch)


@mcp.tool()
async def git_add(
    files: Union[str, List[str]],
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add files to git staging area.
    
    Args:
        files: File(s) to add (string or list of strings)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with add result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.add(files, work_path)


@mcp.tool()
async def git_commit(
    message: str,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Commit staged changes.
    
    Args:
        message: Commit message
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with commit result including commit hash
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.commit(message, work_path)


@mcp.tool()
async def git_push(
    remote: str = "origin",
    branch: Optional[str] = None,
    set_upstream: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Push commits to remote repository.
    
    Args:
        remote: Remote name (default: "origin")
        branch: Branch to push (defaults to current branch)
        set_upstream: Set upstream tracking branch
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with push result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.push(remote, branch, work_path, set_upstream)


@mcp.tool()
async def git_pull(
    remote: str = "origin",
    branch: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pull changes from remote repository.
    
    Args:
        remote: Remote name (default: "origin")
        branch: Branch to pull (defaults to current branch)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with pull result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.pull(remote, branch, work_path)


@mcp.tool()
async def git_log(
    limit: int = 10,
    oneline: bool = True,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git commit log.
    
    Args:
        limit: Number of commits to show (default: 10)
        oneline: Show in compact format (default: True)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with commit log
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.log(limit, oneline, work_path)


@mcp.tool()
async def git_branch(
    create: Optional[str] = None,
    delete: Optional[str] = None,
    list_all: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage git branches.
    
    Args:
        create: Create a new branch with this name
        delete: Delete branch with this name
        list_all: List all branches including remotes
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with branch operation result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.branch(create, delete, list_all, work_path)


@mcp.tool()
async def git_checkout(
    branch: str,
    create: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checkout a branch or commit.
    
    Args:
        branch: Branch or commit to checkout
        create: Create new branch if it doesn't exist
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with checkout result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.checkout(branch, create, work_path)


@mcp.tool()
async def git_diff(
    cached: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git diff output.
    
    Args:
        cached: Show staged changes instead of working directory
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with diff output
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.diff(cached, work_path)


@mcp.tool()
async def git_remote(
    action: str = "list",
    name: Optional[str] = None,
    url: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage git remotes.
    
    Args:
        action: Action to perform - "list", "add", "remove", "get-url"
        name: Remote name (for add/remove/get-url)
        url: Remote URL (for add)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with remote operation result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.remote(action, name, url, work_path)


# Run the server
if __name__ == "__main__":
    mcp.run()

@mcp.tool()
async def delete_file(
    path: str,
    recursive: bool = False
) -> Dict[str, str]:
    """
    Delete a file or directory.

    Args:
        path: File or directory path
        recursive: Delete directories recursively

    Returns:
        Dictionary with deleted path
    """
    target_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(target_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    # Check if path exists
    if not await FILE_OPS.exists(target_path):
        raise ValueError(f"Path does not exist: {path}")
    
    # Delete based on type
    if await FILE_OPS.is_dir(target_path):
        if recursive:
            await FILE_OPS.rmtree(target_path)
        else:
            # For non-recursive directory deletion, check if empty
            entries = await FILE_OPS.listdir(target_path)
            if entries:
                raise ValueError(f"Directory not empty: {path}. Use recursive=True to delete non-empty directories.")
            await FILE_OPS.remove(target_path)
    else:
        await FILE_OPS.remove(target_path)
    
    result = {"deleted": str(target_path)}
    
    # Add relative path for local connections
    if CONNECTION_TYPE == "local":
        try:
            result["deleted_relative"] = str(target_path.relative_to(BASE_DIR))
        except ValueError:
            pass
    
    return result

@mcp.tool()
async def move_file(
    source: str,
    destination: str,
    overwrite: bool = False
) -> Dict[str, str]:
    """
    Move or rename a file.

    Args:
        source: Source path
        destination: Destination path
        overwrite: Overwrite if exists

    Returns:
        Dictionary with source and destination paths
    """
    source_path = resolve_path(source)
    dest_path = resolve_path(destination)
    
    # For local connections, check if paths are safe
    if CONNECTION_TYPE == "local":
        if not is_safe_path(source_path) or not is_safe_path(dest_path):
            raise ValueError("Invalid path: directory traversal detected")
    
    # Check if source exists
    if not await FILE_OPS.exists(source_path):
        raise ValueError(f"Source does not exist: {source}")
    
    # Check destination
    if await FILE_OPS.exists(dest_path) and not overwrite:
        raise ValueError(f"Destination already exists: {destination}")
    
    # Perform the move/rename
    await FILE_OPS.rename(source_path, dest_path)
    
    result = {
        "source": str(source_path),
        "destination": str(dest_path)
    }
    
    # Add relative paths for local connections
    if CONNECTION_TYPE == "local":
        try:
            result["source_relative"] = str(source_path.relative_to(BASE_DIR))
            result["destination_relative"] = str(dest_path.relative_to(BASE_DIR))
        except ValueError:
            pass
    
    return result

@mcp.tool()
async def copy_file(
    source: str,
    destination: str,
    overwrite: bool = False
) -> Dict[str, str]:
    """
    Copy a file or directory.

    Args:
        source: Source path
        destination: Destination path
        overwrite: Overwrite if exists

    Returns:
        Dictionary with source and destination paths
    """
    source_path = resolve_path(source)
    dest_path = resolve_path(destination)
    
    # For local connections, check if paths are safe
    if CONNECTION_TYPE == "local":
        if not is_safe_path(source_path) or not is_safe_path(dest_path):
            raise ValueError("Invalid path: directory traversal detected")
    
    # Check if source exists
    if not await FILE_OPS.exists(source_path):
        raise ValueError(f"Source does not exist: {source}")
    
    # Check destination
    if await FILE_OPS.exists(dest_path) and not overwrite:
        raise ValueError(f"Destination already exists: {destination}")
    
    # Copy based on type
    if await FILE_OPS.is_dir(source_path):
        await FILE_OPS.copy_tree(source_path, dest_path)
    else:
        await FILE_OPS.copy_file(source_path, dest_path)
    
    result = {
        "source": str(source_path),
        "destination": str(dest_path)
    }
    
    # Add relative paths for local connections
    if CONNECTION_TYPE == "local":
        try:
            result["source_relative"] = str(source_path.relative_to(BASE_DIR))
            result["destination_relative"] = str(dest_path.relative_to(BASE_DIR))
        except ValueError:
            pass
    
    return result


async def walk_with_depth_async(path: Path, pattern: str, max_depth: Optional[int] = None) -> AsyncIterator[Path]:
    """Walk directory tree with optional depth limit using current file operations backend"""
    import fnmatch
    
    async def _walk(current_path: Path, current_depth: int = 0) -> AsyncIterator[Path]:
        if max_depth is not None and current_depth > max_depth:
            return
        
        try:
            entries = await FILE_OPS.listdir(current_path)
            for entry_name in entries:
                entry_path = current_path / entry_name
                
                if fnmatch.fnmatch(entry_name, pattern):
                    yield entry_path
                
                if await FILE_OPS.is_dir(entry_path):
                    async for subentry in _walk(entry_path, current_depth + 1):
                        yield subentry
        except Exception:
            pass  # Skip inaccessible directories
    
    async for item in _walk(path):
        yield item

def walk_with_depth(path: Path, pattern: str, max_depth: Optional[int] = None) -> Iterator[Path]:
    """
    Walk directory tree with optional depth limit.
    
    Args:
        path: Starting directory
        pattern: File pattern to match
        max_depth: Maximum depth to traverse (None for unlimited)
        
    Yields:
        Matching file paths
    """
    def _walk(current_path: Path, current_depth: int):
        if max_depth is not None and current_depth > max_depth:
            return
            
        try:
            for item in current_path.iterdir():
                if item.is_file() and item.match(pattern):
                    yield item
                elif item.is_dir() and not item.name.startswith('.'):
                    yield from _walk(item, current_depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    yield from _walk(path, 0)

@mcp.tool()
async def search_files(
    pattern: str,
    path: str = ".",
    file_pattern: str = "*",
    recursive: bool = True,
    max_depth: Optional[int] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Search for patterns in files with timeout and depth control.

    Args:
        pattern: Search pattern (regex)
        path: Directory to search in
        file_pattern: File name pattern
        recursive: Search recursively
        max_depth: Maximum depth for recursive search (None for unlimited)
        timeout: Maximum time in seconds for search operation

    Returns:
        Dictionary containing:
        - results: List of files with matches
        - completed: Whether search completed fully
        - files_searched: Number of files searched
        - timeout_occurred: Whether search timed out
        - error: Any error message
    """
    search_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(search_path):
        return {
            "results": [],
            "completed": False,
            "files_searched": 0,
            "timeout_occurred": False,
            "error": "Invalid path: directory traversal detected"
        }
        
    regex = re.compile(pattern)
    results = []
    files_searched = 0
    timeout_occurred = False
    error = None
    
    async def _search():
        nonlocal files_searched
        
        # Check if search_path exists
        if not await FILE_OPS.exists(search_path):
            raise ValueError(f"Path does not exist: {path}")
        
        files_to_search = []
        
        if await FILE_OPS.is_file(search_path):
            files_to_search = [search_path]
        else:
            if recursive:
                # Use async walk for file discovery
                async for item in walk_with_depth_async(search_path, file_pattern, max_depth):
                    if await FILE_OPS.is_file(item):
                        files_to_search.append(item)
            else:
                # List directory and filter
                import fnmatch
                entries = await FILE_OPS.listdir(search_path)
                for entry_name in entries:
                    if fnmatch.fnmatch(entry_name, file_pattern):
                        entry_path = search_path / entry_name
                        if await FILE_OPS.is_file(entry_path):
                            files_to_search.append(entry_path)
                
        for file_path in files_to_search:
            # Check if we should yield control periodically
            if files_searched % 100 == 0:
                await asyncio.sleep(0)  # Allow other tasks to run
                
            file_type = get_file_type(file_path)
            if file_type != "text":
                continue
                
            matches = []
            try:
                # Read file content
                content = await FILE_OPS.read_file(file_path, encoding='utf-8')
                
                # Search line by line
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        match = regex.search(line)
                        matches.append({
                            "line_number": line_num,
                            "line": line.rstrip(),
                            "column": match.start() if match else 0
                        })
                            
                files_searched += 1
            except Exception as e:
                # Log the error but continue searching
                continue
                
            if matches:
                file_result = {"file": str(file_path)}
                
                # Add relative path for local connections
                if CONNECTION_TYPE == "local":
                    try:
                        file_result["file_relative"] = str(file_path.relative_to(BASE_DIR))
                    except ValueError:
                        pass
                
                file_result["matches"] = matches
                results.append(file_result)
    
    try:
        # Run search with timeout
        await asyncio.wait_for(_search(), timeout=timeout)
        completed = True
    except asyncio.TimeoutError:
        timeout_occurred = True
        completed = False
        error = f"Search timed out after {timeout} seconds. Partial results returned."
    except Exception as e:
        completed = False
        error = str(e)
    
    return {
        "results": results,
        "completed": completed,
        "files_searched": files_searched,
        "timeout_occurred": timeout_occurred,
        "error": error
    }
@mcp.tool()
async def replace_in_files(
    search: str,
    replace: str,
    path: str = ".",
    file_pattern: str = "*",
    recursive: bool = True,
    max_depth: Optional[int] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Replace text in files with timeout and depth control.

    Args:
        search: Search pattern (regex)
        replace: Replacement text
        path: Directory or file path
        file_pattern: File name pattern
        recursive: Search recursively
        max_depth: Maximum depth for recursive search (None for unlimited)
        timeout: Maximum time in seconds for operation

    Returns:
        Dictionary containing:
        - results: List of files with replacement counts
        - completed: Whether operation completed fully
        - files_processed: Number of files processed
        - timeout_occurred: Whether operation timed out
        - error: Any error message
    """
    search_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(search_path):
        return {
            "results": [],
            "completed": False,
            "files_processed": 0,
            "timeout_occurred": False,
            "error": "Invalid path: directory traversal detected"
        }
        
    regex = re.compile(search)
    results = []
    files_processed = 0
    timeout_occurred = False
    error = None
    
    async def _replace():
        nonlocal files_processed
        
        # Check if search_path exists
        if not await FILE_OPS.exists(search_path):
            raise ValueError(f"Path does not exist: {path}")
        
        files_to_process = []
        
        if await FILE_OPS.is_file(search_path):
            files_to_process = [search_path]
        else:
            if recursive:
                # Use async walk for file discovery
                async for item in walk_with_depth_async(search_path, file_pattern, max_depth):
                    if await FILE_OPS.is_file(item):
                        files_to_process.append(item)
            else:
                # List directory and filter
                import fnmatch
                entries = await FILE_OPS.listdir(search_path)
                for entry_name in entries:
                    if fnmatch.fnmatch(entry_name, file_pattern):
                        entry_path = search_path / entry_name
                        if await FILE_OPS.is_file(entry_path):
                            files_to_process.append(entry_path)
                
        for file_path in files_to_process:
            if files_processed % 50 == 0:
                await asyncio.sleep(0)
                
            file_type = get_file_type(file_path)
            if file_type != "text":
                continue
                
            try:
                # Read file content
                content = await FILE_OPS.read_file(file_path, encoding='utf-8')
                
                # Perform replacements
                new_content, count = regex.subn(replace, content)
                
                if count > 0:
                    # Write back the modified content
                    await FILE_OPS.write_file(file_path, new_content, encoding='utf-8')
                    
                    file_result = {"file": str(file_path), "replacements": count}
                    
                    # Add relative path for local connections
                    if CONNECTION_TYPE == "local":
                        try:
                            file_result["file_relative"] = str(file_path.relative_to(BASE_DIR))
                        except ValueError:
                            pass
                    
                    results.append(file_result)
                    
                files_processed += 1
            except Exception:
                continue
    
    try:
        await asyncio.wait_for(_replace(), timeout=timeout)
        completed = True
    except asyncio.TimeoutError:
        timeout_occurred = True
        completed = False
        error = f"Replace operation timed out after {timeout} seconds. Partial results returned."
    except Exception as e:
        completed = False
        error = str(e)
    
    return {
        "results": results,
        "completed": completed,
        "files_processed": files_processed,
        "timeout_occurred": timeout_occurred,
        "error": error
    }


class FilePatcher:
    """Handles various types of file patching operations"""
    
    @staticmethod
    def apply_line_patch(lines: List[str], patch: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """Apply a line-based patch"""
        change_info = {"type": "line", "success": False}
        
        if "line" in patch:
            # Single line replacement
            line_num = patch["line"] - 1  # Convert to 0-based
            if 0 <= line_num < len(lines):
                old_content = lines[line_num].rstrip('\n')
                new_content = patch["content"].rstrip('\n')
                lines[line_num] = new_content + '\n' if lines[line_num].endswith('\n') else new_content
                change_info.update({
                    "line": patch["line"],
                    "old": old_content,
                    "new": new_content,
                    "success": True
                })
        elif "start_line" in patch and "end_line" in patch:
            # Multi-line replacement
            start = patch["start_line"] - 1
            end = patch["end_line"]  # end_line is inclusive, so no -1
            
            if 0 <= start < len(lines) and start < end <= len(lines):
                old_content = [line.rstrip('\n') for line in lines[start:end]]
                new_lines = patch["content"].split('\n')
                
                # Preserve line endings
                for i, new_line in enumerate(new_lines):
                    if i < len(new_lines) - 1 or (start + i < len(lines) and lines[start + i].endswith('\n')):
                        new_lines[i] = new_line + '\n'
                
                lines[start:end] = new_lines
                change_info.update({
                    "start_line": patch["start_line"],
                    "end_line": patch["end_line"],
                    "old": old_content,
                    "new": [line.rstrip('\n') for line in new_lines],
                    "success": True
                })
        
        return lines, change_info
    
    @staticmethod
    def apply_pattern_patch(content: str, patch: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Apply a pattern-based patch"""
        change_info = {"type": "pattern", "success": False}
        
        find_pattern = patch["find"]
        replace_with = patch["replace"]
        occurrence = patch.get("occurrence", None)  # None means all occurrences
        regex = patch.get("regex", False)
        
        if regex:
            pattern = re.compile(find_pattern, re.MULTILINE)
            matches = list(pattern.finditer(content))
            change_info["matches"] = len(matches)
            
            if matches:
                if occurrence is not None:
                    # Replace specific occurrence
                    if 0 < occurrence <= len(matches):
                        match = matches[occurrence - 1]
                        old_text = match.group(0)
                        content = content[:match.start()] + replace_with + content[match.end():]
                        change_info.update({
                            "replaced": 1,
                            "old": old_text,
                            "new": replace_with,
                            "success": True
                        })
                else:
                    # Replace all occurrences
                    old_text = pattern.findall(content)[0] if pattern.findall(content) else ""
                    content, count = pattern.subn(replace_with, content)
                    change_info.update({
                        "replaced": count,
                        "old": old_text,
                        "new": replace_with,
                        "success": count > 0
                    })
        else:
            # Literal string replacement
            occurrences = content.count(find_pattern)
            change_info["matches"] = occurrences
            
            if occurrences > 0:
                if occurrence is not None:
                    # Replace specific occurrence
                    if 0 < occurrence <= occurrences:
                        parts = content.split(find_pattern, occurrence)
                        if len(parts) > occurrence:
                            content = find_pattern.join(parts[:occurrence]) + replace_with + parts[occurrence]
                            change_info.update({
                                "replaced": 1,
                                "old": find_pattern,
                                "new": replace_with,
                                "success": True
                            })
                else:
                    # Replace all occurrences
                    content = content.replace(find_pattern, replace_with)
                    change_info.update({
                        "replaced": occurrences,
                        "old": find_pattern,
                        "new": replace_with,
                        "success": True
                    })
        
        return content, change_info
    
    @staticmethod
    def apply_context_patch(lines: List[str], patch: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """Apply a context-based patch"""
        change_info = {"type": "context", "success": False}
        
        context_lines = patch["context"]
        replacement_lines = patch["replace"]
        
        # Normalize line endings for comparison
        context_normalized = [line.rstrip('\n') for line in context_lines]
        lines_normalized = [line.rstrip('\n') for line in lines]
        
        # Find the context in the file
        for i in range(len(lines_normalized) - len(context_normalized) + 1):
            if lines_normalized[i:i + len(context_normalized)] == context_normalized:
                # Found the context, apply the replacement
                old_content = lines[i:i + len(context_normalized)]
                
                # Prepare replacement with proper line endings
                new_lines = []
                for j, new_line in enumerate(replacement_lines):
                    if j < len(old_content) and old_content[j].endswith('\n'):
                        new_lines.append(new_line + '\n' if not new_line.endswith('\n') else new_line)
                    else:
                        new_lines.append(new_line)
                
                lines[i:i + len(context_normalized)] = new_lines
                
                change_info.update({
                    "line_start": i + 1,
                    "line_end": i + len(context_normalized),
                    "old": [line.rstrip('\n') for line in old_content],
                    "new": [line.rstrip('\n') for line in new_lines],
                    "success": True
                })
                break
        
        return lines, change_info
    
    @staticmethod
    def apply_unified_diff_patch(content: str, patch_content: str) -> Tuple[str, Dict[str, Any]]:
        """Apply a unified diff format patch"""
        change_info = {"type": "unified_diff", "success": False}
        
        # Parse the unified diff
        original_lines = content.splitlines(keepends=True)
        patch_lines = patch_content.splitlines(keepends=True)
        
        # Simple implementation - for more complex patches, consider using python-patch
        # This is a basic implementation that handles simple unified diffs
        try:
            # Apply the patch (simplified version)
            # In production, you'd want to use a proper patch library
            change_info["message"] = "Unified diff patching requires additional implementation"
            change_info["success"] = False
        except Exception as e:
            change_info["error"] = str(e)
        
        return content, change_info


@mcp.tool()
async def set_project_directory(
    path: str,
    connection_type: str = "local",
    ssh_host: Optional[str] = None,
    ssh_username: Optional[str] = None,
    ssh_port: int = 22,
    ssh_key_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set the project directory for relative path operations.
    
    Args:
        path: Path to the project directory (absolute or relative to current directory)
              For SSH: can be a path on the remote system or ssh://user@host:port/path
        connection_type: "local" or "ssh" 
        ssh_host: SSH host (required if connection_type is "ssh" and not using ssh:// URL)
        ssh_username: SSH username (required if connection_type is "ssh" and not using ssh:// URL)
        ssh_port: SSH port (default: 22)
        ssh_key_filename: Path to SSH private key file (default: ~/.ssh/id_rsa)
        
    Returns:
        Dictionary with project directory information
    """
    global PROJECT_DIR, FILE_OPS, CONNECTION_TYPE, GIT_OPS
    
    if connection_type == "ssh":
        # Parse SSH URL if provided
        if path.startswith("ssh://"):
            ssh_params = SSHConnectionManager.parse_ssh_url(path)
            ssh_host = ssh_params['host']
            ssh_username = ssh_params.get('username') or ssh_username
            ssh_port = ssh_params.get('port', ssh_port)
            path = ssh_params['path']
        
        # Validate SSH parameters
        if not ssh_host:
            raise ValueError("SSH host is required for SSH connection")
        if not ssh_username:
            raise ValueError("SSH username is required for SSH connection")
        
        # Set default key if not provided
        if not ssh_key_filename:
            ssh_key_filename = "~/.ssh/id_rsa"
        
        # Connect via SSH
        try:
            conn, sftp = await SSH_MANAGER.connect(
                host=ssh_host,
                username=ssh_username,
                port=ssh_port,
                key_filename=ssh_key_filename
            )
            
            # Create SSH file operations
            FILE_OPS = SSHFileOperations(conn, sftp)
            CONNECTION_TYPE = "ssh"
            
            # Reset git operations to use new connection
            GIT_OPS = None
            
            # Set project directory to the remote path
            PROJECT_DIR = Path(path)
            
            # Verify the directory exists on remote
            if not await FILE_OPS.exists(PROJECT_DIR):
                raise ValueError(f"Remote directory does not exist: {path}")
            
            if not await FILE_OPS.is_dir(PROJECT_DIR):
                raise ValueError(f"Remote path is not a directory: {path}")
            
            return {
                "project_directory": str(PROJECT_DIR),
                "connection_type": "ssh",
                "ssh_host": ssh_host,
                "ssh_username": ssh_username,
                "ssh_port": ssh_port,
                "absolute_path": str(PROJECT_DIR)
            }
            
        except Exception as e:
            # Reset to local on error
            FILE_OPS = LocalFileOperations()
            CONNECTION_TYPE = "local"
            raise ValueError(f"Failed to establish SSH connection: {str(e)}")
    
    else:
        # Local connection
        FILE_OPS = LocalFileOperations()
        CONNECTION_TYPE = "local"
        
        # Reset git operations to use new connection
        GIT_OPS = None
        
        # Close any existing SSH connection
        await SSH_MANAGER.close()
        
        project_path = BASE_DIR / path if not Path(path).is_absolute() else Path(path)
        
        if not is_safe_path(project_path):
            raise ValueError("Invalid path: project directory must be within base directory")
        
        if not project_path.exists():
            raise ValueError(f"Project directory does not exist: {path}")
        
        if not project_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        PROJECT_DIR = project_path
        
        return {
            "project_directory": str(PROJECT_DIR),
            "connection_type": "local",
            "relative_to_base": str(PROJECT_DIR.relative_to(BASE_DIR)),
            "absolute_path": str(PROJECT_DIR.absolute())
        }

@mcp.tool()
async def get_project_directory() -> Dict[str, Any]:
    """
    Get the current project directory.
    
    Returns:
        Dictionary with current project directory information
    """
    if PROJECT_DIR is None:
        return {
            "project_directory": None,
            "connection_type": CONNECTION_TYPE,
            "message": "No project directory set. Use set_project_directory to set one."
        }
    
    result = {
        "project_directory": str(PROJECT_DIR),
        "connection_type": CONNECTION_TYPE,
        "absolute_path": str(PROJECT_DIR.absolute())
    }
    
    # Add local-specific info
    if CONNECTION_TYPE == "local":
        result["relative_to_base"] = str(PROJECT_DIR.relative_to(BASE_DIR))
        result["exists"] = PROJECT_DIR.exists()
    else:
        # For SSH, we're already connected so the directory should exist
        result["ssh_connected"] = SSH_MANAGER.is_connected()
    
    return result



@mcp.tool()
async def list_functions(
    path: str,
    language: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all functions in a code file.
    
    Args:
        path: File path
        language: Programming language (auto-detected if not specified)
        
    Returns:
        List of function information including name, line numbers, signature, etc.
    """
    from code_analyzer import list_functions as _list_functions
    return await _list_functions(path, language)

@mcp.tool()
async def get_function_at_line(
    path: str,
    line_number: int,
    language: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the function that contains a specific line number.
    
    Args:
        path: File path
        line_number: Line number to search for
        language: Programming language (auto-detected if not specified)
        
    Returns:
        Function information if found, None otherwise
    """
    from code_analyzer import get_function_at_line as _get_function_at_line
    return await _get_function_at_line(path, line_number, language)

@mcp.tool()
async def get_code_structure(
    path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the overall code structure of a file.
    
    Args:
        path: File path
        language: Programming language (auto-detected if not specified)
        
    Returns:
        Dictionary containing imports, classes, functions, and other structural elements
    """
    from code_analyzer import get_code_structure as _get_code_structure
    return await _get_code_structure(path, language)

@mcp.tool()
async def search_functions(
    pattern: str,
    path: str = ".",
    file_pattern: str = "*.py",
    recursive: bool = True,
    max_depth: Optional[int] = None
) -> Dict[str, Any]:
    """
    Search for functions by name pattern across files.
    
    Args:
        pattern: Function name pattern (regex)
        path: Directory to search in
        file_pattern: File name pattern
        recursive: Search recursively
        max_depth: Maximum depth for recursive search
        
    Returns:
        Dictionary with search results
    """
    from code_analyzer import search_functions as _search_functions
    return await _search_functions(pattern, path, file_pattern, recursive, max_depth)

@mcp.tool()
async def patch_file(
    path: str,
    patches: List[Dict[str, Any]],
    backup: bool = True,
    dry_run: bool = False,
    create_dirs: bool = False
) -> Dict[str, Any]:
    """
    Apply patches to a file.
    
    Args:
        path: File path to patch
        patches: List of patch operations to apply
        backup: Create a backup before patching
        dry_run: Preview changes without applying them
        create_dirs: Create parent directories if needed
        
    Patch formats:
        Line-based:
            {"line": 10, "content": "new line content"}
            {"start_line": 15, "end_line": 17, "content": "multi-line\\nreplacement"}
            
        Pattern-based:
            {"find": "old text", "replace": "new text", "occurrence": 1}
            {"find": "regex.*pattern", "replace": "replacement", "regex": true}
            
        Context-based:
            {"context": ["line before", "target line", "line after"],
             "replace": ["line before", "new line", "line after"]}
    
    Returns:
        Dict with success status, patches applied, backup path, and change details
    """
    file_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(file_path):
        return {
            "success": False,
            "error": "Invalid path: directory traversal detected",
            "patches_applied": 0
        }
    
    # Check if file exists
    if not await FILE_OPS.exists(file_path):
        if create_dirs and patches:
            await FILE_OPS.makedirs(file_path.parent, exist_ok=True)
            await FILE_OPS.write_file(file_path, "", encoding='utf-8')
        else:
            return {
                "success": False,
                "error": f"File does not exist: {path}",
                "patches_applied": 0
            }
    
    # Check if file is text
    file_type = get_file_type(file_path)
    if file_type != "text":
        return {
            "success": False,
            "error": f"Cannot patch binary file: {path}",
            "patches_applied": 0
        }
    
    # Read the file
    try:
        original_content = await FILE_OPS.read_file(file_path, encoding='utf-8')
        lines = original_content.splitlines(keepends=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "patches_applied": 0
        }
    
    # Create backup if requested
    backup_path = None
    if backup and not dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.backup_{timestamp}"
        try:
            await FILE_OPS.write_file(backup_path, original_content, encoding='utf-8')
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating backup: {str(e)}",
                "patches_applied": 0
            }
    
    # Apply patches
    patcher = FilePatcher()
    changes = []
    patches_applied = 0
    content = original_content
    
    for i, patch in enumerate(patches):
        try:
            if "line" in patch or "start_line" in patch:
                # Line-based patch
                lines, change_info = patcher.apply_line_patch(lines, patch)
                if change_info["success"]:
                    patches_applied += 1
                    content = ''.join(lines)
                changes.append(change_info)
                
            elif "find" in patch:
                # Pattern-based patch
                content, change_info = patcher.apply_pattern_patch(content, patch)
                if change_info["success"]:
                    patches_applied += 1
                    lines = content.splitlines(keepends=True)
                changes.append(change_info)
                
            elif "context" in patch:
                # Context-based patch
                lines, change_info = patcher.apply_context_patch(lines, patch)
                if change_info["success"]:
                    patches_applied += 1
                    content = ''.join(lines)
                changes.append(change_info)
                
            elif "unified_diff" in patch:
                # Unified diff patch
                content, change_info = patcher.apply_unified_diff_patch(content, patch["unified_diff"])
                if change_info["success"]:
                    patches_applied += 1
                    lines = content.splitlines(keepends=True)
                changes.append(change_info)
                
            else:
                changes.append({
                    "type": "unknown",
                    "success": False,
                    "error": f"Unknown patch type in patch {i+1}"
                })
                
        except Exception as e:
            changes.append({
                "type": "error",
                "success": False,
                "error": f"Error in patch {i+1}: {str(e)}"
            })
    
    # Write the file if not dry run and at least one patch succeeded
    if not dry_run and patches_applied > 0:
        try:
            await FILE_OPS.write_file(file_path, content, encoding='utf-8')
        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}",
                "patches_applied": patches_applied,
                "changes": changes
            }
    
    return {
        "success": patches_applied > 0,
        "patches_applied": patches_applied,
        "patches_total": len(patches),
        "backup_path": str(backup_path) if backup_path else None,
        "changes": changes,
        "dry_run": dry_run
    }

@mcp.tool()
async def get_file_info(path: str) -> Dict[str, Any]:
    """
    Get detailed file information.

    Args:
        path: File path

    Returns:
        Detailed file information
    """
    file_path = resolve_path(path)
    
    # For local connections, check if path is safe
    if CONNECTION_TYPE == "local" and not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    # Check if path exists
    if not await FILE_OPS.exists(file_path):
        raise ValueError(f"Path does not exist: {path}")
    
    return await get_file_info_async(file_path)


@mcp.tool()
async def ssh_upload(
    local_path: str,
    remote_path: str,
    recursive: bool = False,
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Upload file(s) from local filesystem to remote SSH server.
    
    Args:
        local_path: Local file or directory path to upload
        remote_path: Remote destination path (on SSH server)
        recursive: Upload directories recursively
        overwrite: Overwrite existing files on remote
        
    Returns:
        Dictionary with upload results
    """
    if CONNECTION_TYPE != "ssh":
        raise ValueError("SSH connection not established. Use set_project_directory with connection_type='ssh' first")
    
    # Ensure we have local file operations for reading
    local_ops = LocalFileOperations()
    
    # Parse paths
    local_path_obj = Path(local_path).resolve()
    remote_path_obj = Path(remote_path)
    
    # If remote path is relative, make it relative to PROJECT_DIR
    if not remote_path_obj.is_absolute():
        remote_path_obj = PROJECT_DIR / remote_path_obj
    
    # Check if local path exists
    if not await local_ops.exists(local_path_obj):
        raise ValueError(f"Local path does not exist: {local_path}")
    
    uploaded_files = []
    errors = []
    
    try:
        if await local_ops.is_file(local_path_obj):
            # Upload single file
            try:
                # Check if remote path exists and is a directory
                remote_exists = await FILE_OPS.exists(remote_path_obj)
                if remote_exists and await FILE_OPS.is_dir(remote_path_obj):
                    # If remote is a directory, use same filename
                    remote_file_path = remote_path_obj / local_path_obj.name
                else:
                    # Use remote path as-is
                    remote_file_path = remote_path_obj
                
                # Check if should overwrite
                if await FILE_OPS.exists(remote_file_path) and not overwrite:
                    errors.append({
                        "file": str(local_path_obj),
                        "error": f"Remote file exists and overwrite=False: {remote_file_path}"
                    })
                else:
                    # Read local file
                    content = await local_ops.read(local_path_obj)
                    
                    # Write to remote
                    await FILE_OPS.write(remote_file_path, content)
                    
                    uploaded_files.append({
                        "local": str(local_path_obj),
                        "remote": str(remote_file_path),
                        "size": len(content)
                    })
            except Exception as e:
                errors.append({
                    "file": str(local_path_obj),
                    "error": str(e)
                })
        
        elif await local_ops.is_dir(local_path_obj):
            if not recursive:
                raise ValueError("Directory upload requires recursive=True")
            
            # Create remote directory if it doesn't exist
            if not await FILE_OPS.exists(remote_path_obj):
                await FILE_OPS.makedirs(remote_path_obj)
            
            # Walk through local directory
            for root, dirs, files in os.walk(local_path_obj):
                root_path = Path(root)
                rel_path = root_path.relative_to(local_path_obj)
                
                # Create directories on remote
                for dir_name in dirs:
                    remote_dir = remote_path_obj / rel_path / dir_name
                    try:
                        if not await FILE_OPS.exists(remote_dir):
                            await FILE_OPS.makedirs(remote_dir)
                    except Exception as e:
                        errors.append({
                            "file": str(root_path / dir_name),
                            "error": f"Failed to create remote directory: {e}"
                        })
                
                # Upload files
                for file_name in files:
                    local_file = root_path / file_name
                    remote_file = remote_path_obj / rel_path / file_name
                    
                    try:
                        if await FILE_OPS.exists(remote_file) and not overwrite:
                            errors.append({
                                "file": str(local_file),
                                "error": f"Remote file exists and overwrite=False: {remote_file}"
                            })
                            continue
                        
                        # Read local file
                        content = await local_ops.read(local_file)
                        
                        # Write to remote
                        await FILE_OPS.write(remote_file, content)
                        
                        uploaded_files.append({
                            "local": str(local_file),
                            "remote": str(remote_file),
                            "size": len(content)
                        })
                    except Exception as e:
                        errors.append({
                            "file": str(local_file),
                            "error": str(e)
                        })
    
    except Exception as e:
        raise ValueError(f"Upload failed: {str(e)}")
    
    return {
        "uploaded": len(uploaded_files),
        "errors": len(errors),
        "files": uploaded_files,
        "error_details": errors,
        "total_size": sum(f["size"] for f in uploaded_files)
    }


@mcp.tool()
async def ssh_download(
    remote_path: str,
    local_path: str,
    recursive: bool = False,
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Download file(s) from remote SSH server to local filesystem.
    
    Args:
        remote_path: Remote file or directory path to download (on SSH server)
        local_path: Local destination path
        recursive: Download directories recursively
        overwrite: Overwrite existing local files
        
    Returns:
        Dictionary with download results
    """
    if CONNECTION_TYPE != "ssh":
        raise ValueError("SSH connection not established. Use set_project_directory with connection_type='ssh' first")
    
    # Ensure we have local file operations for writing
    local_ops = LocalFileOperations()
    
    # Parse paths
    local_path_obj = Path(local_path).resolve()
    remote_path_obj = Path(remote_path)
    
    # If remote path is relative, make it relative to PROJECT_DIR
    if not remote_path_obj.is_absolute():
        remote_path_obj = PROJECT_DIR / remote_path_obj
    
    # Check if remote path exists
    if not await FILE_OPS.exists(remote_path_obj):
        raise ValueError(f"Remote path does not exist: {remote_path}")
    
    downloaded_files = []
    errors = []
    
    try:
        if await FILE_OPS.is_file(remote_path_obj):
            # Download single file
            try:
                # Check if local path exists and is a directory
                local_exists = await local_ops.exists(local_path_obj)
                if local_exists and await local_ops.is_dir(local_path_obj):
                    # If local is a directory, use same filename
                    local_file_path = local_path_obj / remote_path_obj.name
                else:
                    # Use local path as-is
                    local_file_path = local_path_obj
                
                # Check if should overwrite
                if await local_ops.exists(local_file_path) and not overwrite:
                    errors.append({
                        "file": str(remote_path_obj),
                        "error": f"Local file exists and overwrite=False: {local_file_path}"
                    })
                else:
                    # Ensure parent directory exists
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Read remote file
                    content = await FILE_OPS.read(remote_path_obj)
                    
                    # Write to local
                    await local_ops.write(local_file_path, content)
                    
                    downloaded_files.append({
                        "remote": str(remote_path_obj),
                        "local": str(local_file_path),
                        "size": len(content)
                    })
            except Exception as e:
                errors.append({
                    "file": str(remote_path_obj),
                    "error": str(e)
                })
        
        elif await FILE_OPS.is_dir(remote_path_obj):
            if not recursive:
                raise ValueError("Directory download requires recursive=True")
            
            # Create local directory if it doesn't exist
            local_path_obj.mkdir(parents=True, exist_ok=True)
            
            # List and download directory contents recursively
            async def download_dir(remote_dir: Path, local_dir: Path):
                # List remote directory contents
                entries = await FILE_OPS.listdir(remote_dir)
                
                for entry in entries:
                    remote_entry = remote_dir / entry
                    local_entry = local_dir / entry
                    
                    try:
                        if await FILE_OPS.is_dir(remote_entry):
                            # Create local directory
                            local_entry.mkdir(exist_ok=True)
                            # Recursively download subdirectory
                            await download_dir(remote_entry, local_entry)
                        else:
                            # Download file
                            if await local_ops.exists(local_entry) and not overwrite:
                                errors.append({
                                    "file": str(remote_entry),
                                    "error": f"Local file exists and overwrite=False: {local_entry}"
                                })
                                continue
                            
                            # Read remote file
                            content = await FILE_OPS.read(remote_entry)
                            
                            # Write to local
                            await local_ops.write(local_entry, content)
                            
                            downloaded_files.append({
                                "remote": str(remote_entry),
                                "local": str(local_entry),
                                "size": len(content)
                            })
                    except Exception as e:
                        errors.append({
                            "file": str(remote_entry),
                            "error": str(e)
                        })
            
            await download_dir(remote_path_obj, local_path_obj)
    
    except Exception as e:
        raise ValueError(f"Download failed: {str(e)}")
    
    return {
        "downloaded": len(downloaded_files),
        "errors": len(errors),
        "files": downloaded_files,
        "error_details": errors,
        "total_size": sum(f["size"] for f in downloaded_files)
    }


@mcp.tool()
async def ssh_sync(
    local_path: str,
    remote_path: str,
    direction: str = "upload",
    delete: bool = False,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Synchronize files between local and remote filesystems.
    
    Args:
        local_path: Local directory path
        remote_path: Remote directory path (on SSH server)
        direction: Sync direction - "upload" (local to remote) or "download" (remote to local)
        delete: Delete files in destination that don't exist in source
        exclude_patterns: List of glob patterns to exclude from sync
        
    Returns:
        Dictionary with sync results
    """
    if CONNECTION_TYPE != "ssh":
        raise ValueError("SSH connection not established. Use set_project_directory with connection_type='ssh' first")
    
    if direction not in ["upload", "download"]:
        raise ValueError("Direction must be 'upload' or 'download'")
    
    # For now, implement basic sync using upload/download
    # This is a simplified version - a full sync would compare timestamps and checksums
    if direction == "upload":
        result = await ssh_upload(
            local_path=local_path,
            remote_path=remote_path,
            recursive=True,
            overwrite=True
        )
    else:
        result = await ssh_download(
            remote_path=remote_path,
            local_path=local_path,
            recursive=True,
            overwrite=True
        )
    
    result["direction"] = direction
    result["sync_completed"] = True
    
    return result


# Git Operations Tools

@mcp.tool()
async def git_status(
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git repository status.
    
    Args:
        path: Path to check status (defaults to project directory)
        
    Returns:
        Dictionary with repository status information
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.status(work_path)


@mcp.tool()
async def git_init(
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize a new git repository.
    
    Args:
        path: Path to initialize repository (defaults to project directory)
        
    Returns:
        Dictionary with initialization result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.init(work_path)


@mcp.tool()
async def git_clone(
    url: str,
    path: Optional[str] = None,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clone a remote git repository.
    
    Args:
        url: Repository URL to clone
        path: Local path to clone into (defaults to project directory)
        branch: Specific branch to clone
        
    Returns:
        Dictionary with clone result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.clone(url, work_path, branch)


@mcp.tool()
async def git_add(
    files: Union[str, List[str]],
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add files to git staging area.
    
    Args:
        files: File(s) to add (string or list of strings)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with add result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.add(files, work_path)


@mcp.tool()
async def git_commit(
    message: str,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Commit staged changes.
    
    Args:
        message: Commit message
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with commit result including commit hash
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.commit(message, work_path)


@mcp.tool()
async def git_push(
    remote: str = "origin",
    branch: Optional[str] = None,
    set_upstream: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Push commits to remote repository.
    
    Args:
        remote: Remote name (default: "origin")
        branch: Branch to push (defaults to current branch)
        set_upstream: Set upstream tracking branch
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with push result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.push(remote, branch, work_path, set_upstream)


@mcp.tool()
async def git_pull(
    remote: str = "origin",
    branch: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pull changes from remote repository.
    
    Args:
        remote: Remote name (default: "origin")
        branch: Branch to pull (defaults to current branch)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with pull result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.pull(remote, branch, work_path)


@mcp.tool()
async def git_log(
    limit: int = 10,
    oneline: bool = True,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git commit log.
    
    Args:
        limit: Number of commits to show (default: 10)
        oneline: Show in compact format (default: True)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with commit log
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.log(limit, oneline, work_path)


@mcp.tool()
async def git_branch(
    create: Optional[str] = None,
    delete: Optional[str] = None,
    list_all: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage git branches.
    
    Args:
        create: Create a new branch with this name
        delete: Delete branch with this name
        list_all: List all branches including remotes
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with branch operation result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.branch(create, delete, list_all, work_path)


@mcp.tool()
async def git_checkout(
    branch: str,
    create: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checkout a branch or commit.
    
    Args:
        branch: Branch or commit to checkout
        create: Create new branch if it doesn't exist
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with checkout result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.checkout(branch, create, work_path)


@mcp.tool()
async def git_diff(
    cached: bool = False,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git diff output.
    
    Args:
        cached: Show staged changes instead of working directory
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with diff output
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.diff(cached, work_path)


@mcp.tool()
async def git_remote(
    action: str = "list",
    name: Optional[str] = None,
    url: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage git remotes.
    
    Args:
        action: Action to perform - "list", "add", "remove", "get-url"
        name: Remote name (for add/remove/get-url)
        url: Remote URL (for add)
        path: Repository path (defaults to project directory)
        
    Returns:
        Dictionary with remote operation result
    """
    git_ops = get_git_operations()
    if not git_ops:
        raise ValueError("No project directory set. Use set_project_directory first.")
    
    work_path = Path(path) if path else None
    return await git_ops.remote(action, name, url, work_path)


# Run the server
if __name__ == "__main__":
    mcp.run()
