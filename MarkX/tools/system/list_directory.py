# tools/system/list_directory.py
"""
List Directory Tool - Lists contents of a directory.
"""

import os
from datetime import datetime
from typing import List

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class ListDirectoryTool(BaseTool):
    """Tool to list contents of a directory."""
    
    def __init__(self):
        super().__init__()
        self._name = "list_directory"
        self._description = "List files and folders in a directory"
        self._permission_level = PermissionLevel.READ
        self._needs_confirmation = False
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list",
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files/folders",
                    "default": False,
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List recursively (max 2 levels)",
                    "default": False,
                },
            },
            "required": ["path"],
        }
    
    def _get_file_info(self, path: str) -> dict:
        """Get information about a file or directory."""
        try:
            stat = os.stat(path)
            return {
                "name": os.path.basename(path),
                "path": path,
                "is_dir": os.path.isdir(path),
                "size": stat.st_size if os.path.isfile(path) else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception as e:
            return {
                "name": os.path.basename(path),
                "path": path,
                "error": str(e),
            }
    
    def _list_dir(
        self,
        path: str,
        include_hidden: bool,
        recursive: bool,
        depth: int = 0,
        max_depth: int = 2,
    ) -> List[dict]:
        """List directory contents."""
        items = []
        
        try:
            entries = os.listdir(path)
        except PermissionError:
            return [{"error": f"Permission denied: {path}"}]
        except Exception as e:
            return [{"error": str(e)}]
        
        for entry in sorted(entries):
            # Skip hidden files if not requested
            if not include_hidden and entry.startswith("."):
                continue
            
            full_path = os.path.join(path, entry)
            info = self._get_file_info(full_path)
            
            if recursive and info.get("is_dir") and depth < max_depth:
                info["children"] = self._list_dir(
                    full_path,
                    include_hidden,
                    recursive,
                    depth + 1,
                    max_depth,
                )
            
            items.append(info)
        
        return items
    
    def _execute(
        self,
        path: str,
        include_hidden: bool = False,
        recursive: bool = False,
        **kwargs,
    ) -> ToolResult:
        """List the directory contents."""
        # Normalize the path
        path = os.path.normpath(os.path.abspath(path))
        
        # Check if path exists
        if not os.path.exists(path):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Path does not exist: {path}",
            )
        
        # Check if path is a directory
        if not os.path.isdir(path):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Path is not a directory: {path}",
            )
        
        try:
            items = self._list_dir(path, include_hidden, recursive)
            
            # Count files and folders
            files = sum(1 for item in items if not item.get("is_dir", False))
            folders = sum(1 for item in items if item.get("is_dir", False))
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Listed {files} files and {folders} folders in {path}",
                data={
                    "path": path,
                    "items": items,
                    "file_count": files,
                    "folder_count": folders,
                },
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Failed to list directory: {e}",
            )
