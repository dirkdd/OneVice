"""
AI WebSocket Endpoints

Real-time WebSocket communication for AI agent interactions.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ...ai.workflows.orchestrator import AgentOrchestrator
from ...ai.config import AgentType, ai_config
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

websocket_router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")

    def disconnect(self, connection_id: str, user_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        websocket = self.active_connections.get(connection_id)
        if websocket and websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")

    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to specific user"""
        connection_id = self.user_connections.get(user_id)
        if connection_id:
            await self.send_personal_message(message, connection_id)

# Global connection manager
manager = ConnectionManager()

# Initialize orchestrator
orchestrator = AgentOrchestrator(ai_config)

@websocket_router.websocket("/ws/ai/chat/{user_id}")
async def websocket_ai_chat(
    websocket: WebSocket,
    user_id: str,
    conversation_id: Optional[str] = None
):
    """
    WebSocket endpoint for real-time AI chat
    
    Supports:
    - Real-time AI conversations
    - Streaming responses
    - Multi-agent coordination
    - Session management
    """
    
    connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
    
    try:
        # Accept connection
        await manager.connect(websocket, connection_id, user_id)
        
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "available_agents": [agent.value for agent in AgentType],
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process message
                await handle_websocket_message(data, connection_id, user_id)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally: {connection_id}")
                break
                
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                
                # Send error message
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Message processing failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, connection_id)
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        
    finally:
        # Clean up connection
        manager.disconnect(connection_id, user_id)

async def handle_websocket_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str
):
    """Handle incoming WebSocket message"""
    
    message_type = data.get("type", "chat")
    
    if message_type in ["chat", "user_message"]:
        await handle_chat_message(data, connection_id, user_id)
    elif message_type == "ping":
        await handle_ping_message(connection_id)
    elif message_type == "agent_select":
        await handle_agent_selection(data, connection_id)
    else:
        # Log unknown message types instead of erroring
        logger.info(f"Received unknown message type: {message_type}")
        await manager.send_personal_message({
            "type": "info",
            "message": f"Message type {message_type} not yet implemented",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)

async def handle_chat_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str
):
    """Handle chat message with AI agent routing based on preferences"""
    
    try:
        # Support both frontend format (content) and legacy (message)
        message = data.get("content") or data.get("message", "")
        context = data.get("context")
        metadata = data.get("metadata", {})
        conversation_id = data.get("conversation_id")
        
        # Extract agent preferences from message metadata
        agent_preferences = metadata.get("agent_preferences", {})
        routing_mode = agent_preferences.get("routing_mode", "auto")
        selected_agents = agent_preferences.get("selected_agents", [])
        
        # Legacy agent_type support for backwards compatibility
        legacy_agent_type = data.get("agent_type")
        
        if not message.strip():
            await manager.send_personal_message({
                "type": "error",
                "message": "Empty message received",
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
            return
        
        # Determine preferred agent based on routing mode and preferences
        preferred_agent = None
        
        # Log routing information for debugging
        logger.info(f"Message routing - Mode: {routing_mode}, Selected agents: {selected_agents}, Context: {context}")
        
        if legacy_agent_type:
            # Legacy single agent support
            try:
                preferred_agent = AgentType(legacy_agent_type)
                logger.info(f"Using legacy agent type: {preferred_agent}")
            except ValueError:
                logger.warning(f"Invalid legacy agent type: {legacy_agent_type}")
        
        elif routing_mode == "single" and selected_agents:
            # Single agent mode - use the selected agent
            try:
                preferred_agent = AgentType(selected_agents[0])
                logger.info(f"Single agent mode: Using {preferred_agent}")
            except (ValueError, IndexError):
                logger.warning(f"Invalid agent in single mode: {selected_agents}")
        
        elif routing_mode == "multi" and selected_agents:
            # Multi-agent mode - for now use first agent
            # TODO: Implement multi-agent response aggregation
            try:
                preferred_agent = AgentType(selected_agents[0])
                logger.info(f"Multi-agent mode: Using {preferred_agent} (TODO: implement multi-agent aggregation)")
            except (ValueError, IndexError):
                logger.warning(f"Invalid agents in multi mode: {selected_agents}")
        
        # else: auto mode or fallback - let orchestrator decide (preferred_agent = None)
        
        # Send acknowledgment with routing information
        await manager.send_personal_message({
            "type": "message_received",
            "message": message,
            "routing_mode": routing_mode,
            "selected_agent": preferred_agent.value if preferred_agent else "auto",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Prepare user context
        user_context = {
            "user_id": user_id,
            "role": "user",  # In production, this would come from authentication
            "access_level": "basic",
            "connection_type": "websocket"
        }
        
        # Send "thinking" indicator
        await manager.send_personal_message({
            "type": "thinking",
            "agent_type": preferred_agent.value if preferred_agent else "auto",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Route to AI agent
        response = await orchestrator.route_query(
            query=message,
            user_context=user_context,
            preferred_agent=preferred_agent,
            conversation_id=conversation_id
        )
        
        # Send response
        await manager.send_personal_message({
            "type": "ai_response",
            "content": response["content"],
            "conversation_id": response["conversation_id"],
            "agent_type": response["agent_type"],
            "routing": response["routing"],
            "metadata": response.get("metadata", {}),
            "timestamp": response["timestamp"]
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Chat message handling failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to process chat message",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)

async def handle_ping_message(connection_id: str):
    """Handle ping message for connection health check"""
    
    await manager.send_personal_message({
        "type": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }, connection_id)

async def handle_agent_selection(
    data: Dict[str, Any],
    connection_id: str
):
    """Handle agent selection message"""
    
    agent_type_str = data.get("agent_type")
    
    try:
        if agent_type_str == "auto":
            agent_type = None
        else:
            agent_type = AgentType(agent_type_str)
        
        # Get agent capabilities
        if agent_type:
            agent = orchestrator.agents.get(agent_type)
            if agent and hasattr(agent, 'get_agent_capabilities'):
                capabilities = await agent.get_agent_capabilities()
            else:
                capabilities = {"agent_type": agent_type.value, "status": "available"}
        else:
            capabilities = {"agent_type": "auto", "description": "Automatic agent selection"}
        
        await manager.send_personal_message({
            "type": "agent_selected",
            "agent_type": agent_type.value if agent_type else "auto",
            "capabilities": capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
    except ValueError:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Invalid agent type: {agent_type_str}",
            "available_agents": [agent.value for agent in AgentType],
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)

@websocket_router.websocket("/ws/ai/stream/{user_id}")
async def websocket_ai_stream(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint for streaming AI responses
    
    Provides token-by-token streaming of AI responses for better UX.
    """
    
    connection_id = f"stream_{user_id}_{datetime.utcnow().timestamp()}"
    
    try:
        await manager.connect(websocket, connection_id, user_id)
        
        await manager.send_personal_message({
            "type": "stream_ready",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        # Streaming message loop
        while True:
            try:
                data = await websocket.receive_json()
                await handle_streaming_message(data, connection_id, user_id)
                
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                await manager.send_personal_message({
                    "type": "stream_error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, connection_id)
                
    finally:
        manager.disconnect(connection_id, user_id)

async def handle_streaming_message(
    data: Dict[str, Any],
    connection_id: str,
    user_id: str
):
    """Handle streaming AI response"""
    
    # This is a simplified implementation
    # In production, this would use the streaming capabilities of the LLM router
    
    message = data.get("message", "")
    if not message.strip():
        return
    
    # Send streaming start
    await manager.send_personal_message({
        "type": "stream_start",
        "timestamp": datetime.utcnow().isoformat()
    }, connection_id)
    
    try:
        # Get regular response (in production, this would be streaming)
        user_context = {"user_id": user_id, "role": "user"}
        response = await orchestrator.route_query(message, user_context)
        
        # Simulate streaming by sending chunks
        content = response["content"]
        chunk_size = 50
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            
            await manager.send_personal_message({
                "type": "stream_chunk",
                "content": chunk,
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
            
            # Small delay for streaming effect
            await asyncio.sleep(0.1)
        
        # Send stream end
        await manager.send_personal_message({
            "type": "stream_end",
            "conversation_id": response["conversation_id"],
            "agent_type": response["agent_type"],
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Streaming response failed: {e}")
        await manager.send_personal_message({
            "type": "stream_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)