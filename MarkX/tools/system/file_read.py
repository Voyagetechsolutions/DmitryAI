# tools/system/file_read.py
"""
File Read Tool - Reads contents of files.
"""

import os
import mimetypes
from typing import Optional

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class FileReadTool(BaseTool):
    """Tool to read file contents."""
    
    # Maximum file size to read (5 MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Text file extensions
    TEXT_EXTENSIONS = {
        ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
        ".html", ".css", ".scss", ".json", ".yaml", ".yml",
        ".xml", ".csv", ".sql", ".sh", ".bat", ".ps1",
        ".c", ".cpp", ".h", ".hpp", ".java", ".go", ".rs",
        ".rb", ".php", ".swift", ".kt", ".scala", ".r",
        ".ini", ".cfg", ".conf", ".env", ".gitignore",
        ".dockerfile", ".makefile", ".toml", ".lock",
    }
    
    def __init__(self):
        super().__init__()
        self._name = "file_read"
        self._description = "Read the contents of a file"
        self._permission_level = PermissionLevel.READ
        self._needs_confirmation = False
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Start reading from this line (1-indexed)",
                    "default": 1,
                },
                "end_line": {
                    "type": "integer",
                    "description": "Stop reading at this line (inclusive)",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        }
    
    def _is_text_file(self, path: str) -> bool:
        """Check if file appears to be a text file."""
        ext = os.path.splitext(path)[1].lower()
        if ext in self.TEXT_EXTENSIONS:
            return True
        
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type and mime_type.startswith("text/"):
            return True
        
        # Try reading a small sample
        try:
            with open(path, "rb") as f:
                sample = f.read(1024)
            sample.decode("utf-8")
            return True
        except Exception:
            return False
    
    def _execute(
        self,
        path: str,
        start_line: int = 1,
        end_line: Optional[int] = None,
        encoding: str = "utf-8",
        **kwargs,
    ) -> ToolResult:
        """Read the file contents."""
        # Normalize the path
        path = os.path.normpath(os.path.abspath(path))
        
        # Check if file exists
        if not os.path.exists(path):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"File does not exist: {path}",
            )
        
        if not os.path.isfile(path):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Path is not a file: {path}",
            )
        
        # Check file size
        file_size = os.path.getsize(path)
        if file_size > self.MAX_FILE_SIZE:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"File too large ({file_size} bytes). Maximum is {self.MAX_FILE_SIZE} bytes.",
            )
        
        # Check if it's a text file
        if not self._is_text_file(path):
            return ToolResult(
                status=ToolStatus.FAILED,
                error="File does not appear to be a text file. Binary files are not supported.",
            )
        
        try:
            with open(path, "r", encoding=encoding) as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Apply line range
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line else total_lines
            end_idx = min(end_idx, total_lines)
            
            selected_lines = lines[start_idx:end_idx]
            content = "".join(selected_lines)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Read {len(selected_lines)} lines from {os.path.basename(path)}",
                data={
                    "path": path,
                    "content": content,
                    "total_lines": total_lines,
                    "start_line": start_idx + 1,
                    "end_line": end_idx,
                    "lines_read": len(selected_lines),
                    "file_size": file_size,
                },
            )
            
        except UnicodeDecodeError:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Could not decode file with encoding '{encoding}'",
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Failed to read file: {e}",
            )
