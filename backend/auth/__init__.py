"""
OneVice Authentication Module

Comprehensive authentication and authorization system with:
- 4-tier role hierarchy (Leadership → Director → Salesperson/Creative Director)
- 6-level data sensitivity filtering system
- JWT validation with Clerk integration
- Okta SSO support
- RBAC permissions with data filtering
- Audit logging and compliance tracking
"""

from .models import (
    UserRole,
    DataSensitivity,
    PermissionAction,
    PermissionSet,
    AuthUser,
    UserProfile,
    AuditLogEntry,
    AuthToken,
    SessionData,
)

from .middleware import (
    JWTAuthenticationMiddleware,
    RBACMiddleware,
    AuditLoggingMiddleware,
    WebSocketAuthMiddleware,
)

from .services import (
    AuthenticationService,
    AuthorizationService,
    UserService,
    AuditService,
    ClerkIntegration,
    OktaIntegration,
)

from .dependencies import (
    get_current_user,
    require_role,
    require_permission,
    require_data_access,
    get_auth_context,
)

__all__ = [
    # Models
    "UserRole",
    "DataSensitivity", 
    "PermissionAction",
    "PermissionSet",
    "AuthUser",
    "UserProfile",
    "AuditLogEntry",
    "AuthToken",
    "SessionData",
    
    # Middleware
    "JWTAuthenticationMiddleware",
    "RBACMiddleware", 
    "AuditLoggingMiddleware",
    "WebSocketAuthMiddleware",
    
    # Services
    "AuthenticationService",
    "AuthorizationService",
    "UserService",
    "AuditService",
    "ClerkIntegration",
    "OktaIntegration",
    
    # Dependencies
    "get_current_user",
    "require_role",
    "require_permission",
    "require_data_access",
    "get_auth_context",
]