# tools/system/file_write.py
"""
File Write Tool - Writes contents to files.

Requires confirmation before writing.
"""

import os
import shutil
from datetime import datetime
from typing import Optional

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class FileWriteTool(BaseTool):
    """Tool to write content to files."""
    
    # Backup directory for overwritten files
    BACKUP_DIR = ".dmitry_backups"
    
    def __init__(self):
        super().__init__()
        self._name = "file_write"
        self._description = "Write content to a file (requires confirmation)"
        self._permission_level = PermissionLevel.WRITE
        self._needs_confirmation = True
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "description": "Write mode: 'write' (overwrite) or 'append'",
                    "default": "write",
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True,
                },
                "backup": {
                    "type": "boolean",
                    "description": "Create backup before overwriting",
                    "default": True,
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding",
                    "default": "utf-8",
                },
            },
            "required": ["path", "content"],
        }
    
    def _create_backup(self, path: str) -> Optional[str]:
        """Create a backup of an existing file."""
        if not os.path.exists(path):
            return None
        
        try:
            # Create backup directory
            backup_dir = os.path.join(os.path.dirname(path), self.BACKUP_DIR)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            filename = os.path.basename(path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filename}.{timestamp}.bak"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Copy file
            shutil.copy2(path, backup_path)
            
            return backup_path
        except Exception:
            return None
    
    def _execute(
        self,
        path: str,
        content: str,
        mode: str = "write",
        create_dirs: bool = True,
        backup: bool = True,
        encoding: str = "utf-8",
        **kwargs,
    ) -> ToolResult:
        """Write content to the file."""
        # Normalize the path
        path = os.path.normpath(os.path.abspath(path))
        
        # Validate mode
        if mode not in ("write", "append"):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Invalid mode: {mode}. Use 'write' or 'append'.",
            )
        
        # Check if parent directory exists
        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            if create_dirs:
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except Exception as e:
                    return ToolResult(
                        status=ToolStatus.FAILED,
                        error=f"Failed to create directories: {e}",
                    )
            else:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Parent directory does not exist: {parent_dir}",
                )
        
        # Check if we're overwriting an existing file
        file_existed = os.path.exists(path)
        backup_path = None
        
        if file_existed and backup and mode == "write":
            backup_path = self._create_backup(path)
        
        try:
            # Determine file mode
            file_mode = "w" if mode == "write" else "a"
            
            with open(path, file_mode, encoding=encoding) as f:
                f.write(content)
            
            # Get file info
            file_size = os.path.getsize(path)
            lines_written = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            
            message = f"{'Wrote' if mode == 'write' else 'Appended'} to {os.path.basename(path)}"
            if backup_path:
                message += f" (backup: {os.path.basename(backup_path)})"
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=message,
                data={
                    "path": path,
                    "mode": mode,
                    "file_size": file_size,
                    "lines_written": lines_written,
                    "file_existed": file_existed,
                    "backup_path": backup_path,
                },
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Failed to write file: {e}",
            )
    
    def get_confirmation_message(self, params: dict) -> str:
        path = params.get("path", "unknown")
        mode = params.get("mode", "write")
        content_len = len(params.get("content", ""))
        
        if mode == "write":
            return f"Overwrite file '{path}' with {content_len} characters?"
        else:
            return f"Append {content_len} characters to '{path}'?"
