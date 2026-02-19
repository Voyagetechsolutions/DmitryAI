# tools/system/search_files.py
"""
Search Files Tool - Searches for files in directories.
"""

import os
import fnmatch
from typing import List
from datetime import datetime

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class SearchFilesTool(BaseTool):
    """Tool to search for files in directories."""
    
    def __init__(self):
        super().__init__()
        self._name = "search_files"
        self._description = "Search for files by name pattern in a directory"
        self._permission_level = PermissionLevel.READ
        self._needs_confirmation = False
        self._max_results = 100
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to search in",
                },
                "pattern": {
                    "type": "string",
                    "description": "File name pattern (supports wildcards * and ?)",
                },
                "extension": {
                    "type": "string",
                    "description": "File extension filter (e.g., '.py', '.js')",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Search subdirectories",
                    "default": True,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 50,
                },
            },
            "required": ["directory"],
        }
    
    def _matches_pattern(self, filename: str, pattern: str, extension: str) -> bool:
        """Check if filename matches the search criteria."""
        # Check pattern
        if pattern:
            if not fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return False
        
        # Check extension
        if extension:
            ext = extension if extension.startswith(".") else f".{extension}"
            if not filename.lower().endswith(ext.lower()):
                return False
        
        return True
    
    def _search(
        self,
        directory: str,
        pattern: str,
        extension: str,
        recursive: bool,
        max_results: int,
    ) -> List[dict]:
        """Search for matching files."""
        results = []
        
        def add_result(filepath: str):
            if len(results) >= max_results:
                return False
            
            try:
                stat = os.stat(filepath)
                results.append({
                    "name": os.path.basename(filepath),
                    "path": filepath,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception:
                results.append({
                    "name": os.path.basename(filepath),
                    "path": filepath,
                })
            return True
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                
                for filename in files:
                    if self._matches_pattern(filename, pattern, extension):
                        if not add_result(os.path.join(root, filename)):
                            return results
        else:
            try:
                for entry in os.listdir(directory):
                    filepath = os.path.join(directory, entry)
                    if os.path.isfile(filepath):
                        if self._matches_pattern(entry, pattern, extension):
                            if not add_result(filepath):
                                break
            except Exception:
                pass
        
        return results
    
    def _execute(
        self,
        directory: str,
        pattern: str = None,
        extension: str = None,
        recursive: bool = True,
        max_results: int = 50,
        **kwargs,
    ) -> ToolResult:
        """Search for files matching the criteria."""
        # Normalize the path
        directory = os.path.normpath(os.path.abspath(directory))
        
        # Check if directory exists
        if not os.path.exists(directory):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Directory does not exist: {directory}",
            )
        
        if not os.path.isdir(directory):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Path is not a directory: {directory}",
            )
        
        # Validate we have some search criteria
        if not pattern and not extension:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="Please provide a pattern or extension to search for",
            )
        
        # Limit max results
        max_results = min(max_results, self._max_results)
        
        try:
            results = self._search(
                directory,
                pattern,
                extension,
                recursive,
                max_results,
            )
            
            truncated = len(results) >= max_results
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Found {len(results)} files" + (" (truncated)" if truncated else ""),
                data={
                    "directory": directory,
                    "pattern": pattern,
                    "extension": extension,
                    "results": results,
                    "count": len(results),
                    "truncated": truncated,
                },
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Search failed: {e}",
            )
