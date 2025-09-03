"""
Talent Acquisition Agent

Specialized agent for entertainment industry talent sourcing,
matching, and union compliance.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent
from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter
from ..llm.prompt_templates import PromptType
from ..services.knowledge_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class TalentAcquisitionAgent(BaseAgent):
    """Talent acquisition agent specialized in entertainment industry hiring"""
    
    def __init__(
        self,
        config: AIConfig,
        llm_router: LLMRouter,
        knowledge_service: Optional[KnowledgeGraphService] = None,
        redis_client=None,
        model_config_manager=None
    ):
        super().__init__(
            agent_type=AgentType.TALENT,
            config=config,
            llm_router=llm_router,
            redis_client=redis_client,
            model_config_manager=model_config_manager
        )
        
        self.knowledge_service = knowledge_service

    def _get_prompt_type(self) -> PromptType:
        return PromptType.TALENT_ACQUISITION

    async def _analyze_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["find", "search", "hire", "talent"]):
            return {"intent": "talent_search", "task_type": "talent_search"}
        elif any(word in query_lower for word in ["assess", "evaluate", "skill"]):
            return {"intent": "skill_assessment", "task_type": "skill_assessment"}
        else:
            return {"intent": "general", "task_type": None}

    async def find_talent(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Find talent matching requirements"""
        
        if not self.knowledge_service:
            return {"error": "Knowledge service not available"}
        
        try:
            results = await self.knowledge_service.intelligent_talent_search(requirements)
            
            talent_prompt = f"""
            Based on the talent search results for:
            Skills: {requirements.get('skills', [])}
            Location: {requirements.get('location', 'Any')}
            Budget: {requirements.get('budget_range', 'Not specified')}
            
            Search Results Summary:
            - Semantic matches: {len(results.get('semantic_matches', []))}
            - Skill matches: {len(results.get('skill_matches', []))}
            - Network recommendations: {len(results.get('network_recommendations', []))}
            
            Provide:
            1. Top 5 Talent Recommendations
            2. Match Quality Assessment
            3. Availability Considerations
            4. Rate Expectations
            5. Next Steps for Outreach
            """
            
            response = await self.chat(talent_prompt, {"role": "talent_director"})
            
            return {
                "requirements": requirements,
                "search_results": results,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Talent search failed: {e}")
            return {"error": str(e)}