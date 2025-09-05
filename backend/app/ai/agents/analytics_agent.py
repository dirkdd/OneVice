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
from ..tools.tool_mixins import AnalyticsToolsMixin
from ...core.exceptions import AIProcessingError
from database.neo4j_client import Neo4jClient
from tools.folk_ingestion.folk_client import FolkClient

logger = logging.getLogger(__name__)

class LeadershipAnalyticsAgent(BaseAgent, AnalyticsToolsMixin):
    """Leadership analytics agent for business intelligence"""
    
    def __init__(
        self,
        config: AIConfig,
        llm_router: LLMRouter,
        knowledge_service: Optional[KnowledgeGraphService] = None,
        redis_client=None,
        model_config_manager=None,
        neo4j_client: Optional[Neo4jClient] = None,
        folk_client: Optional[FolkClient] = None
    ):
        super().__init__(
            agent_type=AgentType.ANALYTICS,
            config=config,
            llm_router=llm_router,
            redis_client=redis_client,
            model_config_manager=model_config_manager
        )
        
        self.knowledge_service = knowledge_service
        self.specialization = "leadership_analytics"
        
        # Initialize analytics-specific tools
        if neo4j_client:
            self.init_analytics_tools(neo4j_client, folk_client, redis_client)

    def _get_prompt_type(self) -> PromptType:
        return PromptType.LEADERSHIP_ANALYTICS

    def _get_preferred_provider(self) -> Optional[str]:
        return "openai"  # Use OpenAI for complex analytics

    async def _analyze_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze analytics-related query for context"""
        
        query_lower = query.lower()
        
        # Detect query intent
        intent = "general"
        task_params = {}
        
        if any(word in query_lower for word in ["performance", "metrics", "kpi", "analyze"]):
            intent = "performance_analysis"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["forecast", "predict", "trend", "future"]):
            intent = "forecasting"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["document", "search", "find", "report"]):
            intent = "document_analysis"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["vendor", "cost", "budget", "expense"]):
            intent = "vendor_analysis" 
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["team", "talent", "crew", "staff"]):
            intent = "team_analysis"
            task_params = {"query": query, "context": user_context}
        
        return {
            "intent": intent,
            "task_type": intent,
            "task_params": task_params,
            "requires_knowledge_graph": intent in ["performance_analysis", "document_analysis", "vendor_analysis", "team_analysis"],
            "complexity": "high" if intent in ["forecasting", "vendor_analysis"] else "moderate" if intent != "general" else "simple"
        }

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

    async def analyze_creative_trends(
        self,
        concept: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze trends in creative concepts using graph tools"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized - provide neo4j_client during initialization")
        
        try:
            # Use analytics tools to analyze creative trends
            trend_analysis = await self.analyze_creative_trends(concept)
            
            if not trend_analysis.get("found"):
                return {
                    "error": f"No projects found with concept '{concept}'",
                    "found": False
                }
            
            # Generate comprehensive trend report
            trend_prompt = f"""
            Analyze creative trends for concept: {concept}
            
            Trend Analysis Data:
            - Total Projects: {len(trend_analysis.get('projects', []))}
            - Year Distribution: {trend_analysis.get('trend_analysis', {}).get('year_distribution', {})}
            - Client Distribution: {trend_analysis.get('trend_analysis', {}).get('client_distribution', {})}
            - Trend Direction: {trend_analysis.get('trend_analysis', {}).get('trend_direction', 'Unknown')}
            - Top Clients: {trend_analysis.get('trend_analysis', {}).get('top_clients', [])}
            
            Recent Projects Sample:
            {trend_analysis.get('projects', [])[:5]}
            
            Provide:
            1. Market Trend Analysis
            2. Client Demand Patterns
            3. Creative Evolution Assessment
            4. Future Opportunity Predictions
            5. Strategic Recommendations
            """
            
            response = await self.chat(
                message=trend_prompt,
                user_context=user_context or {"role": "creative_director"}
            )
            
            return {
                "concept": concept,
                "trend_data": trend_analysis,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Creative trend analysis failed: {e}")
            raise AIProcessingError(f"Creative trend analysis failed: {e}")

    async def analyze_team_member_performance(
        self,
        name: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze individual team member performance using graph tools"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Get team performance analysis
            performance_data = await self.analyze_team_performance(name)
            
            if not performance_data.get("found"):
                return {
                    "error": f"Team member '{name}' not found in database",
                    "found": False
                }
            
            metrics = performance_data.get("performance_metrics", {})
            
            # Generate performance report
            performance_prompt = f"""
            Analyze team member performance:
            
            Team Member: {performance_data.get('name')}
            Title: {performance_data.get('title', 'Not specified')}
            Organization: {performance_data.get('organization', 'Independent')}
            
            Performance Metrics:
            - Total Projects: {metrics.get('total_projects', 0)}
            - Role Diversity: {metrics.get('roles_diversity', 0)} different roles
            - Recent Projects: {metrics.get('recent_projects', 0)} in recent years
            - Activity Trend: {metrics.get('activity_trend', 'stable')}
            
            Project History:
            {performance_data.get('projects', [])[:5]}
            
            Provide:
            1. Performance Summary and Key Strengths
            2. Career Growth Analysis
            3. Productivity Assessment
            4. Market Value Estimation
            5. Development Recommendations
            """
            
            response = await self.chat(
                message=performance_prompt,
                user_context=user_context or {"role": "performance_analyst"}
            )
            
            return {
                "team_member": name,
                "performance_data": performance_data,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Team performance analysis failed: {e}")
            return {"error": str(e)}

    async def analyze_project_documentation(
        self,
        project_title: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze project documentation and extract insights"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Get project documentation
            docs_result = await self.get_project_documentation(project_title)
            
            if not docs_result.get("found"):
                return {
                    "error": f"No documents found for project '{project_title}'",
                    "found": False
                }
            
            # Generate documentation analysis
            doc_analysis_prompt = f"""
            Analyze project documentation for insights:
            
            Project: {project_title}
            Document Count: {len(docs_result.get('documents', []))}
            
            Document Summary:
            {docs_result.get('documents', [])[:10]}
            
            Provide:
            1. Document Completeness Assessment
            2. Key Project Insights from Documents
            3. Communication Patterns Analysis
            4. Risk Factors Identified
            5. Project Success Indicators
            """
            
            response = await self.chat(
                message=doc_analysis_prompt,
                user_context=user_context or {"role": "project_analyst"}
            )
            
            return {
                "project": project_title,
                "documentation": docs_result,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Documentation analysis failed: {e}")
            return {"error": str(e)}

    async def search_and_analyze_documents(
        self,
        search_query: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Search documents and provide analytical insights"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Search project documents
            search_results = await self.search_project_documents(search_query)
            
            if not search_results.get("found"):
                return {
                    "error": f"No documents found matching '{search_query}'",
                    "found": False
                }
            
            # Generate search analysis
            search_analysis_prompt = f"""
            Analyze document search results for business insights:
            
            Search Query: {search_query}
            Results Count: {len(search_results.get('documents', []))}
            
            Matching Documents:
            {search_results.get('documents', [])[:15]}
            
            Provide:
            1. Document Relevance Assessment
            2. Key Themes and Patterns
            3. Business Intelligence Insights  
            4. Strategic Implications
            5. Action Items and Recommendations
            """
            
            response = await self.chat(
                message=search_analysis_prompt,
                user_context=user_context or {"role": "business_analyst"}
            )
            
            return {
                "search_query": search_query,
                "search_results": search_results,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document search analysis failed: {e}")
            return {"error": str(e)}

    async def analyze_vendor_performance(
        self,
        project_title: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze vendor performance and costs for a project"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Get vendor performance data
            vendor_data = await self.analyze_vendor_performance(project_title)
            
            if not vendor_data.get("found"):
                return {
                    "error": f"No vendor data found for project '{project_title}'",
                    "found": False
                }
            
            # Generate vendor analysis
            vendor_analysis_prompt = f"""
            Analyze vendor performance and cost efficiency:
            
            Project: {project_title}
            Vendor Data: {vendor_data}
            
            Provide:
            1. Vendor Performance Assessment
            2. Cost Analysis and Benchmarking
            3. Quality and Delivery Evaluation
            4. Risk Assessment
            5. Future Vendor Strategy Recommendations
            """
            
            response = await self.chat(
                message=vendor_analysis_prompt,
                user_context=user_context or {"role": "procurement_analyst"}
            )
            
            return {
                "project": project_title,
                "vendor_data": vendor_data,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Vendor analysis failed: {e}")
            return {"error": str(e)}

    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and specializations"""
        
        return {
            "agent_type": "leadership_analytics",
            "specializations": [
                "Business intelligence and performance analytics",
                "Creative trend analysis and market insights",
                "Team performance and productivity assessment",
                "Document intelligence and knowledge extraction",
                "Vendor analysis and procurement optimization"
            ],
            "key_methods": [
                "analyze_performance",
                "analyze_creative_trends",
                "analyze_team_member_performance", 
                "analyze_project_documentation",
                "search_and_analyze_documents",
                "analyze_vendor_performance"
            ],
            "knowledge_domains": [
                "Entertainment industry market trends",
                "Performance metrics and KPI analysis",
                "Document analysis and knowledge extraction",
                "Vendor management and cost optimization",
                "Team productivity and talent assessment"
            ],
            "requires_knowledge_graph": True,
            "graph_tools_available": hasattr(self, 'graph_tools'),
            "preferred_llm_provider": "openai",
            "timestamp": datetime.utcnow().isoformat()
        }