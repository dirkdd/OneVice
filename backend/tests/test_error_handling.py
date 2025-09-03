"""
Test suite for OneVice Error Handling
Comprehensive tests for custom exceptions and error middleware
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from app.core.exceptions import (
    OneViceException,
    OneViceHTTPException,
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
    UserNotFoundError,
    DatabaseError,
    CacheError,
    ValidationError,
    RateLimitExceededError,
    ExternalServiceError,
    AIServiceError,
    BadRequestError,
    NotFoundError,
    ConflictError,
    InternalServerError
)
from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    validation_exception_handler,
    http_exception_handler
)


class TestOneViceExceptions:
    """Test custom OneVice exception classes"""
    
    def test_onevice_exception_basic(self):
        """Test basic OneVice exception"""
        
        exc = OneViceException(
            message="Something went wrong",
            error_code="TEST_ERROR",
            details={"field": "value"},
            correlation_id="test_correlation_123"
        )
        
        assert exc.message == "Something went wrong"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details["field"] == "value"
        assert exc.correlation_id == "test_correlation_123"
        
        # Test to_dict method
        error_dict = exc.to_dict()
        assert error_dict["error"]["code"] == "TEST_ERROR"
        assert error_dict["error"]["message"] == "Something went wrong"
        assert error_dict["error"]["details"]["field"] == "value"
        assert error_dict["error"]["correlation_id"] == "test_correlation_123"
    
    def test_onevice_exception_defaults(self):
        """Test OneVice exception with default values"""
        
        exc = OneViceException("Test error")
        
        assert exc.error_code == "ONEVICEEXCEPTION"  # Default from class name
        assert exc.details == {}
        assert exc.correlation_id is not None  # Should generate UUID
    
    def test_onevice_http_exception(self):
        """Test OneVice HTTP exception"""
        
        exc = OneViceHTTPException(
            status_code=400,
            message="Bad request",
            error_code="INVALID_INPUT",
            details={"field": "email", "issue": "invalid format"},
            headers={"X-Custom": "header"}
        )
        
        assert exc.status_code == 400
        assert exc.error_code == "INVALID_INPUT"
        assert exc.details["field"] == "email"
        assert exc.headers["X-Custom"] == "header"
        
        # Test detail structure
        detail = exc.detail
        assert detail["error"]["code"] == "INVALID_INPUT"
        assert detail["error"]["message"] == "Bad request"
        assert detail["error"]["details"]["field"] == "email"


class TestAuthenticationExceptions:
    """Test authentication-related exceptions"""
    
    def test_authentication_error(self):
        """Test authentication error"""
        
        exc = AuthenticationError("Invalid credentials", details={"reason": "wrong_password"})
        
        assert exc.status_code == 401
        assert exc.error_code == "AUTHENTICATION_FAILED"
        assert exc.headers["WWW-Authenticate"] == "Bearer"
        assert exc.details["reason"] == "wrong_password"
    
    def test_authentication_error_defaults(self):
        """Test authentication error with defaults"""
        
        exc = AuthenticationError()
        
        assert exc.detail["error"]["message"] == "Authentication failed"
        assert exc.status_code == 401
    
    def test_authorization_error(self):
        """Test authorization error"""
        
        exc = AuthorizationError(
            message="Access denied",
            required_permission="admin_access",
            user_role="user"
        )
        
        assert exc.status_code == 403
        assert exc.error_code == "AUTHORIZATION_FAILED"
        assert exc.details["required_permission"] == "admin_access"
        assert exc.details["user_role"] == "user"
    
    def test_invalid_token_error(self):
        """Test invalid token error"""
        
        exc = InvalidTokenError()
        
        assert exc.status_code == 401
        assert exc.details["error_type"] == "invalid_token"
        assert "invalid or expired" in exc.detail["error"]["message"].lower()
    
    def test_token_expired_error(self):
        """Test token expired error"""
        
        exc = TokenExpiredError("JWT expired")
        
        assert exc.status_code == 401
        assert exc.details["error_type"] == "token_expired"
        assert exc.detail["error"]["message"] == "JWT expired"


class TestUserExceptions:
    """Test user-related exceptions"""
    
    def test_user_not_found_error(self):
        """Test user not found error"""
        
        exc = UserNotFoundError("user_123", "id")
        
        assert exc.status_code == 404
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.details["user_identifier"] == "user_123"
        assert exc.details["identifier_type"] == "id"
        assert "User not found" in exc.detail["error"]["message"]
    
    def test_user_not_found_error_email(self):
        """Test user not found by email"""
        
        exc = UserNotFoundError("user@example.com", "email")
        
        assert exc.details["user_identifier"] == "user@example.com"
        assert exc.details["identifier_type"] == "email"


class TestDatabaseExceptions:
    """Test database-related exceptions"""
    
    def test_database_error(self):
        """Test database error"""
        
        exc = DatabaseError(
            message="Connection failed",
            operation="INSERT",
            table="users"
        )
        
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.message == "Connection failed"
        assert exc.details["operation"] == "INSERT"
        assert exc.details["table"] == "users"
    
    def test_database_error_minimal(self):
        """Test database error with minimal info"""
        
        exc = DatabaseError("Query failed")
        
        assert exc.message == "Query failed"
        assert exc.details == {}


class TestCacheExceptions:
    """Test cache-related exceptions"""
    
    def test_cache_error(self):
        """Test cache error"""
        
        exc = CacheError(
            message="Redis timeout",
            operation="GET",
            key="user:123:permissions"
        )
        
        assert exc.error_code == "CACHE_ERROR"
        assert exc.message == "Redis timeout"
        assert exc.details["operation"] == "GET"
        assert exc.details["cache_key"] == "user:123:permissions"


class TestValidationExceptions:
    """Test validation-related exceptions"""
    
    def test_validation_error(self):
        """Test validation error"""
        
        field_errors = {
            "email": "Invalid email format",
            "password": "Password too short"
        }
        
        exc = ValidationError("Validation failed", field_errors)
        
        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field_errors"]["email"] == "Invalid email format"
        assert exc.details["field_errors"]["password"] == "Password too short"


class TestRateLimitExceptions:
    """Test rate limiting exceptions"""
    
    def test_rate_limit_exceeded_error(self):
        """Test rate limit exceeded error"""
        
        exc = RateLimitExceededError(
            message="Too many requests",
            retry_after=60,
            current_rate=101,
            limit=100
        )
        
        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.details["retry_after"] == 60
        assert exc.details["current_rate"] == 101
        assert exc.details["limit"] == 100
        assert exc.headers["Retry-After"] == "60"
    
    def test_rate_limit_exceeded_minimal(self):
        """Test rate limit error with minimal info"""
        
        exc = RateLimitExceededError()
        
        assert exc.detail["error"]["message"] == "Rate limit exceeded"
        assert exc.status_code == 429


class TestExternalServiceExceptions:
    """Test external service exceptions"""
    
    def test_external_service_error(self):
        """Test external service error"""
        
        exc = ExternalServiceError(
            message="Service unavailable",
            service_name="PaymentGateway",
            service_error="Connection timeout"
        )
        
        assert exc.status_code == 502
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.details["service_name"] == "PaymentGateway"
        assert exc.details["service_error"] == "Connection timeout"
    
    def test_ai_service_error(self):
        """Test AI service error"""
        
        exc = AIServiceError(
            message="Model request failed",
            model="gpt-4",
            provider="OpenAI"
        )
        
        assert exc.status_code == 502
        assert exc.error_code == "AI_SERVICE_ERROR"
        assert exc.details["model"] == "gpt-4"
        assert exc.details["provider"] == "OpenAI"


class TestGenericHTTPExceptions:
    """Test generic HTTP exceptions"""
    
    def test_bad_request_error(self):
        """Test bad request error"""
        
        exc = BadRequestError("Invalid request", details={"field": "missing"})
        
        assert exc.status_code == 400
        assert exc.error_code == "BAD_REQUEST"
        assert exc.details["field"] == "missing"
    
    def test_not_found_error(self):
        """Test not found error"""
        
        exc = NotFoundError("Resource not found", resource_type="user", resource_id="123")
        
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert exc.details["resource_type"] == "user"
        assert exc.details["resource_id"] == "123"
    
    def test_conflict_error(self):
        """Test conflict error"""
        
        exc = ConflictError("User already exists", details={"email": "test@example.com"})
        
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"
        assert exc.details["email"] == "test@example.com"
    
    def test_internal_server_error(self):
        """Test internal server error"""
        
        exc = InternalServerError("Unexpected error", details={"trace_id": "abc123"})
        
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_SERVER_ERROR"
        assert exc.details["trace_id"] == "abc123"


class TestErrorHandlerMiddleware:
    """Test error handling middleware"""
    
    @pytest.fixture
    def middleware(self):
        """Create error handler middleware instance"""
        mock_app = Mock()
        return ErrorHandlerMiddleware(mock_app)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request"""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.headers = {"user-agent": "TestClient/1.0"}
        request.client.host = "192.168.1.100"
        request.query_params = {}
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_request):
        """Test middleware with successful request"""
        
        async def call_next(request):
            response = Mock()
            response.status_code = 200
            return response
        
        response = await middleware.dispatch(mock_request, call_next)
        
        # Should pass through successful responses
        assert response.status_code == 200
        assert hasattr(mock_request.state, 'correlation_id')
    
    @pytest.mark.asyncio
    async def test_onevice_http_exception(self, middleware, mock_request):
        """Test middleware handling OneVice HTTP exception"""
        
        async def call_next(request):
            raise AuthenticationError("Invalid token", details={"token": "expired"})
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger.warning = Mock()
            mock_logger_class.return_value = mock_logger
            
            response = await middleware.dispatch(mock_request, call_next)
            
            # Verify error logging
            mock_logger.warning.assert_called_once()
            
            # Verify response format
            assert isinstance(response, JSONResponse)
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_http_exception(self, middleware, mock_request):
        """Test middleware handling standard HTTP exception"""
        
        async def call_next(request):
            raise HTTPException(status_code=404, detail="Not found")
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger.warning = Mock()
            mock_logger_class.return_value = mock_logger
            
            response = await middleware.dispatch(mock_request, call_next)
            
            # Verify response structure
            assert isinstance(response, JSONResponse)
            assert response.status_code == 404
            
            # Check response content
            content = json.loads(response.body)
            assert content["error"]["code"] == "HTTP_404"
            assert content["error"]["message"] == "Not found"
            assert "correlation_id" in content["error"]
    
    @pytest.mark.asyncio
    async def test_validation_error(self, middleware, mock_request):
        """Test middleware handling validation error"""
        
        mock_request.body = AsyncMock(return_value=b'{"invalid": "json"}')
        
        async def call_next(request):
            from pydantic import ValidationError
            raise RequestValidationError([])
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger.warning = Mock()
            mock_logger_class.return_value = mock_logger
            
            response = await middleware.dispatch(mock_request, call_next)
            
            assert response.status_code == 422
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "VALIDATION_ERROR"
            assert content["error"]["message"] == "Request validation failed"
    
    @pytest.mark.asyncio
    async def test_database_error(self, middleware, mock_request):
        """Test middleware handling database error"""
        
        async def call_next(request):
            raise SQLAlchemyError("Database connection failed")
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class, \
             patch('app.middleware.error_handler.SecurityLogger') as mock_security_class:
            
            mock_logger = Mock()
            mock_logger.error = Mock()
            mock_logger_class.return_value = mock_logger
            
            mock_security = Mock()
            mock_security_class.return_value = mock_security
            
            response = await middleware.dispatch(mock_request, call_next)
            
            # Verify error logging
            mock_logger.error.assert_called_once()
            
            assert response.status_code == 500
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "DATABASE_ERROR"
    
    @pytest.mark.asyncio
    async def test_redis_error(self, middleware, mock_request):
        """Test middleware handling Redis error"""
        
        async def call_next(request):
            raise RedisError("Redis connection timeout")
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger.error = Mock()
            mock_logger_class.return_value = mock_logger
            
            response = await middleware.dispatch(mock_request, call_next)
            
            assert response.status_code == 500
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "CACHE_ERROR"
    
    @pytest.mark.asyncio
    async def test_unhandled_exception(self, middleware, mock_request):
        """Test middleware handling unhandled exception"""
        
        async def call_next(request):
            raise Exception("Unexpected error")
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class, \
             patch('app.middleware.error_handler.SecurityLogger') as mock_security_class, \
             patch('app.core.config.settings') as mock_settings:
            
            mock_settings.DEBUG = False
            
            mock_logger = Mock()
            mock_logger.critical = Mock()
            mock_logger_class.return_value = mock_logger
            
            mock_security = Mock()
            mock_security_class.return_value = mock_security
            
            response = await middleware.dispatch(mock_request, call_next)
            
            # Verify critical error logging
            mock_logger.critical.assert_called_once()
            
            assert response.status_code == 500
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"
            assert content["error"]["message"] == "An unexpected error occurred"
            
            # Should not expose internal details in production
            assert "details" not in content["error"]
    
    @pytest.mark.asyncio
    async def test_unhandled_exception_debug_mode(self, middleware, mock_request):
        """Test middleware handling unhandled exception in debug mode"""
        
        async def call_next(request):
            raise ValueError("Debug error with details")
        
        with patch('app.middleware.error_handler.RequestLogger') as mock_logger_class, \
             patch('app.middleware.error_handler.SecurityLogger') as mock_security_class, \
             patch('app.core.config.settings') as mock_settings:
            
            mock_settings.DEBUG = True
            
            mock_logger = Mock()
            mock_logger.critical = Mock()
            mock_logger_class.return_value = mock_logger
            
            mock_security = Mock()
            mock_security_class.return_value = mock_security
            
            response = await middleware.dispatch(mock_request, call_next)
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"
            
            # Should expose debug details in debug mode
            assert "details" in content["error"]
            assert content["error"]["details"]["error_type"] == "ValueError"
            assert "Debug error with details" in content["error"]["details"]["error_message"]
    
    def test_get_client_ip_forwarded_for(self, middleware):
        """Test client IP extraction from X-Forwarded-For"""
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        mock_request.client.host = "10.0.0.1"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.1"  # Should take first IP
    
    def test_get_client_ip_real_ip(self, middleware):
        """Test client IP extraction from X-Real-IP"""
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Real-IP": "198.51.100.1"}
        mock_request.client.host = "10.0.0.1"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "198.51.100.1"
    
    def test_get_client_ip_fallback(self, middleware):
        """Test client IP extraction fallback to client host"""
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.100"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"
    
    def test_suspicious_db_error_detection(self, middleware):
        """Test suspicious database error detection"""
        
        # Test suspicious patterns
        suspicious_errors = [
            SQLAlchemyError("UNION SELECT * FROM users"),
            SQLAlchemyError("DROP TABLE important_data"),
            SQLAlchemyError("SQL injection attempt detected")
        ]
        
        for error in suspicious_errors:
            assert middleware._is_suspicious_db_error(error) is True
        
        # Test normal errors
        normal_error = SQLAlchemyError("Connection timeout")
        assert middleware._is_suspicious_db_error(normal_error) is False
    
    def test_suspicious_error_detection(self, middleware):
        """Test suspicious general error detection"""
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        
        # Test suspicious error message
        suspicious_error = Exception("XSS attack detected in script tag")
        assert middleware._is_suspicious_error(suspicious_error, mock_request) is True
        
        # Test suspicious path
        mock_request.url.path = "/api/../etc/passwd"
        normal_error = Exception("File not found")
        assert middleware._is_suspicious_error(normal_error, mock_request) is True
        
        # Test normal error and path
        mock_request.url.path = "/api/users"
        normal_error = Exception("User not found")
        assert middleware._is_suspicious_error(normal_error, mock_request) is False


class TestExceptionHandlers:
    """Test standalone exception handlers"""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.state.correlation_id = "test_correlation_123"
        return request
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, mock_request):
        """Test validation exception handler"""
        
        validation_errors = [
            {"loc": ["body", "email"], "msg": "Invalid email", "type": "value_error"}
        ]
        exc = RequestValidationError(validation_errors)
        
        with patch('app.middleware.error_handler.logger') as mock_logger:
            response = await validation_exception_handler(mock_request, exc)
            
            # Verify logging
            mock_logger.warning.assert_called_once()
            
            # Verify response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 422
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "VALIDATION_ERROR"
            assert content["error"]["correlation_id"] == "test_correlation_123"
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request):
        """Test HTTP exception handler"""
        
        exc = HTTPException(status_code=403, detail="Access forbidden")
        
        with patch('app.middleware.error_handler.logger') as mock_logger:
            response = await http_exception_handler(mock_request, exc)
            
            # Verify logging
            mock_logger.warning.assert_called_once()
            
            # Verify response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 403
            
            content = json.loads(response.body)
            assert content["error"]["code"] == "HTTP_403"
            assert content["error"]["message"] == "Access forbidden"
            assert content["error"]["correlation_id"] == "test_correlation_123"