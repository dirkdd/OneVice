"""
Tool Dependencies Management

Service locator pattern for managing database connections and external clients
used by LangGraph @tool decorated functions.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import asyncio
from contextlib import asynccontextmanager

# Import existing clients
from database.neo4j_client import Neo4jClient
from ...core.redis import get_redis
from ..llm.router import LLMRouter

logger = logging.getLogger(__name__)


@dataclass
class ToolDependencies:
    """Container for all tool dependencies"""
    neo4j_client: Optional[Neo4jClient] = None
    redis_client: Optional[Any] = None  # Redis client
    folk_client: Optional[Any] = None   # Folk API client
    llm_router: Optional[LLMRouter] = None


class DependencyManager:
    """
    Manages tool dependencies with connection pooling and lifecycle management.
    
    Uses singleton pattern to ensure efficient resource usage across all tools.
    """
    
    _instance: Optional['DependencyManager'] = None
    _dependencies: Optional[ToolDependencies] = None
    _initialized: bool = False
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DependencyManager, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize all dependencies with connection pooling"""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:  # Double-check after acquiring lock
                return
                
            logger.info("Initializing tool dependencies...")
            
            try:
                # Initialize Neo4j client
                neo4j_client = Neo4jClient()
                await neo4j_client.connect()
                logger.info("Neo4j client initialized for tools")
                
                # Initialize Redis client  
                redis_client = await get_redis()
                logger.info("Redis client initialized for tools")
                
                # Initialize Folk client (if available)
                folk_client = None  # Will be implemented based on existing patterns
                
                # Initialize LLM router
                from ..config import AIConfig
                ai_config = AIConfig()
                llm_router = LLMRouter(ai_config)
                logger.info("LLM router initialized for tools")
                
                self._dependencies = ToolDependencies(
                    neo4j_client=neo4j_client,
                    redis_client=redis_client,
                    folk_client=folk_client,
                    llm_router=llm_router
                )
                
                self._initialized = True
                logger.info("All tool dependencies initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize tool dependencies: {e}")
                raise
    
    async def cleanup(self) -> None:
        """Clean up all connections"""
        if not self._initialized or not self._dependencies:
            return
            
        async with self._lock:
            logger.info("Cleaning up tool dependencies...")
            
            # Close Neo4j connection
            if self._dependencies.neo4j_client:
                try:
                    await self._dependencies.neo4j_client.close()
                    logger.info("Neo4j client closed")
                except Exception as e:
                    logger.error(f"Error closing Neo4j client: {e}")
            
            # Close Redis connection
            if self._dependencies.redis_client:
                try:
                    await self._dependencies.redis_client.close()
                    logger.info("Redis client closed")
                except Exception as e:
                    logger.error(f"Error closing Redis client: {e}")
            
            self._dependencies = None
            self._initialized = False
    
    def get_dependencies(self) -> ToolDependencies:
        """Get initialized dependencies"""
        if not self._initialized or not self._dependencies:
            raise RuntimeError("Dependencies not initialized. Call initialize() first.")
        return self._dependencies
    
    @asynccontextmanager
    async def get_neo4j_client(self):
        """Context manager for Neo4j operations with error handling"""
        deps = self.get_dependencies()
        if not deps.neo4j_client:
            raise RuntimeError("Neo4j client not available")
            
        try:
            # Ensure connection is active
            if hasattr(deps.neo4j_client, 'state') and hasattr(deps.neo4j_client, 'connect'):
                from database.neo4j_client import ConnectionState
                if deps.neo4j_client.state != ConnectionState.CONNECTED:
                    await deps.neo4j_client.connect()
            
            yield deps.neo4j_client
            
        except Exception as e:
            logger.error(f"Neo4j client error: {e}")
            raise
    
    @asynccontextmanager
    async def get_redis_client(self):
        """Context manager for Redis operations"""
        deps = self.get_dependencies()
        if not deps.redis_client:
            raise RuntimeError("Redis client not available")
            
        try:
            yield deps.redis_client
        except Exception as e:
            logger.error(f"Redis client error: {e}")
            raise


# Global instance
dependency_manager = DependencyManager()


async def init_tool_dependencies(config: Optional[Dict[str, Any]] = None) -> None:
    """Initialize tool dependencies (call once at startup)"""
    await dependency_manager.initialize(config)


async def cleanup_tool_dependencies() -> None:
    """Cleanup tool dependencies (call at shutdown)"""
    await dependency_manager.cleanup()


def get_tool_dependencies() -> ToolDependencies:
    """Get tool dependencies for use in tool functions"""
    return dependency_manager.get_dependencies()


def get_neo4j_context():
    """Get Neo4j context manager for tools"""
    return dependency_manager.get_neo4j_client()


def get_redis_context():
    """Get Redis context manager for tools"""
    return dependency_manager.get_redis_client()