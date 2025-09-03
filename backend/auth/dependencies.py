"""
OneVice FastAPI Authentication Dependencies

FastAPI dependency injection functions for:
- User authentication and authorization
- Role-based access control
- Permission checking with data sensitivity
- Request context management
- AI agent context integration
"""

from typing import Optional, List, Callable, Any
from functools import wraps

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import (
    AuthUser, AuthContext, UserRole, DataSensitivity, PermissionAction,
    AuditAction, AuditLogEntry
)
from .services import AuthenticationService, AuthorizationService, AuditService

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)

# Global service instances (would be properly initialized in main app)
_auth_service: Optional[AuthenticationService] = None
_authz_service: Optional[AuthorizationService] = None
_audit_service: Optional[AuditService] = None


def init_auth_dependencies(
    auth_service: AuthenticationService,
    authz_service: AuthorizationService,
    audit_service: AuditService
):
    """Initialize authentication dependencies with service instances"""
    global _auth_service, _authz_service, _audit_service
    _auth_service = auth_service
    _authz_service = authz_service
    _audit_service = audit_service


async def get_auth_context(request: Request) -> Optional[AuthContext]:
    """
    Get authentication context from request state
    
    This dependency extracts the auth context that was set by middleware.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AuthContext if available, None otherwise
    """
    
    return getattr(request.state, 'auth_context', None)


async def get_current_user(
    request: Request,
    auth_context: Optional[AuthContext] = Depends(get_auth_context)
) -> Optional[AuthUser]:
    """
    Get currently authenticated user
    
    This function now supports both the new Clerk middleware and the old
    auth context system for backward compatibility.
    
    Args:
        request: FastAPI request object
        auth_context: Authentication context from middleware (if available)
        
    Returns:
        AuthUser if authenticated, None otherwise
    """
    
    # First, try to get user from new Clerk middleware
    current_user = getattr(request.state, 'current_user', None)
    if current_user:
        return current_user
    
    # Fallback to old auth context system
    if not auth_context or not auth_context.is_authenticated():
        return None
    
    return auth_context.user


async def require_authenticated_user(
    current_user: Optional[AuthUser] = Depends(get_current_user)
) -> AuthUser:
    """
    Require authenticated user for endpoint access
    
    Args:
        current_user: Current user from authentication
        
    Returns:
        AuthUser if authenticated
        
    Raises:
        HTTPException: If user is not authenticated
    """
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return current_user


def require_role(required_role: UserRole) -> Callable:
    """
    Create dependency that requires specific user role or higher
    
    Args:
        required_role: Minimum required role level
        
    Returns:
        FastAPI dependency function
    """
    
    async def role_checker(
        current_user: AuthUser = Depends(require_authenticated_user)
    ) -> AuthUser:
        
        if not current_user.has_role_access(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role.name} or higher required"
            )
        
        return current_user
    
    return role_checker


def require_permission(
    action: PermissionAction,
    data_level: Optional[DataSensitivity] = None
) -> Callable:
    """
    Create dependency that requires specific permission
    
    Args:
        action: Required permission action
        data_level: Optional data sensitivity level requirement
        
    Returns:
        FastAPI dependency function
    """
    
    async def permission_checker(
        current_user: AuthUser = Depends(require_authenticated_user),
        auth_context: AuthContext = Depends(get_auth_context)
    ) -> AuthUser:
        
        if not auth_context.has_permission(action, data_level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {action.value} required"
            )
        
        return current_user
    
    return permission_checker


def require_data_access(sensitivity_level: DataSensitivity) -> Callable:
    """
    Create dependency that requires specific data access level
    
    Args:
        sensitivity_level: Required data sensitivity level
        
    Returns:
        FastAPI dependency function
    """
    
    async def data_access_checker(
        current_user: AuthUser = Depends(require_authenticated_user)
    ) -> AuthUser:
        
        if not current_user.can_access_data(sensitivity_level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to {sensitivity_level.name} data required"
            )
        
        return current_user
    
    return data_access_checker


# Pre-defined role dependencies
require_leadership = require_role(UserRole.LEADERSHIP)
require_director = require_role(UserRole.DIRECTOR)
require_creative_director = require_role(UserRole.CREATIVE_DIRECTOR)
require_salesperson = require_role(UserRole.SALESPERSON)

# Pre-defined permission dependencies
require_read_permission = require_permission(PermissionAction.READ)
require_write_permission = require_permission(PermissionAction.WRITE)
require_admin_permission = require_permission(PermissionAction.SYSTEM_CONFIG)
require_user_management = require_permission(PermissionAction.MANAGE_ROLES)
require_audit_access = require_permission(PermissionAction.VIEW_AUDIT_LOGS)
require_ai_access = require_permission(PermissionAction.ACCESS_AI_AGENTS)

# Pre-defined data access dependencies
require_public_access = require_data_access(DataSensitivity.PUBLIC)
require_internal_access = require_data_access(DataSensitivity.INTERNAL)
require_confidential_access = require_data_access(DataSensitivity.CONFIDENTIAL)
require_restricted_access = require_data_access(DataSensitivity.RESTRICTED)
require_secret_access = require_data_access(DataSensitivity.SECRET)
require_top_secret_access = require_data_access(DataSensitivity.TOP_SECRET)


async def get_filtered_data_access(
    current_user: AuthUser = Depends(require_authenticated_user)
) -> Callable:
    """
    Get data filtering function based on user's access level
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Function that can filter data based on user's access level
    """
    
    async def filter_data(data: List[dict], sensitivity_field: str = "sensitivity") -> List[dict]:
        """Filter data based on user's data access level"""
        
        if not _authz_service:
            return data
        
        return await _authz_service.filter_data_by_sensitivity(
            current_user, data, sensitivity_field
        )
    
    return filter_data


class AuthenticationRequired:
    """
    Decorator class for requiring authentication on functions
    
    Usage:
        @AuthenticationRequired()
        async def my_function(user: AuthUser):
            pass
    """
    
    def __init__(
        self,
        role: Optional[UserRole] = None,
        permission: Optional[PermissionAction] = None,
        data_level: Optional[DataSensitivity] = None
    ):
        self.role = role
        self.permission = permission
        self.data_level = data_level
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need to be properly implemented based on how the function is called
            # For now, this is a placeholder for the decorator pattern
            return await func(*args, **kwargs)
        
        return wrapper


async def log_api_access(
    request: Request,
    current_user: Optional[AuthUser] = Depends(get_current_user),
    auth_context: Optional[AuthContext] = Depends(get_auth_context)
) -> None:
    """
    Log API access for audit trail
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        auth_context: Authentication context
    """
    
    if not _audit_service:
        return
    
    # Determine action based on HTTP method
    action_map = {
        "GET": AuditAction.DATA_READ,
        "POST": AuditAction.DATA_WRITE,
        "PUT": AuditAction.DATA_UPDATE,
        "PATCH": AuditAction.DATA_UPDATE,
        "DELETE": AuditAction.DATA_DELETE
    }
    
    action = action_map.get(request.method, AuditAction.DATA_READ)
    
    # Determine data sensitivity based on path
    data_sensitivity = None
    if "/admin/" in str(request.url.path):
        data_sensitivity = DataSensitivity.SECRET
    elif "/users/" in str(request.url.path):
        data_sensitivity = DataSensitivity.CONFIDENTIAL
    elif "/reports/" in str(request.url.path):
        data_sensitivity = DataSensitivity.RESTRICTED
    
    audit_entry = AuditLogEntry(
        user_id=current_user.id if current_user else None,
        session_id=auth_context.session.session_id if auth_context and auth_context.session else None,
        action=action,
        resource=str(request.url.path),
        data_sensitivity=data_sensitivity,
        success=True,  # Will be updated later if needed
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": dict(request.query_params) if request.query_params else {}
        }
    )
    
    await _audit_service.log_event(audit_entry)


async def get_ai_agent_context(
    current_user: AuthUser = Depends(require_ai_access)
) -> dict:
    """
    Get AI agent context for current user
    
    Provides user context information for AI agents including:
    - User role and permissions
    - Data access levels
    - Organization context
    
    Args:
        current_user: Authenticated user with AI access
        
    Returns:
        Dictionary with AI agent context
    """
    
    return {
        "user_id": current_user.id,
        "user_email": current_user.email,
        "user_name": current_user.name,
        "user_role": current_user.role.name,
        "permissions": {
            "actions": [action.value for action in current_user.permissions.actions],
            "data_access_level": current_user.permissions.data_access_level.name,
        },
        "data_access": {
            "can_access_public": current_user.can_access_data(DataSensitivity.PUBLIC),
            "can_access_internal": current_user.can_access_data(DataSensitivity.INTERNAL),
            "can_access_confidential": current_user.can_access_data(DataSensitivity.CONFIDENTIAL),
            "can_access_restricted": current_user.can_access_data(DataSensitivity.RESTRICTED),
            "can_access_secret": current_user.can_access_data(DataSensitivity.SECRET),
            "can_access_top_secret": current_user.can_access_data(DataSensitivity.TOP_SECRET),
        },
        "context": {
            "provider": current_user.provider,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "session_active": current_user.session_id is not None,
        }
    }


# Composite dependencies for common use cases
async def require_user_management_access(
    current_user: AuthUser = Depends(require_user_management)
) -> AuthUser:
    """Require user management permissions (Director+)"""
    return current_user


async def require_admin_access(
    current_user: AuthUser = Depends(require_leadership)
) -> AuthUser:
    """Require administrative access (Leadership only)"""
    return current_user


async def require_reporting_access(
    current_user: AuthUser = Depends(require_permission(PermissionAction.VIEW_REPORTS))
) -> AuthUser:
    """Require reporting access permissions"""
    return current_user


async def require_confidential_data_access(
    current_user: AuthUser = Depends(require_confidential_access)
) -> AuthUser:
    """Require access to confidential data (Creative Director+)"""
    return current_user


# Context managers for specific business operations
class BusinessOperationContext:
    """Context manager for business operations with audit logging"""
    
    def __init__(self, operation_name: str, user: AuthUser):
        self.operation_name = operation_name
        self.user = user
        self.start_time = None
        self.success = False
    
    async def __aenter__(self):
        self.start_time = datetime.now()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if _audit_service:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.success = exc_type is None
            
            await _audit_service.log_event(
                AuditLogEntry(
                    user_id=self.user.id,
                    action=AuditAction.DATA_WRITE if self.success else AuditAction.SECURITY_VIOLATION,
                    resource=self.operation_name,
                    success=self.success,
                    details={
                        "operation": self.operation_name,
                        "duration_seconds": duration,
                        "error": str(exc_val) if exc_val else None
                    }
                )
            )


async def get_business_operation_context(
    operation_name: str,
    current_user: AuthUser = Depends(require_authenticated_user)
) -> BusinessOperationContext:
    """Get business operation context for audit logging"""
    return BusinessOperationContext(operation_name, current_user)