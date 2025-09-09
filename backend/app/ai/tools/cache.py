"""
Tool Caching System

Redis-based caching for LangGraph tools with deterministic key generation,
TTL management, and cache invalidation patterns.
"""

import json
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from datetime import timedelta
from functools import wraps

from .dependencies import get_redis_context

logger = logging.getLogger(__name__)


class ToolCache:
    """Redis-based caching system for LangGraph tools"""
    
    # Default TTL values for different tool types (in seconds)
    DEFAULT_TTLS = {
        "person": 3600,        # 1 hour - people data changes occasionally
        "organization": 1800,  # 30 minutes - org data can change more frequently  
        "project": 3600,      # 1 hour - project data is relatively stable
        "deal": 300,          # 5 minutes - deal data changes frequently
        "document": 7200,     # 2 hours - document data is very stable
        "search": 600,        # 10 minutes - search results can change
        "analytics": 1800,    # 30 minutes - analytics can be refreshed regularly
        "default": 1800       # 30 minutes - safe default
    }
    
    @classmethod
    def generate_cache_key(cls, tool_name: str, **kwargs) -> str:
        """
        Generate deterministic cache key from tool name and parameters.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            Deterministic cache key string
        """
        # Sort parameters for consistent key generation
        sorted_params = sorted(kwargs.items())
        
        # Create parameter string
        param_str = json.dumps(sorted_params, sort_keys=True, ensure_ascii=True)
        
        # Generate hash for long parameter strings
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        # Create cache key
        cache_key = f"tool:{tool_name}:{param_hash}"
        
        logger.debug(f"Generated cache key: {cache_key} for params: {sorted_params}")
        return cache_key
    
    @classmethod
    def get_ttl_for_tool(cls, tool_name: str) -> int:
        """Get appropriate TTL for a tool type"""
        # Extract tool type from tool name
        tool_type = "default"
        
        if "person" in tool_name.lower() or "people" in tool_name.lower():
            tool_type = "person"
        elif "organization" in tool_name.lower() or "company" in tool_name.lower():
            tool_type = "organization"
        elif "project" in tool_name.lower():
            tool_type = "project"
        elif "deal" in tool_name.lower():
            tool_type = "deal"
        elif "document" in tool_name.lower():
            tool_type = "document"
        elif "search" in tool_name.lower():
            tool_type = "search"
        elif "analytic" in tool_name.lower() or "insight" in tool_name.lower():
            tool_type = "analytics"
            
        return cls.DEFAULT_TTLS.get(tool_type, cls.DEFAULT_TTLS["default"])
    
    @classmethod
    async def get(cls, tool_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached result for tool with given parameters.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = cls.generate_cache_key(tool_name, **kwargs)
        
        try:
            async with get_redis_context() as redis:
                cached_data = await redis.get(cache_key)
                
                if cached_data:
                    result = json.loads(cached_data)
                    logger.debug(f"Cache hit for {tool_name}: {cache_key}")
                    return result
                else:
                    logger.debug(f"Cache miss for {tool_name}: {cache_key}")
                    return None
                    
        except Exception as e:
            logger.error(f"Cache get error for {tool_name}: {e}")
            return None
    
    @classmethod
    async def set(
        cls, 
        tool_name: str, 
        result: Dict[str, Any], 
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Cache result for tool with given parameters.
        
        Args:
            tool_name: Name of the tool
            result: Tool result to cache
            ttl: Time to live in seconds (optional)
            **kwargs: Tool parameters
            
        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = cls.generate_cache_key(tool_name, **kwargs)
        
        if ttl is None:
            ttl = cls.get_ttl_for_tool(tool_name)
        
        try:
            # Don't cache error results
            if result.get("error") or not result.get("found", True):
                logger.debug(f"Not caching error result for {tool_name}")
                return False
                
            cached_data = json.dumps(result, ensure_ascii=True)
            
            async with get_redis_context() as redis:
                await redis.setex(cache_key, ttl, cached_data)
                logger.debug(f"Cached result for {tool_name} (TTL: {ttl}s): {cache_key}")
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for {tool_name}: {e}")
            return False
    
    @classmethod
    async def invalidate(cls, tool_name: str, **kwargs) -> bool:
        """
        Invalidate cached result for specific tool parameters.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        cache_key = cls.generate_cache_key(tool_name, **kwargs)
        
        try:
            async with get_redis_context() as redis:
                result = await redis.delete(cache_key)
                logger.debug(f"Invalidated cache for {tool_name}: {cache_key}")
                return bool(result)
                
        except Exception as e:
            logger.error(f"Cache invalidation error for {tool_name}: {e}")
            return False
    
    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> int:
        """
        Invalidate all cached results matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "tool:*person*")
            
        Returns:
            Number of keys invalidated
        """
        try:
            async with get_redis_context() as redis:
                keys = await redis.keys(pattern)
                if keys:
                    count = await redis.delete(*keys)
                    logger.info(f"Invalidated {count} cached results matching pattern: {pattern}")
                    return count
                return 0
                
        except Exception as e:
            logger.error(f"Pattern invalidation error for {pattern}: {e}")
            return 0


def cached_tool(ttl: Optional[int] = None):
    """
    Decorator for LangGraph tools to add automatic caching.
    
    Args:
        ttl: Optional custom TTL in seconds
        
    Example:
        @cached_tool(ttl=3600)
        @tool("get_person_details")
        async def get_person_details(name: str) -> Dict[str, Any]:
            # Tool implementation
    """
    def decorator(tool_func):
        tool_name = getattr(tool_func, 'name', tool_func.__name__)
        
        @wraps(tool_func)
        async def wrapper(*args, **kwargs):
            # Try to get from cache first
            cached_result = await ToolCache.get(tool_name, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute tool function
            result = await tool_func(*args, **kwargs)
            
            # Cache the result
            if isinstance(result, dict):
                await ToolCache.set(tool_name, result, ttl=ttl, **kwargs)
            
            return result
            
        return wrapper
    return decorator


async def warm_cache_for_common_queries():
    """
    Pre-warm cache with results for common queries.
    Call this during startup or periodic maintenance.
    """
    common_queries = [
        # Add common organization queries
        {"tool": "get_organization_profile", "params": {"organization_name": "Sony"}},
        {"tool": "get_organization_profile", "params": {"organization_name": "Disney"}},
        
        # Add common search patterns
        {"tool": "search_projects", "params": {"project_type": "commercial"}},
    ]
    
    logger.info(f"Pre-warming cache with {len(common_queries)} common queries")
    
    # Implementation would call actual tools to populate cache
    # This is optional and can be implemented later
    pass


async def clear_all_tool_cache():
    """Clear all tool cache entries (use with caution)"""
    try:
        count = await ToolCache.invalidate_pattern("tool:*")
        logger.info(f"Cleared {count} tool cache entries")
        return count
    except Exception as e:
        logger.error(f"Error clearing tool cache: {e}")
        return 0