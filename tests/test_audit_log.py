"""
Unit tests for Audit Logging
"""
import pytest
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'MarkX'))

from core.audit_log import AuditLogger


class TestAuditLogger:
    """Test audit logging functionality"""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file"""
        fd, path = tempfile.mkstemp(suffix='.log')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def audit_logger(self, temp_log_file):
        """Create audit logger instance"""
        return AuditLogger(log_file=temp_log_file)
    
    def test_log_action(self, audit_logger, temp_log_file):
        """Test logging an action"""
        audit_logger.log_action(
            event_type="tool_execution",
            user_id="user123",
            action="file_read",
            details={"path": "/test/file.txt"},
            severity="info"
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['user_id'] == "user123"
        assert log_entry['action'] == "file_read"
        assert log_entry['event_type'] == "tool_execution"
    
    def test_log_security_event(self, audit_logger, temp_log_file):
        """Test logging security event"""
        audit_logger.log_security_event(
            user_id="user123",
            event="prompt_injection_detected",
            details={"risk_score": 85},
            severity="critical"
        )
        
        with open(temp_log_file, 'r') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['event_type'] == "security"
        assert log_entry['severity'] == "critical"
        assert log_entry['details']['risk_score'] == 85
    
    def test_query_logs(self, audit_logger):
        """Test querying logs"""
        # Log multiple entries
        for i in range(5):
            audit_logger.log_action(
                event_type="tool_execution",
                user_id=f"user{i}",
                action="test_action",
                details={},
                severity="info"
            )
        
        # Query logs
        results = audit_logger.query_logs(user_id="user2")
        assert len(results) == 1
        assert results[0]['user_id'] == "user2"
    
    def test_get_statistics(self, audit_logger):
        """Test getting log statistics"""
        # Log various events
        audit_logger.log_action("tool_execution", "user1", "action1", {}, "info")
        audit_logger.log_action("tool_execution", "user1", "action2", {}, "warning")
        audit_logger.log_security_event("user1", "test_event", {}, "critical")
        
        stats = audit_logger.get_statistics()
        assert stats['total_events'] == 3
        assert 'tool_execution' in stats['by_type']
        assert 'security' in stats['by_type']
