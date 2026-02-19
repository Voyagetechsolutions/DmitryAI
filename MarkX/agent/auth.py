# agent/auth.py
"""
Authentication & Authorization System

Provides JWT-based authentication for the Dmitry API server.
Includes rate limiting and session management.
"""

import jwt
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
import os


@dataclass
class Session:
    """User session information."""
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    requests: int = 0
    window_start: float = field(default_factory=time.time)
    blocked_until: Optional[float] = None


class AuthManager:
    """
    Manages authentication and authorization for the API server.
    
    Features:
    - JWT token generation and validation
    - Session management
    - Rate limiting per user/IP
    - Token refresh
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        token_expiry_hours: int = 24,
        rate_limit: int = 100,
        rate_window_seconds: int = 60,
    ):
        """
        Initialize authentication manager.
        
        Args:
            secret_key: JWT secret key (generated if not provided)
            token_expiry_hours: Token validity period
            rate_limit: Max requests per window
            rate_window_seconds: Rate limit window duration
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
        self.token_expiry_hours = token_expiry_hours
        self.rate_limit = rate_limit
        self.rate_window_seconds = rate_window_seconds
        
        # Session storage (in-memory for now, should use Redis in production)
        self.sessions: Dict[str, Session] = {}
        
        # Rate limiting storage
        self.rate_limits: Dict[str, RateLimitInfo] = defaultdict(RateLimitInfo)
        
        # Revoked tokens (for logout)
        self.revoked_tokens: set = set()
    
    def generate_token(
        self,
        user_id: str,
        expires_hours: Optional[int] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_id: Unique user identifier
            expires_hours: Token expiry (uses default if not provided)
            additional_claims: Extra claims to include in token
            
        Returns:
            JWT token string
        """
        expires_hours = expires_hours or self.token_expiry_hours
        expiry = datetime.utcnow() + timedelta(hours=expires_hours)
        
        payload = {
            "user_id": user_id,
            "exp": expiry,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Create session
        session = Session(
            user_id=user_id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=expiry,
        )
        self.sessions[token] = session
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        # Check if token is revoked
        if token in self.revoked_tokens:
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Update session activity
            if token in self.sessions:
                self.sessions[token].last_activity = datetime.utcnow()
            
            return payload
        except jwt.ExpiredSignatureError:
            # Clean up expired session
            if token in self.sessions:
                del self.sessions[token]
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (logout).
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked successfully
        """
        self.revoked_tokens.add(token)
        
        if token in self.sessions:
            del self.sessions[token]
        
        return True
    
    def refresh_token(self, old_token: str) -> Optional[str]:
        """
        Refresh an existing token.
        
        Args:
            old_token: Current token
            
        Returns:
            New token if successful, None otherwise
        """
        payload = self.verify_token(old_token)
        if not payload:
            return None
        
        # Revoke old token
        self.revoke_token(old_token)
        
        # Generate new token
        user_id = payload.get("user_id")
        return self.generate_token(user_id)
    
    def check_rate_limit(self, identifier: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: User ID or IP address
            
        Returns:
            (allowed, error_message) tuple
        """
        now = time.time()
        limit_info = self.rate_limits[identifier]
        
        # Check if currently blocked
        if limit_info.blocked_until and now < limit_info.blocked_until:
            remaining = int(limit_info.blocked_until - now)
            return False, f"Rate limit exceeded. Try again in {remaining} seconds."
        
        # Reset window if expired
        if now - limit_info.window_start > self.rate_window_seconds:
            limit_info.requests = 0
            limit_info.window_start = now
            limit_info.blocked_until = None
        
        # Check limit
        if limit_info.requests >= self.rate_limit:
            # Block for remaining window time
            limit_info.blocked_until = limit_info.window_start + self.rate_window_seconds
            remaining = int(limit_info.blocked_until - now)
            return False, f"Rate limit exceeded. Try again in {remaining} seconds."
        
        # Increment counter
        limit_info.requests += 1
        return True, None
    
    def get_session(self, token: str) -> Optional[Session]:
        """Get session information for a token."""
        return self.sessions.get(token)
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> list[Session]:
        """
        Get active sessions.
        
        Args:
            user_id: Filter by user ID (optional)
            
        Returns:
            List of active sessions
        """
        sessions = list(self.sessions.values())
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        # Filter expired sessions
        now = datetime.utcnow()
        return [s for s in sessions if s.expires_at > now]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions and tokens."""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if session.expires_at <= now
        ]
        
        for token in expired_tokens:
            del self.sessions[token]
            self.revoked_tokens.discard(token)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        return {
            "active_sessions": len(self.get_active_sessions()),
            "revoked_tokens": len(self.revoked_tokens),
            "rate_limited_identifiers": len([
                k for k, v in self.rate_limits.items()
                if v.blocked_until and time.time() < v.blocked_until
            ]),
            "total_rate_limit_entries": len(self.rate_limits),
        }


# Global instance
auth_manager = AuthManager()
