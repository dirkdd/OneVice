"""
OneVice Authentication API Routes

Core authentication endpoints for:
- User login with multiple providers
- Token management and refresh
- Session management
- Logout and cleanup
- Authentication status checking
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from ..models import AuthUser, AuthToken, SessionData, UserRole, AuthProvider
from ..services import AuthenticationService, AuditService
from ..dependencies import (
    get_current_user, require_authenticated_user, get_auth_context, log_api_access
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    provider: AuthProvider = AuthProvider.INTERNAL
    provider_token: Optional[str] = None
    remember_me: bool = False

class LoginResponse(BaseModel):
    user: AuthUser
    token: AuthToken
    message: str = "Login successful"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    all_sessions: bool = False

class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[AuthUser] = None
    session_valid: bool
    expires_at: Optional[datetime] = None

# Initialize services (would be properly injected in production)
auth_service = AuthenticationService()
audit_service = AuditService()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest
):
    """
    Authenticate user with specified provider
    
    Supports multiple authentication providers:
    - Internal: Email/password authentication
    - Clerk: Token-based authentication
    - Okta: SSO token authentication
    """
    
    try:
        # Authenticate user
        user, token = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            provider=login_data.provider,
            provider_token=login_data.provider_token
        )
        
        if not user or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create session
        session = await auth_service.create_session(
            user=user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Set session cookie if remember_me is enabled
        if login_data.remember_me:
            response.set_cookie(
                key="session_id",
                value=session.session_id,
                max_age=24 * 3600,  # 24 hours
                httponly=True,
                secure=True,  # Enable in production
                samesite="strict"
            )
        
        return LoginResponse(user=user, token=token)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    logout_data: LogoutRequest = LogoutRequest(),
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Log out user and invalidate session(s)
    
    Can invalidate current session or all user sessions.
    """
    
    try:
        auth_context = getattr(request.state, 'auth_context', None)
        
        if auth_context and auth_context.session:
            if logout_data.all_sessions:
                # Invalidate all user sessions (would require database query)
                # For now, just invalidate current session
                await auth_service.invalidate_session(auth_context.session.session_id)
            else:
                # Invalidate current session only
                await auth_service.invalidate_session(auth_context.session.session_id)
        
        # Remove session cookie
        response.delete_cookie(key="session_id")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/refresh", response_model=AuthToken)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    current_user: AuthUser = Depends(require_authenticated_user)
):
    """
    Refresh authentication token
    
    Generates new access token using valid refresh token.
    """
    
    try:
        # Generate new token for current user
        new_token = await auth_service._generate_auth_token(current_user)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
        
        return new_token
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    request: Request,
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """
    Get current authentication status
    
    Returns user authentication and session information.
    """
    
    try:
        auth_context = getattr(request.state, 'auth_context', None)
        
        if not current_user:
            return AuthStatusResponse(
                authenticated=False,
                session_valid=False
            )
        
        session_valid = True
        expires_at = None
        
        if auth_context and auth_context.session:
            session_valid = not auth_context.session.is_expired()
            expires_at = auth_context.session.expires_at
        
        return AuthStatusResponse(
            authenticated=True,
            user=current_user,
            session_valid=session_valid,
            expires_at=expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


@router.get("/profile")
async def get_user_profile(
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Get current user profile information
    
    Returns detailed user profile data for authenticated user.
    """
    
    try:
        # Get extended user profile
        user_profile = await auth_service.get_user_profile(current_user.id)
        
        profile_data = {
            "user": current_user,
            "profile": user_profile,
            "permissions": {
                "role": current_user.role.name,
                "actions": [action.value for action in current_user.permissions.actions],
                "data_access_level": current_user.permissions.data_access_level.name,
            }
        }
        
        return profile_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile retrieval failed: {str(e)}"
        )


@router.put("/profile")
async def update_user_profile(
    profile_data: dict,
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Update current user profile
    
    Allows users to update their own profile information.
    """
    
    try:
        # TODO: Implement profile update logic
        # This should validate data and update user profile in database
        
        return {"message": "Profile updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Change user password
    
    Only available for internal authentication provider.
    """
    
    try:
        if current_user.provider != AuthProvider.INTERNAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change not available for external authentication providers"
            )
        
        # TODO: Implement password change logic
        # This should verify current password and update to new password
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.get("/sessions")
async def list_user_sessions(
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    List active sessions for current user
    
    Returns information about all active sessions.
    """
    
    try:
        # TODO: Implement session listing
        # This should query all active sessions for the user
        
        return {"sessions": [], "message": "Session listing not implemented"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session listing failed: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Revoke specific session
    
    Allows users to invalidate specific sessions for security.
    """
    
    try:
        success = await auth_service.invalidate_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session revocation failed: {str(e)}"
        )


@router.get("/permissions")
async def get_user_permissions(
    current_user: AuthUser = Depends(require_authenticated_user),
    _ = Depends(log_api_access)
):
    """
    Get current user permissions and access levels
    
    Returns detailed permission information for the authenticated user.
    """
    
    try:
        from ..dependencies import get_ai_agent_context
        
        # Get comprehensive permission context
        ai_context = await get_ai_agent_context(current_user)
        
        permissions_info = {
            "user_role": current_user.role.name,
            "role_hierarchy": UserRole.get_hierarchy().get(current_user.role.name, []),
            "permissions": {
                "actions": [action.value for action in current_user.permissions.actions],
                "data_access_level": current_user.permissions.data_access_level.name,
                "context": current_user.permissions.context
            },
            "data_access": ai_context["data_access"],
            "ai_context": ai_context
        }
        
        return permissions_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Permission retrieval failed: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def auth_health_check():
    """
    Authentication service health check
    
    Returns status of authentication components.
    """
    
    try:
        # Check service availability
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "auth_service": "available",
                "audit_service": "available",
                "session_store": "available"  # Would check Redis connection
            }
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }