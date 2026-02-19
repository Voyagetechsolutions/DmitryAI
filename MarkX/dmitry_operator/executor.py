# operator/executor.py
"""
Dmitry Action Executor - Runs Action Plans

Executes structured action plans step-by-step with:
- Progress tracking
- Error handling and recovery
- Confirmation gating for dangerous actions
- Cancellation support
"""

import json
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from .tools import OperatorTools, ActionResult, ToolResult
from .permissions import PermissionManager, RiskLevel
from core.learning import learning_system


class ExecutionStatus(Enum):
    """Status of an action plan execution."""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActionStep:
    """A single step in an action plan."""
    tool: str
    args: Dict[str, Any]
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[ActionResult] = None


@dataclass
class ActionPlan:
    """
    A structured action plan from Dmitry.
    
    Example:
    {
        "type": "action_plan",
        "goal": "Open Documents folder",
        "steps": [
            {"tool": "os.open_path", "args": {"path": "~/Documents"}}
        ],
        "requires_confirmation": false
    }
    """
    goal: str
    steps: List[ActionStep]
    requires_confirmation: bool = False
    status: ExecutionStatus = ExecutionStatus.PENDING
    current_step: int = 0


class ActionExecutor:
    """
    Executes action plans from Dmitry.
    
    Usage:
        executor = ActionExecutor()
        
        # Parse action plan from LLM
        plan = executor.parse_action_plan(llm_output)
        
        # Execute (with optional callbacks)
        results = executor.execute(
            plan,
            on_step_complete=lambda step, result: print(f"✅ {step}"),
            on_confirmation_needed=lambda step: input("Confirm? "),
        )
    """
    
    def __init__(self):
        self.tools = OperatorTools()
        self.permissions = PermissionManager(auto_confirm_low_risk=True)
        self._cancel_flag = threading.Event()
    
    def parse_action_plan(self, data: Dict[str, Any]) -> Optional[ActionPlan]:
        """
        Parse an action plan from LLM output.
        
        Args:
            data: Dictionary with action plan structure
            
        Returns:
            ActionPlan object or None if invalid
        """
        if data.get("type") != "action_plan":
            return None
        
        try:
            steps = [
                ActionStep(tool=s["tool"], args=s.get("args", {}))
                for s in data.get("steps", [])
            ]
            
            return ActionPlan(
                goal=data.get("goal", "Unknown action"),
                steps=steps,
                requires_confirmation=data.get("requires_confirmation", False),
            )
        except (KeyError, TypeError) as e:
            print(f"Invalid action plan: {e}")
            return None
    
    def cancel(self):
        """Cancel the current execution."""
        self._cancel_flag.set()
    
    def execute(
        self,
        plan: ActionPlan,
        on_step_start: Optional[Callable[[int, ActionStep], None]] = None,
        on_step_complete: Optional[Callable[[int, ActionStep, ActionResult], None]] = None,
        on_confirmation_needed: Optional[Callable[[ActionStep], bool]] = None,
        on_error: Optional[Callable[[int, ActionStep, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an action plan.
        
        Args:
            plan: The action plan to execute
            on_step_start: Callback when a step starts
            on_step_complete: Callback when a step completes
            on_confirmation_needed: Callback to ask for confirmation (return True to proceed)
            on_error: Callback when a step fails
            
        Returns:
            Execution result dictionary
        """
        self._cancel_flag.clear()
        plan.status = ExecutionStatus.RUNNING
        
        results = []
        
        for i, step in enumerate(plan.steps):
            plan.current_step = i
            
            # Check cancellation
            if self._cancel_flag.is_set():
                plan.status = ExecutionStatus.CANCELLED
                return {
                    "status": "cancelled",
                    "completed_steps": i,
                    "total_steps": len(plan.steps),
                    "results": results,
                }
            
            # Check if confirmation needed
            if self.permissions.requires_confirmation(step.tool):
                step.status = ExecutionStatus.AWAITING_CONFIRMATION
                plan.status = ExecutionStatus.AWAITING_CONFIRMATION
                
                if on_confirmation_needed:
                    confirmed = on_confirmation_needed(step)
                    if not confirmed:
                        plan.status = ExecutionStatus.CANCELLED
                        step.status = ExecutionStatus.CANCELLED
                        return {
                            "status": "cancelled",
                            "reason": "User declined confirmation",
                            "step": i,
                            "results": results,
                        }
                else:
                    # No confirmation handler, skip dangerous action
                    step.status = ExecutionStatus.CANCELLED
                    continue
            
            # Start step
            step.status = ExecutionStatus.RUNNING
            if on_step_start:
                on_step_start(i, step)
            
            # Get and execute tool
            tool_func = self.tools.get_tool(step.tool)
            if not tool_func:
                error_msg = f"Unknown tool: {step.tool}"
                step.status = ExecutionStatus.FAILED
                if on_error:
                    on_error(i, step, error_msg)
                results.append({"step": i, "status": "failed", "error": error_msg})
                continue
            
            # Execute
            try:
                result = tool_func(**step.args)
                step.result = result
                
                # Record learning data
                learning_system.record_action(
                    tool=step.tool,
                    args=step.args,
                    success=(result.status == ToolResult.SUCCESS),
                    context=plan.goal
                )
                
                if result.status == ToolResult.SUCCESS:
                    step.status = ExecutionStatus.COMPLETED
                    results.append({
                        "step": i,
                        "tool": step.tool,
                        "status": "success",
                        "message": result.message,
                        "data": result.data,
                    })
                    if on_step_complete:
                        on_step_complete(i, step, result)
                else:
                    step.status = ExecutionStatus.FAILED
                    
                    # Try to suggest alternative
                    suggestion = learning_system.suggest_alternative(step.tool, step.args)
                    error_msg = result.message
                    if suggestion:
                        error_msg += f" | Suggestion: {suggestion}"
                    
                    results.append({
                        "step": i,
                        "tool": step.tool,
                        "status": "failed",
                        "message": error_msg,
                    })
                    if on_error:
                        on_error(i, step, error_msg)
                        
            except Exception as e:
                step.status = ExecutionStatus.FAILED
                error_msg = str(e)
                
                # Record failure
                learning_system.record_action(
                    tool=step.tool,
                    args=step.args,
                    success=False,
                    context=plan.goal
                )
                
                results.append({"step": i, "status": "failed", "error": error_msg})
                if on_error:
                    on_error(i, step, error_msg)
        
        # Check if all steps completed
        all_success = all(r.get("status") == "success" for r in results)
        plan.status = ExecutionStatus.COMPLETED if all_success else ExecutionStatus.FAILED
        
        return {
            "status": "completed" if all_success else "partial_failure",
            "goal": plan.goal,
            "completed_steps": sum(1 for r in results if r.get("status") == "success"),
            "total_steps": len(plan.steps),
            "results": results,
        }
    
    def execute_single(self, tool: str, args: Dict[str, Any]) -> ActionResult:
        """
        Execute a single tool directly.
        
        Args:
            tool: Tool name (e.g., "os.open_app")
            args: Tool arguments
            
        Returns:
            ActionResult
        """
        tool_func = self.tools.get_tool(tool)
        if not tool_func:
            return ActionResult(
                status=ToolResult.FAILED,
                message=f"Unknown tool: {tool}"
            )
        
        return tool_func(**args)


# Quick access function for simple actions
def quick_action(tool: str, **kwargs) -> ActionResult:
    """
    Execute a single action quickly.
    
    Usage:
        quick_action("os.open_app", app="explorer")
        quick_action("browser.open_url", url="google.com")
    """
    executor = ActionExecutor()
    return executor.execute_single(tool, kwargs)
