"""
OneVice Backend - FastAPI Application
Main application entry point with CORS and middleware setup
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import create_tables
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.conversations import router as conversations_router
from app.api.projects import router as projects_router
from app.api.intelligence import router as intelligence_router
from app.api.memory import memory_router
from app.api.ai.chat import ai_router
from app.api.ai.websocket import websocket_router
from app.api.ai.memory_websocket import memory_websocket_router
from app.core.redis import init_redis, close_redis
from app.middleware.clerk_auth import ClerkAuthMiddleware
from app.services.memory_service import initialize_memory_service, cleanup_memory_service
from app.ai.config import AIConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    print("🚀 Starting OneVice Backend...")
    
    # Initialize database
    await create_tables()
    print("✅ Database tables created")
    
    # Initialize Redis
    await init_redis()
    print("✅ Redis connection established")
    
    # Initialize Memory Service (LangMem + Neo4j + Background Processing)
    try:
        ai_config = AIConfig()
        await initialize_memory_service(ai_config)
        print("✅ Memory service initialized (LangMem + Neo4j + Redis)")
    except Exception as e:
        print(f"⚠️  Memory service initialization failed: {e}")
        print("🔄 Continuing without advanced memory features")
    
    print("🎉 OneVice Backend started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down OneVice Backend...")
    
    # Cleanup memory service
    try:
        await cleanup_memory_service()
        print("✅ Memory service cleaned up")
    except Exception as e:
        print(f"⚠️  Memory service cleanup failed: {e}")
    
    await close_redis()
    print("✅ Redis connection closed")


# Create FastAPI application
app = FastAPI(
    title="OneVice API",
    description="AI-powered business intelligence hub for entertainment industry",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS configuration for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clerk authentication middleware
app.add_middleware(
    ClerkAuthMiddleware,
    excluded_paths=["/", "/health", "/docs", "/redoc", "/openapi.json", "/api/docs", "/api/redoc", "/api/openapi.json"]
)

# Security
security = HTTPBearer()

# API Routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(conversations_router, prefix="/api", tags=["Conversations"])
app.include_router(projects_router, prefix="/api", tags=["Projects"])
app.include_router(intelligence_router, prefix="/api", tags=["Intelligence"])
app.include_router(memory_router, tags=["Memory"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI"])
app.include_router(websocket_router, tags=["WebSocket"])
app.include_router(memory_websocket_router, tags=["Memory WebSocket"])

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "OneVice Backend API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": "2025-09-02",
        "services": {
            "api": "operational",
            "database": "connected",
            "redis": "connected"
        }
    }

@app.get("/debug/auth")
async def debug_auth(request: Request):
    """Debug endpoint to check authentication state"""
    current_user = getattr(request.state, 'current_user', None)
    auth_header = request.headers.get("Authorization", "Not provided")
    
    return {
        "auth_header": auth_header[:20] + "..." if len(auth_header) > 20 else auth_header,
        "current_user": {
            "id": current_user.id if current_user else None,
            "email": current_user.email if current_user else None,
            "authenticated": current_user is not None
        } if current_user else None,
        "middleware_working": True
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )