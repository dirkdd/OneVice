"""
OneVice Redis Configuration
Session management and caching with Redis
"""

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError
from app.core.config import settings
import json
import logging
import asyncio
from typing import Optional, Any, Dict
from datetime import timedelta
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Redis client instance
redis_client: Optional[redis.Redis] = None

def redis_retry(max_attempts=3, delay=1):
    """Decorator to retry Redis operations on connection failures"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Redis operation failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

async def init_redis() -> None:
    """Initialize Redis connection with enhanced pooling"""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,  # Increased from 20
            socket_keepalive=True,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 5,  # TCP_KEEPCNT
            },
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError],
            health_check_interval=30
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("✅ Redis connection established with enhanced pooling")
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

async def close_redis() -> None:
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("✅ Redis connection closed")

async def get_redis() -> redis.Redis:
    """Get Redis client instance with auto-reconnection"""
    global redis_client
    if redis_client is None:
        await init_redis()
    
    # Validate connection and reconnect if needed
    try:
        await redis_client.ping()
    except (ConnectionError, TimeoutError):
        logger.warning("Redis connection lost, reconnecting...")
        await init_redis()
    
    return redis_client

class SessionManager:
    """Redis-based session management"""
    
    def __init__(self, prefix: str = "session"):
        self.prefix = prefix
        self.default_ttl = timedelta(hours=24)  # 24 hour session expiry
    
    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"{self.prefix}:{session_id}"
    
    @redis_retry(max_attempts=3, delay=1)
    async def create_session(self, session_id: str, user_data: Dict[str, Any], ttl: Optional[timedelta] = None) -> bool:
        """Create a new session"""
        try:
            redis_instance = await get_redis()
            key = self._get_key(session_id)
            data = json.dumps(user_data, default=str)
            
            expire_time = ttl or self.default_ttl
            result = await redis_instance.setex(key, expire_time, data)
            
            logger.info(f"✅ Session created: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to create session {session_id}: {e}")
            return False
    
    @redis_retry(max_attempts=3, delay=1)
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            redis_instance = await get_redis()
            key = self._get_key(session_id)
            data = await redis_instance.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get session {session_id}: {e}")
            return None
    
    @redis_retry(max_attempts=3, delay=1)
    async def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """Update existing session data"""
        try:
            redis_instance = await get_redis()
            key = self._get_key(session_id)
            
            # Check if session exists
            if not await redis_instance.exists(key):
                logger.warning(f"Session {session_id} does not exist")
                return False
            
            # Get current TTL and preserve it
            ttl = await redis_instance.ttl(key)
            data = json.dumps(user_data, default=str)
            
            if ttl > 0:
                await redis_instance.setex(key, ttl, data)
            else:
                await redis_instance.set(key, data)
            
            logger.info(f"✅ Session updated: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update session {session_id}: {e}")
            return False
    
    @redis_retry(max_attempts=3, delay=1)
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            redis_instance = await get_redis()
            key = self._get_key(session_id)
            result = await redis_instance.delete(key)
            
            if result:
                logger.info(f"✅ Session deleted: {session_id}")
            else:
                logger.warning(f"Session {session_id} was not found")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"❌ Failed to delete session {session_id}: {e}")
            return False
    
    async def refresh_session(self, session_id: str, ttl: Optional[timedelta] = None) -> bool:
        """Refresh session TTL"""
        try:
            redis_instance = await get_redis()
            key = self._get_key(session_id)
            
            if not await redis_instance.exists(key):
                return False
            
            expire_time = ttl or self.default_ttl
            result = await redis_instance.expire(key, expire_time)
            
            if result:
                logger.info(f"✅ Session refreshed: {session_id}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh session {session_id}: {e}")
            return False

class CacheManager:
    """Redis-based caching for API responses and data"""
    
    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix
        self.default_ttl = timedelta(minutes=15)  # 15 minute cache by default
    
    def _get_key(self, cache_key: str) -> str:
        """Get Redis key for cache"""
        return f"{self.prefix}:{cache_key}"
    
    @redis_retry(max_attempts=3, delay=1)
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set cached value"""
        try:
            redis_instance = await get_redis()
            cache_key = self._get_key(key)
            data = json.dumps(value, default=str)
            
            expire_time = ttl or self.default_ttl
            result = await redis_instance.setex(cache_key, expire_time, data)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Cache set failed for {key}: {e}")
            return False
    
    @redis_retry(max_attempts=3, delay=1)
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            redis_instance = await get_redis()
            cache_key = self._get_key(key)
            data = await redis_instance.get(cache_key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Cache get failed for {key}: {e}")
            return None
    
    @redis_retry(max_attempts=3, delay=1)
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            redis_instance = await get_redis()
            cache_key = self._get_key(key)
            result = await redis_instance.delete(cache_key)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"❌ Cache delete failed for {key}: {e}")
            return False

# Global instances
session_manager = SessionManager()
cache_manager = CacheManager()

# Redis health check
async def health_check():
    """Check Redis health status"""
    try:
        if redis_client:
            await redis_client.ping()
            return {
                "redis": "healthy",
                "connection": "active"
            }
        else:
            return {
                "redis": "unhealthy",
                "connection": "not_initialized"
            }
    except Exception as e:
        return {
            "redis": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }