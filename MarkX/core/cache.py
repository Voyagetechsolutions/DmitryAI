# core/cache.py
"""
LLM Response Caching System
"""

import json
import hashlib
import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CacheEntry:
    response: dict
    timestamp: float
    hit_count: int = 0


class LLMCache:
    def __init__(self, cache_file: str = "memory/llm_cache.json", ttl: int = 3600):
        self.cache_file = cache_file
        self.ttl = ttl  # Time to live in seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.load_cache()
    
    def _hash_request(self, user_text: str, context: dict = None) -> str:
        """Create hash key for request"""
        data = {
            "text": user_text.strip().lower(),
            "context": context or {}
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def get(self, user_text: str, context: dict = None) -> Optional[dict]:
        """Get cached response if available and fresh"""
        key = self._hash_request(user_text, context)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() - entry.timestamp > self.ttl:
                del self.cache[key]
                return None
            
            # Update hit count
            entry.hit_count += 1
            return entry.response
        
        return None
    
    def set(self, user_text: str, response: dict, context: dict = None):
        """Cache response"""
        key = self._hash_request(user_text, context)
        
        self.cache[key] = CacheEntry(
            response=response,
            timestamp=time.time(),
            hit_count=0
        )
        
        # Cleanup old entries
        self._cleanup()
        self.save_cache()
    
    def _cleanup(self):
        """Remove expired and least used entries"""
        now = time.time()
        
        # Remove expired
        expired_keys = [k for k, v in self.cache.items() if now - v.timestamp > self.ttl]
        for key in expired_keys:
            del self.cache[key]
        
        # Keep only top 100 by hit count if too many
        if len(self.cache) > 100:
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1].hit_count, reverse=True)
            self.cache = dict(sorted_items[:100])
    
    def save_cache(self):
        """Save cache to disk"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Convert to serializable format
        data = {}
        for key, entry in self.cache.items():
            data[key] = {
                "response": entry.response,
                "timestamp": entry.timestamp,
                "hit_count": entry.hit_count
            }
        
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_cache(self):
        """Load cache from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                
                for key, entry_data in data.items():
                    self.cache[key] = CacheEntry(
                        response=entry_data["response"],
                        timestamp=entry_data["timestamp"],
                        hit_count=entry_data.get("hit_count", 0)
                    )
            except:
                pass  # Start fresh if corrupted
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
    
    def stats(self) -> dict:
        """Get cache statistics"""
        total_entries = len(self.cache)
        total_hits = sum(entry.hit_count for entry in self.cache.values())
        
        return {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "hit_rate": total_hits / max(total_entries, 1),
            "cache_size_mb": os.path.getsize(self.cache_file) / 1024 / 1024 if os.path.exists(self.cache_file) else 0
        }


# Global instance
llm_cache = LLMCache()