"""
OneVice Admin API Tests
Comprehensive tests for admin role management endpoints
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import uuid

from app.main import app
from app.services.auth_service import auth_service
from app.models.user import User
from app.models.auth import Role, UserRole
from app.core.exceptions import UserNotFoundError, RoleNotFoundError


class TestAdminRoleAssignment:
    """Test role assignment functionality"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        return User(
            id=uuid.uuid4(),
            clerk_id="user_test123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_active=True
        )
    
    @pytest.fixture
    def mock_role(self):
        """Mock role for testing"""
        return Role(
            id=uuid.uuid4(),
            name="Director",
            slug="director",
            hierarchy_level=3,
            is_active=True
        )
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for testing"""
        return User(
            id=uuid.uuid4(),
            clerk_id="admin_test123",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            is_active=True
        )
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    @patch('app.services.auth_service.auth_service.get_user_with_roles')
    @patch('app.services.auth_service.auth_service.get_user_roles')
    def test_assign_role_success(
        self, mock_get_roles, mock_get_user, mock_require_perm, 
        mock_get_current, client, mock_user, mock_role, mock_admin_user
    ):
        """Test successful role assignment"""
        # Mock dependencies
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        mock_get_user.return_value = mock_user
        mock_get_roles.return_value = []  # User has no roles initially
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock role lookup
            mock_db_session.get.return_value = mock_role
            
            # Mock audit service
            with patch('app.services.audit_service.audit_service.log_role_assignment') as mock_audit:
                mock_audit.return_value = True
                
                # Test request
                response = client.post(
                    f"/api/v1/admin/users/{mock_user.id}/roles",
                    json={
                        "role_id": str(mock_role.id),
                        "reason": "Promotion to Director"
                    },
                    headers={"Authorization": "Bearer test_token"}
                )
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["success"] == True
        assert response_data["message"] == "Role assigned successfully"
        assert response_data["assignment"]["role_name"] == "Director"
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    def test_assign_role_user_not_found(
        self, mock_require_perm, mock_get_current, client, mock_admin_user
    ):
        """Test role assignment with non-existent user"""
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock user not found
            mock_db_session.get.return_value = None
            
            fake_user_id = str(uuid.uuid4())
            response = client.post(
                f"/api/v1/admin/users/{fake_user_id}/roles",
                json={
                    "role_id": str(uuid.uuid4()),
                    "reason": "Test assignment"
                },
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 404
        response_data = response.json()
        assert "User not found" in response_data["error"]["message"]
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    @patch('app.services.auth_service.auth_service.get_user_with_roles')
    @patch('app.services.auth_service.auth_service.get_user_roles')
    def test_assign_role_already_has_role(
        self, mock_get_roles, mock_get_user, mock_require_perm, 
        mock_get_current, client, mock_user, mock_role, mock_admin_user
    ):
        """Test assigning role that user already has"""
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        mock_get_user.return_value = mock_user
        
        # User already has the role
        mock_get_roles.return_value = [{
            "id": str(mock_role.id),
            "name": "Director",
            "slug": "director"
        }]
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            mock_db_session.get.return_value = mock_role
            
            response = client.post(
                f"/api/v1/admin/users/{mock_user.id}/roles",
                json={
                    "role_id": str(mock_role.id),
                    "reason": "Test assignment"
                },
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 409
        response_data = response.json()
        assert "already has the role" in response_data["error"]["message"]


class TestAdminRoleRemoval:
    """Test role removal functionality"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_role(self):
        """Mock user role for testing"""
        return UserRole(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            is_active=True,
            assigned_at=datetime.now(timezone.utc)
        )
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    def test_remove_role_success(
        self, mock_require_perm, mock_get_current, client, mock_user_role
    ):
        """Test successful role removal"""
        mock_admin_user = User(
            id=uuid.uuid4(),
            clerk_id="admin_test",
            email="admin@test.com"
        )
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock finding the user role
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user_role
            
            # Mock role for audit logging
            mock_role = Role(name="Director", slug="director")
            mock_user_role.role = mock_role
            
            with patch('app.services.audit_service.audit_service.log_role_removal') as mock_audit:
                mock_audit.return_value = True
                
                response = client.delete(
                    f"/api/v1/admin/users/{mock_user_role.user_id}/roles/{mock_user_role.role_id}",
                    json={"reason": "Role restructuring"},
                    headers={"Authorization": "Bearer test_token"}
                )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        assert response_data["message"] == "Role removed successfully"
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    def test_remove_role_not_found(
        self, mock_require_perm, mock_get_current, client
    ):
        """Test removing non-existent role assignment"""
        mock_admin_user = User(id=uuid.uuid4(), clerk_id="admin_test", email="admin@test.com")
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock role assignment not found
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
            
            fake_user_id = str(uuid.uuid4())
            fake_role_id = str(uuid.uuid4())
            
            response = client.delete(
                f"/api/v1/admin/users/{fake_user_id}/roles/{fake_role_id}",
                json={"reason": "Test removal"},
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 404
        response_data = response.json()
        assert "Role assignment not found" in response_data["error"]["message"]


class TestAdminRoleQueries:
    """Test role query endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    @patch('app.services.auth_service.auth_service.get_user_roles')
    @patch('app.services.auth_service.auth_service.get_user_permissions')
    @patch('app.services.auth_service.auth_service.get_highest_role_level')
    def test_get_user_roles_success(
        self, mock_get_level, mock_get_permissions, mock_get_roles,
        mock_require_perm, mock_get_current, client
    ):
        """Test successful user roles retrieval"""
        mock_admin_user = User(id=uuid.uuid4(), clerk_id="admin_test", email="admin@test.com")
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        # Mock return data
        mock_roles = [{
            "id": str(uuid.uuid4()),
            "name": "Director",
            "slug": "director",
            "hierarchyLevel": 3,
            "assignedAt": datetime.now(timezone.utc),
            "permissions": ["users:read", "agents:create"]
        }]
        mock_permissions = ["users:read", "agents:create", "agents:update"]
        
        mock_get_roles.return_value = mock_roles
        mock_get_permissions.return_value = mock_permissions
        mock_get_level.return_value = 3
        
        test_user_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/admin/users/{test_user_id}/roles",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["user_id"] == test_user_id
        assert len(response_data["roles"]) == 1
        assert response_data["roles"][0]["name"] == "Director"
        assert response_data["highest_role_level"] == 3
        assert "users:read" in response_data["effective_permissions"]
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    def test_get_all_roles_success(self, mock_require_perm, mock_get_current, client):
        """Test successful retrieval of all system roles"""
        mock_admin_user = User(id=uuid.uuid4(), clerk_id="admin_test", email="admin@test.com")
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock roles data
            mock_roles = [
                Role(
                    id=uuid.uuid4(),
                    name="Leadership",
                    slug="leadership",
                    hierarchy_level=4,
                    description="Full system access",
                    is_active=True,
                    is_system=True,
                    permissions=[]
                ),
                Role(
                    id=uuid.uuid4(),
                    name="Director",
                    slug="director",
                    hierarchy_level=3,
                    description="Department management",
                    is_active=True,
                    is_system=True,
                    permissions=[]
                )
            ]
            
            mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_roles
            
            response = client.get(
                "/api/v1/admin/roles",
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        response_data = response.json()
        assert "roles" in response_data
        assert len(response_data["roles"]) == 2
        assert response_data["roles"][0]["name"] == "Leadership"
        assert response_data["roles"][1]["name"] == "Director"


class TestAdminAuditLogs:
    """Test audit log retrieval"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    def test_get_audit_logs_success(self, mock_require_perm, mock_get_current, client):
        """Test successful audit logs retrieval"""
        mock_admin_user = User(id=uuid.uuid4(), clerk_id="admin_test", email="admin@test.com")
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock audit logs
            from app.models.audit import AuditLog
            mock_logs = [
                AuditLog(
                    id=uuid.uuid4(),
                    action="ROLE_ASSIGNED",
                    description="Role 'Director' assigned to user@example.com",
                    severity="MEDIUM",
                    actor_user_id=uuid.uuid4(),
                    actor_email="admin@example.com",
                    target_user_id=uuid.uuid4(),
                    success=True,
                    created_at=datetime.now(timezone.utc)
                )
            ]
            
            # Mock the query chain
            mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_logs
            
            response = client.get(
                "/api/v1/admin/audit/logs?page=1&limit=50",
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        response_data = response.json()
        assert "logs" in response_data
        assert "pagination" in response_data
        assert len(response_data["logs"]) == 1
        assert response_data["logs"][0]["action"] == "ROLE_ASSIGNED"
    
    @patch('app.api.admin.get_current_user')
    @patch('app.api.admin.require_permission')
    def test_get_audit_logs_with_filters(self, mock_require_perm, mock_get_current, client):
        """Test audit logs retrieval with filters"""
        mock_admin_user = User(id=uuid.uuid4(), clerk_id="admin_test", email="admin@test.com")
        mock_get_current.return_value = mock_admin_user
        mock_require_perm.return_value = None
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            # Mock empty results for filtered query
            mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
            
            response = client.get(
                "/api/v1/admin/audit/logs?action=ROLE_ASSIGNED&severity=MEDIUM&page=1&limit=10",
                headers={"Authorization": "Bearer test_token"}
            )
        
        assert response.status_code == 200
        response_data = response.json()
        assert "logs" in response_data
        assert "pagination" in response_data


class TestAdminPermissions:
    """Test admin permission requirements"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    def test_assign_role_without_permission(self, client):
        """Test role assignment without proper permissions"""
        with patch('app.api.admin.get_current_user') as mock_get_current:
            mock_user = User(id=uuid.uuid4(), clerk_id="user_test", email="user@test.com")
            mock_get_current.return_value = mock_user
            
            with patch('app.api.admin.require_permission') as mock_require_perm:
                from app.core.exceptions import AuthorizationError
                mock_require_perm.side_effect = AuthorizationError(
                    "Insufficient permissions",
                    required_permission="users:manage_roles"
                )
                
                response = client.post(
                    f"/api/v1/admin/users/{uuid.uuid4()}/roles",
                    json={"role_id": str(uuid.uuid4())},
                    headers={"Authorization": "Bearer test_token"}
                )
        
        assert response.status_code == 403
        response_data = response.json()
        assert "Insufficient permissions" in response_data["error"]["message"]
    
    def test_get_audit_logs_without_admin_permission(self, client):
        """Test audit logs access without system admin permission"""
        with patch('app.api.admin.get_current_user') as mock_get_current:
            mock_user = User(id=uuid.uuid4(), clerk_id="user_test", email="user@test.com")
            mock_get_current.return_value = mock_user
            
            with patch('app.api.admin.require_permission') as mock_require_perm:
                from app.core.exceptions import AuthorizationError
                mock_require_perm.side_effect = AuthorizationError(
                    "Insufficient permissions",
                    required_permission="system:admin"
                )
                
                response = client.get(
                    "/api/v1/admin/audit/logs",
                    headers={"Authorization": "Bearer test_token"}
                )
        
        assert response.status_code == 403
        response_data = response.json()
        assert "Insufficient permissions" in response_data["error"]["message"]