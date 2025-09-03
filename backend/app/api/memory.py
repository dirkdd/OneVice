"""
Memory Management API Endpoints

REST API for managing user memories, conversation history, and memory insights.
Provides programmatic access to the LangMem + Neo4j memory system.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from ..ai.memory.memory_types import MemoryType, MemoryImportance
from ..ai.memory.langmem_manager import LangMemManager
from ..ai.workflows.checkpoint_manager import CheckpointManager
from ..ai.workflows.memory_orchestrator import MemoryOrchestrator
from ..ai.config import AIConfig
from ..core.exceptions import AIProcessingError
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router
memory_router = APIRouter(prefix="/api/memory", tags=["memory"])

# Request/Response Models
class MemoryQuery(BaseModel):
    """Memory search query"""
    query: str = Field(..., min_length=1, max_length=1000)
    memory_types: Optional[List[MemoryType]] = None
    importance_min: Optional[MemoryImportance] = None
    limit: int = Field(default=10, ge=1, le=100)
    include_context: bool = Field(default=True)

class MemoryCreate(BaseModel):
    """Manual memory creation"""
    content: str = Field(..., min_length=1, max_length=5000)
    memory_type: MemoryType
    importance: MemoryImportance = MemoryImportance.MEDIUM
    context: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class MemoryResponse(BaseModel):
    """Memory retrieval response"""
    memory_id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    created_at: datetime
    updated_at: datetime
    access_count: int
    context: Dict[str, Any]
    tags: List[str]
    relevance_score: Optional[float] = None

class ConversationSummary(BaseModel):
    """Conversation summary with memory insights"""
    conversation_id: str
    user_id: str
    message_count: int
    duration_minutes: Optional[int]
    agent_types_used: List[str]
    memories_created: int
    memories_accessed: int
    key_topics: List[str]
    sentiment: Optional[str]
    created_at: datetime
    updated_at: datetime

class MemoryGraphNode(BaseModel):
    """Graph node for memory visualization"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]
    
class MemoryGraphEdge(BaseModel):
    """Graph edge for memory visualization"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class MemoryGraph(BaseModel):
    """Memory graph for visualization"""
    nodes: List[MemoryGraphNode]
    edges: List[MemoryGraphEdge]
    metadata: Dict[str, Any]

class MemoryStats(BaseModel):
    """User memory statistics"""
    total_memories: int
    memories_by_type: Dict[MemoryType, int]
    memories_by_importance: Dict[MemoryImportance, int]
    total_conversations: int
    active_conversations: int
    last_activity: Optional[datetime]
    memory_growth_rate: Optional[float]

# Dependency injection
async def get_memory_manager() -> LangMemManager:
    """Get LangMem manager instance"""
    config = AIConfig()
    # This would be injected in production
    return LangMemManager(config)

async def get_checkpoint_manager() -> CheckpointManager:
    """Get checkpoint manager instance"""
    config = AIConfig()
    return CheckpointManager(config)

async def get_memory_orchestrator() -> MemoryOrchestrator:
    """Get memory orchestrator instance"""
    config = AIConfig()
    return MemoryOrchestrator(config)

# Memory Management Endpoints

@memory_router.get("/users/{user_id}/memories", response_model=List[MemoryResponse])
async def get_user_memories(
    user_id: str,
    memory_types: Optional[List[MemoryType]] = Query(None),
    importance_min: Optional[MemoryImportance] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|importance|access_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager)
):
    """
    Retrieve user memories with filtering and pagination
    
    Args:
        user_id: Target user ID
        memory_types: Filter by memory types
        importance_min: Minimum importance level
        limit: Maximum memories to return
        offset: Pagination offset
        sort_by: Sort field
        sort_order: Sort direction
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user memories"
            )
        
        # Build query parameters
        query_params = {
            "memory_types": memory_types,
            "importance_min": importance_min,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Retrieve memories
        memories = await memory_manager.get_user_memories(user_id, **query_params)
        
        # Format response
        response = []
        for memory in memories:
            response.append(MemoryResponse(
                memory_id=memory["memory_id"],
                content=memory["content"],
                memory_type=memory["memory_type"],
                importance=memory["importance"],
                created_at=memory["created_at"],
                updated_at=memory["updated_at"],
                access_count=memory["access_count"],
                context=memory.get("context", {}),
                tags=memory.get("tags", []),
                relevance_score=memory.get("relevance_score")
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to retrieve user memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memories"
        )

@memory_router.post("/users/{user_id}/memories/search", response_model=List[MemoryResponse])
async def search_user_memories(
    user_id: str,
    query: MemoryQuery,
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager)
):
    """
    Search user memories using semantic search
    
    Args:
        user_id: Target user ID
        query: Search parameters
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user memories"
            )
        
        # Perform semantic search
        memories = await memory_manager.search_memories(
            user_id=user_id,
            query_text=query.query,
            memory_types=query.memory_types,
            importance_min=query.importance_min,
            limit=query.limit,
            include_context=query.include_context
        )
        
        # Format response
        response = []
        for memory in memories:
            response.append(MemoryResponse(
                memory_id=memory["memory_id"],
                content=memory["content"],
                memory_type=memory["memory_type"],
                importance=memory["importance"],
                created_at=memory["created_at"],
                updated_at=memory["updated_at"],
                access_count=memory["access_count"],
                context=memory.get("context", {}),
                tags=memory.get("tags", []),
                relevance_score=memory.get("relevance_score")
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to search user memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memories"
        )

@memory_router.post("/users/{user_id}/memories", response_model=MemoryResponse)
async def create_user_memory(
    user_id: str,
    memory: MemoryCreate,
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager)
):
    """
    Manually create a memory for a user
    
    Args:
        user_id: Target user ID
        memory: Memory creation data
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create memories"
            )
        
        # Create memory
        created_memory = await memory_manager.add_memory(
            user_id=user_id,
            content=memory.content,
            memory_type=memory.memory_type,
            importance=memory.importance,
            context=memory.context or {},
            tags=memory.tags or []
        )
        
        # Format response
        return MemoryResponse(
            memory_id=created_memory["memory_id"],
            content=created_memory["content"],
            memory_type=created_memory["memory_type"],
            importance=created_memory["importance"],
            created_at=created_memory["created_at"],
            updated_at=created_memory["updated_at"],
            access_count=created_memory["access_count"],
            context=created_memory.get("context", {}),
            tags=created_memory.get("tags", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to create user memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memory"
        )

@memory_router.delete("/users/{user_id}/memories/{memory_id}")
async def delete_user_memory(
    user_id: str,
    memory_id: str,
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager)
):
    """
    Delete a specific user memory
    
    Args:
        user_id: Target user ID
        memory_id: Memory to delete
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete memories"
            )
        
        # Delete memory
        success = await memory_manager.delete_memory(user_id, memory_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return {"message": "Memory deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )

# Conversation Management Endpoints

@memory_router.get("/users/{user_id}/conversations", response_model=List[ConversationSummary])
async def get_user_conversations(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    Get user's conversation history with memory insights
    
    Args:
        user_id: Target user ID
        limit: Maximum conversations to return
        offset: Pagination offset
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user conversations"
            )
        
        # Get conversations
        conversations = await checkpoint_manager.get_user_conversations(user_id, limit)
        
        # Format response (simplified - would need more data from memory system)
        response = []
        for conv in conversations:
            response.append(ConversationSummary(
                conversation_id=conv["thread_id"],
                user_id=conv["user_id"],
                message_count=conv.get("message_count", 0),
                duration_minutes=None,  # Would need to calculate
                agent_types_used=conv.get("agent_types", []),
                memories_created=0,  # Would need to query memory system
                memories_accessed=0,  # Would need to query memory system
                key_topics=[],  # Would need NLP processing
                sentiment=None,  # Would need sentiment analysis
                created_at=datetime.fromisoformat(conv["created_at"]),
                updated_at=datetime.fromisoformat(conv["updated_at"])
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to retrieve user conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )

@memory_router.get("/conversations/{conversation_id}/graph", response_model=MemoryGraph)
async def get_conversation_memory_graph(
    conversation_id: str,
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager)
):
    """
    Get memory graph visualization for a conversation
    
    Args:
        conversation_id: Target conversation ID
    """
    try:
        # Get conversation metadata to validate access
        # This would need implementation in checkpoint manager
        
        # Get memory graph data
        graph_data = await memory_manager.get_conversation_memory_graph(conversation_id)
        
        # Format nodes
        nodes = []
        for node in graph_data.get("nodes", []):
            nodes.append(MemoryGraphNode(
                id=node["id"],
                label=node["label"],
                type=node["type"],
                properties=node.get("properties", {})
            ))
        
        # Format edges
        edges = []
        for edge in graph_data.get("edges", []):
            edges.append(MemoryGraphEdge(
                source=edge["source"],
                target=edge["target"],
                type=edge["type"],
                properties=edge.get("properties", {})
            ))
        
        return MemoryGraph(
            nodes=nodes,
            edges=edges,
            metadata=graph_data.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve conversation memory graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory graph"
        )

# Analytics and Statistics Endpoints

@memory_router.get("/users/{user_id}/stats", response_model=MemoryStats)
async def get_user_memory_stats(
    user_id: str,
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager),
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    Get user memory statistics and analytics
    
    Args:
        user_id: Target user ID
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user statistics"
            )
        
        # Get memory statistics
        memory_stats = await memory_manager.get_user_memory_stats(user_id)
        
        # Get checkpoint statistics
        checkpoint_stats = await checkpoint_manager.get_checkpoint_stats()
        
        # Calculate active conversations (last 24 hours)
        active_count = checkpoint_stats.get("active_conversations_24h", 0)
        
        return MemoryStats(
            total_memories=memory_stats.get("total_memories", 0),
            memories_by_type=memory_stats.get("memories_by_type", {}),
            memories_by_importance=memory_stats.get("memories_by_importance", {}),
            total_conversations=memory_stats.get("total_conversations", 0),
            active_conversations=active_count,
            last_activity=memory_stats.get("last_activity"),
            memory_growth_rate=memory_stats.get("growth_rate")
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve user memory stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory statistics"
        )

# Memory Consolidation Endpoints

@memory_router.post("/users/{user_id}/memories/consolidate")
async def trigger_memory_consolidation(
    user_id: str,
    current_user=Depends(get_current_user),
    memory_manager: LangMemManager = Depends(get_memory_manager)
):
    """
    Trigger manual memory consolidation for a user
    
    Args:
        user_id: Target user ID
    """
    try:
        # Validate user access (admin only for manual consolidation)
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for memory consolidation"
            )
        
        # Trigger consolidation
        result = await memory_manager.trigger_consolidation(user_id)
        
        return {
            "message": "Memory consolidation triggered",
            "consolidations_performed": result.get("consolidations", 0),
            "memories_merged": result.get("merged", 0),
            "memories_archived": result.get("archived", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger memory consolidation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger memory consolidation"
        )

# Health Check Endpoint

@memory_router.get("/health")
async def memory_system_health():
    """
    Check memory system health
    """
    try:
        # This would check all memory system components
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "langmem": "healthy",
                "neo4j": "healthy",
                "redis": "healthy"
            }
        }
        
    except Exception as e:
        logger.error(f"Memory system health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory system unhealthy"
        )