"""
OneVice Permission Caching Service
Redis-based caching for user permissions and roles
High-performance RBAC with intelligent cache invalidation
"""

from typing import Optional, List, Dict, Any, Set
from datetime import timedelta
from app.core.redis import get_redis, cache_manager
from app.models.user import User
from app.models.auth import Role, Permission, UserRole
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

class PermissionCacheService:
    """High-performance permission caching with Redis"""
    
    def __init__(self):
        self.cache_prefix = "permissions"
        self.role_cache_prefix = "roles" 
        self.default_ttl = timedelta(minutes=15)  # 15 minute cache
        self.fast_ttl = timedelta(minutes=5)      # For frequently changing data
        
    # Cache Key Generators
    def _user_permissions_key(self, user_id: str) -> str:
        """Get cache key for user permissions"""
        return f"{self.cache_prefix}:user:{user_id}"
    
    def _user_roles_key(self, user_id: str) -> str:
        """Get cache key for user roles"""
        return f"{self.role_cache_prefix}:user:{user_id}"
    
    def _role_permissions_key(self, role_id: str) -> str:
        """Get cache key for role permissions"""
        return f"{self.cache_prefix}:role:{role_id}"
    
    def _permission_users_key(self, permission_slug: str) -> str:
        """Get cache key for users with specific permission"""
        return f"{self.cache_prefix}:permission:{permission_slug}:users"
    
    # User Permission Caching
    async def get_user_permissions(self, user_id: str) -> Optional[List[str]]:
        """Get cached user permissions"""
        try:
            redis_client = await get_redis()
            cache_key = self._user_permissions_key(user_id)
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                permissions = json.loads(cached_data)
                logger.debug(f"✅ Cache HIT: User {user_id} permissions ({len(permissions)} perms)")
                return permissions
            
            logger.debug(f"❌ Cache MISS: User {user_id} permissions")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get cached permissions for user {user_id}: {e}")
            return None
    
    async def set_user_permissions(self, user_id: str, permissions: List[str], ttl: Optional[timedelta] = None) -> bool:
        """Cache user permissions"""
        try:
            redis_client = await get_redis()
            cache_key = self._user_permissions_key(user_id)
            cache_ttl = ttl or self.default_ttl
            
            permissions_json = json.dumps(permissions)
            result = await redis_client.setex(cache_key, cache_ttl, permissions_json)
            
            if result:
                logger.info(f"✅ Cached permissions for user {user_id} ({len(permissions)} perms, TTL: {cache_ttl})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to cache permissions for user {user_id}: {e}")
            return False
    
    # User Role Caching
    async def get_user_roles(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached user roles"""
        try:
            redis_client = await get_redis()
            cache_key = self._user_roles_key(user_id)
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                roles = json.loads(cached_data)
                logger.debug(f"✅ Cache HIT: User {user_id} roles ({len(roles)} roles)")
                return roles
            
            logger.debug(f"❌ Cache MISS: User {user_id} roles")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get cached roles for user {user_id}: {e}")
            return None
    
    async def set_user_roles(self, user_id: str, roles: List[Dict[str, Any]], ttl: Optional[timedelta] = None) -> bool:
        """Cache user roles"""
        try:
            redis_client = await get_redis()
            cache_key = self._user_roles_key(user_id)
            cache_ttl = ttl or self.default_ttl
            
            roles_json = json.dumps(roles, default=str)  # Handle datetime serialization
            result = await redis_client.setex(cache_key, cache_ttl, roles_json)
            
            if result:
                logger.info(f"✅ Cached roles for user {user_id} ({len(roles)} roles, TTL: {cache_ttl})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to cache roles for user {user_id}: {e}")
            return False
    
    # Permission Checking with Cache
    async def has_permission_cached(self, user_id: str, permission_slug: str) -> Optional[bool]:
        """Check if user has permission using cache"""
        try:
            permissions = await self.get_user_permissions(user_id)
            if permissions is not None:
                has_perm = permission_slug in permissions
                logger.debug(f"🔍 Permission check (cached): {user_id} -> {permission_slug}: {has_perm}")
                return has_perm
            
            return None  # Cache miss, need to query database
            
        except Exception as e:
            logger.error(f"❌ Failed cached permission check for {user_id}: {e}")
            return None
    
    # Role Permission Caching
    async def get_role_permissions(self, role_id: str) -> Optional[List[str]]:
        """Get cached role permissions"""
        try:
            redis_client = await get_redis()
            cache_key = self._role_permissions_key(role_id)
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                permissions = json.loads(cached_data)
                logger.debug(f"✅ Cache HIT: Role {role_id} permissions ({len(permissions)} perms)")
                return permissions
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get cached role permissions for {role_id}: {e}")
            return None
    
    async def set_role_permissions(self, role_id: str, permissions: List[str], ttl: Optional[timedelta] = None) -> bool:
        """Cache role permissions"""
        try:
            redis_client = await get_redis()
            cache_key = self._role_permissions_key(role_id)
            cache_ttl = ttl or self.default_ttl
            
            permissions_json = json.dumps(permissions)
            result = await redis_client.setex(cache_key, cache_ttl, permissions_json)
            
            if result:
                logger.info(f"✅ Cached permissions for role {role_id} ({len(permissions)} perms)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to cache role permissions for {role_id}: {e}")
            return False
    
    # Cache Invalidation
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cache entries for a user"""
        try:
            redis_client = await get_redis()
            
            # Keys to invalidate
            keys_to_delete = [
                self._user_permissions_key(user_id),
                self._user_roles_key(user_id)
            ]
            
            deleted_count = 0
            for key in keys_to_delete:
                if await redis_client.delete(key):
                    deleted_count += 1
            
            logger.info(f"✅ Invalidated {deleted_count} cache entries for user {user_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to invalidate cache for user {user_id}: {e}")
            return False
    
    async def invalidate_role_cache(self, role_id: str) -> bool:
        """Invalidate cache entries for a role"""
        try:
            redis_client = await get_redis()
            
            # Invalidate role permissions
            role_key = self._role_permissions_key(role_id)
            result = await redis_client.delete(role_key)
            
            # Find and invalidate all users with this role
            # This is expensive but necessary for consistency
            pattern = f"{self.cache_prefix}:user:*"
            keys = await redis_client.keys(pattern)
            
            invalidated_users = 0
            for key in keys:
                if await redis_client.delete(key):
                    invalidated_users += 1
            
            logger.info(f"✅ Invalidated role {role_id} cache and {invalidated_users} user caches")
            return result or invalidated_users > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to invalidate role cache for {role_id}: {e}")
            return False
    
    async def invalidate_all_permissions(self) -> bool:
        """Invalidate all permission-related cache (use sparingly)"""
        try:
            redis_client = await get_redis()
            
            # Delete all permission and role cache keys
            patterns = [
                f"{self.cache_prefix}:*",
                f"{self.role_cache_prefix}:*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                keys = await redis_client.keys(pattern)
                if keys:
                    deleted = await redis_client.delete(*keys)
                    total_deleted += deleted
            
            logger.warning(f"🗑️ FULL CACHE INVALIDATION: Deleted {total_deleted} cache entries")
            return total_deleted > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to invalidate all permission cache: {e}")
            return False
    
    # Warm-up Cache
    async def warmup_user_cache(self, db: AsyncSession, user_id: str) -> bool:
        """Pre-populate cache for a user (useful after role changes)"""
        try:
            # Import here to avoid circular imports
            from app.services.auth_service import auth_service
            
            # Get fresh data from database
            permissions = await auth_service.get_user_permissions(db, user_id)
            roles = await auth_service.get_user_roles(db, user_id)
            
            # Cache the data
            perm_cached = await self.set_user_permissions(user_id, permissions)
            roles_cached = await self.set_user_roles(user_id, roles)
            
            if perm_cached and roles_cached:
                logger.info(f"🔥 Warmed up cache for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to warm up cache for user {user_id}: {e}")
            return False
    
    # Cache Statistics
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        try:
            redis_client = await get_redis()
            
            # Count cache entries by type
            permission_keys = await redis_client.keys(f"{self.cache_prefix}:*")
            role_keys = await redis_client.keys(f"{self.role_cache_prefix}:*")
            
            # Get Redis info
            redis_info = await redis_client.info('memory')
            
            stats = {
                "permission_cache_entries": len(permission_keys),
                "role_cache_entries": len(role_keys), 
                "total_cache_entries": len(permission_keys) + len(role_keys),
                "redis_memory_used": redis_info.get('used_memory_human', 'unknown'),
                "cache_ttl_seconds": int(self.default_ttl.total_seconds()),
                "cache_hit_efficiency": "tracked_separately"  # Would need separate metrics
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {"error": str(e)}

# Global cache service instance
permission_cache = PermissionCacheService()

# Convenience functions for easy integration
async def get_cached_user_permissions(user_id: str) -> Optional[List[str]]:
    """Convenience function to get cached user permissions"""
    return await permission_cache.get_user_permissions(user_id)

async def cache_user_permissions(user_id: str, permissions: List[str]) -> bool:
    """Convenience function to cache user permissions"""
    return await permission_cache.set_user_permissions(user_id, permissions)

async def invalidate_user_permissions(user_id: str) -> bool:
    """Convenience function to invalidate user permission cache"""
    return await permission_cache.invalidate_user_cache(user_id)

async def has_cached_permission(user_id: str, permission_slug: str) -> Optional[bool]:
    """Convenience function for cached permission checking"""
    return await permission_cache.has_permission_cached(user_id, permission_slug)