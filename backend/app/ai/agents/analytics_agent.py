"""
Leadership Analytics Agent

Specialized agent for entertainment industry business intelligence
and performance analytics.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter
from ..llm.prompt_templates import PromptType
from ..services.knowledge_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class LeadershipAnalyticsAgent(BaseAgent):
    """Leadership analytics agent for business intelligence"""
    
    def __init__(
        self,
        config: AIConfig,
        llm_router: LLMRouter,
        knowledge_service: Optional[KnowledgeGraphService] = None,
        redis_client=None,
        model_config_manager=None
    ):
        super().__init__(
            agent_type=AgentType.ANALYTICS,
            config=config,
            llm_router=llm_router,
            redis_client=redis_client,
            model_config_manager=model_config_manager
        )
        
        self.knowledge_service = knowledge_service

    def _get_prompt_type(self) -> PromptType:
        return PromptType.LEADERSHIP_ANALYTICS

    def _get_preferred_provider(self) -> Optional[str]:
        return "openai"  # Use OpenAI for complex analytics

    async def _analyze_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["performance", "metrics", "kpi"]):
            return {"intent": "performance_analysis", "task_type": "performance_analysis"}
        elif any(word in query_lower for word in ["forecast", "predict", "trend"]):
            return {"intent": "forecasting", "task_type": "forecasting"}
        else:
            return {"intent": "general", "task_type": None}

    async def analyze_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        
        if not self.knowledge_service:
            return {"error": "Knowledge service not available"}
        
        try:
            insights = await self.knowledge_service.generate_insights(
                context=metrics,
                insight_type="talent_market"
            )
            
            analysis_prompt = f"""
            Analyze performance metrics:
            {metrics}
            
            Market Context:
            {insights}
            
            Provide:
            1. Performance Summary
            2. Key Trends and Insights  
            3. Benchmark Comparisons
            4. Areas for Improvement
            5. Strategic Recommendations
            """
            
            response = await self.chat(analysis_prompt, {"role": "analytics_director"})
            
            return {
                "metrics": metrics,
                "analysis": response["content"],
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}