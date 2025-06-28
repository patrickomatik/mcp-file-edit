#!/usr/bin/env python3
"""
Update Claude Desktop configuration to use the new MCP File Editor server
"""

import json
import os
import shutil
from pathlib import Path

def update_claude_config():
    """Update the Claude Desktop configuration"""
    config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return False
    
    # Backup the current config
    backup_path = config_path.with_suffix('.bak.json')
    shutil.copy2(config_path, backup_path)
    print(f"Created backup at: {backup_path}")
    
    # Read the current configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Remove old file-edit entry if it exists
    if "file-edit" in config.get("mcpServers", {}):
        del config["mcpServers"]["file-edit"]
        print("Removed old 'file-edit' entry")
    
    # Add the new file-editor entry
    server_path = Path(__file__).parent / "mcp_file_server.py"
    config["mcpServers"]["file-editor"] = {
        "command": "python3",
        "args": [str(server_path.absolute())]
    }
    
    # Write the updated configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Updated configuration at: {config_path}")
    print(f"Added 'file-editor' server pointing to: {server_path}")
    print("\nConfiguration updated successfully!")
    print("Please restart Claude Desktop for changes to take effect.")
    
    return True

if __name__ == "__main__":
    update_claude_config()
