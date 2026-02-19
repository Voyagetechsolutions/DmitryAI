# core/call_ledger.py
"""
Call Ledger - Immutable audit trail for Platform API calls.

Makes Dmitry incapable of lying about sources by recording every
Platform call with cryptographic hashes.

No ledger entry = no citation allowed.
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from threading import Lock
import uuid


@dataclass
class CallRecord:
    """Immutable record of a Platform API call."""
    
    call_id: str
    timestamp: float
    endpoint: str
    args_hash: str
    response_hash: str
    response_status: str  # success, error, timeout
    latency_ms: int
    
    # Evidence
    args_redacted: Dict[str, Any]  # Redacted args for audit
    response_summary: Dict[str, Any]  # Summary, not full response
    
    # Traceability
    request_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_citation(self) -> Dict[str, Any]:
        """Convert to citation format for responses."""
        return {
            "call_id": self.call_id,
            "endpoint": self.endpoint,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "args_hash": self.args_hash,
            "response_hash": self.response_hash,
            "status": self.response_status,
            "latency_ms": self.latency_ms
        }


class CallLedger:
    """
    Immutable audit trail for Platform API calls.
    
    Thread-safe, append-only ledger that records every Platform call
    with cryptographic hashes to prevent fabrication of sources.
    """
    
    def __init__(self, max_entries: int = 10000):
        """
        Initialize call ledger.
        
        Args:
            max_entries: Maximum entries to keep in memory
        """
        self._ledger: List[CallRecord] = []
        self._lock = Lock()
        self._max_entries = max_entries
        self._call_index: Dict[str, CallRecord] = {}  # call_id -> record
    
    def record_call(
        self,
        endpoint: str,
        args: Dict[str, Any],
        response: Dict[str, Any],
        status: str,
        latency_ms: int,
        request_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Record a Platform API call.
        
        Args:
            endpoint: API endpoint called
            args: Request arguments
            response: Response data
            status: Call status (success, error, timeout)
            latency_ms: Call latency
            request_id: Request trace ID
            user_id: User/service ID
            tenant_id: Tenant ID
            
        Returns:
            call_id for referencing this record
        """
        call_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Hash arguments and response
        args_hash = self._hash_data(args)
        response_hash = self._hash_data(response)
        
        # Redact sensitive data
        args_redacted = self._redact_sensitive(args)
        response_summary = self._summarize_response(response)
        
        # Create immutable record
        record = CallRecord(
            call_id=call_id,
            timestamp=timestamp,
            endpoint=endpoint,
            args_hash=args_hash,
            response_hash=response_hash,
            response_status=status,
            latency_ms=latency_ms,
            args_redacted=args_redacted,
            response_summary=response_summary,
            request_id=request_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        
        # Append to ledger (thread-safe)
        with self._lock:
            self._ledger.append(record)
            self._call_index[call_id] = record
            
            # Trim if needed
            if len(self._ledger) > self._max_entries:
                removed = self._ledger.pop(0)
                del self._call_index[removed.call_id]
        
        return call_id
    
    def get_record(self, call_id: str) -> Optional[CallRecord]:
        """Get a call record by ID."""
        with self._lock:
            return self._call_index.get(call_id)
    
    def get_records_for_request(self, request_id: str) -> List[CallRecord]:
        """Get all call records for a request."""
        with self._lock:
            return [r for r in self._ledger if r.request_id == request_id]
    
    def verify_citation(self, call_id: str, claimed_endpoint: str) -> bool:
        """
        Verify that a citation is legitimate.
        
        Args:
            call_id: Call ID being cited
            claimed_endpoint: Endpoint claimed to have been called
            
        Returns:
            True if citation is valid
        """
        record = self.get_record(call_id)
        if not record:
            return False
        
        return record.endpoint == claimed_endpoint
    
    def get_citations_for_request(self, request_id: str) -> List[Dict[str, Any]]:
        """
        Get all valid citations for a request.
        
        Args:
            request_id: Request trace ID
            
        Returns:
            List of citation objects
        """
        records = self.get_records_for_request(request_id)
        return [r.to_citation() for r in records]
    
    def get_data_dependencies(self, request_id: str) -> List[str]:
        """
        Get list of endpoints called for a request.
        
        Args:
            request_id: Request trace ID
            
        Returns:
            List of unique endpoints
        """
        records = self.get_records_for_request(request_id)
        return list(set(r.endpoint for r in records))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ledger statistics."""
        with self._lock:
            total_calls = len(self._ledger)
            successful = sum(1 for r in self._ledger if r.response_status == "success")
            failed = sum(1 for r in self._ledger if r.response_status == "error")
            
            if self._ledger:
                avg_latency = sum(r.latency_ms for r in self._ledger) / len(self._ledger)
                oldest = datetime.fromtimestamp(self._ledger[0].timestamp).isoformat()
                newest = datetime.fromtimestamp(self._ledger[-1].timestamp).isoformat()
            else:
                avg_latency = 0
                oldest = None
                newest = None
            
            return {
                "total_calls": total_calls,
                "successful_calls": successful,
                "failed_calls": failed,
                "avg_latency_ms": int(avg_latency),
                "oldest_record": oldest,
                "newest_record": newest,
            }
    
    def _hash_data(self, data: Any) -> str:
        """Create SHA-256 hash of data."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive fields from data."""
        redacted = {}
        sensitive_keys = {
            "password", "secret", "token", "api_key", "apikey",
            "authorization", "auth", "credential", "ssn", "credit_card"
        }
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self._redact_sensitive(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value
        
        return redacted
    
    def _summarize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of response (not full data)."""
        summary = {}
        
        # Include metadata
        if "total" in response:
            summary["total"] = response["total"]
        if "count" in response:
            summary["count"] = response["count"]
        if "status" in response:
            summary["status"] = response["status"]
        
        # Include array lengths, not contents
        for key, value in response.items():
            if isinstance(value, list):
                summary[f"{key}_count"] = len(value)
        
        return summary


# Global ledger instance
_call_ledger: Optional[CallLedger] = None


def get_call_ledger() -> CallLedger:
    """Get or create the global call ledger."""
    global _call_ledger
    if _call_ledger is None:
        _call_ledger = CallLedger()
    return _call_ledger


def record_platform_call(
    endpoint: str,
    args: Dict[str, Any],
    response: Dict[str, Any],
    status: str,
    latency_ms: int,
    request_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> str:
    """
    Record a Platform API call in the ledger.
    
    Returns:
        call_id for citing this call
    """
    ledger = get_call_ledger()
    return ledger.record_call(
        endpoint=endpoint,
        args=args,
        response=response,
        status=status,
        latency_ms=latency_ms,
        request_id=request_id,
        user_id=user_id,
        tenant_id=tenant_id,
    )


def get_verified_citations(request_id: str) -> List[Dict[str, Any]]:
    """
    Get all verified citations for a request.
    
    Only returns citations that exist in the ledger.
    """
    ledger = get_call_ledger()
    return ledger.get_citations_for_request(request_id)


def get_verified_dependencies(request_id: str) -> List[str]:
    """
    Get all verified data dependencies for a request.
    
    Only returns endpoints that were actually called.
    """
    ledger = get_call_ledger()
    return ledger.get_data_dependencies(request_id)


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    # Example usage
    ledger = get_call_ledger()
    
    # Record a call
    call_id = ledger.record_call(
        endpoint="platform_get_risk_findings",
        args={"filters": {"risk_level": "HIGH"}},
        response={"findings": [{"id": "f1", "score": 85}], "total": 1},
        status="success",
        latency_ms=245,
        request_id="req-123",
        user_id="platform-service",
        tenant_id="tenant-1",
    )
    
    print(f"Recorded call: {call_id}")
    
    # Get citations
    citations = ledger.get_citations_for_request("req-123")
    print(f"Citations: {json.dumps(citations, indent=2)}")
    
    # Get dependencies
    deps = ledger.get_data_dependencies("req-123")
    print(f"Dependencies: {deps}")
    
    # Verify citation
    valid = ledger.verify_citation(call_id, "platform_get_risk_findings")
    print(f"Citation valid: {valid}")
    
    # Statistics
    stats = ledger.get_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2)}")
