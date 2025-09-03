"""
Memory Service Manager

Coordinates memory operations across the entire system,
integrating LangMem, Neo4j, Redis, and background processing.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..ai.config import AIConfig
from ..ai.memory.modern_langmem_manager import ModernLangMemManager
from ..ai.workflows.checkpoint_manager import CheckpointManager
from ..ai.workflows.memory_orchestrator import MemoryOrchestrator
from ..ai.workflows.background_processor import BackgroundMemoryProcessor
from ..ai.graph.connection import Neo4jClient
from ..ai.services.vector_service import VectorSearchService
from ..ai.llm.router import LLMRouter
from ..core.exceptions import AIProcessingError
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class MemoryServiceManager:
    """
    Central service manager for all memory operations
    
    Coordinates:
    - LangMem manager for intelligent memory operations
    - Background processor for async operations
    - Checkpoint manager for conversation persistence
    - Memory orchestrator for agent integration
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.is_initialized = False
        
        # Core services
        self.neo4j_client: Optional[Neo4jClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.llm_router: Optional[LLMRouter] = None
        self.vector_service: Optional[VectorSearchService] = None
        
        # Memory components
        self.memory_manager: Optional[ModernLangMemManager] = None
        self.checkpoint_manager: Optional[CheckpointManager] = None
        self.memory_orchestrator: Optional[MemoryOrchestrator] = None
        self.background_processor: Optional[BackgroundMemoryProcessor] = None
        
        # Background task
        self._background_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize all memory system components"""
        if self.is_initialized:
            logger.warning("Memory service already initialized")
            return True
        
        try:
            logger.info("Initializing memory service manager...")
            
            # Initialize core services
            await self._initialize_core_services()
            
            # Initialize memory components
            await self._initialize_memory_components()
            
            # Start background processing
            await self._start_background_processing()
            
            self.is_initialized = True
            logger.info("Memory service manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Memory service initialization failed: {e}")
            await self.cleanup()
            raise AIProcessingError(f"Memory service initialization failed: {e}")
    
    async def _initialize_core_services(self):
        """Initialize core infrastructure services"""
        # Neo4j client
        self.neo4j_client = Neo4jClient(self.config)
        await self.neo4j_client.connect()
        
        # Redis client
        self.redis_client = redis.from_url(self.config.redis_url)
        await self.redis_client.ping()
        
        # LLM router
        self.llm_router = LLMRouter(self.config)
        
        # Vector search service
        self.vector_service = VectorSearchService(
            config=self.config,
            llm_router=self.llm_router,
            neo4j_client=self.neo4j_client,
            redis_client=self.redis_client
        )
        
        logger.debug("Core services initialized")
    
    async def _initialize_memory_components(self):
        """Initialize memory-specific components"""
        # Modern LangMem manager
        self.memory_manager = ModernLangMemManager(
            config=self.config,
            neo4j_client=self.neo4j_client,
            vector_service=self.vector_service
        )
        await self.memory_manager.initialize()
        
        # Checkpoint manager
        self.checkpoint_manager = CheckpointManager(self.config)
        await self.checkpoint_manager.initialize()
        
        # Memory orchestrator
        self.memory_orchestrator = MemoryOrchestrator(
            config=self.config,
            memory_manager=self.memory_manager,
            checkpoint_manager=self.checkpoint_manager
        )
        await self.memory_orchestrator.initialize()
        
        # Background processor
        self.background_processor = BackgroundMemoryProcessor(
            config=self.config,
            memory_manager=self.memory_manager
        )
        await self.background_processor.initialize()
        
        logger.debug("Memory components initialized")
    
    async def _start_background_processing(self):
        """Start background memory processing"""
        if self.background_processor:
            self._background_task = asyncio.create_task(
                self.background_processor.start_processing()
            )
            logger.debug("Background processing started")
    
    # Public API methods
    
    async def process_chat_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        agent_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat message with memory integration
        
        Args:
            user_id: User ID
            message: User message
            conversation_id: Optional conversation ID
            agent_preference: Optional preferred agent type
            
        Returns:
            Response with memory insights
        """
        if not self.is_initialized:
            raise AIProcessingError("Memory service not initialized")
        
        try:
            response = await self.memory_orchestrator.chat_with_memory(
                user_id=user_id,
                message=message,
                conversation_id=conversation_id,
                agent_preference=agent_preference
            )
            
            # Queue background memory extraction
            if self.background_processor:
                await self.background_processor.queue_memory_extraction(
                    user_id=user_id,
                    conversation_id=response.get("conversation_id", ""),
                    messages=[
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response.get("content", "")}
                    ],
                    priority=2  # High priority for real-time conversations
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            raise AIProcessingError(f"Chat processing failed: {e}")
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search user memories
        
        Args:
            user_id: User ID
            query: Search query
            memory_types: Optional memory types filter
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        if not self.is_initialized or not self.memory_manager:
            raise AIProcessingError("Memory service not initialized")
        
        try:
            return await self.memory_manager.search_memories(
                user_id=user_id,
                query_text=query,
                memory_types=memory_types,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise AIProcessingError(f"Memory search failed: {e}")
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's conversation history
        
        Args:
            user_id: User ID
            limit: Maximum conversations
            
        Returns:
            List of conversations with metadata
        """
        if not self.is_initialized or not self.checkpoint_manager:
            raise AIProcessingError("Memory service not initialized")
        
        try:
            return await self.checkpoint_manager.get_user_conversations(user_id, limit)
            
        except Exception as e:
            logger.error(f"Conversation retrieval failed: {e}")
            raise AIProcessingError(f"Conversation retrieval failed: {e}")
    
    async def trigger_memory_consolidation(
        self,
        user_id: str,
        background: bool = True
    ) -> Dict[str, Any]:
        """
        Trigger memory consolidation
        
        Args:
            user_id: User ID
            background: Whether to run in background
            
        Returns:
            Consolidation result or task ID
        """
        if not self.is_initialized:
            raise AIProcessingError("Memory service not initialized")
        
        try:
            if background and self.background_processor:
                # Queue background consolidation
                await self.background_processor.queue_memory_consolidation(
                    user_id=user_id,
                    priority=3
                )
                return {"status": "queued", "background": True}
            else:
                # Run immediate consolidation
                result = await self.memory_manager.consolidate_memories(user_id)
                return {"status": "completed", "result": result}
                
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            raise AIProcessingError(f"Memory consolidation failed: {e}")
    
    async def get_memory_graph(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get memory graph for visualization
        
        Args:
            user_id: User ID
            conversation_id: Optional conversation filter
            
        Returns:
            Graph data with nodes and edges
        """
        if not self.is_initialized or not self.memory_manager:
            raise AIProcessingError("Memory service not initialized")
        
        try:
            if conversation_id:
                return await self.memory_manager.get_conversation_memory_graph(conversation_id)
            else:
                return await self.memory_manager.get_user_memory_graph(user_id)
                
        except Exception as e:
            logger.error(f"Memory graph retrieval failed: {e}")
            raise AIProcessingError(f"Memory graph retrieval failed: {e}")
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory service statistics
        
        Returns:
            Service statistics and health metrics
        """
        try:
            stats = {
                "service_status": "healthy" if self.is_initialized else "not_initialized",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {}
            }
            
            # Memory manager stats
            if self.memory_manager:
                try:
                    memory_stats = await self.memory_manager.get_service_stats()
                    stats["components"]["memory_manager"] = {
                        "status": "healthy",
                        "stats": memory_stats
                    }
                except Exception as e:
                    stats["components"]["memory_manager"] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Checkpoint manager stats
            if self.checkpoint_manager:
                try:
                    checkpoint_stats = await self.checkpoint_manager.get_checkpoint_stats()
                    stats["components"]["checkpoint_manager"] = {
                        "status": "healthy",
                        "stats": checkpoint_stats
                    }
                except Exception as e:
                    stats["components"]["checkpoint_manager"] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Background processor stats
            if self.background_processor:
                try:
                    bg_stats = await self.background_processor.get_processing_status()
                    stats["components"]["background_processor"] = {
                        "status": "healthy",
                        "stats": bg_stats
                    }
                except Exception as e:
                    stats["components"]["background_processor"] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {
                "service_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up memory service manager...")
        
        try:
            # Stop background processing
            if self._background_task and not self._background_task.done():
                self._background_task.cancel()
                try:
                    await self._background_task
                except asyncio.CancelledError:
                    pass
            
            # Cleanup components
            if self.background_processor:
                await self.background_processor.close()
            
            if self.memory_orchestrator:
                await self.memory_orchestrator.cleanup()
            
            if self.checkpoint_manager:
                await self.checkpoint_manager.close()
            
            if self.memory_manager:
                await self.memory_manager.close()
            
            # Cleanup core services
            if self.neo4j_client:
                await self.neo4j_client.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            self.is_initialized = False
            logger.info("Memory service manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global service instance (will be initialized in main app)
memory_service: Optional[MemoryServiceManager] = None

async def get_memory_service() -> MemoryServiceManager:
    """Get global memory service instance"""
    global memory_service
    
    if not memory_service:
        config = AIConfig()
        memory_service = MemoryServiceManager(config)
        await memory_service.initialize()
    
    return memory_service

async def initialize_memory_service(config: AIConfig) -> MemoryServiceManager:
    """Initialize global memory service"""
    global memory_service
    
    if memory_service:
        await memory_service.cleanup()
    
    memory_service = MemoryServiceManager(config)
    await memory_service.initialize()
    return memory_service

async def cleanup_memory_service():
    """Cleanup global memory service"""
    global memory_service
    
    if memory_service:
        await memory_service.cleanup()
        memory_service = None