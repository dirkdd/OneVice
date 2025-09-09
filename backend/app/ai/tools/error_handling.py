"""
Error Handling and Resilience for LangGraph Tools

Implements circuit breakers, retry logic, and error recovery patterns
for robust tool execution in production environments.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Callable, List, Union
from functools import wraps
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5         # Failures before opening
    recovery_timeout: float = 60.0     # Seconds before trying recovery
    expected_exception: type = Exception
    failure_threshold_percentage: float = 50.0  # % failures to open
    minimum_throughput: int = 10       # Min requests before checking percentage


@dataclass
class RetryConfig:
    """Retry configuration with exponential backoff"""
    max_attempts: int = 3
    base_delay: float = 1.0           # Base delay in seconds
    max_delay: float = 60.0           # Maximum delay between retries
    exponential_base: float = 2.0     # Multiplier for exponential backoff
    jitter: bool = True               # Add randomness to prevent thundering herd
    retryable_exceptions: tuple = (
        ConnectionError, 
        TimeoutError,
        OSError,
        asyncio.TimeoutError
    )


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class ToolExecutionError(Exception):
    """Base exception for tool execution errors"""
    
    def __init__(self, message: str, tool_name: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.tool_name = tool_name
        self.original_error = original_error
        self.timestamp = datetime.utcnow()


class CircuitBreaker:
    """Circuit breaker implementation for tool resilience"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self.total_requests = 0
        
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.state == CircuitBreakerState.OPEN and
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    def _failure_rate_exceeded(self) -> bool:
        """Check if failure rate exceeds threshold"""
        if self.total_requests < self.config.minimum_throughput:
            return False
            
        failure_rate = (self.failure_count / self.total_requests) * 100
        return failure_rate >= self.config.failure_threshold_percentage
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_requests += 1
        
        # Check if circuit breaker should attempt reset
        if self._should_attempt_reset():
            self.state = CircuitBreakerState.HALF_OPEN
            logger.info(f"Circuit breaker {self.name} attempting recovery")
        
        # Fail fast if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - update counters and potentially close circuit
            self.success_count += 1
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.name} recovered - CLOSED")
            
            return result
            
        except self.config.expected_exception as e:
            # Failure - update counters and potentially open circuit
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(f"Circuit breaker {self.name} failure {self.failure_count}: {e}")
            
            # Check if we should open the circuit
            should_open = (
                self.failure_count >= self.config.failure_threshold or
                self._failure_rate_exceeded()
            )
            
            if should_open and self.state != CircuitBreakerState.OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.error(f"Circuit breaker {self.name} OPENED after {self.failure_count} failures")
            
            raise


class RetryHandler:
    """Handles retry logic with exponential backoff and jitter"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff and jitter"""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay
        )
        
        if self.config.jitter:
            # Add up to 25% jitter
            import random
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except self.config.retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_attempts:
                    logger.error(f"All {self.config.max_attempts} retry attempts failed")
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable exception on attempt {attempt}: {e}")
                raise
        
        # All retries exhausted
        raise ToolExecutionError(
            f"Function failed after {self.config.max_attempts} attempts",
            tool_name="unknown",
            original_error=last_exception
        )


class ToolErrorHandler:
    """Centralized error handling for LangGraph tools"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for a tool"""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    def get_retry_handler(self, name: str, config: Optional[RetryConfig] = None) -> RetryHandler:
        """Get or create retry handler for a tool"""
        if name not in self.retry_handlers:
            if config is None:
                config = RetryConfig()
            self.retry_handlers[name] = RetryHandler(config)
        return self.retry_handlers[name]


# Global error handler instance
error_handler = ToolErrorHandler()


def resilient_tool(
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    retry_config: Optional[RetryConfig] = None,
    tool_name: Optional[str] = None
):
    """
    Decorator to add resilience patterns to LangGraph tools.
    
    Combines circuit breaker and retry logic for robust tool execution.
    
    Args:
        circuit_breaker_config: Circuit breaker configuration
        retry_config: Retry configuration
        tool_name: Name for logging and metrics (defaults to function name)
        
    Example:
        @resilient_tool(
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3),
            retry_config=RetryConfig(max_attempts=2)
        )
        @tool("get_organization_profile")
        async def get_organization_profile(org_name: str) -> Dict[str, Any]:
            # Tool implementation
    """
    def decorator(func: Callable):
        name = tool_name or func.__name__
        
        # Get or create handlers
        circuit_breaker = error_handler.get_circuit_breaker(name, circuit_breaker_config)
        retry_handler = error_handler.get_retry_handler(name, retry_config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Wrap function execution with retry logic
                async def execute():
                    return await retry_handler.execute_with_retry(func, *args, **kwargs)
                
                # Wrap retry logic with circuit breaker
                result = await circuit_breaker.call(execute)
                return result
                
            except Exception as e:
                # Log and re-raise with context
                logger.error(f"Tool {name} failed: {e}")
                raise ToolExecutionError(
                    f"Tool execution failed: {str(e)}",
                    tool_name=name,
                    original_error=e
                )
        
        return wrapper
    return decorator


def safe_tool_execution(timeout: float = 30.0):
    """
    Simple decorator for basic tool safety with timeout.
    
    Args:
        timeout: Maximum execution time in seconds
        
    Example:
        @safe_tool_execution(timeout=10.0)
        @tool("quick_lookup")
        async def quick_lookup(query: str) -> Dict[str, Any]:
            # Tool implementation
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs) if asyncio.iscoroutinefunction(func) 
                    else asyncio.coroutine(func)(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise ToolExecutionError(
                    f"Tool timed out after {timeout} seconds",
                    tool_name=func.__name__
                )
            except Exception as e:
                raise ToolExecutionError(
                    f"Tool execution failed: {str(e)}",
                    tool_name=func.__name__,
                    original_error=e
                )
        
        return wrapper
    return decorator


async def get_tool_health_status() -> Dict[str, Any]:
    """Get health status of all circuit breakers"""
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "circuit_breakers": {}
    }
    
    for name, cb in error_handler.circuit_breakers.items():
        status["circuit_breakers"][name] = {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
            "success_count": cb.success_count,
            "total_requests": cb.total_requests,
            "failure_rate": (cb.failure_count / cb.total_requests * 100) if cb.total_requests > 0 else 0,
            "last_failure": datetime.fromtimestamp(cb.last_failure_time).isoformat() if cb.last_failure_time else None
        }
    
    return status


async def reset_circuit_breaker(name: str) -> bool:
    """Manually reset a circuit breaker"""
    if name in error_handler.circuit_breakers:
        cb = error_handler.circuit_breakers[name]
        cb.state = CircuitBreakerState.CLOSED
        cb.failure_count = 0
        cb.last_failure_time = None
        logger.info(f"Circuit breaker {name} manually reset")
        return True
    return False