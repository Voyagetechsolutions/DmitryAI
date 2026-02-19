# run_dmitry.py - Dmitry v1.2 Unified Launcher
"""
Unified launcher for Dmitry.

Modes:
- tkinter: Original Tkinter UI (default)
- server: Start agent API server for Electron UI
- headless: Run without UI (API only)
"""

import sys
import os
import argparse
import subprocess

# Auto-activate venv if running from global python
if "Mark-X" in os.getcwd() and ".venv" not in sys.executable:
    venv_python = os.path.join(os.getcwd(), "..", ".venv", "Scripts", "python.exe")
    venv_python = os.path.abspath(venv_python)
    if os.path.exists(venv_python):
        # Re-execute with venv python
        print(f"🔄 Switching to venv: {venv_python}")
        subprocess.call([venv_python] + sys.argv)
        sys.exit(0)


def run_tkinter():
    """Run with Tkinter UI."""
    from main import main
    main()


def run_server():
    """Run agent server for Electron UI."""
    from agent import AgentServer
    from modes import ModeManager
    from llm import DmitryLLM
    from dmitry_operator import DmitryOrchestrator
    
    print("=" * 50)
    print("  DMITRY v1.2 - Agent Mode")
    print("=" * 50)
    
    # Initialize components
    mode_manager = ModeManager()
    
    # Initialize LLM (knowledge retrieval integrated internally if needed)
    llm = DmitryLLM(mode_manager=mode_manager)
    
    # Initialize Orchestrator (The Brain Router)
    orchestrator = DmitryOrchestrator(llm=llm)
    
    # Create server
    server = AgentServer()
    
    # Set handlers
    server.set_orchestrator(orchestrator)
    
    def handle_mode_switch(mode: str) -> tuple:
        """Handle mode switch from UI."""
        success, message = mode_manager.switch_mode(mode)
        return success, message
    
    server.set_mode_switch_handler(handle_mode_switch)
    
    # Start server
    server.start()
    
    print(f"\n✓ Mode: {mode_manager.current_mode_name}")
    print(f"✓ Orchestrator: Ready (Hands & Eyes active)")
    print(f"\nAgent ready. Connect with Electron UI or API client.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()


def main():
    parser = argparse.ArgumentParser(description="Dmitry v1.2 AI Assistant")
    parser.add_argument(
        "--mode",
        choices=["tkinter", "server", "headless"],
        default="tkinter",
        help="UI mode: tkinter (default), server (for Electron), headless"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="API server port (default: 8765)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "tkinter":
        run_tkinter()
    elif args.mode == "server":
        run_server()
    elif args.mode == "headless":
        run_server()


if __name__ == "__main__":
    main()
