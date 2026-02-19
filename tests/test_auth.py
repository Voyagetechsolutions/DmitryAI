"""
Unit tests for Authentication System
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'MarkX'))

from agent.auth import AuthManager


class TestAuthManager:
    """Test JWT authentication"""
    
    @pytest.fixture
    def auth_manager(self):
        """Create auth manager instance"""
        return AuthManager(secret_key="test_secret_key_12345")
    
    def test_token_generation(self, auth_manager):
        """Test JWT token generation"""
        token = auth_manager.generate_token("user123")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_verification(self, auth_manager):
        """Test token verification"""
        token = auth_manager.generate_token("user123")
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload['user_id'] == "user123"
    
    def test_invalid_token(self, auth_manager):
        """Test invalid token rejection"""
        payload = auth_manager.verify_token("invalid.token.here")
        assert payload is None
    
    def test_token_expiration(self, auth_manager):
        """Test expired token rejection"""
        # Generate token that expires immediately
        token = auth_manager.generate_token("user123", expires_hours=-1)
        payload = auth_manager.verify_token(token)
        assert payload is None
    
    def test_session_management(self, auth_manager):
        """Test session creation and validation"""
        session_id = auth_manager.create_session("user123", "192.168.1.1")
        assert session_id is not None
        
        is_valid = auth_manager.validate_session(session_id)
        assert is_valid is True
    
    def test_session_revocation(self, auth_manager):
        """Test session revocation"""
        session_id = auth_manager.create_session("user123", "192.168.1.1")
        auth_manager.revoke_session(session_id)
        
        is_valid = auth_manager.validate_session(session_id)
        assert is_valid is False
    
    def test_rate_limiting(self, auth_manager):
        """Test rate limiting"""
        user_id = "user123"
        
        # Should allow first requests
        for i in range(5):
            allowed = auth_manager.check_rate_limit(user_id)
            assert allowed is True
        
        # Should block after limit
        for i in range(100):
            auth_manager.check_rate_limit(user_id)
        
        allowed = auth_manager.check_rate_limit(user_id)
        assert allowed is False
