"""
OneVice Authentication Service
Business logic for user authentication and RBAC management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from app.models.user import User, SSOProvider
from app.models.auth import Role, Permission, UserRole, DataSensitivityLevel
from app.core.redis import session_manager
from app.services.cache_service import permission_cache
from app.services.audit_service import audit_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        self.session_manager = session_manager
    
    async def sync_clerk_user(self, db: AsyncSession, clerk_data: Dict[str, Any]) -> User:
        """
        Sync user from Clerk webhook or API call
        Creates or updates user based on Clerk data
        """
        clerk_id = clerk_data.get("clerk_id") or clerk_data.get("id")
        email = clerk_data.get("email")
        
        if not clerk_id or not email:
            raise ValueError("Missing required clerk_id or email")
        
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.clerk_id == clerk_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.email = email
            user.first_name = clerk_data.get("first_name")
            user.last_name = clerk_data.get("last_name")
            user.username = clerk_data.get("username")
            user.image_url = clerk_data.get("image_url", "")
            user.updated_at = datetime.utcnow()
            user.last_login_at = datetime.utcnow()
            
            logger.info(f"✅ Updated existing user: {user.email}")
        else:
            # Create new user
            user = User(
                clerk_id=clerk_id,
                email=email,
                first_name=clerk_data.get("first_name"),
                last_name=clerk_data.get("last_name"), 
                username=clerk_data.get("username"),
                image_url=clerk_data.get("image_url", ""),
                sso_provider=SSOProvider.CLERK,
                sso_id=clerk_id,
                is_verified=True,  # Clerk handles verification
                last_login_at=datetime.utcnow()
            )
            
            db.add(user)
            await db.flush()  # Get the user ID
            
            # Assign default role
            await self.assign_default_role(db, user)
            
            # Log user creation
            await audit_service.log_user_creation(
                db, None, None, str(user.id), user.email, clerk_id
            )
            
            logger.info(f"✅ Created new user: {user.email}")
        
        await db.commit()
        
        # Refresh user with relationships
        await db.refresh(user)
        return user
    
    async def assign_default_role(self, db: AsyncSession, user: User) -> None:
        """Assign default role to new user"""
        # Get default role (Creative Director - lowest level)
        result = await db.execute(
            select(Role).where(Role.slug == "creative_director")
        )
        default_role = result.scalar_one_or_none()
        
        if not default_role:
            logger.warning("Default role 'creative_director' not found")
            return
        
        # Create user role assignment
        user_role = UserRole(
            user_id=user.id,
            role_id=default_role.id,
            assigned_at=datetime.utcnow()
        )
        
        db.add(user_role)
        logger.info(f"✅ Assigned default role '{default_role.name}' to {user.email}")
    
    async def get_user_with_roles(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user with all roles and permissions"""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role).selectinload(Role.permissions)
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_clerk_id(self, db: AsyncSession, clerk_id: str) -> Optional[User]:
        """Get user by Clerk ID with roles and permissions"""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role).selectinload(Role.permissions)
            )
            .where(User.clerk_id == clerk_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_permissions(self, db: AsyncSession, user_id: str) -> List[str]:
        """Get all permissions for a user (with caching)"""
        # Try cache first
        cached_permissions = await permission_cache.get_user_permissions(user_id)
        if cached_permissions is not None:
            return cached_permissions
        
        # Cache miss - get from database
        user = await self.get_user_with_roles(db, user_id)
        if not user:
            return []
        
        permissions = set()
        for user_role in user.user_roles:
            if user_role.is_active and user_role.role.is_active:
                for permission in user_role.role.permissions:
                    if permission.is_active:
                        permissions.add(permission.slug)
        
        permissions_list = list(permissions)
        
        # Cache the result
        await permission_cache.set_user_permissions(user_id, permissions_list)
        
        return permissions_list
    
    async def get_user_roles(self, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """Get all roles for a user (with caching)"""
        # Try cache first
        cached_roles = await permission_cache.get_user_roles(user_id)
        if cached_roles is not None:
            return cached_roles
        
        # Cache miss - get from database
        user = await self.get_user_with_roles(db, user_id)
        if not user:
            return []
        
        roles = []
        for user_role in user.user_roles:
            if user_role.is_active and user_role.role.is_active:
                roles.append({
                    "id": str(user_role.role.id),
                    "name": user_role.role.name,
                    "slug": user_role.role.slug,
                    "hierarchyLevel": user_role.role.hierarchy_level,
                    "assignedAt": user_role.assigned_at,
                    "permissions": [perm.slug for perm in user_role.role.permissions if perm.is_active]
                })
        
        roles_sorted = sorted(roles, key=lambda x: x["hierarchyLevel"], reverse=True)
        
        # Cache the result
        await permission_cache.set_user_roles(user_id, roles_sorted)
        
        return roles_sorted
    
    async def has_permission(self, db: AsyncSession, user_id: str, permission_slug: str) -> bool:
        """Check if user has specific permission"""
        permissions = await self.get_user_permissions(db, user_id)
        return permission_slug in permissions
    
    async def has_role(self, db: AsyncSession, user_id: str, role_slug: str) -> bool:
        """Check if user has specific role"""
        roles = await self.get_user_roles(db, user_id)
        return any(role["slug"] == role_slug for role in roles)
    
    async def get_highest_role_level(self, db: AsyncSession, user_id: str) -> int:
        """Get user's highest role hierarchy level"""
        roles = await self.get_user_roles(db, user_id)
        if not roles:
            return 0
        return max(role["hierarchyLevel"] for role in roles)
    
    async def create_user_session(self, user: User, session_id: str) -> bool:
        """Create Redis session for user"""
        session_data = {
            "user_id": str(user.id),
            "clerk_id": user.clerk_id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return await self.session_manager.create_session(
            session_id, 
            session_data, 
            ttl=timedelta(hours=24)
        )
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        return await self.session_manager.get_session(session_id)
    
    async def delete_user_session(self, session_id: str) -> bool:
        """Delete user session"""
        return await self.session_manager.delete_session(session_id)

async def create_default_roles_and_permissions(db: AsyncSession):
    """Initialize database with default roles and permissions"""
    
    # Check if roles already exist
    result = await db.execute(select(Role))
    existing_roles = result.scalars().all()
    if existing_roles:
        logger.info("Roles already exist, skipping initialization")
        return
    
    # Create permissions first
    permissions_data = [
        # Agent management
        {"name": "Create Agents", "slug": "agents:create", "resource": "agents", "action": "create"},
        {"name": "View Agents", "slug": "agents:read", "resource": "agents", "action": "read"},
        {"name": "Update Agents", "slug": "agents:update", "resource": "agents", "action": "update"},
        {"name": "Delete Agents", "slug": "agents:delete", "resource": "agents", "action": "delete"},
        {"name": "Deploy Agents", "slug": "agents:deploy", "resource": "agents", "action": "deploy"},
        
        # User management
        {"name": "Create Users", "slug": "users:create", "resource": "users", "action": "create"},
        {"name": "View Users", "slug": "users:read", "resource": "users", "action": "read"},
        {"name": "Update Users", "slug": "users:update", "resource": "users", "action": "update"},
        {"name": "Delete Users", "slug": "users:delete", "resource": "users", "action": "delete"},
        {"name": "Manage User Roles", "slug": "users:manage_roles", "resource": "users", "action": "manage_roles"},
        
        # Organization management
        {"name": "Create Organizations", "slug": "organizations:create", "resource": "organizations", "action": "create"},
        {"name": "View Organizations", "slug": "organizations:read", "resource": "organizations", "action": "read"},
        {"name": "Update Organizations", "slug": "organizations:update", "resource": "organizations", "action": "update"},
        {"name": "Delete Organizations", "slug": "organizations:delete", "resource": "organizations", "action": "delete"},
        {"name": "Manage Organization Members", "slug": "organizations:manage_members", "resource": "organizations", "action": "manage_members"},
        
        # System administration
        {"name": "System Administration", "slug": "system:admin", "resource": "system", "action": "admin"},
        {"name": "View System Logs", "slug": "system:logs", "resource": "system", "action": "logs"},
        {"name": "View Analytics", "slug": "system:analytics", "resource": "system", "action": "analytics"},
        {"name": "Manage System Settings", "slug": "system:settings", "resource": "system", "action": "settings"}
    ]
    
    permissions_map = {}
    for perm_data in permissions_data:
        permission = Permission(
            name=perm_data["name"],
            slug=perm_data["slug"], 
            resource=perm_data["resource"],
            action=perm_data["action"],
            is_system=True
        )
        db.add(permission)
        permissions_map[perm_data["slug"]] = permission
    
    await db.flush()  # Ensure permissions have IDs
    
    # Create roles with hierarchy
    roles_data = [
        {
            "name": "Leadership",
            "slug": "leadership",
            "hierarchy_level": 4,
            "description": "Full system access and leadership oversight",
            "permissions": ["users:create", "users:read", "users:update", "users:delete", "users:manage_roles",
                          "agents:create", "agents:read", "agents:update", "agents:delete", "agents:deploy",
                          "organizations:create", "organizations:read", "organizations:update", "organizations:delete", "organizations:manage_members",
                          "system:admin", "system:logs", "system:analytics", "system:settings"]
        },
        {
            "name": "Director",
            "slug": "director", 
            "hierarchy_level": 3,
            "description": "Department management and advanced agent access",
            "permissions": ["users:read", "agents:create", "agents:read", "agents:update", "agents:delete", "agents:deploy",
                          "organizations:read", "organizations:update", "organizations:manage_members", "system:analytics"]
        },
        {
            "name": "Salesperson",
            "slug": "salesperson",
            "hierarchy_level": 2,
            "description": "Sales-focused agent access and basic user management",
            "permissions": ["agents:create", "agents:read", "agents:update", "organizations:read"]
        },
        {
            "name": "Creative Director",
            "slug": "creative_director",
            "hierarchy_level": 1,
            "description": "Basic agent access for creative work",
            "permissions": ["agents:read", "agents:create"]
        }
    ]
    
    for role_data in roles_data:
        role = Role(
            name=role_data["name"],
            slug=role_data["slug"],
            hierarchy_level=role_data["hierarchy_level"],
            description=role_data["description"],
            is_system=True
        )
        
        # Add permissions to role
        for perm_slug in role_data["permissions"]:
            if perm_slug in permissions_map:
                role.permissions.append(permissions_map[perm_slug])
        
        db.add(role)
    
    await db.commit()
    logger.info("✅ Created default roles and permissions")

# Global service instance
auth_service = AuthService()