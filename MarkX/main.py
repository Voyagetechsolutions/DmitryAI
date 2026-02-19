# main.py - Dmitry v1.2 (Operator Enabled)
"""
Dmitry - AI System & Security Assistant

A multi-modal AI assistant with:
- Cognitive modes for different task types
- Operator System (Hands & Eyes)
- Unrestricted Action Execution
- Knowledge retrieval (RAG)
"""

import asyncio
import os
import threading
from typing import Optional

# Core components
from speech_to_text import record_voice, stop_listening_flag
from llm import DmitryLLM
from tts import edge_speak, stop_speaking
from ui import DmitryUI
from dmitry_operator import DmitryOrchestrator, OrchestratorResult

# Modes
from modes import ModeManager

# Knowledge
from knowledge import VectorStore, KnowledgeRetriever, DocumentIngester

# Memory
from memory.memory_manager import load_memory, update_memory
from memory.temporary_memory import TemporaryMemory

# Interrupt commands
INTERRUPT_COMMANDS = ["mute", "quit", "exit", "stop"]

# Mode switch commands
MODE_SWITCH_KEYWORDS = {
    "architect mode": "architect",
    "developer mode": "developer",
    "dev mode": "developer",
    "research mode": "research",
    "security mode": "security",
    "simulation mode": "simulation",
    "general mode": "general",
    "normal mode": "general",
    "utility mode": "utility",
}


class Dmitry:
    """Main Dmitry assistant class."""
    
    def __init__(self, ui: DmitryUI):
        self.ui = ui
        self.mode_manager = ModeManager()
        
        self.vector_store = VectorStore("knowledge_base")
        self.retriever = KnowledgeRetriever(self.vector_store)
        self.ingester = DocumentIngester(self.vector_store)
        
        self.llm = DmitryLLM(
            mode_manager=self.mode_manager,
            knowledge_retriever=self.retriever,
        )
        
        self.orchestrator = DmitryOrchestrator(
            llm=self.llm,
            on_action_start=self._on_action_start,
            on_action_complete=self._on_action_complete,
            on_confirmation_needed=self._on_confirmation_needed,
        )
        
        self.logger = self.ui.write_log
        self.temp_memory = TemporaryMemory()
        self._update_mode_ui()
    
    def _on_action_start(self, message: str):
        self.ui.show_tool_execution(message, "running")
    
    def _on_action_complete(self, message: str, success: bool):
        self.ui.show_tool_execution(message, "success" if success else "failed")
    
    def _on_confirmation_needed(self, message: str) -> bool:
        return True  # Auto-confirm in God Mode
    
    def _update_mode_ui(self) -> None:
        mode = self.mode_manager.current_mode
        self.ui.set_mode(mode.name, mode.icon)
    
    def _check_mode_switch(self, user_text: str) -> bool:
        text_lower = user_text.lower()
        for keyword, mode_name in MODE_SWITCH_KEYWORDS.items():
            if keyword in text_lower:
                success, message = self.mode_manager.switch_mode(mode_name)
                if success:
                    self._update_mode_ui()
                    self.ui.write_log(f"AI: {message}", "ai")
                    edge_speak(message, self.ui)
                    return True
        return False
    
    def process_input(self, user_text: str) -> None:
        if not user_text:
            return
        
        if any(cmd in user_text.lower() for cmd in INTERRUPT_COMMANDS):
            stop_speaking()
            self.temp_memory.reset()
            return
        
        self.ui.write_log(f"You: {user_text}", "user")
        
        if self._check_mode_switch(user_text):
            return
        
        self.temp_memory.set_last_user_text(user_text)
        
        long_term_memory = load_memory()
        memory_context = {} 
        identity = long_term_memory.get("identity", {})
        if "name" in identity:
            memory_context["user_name"] = identity["name"].get("value")
            
        history = [
            {"role": m["role"], "text": m["text"]}
            for m in self.temp_memory.conversation_history[-5:]
        ]
        
        try:
            result = self.orchestrator.process(
                user_text,
                memory_context=memory_context,
                conversation_history=history
            )
            
            response_text = result.content
            
            if result.raw_response and result.raw_response.get("memory_update"):
                update_memory(result.raw_response["memory_update"])
            
            self.temp_memory.set_last_ai_response(response_text)
            
            if response_text:
                prefix = "ACTION: " if result.type == "action" else "AI: "
                self.ui.write_log(f"{prefix}{response_text}", "ai")
                edge_speak(response_text, self.ui)
                
        except Exception as e:
            self.ui.write_log(f"AI ERROR: {e}", "error")
            print(f"Error processing input: {e}")


async def get_voice_input():
    return await asyncio.to_thread(record_voice)


async def ai_loop(dmitry: Dmitry):
    print("Voice loop started")
    while True:
        stop_listening_flag.clear()
        user_text = await get_voice_input()
        
        if user_text:
            dmitry.process_input(user_text)
        
        await asyncio.sleep(0.01)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    face_path = os.path.join(base_dir, "face.png")
    
    ui = DmitryUI(face_path, size=(900, 900))
    dmitry = Dmitry(ui)
    
    def runner():
        asyncio.run(ai_loop(dmitry))
    
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    
    ui.root.mainloop()


if __name__ == "__main__":
    main()
