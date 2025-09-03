"""
OneVice Custom Exception Classes
Structured exception hierarchy for better error handling and API responses
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import uuid


class OneViceException(Exception):
    """Base exception class for OneVice application"""
    
    def __init__(
        self, 
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        correlation_id: str = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "correlation_id": self.correlation_id
            }
        }


class OneViceHTTPException(HTTPException):
    """Base HTTP exception for OneVice API responses"""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        correlation_id: str = None,
        headers: Dict[str, str] = None
    ):
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        
        detail = {
            "error": {
                "code": self.error_code,
                "message": message,
                "details": self.details,
                "correlation_id": self.correlation_id
            }
        }
        
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# Authentication and Authorization Exceptions
class AuthenticationError(OneViceHTTPException):
    """Authentication failed - invalid credentials or tokens"""
    
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTHENTICATION_FAILED",
            details=details,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(OneViceHTTPException):
    """Authorization failed - insufficient permissions"""
    
    def __init__(self, message: str = "Insufficient permissions", 
                 required_permission: str = None, user_role: str = None):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        if user_role:
            details["user_role"] = user_role
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="AUTHORIZATION_FAILED",
            details=details
        )


class InvalidTokenError(AuthenticationError):
    """Invalid or expired JWT token"""
    
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message, details={"error_type": "invalid_token"})


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message, details={"error_type": "token_expired"})


# User and Role Management Exceptions
class UserNotFoundError(OneViceHTTPException):
    """User not found in the system"""
    
    def __init__(self, user_identifier: str, identifier_type: str = "id"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"User not found",
            error_code="USER_NOT_FOUND",
            details={
                "user_identifier": user_identifier,
                "identifier_type": identifier_type
            }
        )


class RoleNotFoundError(OneViceHTTPException):
    """Role not found in the system"""
    
    def __init__(self, role_identifier: str, identifier_type: str = "id"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Role not found",
            error_code="ROLE_NOT_FOUND",
            details={
                "role_identifier": role_identifier,
                "identifier_type": identifier_type
            }
        )


class PermissionNotFoundError(OneViceHTTPException):
    """Permission not found in the system"""
    
    def __init__(self, permission_slug: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Permission not found",
            error_code="PERMISSION_NOT_FOUND",
            details={"permission_slug": permission_slug}
        )


class UserAlreadyHasRoleError(OneViceHTTPException):
    """User already has the specified role"""
    
    def __init__(self, user_id: str, role_name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=f"User already has the role",
            error_code="USER_ALREADY_HAS_ROLE",
            details={
                "user_id": user_id,
                "role_name": role_name
            }
        )


class RoleAssignmentError(OneViceHTTPException):
    """Error assigning role to user"""
    
    def __init__(self, message: str, user_id: str = None, role_id: str = None, reason: str = None):
        details = {"reason": reason} if reason else {}
        if user_id:
            details["user_id"] = user_id
        if role_id:
            details["role_id"] = role_id
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="ROLE_ASSIGNMENT_ERROR",
            details=details
        )


# Database and Cache Exceptions
class DatabaseError(OneViceException):
    """Database operation failed"""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""
    
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message=message, details={"error_type": "connection_failed"})


class CacheError(OneViceException):
    """Cache operation failed"""
    
    def __init__(self, message: str, operation: str = None, key: str = None):
        details = {}
        if operation:
            details["operation"] = operation
        if key:
            details["cache_key"] = key
            
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details
        )


class CacheConnectionError(CacheError):
    """Redis cache connection failed"""
    
    def __init__(self, message: str = "Cache connection failed"):
        super().__init__(message=message, details={"error_type": "connection_failed"})


# Validation Exceptions
class ValidationError(OneViceHTTPException):
    """Request validation failed"""
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None):
        details = {}
        if field_errors:
            details["field_errors"] = field_errors
            
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ConfigurationError(OneViceException):
    """Application configuration error"""
    
    def __init__(self, message: str, config_key: str = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


# Rate Limiting Exceptions
class RateLimitExceededError(OneViceHTTPException):
    """Rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, 
                 current_rate: int = None, limit: int = None):
        details = {}
        if current_rate is not None:
            details["current_rate"] = current_rate
        if limit is not None:
            details["limit"] = limit
            
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
            details["retry_after"] = retry_after
            
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            headers=headers
        )


# External Service Exceptions
class ExternalServiceError(OneViceHTTPException):
    """External service error"""
    
    def __init__(self, message: str, service_name: str, service_error: str = None):
        details = {"service_name": service_name}
        if service_error:
            details["service_error"] = service_error
            
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )


class ClerkServiceError(ExternalServiceError):
    """Clerk authentication service error"""
    
    def __init__(self, message: str, clerk_error: str = None):
        super().__init__(
            message=message,
            service_name="Clerk",
            service_error=clerk_error
        )


class Neo4jServiceError(ExternalServiceError):
    """Neo4j graph database service error"""
    
    def __init__(self, message: str, neo4j_error: str = None):
        super().__init__(
            message=message,
            service_name="Neo4j",
            service_error=neo4j_error
        )


# AI and LLM Exceptions
class AIServiceError(OneViceHTTPException):
    """AI service error"""
    
    def __init__(self, message: str, model: str = None, provider: str = None):
        details = {}
        if model:
            details["model"] = model
        if provider:
            details["provider"] = provider
            
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=message,
            error_code="AI_SERVICE_ERROR",
            details=details
        )


class OpenAIServiceError(AIServiceError):
    """OpenAI API service error"""
    
    def __init__(self, message: str, model: str = None, openai_error: str = None):
        details = {"provider": "OpenAI"}
        if model:
            details["model"] = model
        if openai_error:
            details["openai_error"] = openai_error
            
        super().__init__(
            message=message,
            details=details
        )


class AIProcessingError(OneViceException):
    """AI processing or agent orchestration error"""
    
    def __init__(self, message: str, agent_type: str = None, processing_step: str = None):
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        if processing_step:
            details["processing_step"] = processing_step
            
        super().__init__(
            message=message,
            error_code="AI_PROCESSING_ERROR",
            details=details
        )


# Generic HTTP Exceptions with better error formatting
class BadRequestError(OneViceHTTPException):
    """Bad request error"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="BAD_REQUEST",
            details=details
        )


class NotFoundError(OneViceHTTPException):
    """Resource not found error"""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND",
            details=details
        )


class ConflictError(OneViceHTTPException):
    """Resource conflict error"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="CONFLICT",
            details=details
        )


class InternalServerError(OneViceHTTPException):
    """Internal server error"""
    
    def __init__(self, message: str = "Internal server error", details: Dict[str, Any] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            details=details
        )


class ServiceUnavailableError(OneViceHTTPException):
    """Service unavailable error"""
    
    def __init__(self, message: str = "Service temporarily unavailable", retry_after: int = None):
        details = {}
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
            details["retry_after"] = retry_after
            
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
            headers=headers
        )