"""
OneVice Audit Service
Centralized audit logging for all RBAC operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.audit import AuditLog, AuditAction, AuditSeverity
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Centralized audit logging service"""
    
    async def log_user_login(
        self,
        db: AsyncSession,
        user_id: str,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """Log user login attempt"""
        try:
            audit_log = AuditLog.create_log(
                action=AuditAction.USER_LOGIN.value,
                description=f"User {email} {'logged in successfully' if success else 'failed to log in'}",
                severity=AuditSeverity.LOW.value if success else AuditSeverity.MEDIUM.value,
                actor_user_id=user_id if success else None,
                actor_email=email,
                actor_ip=ip_address,
                actor_user_agent=user_agent,
                session_id=session_id,
                target_resource="auth",
                success=success,
                error_message=error_message
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(f"✅ Audit: User login - {email} ({'success' if success else 'failed'})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log user login audit: {e}")
            return False
    
    async def log_permission_check(
        self,
        db: AsyncSession,
        user_id: str,
        permission_slug: str,
        granted: bool,
        request_path: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Log permission check (for high-value permissions only)"""
        try:
            # Only log certain high-value permission checks to avoid spam
            high_value_permissions = ["system:admin", "users:manage_roles", "users:delete", "system:settings"]
            
            if permission_slug not in high_value_permissions:
                return True  # Skip logging for routine permissions
            
            audit_log = AuditLog.create_log(
                action=AuditAction.PERMISSION_CHECKED.value,
                description=f"Permission '{permission_slug}' {'granted' if granted else 'denied'}",
                severity=AuditSeverity.LOW.value if granted else AuditSeverity.HIGH.value,
                actor_user_id=user_id,
                actor_ip=ip_address,
                target_resource="permission",
                target_resource_id=permission_slug,
                request_path=request_path,
                success=granted,
                error_message="Permission denied" if not granted else None
            )
            
            db.add(audit_log)
            await db.commit()
            
            if not granted:
                logger.warning(f"⚠️ Audit: Permission denied - {permission_slug} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log permission check audit: {e}")
            return False
    
    async def log_role_assignment(
        self,
        db: AsyncSession,
        actor_user_id: str,
        actor_email: str,
        target_user_id: str,
        target_email: str,
        role_id: str,
        role_name: str,
        request: Optional[Request] = None,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Log role assignment"""
        try:
            audit_log = AuditLog.create_log(
                action=AuditAction.ROLE_ASSIGNED.value,
                description=f"Role '{role_name}' assigned to {target_email}",
                severity=AuditSeverity.MEDIUM.value,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
                actor_ip=request.client.host if request and request.client else None,
                actor_user_agent=request.headers.get("user-agent") if request else None,
                target_user_id=target_user_id,
                target_role_id=role_id,
                target_resource="user_role",
                request_method=request.method if request else None,
                request_path=str(request.url.path) if request else None,
                new_values={
                    "role_name": role_name,
                    "target_email": target_email,
                    "reason": reason,
                    "expires_at": expires_at.isoformat() if expires_at else None
                },
                success=True
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(f"✅ Audit: Role assigned - '{role_name}' to {target_email} by {actor_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log role assignment audit: {e}")
            return False
    
    async def log_role_removal(
        self,
        db: AsyncSession,
        actor_user_id: str,
        actor_email: str,
        target_user_id: str,
        target_email: str,
        role_id: str,
        role_name: str,
        request: Optional[Request] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Log role removal"""
        try:
            audit_log = AuditLog.create_log(
                action=AuditAction.ROLE_REMOVED.value,
                description=f"Role '{role_name}' removed from {target_email}",
                severity=AuditSeverity.MEDIUM.value,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
                actor_ip=request.client.host if request and request.client else None,
                actor_user_agent=request.headers.get("user-agent") if request else None,
                target_user_id=target_user_id,
                target_role_id=role_id,
                target_resource="user_role",
                request_method=request.method if request else None,
                request_path=str(request.url.path) if request else None,
                old_values={
                    "role_name": role_name,
                    "target_email": target_email,
                    "was_active": True
                },
                new_values={
                    "is_active": False,
                    "reason": reason
                },
                success=True
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(f"✅ Audit: Role removed - '{role_name}' from {target_email} by {actor_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log role removal audit: {e}")
            return False
    
    async def log_unauthorized_access(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        email: Optional[str],
        requested_resource: str,
        required_permission: str,
        request: Optional[Request] = None,
        error_details: Optional[str] = None
    ) -> bool:
        """Log unauthorized access attempt"""
        try:
            audit_log = AuditLog.create_log(
                action=AuditAction.UNAUTHORIZED_ACCESS.value,
                description=f"Unauthorized access to {requested_resource}",
                severity=AuditSeverity.CRITICAL.value,
                actor_user_id=user_id,
                actor_email=email or "unknown",
                actor_ip=request.client.host if request and request.client else None,
                actor_user_agent=request.headers.get("user-agent") if request else None,
                target_resource=requested_resource,
                request_method=request.method if request else None,
                request_path=str(request.url.path) if request else None,
                meta_data={
                    "required_permission": required_permission,
                    "error_details": error_details
                },
                success=False,
                error_message=f"Access denied - missing permission: {required_permission}"
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.warning(f"🚨 Audit: Unauthorized access - {requested_resource} by {email or 'unknown'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log unauthorized access audit: {e}")
            return False
    
    async def log_user_creation(
        self,
        db: AsyncSession,
        actor_user_id: Optional[str],
        actor_email: Optional[str],
        target_user_id: str,
        target_email: str,
        clerk_id: str,
        request: Optional[Request] = None
    ) -> bool:
        """Log user creation from Clerk sync"""
        try:
            audit_log = AuditLog.create_log(
                action=AuditAction.USER_CREATED.value,
                description=f"New user created: {target_email}",
                severity=AuditSeverity.MEDIUM.value,
                actor_user_id=actor_user_id,
                actor_email=actor_email or "system",
                actor_ip=request.client.host if request and request.client else None,
                target_user_id=target_user_id,
                target_resource="user",
                target_resource_id=target_user_id,
                request_method=request.method if request else None,
                request_path=str(request.url.path) if request else None,
                new_values={
                    "email": target_email,
                    "clerk_id": clerk_id,
                    "source": "clerk_sync"
                },
                success=True
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(f"✅ Audit: User created - {target_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log user creation audit: {e}")
            return False

# Global audit service instance
audit_service = AuditService()