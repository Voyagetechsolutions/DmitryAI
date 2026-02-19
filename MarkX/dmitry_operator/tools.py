# operator/tools.py
"""
Dmitry Operator Tools - Device Action Functions

These are the "hands" Dmitry uses to interact with the OS.
Each tool is a discrete, safe action that can be executed.
"""

import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ToolResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActionResult:
    """Result of a tool execution."""
    status: ToolResult
    message: str
    data: Optional[Dict[str, Any]] = None


class OperatorTools:
    """
    Core tools for device interaction.
    
    Categories:
    - os.* - Operating system actions
    - browser.* - Web browser actions
    - file.* - File system operations
    """
    
    def __init__(self):
        self.user_home = Path.home()
        self.common_apps = {
            "explorer": "explorer",
            "file explorer": "explorer",
            "notepad": "notepad",
            "calculator": "calc",
            "chrome": "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "code": "code",
            "vscode": "code",
            "terminal": "wt",
            "cmd": "cmd",
            "powershell": "powershell",
        }
        # Common folder shortcuts
        self.common_folders = {
            "documents": str(self.user_home / "Documents"),
            "document": str(self.user_home / "Documents"),
            "docs": str(self.user_home / "Documents"),
            "desktop": str(self.user_home / "Desktop"),
            "downloads": str(self.user_home / "Downloads"),
            "download": str(self.user_home / "Downloads"),
            "pictures": str(self.user_home / "Pictures"),
            "photos": str(self.user_home / "Pictures"),
            "music": str(self.user_home / "Music"),
            "videos": str(self.user_home / "Videos"),
            "home": str(self.user_home),
            "user": str(self.user_home),
        }
    
    # ========== OS TOOLS ==========
    
    def os_open_app(self, app: str) -> ActionResult:
        """
        Launch an application.
        
        Args:
            app: Application name or executable
        """
        app_lower = app.lower()
        executable = self.common_apps.get(app_lower, app)
        
        try:
            # Windows-specific launch
            if os.name == 'nt':
                subprocess.Popen(
                    executable,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen([executable])
            
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Opened {app}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to open {app}: {str(e)}"
            )
    
    def os_open_path(self, path: str) -> ActionResult:
        """
        Open a file or folder.
        
        Args:
            path: File or folder path (supports ~ for home and common names like 'documents')
        """
        path_lower = path.lower().strip()
        
        # Check common folder shortcuts first
        if path_lower in self.common_folders:
            expanded = self.common_folders[path_lower]
        else:
            # Expand path normally
            expanded = os.path.expanduser(path)
            expanded = os.path.expandvars(expanded)
        
        if not os.path.exists(expanded):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Path not found: {expanded}"
            )
        
        try:
            os.startfile(expanded)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Opened {expanded}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to open path: {str(e)}"
            )
    
    def os_find_open(self, name: str, item_type: str = "any") -> ActionResult:
        """
        Find and open a file or folder by name (searches common locations).
        
        Args:
            name: Name of file or folder to find and open
            item_type: "file", "folder", or "any"
        """
        name_lower = name.lower().strip()
        
        # Check common folder shortcuts first
        if name_lower in self.common_folders:
            try:
                os.startfile(self.common_folders[name_lower])
                return ActionResult(
                    status=ToolResult.SUCCESS,
                    message=f"Opened {self.common_folders[name_lower]}"
                )
            except Exception as e:
                pass
        
        # Priority search locations (most likely places for new downloads, projects, etc.)
        search_locations = [
            self.user_home / "Downloads",
            self.user_home / "Desktop",
            self.user_home / "Documents",
            self.user_home,
            Path("C:/"),
        ]
        
        found_items = []
        
        for base_path in search_locations:
            if not base_path.exists():
                continue
            
            try:
                # Search one level deep first (faster)
                for item in base_path.iterdir():
                    if name_lower in item.name.lower():
                        # Filter by type if specified
                        if item_type == "file" and not item.is_file():
                            continue
                        if item_type == "folder" and not item.is_dir():
                            continue
                        found_items.append(item)
                        
                        # Open the first match immediately
                        if len(found_items) == 1:
                            os.startfile(str(item))
                            return ActionResult(
                                status=ToolResult.SUCCESS,
                                message=f"Opened {item}",
                                data={"path": str(item)}
                            )
            except PermissionError:
                continue
        
        # If nothing found in first level, do a deeper search
        for base_path in search_locations[:3]:  # Only search top 3 for performance
            if not base_path.exists():
                continue
            try:
                for item in base_path.rglob(f"*{name_lower}*"):
                    if item_type == "file" and not item.is_file():
                        continue
                    if item_type == "folder" and not item.is_dir():
                        continue
                    
                    os.startfile(str(item))
                    return ActionResult(
                        status=ToolResult.SUCCESS,
                        message=f"Opened {item}",
                        data={"path": str(item)}
                    )
            except (PermissionError, OSError):
                continue
        
        return ActionResult(
            status=ToolResult.FAILED,
            message=f"Could not find '{name}' in Downloads, Desktop, Documents, or Home"
        )
    
    def os_create_folder(self, path: str) -> ActionResult:
        """
        Create a new folder.
        
        Args:
            path: Folder path to create
        """
        expanded = os.path.expanduser(path)
        
        try:
            os.makedirs(expanded, exist_ok=True)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Created folder: {expanded}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to create folder: {str(e)}"
            )
    
    def os_search_files(
        self, 
        query: str, 
        path: Optional[str] = None,
        limit: int = 10
    ) -> ActionResult:
        """
        Search for files matching query.
        
        Args:
            query: Search pattern
            path: Directory to search (default: user home)
            limit: Max results to return
        """
        search_path = Path(os.path.expanduser(path)) if path else self.user_home
        
        try:
            results = []
            for file in search_path.rglob(f"*{query}*"):
                if len(results) >= limit:
                    break
                results.append(str(file))
            
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Found {len(results)} files",
                data={"files": results}
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Search failed: {str(e)}"
            )
    
    def os_focus_app(self, app: str) -> ActionResult:
        """Bring an app window to foreground (Windows)."""
        try:
            # Use PowerShell to focus window
            script = f'''
            $app = Get-Process | Where-Object {{$_.MainWindowTitle -like "*{app}*"}} | Select-Object -First 1
            if ($app) {{
                [void] [System.Reflection.Assembly]::LoadWithPartialName("Microsoft.VisualBasic")
                [Microsoft.VisualBasic.Interaction]::AppActivate($app.Id)
            }}
            '''
            subprocess.run(["powershell", "-Command", script], capture_output=True)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Focused {app}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to focus: {str(e)}"
            )
    
    # ========== BROWSER TOOLS ==========
    
    def browser_open_url(self, url: str) -> ActionResult:
        """
        Open a URL in the default browser.
        
        Args:
            url: URL to open
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        try:
            webbrowser.open(url)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Opened {url}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to open URL: {str(e)}"
            )
    
    def browser_search(self, query: str, engine: str = "google") -> ActionResult:
        """
        Search the web.
        
        Args:
            query: Search query
            engine: Search engine (google, bing, duckduckgo)
        """
        engines = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q=",
        }
        
        base_url = engines.get(engine.lower(), engines["google"])
        search_url = base_url + query.replace(" ", "+")
        
        return self.browser_open_url(search_url)
    
    # ========== FILE TOOLS ==========
    
    def file_read(self, path: str) -> ActionResult:
        """
        Read the contents of a file.
        
        Args:
            path: File path to read
        """
        expanded = os.path.expanduser(path)
        
        if not os.path.exists(expanded):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"File not found: {expanded}"
            )
        
        if os.path.isdir(expanded):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Path is a directory, not a file: {expanded}"
            )
        
        try:
            with open(expanded, 'r', encoding='utf-8') as f:
                content = f.read()
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Read {len(content)} characters from {expanded}",
                data={"content": content, "path": expanded}
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to read file: {str(e)}"
            )
    
    def file_write(self, path: str, content: str, mode: str = "write") -> ActionResult:
        """
        Write content to a file.
        
        Args:
            path: File path to write
            content: Content to write
            mode: "write" (overwrite) or "append"
        """
        expanded = os.path.expanduser(path)
        
        # Create parent directories if needed
        parent = os.path.dirname(expanded)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        
        try:
            file_mode = 'a' if mode == "append" else 'w'
            with open(expanded, file_mode, encoding='utf-8') as f:
                f.write(content)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Wrote {len(content)} characters to {expanded}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to write file: {str(e)}"
            )
    
    def file_list(self, path: str = None) -> ActionResult:
        """
        List contents of a directory.
        
        Args:
            path: Directory path (default: current directory)
        """
        if path:
            path_lower = path.lower().strip()
            if path_lower in self.common_folders:
                expanded = self.common_folders[path_lower]
            else:
                expanded = os.path.expanduser(path)
        else:
            expanded = os.getcwd()
        
        if not os.path.exists(expanded):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Directory not found: {expanded}"
            )
        
        if not os.path.isdir(expanded):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Path is not a directory: {expanded}"
            )
        
        try:
            items = []
            for item in os.listdir(expanded):
                full_path = os.path.join(expanded, item)
                item_type = "folder" if os.path.isdir(full_path) else "file"
                items.append({"name": item, "type": item_type, "path": full_path})
            
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Found {len(items)} items in {expanded}",
                data={"items": items, "directory": expanded}
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Failed to list directory: {str(e)}"
            )
    
    def file_copy(self, source: str, destination: str) -> ActionResult:
        """
        Copy a file or folder.
        
        Args:
            source: Source path
            destination: Destination path
        """
        src = os.path.expanduser(source)
        dst = os.path.expanduser(destination)
        
        if not os.path.exists(src):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Source not found: {src}"
            )
        
        try:
            import shutil
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Copied {src} to {dst}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Copy failed: {str(e)}"
            )
    
    def file_move(self, source: str, destination: str) -> ActionResult:
        """
        Move a file or folder.
        
        Args:
            source: Source path
            destination: Destination path
        """
        src = os.path.expanduser(source)
        dst = os.path.expanduser(destination)
        
        if not os.path.exists(src):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Source not found: {src}"
            )
        
        try:
            import shutil
            shutil.move(src, dst)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Moved {src} to {dst}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Move failed: {str(e)}"
            )
    
    def file_delete(self, path: str) -> ActionResult:
        """
        Delete a file or folder.
        
        Args:
            path: Path to delete
        """
        expanded = os.path.expanduser(path)
        
        if not os.path.exists(expanded):
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Path not found: {expanded}"
            )
        
        try:
            if os.path.isdir(expanded):
                import shutil
                shutil.rmtree(expanded)
            else:
                os.remove(expanded)
            
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Deleted {expanded}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Delete failed: {str(e)}"
            )
    
    # ========== INPUT CONTROL TOOLS ==========
    
    def input_click(self, x: int = None, y: int = None, button: str = "left", clicks: int = 1) -> ActionResult:
        """
        Click the mouse at a position.
        
        Args:
            x: X coordinate (None = current position)
            y: Y coordinate (None = current position)
            button: "left", "right", or "middle"
            clicks: Number of clicks (2 for double-click)
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False  # Disable fail-safe for God Mode
            
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)
            
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Clicked {button} button {clicks}x at ({x}, {y})"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Click failed: {str(e)}"
            )
    
    def input_move(self, x: int, y: int, duration: float = 0.25) -> ActionResult:
        """
        Move the mouse to a position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Time to move (seconds)
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.moveTo(x, y, duration=duration)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Moved mouse to ({x}, {y})"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Move failed: {str(e)}"
            )
    
    def input_type(self, text: str, interval: float = 0.02) -> ActionResult:
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.typewrite(text, interval=interval)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Typed: {text[:50]}..."
            )
        except Exception as e:
            # Fallback for special characters
            try:
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
                return ActionResult(
                    status=ToolResult.SUCCESS,
                    message=f"Pasted: {text[:50]}..."
                )
            except:
                return ActionResult(
                    status=ToolResult.FAILED,
                    message=f"Type failed: {str(e)}"
                )
    
    def input_hotkey(self, *keys) -> ActionResult:
        """
        Press a keyboard hotkey combination.
        
        Args:
            keys: Keys to press (e.g., "ctrl", "c" for Ctrl+C)
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.hotkey(*keys)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Pressed: {'+'.join(keys)}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Hotkey failed: {str(e)}"
            )
    
    def input_press(self, key: str) -> ActionResult:
        """
        Press a single key.
        
        Args:
            key: Key to press (e.g., "enter", "tab", "escape", "f1")
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.press(key)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Pressed: {key}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Press failed: {str(e)}"
            )
    
    def input_scroll(self, amount: int, x: int = None, y: int = None) -> ActionResult:
        """
        Scroll the mouse wheel.
        
        Args:
            amount: Scroll amount (positive = up, negative = down)
            x: X position to scroll at (optional)
            y: Y position to scroll at (optional)
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            if x is not None and y is not None:
                pyautogui.scroll(amount, x, y)
            else:
                pyautogui.scroll(amount)
            direction = "up" if amount > 0 else "down"
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Scrolled {direction} by {abs(amount)}"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Scroll failed: {str(e)}"
            )
    
    def input_drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> ActionResult:
        """
        Drag from one position to another.
        
        Args:
            x1, y1: Start position
            x2, y2: End position
            duration: Time to drag
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.moveTo(x1, y1)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration)
            return ActionResult(
                status=ToolResult.SUCCESS,
                message=f"Dragged from ({x1},{y1}) to ({x2},{y2})"
            )
        except Exception as e:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Drag failed: {str(e)}"
            )
    
    # ========== TOOL REGISTRY ==========
    
    def get_tool(self, tool_name: str):
        """Get a tool function by name."""
        tool_map = {
            "os.open_app": self.os_open_app,
            "os.open_path": self.os_open_path,
            "os.create_folder": self.os_create_folder,
            "os.find_open": self.os_find_open,
            "os.search_files": self.os_search_files,
            "os.focus_app": self.os_focus_app,
            "browser.open_url": self.browser_open_url,
            "browser.search": self.browser_search,
            "file.read": self.file_read,
            "file.write": self.file_write,
            "file.list": self.file_list,
            "file.copy": self.file_copy,
            "file.move": self.file_move,
            "file.delete": self.file_delete,
            "input.click": self.input_click,
            "input.move": self.input_move,
            "input.type": self.input_type,
            "input.hotkey": self.input_hotkey,
            "input.press": self.input_press,
            "input.scroll": self.input_scroll,
            "input.drag": self.input_drag,
        }
        return tool_map.get(tool_name)
    
    def list_tools(self) -> list:
        """List all available tools."""
        return [
            "os.open_app",
            "os.open_path", 
            "os.create_folder",
            "os.find_open",
            "os.search_files",
            "os.focus_app",
            "browser.open_url",
            "browser.search",
            "file.read",
            "file.write",
            "file.list",
            "file.copy",
            "file.move",
            "file.delete",
            "input.click",
            "input.move",
            "input.type",
            "input.hotkey",
            "input.press",
            "input.scroll",
            "input.drag",
        ]
