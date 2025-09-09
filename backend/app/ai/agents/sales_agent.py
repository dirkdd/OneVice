"""
Sales Intelligence Agent - LangGraph Tool Binding Version

Specialized agent for entertainment industry sales analysis using intelligent
tool selection instead of regex-based routing.
"""

import logging
from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent
from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter  
from ..llm.prompt_templates import PromptType
from ..services.knowledge_service import KnowledgeGraphService
from ...core.exceptions import AIProcessingError

# Import the new tool definitions
from ..tools.tool_definitions import get_all_priority_tools
from ..tools.dependencies import init_tool_dependencies

logger = logging.getLogger(__name__)


class SalesIntelligenceAgent(BaseAgent):
    """
    Sales intelligence agent with LangGraph tool binding.
    
    Key improvements over previous version:
    - Eliminates 200+ lines of regex patterns
    - Uses LLM-driven tool selection instead of manual intent detection
    - Automatic tool routing based on natural language understanding
    - Cleaner architecture with proper separation of concerns
    
    Specializes in:
    - Lead qualification and scoring
    - Market analysis and trends  
    - Competitive intelligence
    - Organization and person lookup
    - Project search and analysis
    """
    
    def __init__(
        self,
        config: AIConfig,
        llm_router: LLMRouter,
        knowledge_service: Optional[KnowledgeGraphService] = None,
        redis_client=None,
        model_config_manager=None
    ):
        super().__init__(
            agent_type=AgentType.SALES,
            config=config,
            llm_router=llm_router,
            redis_client=redis_client,
            model_config_manager=model_config_manager
        )
        
        self.knowledge_service = knowledge_service
        self.specialization = "sales_intelligence"
        
        logger.info("Initialized SalesIntelligenceAgent with LangGraph tool binding")

    async def setup(self):
        """Initialize async resources and bind tools"""
        await super().setup()
        
        # Initialize tool dependencies
        await init_tool_dependencies()
        
        # Bind the priority tools to this agent
        tools = get_all_priority_tools()
        self.bind_tools(tools)
        
        logger.info(f"SalesIntelligenceAgent setup complete with {len(tools)} tools bound")

    def _get_prompt_type(self) -> PromptType:
        """Get prompt type for sales agent"""
        return PromptType.SALES_INTELLIGENCE

    async def _analyze_query(
        self,
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simplified query analysis - no more regex patterns!
        
        With LangGraph tool binding, the LLM will intelligently decide
        which tools to call based on the tool descriptions and user query.
        We just need basic context preparation.
        """
        
        logger.debug(f"Analyzing sales query: '{query[:100]}...'")
        
        # Simple context preparation - no intent detection needed
        analysis_context = {
            "query_type": "sales_intelligence",
            "domain": "entertainment_industry", 
            "user_role": user_context.get("role", "sales"),
            "complexity": "moderate",
            "requires_tools": True  # This agent is tool-focused
        }
        
        # Add any specific user context that might help tool selection
        if "organization" in user_context:
            analysis_context["organization_context"] = user_context["organization"]
        if "project_type" in user_context:
            analysis_context["project_context"] = user_context["project_type"]
        
        logger.debug(f"Query analysis complete: {analysis_context}")
        return analysis_context

    async def get_sales_insights(
        self,
        query: str,
        user_context: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main interface for sales intelligence queries.
        
        This method leverages LangGraph's intelligent tool selection to provide
        comprehensive sales insights without manual routing.
        
        Examples of queries this handles automatically:
        - "Do we work with CocaCola?" → calls get_organization_profile
        - "Who is John Smith at Netflix?" → calls get_person_details  
        - "Find all automotive projects from 2023" → calls search_projects_by_criteria
        - "What similar projects exist to Nike campaign?" → calls find_similar_projects
        """
        
        try:
            # Use the base chat method which now includes intelligent tool routing
            response = await self.chat(
                message=query,
                user_context=user_context,
                conversation_id=conversation_id
            )
            
            # Enhanced response with sales-specific metadata
            enhanced_response = {
                **response,
                "agent_specialization": self.specialization,
                "tools_available": self.get_bound_tools(),
                "intelligence_type": "sales_analysis"
            }
            
            logger.info(f"Sales intelligence query processed: {len(response.get('content', ''))} chars")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Sales intelligence query failed: {e}")
            raise AIProcessingError(f"Sales intelligence processing failed: {e}")

    async def qualify_lead(
        self,
        lead_info: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Lead qualification using intelligent tool selection.
        
        The LLM will automatically select appropriate tools based on the lead information.
        """
        
        # Format the lead qualification query
        query_parts = []
        
        if lead_info.get("company_name"):
            query_parts.append(f"company: {lead_info['company_name']}")
        if lead_info.get("contact_name"):  
            query_parts.append(f"contact: {lead_info['contact_name']}")
        if lead_info.get("project_type"):
            query_parts.append(f"project type: {lead_info['project_type']}")
        if lead_info.get("budget"):
            query_parts.append(f"budget: {lead_info['budget']}")
        
        query = f"Qualify this lead and provide insights: {', '.join(query_parts)}"
        
        return await self.get_sales_insights(query, user_context)

    async def analyze_market_opportunity(
        self,
        segment: str,
        location: str = "global"
    ) -> Dict[str, Any]:
        """
        Market opportunity analysis using intelligent tool selection.
        """
        
        query = f"Analyze market opportunities for {segment} segment in {location} market. What similar projects and organizations should we consider?"
        
        user_context = {
            "role": "sales_analyst",
            "market_segment": segment,
            "geographic_focus": location
        }
        
        return await self.get_sales_insights(query, user_context)

    async def get_competitive_intelligence(
        self,
        competitor: str,
        focus_area: str = "projects"
    ) -> Dict[str, Any]:
        """
        Competitive intelligence gathering using intelligent tool selection.
        """
        
        query = f"Get competitive intelligence on {competitor}, focusing on {focus_area}. What projects have they done and who are the key people?"
        
        user_context = {
            "role": "competitive_analyst", 
            "competitor": competitor,
            "focus": focus_area
        }
        
        return await self.get_sales_insights(query, user_context)

    async def get_pricing_insights(
        self,
        project_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pricing insights using historical project data and intelligent tool selection.
        """
        
        project_type = project_details.get("type", "entertainment")
        scope = project_details.get("scope", "standard")
        timeline = project_details.get("timeline", "not specified")
        
        query = f"Find similar {project_type} projects with {scope} scope and provide pricing insights based on historical data. Timeline: {timeline}"
        
        user_context = {
            "role": "pricing_analyst",
            "project_type": project_type,
            "scope": scope
        }
        
        return await self.get_sales_insights(query, user_context)

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """
        Get comprehensive agent capabilities including tool information.
        """
        
        return {
            "agent_type": "sales_intelligence",
            "specialization": self.specialization,
            "architecture": "langgraph_tool_binding",
            "capabilities": [
                "Organization profile lookup",
                "Person details and contact information", 
                "People discovery at organizations",
                "Project search with multiple criteria",
                "Similar project recommendations",
                "Lead qualification automation",
                "Market opportunity analysis", 
                "Competitive intelligence gathering",
                "Pricing insights and recommendations"
            ],
            "tools": {
                "bound_tools": self.get_bound_tools(),
                "tool_count": self.get_tool_count(),
                "intelligent_selection": True,
                "manual_routing": False
            },
            "improvements": [
                "Eliminated 200+ lines of regex patterns",
                "LLM-driven tool selection", 
                "Natural language query understanding",
                "Automatic tool routing",
                "Reduced maintenance overhead",
                "Better query coverage",
                "More intelligent responses"
            ],
            "query_examples": [
                "Do we work with CocaCola?",
                "Who is the CMO at Netflix?", 
                "Find all automotive campaigns from 2023",
                "What projects are similar to the Nike campaign?",
                "Who wrote treatments for Boost Mobile?",
                "Show me commercial projects for Disney"
            ]
        }


# Backward compatibility aliases
SalesAgent = SalesIntelligenceAgent  # For existing imports