# dmitry_operator/intent_classifier.py
"""
Intent Classification - Transform vs Act

Classifies user requests into two tracks:
- TRANSFORM: Writing/content changes (rewrite, summarize, format, translate)
- ACT: Device actions (open, click, create, move, search, run)

This prevents Dmitry from giving "press Win+E" advice when the user wants action.
"""

import re
from enum import Enum
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


class IntentType(Enum):
    """The two main intent types."""
    TRANSFORM = "transform"  # Text/content tasks
    ACT = "act"              # Device/system actions
    CHAT = "chat"            # General conversation


@dataclass
class ClassifiedIntent:
    """Result of intent classification."""
    type: IntentType
    confidence: float  # 0.0 to 1.0
    action_hints: list[str]  # Detected action keywords
    target: Optional[str]  # Detected target (app, file, url, etc.)


class IntentClassifier:
    """
    Fast intent classifier that can determine if a request
    needs text transformation or device action.
    
    This runs BEFORE the LLM call to route appropriately.
    """
    
    # Keywords that strongly indicate ACTION intent
    ACTION_KEYWORDS = {
        # App control
        "open", "launch", "start", "run", "close", "quit", "exit",
        "focus", "switch to", "go to", "bring up",
        
        # File operations (Explicit)
        "create folder", "make folder", "new folder",
        "create file", "make file", "new file",
        "delete", "remove", "move", "copy", "rename",
        "read", "read file", "read this file", "show contents",
        "write", "write to", "save to", "append to",
        "list", "list files", "show files", "what files", "what's in",
        
        # Generic Creation/Action (Aggressive)
        "create", "make", "generate", "build", "construct",
        "code", "script", "program", "develop",
        
        # Navigation
        "navigate to", "show me", "take me to",
        "search for", "find", "look for", "locate",
        
        # Browser
        "google", "search the web", "browse to", "open website",
        
        # System
        "click", "press", "type", "scroll",
        "shutdown", "restart", "lock",
    }
    
    # Keywords that strongly indicate TRANSFORM intent
    TRANSFORM_KEYWORDS = {
        # Writing tasks
        "rewrite", "rephrase", "reword", "paraphrase",
        "summarize", "summary", "shorten", "condense",
        "expand", "elaborate", "explain",
        "translate", "convert",
        "format", "clean up", "fix grammar", "proofread",
        "make it", "sound more", "tone",
        
        # Content generation
        "draft", "compose", "create a message",
        "caption", "headline", "title",
        "reply", "respond to", "answer this",
        
        # Analysis (still text output)
        "what does this mean", "explain this", "analyze",
    }
    
    # Common apps for action detection
    COMMON_APPS = {
        "explorer", "file explorer", "files",
        "chrome", "firefox", "edge", "browser",
        "notepad", "calculator", "terminal", "cmd", "powershell",
        "vscode", "code", "spotify", "discord", "slack",
        "word", "excel", "powerpoint", "outlook",
        "settings", "control panel",
    }
    
    # Common paths
    COMMON_PATHS = {
        "documents", "downloads", "desktop", "pictures", "music", "videos",
        "home", "my computer", "this pc",
    }
    
    def classify(self, user_input: str) -> ClassifiedIntent:
        """
        Classify user input as TRANSFORM, ACT, or CHAT.
        
        Args:
            user_input: The user's message
            
        Returns:
            ClassifiedIntent with type, confidence, and hints
        """
        text = user_input.lower().strip()
        
        action_score = 0.0
        transform_score = 0.0
        action_hints = []
        target = None
        
        # Check for action keywords
        for keyword in self.ACTION_KEYWORDS:
            if keyword in text:
                action_score += 0.3
                action_hints.append(keyword)
        
        # Check for transform keywords
        for keyword in self.TRANSFORM_KEYWORDS:
            if keyword in text:
                transform_score += 0.3
        
        # Check for app names (strong action signal)
        for app in self.COMMON_APPS:
            if app in text:
                action_score += 0.4
                target = app
                break
        
        # Check for paths (strong action signal)
        for path in self.COMMON_PATHS:
            if path in text:
                action_score += 0.3
                if not target:
                    target = path
                break
        
        # Check for URLs (action)
        if re.search(r'https?://|www\.|\.\w{2,3}(?:\s|$)', text):
            action_score += 0.4
            url_match = re.search(r'(https?://\S+|www\.\S+|\S+\.\w{2,3})', text)
            if url_match:
                target = url_match.group(1)
        
        # Quoted text often means transform
        if '"' in text or "'" in text:
            transform_score += 0.2
        
        # "This" usually refers to text to transform
        if text.startswith("this ") or " this " in text:
            transform_score += 0.15
        
        # Cap scores
        action_score = min(action_score, 1.0)
        transform_score = min(transform_score, 1.0)
        
        # Determine final intent
        if action_score > transform_score and action_score > 0.3:
            return ClassifiedIntent(
                type=IntentType.ACT,
                confidence=action_score,
                action_hints=action_hints,
                target=target,
            )
        elif transform_score > action_score and transform_score > 0.3:
            return ClassifiedIntent(
                type=IntentType.TRANSFORM,
                confidence=transform_score,
                action_hints=[],
                target=None,
            )
        else:
            # Default to chat
            return ClassifiedIntent(
                type=IntentType.CHAT,
                confidence=0.5,
                action_hints=[],
                target=None,
            )
    
    def is_action_request(self, user_input: str) -> bool:
        """Quick check if this is likely an action request."""
        result = self.classify(user_input)
        return result.type == IntentType.ACT
    
    def get_action_schema_prompt(self) -> str:
        """Get the prompt injection for action schema output."""
        return """
## ACTION MODE ACTIVATED

The user wants you to DO something, not just explain.
You MUST respond with a structured action plan:

```json
{
  "type": "action_plan",
  "goal": "<what you're trying to accomplish>",
  "steps": [
    { "tool": "<tool_name>", "args": { "<arg>": "<value>" } }
  ],
  "requires_confirmation": false
}
```

Available tools:

OS & Apps:
- os.open_app(app) - Open an application
- os.open_path(path) - Open a file or folder (requires exact path)
- os.find_open(name, type?) - Find and open file/folder by name (smart search)
- os.create_folder(path) - Create a new folder
- os.search_files(query, path?, limit?) - Search for files

Browser:
- browser.open_url(url) - Open a URL
- browser.search(query, engine?) - Search the web

Files:
- file.read(path) - Read contents of a file
- file.write(path, content, mode?) - Write to a file (mode: "write" or "append")
- file.list(path?) - List files in a directory
- file.copy(source, destination) - Copy a file or folder
- file.move(source, destination) - Move a file or folder
- file.delete(path) - Delete a file or folder

Input Control (Mouse & Keyboard):
- input.click(x?, y?, button?, clicks?) - Click mouse at position
- input.move(x, y, duration?) - Move mouse to position
- input.type(text, interval?) - Type text
- input.hotkey(*keys) - Press hotkey (e.g., "ctrl", "s" for Ctrl+S)
- input.press(key) - Press single key (e.g., "enter", "escape")
- input.scroll(amount, x?, y?) - Scroll mouse wheel
- input.drag(x1, y1, x2, y2, duration?) - Drag from one position to another

DO NOT give instructions like "press Win+E".
DO NOT explain how to do it manually.
JUST output the action plan JSON.
"""


# Quick access
classifier = IntentClassifier()


def classify_intent(user_input: str) -> ClassifiedIntent:
    """Classify user input intent."""
    return classifier.classify(user_input)


def is_action_request(user_input: str) -> bool:
    """Quick check if this is an action request."""
    return classifier.is_action_request(user_input)
