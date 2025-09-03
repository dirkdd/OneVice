#!/usr/bin/env python3
"""
OneVice Backend Startup Script
Quick start script for development with database initialization
"""

import asyncio
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import create_tables, init_database, test_connection
from app.core.redis import init_redis
import uvicorn

async def initialize_backend():
    """Initialize backend services"""
    print("🚀 Initializing OneVice Backend...")
    
    try:
        # Test database connection
        print("📊 Testing database connection...")
        db_connected = await test_connection()
        if not db_connected:
            print("❌ Database connection failed. Please check your DATABASE_URL configuration.")
            return False
        
        # Create tables
        print("🗄️ Creating database tables...")
        await create_tables()
        
        # Initialize Redis
        print("⚡ Initializing Redis...")
        await init_redis()
        
        # Initialize default data
        print("🔧 Setting up default roles and permissions...")
        await init_database()
        
        print("✅ Backend initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🌟 Starting OneVice Backend Server...")
    print("📝 API Documentation: http://localhost:8000/api/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🔌 CORS configured for http://localhost:3000")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

async def main():
    """Main startup function"""
    # Initialize backend
    success = await initialize_backend()
    if not success:
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    asyncio.run(main())