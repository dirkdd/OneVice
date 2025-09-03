"""
Simplified OneVice Backend for Development

Basic FastAPI application without complex auth system.
Use this for frontend development and testing.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Create FastAPI app
app = FastAPI(
    title="OneVice Backend API",
    description="AI-powered business intelligence platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("JWT_SECRET_KEY", "development-secret-key-change-in-production")
)

# Basic health check
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "OneVice Backend is running"}

# Basic auth endpoint for frontend testing
@app.post("/auth/login")
def login(credentials: dict):
    """Simple auth endpoint for frontend testing"""
    return {
        "access_token": "test-jwt-token",
        "token_type": "bearer",
        "user": {
            "id": "test-user-id",
            "email": credentials.get("email", "test@example.com"),
            "role": "admin"
        }
    }

@app.get("/auth/me")
def get_current_user():
    """Get current user info"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "admin",
        "name": "Test User"
    }

# Basic API endpoints for frontend testing
@app.get("/api/projects")
def get_projects():
    return {
        "items": [
            {
                "id": "1",
                "title": "Test Project",
                "description": "A test project",
                "status": "active",
                "type": "documentary",
                "budget": {"total": 100000},
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 1,
        "page": 1,
        "pages": 1
    }

@app.get("/api/conversations/recent")
def get_recent_conversations():
    return [
        {
            "id": "1",
            "title": "Test Conversation",
            "context": "home",
            "message_count": 5,
            "updated_at": "2024-01-01T00:00:00Z",
            "last_message_preview": "This is a test message"
        }
    ]

# WebSocket endpoint placeholder
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    await websocket.send_text("WebSocket connected")
    await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)