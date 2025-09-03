"""
OneVice Authentication API Module

FastAPI routers and endpoints for:
- Authentication (login, logout, token refresh)
- User management (CRUD operations)
- Role and permission management
- SSO integration (Clerk, Okta)
- Audit log access
"""

from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .admin_routes import router as admin_router
from .sso_routes import router as sso_router

__all__ = [
    "auth_router",
    "user_router", 
    "admin_router",
    "sso_router",
]