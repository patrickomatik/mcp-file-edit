#!/usr/bin/env python3
"""
Test script for SSH upload/download functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import (
    set_project_directory, ssh_upload, ssh_download, ssh_sync,
    list_files, read_file, write_file, create_file
)


async def test_ssh_transfers():
    """Test SSH file transfer operations"""
    
    print("SSH File Transfer Test Suite")
    print("=" * 50)
    
    # Test configuration - modify these for your test environment
    SSH_HOST = "localhost"  # Change to your test SSH server
    SSH_USER = "testuser"   # Change to your SSH username
    SSH_PORT = 22
    REMOTE_BASE = "/tmp/mcp_ssh_test"
    LOCAL_BASE = "/tmp/mcp_local_test"
    
    try:
        # 1. Setup local test directory
        print("\n1. Setting up local test directory...")
        local_dir = Path(LOCAL_BASE)
        local_dir.mkdir(exist_ok=True)
        
        # Create test files locally
        (local_dir / "test1.txt").write_text("This is test file 1")
        (local_dir / "test2.txt").write_text("This is test file 2")
        
        # Create test subdirectory
        (local_dir / "subdir").mkdir(exist_ok=True)
        (local_dir / "subdir" / "test3.txt").write_text("This is test file 3 in subdir")
        
        print(f"Created test files in {LOCAL_BASE}")
        
        # 2. Connect to SSH server
        print(f"\n2. Connecting to SSH server {SSH_HOST}...")
        await set_project_directory(
            path=REMOTE_BASE,
            connection_type="ssh",
            ssh_host=SSH_HOST,
            ssh_username=SSH_USER,
            ssh_port=SSH_PORT
        )
        print("Connected successfully!")
        
        # 3. Test single file upload
        print("\n3. Testing single file upload...")
        result = await ssh_upload(
            local_path=str(local_dir / "test1.txt"),
            remote_path="uploaded_test1.txt"
        )
        print(f"Upload result: {result}")
        
        # Verify upload
        files = await list_files(pattern="*.txt")
        print(f"Remote files after upload: {[f['name'] for f in files]}")
        
        # 4. Test directory upload
        print("\n4. Testing recursive directory upload...")
        result = await ssh_upload(
            local_path=str(local_dir),
            remote_path="uploaded_dir",
            recursive=True
        )
        print(f"Directory upload result: {result}")
        
        # 5. Test single file download
        print("\n5. Testing single file download...")
        download_dir = Path(LOCAL_BASE + "_download")
        download_dir.mkdir(exist_ok=True)
        
        result = await ssh_download(
            remote_path="uploaded_test1.txt",
            local_path=str(download_dir / "downloaded_test1.txt")
        )
        print(f"Download result: {result}")
        
        # Verify download
        downloaded_content = (download_dir / "downloaded_test1.txt").read_text()
        print(f"Downloaded content: {downloaded_content}")
        
        # 6. Test directory download
        print("\n6. Testing recursive directory download...")
        result = await ssh_download(
            remote_path="uploaded_dir",
            local_path=str(download_dir / "downloaded_dir"),
            recursive=True
        )
        print(f"Directory download result: {result}")
        
        # 7. Test sync operation
        print("\n7. Testing sync operation...")
        
        # Modify a local file
        (local_dir / "test1.txt").write_text("Modified test file 1")
        
        # Sync upload with rsync
        result = await ssh_sync(
            local_path=str(local_dir),
            remote_path="synced_dir",
            direction="upload",
            update_only=True,
            show_progress=True
        )
        print(f"Sync upload result: {result}")
        assert result['success'], f"Sync upload failed: {result.get('error', 'Unknown error')}"
        
        # Test sync download with exclusions
        sync_download_dir = Path(LOCAL_BASE + "_sync")
        sync_download_dir.mkdir(exist_ok=True)
        
        result = await ssh_sync(
            local_path=str(sync_download_dir),
            remote_path="synced_dir",
            direction="download",
            exclude_patterns=["*.tmp", "*.log"],
            update_only=True,
            show_progress=False  # Quiet mode
        )
        print(f"Sync download result: {result}")
        assert result['success'], f"Sync download failed: {result.get('error', 'Unknown error')}"
        print(f"Sync download result: {result}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n8. Cleaning up test files...")
        # Note: Add cleanup code here if needed


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_ssh_transfers())
