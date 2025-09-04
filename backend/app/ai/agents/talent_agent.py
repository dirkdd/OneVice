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
from ..tools.tool_mixins import TalentToolsMixin
from ...core.exceptions import AIProcessingError
from ...database.neo4j_client import Neo4jClient
from ...tools.folk_ingestion.folk_client import FolkClient

logger = logging.getLogger(__name__)

class TalentAcquisitionAgent(BaseAgent, TalentToolsMixin):
    """Talent acquisition agent specialized in entertainment industry hiring"""
    
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
            agent_type=AgentType.TALENT,
            config=config,
            llm_router=llm_router,
            redis_client=redis_client,
            model_config_manager=model_config_manager
        )
        
        self.knowledge_service = knowledge_service
        self.specialization = "talent_acquisition"
        
        # Initialize talent-specific tools
        if neo4j_client:
            self.init_talent_tools(neo4j_client, folk_client, redis_client)

    def _get_prompt_type(self) -> PromptType:
        return PromptType.TALENT_ACQUISITION

    async def _analyze_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze talent-related query for context"""
        
        query_lower = query.lower()
        
        # Detect query intent
        intent = "general"
        task_params = {}
        
        if any(word in query_lower for word in ["find", "search", "hire", "talent", "crew"]):
            intent = "talent_search"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["assess", "evaluate", "skill", "experience"]):
            intent = "skill_assessment"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["project", "cast", "crew", "team"]):
            intent = "project_matching"
            task_params = {"query": query, "context": user_context}
            
        elif any(word in query_lower for word in ["style", "concept", "creative", "genre"]):
            intent = "creative_matching"
            task_params = {"query": query, "context": user_context}
        
        return {
            "intent": intent,
            "task_type": intent,
            "task_params": task_params,
            "requires_knowledge_graph": intent in ["talent_search", "project_matching", "creative_matching"],
            "complexity": "moderate" if intent != "general" else "simple"
        }

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

    async def find_talent_by_style(
        self,
        concept: str,
        role: Optional[str] = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Find talent experienced in specific creative styles using graph tools"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized - provide neo4j_client during initialization")
        
        try:
            # Use graph tools to find crew by creative style
            crew_results = await self.find_crew_by_style(concept, role)
            
            if not crew_results.get("found"):
                return crew_results
            
            # Generate AI analysis of the talent matches
            analysis_prompt = f"""
            Analyze talent recommendations for {concept} creative concept:
            
            Role: {role or 'Any role'}
            Found Talent: {len(crew_results.get('crew', []))} candidates
            
            Crew Matches:
            {crew_results.get('crew', [])[:5]}  # Top 5 matches
            
            Provide:
            1. Top Talent Recommendations with Experience Levels
            2. Creative Style Match Assessment
            3. Portfolio Highlights
            4. Estimated Rates and Availability
            5. Recommended Outreach Strategy
            """
            
            response = await self.chat(
                message=analysis_prompt,
                user_context=user_context or {"role": "talent_director"}
            )
            
            return {
                "concept": concept,
                "role": role,
                "talent_matches": crew_results,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Talent style search failed: {e}")
            raise AIProcessingError(f"Talent style search failed: {e}")

    async def assess_talent_experience(
        self,
        name: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Assess talent experience and project history using graph tools"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Get comprehensive talent profile
            profile = await self.get_talent_profile(name)
            
            if not profile.get("found"):
                return {
                    "error": f"Talent '{name}' not found in database",
                    "found": False
                }
            
            # Generate AI assessment
            assessment_prompt = f"""
            Assess talent experience and suitability:
            
            Name: {profile.get('name')}
            Title: {profile.get('title', 'Not specified')}
            Organization: {profile.get('organization', 'Independent')}
            
            Experience Profile:
            - Total Projects: {profile.get('talent_context', {}).get('project_count', 0)}
            - Experience Level: {profile.get('talent_context', {}).get('experience_level', 'Unknown')}
            - Primary Roles: {profile.get('talent_context', {}).get('primary_roles', [])}
            - Recent Activity: {profile.get('talent_context', {}).get('recent_activity', False)}
            - Versatility Score: {profile.get('talent_context', {}).get('versatility_score', 0)}
            
            Recent Projects:
            {profile.get('projects', [])[:3]}  # Last 3 projects
            
            Provide:
            1. Experience Level Assessment
            2. Specialty Areas and Strengths
            3. Project Diversity Analysis
            4. Market Rate Estimation
            5. Hiring Recommendation
            """
            
            response = await self.chat(
                message=assessment_prompt,
                user_context=user_context or {"role": "talent_assessor"}
            )
            
            return {
                "talent": name,
                "profile": profile,
                "assessment": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Talent assessment failed: {e}")
            raise AIProcessingError(f"Talent assessment failed: {e}")

    async def find_client_experienced_talent(
        self,
        client_name: str,
        role: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Find talent with specific client experience"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Use graph tools to find experienced crew
            crew_results = await self.find_experienced_crew(client_name, role)
            
            # Generate analysis prompt
            analysis_prompt = f"""
            Analyze talent with {client_name} client experience:
            
            Role: {role}
            Search Results: {crew_results}
            
            Provide:
            1. Top Talent Recommendations
            2. Client Relationship Assessment
            3. Previous Project Performance
            4. Availability and Rate Expectations
            5. Onboarding Advantages
            """
            
            response = await self.chat(
                message=analysis_prompt,
                user_context=user_context or {"role": "client_relations_manager"}
            )
            
            return {
                "client": client_name,
                "role": role,
                "experienced_talent": crew_results,
                "analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Client talent search failed: {e}")
            return {"error": str(e)}

    async def analyze_project_crew_gaps(
        self,
        project_title: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze project crew composition and identify hiring needs"""
        
        if not hasattr(self, 'graph_tools'):
            raise AIProcessingError("Graph tools not initialized")
        
        try:
            # Get project crew analysis
            crew_analysis = await self.get_project_crew_needs(project_title)
            
            if not crew_analysis.get("found"):
                return {
                    "error": f"Project '{project_title}' not found in database",
                    "found": False
                }
            
            analysis = crew_analysis.get("crew_analysis", {})
            
            # Generate hiring strategy prompt
            strategy_prompt = f"""
            Analyze hiring needs for project: {project_title}
            
            Current Crew Analysis:
            - Total Crew Size: {analysis.get('crew_size', 0)}
            - Role Distribution: {analysis.get('role_distribution', {})}
            - Missing Standard Roles: {analysis.get('missing_standard_roles', [])}
            - Completion Score: {analysis.get('completion_score', 0):.2f}
            
            Current Crew:
            {crew_analysis.get('crew', [])[:10]}  # First 10 crew members
            
            Provide:
            1. Critical Hiring Priorities
            2. Role Gap Analysis
            3. Skill Set Requirements
            4. Budget Allocation Recommendations
            5. Hiring Timeline and Strategy
            """
            
            response = await self.chat(
                message=strategy_prompt,
                user_context=user_context or {"role": "production_manager"}
            )
            
            return {
                "project": project_title,
                "crew_analysis": crew_analysis,
                "hiring_strategy": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Project crew analysis failed: {e}")
            return {"error": str(e)}

    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and specializations"""
        
        return {
            "agent_type": "talent_acquisition",
            "specializations": [
                "Entertainment industry talent sourcing",
                "Creative style and concept matching",
                "Crew composition and gap analysis",
                "Union compliance and rate negotiation",
                "Client relationship leveraging"
            ],
            "key_methods": [
                "find_talent",
                "find_talent_by_style",
                "assess_talent_experience",
                "find_client_experienced_talent",
                "analyze_project_crew_gaps"
            ],
            "knowledge_domains": [
                "Entertainment industry roles and skills",
                "Creative concepts and artistic styles",
                "Production workflows and crew needs",
                "Union regulations and compliance",
                "Talent market rates and availability"
            ],
            "requires_knowledge_graph": True,
            "graph_tools_available": hasattr(self, 'graph_tools'),
            "timestamp": datetime.utcnow().isoformat()
        }