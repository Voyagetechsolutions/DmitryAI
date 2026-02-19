"""
Platform API Client for Dmitry

Connects Dmitry to the unified Platform API for:
- Risk findings and analysis
- Entity search and discovery
- Action recommendations
- Security operations

Dmitry does NOT know about PDRI, Aegis, or Neo4j.
Only the Platform knows about backend services.
"""

import requests
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv
from tools.platform.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

load_dotenv()


class PlatformClient:
    """
    Client for querying the unified Platform API.
    
    The Platform orchestrates all backend services
    and provides a clean interface for Dmitry.
    """
    
    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        timeout: int = 30,
        tenant_id: str = None
    ):
        """
        Initialize Platform client.
        
        Args:
            base_url: Platform API base URL (default: from env)
            api_key: Platform API key (default: from env)
            timeout: Request timeout in seconds
            tenant_id: Tenant identifier for multi-tenant deployments
        """
        self.base_url = (base_url or os.getenv("PLATFORM_API_URL", "http://localhost:9000")).rstrip('/')
        self.api_key = api_key or os.getenv("PLATFORM_API_KEY", "")
        self.timeout = timeout
        self.tenant_id = tenant_id or os.getenv("TENANT_ID", "default")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Dmitry-AI/2.0",
            "X-Tenant-ID": self.tenant_id
        })
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
        
        # Circuit breaker to prevent cascading failures
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exception=requests.exceptions.RequestException
        )
    
    def _sanitize_error(self, error: str) -> str:
        """
        Remove sensitive data from error messages.
        
        Args:
            error: Error message
            
        Returns:
            Sanitized error message
        """
        # Remove API keys
        error = re.sub(r'api_key=[^&\s]+', 'api_key=***', error)
        error = re.sub(r'Bearer [^\s]+', 'Bearer ***', error)
        # Remove entity IDs that might be sensitive
        error = re.sub(r'entity_id=[^&\s]+', 'entity_id=***', error)
        # Remove passwords
        error = re.sub(r'password=[^&\s]+', 'password=***', error)
        return error
    
    def _do_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to Platform API (internal, called by circuit breaker).
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
            
        Raises:
            requests.exceptions.RequestException: On request failure
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add trace ID for request correlation
        import uuid
        trace_id = str(uuid.uuid4())
        headers = kwargs.get("headers", {})
        headers["X-Trace-ID"] = trace_id
        kwargs["headers"] = headers
        
        response = self.session.request(
            method,
            url,
            timeout=self.timeout,
            **kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to Platform API with circuit breaker and call ledger.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data or error dict with call_id
        """
        import time
        start_time = time.time()
        
        # Extract args for ledger
        args = {
            "method": method,
            "endpoint": endpoint,
            "params": kwargs.get("params", {}),
            "json": kwargs.get("json", {}),
        }
        
        # Get request context
        request_id = kwargs.get("headers", {}).get("X-Trace-ID", "unknown")
        
        try:
            response_data = self.circuit_breaker.call(self._do_request, method, endpoint, **kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Record successful call in ledger
            from core.call_ledger import record_platform_call
            call_id = record_platform_call(
                endpoint=endpoint,
                args=args,
                response=response_data,
                status="success",
                latency_ms=latency_ms,
                request_id=request_id,
                tenant_id=self.tenant_id,
            )
            
            # Add call_id to response
            response_data["_call_id"] = call_id
            return response_data
            
        except CircuitBreakerOpen as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "error": "Platform temporarily unavailable (circuit breaker open)",
                "connected": False,
                "circuit_breaker": "open"
            }
            
            # Record failed call
            from core.call_ledger import record_platform_call
            call_id = record_platform_call(
                endpoint=endpoint,
                args=args,
                response=error_response,
                status="error",
                latency_ms=latency_ms,
                request_id=request_id,
                tenant_id=self.tenant_id,
            )
            error_response["_call_id"] = call_id
            return error_response
            
        except requests.exceptions.ConnectionError:
            latency_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "error": "Platform connection failed",
                "connected": False
            }
            
            from core.call_ledger import record_platform_call
            call_id = record_platform_call(
                endpoint=endpoint,
                args=args,
                response=error_response,
                status="error",
                latency_ms=latency_ms,
                request_id=request_id,
                tenant_id=self.tenant_id,
            )
            error_response["_call_id"] = call_id
            return error_response
            
        except requests.exceptions.Timeout:
            latency_ms = int((time.time() - start_time) * 1000)
            error_response = {
                "error": "Platform request timeout",
                "connected": False
            }
            
            from core.call_ledger import record_platform_call
            call_id = record_platform_call(
                endpoint=endpoint,
                args=args,
                response=error_response,
                status="timeout",
                latency_ms=latency_ms,
                request_id=request_id,
                tenant_id=self.tenant_id,
            )
            error_response["_call_id"] = call_id
            return error_response
            
        except requests.exceptions.HTTPError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            sanitized_error = self._sanitize_error(str(e))
            error_response = {
                "error": f"Platform HTTP error: {e.response.status_code}",
                "status_code": e.response.status_code,
                "connected": False
            }
            
            from core.call_ledger import record_platform_call
            call_id = record_platform_call(
                endpoint=endpoint,
                args=args,
                response=error_response,
                status="error",
                latency_ms=latency_ms,
                request_id=request_id,
                tenant_id=self.tenant_id,
            )
            error_response["_call_id"] = call_id
            return error_response
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            sanitized_error = self._sanitize_error(str(e))
            error_response = {
                "error": f"Platform error: {sanitized_error}",
                "connected": False
            }
            
            from core.call_ledger import record_platform_call
            call_id = record_platform_call(
                endpoint=endpoint,
                args=args,
                response=error_response,
                status="error",
                latency_ms=latency_ms,
                request_id=request_id,
                tenant_id=self.tenant_id,
            )
            error_response["_call_id"] = call_id
            return error_response
    
    # ========== RISK FINDINGS ==========
    
    def get_risk_findings(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get risk findings from Platform.
        
        Args:
            filters: Optional filters (risk_level, entity_type, etc.)
            
        Returns:
            {
                "findings": [
                    {
                        "id": "finding-123",
                        "entity_id": "customer-db",
                        "risk_score": 85,
                        "risk_level": "HIGH",
                        "description": "...",
                        "timestamp": "2026-02-19T10:30:00Z"
                    },
                    ...
                ],
                "total": 42
            }
        """
        params = filters or {}
        return self._request("GET", "/api/v1/risk-findings", params=params)
    
    def get_finding_details(self, finding_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific finding.
        
        Args:
            finding_id: Finding identifier
            
        Returns:
            {
                "id": "finding-123",
                "entity_id": "customer-db",
                "risk_score": 85,
                "risk_level": "HIGH",
                "description": "...",
                "factors": [...],
                "related_entities": [...],  # Generic relationships, not graph-specific
                "recommendations": [...],
                "timestamp": "2026-02-19T10:30:00Z"
            }
        """
        return self._request("GET", f"/api/v1/risk-findings/{finding_id}")
    
    # ========== ENTITY SEARCH ==========
    
    def search_entities(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search for entities across the platform.
        
        Args:
            query: Search query
            filters: Optional filters (entity_type, risk_level, etc.)
            
        Returns:
            {
                "entities": [
                    {
                        "entity_id": "customer-db",
                        "entity_type": "database",
                        "risk_score": 85,
                        "risk_level": "HIGH"
                    },
                    ...
                ],
                "total": 15
            }
        """
        params = {"q": query, **(filters or {})}
        return self._request("GET", "/api/v1/entities/search", params=params)
    
    # ========== ACTIONS ==========
    
    def propose_actions(self, finding_id: str) -> Dict[str, Any]:
        """
        Get recommended actions for a finding.
        
        Args:
            finding_id: Finding identifier
            
        Returns:
            {
                "finding_id": "finding-123",
                "actions": [
                    {
                        "action_id": "action-456",
                        "action_type": "isolate",
                        "description": "Isolate customer-db from network",
                        "priority": "HIGH",
                        "estimated_impact": "..."
                    },
                    ...
                ]
            }
        """
        return self._request("GET", f"/api/v1/risk-findings/{finding_id}/actions")
    
    def execute_action(self, action_id: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a security action.
        
        Args:
            action_id: Action identifier
            params: Optional action parameters
            
        Returns:
            {
                "action_id": "action-456",
                "status": "executed",
                "result": "...",
                "timestamp": "2026-02-19T10:30:00Z"
            }
        """
        payload = {"action_id": action_id, "params": params or {}}
        return self._request("POST", "/api/v1/actions/execute", json=payload)
    
    # ========== HEALTH & STATUS ==========
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check Platform health status.
        
        Returns:
            {
                "status": "healthy",
                "version": "1.0.0",
                "services": {
                    "pdri": "healthy",
                    "aegis": "healthy",
                    "neo4j": "healthy"
                },
                "connected": true
            }
        """
        result = self._request("GET", "/api/v1/health")
        if result.get("error"):
            return {
                "status": "unhealthy",
                "connected": False,
                "error": result.get("error")
            }
        return {**result, "connected": True}
    
    def is_connected(self) -> bool:
        """Check if Platform is connected and responsive."""
        health = self.health_check()
        return health.get("connected", False)


# ========== SINGLETON INSTANCE ==========

_platform_client: Optional[PlatformClient] = None


def get_platform_client() -> PlatformClient:
    """Get or create the global Platform client instance."""
    global _platform_client
    if _platform_client is None:
        _platform_client = PlatformClient()
    return _platform_client


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    # Test Platform connection
    platform = get_platform_client()
    
    print("Testing Platform connection...")
    health = platform.health_check()
    print(f"Connected: {health.get('connected')}")
    print(f"Status: {health.get('status')}")
    
    if health.get("connected"):
        # Test risk findings
        print("\nTesting risk findings...")
        findings = platform.get_risk_findings({"risk_level": "HIGH"})
        print(f"Found {findings.get('total', 0)} high-risk findings")
        
        # Test entity search
        print("\nTesting entity search...")
        results = platform.search_entities("customer")
        print(f"Found {results.get('total', 0)} entities matching 'customer'")
