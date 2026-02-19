# tools/system/open_folder.py
"""
Open Folder Tool - Opens a folder in the file explorer.
"""

import os
import subprocess
import platform

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class OpenFolderTool(BaseTool):
    """Tool to open a folder in the system file explorer."""
    
    def __init__(self):
        super().__init__()
        self._name = "open_folder"
        self._description = "Open a folder in the file explorer"
        self._permission_level = PermissionLevel.OPEN
        self._needs_confirmation = False
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the folder to open",
                }
            },
            "required": ["path"],
        }
    
    def _execute(self, path: str, **kwargs) -> ToolResult:
        """Open the folder in the system file explorer."""
        # Normalize the path
        path = os.path.normpath(os.path.abspath(path))
        
        # Check if path exists
        if not os.path.exists(path):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Path does not exist: {path}",
            )
        
        # Get the folder (if path is a file, get its directory)
        if os.path.isfile(path):
            folder = os.path.dirname(path)
        else:
            folder = path
        
        try:
            system = platform.system()
            
            if system == "Windows":
                os.startfile(folder)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", folder], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", folder], check=True)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Opened folder: {folder}",
                data={"path": folder},
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Failed to open folder: {e}",
            )
    
    def get_confirmation_message(self, params: dict) -> str:
        return f"Open folder: {params.get('path', 'unknown')}?"
