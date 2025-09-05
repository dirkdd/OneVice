"""
Agent Tool Mixins for Shared Graph Query Tools

Provides composable tool mixins that can be added to different agent types,
allowing agents to access only the tools relevant to their domain while
sharing the underlying GraphQueryTools implementation.
"""

import logging
from typing import Dict, List, Any, Optional
from .graph_tools import GraphQueryTools

logger = logging.getLogger(__name__)


class BaseToolsMixin:
    """Base mixin for shared tool functionality"""
    
    def _init_graph_tools(
        self, 
        neo4j_client, 
        folk_client=None, 
        redis_client=None
    ) -> GraphQueryTools:
        """Initialize shared GraphQueryTools instance"""
        return GraphQueryTools(
            neo4j_client=neo4j_client,
            folk_client=folk_client,
            redis_client=redis_client
        )


class CRMToolsMixin(BaseToolsMixin):
    """
    CRM and Sales tools for Sales Intelligence Agent
    
    Focus: Lead management, deal tracking, relationship mapping
    """
    
    def init_crm_tools(self, neo4j_client, folk_client=None, redis_client=None):
        """Initialize CRM-specific tools"""
        if not neo4j_client:
            logger.error("Neo4j client is None in init_crm_tools")
            self.graph_tools = None
            return
        
        try:
            self.graph_tools = self._init_graph_tools(neo4j_client, folk_client, redis_client)
            logger.info(f"CRM tools initialized successfully for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize CRM tools for {self.__class__.__name__}: {e}")
            self.graph_tools = None
    
    # CRM-specific tool methods
    async def get_lead_profile(self, name: str) -> Dict[str, Any]:
        """Get comprehensive lead profile (wrapper for get_person_details)"""
        if not self.graph_tools:
            logger.error("Graph tools not initialized in get_lead_profile")
            return {"found": False, "error": "Graph tools not available"}
        
        try:
            result = await self.graph_tools.get_person_details(name)
            
            # Add CRM-specific context
            if result.get("found"):
                result["lead_context"] = {
                    "is_warm_lead": len(result.get("projects", [])) > 0,
                    "has_internal_contact": result.get("contact_owner") is not None,
                    "organization_size": "large" if result.get("organization") else "individual"
                }
            
            return result
        except Exception as e:
            logger.error(f"Error in get_lead_profile for '{name}': {e}")
            return {"found": False, "error": str(e)}
    
    async def find_decision_makers(self, organization_name: str) -> List[Dict[str, Any]]:
        """Find decision makers at target organization"""
        result = await self.graph_tools.find_people_at_organization(organization_name)
        
        # Filter for decision-maker roles
        if result.get("found"):
            decision_makers = []
            for person in result.get("people", []):
                title = (person.get("title") or "").lower()
                if any(role in title for role in ["director", "manager", "head", "vp", "ceo", "cmo", "producer"]):
                    person["decision_maker_score"] = "high"
                    decision_makers.append(person)
                elif any(role in title for role in ["coordinator", "assistant", "associate"]):
                    person["decision_maker_score"] = "medium"
                    decision_makers.append(person)
            
            result["decision_makers"] = decision_makers
            result["dm_count"] = len(decision_makers)
        
        return result
    
    async def get_deal_attribution(self, deal_name: str) -> Dict[str, Any]:
        """Get deal sourcing attribution"""
        return await self.graph_tools.get_deal_sourcer(deal_name)
    
    async def get_live_deal_status(self, deal_name: str) -> Dict[str, Any]:
        """Get real-time deal status with Folk API"""
        return await self.graph_tools.get_deal_details_with_live_status(deal_name)


class TalentToolsMixin(BaseToolsMixin):
    """
    Talent search and crew management tools for Talent Acquisition Agent
    
    Focus: Crew matching, availability, project history, skill assessment
    """
    
    def init_talent_tools(self, neo4j_client, folk_client=None, redis_client=None):
        """Initialize talent-specific tools"""
        self.graph_tools = self._init_graph_tools(neo4j_client, folk_client, redis_client)
        
        logger.info(f"Talent tools initialized for {self.__class__.__name__}")
    
    async def get_talent_profile(self, name: str) -> Dict[str, Any]:
        """Get comprehensive talent profile with project history"""
        result = await self.graph_tools.get_person_details(name)
        
        # Add talent-specific context
        if result.get("found"):
            projects = result.get("projects", [])
            
            # Analyze talent's experience
            roles = [p.get("role") for p in projects if p.get("role")]
            unique_roles = list(set(roles))
            
            result["talent_context"] = {
                "experience_level": "senior" if len(projects) > 5 else "mid" if len(projects) > 2 else "junior",
                "primary_roles": unique_roles[:3],  # Top 3 roles
                "project_count": len(projects),
                "recent_activity": any(p.get("startDate", "").startswith("202") for p in projects[-3:]),
                "versatility_score": len(unique_roles)
            }
        
        return result
    
    async def find_crew_by_style(self, concept_name: str, role: str = None) -> Dict[str, Any]:
        """Find crew experienced in specific creative styles"""
        # First, find projects with this concept
        projects_result = await self.graph_tools.find_projects_by_concept(concept_name, include_related=True)
        
        if not projects_result.get("found"):
            return {
                "crew": [],
                "concept": concept_name,
                "role": role,
                "found": False,
                "error": "No projects found with this creative concept"
            }
        
        # Extract unique crew members from these projects
        crew_members = {}
        for project in projects_result.get("projects", []):
            project_title = project.get("project", {}).get("title", "")
            if project_title:
                # Get project crew
                project_details = await self.graph_tools.get_project_details(project_title)
                if project_details.get("found"):
                    for crew_member in project_details.get("crew", []):
                        person_name = crew_member.get("person")
                        person_role = crew_member.get("role")
                        
                        # Filter by role if specified
                        if role and role.lower() not in person_role.lower():
                            continue
                        
                        if person_name not in crew_members:
                            crew_members[person_name] = {
                                "name": person_name,
                                "roles": [],
                                "projects": [],
                                "concept_experience": 0
                            }
                        
                        crew_members[person_name]["roles"].append(person_role)
                        crew_members[person_name]["projects"].append(project_title)
                        crew_members[person_name]["concept_experience"] += 1
        
        # Convert to list and sort by experience
        crew_list = list(crew_members.values())
        crew_list.sort(key=lambda x: x["concept_experience"], reverse=True)
        
        return {
            "crew": crew_list,
            "concept": concept_name,
            "role": role,
            "count": len(crew_list),
            "found": len(crew_list) > 0
        }
    
    async def find_experienced_crew(self, client_name: str, role: str) -> List[Dict[str, Any]]:
        """Find crew with specific client experience"""
        return await self.graph_tools.find_contributors_on_client_projects(role, client_name)
    
    async def get_project_crew_needs(self, project_title: str) -> Dict[str, Any]:
        """Analyze project crew composition and identify needs"""
        result = await self.graph_tools.get_project_details(project_title)
        
        if result.get("found"):
            crew = result.get("crew", [])
            roles = [member.get("role") for member in crew]
            role_counts = {}
            
            for role in roles:
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Standard crew composition check
            standard_roles = ["Director", "Producer", "Cinematographer", "Editor"]
            missing_roles = [role for role in standard_roles if role not in roles]
            
            result["crew_analysis"] = {
                "role_distribution": role_counts,
                "missing_standard_roles": missing_roles,
                "crew_size": len(crew),
                "completion_score": (len(standard_roles) - len(missing_roles)) / len(standard_roles)
            }
        
        return result


class AnalyticsToolsMixin(BaseToolsMixin):
    """
    Analytics and business intelligence tools for Leadership Analytics Agent
    
    Focus: Performance analysis, trend analysis, document insights, vendor analysis
    """
    
    def init_analytics_tools(self, neo4j_client, folk_client=None, redis_client=None):
        """Initialize analytics-specific tools"""
        self.graph_tools = self._init_graph_tools(neo4j_client, folk_client, redis_client)
        
        logger.info(f"Analytics tools initialized for {self.__class__.__name__}")
    
    async def analyze_team_performance(self, name: str) -> Dict[str, Any]:
        """Analyze individual team member performance"""
        result = await self.graph_tools.get_person_details(name)
        
        if result.get("found"):
            projects = result.get("projects", [])
            
            # Performance analytics
            result["performance_metrics"] = {
                "total_projects": len(projects),
                "roles_diversity": len(set(p.get("role") for p in projects if p.get("role"))),
                "recent_projects": len([p for p in projects if p.get("startDate", "").startswith("202")]),
                "activity_trend": "increasing" if len(projects[-2:]) > len(projects[-4:-2]) else "stable"
            }
        
        return result
    
    async def analyze_creative_trends(self, concept_name: str) -> Dict[str, Any]:
        """Analyze trends in creative concepts"""
        result = await self.graph_tools.find_projects_by_concept(concept_name, include_related=True)
        
        if result.get("found"):
            projects = result.get("projects", [])
            
            # Trend analysis
            years = []
            clients = []
            for project in projects:
                project_data = project.get("project", {})
                if project_data.get("year"):
                    years.append(int(project_data["year"]))
                if project.get("client"):
                    clients.append(project["client"])
            
            year_distribution = {}
            for year in years:
                year_distribution[year] = year_distribution.get(year, 0) + 1
            
            client_distribution = {}
            for client in clients:
                client_distribution[client] = client_distribution.get(client, 0) + 1
            
            result["trend_analysis"] = {
                "year_distribution": year_distribution,
                "client_distribution": client_distribution,
                "trend_direction": "growing" if years and max(years) >= 2023 else "stable",
                "top_clients": sorted(client_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            }
        
        return result
    
    async def analyze_vendor_performance(self, project_title: str = None) -> Dict[str, Any]:
        """Analyze vendor performance and costs"""
        if project_title:
            return await self.graph_tools.get_project_vendors(project_title)
        else:
            # Could implement broader vendor analysis across all projects
            return {
                "error": "Project title required for vendor analysis",
                "found": False
            }
    
    async def search_project_documents(self, search_query: str) -> Dict[str, Any]:
        """Search through project documentation"""
        return await self.graph_tools.search_documents_full_text(search_query)
    
    async def get_document_insights(self, document_id: str, field_path: str = None) -> Dict[str, Any]:
        """Extract insights from document profiles"""
        return await self.graph_tools.get_document_profile_details(document_id, field_path)
    
    async def get_project_documentation(self, project_title: str) -> Dict[str, Any]:
        """Get all documents for a project"""
        return await self.graph_tools.find_documents_for_project(project_title)


class SharedToolsMixin(CRMToolsMixin, TalentToolsMixin, AnalyticsToolsMixin):
    """
    Complete tool set for agents that need access to all tools
    
    This can be used for general-purpose agents or for development/testing
    """
    
    def init_all_tools(self, neo4j_client, folk_client=None, redis_client=None):
        """Initialize all available tools"""
        self.graph_tools = self._init_graph_tools(neo4j_client, folk_client, redis_client)
        
        logger.info(f"All graph tools initialized for {self.__class__.__name__}")