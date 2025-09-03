"""
OneVice Structured Logging Configuration
Production-ready logging with JSON output and structured data
"""

import logging
import logging.config
import sys
from typing import Dict, Any
import structlog
from datetime import datetime
import uuid
from app.core.config import settings


def configure_logging():
    """Configure structured logging for the application"""
    
    # Configure standard library logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure structlog processors
    processors = [
        # Add correlation ID if not present
        add_correlation_id,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Process stack info if present
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.dev.set_exc_info,
    ]
    
    # In production, use JSON format; in development, use console format
    if settings.DEBUG:
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    else:
        processors.extend([
            # Add service information for production
            add_service_info,
            # JSON renderer for production logs
            structlog.processors.JSONRenderer()
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def add_correlation_id(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to log entries if not present"""
    if "correlation_id" not in event_dict:
        event_dict["correlation_id"] = str(uuid.uuid4())
    return event_dict


def add_service_info(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service information to log entries"""
    event_dict.update({
        "service": "onevice-backend",
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development"
    })
    return event_dict


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


# Request context logger for adding request-specific information
class RequestLogger:
    """Logger with request context"""
    
    def __init__(self, correlation_id: str = None, user_id: str = None, 
                 ip_address: str = None, user_agent: str = None):
        self.logger = get_logger()
        self.context = {
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        # Remove None values
        self.context = {k: v for k, v in self.context.items() if v is not None}
    
    def bind(self, **kwargs) -> structlog.BoundLogger:
        """Bind additional context to the logger"""
        return self.logger.bind(**self.context, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with request context"""
        self.logger.info(message, **self.context, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with request context"""
        self.logger.warning(message, **self.context, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with request context"""
        self.logger.error(message, **self.context, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with request context"""
        self.logger.debug(message, **self.context, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with request context"""
        self.logger.critical(message, **self.context, **kwargs)


# Performance logging helpers
class PerformanceLogger:
    """Logger for performance metrics and timings"""
    
    def __init__(self, correlation_id: str = None):
        self.logger = get_logger("performance")
        self.correlation_id = correlation_id or str(uuid.uuid4())
    
    def log_database_query(self, query: str, duration_ms: float, result_count: int = None):
        """Log database query performance"""
        self.logger.info(
            "Database query executed",
            correlation_id=self.correlation_id,
            query_type="database",
            duration_ms=duration_ms,
            query=query[:200],  # Truncate long queries
            result_count=result_count,
            performance_category="database"
        )
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration_ms: float, user_id: str = None):
        """Log API request performance"""
        self.logger.info(
            "API request completed",
            correlation_id=self.correlation_id,
            request_method=method,
            request_path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            performance_category="api"
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool, duration_ms: float):
        """Log cache operation performance"""
        self.logger.info(
            "Cache operation",
            correlation_id=self.correlation_id,
            cache_operation=operation,
            cache_key=key,
            cache_hit=hit,
            duration_ms=duration_ms,
            performance_category="cache"
        )


# Security event logging
class SecurityLogger:
    """Logger for security-related events"""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_authentication_success(self, user_id: str, email: str, ip_address: str, 
                                 user_agent: str, correlation_id: str = None):
        """Log successful authentication"""
        self.logger.info(
            "Authentication successful",
            correlation_id=correlation_id or str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            security_event="authentication_success"
        )
    
    def log_authentication_failure(self, email: str, reason: str, ip_address: str, 
                                 user_agent: str, correlation_id: str = None):
        """Log failed authentication attempt"""
        self.logger.warning(
            "Authentication failed",
            correlation_id=correlation_id or str(uuid.uuid4()),
            email=email,
            failure_reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            security_event="authentication_failure"
        )
    
    def log_permission_denied(self, user_id: str, resource: str, permission: str, 
                            ip_address: str, correlation_id: str = None):
        """Log permission denied event"""
        self.logger.warning(
            "Permission denied",
            correlation_id=correlation_id or str(uuid.uuid4()),
            user_id=user_id,
            requested_resource=resource,
            required_permission=permission,
            ip_address=ip_address,
            security_event="permission_denied"
        )
    
    def log_suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any], 
                              ip_address: str, correlation_id: str = None):
        """Log suspicious activity"""
        self.logger.error(
            "Suspicious activity detected",
            correlation_id=correlation_id or str(uuid.uuid4()),
            user_id=user_id,
            suspicious_activity=activity,
            activity_details=details,
            ip_address=ip_address,
            security_event="suspicious_activity"
        )


# Application-specific loggers
def get_audit_logger() -> structlog.BoundLogger:
    """Get logger for audit operations"""
    return get_logger("audit").bind(component="audit")


def get_auth_logger() -> structlog.BoundLogger:
    """Get logger for authentication operations"""
    return get_logger("auth").bind(component="authentication")


def get_api_logger() -> structlog.BoundLogger:
    """Get logger for API operations"""
    return get_logger("api").bind(component="api")


def get_database_logger() -> structlog.BoundLogger:
    """Get logger for database operations"""
    return get_logger("database").bind(component="database")


# Initialize logging on import
configure_logging()


# Global logger instances
logger = get_logger()
audit_logger = get_audit_logger()
auth_logger = get_auth_logger()
api_logger = get_api_logger()
database_logger = get_database_logger()
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()