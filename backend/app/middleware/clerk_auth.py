"""
Clerk JWT Authentication Middleware for FastAPI

This middleware validates Clerk JWT tokens for HTTP requests using the same
validation logic that already works for WebSocket connections. It extracts
the Bearer token, validates it with Clerk, and sets the user data in the
request state for use by dependency injection.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from auth.clerk_jwt import validate_clerk_token

logger = logging.getLogger(__name__)


# Global request-scoped auth cache with TTL
_auth_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl_seconds = 60  # Cache auth results for 60 seconds


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate HTTP requests using Clerk JWT tokens.
    
    Uses the existing validate_clerk_token() function that already works
    for WebSocket authentication to ensure consistency.
    """
    
    def __init__(
        self,
        app,
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health", 
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/",  # Root endpoint
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json"
        ]
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid based on TTL"""
        return time.time() - cache_entry.get("timestamp", 0) < _cache_ttl_seconds
    
    def _clean_expired_cache_entries(self) -> None:
        """Remove expired entries from the auth cache"""
        current_time = time.time()
        expired_tokens = [
            token for token, entry in _auth_cache.items()
            if current_time - entry.get("timestamp", 0) >= _cache_ttl_seconds
        ]
        for token in expired_tokens:
            del _auth_cache[token]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through Clerk JWT authentication with caching"""
        
        # Skip authentication for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.debug(f"No valid Authorization header for {request.url.path}")
            # Set empty user state so endpoints can handle optional auth
            request.state.current_user = None
            return await call_next(request)
        
        # Extract token (remove 'Bearer ' prefix)
        token = auth_header[7:]
        
        # Clean expired cache entries periodically
        self._clean_expired_cache_entries()
        
        # Check if token result is cached and valid
        if token in _auth_cache and self._is_cache_valid(_auth_cache[token]):
            logger.debug(f"Using cached auth result for token ending in ...{token[-8:]}")
            user_data = _auth_cache[token].get("user_data")
        else:
            try:
                # Validate token using existing Clerk validation
                user_data = await validate_clerk_token(token)
                
                # Cache the result with timestamp
                _auth_cache[token] = {
                    "user_data": user_data,
                    "timestamp": time.time()
                }
                logger.debug(f"Cached new auth result for token ending in ...{token[-8:]}")
                
            except Exception as e:
                logger.error(f"Auth validation error: {e}")
                user_data = None
        
        try:    
            if user_data:
                # Create AuthUser compatible with existing API endpoints
                from auth.models import AuthUser, UserRole, AuthProvider, get_role_permissions
                
                # Create AuthUser with all required fields
                # Process user data from Clerk token validation
                
                # Get email from token, with proper default
                email = user_data.get('email') or user_data.get('email_address', 'unknown@clerk.user')
                if not email or email == '':
                    email = f"{user_data.get('id', 'unknown')}@clerk.user"
                
                # Map role string from Clerk to UserRole enum
                role_str = user_data.get('role', 'SALESPERSON').upper()
                try:
                    user_role = UserRole[role_str]
                    logger.info(f"Mapped role '{role_str}' to UserRole.{user_role.name}")
                except KeyError:
                    logger.warning(f"Unknown role '{role_str}' from Clerk, defaulting to SALESPERSON")
                    user_role = UserRole.SALESPERSON
                
                user = AuthUser(
                    id=user_data.get('id', ''),
                    email=email,  # Use processed email
                    name=user_data.get('name', 'Unknown User'),
                    role=user_role,  # Use mapped role from Clerk metadata
                    permissions=get_role_permissions(user_role),
                    provider=AuthProvider.CLERK,  # Required field
                    provider_id=user_data.get('id', '')  # Required field - use same as id
                )
                
                # Store additional metadata in request state for use by API endpoints
                request.state.user_metadata = {
                    'data_access_level': user_data.get('data_access_level', 1),
                    'department': user_data.get('department', 'general')
                }
                
                request.state.current_user = user
                logger.debug(f"Successfully authenticated user {user.id} for {request.url.path}")
            else:
                logger.warning(f"Token validation failed for {request.url.path}")
                request.state.current_user = None
                
        except Exception as e:
            logger.error(f"Error validating token for {request.url.path}: {e}")
            request.state.current_user = None
        
        return await call_next(request)
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if the path should skip authentication"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)