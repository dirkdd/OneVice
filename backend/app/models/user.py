"""
OneVice User Models
SQLAlchemy models for user management with Clerk integration
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class SSOProvider(enum.Enum):
    """SSO Provider enumeration"""
    CLERK = "clerk"
    OKTA = "okta" 
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class User(Base):
    """
    User model with Clerk integration and OneVice-specific data
    Maps to frontend OneViceUser interface
    """
    __tablename__ = "users"

    # Primary identifier (matches Clerk user ID)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Clerk Integration
    clerk_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Basic User Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=True)
    image_url = Column(Text, nullable=True)
    
    # Status and Activity
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Organization Management
    organization_id = Column(UUID(as_uuid=True), nullable=True)  # For multi-tenancy
    organization_role = Column(String(100), nullable=True)  # Role within organization
    
    # SSO Configuration
    sso_provider = Column(SQLEnum(SSOProvider), nullable=True)
    sso_id = Column(String(255), nullable=True)
    
    # Relationships with auth models
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # Audit trail relationships
    audit_logs_as_actor = relationship("AuditLog", foreign_keys="AuditLog.actor_user_id", back_populates="actor_user")
    audit_logs_as_target = relationship("AuditLog", foreign_keys="AuditLog.target_user_id", back_populates="target_user")
    
    def __repr__(self):
        return f"<User {self.username or self.email}>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username or self.email
    
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        return self.full_name
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching frontend OneViceUser interface"""
        return {
            "id": str(self.id),
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name, 
            "username": self.username,
            "imageUrl": self.image_url or "",
            "isActive": self.is_active,
            "lastLoginAt": self.last_login_at,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "organizationId": str(self.organization_id) if self.organization_id else None,
            "organizationRole": self.organization_role,
            "ssoProvider": self.sso_provider.value if self.sso_provider else None,
            "ssoId": self.sso_id
        }