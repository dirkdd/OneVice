"""
OneVice User Management API Routes

User management endpoints for:
- User CRUD operations with proper authorization
- Role assignment and permission management
- User search and filtering
- Profile management for other users
- Data access control based on sensitivity levels
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from ..models import AuthUser, UserProfile, UserRole, DataSensitivity, PermissionAction
from ..services import UserService, AuthorizationService
from ..dependencies import (
    require_authenticated_user, require_user_management_access, require_admin_access,
    get_filtered_data_access, log_api_access
)

router = APIRouter(prefix="/users", tags=["user-management"])

# Request/Response Models
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    role: UserRole
    password: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    user: AuthUser
    profile: Optional[UserProfile] = None

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int

class RoleAssignmentRequest(BaseModel):
    user_id: str
    new_role: UserRole
    reason: Optional[str] = None

# Initialize services
user_service = UserService()
authz_service = AuthorizationService()


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: AuthUser = Depends(require_user_management_access),
    _ = Depends(log_api_access)
):
    """
    Create new user account
    
    Requires user management permissions (Director level or higher).
    Only Leadership can create other Leadership users.
    """
    
    try:
        # Check if current user can create user with specified role
        if user_data.role == UserRole.LEADERSHIP and current_user.role != UserRole.LEADERSHIP:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Leadership can create Leadership users"
            )
        
        if user_data.role.value > current_user.role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create user with higher role than your own"
            )
        
        # Create user
        new_user = await user_service.create_user(
            email=user_data.email,
            name=user_data.name,
            role=user_data.role,
            password=user_data.password,
            creator_user=current_user
        )
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed"
            )
        
        # Create user profile
        profile = UserProfile(
            user_id=new_user.id,
            department=user_data.department,
            title=user_data.title,
            phone=user_data.phone,
            location=user_data.location
        )
        
        # TODO: Save profile to database
        
        return UserResponse(user=new_user, profile=profile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    role: Optional[UserRole] = Query(None),
    department: Optional[str] = Query(None),
    active_only: bool = Query(True),
    current_user: AuthUser = Depends(require_authenticated_user),
    filter_data = Depends(get_filtered_data_access),
    _ = Depends(log_api_access)
):
    """
    List users with filtering and pagination
    
    Users can only see other users at their level or below in the hierarchy.
    Data sensitivity filtering applies based on user's access level.
    """
    
    try:
        # Check basic permission
        if not current_user.has_permission(PermissionAction.VIEW_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view users"
            )
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get users from service
        users = await user_service.list_users(
            requester_user=current_user,
            limit=per_page,
            offset=offset
        )
        
        # Apply role hierarchy filtering
        accessible_roles = await authz_service.get_user_accessible_roles(current_user)
        filtered_users = [user for user in users if user.role in accessible_roles]
        
        # Apply additional filters
        if role:
            filtered_users = [user for user in filtered_users if user.role == role]
        
        if active_only:
            filtered_users = [user for user in filtered_users if user.is_active]
        
        # Create user responses with profiles
        user_responses = []
        for user in filtered_users:
            # TODO: Get user profile from database
            profile = None
            user_responses.append(UserResponse(user=user, profile=profile))
        
        # Apply data sensitivity filtering (simulated)
        user_data = [{"user": resp.user.dict(), "profile": resp.profile.dict() if resp.profile else None, "sensitivity": DataSensitivity.CONFIDENTIAL.value} for resp in user_responses]
        filtered_data = await filter_data(user_data, "sensitivity")
        
        # Convert back to user responses
        final_responses = [UserResponse(**item) for item in filtered_data]
        
        return UserListResponse(
            users=final_responses,
            total=len(final_responses),
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User listing failed: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Get specific user by ID
    
    Users can view their own profile or other users if they have appropriate permissions.
    """
    
    try:
        # Check if requesting own profile or have permission to view others
        if user_id != current_user.id and not current_user.has_permission(PermissionAction.VIEW_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user"
            )
        
        # Get user
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check role hierarchy access if viewing other user
        if user_id != current_user.id:
            accessible_roles = await authz_service.get_user_accessible_roles(current_user)
            if user.role not in accessible_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view this user"
                )
        
        # TODO: Get user profile from database
        profile = None
        
        return UserResponse(user=user, profile=profile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User retrieval failed: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Update user information
    
    Users can update their own profile or other users if they have appropriate permissions.
    Role changes require higher-level permissions.
    """
    
    try:
        # Check permissions
        is_self_update = user_id == current_user.id
        
        if not is_self_update:
            if not current_user.has_permission(PermissionAction.UPDATE_USER):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update user"
                )
        
        # Get target user
        target_user = await user_service.get_user_by_id(user_id)
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check role change permissions
        if user_data.role and user_data.role != target_user.role:
            if is_self_update:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot change your own role"
                )
            
            if not current_user.has_permission(PermissionAction.MANAGE_ROLES):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to change user role"
                )
            
            # Check hierarchy constraints
            if user_data.role.value > current_user.role.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot assign role higher than your own"
                )
        
        # TODO: Update user in database
        # This should update both auth and profile data
        
        return UserResponse(user=target_user, profile=None)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User update failed: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: AuthUser = Depends(require_user_management_access),
    _ = Depends(log_api_access)
):
    """
    Delete user account
    
    Requires user management permissions. Cannot delete your own account.
    """
    
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Get target user to check hierarchy
        target_user = await user_service.get_user_by_id(user_id)
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if can delete user of this role
        accessible_roles = await authz_service.get_user_accessible_roles(current_user)
        if target_user.role not in accessible_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete this user"
            )
        
        # Delete user
        success = await user_service.delete_user(user_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User deletion failed"
            )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User deletion failed: {str(e)}"
        )


@router.post("/{user_id}/role", response_model=UserResponse)
async def assign_role(
    user_id: str,
    role_data: RoleAssignmentRequest,
    current_user: AuthUser = Depends(require_admin_access),
    _ = Depends(log_api_access)
):
    """
    Assign role to user
    
    Requires admin permissions (Leadership level).
    Includes audit logging for role changes.
    """
    
    try:
        # Validate user ID in request body matches path parameter
        if role_data.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID mismatch"
            )
        
        # Update user role
        success = await user_service.update_user_role(
            user_id=user_id,
            new_role=role_data.new_role,
            updater_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Role assignment failed"
            )
        
        # Get updated user
        updated_user = await user_service.get_user_by_id(user_id)
        
        return UserResponse(user=updated_user, profile=None)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Role assignment failed: {str(e)}"
        )


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Get user permissions and access levels
    
    Returns detailed permission information for specified user.
    """
    
    try:
        # Check permissions to view user permissions
        if user_id != current_user.id and not current_user.has_permission(PermissionAction.VIEW_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user permissions"
            )
        
        # Get target user
        target_user = await user_service.get_user_by_id(user_id)
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get comprehensive permission information
        permissions_info = {
            "user_id": target_user.id,
            "user_role": target_user.role.name,
            "role_hierarchy": UserRole.get_hierarchy().get(target_user.role.name, []),
            "permissions": {
                "actions": [action.value for action in target_user.permissions.actions],
                "data_access_level": target_user.permissions.data_access_level.name,
                "context": target_user.permissions.context
            },
            "data_access": {
                "can_access_public": target_user.can_access_data(DataSensitivity.PUBLIC),
                "can_access_internal": target_user.can_access_data(DataSensitivity.INTERNAL),
                "can_access_confidential": target_user.can_access_data(DataSensitivity.CONFIDENTIAL),
                "can_access_restricted": target_user.can_access_data(DataSensitivity.RESTRICTED),
                "can_access_secret": target_user.can_access_data(DataSensitivity.SECRET),
                "can_access_top_secret": target_user.can_access_data(DataSensitivity.TOP_SECRET),
            }
        }
        
        return permissions_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Permission retrieval failed: {str(e)}"
        )


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: AuthUser = Depends(require_user_management_access),
    _ = Depends(log_api_access)
):
    """
    Activate user account
    
    Requires user management permissions.
    """
    
    try:
        # TODO: Implement user activation
        return {"message": "User activated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User activation failed: {str(e)}"
        )


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: AuthUser = Depends(require_user_management_access),
    _ = Depends(log_api_access)
):
    """
    Deactivate user account
    
    Requires user management permissions. Cannot deactivate your own account.
    """
    
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        # TODO: Implement user deactivation
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User deactivation failed: {str(e)}"
        )


@router.get("/{user_id}/audit-log")
async def get_user_audit_log(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_admin_access),
    _ = Depends(log_api_access)
):
    """
    Get audit log for specific user
    
    Requires admin permissions (Leadership level).
    """
    
    try:
        # TODO: Implement audit log retrieval for user
        return {
            "user_id": user_id,
            "audit_logs": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit log retrieval failed: {str(e)}"
        )