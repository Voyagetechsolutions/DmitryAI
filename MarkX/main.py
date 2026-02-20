# main.py - Dmitry v1.2 (Production Ready)
"""
Dmitry - AI Security Agent

Production-ready AI agent with:
- Trust enforcement (call ledger, action safety, input/output validation)
- Platform integration (circuit breaker, retry logic, connection pooling)
- Service mesh (registration, heartbeat, health endpoints)
- Observability (structured logging, distributed tracing)
- Type-safe configuration
"""

import asyncio
import os
import sys
import threading
from pathlib import Path
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# NEW: Configuration, Logging, Tracing
from config import get_settings
from core.logging import setup_logging, get_logger
from core.tracing import setup_tracing

# HTTP Server
from agent.server import AgentServer

# Core components (if available)
try:
    from speech_to_text import record_voice, stop_listening_flag
    from llm import DmitryLLM
    from tts import edge_speak, stop_speaking
    from ui import DmitryUI
    from dmitry_operator import DmitryOrchestrator, OrchestratorResult
    from modes import ModeManager
    from knowledge import VectorStore, KnowledgeRetriever, DocumentIngester
    from memory.memory_manager import load_memory, update_memory
    from memory.temporary_memory import TemporaryMemory
    VOICE_UI_AVAILABLE = True
except ImportError:
    VOICE_UI_AVAILABLE = False
    print("⚠️  Voice UI components not available. Running in server-only mode.")

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
    """Main Dmitry assistant class (Voice UI mode)."""
    
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
    """Get voice input asynchronously."""
    return await asyncio.to_thread(record_voice)


async def ai_loop(dmitry: Dmitry):
    """Voice UI loop."""
    print("Voice loop started")
    while True:
        stop_listening_flag.clear()
        user_text = await get_voice_input()
        
        if user_text:
            dmitry.process_input(user_text)
        
        await asyncio.sleep(0.01)


def start_voice_ui():
    """Start voice UI mode (optional)."""
    if not VOICE_UI_AVAILABLE:
        print("❌ Voice UI components not available")
        return
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    face_path = os.path.join(base_dir, "face.png")
    
    ui = DmitryUI(face_path, size=(900, 900))
    dmitry = Dmitry(ui)
    
    def runner():
        asyncio.run(ai_loop(dmitry))
    
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    
    ui.root.mainloop()


def main():
    """Main entry point with configuration, logging, and tracing."""
    
    # Load configuration
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_dir=settings.log_dir if settings.log_level == "DEBUG" else None,
        json_logs=settings.is_production,
        enable_console=True
    )
    logger = get_logger(__name__)
    
    logger.info(
        "dmitry_starting",
        version="1.2.0",
        port=settings.dmitry_port,
        platform_url=settings.platform_url,
        is_production=settings.is_production
    )
    
    # Setup tracing (if enabled)
    if settings.enable_tracing and settings.otel_exporter_otlp_endpoint:
        setup_tracing(
            service_name=settings.service_name,
            service_version="1.2.0",
            otlp_endpoint=settings.otel_exporter_otlp_endpoint,
            enable_console=settings.debug
        )
        logger.info("tracing_enabled", endpoint=settings.otel_exporter_otlp_endpoint)
    
    # Start HTTP server
    server = AgentServer(
        port=settings.dmitry_port,
        platform_url=settings.platform_url
    )
    
    # Set up orchestrator if voice UI available
    if VOICE_UI_AVAILABLE:
        try:
            mode_manager = ModeManager()
            vector_store = VectorStore("knowledge_base")
            retriever = KnowledgeRetriever(vector_store)
            
            llm = DmitryLLM(
                mode_manager=mode_manager,
                knowledge_retriever=retriever,
            )
            
            orchestrator = DmitryOrchestrator(llm=llm)
            server.set_orchestrator(orchestrator)
            
            logger.info("orchestrator_configured", mode="voice_ui")
        except Exception as e:
            logger.warning("orchestrator_setup_failed", error=str(e))
    
    # Start server
    try:
        server.start()
        logger.info(
            "server_started",
            url=f"http://127.0.0.1:{settings.dmitry_port}",
            platform_registered=settings.platform_url is not None
        )
        
        print(f"\n{'='*60}")
        print(f"🚀 Dmitry v1.2.0 - Production Ready")
        print(f"{'='*60}")
        print(f"✓ Server: http://127.0.0.1:{settings.dmitry_port}")
        print(f"✓ Health: http://127.0.0.1:{settings.dmitry_port}/health")
        print(f"✓ Docs: http://127.0.0.1:{settings.dmitry_port}/version")
        if settings.platform_url:
            print(f"✓ Platform: {settings.platform_url}")
        print(f"✓ Log Level: {settings.log_level}")
        if settings.enable_tracing:
            print(f"✓ Tracing: Enabled")
        print(f"{'='*60}")
        print(f"\nPress Ctrl+C to stop\n")
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("shutdown_requested")
            print("\n\nShutting down gracefully...")
            server.stop()
            logger.info("shutdown_complete")
            print("✓ Shutdown complete")
            
    except Exception as e:
        logger.error("startup_failed", error=str(e))
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
