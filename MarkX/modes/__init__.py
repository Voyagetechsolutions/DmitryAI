# modes/__init__.py
"""
Dmitry v1.2 Cognitive Mode System

Modes control reasoning behavior and output structure, not permissions.
Each mode tailors how Dmitry thinks and responds to specific task types.

Architecture:
- Layer 1: Core Identity (permanent security-first persona)
- Layer 2: Core Modes (task category)
- Layer 3: Specialist Sub-Modes (intensity/perspective)
"""

from .base_mode import BaseMode, ModeContext, SubMode, CORE_IDENTITY
from .mode_manager import ModeManager
from .utility_mode import UtilityMode
from .general_mode import GeneralMode
from .design_mode import DesignMode
from .developer_mode import DeveloperMode
from .research_mode import ResearchMode
from .security_mode import SecurityMode  # Import from .py file, not package
from .simulation_mode import SimulationMode

__all__ = [
    "BaseMode",
    "ModeContext",
    "SubMode",
    "CORE_IDENTITY",
    "ModeManager",
    "UtilityMode",
    "GeneralMode",
    "DesignMode",
    "DeveloperMode",
    "ResearchMode",
    "SecurityMode",
    "SimulationMode",
]

