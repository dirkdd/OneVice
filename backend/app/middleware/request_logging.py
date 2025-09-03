"""
OneVice Request Logging Middleware
Structured logging for all HTTP requests and responses with performance metrics
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

from app.core.logging import RequestLogger, PerformanceLogger, get_logger


logger = get_logger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses with performance metrics"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        # Paths to exclude from logging (e.g., health checks, metrics endpoints)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with timing information"""
        start_time = time.time()
        
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate correlation ID if not already present
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        user_id = getattr(request.state, 'user_id', None)
        
        # Create request logger
        request_logger = RequestLogger(
            correlation_id=correlation_id,
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Log incoming request
        request_logger.info(
            "Incoming request",
            request_method=request.method,
            request_path=str(request.url.path),
            request_query_params=dict(request.query_params) if request.query_params else None,
            request_headers=self._sanitize_headers(dict(request.headers)),
            request_size=request.headers.get("content-length"),
            content_type=request.headers.get("content-type")
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log failed request
            duration_ms = (time.time() - start_time) * 1000
            
            request_logger.error(
                "Request failed with exception",
                request_method=request.method,
                request_path=str(request.url.path),
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
        
        # Calculate response time
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        request_logger.info(
            "Request completed",
            request_method=request.method,
            request_path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            response_size=response.headers.get("content-length"),
            response_headers=self._sanitize_response_headers(dict(response.headers))
        )
        
        # Log performance metrics
        performance_logger = PerformanceLogger(correlation_id)
        performance_logger.log_api_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id
        )
        
        # Add correlation ID to response headers for tracing
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{round(duration_ms, 2)}ms"
        
        return response
    
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
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive headers from logging"""
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "clerk-api-key",
            "openai-api-key"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_response_headers(self, headers: dict) -> dict:
        """Remove sensitive response headers from logging"""
        sensitive_headers = {
            "set-cookie",
            "authorization"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized


class DetailedRequestLoggingMiddleware(RequestLoggingMiddleware):
    """Extended request logging middleware with request/response body logging"""
    
    def __init__(self, app, exclude_paths: list = None, log_request_body: bool = False, 
                 log_response_body: bool = False, max_body_size: int = 1000):
        super().__init__(app, exclude_paths)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with optional body logging"""
        start_time = time.time()
        
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate correlation ID if not already present
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        user_id = getattr(request.state, 'user_id', None)
        
        # Create request logger
        request_logger = RequestLogger(
            correlation_id=correlation_id,
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Get request body if enabled
        request_body = None
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    request_body = body.decode('utf-8')
                else:
                    request_body = f"<body too large: {len(body)} bytes>"
            except Exception as e:
                request_body = f"<could not read body: {str(e)}>"
        
        # Log incoming request with optional body
        log_data = {
            "request_method": request.method,
            "request_path": str(request.url.path),
            "request_query_params": dict(request.query_params) if request.query_params else None,
            "request_headers": self._sanitize_headers(dict(request.headers)),
            "request_size": request.headers.get("content-length"),
            "content_type": request.headers.get("content-type")
        }
        
        if request_body is not None:
            log_data["request_body"] = self._sanitize_request_body(request_body)
        
        request_logger.info("Incoming request with details", **log_data)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log failed request
            duration_ms = (time.time() - start_time) * 1000
            
            request_logger.error(
                "Request failed with exception",
                request_method=request.method,
                request_path=str(request.url.path),
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                request_body=self._sanitize_request_body(request_body) if request_body else None
            )
            raise
        
        # Calculate response time
        duration_ms = (time.time() - start_time) * 1000
        
        # Get response body if enabled
        response_body = None
        if self.log_response_body and hasattr(response, 'body'):
            try:
                if len(response.body) <= self.max_body_size:
                    response_body = response.body.decode('utf-8')
                else:
                    response_body = f"<response too large: {len(response.body)} bytes>"
            except Exception:
                response_body = "<could not read response body>"
        
        # Log response with optional body
        log_data = {
            "request_method": request.method,
            "request_path": str(request.url.path),
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size": response.headers.get("content-length"),
            "response_headers": self._sanitize_response_headers(dict(response.headers))
        }
        
        if response_body is not None:
            log_data["response_body"] = response_body
        
        request_logger.info("Request completed with details", **log_data)
        
        # Log performance metrics
        performance_logger = PerformanceLogger(correlation_id)
        performance_logger.log_api_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id
        )
        
        # Add correlation ID to response headers for tracing
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{round(duration_ms, 2)}ms"
        
        return response
    
    def _sanitize_request_body(self, body: str) -> str:
        """Remove sensitive data from request body"""
        if not body:
            return body
        
        # Basic sanitization for common sensitive fields
        sensitive_patterns = [
            ("password", "[REDACTED]"),
            ("secret", "[REDACTED]"),
            ("token", "[REDACTED]"),
            ("api_key", "[REDACTED]"),
            ("apikey", "[REDACTED]")
        ]
        
        sanitized_body = body
        for pattern, replacement in sensitive_patterns:
            # Simple JSON field replacement (not comprehensive, but basic protection)
            import re
            sanitized_body = re.sub(
                f'"{pattern}"\\s*:\\s*"[^"]*"', 
                f'"{pattern}": "{replacement}"', 
                sanitized_body, 
                flags=re.IGNORECASE
            )
        
        return sanitized_body