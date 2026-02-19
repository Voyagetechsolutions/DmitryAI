# core/audit_log.py
"""
Audit Logging System

Comprehensive audit trail for all security-relevant operations.
Logs tool executions, security events, and user actions.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class AuditEventType(Enum):
    """Types of audit events."""
    TOOL_EXECUTION = "tool_execution"
    SECURITY_EVENT = "security_event"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION_CHANGE = "configuration_change"
    DATA_ACCESS = "data_access"
    SYSTEM_EVENT = "system_event"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """An audit log entry."""
    timestamp: str
    event_type: str
    severity: str
    user_id: str
    action: str
    resource: str
    result: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    risk_level: Optional[str] = None


class AuditLogger:
    """
    Audit logging system with structured logging and rotation.
    
    Features:
    - Structured JSON logging
    - Log rotation
    - Query capabilities
    - Security event correlation
    - Compliance reporting
    """
    
    def __init__(
        self,
        log_file: str = "logs/audit.log",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 10,
    ):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to audit log file
            max_file_size: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Create logs directory
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Thread lock for concurrent writes
        self._lock = threading.Lock()
        
        # In-memory cache for recent events (for quick queries)
        self._recent_events: List[AuditEvent] = []
        self._max_recent = 1000
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        risk_level: Optional[str] = None,
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            severity: Event severity
            user_id: User who performed the action
            action: Action performed
            resource: Resource affected
            result: Result of the action (success, failure, etc.)
            details: Additional event details
            ip_address: Source IP address
            session_id: Session identifier
            risk_level: Risk level (low, medium, high)
        """
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type.value,
            severity=severity.value,
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
            risk_level=risk_level,
        )
        
        # Write to file
        self._write_event(event)
        
        # Add to recent events cache
        self._add_to_cache(event)
        
        # Check if rotation needed
        self._check_rotation()
    
    def log_tool_execution(
        self,
        user_id: str,
        tool: str,
        parameters: Dict[str, Any],
        result: str,
        risk_level: str,
        execution_time: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """
        Log a tool execution event.
        
        Args:
            user_id: User who executed the tool
            tool: Tool name
            parameters: Tool parameters
            result: Execution result (success, failure)
            risk_level: Risk level of the tool
            execution_time: Execution time in seconds
            error: Error message if failed
        """
        details = {
            "tool": tool,
            "parameters": parameters,
            "execution_time": execution_time,
        }
        
        if error:
            details["error"] = error
        
        severity = AuditSeverity.INFO if result == "success" else AuditSeverity.ERROR
        
        self.log_event(
            event_type=AuditEventType.TOOL_EXECUTION,
            severity=severity,
            user_id=user_id,
            action=f"execute_tool:{tool}",
            resource=tool,
            result=result,
            details=details,
            risk_level=risk_level,
        )
    
    def log_security_event(
        self,
        user_id: str,
        event_description: str,
        severity: AuditSeverity,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a security event.
        
        Args:
            user_id: User associated with the event
            event_description: Description of the security event
            severity: Event severity
            details: Additional details
        """
        self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            severity=severity,
            user_id=user_id,
            action="security_event",
            resource="system",
            result="detected",
            details=details or {"description": event_description},
        )
    
    def log_authentication(
        self,
        user_id: str,
        action: str,  # login, logout, token_refresh
        result: str,  # success, failure
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        Log an authentication event.
        
        Args:
            user_id: User ID
            action: Authentication action
            result: Result of the action
            ip_address: Source IP
            reason: Failure reason if applicable
        """
        details = {}
        if reason:
            details["reason"] = reason
        
        severity = AuditSeverity.INFO if result == "success" else AuditSeverity.WARNING
        
        self.log_event(
            event_type=AuditEventType.AUTHENTICATION,
            severity=severity,
            user_id=user_id,
            action=action,
            resource="authentication",
            result=result,
            details=details,
            ip_address=ip_address,
        )
    
    def _write_event(self, event: AuditEvent):
        """Write event to log file."""
        with self._lock:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(event)) + "\n")
            except Exception as e:
                # Fallback to stderr if file write fails
                print(f"ERROR: Failed to write audit log: {e}", file=__import__('sys').stderr)
    
    def _add_to_cache(self, event: AuditEvent):
        """Add event to recent events cache."""
        self._recent_events.append(event)
        
        # Trim cache if too large
        if len(self._recent_events) > self._max_recent:
            self._recent_events = self._recent_events[-self._max_recent:]
    
    def _check_rotation(self):
        """Check if log rotation is needed."""
        try:
            if os.path.exists(self.log_file):
                size = os.path.getsize(self.log_file)
                if size >= self.max_file_size:
                    self._rotate_logs()
        except Exception:
            pass
    
    def _rotate_logs(self):
        """Rotate log files."""
        with self._lock:
            try:
                # Rotate existing backups
                for i in range(self.backup_count - 1, 0, -1):
                    old_file = f"{self.log_file}.{i}"
                    new_file = f"{self.log_file}.{i + 1}"
                    
                    if os.path.exists(old_file):
                        if os.path.exists(new_file):
                            os.remove(new_file)
                        os.rename(old_file, new_file)
                
                # Rotate current log
                if os.path.exists(self.log_file):
                    os.rename(self.log_file, f"{self.log_file}.1")
            except Exception as e:
                print(f"ERROR: Log rotation failed: {e}", file=__import__('sys').stderr)
    
    def query_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Query audit events from recent cache.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            
        Returns:
            List of matching audit events
        """
        results = []
        
        for event in reversed(self._recent_events):
            # Apply filters
            if event_type and event.event_type != event_type.value:
                continue
            if user_id and event.user_id != user_id:
                continue
            if severity and event.severity != severity.value:
                continue
            
            # Time filters
            event_time = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
            if start_time and event_time < start_time:
                continue
            if end_time and event_time > end_time:
                continue
            
            results.append(event)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        total_events = len(self._recent_events)
        
        by_type = {}
        by_severity = {}
        by_user = {}
        
        for event in self._recent_events:
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
            by_severity[event.severity] = by_severity.get(event.severity, 0) + 1
            by_user[event.user_id] = by_user.get(event.user_id, 0) + 1
        
        return {
            "total_events": total_events,
            "by_type": by_type,
            "by_severity": by_severity,
            "top_users": sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10],
            "log_file": self.log_file,
            "log_file_size": os.path.getsize(self.log_file) if os.path.exists(self.log_file) else 0,
        }


# Global instance
audit_logger = AuditLogger()
