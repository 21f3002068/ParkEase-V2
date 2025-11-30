"""
Cache Middleware for Automatic Cache Invalidation
"""
from functools import wraps
from flask import request
from .cache_hooks import invalidate_user_cache, invalidate_lot_cache, invalidate_admin_cache, invalidate_reservation_cache

def auto_invalidate_cache(cache_type="general"):
    """
    Decorator to automatically invalidate cache after data modifications
    
    Args:
        cache_type (str): Type of cache to invalidate ('user', 'lot', 'admin', 'reservation')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Only invalidate cache on successful operations (2xx status codes)
            if hasattr(result, '__len__') and len(result) == 2:
                # Flask returns (data, status_code) tuple
                data, status_code = result
                if 200 <= status_code < 300:
                    _invalidate_cache_by_type(cache_type, args, kwargs)
            elif not hasattr(result, '__len__') or len(result) == 1:
                # Assume success if no status code provided
                _invalidate_cache_by_type(cache_type, args, kwargs)
            
            return result
        return wrapper
    return decorator

def _invalidate_cache_by_type(cache_type, args, kwargs):
    """Helper function to invalidate cache based on type"""
    try:
        if cache_type == "user":
            # Try to extract user_id from various sources
            user_id = _extract_user_id(args, kwargs)
            if user_id:
                invalidate_user_cache(user_id)
        
        elif cache_type == "lot":
            # Try to extract lot_id from various sources
            lot_id = _extract_lot_id(args, kwargs)
            if lot_id:
                invalidate_lot_cache(lot_id)
        
        elif cache_type == "admin":
            invalidate_admin_cache()
        
        elif cache_type == "reservation":
            # This would need the reservation object
            pass
        
        elif cache_type == "general":
            # Invalidate commonly affected caches
            invalidate_admin_cache()
            
    except Exception as e:
        print(f"Cache invalidation error: {e}")

def _extract_user_id(args, kwargs):
    """Extract user_id from function arguments"""
    # Check kwargs first
    if 'user_id' in kwargs:
        return kwargs['user_id']
    
    # Check URL parameters
    if hasattr(request, 'view_args') and request.view_args:
        if 'user_id' in request.view_args:
            return request.view_args['user_id']
    
    # Check if it's in args (positional arguments)
    if len(args) > 1 and isinstance(args[1], int):
        return args[1]
    
    return None

def _extract_lot_id(args, kwargs):
    """Extract lot_id from function arguments"""
    # Check kwargs first
    if 'lot_id' in kwargs:
        return kwargs['lot_id']
    
    # Check URL parameters
    if hasattr(request, 'view_args') and request.view_args:
        if 'lot_id' in request.view_args:
            return request.view_args['lot_id']
    
    # Check if it's in args (positional arguments)
    if len(args) > 1 and isinstance(args[1], int):
        return args[1]
    
    return None