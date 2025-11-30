"""
Redis Cache Utility for API Performance
"""
import redis
import json
import pickle
from functools import wraps
from datetime import datetime, timedelta
from flask import current_app, request
import hashlib

class RedisCache:
    def __init__(self, redis_url='redis://localhost:6379/1'):
        """Initialize Redis cache with separate database for caching"""
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=False)
        self.redis_json = redis.Redis.from_url(redis_url, decode_responses=True)
    
    def _generate_cache_key(self, prefix, *args, **kwargs):
        """Generate unique cache key from function arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get(self, key):
        """Get value from cache"""
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key, value, expiry=300):
        """Set value in cache with expiry (default 5 minutes)"""
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, expiry, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern):
        """Delete all keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0
    
    def clear_all(self):
        """Clear all cache"""
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

# Global cache instance
cache = RedisCache()

def cached(expiry=300, key_prefix=None):
    """
    Decorator for caching function results
    
    Args:
        expiry (int): Cache expiry time in seconds (default 5 minutes)
        key_prefix (str): Custom prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = cache._generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                print(f"Cache HIT: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            print(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expiry)
            
            return result
        return wrapper
    return decorator

def cache_invalidate_pattern(pattern):
    """Invalidate cache entries matching pattern"""
    return cache.delete_pattern(f"cache:*{pattern}*")

def cache_key_for_user(user_id, endpoint):
    """Generate cache key for user-specific data"""
    return f"user:{user_id}:{endpoint}"

def cache_key_for_admin(endpoint):
    """Generate cache key for admin data"""
    return f"admin:{endpoint}"

def cache_key_for_lot(lot_id, endpoint):
    """Generate cache key for parking lot data"""
    return f"lot:{lot_id}:{endpoint}"