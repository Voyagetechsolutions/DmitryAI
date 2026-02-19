# tools/logging.py
"""
Action logging system for tool executions.

All tool actions log:
- Timestamp
- Mode active
- Tool called
- Parameters (safe subset)
- Result
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional
from threading import Lock


@dataclass
class ActionLog:
    """Represents a logged action."""
    timestamp: str
    mode: str
    tool: str
    parameters: dict
    result_status: str
    result_message: str
    execution_time_ms: float
    user_confirmed: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ActionLogger:
    """
    Centralized action logging for transparency and audit.
    """
    
    # Parameters that should be redacted from logs
    SENSITIVE_PARAMS = {"password", "secret", "token", "key", "api_key", "credential"}
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the action logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self._log_dir = log_dir
        self._logs: list[ActionLog] = []
        self._lock = Lock()
        self._max_memory_logs = 1000
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
    
    def _get_log_file_path(self) -> str:
        """Get the current log file path (daily rotation)."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return os.path.join(self._log_dir, f"actions_{date_str}.jsonl")
    
    def _sanitize_params(self, params: dict) -> dict:
        """Remove sensitive parameters from logging."""
        if not params:
            return {}
        
        sanitized = {}
        for key, value in params.items():
            # Check if key contains sensitive words
            if any(s in key.lower() for s in self.SENSITIVE_PARAMS):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_action(
        self,
        mode: str,
        tool: str,
        parameters: dict,
        result_status: str,
        result_message: str = "",
        execution_time_ms: float = 0,
        user_confirmed: bool = False,
    ) -> ActionLog:
        """
        Log a tool action.
        
        Args:
            mode: Current cognitive mode
            tool: Tool name
            parameters: Tool parameters (will be sanitized)
            result_status: Status of execution
            result_message: Result message
            execution_time_ms: Execution time in milliseconds
            user_confirmed: Whether user confirmed the action
            
        Returns:
            The created ActionLog
        """
        log_entry = ActionLog(
            timestamp=datetime.utcnow().isoformat() + "Z",
            mode=mode,
            tool=tool,
            parameters=self._sanitize_params(parameters),
            result_status=result_status,
            result_message=result_message[:200] if result_message else "",  # Truncate
            execution_time_ms=round(execution_time_ms, 2),
            user_confirmed=user_confirmed,
        )
        
        with self._lock:
            # Add to memory
            self._logs.append(log_entry)
            
            # Trim memory logs if too many
            if len(self._logs) > self._max_memory_logs:
                self._logs = self._logs[-self._max_memory_logs:]
            
            # Write to file
            try:
                with open(self._get_log_file_path(), "a", encoding="utf-8") as f:
                    f.write(log_entry.to_json() + "\n")
            except Exception as e:
                print(f"⚠️ Failed to write log: {e}")
        
        return log_entry
    
    def get_recent_logs(self, limit: int = 50) -> list[ActionLog]:
        """Get recent action logs from memory."""
        with self._lock:
            return self._logs[-limit:]
    
    def get_logs_by_tool(self, tool_name: str, limit: int = 50) -> list[ActionLog]:
        """Get logs filtered by tool name."""
        with self._lock:
            filtered = [log for log in self._logs if log.tool == tool_name]
            return filtered[-limit:]
    
    def get_logs_by_mode(self, mode: str, limit: int = 50) -> list[ActionLog]:
        """Get logs filtered by mode."""
        with self._lock:
            filtered = [log for log in self._logs if log.mode == mode]
            return filtered[-limit:]
    
    def export_audit_trail(self, start_date: str = None, end_date: str = None) -> str:
        """
        Export audit trail as JSON.
        
        Args:
            start_date: Optional ISO date string for start filter
            end_date: Optional ISO date string for end filter
            
        Returns:
            JSON string of logs
        """
        logs_to_export = []
        
        with self._lock:
            for log in self._logs:
                # Apply date filters if provided
                if start_date and log.timestamp < start_date:
                    continue
                if end_date and log.timestamp > end_date:
                    continue
                
                logs_to_export.append(log.to_dict())
        
        return json.dumps(logs_to_export, indent=2)
    
    def get_statistics(self) -> dict:
        """Get statistics about logged actions."""
        with self._lock:
            if not self._logs:
                return {"total": 0}
            
            by_tool = {}
            by_mode = {}
            by_status = {}
            total_time = 0
            
            for log in self._logs:
                by_tool[log.tool] = by_tool.get(log.tool, 0) + 1
                by_mode[log.mode] = by_mode.get(log.mode, 0) + 1
                by_status[log.result_status] = by_status.get(log.result_status, 0) + 1
                total_time += log.execution_time_ms
            
            return {
                "total": len(self._logs),
                "by_tool": by_tool,
                "by_mode": by_mode,
                "by_status": by_status,
                "avg_execution_time_ms": round(total_time / len(self._logs), 2),
            }


# Global logger instance
_action_logger: Optional[ActionLogger] = None


def get_action_logger() -> ActionLogger:
    """Get or create the global action logger."""
    global _action_logger
    if _action_logger is None:
        _action_logger = ActionLogger()
    return _action_logger
