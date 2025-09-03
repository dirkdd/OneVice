"""
OneVice Authentication Models Tests

Unit tests for authentication models including:
- User roles and hierarchy validation
- Data sensitivity levels and access control
- Permission sets and validation
- Audit logging models
"""

import pytest
from datetime import datetime, timezone

from auth.models import (
    UserRole, DataSensitivity, PermissionAction, AuthUser, UserProfile,
    AuditLogEntry, AuditAction, AuthToken, SessionData, AuthContext,
    PermissionSet, get_role_permissions, ROLE_PERMISSIONS
)


class TestUserRole:
    """Test UserRole enum and hierarchy"""
    
    def test_role_values(self):
        """Test role numeric values for hierarchy"""
        assert UserRole.SALESPERSON.value == 1
        assert UserRole.CREATIVE_DIRECTOR.value == 2
        assert UserRole.DIRECTOR.value == 3
        assert UserRole.LEADERSHIP.value == 4
    
    def test_role_hierarchy(self):
        """Test role hierarchy access"""
        hierarchy = UserRole.get_hierarchy()
        
        # Leadership can access all roles
        assert "SALESPERSON" in hierarchy["LEADERSHIP"]
        assert "CREATIVE_DIRECTOR" in hierarchy["LEADERSHIP"]
        assert "DIRECTOR" in hierarchy["LEADERSHIP"]
        assert "LEADERSHIP" in hierarchy["LEADERSHIP"]
        
        # Director cannot access Leadership
        assert "LEADERSHIP" not in hierarchy["DIRECTOR"]
        assert "SALESPERSON" in hierarchy["DIRECTOR"]
        
        # Salesperson can only access own level
        assert hierarchy["SALESPERSON"] == ["SALESPERSON"]
    
    def test_has_role_access(self):
        """Test role access validation"""
        # Leadership can access all roles
        assert UserRole.has_role_access(UserRole.LEADERSHIP, UserRole.SALESPERSON)
        assert UserRole.has_role_access(UserRole.LEADERSHIP, UserRole.LEADERSHIP)
        
        # Director cannot access Leadership
        assert not UserRole.has_role_access(UserRole.DIRECTOR, UserRole.LEADERSHIP)
        assert UserRole.has_role_access(UserRole.DIRECTOR, UserRole.SALESPERSON)
        
        # Salesperson cannot access higher roles
        assert not UserRole.has_role_access(UserRole.SALESPERSON, UserRole.DIRECTOR)
        assert UserRole.has_role_access(UserRole.SALESPERSON, UserRole.SALESPERSON)
    
    def test_role_string_representation(self):
        """Test role string conversion"""
        assert str(UserRole.CREATIVE_DIRECTOR) == "Creative Director"
        assert str(UserRole.LEADERSHIP) == "Leadership"


class TestDataSensitivity:
    """Test DataSensitivity enum and access control"""
    
    def test_sensitivity_values(self):
        """Test data sensitivity numeric values"""
        assert DataSensitivity.PUBLIC.value == 1
        assert DataSensitivity.INTERNAL.value == 2
        assert DataSensitivity.CONFIDENTIAL.value == 3
        assert DataSensitivity.RESTRICTED.value == 4
        assert DataSensitivity.SECRET.value == 5
        assert DataSensitivity.TOP_SECRET.value == 6
    
    def test_access_matrix(self):
        """Test data access matrix for roles"""
        access_matrix = DataSensitivity.get_access_matrix()
        
        # Leadership has access to all levels
        leadership_access = access_matrix[UserRole.LEADERSHIP]
        assert DataSensitivity.TOP_SECRET in leadership_access
        assert DataSensitivity.PUBLIC in leadership_access
        
        # Salesperson has limited access
        sales_access = access_matrix[UserRole.SALESPERSON]
        assert DataSensitivity.PUBLIC in sales_access
        assert DataSensitivity.CONFIDENTIAL in sales_access
        assert DataSensitivity.SECRET not in sales_access
        assert DataSensitivity.TOP_SECRET not in sales_access
    
    def test_can_access_data(self):
        """Test data access validation"""
        # Leadership can access all data
        assert DataSensitivity.can_access_data(UserRole.LEADERSHIP, DataSensitivity.TOP_SECRET)
        assert DataSensitivity.can_access_data(UserRole.LEADERSHIP, DataSensitivity.PUBLIC)
        
        # Salesperson cannot access secret data
        assert not DataSensitivity.can_access_data(UserRole.SALESPERSON, DataSensitivity.SECRET)
        assert DataSensitivity.can_access_data(UserRole.SALESPERSON, DataSensitivity.CONFIDENTIAL)
        
        # Director cannot access top secret
        assert not DataSensitivity.can_access_data(UserRole.DIRECTOR, DataSensitivity.TOP_SECRET)
        assert DataSensitivity.can_access_data(UserRole.DIRECTOR, DataSensitivity.SECRET)


class TestPermissionSet:
    """Test PermissionSet functionality"""
    
    def test_permission_creation(self):
        """Test permission set creation"""
        actions = {PermissionAction.READ, PermissionAction.WRITE}
        data_level = DataSensitivity.CONFIDENTIAL
        
        perm_set = PermissionSet(
            actions=actions,
            data_access_level=data_level,
            context={"test": "value"}
        )
        
        assert perm_set.actions == actions
        assert perm_set.data_access_level == data_level
        assert perm_set.context["test"] == "value"
    
    def test_has_permission(self):
        """Test permission checking"""
        perm_set = PermissionSet(
            actions={PermissionAction.READ, PermissionAction.WRITE},
            data_access_level=DataSensitivity.CONFIDENTIAL
        )
        
        # Has action permission
        assert perm_set.has_permission(PermissionAction.READ)
        assert not perm_set.has_permission(PermissionAction.DELETE)
        
        # Has data access permission
        assert perm_set.has_permission(PermissionAction.READ, DataSensitivity.PUBLIC)
        assert perm_set.has_permission(PermissionAction.READ, DataSensitivity.CONFIDENTIAL)
        assert not perm_set.has_permission(PermissionAction.READ, DataSensitivity.SECRET)


class TestAuthUser:
    """Test AuthUser model"""
    
    def test_user_creation(self):
        """Test auth user creation"""
        permissions = get_role_permissions(UserRole.DIRECTOR)
        
        user = AuthUser(
            id="test-123",
            email="test@onevice.com",
            name="Test User",
            role=UserRole.DIRECTOR,
            permissions=permissions,
            provider="internal",
            provider_id="test-123"
        )
        
        assert user.id == "test-123"
        assert user.email == "test@onevice.com"
        assert user.role == UserRole.DIRECTOR
        assert user.is_active is True
    
    def test_user_permissions(self):
        """Test user permission checking"""
        permissions = get_role_permissions(UserRole.DIRECTOR)
        
        user = AuthUser(
            id="test-123",
            email="test@onevice.com", 
            name="Test User",
            role=UserRole.DIRECTOR,
            permissions=permissions,
            provider="internal",
            provider_id="test-123"
        )
        
        # Director should have read/write permissions
        assert user.has_permission(PermissionAction.READ)
        assert user.has_permission(PermissionAction.WRITE)
        
        # Director should not have system config permission
        assert not user.has_permission(PermissionAction.SYSTEM_CONFIG)
    
    def test_user_role_access(self):
        """Test user role access validation"""
        permissions = get_role_permissions(UserRole.DIRECTOR)
        
        user = AuthUser(
            id="test-123",
            email="test@onevice.com",
            name="Test User", 
            role=UserRole.DIRECTOR,
            permissions=permissions,
            provider="internal",
            provider_id="test-123"
        )
        
        # Director can access salesperson and creative director
        assert user.has_role_access(UserRole.SALESPERSON)
        assert user.has_role_access(UserRole.CREATIVE_DIRECTOR)
        assert user.has_role_access(UserRole.DIRECTOR)
        
        # Director cannot access leadership
        assert not user.has_role_access(UserRole.LEADERSHIP)
    
    def test_user_data_access(self):
        """Test user data access validation"""
        permissions = get_role_permissions(UserRole.CREATIVE_DIRECTOR)
        
        user = AuthUser(
            id="test-123",
            email="test@onevice.com",
            name="Test User",
            role=UserRole.CREATIVE_DIRECTOR,
            permissions=permissions,
            provider="internal", 
            provider_id="test-123"
        )
        
        # Creative Director can access up to restricted data
        assert user.can_access_data(DataSensitivity.PUBLIC)
        assert user.can_access_data(DataSensitivity.CONFIDENTIAL)
        assert user.can_access_data(DataSensitivity.RESTRICTED)
        
        # Creative Director cannot access secret data
        assert not user.can_access_data(DataSensitivity.SECRET)
        assert not user.can_access_data(DataSensitivity.TOP_SECRET)


class TestAuditLogEntry:
    """Test AuditLogEntry model"""
    
    def test_audit_log_creation(self):
        """Test audit log entry creation"""
        entry = AuditLogEntry(
            user_id="test-123",
            action=AuditAction.LOGIN_SUCCESS,
            resource="/auth/login",
            success=True,
            ip_address="192.168.1.100",
            details={"provider": "clerk"}
        )
        
        assert entry.user_id == "test-123"
        assert entry.action == AuditAction.LOGIN_SUCCESS
        assert entry.success is True
        assert entry.details["provider"] == "clerk"
        assert entry.id is not None  # UUID should be generated
        assert isinstance(entry.timestamp, datetime)
    
    def test_audit_log_with_risk_score(self):
        """Test audit log with risk assessment"""
        entry = AuditLogEntry(
            user_id="test-123",
            action=AuditAction.ACCESS_DENIED,
            resource="/admin/config",
            success=False,
            risk_score=0.8,
            details={"reason": "insufficient_permissions"}
        )
        
        assert entry.risk_score == 0.8
        assert entry.success is False
        assert entry.action == AuditAction.ACCESS_DENIED


class TestSessionData:
    """Test SessionData model"""
    
    def test_session_creation(self):
        """Test session data creation"""
        session = SessionData(
            user_id="test-123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        assert session.user_id == "test-123"
        assert session.ip_address == "192.168.1.100"
        assert session.session_id is not None  # UUID should be generated
        assert isinstance(session.created_at, datetime)
    
    def test_session_expiration(self):
        """Test session expiration logic"""
        # Non-expired session
        session = SessionData(
            user_id="test-123",
            expires_at=datetime.now(timezone.utc).replace(year=2030)  # Far future
        )
        assert not session.is_expired()
        
        # Expired session
        expired_session = SessionData(
            user_id="test-123", 
            expires_at=datetime.now(timezone.utc).replace(year=2020)  # Past
        )
        assert expired_session.is_expired()
        
        # Session without expiration
        no_expiry_session = SessionData(user_id="test-123")
        assert not no_expiry_session.is_expired()


class TestAuthContext:
    """Test AuthContext model"""
    
    def test_auth_context_creation(self):
        """Test authentication context creation"""
        permissions = get_role_permissions(UserRole.DIRECTOR)
        
        user = AuthUser(
            id="test-123",
            email="test@onevice.com",
            name="Test User",
            role=UserRole.DIRECTOR,
            permissions=permissions,
            provider="internal",
            provider_id="test-123"
        )
        
        session = SessionData(user_id=user.id)
        
        context = AuthContext(
            user=user,
            session=session,
            permissions=permissions,
            ip_address="192.168.1.100"
        )
        
        assert context.user == user
        assert context.session == session
        assert context.is_authenticated() is True
    
    def test_unauthenticated_context(self):
        """Test unauthenticated context"""
        context = AuthContext(
            ip_address="192.168.1.100",
            user_agent="test-client"
        )
        
        assert context.user is None
        assert context.is_authenticated() is False
        assert not context.has_permission(PermissionAction.READ)


class TestRolePermissions:
    """Test role permission mappings"""
    
    def test_role_permission_completeness(self):
        """Test that all roles have permission mappings"""
        for role in UserRole:
            assert role in ROLE_PERMISSIONS
            permissions = ROLE_PERMISSIONS[role]
            assert isinstance(permissions, set)
            assert len(permissions) > 0
    
    def test_leadership_has_all_permissions(self):
        """Test that leadership has all available permissions"""
        leadership_perms = ROLE_PERMISSIONS[UserRole.LEADERSHIP]
        
        # Leadership should have system config permissions
        assert PermissionAction.SYSTEM_CONFIG in leadership_perms
        assert PermissionAction.MANAGE_ROLES in leadership_perms
        assert PermissionAction.DELETE_USER in leadership_perms
    
    def test_salesperson_limited_permissions(self):
        """Test that salesperson has limited permissions"""
        sales_perms = ROLE_PERMISSIONS[UserRole.SALESPERSON]
        
        # Should have basic permissions
        assert PermissionAction.READ in sales_perms
        assert PermissionAction.ACCESS_AI_AGENTS in sales_perms
        
        # Should not have admin permissions
        assert PermissionAction.SYSTEM_CONFIG not in sales_perms
        assert PermissionAction.DELETE_USER not in sales_perms
        assert PermissionAction.MANAGE_ROLES not in sales_perms
    
    def test_get_role_permissions(self):
        """Test get_role_permissions function"""
        # Test with explicit data level
        perm_set = get_role_permissions(UserRole.DIRECTOR, DataSensitivity.CONFIDENTIAL)
        assert perm_set.data_access_level == DataSensitivity.CONFIDENTIAL
        assert PermissionAction.READ in perm_set.actions
        
        # Test with automatic data level
        perm_set_auto = get_role_permissions(UserRole.CREATIVE_DIRECTOR)
        assert perm_set_auto.data_access_level == DataSensitivity.RESTRICTED  # Max for creative director