"""
Tool Factory for LangGraph Tool Creation

Factory pattern for creating @tool decorated functions with dependency injection,
caching, and error handling. Provides consistent tool creation across the system.
"""

import logging
from typing import Any, Dict, Optional, Callable, List, Type, Union
from functools import wraps
import inspect
from datetime import datetime

# LangGraph imports
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# Local imports
from .dependencies import get_tool_dependencies, get_neo4j_context, get_redis_context
from .cache import ToolCache, cached_tool
from .error_handling import (
    resilient_tool, 
    safe_tool_execution,
    CircuitBreakerConfig, 
    RetryConfig,
    ToolExecutionError
)

logger = logging.getLogger(__name__)


class ToolFactory:
    """
    Factory for creating LangGraph tools with consistent patterns.
    
    Handles dependency injection, caching, error handling, and tool registration
    for all OneVice AI tools.
    """
    
    def __init__(self):
        self.registered_tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_database_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        enable_cache: bool = True,
        cache_ttl: Optional[int] = None,
        enable_resilience: bool = True,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout: float = 30.0
    ) -> Callable:
        """
        Create a database tool with dependency injection and resilience patterns.
        
        Args:
            name: Tool name for LangGraph
            description: Tool description for LLM context
            func: Tool implementation function
            enable_cache: Enable Redis caching
            cache_ttl: Cache TTL override (seconds)
            enable_resilience: Enable circuit breaker and retry
            circuit_breaker_config: Custom circuit breaker config
            retry_config: Custom retry config
            timeout: Tool execution timeout
            
        Returns:
            Decorated tool function ready for LangGraph binding
        """
        
        # Check if func is already a StructuredTool (wrapped) or a raw function
        from langchain_core.tools import StructuredTool
        
        if isinstance(func, StructuredTool):
            logger.info(f"🔍 DETECTED: {name} is already a StructuredTool, unwrapping...")
            # Extract the original function from the StructuredTool's coroutine attribute
            original_func = func.coroutine
            func_name = func.name
            func_doc = func.description
            # Get signature from the original function
            sig = inspect.signature(original_func)
        else:
            logger.info(f"🔍 DETECTED: {name} is a raw function")
            original_func = func
            func_name = getattr(func, '__name__', name)
            func_doc = getattr(func, '__doc__', description)
            sig = inspect.signature(func)
        
        dependency_params = {'neo4j_client', 'redis_client', 'llm_client'}
        
        # Create parameters for the clean wrapper (excluding dependencies)
        clean_params = []
        for param_name, param in sig.parameters.items():
            if param_name not in dependency_params:
                clean_params.append(param)
        
        # Create the clean wrapper function that only exposes user parameters
        @wraps(original_func)
        async def clean_tool_wrapper(*args, **kwargs):
            """Clean wrapper that hides dependency injection from LLM"""
            
            logger.info(f"🔧 WRAPPER START: {name} called with args={args}, kwargs={kwargs}")
            
            try:
                # Inject dependencies based on function signature
                if 'neo4j_client' in sig.parameters:
                    logger.info(f"🔌 INJECTING: neo4j_client for {name}")
                    async with get_neo4j_context() as neo4j:
                        kwargs['neo4j_client'] = neo4j
                        logger.info(f"🚀 CALLING: {name} with neo4j injection")
                        result = await original_func(*args, **kwargs)
                        logger.info(f"✅ WRAPPER SUCCESS: {name} returned {type(result)}")
                        return result
                elif 'redis_client' in sig.parameters:
                    logger.info(f"🔌 INJECTING: redis_client for {name}")
                    async with get_redis_context() as redis:
                        kwargs['redis_client'] = redis
                        logger.info(f"🚀 CALLING: {name} with redis injection")
                        result = await original_func(*args, **kwargs)
                        logger.info(f"✅ WRAPPER SUCCESS: {name} returned {type(result)}")
                        return result
                else:
                    # No special dependencies needed
                    logger.info(f"🚀 CALLING: {name} with no injection")
                    result = await original_func(*args, **kwargs)
                    logger.info(f"✅ WRAPPER SUCCESS: {name} returned {type(result)}")
                    return result
                    
            except Exception as e:
                logger.error(f"💥 WRAPPER ERROR: {name} failed with {type(e).__name__}: {e}")
                raise
        
        # Update the wrapper's signature to only include non-dependency parameters
        clean_sig = sig.replace(parameters=clean_params)
        clean_tool_wrapper.__signature__ = clean_sig
        clean_tool_wrapper.__name__ = func_name
        clean_tool_wrapper.__doc__ = func_doc
        
        # Apply decorators in correct order
        decorated_func = clean_tool_wrapper
        
        # 1. Apply timeout wrapper
        if timeout > 0:
            decorated_func = safe_tool_execution(timeout=timeout)(decorated_func)
        
        # 2. Apply resilience patterns
        if enable_resilience:
            decorated_func = resilient_tool(
                circuit_breaker_config=circuit_breaker_config,
                retry_config=retry_config,
                tool_name=name
            )(decorated_func)
        
        # 3. Apply caching
        if enable_cache:
            decorated_func = cached_tool(ttl=cache_ttl)(decorated_func)
        
        # 4. Add debug wrapper before @tool decorator
        @wraps(decorated_func)
        async def debug_tool_wrapper(*args, **kwargs):
            logger.info(f"🔍 DEBUG TOOL: {name} being called by LangGraph with args={args}, kwargs={kwargs}")
            result = await decorated_func(*args, **kwargs)
            logger.info(f"🎯 DEBUG TOOL: {name} completed successfully")
            return result
        
        # 5. Apply LangGraph @tool decorator to the debug wrapper
        langraph_tool = tool(name, description=description)(debug_tool_wrapper)
        
        # Register the tool
        self.registered_tools[name] = langraph_tool
        self.tool_metadata[name] = {
            "description": description,
            "cache_enabled": enable_cache,
            "resilience_enabled": enable_resilience,
            "timeout": timeout,
            "created_at": datetime.utcnow().isoformat(),
            "dependencies_injected": list(dependency_params.intersection(sig.parameters.keys()))
        }
        
        logger.info(f"📝 REGISTERED: Tool {name} successfully registered")
        logger.info(f"🔧 TOOL TYPE: {type(langraph_tool)} with callable={callable(langraph_tool)}")
        logger.info(f"🎯 TOOL ATTRS: name='{getattr(langraph_tool, 'name', 'MISSING')}', func={getattr(langraph_tool, 'func', 'MISSING')}")
        logger.info(f"Created database tool: {name} with caching={enable_cache}, resilience={enable_resilience}")
        logger.debug(f"Tool {name} dependencies: {self.tool_metadata[name]['dependencies_injected']}")
        return langraph_tool
    
    def create_api_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        enable_cache: bool = True,
        cache_ttl: Optional[int] = None,
        timeout: float = 60.0,
        retryable: bool = True
    ) -> Callable:
        """
        Create an API tool optimized for external service calls.
        
        Args:
            name: Tool name for LangGraph
            description: Tool description for LLM context  
            func: Tool implementation function
            enable_cache: Enable Redis caching
            cache_ttl: Cache TTL override (seconds)
            timeout: Tool execution timeout
            retryable: Enable retry logic for API calls
            
        Returns:
            Decorated tool function for external APIs
        """
        
        # API-specific configurations
        circuit_config = CircuitBreakerConfig(
            failure_threshold=3,  # More aggressive for external APIs
            recovery_timeout=30.0,  # Faster recovery attempts
            failure_threshold_percentage=30.0  # Lower threshold for APIs
        )
        
        retry_config = RetryConfig(
            max_attempts=3 if retryable else 1,
            base_delay=2.0,  # Longer initial delay for APIs
            max_delay=30.0,
            retryable_exceptions=(
                ConnectionError,
                TimeoutError,
                OSError
            )
        ) if retryable else None
        
        return self.create_database_tool(
            name=name,
            description=description,
            func=func,
            enable_cache=enable_cache,
            cache_ttl=cache_ttl or 1800,  # 30 min default for API calls
            enable_resilience=retryable,
            circuit_breaker_config=circuit_config,
            retry_config=retry_config,
            timeout=timeout
        )
    
    def create_search_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        cache_ttl: int = 600,  # 10 minutes default
        timeout: float = 15.0
    ) -> Callable:
        """
        Create a search tool optimized for quick lookups.
        
        Args:
            name: Tool name for LangGraph
            description: Tool description for LLM context
            func: Tool implementation function
            cache_ttl: Cache TTL in seconds
            timeout: Tool execution timeout
            
        Returns:
            Decorated search tool function
        """
        
        return self.create_database_tool(
            name=name,
            description=description,
            func=func,
            enable_cache=True,
            cache_ttl=cache_ttl,
            enable_resilience=True,
            timeout=timeout
        )
    
    def create_analytics_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        cache_ttl: int = 1800,  # 30 minutes default
        timeout: float = 120.0  # Longer timeout for complex analytics
    ) -> Callable:
        """
        Create an analytics tool for complex computations.
        
        Args:
            name: Tool name for LangGraph
            description: Tool description for LLM context
            func: Tool implementation function
            cache_ttl: Cache TTL in seconds
            timeout: Tool execution timeout
            
        Returns:
            Decorated analytics tool function
        """
        
        circuit_config = CircuitBreakerConfig(
            failure_threshold=2,  # Lower threshold for heavy operations
            recovery_timeout=120.0,  # Longer recovery time
            failure_threshold_percentage=25.0
        )
        
        return self.create_database_tool(
            name=name,
            description=description,
            func=func,
            enable_cache=True,
            cache_ttl=cache_ttl,
            enable_resilience=True,
            circuit_breaker_config=circuit_config,
            timeout=timeout
        )
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a registered tool by name"""
        return self.registered_tools.get(name)
    
    def get_all_tools(self) -> List[Callable]:
        """Get all registered tools for LangGraph binding"""
        return list(self.registered_tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names"""
        return list(self.registered_tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[Callable]:
        """
        Get tools by category based on name patterns.
        
        Categories: database, api, search, analytics, organization, person, project
        """
        tools = []
        for name, tool_func in self.registered_tools.items():
            if category.lower() in name.lower():
                tools.append(tool_func)
        return tools
    
    def create_tool_node(self, tool_names: Optional[List[str]] = None) -> ToolNode:
        """
        Create a LangGraph ToolNode with specified tools.
        
        Args:
            tool_names: List of tool names to include (None = all tools)
            
        Returns:
            ToolNode for LangGraph state machine
        """
        if tool_names is None:
            tools = self.get_all_tools()
        else:
            tools = [self.get_tool(name) for name in tool_names if self.get_tool(name)]
        
        if not tools:
            raise ValueError("No valid tools found for ToolNode creation")
        
        logger.info(f"Created ToolNode with {len(tools)} tools")
        return ToolNode(tools)
    
    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool"""
        return self.tool_metadata.get(name)
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """Get comprehensive tool factory status"""
        return {
            "registered_tools": len(self.registered_tools),
            "tool_names": list(self.registered_tools.keys()),
            "metadata": self.tool_metadata,
            "factory_initialized": datetime.utcnow().isoformat()
        }


# Global factory instance
tool_factory = ToolFactory()


def create_organization_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    cache_ttl: int = 1800  # 30 minutes
):
    """
    Decorator factory for creating organization-focused tools.
    
    Example:
        @create_organization_tool(
            name="get_organization_profile",
            description="Tool for organization operations"
        )
        async def get_organization_profile(org_name: str, neo4j_client) -> Dict[str, Any]:
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or f"Tool for organization operations: {func.__name__}"
        
        return tool_factory.create_database_tool(
            name=tool_name,
            description=tool_desc,
            func=func,
            cache_ttl=cache_ttl
        )
    return decorator


def create_person_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    cache_ttl: int = 3600  # 1 hour
):
    """
    Decorator factory for creating person-focused tools.
    
    Example:
        @create_person_tool(
            name="get_person_details",
            description="Tool for person operations"
        )
        async def get_person_profile(person_name: str, neo4j_client) -> Dict[str, Any]:
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or f"Tool for person operations: {func.__name__}"
        
        return tool_factory.create_database_tool(
            name=tool_name,
            description=tool_desc,
            func=func,
            cache_ttl=cache_ttl
        )
    return decorator


def create_project_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    cache_ttl: int = 3600  # 1 hour
):
    """
    Decorator factory for creating project-focused tools.
    
    Example:
        @create_project_tool(
            name="get_project_details",
            description="Tool for project operations"
        )
        async def get_project_details(project_name: str, neo4j_client) -> Dict[str, Any]:
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or f"Tool for project operations: {func.__name__}"
        
        return tool_factory.create_database_tool(
            name=tool_name,
            description=tool_desc,
            func=func,
            cache_ttl=cache_ttl
        )
    return decorator


def get_factory() -> ToolFactory:
    """Get the global tool factory instance"""
    return tool_factory


def get_all_tools() -> List[Callable]:
    """Get all registered tools from factory"""
    return tool_factory.get_all_tools()


def create_tool_node(tool_names: Optional[List[str]] = None) -> ToolNode:
    """Create ToolNode from factory tools"""
    return tool_factory.create_tool_node(tool_names)


async def get_factory_status() -> Dict[str, Any]:
    """Get comprehensive tool factory status for monitoring"""
    return tool_factory.get_all_metadata()