"""
OneVice Database Configuration
SQLAlchemy setup for PostgreSQL with async support
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, text
from app.core.config import settings
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Dependency to get database session
    Used in FastAPI endpoints with Depends(get_db)
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to register them with Base
            from app.models.user import User
            from auth.models import UserRole, PermissionSet, PermissionAction
            from app.models.audit import AuditLog, AuditSummary
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
            
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise

async def drop_tables():
    """Drop all database tables (for testing)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("🗑️ All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise

async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def init_database():
    """Initialize database with default data"""
    from auth.models import PermissionSet, PermissionAction
    from app.services.auth_service import create_default_roles_and_permissions
    
    try:
        async with async_session() as session:
            # Create default roles and permissions
            await create_default_roles_and_permissions(session)
            logger.info("✅ Database initialized with default data")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

# Database health check
async def health_check():
    """Check database health status"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "database": "healthy",
            "connection": "active",
            "engine": "postgresql+asyncpg"
        }
    except Exception as e:
        return {
            "database": "unhealthy", 
            "error": str(e),
            "connection": "failed"
        }