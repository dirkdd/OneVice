"""
OneVice Authentication Models

Comprehensive data models for authentication, authorization, and audit logging.
Supports 4-tier role hierarchy and 6-level data sensitivity system.
"""

import uuid
from enum import Enum, IntEnum
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Union, Any
from pydantic import BaseModel, Field, EmailStr, validator
from dataclasses import dataclass


class UserRole(IntEnum):
    """
    4-tier hierarchical role system for OneVice platform
    
    Higher values indicate higher privilege levels.
    Role hierarchy determines data access and system permissions.
    """
    
    SALESPERSON = 1
    CREATIVE_DIRECTOR = 2  # Same level as salesperson but different permissions
    DIRECTOR = 3
    LEADERSHIP = 4
    
    @classmethod
    def get_hierarchy(cls) -> Dict[str, List[str]]:
        """Get role hierarchy mapping for access control"""
        return {
            "LEADERSHIP": ["LEADERSHIP", "DIRECTOR", "CREATIVE_DIRECTOR", "SALESPERSON"],
            "DIRECTOR": ["DIRECTOR", "CREATIVE_DIRECTOR", "SALESPERSON"], 
            "CREATIVE_DIRECTOR": ["CREATIVE_DIRECTOR", "SALESPERSON"],
            "SALESPERSON": ["SALESPERSON"],
        }
    
    @classmethod
    def has_role_access(cls, user_role: "UserRole", required_role: "UserRole") -> bool:
        """Check if user role has access to required role level"""
        hierarchy = cls.get_hierarchy()
        user_role_name = user_role.name
        required_role_name = required_role.name
        
        return required_role_name in hierarchy.get(user_role_name, [])
    
    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class DataSensitivity(IntEnum):
    """
    6-level data sensitivity classification system
    
    Controls data access based on sensitivity levels.
    Higher values indicate more sensitive data.
    """
    
    PUBLIC = 1           # Public information, no restrictions
    INTERNAL = 2         # Internal company information
    CONFIDENTIAL = 3     # Confidential business data
    RESTRICTED = 4       # Restricted access data
    SECRET = 5           # Secret/highly sensitive data
    TOP_SECRET = 6       # Top secret/maximum security data
    
    @classmethod
    def get_access_matrix(cls) -> Dict[UserRole, List["DataSensitivity"]]:
        """Get data access matrix for role-based filtering"""
        return {
            UserRole.LEADERSHIP: [cls.PUBLIC, cls.INTERNAL, cls.CONFIDENTIAL, 
                                 cls.RESTRICTED, cls.SECRET, cls.TOP_SECRET],
            UserRole.DIRECTOR: [cls.PUBLIC, cls.INTERNAL, cls.CONFIDENTIAL, 
                               cls.RESTRICTED, cls.SECRET],
            UserRole.CREATIVE_DIRECTOR: [cls.PUBLIC, cls.INTERNAL, cls.CONFIDENTIAL, 
                                       cls.RESTRICTED],
            UserRole.SALESPERSON: [cls.PUBLIC, cls.INTERNAL, cls.CONFIDENTIAL],
        }
    
    @classmethod
    def can_access_data(cls, user_role: UserRole, data_sensitivity: "DataSensitivity") -> bool:
        """Check if user role can access data at given sensitivity level"""
        access_matrix = cls.get_access_matrix()
        allowed_levels = access_matrix.get(user_role, [])
        return data_sensitivity in allowed_levels
    
    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class PermissionAction(str, Enum):
    """
    System permission actions for granular access control
    """
    
    # Data operations
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    
    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user" 
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"
    
    # System administration
    MANAGE_ROLES = "manage_roles"
    MANAGE_PERMISSIONS = "manage_permissions"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    SYSTEM_CONFIG = "system_config"
    
    # Business operations
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    MANAGE_PROJECTS = "manage_projects"
    APPROVE_TRANSACTIONS = "approve_transactions"
    
    # AI and automation
    ACCESS_AI_AGENTS = "access_ai_agents"
    CONFIGURE_AI = "configure_ai"
    VIEW_AI_LOGS = "view_ai_logs"


class AuthProvider(str, Enum):
    """Authentication providers supported by the system"""
    
    CLERK = "clerk"
    OKTA = "okta"
    INTERNAL = "internal"


@dataclass
class PermissionSet:
    """
    Collection of permissions with context
    """
    
    actions: Set[PermissionAction]
    data_access_level: DataSensitivity
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
    
    def has_permission(self, action: PermissionAction, data_level: Optional[DataSensitivity] = None) -> bool:
        """Check if permission set includes specific action and data access"""
        has_action = action in self.actions
        
        if data_level is None:
            return has_action
            
        has_data_access = data_level.value <= self.data_access_level.value
        return has_action and has_data_access


class AuthUser(BaseModel):
    """
    Authenticated user model with role and permission context
    """
    
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="Full name")
    role: UserRole = Field(..., description="User role in hierarchy")
    permissions: PermissionSet = Field(..., description="User permission set")
    provider: AuthProvider = Field(..., description="Authentication provider")
    provider_id: str = Field(..., description="Provider-specific user ID")
    is_active: bool = Field(default=True, description="User account status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    session_id: Optional[str] = Field(None, description="Current session ID")
    
    class Config:
        use_enum_values = False  # Keep enums as enum objects, not values
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PermissionSet: lambda v: {
                "actions": [action.value for action in v.actions],
                "data_access_level": v.data_access_level.value,
                "context": v.context
            }
        }
    
    @validator('permissions', pre=True)
    def validate_permissions(cls, v):
        if isinstance(v, dict):
            actions = {PermissionAction(action) for action in v.get('actions', [])}
            data_level = DataSensitivity(v.get('data_access_level', 1))
            context = v.get('context', {})
            return PermissionSet(actions=actions, data_access_level=data_level, context=context)
        return v
    
    def has_role_access(self, required_role: UserRole) -> bool:
        """Check if user has access to required role level"""
        return UserRole.has_role_access(self.role, required_role)
    
    def has_permission(self, action: PermissionAction, data_level: Optional[DataSensitivity] = None) -> bool:
        """Check if user has specific permission"""
        return self.permissions.has_permission(action, data_level)
    
    def can_access_data(self, sensitivity: DataSensitivity) -> bool:
        """Check if user can access data at given sensitivity level"""
        return DataSensitivity.can_access_data(self.role, sensitivity)


class UserProfile(BaseModel):
    """
    Extended user profile with additional attributes for OneVice platform
    """
    
    user_id: str = Field(..., description="User ID reference")
    department: Optional[str] = Field(None, description="User department")
    title: Optional[str] = Field(None, description="Job title")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Office location")
    timezone: str = Field(default="UTC", description="User timezone")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AuthToken(BaseModel):
    """
    JWT token model with validation and metadata
    """
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    scope: List[str] = Field(default_factory=list, description="Token scope")
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SessionData(BaseModel):
    """
    User session data for state management
    """
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    expires_at: Optional[datetime] = Field(None, description="Session expiration")
    data: Dict[str, Any] = Field(default_factory=dict, description="Session data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class AuditAction(str, Enum):
    """Audit log action types for compliance tracking"""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # Authorization events  
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_CHANGED = "role_changed"
    
    # Data access events
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # System events
    CONFIG_CHANGE = "config_change"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    
    # Security events
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditLogEntry(BaseModel):
    """
    Comprehensive audit log entry for compliance and security monitoring
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = Field(None, description="User who performed action")
    session_id: Optional[str] = Field(None, description="Session ID")
    action: AuditAction = Field(..., description="Action performed")
    resource: Optional[str] = Field(None, description="Resource accessed/modified")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    data_sensitivity: Optional[DataSensitivity] = Field(None, description="Data sensitivity level")
    success: bool = Field(..., description="Whether action succeeded")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    risk_score: Optional[float] = Field(None, description="Risk assessment score")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AuthContext(BaseModel):
    """
    Authentication context for request processing
    """
    
    user: Optional[AuthUser] = Field(None, description="Authenticated user")
    session: Optional[SessionData] = Field(None, description="Session data") 
    permissions: Optional[PermissionSet] = Field(None, description="Effective permissions")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: Optional[str] = Field(None, description="Request IP address")
    user_agent: Optional[str] = Field(None, description="Request user agent")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    def is_authenticated(self) -> bool:
        """Check if context represents authenticated user"""
        return self.user is not None and self.user.is_active
    
    def has_permission(self, action: PermissionAction, data_level: Optional[DataSensitivity] = None) -> bool:
        """Check permission through context"""
        if not self.is_authenticated() or self.permissions is None:
            return False
        return self.permissions.has_permission(action, data_level)


# Permission mappings for different roles
ROLE_PERMISSIONS: Dict[UserRole, Set[PermissionAction]] = {
    UserRole.LEADERSHIP: {
        PermissionAction.READ, PermissionAction.WRITE, PermissionAction.UPDATE, PermissionAction.DELETE,
        PermissionAction.CREATE_USER, PermissionAction.UPDATE_USER, PermissionAction.DELETE_USER, PermissionAction.VIEW_USERS,
        PermissionAction.MANAGE_ROLES, PermissionAction.MANAGE_PERMISSIONS, PermissionAction.VIEW_AUDIT_LOGS, PermissionAction.SYSTEM_CONFIG,
        PermissionAction.VIEW_REPORTS, PermissionAction.EXPORT_DATA, PermissionAction.MANAGE_PROJECTS, PermissionAction.APPROVE_TRANSACTIONS,
        PermissionAction.ACCESS_AI_AGENTS, PermissionAction.CONFIGURE_AI, PermissionAction.VIEW_AI_LOGS,
    },
    UserRole.DIRECTOR: {
        PermissionAction.READ, PermissionAction.WRITE, PermissionAction.UPDATE,
        PermissionAction.UPDATE_USER, PermissionAction.VIEW_USERS,
        PermissionAction.VIEW_AUDIT_LOGS,
        PermissionAction.VIEW_REPORTS, PermissionAction.EXPORT_DATA, PermissionAction.MANAGE_PROJECTS, PermissionAction.APPROVE_TRANSACTIONS,
        PermissionAction.ACCESS_AI_AGENTS, PermissionAction.VIEW_AI_LOGS,
    },
    UserRole.CREATIVE_DIRECTOR: {
        PermissionAction.READ, PermissionAction.WRITE, PermissionAction.UPDATE,
        PermissionAction.VIEW_USERS,
        PermissionAction.VIEW_REPORTS, PermissionAction.MANAGE_PROJECTS,
        PermissionAction.ACCESS_AI_AGENTS,
    },
    UserRole.SALESPERSON: {
        PermissionAction.READ, PermissionAction.WRITE, PermissionAction.UPDATE,
        PermissionAction.VIEW_REPORTS,
        PermissionAction.ACCESS_AI_AGENTS,
    },
}


def get_role_permissions(role: UserRole, data_access_level: Optional[DataSensitivity] = None) -> PermissionSet:
    """
    Get permission set for a given role
    
    Args:
        role: User role
        data_access_level: Optional data access level override
        
    Returns:
        PermissionSet for the role
    """
    
    actions = ROLE_PERMISSIONS.get(role, set())
    
    if data_access_level is None:
        # Use maximum data access level for the role
        access_matrix = DataSensitivity.get_access_matrix()
        allowed_levels = access_matrix.get(role, [DataSensitivity.PUBLIC])
        data_access_level = max(allowed_levels) if allowed_levels else DataSensitivity.PUBLIC
    
    return PermissionSet(
        actions=actions,
        data_access_level=data_access_level,
        context={"role": role.name}
    )