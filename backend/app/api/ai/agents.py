"""
AI Agents API Endpoints

Management endpoints for AI agents and specialized operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...ai.workflows.orchestrator import AgentOrchestrator
from ...ai.config import AgentType, ai_config
from ...middleware.auth import get_current_user

logger = logging.getLogger(__name__)

agents_router = APIRouter(prefix="/ai/agents", tags=["AI Agents"])

# Initialize orchestrator
orchestrator = AgentOrchestrator(ai_config)

# Pydantic models
class TalentSearchRequest(BaseModel):
    skills: List[str] = Field(..., description="Required skills")
    location: Optional[str] = Field(None, description="Location preference")
    budget_range: Optional[tuple] = Field(None, description="Budget range")
    project_type: Optional[str] = Field(None, description="Project type")
    description: Optional[str] = Field(None, description="Additional requirements")

class LeadQualificationRequest(BaseModel):
    company_name: str = Field(..., description="Company name")
    project_type: str = Field(..., description="Project type")
    budget: Optional[int] = Field(None, description="Project budget")
    timeline: Optional[str] = Field(None, description="Project timeline")
    location: Optional[str] = Field(None, description="Project location")
    contact_name: Optional[str] = Field(None, description="Contact person")

class PerformanceAnalysisRequest(BaseModel):
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    time_period: str = Field(..., description="Time period for analysis")
    focus_areas: Optional[List[str]] = Field(None, description="Specific focus areas")

@agents_router.get("/")
async def list_agents(
    current_user: dict = Depends(get_current_user)
):
    """List all available AI agents and their capabilities"""
    
    try:
        agents_info = []
        
        for agent_type, agent in orchestrator.agents.items():
            try:
                status = await agent.get_agent_status()
                
                # Get capabilities if available
                capabilities = {}
                if hasattr(agent, 'get_agent_capabilities'):
                    capabilities = await agent.get_agent_capabilities()
                
                agents_info.append({
                    "agent_type": agent_type.value,
                    "status": status.get("status", "unknown"),
                    "capabilities": capabilities,
                    "configuration": status.get("configuration", {})
                })
                
            except Exception as e:
                logger.error(f"Failed to get info for agent {agent_type}: {e}")
                agents_info.append({
                    "agent_type": agent_type.value,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "agents": agents_info,
            "total_agents": len(agents_info),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agents information")

@agents_router.post("/sales/qualify-lead")
async def qualify_lead(
    request: LeadQualificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Qualify a sales lead using the Sales Intelligence Agent"""
    
    try:
        sales_agent = orchestrator.agents.get(AgentType.SALES)
        if not sales_agent or not hasattr(sales_agent, 'qualify_lead'):
            raise HTTPException(status_code=404, detail="Sales agent not available")
        
        user_context = {
            "user_id": current_user.get("user_id"),
            "role": current_user.get("role", "user"),
            "department": current_user.get("department")
        }
        
        lead_info = request.dict()
        result = await sales_agent.qualify_lead(lead_info, user_context)
        
        return result
        
    except Exception as e:
        logger.error(f"Lead qualification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Lead qualification failed: {str(e)}")

@agents_router.post("/talent/search")
async def search_talent(
    request: TalentSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search for talent using the Talent Acquisition Agent"""
    
    try:
        talent_agent = orchestrator.agents.get(AgentType.TALENT)
        if not talent_agent or not hasattr(talent_agent, 'find_talent'):
            raise HTTPException(status_code=404, detail="Talent agent not available")
        
        requirements = request.dict()
        result = await talent_agent.find_talent(requirements)
        
        return result
        
    except Exception as e:
        logger.error(f"Talent search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Talent search failed: {str(e)}")

@agents_router.post("/analytics/performance")
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze performance metrics using the Leadership Analytics Agent"""
    
    try:
        analytics_agent = orchestrator.agents.get(AgentType.ANALYTICS)
        if not analytics_agent or not hasattr(analytics_agent, 'analyze_performance'):
            raise HTTPException(status_code=404, detail="Analytics agent not available")
        
        metrics_data = request.dict()
        result = await analytics_agent.analyze_performance(metrics_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

@agents_router.get("/{agent_type}/capabilities")
async def get_agent_capabilities(
    agent_type: AgentType,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed capabilities of a specific agent"""
    
    try:
        agent = orchestrator.agents.get(agent_type)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
        
        if hasattr(agent, 'get_agent_capabilities'):
            capabilities = await agent.get_agent_capabilities()
            return capabilities
        else:
            # Basic capabilities info
            status = await agent.get_agent_status()
            return {
                "agent_type": agent_type.value,
                "status": status.get("status"),
                "configuration": status.get("configuration"),
                "basic_capabilities": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get capabilities for {agent_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent capabilities")

@agents_router.post("/{agent_type}/direct-chat")
async def direct_agent_chat(
    agent_type: AgentType,
    message: str,
    current_user: dict = Depends(get_current_user),
    conversation_id: Optional[str] = None
):
    """Direct chat with a specific agent (bypassing orchestrator routing)"""
    
    try:
        agent = orchestrator.agents.get(agent_type)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
        
        user_context = {
            "user_id": current_user.get("user_id"),
            "role": current_user.get("role", "user"),
            "access_level": current_user.get("access_level", "basic"),
            "department": current_user.get("department")
        }
        
        response = await agent.chat(
            message=message,
            user_context=user_context,
            conversation_id=conversation_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Direct chat with {agent_type} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat with {agent_type} failed: {str(e)}")

@agents_router.get("/knowledge/search")
async def knowledge_search(
    query: str,
    search_type: str = "semantic",
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Search the knowledge graph"""
    
    try:
        if search_type == "semantic":
            results = await orchestrator.vector_service.semantic_search(
                query=query,
                limit=limit
            )
        else:
            results = await orchestrator.knowledge_service.queries.search_entities(
                search_term=query,
                limit=limit
            )
        
        return {
            "query": query,
            "search_type": search_type,
            "results": results,
            "count": len(results) if isinstance(results, list) else sum(len(v) for v in results.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")

@agents_router.get("/system/health")
async def system_health():
    """Get comprehensive system health status"""
    
    try:
        health = await orchestrator.get_agent_status()
        return health
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }