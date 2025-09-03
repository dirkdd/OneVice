"""
OneVice Authentication Database Integration

Database operations for:
- User profile management in Neo4j and PostgreSQL
- Audit logging storage and retrieval
- Session management with Redis
- Role and permission persistence
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import asyncpg
import redis.asyncio as aioredis
from neo4j import AsyncGraphDatabase

from .models import (
    AuthUser, UserProfile, AuditLogEntry, AuditAction, SessionData,
    UserRole, DataSensitivity, PermissionAction, AuthProvider,
    get_role_permissions
)

logger = logging.getLogger(__name__)


class AuthUserRepository:
    """
    User management repository with dual database support
    
    - Neo4j: User profiles, relationships, and graph data
    - PostgreSQL: Authentication data, roles, and relational data
    - Redis: Session management and caching
    """
    
    def __init__(
        self,
        neo4j_driver=None,
        postgres_pool: asyncpg.Pool = None,
        redis_client: aioredis.Redis = None
    ):
        self.neo4j_driver = neo4j_driver
        self.postgres_pool = postgres_pool
        self.redis_client = redis_client
    
    async def create_user(
        self,
        user_id: str,
        email: str,
        name: str,
        role: UserRole,
        provider: AuthProvider,
        provider_id: str,
        password_hash: Optional[str] = None
    ) -> bool:
        """
        Create user in both PostgreSQL and Neo4j
        
        Args:
            user_id: Unique user identifier
            email: User email address
            name: User full name
            role: User role
            provider: Authentication provider
            provider_id: Provider-specific user ID
            password_hash: Hashed password for internal auth
            
        Returns:
            True if user created successfully
        """
        
        try:
            # Create user in PostgreSQL (authentication data)
            await self._create_user_postgres(
                user_id, email, name, role, provider, provider_id, password_hash
            )
            
            # Create user profile in Neo4j (profile and relationship data)
            await self._create_user_neo4j(user_id, email, name, role)
            
            logger.info(f"Created user {email} with ID {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            # TODO: Implement rollback mechanism
            return False
    
    async def _create_user_postgres(
        self,
        user_id: str,
        email: str,
        name: str,
        role: UserRole,
        provider: AuthProvider,
        provider_id: str,
        password_hash: Optional[str]
    ):
        """Create user in PostgreSQL"""
        
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (
                    id, email, name, role, provider, provider_id, 
                    password_hash, is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
            user_id, email, name, role.name, provider.value, provider_id,
            password_hash, True, datetime.now(timezone.utc), datetime.now(timezone.utc)
            )
    
    async def _create_user_neo4j(
        self,
        user_id: str,
        email: str,
        name: str,
        role: UserRole
    ):
        """Create user profile in Neo4j"""
        
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        async with self.neo4j_driver.session() as session:
            await session.run("""
                CREATE (u:User {
                    id: $user_id,
                    email: $email,
                    name: $name,
                    role: $role,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, 
            user_id=user_id, email=email, name=name, role=role.name
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID from PostgreSQL"""
        
        if not self.postgres_pool:
            return None
        
        try:
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, email, name, role, provider, provider_id,
                           is_active, created_at, last_login_at
                    FROM users WHERE id = $1
                """, user_id)
                
                if not row:
                    return None
                
                return self._row_to_auth_user(row)
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email from PostgreSQL"""
        
        if not self.postgres_pool:
            return None
        
        try:
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, email, name, role, provider, provider_id,
                           password_hash, is_active, created_at, last_login_at
                    FROM users WHERE email = $1
                """, email)
                
                if not row:
                    return None
                
                return self._row_to_auth_user(row)
                
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update user role in both databases"""
        
        try:
            # Update PostgreSQL
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE users 
                        SET role = $1, updated_at = $2 
                        WHERE id = $3
                    """, new_role.name, datetime.now(timezone.utc), user_id)
            
            # Update Neo4j
            if self.neo4j_driver:
                async with self.neo4j_driver.session() as session:
                    await session.run("""
                        MATCH (u:User {id: $user_id})
                        SET u.role = $role, u.updated_at = datetime()
                    """, user_id=user_id, role=new_role.name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user role for {user_id}: {e}")
            return False
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        
        if not self.postgres_pool:
            return False
        
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET last_login_at = $1, updated_at = $2 
                    WHERE id = $3
                """, datetime.now(timezone.utc), datetime.now(timezone.utc), user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update last login for {user_id}: {e}")
            return False
    
    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        role_filter: Optional[UserRole] = None,
        active_only: bool = True
    ) -> List[AuthUser]:
        """List users with filtering"""
        
        if not self.postgres_pool:
            return []
        
        try:
            query = """
                SELECT id, email, name, role, provider, provider_id,
                       is_active, created_at, last_login_at
                FROM users
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if active_only:
                param_count += 1
                query += f" AND is_active = ${param_count}"
                params.append(True)
            
            if role_filter:
                param_count += 1
                query += f" AND role = ${param_count}"
                params.append(role_filter.name)
            
            query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                return [self._row_to_auth_user(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user (mark as inactive)"""
        
        if not self.postgres_pool:
            return False
        
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET is_active = false, updated_at = $1 
                    WHERE id = $2
                """, datetime.now(timezone.utc), user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    def _row_to_auth_user(self, row) -> AuthUser:
        """Convert database row to AuthUser object"""
        
        role = UserRole[row['role']]
        provider = AuthProvider(row['provider'])
        permissions = get_role_permissions(role)
        
        return AuthUser(
            id=row['id'],
            email=row['email'],
            name=row['name'],
            role=role,
            permissions=permissions,
            provider=provider,
            provider_id=row['provider_id'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            last_login=row.get('last_login_at')
        )


class UserProfileRepository:
    """
    User profile repository for Neo4j
    
    Manages extended user profiles, relationships, and graph data.
    """
    
    def __init__(self, neo4j_driver=None):
        self.neo4j_driver = neo4j_driver
    
    async def create_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """Create user profile in Neo4j"""
        
        if not self.neo4j_driver:
            return False
        
        try:
            async with self.neo4j_driver.session() as session:
                await session.run("""
                    MATCH (u:User {id: $user_id})
                    SET u.department = $department,
                        u.title = $title,
                        u.phone = $phone,
                        u.location = $location,
                        u.timezone = $timezone,
                        u.preferences = $preferences,
                        u.metadata = $metadata,
                        u.updated_at = datetime()
                """,
                user_id=user_id,
                department=profile_data.get('department'),
                title=profile_data.get('title'),
                phone=profile_data.get('phone'),
                location=profile_data.get('location'),
                timezone=profile_data.get('timezone', 'UTC'),
                preferences=json.dumps(profile_data.get('preferences', {})),
                metadata=json.dumps(profile_data.get('metadata', {}))
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create profile for {user_id}: {e}")
            return False
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from Neo4j"""
        
        if not self.neo4j_driver:
            return None
        
        try:
            async with self.neo4j_driver.session() as session:
                result = await session.run("""
                    MATCH (u:User {id: $user_id})
                    RETURN u.department as department,
                           u.title as title,
                           u.phone as phone,
                           u.location as location,
                           u.timezone as timezone,
                           u.preferences as preferences,
                           u.metadata as metadata,
                           u.updated_at as updated_at
                """, user_id=user_id)
                
                record = await result.single()
                
                if not record:
                    return None
                
                return UserProfile(
                    user_id=user_id,
                    department=record['department'],
                    title=record['title'],
                    phone=record['phone'],
                    location=record['location'],
                    timezone=record['timezone'] or 'UTC',
                    preferences=json.loads(record['preferences'] or '{}'),
                    metadata=json.loads(record['metadata'] or '{}'),
                    updated_at=record['updated_at']
                )
                
        except Exception as e:
            logger.error(f"Failed to get profile for {user_id}: {e}")
            return None


class AuditLogRepository:
    """
    Audit log repository for PostgreSQL
    
    Manages comprehensive audit logging for compliance and security monitoring.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool = None):
        self.postgres_pool = postgres_pool
    
    async def create_audit_log(self, audit_entry: AuditLogEntry) -> bool:
        """Store audit log entry in PostgreSQL"""
        
        if not self.postgres_pool:
            return False
        
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO audit_logs (
                        id, timestamp, user_id, session_id, action, resource,
                        resource_id, data_sensitivity, success, ip_address,
                        user_agent, details, risk_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                audit_entry.id,
                audit_entry.timestamp,
                audit_entry.user_id,
                audit_entry.session_id,
                audit_entry.action.value,
                audit_entry.resource,
                audit_entry.resource_id,
                audit_entry.data_sensitivity.name if audit_entry.data_sensitivity else None,
                audit_entry.success,
                audit_entry.ip_address,
                audit_entry.user_agent,
                json.dumps(audit_entry.details),
                audit_entry.risk_score
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return False
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """Retrieve audit logs with filtering"""
        
        if not self.postgres_pool:
            return []
        
        try:
            query = """
                SELECT id, timestamp, user_id, session_id, action, resource,
                       resource_id, data_sensitivity, success, ip_address,
                       user_agent, details, risk_score
                FROM audit_logs
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if user_id:
                param_count += 1
                query += f" AND user_id = ${param_count}"
                params.append(user_id)
            
            if action:
                param_count += 1
                query += f" AND action = ${param_count}"
                params.append(action.value)
            
            if start_time:
                param_count += 1
                query += f" AND timestamp >= ${param_count}"
                params.append(start_time)
            
            if end_time:
                param_count += 1
                query += f" AND timestamp <= ${param_count}"
                params.append(end_time)
            
            query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                audit_logs = []
                for row in rows:
                    audit_logs.append(AuditLogEntry(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        action=AuditAction(row['action']),
                        resource=row['resource'],
                        resource_id=row['resource_id'],
                        data_sensitivity=DataSensitivity[row['data_sensitivity']] if row['data_sensitivity'] else None,
                        success=row['success'],
                        ip_address=row['ip_address'],
                        user_agent=row['user_agent'],
                        details=json.loads(row['details'] or '{}'),
                        risk_score=row['risk_score']
                    ))
                
                return audit_logs
                
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []


class SessionRepository:
    """
    Session repository for Redis
    
    Manages user sessions with expiration and cleanup.
    """
    
    def __init__(self, redis_client: aioredis.Redis = None):
        self.redis_client = redis_client
        self.session_timeout = timedelta(hours=24)
    
    async def create_session(self, session: SessionData) -> bool:
        """Store session in Redis"""
        
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session.session_id}"
            session_data = session.dict()
            
            await self.redis_client.setex(
                session_key,
                int(self.session_timeout.total_seconds()),
                json.dumps(session_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session {session.session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session from Redis"""
        
        if not self.redis_client:
            return None
        
        try:
            session_key = f"session:{session_id}"
            session_data = await self.redis_client.get(session_key)
            
            if session_data:
                data = json.loads(session_data)
                return SessionData(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(self, session: SessionData) -> bool:
        """Update session in Redis"""
        
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session.session_id}"
            session_data = session.dict()
            
            # Update last accessed time
            session.last_accessed = datetime.now(timezone.utc)
            
            await self.redis_client.setex(
                session_key,
                int(self.session_timeout.total_seconds()),
                json.dumps(session_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session.session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session_id}"
            await self.redis_client.delete(session_key)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False


# Database schema initialization scripts
POSTGRES_SCHEMA = """
-- Users table for authentication data
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_id VARCHAR(255) NOT NULL,
    password_hash TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Audit logs table for compliance tracking
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id UUID,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    resource_id VARCHAR(255),
    data_sensitivity VARCHAR(50),
    success BOOLEAN NOT NULL,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    risk_score FLOAT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
"""


async def initialize_postgres_schema(postgres_pool: asyncpg.Pool):
    """Initialize PostgreSQL schema"""
    
    try:
        async with postgres_pool.acquire() as conn:
            await conn.execute(POSTGRES_SCHEMA)
        
        logger.info("PostgreSQL schema initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL schema: {e}")
        raise