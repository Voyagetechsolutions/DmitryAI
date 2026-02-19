"""
Simple cache for Platform API responses.

Provides graceful degradation when Platform is unavailable.
"""

import time
from typing import Any, Optional, Dict
from threading import Lock


class SimpleCache:
    """
    Thread-safe in-memory cache with TTL.
    
    Used to cache Platform API responses for graceful degradation.
    """
    
    def __init__(self, ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() - entry["timestamp"] > self.ttl:
                del self._cache[key]
                return None
            
            return entry["value"]
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = {
                "value": value,
                "timestamp": time.time()
            }
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time - entry["timestamp"] > self.ttl
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for entry in self._cache.values()
                if current_time - entry["timestamp"] > self.ttl
            )
            
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "active_entries": len(self._cache) - expired_count,
                "ttl": self.ttl
            }
