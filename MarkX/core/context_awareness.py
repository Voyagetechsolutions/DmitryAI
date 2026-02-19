# core/context_awareness.py
"""
Context Awareness System
"""

import os
import subprocess
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemContext:
    active_window: Optional[str] = None
    current_directory: str = ""
    clipboard_content: str = ""
    recent_files: list = None
    timestamp: str = ""


class ContextManager:
    def __init__(self):
        self.last_context = None
        
    def get_active_window(self) -> Optional[str]:
        try:
            # Windows
            result = subprocess.run([
                'powershell', '-Command',
                'Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object -First 1 | ForEach-Object {$_.MainWindowTitle}'
            ], capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.stdout.strip() else None
        except:
            return None
    
    def get_clipboard_content(self) -> str:
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-Clipboard'], 
                                  capture_output=True, text=True, timeout=3)
            content = result.stdout.strip()
            return content[:500] if content else ""  # Limit size
        except:
            return ""
    
    def get_recent_files(self, directory: str = None, limit: int = 5) -> list:
        try:
            target_dir = directory or os.getcwd()
            files = []
            for item in os.listdir(target_dir):
                path = os.path.join(target_dir, item)
                if os.path.isfile(path):
                    files.append({
                        "name": item,
                        "path": path,
                        "modified": os.path.getmtime(path)
                    })
            return sorted(files, key=lambda x: x["modified"], reverse=True)[:limit]
        except:
            return []
    
    def get_current_context(self) -> SystemContext:
        context = SystemContext(
            active_window=self.get_active_window(),
            current_directory=os.getcwd(),
            clipboard_content=self.get_clipboard_content(),
            recent_files=self.get_recent_files(),
            timestamp=datetime.now().isoformat()
        )
        self.last_context = context
        return context
    
    def format_context_for_llm(self, context: SystemContext = None) -> str:
        if context is None:
            context = self.get_current_context()
        
        parts = []
        
        if context.active_window:
            parts.append(f"Active window: {context.active_window}")
        
        parts.append(f"Working directory: {context.current_directory}")
        
        if context.clipboard_content:
            parts.append(f"Clipboard: {context.clipboard_content[:100]}...")
        
        if context.recent_files:
            files = [f["name"] for f in context.recent_files[:3]]
            parts.append(f"Recent files: {', '.join(files)}")
        
        return "\n".join(parts)


# Global instance
context_manager = ContextManager()