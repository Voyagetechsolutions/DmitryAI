# modes/mode_manager.py
"""
Mode Manager - Central orchestrator for cognitive modes.

Handles:
- Mode switching
- Mode context building
- Default mode selection
- Mode persistence across sessions
"""

from typing import Optional
from .base_mode import BaseMode, ModeContext
from .general_mode import GeneralMode
from .design_mode import DesignMode
from .developer_mode import DeveloperMode
from .research_mode import ResearchMode
from .simulation_mode import SimulationMode
from .utility_mode import UtilityMode

# Import Enhanced Security Mode
try:
    from .security_mode_enhanced import EnhancedSecurityMode
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError:
    from .security_mode import SecurityMode
    ENHANCED_SECURITY_AVAILABLE = False


class ModeManager:
    """Central manager for cognitive modes."""
    
    # Mode name aliases for natural language switching
    MODE_ALIASES = {
        # General mode
        "general": "general",
        "default": "general",
        "normal": "general",
        "chat": "general",
        "conversation": "general",
        
        # Design mode (formerly architect)
        "design": "design",
        "system design": "design",
        "planning": "design",
        "architect": "design",
        "architecture": "design",
        
        # Developer mode
        "developer": "developer",
        "dev": "developer",
        "code": "developer",
        "coding": "developer",
        "programming": "developer",
        "debug": "developer",
        
        # Research mode
        "research": "research",
        "search": "research",
        "investigate": "research",
        "compare": "research",
        
        # Security mode
        "security": "security",
        "secure": "security",
        "audit": "security",
        "compliance": "security",
        "governance": "security",
        
        # Simulation mode
        "simulation": "simulation",
        "simulate": "simulation",
        "whatif": "simulation",
        "what-if": "simulation",
        "predict": "simulation",
        "impact": "simulation",
        
        # Utility mode (casual helper)
        "utility": "utility",
        "helper": "utility",
        "casual": "utility",
        "simple": "utility",
        "write": "utility",
        "caption": "utility",
        "reply": "utility",
    }
    
    def __init__(self):
        """Initialize the mode manager with all available modes."""
        # Use Enhanced Security Mode if available
        if ENHANCED_SECURITY_AVAILABLE:
            security_mode = EnhancedSecurityMode()
            print("✓ Enhanced Security Mode loaded")
        else:
            security_mode = SecurityMode()
            print("⚠ Using basic Security Mode (Enhanced version not available)")
        
        self._modes: dict[str, BaseMode] = {
            "utility": UtilityMode(),  # Default startup mode
            "general": GeneralMode(),
            "design": DesignMode(),
            "developer": DeveloperMode(),
            "research": ResearchMode(),
            "security": security_mode,  # Enhanced or basic
            "simulation": SimulationMode(),
        }
        # Dmitry starts in Utility Mode (casual helper)
        self._current_mode_name: str = "utility"
        self._mode_history: list[str] = ["utility"]
    
    @property
    def current_mode(self) -> BaseMode:
        """Get the current active mode."""
        return self._modes[self._current_mode_name]
    
    @property
    def current_mode_name(self) -> str:
        """Get the current mode name."""
        return self._current_mode_name
    
    def get_mode(self, mode_name: str) -> Optional[BaseMode]:
        """Get a mode by name."""
        normalized = self._normalize_mode_name(mode_name)
        return self._modes.get(normalized)
    
    def _normalize_mode_name(self, name: str) -> str:
        """Normalize mode name using aliases."""
        name_lower = name.lower().strip()
        return self.MODE_ALIASES.get(name_lower, name_lower)
    
    def switch_mode(self, mode_name: str) -> tuple[bool, str]:
        """
        Switch to a different mode.
        
        Returns:
            (success, message) tuple
        """
        normalized = self._normalize_mode_name(mode_name)
        
        if normalized not in self._modes:
            available = ", ".join(self._modes.keys())
            return False, f"Unknown mode '{mode_name}'. Available modes: {available}"
        
        if normalized == self._current_mode_name:
            return True, f"Already in {self.current_mode} mode."
        
        previous_mode = self._current_mode_name
        self._current_mode_name = normalized
        self._mode_history.append(normalized)
        
        # Keep history limited
        if len(self._mode_history) > 20:
            self._mode_history = self._mode_history[-20:]
        
        new_mode = self.current_mode
        return True, f"Switched from {previous_mode.title()} to {new_mode}"
    
    def get_available_modes(self) -> list[dict]:
        """Get list of available modes with details."""
        return [
            {
                "name": mode.name,
                "description": mode.description,
                "icon": mode.icon,
                "is_current": mode.name == self._current_mode_name,
            }
            for mode in self._modes.values()
        ]
    
    def get_mode_history(self) -> list[str]:
        """Get history of mode switches."""
        return self._mode_history.copy()
    
    def previous_mode(self) -> tuple[bool, str]:
        """Switch back to the previous mode."""
        if len(self._mode_history) < 2:
            return False, "No previous mode in history."
        
        # Remove current mode from history
        self._mode_history.pop()
        previous = self._mode_history[-1]
        
        # Don't add to history again, just set it
        self._current_mode_name = previous
        
        return True, f"Returned to {self.current_mode}"
    
    def build_context(
        self,
        user_message: str,
        memory_context: dict = None,
        rag_context: str = "",
        conversation_history: list = None,
        available_tools: list = None,
    ) -> ModeContext:
        """Build context for the current mode."""
        return ModeContext(
            user_message=user_message,
            memory_context=memory_context or {},
            rag_context=rag_context,
            conversation_history=conversation_history or [],
            available_tools=available_tools or self.current_mode.allowed_tools,
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the current mode."""
        return self.current_mode.get_system_prompt()
    
    def build_user_prompt(self, context: ModeContext) -> str:
        """Build the user prompt using the current mode."""
        return self.current_mode.build_prompt(context)
    
    def detect_suggested_mode(self, user_message: str) -> Optional[str]:
        """
        Detect if user message suggests switching to a different mode.
        
        Returns suggested mode name or None.
        """
        message_lower = user_message.lower()
        
        # Explicit mode switch commands
        switch_patterns = [
            "switch to",
            "go to",
            "enter",
            "use",
            "activate",
            "mode:",
        ]
        
        for pattern in switch_patterns:
            if pattern in message_lower:
                for alias, mode in self.MODE_ALIASES.items():
                    if alias in message_lower:
                        return mode
        
        # Implicit mode detection - DISABLED to prevent random switching
        # Users must explicitly ask to switch modes (e.g. "Switch to Developer Mode")
        """
        if any(kw in message_lower for kw in ["design", "architecture", "schema", "api design"]):
            return "design"
        
        if any(kw in message_lower for kw in ["code", "function", "debug", "fix this", "implement"]):
            return "developer"
        
        if any(kw in message_lower for kw in ["research", "compare", "what is", "how does"]):
            return "research"
        
        if any(kw in message_lower for kw in ["security", "vulnerability", "audit", "compliance"]):
            return "security"
        
        if any(kw in message_lower for kw in ["what if", "simulate", "predict", "impact"]):
            return "simulation"
        """
        
        return None
    
    def __repr__(self) -> str:
        return f"ModeManager(current={self.current_mode})"
