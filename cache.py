"""
Simple caching system for Market Pulse with bounded size and LRU eviction.
Prevents unbounded memory growth from long-running operations.
"""

import time
from functools import wraps
from typing import Any, Dict, Optional
import threading
from collections import OrderedDict


class BoundedCache:
    """Thread-safe cache with LRU eviction and TTL.
    
    Prevents memory exhaustion by:
    - Limiting maximum cache size (evicts oldest on overflow)
    - Supporting TTL for automatic expiration
    - Periodically cleaning expired entries
    """
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 3600):
        """Initialize bounded cache.
        
        Args:
            max_size: Maximum number of entries before LRU eviction
            cleanup_interval: Seconds between expired entry cleanup
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Returns None if key doesn't exist or is expired.
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            # Check if expired
            if time.time() - entry['timestamp'] > entry['ttl']:
                del self.cache[key]
                return None
            
            # Move to end (most recent - LRU)
            self.cache.move_to_end(key)
            return entry['result']
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self.lock:
            # Remove if exists
            if key in self.cache:
                del self.cache[key]
            
            # Add new entry
            self.cache[key] = {
                'result': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            
            # Evict oldest if over capacity
            if len(self.cache) > self.max_size:
                oldest_key, _ = self.cache.popitem(last=False)
                # Could optionally log: f"Cache evicted oldest entry: {oldest_key}"
            
            # Periodic cleanup of expired entries
            if time.time() - self.last_cleanup > self.cleanup_interval:
                self._cleanup_expired()
    
    def _cleanup_expired(self):
        """Remove expired entries from cache.
        
        Called periodically to prevent memory accumulation
        of expired but not-yet-accessed entries.
        """
        current_time = time.time()
        expired_keys = [
            k for k, v in self.cache.items()
            if current_time - v['timestamp'] > v['ttl']
        ]
        for k in expired_keys:
            del self.cache[k]
        self.last_cleanup = current_time
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'usage_percent': (len(self.cache) / self.max_size * 100) if self.max_size > 0 else 0,
                'sample_keys': list(self.cache.keys())[:10]
            }


# Global cache instance with 1000 entry limit
_bounded_cache = BoundedCache(max_size=1000)


def cache_result(ttl_seconds: int = 300):
    """Decorator to cache function results with TTL and LRU eviction.
    
    Args:
        ttl_seconds: Time to live for cached result
        
    Usage:
        @cache_result(ttl_seconds=600)
        def expensive_function(arg1, arg2):
            return compute_result()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = _bounded_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result and cache it
            result = func(*args, **kwargs)
            _bounded_cache.set(cache_key, result, ttl=ttl_seconds)
            
            return result
        return wrapper
    return decorator


def clear_cache():
    """Clear all cached results."""
    _bounded_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring and debugging."""
    return _bounded_cache.get_stats()
