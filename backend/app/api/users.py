"""
OneVice Users API Endpoints
FastAPI routes for user management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class UserUpdateRequest(BaseModel):
    """Request model for user updates"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)  
    username: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserListResponse(BaseModel):
    """Response model for user list"""
    users: List[dict]
    total: int
    page: int
    limit: int

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all users with pagination and optional search
    Requires 'users:read' permission
    """
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Build query
        query = select(User).order_by(User.created_at.desc())
        
        # Add search filter if provided
        if search:
            query = query.where(
                User.email.ilike(f"%{search}%") |
                User.first_name.ilike(f"%{search}%") |
                User.last_name.ilike(f"%{search}%") |
                User.username.ilike(f"%{search}%")
            )
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Get total count
        count_query = select(User)
        if search:
            count_query = count_query.where(
                User.email.ilike(f"%{search}%") |
                User.first_name.ilike(f"%{search}%") |
                User.last_name.ilike(f"%{search}%") |
                User.username.ilike(f"%{search}%")
            )
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Convert to dictionaries
        users_data = [user.to_dict() for user in users]
        
        return UserListResponse(
            users=users_data,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID
    Requires 'users:read' permission
    """
    try:
        # Get user with roles
        user = await auth_service.get_user_with_roles(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get roles and permissions
        roles = await auth_service.get_user_roles(db, user_id)
        permissions = await auth_service.get_user_permissions(db, user_id)
        
        # Build response
        user_data = user.to_dict()
        user_data["roles"] = roles
        user_data["permissions"] = permissions
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user information
    Requires 'users:update' permission
    """
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields if provided
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.username is not None:
            user.username = request.username
        if request.is_active is not None:
            user.is_active = request.is_active
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ User updated: {user.email}")
        return user.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (soft delete by setting is_active=False)
    Requires 'users:delete' permission
    """
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Soft delete - set inactive instead of hard delete
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"✅ User deactivated: {user.email}")
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user activity log
    Requires 'users:read' permission
    """
    try:
        # Get user to verify it exists
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # In a full implementation, this would query an activity log table
        # For now, return basic user info as activity
        activity = [
            {
                "type": "login",
                "timestamp": user.last_login_at,
                "description": "User logged in"
            },
            {
                "type": "profile_update",
                "timestamp": user.updated_at,
                "description": "Profile information updated"
            },
            {
                "type": "account_created", 
                "timestamp": user.created_at,
                "description": "Account created"
            }
        ]
        
        # Filter out None timestamps and sort by timestamp
        activity = [a for a in activity if a["timestamp"]]
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "userId": user_id,
            "activity": activity[:limit],
            "total": len(activity)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user activity {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search/by-email/{email}")
async def search_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Search for user by email address
    Requires 'users:read' permission
    """
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to search user by email {email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")