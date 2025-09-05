"""
OneVice Admin API Endpoints
FastAPI routes for administrative role and permission management
Requires high-level permissions for access
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum

from app.core.database import get_db
from app.models.user import User
from auth.models import UserRole, PermissionSet, PermissionAction
from app.models.audit import AuditLog, AuditSummary
from app.services.auth_service import auth_service
from app.services.cache_service import permission_cache
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

# Request/Response Models
class RoleAssignmentRequest(BaseModel):
    """Request model for role assignment"""
    role_id: str = Field(..., description="Role ID to assign")
    assigned_by: Optional[str] = Field(None, description="User ID of assigner")
    expires_at: Optional[datetime] = Field(None, description="Optional role expiration")
    reason: Optional[str] = Field(None, description="Reason for assignment")

class RoleAssignmentResponse(BaseModel):
    """Response model for role assignment"""
    success: bool
    message: str
    user_id: str
    role_id: str
    role_name: str
    assigned_at: datetime
    expires_at: Optional[datetime] = None

class RoleListResponse(BaseModel):
    """Response model for role listing"""
    roles: List[Dict[str, Any]]
    total: int
    active_count: int

class AuditLogQuery(BaseModel):
    """Query parameters for audit log filtering"""
    action: Optional[str] = None
    severity: Optional[str] = None
    actor_user_id: Optional[str] = None
    target_user_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = 1
    limit: int = 50

class AdminStatsResponse(BaseModel):
    """Response model for admin statistics"""
    total_users: int
    active_users: int
    total_roles: int
    active_roles: int
    permission_checks_today: int
    role_changes_today: int
    cache_stats: Dict[str, Any]

# Admin Middleware Dependency
async def require_admin_permission(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token = Depends(security)
) -> User:
    """
    Middleware to require admin-level permissions
    Checks for 'system:admin' or 'users:manage_roles' permission
    """
    try:
        # Extract user ID from token/session (simplified for demo)
        # In production, this would validate JWT and extract user info
        user_id = request.headers.get("x-user-id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get user with full permissions
        user = await auth_service.get_user_with_roles(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Check for admin permissions
        has_admin = await auth_service.has_permission(db, user_id, "system:admin")
        has_role_mgmt = await auth_service.has_permission(db, user_id, "users:manage_roles")
        
        if not (has_admin or has_role_mgmt):
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions - admin access required"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Admin permission check failed: {e}")
        raise HTTPException(status_code=500, detail="Permission check failed")

# Role Management Endpoints
@router.get("/roles", response_model=RoleListResponse)
async def list_all_roles(
    include_inactive: bool = Query(False, description="Include inactive roles"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_permission)
):
    """List all roles in the system"""
    try:
        # Build query
        query = select(Role).options(selectinload(Role.permissions))
        
        if not include_inactive:
            query = query.where(Role.is_active == True)
        
        # Execute query
        result = await db.execute(query.order_by(Role.hierarchy_level.desc()))
        roles = result.scalars().all()
        
        # Convert to response format
        roles_data = [role.to_dict() for role in roles]
        active_count = sum(1 for role in roles if role.is_active)
        
        logger.info(f"✅ Admin {admin_user.email} listed {len(roles)} roles")
        
        return RoleListResponse(
            roles=roles_data,
            total=len(roles),
            active_count=active_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve roles")

@router.post("/users/{user_id}/roles", response_model=RoleAssignmentResponse)
async def assign_role_to_user(
    user_id: str,
    request: RoleAssignmentRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_permission)
):
    """Assign a role to a user"""
    try:
        # Validate target user exists
        target_user = await auth_service.get_user_with_roles(db, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate role exists
        result = await db.execute(select(Role).where(Role.id == request.role_id))
        role = result.scalar_one_or_none()
        if not role or not role.is_active:
            raise HTTPException(status_code=404, detail="Role not found or inactive")
        
        # Check if user already has this role
        existing_role_query = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == request.role_id,
                UserRole.is_active == True
            )
        )
        result = await db.execute(existing_role_query)
        existing_role = result.scalar_one_or_none()
        
        if existing_role:
            raise HTTPException(status_code=409, detail="User already has this role")
        
        # Create role assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=request.role_id,
            assigned_by=str(admin_user.id),
            expires_at=request.expires_at,
            assigned_at=datetime.utcnow()
        )
        
        db.add(user_role)
        await db.flush()  # Get the ID
        
        # Create audit log
        audit_log = AuditLog.create_log(
            action="role_assigned",
            description=f"Role '{role.name}' assigned to user {target_user.email}",
            severity="medium",
            actor_user_id=str(admin_user.id),
            actor_email=admin_user.email,
            actor_ip=http_request.client.host if http_request.client else None,
            target_user_id=user_id,
            target_role_id=request.role_id,
            target_resource="user_role",
            target_resource_id=str(user_role.id),
            request_method=http_request.method,
            request_path=str(http_request.url.path),
            new_values={
                "role_name": role.name,
                "role_slug": role.slug,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None,
                "reason": request.reason
            },
            success=True
        )
        
        db.add(audit_log)
        await db.commit()
        
        # Invalidate user's permission cache
        await permission_cache.invalidate_user_cache(user_id)
        
        # Warm up cache with new permissions
        await permission_cache.warmup_user_cache(db, user_id)
        
        logger.info(f"✅ Admin {admin_user.email} assigned role '{role.name}' to {target_user.email}")
        
        return RoleAssignmentResponse(
            success=True,
            message="Role assigned successfully",
            user_id=user_id,
            role_id=request.role_id,
            role_name=role.name,
            assigned_at=user_role.assigned_at,
            expires_at=user_role.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to assign role: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Role assignment failed")

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    reason: Optional[str] = Query(None, description="Reason for removal"),
    http_request: Request = None,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_permission)
):
    """Remove a role from a user"""
    try:
        # Validate target user
        target_user = await auth_service.get_user_with_roles(db, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find the user role assignment
        user_role_query = select(UserRole).options(selectinload(UserRole.role)).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            )
        )
        result = await db.execute(user_role_query)
        user_role = result.scalar_one_or_none()
        
        if not user_role:
            raise HTTPException(status_code=404, detail="User does not have this role")
        
        # Deactivate the role assignment (soft delete)
        old_values = {
            "role_name": user_role.role.name,
            "role_slug": user_role.role.slug,
            "assigned_at": user_role.assigned_at.isoformat(),
            "was_active": True
        }
        
        user_role.is_active = False
        user_role.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog.create_log(
            action="role_removed",
            description=f"Role '{user_role.role.name}' removed from user {target_user.email}",
            severity="medium",
            actor_user_id=str(admin_user.id),
            actor_email=admin_user.email,
            actor_ip=http_request.client.host if http_request.client else None,
            target_user_id=user_id,
            target_role_id=role_id,
            target_resource="user_role",
            target_resource_id=str(user_role.id),
            request_method=http_request.method,
            request_path=str(http_request.url.path),
            old_values=old_values,
            new_values={"is_active": False, "reason": reason},
            success=True
        )
        
        db.add(audit_log)
        await db.commit()
        
        # Invalidate user's permission cache
        await permission_cache.invalidate_user_cache(user_id)
        
        # Warm up cache with updated permissions
        await permission_cache.warmup_user_cache(db, user_id)
        
        logger.info(f"✅ Admin {admin_user.email} removed role '{user_role.role.name}' from {target_user.email}")
        
        return {
            "success": True,
            "message": "Role removed successfully",
            "user_id": user_id,
            "role_id": role_id,
            "role_name": user_role.role.name,
            "removed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to remove role: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Role removal failed")

# Audit Log Endpoints
@router.get("/audit-logs")
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    actor_email: Optional[str] = Query(None, description="Filter by actor email"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_permission)
):
    """Get audit logs with filtering"""
    try:
        # Build query with filters
        query = select(AuditLog).order_by(desc(AuditLog.created_at))
        
        # Apply filters
        if action:
            query = query.where(AuditLog.action == action)
        if severity:
            query = query.where(AuditLog.severity == severity)
        if actor_email:
            query = query.where(AuditLog.actor_email.ilike(f"%{actor_email}%"))
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where(AuditLog.created_at <= end_datetime)
        
        # Count total (before pagination)
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        # Convert to response format
        logs_data = [log.to_dict() for log in audit_logs]
        
        logger.info(f"✅ Admin {admin_user.email} retrieved {len(audit_logs)} audit logs")
        
        return {
            "audit_logs": logs_data,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": offset + len(audit_logs) < total
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")

# Admin Statistics
@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_permission)
):
    """Get administrative statistics"""
    try:
        # User statistics
        user_count_result = await db.execute(select(func.count(User.id)))
        total_users = user_count_result.scalar()
        
        active_user_count_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_user_count_result.scalar()
        
        # Role statistics
        role_count_result = await db.execute(select(func.count(Role.id)))
        total_roles = role_count_result.scalar()
        
        active_role_count_result = await db.execute(
            select(func.count(Role.id)).where(Role.is_active == True)
        )
        active_roles = active_role_count_result.scalar()
        
        # Today's activity
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        permission_checks_result = await db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action == "permission_checked",
                    AuditLog.created_at >= today,
                    AuditLog.created_at < tomorrow
                )
            )
        )
        permission_checks_today = permission_checks_result.scalar() or 0
        
        role_changes_result = await db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action.in_(["role_assigned", "role_removed"]),
                    AuditLog.created_at >= today,
                    AuditLog.created_at < tomorrow
                )
            )
        )
        role_changes_today = role_changes_result.scalar() or 0
        
        # Cache statistics
        cache_stats = await permission_cache.get_cache_stats()
        
        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_roles=total_roles,
            active_roles=active_roles,
            permission_checks_today=permission_checks_today,
            role_changes_today=role_changes_today,
            cache_stats=cache_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# Cache Management
@router.post("/cache/invalidate")
async def invalidate_cache(
    user_id: Optional[str] = Query(None, description="Specific user ID to invalidate"),
    all_cache: bool = Query(False, description="Invalidate all permission cache"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_permission)
):
    """Manually invalidate permission cache"""
    try:
        if all_cache:
            # Nuclear option - invalidate everything
            result = await permission_cache.invalidate_all_permissions()
            action = "cache_invalidated_all"
            message = "All permission cache invalidated"
        elif user_id:
            # Invalidate specific user
            result = await permission_cache.invalidate_user_cache(user_id)
            action = "cache_invalidated_user"
            message = f"Cache invalidated for user {user_id}"
        else:
            raise HTTPException(status_code=400, detail="Must specify user_id or all_cache=true")
        
        # Create audit log
        audit_log = AuditLog.create_log(
            action=action,
            description=message,
            severity="low",
            actor_user_id=str(admin_user.id),
            actor_email=admin_user.email,
            target_user_id=user_id if user_id else None,
            target_resource="cache",
            metadata={"all_cache": all_cache},
            success=result
        )
        
        db.add(audit_log)
        await db.commit()
        
        logger.info(f"✅ Admin {admin_user.email} invalidated cache: {message}")
        
        return {
            "success": result,
            "message": message,
            "invalidated_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail="Cache invalidation failed")