"""
AI Chat API Endpoints

REST endpoints for AI agent conversations and interactions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ...ai.workflows.orchestrator import AgentOrchestrator
from ...ai.config import AgentType, AIConfig, ai_config
from ...core.exceptions import AIProcessingError
from ...middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Initialize orchestrator (in production, this would be a dependency)
orchestrator = AgentOrchestrator(ai_config)

ai_chat_router = APIRouter(prefix="/ai", tags=["AI Chat"])

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    agent_type: Optional[AgentType] = Field(None, description="Preferred agent type")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuity")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")

class ChatResponse(BaseModel):
    content: str = Field(..., description="AI response content")
    conversation_id: str = Field(..., description="Conversation ID")
    agent_type: str = Field(..., description="Agent that handled the request")
    routing: Dict[str, Any] = Field(..., description="Routing information")
    metadata: Dict[str, Any] = Field(default={}, description="Response metadata")
    timestamp: str = Field(..., description="Response timestamp")

class AgentStatusResponse(BaseModel):
    agent_type: str
    status: str
    configuration: Dict[str, Any]
    llm_provider_stats: Dict[str, Any]
    timestamp: str

@ai_chat_router.on_event("startup")
async def startup_event():
    """Initialize AI services on startup"""
    try:
        await orchestrator.initialize_services()
        logger.info("AI services initialized successfully")
    except Exception as e:
        logger.error(f"AI service initialization failed: {e}")

@ai_chat_router.on_event("shutdown")
async def shutdown_event():
    """Cleanup AI services on shutdown"""
    try:
        await orchestrator.cleanup()
        logger.info("AI services cleaned up successfully")
    except Exception as e:
        logger.error(f"AI service cleanup failed: {e}")

@ai_chat_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Chat with AI agents
    
    Routes user queries to appropriate entertainment industry AI agents
    based on query content and user preferences.
    """
    
    try:
        # Prepare user context
        user_context = {
            "user_id": current_user.get("user_id"),
            "role": current_user.get("role", "user"),
            "access_level": current_user.get("access_level", "basic"),
            "department": current_user.get("department"),
            **request.context
        }
        
        # Route query to appropriate agent(s)
        response = await orchestrator.route_query(
            query=request.message,
            user_context=user_context,
            preferred_agent=request.agent_type,
            conversation_id=request.conversation_id
        )
        
        # Log interaction in background
        background_tasks.add_task(
            log_ai_interaction,
            user_id=current_user.get("user_id"),
            query=request.message,
            agent_type=response.get("agent_type"),
            conversation_id=response.get("conversation_id")
        )
        
        return ChatResponse(**response)
        
    except AIProcessingError as e:
        logger.error(f"AI processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@ai_chat_router.get("/agents/status")
async def get_agents_status(
    current_user: dict = Depends(get_current_user)
):
    """Get status of all AI agents and services"""
    
    try:
        status = await orchestrator.get_agent_status()
        return status
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")

@ai_chat_router.get("/agents/{agent_type}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_type: AgentType,
    current_user: dict = Depends(get_current_user)
):
    """Get status of specific AI agent"""
    
    try:
        agent = orchestrator.agents.get(agent_type)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
        
        status = await agent.get_agent_status()
        return AgentStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent status check failed: {e}")
        raise HTTPException(status_code=500, detail="Agent status check failed")

@ai_chat_router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history"""
    
    try:
        # This would need to be implemented based on how conversation history is stored
        # For now, return a placeholder
        return {
            "conversation_id": conversation_id,
            "messages": [],
            "participant_count": 1,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="History retrieval failed")

@ai_chat_router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Clear conversation history and state"""
    
    try:
        # Clear conversation for all agents
        success_count = 0
        for agent in orchestrator.agents.values():
            try:
                if await agent.clear_conversation(conversation_id):
                    success_count += 1
            except Exception as e:
                logger.warning(f"Failed to clear conversation for agent: {e}")
        
        return {
            "conversation_id": conversation_id,
            "cleared": success_count > 0,
            "agents_cleared": success_count,
            "total_agents": len(orchestrator.agents)
        }
        
    except Exception as e:
        logger.error(f"Conversation clearing failed: {e}")
        raise HTTPException(status_code=500, detail="Conversation clearing failed")

# Background task functions
async def log_ai_interaction(
    user_id: str,
    query: str,
    agent_type: str,
    conversation_id: str
):
    """Log AI interaction for analytics"""
    
    try:
        # This would typically log to a database or analytics service
        logger.info(f"AI Interaction: user={user_id}, agent={agent_type}, conv={conversation_id}")
        
    except Exception as e:
        logger.error(f"Interaction logging failed: {e}")

# Health check endpoints
@ai_chat_router.get("/health")
async def ai_health_check():
    """Health check for AI services"""
    
    try:
        # Check orchestrator status
        status = await orchestrator.get_agent_status()
        
        return {
            "status": "healthy" if status.get("orchestrator_status") == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": status.get("services", {}),
            "agents": {
                agent: info.get("status", "unknown")
                for agent, info in status.get("agents", {}).items()
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }