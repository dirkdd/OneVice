"""
Neo4j Graph Query Tools for LangGraph Agents

Provides a comprehensive set of graph query tools that can be shared across
multiple agent types for accessing Folk CRM data, project information, and
creative intelligence from the OneVice knowledge graph.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from ...database.neo4j_client import Neo4jClient
from ...tools.folk_ingestion.folk_client import FolkClient
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


class GraphQueryTools:
    """
    Shared graph query tools for LangGraph agents
    
    Provides 12 comprehensive tools across 3 categories:
    - People/CRM tools (Folk integration)
    - Project/Creative tools  
    - Document/Content tools
    
    Features:
    - Redis caching for performance
    - Folk API hybrid queries for live data
    - Graceful error handling and fallback
    - Structured responses for agent consumption
    """
    
    def __init__(
        self, 
        neo4j_client: Neo4jClient,
        folk_client: Optional[FolkClient] = None,
        redis_client = None
    ):
        self.neo4j_client = neo4j_client
        self.folk_client = folk_client
        self.redis_client = redis_client
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "person": 300,      # 5 minutes for person data
            "concept": 600,     # 10 minutes for creative concepts
            "project": 300,     # 5 minutes for project data
            "document": 1800,   # 30 minutes for document data
            "organization": 600 # 10 minutes for org data
        }
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from Redis cache if available"""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {cache_key}: {e}")
        
        return None
    
    async def _set_cached_result(self, cache_key: str, result: Dict[str, Any], ttl: int):
        """Store result in Redis cache"""
        if not self.redis_client or not result:
            return
        
        try:
            await self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(result, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache storage failed for {cache_key}: {e}")
    
    # ==========================================================================
    # Category 1: People, Companies & Relationships (CRM & HR Focus)
    # ==========================================================================
    
    async def get_person_details(self, name: str) -> Dict[str, Any]:
        """
        Get comprehensive profile for a person including projects, organizations, and groups
        
        Used by: Sales Agent (lead profiles), Talent Agent (crew profiles), Analytics Agent (team analysis)
        """
        cache_key = f"person_details:{name.lower().replace(' ', '_')}"
        
        # Try cache first
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (p:Person)
        WHERE p.name CONTAINS $name OR p.fullName CONTAINS $name
        OPTIONAL MATCH (p)-[r:CONTRIBUTED_TO]->(proj:Project)
        OPTIONAL MATCH (p)-[:WORKS_FOR]->(org:Organization)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(g:Group)
        OPTIONAL MATCH (internal:Person {isInternal: true})-[:OWNS_CONTACT]->(p)
        RETURN p {
            .name, .fullName, .email, .folkId, .isInternal,
            .bio, .role, .phone, .location, .linkedinUrl, .website, .tags
        } AS person,
        org.name AS organization,
        collect(DISTINCT {
            project: proj.name, 
            role: r.role, 
            startDate: r.startDate,
            projectId: proj.id
        }) AS projects,
        collect(DISTINCT g.name) AS groups,
        internal.name AS contact_owner
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"name": name})
            
            if result and result.records:
                # Take the first matching person
                person_data = result.records[0]
                
                # Clean up None values and empty collections
                response = {
                    "person": person_data.get("person", {}),
                    "organization": person_data.get("organization"),
                    "projects": [p for p in person_data.get("projects", []) if p.get("project")],
                    "groups": [g for g in person_data.get("groups", []) if g],
                    "contact_owner": person_data.get("contact_owner"),
                    "query": name,
                    "found": True
                }
                
                # Cache successful result
                await self._set_cached_result(cache_key, response, self.cache_ttl["person"])
                return response
            else:
                return {
                    "person": None,
                    "organization": None,
                    "projects": [],
                    "groups": [],
                    "contact_owner": None,
                    "query": name,
                    "found": False,
                    "error": "Person not found in knowledge graph"
                }
        
        except Exception as e:
            logger.error(f"Error in get_person_details for '{name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "query": name,
                "found": False
            }
    
    async def find_people_at_organization(self, organization_name: str) -> List[Dict[str, Any]]:
        """
        Find all people who work for a specific organization
        
        Used by: Sales Agent (find decision makers), Talent Agent (find available crew)
        """
        cache_key = f"org_people:{organization_name.lower().replace(' ', '_')}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
        WHERE o.name CONTAINS $org_name
        RETURN p {
            .name, .role, .email, .folkId, .isInternal
        } AS person,
        o.name AS organization
        ORDER BY p.name
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"org_name": organization_name})
            
            if result and result.records:
                people = []
                for record in result.records:
                    person_data = record.get("person", {})
                    people.append({
                        "name": person_data.get("name"),
                        "title": person_data.get("role"),  # Map role to title for API consistency
                        "email": person_data.get("email"),
                        "folkId": person_data.get("folkId"),
                        "isInternal": person_data.get("isInternal", False),
                        "organization": record.get("organization")
                    })
                
                response = {
                    "people": people,
                    "organization": organization_name,
                    "count": len(people),
                    "found": len(people) > 0
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["organization"])
                return response
            else:
                return {
                    "people": [],
                    "organization": organization_name,
                    "count": 0,
                    "found": False,
                    "error": "No people found at this organization"
                }
        
        except Exception as e:
            logger.error(f"Error in find_people_at_organization for '{organization_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "organization": organization_name,
                "found": False
            }
    
    async def get_deal_sourcer(self, deal_name: str) -> Dict[str, Any]:
        """
        Find internal team member who sourced a specific deal
        
        Used by: Sales Agent (deal attribution), Analytics Agent (sourcing analysis)
        """
        query = """
        MATCH (p:Person {isInternal: true})-[:SOURCED]->(d:Deal)
        WHERE d.name CONTAINS $deal_name
        
        // Get sourcing history for context
        OPTIONAL MATCH (p)-[:SOURCED]->(other_deals:Deal)
        WHERE other_deals <> d
        
        // Get their department/role
        OPTIONAL MATCH (p)-[:WORKS_FOR]->(dept:Department)
        
        RETURN p {
            .name, .fullName, .email, .folkUserId, .role
        } AS sourcer,
        d {
            .name, .status, .value, .currency, .folkId
        } AS deal,
        dept.name AS department,
        count(other_deals) AS total_deals_sourced,
        collect(other_deals.name)[..3] AS recent_other_deals
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"deal_name": deal_name})
            
            if result and result.records:
                record = result.records[0]
                return {
                    "sourcer": record.get("sourcer", {}),
                    "deal": record.get("deal", {}),
                    "department": record.get("department"),
                    "sourcing_stats": {
                        "total_deals": record.get("total_deals_sourced", 0),
                        "recent_deals": record.get("recent_other_deals", [])
                    },
                    "found": True
                }
            else:
                return {
                    "sourcer": None,
                    "deal": None,
                    "found": False,
                    "error": "Deal not found or not sourced by internal team"
                }
        
        except Exception as e:
            logger.error(f"Error in get_deal_sourcer for '{deal_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "deal_name": deal_name,
                "found": False
            }
    
    async def get_deal_details_with_live_status(self, deal_name: str) -> Dict[str, Any]:
        """
        Get deal details with hybrid graph + Folk API for live status
        
        Used by: Sales Agent (deal management), Analytics Agent (pipeline analysis)
        """
        # Step 1: Get rich context from graph
        query = """
        MATCH (sourcer:Person)-[:SOURCED]->(d:Deal)
        WHERE d.name CONTAINS $deal_name
        OPTIONAL MATCH (d)-[:WITH_CONTACT]->(contact:Person)
        OPTIONAL MATCH (d)-[:FOR_ORGANIZATION]->(org:Organization)
        RETURN d {
            .name, .status, .value, .currency, .folkId,
            .probability, .expectedCloseDate, .description
        } AS deal,
        sourcer.name AS sourced_by,
        collect(contact.name) AS contacts,
        org.name AS organization
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"deal_name": deal_name})
            
            if result and result.records:
                graph_data = result.records[0]
                deal_data = graph_data.get("deal", {})
                
                response = {
                    "deal": deal_data,
                    "sourced_by": graph_data.get("sourced_by"),
                    "contacts": graph_data.get("contacts", []),
                    "organization": graph_data.get("organization"),
                    "data_freshness": "graph_only",
                    "found": True
                }
                
                # Step 2: Enrich with live Folk API data if available
                if deal_data.get("folkId") and self.folk_client:
                    try:
                        live_status = await self.folk_client.get_deal_status(deal_data["folkId"])
                        response["live_status"] = live_status
                        response["data_freshness"] = "live_api_enhanced"
                    except Exception as api_error:
                        logger.warning(f"Folk API enrichment failed: {api_error}")
                        response["live_status"] = "api_unavailable"
                
                return response
            else:
                return {
                    "deal": None,
                    "found": False,
                    "error": "Deal not found in knowledge graph"
                }
        
        except Exception as e:
            logger.error(f"Error in get_deal_details_with_live_status for '{deal_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "deal_name": deal_name,
                "found": False
            }
    
    # ==========================================================================
    # Category 2: Projects & Creative DNA (Production & Creative Focus) 
    # ==========================================================================
    
    async def get_project_details(self, project_title: str) -> Dict[str, Any]:
        """
        Get comprehensive project information including crew, concepts, and client
        
        Used by: Talent Agent (crew requirements), Analytics Agent (project analysis)
        """
        cache_key = f"project_details:{project_title.lower().replace(' ', '_')}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (proj:Project)
        WHERE proj.name CONTAINS $title
        OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
        OPTIONAL MATCH (proj)-[:FEATURES_CONCEPT]->(c:CreativeConcept)
        OPTIONAL MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj)
        OPTIONAL MATCH (proj)-[:MANAGED_BY]->(dept:Department)
        RETURN proj {
            .name, .id, .logline, .status, .year, .description
        } AS project,
        client.name AS client,
        dept.name AS department,
        collect(DISTINCT c.name) AS concepts,
        collect(DISTINCT {
            person: p.name, 
            role: r.role,
            startDate: r.startDate
        }) AS crew
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"title": project_title})
            
            if result and result.records:
                record = result.records[0]
                project_data = record.get("project", {})
                
                # Clean up crew data
                crew = [c for c in record.get("crew", []) if c.get("person")]
                
                response = {
                    "project": project_data,
                    "client": record.get("client"),
                    "department": record.get("department"),
                    "concepts": [c for c in record.get("concepts", []) if c],
                    "crew": crew,
                    "crew_count": len(crew),
                    "found": True
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["project"])
                return response
            else:
                return {
                    "project": None,
                    "found": False,
                    "error": "Project not found in knowledge graph"
                }
        
        except Exception as e:
            logger.error(f"Error in get_project_details for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "project_title": project_title,
                "found": False
            }
    
    async def find_projects_by_concept(
        self, 
        concept_name: str, 
        include_related: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Find projects associated with creative concepts
        
        Used by: Talent Agent (match talent to style), Analytics Agent (trend analysis)
        """
        cache_key = f"projects_by_concept:{concept_name.lower()}:{include_related}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # Base query for direct concept matches
        query = """
        MATCH (proj:Project)-[:FEATURES_CONCEPT]->(c:CreativeConcept)
        WHERE c.name CONTAINS $concept_name
        OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
        OPTIONAL MATCH (director:Person)-[r:CONTRIBUTED_TO {role: 'Director'}]->(proj)
        RETURN proj {
            .name, .id, .logline, .status, .year
        } AS project,
        collect(c.name) AS concepts,
        client.name AS client,
        director.name AS director,
        'direct_match' AS match_type
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"concept_name": concept_name})
            
            projects = []
            if result and result.records:
                for record in result.records:
                    projects.append({
                        "project": record.get("project", {}),
                        "concepts": record.get("concepts", []),
                        "client": record.get("client"),
                        "director": record.get("director"),
                        "match_type": record.get("match_type")
                    })
            
            # If include_related and we found results, also find related concepts
            if include_related and projects:
                related_query = """
                MATCH (c1:CreativeConcept)-[:RELATED_TO*1..2]->(c2:CreativeConcept)
                WHERE c1.name CONTAINS $concept_name
                MATCH (proj:Project)-[:FEATURES_CONCEPT]->(c2)
                WHERE NOT proj.name IN $existing_titles
                OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
                RETURN proj {
                    .name, .id, .logline, .status, .year
                } AS project,
                collect(c2.name) AS concepts,
                client.name AS client,
                'related_concept' AS match_type
                """
                
                existing_titles = [p["project"]["name"] for p in projects if p["project"]]
                related_result = await self.neo4j_client.execute_query(
                    related_query,
                    {"concept_name": concept_name, "existing_titles": existing_titles}
                )
                
                if related_result and related_result.records:
                    for record in related_result.records:
                        projects.append({
                            "project": record.get("project", {}),
                            "concepts": record.get("concepts", []),
                            "client": record.get("client"),
                            "director": None,
                            "match_type": record.get("match_type")
                        })
            
            response = {
                "projects": projects,
                "concept": concept_name,
                "count": len(projects),
                "include_related": include_related,
                "found": len(projects) > 0
            }
            
            # Cache for longer since concept relationships change infrequently
            await self._set_cached_result(cache_key, response, self.cache_ttl["concept"])
            return response
        
        except Exception as e:
            logger.error(f"Error in find_projects_by_concept for '{concept_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "concept": concept_name,
                "found": False
            }
    
    async def find_contributors_on_client_projects(
        self, 
        role: str, 
        client_name: str
    ) -> List[Dict[str, Any]]:
        """
        Find people who performed specific roles on projects for a client
        
        Used by: Talent Agent (find experienced crew), Sales Agent (team capabilities)
        """
        query = """
        MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj:Project)-[:FOR_CLIENT]->(o:Organization)
        WHERE r.role CONTAINS $role AND o.name CONTAINS $client_name
        RETURN DISTINCT p {
            .name, .role, .email, .bio
        } AS person,
        collect(DISTINCT proj.name) AS projects,
        count(DISTINCT proj) AS project_count
        ORDER BY project_count DESC
        """
        
        try:
            result = await self.neo4j_client.execute_query(
                query, 
                {"role": role, "client_name": client_name}
            )
            
            contributors = []
            if result and result.records:
                for record in result.records:
                    contributors.append({
                        "person": record.get("person", {}),
                        "projects": record.get("projects", []),
                        "project_count": record.get("project_count", 0)
                    })
            
            return {
                "contributors": contributors,
                "role": role,
                "client": client_name,
                "count": len(contributors),
                "found": len(contributors) > 0
            }
        
        except Exception as e:
            logger.error(f"Error in find_contributors_on_client_projects: {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "role": role,
                "client": client_name,
                "found": False
            }
    
    async def get_project_vendors(self, project_title: str) -> List[Dict[str, Any]]:
        """
        Get external vendors that provided services for a project
        
        Used by: Analytics Agent (vendor analysis), Talent Agent (vendor relationships)
        """
        query = """
        MATCH (o:Organization)-[r:PROVIDED_SERVICE]->(p:Project)
        WHERE p.name CONTAINS $title
        RETURN o {
            .name, .organizationId, .folkId
        } AS vendor,
        r.service AS service,
        r.cost AS cost,
        r.startDate AS start_date
        ORDER BY o.name
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"title": project_title})
            
            vendors = []
            if result and result.records:
                for record in result.records:
                    vendors.append({
                        "vendor": record.get("vendor", {}),
                        "service": record.get("service"),
                        "cost": record.get("cost"),
                        "start_date": record.get("start_date")
                    })
            
            return {
                "vendors": vendors,
                "project": project_title,
                "count": len(vendors),
                "found": len(vendors) > 0
            }
        
        except Exception as e:
            logger.error(f"Error in get_project_vendors for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "project": project_title,
                "found": False
            }
    
    # ==========================================================================
    # Category 3: Document & Content Analysis
    # ==========================================================================
    
    async def find_documents_for_project(self, project_title: str) -> List[Dict[str, Any]]:
        """
        Find documents related to a specific project
        
        Used by: Analytics Agent (project documentation)
        """
        query = """
        MATCH (d:Document)-[]->(p:Project)
        WHERE p.name CONTAINS $title
        RETURN d {
            .title, .type, .id, .created_at
        } AS document
        ORDER BY d.created_at DESC
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"title": project_title})
            
            documents = []
            if result and result.records:
                for record in result.records:
                    documents.append(record.get("document", {}))
            
            return {
                "documents": documents,
                "project": project_title,
                "count": len(documents),
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error in find_documents_for_project for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "project": project_title,
                "found": False
            }
    
    async def get_document_profile_details(
        self, 
        document_id: str, 
        json_path: str = None
    ) -> Dict[str, Any]:
        """
        Get structured information from document JSON profile
        
        Used by: Analytics Agent (extract specific document data)
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        RETURN d.profile AS profile, d.title AS title, d.type AS type
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"doc_id": document_id})
            
            if result and result.records:
                record = result.records[0]
                profile = record.get("profile")
                
                if profile and isinstance(profile, str):
                    try:
                        profile_data = json.loads(profile)
                        
                        # If json_path specified, extract specific field
                        if json_path:
                            # Simple JSON path extraction (could be enhanced with JSONPath library)
                            keys = json_path.replace('$.', '').split('.')
                            value = profile_data
                            for key in keys:
                                value = value.get(key, None) if isinstance(value, dict) else None
                                if value is None:
                                    break
                            
                            return {
                                "document_id": document_id,
                                "title": record.get("title"),
                                "type": record.get("type"),
                                "json_path": json_path,
                                "value": value,
                                "found": value is not None
                            }
                        else:
                            return {
                                "document_id": document_id,
                                "title": record.get("title"),
                                "type": record.get("type"),
                                "profile": profile_data,
                                "found": True
                            }
                    
                    except json.JSONDecodeError:
                        return {
                            "document_id": document_id,
                            "error": "Document profile is not valid JSON",
                            "found": False
                        }
                else:
                    return {
                        "document_id": document_id,
                        "error": "Document has no profile data",
                        "found": False
                    }
            else:
                return {
                    "document_id": document_id,
                    "error": "Document not found",
                    "found": False
                }
        
        except Exception as e:
            logger.error(f"Error in get_document_profile_details for '{document_id}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "document_id": document_id,
                "found": False
            }
    
    async def search_documents_full_text(
        self, 
        search_query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across all documents
        
        Used by: Analytics Agent (document search and analysis)
        """
        # Use Neo4j full-text search with ranking
        query = """
        CALL db.index.fulltext.queryNodes('documentTextIndex', $search_query)
        YIELD node, score
        MATCH (node:Document)
        RETURN node.title AS title, 
               node.type AS type,
               node.id AS id,
               score,
               node.fullTextContent AS content
        ORDER BY score DESC
        LIMIT $limit
        """
        
        try:
            result = await self.neo4j_client.execute_query(
                query, 
                {"search_query": search_query, "limit": limit}
            )
            
            documents = []
            if result and result.records:
                for record in result.records:
                    content = record.get("content", "")
                    snippet = self._extract_snippet(content, search_query)
                    
                    documents.append({
                        "title": record.get("title"),
                        "type": record.get("type"),
                        "id": record.get("id"),
                        "score": record.get("score", 0),
                        "snippet": snippet
                    })
            
            return {
                "documents": documents,
                "query": search_query,
                "count": len(documents),
                "limit": limit,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error in search_documents_full_text for '{search_query}': {e}")
            return {
                "error": f"Full-text search failed: {str(e)}",
                "query": search_query,
                "found": False
            }
    
    def _extract_snippet(self, content: str, search_query: str, snippet_length: int = 200) -> str:
        """Extract relevant text snippet around search terms"""
        if not content or not search_query:
            return ""
        
        # Simple snippet extraction - find first occurrence of search term
        content_lower = content.lower()
        query_lower = search_query.lower()
        
        # Find the first search term
        search_terms = query_lower.split()
        best_pos = -1
        for term in search_terms:
            pos = content_lower.find(term)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
        
        if best_pos == -1:
            # No terms found, return beginning
            return content[:snippet_length] + "..." if len(content) > snippet_length else content
        
        # Extract snippet around the found term
        start = max(0, best_pos - snippet_length // 2)
        end = min(len(content), start + snippet_length)
        
        snippet = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet

    # ==========================================================================
    # Additional Methods from Original Specification
    # ==========================================================================
    
    async def find_collaborators(self, person_name: str, project_type: str = None) -> Dict[str, Any]:
        """
        Find people who have collaborated with a specific person on projects
        
        Used by: Sales Agent (network analysis), Talent Agent (crew recommendations)
        """
        cache_key = f"collaborators:{person_name.lower().replace(' ', '_')}:{project_type or 'all'}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (p1:Person)-[:CONTRIBUTED_TO]->(proj:Project)<-[:CONTRIBUTED_TO]-(p2:Person)
        WHERE p1.name CONTAINS $person_name AND p1 <> p2
        """
        
        # Add project type filter if specified
        if project_type:
            query += " AND proj.type CONTAINS $project_type"
        
        query += """
        WITH p2, collect(DISTINCT proj.name) AS shared_projects, count(DISTINCT proj) AS collaboration_count
        ORDER BY collaboration_count DESC
        LIMIT 20
        RETURN p2 {
            .name, .role, .email, .folkId
        } AS collaborator,
        shared_projects,
        collaboration_count
        """
        
        try:
            params = {"person_name": person_name}
            if project_type:
                params["project_type"] = project_type
                
            result = await self.neo4j_client.execute_query(query, params)
            
            collaborators = []
            if result and result.records:
                for record in result.records:
                    collaborators.append({
                        "collaborator": record.get("collaborator", {}),
                        "shared_projects": record.get("shared_projects", []),
                        "collaboration_count": record.get("collaboration_count", 0)
                    })
            
            response = {
                "collaborators": collaborators,
                "person": person_name,
                "project_type": project_type,
                "count": len(collaborators),
                "found": len(collaborators) > 0
            }
            
            await self._set_cached_result(cache_key, response, self.cache_ttl["person"])
            return response
            
        except Exception as e:
            logger.error(f"Error in find_collaborators for '{person_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "person": person_name,
                "found": False
            }
    
    async def get_organization_profile(self, org_name: str) -> Dict[str, Any]:
        """
        Get comprehensive organization profile with projects and people
        
        Used by: Sales Agent (client research), Analytics Agent (market analysis)
        """
        cache_key = f"org_profile:{org_name.lower().replace(' ', '_')}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (o:Organization)
        WHERE o.name CONTAINS $org_name
        OPTIONAL MATCH (o)<-[:WORKS_FOR]-(p:Person)
        OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(proj:Project)
        OPTIONAL MATCH (o)<-[:FOR_ORGANIZATION]-(d:Deal)
        RETURN o {
            .name, .type, .description, .folkId, .tier, .industry
        } AS organization,
        collect(DISTINCT p.name) AS people,
        collect(DISTINCT proj.title) AS projects,
        collect(DISTINCT d.name) AS deals,
        count(DISTINCT p) AS people_count,
        count(DISTINCT proj) AS project_count
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"org_name": org_name})
            
            if result and result.records:
                record = result.records[0]
                
                response = {
                    "organization": record.get("organization", {}),
                    "people": [p for p in record.get("people", []) if p],
                    "projects": [p for p in record.get("projects", []) if p],
                    "deals": [d for d in record.get("deals", []) if d],
                    "stats": {
                        "people_count": record.get("people_count", 0),
                        "project_count": record.get("project_count", 0)
                    },
                    "query": org_name,
                    "found": True
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["organization"])
                return response
            else:
                return {
                    "organization": None,
                    "people": [],
                    "projects": [],
                    "deals": [],
                    "stats": {"people_count": 0, "project_count": 0},
                    "query": org_name,
                    "found": False,
                    "error": "Organization not found"
                }
                
        except Exception as e:
            logger.error(f"Error in get_organization_profile for '{org_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "query": org_name,
                "found": False
            }
    
    async def get_network_connections(self, person_name: str, degrees: int = 2) -> Dict[str, Any]:
        """
        Get network connections within specified degrees of separation
        
        Used by: Sales Agent (influence mapping), Analytics Agent (network analysis)
        """
        cache_key = f"network:{person_name.lower().replace(' ', '_')}:deg_{degrees}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # Build variable-length relationship query
        degrees_pattern = f"*1..{degrees}"
        
        query = f"""
        MATCH path = (start:Person)-[:WORKS_FOR|:CONTRIBUTED_TO|:BELONGS_TO{degrees_pattern}]-(connected:Person)
        WHERE start.name CONTAINS $person_name AND start <> connected
        WITH connected, length(path) AS distance, path
        ORDER BY distance, connected.name
        RETURN DISTINCT connected {{
            .name, .role, .email, .folkId, .isInternal
        }} AS person,
        min(distance) AS degrees_of_separation
        LIMIT 50
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"person_name": person_name})
            
            connections = []
            if result and result.records:
                for record in result.records:
                    connections.append({
                        "person": record.get("person", {}),
                        "degrees_of_separation": record.get("degrees_of_separation", 0)
                    })
            
            response = {
                "connections": connections,
                "source_person": person_name,
                "max_degrees": degrees,
                "count": len(connections),
                "found": len(connections) > 0
            }
            
            await self._set_cached_result(cache_key, response, self.cache_ttl["person"])
            return response
            
        except Exception as e:
            logger.error(f"Error in get_network_connections for '{person_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "person": person_name,
                "found": False
            }
    
    async def search_projects_by_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search projects by multiple criteria (type, year, status, client, etc.)
        
        Used by: All agents for project discovery and analysis
        """
        cache_key = f"project_search:{hash(str(sorted(criteria.items())))}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # Build dynamic query based on criteria
        where_clauses = []
        params = {}
        
        if criteria.get("type"):
            where_clauses.append("proj.type CONTAINS $project_type")
            params["project_type"] = criteria["type"]
            
        if criteria.get("year"):
            where_clauses.append("proj.year = $year")
            params["year"] = criteria["year"]
            
        if criteria.get("status"):
            where_clauses.append("proj.status CONTAINS $status")
            params["status"] = criteria["status"]
            
        if criteria.get("client"):
            where_clauses.append("client.name CONTAINS $client_name")
            params["client_name"] = criteria["client"]
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        MATCH (proj:Project)
        OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
        OPTIONAL MATCH (director:Person)-[:CONTRIBUTED_TO {{role: 'Director'}}]->(proj)
        WHERE {where_clause}
        RETURN proj {{
            .name, .type, .status, .year, .description, .budget
        }} AS project,
        client.name AS client,
        director.name AS director
        ORDER BY proj.year DESC, proj.name
        LIMIT 25
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, params)
            
            projects = []
            if result and result.records:
                for record in result.records:
                    projects.append({
                        "project": record.get("project", {}),
                        "client": record.get("client"),
                        "director": record.get("director")
                    })
            
            response = {
                "projects": projects,
                "criteria": criteria,
                "count": len(projects),
                "found": len(projects) > 0
            }
            
            await self._set_cached_result(cache_key, response, self.cache_ttl["project"])
            return response
            
        except Exception as e:
            logger.error(f"Error in search_projects_by_criteria: {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "criteria": criteria,
                "found": False
            }
    
    async def find_similar_projects(self, project_title: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Find projects similar to a given project using vector similarity
        
        Used by: Talent Agent (crew patterns), Analytics Agent (trend analysis)
        """
        cache_key = f"similar_projects:{project_title.lower().replace(' ', '_')}:{similarity_threshold}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # First get the target project's embedding
        target_query = """
        MATCH (proj:Project)
        WHERE proj.name CONTAINS $title
        RETURN proj.concept_embedding AS embedding, proj.name AS exact_title
        LIMIT 1
        """
        
        try:
            target_result = await self.neo4j_client.execute_query(target_query, {"title": project_title})
            
            if not target_result or not target_result.records:
                return {
                    "similar_projects": [],
                    "target_project": project_title,
                    "error": "Target project not found or no embedding available",
                    "found": False
                }
            
            target_embedding = target_result.records[0].get("embedding")
            exact_title = target_result.records[0].get("exact_title")
            
            if not target_embedding:
                return {
                    "similar_projects": [],
                    "target_project": project_title,
                    "error": "Target project has no concept embedding",
                    "found": False
                }
            
            # Find similar projects using vector similarity
            similarity_query = """
            MATCH (proj:Project)
            WHERE proj.concept_embedding IS NOT NULL 
            AND proj.name <> $exact_title
            WITH proj, gds.similarity.cosine(proj.concept_embedding, $target_embedding) AS similarity
            WHERE similarity >= $threshold
            OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
            RETURN proj {
                .name, .type, .year, .status
            } AS project,
            client.name AS client,
            similarity
            ORDER BY similarity DESC
            LIMIT 10
            """
            
            result = await self.neo4j_client.execute_query(
                similarity_query, 
                {
                    "exact_title": exact_title,
                    "target_embedding": target_embedding,
                    "threshold": similarity_threshold
                }
            )
            
            similar_projects = []
            if result and result.records:
                for record in result.records:
                    similar_projects.append({
                        "project": record.get("project", {}),
                        "client": record.get("client"),
                        "similarity_score": record.get("similarity", 0)
                    })
            
            response = {
                "similar_projects": similar_projects,
                "target_project": exact_title,
                "similarity_threshold": similarity_threshold,
                "count": len(similar_projects),
                "found": len(similar_projects) > 0
            }
            
            await self._set_cached_result(cache_key, response, self.cache_ttl["project"])
            return response
            
        except Exception as e:
            logger.error(f"Error in find_similar_projects for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "target_project": project_title,
                "found": False
            }
    
    async def get_project_team_details(self, project_title: str) -> Dict[str, Any]:
        """
        Get detailed team composition and roles for a project
        
        Used by: Talent Agent (team analysis), Analytics Agent (crew patterns)
        """
        cache_key = f"project_team:{project_title.lower().replace(' ', '_')}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj:Project)
        WHERE proj.name CONTAINS $title
        OPTIONAL MATCH (p)-[:WORKS_FOR]->(org:Organization)
        RETURN proj {
            .name, .type, .status, .year
        } AS project,
        collect({
            person: p {.name, .role, .email, .folkId},
            role: r.role,
            startDate: r.startDate,
            endDate: r.endDate,
            organization: org.name
        }) AS crew
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"title": project_title})
            
            if result and result.records:
                record = result.records[0]
                crew = record.get("crew", [])
                
                # Organize crew by roles
                roles = {}
                for member in crew:
                    role = member.get("role", "Unknown")
                    if role not in roles:
                        roles[role] = []
                    roles[role].append(member)
                
                response = {
                    "project": record.get("project", {}),
                    "crew": crew,
                    "crew_by_role": roles,
                    "total_crew_size": len(crew),
                    "unique_roles": len(roles),
                    "found": True
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["project"])
                return response
            else:
                return {
                    "project": None,
                    "crew": [],
                    "crew_by_role": {},
                    "total_crew_size": 0,
                    "unique_roles": 0,
                    "query": project_title,
                    "found": False,
                    "error": "Project not found"
                }
                
        except Exception as e:
            logger.error(f"Error in get_project_team_details for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "query": project_title,
                "found": False
            }
    
    async def get_creative_concepts_for_project(self, project_title: str) -> Dict[str, Any]:
        """
        Get creative concepts and styles associated with a project
        
        Used by: Talent Agent (style matching), Analytics Agent (creative analysis)
        """
        cache_key = f"project_concepts:{project_title.lower().replace(' ', '_')}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (proj:Project)-[:FEATURES_CONCEPT]->(c:CreativeConcept)
        WHERE proj.name CONTAINS $title
        OPTIONAL MATCH (c)-[:RELATED_TO]->(related:CreativeConcept)
        RETURN proj {
            .name, .type, .year
        } AS project,
        collect(DISTINCT c {
            .name, .category, .description, .tags
        }) AS concepts,
        collect(DISTINCT related.name) AS related_concepts
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"title": project_title})
            
            if result and result.records:
                record = result.records[0]
                
                response = {
                    "project": record.get("project", {}),
                    "concepts": record.get("concepts", []),
                    "related_concepts": [r for r in record.get("related_concepts", []) if r],
                    "concept_count": len(record.get("concepts", [])),
                    "found": True
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["concept"])
                return response
            else:
                return {
                    "project": None,
                    "concepts": [],
                    "related_concepts": [],
                    "concept_count": 0,
                    "query": project_title,
                    "found": False,
                    "error": "Project not found or no concepts associated"
                }
                
        except Exception as e:
            logger.error(f"Error in get_creative_concepts_for_project for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "query": project_title,
                "found": False
            }
    
    async def find_creative_references(self, concept_name: str, medium: str = None) -> Dict[str, Any]:
        """
        Find creative references and inspirations for concepts
        
        Used by: Talent Agent (style research), Analytics Agent (trend analysis)
        """
        cache_key = f"creative_refs:{concept_name.lower().replace(' ', '_')}:{medium or 'all'}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (c:CreativeConcept)-[:INSPIRED_BY]->(ref:Reference)
        WHERE c.name CONTAINS $concept_name
        """
        
        if medium:
            query += " AND ref.medium CONTAINS $medium"
        
        query += """
        RETURN c {
            .name, .category, .description
        } AS concept,
        collect(ref {
            .title, .creator, .medium, .year, .url, .description
        }) AS references
        """
        
        try:
            params = {"concept_name": concept_name}
            if medium:
                params["medium"] = medium
                
            result = await self.neo4j_client.execute_query(query, params)
            
            references = []
            if result and result.records:
                for record in result.records:
                    references.extend(record.get("references", []))
            
            response = {
                "references": references,
                "concept": concept_name,
                "medium": medium,
                "count": len(references),
                "found": len(references) > 0
            }
            
            await self._set_cached_result(cache_key, response, self.cache_ttl["concept"])
            return response
            
        except Exception as e:
            logger.error(f"Error in find_creative_references for '{concept_name}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "concept": concept_name,
                "found": False
            }
    
    async def search_documents_by_content(self, query: str, doc_type: str = None) -> Dict[str, Any]:
        """
        Search documents by content with optional type filtering
        
        Used by: Analytics Agent (document analysis), Sales Agent (research)
        """
        cache_key = f"doc_search:{hash(query)}:{doc_type or 'all'}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # Use full-text search with optional type filter
        if doc_type:
            search_query = f"""
            CALL db.index.fulltext.queryNodes('document_fulltext_index', $search_query)
            YIELD node, score
            MATCH (node:Document)
            WHERE node.type CONTAINS $doc_type
            RETURN node {
                .title, .type, .id, .created_at
            } AS document,
            score,
            node.content AS content
            ORDER BY score DESC
            LIMIT 15
            """
        else:
            search_query = f"""
            CALL db.index.fulltext.queryNodes('document_fulltext_index', $search_query)
            YIELD node, score
            MATCH (node:Document)
            RETURN node {
                .title, .type, .id, .created_at
            } AS document,
            score,
            node.content AS content
            ORDER BY score DESC
            LIMIT 15
            """
        
        try:
            params = {"search_query": query}
            if doc_type:
                params["doc_type"] = doc_type
                
            result = await self.neo4j_client.execute_query(search_query, params)
            
            documents = []
            if result and result.records:
                for record in result.records:
                    content = record.get("content", "")
                    snippet = self._extract_snippet(content, query)
                    
                    documents.append({
                        "document": record.get("document", {}),
                        "relevance_score": record.get("score", 0),
                        "snippet": snippet
                    })
            
            response = {
                "documents": documents,
                "search_query": query,
                "document_type": doc_type,
                "count": len(documents),
                "found": len(documents) > 0
            }
            
            await self._set_cached_result(cache_key, response, self.cache_ttl["document"])
            return response
            
        except Exception as e:
            logger.error(f"Error in search_documents_by_content for '{query}': {e}")
            return {
                "error": f"Search failed: {str(e)}",
                "search_query": query,
                "found": False
            }
    
    async def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """
        Get complete document details by ID
        
        Used by: All agents for document retrieval
        """
        cache_key = f"doc_by_id:{document_id}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        query = """
        MATCH (d:Document {id: $doc_id})
        OPTIONAL MATCH (d)-[:RELATED_TO]->(proj:Project)
        OPTIONAL MATCH (d)-[:CREATED_BY]->(author:Person)
        RETURN d {
            .title, .type, .id, .content, .summary,
            .created_at, .sensitivityLevel
        } AS document,
        proj.name AS project,
        author.name AS author
        """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"doc_id": document_id})
            
            if result and result.records:
                record = result.records[0]
                
                response = {
                    "document": record.get("document", {}),
                    "project": record.get("project"),
                    "author": record.get("author"),
                    "found": True
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["document"])
                return response
            else:
                return {
                    "document": None,
                    "project": None,
                    "author": None,
                    "document_id": document_id,
                    "found": False,
                    "error": "Document not found"
                }
                
        except Exception as e:
            logger.error(f"Error in get_document_by_id for '{document_id}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "document_id": document_id,
                "found": False
            }
    
    async def extract_project_insights(self, project_title: str, insight_type: str) -> Dict[str, Any]:
        """
        Extract specific insights from project data (performance, budget, team, etc.)
        
        Used by: Analytics Agent (comprehensive project analysis)
        """
        cache_key = f"project_insights:{project_title.lower().replace(' ', '_')}:{insight_type}"
        
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # Different queries based on insight type
        if insight_type == "performance":
            query = """
            MATCH (proj:Project)
            WHERE proj.name CONTAINS $title
            OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
            OPTIONAL MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj)
            WITH proj, client, count(p) AS crew_size
            RETURN proj {
                .name, .status, .year, .budget, .actualCost, .duration
            } AS project,
            client.name AS client,
            crew_size,
            {
                budget_efficiency: CASE 
                    WHEN proj.budget IS NOT NULL AND proj.actualCost IS NOT NULL 
                    THEN round((proj.budget - proj.actualCost) * 100.0 / proj.budget)
                    ELSE null 
                END,
                crew_efficiency: CASE 
                    WHEN crew_size > 15 THEN 'large_team'
                    WHEN crew_size > 8 THEN 'medium_team'
                    ELSE 'small_team'
                END
            } AS performance_metrics
            """
        
        elif insight_type == "team":
            query = """
            MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj:Project)
            WHERE proj.name CONTAINS $title
            WITH proj, collect({
                name: p.name, 
                role: r.role, 
                experience_level: CASE 
                    WHEN size((p)-[:CONTRIBUTED_TO]->(:Project)) > 10 THEN 'senior'
                    WHEN size((p)-[:CONTRIBUTED_TO]->(:Project)) > 3 THEN 'mid'
                    ELSE 'junior'
                END
            }) AS team_analysis
            RETURN proj.name AS project_title,
            size(team_analysis) AS total_crew,
            size([m IN team_analysis WHERE m.experience_level = 'senior']) AS senior_count,
            size([m IN team_analysis WHERE m.experience_level = 'mid']) AS mid_count,
            size([m IN team_analysis WHERE m.experience_level = 'junior']) AS junior_count,
            team_analysis
            """
        
        else:  # Default general insights
            query = """
            MATCH (proj:Project)
            WHERE proj.name CONTAINS $title
            OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
            OPTIONAL MATCH (proj)-[:FEATURES_CONCEPT]->(concept:CreativeConcept)
            OPTIONAL MATCH (p:Person)-[:CONTRIBUTED_TO]->(proj)
            RETURN proj {
                .name, .type, .status, .year, .budget, .description
            } AS project,
            client.name AS client,
            collect(DISTINCT concept.name) AS concepts,
            count(DISTINCT p) AS crew_size
            """
        
        try:
            result = await self.neo4j_client.execute_query(query, {"title": project_title})
            
            if result and result.records:
                record = result.records[0]
                
                if insight_type == "performance":
                    insights = {
                        "project": record.get("project", {}),
                        "client": record.get("client"),
                        "crew_size": record.get("crew_size", 0),
                        "performance_metrics": record.get("performance_metrics", {}),
                        "insight_type": insight_type
                    }
                elif insight_type == "team":
                    insights = {
                        "project_title": record.get("project_title"),
                        "team_composition": {
                            "total_crew": record.get("total_crew", 0),
                            "senior_count": record.get("senior_count", 0),
                            "mid_count": record.get("mid_count", 0),
                            "junior_count": record.get("junior_count", 0)
                        },
                        "team_analysis": record.get("team_analysis", []),
                        "insight_type": insight_type
                    }
                else:
                    insights = {
                        "project": record.get("project", {}),
                        "client": record.get("client"),
                        "concepts": record.get("concepts", []),
                        "crew_size": record.get("crew_size", 0),
                        "insight_type": insight_type
                    }
                
                response = {
                    "insights": insights,
                    "project_title": project_title,
                    "insight_type": insight_type,
                    "found": True
                }
                
                await self._set_cached_result(cache_key, response, self.cache_ttl["project"])
                return response
            else:
                return {
                    "insights": None,
                    "project_title": project_title,
                    "insight_type": insight_type,
                    "found": False,
                    "error": "Project not found"
                }
                
        except Exception as e:
            logger.error(f"Error in extract_project_insights for '{project_title}': {e}")
            return {
                "error": f"Query failed: {str(e)}",
                "project_title": project_title,
                "insight_type": insight_type,
                "found": False
            }