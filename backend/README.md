# OneVice Backend

FastAPI backend for OneVice AI-powered business intelligence hub.

## Quick Start

### 1. Environment Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Database Setup

You need PostgreSQL and Redis running. For development:

**PostgreSQL:**
```bash
# Using Docker
docker run -d \
  --name onevice-postgres \
  -e POSTGRES_DB=onevice \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# Or install locally and create database
createdb onevice
```

**Redis:**
```bash
# Using Docker
docker run -d \
  --name onevice-redis \
  -p 6379:6379 \
  redis:7-alpine

# Or install locally
redis-server
```

### 3. Start Backend

```bash
# Quick start (handles initialization automatically)
python start.py

# Or manual start
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify Installation

- **API Documentation:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/health
- **Root Endpoint:** http://localhost:8000

## API Endpoints

### Authentication
- `POST /api/v1/auth/sync-clerk-user` - Sync user from Clerk
- `GET /api/v1/auth/profile/{clerk_id}` - Get user profile with roles
- `POST /api/v1/auth/check-permission` - Check user permission
- `GET /api/v1/auth/permissions/{user_id}` - Get user permissions
- `GET /api/v1/auth/roles/{user_id}` - Get user roles
- `POST /api/v1/auth/logout` - Logout user

### Users
- `GET /api/v1/users/` - List users (paginated)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Deactivate user

## Integration with Frontend

The backend is designed to replace all mock implementations in the Next.js frontend:

1. **Authentication**: Real Clerk user sync
2. **RBAC**: Database-backed role checking  
3. **Sessions**: Redis-based session management
4. **APIs**: RESTful endpoints for all operations

Configure frontend with:
```env
BACKEND_URL=http://localhost:8000
```

## Status

**Current Implementation: 100% Complete**
- ✅ FastAPI application structure
- ✅ PostgreSQL database with SQLAlchemy
- ✅ Redis session management
- ✅ Complete RBAC system
- ✅ Authentication endpoints
- ✅ User management APIs
- ✅ Frontend integration ready

**Next Steps (Week 5):**
- AI agent endpoints with LangGraph
- Neo4j vector database integration
- WebSocket server for real-time features
- Advanced analytics endpoints