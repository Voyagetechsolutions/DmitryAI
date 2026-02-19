# agent/server.py
"""
Agent API Server - HTTP API for Electron UI communication.

Endpoints:
- POST /message - Send message to Dmitry
- POST /mode - Switch cognitive mode
- POST /confirm - Confirm/deny pending action
- GET /logs - Get action logs
- GET /status - Get agent status
"""

import json
import threading
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Callable
from datetime import datetime


class AgentState:
    """Shared state for the agent."""
    
    def __init__(self):
        self.current_mode = "general"
        self.pending_confirmations = {}
        self.confirmation_responses = queue.Queue()
        self.message_handler: Optional[Callable] = None
        self.mode_switch_handler: Optional[Callable] = None
        self.logs = []
        self.max_logs = 100
    
    def add_log(self, tool: str, status: str, message: str = ""):
        """Add an action log entry."""
        log = {
            "tool": tool,
            "status": status,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": datetime.now().isoformat(),
        }
        self.logs.insert(0, log)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[:self.max_logs]
        return log
    
    def request_confirmation(self, action_id: str, message: str) -> bool:
        """Request confirmation from UI and wait for response."""
        self.pending_confirmations[action_id] = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Wait for response (with timeout)
        try:
            response = self.confirmation_responses.get(timeout=60)
            if response.get("action_id") == action_id:
                return response.get("confirmed", False)
        except queue.Empty:
            pass
        
        return False


# Global state
agent_state = AgentState()


class AgentRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for agent API."""
    
    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _read_json(self) -> dict:
        """Read JSON from request body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            return json.loads(body.decode())
        return {}
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, api-key, authorization")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == "/status":
            self._handle_status()
        elif path == "/logs":
            limit = int(query.get("limit", [50])[0])
            self._handle_logs(limit)
        elif path == "/confirmations":
            self._handle_pending_confirmations()
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        
        if path == "/message":
            self._handle_message()
        elif path == "/mode":
            self._handle_mode_switch()
        elif path == "/confirm":
            self._handle_confirmation()
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _handle_status(self):
        """Return agent status."""
        self._send_json({
            "connected": True,
            "mode": agent_state.current_mode,
            "pending_confirmations": len(agent_state.pending_confirmations),
            "timestamp": datetime.now().isoformat(),
        })
    
    def _handle_logs(self, limit: int):
        """Return action logs."""
        self._send_json({
            "logs": agent_state.logs[:limit],
            "total": len(agent_state.logs),
        })
    
    def _handle_pending_confirmations(self):
        """Return pending confirmations."""
        self._send_json({
            "confirmations": [
                {"action_id": k, **v}
                for k, v in agent_state.pending_confirmations.items()
            ]
        })
    
    def _handle_message(self):
        """Handle incoming message from UI."""
        try:
            data = self._read_json()
            message = data.get("message", "")
            
            if not message:
                self._send_json({"error": "No message provided"}, 400)
                return
            
            # Use Orchestrator if available (New Path)
            if hasattr(agent_state, 'orchestrator') and agent_state.orchestrator:
                result = agent_state.orchestrator.process(
                    message,
                    conversation_history=agent_state.logs[-10:] if hasattr(agent_state, 'logs') else []
                )
                
                response = {
                    "text": result.content,
                    "intent": result.type,
                    "mode": agent_state.current_mode,
                }
                
                if result.action_results:
                    response["tool_executed"] = "Action Plan"
                    response["tool_result"] = f"Executed {len(result.action_results)} steps"
                    
                    for step_res in result.action_results:
                        agent_state.add_log(
                            step_res.get("tool", "action"),
                            step_res.get("status", "unknown"),
                            step_res.get("message", "")
                        )
                
                self._send_json(response)
                
            # Legacy Path
            elif agent_state.message_handler:
                result = agent_state.message_handler(message)
                
                # Extract response components
                response = {
                    "text": result.get("text", ""),
                    "intent": result.get("intent", "chat"),
                    "mode": agent_state.current_mode,
                }
                
                # Add tool execution info if applicable
                if result.get("tool_executed"):
                    response["tool_executed"] = result["tool_executed"]
                    response["tool_result"] = result.get("tool_result")
                    
                    # Add to logs
                    log = agent_state.add_log(
                        result["tool_executed"],
                        "success" if result.get("tool_success") else "failed",
                        result.get("tool_result", ""),
                    )
                    response["log"] = log
                
                self._send_json(response)
            else:
                self._send_json({
                    "text": "Agent handler not configured",
                    "error": "No handler",
                })
                
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _handle_mode_switch(self):
        """Handle mode switch request."""
        try:
            data = self._read_json()
            mode = data.get("mode", "")
            
            if not mode:
                self._send_json({"error": "No mode specified"}, 400)
                return
            
            # Call mode switch handler if set
            if agent_state.mode_switch_handler:
                success, message = agent_state.mode_switch_handler(mode)
                if success:
                    agent_state.current_mode = mode
                self._send_json({
                    "success": success,
                    "message": message,
                    "mode": agent_state.current_mode,
                })
            else:
                agent_state.current_mode = mode
                self._send_json({
                    "success": True,
                    "mode": mode,
                })
                
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _handle_confirmation(self):
        """Handle confirmation response from UI."""
        try:
            data = self._read_json()
            action_id = data.get("actionId")
            confirmed = data.get("confirmed", False)
            
            if not action_id:
                self._send_json({"error": "No actionId"}, 400)
                return
            
            # Remove from pending and queue response
            if action_id in agent_state.pending_confirmations:
                del agent_state.pending_confirmations[action_id]
            
            agent_state.confirmation_responses.put({
                "action_id": action_id,
                "confirmed": confirmed,
            })
            
            self._send_json({"success": True})
            
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class AgentServer:
    """
    HTTP server for agent-UI communication.
    """
    
    DEFAULT_PORT = 8765
    
    def __init__(self, port: int = None):
        """
        Initialize agent server.
        
        Args:
            port: Port to listen on
        """
        self.port = port or self.DEFAULT_PORT
        self._server = None
        self._thread = None
        self._running = False
    
    def set_message_handler(self, handler: Callable):
        """Set the message handler function (Legacy - now uses orchestrator)."""
        agent_state.message_handler = handler

    def set_orchestrator(self, orchestrator):
        """Set the orchestrator instance."""
        agent_state.orchestrator = orchestrator
        
        # Configure orchestrator callbacks
        if orchestrator:
            orchestrator.on_action_start = lambda msg: self.add_log("System", "running", msg)
            orchestrator.on_action_complete = lambda msg, success: self.add_log(
                "System", "success" if success else "failed", msg
            )
            orchestrator.on_confirmation_needed = lambda msg: self.request_confirmation(
                f"conf_{datetime.now().timestamp()}", msg
            )
    
    def set_mode_switch_handler(self, handler: Callable):
        """Set the mode switch handler function."""
        agent_state.mode_switch_handler = handler
    
    def request_confirmation(self, action_id: str, message: str) -> bool:
        """Request confirmation from UI."""
        return agent_state.request_confirmation(action_id, message)
    
    def add_log(self, tool: str, status: str, message: str = "") -> dict:
        """Add an action log entry."""
        return agent_state.add_log(tool, status, message)
    
    def start(self):
        """Start the server."""
        if self._running:
            return
        
        self._server = HTTPServer(("127.0.0.1", self.port), AgentRequestHandler)
        self._running = True
        
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
        print(f"✓ Agent API server started on http://127.0.0.1:{self.port}")
    
    def _run(self):
        """Server loop."""
        while self._running:
            self._server.handle_request()
    
    def stop(self):
        """Stop the server."""
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server = None
    
    def get_state(self) -> AgentState:
        """Get the agent state."""
        return agent_state
