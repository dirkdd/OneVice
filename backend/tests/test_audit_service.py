"""
Test suite for OneVice Audit Service
Comprehensive tests for audit logging functionality
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.audit_service import AuditService, PermissionCacheService
from app.models.audit import AuditLog, AuditSummary
from app.models.auth import Role, Permission
from app.core.exceptions import DatabaseError


class TestAuditService:
    """Test audit logging service functionality"""
    
    @pytest.fixture
    def audit_service(self):
        """Create audit service instance with mocked dependencies"""
        return AuditService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.query = Mock()
        session.close = Mock()
        return session
    
    @pytest.fixture
    def sample_audit_data(self):
        """Sample audit log data for testing"""
        return {
            "user_id": "user_123",
            "action": "role_assigned",
            "resource_type": "user_role",
            "resource_id": "role_456",
            "details": "Assigned Salesperson role",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 Test",
            "correlation_id": "corr_789",
            "meta_data": {"role_name": "Salesperson", "assigned_by": "admin_001"}
        }
    
    @pytest.mark.asyncio
    async def test_log_user_action_success(self, audit_service, mock_db_session, sample_audit_data):
        """Test successful user action logging"""
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            result = await audit_service.log_user_action(**sample_audit_data)
            
            # Verify database operations
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            
            # Verify audit log creation
            audit_call = mock_db_session.add.call_args[0][0]
            assert isinstance(audit_call, AuditLog)
            assert audit_call.user_id == "user_123"
            assert audit_call.action == "role_assigned"
            assert audit_call.resource_type == "user_role"
            assert audit_call.ip_address == "192.168.1.100"
            
            # Verify return value
            assert result is True
    
    @pytest.mark.asyncio
    async def test_log_user_action_database_error(self, audit_service, mock_db_session, sample_audit_data):
        """Test audit logging with database error"""
        
        mock_db_session.commit.side_effect = Exception("Database connection failed")
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            result = await audit_service.log_user_action(**sample_audit_data)
            
            # Verify error handling
            mock_db_session.rollback.assert_called_once()
            mock_db_session.close.assert_called_once()
            
            # Should return False on error
            assert result is False
    
    @pytest.mark.asyncio
    async def test_log_security_event(self, audit_service, mock_db_session):
        """Test security event logging"""
        
        security_data = {
            "user_id": "user_456",
            "event_type": "failed_login_attempt",
            "severity": "HIGH",
            "description": "Multiple failed login attempts",
            "ip_address": "10.0.0.1",
            "user_agent": "Suspicious Bot",
            "meta_data": {"attempt_count": 5, "time_window": "5min"}
        }
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            result = await audit_service.log_security_event(**security_data)
            
            # Verify audit log creation
            mock_db_session.add.assert_called_once()
            audit_call = mock_db_session.add.call_args[0][0]
            assert audit_call.action == "security_event"
            assert audit_call.resource_type == "security"
            assert audit_call.severity == "HIGH"
            assert result is True
    
    @pytest.mark.asyncio
    async def test_log_admin_action(self, audit_service, mock_db_session):
        """Test administrative action logging"""
        
        admin_data = {
            "admin_id": "admin_123",
            "action": "user_role_modified",
            "target_user_id": "user_789",
            "details": "Changed role from Director to Creative Director",
            "ip_address": "172.16.0.1",
            "meta_data": {"old_role": "Director", "new_role": "Creative Director"}
        }
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            result = await audit_service.log_admin_action(**admin_data)
            
            # Verify audit log creation
            mock_db_session.add.assert_called_once()
            audit_call = mock_db_session.add.call_args[0][0]
            assert audit_call.user_id == "admin_123"
            assert audit_call.action == "user_role_modified"
            assert audit_call.resource_id == "user_789"
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_audit_logs(self, audit_service, mock_db_session):
        """Test retrieving user audit logs"""
        
        # Mock query results
        mock_logs = [
            AuditLog(
                id=1,
                user_id="user_123",
                action="login",
                timestamp=datetime.utcnow(),
                ip_address="192.168.1.1"
            ),
            AuditLog(
                id=2,
                user_id="user_123", 
                action="profile_update",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                ip_address="192.168.1.1"
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = mock_logs
        mock_db_session.query.return_value = mock_query
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            logs = await audit_service.get_user_audit_logs("user_123", limit=10, offset=0)
            
            # Verify query construction
            mock_db_session.query.assert_called_with(AuditLog)
            mock_query.filter.assert_called_once()
            mock_query.order_by.assert_called_once()
            mock_query.limit.assert_called_with(10)
            mock_query.offset.assert_called_with(0)
            
            # Verify results
            assert len(logs) == 2
            assert logs[0].action == "login"
            assert logs[1].action == "profile_update"
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_by_action(self, audit_service, mock_db_session):
        """Test retrieving audit logs by action type"""
        
        mock_logs = [
            AuditLog(id=1, action="role_assigned", user_id="user_1"),
            AuditLog(id=2, action="role_assigned", user_id="user_2")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_logs
        mock_db_session.query.return_value = mock_query
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            logs = await audit_service.get_audit_logs_by_action("role_assigned")
            
            assert len(logs) == 2
            assert all(log.action == "role_assigned" for log in logs)
    
    @pytest.mark.asyncio
    async def test_create_audit_summary(self, audit_service, mock_db_session):
        """Test creating audit summary"""
        
        summary_data = {
            "time_period": "daily",
            "start_date": datetime.utcnow() - timedelta(days=1),
            "end_date": datetime.utcnow(),
            "total_events": 150,
            "unique_users": 45,
            "top_actions": {"login": 80, "profile_update": 35, "role_assigned": 35},
            "security_events": 3
        }
        
        with patch('app.services.audit_service.get_db_session', return_value=mock_db_session):
            result = await audit_service.create_audit_summary(**summary_data)
            
            # Verify summary creation
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            
            summary_call = mock_db_session.add.call_args[0][0]
            assert isinstance(summary_call, AuditSummary)
            assert summary_call.time_period == "daily"
            assert summary_call.total_events == 150
            assert summary_call.unique_users == 45
            assert result is True


class TestPermissionCacheService:
    """Test permission caching service functionality"""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance"""
        return PermissionCacheService()
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        redis_mock = Mock()
        redis_mock.get = AsyncMock()
        redis_mock.set = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.exists = AsyncMock()
        redis_mock.expire = AsyncMock()
        return redis_mock
    
    @pytest.mark.asyncio
    async def test_cache_user_permissions(self, cache_service, mock_redis_client):
        """Test caching user permissions"""
        
        permissions = ["read_reports", "create_projects", "manage_users"]
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            result = await cache_service.cache_user_permissions("user_123", permissions)
            
            # Verify Redis operations
            mock_redis_client.set.assert_called_once()
            mock_redis_client.expire.assert_called_once()
            
            # Verify cache key and expiration
            set_call_args = mock_redis_client.set.call_args
            assert "permissions:user_123" in set_call_args[0][0]
            expire_call_args = mock_redis_client.expire.call_args
            assert expire_call_args[0][1] == 3600  # 1 hour TTL
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_cached_permissions_hit(self, cache_service, mock_redis_client):
        """Test retrieving cached permissions - cache hit"""
        
        cached_permissions = '["read_reports", "create_projects", "manage_users"]'
        mock_redis_client.get.return_value = cached_permissions.encode()
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            permissions = await cache_service.get_cached_permissions("user_123")
            
            # Verify Redis query
            mock_redis_client.get.assert_called_once()
            cache_key = mock_redis_client.get.call_args[0][0]
            assert "permissions:user_123" in cache_key
            
            # Verify parsed permissions
            assert permissions == ["read_reports", "create_projects", "manage_users"]
    
    @pytest.mark.asyncio
    async def test_get_cached_permissions_miss(self, cache_service, mock_redis_client):
        """Test retrieving cached permissions - cache miss"""
        
        mock_redis_client.get.return_value = None
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            permissions = await cache_service.get_cached_permissions("user_456")
            
            # Should return None for cache miss
            assert permissions is None
    
    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self, cache_service, mock_redis_client):
        """Test cache invalidation for user"""
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            result = await cache_service.invalidate_user_cache("user_789")
            
            # Verify cache deletion
            mock_redis_client.delete.assert_called_once()
            cache_key = mock_redis_client.delete.call_args[0][0]
            assert "permissions:user_789" in cache_key
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_cache_role_permissions(self, cache_service, mock_redis_client):
        """Test caching role permissions"""
        
        role_permissions = {
            "Salesperson": ["read_reports", "create_projects"],
            "Director": ["read_reports", "create_projects", "manage_team", "approve_budgets"]
        }
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            result = await cache_service.cache_role_permissions(role_permissions)
            
            # Should cache each role separately
            assert mock_redis_client.set.call_count == 2
            assert mock_redis_client.expire.call_count == 2
            assert result is True
    
    @pytest.mark.asyncio
    async def test_cache_service_error_handling(self, cache_service, mock_redis_client):
        """Test cache service error handling"""
        
        mock_redis_client.set.side_effect = Exception("Redis connection failed")
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            result = await cache_service.cache_user_permissions("user_error", ["permission1"])
            
            # Should gracefully handle Redis errors
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_permission_cached(self, cache_service, mock_redis_client):
        """Test checking if user has specific permission (cached)"""
        
        cached_permissions = '["read_reports", "create_projects", "manage_users"]'
        mock_redis_client.get.return_value = cached_permissions.encode()
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            # Test existing permission
            has_permission = await cache_service.user_has_permission("user_123", "read_reports")
            assert has_permission is True
            
            # Test non-existing permission
            has_permission = await cache_service.user_has_permission("user_123", "admin_access")
            assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_check_permission_uncached(self, cache_service, mock_redis_client):
        """Test checking permission when not cached"""
        
        mock_redis_client.get.return_value = None
        
        with patch('app.services.audit_service.get_redis_client', return_value=mock_redis_client):
            # Should return None when not cached (requires DB lookup)
            has_permission = await cache_service.user_has_permission("user_456", "read_reports")
            assert has_permission is None


class TestAuditServiceIntegration:
    """Integration tests for audit service with real scenarios"""
    
    @pytest.mark.asyncio
    async def test_role_assignment_audit_flow(self):
        """Test complete audit flow for role assignment"""
        
        audit_service = AuditService()
        
        # Mock database and Redis
        with patch('app.services.audit_service.get_db_session') as mock_db, \
             patch('app.services.audit_service.get_redis_client') as mock_redis:
            
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_db.return_value = mock_session
            
            # Test role assignment audit
            success = await audit_service.log_admin_action(
                admin_id="admin_001",
                action="role_assigned", 
                target_user_id="user_123",
                details="Assigned Director role to user",
                ip_address="10.0.0.1",
                meta_data={"role_name": "Director", "previous_role": "Salesperson"}
            )
            
            assert success is True
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_security_incident_audit_flow(self):
        """Test complete audit flow for security incident"""
        
        audit_service = AuditService()
        
        with patch('app.services.audit_service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_db.return_value = mock_session
            
            # Test security event logging
            success = await audit_service.log_security_event(
                user_id="user_suspicious",
                event_type="multiple_failed_logins",
                severity="HIGH",
                description="5 failed login attempts in 2 minutes",
                ip_address="203.0.113.1",
                user_agent="Unknown Bot",
                meta_data={
                    "attempt_count": 5,
                    "time_window": "2min",
                    "blocked": True
                }
            )
            
            assert success is True
            
            # Verify high-severity security event was logged
            audit_call = mock_session.add.call_args[0][0]
            assert audit_call.severity == "HIGH"
            assert audit_call.action == "security_event"
            assert "blocked" in audit_call.meta_data