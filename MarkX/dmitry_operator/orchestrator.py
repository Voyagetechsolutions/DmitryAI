# dmitry_operator/orchestrator.py
"""
Dmitry Orchestrator - The Brain Router

Connects all components:
1. Receives user input (text or voice-transcribed)
2. Classifies intent (Transform vs Act)
3. Routes to appropriate handler:
   - TRANSFORM → LLM for text response
   - ACT → LLM for action plan → Executor
4. Returns result to user

This is the main entry point for handling user requests.
"""

import json
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from .intent_classifier import IntentClassifier, IntentType, ClassifiedIntent
from .executor import ActionExecutor, ActionPlan
from .tools import ActionResult, ToolResult
from core.learning import learning_system


@dataclass
class OrchestratorResult:
    """Result from the orchestrator."""
    type: str  # "text", "action", "error"
    content: str  # Text response or action summary
    action_results: Optional[list] = None  # For action responses
    raw_response: Optional[dict] = None  # Full LLM response


class DmitryOrchestrator:
    """
    Main orchestrator for Dmitry's request handling.
    """
    
    def __init__(
        self, 
        llm=None,
        on_action_start: Optional[Callable[[str], None]] = None,
        on_action_complete: Optional[Callable[[str, bool], None]] = None,
        on_confirmation_needed: Optional[Callable[[str], bool]] = None,
    ):
        self.llm = llm
        self.classifier = IntentClassifier()
        self.executor = ActionExecutor()
        
        self.on_action_start = on_action_start
        self.on_action_complete = on_action_complete
        self.on_confirmation_needed = on_confirmation_needed
    
    def process(
        self, 
        user_input: str,
        memory_context: dict = None,
        conversation_history: list = None,
    ) -> OrchestratorResult:
        """Process a user request with learning and enhanced capabilities."""
        
        # Check for learned shortcuts first
        shortcut = learning_system.get_shortcut_suggestion(user_input)
        if shortcut:
            print(f"🎯 Using learned shortcut for: {user_input}")
            return self._execute_shortcut(shortcut)
        
        # Step 1: Detect Vision Intent
        vision_keywords = [
            "what can you see", "look at this", "read this", 
            "describe the screen", "what is on my screen", 
            "what's on my screen", "whats on my screen",
            "check my screen", "analyze this", "see my screen",
            "what do you see", "on my screen", "screen",
            "click on", "find on screen", "text on screen"
        ]
        
        is_vision_request = any(kw in user_input.lower() for kw in vision_keywords)
        
        if is_vision_request:
            return self._handle_vision(user_input, memory_context, conversation_history)
        
        intent = self.classifier.classify(user_input)
        
        if intent.type == IntentType.ACT:
            result = self._handle_action(user_input, intent, memory_context, conversation_history)
            
            # Learn successful patterns
            if result.type == "action" and result.action_results:
                successful_actions = [r for r in result.action_results if r.get("status") == "success"]
                if successful_actions:
                    learning_system.learn_command_shortcut(user_input, {
                        "type": "action",
                        "actions": successful_actions
                    })
            
            return result
        else:
            return self._handle_text(user_input, memory_context, conversation_history)
            
    def _handle_vision(self, user_input: str, memory_context: dict, conversation_history: list) -> OrchestratorResult:
        """Handle vision/screen perception requests with enhanced capabilities."""
        if not self.llm:
            return OrchestratorResult(type="error", content="LLM not configured")
        
        # Import here to avoid circular import
        from core.enhanced_vision import enhanced_vision
        
        # Check if this is a click request
        click_keywords = ["click on", "click the", "press", "tap"]
        is_click_request = any(kw in user_input.lower() for kw in click_keywords)
        
        if is_click_request:
            # Extract what to click
            text = user_input.lower()
            for kw in click_keywords:
                if kw in text:
                    target = text.split(kw, 1)[-1].strip()
                    if target:
                        result = enhanced_vision.smart_click(target)
                        if result["success"]:
                            return OrchestratorResult(
                                type="action",
                                content=f"✅ Clicked on '{target}'",
                                action_results=[{"status": "success", "message": result["message"]}]
                            )
                        else:
                            return OrchestratorResult(
                                type="text",
                                content=f"❌ Could not click on '{target}': {result['error']}"
                            )
        
        # Regular vision processing
        if self.on_action_start:
            self.on_action_start("Capturing screen...")
            
        capture_data = enhanced_vision.capture_for_llm()
        
        if not capture_data:
            # Fallback to text summary
            text_summary = enhanced_vision.get_screen_text_summary()
            if text_summary != "Could not capture screen":
                return OrchestratorResult(
                    type="text", 
                    content=f"I can see text on screen: {text_summary}"
                )
            return OrchestratorResult(type="text", content="I tried to look at the screen, but the capture failed.")
            
        if self.on_action_complete:
            self.on_action_complete("Screen captured", True)
            
        response = self.llm.get_response(
            user_input,
            memory_context=memory_context,
            conversation_history=conversation_history,
            image_data=capture_data["data"]
        )
        
        return OrchestratorResult(
            type="text",
            content=response.get("text") or "I see the screen but couldn't describe it.",
            raw_response=response,
        )
    
    def _handle_text(self, user_input: str, memory_context: dict, conversation_history: list) -> OrchestratorResult:
        """Handle text/transform requests."""
        if not self.llm:
            return OrchestratorResult(type="error", content="LLM not configured")
        
        response = self.llm.get_response(
            user_input,
            memory_context=memory_context,
            conversation_history=conversation_history,
        )
        
        return OrchestratorResult(
            type="text",
            content=response.get("text") or "I couldn't process that.",
            raw_response=response,
        )
    
    def _handle_action(self, user_input: str, intent: ClassifiedIntent, memory_context: dict, conversation_history: list) -> OrchestratorResult:
        """Handle action requests."""
        if self.llm:
            action_prompt = self.classifier.get_action_schema_prompt()
            enhanced_input = f"{action_prompt}\n\nUser request: {user_input}"
            
            response = self.llm.get_response(
                enhanced_input,
                memory_context=memory_context,
                conversation_history=conversation_history,
            )
            
            action_plan = self._extract_action_plan(response)
            
            if action_plan:
                return self._execute_action_plan(action_plan)
        
        return self._execute_inferred_action(user_input, intent)
    
    def _extract_action_plan(self, response: dict) -> Optional[ActionPlan]:
        """Extract action plan from LLM response."""
        if response.get("type") == "action_plan":
            return self.executor.parse_action_plan(response)
        
        text = response.get("text") or ""
        if "action_plan" in text.lower():
            try:
                import re
                json_match = re.search(r'\{[^{}]*"type"\s*:\s*"action_plan"[^{}]*\}', text, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                    return self.executor.parse_action_plan(plan_data)
            except:
                pass
        
        return None
    
    def _execute_action_plan(self, plan: ActionPlan) -> OrchestratorResult:
        """Execute an action plan."""
        if self.on_action_start:
            self.on_action_start(plan.goal)
        
        def confirm_handler(step):
            if self.on_confirmation_needed:
                return self.on_confirmation_needed(f"Execute {step.tool}?")
            return True
        
        results = self.executor.execute(plan, on_confirmation_needed=confirm_handler)
        success = results.get("status") == "completed"
        
        if self.on_action_complete:
            self.on_action_complete(plan.goal, success)
        
        summary = f"✅ {plan.goal}" if success else f"⚠️ {plan.goal} (partial)"
        
        return OrchestratorResult(type="action", content=summary, action_results=results.get("results", []))
    
    def _execute_inferred_action(self, user_input: str, intent: ClassifiedIntent) -> OrchestratorResult:
        """Execute action inferred directly from intent."""
        text = user_input.lower()
        
        # Common folder keywords - try path first
        folder_keywords = ["documents", "desktop", "downloads", "pictures", "music", "videos", "folder"]
        is_folder_request = any(kw in text for kw in folder_keywords)
        
        if any(kw in text for kw in ["open", "launch", "start", "go to", "navigate"]):
            if intent.target:
                if self.on_action_start:
                    self.on_action_start(f"Opening {intent.target}...")
                
                # Try path first if it looks like a folder request
                if is_folder_request or any(kw in intent.target.lower() for kw in folder_keywords):
                    result = self.executor.execute_single("os.open_path", {"path": intent.target})
                    if result.status == ToolResult.SUCCESS:
                        return OrchestratorResult(type="action", content=f"✅ Opened {intent.target}", action_results=[{"status": "success", "message": result.message}])
                
                # Try as app
                result = self.executor.execute_single("os.open_app", {"app": intent.target})
                if result.status == ToolResult.SUCCESS:
                    return OrchestratorResult(type="action", content=f"✅ Opened {intent.target}", action_results=[{"status": "success", "message": result.message}])
                
                # Fallback to path with ~/ prefix
                result = self.executor.execute_single("os.open_path", {"path": intent.target})
                if result.status == ToolResult.SUCCESS:
                    return OrchestratorResult(type="action", content=f"✅ Opened {intent.target}", action_results=[{"status": "success", "message": result.message}])
        
        if any(kw in text for kw in ["search", "google", "look up"]):
            query = user_input
            for prefix in ["search for", "google", "search", "look up"]:
                if prefix in text:
                    query = text.split(prefix, 1)[-1].strip()
                    break
            
            if query:
                result = self.executor.execute_single("browser.search", {"query": query})
                return OrchestratorResult(type="action", content=f"✅ Searching: {query}", action_results=[{"status": "success", "message": result.message}])
        
        return OrchestratorResult(type="text", content=f"I understood you want to do something with '{intent.target or 'unknown'}', but I need more specific instructions.")
    
    def _execute_shortcut(self, shortcut: dict) -> OrchestratorResult:
        """Execute a learned shortcut action."""
        try:
            if shortcut.get("type") == "action" and shortcut.get("actions"):
                return OrchestratorResult(
                    type="action",
                    content="✅ Executed learned shortcut",
                    action_results=shortcut["actions"]
                )
            else:
                return OrchestratorResult(
                    type="text",
                    content="Shortcut format not recognized"
                )
        except Exception as e:
            return OrchestratorResult(
                type="error",
                content=f"Shortcut execution failed: {e}"
            )


def process_request(user_input: str, llm=None, memory_context: dict = None, conversation_history: list = None) -> OrchestratorResult:
    """Process a user request with automatic routing."""
    orch = DmitryOrchestrator(llm=llm)
    return orch.process(user_input, memory_context, conversation_history)
