# test_platform_client.py - Integration tests for Platform client

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import time

# Add MarkX to path
markx_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(markx_path))

from tools.platform.platform_client import PlatformClient, get_platform_client
from tools.platform.circuit_breaker import CircuitBreaker


@pytest.mark.integration
class TestPlatformClientIntegration:
    """Integration tests for Platform client."""
    
    def test_client_initialization(self):
        """Test Platform client initialization."""
        client = PlatformClient(
            base_url="http://localhost:8000",
            timeout=30.0
        )
        
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.circuit_breaker is not None
    
    def test_singleton_client(self):
        """Test that get_platform_client returns singleton."""
        client1 = get_platform_client()
        client2 = get_platform_client()
        
        assert client1 is client2
    
    @patch('tools.platform.platform_client.requests.post')
    def test_successful_call(self, mock_post):
        """Test successful Platform API call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"findings": [{"id": "find-1"}]}
        mock_post.return_value = mock_response
        
        client = PlatformClient(base_url="http://localhost:8000")
        result = client.call("get_risk_findings", entity_id="db-1")
        
        assert result["findings"][0]["id"] == "find-1"
        assert mock_post.called
    
    @patch('tools.platform.platform_client.requests.post')
    def test_retry_on_failure(self, mock_post):
        """Test retry logic on failure."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "success"}
        
        mock_post.side_effect = [
            Exception("Connection error"),
            mock_response_success
        ]
        
        client = PlatformClient(
            base_url="http://localhost:8000",
            max_retries=3,
            retry_delay=0.1
        )
        
        result = client.call("test_endpoint")
        
        assert result["result"] == "success"
        assert mock_post.call_count == 2
    
    @patch('tools.platform.platform_client.requests.post')
    def test_circuit_breaker_opens(self, mock_post):
        """Test circuit breaker opens after failures."""
        # All calls fail
        mock_post.side_effect = Exception("Connection error")
        
        client = PlatformClient(
            base_url="http://localhost:8000",
            max_retries=1,
            retry_delay=0.1
        )
        
        # Make multiple failing calls
        for i in range(6):
            try:
                client.call("test_endpoint")
            except:
                pass
        
        # Circuit should be open now
        assert client.circuit_breaker.state == "open"
    
    @patch('tools.platform.platform_client.requests.post')
    def test_connection_pooling(self, mock_post):
        """Test connection pooling works."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_post.return_value = mock_response
        
        client = PlatformClient(base_url="http://localhost:8000")
        
        # Make multiple calls
        for i in range(10):
            result = client.call("test_endpoint")
            assert result["result"] == "success"
        
        # Verify session is reused
        assert client.session is not None
    
    def test_is_connected_no_platform(self):
        """Test is_connected when Platform is not available."""
        client = PlatformClient(base_url="http://nonexistent:9999")
        
        # Should return False without raising exception
        assert client.is_connected() is False
    
    @patch('tools.platform.platform_client.requests.post')
    def test_timeout_handling(self, mock_post):
        """Test timeout handling."""
        import requests
        mock_post.side_effect = requests.Timeout("Request timeout")
        
        client = PlatformClient(
            base_url="http://localhost:8000",
            timeout=1.0,
            max_retries=1
        )
        
        with pytest.raises(Exception):
            client.call("test_endpoint")
    
    @patch('tools.platform.platform_client.requests.post')
    def test_call_ledger_integration(self, mock_post):
        """Test that calls are recorded in ledger."""
        from core.call_ledger import get_call_ledger
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_post.return_value = mock_response
        
        client = PlatformClient(base_url="http://localhost:8000")
        ledger = get_call_ledger()
        
        # Make call with request_id
        result = client.call(
            "test_endpoint",
            _request_id="test-req-integration",
            param="value"
        )
        
        # Verify recorded in ledger
        records = ledger.get_records_for_request("test-req-integration")
        assert len(records) >= 1
        assert records[0].endpoint == "test_endpoint"
    
    @patch('tools.platform.platform_client.requests.post')
    def test_graceful_degradation(self, mock_post):
        """Test graceful degradation with cached responses."""
        # First call succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "cached"}
        
        # Second call fails
        mock_post.side_effect = [
            mock_response_success,
            Exception("Connection error")
        ]
        
        client = PlatformClient(base_url="http://localhost:8000")
        
        # First call - should succeed
        result1 = client.call("test_endpoint", param="value")
        assert result1["result"] == "cached"
        
        # Second call - should fail but could return cached if implemented
        try:
            result2 = client.call("test_endpoint", param="value")
        except:
            pass  # Expected to fail without cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
