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
from typing import List, Dict, Any, Optional, Union, Iterator, Tuple
from datetime import datetime

from code_analyzer import CodeAnalyzer, list_functions, get_function_at_line, get_code_structure, search_functions
from mcp.server.fastmcp import FastMCP

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

def is_safe_path(path: Path) -> bool:
    """Check if a path is safe to access (no directory traversal)"""
    try:
        resolved = path.resolve()
        return resolved.is_relative_to(BASE_DIR)
    except (ValueError, RuntimeError):
        return False


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

def get_file_info(path: Path) -> Dict[str, Any]:
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
    if not is_safe_path(target_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if not target_path.exists():
        raise ValueError(f"Path does not exist: {path}")
        
    results = []
    
    if recursive:
        if max_depth is not None:
            # Use depth-limited walk
            for item in walk_with_depth(target_path, pattern, max_depth):
                if not include_hidden and item.name.startswith('.'):
                    continue
                results.append(get_file_info(item))
        else:
            for item in target_path.rglob(pattern):
                if not include_hidden and item.name.startswith('.'):
                    continue
                results.append(get_file_info(item))
    else:
        for item in target_path.glob(pattern):
            if not include_hidden and item.name.startswith('.'):
                continue
            results.append(get_file_info(item))
            
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
    if not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if not file_path.exists():
        raise ValueError(f"File does not exist: {path}")
        
    if not file_path.is_file():
        raise ValueError(f"Not a file: {path}")
        
    file_type = get_file_type(file_path)
    
    if file_type == "binary":
        # Read binary file and encode as base64
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('ascii')
        return {
            "content": content,
            "encoding": "base64",
            "file_type": "binary"
        }
    else:
        # Read text file
        with open(file_path, 'r', encoding=encoding) as f:
            if start_line is not None or end_line is not None:
                lines = f.readlines()
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                content = ''.join(lines[start_idx:end_idx])
            else:
                content = f.read()
                
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
    if not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
    # Check if content is base64 encoded
    if encoding == "base64":
        content_bytes = base64.b64decode(content)
        with open(file_path, 'wb') as f:
            f.write(content_bytes)
    else:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
            
    return {
        "path": str(file_path.relative_to(BASE_DIR)),
        "size": file_path.stat().st_size
    }

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
        content: Initial content
        create_dirs: Create parent directories if needed

    Returns:
        File information
    """
    file_path = resolve_path(path)
    if not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if file_path.exists():
        raise ValueError(f"File already exists: {path}")
        
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return get_file_info(file_path)

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
    if not is_safe_path(target_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if not target_path.exists():
        raise ValueError(f"Path does not exist: {path}")
        
    if target_path.is_dir():
        if recursive:
            shutil.rmtree(target_path)
        else:
            target_path.rmdir()
    else:
        target_path.unlink()
        
    return {"deleted": str(target_path.relative_to(BASE_DIR))}

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
    
    if not is_safe_path(source_path) or not is_safe_path(dest_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if not source_path.exists():
        raise ValueError(f"Source does not exist: {source}")
        
    if dest_path.exists() and not overwrite:
        raise ValueError(f"Destination already exists: {destination}")
        
    source_path.rename(dest_path)
    
    return {
        "source": str(source_path.relative_to(BASE_DIR)),
        "destination": str(dest_path.relative_to(BASE_DIR))
    }

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
    
    if not is_safe_path(source_path) or not is_safe_path(dest_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if not source_path.exists():
        raise ValueError(f"Source does not exist: {source}")
        
    if dest_path.exists() and not overwrite:
        raise ValueError(f"Destination already exists: {destination}")
        
    if source_path.is_dir():
        shutil.copytree(source_path, dest_path, dirs_exist_ok=overwrite)
    else:
        shutil.copy2(source_path, dest_path)
        
    return {
        "source": str(source_path.relative_to(BASE_DIR)),
        "destination": str(dest_path.relative_to(BASE_DIR))
    }


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
    if not is_safe_path(search_path):
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
        
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            if recursive:
                if max_depth is not None:
                    # Use depth-limited walk
                    files_to_search = list(walk_with_depth(search_path, file_pattern, max_depth))
                else:
                    files_to_search = list(search_path.rglob(file_pattern))
            else:
                files_to_search = list(search_path.glob(file_pattern))
                
        for file_path in files_to_search:
            # Check if we should yield control periodically
            if files_searched % 100 == 0:
                await asyncio.sleep(0)  # Allow other tasks to run
                
            if not file_path.is_file():
                continue
                
            file_type = get_file_type(file_path)
            if file_type != "text":
                continue
                
            matches = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
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
                results.append({
                    "file": str(file_path.relative_to(BASE_DIR)),
                    "matches": matches
                })
    
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
    if not is_safe_path(search_path):
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
        
        if search_path.is_file():
            files_to_process = [search_path]
        else:
            if recursive:
                if max_depth is not None:
                    files_to_process = list(walk_with_depth(search_path, file_pattern, max_depth))
                else:
                    files_to_process = list(search_path.rglob(file_pattern))
            else:
                files_to_process = list(search_path.glob(file_pattern))
                
        for file_path in files_to_process:
            if files_processed % 50 == 0:
                await asyncio.sleep(0)
                
            if not file_path.is_file():
                continue
                
            file_type = get_file_type(file_path)
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
                        "file": str(file_path.relative_to(BASE_DIR)),
                        "replacements": count
                    })
                    
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
async def set_project_directory(path: str) -> Dict[str, Any]:
    """
    Set the project directory for relative path operations.
    
    Args:
        path: Path to the project directory (absolute or relative to current directory)
        
    Returns:
        Dictionary with project directory information
    """
    global PROJECT_DIR
    
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
            "message": "No project directory set. Use set_project_directory to set one."
        }
    
    return {
        "project_directory": str(PROJECT_DIR),
        "relative_to_base": str(PROJECT_DIR.relative_to(BASE_DIR)),
        "absolute_path": str(PROJECT_DIR.absolute()),
        "exists": PROJECT_DIR.exists()
    }



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
    from server import BASE_DIR, is_safe_path, get_file_type
    
    file_path = resolve_path(path)
    if not is_safe_path(file_path):
        return {
            "success": False,
            "error": "Invalid path: directory traversal detected",
            "patches_applied": 0
        }
    
    if not file_path.exists():
        if create_dirs and patches:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("")
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
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
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
            backup_path.write_text(original_content)
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
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
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
        "backup_path": str(backup_path.relative_to(BASE_DIR)) if backup_path else None,
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
    if not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
        
    if not file_path.exists():
        raise ValueError(f"Path does not exist: {path}")
        
    return get_file_info(file_path)
