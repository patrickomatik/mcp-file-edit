#!/usr/bin/env python3
"""
Example: Git Operations with MCP File Editor
Demonstrates using git commands through the file editor for both local and remote repositories
"""

import asyncio
from pathlib import Path

# Import the MCP tools
from server import (
    set_project_directory,
    git_status,
    git_init,
    git_clone,
    git_add,
    git_commit,
    git_push,
    git_pull,
    git_log,
    git_branch,
    git_checkout,
    git_diff,
    git_remote,
    create_file,
    write_file,
    list_files
)


async def local_git_examples():
    """Demonstrate git operations on a local repository"""
    
    print("Git Operations - Local Repository")
    print("=" * 50)
    
    # Set up a local project directory
    await set_project_directory("/tmp/my_project")
    
    # Example 1: Initialize a new repository
    print("\n1. Initializing a new git repository...")
    result = await git_init()
    print(f"Repository initialized: {result['success']}")
    
    # Example 2: Create some files
    print("\n2. Creating project files...")
    await create_file("README.md", """# My Project
    
This is a sample project to demonstrate git operations.
""")
    
    await create_file("main.py", """#!/usr/bin/env python3

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
    
    await create_file(".gitignore", """# Python
__pycache__/
*.pyc
.env
venv/
""")
    
    # Example 3: Check status
    print("\n3. Checking git status...")
    status = await git_status()
    print(f"Branch: {status['branch']}")
    print(f"Untracked files: {status['untracked']}")
    
    # Example 4: Stage files
    print("\n4. Staging files...")
    await git_add(".")
    status = await git_status()
    print(f"Staged files: {len(status['staged'])}")
    
    # Example 5: Commit changes
    print("\n5. Committing changes...")
    commit_result = await git_commit("Initial commit: Project setup")
    print(f"Commit created: {commit_result['commit_hash']}")
    
    # Example 6: Create a feature branch
    print("\n6. Creating a feature branch...")
    await git_branch(create="feature/add-config")
    await git_checkout("feature/add-config")
    
    # Example 7: Make changes on the branch
    print("\n7. Adding configuration file...")
    await create_file("config.json", """{
    "app_name": "My Project",
    "version": "1.0.0",
    "debug": true
}
""")
    
    await git_add("config.json")
    await git_commit("feat: Add configuration file")
    
    # Example 8: View commit log
    print("\n8. Viewing commit history...")
    log_result = await git_log(limit=5, oneline=True)
    print("Recent commits:")
    for commit in log_result['commits']:
        print(f"  {commit}")
    
    # Example 9: Switch back to main branch
    print("\n9. Switching back to main branch...")
    await git_checkout("main")
    
    # Example 10: View differences
    print("\n10. Viewing branch differences...")
    # This would show differences if we had uncommitted changes
    diff_result = await git_diff()
    if diff_result['diff']:
        print("Changes in working directory:")
        print(diff_result['diff'][:200] + "...")
    else:
        print("No changes in working directory")


async def remote_git_examples():
    """Demonstrate git operations on a remote repository via SSH"""
    
    print("\n\nGit Operations - Remote Repository (SSH)")
    print("=" * 50)
    
    # Connect to a remote server
    print("\n1. Connecting to remote server...")
    await set_project_directory(
        path="/home/user/projects",
        connection_type="ssh",
        ssh_host="example.com",  # Replace with actual server
        ssh_username="user"      # Replace with actual username
    )
    
    # Example 1: Clone a repository on the remote server
    print("\n2. Cloning a repository on remote server...")
    clone_result = await git_clone(
        "https://github.com/example/repo.git",
        path="/home/user/projects/cloned-repo"
    )
    print(f"Repository cloned: {clone_result['success']}")
    
    # Example 2: Check status on remote
    print("\n3. Checking status on remote repository...")
    status = await git_status()
    print(f"Remote branch: {status['branch']}")
    print(f"Clean: {status['clean']}")
    
    # Example 3: Create and push changes from remote
    print("\n4. Making changes on remote...")
    await write_file("remote-file.txt", "This file was created on the remote server")
    await git_add("remote-file.txt")
    await git_commit("feat: Add file from remote server")
    
    # Example 4: Push from remote to origin
    print("\n5. Pushing from remote to origin...")
    push_result = await git_push()
    print(f"Push successful: {push_result['success']}")
    
    # Example 5: Managing remotes
    print("\n6. Managing git remotes...")
    remotes = await git_remote()
    print("Current remotes:")
    for remote in remotes['remotes']:
        print(f"  {remote['name']}: {remote['url']}")


async def git_workflow_example():
    """Demonstrate a complete git workflow"""
    
    print("\n\nComplete Git Workflow Example")
    print("=" * 50)
    
    # This example shows a typical development workflow
    await set_project_directory("/tmp/workflow_example")
    
    # Initialize repository
    await git_init()
    
    # Create initial files
    await create_file("app.py", """from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"
""")
    
    await create_file("requirements.txt", """flask==2.3.2
gunicorn==20.1.0
""")
    
    # Initial commit
    await git_add(".")
    await git_commit("Initial commit: Flask app setup")
    
    # Add git remote
    await git_remote(
        action="add",
        name="origin",
        url="https://github.com/user/flask-app.git"
    )
    
    # Create feature branch
    await git_branch(create="feature/add-about-page")
    await git_checkout("feature/add-about-page")
    
    # Add new feature
    await write_file("app.py", """from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

@app.route('/about')
def about():
    return "About our application"
""")
    
    # Commit feature
    await git_add("app.py")
    await git_commit("feat: Add about page route")
    
    # Check branch status
    branches = await git_branch()
    print("\nCurrent branches:")
    for branch in branches['branches']:
        marker = "*" if branch['current'] else " "
        print(f"  {marker} {branch['name']}")
    
    # View the changes
    print("\n7. Changes made on feature branch:")
    log_result = await git_log(limit=2, oneline=False)
    for commit in log_result['commits']:
        print(f"\nCommit: {commit['hash'][:7]}")
        print(f"Author: {commit['author']} <{commit['email']}>")
        print(f"Date: {commit['date']}")
        print(f"Message: {commit['message']}")


async def error_handling_example():
    """Show how git operations handle errors"""
    
    print("\n\nGit Error Handling")
    print("=" * 50)
    
    await set_project_directory("/tmp/error_example")
    
    # Try to get status on non-git directory
    print("\n1. Checking status on non-git directory...")
    status = await git_status()
    if not status['is_repository']:
        print(f"Error: {status['error']}")
    
    # Initialize and try invalid operations
    await git_init()
    
    # Try to checkout non-existent branch
    print("\n2. Trying to checkout non-existent branch...")
    result = await git_checkout("non-existent-branch")
    if not result['success']:
        print(f"Error: {result['stderr']}")
    
    # Try to push without remote
    print("\n3. Trying to push without remote...")
    result = await git_push()
    if not result['success']:
        print(f"Error: {result['stderr']}")


if __name__ == "__main__":
    print("Git Operations Examples")
    print("=" * 50)
    print("Note: These examples demonstrate git functionality.")
    print("Modify the SSH connection parameters for remote examples.")
    
    # Run the examples
    try:
        asyncio.run(local_git_examples())
        # Uncomment to run remote examples (requires valid SSH server)
        # asyncio.run(remote_git_examples())
        asyncio.run(git_workflow_example())
        asyncio.run(error_handling_example())
    except Exception as e:
        print(f"Error: {e}")
