"""
OneVice SSO Integration API Routes

Single Sign-On integration endpoints for:
- Clerk authentication callbacks and webhooks
- Okta SSO authentication flow
- Provider user synchronization
- SSO configuration management
"""

import json
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from pydantic import BaseModel

from ..models import AuthUser, UserRole, AuthProvider
from ..services import ClerkIntegration, OktaIntegration, AuthenticationService, UserService
from ..dependencies import require_admin_access, log_api_access

router = APIRouter(prefix="/sso", tags=["sso"])

# Request/Response Models
class ClerkWebhookPayload(BaseModel):
    data: Dict[str, Any]
    object: str
    type: str

class OktaCallbackRequest(BaseModel):
    code: str
    state: str

class UserSyncRequest(BaseModel):
    provider: AuthProvider
    provider_user_id: str
    force_update: bool = False

class SSOConfigResponse(BaseModel):
    clerk_configured: bool
    okta_configured: bool
    available_providers: list

# Initialize services (would be properly injected)
clerk_integration = ClerkIntegration("", "")  # Will be initialized with actual keys
okta_integration = OktaIntegration("", "", "")  # Will be initialized with actual config
auth_service = AuthenticationService()
user_service = UserService()


@router.get("/config", response_model=SSOConfigResponse)
async def get_sso_config(
    current_user: AuthUser = Depends(require_admin_access),
    _ = Depends(log_api_access)
):
    """
    Get SSO configuration status
    
    Returns configuration status for available SSO providers.
    """
    
    try:
        import os
        
        clerk_configured = bool(
            os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY") and 
            os.getenv("CLERK_SECRET_KEY")
        )
        
        okta_configured = bool(
            os.getenv("OKTA_DOMAIN") and
            os.getenv("OKTA_CLIENT_ID") and 
            os.getenv("OKTA_CLIENT_SECRET")
        )
        
        available_providers = []
        if clerk_configured:
            available_providers.append("clerk")
        if okta_configured:
            available_providers.append("okta")
        
        return SSOConfigResponse(
            clerk_configured=clerk_configured,
            okta_configured=okta_configured,
            available_providers=available_providers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSO config retrieval failed: {str(e)}"
        )


@router.post("/clerk/webhook")
async def clerk_webhook(
    request: Request,
    payload: ClerkWebhookPayload,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature")
):
    """
    Handle Clerk webhooks for user lifecycle events
    
    Processes user creation, updates, and deletions from Clerk.
    """
    
    try:
        # Verify webhook signature
        webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")
        if webhook_secret:
            if not _verify_clerk_webhook(
                await request.body(), 
                svix_signature, 
                svix_timestamp, 
                svix_id, 
                webhook_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        event_type = payload.type
        user_data = payload.data
        
        if event_type == "user.created":
            await _handle_clerk_user_created(user_data)
        elif event_type == "user.updated":
            await _handle_clerk_user_updated(user_data)
        elif event_type == "user.deleted":
            await _handle_clerk_user_deleted(user_data)
        elif event_type == "session.created":
            await _handle_clerk_session_created(user_data)
        elif event_type == "session.ended":
            await _handle_clerk_session_ended(user_data)
        
        return {"status": "success", "message": f"Processed {event_type}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/okta/login")
async def okta_login_redirect():
    """
    Initiate Okta SSO login flow
    
    Redirects user to Okta for authentication.
    """
    
    try:
        import os
        from urllib.parse import urlencode
        
        okta_domain = os.getenv("OKTA_DOMAIN")
        client_id = os.getenv("OKTA_CLIENT_ID")
        
        if not okta_domain or not client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Okta not configured"
            )
        
        # Generate state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)
        
        # TODO: Store state in Redis for validation
        
        # Build authorization URL
        auth_params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/sso/okta/callback",
            "state": state
        }
        
        auth_url = f"https://{okta_domain}.okta.com/oauth2/v1/authorize?" + urlencode(auth_params)
        
        return {"auth_url": auth_url, "state": state}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Okta login initiation failed: {str(e)}"
        )


@router.post("/okta/callback")
async def okta_callback(
    callback_data: OktaCallbackRequest
):
    """
    Handle Okta SSO callback
    
    Processes authorization code and creates user session.
    """
    
    try:
        import os
        import httpx
        
        # TODO: Validate state parameter
        
        # Exchange authorization code for tokens
        token_endpoint = f"https://{os.getenv('OKTA_DOMAIN')}.okta.com/oauth2/v1/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": os.getenv("OKTA_CLIENT_ID"),
                    "client_secret": os.getenv("OKTA_CLIENT_SECRET"),
                    "code": callback_data.code,
                    "redirect_uri": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/sso/okta/callback"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token exchange failed"
                )
            
            tokens = response.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received"
                )
        
        # Authenticate user with Okta token
        user, auth_token = await auth_service.authenticate_user(
            email="",  # Will be extracted from token
            provider=AuthProvider.OKTA,
            provider_token=access_token
        )
        
        if not user or not auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        return {
            "user": user,
            "token": auth_token,
            "message": "Okta authentication successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Okta callback processing failed: {str(e)}"
        )


@router.post("/sync-user")
async def sync_user(
    sync_request: UserSyncRequest,
    current_user: AuthUser = Depends(require_admin_access),
    _ = Depends(log_api_access)
):
    """
    Synchronize user from SSO provider
    
    Manually sync user data from external provider.
    """
    
    try:
        if sync_request.provider == AuthProvider.CLERK:
            user_data = await clerk_integration.sync_user_from_clerk(
                sync_request.provider_user_id
            )
        elif sync_request.provider == AuthProvider.OKTA:
            user_data = await okta_integration.sync_user_from_okta(
                sync_request.provider_user_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider"
            )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in provider"
            )
        
        # TODO: Update user data in local database
        
        return {
            "message": "User synchronized successfully",
            "provider": sync_request.provider,
            "user_data": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User sync failed: {str(e)}"
        )


def _verify_clerk_webhook(
    payload: bytes,
    signature: str,
    timestamp: str,
    webhook_id: str,
    secret: str
) -> bool:
    """Verify Clerk webhook signature"""
    
    try:
        # Clerk uses Svix for webhooks, implement signature verification
        # This is a simplified version - in production, use the Svix library
        
        expected_signature = f"v1,{hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()}"
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception:
        return False


async def _handle_clerk_user_created(user_data: Dict[str, Any]):
    """Handle Clerk user creation webhook"""
    
    try:
        user_id = user_data.get("id")
        email_addresses = user_data.get("email_addresses", [])
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        
        if not user_id or not email_addresses:
            return
        
        primary_email = next(
            (email["email_address"] for email in email_addresses if email.get("verification", {}).get("status") == "verified"),
            email_addresses[0]["email_address"] if email_addresses else None
        )
        
        if not primary_email:
            return
        
        name = f"{first_name} {last_name}".strip()
        
        # Create user in local database
        await user_service.create_user(
            email=primary_email,
            name=name or primary_email.split("@")[0],
            role=UserRole.SALESPERSON,  # Default role
            password=None  # No password for SSO users
        )
        
    except Exception as e:
        logger.error(f"Failed to handle Clerk user creation: {e}")


async def _handle_clerk_user_updated(user_data: Dict[str, Any]):
    """Handle Clerk user update webhook"""
    
    try:
        user_id = user_data.get("id")
        
        if not user_id:
            return
        
        # TODO: Update user data in local database
        
    except Exception as e:
        logger.error(f"Failed to handle Clerk user update: {e}")


async def _handle_clerk_user_deleted(user_data: Dict[str, Any]):
    """Handle Clerk user deletion webhook"""
    
    try:
        user_id = user_data.get("id")
        
        if not user_id:
            return
        
        # TODO: Deactivate or delete user in local database
        
    except Exception as e:
        logger.error(f"Failed to handle Clerk user deletion: {e}")


async def _handle_clerk_session_created(session_data: Dict[str, Any]):
    """Handle Clerk session creation webhook"""
    
    try:
        session_id = session_data.get("id")
        user_id = session_data.get("user_id")
        
        if not session_id or not user_id:
            return
        
        # TODO: Create session record in local database
        
    except Exception as e:
        logger.error(f"Failed to handle Clerk session creation: {e}")


async def _handle_clerk_session_ended(session_data: Dict[str, Any]):
    """Handle Clerk session end webhook"""
    
    try:
        session_id = session_data.get("id")
        
        if not session_id:
            return
        
        # TODO: Invalidate session in local database
        
    except Exception as e:
        logger.error(f"Failed to handle Clerk session end: {e}")


@router.get("/providers/{provider}/users")
async def list_provider_users(
    provider: AuthProvider,
    limit: int = 50,
    offset: int = 0,
    current_user: AuthUser = Depends(require_admin_access),
    _ = Depends(log_api_access)
):
    """
    List users from SSO provider
    
    Retrieves user list from external provider for comparison/sync.
    """
    
    try:
        # TODO: Implement provider user listing
        return {
            "provider": provider,
            "users": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provider user listing failed: {str(e)}"
        )


@router.post("/test-connection/{provider}")
async def test_sso_connection(
    provider: AuthProvider,
    current_user: AuthUser = Depends(require_admin_access),
    _ = Depends(log_api_access)
):
    """
    Test SSO provider connection
    
    Validates configuration and connectivity to SSO provider.
    """
    
    try:
        if provider == AuthProvider.CLERK:
            # Test Clerk connection
            test_result = await _test_clerk_connection()
        elif provider == AuthProvider.OKTA:
            # Test Okta connection
            test_result = await _test_okta_connection()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider"
            )
        
        return {
            "provider": provider,
            "connection_status": "success" if test_result else "failed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )


async def _test_clerk_connection() -> bool:
    """Test Clerk API connection"""
    
    try:
        import os
        import httpx
        
        secret_key = os.getenv("CLERK_SECRET_KEY")
        if not secret_key:
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.dev/v1/users",
                headers={"Authorization": f"Bearer {secret_key}"},
                params={"limit": 1}
            )
            
            return response.status_code == 200
            
    except Exception:
        return False


async def _test_okta_connection() -> bool:
    """Test Okta API connection"""
    
    try:
        # Get access token and test API call
        token = await okta_integration._get_access_token()
        return token is not None
        
    except Exception:
        return False