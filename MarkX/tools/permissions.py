# tools/permissions.py
"""
Permission levels and validation for tool execution.

Permission Matrix (from PRD):
| Action Type           | Allowed | Needs Confirmation |
| Read files            | ✅       | ❌                  |
| Write project files   | ✅       | ⚠️                 |
| Open folders/apps     | ✅       | ❌                  |
| Run scripts           | ⚠️      | ✅                  |
| Delete/move files     | ❌       | Always blocked     |
| Apply security policy | ❌       | Requires approval  |
"""

from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional
import os


class PermissionLevel(Enum):
    """Permission levels for tools."""
    READ = "read"           # File reads, listings - always allowed
    OPEN = "open"           # Open folders/apps - allowed
    WRITE = "write"         # Project file writes - needs confirmation
    EXECUTE = "execute"     # Run scripts - needs confirmation
    DANGEROUS = "dangerous" # Delete/move files - always blocked


@dataclass
class PermissionConfig:
    """Configuration for a permission level."""
    level: PermissionLevel
    allowed: bool
    needs_confirmation: bool
    blocked_message: str = ""


# Permission matrix from PRD
PERMISSION_MATRIX: dict[PermissionLevel, PermissionConfig] = {
    PermissionLevel.READ: PermissionConfig(
        level=PermissionLevel.READ,
        allowed=True,
        needs_confirmation=False,
    ),
    PermissionLevel.OPEN: PermissionConfig(
        level=PermissionLevel.OPEN,
        allowed=True,
        needs_confirmation=False,
    ),
    PermissionLevel.WRITE: PermissionConfig(
        level=PermissionLevel.WRITE,
        allowed=True,
        needs_confirmation=True,
    ),
    PermissionLevel.EXECUTE: PermissionConfig(
        level=PermissionLevel.EXECUTE,
        allowed=True,
        needs_confirmation=True,
    ),
    PermissionLevel.DANGEROUS: PermissionConfig(
        level=PermissionLevel.DANGEROUS,
        allowed=False,
        needs_confirmation=False,
        blocked_message="This action is blocked for safety. Destructive file operations are not allowed.",
    ),
}


class AllowedPaths:
    """
    Manages allowed directories for file operations.
    All file operations are restricted to these paths.
    """
    
    def __init__(self, allowed_dirs: list[str] = None):
        """Initialize with allowed directories."""
        self._allowed_dirs: list[str] = []
        
        if allowed_dirs:
            for d in allowed_dirs:
                self.add_allowed_dir(d)
        else:
            # Default: user's Documents and current project
            home = os.path.expanduser("~")
            self.add_allowed_dir(os.path.join(home, "Documents"))
    
    def add_allowed_dir(self, directory: str) -> None:
        """Add a directory to allowed list."""
        normalized = os.path.normpath(os.path.abspath(directory))
        if normalized not in self._allowed_dirs:
            self._allowed_dirs.append(normalized)
    
    def remove_allowed_dir(self, directory: str) -> bool:
        """Remove a directory from allowed list."""
        normalized = os.path.normpath(os.path.abspath(directory))
        if normalized in self._allowed_dirs:
            self._allowed_dirs.remove(normalized)
            return True
        return False
    
    def is_allowed(self, path: str) -> bool:
        """Check if a path is within allowed directories."""
        normalized = os.path.normpath(os.path.abspath(path))
        
        for allowed_dir in self._allowed_dirs:
            try:
                # Check if path is under allowed directory
                if normalized.startswith(allowed_dir + os.sep) or normalized == allowed_dir:
                    return True
            except Exception:
                continue
        
        return False
    
    def get_allowed_dirs(self) -> list[str]:
        """Get list of allowed directories."""
        return self._allowed_dirs.copy()


# Global allowed paths instance
_allowed_paths = AllowedPaths()


def get_allowed_paths() -> AllowedPaths:
    """Get the global allowed paths instance."""
    return _allowed_paths


def check_permission(
    level: PermissionLevel,
    path: str = None,
    confirm_callback: Callable[[], bool] = None,
) -> tuple[bool, str]:
    """
    Check if an action is permitted.
    
    Args:
        level: The permission level required
        path: Optional path to validate against allowed directories
        confirm_callback: Optional callback to get user confirmation
        
    Returns:
        (allowed, message) tuple
    """
    config = PERMISSION_MATRIX.get(level)
    
    if not config:
        return False, f"Unknown permission level: {level}"
    
    # Check if action type is allowed at all
    if not config.allowed:
        return False, config.blocked_message
    
    # Check path restrictions for file operations
    if path and level in (PermissionLevel.READ, PermissionLevel.WRITE):
        if not _allowed_paths.is_allowed(path):
            return False, f"Path '{path}' is outside allowed directories."
    
    # Check if confirmation is needed
    if config.needs_confirmation:
        if confirm_callback is None:
            return False, f"Action requires confirmation but no confirmation callback provided."
        
        if not confirm_callback():
            return False, "Action cancelled by user."
    
    return True, "Action permitted."


def validate_path_safety(path: str) -> tuple[bool, str]:
    """
    Validate that a path is safe to operate on.
    
    Checks:
    - Path traversal attacks (..)
    - Absolute path requirements
    - Special system directories
    """
    if not path:
        return False, "Empty path provided."
    
    # Normalize the path
    normalized = os.path.normpath(path)
    
    # Check for path traversal
    if ".." in path:
        return False, "Path traversal detected. '..' is not allowed."
    
    # Block operations on system directories
    system_dirs = [
        os.environ.get("SYSTEMROOT", "C:\\Windows"),
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        "C:\\Windows",
        "C:\\Program Files",
    ]
    
    for sys_dir in system_dirs:
        if sys_dir and normalized.lower().startswith(sys_dir.lower()):
            return False, f"Operations on system directory '{sys_dir}' are blocked."
    
    return True, "Path is safe."
