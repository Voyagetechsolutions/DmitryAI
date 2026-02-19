# tools/system/launch_app.py
"""
Launch App Tool - Launches applications by name.

Refactored from the original open_app.py action.
"""

import os
import subprocess
import platform
from typing import Optional

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


# Common application mappings (Windows)
APP_MAPPINGS = {
    # Browsers
    "chrome": ["chrome", "google chrome"],
    "firefox": ["firefox", "mozilla firefox"],
    "edge": ["msedge", "microsoft edge", "edge"],
    "brave": ["brave", "brave browser"],
    
    # Development
    "vscode": ["code", "visual studio code", "vs code"],
    "pycharm": ["pycharm", "pycharm64"],
    "terminal": ["cmd", "command prompt", "powershell", "terminal"],
    "git bash": ["git-bash", "git bash"],
    
    # Communication
    "discord": ["discord"],
    "slack": ["slack"],
    "teams": ["teams", "microsoft teams"],
    "whatsapp": ["whatsapp"],
    "telegram": ["telegram"],
    
    # Productivity
    "notepad": ["notepad"],
    "word": ["winword", "microsoft word", "word"],
    "excel": ["excel", "microsoft excel"],
    "powerpoint": ["powerpnt", "powerpoint", "microsoft powerpoint"],
    "outlook": ["outlook", "microsoft outlook"],
    
    # Media
    "spotify": ["spotify"],
    "vlc": ["vlc", "vlc media player"],
    "youtube": ["youtube"],  # Will open in browser
    
    # System
    "settings": ["ms-settings:", "settings"],
    "calculator": ["calc", "calculator"],
    "explorer": ["explorer", "file explorer"],
    "task manager": ["taskmgr", "task manager"],
}


class LaunchAppTool(BaseTool):
    """Tool to launch applications by name."""
    
    def __init__(self):
        super().__init__()
        self._name = "launch_app"
        self._description = "Launch an application by name"
        self._permission_level = PermissionLevel.OPEN
        self._needs_confirmation = False
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the application to launch",
                },
            },
            "required": ["app_name"],
        }
    
    def _find_app_executable(self, app_name: str) -> Optional[str]:
        """Try to find the executable for an app."""
        app_lower = app_name.lower().strip()
        
        # Check mappings
        for exe, aliases in APP_MAPPINGS.items():
            if app_lower in aliases or app_lower == exe:
                return exe
        
        # Return the name as-is (might work if it's in PATH)
        return app_name
    
    def _launch_windows(self, app_name: str) -> ToolResult:
        """Launch application on Windows."""
        executable = self._find_app_executable(app_name)
        
        # Handle special cases
        if executable == "youtube":
            os.startfile("https://www.youtube.com")
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message="Opened YouTube in browser",
                data={"app": "youtube", "type": "web"},
            )
        
        if executable.startswith("ms-settings:"):
            os.startfile(executable)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message="Opened Windows Settings",
                data={"app": "settings", "type": "system"},
            )
        
        try:
            # Try to start the app
            os.startfile(executable)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Launched {app_name}",
                data={"app": app_name, "executable": executable},
            )
        except FileNotFoundError:
            # Try using 'start' command
            try:
                subprocess.Popen(
                    f'start "" "{executable}"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    message=f"Launched {app_name}",
                    data={"app": app_name, "executable": executable},
                )
            except Exception as e:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Could not find or launch '{app_name}': {e}",
                )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Failed to launch '{app_name}': {e}",
            )
    
    def _launch_mac(self, app_name: str) -> ToolResult:
        """Launch application on macOS."""
        try:
            subprocess.run(["open", "-a", app_name], check=True)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Launched {app_name}",
                data={"app": app_name},
            )
        except subprocess.CalledProcessError:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Could not find application '{app_name}'",
            )
    
    def _launch_linux(self, app_name: str) -> ToolResult:
        """Launch application on Linux."""
        try:
            subprocess.Popen(
                [app_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Launched {app_name}",
                data={"app": app_name},
            )
        except FileNotFoundError:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Could not find application '{app_name}'",
            )
    
    def _execute(self, app_name: str, **kwargs) -> ToolResult:
        """Launch the application."""
        if not app_name or not app_name.strip():
            return ToolResult(
                status=ToolStatus.FAILED,
                error="Application name is required",
            )
        
        system = platform.system()
        
        if system == "Windows":
            return self._launch_windows(app_name)
        elif system == "Darwin":
            return self._launch_mac(app_name)
        else:
            return self._launch_linux(app_name)
    
    def get_confirmation_message(self, params: dict) -> str:
        return f"Launch application: {params.get('app_name', 'unknown')}?"
