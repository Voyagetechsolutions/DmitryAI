# dmitry_operator/__init__.py
"""
Dmitry Operator System - Action Execution Layer

Gives Dmitry "hands" to execute commands on the device:
- Open apps, files, folders
- Browser navigation
- File operations
- System commands

And "eyes" to perceive the screen for context-aware decisions.
"""

from .tools import OperatorTools, ActionResult, ToolResult
from .executor import ActionExecutor, ActionPlan, ActionStep, quick_action
from .permissions import PermissionManager, RiskLevel
from .vision import VisionSystem, ScreenCapture
from .intent_classifier import (
    IntentClassifier, 
    IntentType, 
    ClassifiedIntent,
    classify_intent,
    is_action_request,
)
from .orchestrator import (
    DmitryOrchestrator,
    OrchestratorResult,
    process_request,
)

__all__ = [
    "OperatorTools",
    "ActionResult",
    "ToolResult",
    "ActionExecutor",
    "ActionPlan",
    "ActionStep",
    "quick_action",
    "PermissionManager",
    "RiskLevel",
    "VisionSystem",
    "ScreenCapture",
    "IntentClassifier",
    "IntentType",
    "ClassifiedIntent",
    "classify_intent",
    "is_action_request",
    "DmitryOrchestrator",
    "OrchestratorResult",
    "process_request",
]


