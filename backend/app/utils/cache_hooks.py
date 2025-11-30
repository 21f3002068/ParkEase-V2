"""
Cache Invalidation Hooks for Data Consistency
"""
from .cache import cache_invalidate_pattern, cache, cache_key_for_user, cache_key_for_lot, cache_key_for_admin

def invalidate_user_cache(user_id):
    """Invalidate all cache entries for a specific user"""
    patterns = [
        f"user:{user_id}:*",
        f"*user:{user_id}*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        deleted = cache_invalidate_pattern(pattern)
        total_deleted += deleted
    
    return total_deleted

def invalidate_lot_cache(lot_id):
    """Invalidate all cache entries for a specific parking lot"""
    patterns = [
        f"lot:{lot_id}:*",
        f"*lot:{lot_id}*",
        "available_lots",  # Invalidate general lots listing
        "admin_lots_summary"  # Invalidate admin summary
    ]
    
    total_deleted = 0
    for pattern in patterns:
        deleted = cache_invalidate_pattern(pattern)
        total_deleted += deleted
    
    return total_deleted

def invalidate_admin_cache():
    """Invalidate all admin-related cache entries"""
    patterns = [
        "admin:*",
        "*admin*",
        "available_lots",
        "admin_lots_summary"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        deleted = cache_invalidate_pattern(pattern)
        total_deleted += deleted
    
    return total_deleted

def invalidate_reservation_cache(reservation):
    """Invalidate cache when reservation changes"""
    total_deleted = 0
    
    # Invalidate user cache
    if hasattr(reservation, 'user_id') and reservation.user_id:
        total_deleted += invalidate_user_cache(reservation.user_id)
    
    # Invalidate lot cache
    if hasattr(reservation, 'spot') and reservation.spot and hasattr(reservation.spot, 'lot_id'):
        total_deleted += invalidate_lot_cache(reservation.spot.lot_id)
    
    # Invalidate admin cache
    total_deleted += invalidate_admin_cache()
    
    return total_deleted

def invalidate_spot_cache(spot):
    """Invalidate cache when parking spot changes"""
    total_deleted = 0
    
    # Invalidate lot cache
    if hasattr(spot, 'lot_id') and spot.lot_id:
        total_deleted += invalidate_lot_cache(spot.lot_id)
    
    # Invalidate admin cache
    total_deleted += invalidate_admin_cache()
    
    return total_deleted

def invalidate_all_cache():
    """Nuclear option - clear all cache"""
    return cache.clear_all()

# Cache warming functions
def warm_popular_caches():
    """Pre-populate frequently accessed cache entries"""
    try:
        # This would typically be called during off-peak hours
        # to pre-populate cache with commonly requested data
        
        from ..models import ParkingLot, User
        from .. import db
        
        # Warm up lots cache
        lots = db.session.query(ParkingLot).limit(10).all()  # Top 10 lots
        for lot in lots:
            cache_key = cache_key_for_lot(lot.id, "availability")
            # The actual data would be populated by the first request
            
        # Warm up active users cache
        active_users = db.session.query(User).limit(50).all()  # Top 50 active users
        for user in active_users:
            cache_key = cache_key_for_user(user.id, "dashboard")
            # The actual data would be populated by the first request
            
        return True
    except Exception as e:
        print(f"Cache warming error: {e}")
        return False