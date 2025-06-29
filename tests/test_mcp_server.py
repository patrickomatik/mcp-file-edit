#!/usr/bin/env python3
"""
Test script for MCP File Editor Server
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def send_request(proc, request):
    """Send a JSON-RPC request and get response"""
    json_str = json.dumps(request) + '\n'
    proc.stdin.write(json_str.encode())
    proc.stdin.flush()
    
    # Read response
    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        return json.loads(response_line)
    return None

def test_server():
    """Test the MCP server functionality"""
    # Start the server
    proc = subprocess.Popen(
        [sys.executable, 'mcp_file_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False
    )
    
    print("Testing MCP File Editor Server...\n")
    
    try:
        # Skip server info message
        proc.stdout.readline()
        
        # Test 1: Initialize
        print("1. Testing initialize...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        })
        print(f"Response: {json.dumps(response, indent=2)}\n")
        
        # Test 2: List tools
        print("2. Testing tools/list...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })
        print(f"Available tools: {len(response['result']['tools'])}\n")
        
        # Test 3: Create a test file
        print("3. Testing create_file...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_file",
                "arguments": {
                    "path": "test_file.txt",
                    "content": "Hello from MCP File Editor!\nThis is a test file."
                }
            },
            "id": 3
        })
        print(f"Created file: {response['result']['name']}\n")
        
        # Test 4: Read the file
        print("4. Testing read_file...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": "test_file.txt"
                }
            },
            "id": 4
        })
        print(f"File content:\n{response['result']['content']}\n")
        
        # Test 5: List files
        print("5. Testing list_files...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_files",
                "arguments": {
                    "path": ".",
                    "pattern": "*.txt"
                }
            },
            "id": 5
        })
        print(f"Found {len(response['result'])} .txt files\n")
        
        # Test 6: Search in files
        print("6. Testing search_files...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "pattern": "Hello",
                    "file_pattern": "*.txt"
                }
            },
            "id": 6
        })
        print(f"Search results: {json.dumps(response['result'], indent=2)}\n")
        
        # Test 7: Delete the test file
        print("7. Testing delete_file...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "delete_file",
                "arguments": {
                    "path": "test_file.txt"
                }
            },
            "id": 7
        })
        print(f"Deleted: {response['result']['deleted']}\n")
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        
    finally:
        # Clean up
        proc.terminate()
        proc.wait()
        
        # Remove test file if it still exists
        test_file = Path("test_file.txt")
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    test_server()
