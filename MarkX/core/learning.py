# core/learning.py
"""
Learning & Adaptation System
"""

import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ActionResult:
    tool: str
    args: dict
    success: bool
    timestamp: str
    context: str = ""


class LearningSystem:
    def __init__(self, data_file: str = "memory/learning_data.json"):
        self.data_file = data_file
        self.action_history = []
        self.success_patterns = defaultdict(int)
        self.failure_patterns = defaultdict(int)
        self.user_preferences = defaultdict(int)
        self.command_shortcuts = {}
        self.load_data()
    
    def record_action(self, tool: str, args: dict, success: bool, context: str = ""):
        result = ActionResult(
            tool=tool,
            args=args,
            success=success,
            timestamp=datetime.now().isoformat(),
            context=context
        )
        
        self.action_history.append(result)
        
        # Track patterns
        pattern_key = f"{tool}:{json.dumps(args, sort_keys=True)}"
        if success:
            self.success_patterns[pattern_key] += 1
        else:
            self.failure_patterns[pattern_key] += 1
        
        # Learn preferences
        if success and tool.startswith("os.open"):
            app_name = args.get("app") or args.get("path", "").split("\\")[-1]
            if app_name:
                self.user_preferences[f"preferred_app:{app_name}"] += 1
        
        # Keep history manageable
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-500:]
        
        self.save_data()
    
    def get_success_rate(self, tool: str, args: dict = None) -> float:
        if args:
            pattern_key = f"{tool}:{json.dumps(args, sort_keys=True)}"
            total = self.success_patterns[pattern_key] + self.failure_patterns[pattern_key]
            return self.success_patterns[pattern_key] / total if total > 0 else 0.5
        else:
            # Overall tool success rate
            tool_successes = sum(1 for a in self.action_history if a.tool == tool and a.success)
            tool_total = sum(1 for a in self.action_history if a.tool == tool)
            return tool_successes / tool_total if tool_total > 0 else 0.5
    
    def suggest_alternative(self, failed_tool: str, args: dict) -> Optional[str]:
        # Find similar successful patterns
        for pattern, count in self.success_patterns.items():
            if pattern.startswith(failed_tool) and count > 2:
                try:
                    stored_args = json.loads(pattern.split(":", 1)[1])
                    if self._args_similar(args, stored_args):
                        return f"Try with args: {stored_args}"
                except:
                    continue
        return None
    
    def get_preferred_app(self, category: str) -> Optional[str]:
        # Find most used app in category
        prefs = [(k, v) for k, v in self.user_preferences.items() 
                if k.startswith(f"preferred_app:") and category.lower() in k.lower()]
        if prefs:
            return max(prefs, key=lambda x: x[1])[0].split(":", 1)[1]
        return None
    
    def learn_command_shortcut(self, user_input: str, successful_action: dict):
        # Learn patterns like "open chrome" -> {"tool": "os.open_app", "args": {"app": "chrome"}}
        key_words = user_input.lower().split()[:3]  # First 3 words
        pattern = " ".join(key_words)
        self.command_shortcuts[pattern] = successful_action
        self.save_data()
    
    def get_shortcut_suggestion(self, user_input: str) -> Optional[dict]:
        key_words = user_input.lower().split()[:3]
        pattern = " ".join(key_words)
        return self.command_shortcuts.get(pattern)
    
    def _args_similar(self, args1: dict, args2: dict) -> bool:
        # Simple similarity check
        common_keys = set(args1.keys()) & set(args2.keys())
        if not common_keys:
            return False
        
        similar_count = sum(1 for k in common_keys if str(args1[k]).lower() in str(args2[k]).lower())
        return similar_count / len(common_keys) > 0.5
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        data = {
            "success_patterns": dict(self.success_patterns),
            "failure_patterns": dict(self.failure_patterns),
            "user_preferences": dict(self.user_preferences),
            "command_shortcuts": self.command_shortcuts,
            "recent_actions": [asdict(a) for a in self.action_history[-100:]]  # Save last 100
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                
                self.success_patterns = defaultdict(int, data.get("success_patterns", {}))
                self.failure_patterns = defaultdict(int, data.get("failure_patterns", {}))
                self.user_preferences = defaultdict(int, data.get("user_preferences", {}))
                self.command_shortcuts = data.get("command_shortcuts", {})
                
                # Restore recent actions
                recent = data.get("recent_actions", [])
                self.action_history = [ActionResult(**a) for a in recent]
            except:
                pass  # Start fresh if corrupted


# Global instance
learning_system = LearningSystem()