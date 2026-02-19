# tools/base_tool.py
"""
Base class for all Dmitry tools.

Tools are capabilities that:
- Perform real-world actions
- Are permission-controlled
- Log all executions
- Are transparent to users
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from datetime import datetime
from enum import Enum

from .permissions import PermissionLevel, check_permission, validate_path_safety


class ToolStatus(Enum):
    """Status of a tool execution."""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class ToolResult:
    """Result of a tool execution."""
    status: ToolStatus
    data: Any = None
    message: str = ""
    error: str = ""
    execution_time_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    @property
    def success(self) -> bool:
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
        }


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self):
        self._name: str = "base_tool"
        self._description: str = "Base tool"
        self._permission_level: PermissionLevel = PermissionLevel.READ
        self._needs_confirmation: bool = False
        self._confirm_callback: Optional[Callable[[], bool]] = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def permission_level(self) -> PermissionLevel:
        return self._permission_level
    
    @property
    def needs_confirmation(self) -> bool:
        return self._needs_confirmation
    
    def set_confirm_callback(self, callback: Callable[[], bool]) -> None:
        """Set the callback for user confirmation."""
        self._confirm_callback = callback
    
    @abstractmethod
    def get_parameters_schema(self) -> dict:
        """
        Return JSON schema for parameters.
        Used for validation and documentation.
        """
        pass
    
    @abstractmethod
    def _execute(self, **params) -> ToolResult:
        """
        Internal execution method to be implemented by subclasses.
        
        This method should NOT check permissions - that's done in execute().
        """
        pass
    
    def validate_params(self, params: dict) -> tuple[bool, str]:
        """
        Validate parameters before execution.
        Override for custom validation.
        """
        schema = self.get_parameters_schema()
        required = schema.get("required", [])
        
        for req in required:
            if req not in params or params[req] is None:
                return False, f"Missing required parameter: {req}"
        
        return True, "Parameters valid."
    
    def check_permissions(self, params: dict) -> tuple[bool, str]:
        """
        Check if execution is permitted with given parameters.
        """
        # Get path if this is a file operation
        path = params.get("path") or params.get("file_path") or params.get("directory")
        
        # Validate path safety if provided
        if path:
            safe, msg = validate_path_safety(path)
            if not safe:
                return False, msg
        
        # Check permission level
        return check_permission(
            self._permission_level,
            path=path,
            confirm_callback=self._confirm_callback if self._needs_confirmation else None,
        )
    
    def execute(self, **params) -> ToolResult:
        """
        Execute the tool with permission checks.
        
        This is the main entry point - handles validation,
        permission checks, and timing.
        """
        import time
        start_time = time.time()
        
        try:
            # Validate parameters
            valid, msg = self.validate_params(params)
            if not valid:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=msg,
                )
            
            # Check permissions
            allowed, msg = self.check_permissions(params)
            if not allowed:
                status = ToolStatus.BLOCKED
                if "cancelled" in msg.lower():
                    status = ToolStatus.CANCELLED
                
                return ToolResult(
                    status=status,
                    error=msg,
                )
            
            # Execute the tool
            result = self._execute(**params)
            
            # Add execution time
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
    
    def get_confirmation_message(self, params: dict) -> str:
        """
        Get the message to show when asking for confirmation.
        Override for custom messages.
        """
        return f"Allow {self._name} with parameters: {params}?"
    
    def __repr__(self) -> str:
        return f"Tool({self._name}, permission={self._permission_level.value})"
