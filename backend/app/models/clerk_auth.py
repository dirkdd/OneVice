"""
Simple Authentication Models for Clerk Integration

These models provide a simple interface for working with Clerk-authenticated
users in the FastAPI application. They are designed to be compatible with
the existing Optional[AuthUser] patterns used throughout the API endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class AuthUser(BaseModel):
    """
    Simple user model for Clerk-authenticated users.
    
    This represents the authenticated user data extracted from Clerk JWT tokens.
    It's designed to be lightweight and compatible with existing API endpoint
    patterns that expect Optional[AuthUser].
    """
    
    id: str
    email: str
    name: str
    
    def __str__(self) -> str:
        return f"AuthUser(id={self.id}, email={self.email}, name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (has valid ID)"""
        return bool(self.id)


class AuthContext(BaseModel):
    """
    Authentication context for request processing.
    
    This provides additional context about the authentication state
    beyond just the user object.
    """
    
    user: Optional[AuthUser] = None
    is_authenticated: bool = False
    auth_method: str = "clerk_jwt"
    
    def __init__(self, user: Optional[AuthUser] = None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.is_authenticated = user is not None and user.is_authenticated
    
    def __str__(self) -> str:
        return f"AuthContext(authenticated={self.is_authenticated}, user={self.user})"