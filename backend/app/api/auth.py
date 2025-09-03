"""
OneVice Authentication API Endpoints
FastAPI routes for authentication and RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.models.user import User
import logging
import uuid

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

# Request/Response Models
class ClerkSyncRequest(BaseModel):
    """Request model for Clerk user sync"""
    clerk_id: str = Field(..., description="Clerk user ID")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name") 
    username: Optional[str] = Field(None, description="Username")
    image_url: Optional[str] = Field("", description="Profile image URL")

class UserResponse(BaseModel):
    """Response model for user data"""
    id: str
    email: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    username: Optional[str] = None
    imageUrl: str = ""
    isActive: bool
    lastLoginAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
    organizationId: Optional[str] = None
    organizationRole: Optional[str] = None
    ssoProvider: Optional[str] = None
    ssoId: Optional[str] = None

class UserWithRolesResponse(UserResponse):
    """Extended user response with roles and permissions"""
    roles: List[Dict[str, Any]] = []
    permissions: List[str] = []
    highestRoleLevel: int = 0

class PermissionCheckRequest(BaseModel):
    """Request model for permission checking"""
    user_id: str
    permission: str

class PermissionCheckResponse(BaseModel):
    """Response model for permission checking"""
    hasPermission: bool
    permission: str
    userId: str

@router.post("/sync-clerk-user", response_model=UserWithRolesResponse)
async def sync_clerk_user(
    request: ClerkSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sync user from Clerk authentication
    Creates or updates user in OneVice database
    Replaces the mock implementation in frontend
    """
    try:
        # Convert request to dict for service
        clerk_data = {
            "clerk_id": request.clerk_id,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "username": request.username,
            "image_url": request.image_url
        }
        
        # Sync user via service
        user = await auth_service.sync_clerk_user(db, clerk_data)
        
        # Get user roles and permissions
        roles = await auth_service.get_user_roles(db, str(user.id))
        permissions = await auth_service.get_user_permissions(db, str(user.id))
        highest_role_level = await auth_service.get_highest_role_level(db, str(user.id))
        
        # Create session
        session_id = str(uuid.uuid4())
        await auth_service.create_user_session(user, session_id)
        
        # Build response
        user_dict = user.to_dict()
        response = UserWithRolesResponse(
            **user_dict,
            roles=roles,
            permissions=permissions,
            highestRoleLevel=highest_role_level
        )
        
        logger.info(f"✅ User synced successfully: {user.email}")
        return response
        
    except ValueError as e:
        logger.error(f"❌ Invalid sync request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ User sync failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/profile/{clerk_id}", response_model=UserWithRolesResponse)
async def get_user_profile(
    clerk_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile with roles and permissions
    Used by frontend for authentication state management
    """
    try:
        # Get user by Clerk ID
        user = await auth_service.get_user_by_clerk_id(db, clerk_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get roles and permissions
        roles = await auth_service.get_user_roles(db, str(user.id))
        permissions = await auth_service.get_user_permissions(db, str(user.id))
        highest_role_level = await auth_service.get_highest_role_level(db, str(user.id))
        
        # Build response
        user_dict = user.to_dict()
        response = UserWithRolesResponse(
            **user_dict,
            roles=roles,
            permissions=permissions,
            highestRoleLevel=highest_role_level
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    request: PermissionCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if user has specific permission
    Used by frontend for UI authorization
    """
    try:
        has_permission = await auth_service.has_permission(
            db, request.user_id, request.permission
        )
        
        return PermissionCheckResponse(
            hasPermission=has_permission,
            permission=request.permission,
            userId=request.user_id
        )
        
    except Exception as e:
        logger.error(f"❌ Permission check failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions/{user_id}")
async def get_user_permissions(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all permissions for a user
    Used by frontend middleware for route protection
    """
    try:
        permissions = await auth_service.get_user_permissions(db, user_id)
        
        return {
            "userId": user_id,
            "permissions": permissions,
            "count": len(permissions),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/roles/{user_id}")
async def get_user_roles(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all roles for a user
    Used by frontend for role-based UI rendering
    """
    try:
        roles = await auth_service.get_user_roles(db, user_id)
        highest_level = await auth_service.get_highest_role_level(db, user_id)
        
        return {
            "userId": user_id,
            "roles": roles,
            "highestRoleLevel": highest_level,
            "count": len(roles),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get roles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate session
    Cleans up Redis session data
    """
    try:
        # Get session ID from request (could be from header or cookie)
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return {"message": "No active session found"}
        
        # Delete session
        deleted = await auth_service.delete_user_session(session_id)
        
        if deleted:
            logger.info(f"✅ Session deleted: {session_id}")
            return {"message": "Logout successful"}
        else:
            return {"message": "Session not found"}
        
    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def auth_health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check for authentication service
    Tests database and Redis connectivity
    """
    try:
        from app.core.redis import health_check as redis_health
        from app.core.database import health_check as db_health
        
        # Check database
        db_status = await db_health()
        
        # Check Redis
        redis_status = await redis_health()
        
        return {
            "service": "authentication",
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "dependencies": {
                **db_status,
                **redis_status
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Auth health check failed: {e}")
        return {
            "service": "authentication", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }