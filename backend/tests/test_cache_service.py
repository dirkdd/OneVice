"""
Test suite for OneVice Cache Service
Comprehensive tests for Redis caching functionality
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import redis.asyncio as redis

from app.services.cache_service import CacheService
from app.core.exceptions import CacheError, CacheConnectionError


class TestCacheService:
    """Test Redis cache service functionality"""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance"""
        return CacheService()
    
    @pytest.fixture
    def mock_redis_pool(self):
        """Create mock Redis connection pool"""
        pool_mock = Mock()
        redis_mock = Mock()
        redis_mock.get = AsyncMock()
        redis_mock.set = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.exists = AsyncMock()
        redis_mock.expire = AsyncMock()
        redis_mock.ttl = AsyncMock()
        redis_mock.incr = AsyncMock()
        redis_mock.decr = AsyncMock()
        redis_mock.sadd = AsyncMock()
        redis_mock.smembers = AsyncMock()
        redis_mock.srem = AsyncMock()
        redis_mock.hset = AsyncMock()
        redis_mock.hget = AsyncMock()
        redis_mock.hgetall = AsyncMock()
        redis_mock.hdel = AsyncMock()
        pool_mock.get_connection = AsyncMock(return_value=redis_mock)
        return pool_mock, redis_mock
    
    @pytest.mark.asyncio
    async def test_set_cache_success(self, cache_service):
        """Test successful cache set operation"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.set = AsyncMock(return_value=True)
            mock_client.return_value = mock_redis
            
            result = await cache_service.set("test_key", "test_value", ttl=300)
            
            # Verify Redis set operation
            mock_redis.set.assert_called_once_with(
                "test_key", 
                json.dumps("test_value"),
                ex=300
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_set_cache_with_complex_data(self, cache_service):
        """Test caching complex data structures"""
        
        complex_data = {
            "user_id": "user_123",
            "permissions": ["read", "write", "admin"],
            "metadata": {
                "last_login": "2024-01-15T10:30:00Z",
                "session_count": 5
            }
        }
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.set = AsyncMock(return_value=True)
            mock_client.return_value = mock_redis
            
            result = await cache_service.set("complex_data", complex_data, ttl=600)
            
            # Verify JSON serialization
            set_call = mock_redis.set.call_args
            stored_data = json.loads(set_call[0][1])
            assert stored_data["user_id"] == "user_123"
            assert len(stored_data["permissions"]) == 3
            assert stored_data["metadata"]["session_count"] == 5
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service):
        """Test successful cache retrieval"""
        
        stored_data = json.dumps({"message": "cached_value", "count": 42})
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.get = AsyncMock(return_value=stored_data.encode())
            mock_client.return_value = mock_redis
            
            result = await cache_service.get("test_key")
            
            # Verify Redis get operation
            mock_redis.get.assert_called_once_with("test_key")
            assert result["message"] == "cached_value"
            assert result["count"] == 42
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service):
        """Test cache miss scenario"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_client.return_value = mock_redis
            
            result = await cache_service.get("nonexistent_key")
            
            # Should return None for cache miss
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_service):
        """Test cache deletion"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.delete = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            result = await cache_service.delete("test_key")
            
            # Verify deletion
            mock_redis.delete.assert_called_once_with("test_key")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_cache_nonexistent(self, cache_service):
        """Test deleting nonexistent cache key"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.delete = AsyncMock(return_value=0)
            mock_client.return_value = mock_redis
            
            result = await cache_service.delete("nonexistent_key")
            
            # Should still return True (idempotent operation)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_cache(self, cache_service):
        """Test checking if cache key exists"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.exists = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            result = await cache_service.exists("test_key")
            
            mock_redis.exists.assert_called_once_with("test_key")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_expire_cache(self, cache_service):
        """Test setting cache expiration"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.expire = AsyncMock(return_value=True)
            mock_client.return_value = mock_redis
            
            result = await cache_service.expire("test_key", 600)
            
            mock_redis.expire.assert_called_once_with("test_key", 600)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_ttl_cache(self, cache_service):
        """Test getting cache TTL"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.ttl = AsyncMock(return_value=300)
            mock_client.return_value = mock_redis
            
            result = await cache_service.ttl("test_key")
            
            mock_redis.ttl.assert_called_once_with("test_key")
            assert result == 300
    
    @pytest.mark.asyncio
    async def test_increment_counter(self, cache_service):
        """Test incrementing cache counter"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.incr = AsyncMock(return_value=5)
            mock_client.return_value = mock_redis
            
            result = await cache_service.increment("counter_key", amount=2)
            
            mock_redis.incr.assert_called_once_with("counter_key", amount=2)
            assert result == 5
    
    @pytest.mark.asyncio
    async def test_decrement_counter(self, cache_service):
        """Test decrementing cache counter"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.decr = AsyncMock(return_value=3)
            mock_client.return_value = mock_redis
            
            result = await cache_service.decrement("counter_key", amount=1)
            
            mock_redis.decr.assert_called_once_with("counter_key", amount=1)
            assert result == 3


class TestCacheServiceSets:
    """Test Redis set operations for cache service"""
    
    @pytest.fixture
    def cache_service(self):
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_set_add(self, cache_service):
        """Test adding to Redis set"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.sadd = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            result = await cache_service.set_add("user_sessions:user_123", "session_456")
            
            mock_redis.sadd.assert_called_once_with("user_sessions:user_123", "session_456")
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_set_members(self, cache_service):
        """Test getting Redis set members"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.smembers = AsyncMock(return_value={b"session_1", b"session_2", b"session_3"})
            mock_client.return_value = mock_redis
            
            result = await cache_service.set_members("user_sessions:user_123")
            
            mock_redis.smembers.assert_called_once_with("user_sessions:user_123")
            assert result == {"session_1", "session_2", "session_3"}
    
    @pytest.mark.asyncio
    async def test_set_remove(self, cache_service):
        """Test removing from Redis set"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.srem = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            result = await cache_service.set_remove("user_sessions:user_123", "session_456")
            
            mock_redis.srem.assert_called_once_with("user_sessions:user_123", "session_456")
            assert result == 1


class TestCacheServiceHashes:
    """Test Redis hash operations for cache service"""
    
    @pytest.fixture
    def cache_service(self):
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_hash_set(self, cache_service):
        """Test setting Redis hash field"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.hset = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            result = await cache_service.hash_set("user:123", "email", "user@example.com")
            
            mock_redis.hset.assert_called_once_with("user:123", "email", "user@example.com")
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_hash_get(self, cache_service):
        """Test getting Redis hash field"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.hget = AsyncMock(return_value=b"user@example.com")
            mock_client.return_value = mock_redis
            
            result = await cache_service.hash_get("user:123", "email")
            
            mock_redis.hget.assert_called_once_with("user:123", "email")
            assert result == "user@example.com"
    
    @pytest.mark.asyncio
    async def test_hash_get_all(self, cache_service):
        """Test getting all Redis hash fields"""
        
        hash_data = {
            b"email": b"user@example.com",
            b"name": b"John Doe",
            b"role": b"Director"
        }
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.hgetall = AsyncMock(return_value=hash_data)
            mock_client.return_value = mock_redis
            
            result = await cache_service.hash_get_all("user:123")
            
            mock_redis.hgetall.assert_called_once_with("user:123")
            assert result["email"] == "user@example.com"
            assert result["name"] == "John Doe"
            assert result["role"] == "Director"
    
    @pytest.mark.asyncio
    async def test_hash_delete(self, cache_service):
        """Test deleting Redis hash field"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.hdel = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            result = await cache_service.hash_delete("user:123", "temp_field")
            
            mock_redis.hdel.assert_called_once_with("user:123", "temp_field")
            assert result == 1


class TestCacheServiceErrorHandling:
    """Test cache service error handling"""
    
    @pytest.fixture
    def cache_service(self):
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_connection_error(self, cache_service):
        """Test Redis connection error handling"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_client.side_effect = redis.ConnectionError("Redis server unavailable")
            
            with pytest.raises(CacheConnectionError):
                await cache_service.get("test_key")
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, cache_service):
        """Test Redis timeout error handling"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.get = AsyncMock(side_effect=redis.TimeoutError("Operation timed out"))
            mock_client.return_value = mock_redis
            
            with pytest.raises(CacheError):
                await cache_service.get("test_key")
    
    @pytest.mark.asyncio
    async def test_redis_error(self, cache_service):
        """Test general Redis error handling"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.set = AsyncMock(side_effect=redis.RedisError("Redis operation failed"))
            mock_client.return_value = mock_redis
            
            with pytest.raises(CacheError):
                await cache_service.set("test_key", "test_value")
    
    @pytest.mark.asyncio
    async def test_json_serialization_error(self, cache_service):
        """Test JSON serialization error handling"""
        
        # Create an object that can't be JSON serialized
        class UnserializableObject:
            def __init__(self):
                self.func = lambda x: x  # Functions can't be serialized
        
        unserializable = UnserializableObject()
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_client.return_value = mock_redis
            
            with pytest.raises(CacheError):
                await cache_service.set("test_key", unserializable)
    
    @pytest.mark.asyncio
    async def test_json_deserialization_error(self, cache_service):
        """Test JSON deserialization error handling"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.get = AsyncMock(return_value=b"invalid json data {")
            mock_client.return_value = mock_redis
            
            # Should return None for invalid JSON instead of raising error
            result = await cache_service.get("test_key")
            assert result is None


class TestCacheServiceIntegration:
    """Integration tests for cache service scenarios"""
    
    @pytest.fixture
    def cache_service(self):
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_user_session_management(self, cache_service):
        """Test complete user session management workflow"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock()
            mock_redis.sadd = AsyncMock(return_value=1)
            mock_redis.smembers = AsyncMock(return_value={b"session_1", b"session_2"})
            mock_redis.srem = AsyncMock(return_value=1)
            mock_redis.delete = AsyncMock(return_value=1)
            mock_client.return_value = mock_redis
            
            # 1. Store user session data
            session_data = {
                "user_id": "user_123",
                "login_time": "2024-01-15T10:00:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
            
            await cache_service.set("session:abc123", session_data, ttl=3600)
            
            # 2. Add session to user's active sessions set
            await cache_service.set_add("user_sessions:user_123", "session:abc123")
            
            # 3. Get all user sessions
            sessions = await cache_service.set_members("user_sessions:user_123")
            assert len(sessions) == 2
            
            # 4. Remove expired session
            await cache_service.set_remove("user_sessions:user_123", "session:abc123")
            await cache_service.delete("session:abc123")
            
            # Verify all operations were called
            mock_redis.set.assert_called()
            mock_redis.sadd.assert_called()
            mock_redis.smembers.assert_called()
            mock_redis.srem.assert_called()
            mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self, cache_service):
        """Test rate limiting implementation using cache"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.incr = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock(return_value=True)
            mock_redis.ttl = AsyncMock(return_value=3600)
            mock_client.return_value = mock_redis
            
            # Simulate rate limiting for API calls
            user_id = "user_123"
            rate_key = f"rate_limit:{user_id}:api_calls"
            
            # 1. Increment rate limit counter
            current_count = await cache_service.increment(rate_key)
            
            # 2. Set expiration on first call
            if current_count == 1:
                await cache_service.expire(rate_key, 3600)  # 1 hour window
            
            # 3. Check remaining TTL
            remaining_ttl = await cache_service.ttl(rate_key)
            
            # Verify operations
            mock_redis.incr.assert_called_with(rate_key, amount=1)
            mock_redis.expire.assert_called_with(rate_key, 3600)
            mock_redis.ttl.assert_called_with(rate_key)
            
            assert current_count == 1
            assert remaining_ttl == 3600
    
    @pytest.mark.asyncio
    async def test_permission_caching_workflow(self, cache_service):
        """Test permission caching workflow"""
        
        with patch('app.services.cache_service.get_redis_client') as mock_client:
            mock_redis = Mock()
            mock_redis.hset = AsyncMock(return_value=1)
            mock_redis.hget = AsyncMock(return_value=b'["read", "write", "admin"]')
            mock_redis.hdel = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock(return_value=True)
            mock_client.return_value = mock_redis
            
            user_id = "user_123"
            permissions_key = f"permissions:{user_id}"
            
            # 1. Cache user permissions
            permissions = ["read", "write", "admin"]
            await cache_service.hash_set(permissions_key, "data", json.dumps(permissions))
            await cache_service.expire(permissions_key, 1800)  # 30 minutes
            
            # 2. Retrieve cached permissions
            cached_data = await cache_service.hash_get(permissions_key, "data")
            cached_permissions = json.loads(cached_data)
            
            # 3. Invalidate cache on permission change
            await cache_service.hash_delete(permissions_key, "data")
            
            # Verify operations
            mock_redis.hset.assert_called_with(permissions_key, "data", json.dumps(permissions))
            mock_redis.expire.assert_called_with(permissions_key, 1800)
            mock_redis.hget.assert_called_with(permissions_key, "data")
            mock_redis.hdel.assert_called_with(permissions_key, "data")
            
            assert cached_permissions == ["read", "write", "admin"]