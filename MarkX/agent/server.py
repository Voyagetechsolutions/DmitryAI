# agent/server.py
"""
Agent API Server - HTTP API for Platform and UI communication.

Endpoints:
- POST /message - Send message to Dmitry (legacy UI)
- POST /chat - Platform chat with context + explainability
- POST /advise - Get action recommendations with reasoning
- POST /mode - Switch cognitive mode
- POST /confirm - Confirm/deny pending action
- GET /logs - Get action logs
- GET /status - Get agent status
- GET /health - Basic health check
- GET /ready - Readiness check with dependencies
- GET /version - Version and capabilities
- GET /metrics - Observability metrics
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
        self.start_time = datetime.now().timestamp()
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "avg_latency_ms": 0,
            "llm_inference_time_ms": 0,
            "active_sessions": 0,
            "latencies": []
        }
    
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
        elif path == "/health":
            self._handle_health()
        elif path == "/ready":
            self._handle_ready()
        elif path == "/live":
            self._handle_live()
        elif path == "/version":
            self._handle_version()
        elif path == "/metrics":
            self._handle_metrics()
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        
        if path == "/message":
            self._handle_message()
        elif path == "/chat":
            self._handle_chat()
        elif path == "/advise":
            self._handle_advise()
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
        import time
        start_time = time.time()
        agent_state.metrics["requests_total"] += 1
        
        try:
            data = self._read_json()
            message = data.get("message", "")
            
            if not message:
                agent_state.metrics["requests_failed"] += 1
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
                
                agent_state.metrics["requests_success"] += 1
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
                
                agent_state.metrics["requests_success"] += 1
                self._send_json(response)
            else:
                agent_state.metrics["requests_failed"] += 1
                self._send_json({
                    "text": "Agent handler not configured",
                    "error": "No handler",
                })
                
        except Exception as e:
            agent_state.metrics["requests_failed"] += 1
            self._send_json({"error": str(e)}, 500)
        finally:
            # Track latency
            latency = int((time.time() - start_time) * 1000)
            agent_state.metrics["latencies"].append(latency)
            if len(agent_state.metrics["latencies"]) > 100:
                agent_state.metrics["latencies"] = agent_state.metrics["latencies"][-100:]
            agent_state.metrics["avg_latency_ms"] = sum(agent_state.metrics["latencies"]) // len(agent_state.metrics["latencies"])
    
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
    
    def _handle_chat(self):
        """
        Handle Platform chat request with context.
        
        POST /chat
        {
            "message": "What's the risk?",
            "context": {
                "incident_id": "inc-123",
                "entity_id": "customer-db"
            }
        }
        
        Response:
        {
            "answer": "The risk score is 85/100...",
            "citations": [...],
            "proposed_actions": [...],
            "sources": [...],
            "confidence": 0.85,
            "schema_version": "1.0",
            "producer_version": "1.2"
        }
        """
        try:
            data = self._read_json()
            message = data.get("message", "")
            context = data.get("context", {})
            
            if not message:
                self._send_json({"error": "No message provided"}, 400)
                return
            
            # Generate request ID for tracing
            import uuid
            request_id = str(uuid.uuid4())
            
            # CRITICAL: Sanitize input BEFORE processing
            from core.input_sanitizer import InputSanitizer
            
            sanitized_message, msg_modified = InputSanitizer.sanitize_message(message)
            sanitization_result = InputSanitizer.sanitize_context(context)
            
            if not sanitization_result.is_safe:
                self._send_json({
                    "error": "Input validation failed",
                    "validation_errors": sanitization_result.validation_errors,
                    "schema_version": "1.0",
                    "producer_version": "1.2"
                }, 400)
                return
            
            # Use sanitized data
            context = sanitization_result.sanitized_data
            message = sanitized_message
            
            # Enhance message with context
            enhanced_message = message
            if context:
                context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
                enhanced_message = f"[Context: {context_str}] {message}"
            
            # Process through orchestrator
            if hasattr(agent_state, 'orchestrator') and agent_state.orchestrator:
                result = agent_state.orchestrator.process(
                    enhanced_message,
                    conversation_history=agent_state.logs[-10:]
                )
                
                # Build evidence chain
                from core.evidence_chain import build_evidence_chain, enrich_actions_with_evidence
                
                evidence_chain = build_evidence_chain(context, request_id)
                proposed_actions = self._extract_proposed_actions(result, request_id, context)
                
                # Enrich actions with evidence
                if proposed_actions:
                    proposed_actions = enrich_actions_with_evidence(proposed_actions, evidence_chain)
                
                # Build explainable response with verified citations only
                response = {
                    "answer": result.content,
                    "citations": self._extract_citations(result, request_id),
                    "proposed_actions": proposed_actions,
                    "sources": self._extract_sources(result, request_id),
                    "reasoning_summary": self._extract_reasoning(result),
                    "confidence": self._calculate_confidence(result, request_id),
                    "data_dependencies": self._extract_dependencies(result, request_id),
                    "evidence_chain": evidence_chain.to_dict(),
                    "request_id": request_id,
                    "schema_version": "1.0",
                    "producer_version": "1.2"
                }
                
                # CRITICAL: Validate output BEFORE returning
                from core.output_validator import OutputValidator
                
                validation = OutputValidator.validate_chat_response(response, request_id)
                
                if not validation.is_valid:
                    # Output validation failed - return error instead of invalid data
                    self._send_json({
                        "error": "Output validation failed",
                        "validation_errors": validation.errors,
                        "schema_version": "1.0",
                        "producer_version": "1.2"
                    }, 500)
                    return
                
                # Add warnings if any
                if validation.warnings:
                    response["_warnings"] = validation.warnings
                
                self._send_json(response)
            else:
                self._send_json({
                    "error": "Orchestrator not configured",
                    "schema_version": "1.0",
                    "producer_version": "1.2"
                }, 500)
                
        except Exception as e:
            self._send_json({
                "error": str(e),
                "schema_version": "1.0",
                "producer_version": "1.2"
            }, 500)
    
    def _handle_advise(self):
        """
        Handle action proposal request.
        
        POST /advise
        Request (AdviseRequest model):
        {
            "finding_id": "find-456",
            "tenant_id": "tenant-1",
            "entity": {
                "type": "database",
                "id": "customer-db",
                "name": "Customer Database",
                "attributes": {}
            },
            "severity": "high",
            "risk_score": 85.0,
            "exposure_paths": [...],
            "evidence_refs": ["evt-123", "find-456"],
            "policy_context": {}
        }
        
        Response (AdviseResponse model):
        {
            "summary": "High risk detected on customer-db...",
            "risk_factors": [...],
            "impact_analysis": "...",
            "recommended_actions": [...],
            "evidence_chain": [...],
            "confidence": 0.87,
            "citations": [...],
            "processing_time_ms": 245
        }
        """
        import time
        start_time = time.time()
        
        try:
            data = self._read_json()
            
            # Validate against AdviseRequest schema
            from shared.contracts.dmitry import AdviseRequest
            try:
                request = AdviseRequest(**data)
            except Exception as e:
                self._send_json({
                    "error": "Invalid request format",
                    "details": str(e),
                    "schema_version": "1.0",
                    "producer_version": "1.2"
                }, 400)
                return
            
            # Generate request ID for tracing
            import uuid
            request_id = str(uuid.uuid4())
            
            # Build context from request
            context = {
                "finding_id": request.finding_id,
                "tenant_id": request.tenant_id,
                "entity_id": request.entity.id,
                "entity_type": request.entity.type,
                "entity_name": request.entity.name,
                "severity": request.severity,
                "risk_score": request.risk_score,
                "evidence_refs": request.evidence_refs,
            }
            
            # CRITICAL: Sanitize input BEFORE processing
            from core.input_sanitizer import InputSanitizer
            
            sanitization_result = InputSanitizer.sanitize_context(context)
            
            if not sanitization_result.is_safe:
                self._send_json({
                    "error": "Input validation failed",
                    "validation_errors": sanitization_result.validation_errors,
                    "schema_version": "1.0",
                    "producer_version": "1.2"
                }, 400)
                return
            
            # Use sanitized data
            context = sanitization_result.sanitized_data
            
            # Build advisory prompt with structured output request
            from core.structured_actions import get_structured_prompt_suffix
            
            prompt = f"""Analyze this security finding and provide recommendations:

Finding ID: {request.finding_id}
Entity: {request.entity.name} ({request.entity.type})
Severity: {request.severity}
Risk Score: {request.risk_score}/100
Evidence: {', '.join(request.evidence_refs)}

Provide:
1. Summary of the risk
2. Key risk factors
3. Impact analysis
4. Specific actionable recommendations

"""
            prompt += get_structured_prompt_suffix()
            
            # Process through orchestrator
            if hasattr(agent_state, 'orchestrator') and agent_state.orchestrator:
                result = agent_state.orchestrator.process(
                    prompt,
                    conversation_history=[]
                )
                
                # Build evidence chain
                from core.evidence_chain import build_evidence_chain, enrich_actions_with_evidence
                
                evidence_chain = build_evidence_chain(context, request_id)
                
                # Parse recommendations with safety validation
                actions = self._parse_action_recommendations(result.content, context, request_id)
                
                # Enrich actions with evidence
                if actions:
                    actions = enrich_actions_with_evidence(actions, evidence_chain)
                
                # Convert to AdviseResponse format
                from shared.contracts.dmitry import RecommendedAction, RiskFactorExplanation
                
                # Extract risk factors from content
                risk_factors = self._extract_risk_factors(result.content, request.severity, request.evidence_refs)
                
                # Convert actions to RecommendedAction format
                recommended_actions = []
                for action in actions:
                    recommended_actions.append({
                        "action_type": action.get("action", "unknown"),
                        "target_type": context.get("entity_type", "unknown"),
                        "target_id": action.get("target", "unknown"),
                        "target_name": context.get("entity_name"),
                        "reason": action.get("reason", ""),
                        "confidence": action.get("confidence", 0.5),
                        "evidence_refs": action.get("evidence_required", request.evidence_refs),
                        "blast_radius": self._map_blast_radius(action.get("blast_radius", "entity_only")),
                        "priority": self._map_priority(action.get("priority", "MEDIUM")),
                    })
                
                # Build response
                processing_time = int((time.time() - start_time) * 1000)
                
                response = {
                    "summary": self._extract_summary(result.content),
                    "risk_factors": risk_factors,
                    "impact_analysis": self._extract_impact_analysis(result.content, request.risk_score),
                    "recommended_actions": recommended_actions,
                    "evidence_chain": self._format_evidence_chain(evidence_chain),
                    "confidence": self._calculate_confidence(result, request_id),
                    "citations": self._extract_citations(result, request_id),
                    "processing_time_ms": processing_time,
                }
                
                # Validate against AdviseResponse schema
                from shared.contracts.dmitry import AdviseResponse
                try:
                    validated_response = AdviseResponse(**response)
                    self._send_json(validated_response.dict())
                except Exception as e:
                    self._send_json({
                        "error": "Response validation failed",
                        "details": str(e),
                        "schema_version": "1.0",
                        "producer_version": "1.2"
                    }, 500)
            else:
                self._send_json({
                    "error": "Orchestrator not configured",
                    "schema_version": "1.0",
                    "producer_version": "1.2"
                }, 500)
                
        except Exception as e:
            self._send_json({
                "error": str(e),
                "schema_version": "1.0",
                "producer_version": "1.2"
            }, 500)
    
    def _handle_health(self):
        """
        Detailed health check with dependencies.
        
        GET /health
        Response (ServiceHealth model):
        {
            "service": "dmitry",
            "status": "healthy",
            "version": "1.2",
            "uptime_seconds": 3600.5,
            "checks": {
                "llm": true,
                "platform": true,
                "call_ledger": true
            },
            "timestamp": "2026-02-19T10:30:00Z"
        }
        """
        import time
        uptime = time.time() - agent_state.start_time if hasattr(agent_state, 'start_time') else 0
        
        # Run health checks
        checks = {}
        status = "healthy"
        
        # Check LLM
        if hasattr(agent_state, 'orchestrator') and agent_state.orchestrator:
            checks["llm"] = True
        else:
            checks["llm"] = False
            status = "degraded"
        
        # Check Platform connection
        try:
            from tools.platform.platform_client import get_platform_client
            platform = get_platform_client()
            checks["platform"] = platform.is_connected()
            if not checks["platform"]:
                status = "degraded"
        except Exception:
            checks["platform"] = False
            status = "degraded"
        
        # Check call ledger
        try:
            from core.call_ledger import get_call_ledger
            ledger = get_call_ledger()
            checks["call_ledger"] = True
        except Exception:
            checks["call_ledger"] = False
            status = "unhealthy"
        
        # Return ServiceHealth model format
        self._send_json({
            "service": "dmitry",
            "status": status,
            "version": "1.2",
            "uptime_seconds": uptime,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    def _handle_ready(self):
        """
        Readiness check with dependencies (Kubernetes probe).
        
        GET /ready
        Response:
        {
            "ready": true,
            "dependencies": {
                "llm": "healthy",
                "platform": "healthy"
            }
        }
        """
        dependencies = {}
        ready = True
        
        # Check LLM
        if hasattr(agent_state, 'orchestrator') and agent_state.orchestrator:
            dependencies["llm"] = "healthy"
        else:
            dependencies["llm"] = "unavailable"
            ready = False
        
        # Check Platform connection
        try:
            from tools.platform.platform_client import get_platform_client
            platform = get_platform_client()
            if platform.is_connected():
                dependencies["platform"] = "healthy"
            else:
                dependencies["platform"] = "unavailable"
                ready = False
        except Exception as e:
            dependencies["platform"] = "error"
            ready = False
        
        status_code = 200 if ready else 503
        self._send_json({
            "ready": ready,
            "dependencies": dependencies,
            "timestamp": datetime.now().isoformat()
        }, status_code)
    
    def _handle_live(self):
        """
        Liveness check (Kubernetes probe).
        
        GET /live
        Response:
        {
            "alive": true
        }
        """
        # Simple check - if we can respond, we're alive
        self._send_json({
            "alive": True,
            "timestamp": datetime.now().isoformat()
        })
    
    def _handle_version(self):
        """
        Version information.
        
        GET /version
        Response:
        {
            "version": "1.2",
            "build": "2026-02-19",
            "capabilities": ["chat", "vision", "security_tools"]
        }
        """
        self._send_json({
            "version": "1.2",
            "build": "2026-02-19",
            "capabilities": [
                "chat",
                "advise",
                "vision",
                "security_tools",
                "platform_integration"
            ],
            "schema_version": "1.0"
        })
    
    def _handle_metrics(self):
        """
        Observability metrics.
        
        GET /metrics
        Response:
        {
            "requests_total": 1523,
            "requests_success": 1498,
            "requests_failed": 25,
            "avg_latency_ms": 245,
            "llm_inference_time_ms": 180,
            "active_sessions": 3
        }
        """
        metrics = agent_state.metrics if hasattr(agent_state, 'metrics') else {}
        
        self._send_json({
            "requests_total": metrics.get("requests_total", 0),
            "requests_success": metrics.get("requests_success", 0),
            "requests_failed": metrics.get("requests_failed", 0),
            "avg_latency_ms": metrics.get("avg_latency_ms", 0),
            "llm_inference_time_ms": metrics.get("llm_inference_time_ms", 0),
            "active_sessions": metrics.get("active_sessions", 0),
            "timestamp": datetime.now().isoformat()
        })
    
    # ========== HELPER METHODS FOR EXPLAINABILITY ==========
    
    def _extract_citations(self, result, request_id: str) -> list:
        """Extract verified citations from call ledger only."""
        from core.call_ledger import get_verified_citations
        
        # Get verified citations from ledger
        citations = get_verified_citations(request_id)
        
        # No fabrication allowed - only ledger citations
        return citations
    
    def _extract_proposed_actions(self, result, request_id: str, context: dict) -> list:
        """Extract proposed actions with safety validation."""
        from core.action_safety import ActionSafetyGate
        from core.call_ledger import get_call_ledger
        
        actions = []
        ledger = get_call_ledger()
        
        # Get evidence from ledger
        records = ledger.get_records_for_request(request_id)
        evidence_call_ids = [r.call_id for r in records]
        
        # Parse content for action keywords
        content = result.content.lower()
        
        if "recommend" in content or "suggest" in content or "should" in content:
            # Detect action types
            if "isolate" in content:
                rec = ActionSafetyGate.create_safe_recommendation(
                    action="isolate_entity",
                    target=context.get("entity_id", "unknown"),
                    reason="High risk score detected",
                    risk_reduction_estimate=0.35,
                    confidence=0.7,
                    priority="HIGH",
                    evidence_call_ids=evidence_call_ids,
                )
                if rec.is_valid:
                    actions.append({
                        "action": rec.action,
                        "target": rec.target,
                        "reason": rec.reason,
                        "risk_reduction_estimate": rec.risk_reduction_estimate,
                        "confidence": rec.confidence,
                        "priority": rec.priority,
                        "approval_required": rec.approval_required,
                        "blast_radius": rec.blast_radius,
                        "impact_level": rec.impact_level,
                        "evidence_count": rec.evidence_count,
                    })
            
            if "block" in content:
                rec = ActionSafetyGate.create_safe_recommendation(
                    action="block_access",
                    target=context.get("entity_id", "unknown"),
                    reason="Access control violation detected",
                    risk_reduction_estimate=0.30,
                    confidence=0.7,
                    priority="HIGH",
                    evidence_call_ids=evidence_call_ids,
                )
                if rec.is_valid:
                    actions.append({
                        "action": rec.action,
                        "target": rec.target,
                        "reason": rec.reason,
                        "risk_reduction_estimate": rec.risk_reduction_estimate,
                        "confidence": rec.confidence,
                        "priority": rec.priority,
                        "approval_required": rec.approval_required,
                        "blast_radius": rec.blast_radius,
                        "impact_level": rec.impact_level,
                        "evidence_count": rec.evidence_count,
                    })
            
            if "monitor" in content:
                rec = ActionSafetyGate.create_safe_recommendation(
                    action="increase_monitoring",
                    target=context.get("entity_id", "unknown"),
                    reason="Suspicious activity detected",
                    risk_reduction_estimate=0.15,
                    confidence=0.8,
                    priority="MEDIUM",
                    evidence_call_ids=evidence_call_ids,
                )
                if rec.is_valid:
                    actions.append({
                        "action": rec.action,
                        "target": rec.target,
                        "reason": rec.reason,
                        "risk_reduction_estimate": rec.risk_reduction_estimate,
                        "confidence": rec.confidence,
                        "priority": rec.priority,
                        "approval_required": rec.approval_required,
                        "blast_radius": rec.blast_radius,
                        "impact_level": rec.impact_level,
                        "evidence_count": rec.evidence_count,
                    })
        
        return actions
    
    def _extract_sources(self, result, request_id: str) -> list:
        """Extract data sources from verified ledger only."""
        from core.call_ledger import get_call_ledger
        
        ledger = get_call_ledger()
        records = ledger.get_records_for_request(request_id)
        
        sources = []
        for record in records:
            sources.append({
                "type": "platform_api",
                "endpoint": record.endpoint,
                "call_id": record.call_id,
                "timestamp": datetime.fromtimestamp(record.timestamp).isoformat(),
                "status": record.response_status,
                "relevance": 0.9 if record.response_status == "success" else 0.5,
            })
        
        return sources
    
    def _extract_reasoning(self, result) -> str:
        """Extract reasoning summary."""
        # Simple extraction - first sentence or paragraph
        content = result.content
        sentences = content.split(". ")
        if sentences:
            return sentences[0] + "."
        return content[:200]
    
    def _calculate_confidence(self, result, request_id: str) -> float:
        """Calculate confidence based on evidence."""
        from core.call_ledger import get_call_ledger
        
        confidence = 0.5
        
        # Higher confidence if tools were used
        ledger = get_call_ledger()
        records = ledger.get_records_for_request(request_id)
        
        if records:
            # More evidence = higher confidence
            evidence_count = len(records)
            confidence += min(0.2, evidence_count * 0.05)
            
            # Successful calls = higher confidence
            successful = sum(1 for r in records if r.response_status == "success")
            if evidence_count > 0:
                success_rate = successful / evidence_count
                confidence += success_rate * 0.2
        
        # Higher confidence if response is detailed
        if len(result.content) > 100:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_dependencies(self, result, request_id: str) -> list:
        """Extract data dependencies from verified ledger only."""
        from core.call_ledger import get_verified_dependencies
        
        # Only return verified dependencies from ledger
        return get_verified_dependencies(request_id)
    
    def _parse_action_recommendations(self, content: str, context: dict, request_id: str) -> list:
        """Parse action recommendations using structured parser (JSON preferred, text fallback)."""
        from core.structured_actions import parse_structured_actions
        from core.call_ledger import get_call_ledger
        
        # Get evidence from ledger
        ledger = get_call_ledger()
        records = ledger.get_records_for_request(request_id)
        evidence_call_ids = [r.call_id for r in records]
        
        # Use structured parser (tries JSON first, falls back to text)
        return parse_structured_actions(content, context, evidence_call_ids)
    
    def _extract_risk_factors(self, content: str, severity: str, evidence_refs: list) -> list:
        """Extract risk factors from LLM response."""
        risk_factors = []
        
        # Parse content for risk factors
        if "high risk" in content.lower() or severity.lower() == "high":
            risk_factors.append({
                "factor": "high_risk_score",
                "severity": severity,
                "description": "Elevated risk score detected",
                "evidence": evidence_refs
            })
        
        if "data" in content.lower() and ("leak" in content.lower() or "exposure" in content.lower()):
            risk_factors.append({
                "factor": "data_exposure",
                "severity": severity,
                "description": "Potential data exposure threat",
                "evidence": evidence_refs
            })
        
        if "access" in content.lower() and "unauthorized" in content.lower():
            risk_factors.append({
                "factor": "unauthorized_access",
                "severity": severity,
                "description": "Unauthorized access detected",
                "evidence": evidence_refs
            })
        
        # Default if none found
        if not risk_factors:
            risk_factors.append({
                "factor": "security_concern",
                "severity": severity,
                "description": "Security concern identified",
                "evidence": evidence_refs
            })
        
        return risk_factors
    
    def _extract_summary(self, content: str) -> str:
        """Extract summary from LLM response."""
        # First sentence or first 200 chars
        sentences = content.split(". ")
        if sentences:
            return sentences[0] + "."
        return content[:200]
    
    def _extract_impact_analysis(self, content: str, risk_score: float) -> str:
        """Extract impact analysis from LLM response."""
        # Look for impact-related content
        lines = content.split("\n")
        for line in lines:
            if "impact" in line.lower():
                return line.strip()
        
        # Default based on risk score
        if risk_score >= 80:
            return "Critical impact - immediate action required to prevent data breach or service disruption."
        elif risk_score >= 60:
            return "High impact - prompt action needed to mitigate security risks."
        elif risk_score >= 40:
            return "Moderate impact - action recommended to reduce exposure."
        else:
            return "Low impact - monitoring and preventive measures advised."
    
    def _format_evidence_chain(self, evidence_chain) -> list:
        """Format evidence chain for AdviseResponse."""
        chain = []
        
        if hasattr(evidence_chain, 'event_id') and evidence_chain.event_id:
            chain.append({"type": "event", "id": evidence_chain.event_id})
        
        if hasattr(evidence_chain, 'finding_id') and evidence_chain.finding_id:
            chain.append({"type": "finding", "id": evidence_chain.finding_id})
        
        if hasattr(evidence_chain, 'call_ids'):
            for call_id in evidence_chain.call_ids:
                chain.append({"type": "platform_call", "id": call_id})
        
        return chain
    
    def _map_blast_radius(self, internal_radius: str) -> str:
        """Map internal blast radius to Platform format."""
        mapping = {
            "entity_only": "low",
            "segment": "medium",
            "org_wide": "high",
            "critical": "critical"
        }
        return mapping.get(internal_radius, "medium")
    
    def _map_priority(self, internal_priority: str) -> int:
        """Map internal priority to Platform format (1-10)."""
        mapping = {
            "LOW": 3,
            "MEDIUM": 5,
            "HIGH": 8,
            "CRITICAL": 10
        }
        return mapping.get(internal_priority, 5)
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class AgentServer:
    """
    HTTP server for agent-UI communication.
    """
    
    DEFAULT_PORT = 8765
    
    def __init__(self, port: int = None, platform_url: str = None):
        """
        Initialize agent server.
        
        Args:
            port: Port to listen on
            platform_url: Platform URL for service registration
        """
        self.port = port or self.DEFAULT_PORT
        self._server = None
        self._thread = None
        self._running = False
        self._registry = None
        self._heartbeat_thread = None
        
        # Initialize service registry if platform_url provided
        if platform_url:
            from shared.registry import ServiceRegistry
            self._registry = ServiceRegistry(
                platform_url=platform_url,
                service_name="dmitry",
                service_type="dmitry",
                service_url=f"http://127.0.0.1:{self.port}",
                version="1.2",
                capabilities=["chat", "advise", "vision", "security_tools", "platform_integration"],
                heartbeat_interval=10,
            )
    
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
        
        # Register with Platform if registry configured
        if self._registry:
            if self._registry.register():
                # Start heartbeat thread
                self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
                self._heartbeat_thread.start()
                print(f"✓ Registered with Platform, heartbeat started")
            else:
                print(f"⚠ Failed to register with Platform (continuing anyway)")
    
    def _run(self):
        """Server loop."""
        while self._running:
            self._server.handle_request()
    
    def _heartbeat_loop(self):
        """Send heartbeats to Platform."""
        import time
        while self._running:
            if self._registry:
                self._registry.send_heartbeat()
            time.sleep(10)  # Every 10 seconds
    
    def stop(self):
        """Stop the server."""
        self._running = False
        
        # Deregister from Platform
        if self._registry:
            self._registry.deregister()
            print(f"✓ Deregistered from Platform")
        
        if self._server:
            self._server.shutdown()
            self._server = None
    
    def get_state(self) -> AgentState:
        """Get the agent state."""
        return agent_state
