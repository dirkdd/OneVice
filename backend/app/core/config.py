"""
OneVice Configuration Management
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "OneVice Backend"
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="localhost")
    PORT: int = Field(default=8000)
    
    # CORS Origins for development
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000",
        "https://onevice-frontend.vercel.app"  # Production frontend (if deployed)
    ]
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/onevice",
        description="PostgreSQL connection string"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    # Neo4j Configuration (for AI vector search)
    NEO4J_URI: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    NEO4J_USERNAME: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")
    
    # JWT Authentication
    SECRET_KEY: str = Field(
        default="onevice-super-secret-key-change-in-production",
        description="JWT signing secret"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Clerk Integration (for frontend authentication)
    CLERK_SECRET_KEY: str = Field(default="", description="Clerk secret key")
    CLERK_PUBLISHABLE_KEY: str = Field(default="", description="Clerk publishable key")
    CLERK_WEBHOOK_SECRET: str = Field(default="", description="Clerk webhook secret")
    
    # OpenAI Configuration (for AI agents)
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)  # seconds
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


# Create settings instance
settings = Settings()

# Database URL for SQLAlchemy
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Redis configuration
REDIS_CONFIG = {
    "url": settings.REDIS_URL,
    "encoding": "utf-8",
    "decode_responses": True
}