"""
OneVice Audit Logging Models
SQLAlchemy models for comprehensive audit trail tracking
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class AuditAction(enum.Enum):
    """Audit action types for RBAC operations"""
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DEACTIVATED = "user_deactivated"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHECKED = "permission_checked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    PERMISSION_CREATED = "permission_created"
    PERMISSION_UPDATED = "permission_updated"
    PERMISSION_DELETED = "permission_deleted"

class AuditSeverity(enum.Enum):
    """Audit severity levels"""
    LOW = "low"           # Normal operations (login, permission checks)
    MEDIUM = "medium"     # Administrative changes (role assignments)
    HIGH = "high"         # Critical changes (role deletion, user deactivation)
    CRITICAL = "critical" # Security events (unauthorized access)

class AuditLog(Base):
    """
    Comprehensive audit logging for all RBAC operations
    Tracks who did what, when, where, and why
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Action Information
    action = Column(String(50), nullable=False, index=True)  # AuditAction enum value
    severity = Column(String(20), nullable=False, default="medium", index=True)  # AuditSeverity enum value
    description = Column(Text, nullable=False)  # Human-readable description
    
    # Actor Information (who performed the action)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)  # Cached for performance
    actor_ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 support
    actor_user_agent = Column(Text, nullable=True)
    
    # Target Information (what was acted upon)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    target_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    target_permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=True)
    target_resource = Column(String(100), nullable=True)  # e.g., "user", "role", "permission"
    target_resource_id = Column(String(255), nullable=True)  # Generic resource identifier
    
    # Context Information
    request_method = Column(String(10), nullable=True)  # HTTP method
    request_path = Column(String(500), nullable=True)   # API endpoint
    request_query = Column(Text, nullable=True)         # Query parameters
    session_id = Column(String(255), nullable=True, index=True)  # User session
    
    # Change Details
    old_values = Column(JSON, nullable=True)  # Before state
    new_values = Column(JSON, nullable=True)  # After state
    meta_data = Column(JSON, nullable=True)    # Additional context
    
    # Status and Outcome
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    actor_user = relationship("User", foreign_keys=[actor_user_id], back_populates="audit_logs_as_actor")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="audit_logs_as_target")
    target_role = relationship("Role", foreign_keys=[target_role_id])
    target_permission = relationship("Permission", foreign_keys=[target_permission_id])
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.actor_email or 'system'} at {self.created_at}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "action": self.action,
            "severity": self.severity,
            "description": self.description,
            "actorUserId": str(self.actor_user_id) if self.actor_user_id else None,
            "actorEmail": self.actor_email,
            "actorIpAddress": self.actor_ip_address,
            "targetUserId": str(self.target_user_id) if self.target_user_id else None,
            "targetRoleId": str(self.target_role_id) if self.target_role_id else None,
            "targetPermissionId": str(self.target_permission_id) if self.target_permission_id else None,
            "targetResource": self.target_resource,
            "targetResourceId": self.target_resource_id,
            "requestMethod": self.request_method,
            "requestPath": self.request_path,
            "sessionId": self.session_id,
            "oldValues": self.old_values,
            "newValues": self.new_values,
            "metadata": self.meta_data,
            "success": self.success,
            "errorMessage": self.error_message,
            "createdAt": self.created_at
        }
    
    @classmethod
    def create_log(
        cls,
        action: str,
        description: str,
        severity: str = "medium",
        actor_user_id: str = None,
        actor_email: str = None,
        actor_ip: str = None,
        actor_user_agent: str = None,
        target_user_id: str = None,
        target_role_id: str = None,
        target_permission_id: str = None,
        target_resource: str = None,
        target_resource_id: str = None,
        request_method: str = None,
        request_path: str = None,
        request_query: str = None,
        session_id: str = None,
        old_values: dict = None,
        new_values: dict = None,
        meta_data: dict = None,
        success: bool = True,
        error_message: str = None
    ) -> "AuditLog":
        """Factory method to create audit log entries"""
        return cls(
            action=action,
            description=description,
            severity=severity,
            actor_user_id=uuid.UUID(actor_user_id) if actor_user_id else None,
            actor_email=actor_email,
            actor_ip_address=actor_ip,
            actor_user_agent=actor_user_agent,
            target_user_id=uuid.UUID(target_user_id) if target_user_id else None,
            target_role_id=uuid.UUID(target_role_id) if target_role_id else None,
            target_permission_id=uuid.UUID(target_permission_id) if target_permission_id else None,
            target_resource=target_resource,
            target_resource_id=target_resource_id,
            request_method=request_method,
            request_path=request_path,
            request_query=request_query,
            session_id=session_id,
            old_values=old_values,
            new_values=new_values,
            meta_data=meta_data,
            success=success,
            error_message=error_message
        )

class AuditSummary(Base):
    """
    Daily audit summary for reporting and monitoring
    Aggregates audit logs for performance and overview
    """
    __tablename__ = "audit_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Summary Period
    summary_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Counts by Action
    role_assignments = Column(Integer, default=0)
    role_removals = Column(Integer, default=0)
    permission_checks = Column(Integer, default=0)
    user_logins = Column(Integer, default=0)
    unauthorized_attempts = Column(Integer, default=0)
    
    # Counts by Severity
    low_severity_count = Column(Integer, default=0)
    medium_severity_count = Column(Integer, default=0)
    high_severity_count = Column(Integer, default=0)
    critical_severity_count = Column(Integer, default=0)
    
    # Top Actors (JSON array of user IDs)
    top_actors = Column(JSON, nullable=True)
    
    # Alert Indicators
    has_critical_events = Column(Boolean, default=False)
    has_suspicious_activity = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditSummary {self.summary_date.date()} - {self.role_assignments} role changes>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "summaryDate": self.summary_date,
            "roleAssignments": self.role_assignments,
            "roleRemovals": self.role_removals,
            "permissionChecks": self.permission_checks,
            "userLogins": self.user_logins,
            "unauthorizedAttempts": self.unauthorized_attempts,
            "lowSeverityCount": self.low_severity_count,
            "mediumSeverityCount": self.medium_severity_count,
            "highSeverityCount": self.high_severity_count,
            "criticalSeverityCount": self.critical_severity_count,
            "topActors": self.top_actors,
            "hasCriticalEvents": self.has_critical_events,
            "hasSuspiciousActivity": self.has_suspicious_activity,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }