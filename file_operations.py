"""
File operations abstraction layer for local and SSH operations.
"""

import os
import stat
import shutil
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, AsyncIterator, Tuple
import asyncssh
from datetime import datetime


class FileOperationsInterface(ABC):
    """Abstract interface for file operations."""
    
    @abstractmethod
    async def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        pass
    
    @abstractmethod
    async def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        pass
    
    @abstractmethod
    async def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        pass
    
    @abstractmethod
    async def stat(self, path: Path) -> os.stat_result:
        """Get file statistics."""
        pass
    
    @abstractmethod
    async def listdir(self, path: Path) -> List[str]:
        """List directory contents."""
        pass
    
    @abstractmethod
    async def glob(self, path: Path, pattern: str) -> AsyncIterator[Path]:
        """Glob pattern matching."""
        pass
    
    @abstractmethod
    async def read_file(self, path: Path, encoding: str = 'utf-8') -> str:
        """Read file contents."""
        pass
    
    @abstractmethod
    async def read_binary(self, path: Path) -> bytes:
        """Read binary file contents."""
        pass
    
    @abstractmethod
    async def write_file(self, path: Path, content: Union[str, bytes], encoding: str = 'utf-8') -> None:
        """Write file contents."""
        pass
    
    @abstractmethod
    async def makedirs(self, path: Path, exist_ok: bool = True) -> None:
        """Create directories recursively."""
        pass
    
    @abstractmethod
    async def remove(self, path: Path) -> None:
        """Remove a file."""
        pass
    
    @abstractmethod
    async def rmtree(self, path: Path) -> None:
        """Remove directory tree."""
        pass
    
    @abstractmethod
    async def rename(self, src: Path, dst: Path) -> None:
        """Rename/move a file or directory."""
        pass
    
    @abstractmethod
    async def copy_file(self, src: Path, dst: Path) -> None:
        """Copy a file."""
        pass
    
    @abstractmethod
    async def copy_tree(self, src: Path, dst: Path) -> None:
        """Copy directory tree."""
        pass
    
    @abstractmethod
    async def search_files(self, path: Path, pattern: str, max_depth: Optional[int] = None) -> List[Tuple[Path, List[str]]]:
        """Search for pattern in files."""
        pass


class LocalFileOperations(FileOperationsInterface):
    """Local filesystem operations implementation."""
    
    async def exists(self, path: Path) -> bool:
        return path.exists()
    
    async def is_file(self, path: Path) -> bool:
        return path.is_file()
    
    async def is_dir(self, path: Path) -> bool:
        return path.is_dir()
    
    async def stat(self, path: Path) -> os.stat_result:
        return path.stat()
    
    async def listdir(self, path: Path) -> List[str]:
        return list(os.listdir(path))
    
    async def glob(self, path: Path, pattern: str) -> AsyncIterator[Path]:
        for item in path.glob(pattern):
            yield item
    
    async def read_file(self, path: Path, encoding: str = 'utf-8') -> str:
        return path.read_text(encoding=encoding)
    
    async def read_binary(self, path: Path) -> bytes:
        return path.read_bytes()
    
    async def write_file(self, path: Path, content: Union[str, bytes], encoding: str = 'utf-8') -> None:
        if isinstance(content, str):
            path.write_text(content, encoding=encoding)
        else:
            path.write_bytes(content)
    
    async def makedirs(self, path: Path, exist_ok: bool = True) -> None:
        path.mkdir(parents=True, exist_ok=exist_ok)
    
    async def remove(self, path: Path) -> None:
        path.unlink()
    
    async def rmtree(self, path: Path) -> None:
        await asyncio.to_thread(shutil.rmtree, path)
    
    async def rename(self, src: Path, dst: Path) -> None:
        src.rename(dst)
    
    async def copy_file(self, src: Path, dst: Path) -> None:
        await asyncio.to_thread(shutil.copy2, src, dst)
    
    async def copy_tree(self, src: Path, dst: Path) -> None:
        await asyncio.to_thread(shutil.copytree, src, dst)
    
    async def search_files(self, path: Path, pattern: str, max_depth: Optional[int] = None) -> List[Tuple[Path, List[str]]]:
        # Simple implementation - can be enhanced
        results = []
        import re
        regex = re.compile(pattern)
        
        async for file_path in self._walk_files(path, max_depth):
            if file_path.is_file():
                try:
                    content = await self.read_file(file_path)
                    matches = []
                    for i, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            matches.append(f"{i}: {line.strip()}")
                    if matches:
                        results.append((file_path, matches))
                except Exception:
                    pass  # Skip files that can't be read
        
        return results
    
    async def _walk_files(self, path: Path, max_depth: Optional[int] = None, current_depth: int = 0) -> AsyncIterator[Path]:
        """Walk directory tree with optional depth limit."""
        if max_depth is not None and current_depth >= max_depth:
            return
            
        try:
            for item in path.iterdir():
                yield item
                if item.is_dir():
                    async for subitem in self._walk_files(item, max_depth, current_depth + 1):
                        yield subitem
        except PermissionError:
            pass


class SSHFileOperations(FileOperationsInterface):
    """SSH-based filesystem operations implementation."""
    
    def __init__(self, conn: asyncssh.SSHClientConnection, sftp: asyncssh.SFTPClient):
        self.conn = conn
        self.sftp = sftp
        self._host = conn.get_extra_info('peername')[0]
    
    def _to_remote_path(self, path: Path) -> str:
        """Convert Path object to remote path string."""
        # Use POSIX path format for remote paths
        return str(path).replace('\\', '/')
    
    async def exists(self, path: Path) -> bool:
        try:
            await self.sftp.stat(self._to_remote_path(path))
            return True
        except asyncssh.SFTPNoSuchFile:
            return False
    
    async def is_file(self, path: Path) -> bool:
        try:
            attrs = await self.sftp.stat(self._to_remote_path(path))
            return attrs.type == asyncssh.FILEXFER_TYPE_REGULAR
        except asyncssh.SFTPNoSuchFile:
            return False
    
    async def is_dir(self, path: Path) -> bool:
        try:
            attrs = await self.sftp.stat(self._to_remote_path(path))
            return attrs.type == asyncssh.FILEXFER_TYPE_DIRECTORY
        except asyncssh.SFTPNoSuchFile:
            return False
    
    async def stat(self, path: Path) -> os.stat_result:
        attrs = await self.sftp.stat(self._to_remote_path(path))
        # Create a stat_result-like object
        # Note: This is a simplified version - some fields may not be accurate
        return os.stat_result((
            attrs.permissions or 0,  # st_mode
            0,  # st_ino
            0,  # st_dev
            1,  # st_nlink
            attrs.uid or 0,  # st_uid
            attrs.gid or 0,  # st_gid
            attrs.size or 0,  # st_size
            attrs.atime or 0,  # st_atime
            attrs.mtime or 0,  # st_mtime
            attrs.mtime or 0,  # st_ctime
        ))
    
    async def listdir(self, path: Path) -> List[str]:
        remote_path = self._to_remote_path(path)
        entries = await self.sftp.listdir(remote_path)
        return [entry.filename for entry in entries]
    
    async def glob(self, path: Path, pattern: str) -> AsyncIterator[Path]:
        # Simple glob implementation for SSH
        import fnmatch
        base_path = self._to_remote_path(path)
        
        try:
            entries = await self.sftp.listdir(base_path)
            for entry in entries:
                if fnmatch.fnmatch(entry.filename, pattern):
                    yield path / entry.filename
        except asyncssh.SFTPNoSuchFile:
            pass
    
    async def read_file(self, path: Path, encoding: str = 'utf-8') -> str:
        remote_path = self._to_remote_path(path)
        async with self.sftp.open(remote_path, 'r') as f:
            content = await f.read()
        return content.decode(encoding)
    
    async def read_binary(self, path: Path) -> bytes:
        remote_path = self._to_remote_path(path)
        async with self.sftp.open(remote_path, 'rb') as f:
            return await f.read()
    
    async def write_file(self, path: Path, content: Union[str, bytes], encoding: str = 'utf-8') -> None:
        remote_path = self._to_remote_path(path)
        if isinstance(content, str):
            content = content.encode(encoding)
        
        async with self.sftp.open(remote_path, 'wb') as f:
            await f.write(content)
    
    async def makedirs(self, path: Path, exist_ok: bool = True) -> None:
        remote_path = self._to_remote_path(path)
        
        # Check if exists
        if exist_ok:
            try:
                attrs = await self.sftp.stat(remote_path)
                if attrs.type == asyncssh.FILEXFER_TYPE_DIRECTORY:
                    return
            except asyncssh.SFTPNoSuchFile:
                pass
        
        # Create parent directories if needed
        parts = remote_path.split('/')
        current = ''
        for part in parts:
            if not part:
                continue
            current = current + '/' + part if current else part
            try:
                await self.sftp.mkdir(current)
            except asyncssh.SFTPFailure:
                # Directory might already exist
                pass
    
    async def remove(self, path: Path) -> None:
        remote_path = self._to_remote_path(path)
        await self.sftp.remove(remote_path)
    
    async def rmtree(self, path: Path) -> None:
        remote_path = self._to_remote_path(path)
        # Recursively remove directory
        await self._rmtree_recursive(remote_path)
    
    async def _rmtree_recursive(self, remote_path: str) -> None:
        """Recursively remove directory tree."""
        try:
            entries = await self.sftp.listdir(remote_path)
            for entry in entries:
                entry_path = f"{remote_path}/{entry.filename}"
                if entry.type == asyncssh.FILEXFER_TYPE_DIRECTORY:
                    await self._rmtree_recursive(entry_path)
                else:
                    await self.sftp.remove(entry_path)
            await self.sftp.rmdir(remote_path)
        except asyncssh.SFTPNoSuchFile:
            pass
    
    async def rename(self, src: Path, dst: Path) -> None:
        src_remote = self._to_remote_path(src)
        dst_remote = self._to_remote_path(dst)
        await self.sftp.rename(src_remote, dst_remote)
    
    async def copy_file(self, src: Path, dst: Path) -> None:
        # Read and write to copy
        content = await self.read_binary(src)
        await self.write_file(dst, content)
        
        # Try to preserve permissions
        try:
            attrs = await self.sftp.stat(self._to_remote_path(src))
            await self.sftp.chmod(self._to_remote_path(dst), attrs.permissions)
        except:
            pass
    
    async def copy_tree(self, src: Path, dst: Path) -> None:
        """Copy directory tree recursively."""
        await self._copy_tree_recursive(src, dst)
    
    async def _copy_tree_recursive(self, src: Path, dst: Path) -> None:
        """Recursively copy directory tree."""
        # Create destination directory
        await self.makedirs(dst, exist_ok=True)
        
        # Copy contents
        src_remote = self._to_remote_path(src)
        entries = await self.sftp.listdir(src_remote)
        
        for entry in entries:
            src_item = src / entry.filename
            dst_item = dst / entry.filename
            
            if entry.type == asyncssh.FILEXFER_TYPE_DIRECTORY:
                await self._copy_tree_recursive(src_item, dst_item)
            else:
                await self.copy_file(src_item, dst_item)
    
    async def search_files(self, path: Path, pattern: str, max_depth: Optional[int] = None) -> List[Tuple[Path, List[str]]]:
        """Search for pattern in files using remote grep."""
        import re
        results = []
        
        # Use find and grep on remote system for efficiency
        remote_path = self._to_remote_path(path)
        depth_arg = f"-maxdepth {max_depth}" if max_depth else ""
        
        # Execute remote find + grep
        cmd = f'find {remote_path} {depth_arg} -type f -exec grep -Hn "{pattern}" {{}} +'
        
        try:
            result = await self.conn.run(cmd, check=False)
            if result.stdout:
                # Parse grep output
                for line in result.stdout.splitlines():
                    if ':' in line:
                        file_path, line_num, content = line.split(':', 2)
                        file_path = Path(file_path)
                        
                        # Group by file
                        existing = next((r for r in results if r[0] == file_path), None)
                        if existing:
                            existing[1].append(f"{line_num}: {content.strip()}")
                        else:
                            results.append((file_path, [f"{line_num}: {content.strip()}"]))
        except Exception:
            # Fallback to manual search if command fails
            async for file_path in self._walk_files(path, max_depth):
                if await self.is_file(file_path):
                    try:
                        content = await self.read_file(file_path)
                        matches = []
                        regex = re.compile(pattern)
                        for i, line in enumerate(content.splitlines(), 1):
                            if regex.search(line):
                                matches.append(f"{i}: {line.strip()}")
                        if matches:
                            results.append((file_path, matches))
                    except Exception:
                        pass
        
        return results
    
    async def _walk_files(self, path: Path, max_depth: Optional[int] = None, current_depth: int = 0) -> AsyncIterator[Path]:
        """Walk directory tree with optional depth limit."""
        if max_depth is not None and current_depth >= max_depth:
            return
        
        try:
            remote_path = self._to_remote_path(path)
            entries = await self.sftp.listdir(remote_path)
            
            for entry in entries:
                item_path = path / entry.filename
                yield item_path
                
                if entry.type == asyncssh.FILEXFER_TYPE_DIRECTORY:
                    async for subitem in self._walk_files(item_path, max_depth, current_depth + 1):
                        yield subitem
        except asyncssh.SFTPNoSuchFile:
            pass
