# tools/__init__.py
"""
Dmitry v1.2 Tool System

Tools are capabilities shared across modes, with permission controls.
All real-world actions happen via tools - no blind execution.
"""

from .base_tool import BaseTool, ToolResult
from .permissions import PermissionLevel, check_permission
from .registry import ToolRegistry
from .logging import ActionLogger

# Singleton logger instance
_action_logger = None

def get_action_logger() -> ActionLogger:
    """Get the global action logger instance."""
    global _action_logger
    if _action_logger is None:
        _action_logger = ActionLogger()
    return _action_logger

__all__ = [
    "BaseTool",
    "ToolResult",
    "PermissionLevel",
    "check_permission",
    "ToolRegistry",
    "ActionLogger",
    "get_action_logger",
]
