"""
Knowledge Graph Service

High-level service for interacting with entertainment industry
knowledge graph and orchestrating complex queries.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import AIConfig
from ..graph.connection import Neo4jClient
from ..graph.queries import EntertainmentQueries
from .vector_service import VectorSearchService, VectorType
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """
    High-level knowledge graph service that orchestrates
    complex queries combining graph traversal and vector search
    """
    
    def __init__(
        self,
        config: AIConfig,
        neo4j_client: Neo4jClient,
        vector_service: VectorSearchService
    ):
        self.config = config
        self.neo4j = neo4j_client
        self.vector_service = vector_service
        self.queries = EntertainmentQueries(neo4j_client)

    async def intelligent_talent_search(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligent talent search combining semantic and graph-based matching
        """
        
        # Extract search criteria
        skills = requirements.get("skills", [])
        description = requirements.get("description", "")
        location = requirements.get("location")
        budget_range = requirements.get("budget_range")
        project_type = requirements.get("project_type")
        
        results = {
            "semantic_matches": [],
            "skill_matches": [],
            "network_recommendations": [],
            "summary": {}
        }
        
        # 1. Semantic search using description
        if description:
            semantic_results = await self.vector_service.semantic_search(
                query=description,
                search_types=[VectorType.PERSON_BIO],
                limit=10
            )
            results["semantic_matches"] = semantic_results.get(VectorType.PERSON_BIO.value, [])
        
        # 2. Skill-based graph search
        if skills:
            skill_results = await self.queries.find_talent_by_skills(
                skills=skills,
                location=location,
                max_day_rate=budget_range[1] if budget_range else None,
                limit=10
            )
            results["skill_matches"] = skill_results
        
        # 3. Network recommendations based on similar projects
        if project_type:
            similar_projects = await self.queries.find_similar_projects(
                project_type=project_type,
                budget_range=budget_range,
                location=location,
                limit=5
            )
            
            # Extract talent from similar projects
            network_recommendations = []
            for project in similar_projects:
                for team_member in project.get("team_members", []):
                    network_recommendations.append({
                        "person": team_member["person"],
                        "role": team_member["role"],
                        "project_reference": project["name"],
                        "day_rate": team_member.get("day_rate")
                    })
            
            results["network_recommendations"] = network_recommendations[:10]
        
        # Generate summary
        results["summary"] = {
            "total_candidates": (
                len(results["semantic_matches"]) +
                len(results["skill_matches"]) +
                len(results["network_recommendations"])
            ),
            "search_strategy": {
                "semantic_search": bool(description),
                "skill_matching": bool(skills),
                "network_analysis": bool(project_type)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return results

    async def project_intelligence(
        self,
        project_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive project intelligence analysis
        """
        
        project_type = project_details.get("type")
        budget = project_details.get("budget")
        location = project_details.get("location")
        
        intelligence = {
            "market_analysis": {},
            "similar_projects": [],
            "cost_benchmarks": {},
            "talent_recommendations": [],
            "risk_assessment": {}
        }
        
        try:
            # Market analysis
            if project_type:
                market_trends = await self.queries.get_market_trends()
                intelligence["market_analysis"] = {
                    "trends": market_trends,
                    "project_type": project_type
                }
            
            # Similar projects
            if project_type and budget:
                budget_range = (budget * 0.8, budget * 1.2)  # ±20%
                similar_projects = await self.queries.find_similar_projects(
                    project_type=project_type,
                    budget_range=budget_range,
                    location=location,
                    limit=10
                )
                intelligence["similar_projects"] = similar_projects
            
            # Cost benchmarking
            if similar_projects:
                budgets = [p.get("budget", 0) for p in similar_projects if p.get("budget")]
                if budgets:
                    intelligence["cost_benchmarks"] = {
                        "average_budget": sum(budgets) / len(budgets),
                        "min_budget": min(budgets),
                        "max_budget": max(budgets),
                        "sample_size": len(budgets)
                    }
            
            # Talent recommendations
            talent_search = await self.intelligent_talent_search({
                "project_type": project_type,
                "description": f"{project_type} project in {location}",
                "budget_range": (0, budget) if budget else None
            })
            intelligence["talent_recommendations"] = talent_search
            
        except Exception as e:
            logger.error(f"Project intelligence analysis failed: {e}")
            intelligence["error"] = str(e)
        
        return intelligence

    async def company_analysis(
        self,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze company performance and network"""
        
        if not company_id and not company_name:
            raise AIProcessingError("Company ID or name required")
        
        # Find company
        if company_name and not company_id:
            search_results = await self.queries.search_entities(
                search_term=company_name,
                entity_types=["Company"],
                limit=1
            )
            if not search_results:
                raise AIProcessingError(f"Company not found: {company_name}")
            company_id = search_results[0]["n"]["id"]
        
        analysis = {
            "company_info": {},
            "project_history": [],
            "talent_network": [],
            "performance_metrics": {},
            "market_position": {}
        }
        
        # Implementation would continue with detailed company analysis
        # For brevity, returning basic structure
        
        return analysis

    async def generate_insights(
        self,
        context: Dict[str, Any],
        insight_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """Generate business insights based on context"""
        
        insights = []
        
        try:
            if insight_type == "talent_market":
                # Analyze talent market trends
                utilization = await self.queries.get_talent_utilization()
                
                insights.append({
                    "type": "talent_utilization",
                    "title": "Talent Market Analysis",
                    "data": utilization[:10],
                    "summary": f"Top talent showing high utilization rates",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif insight_type == "project_trends":
                # Analyze project trends
                trends = await self.queries.get_market_trends()
                
                insights.append({
                    "type": "market_trends",
                    "title": "Project Market Trends",
                    "data": trends,
                    "summary": "Recent market activity analysis",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            insights.append({
                "type": "error",
                "title": "Analysis Error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return insights

    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check Neo4j
        neo4j_health = await self.neo4j.health_check()
        health["components"]["neo4j"] = neo4j_health
        
        # Check vector service
        vector_stats = await self.vector_service.get_service_stats()
        health["components"]["vector_service"] = {
            "status": "healthy",
            "stats": vector_stats
        }
        
        # Overall status
        if neo4j_health["status"] != "healthy":
            health["status"] = "degraded"
        
        return health