"""
OneVice RBAC Models
SQLAlchemy models for Role-Based Access Control
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)

class Role(Base):
    """
    Role model for RBAC system
    Matches frontend USER_ROLES constants
    """
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Role identification
    name = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "Leadership", "Director"
    slug = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "leadership", "director"
    description = Column(Text, nullable=True)
    
    # Hierarchy level (1=lowest, 4=highest)
    hierarchy_level = Column(Integer, nullable=False, default=1)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "hierarchyLevel": self.hierarchy_level,
            "isActive": self.is_active,
            "isSystem": self.is_system,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "permissions": [perm.slug for perm in self.permissions]
        }

class Permission(Base):
    """
    Permission model for granular access control
    Matches frontend PERMISSIONS constants
    """
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Permission identification
    name = Column(String(100), nullable=False)  # Human readable name
    slug = Column(String(100), unique=True, index=True, nullable=False)  # e.g., "agents:create"
    description = Column(Text, nullable=True)
    
    # Permission categorization
    resource = Column(String(50), nullable=False)  # e.g., "agents", "users", "system"
    action = Column(String(50), nullable=False)    # e.g., "create", "read", "update", "delete"
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System permissions cannot be deleted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission {self.slug}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "isActive": self.is_active,
            "isSystem": self.is_system,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }

class UserRole(Base):
    """
    User-Role assignment model
    Many-to-many relationship with additional metadata
    """
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    
    # Assignment metadata
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Who assigned this role
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional role expiration
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRole {self.user.email if self.user else 'Unknown'} -> {self.role.name if self.role else 'Unknown'}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "userId": str(self.user_id),
            "roleId": str(self.role_id),
            "roleName": self.role.name if self.role else None,
            "assignedBy": str(self.assigned_by) if self.assigned_by else None,
            "assignedAt": self.assigned_at,
            "expiresAt": self.expires_at,
            "isActive": self.is_active,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }

# Data sensitivity levels (matching frontend specifications)
class DataSensitivityLevel(Base):
    """
    Data sensitivity levels for RBAC filtering
    Matches frontend 6-level sensitivity system
    """
    __tablename__ = "data_sensitivity_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Sensitivity configuration
    name = Column(String(100), nullable=False)  # e.g., "Exact Budgets", "Contracts"
    slug = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "exact_budgets"
    level = Column(Integer, nullable=False)  # 1-6 (1=most sensitive)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color for UI
    
    # Required role level to access
    min_role_level = Column(Integer, nullable=False, default=1)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DataSensitivityLevel {self.name} (L{self.level})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "level": self.level,
            "description": self.description,
            "color": self.color,
            "minRoleLevel": self.min_role_level,
            "isActive": self.is_active,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }