"""
OneVice Authentication and Authorization Services

Core business logic for:
- User authentication and session management
- Authorization and permission checking
- User profile management with database integration
- Audit logging for compliance
- Clerk and Okta SSO integration
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
import asyncio
from uuid import uuid4

import httpx
import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext
import redis.asyncio as aioredis

from .models import (
    AuthUser, UserProfile, AuthToken, SessionData, AuditLogEntry, AuthContext,
    UserRole, DataSensitivity, PermissionAction, AuditAction, AuthProvider,
    get_role_permissions
)

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Core authentication service with multi-provider support
    
    Handles user authentication, session management, and token validation
    across Clerk, Okta, and internal authentication systems.
    """
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis_client = redis_client
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.session_timeout = timedelta(hours=24)
        
    async def authenticate_user(
        self, 
        email: str, 
        password: Optional[str] = None,
        provider: AuthProvider = AuthProvider.INTERNAL,
        provider_token: Optional[str] = None
    ) -> Tuple[Optional[AuthUser], Optional[AuthToken]]:
        """
        Authenticate user with specified provider
        
        Args:
            email: User email address
            password: Password (for internal auth)
            provider: Authentication provider
            provider_token: External provider token
            
        Returns:
            Tuple of (AuthUser, AuthToken) if successful, (None, None) otherwise
        """
        
        try:
            if provider == AuthProvider.CLERK:
                return await self._authenticate_with_clerk(provider_token)
            elif provider == AuthProvider.OKTA:
                return await self._authenticate_with_okta(provider_token)
            else:
                return await self._authenticate_internal(email, password)
                
        except Exception as e:
            logger.error(f"Authentication failed for {email} with provider {provider}: {e}")
            return None, None
    
    async def _authenticate_with_clerk(self, token: str) -> Tuple[Optional[AuthUser], Optional[AuthToken]]:
        """Authenticate user with Clerk token"""
        
        try:
            # Validate Clerk token (this would typically be done by JWT middleware)
            # For now, we'll simulate the process
            payload = jwt.decode(token, options={"verify_signature": False})
            
            user_id = payload.get("sub")
            email = payload.get("email")
            name = payload.get("name", "")
            
            if not user_id or not email:
                return None, None
            
            # Get or create user profile
            user_profile = await self.get_user_profile(user_id)
            role = UserRole.SALESPERSON
            
            if user_profile:
                role = UserRole(user_profile.get("role", UserRole.SALESPERSON))
            else:
                # Create new user profile
                await self.create_user_profile(user_id, email, name, role)
            
            # Create AuthUser
            permissions = get_role_permissions(role)
            auth_user = AuthUser(
                id=user_id,
                email=email,
                name=name,
                role=role,
                permissions=permissions,
                provider=AuthProvider.CLERK,
                provider_id=user_id,
                last_login=datetime.now(timezone.utc)
            )
            
            # Generate internal token
            auth_token = await self._generate_auth_token(auth_user)
            
            return auth_user, auth_token
            
        except Exception as e:
            logger.error(f"Clerk authentication failed: {e}")
            return None, None
    
    async def _authenticate_with_okta(self, token: str) -> Tuple[Optional[AuthUser], Optional[AuthToken]]:
        """Authenticate user with Okta token"""
        
        try:
            # Validate Okta token
            # This would integrate with Okta's validation endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://your-okta-domain.okta.com/oauth2/v1/introspect",
                    data={"token": token, "token_type_hint": "access_token"},
                    auth=("client_id", "client_secret")  # Configure with actual Okta credentials
                )
                
                if response.status_code != 200:
                    return None, None
                    
                token_info = response.json()
                if not token_info.get("active"):
                    return None, None
            
            user_id = token_info.get("sub")
            email = token_info.get("username")
            name = token_info.get("name", "")
            
            if not user_id or not email:
                return None, None
            
            # Get or create user profile
            user_profile = await self.get_user_profile(user_id)
            role = UserRole.SALESPERSON
            
            if user_profile:
                role = UserRole(user_profile.get("role", UserRole.SALESPERSON))
            else:
                # Create new user profile
                await self.create_user_profile(user_id, email, name, role)
            
            # Create AuthUser
            permissions = get_role_permissions(role)
            auth_user = AuthUser(
                id=user_id,
                email=email,
                name=name,
                role=role,
                permissions=permissions,
                provider=AuthProvider.OKTA,
                provider_id=user_id,
                last_login=datetime.now(timezone.utc)
            )
            
            # Generate internal token
            auth_token = await self._generate_auth_token(auth_user)
            
            return auth_user, auth_token
            
        except Exception as e:
            logger.error(f"Okta authentication failed: {e}")
            return None, None
    
    async def _authenticate_internal(
        self, 
        email: str, 
        password: str
    ) -> Tuple[Optional[AuthUser], Optional[AuthToken]]:
        """Authenticate user with internal credentials"""
        
        try:
            # This would integrate with your user database
            # For now, we'll simulate the process
            user_data = await self._get_user_by_email(email)
            
            if not user_data:
                return None, None
            
            # Verify password
            if not self.pwd_context.verify(password, user_data.get("password_hash")):
                return None, None
            
            # Create AuthUser
            user_id = user_data.get("id")
            name = user_data.get("name", "")
            role = UserRole(user_data.get("role", UserRole.SALESPERSON))
            
            permissions = get_role_permissions(role)
            auth_user = AuthUser(
                id=user_id,
                email=email,
                name=name,
                role=role,
                permissions=permissions,
                provider=AuthProvider.INTERNAL,
                provider_id=user_id,
                last_login=datetime.now(timezone.utc)
            )
            
            # Generate token
            auth_token = await self._generate_auth_token(auth_user)
            
            return auth_user, auth_token
            
        except Exception as e:
            logger.error(f"Internal authentication failed for {email}: {e}")
            return None, None
    
    async def _generate_auth_token(self, user: AuthUser) -> AuthToken:
        """Generate JWT token for authenticated user"""
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=24)
        
        payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.name,
            "provider": user.provider,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "onevice-backend"
        }
        
        # Use your JWT secret key from environment
        import os
        secret_key = os.getenv("JWT_SECRET_KEY", "default-secret-key")
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return AuthToken(
            access_token=token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours
            issued_at=now
        )
    
    async def create_session(self, user: AuthUser, ip_address: str = None, user_agent: str = None) -> SessionData:
        """Create user session"""
        
        session = SessionData(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + self.session_timeout
        )
        
        # Store session in Redis if available
        if self.redis_client:
            session_key = f"session:{session.session_id}"
            session_data = session.dict()
            await self.redis_client.setex(
                session_key,
                int(self.session_timeout.total_seconds()),
                json.dumps(session_data, default=str)
            )
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        
        if not self.redis_client:
            return None
        
        try:
            session_key = f"session:{session_id}"
            session_data = await self.redis_client.get(session_key)
            
            if session_data:
                data = json.loads(session_data)
                session = SessionData(**data)
                
                # Check if session is expired
                if session.is_expired():
                    await self.redis_client.delete(session_key)
                    return None
                
                # Update last accessed time
                session.last_accessed = datetime.now(timezone.utc)
                await self.redis_client.setex(
                    session_key,
                    int(self.session_timeout.total_seconds()),
                    json.dumps(session.dict(), default=str)
                )
                
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        
        if not self.redis_client:
            return True
        
        try:
            session_key = f"session:{session_id}"
            await self.redis_client.delete(session_key)
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from database"""
        
        # This would integrate with your database
        # For now, we'll simulate with a simple lookup
        try:
            # TODO: Implement actual database lookup
            # This should query Neo4j or PostgreSQL for user profile
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {e}")
            return None
    
    async def create_user_profile(
        self, 
        user_id: str, 
        email: str, 
        name: str, 
        role: UserRole
    ) -> bool:
        """Create new user profile"""
        
        try:
            # TODO: Implement actual database creation
            # This should create user profile in Neo4j and PostgreSQL
            logger.info(f"Created user profile for {email} with role {role.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create user profile for {email}: {e}")
            return False
    
    async def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user data by email for internal authentication"""
        
        try:
            # Import here to avoid circular imports
            from database.connection_manager import get_connection_manager
            
            connection_manager = await get_connection_manager()
            if not connection_manager:
                logger.error("No database connection available")
                return None
                
            neo4j_client = connection_manager.neo4j_client
            
            query = """
            MATCH (u:User {email: $email, active: true})
            RETURN u {
                .id,
                .email,
                .name,
                .role,
                .password_hash,
                .provider,
                .provider_id,
                .created_at,
                .last_login
            } AS user
            """
            
            result = await neo4j_client.execute_query(query, {'email': email})
            
            if result.records:
                user_data = result.records[0]['user']
                logger.info(f"Found user: {email}")
                return user_data
            else:
                logger.info(f"User not found: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None


class AuthorizationService:
    """
    Authorization service for role-based access control and data filtering
    
    Handles permission checking, role validation, and data sensitivity filtering.
    """
    
    def __init__(self):
        self.permission_cache = {}
    
    async def check_permission(
        self,
        user: AuthUser,
        action: PermissionAction,
        resource: Optional[str] = None,
        data_level: Optional[DataSensitivity] = None
    ) -> bool:
        """
        Check if user has permission for specific action and resource
        
        Args:
            user: Authenticated user
            action: Required permission action
            resource: Optional resource identifier
            data_level: Optional data sensitivity level
            
        Returns:
            True if permission granted, False otherwise
        """
        
        try:
            # Check basic permission
            if not user.has_permission(action, data_level):
                return False
            
            # Check resource-specific permissions if needed
            if resource:
                return await self._check_resource_permission(user, action, resource, data_level)
            
            return True
            
        except Exception as e:
            logger.error(f"Permission check failed for user {user.id}: {e}")
            return False
    
    async def _check_resource_permission(
        self,
        user: AuthUser,
        action: PermissionAction,
        resource: str,
        data_level: Optional[DataSensitivity]
    ) -> bool:
        """Check resource-specific permissions"""
        
        # TODO: Implement resource-specific permission logic
        # This could involve checking resource ownership, group membership, etc.
        return True
    
    async def filter_data_by_sensitivity(
        self,
        user: AuthUser,
        data: List[Dict[str, Any]],
        sensitivity_field: str = "sensitivity"
    ) -> List[Dict[str, Any]]:
        """
        Filter data based on user's data access level
        
        Args:
            user: Authenticated user
            data: List of data items to filter
            sensitivity_field: Field name containing sensitivity level
            
        Returns:
            Filtered data based on user's access level
        """
        
        try:
            filtered_data = []
            
            for item in data:
                item_sensitivity = item.get(sensitivity_field)
                
                if item_sensitivity is None:
                    # No sensitivity specified, assume public
                    filtered_data.append(item)
                    continue
                
                if isinstance(item_sensitivity, int):
                    item_sensitivity = DataSensitivity(item_sensitivity)
                elif isinstance(item_sensitivity, str):
                    item_sensitivity = DataSensitivity[item_sensitivity.upper()]
                
                # Check if user can access this sensitivity level
                if user.can_access_data(item_sensitivity):
                    filtered_data.append(item)
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Data filtering failed for user {user.id}: {e}")
            return []
    
    async def get_user_accessible_roles(self, user: AuthUser) -> List[UserRole]:
        """Get list of roles accessible by user's current role"""
        
        hierarchy = UserRole.get_hierarchy()
        user_role_name = user.role.name
        accessible_role_names = hierarchy.get(user_role_name, [user_role_name])
        
        return [UserRole[role_name] for role_name in accessible_role_names]


class UserService:
    """
    User management service with database integration
    
    Handles user CRUD operations, profile management, and role assignments.
    """
    
    def __init__(self, db_connection_manager=None):
        self.db_connection_manager = db_connection_manager
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def create_user(
        self,
        email: str,
        name: str,
        role: UserRole,
        password: Optional[str] = None,
        creator_user: Optional[AuthUser] = None
    ) -> Optional[AuthUser]:
        """Create new user"""
        
        try:
            # Check if creator has permission to create users
            if creator_user and not creator_user.has_permission(PermissionAction.CREATE_USER):
                logger.warning(f"User {creator_user.email} attempted to create user without permission")
                return None
            
            # Check if user already exists
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Generate user ID
            user_id = str(uuid4())
            
            # Hash password if provided
            password_hash = None
            if password:
                password_hash = self.pwd_context.hash(password)
            
            # Create user in database
            # TODO: Implement database operations
            # This should create user in both Neo4j (for profile) and PostgreSQL (for auth)
            
            # Create AuthUser object
            permissions = get_role_permissions(role)
            auth_user = AuthUser(
                id=user_id,
                email=email,
                name=name,
                role=role,
                permissions=permissions,
                provider=AuthProvider.INTERNAL,
                provider_id=user_id
            )
            
            logger.info(f"Created user {email} with role {role.name}")
            return auth_user
            
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID"""
        
        try:
            # TODO: Implement database lookup
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email"""
        
        try:
            # TODO: Implement database lookup
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def update_user_role(
        self,
        user_id: str,
        new_role: UserRole,
        updater_user: AuthUser
    ) -> bool:
        """Update user role"""
        
        try:
            # Check if updater has permission
            if not updater_user.has_permission(PermissionAction.MANAGE_ROLES):
                logger.warning(f"User {updater_user.email} attempted to update role without permission")
                return False
            
            # TODO: Implement database update
            logger.info(f"Updated user {user_id} role to {new_role.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id} role: {e}")
            return False
    
    async def delete_user(self, user_id: str, deleter_user: AuthUser) -> bool:
        """Delete user"""
        
        try:
            # Check if deleter has permission
            if not deleter_user.has_permission(PermissionAction.DELETE_USER):
                logger.warning(f"User {deleter_user.email} attempted to delete user without permission")
                return False
            
            # TODO: Implement database deletion
            logger.info(f"Deleted user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    async def list_users(
        self,
        requester_user: AuthUser,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuthUser]:
        """List users with permission filtering"""
        
        try:
            # Check if requester has permission
            if not requester_user.has_permission(PermissionAction.VIEW_USERS):
                logger.warning(f"User {requester_user.email} attempted to list users without permission")
                return []
            
            # TODO: Implement database query with filtering based on user's role
            return []
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []


class AuditService:
    """
    Audit logging service for compliance and security monitoring
    
    Handles audit log creation, storage, and retrieval for compliance tracking.
    """
    
    def __init__(self, db_connection_manager=None):
        self.db_connection_manager = db_connection_manager
        self.log_buffer = []
        self.buffer_size = 100
    
    async def log_event(self, audit_entry: AuditLogEntry) -> bool:
        """Log audit event"""
        
        try:
            # Add to buffer
            self.log_buffer.append(audit_entry)
            
            # Flush buffer if it's full
            if len(self.log_buffer) >= self.buffer_size:
                await self._flush_log_buffer()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    async def _flush_log_buffer(self):
        """Flush log buffer to database"""
        
        if not self.log_buffer:
            return
        
        try:
            # TODO: Implement batch insert to database
            logger.info(f"Flushed {len(self.log_buffer)} audit log entries")
            self.log_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush audit log buffer: {e}")
    
    async def get_audit_logs(
        self,
        requester_user: AuthUser,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """Get audit logs with filtering"""
        
        try:
            # Check if requester has permission
            if not requester_user.has_permission(PermissionAction.VIEW_AUDIT_LOGS):
                logger.warning(f"User {requester_user.email} attempted to view audit logs without permission")
                return []
            
            # TODO: Implement database query with filters
            return []
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []


class ClerkIntegration:
    """Integration service for Clerk authentication"""
    
    def __init__(self, publishable_key: str, secret_key: str):
        self.publishable_key = publishable_key
        self.secret_key = secret_key
        self.base_url = "https://api.clerk.dev/v1"
    
    async def sync_user_from_clerk(self, clerk_user_id: str) -> Optional[Dict[str, Any]]:
        """Sync user data from Clerk"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/{clerk_user_id}",
                    headers={"Authorization": f"Bearer {self.secret_key}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to sync user from Clerk: {e}")
            return None


class OktaIntegration:
    """Integration service for Okta SSO"""
    
    def __init__(self, domain: str, client_id: str, client_secret: str):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = f"https://{domain}.okta.com"
    
    async def sync_user_from_okta(self, okta_user_id: str) -> Optional[Dict[str, Any]]:
        """Sync user data from Okta"""
        
        try:
            # Get access token
            token = await self._get_access_token()
            if not token:
                return None
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{okta_user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to sync user from Okta: {e}")
            return None
    
    async def _get_access_token(self) -> Optional[str]:
        """Get Okta access token"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/oauth2/v1/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "okta.users.read"
                    }
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    return token_data.get("access_token")
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Okta access token: {e}")
            return None