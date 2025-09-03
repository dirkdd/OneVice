"""
Memory-Enhanced AI WebSocket Endpoints

Real-time WebSocket communication for AI agent interactions with
advanced memory capabilities and conversation continuity.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState

from ...ai.workflows.memory_orchestrator import MemoryOrchestrator
from ...ai.config import AgentType, ai_config
from ...ai.memory.memory_types import MemoryQuery, MemoryType
from ...core.exceptions import AIProcessingError
from ...core.redis import get_redis

logger = logging.getLogger(__name__)

memory_websocket_router = APIRouter()

# Global memory orchestrator
memory_orchestrator: Optional[MemoryOrchestrator] = None


class MemoryConnectionManager:
    """Enhanced WebSocket connection manager with memory capabilities"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(
        self, 
        websocket: WebSocket, 
        connection_id: str, 
        user_id: str,
        conversation_id: Optional[str] = None
    ):
        """Accept and store WebSocket connection with metadata"""
        
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "connected_at": datetime.utcnow().isoformat(),
            "message_count": 0
        }
        
        logger.info(f"Memory WebSocket connected: {connection_id} for user {user_id}")

    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        if connection_id in self.connection_metadata:
            user_id = self.connection_metadata[connection_id]["user_id"]
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            del self.connection_metadata[connection_id]
            
        logger.info(f"Memory WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        
        websocket = self.active_connections.get(connection_id)
        if websocket and websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
                
                # Update message count
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["message_count"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")

    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all user's connections"""
        
        connection_ids = self.user_connections.get(user_id, set())
        
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)

    async def broadcast_to_conversation(
        self, 
        message: Dict[str, Any], 
        conversation_id: str,
        exclude_connection: Optional[str] = None
    ):
        """Broadcast message to all connections in a conversation"""
        
        for connection_id, metadata in self.connection_metadata.items():
            if (metadata.get("conversation_id") == conversation_id and 
                connection_id != exclude_connection):
                await self.send_personal_message(message, connection_id)


# Global connection manager
manager = MemoryConnectionManager()


async def get_memory_orchestrator() -> MemoryOrchestrator:
    """Get initialized memory orchestrator"""
    
    global memory_orchestrator
    if not memory_orchestrator:
        memory_orchestrator = MemoryOrchestrator(ai_config)
        await memory_orchestrator.initialize()
    return memory_orchestrator


@memory_websocket_router.websocket("/ws/ai/memory-chat/{user_id}")
async def websocket_memory_chat(
    websocket: WebSocket,
    user_id: str,
    conversation_id: Optional[str] = None
):
    """
    Enhanced WebSocket endpoint for AI chat with memory capabilities
    
    Features:
    - Conversation persistence across sessions
    - Memory-aware agent routing
    - Real-time memory insights
    - Background memory processing
    """
    
    connection_id = f"memory_{user_id}_{datetime.utcnow().timestamp()}"
    orchestrator = await get_memory_orchestrator()
    
    try:
        # Accept connection
        await manager.connect(websocket, connection_id, user_id, conversation_id)
        
        # Send welcome message with memory capabilities
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "features": [
                "memory_awareness",
                "conversation_persistence", 
                "intelligent_routing",
                "real_time_insights"
            ],
            "available_agents": [agent.value for agent in AgentType],
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Load conversation history if resuming
        if conversation_id:
            await send_conversation_history(connection_id, conversation_id, user_id)
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process message with memory
                await handle_memory_websocket_message(
                    data, connection_id, user_id, conversation_id, orchestrator
                )
                
            except WebSocketDisconnect:
                logger.info(f"Memory WebSocket disconnected normally: {connection_id}")
                break
                
            except Exception as e:
                logger.error(f"Memory WebSocket message handling error: {e}")
                
                # Send error message
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Message processing failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, connection_id)
                
    except Exception as e:
        logger.error(f"Memory WebSocket connection error: {e}")
        
    finally:
        # Clean up connection
        manager.disconnect(connection_id)


async def handle_memory_websocket_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str,
    conversation_id: Optional[str],
    orchestrator: MemoryOrchestrator
):
    """Handle incoming WebSocket message with memory capabilities"""
    
    message_type = data.get("type", "chat")
    
    if message_type == "chat":
        await handle_memory_chat_message(
            data, connection_id, user_id, conversation_id, orchestrator
        )
    elif message_type == "memory_query":
        await handle_memory_query_message(data, connection_id, user_id, orchestrator)
    elif message_type == "conversation_history":
        await handle_conversation_history_request(data, connection_id, user_id)
    elif message_type == "agent_preference":
        await handle_agent_preference_message(data, connection_id, user_id)
    elif message_type == "memory_insights":
        await handle_memory_insights_request(data, connection_id, user_id, orchestrator)
    elif message_type == "ping":
        await handle_ping_message(connection_id)
    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def handle_memory_chat_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str,
    conversation_id: Optional[str],
    orchestrator: MemoryOrchestrator
):
    """Handle chat message with memory-enhanced processing"""
    
    try:
        message = data.get("message", "")
        preferred_agent = data.get("preferred_agent")
        
        if not message.strip():
            await manager.send_personal_message({
                "type": "error",
                "message": "Empty message received",
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
            return
        
        # Parse preferred agent
        agent_type = None
        if preferred_agent:
            try:
                agent_type = AgentType(preferred_agent)
            except ValueError:
                logger.warning(f"Invalid agent type: {preferred_agent}")
        
        # Send acknowledgment with memory loading indicator
        await manager.send_personal_message({
            "type": "message_received",
            "message": message,
            "status": "loading_memory",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Send processing indicator
        await manager.send_personal_message({
            "type": "processing",
            "status": "memory_analysis",
            "agent_type": agent_type.value if agent_type else "auto",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Process with memory orchestrator
        response = await orchestrator.chat_with_memory(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            preferred_agent=agent_type,
            resume_from_checkpoint=True
        )
        
        # Update connection metadata with conversation ID
        if connection_id in manager.connection_metadata:
            manager.connection_metadata[connection_id]["conversation_id"] = response["conversation_id"]
        
        # Send enhanced response with memory context
        await manager.send_personal_message({
            "type": "ai_response",
            "content": response["content"],
            "conversation_id": response["conversation_id"],
            "agent_type": response["agent_type"],
            "routing": response["routing"],
            "memory_context": {
                "memories_used": response["memory_context"].get("total_memories", 0),
                "semantic_facts": len(response["memory_context"].get("semantic_facts", [])),
                "past_interactions": len(response["memory_context"].get("past_interactions", [])),
                "behavioral_patterns": len(response["memory_context"].get("behavioral_patterns", []))
            },
            "timestamp": response["timestamp"]
        }, connection_id)
        
        # Send memory insights if significant
        memory_context = response.get("memory_context", {})
        if memory_context.get("total_memories", 0) > 0:
            await send_memory_insights(connection_id, memory_context)
        
    except Exception as e:
        logger.error(f"Memory chat message handling failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to process chat message",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def handle_memory_query_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str,
    orchestrator: MemoryOrchestrator
):
    """Handle direct memory query requests"""
    
    try:
        query_text = data.get("query", "")
        memory_types_str = data.get("memory_types", [])
        limit = data.get("limit", 10)
        
        # Convert memory types
        memory_types = []
        for mt_str in memory_types_str:
            try:
                memory_types.append(MemoryType(mt_str))
            except ValueError:
                pass
        
        if not query_text.strip():
            await manager.send_personal_message({
                "type": "memory_query_error",
                "message": "Empty query provided",
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
            return
        
        # Search memories
        results = await orchestrator.memory_manager.get_relevant_memories(
            user_id=user_id,
            query=query_text,
            memory_types=memory_types or None,
            limit=limit
        )
        
        # Format results for WebSocket
        memory_results = []
        for result in results:
            memory_results.append({
                "id": result.memory.id,
                "content": result.memory.content,
                "type": result.memory.memory_type.value,
                "importance": result.memory.importance.value,
                "similarity_score": result.similarity_score,
                "created_at": result.memory.created_at.isoformat()
            })
        
        await manager.send_personal_message({
            "type": "memory_query_result",
            "query": query_text,
            "results": memory_results,
            "total_found": len(memory_results),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Memory query handling failed: {e}")
        await manager.send_personal_message({
            "type": "memory_query_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def handle_conversation_history_request(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str
):
    """Handle conversation history requests"""
    
    try:
        requested_conversation_id = data.get("conversation_id")
        
        if requested_conversation_id:
            await send_conversation_history(connection_id, requested_conversation_id, user_id)
        else:
            # Send list of recent conversations
            orchestrator = await get_memory_orchestrator()
            conversations = await orchestrator.checkpoint_manager.get_user_conversations(
                user_id, limit=20
            )
            
            await manager.send_personal_message({
                "type": "conversation_list",
                "conversations": conversations,
                "total": len(conversations),
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
            
    except Exception as e:
        logger.error(f"Conversation history request failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to get conversation history",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def handle_agent_preference_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str
):
    """Handle agent preference updates"""
    
    try:
        preferred_agent = data.get("preferred_agent")
        routing_mode = data.get("routing_mode", "auto")
        
        # Store preference in Redis for session
        redis_client = await get_redis()
        preference_key = f"agent_preference:{user_id}"
        
        preference_data = {
            "preferred_agent": preferred_agent,
            "routing_mode": routing_mode,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await redis_client.setex(
            preference_key,
            3600,  # 1 hour TTL
            json.dumps(preference_data)
        )
        
        await manager.send_personal_message({
            "type": "preference_updated",
            "preferred_agent": preferred_agent,
            "routing_mode": routing_mode,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Agent preference update failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to update agent preference",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def handle_memory_insights_request(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str,
    orchestrator: MemoryOrchestrator
):
    """Handle memory insights requests"""
    
    try:
        # Get user memory statistics
        stats = await orchestrator.memory_manager.schema.get_user_memory_stats(user_id)
        
        await manager.send_personal_message({
            "type": "memory_insights",
            "stats": {
                "total_memories": stats.total_memories,
                "memory_breakdown": {k.value: v for k, v in stats.memory_breakdown.items()},
                "importance_breakdown": {k.value: v for k, v in stats.importance_breakdown.items()},
                "avg_access_frequency": stats.avg_access_frequency,
                "oldest_memory": stats.oldest_memory_date.isoformat() if stats.oldest_memory_date else None,
                "most_recent": stats.most_recent_date.isoformat() if stats.most_recent_date else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Memory insights request failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to get memory insights",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def handle_ping_message(connection_id: str):
    """Handle ping message for connection health check"""
    
    await manager.send_personal_message({
        "type": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }, connection_id)


async def send_conversation_history(
    connection_id: str,
    conversation_id: str,
    user_id: str
):
    """Send conversation history to client"""
    
    try:
        orchestrator = await get_memory_orchestrator()
        history = await orchestrator.get_conversation_history(
            conversation_id, user_id, include_checkpoints=True
        )
        
        await manager.send_personal_message({
            "type": "conversation_history",
            "conversation_id": conversation_id,
            "history": history,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Failed to send conversation history: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to load conversation history",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)


async def send_memory_insights(
    connection_id: str,
    memory_context: Dict[str, Any]
):
    """Send relevant memory insights to client"""
    
    try:
        insights = []
        
        # Highlight important semantic facts
        semantic_facts = memory_context.get("semantic_facts", [])
        high_confidence_facts = [
            fact for fact in semantic_facts 
            if fact.get("confidence", 0) > 0.9
        ]
        
        if high_confidence_facts:
            insights.append({
                "type": "high_confidence_facts",
                "message": f"Found {len(high_confidence_facts)} high-confidence facts about your preferences",
                "data": high_confidence_facts[:3]  # Top 3
            })
        
        # Highlight behavioral patterns
        patterns = memory_context.get("behavioral_patterns", [])
        successful_patterns = [
            pattern for pattern in patterns
            if pattern.get("success_rate", 0) > 0.8
        ]
        
        if successful_patterns:
            insights.append({
                "type": "behavioral_patterns",
                "message": f"Applied {len(successful_patterns)} successful interaction patterns",
                "data": successful_patterns[:2]  # Top 2
            })
        
        # Send insights if any
        if insights:
            await manager.send_personal_message({
                "type": "memory_insights_realtime",
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
            
    except Exception as e:
        logger.error(f"Failed to send memory insights: {e}")


# Cleanup function for graceful shutdown
async def cleanup_memory_websockets():
    """Cleanup WebSocket connections on shutdown"""
    
    logger.info("Cleaning up memory WebSocket connections...")
    
    # Close all active connections
    for connection_id, websocket in manager.active_connections.items():
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket {connection_id}: {e}")
    
    # Cleanup orchestrator
    global memory_orchestrator
    if memory_orchestrator:
        await memory_orchestrator.cleanup()
    
    logger.info("Memory WebSocket cleanup completed")