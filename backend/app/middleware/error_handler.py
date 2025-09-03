"""
OneVice Error Handling Middleware
Global error handling with structured logging and consistent API responses
"""

import traceback
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
import uuid

from app.core.exceptions import (
    OneViceException, 
    OneViceHTTPException,
    DatabaseError,
    CacheError,
    InternalServerError
)
from app.core.logging import get_logger, SecurityLogger, RequestLogger


logger = get_logger("error_handler")
security_logger = SecurityLogger()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware with structured logging"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any exceptions"""
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Create request-specific logger
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        request_logger = RequestLogger(
            correlation_id=correlation_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except OneViceHTTPException as e:
            # Our custom HTTP exceptions - already formatted
            request_logger.warning(
                "OneVice HTTP exception",
                error_code=e.error_code,
                status_code=e.status_code,
                error_details=e.details,
                request_path=str(request.url.path),
                request_method=request.method
            )
            
            # Convert to FastAPI HTTPException format
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=e.headers
            )
            
        except HTTPException as e:
            # FastAPI HTTP exceptions
            request_logger.warning(
                "HTTP exception",
                status_code=e.status_code,
                error_detail=str(e.detail),
                request_path=str(request.url.path),
                request_method=request.method
            )
            
            # Format as consistent error response
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": f"HTTP_{e.status_code}",
                        "message": str(e.detail),
                        "correlation_id": correlation_id
                    }
                },
                headers=e.headers
            )
            
        except RequestValidationError as e:
            # Pydantic validation errors
            request_logger.warning(
                "Request validation error",
                validation_errors=e.errors(),
                request_path=str(request.url.path),
                request_method=request.method,
                request_body=await self._get_request_body_safely(request)
            )
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "details": {
                            "validation_errors": e.errors()
                        },
                        "correlation_id": correlation_id
                    }
                }
            )
            
        except SQLAlchemyError as e:
            # Database errors
            request_logger.error(
                "Database error",
                error_type=type(e).__name__,
                error_message=str(e),
                request_path=str(request.url.path),
                request_method=request.method
            )
            
            # Log security event for potential database attacks
            if self._is_suspicious_db_error(e):
                security_logger.log_suspicious_activity(
                    user_id=getattr(request.state, 'user_id', None),
                    activity="suspicious_database_query",
                    details={
                        "error_type": type(e).__name__,
                        "error_message": str(e)[:200],
                        "request_path": str(request.url.path)
                    },
                    ip_address=client_ip,
                    correlation_id=correlation_id
                )
            
            return self._create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="DATABASE_ERROR",
                message="Database operation failed",
                correlation_id=correlation_id,
                details={"error_type": type(e).__name__} if logger.level == "DEBUG" else None
            )
            
        except RedisError as e:
            # Cache errors
            request_logger.error(
                "Cache error",
                error_type=type(e).__name__,
                error_message=str(e),
                request_path=str(request.url.path),
                request_method=request.method
            )
            
            return self._create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="CACHE_ERROR",
                message="Cache operation failed",
                correlation_id=correlation_id,
                details={"error_type": type(e).__name__} if logger.level == "DEBUG" else None
            )
            
        except OneViceException as e:
            # Our custom non-HTTP exceptions
            request_logger.error(
                "OneVice application error",
                error_code=e.error_code,
                error_message=e.message,
                error_details=e.details,
                request_path=str(request.url.path),
                request_method=request.method
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=e.to_dict()
            )
            
        except Exception as e:
            # Unhandled exceptions
            error_traceback = traceback.format_exc()
            
            request_logger.critical(
                "Unhandled exception",
                error_type=type(e).__name__,
                error_message=str(e),
                error_traceback=error_traceback,
                request_path=str(request.url.path),
                request_method=request.method,
                request_headers=dict(request.headers),
                request_query_params=dict(request.query_params)
            )
            
            # Log as security event if it looks suspicious
            if self._is_suspicious_error(e, request):
                security_logger.log_suspicious_activity(
                    user_id=getattr(request.state, 'user_id', None),
                    activity="unhandled_exception",
                    details={
                        "error_type": type(e).__name__,
                        "error_message": str(e)[:200],
                        "request_path": str(request.url.path)
                    },
                    ip_address=client_ip,
                    correlation_id=correlation_id
                )
            
            # Don't expose internal error details in production
            from app.core.config import settings
            if settings.DEBUG:
                details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": error_traceback.split('\n')
                }
            else:
                details = None
            
            return self._create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                correlation_id=correlation_id,
                details=details
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded IP headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client IP
        return getattr(request.client, "host", "unknown")
    
    async def _get_request_body_safely(self, request: Request) -> str:
        """Safely get request body for logging (without consuming it)"""
        try:
            # Only log first 500 characters to avoid huge logs
            body = await request.body()
            body_str = body.decode('utf-8')[:500]
            return body_str if len(body_str) < 500 else body_str + "..."
        except Exception:
            return "Could not read request body"
    
    def _is_suspicious_db_error(self, error: SQLAlchemyError) -> bool:
        """Check if database error looks like a potential attack"""
        error_message = str(error).lower()
        suspicious_patterns = [
            "union select",
            "drop table",
            "delete from",
            "update set",
            "insert into",
            "sql injection",
            "script tag",
            "javascript:",
            "on error resume next"
        ]
        return any(pattern in error_message for pattern in suspicious_patterns)
    
    def _is_suspicious_error(self, error: Exception, request: Request) -> bool:
        """Check if error looks suspicious and should be logged as security event"""
        error_message = str(error).lower()
        request_path = str(request.url.path).lower()
        
        suspicious_patterns = [
            "sql injection",
            "xss",
            "script",
            "javascript:",
            "eval(",
            "exec(",
            "../",
            "passwd",
            "/etc/",
            "cmd.exe",
            "powershell"
        ]
        
        # Check both error message and request path
        return (
            any(pattern in error_message for pattern in suspicious_patterns) or
            any(pattern in request_path for pattern in suspicious_patterns)
        )
    
    def _create_error_response(
        self, 
        status_code: int, 
        error_code: str, 
        message: str, 
        correlation_id: str,
        details: Dict[str, Any] = None
    ) -> JSONResponse:
        """Create standardized error response"""
        error_response = {
            "error": {
                "code": error_code,
                "message": message,
                "correlation_id": correlation_id
            }
        }
        
        if details:
            error_response["error"]["details"] = details
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )


# Exception handlers for specific FastAPI integration
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        "Request validation failed",
        correlation_id=correlation_id,
        validation_errors=exc.errors(),
        request_path=str(request.url.path),
        request_method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": exc.errors()
                },
                "correlation_id": correlation_id
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent formatting"""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        "HTTP exception",
        correlation_id=correlation_id,
        status_code=exc.status_code,
        error_detail=str(exc.detail),
        request_path=str(request.url.path),
        request_method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "correlation_id": correlation_id
            }
        },
        headers=exc.headers
    )