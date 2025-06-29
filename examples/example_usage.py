#!/usr/bin/env python3
"""
Example usage of MCP File Editor Server
Shows how to interact with the server programmatically
"""

import json
import subprocess
import sys

class MCPClient:
    """Simple client for MCP File Editor Server"""
    
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, 'mcp_file_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )
        # Skip server info
        self.proc.stdout.readline()
        self.request_id = 0
        
    def send_request(self, method, params=None):
        """Send a request and get response"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id
        }
        if params:
            request["params"] = params
            
        json_str = json.dumps(request) + '\n'
        self.proc.stdin.write(json_str.encode())
        self.proc.stdin.flush()
        
        response_line = self.proc.stdout.readline().decode().strip()
        return json.loads(response_line)
        
    def call_tool(self, tool_name, arguments):
        """Call a specific tool"""
        return self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
    def close(self):
        """Close the client"""
        self.proc.terminate()
        self.proc.wait()

def main():
    """Demonstrate various file operations"""
    client = MCPClient()
    
    try:
        # Initialize
        response = client.send_request("initialize")
        print("Server initialized:", response["result"]["serverInfo"]["name"])
        print()
        
        # Create a project structure
        print("Creating project structure...")
        
        # Create directories and files
        client.call_tool("create_file", {
            "path": "project/src/main.py",
            "content": '''#!/usr/bin/env python3
"""Main application file"""

def main():
    print("Hello from MCP File Editor!")
    
if __name__ == "__main__":
    main()
''',
            "create_dirs": True
        })
        
        client.call_tool("create_file", {
            "path": "project/src/utils.py",
            "content": '''"""Utility functions"""

def format_name(first, last):
    """Format a name"""
    return f"{first} {last}"
    
def calculate_sum(numbers):
    """Calculate sum of numbers"""
    return sum(numbers)
''',
            "create_dirs": True
        })
        
        client.call_tool("create_file", {
            "path": "project/README.md",
            "content": '''# Example Project

This is an example project created with MCP File Editor.

## Features
- Simple Python application
- Utility functions
- Clean structure

## Usage
```bash
python src/main.py
```
''',
            "create_dirs": True
        })
        
        print("Project structure created!")
        print()
        
        # List files
        print("Project files:")
        result = client.call_tool("list_files", {
            "path": "project",
            "recursive": True
        })
        
        for file_info in result["result"]:
            if file_info["type"] == "file":
                print(f"  {file_info['path']} ({file_info['size']} bytes)")
        print()
        
        # Search for functions
        print("Searching for function definitions...")
        result = client.call_tool("search_files", {
            "path": "project",
            "pattern": "^def ",
            "recursive": True
        })
        
        for file_result in result["result"]:
            print(f"  {file_result['file']}:")
            for match in file_result["matches"]:
                print(f"    Line {match['line_number']}: {match['line']}")
        print()
        
        # Read a specific file
        print("Reading main.py:")
        result = client.call_tool("read_file", {
            "path": "project/src/main.py"
        })
        print(result["result"]["content"])
        
        # Clean up
        print("Cleaning up...")
        client.call_tool("delete_file", {
            "path": "project",
            "recursive": True
        })
        print("Done!")
        
    finally:
        client.close()

if __name__ == "__main__":
    main()
