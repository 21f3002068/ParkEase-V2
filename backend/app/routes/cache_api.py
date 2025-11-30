"""
Cache Management API Routes
"""
from flask import request, jsonify
from flask_security import auth_required, roles_required
from flask_restx import Namespace, Resource
from ..utils.cache import cache, cache_invalidate_pattern

cache_ns = Namespace('cache', description='Cache management operations')

@cache_ns.route('/stats')
class CacheStats(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get cache statistics"""
        try:
            info = cache.redis_client.info()
            stats = {
                "redis_version": info.get('redis_version'),
                "used_memory": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "total_commands_processed": info.get('total_commands_processed'),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": 0
            }
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            if hits + misses > 0:
                stats['hit_rate'] = round((hits / (hits + misses)) * 100, 2)
            
            return stats
        except Exception as e:
            return {"error": f"Failed to get cache stats: {str(e)}"}, 500

@cache_ns.route('/clear')
class CacheClear(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Clear all cache"""
        try:
            cache.clear_all()
            return {"message": "Cache cleared successfully"}
        except Exception as e:
            return {"error": f"Failed to clear cache: {str(e)}"}, 500

@cache_ns.route('/invalidate')
class CacheInvalidate(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Invalidate cache by pattern"""
        data = request.get_json()
        pattern = data.get('pattern', '')
        
        if not pattern:
            return {"error": "Pattern is required"}, 400
        
        try:
            deleted_count = cache_invalidate_pattern(pattern)
            return {
                "message": f"Invalidated {deleted_count} cache entries",
                "pattern": pattern
            }
        except Exception as e:
            return {"error": f"Failed to invalidate cache: {str(e)}"}, 500

@cache_ns.route('/keys')
class CacheKeys(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get all cache keys (for debugging)"""
        try:
            keys = cache.redis_client.keys('cache:*')
            return {
                "total_keys": len(keys),
                "keys": [key.decode() if isinstance(key, bytes) else key for key in keys[:50]]  # Limit to 50 for performance
            }
        except Exception as e:
            return {"error": f"Failed to get cache keys: {str(e)}"}, 500