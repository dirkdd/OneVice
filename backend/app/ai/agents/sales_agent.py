"""
Sales Intelligence Agent

Specialized agent for entertainment industry sales analysis,
lead qualification, and market intelligence.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent
from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter  
from ..llm.prompt_templates import PromptType
from ..services.knowledge_service import KnowledgeGraphService
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class SalesIntelligenceAgent(BaseAgent):
    """
    Sales intelligence agent specialized in:
    - Lead qualification and scoring
    - Market analysis and trends  
    - Competitive intelligence
    - Pricing optimization
    - Opportunity assessment
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

    def _get_prompt_type(self) -> PromptType:
        """Get prompt type for sales agent"""
        return PromptType.SALES_INTELLIGENCE

    async def _analyze_query(
        self,
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze sales-related query for context"""
        
        query_lower = query.lower()
        
        # Detect query intent
        intent = "general"
        task_params = {}
        
        if any(word in query_lower for word in ["lead", "qualify", "score", "prospect"]):
            intent = "lead_qualification"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["market", "trend", "analysis", "competitive"]):
            intent = "market_analysis"
            task_params = {
                "query": query,
                "timeframe": "current",
                "segment": user_context.get("industry_segment", "entertainment"),
                "location": user_context.get("location", "global")
            }
            
        elif any(word in query_lower for word in ["budget", "cost", "pricing", "rate"]):
            intent = "budget_analysis"
            task_params = {"query": query, "context": user_context}
        
        return {
            "intent": intent,
            "task_type": intent,
            "task_params": task_params,
            "requires_knowledge_graph": intent in ["market_analysis", "lead_qualification"],
            "complexity": "moderate" if intent != "general" else "simple"
        }

    async def qualify_lead(
        self,
        lead_info: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Qualify and score a sales lead"""
        
        if not self.knowledge_service:
            raise AIProcessingError("Knowledge service required for lead qualification")
        
        try:
            # Analyze lead against similar projects
            project_intelligence = await self.knowledge_service.project_intelligence({
                "type": lead_info.get("project_type"),
                "budget": lead_info.get("budget"),
                "location": lead_info.get("location")
            })
            
            # Generate qualification prompt
            qualification_prompt = f"""
            Qualify this lead for our entertainment production services:
            
            Lead Information:
            - Company: {lead_info.get('company_name', 'Not specified')}
            - Project Type: {lead_info.get('project_type', 'Not specified')}
            - Budget Range: {lead_info.get('budget', 'Not specified')}
            - Timeline: {lead_info.get('timeline', 'Not specified')}
            - Location: {lead_info.get('location', 'Not specified')}
            - Contact: {lead_info.get('contact_name', 'Not specified')}
            
            Market Context:
            - Similar Projects: {len(project_intelligence.get('similar_projects', []))} found
            - Average Budget Range: {project_intelligence.get('cost_benchmarks', {}).get('average_budget', 'Unknown')}
            
            Provide:
            1. Qualification Score (1-10)
            2. Key Strengths
            3. Risk Factors
            4. Recommended Actions
            5. Timeline Assessment
            """
            
            # Get AI analysis
            response = await self.chat(
                message=qualification_prompt,
                user_context=user_context
            )
            
            return {
                "lead_info": lead_info,
                "qualification_analysis": response["content"],
                "market_context": project_intelligence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lead qualification failed: {e}")
            raise AIProcessingError(f"Lead qualification failed: {e}")

    async def market_analysis(
        self,
        segment: str,
        location: Optional[str] = None,
        timeframe: str = "current"
    ) -> Dict[str, Any]:
        """Perform market analysis for specific segment"""
        
        if not self.knowledge_service:
            return {"error": "Knowledge service not available"}
        
        try:
            # Get market insights
            insights = await self.knowledge_service.generate_insights(
                context={"segment": segment, "location": location},
                insight_type="project_trends"
            )
            
            # Generate analysis prompt
            analysis_prompt = f"""
            Analyze the {segment} market segment in {location or 'all locations'}:
            
            Recent Market Data:
            {insights}
            
            Provide:
            1. Market Size and Growth Trends
            2. Key Competitors and Market Share
            3. Pricing Benchmarks
            4. Opportunities and Threats
            5. Strategic Recommendations
            """
            
            response = await self.chat(
                message=analysis_prompt,
                user_context={"role": "sales_analyst"}
            )
            
            return {
                "segment": segment,
                "location": location,
                "timeframe": timeframe,
                "analysis": response["content"],
                "data_sources": insights,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": str(e)}

    async def get_pricing_recommendations(
        self,
        project_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate pricing recommendations based on market data"""
        
        if not self.knowledge_service:
            return {"error": "Knowledge service not available"}
        
        try:
            # Get project intelligence
            intelligence = await self.knowledge_service.project_intelligence(project_details)
            
            cost_benchmarks = intelligence.get("cost_benchmarks", {})
            similar_projects = intelligence.get("similar_projects", [])
            
            pricing_prompt = f"""
            Recommend pricing strategy for this project:
            
            Project Details:
            - Type: {project_details.get('type')}
            - Scope: {project_details.get('scope', 'Standard')}
            - Timeline: {project_details.get('timeline')}
            - Location: {project_details.get('location')}
            
            Market Benchmarks:
            - Average Similar Project Budget: ${cost_benchmarks.get('average_budget', 'Unknown')}
            - Budget Range: ${cost_benchmarks.get('min_budget', 'N/A')} - ${cost_benchmarks.get('max_budget', 'N/A')}
            - Sample Size: {cost_benchmarks.get('sample_size', 0)} projects
            
            Similar Projects Reference:
            {len(similar_projects)} comparable projects found
            
            Provide:
            1. Recommended Pricing Range
            2. Pricing Strategy Rationale
            3. Value Proposition Points
            4. Negotiation Guidelines
            5. Risk Considerations
            """
            
            response = await self.chat(
                message=pricing_prompt,
                user_context={"role": "sales_manager"}
            )
            
            return {
                "project_details": project_details,
                "pricing_analysis": response["content"],
                "market_benchmarks": cost_benchmarks,
                "comparable_projects": len(similar_projects),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Pricing recommendation failed: {e}")
            return {"error": str(e)}

    async def sales_forecast(
        self,
        pipeline_data: List[Dict[str, Any]],
        timeframe: str = "quarterly"
    ) -> Dict[str, Any]:
        """Generate sales forecast based on pipeline data"""
        
        try:
            # Analyze pipeline
            total_pipeline_value = sum(
                lead.get("budget", 0) * lead.get("probability", 0.5)
                for lead in pipeline_data
            )
            
            pipeline_summary = {
                "total_leads": len(pipeline_data),
                "total_value": total_pipeline_value,
                "avg_deal_size": total_pipeline_value / max(1, len(pipeline_data)),
                "stages": {}
            }
            
            # Stage analysis
            for lead in pipeline_data:
                stage = lead.get("stage", "unknown")
                if stage not in pipeline_summary["stages"]:
                    pipeline_summary["stages"][stage] = {"count": 0, "value": 0}
                pipeline_summary["stages"][stage]["count"] += 1
                pipeline_summary["stages"][stage]["value"] += lead.get("budget", 0)
            
            forecast_prompt = f"""
            Generate {timeframe} sales forecast based on current pipeline:
            
            Pipeline Summary:
            - Total Leads: {pipeline_summary['total_leads']}
            - Total Pipeline Value: ${pipeline_summary['total_value']:,.2f}
            - Average Deal Size: ${pipeline_summary['avg_deal_size']:,.2f}
            
            Pipeline by Stage:
            {pipeline_summary['stages']}
            
            Provide:
            1. Forecasted Revenue
            2. Confidence Intervals
            3. Key Assumptions
            4. Risk Factors
            5. Action Items to Improve Forecast
            """
            
            response = await self.chat(
                message=forecast_prompt,
                user_context={"role": "sales_director"}
            )
            
            return {
                "timeframe": timeframe,
                "pipeline_summary": pipeline_summary,
                "forecast_analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sales forecast failed: {e}")
            return {"error": str(e)}

    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and specializations"""
        
        return {
            "agent_type": "sales_intelligence",
            "specializations": [
                "Lead qualification and scoring",
                "Market analysis and competitive intelligence",
                "Pricing strategy optimization",
                "Sales forecasting and pipeline analysis",
                "Entertainment industry expertise"
            ],
            "key_methods": [
                "qualify_lead",
                "market_analysis", 
                "get_pricing_recommendations",
                "sales_forecast"
            ],
            "knowledge_domains": [
                "Entertainment industry trends",
                "Production budgets and costs",
                "Client relationship management",
                "Union compliance and rates",
                "Market segmentation"
            ],
            "requires_knowledge_graph": True,
            "timestamp": datetime.utcnow().isoformat()
        }