# tools/registry.py
"""
Tool Registry - Central management of all available tools.

Handles:
- Tool registration
- Tool discovery by mode
- Tool execution with logging
"""

from typing import Callable, Optional
from .base_tool import BaseTool, ToolResult, ToolStatus
from .logging import get_action_logger


class ToolRegistry:
    """
    Central registry for all available tools.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._tools: dict[str, BaseTool] = {}
        self._current_mode: str = "general"
        self._confirm_callback: Optional[Callable[[str], bool]] = None
        self._logger = get_action_logger()
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: The tool instance to register
        """
        if tool.name in self._tools:
            print(f"⚠️ Tool '{tool.name}' already registered, replacing.")
        
        self._tools[tool.name] = tool
        
        # Set confirm callback if available
        if self._confirm_callback and tool.needs_confirmation:
            tool.set_confirm_callback(
                lambda: self._confirm_callback(tool.get_confirmation_message({}))
            )
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of the tool to remove
            
        Returns:
            True if removed, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_tool_names(self) -> list[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())
    
    def get_tools_for_mode(self, mode_name: str, allowed_tools: list[str]) -> list[BaseTool]:
        """
        Get tools available for a specific mode.
        
        Args:
            mode_name: The mode name
            allowed_tools: List of tool names allowed in this mode
            
        Returns:
            List of tool instances
        """
        return [
            tool for name, tool in self._tools.items()
            if name in allowed_tools
        ]
    
    def set_current_mode(self, mode: str) -> None:
        """Set the current mode for logging purposes."""
        self._current_mode = mode
    
    def set_confirm_callback(self, callback: Callable[[str], bool]) -> None:
        """
        Set the global confirmation callback.
        
        Args:
            callback: Function that takes a message and returns True/False
        """
        self._confirm_callback = callback
        
        # Update all tools that need confirmation
        for tool in self._tools.values():
            if tool.needs_confirmation:
                def make_callback(t):
                    return lambda: callback(t.get_confirmation_message({}))
                tool.set_confirm_callback(make_callback(tool))
    
    def execute(
        self,
        tool_name: str,
        params: dict = None,
        confirm_callback: Callable[[], bool] = None,
    ) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            confirm_callback: Optional override for confirmation
            
        Returns:
            ToolResult from the execution
        """
        params = params or {}
        
        # Get the tool
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Tool '{tool_name}' not found.",
            )
        
        # Set confirmation callback if provided
        if confirm_callback:
            tool.set_confirm_callback(confirm_callback)
        elif self._confirm_callback and tool.needs_confirmation:
            tool.set_confirm_callback(
                lambda: self._confirm_callback(tool.get_confirmation_message(params))
            )
        
        # Execute the tool
        result = tool.execute(**params)
        
        # Log the action
        self._logger.log_action(
            mode=self._current_mode,
            tool=tool_name,
            parameters=params,
            result_status=result.status.value,
            result_message=result.message or result.error,
            execution_time_ms=result.execution_time_ms,
            user_confirmed=tool.needs_confirmation,
        )
        
        return result
    
    def get_tools_info(self) -> list[dict]:
        """Get information about all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "permission_level": tool.permission_level.value,
                "needs_confirmation": tool.needs_confirmation,
            }
            for tool in self._tools.values()
        ]
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools


# Global registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
