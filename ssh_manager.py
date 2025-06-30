"""
SSH connection manager for handling SSH connections and SFTP clients.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import asyncssh
from urllib.parse import urlparse


class SSHConnectionManager:
    """Manages SSH connections and SFTP clients."""
    
    def __init__(self):
        self._connection: Optional[asyncssh.SSHClientConnection] = None
        self._sftp: Optional[asyncssh.SFTPClient] = None
        self._connection_params: Optional[Dict[str, Any]] = None
    
    async def connect(self, host: str, username: str, port: int = 22, 
                     key_filename: Optional[str] = None, 
                     known_hosts: Optional[str] = None) -> Tuple[asyncssh.SSHClientConnection, asyncssh.SFTPClient]:
        """Establish SSH connection and create SFTP client."""
        # Close existing connection if any
        await self.close()
        
        # Prepare connection options
        connect_options = {
            'host': host,
            'username': username,
            'port': port,
            'known_hosts': known_hosts
        }
        
        # Add key authentication
        if key_filename:
            key_path = Path(key_filename).expanduser()
            if not key_path.exists():
                raise ValueError(f"SSH key file not found: {key_filename}")
            connect_options['client_keys'] = [str(key_path)]
        
        # Store connection parameters for reconnection
        self._connection_params = connect_options.copy()
        
        # Establish connection
        self._connection = await asyncssh.connect(**connect_options)
        self._sftp = await self._connection.start_sftp_client()
        
        return self._connection, self._sftp
    
    async def close(self) -> None:
        """Close SSH connection and SFTP client."""
        if self._sftp:
            self._sftp.exit()
            self._sftp = None
        
        if self._connection:
            self._connection.close()
            await self._connection.wait_closed()
            self._connection = None
    
    async def reconnect(self) -> Tuple[asyncssh.SSHClientConnection, asyncssh.SFTPClient]:
        """Reconnect using stored parameters."""
        if not self._connection_params:
            raise RuntimeError("No connection parameters stored for reconnection")
        
        return await self.connect(**self._connection_params)
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connection is not None and not self._connection.is_closing()
    
    @property
    def connection(self) -> Optional[asyncssh.SSHClientConnection]:
        """Get current SSH connection."""
        return self._connection
    
    @property
    def sftp(self) -> Optional[asyncssh.SFTPClient]:
        """Get current SFTP client."""
        return self._sftp
    
    @staticmethod
    def parse_ssh_url(url: str) -> Dict[str, Any]:
        """Parse SSH URL format: ssh://[user@]host[:port]/path
        
        Returns dict with: host, username, port, path
        """
        if not url.startswith('ssh://'):
            raise ValueError("SSH URL must start with 'ssh://'")
        
        parsed = urlparse(url)
        
        result = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 22,
            'path': parsed.path or '/',
            'username': parsed.username or None
        }
        
        # Clean up path
        if result['path'].startswith('/'):
            result['path'] = result['path'][1:]  # Remove leading slash for relative paths
        
        return result
