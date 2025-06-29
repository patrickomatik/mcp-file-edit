#!/usr/bin/env python3
"""
Patch functionality for MCP File Editor
Provides various ways to patch/modify files precisely
"""

import re
import difflib
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

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
    
    file_path = BASE_DIR / path
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
