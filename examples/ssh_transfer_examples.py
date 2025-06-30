#!/usr/bin/env python3
"""
Example: SSH File Transfer Operations
Demonstrates uploading and downloading files between local and remote systems
"""

import asyncio
from pathlib import Path

# Import the MCP tools
from server import (
    set_project_directory, 
    ssh_upload, 
    ssh_download, 
    ssh_sync,
    list_files,
    read_file,
    write_file
)


async def ssh_transfer_examples():
    """Demonstrate SSH file transfer operations"""
    
    # First, establish an SSH connection
    # Replace these with your actual SSH server details
    await set_project_directory(
        path="/home/user/remote_project",
        connection_type="ssh",
        ssh_host="example.com",
        ssh_username="myuser",
        ssh_port=22,
        ssh_key_filename="~/.ssh/id_rsa"
    )
    
    print("Connected to remote server via SSH")
    
    # Example 1: Upload a single file
    print("\n1. Uploading a single file...")
    result = await ssh_upload(
        local_path="/local/documents/report.pdf",
        remote_path="uploads/report.pdf"
    )
    print(f"Uploaded {result['uploaded']} file(s), total size: {result['total_size']} bytes")
    
    # Example 2: Upload a directory recursively
    print("\n2. Uploading a directory...")
    result = await ssh_upload(
        local_path="/local/projects/my_app",
        remote_path="backups/my_app_backup",
        recursive=True,
        overwrite=True
    )
    print(f"Uploaded {result['uploaded']} files with {result['errors']} errors")
    if result['errors'] > 0:
        print("Errors:", result['error_details'])
    
    # Example 3: Download a file
    print("\n3. Downloading a file...")
    result = await ssh_download(
        remote_path="data/dataset.csv",
        local_path="/local/downloads/dataset.csv"
    )
    print(f"Downloaded {result['downloaded']} file(s)")
    
    # Example 4: Download a directory
    print("\n4. Downloading a directory...")
    result = await ssh_download(
        remote_path="logs/2025-06",
        local_path="/local/log_backups/2025-06",
        recursive=True
    )
    print(f"Downloaded {result['downloaded']} files, total: {result['total_size']} bytes")
    
    # Example 5: Sync directories (upload direction)
    print("\n5. Syncing local to remote...")
    result = await ssh_sync(
        local_path="/local/website",
        remote_path="/var/www/html",
        direction="upload"
    )
    print(f"Sync completed: {result['uploaded']} files uploaded")
    
    # Example 6: Sync directories (download direction)
    print("\n6. Syncing remote to local...")
    result = await ssh_sync(
        local_path="/local/database_backups",
        remote_path="/remote/db_dumps",
        direction="download"
    )
    print(f"Sync completed: {result['downloaded']} files downloaded")
    
    # Example 7: Upload with error handling
    print("\n7. Upload with comprehensive error handling...")
    try:
        result = await ssh_upload(
            local_path="/local/important_data",
            remote_path="/remote/secure_backup",
            recursive=True,
            overwrite=False  # Don't overwrite existing files
        )
        
        print(f"Successfully uploaded: {result['uploaded']} files")
        print(f"Failed uploads: {result['errors']}")
        
        # Check each uploaded file
        for file_info in result['files']:
            print(f"  ✓ {file_info['local']} -> {file_info['remote']} ({file_info['size']} bytes)")
        
        # Check errors if any
        for error in result['error_details']:
            print(f"  ✗ {error['file']}: {error['error']}")
            
    except ValueError as e:
        print(f"Upload failed: {e}")
    
    # Example 8: Working with both local and remote files
    print("\n8. Combined local and remote operations...")
    
    # Read a local file
    local_content = Path("/local/config.json").read_text()
    
    # Process it somehow
    modified_content = local_content.replace("localhost", "example.com")
    
    # Write it to the remote server
    await write_file("config/production.json", modified_content)
    
    # Verify it was written
    remote_files = await list_files("config", pattern="*.json")
    print(f"Remote config files: {[f['name'] for f in remote_files]}")


async def advanced_ssh_example():
    """Advanced example with multiple SSH connections"""
    
    # Connect to staging server
    await set_project_directory(
        "ssh://deploy@staging.example.com/var/app",
        connection_type="ssh"
    )
    
    # Download application logs
    result = await ssh_download(
        remote_path="logs",
        local_path="/tmp/staging_logs",
        recursive=True
    )
    print(f"Downloaded {result['downloaded']} log files from staging")
    
    # Connect to production server
    await set_project_directory(
        "ssh://deploy@prod.example.com/var/app",
        connection_type="ssh"
    )
    
    # Upload updated configuration
    result = await ssh_upload(
        local_path="/local/prod_config",
        remote_path="config",
        recursive=True,
        overwrite=True
    )
    print(f"Uploaded {result['uploaded']} config files to production")
    
    # Switch back to local for processing
    await set_project_directory("/local/workspace", connection_type="local")
    print("Switched back to local filesystem")


if __name__ == "__main__":
    # Run the examples
    print("SSH File Transfer Examples")
    print("=" * 50)
    
    # Note: These examples won't run without a configured SSH server
    # Modify the connection parameters to match your environment
    
    try:
        asyncio.run(ssh_transfer_examples())
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Make sure to configure valid SSH connection parameters")
