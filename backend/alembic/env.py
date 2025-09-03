"""
OneVice Database Migration Environment
SQLAlchemy configuration for Alembic migrations
"""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool, engine_from_config
from alembic import context

# Add the app directory to the path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import our models and database setup
from app.core.config import settings
from app.core.database import Base

# Import all models so they register with Base.metadata
from app.models.user import User
from app.models.auth import Role, Permission, UserRole, role_permissions
from app.models.audit import AuditLog, AuditSummary

# Set target metadata for autogenerate support
target_metadata = Base.metadata

# Set database URL from environment
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()




def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Convert async URL to sync URL for migration
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql+asyncpg://"):
        sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    else:
        sync_database_url = database_url

    # Use synchronous engine for migrations
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = sync_database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()