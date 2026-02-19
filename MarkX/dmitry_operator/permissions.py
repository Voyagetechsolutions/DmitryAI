# operator/permissions.py
"""
Dmitry Permission Manager - Safety Layer

Controls what actions can be executed silently vs require confirmation.
Prevents Dmitry from becoming a chaos button.
"""

from enum import Enum
from typing import Dict, Set
from dataclasses import dataclass


class RiskLevel(Enum):
    """Risk classification for actions."""
    LOW = "low"          # No confirmation needed
    MEDIUM = "medium"    # Ask user
    HIGH = "high"        # Explicit confirmation required


@dataclass
class PermissionRule:
    """Rule defining how to handle a tool."""
    tool_name: str
    risk_level: RiskLevel
    description: str


class PermissionManager:
    """
    Manages action permissions and confirmation requirements.
    
    Risk Levels:
    - LOW: Open apps, navigate, search (auto-execute)
    - MEDIUM: Send messages, run scripts (ask first)
    - HIGH: Delete files, move/overwrite, payments (confirm required)
    """
    
    # Tool risk classifications - PROPERLY CONFIGURED
    TOOL_RISKS: Dict[str, RiskLevel] = {
        # LOW RISK: Safe read operations and navigation
        "os.open_app": RiskLevel.LOW,
        "os.open_path": RiskLevel.LOW,
        "os.find_open": RiskLevel.LOW,
        "os.search_files": RiskLevel.LOW,
        "os.focus_app": RiskLevel.LOW,
        "browser.open_url": RiskLevel.LOW,
        "browser.search": RiskLevel.LOW,
        "file.read": RiskLevel.LOW,
        "file.list": RiskLevel.LOW,
        "input.move": RiskLevel.LOW,
        "input.scroll": RiskLevel.LOW,
        
        # MEDIUM RISK: Write operations and modifications
        "os.create_folder": RiskLevel.MEDIUM,
        "file.write": RiskLevel.MEDIUM,
        "file.copy": RiskLevel.MEDIUM,
        "input.click": RiskLevel.MEDIUM,
        "input.type": RiskLevel.MEDIUM,
        "input.hotkey": RiskLevel.MEDIUM,
        "input.press": RiskLevel.MEDIUM,
        "input.drag": RiskLevel.MEDIUM,
        "messaging.draft": RiskLevel.MEDIUM,
        "messaging.send": RiskLevel.MEDIUM,
        
        # HIGH RISK: Destructive operations
        "file.delete": RiskLevel.HIGH,
        "file.move": RiskLevel.HIGH,
        "os.run_script": RiskLevel.HIGH,
    }
    
    # User preferences
    ALWAYS_ALLOW: Set[str] = set()
    ALWAYS_BLOCK: Set[str] = set()
    
    def __init__(self, auto_confirm_low_risk: bool = True):
        """
        Initialize permission manager.
        
        Args:
            auto_confirm_low_risk: If True, LOW risk operations execute without confirmation
        """
        self.auto_confirm_low_risk = auto_confirm_low_risk
    
    def get_risk_level(self, tool_name: str) -> RiskLevel:
        """Get the risk level for a tool."""
        return self.TOOL_RISKS.get(tool_name, RiskLevel.MEDIUM)
    
    def requires_confirmation(self, tool_name: str) -> bool:
        """
        Check if a tool requires user confirmation before execution.
        
        Returns:
            True if confirmation is needed, False if can auto-execute
        """
        # Check user overrides
        if tool_name in self.ALWAYS_ALLOW:
            return False
        if tool_name in self.ALWAYS_BLOCK:
            return True
        
        risk = self.get_risk_level(tool_name)
        
        if risk == RiskLevel.LOW and self.auto_confirm_low_risk:
            return False
        elif risk == RiskLevel.LOW:
            return False
        elif risk == RiskLevel.MEDIUM:
            return True
        elif risk == RiskLevel.HIGH:
            return True
        
        return True  # Default to requiring confirmation
    
    def allow_tool(self, tool_name: str):
        """Add tool to always-allow list."""
        self.ALWAYS_ALLOW.add(tool_name)
        self.ALWAYS_BLOCK.discard(tool_name)
    
    def block_tool(self, tool_name: str):
        """Add tool to always-block list."""
        self.ALWAYS_BLOCK.add(tool_name)
        self.ALWAYS_ALLOW.discard(tool_name)
    
    def reset_tool(self, tool_name: str):
        """Reset tool to default permission."""
        self.ALWAYS_ALLOW.discard(tool_name)
        self.ALWAYS_BLOCK.discard(tool_name)
    
    def get_confirmation_message(self, tool_name: str, args: dict) -> str:
        """Generate a user-friendly confirmation message."""
        risk = self.get_risk_level(tool_name)
        
        messages = {
            "file.delete": f"⚠️ Delete: {args.get('path', 'unknown')}?",
            "file.move": f"📦 Move {args.get('source', '?')} to {args.get('destination', '?')}?",
            "os.create_folder": f"📁 Create folder: {args.get('path', '?')}?",
            "messaging.send": f"📤 Send message to {args.get('contact', '?')}?",
        }
        
        if tool_name in messages:
            return messages[tool_name]
        
        if risk == RiskLevel.HIGH:
            return f"⚠️ Execute {tool_name}?"
        else:
            return f"Execute {tool_name}?"
