# test_call_ledger.py - Unit tests for call ledger

import pytest
import sys
from pathlib import Path

# Add MarkX to path
markx_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(markx_path))

from core.call_ledger import CallLedger, get_call_ledger, get_verified_citations, get_verified_dependencies


class TestCallLedger:
    """Test CallLedger class."""
    
    def test_record_call(self):
        """Test recording a Platform call."""
        ledger = CallLedger()
        
        call_id = ledger.record_call(
            request_id="test-req-1",
            endpoint="get_risk_findings",
            args={"entity_id": "db-1"},
            response={"findings": []},
            status="success"
        )
        
        assert call_id is not None
        assert len(call_id) == 36  # UUID format
        
        # Verify record exists
        records = ledger.get_records_for_request("test-req-1")
        assert len(records) == 1
        assert records[0].endpoint == "get_risk_findings"
        assert records[0].response_status == "success"
    
    def test_multiple_calls_same_request(self):
        """Test recording multiple calls for same request."""
        ledger = CallLedger()
        request_id = "test-req-2"
        
        # Record multiple calls
        call_id_1 = ledger.record_call(
            request_id=request_id,
            endpoint="get_risk_findings",
            args={},
            response={},
            status="success"
        )
        
        call_id_2 = ledger.record_call(
            request_id=request_id,
            endpoint="get_finding_details",
            args={"finding_id": "find-1"},
            response={},
            status="success"
        )
        
        # Verify both recorded
        records = ledger.get_records_for_request(request_id)
        assert len(records) == 2
        assert call_id_1 != call_id_2
    
    def test_hash_generation(self):
        """Test that hashes are generated correctly."""
        ledger = CallLedger()
        
        call_id = ledger.record_call(
            request_id="test-req-3",
            endpoint="test_endpoint",
            args={"key": "value"},
            response={"result": "ok"},
            status="success"
        )
        
        records = ledger.get_records_for_request("test-req-3")
        record = records[0]
        
        # Verify hashes exist and are SHA-256 format (64 hex chars)
        assert record.args_hash is not None
        assert len(record.args_hash) == 64
        assert record.response_hash is not None
        assert len(record.response_hash) == 64
    
    def test_immutable_ledger(self):
        """Test that ledger records cannot be modified."""
        ledger = CallLedger()
        
        call_id = ledger.record_call(
            request_id="test-req-4",
            endpoint="test_endpoint",
            args={"key": "value"},
            response={"result": "ok"},
            status="success"
        )
        
        # Get record
        records = ledger.get_records_for_request("test-req-4")
        original_hash = records[0].args_hash
        
        # Try to modify (should not affect ledger)
        records[0].args_hash = "modified"
        
        # Verify hash hasn't changed in ledger
        records_again = ledger.get_records_for_request("test-req-4")
        assert records_again[0].args_hash == original_hash
    
    def test_get_verified_citations(self):
        """Test getting verified citations from ledger."""
        ledger = CallLedger()
        request_id = "test-req-5"
        
        # Record some calls
        ledger.record_call(
            request_id=request_id,
            endpoint="get_risk_findings",
            args={},
            response={"findings": []},
            status="success"
        )
        
        ledger.record_call(
            request_id=request_id,
            endpoint="get_finding_details",
            args={"finding_id": "find-1"},
            response={},
            status="success"
        )
        
        # Get citations
        citations = get_verified_citations(request_id)
        
        assert len(citations) == 2
        assert citations[0]["endpoint"] == "get_risk_findings"
        assert "call_id" in citations[0]
        assert "args_hash" in citations[0]
        assert "response_hash" in citations[0]
        assert "timestamp" in citations[0]
    
    def test_get_verified_dependencies(self):
        """Test getting verified dependencies from ledger."""
        ledger = CallLedger()
        request_id = "test-req-6"
        
        # Record call
        ledger.record_call(
            request_id=request_id,
            endpoint="get_risk_findings",
            args={"entity_id": "db-1"},
            response={"findings": []},
            status="success"
        )
        
        # Get dependencies
        dependencies = get_verified_dependencies(request_id)
        
        assert len(dependencies) == 1
        assert dependencies[0]["type"] == "platform_api"
        assert dependencies[0]["endpoint"] == "get_risk_findings"
    
    def test_failed_call_recorded(self):
        """Test that failed calls are also recorded."""
        ledger = CallLedger()
        
        call_id = ledger.record_call(
            request_id="test-req-7",
            endpoint="get_risk_findings",
            args={},
            response={"error": "Connection failed"},
            status="failed"
        )
        
        records = ledger.get_records_for_request("test-req-7")
        assert len(records) == 1
        assert records[0].response_status == "failed"
    
    def test_empty_request_id(self):
        """Test handling of empty request_id."""
        ledger = CallLedger()
        
        records = ledger.get_records_for_request("")
        assert len(records) == 0
    
    def test_nonexistent_request_id(self):
        """Test handling of nonexistent request_id."""
        ledger = CallLedger()
        
        records = ledger.get_records_for_request("nonexistent")
        assert len(records) == 0
    
    def test_singleton_ledger(self):
        """Test that get_call_ledger returns singleton."""
        ledger1 = get_call_ledger()
        ledger2 = get_call_ledger()
        
        assert ledger1 is ledger2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
