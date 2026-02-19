# modes/base_mode.py
"""
Base class for all Dmitry cognitive modes.

Modes define:
- System prompt adjustments
- Output format expectations
- Allowed tools for the mode
- Behavioral guidelines
- Sub-mode specializations
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field


# =============================================================================
# CORE IDENTITY - The permanent behavioral baseline for Dmitry
# This is injected into EVERY mode's system prompt.
# =============================================================================
CORE_IDENTITY = """
# DMITRY - AI Cybersecurity & Technical Strategy Copilot

## Core Identity
You are Dmitry, an AI Cybersecurity Intelligence System operating as a security-first technical cofounder for software products and digital businesses.

## Permanent Traits (Apply in ALL modes)
- **Decision Priority Order**: Security → Scalability → Maintainability → Speed
- **Core Bias**: Prevention over reaction
- **Communication Style**: Direct, analytical, structured
- You ALWAYS evaluate risk before recommending any approach.
- You question unsafe shortcuts—never approve them silently.
- You prefer proven patterns over hype.
- You focus on long-term consequences over quick wins.
- You avoid emotional tone or motivational fluff.

## Response Framework
All responses follow this logic chain:
**Engineering Context → Risk → Recommendation → Long-Term Impact**

You avoid:
- Vague advice
- Pure theory without action
- Blind agreement with the user
"""


@dataclass
class ModeContext:
    """Context passed to mode for prompt building."""
    user_message: str
    memory_context: dict = field(default_factory=dict)
    rag_context: str = ""
    conversation_history: list = field(default_factory=list)
    available_tools: list = field(default_factory=list)
    active_sub_mode: Optional[str] = None


@dataclass
class SubMode:
    """Defines a specialist sub-mode within a core mode."""
    name: str
    description: str
    trigger_phrases: list[str]
    prompt_injection: str
    output_structure: str


class BaseMode(ABC):
    """Abstract base class for cognitive modes."""
    
    def __init__(self):
        self._name: str = "base"
        self._description: str = "Base mode"
        self._icon: str = "🧠"
        self._allowed_tools: list[str] = []
        self._output_format: dict = {}
        self._sub_modes: dict[str, SubMode] = {}
        self._active_sub_mode: Optional[str] = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def icon(self) -> str:
        return self._icon
    
    @property
    def allowed_tools(self) -> list[str]:
        return self._allowed_tools
    
    @property
    def output_format(self) -> dict:
        return self._output_format
    
    @property
    def sub_modes(self) -> dict[str, SubMode]:
        return self._sub_modes
    
    @property
    def active_sub_mode(self) -> Optional[str]:
        return self._active_sub_mode
    
    def set_sub_mode(self, sub_mode_name: Optional[str]) -> bool:
        """Activate a sub-mode. Returns True if successful."""
        if sub_mode_name is None:
            self._active_sub_mode = None
            return True
        if sub_mode_name in self._sub_modes:
            self._active_sub_mode = sub_mode_name
            return True
        return False
    
    def detect_sub_mode(self, message: str) -> Optional[str]:
        """Detect if a message should trigger a sub-mode."""
        message_lower = message.lower()
        for name, sub_mode in self._sub_modes.items():
            for phrase in sub_mode.trigger_phrases:
                if phrase in message_lower:
                    return name
        return None
    
    def get_core_identity(self) -> str:
        """Return the immutable core identity prompt."""
        return CORE_IDENTITY
    
    @abstractmethod
    def get_mode_prompt(self) -> str:
        """Return the mode-specific prompt (Layer 1)."""
        pass
    
    def get_sub_mode_prompt(self) -> str:
        """Return the sub-mode prompt if one is active (Layer 2)."""
        if self._active_sub_mode and self._active_sub_mode in self._sub_modes:
            sub_mode = self._sub_modes[self._active_sub_mode]
            return f"\n\n## Active Sub-Mode: {sub_mode.name}\n{sub_mode.prompt_injection}\n\n### Output Structure\n{sub_mode.output_structure}"
        return ""
    
    def get_system_prompt(self) -> str:
        """
        Build the complete system prompt using the 3-layer architecture:
        1. Core Identity (Base - permanent)
        2. Mode Identity (Layer 1 - task category)
        3. Sub-Mode Identity (Layer 2 - intensity/perspective)
        """
        layers = [
            self.get_core_identity(),
            self.get_mode_prompt(),
            self.get_sub_mode_prompt(),
        ]
        return "\n".join(filter(None, layers))
    
    @abstractmethod
    def build_prompt(self, context: ModeContext) -> str:
        """Build the complete prompt including context."""
        pass
    
    def validate_output(self, output: dict) -> bool:
        """Validate LLM output matches expected format."""
        required_fields = ["intent", "text"]
        return all(field in output for field in required_fields)
    
    def get_mode_instructions(self) -> str:
        """Return mode-specific behavioral instructions."""
        return ""
    
    def format_tool_availability(self, tools: list[str]) -> str:
        """Format available tools for prompt inclusion."""
        if not tools:
            return "No tools available in this mode."
        
        tool_list = "\n".join(f"  - {tool}" for tool in tools)
        return f"Available tools:\n{tool_list}"
    
    def __repr__(self) -> str:
        sub_mode_str = f" [{self._active_sub_mode}]" if self._active_sub_mode else ""
        return f"{self.icon} {self.name.title()} Mode{sub_mode_str}"
