"""
OneVice Authentication and Authorization Middleware

Comprehensive middleware stack for:
- JWT token validation with Clerk integration
- Role-based access control (RBAC) 
- Data sensitivity filtering
- Audit logging for compliance
- WebSocket authentication support
"""

import json
import time
import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime, timezone

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from jwt import PyJWKClient
import httpx

from .models import (
    AuthUser, AuthContext, UserRole, DataSensitivity, PermissionAction,
    AuditAction, AuditLogEntry, SessionData, get_role_permissions
)
from .services import AuditService, AuthenticationService

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication Middleware with Clerk integration
    
    Validates JWT tokens from Clerk and establishes user authentication context.
    Supports both web and API authentication flows.
    """
    
    def __init__(
        self,
        app,
        clerk_publishable_key: str,
        clerk_secret_key: str,
        excluded_paths: Optional[List[str]] = None,
        require_auth: bool = True
    ):
        super().__init__(app)
        self.clerk_publishable_key = clerk_publishable_key
        self.clerk_secret_key = clerk_secret_key
        self.excluded_paths = excluded_paths or [
            "/health", "/docs", "/redoc", "/openapi.json", "/auth/login", "/auth/callback"
        ]
        self.require_auth = require_auth
        
        # Initialize Clerk JWT validation
        self.jwks_client = None
        self._setup_jwt_validation()
        
        # Initialize services
        self.auth_service = None
        self.audit_service = None
    
    def _setup_jwt_validation(self):
        """Setup JWT validation with Clerk JWKS"""
        try:
            # Extract domain from publishable key for JWKS URL
            if self.clerk_publishable_key.startswith("pk_test_"):
                # Development environment
                clerk_domain = "clerk.accounts.dev"
            elif self.clerk_publishable_key.startswith("pk_live_"):
                # Production environment - extract from key
                # This would need to be configured based on actual Clerk setup
                clerk_domain = "clerk.your-domain.com"  # Update with actual domain
            else:
                clerk_domain = "clerk.accounts.dev"  # Fallback
            
            jwks_url = f"https://{clerk_domain}/.well-known/jwks.json"
            self.jwks_client = PyJWKClient(jwks_url)
            logger.info(f"JWT validation configured with JWKS URL: {jwks_url}")
            
        except Exception as e:
            logger.error(f"Failed to setup JWT validation: {e}")
            self.jwks_client = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through JWT authentication middleware"""
        
        # Initialize services if needed
        if self.auth_service is None:
            self.auth_service = AuthenticationService()
        if self.audit_service is None:
            self.audit_service = AuditService()
        
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extract and validate JWT token
        auth_context = await self._authenticate_request(request)
        
        # Check if authentication is required
        if self.require_auth and not auth_context.is_authenticated():
            await self._log_auth_failure(request, "Missing or invalid authentication")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
        
        # Add auth context to request state
        request.state.auth_context = auth_context
        request.state.user = auth_context.user
        
        # Log successful authentication
        if auth_context.is_authenticated():
            await self._log_auth_success(request, auth_context.user)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    async def _authenticate_request(self, request: Request) -> AuthContext:
        """
        Authenticate request and build auth context
        
        Args:
            request: FastAPI request object
            
        Returns:
            AuthContext with authentication status and user info
        """
        
        auth_context = AuthContext(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            # Extract JWT token from Authorization header
            authorization = request.headers.get("Authorization")
            if not authorization:
                return auth_context
            
            if not authorization.startswith("Bearer "):
                return auth_context
            
            token = authorization.split(" ")[1]
            
            # Validate JWT token with Clerk
            user = await self._validate_jwt_token(token)
            if user:
                auth_context.user = user
                auth_context.permissions = user.permissions
                
                # Create session data
                auth_context.session = SessionData(
                    user_id=user.id,
                    ip_address=auth_context.ip_address,
                    user_agent=auth_context.user_agent
                )
            
            return auth_context
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return auth_context
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return auth_context
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return auth_context
    
    async def _validate_jwt_token(self, token: str) -> Optional[AuthUser]:
        """
        Validate JWT token with Clerk and extract user information
        
        Args:
            token: JWT token string
            
        Returns:
            AuthUser if token is valid, None otherwise
        """
        
        try:
            if not self.jwks_client:
                logger.error("JWKS client not initialized")
                return None
            
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and verify token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_signature": True, "verify_exp": True}
            )
            
            # Extract user information from token payload
            user_id = payload.get("sub")
            email = payload.get("email")
            name = payload.get("name", "")
            
            if not user_id or not email:
                logger.warning("Missing required fields in JWT payload")
                return None
            
            # Get user profile and role from database
            user_profile = await self.auth_service.get_user_profile(user_id)
            
            # Determine user role (default to SALESPERSON if not found)
            user_role = UserRole.SALESPERSON
            if user_profile:
                user_role = UserRole(user_profile.get("role", UserRole.SALESPERSON))
            
            # Get permissions for role
            permissions = get_role_permissions(user_role)
            
            # Create AuthUser object
            auth_user = AuthUser(
                id=user_id,
                email=email,
                name=name,
                role=user_role,
                permissions=permissions,
                provider="clerk",
                provider_id=user_id,
                last_login=datetime.now(timezone.utc)
            )
            
            logger.info(f"Successfully authenticated user: {email} with role: {user_role.name}")
            return auth_user
            
        except jwt.ExpiredSignatureError:
            logger.info("JWT token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None
    
    async def _log_auth_success(self, request: Request, user: AuthUser):
        """Log successful authentication"""
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=user.id,
                    action=AuditAction.LOGIN_SUCCESS,
                    success=True,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "provider": user.provider,
                        "role": user.role.name,
                        "path": str(request.url.path)
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log auth success: {e}")
    
    async def _log_auth_failure(self, request: Request, reason: str):
        """Log authentication failure"""
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    action=AuditAction.LOGIN_FAILURE,
                    success=False,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "reason": reason,
                        "path": str(request.url.path)
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log auth failure: {e}")


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Role-Based Access Control Middleware
    
    Enforces permissions based on user role and data sensitivity levels.
    Provides fine-grained access control for API endpoints.
    """
    
    def __init__(
        self,
        app,
        permission_config: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        super().__init__(app)
        self.permission_config = permission_config or {}
        self.audit_service = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through RBAC middleware"""
        
        # Initialize audit service
        if self.audit_service is None:
            self.audit_service = AuditService()
        
        # Get auth context from previous middleware
        auth_context: Optional[AuthContext] = getattr(request.state, 'auth_context', None)
        
        if not auth_context or not auth_context.is_authenticated():
            # No authentication context, let JWT middleware handle it
            return await call_next(request)
        
        # Check permissions for the requested endpoint
        access_granted = await self._check_endpoint_permissions(request, auth_context)
        
        if not access_granted:
            await self._log_access_denied(request, auth_context)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Insufficient permissions"}
            )
        
        # Log access granted
        await self._log_access_granted(request, auth_context)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    async def _check_endpoint_permissions(self, request: Request, auth_context: AuthContext) -> bool:
        """
        Check if user has permission to access endpoint
        
        Args:
            request: FastAPI request
            auth_context: Authentication context
            
        Returns:
            True if access is granted, False otherwise
        """
        
        path = request.url.path
        method = request.method.lower()
        
        # Check path-specific permissions from config
        endpoint_key = f"{method}:{path}"
        endpoint_config = self.permission_config.get(endpoint_key)
        
        if endpoint_config:
            required_role = endpoint_config.get("role")
            required_permission = endpoint_config.get("permission")
            required_data_level = endpoint_config.get("data_level")
            
            # Check role requirement
            if required_role and not auth_context.user.has_role_access(UserRole(required_role)):
                return False
            
            # Check permission requirement
            if required_permission:
                permission_action = PermissionAction(required_permission)
                data_level = DataSensitivity(required_data_level) if required_data_level else None
                
                if not auth_context.has_permission(permission_action, data_level):
                    return False
        
        # Default permission checks based on HTTP method
        return await self._check_default_permissions(request, auth_context)
    
    async def _check_default_permissions(self, request: Request, auth_context: AuthContext) -> bool:
        """
        Check default permissions based on HTTP method and path patterns
        
        Args:
            request: FastAPI request
            auth_context: Authentication context
            
        Returns:
            True if access is granted, False otherwise
        """
        
        method = request.method.lower()
        path = request.url.path
        
        # Admin endpoints require leadership role
        if "/admin/" in path:
            return auth_context.user.has_role_access(UserRole.LEADERSHIP)
        
        # User management endpoints require director role or higher
        if "/users/" in path and method in ["post", "put", "delete"]:
            return auth_context.user.has_role_access(UserRole.DIRECTOR)
        
        # Report endpoints require appropriate permissions
        if "/reports/" in path:
            return auth_context.has_permission(PermissionAction.VIEW_REPORTS)
        
        # AI endpoints require AI access permission
        if "/ai/" in path:
            return auth_context.has_permission(PermissionAction.ACCESS_AI_AGENTS)
        
        # Default: allow GET requests for authenticated users, restrict others
        if method == "get":
            return auth_context.has_permission(PermissionAction.READ)
        elif method in ["post", "put", "patch"]:
            return auth_context.has_permission(PermissionAction.WRITE)
        elif method == "delete":
            return auth_context.has_permission(PermissionAction.DELETE)
        
        return True  # Default allow
    
    async def _log_access_granted(self, request: Request, auth_context: AuthContext):
        """Log successful access grant"""
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=auth_context.user.id,
                    session_id=auth_context.session.session_id if auth_context.session else None,
                    action=AuditAction.ACCESS_GRANTED,
                    resource=request.url.path,
                    success=True,
                    ip_address=auth_context.ip_address,
                    user_agent=auth_context.user_agent,
                    details={
                        "method": request.method,
                        "role": auth_context.user.role.name
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log access granted: {e}")
    
    async def _log_access_denied(self, request: Request, auth_context: AuthContext):
        """Log access denial"""
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=auth_context.user.id,
                    session_id=auth_context.session.session_id if auth_context.session else None,
                    action=AuditAction.ACCESS_DENIED,
                    resource=request.url.path,
                    success=False,
                    ip_address=auth_context.ip_address,
                    user_agent=auth_context.user_agent,
                    details={
                        "method": request.method,
                        "role": auth_context.user.role.name,
                        "reason": "insufficient_permissions"
                    },
                    risk_score=0.7  # Access denial increases risk score
                )
            )
        except Exception as e:
            logger.error(f"Failed to log access denied: {e}")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive audit logging middleware for compliance tracking
    
    Logs all requests, responses, and data access for security and compliance.
    """
    
    def __init__(
        self,
        app,
        log_requests: bool = True,
        log_responses: bool = False,
        sensitive_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.sensitive_paths = sensitive_paths or ["/admin/", "/users/", "/reports/"]
        self.audit_service = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through audit logging middleware"""
        
        # Initialize audit service
        if self.audit_service is None:
            self.audit_service = AuditService()
        
        start_time = time.time()
        
        # Get auth context
        auth_context: Optional[AuthContext] = getattr(request.state, 'auth_context', None)
        
        # Log request if enabled
        if self.log_requests:
            await self._log_request(request, auth_context)
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log response if enabled
        if self.log_responses:
            await self._log_response(request, response, auth_context, response_time)
        
        # Log data access for sensitive paths
        if any(sensitive_path in request.url.path for sensitive_path in self.sensitive_paths):
            await self._log_data_access(request, response, auth_context)
        
        return response
    
    async def _log_request(self, request: Request, auth_context: Optional[AuthContext]):
        """Log incoming request"""
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=auth_context.user.id if auth_context and auth_context.user else None,
                    session_id=auth_context.session.session_id if auth_context and auth_context.session else None,
                    action=AuditAction.DATA_READ if request.method.upper() == "GET" else AuditAction.DATA_WRITE,
                    resource=request.url.path,
                    success=True,  # Will be updated by response logging if needed
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "method": request.method,
                        "path": str(request.url.path),
                        "query_params": dict(request.query_params) if request.query_params else {},
                        "content_type": request.headers.get("content-type"),
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        auth_context: Optional[AuthContext],
        response_time: float
    ):
        """Log response details"""
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=auth_context.user.id if auth_context and auth_context.user else None,
                    session_id=auth_context.session.session_id if auth_context and auth_context.session else None,
                    action=AuditAction.DATA_READ if request.method.upper() == "GET" else AuditAction.DATA_WRITE,
                    resource=request.url.path,
                    success=response.status_code < 400,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "method": request.method,
                        "status_code": response.status_code,
                        "response_time_ms": round(response_time * 1000, 2),
                        "content_type": response.headers.get("content-type"),
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log response: {e}")
    
    async def _log_data_access(
        self, 
        request: Request, 
        response: Response, 
        auth_context: Optional[AuthContext]
    ):
        """Log data access for sensitive endpoints"""
        try:
            # Determine data sensitivity based on path
            data_sensitivity = None
            if "/admin/" in request.url.path:
                data_sensitivity = DataSensitivity.SECRET
            elif "/users/" in request.url.path:
                data_sensitivity = DataSensitivity.CONFIDENTIAL
            elif "/reports/" in request.url.path:
                data_sensitivity = DataSensitivity.RESTRICTED
            
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=auth_context.user.id if auth_context and auth_context.user else None,
                    session_id=auth_context.session.session_id if auth_context and auth_context.session else None,
                    action=AuditAction.DATA_READ if request.method.upper() == "GET" else AuditAction.DATA_WRITE,
                    resource=request.url.path,
                    data_sensitivity=data_sensitivity,
                    success=response.status_code < 400,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "method": request.method,
                        "sensitive_data_accessed": True,
                        "status_code": response.status_code,
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")


class WebSocketAuthMiddleware:
    """
    WebSocket Authentication Middleware
    
    Handles authentication for WebSocket connections using JWT tokens.
    """
    
    def __init__(
        self,
        clerk_publishable_key: str,
        clerk_secret_key: str
    ):
        self.clerk_publishable_key = clerk_publishable_key
        self.clerk_secret_key = clerk_secret_key
        self.jwt_middleware = JWTAuthenticationMiddleware(
            None, clerk_publishable_key, clerk_secret_key
        )
    
    async def authenticate_websocket(self, websocket, token: str) -> Optional[AuthUser]:
        """
        Authenticate WebSocket connection with JWT token
        
        Args:
            websocket: WebSocket connection
            token: JWT token for authentication
            
        Returns:
            AuthUser if authentication successful, None otherwise
        """
        
        try:
            # Validate JWT token
            user = await self.jwt_middleware._validate_jwt_token(token)
            return user
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            return None
    
    async def require_websocket_auth(self, websocket) -> AuthUser:
        """
        Require authentication for WebSocket connection
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            AuthUser if authenticated
            
        Raises:
            WebSocketException: If authentication fails
        """
        
        from fastapi import WebSocketException, status as ws_status
        
        # Get token from query parameters or headers
        token = websocket.query_params.get("token")
        if not token:
            token = websocket.headers.get("authorization")
            if token and token.startswith("Bearer "):
                token = token.split(" ")[1]
        
        if not token:
            raise WebSocketException(
                code=ws_status.WS_1008_POLICY_VIOLATION,
                reason="Authentication token required"
            )
        
        user = await self.authenticate_websocket(websocket, token)
        if not user:
            raise WebSocketException(
                code=ws_status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication token"
            )
        
        return user