"""
Standalone Broad Vector Search Tool

A comprehensive graph search tool that can be called in parallel with any other tool
to provide broad coverage across the entire Neo4j knowledge graph.
"""

import logging
from typing import Dict, Any
from .factory import create_organization_tool
from .universal_vector_search import universal_vector_search

logger = logging.getLogger(__name__)

@create_organization_tool(
    name="broad_vector_search",
    description="""Perform comprehensive vector search across the entire knowledge graph.

SEARCH_SCOPE: ALL entities (people, projects, organizations, documents, treatments, content)
SEARCH_METHOD: Vector similarity + text matching across entire graph

MANDATORY_PARALLEL_EXECUTION: 
⚠️  CRITICAL: Always call this tool IN PARALLEL with specific entity tools
⚠️  NEVER call this tool alone for comprehensive queries

PARALLEL_PATTERNS:
✅ Organization query: get_organization_profile("company") + broad_vector_search("company treatment writer")
✅ Person query: get_person_details("person") + broad_vector_search("person")
✅ Treatment query: search_projects_by_criteria + broad_vector_search("treatment writer company")

USE_WHEN:
- ANY query requiring comprehensive coverage
- Treatment/project writer searches
- Cross-entity relationship discovery  
- Ensuring no relevant information is missed
- Finding connections between different entity types

QUERY_ENHANCEMENT_EXAMPLES:
✅ "boost mobile" → broad_vector_search("boost mobile treatment writer director")
✅ "courtney phillips" → broad_vector_search("courtney phillips writer director projects")
✅ "who wrote treatments" → broad_vector_search("treatment writer screenplay director")

COVERAGE: Vector similarity across people bios, project descriptions, organization data, document content

Input: search_query (str) - Enhanced query to find relevant data across the entire graph
Returns: Comprehensive results across people, projects, organizations, and documents"""
)
async def broad_vector_search(search_query: str, neo4j_client) -> Dict[str, Any]:
    """
    Perform comprehensive vector search across the entire Neo4j knowledge graph.
    
    This tool provides broad coverage by searching across:
    - People (roles, bios, names)
    - Projects (names, descriptions, types)
    - Organizations (names, descriptions, types)
    - Documents (content, text)
    - Treatment Writers (through relationship queries)
    
    Returns comprehensive results with similarity scores and relationship context.
    """
    
    logger.info(f"🔍 BROAD VECTOR SEARCH: '{search_query}'")
    
    try:
        # First check if this might be a treatment writer query
        is_treatment_query = any(word in search_query.lower() for word in ['treatment', 'writer', 'wrote', 'author'])
        treatment_writers = []
        
        if is_treatment_query:
            logger.info(f"🎭 TREATMENT QUERY DETECTED: Running relationship-based writer search")
            
            # Extract potential company/project names from query
            query_words = search_query.lower().split()
            for word in ['treatment', 'writer', 'wrote', 'author', 'for', 'the', 'who']:
                if word in query_words:
                    query_words.remove(word)
            
            if query_words:  # If we have remaining words that might be company/project names
                search_term = ' '.join(query_words)
                logger.info(f"🔍 RELATIONSHIP SEARCH for: '{search_term}'")
                
                # Query for treatment writers through relationships
                writer_query = """
                MATCH (writer:Person)-[r:AUTHORED_BY|WROTE_TREATMENT_FOR|DIRECTED|CREATED]-(item)
                WHERE (
                    toLower(item.id) CONTAINS toLower($search_term) OR
                    toLower(item.name) CONTAINS toLower($search_term) OR
                    toLower(item.client) CONTAINS toLower($search_term) OR
                    ANY(word IN $query_words WHERE toLower(item.id) CONTAINS word)
                )
                AND (
                    toLower(writer.role) CONTAINS 'writer' OR
                    toLower(writer.role) CONTAINS 'director' OR  
                    toLower(writer.role) CONTAINS 'author'
                )
                RETURN writer.id AS writer_id, writer.name AS writer_name, writer.role AS writer_role,
                       writer.bio AS writer_bio,
                       item.id AS item_id, item.name AS item_name, item.type AS item_type,
                       type(r) AS relationship_type,
                       item.description AS item_description
                ORDER BY writer.id
                LIMIT 10
                """
                
                try:
                    result = await neo4j_client.execute_query(writer_query, {
                        "search_term": search_term,
                        "query_words": query_words
                    })
                    
                    if result and result.records:
                        logger.info(f"🎯 FOUND {len(result.records)} treatment writer relationships")
                        for record in result.records:
                            treatment_writers.append({
                                "entity": {
                                    "id": record.get('writer_id', 'unknown'),
                                    "name": record.get('writer_name', 'unknown'),
                                    "role": record.get('writer_role', 'unknown'),
                                    "bio": record.get('writer_bio', ''),
                                },
                                "score": 1.0,  # High relevance for relationship matches
                                "relationship": {
                                    "type": record.get('relationship_type', 'unknown'),
                                    "target_id": record.get('item_id', 'unknown'),
                                    "target_name": record.get('item_name', 'unknown'),
                                    "target_type": record.get('item_type', 'unknown')
                                }
                            })
                except Exception as e:
                    logger.error(f"❌ RELATIONSHIP SEARCH failed: {e}")
        
        # Use the universal vector search function
        vector_results = await universal_vector_search(
            query_text=search_query,
            neo4j_client=neo4j_client,
            max_results=20,  # Higher limit for comprehensive search
            similarity_threshold=0.6  # Lower threshold for broader coverage
        )
        
        if vector_results.get("found", False) or treatment_writers:
            people = vector_results.get("people", [])
            projects = vector_results.get("projects", [])
            organizations = vector_results.get("organizations", [])
            documents = vector_results.get("documents", [])
            total = vector_results.get("total_results", 0)
            
            # Merge treatment writers with regular people results
            all_people = people + treatment_writers
            total_with_writers = total + len(treatment_writers)
            
            logger.info(f"🎯 BROAD SEARCH RESULTS: {total_with_writers} total across all entities")
            logger.info(f"🔍 PROCESSING INSIGHTS: people={len(all_people)} (including {len(treatment_writers)} treatment writers), projects={len(projects)}, orgs={len(organizations)}")
            
            # Extract key insights for easy consumption
            insights = []
            
            # Treatment writer insights (prioritized)
            for writer in treatment_writers:
                entity = writer.get("entity", {})
                score = writer.get("score", 0)
                relationship = writer.get("relationship", {})
                writer_id = entity.get("id", "unknown")
                writer_role = entity.get("role", "unknown")
                target_id = relationship.get("target_id", "unknown")
                rel_type = relationship.get("type", "unknown")
                
                logger.info(f"    🎭 Processing treatment writer: id='{writer_id}', role='{writer_role}', target='{target_id}'")
                insights.append({
                    "type": "treatment_writer",
                    "id": writer_id,
                    "role": writer_role,
                    "relevance_score": score,
                    "relationship_type": rel_type,
                    "connected_to": target_id,
                    "insight": f"Treatment writer '{writer_id}' ({writer_role}) {rel_type.lower()} '{target_id}'"
                })
            
            # People insights (regular vector search results)
            for person in people[:3]:  # Top 3 people
                if person is None:
                    continue
                entity = person.get("entity", {})
                score = person.get("score", 0)
                person_id = entity.get("id", "unknown")
                person_role = entity.get("role", "unknown")
                logger.info(f"    🔍 Processing person: entity_keys={list(entity.keys())}, id='{person_id}', role='{person_role}'")
                insights.append({
                    "type": "person",
                    "id": person_id,
                    "role": person_role,
                    "relevance_score": score,
                    "insight": f"Person '{person_id}' with role '{person_role}' matches query"
                })
            
            # Project insights
            for project in projects[:3]:  # Top 3 projects
                if project is None:
                    continue
                entity = project.get("entity", {})
                score = project.get("score", 0)
                client = entity.get("client", "unknown")
                project_id = entity.get("id", "unknown")
                logger.info(f"    🔍 Processing project: entity_keys={list(entity.keys())}, id='{project_id}', client='{client}'")
                insights.append({
                    "type": "project", 
                    "id": project_id,
                    "client": client,
                    "relevance_score": score,
                    "insight": f"Project '{project_id}' for client '{client}' matches query"
                })
            
            # Organization insights
            for org in organizations[:3]:  # Top 3 organizations
                if org is None:
                    continue
                entity = org.get("entity", {})
                score = org.get("score", 0)
                org_id = entity.get("id", "unknown")
                insights.append({
                    "type": "organization",
                    "id": org_id,
                    "relevance_score": score,
                    "insight": f"Organization '{org_id}' matches query"
                })
            
            # Document insights
            if documents:
                insights.append({
                    "type": "documents",
                    "count": len(documents),
                    "insight": f"Found {len(documents)} documents with relevant content"
                })
            
            return {
                "search_query": search_query,
                "found": True,
                "total_results": total_with_writers,
                "summary": {
                    "people_found": len(all_people),
                    "treatment_writers_found": len(treatment_writers),
                    "projects_found": len(projects), 
                    "organizations_found": len(organizations),
                    "documents_found": len(documents)
                },
                "key_insights": insights,
                "detailed_results": {
                    "people": all_people,
                    "treatment_writers": treatment_writers,
                    "projects": projects,
                    "organizations": organizations,
                    "documents": documents
                },
                "search_method": "comprehensive_vector_search_with_relationships",
                "coverage": "all_entity_types_plus_relationships"
            }
        else:
            return {
                "search_query": search_query,
                "found": False,
                "total_results": 0,
                "summary": {
                    "people_found": 0,
                    "projects_found": 0,
                    "organizations_found": 0,
                    "documents_found": 0
                },
                "key_insights": [],
                "message": "No relevant data found across the knowledge graph",
                "search_method": "comprehensive_vector_search",
                "coverage": "all_entity_types"
            }
            
    except Exception as e:
        logger.error(f"❌ BROAD VECTOR SEARCH failed: {e}")
        return {
            "search_query": search_query,
            "found": False,
            "error": f"Search failed: {str(e)}",
            "total_results": 0,
            "summary": {
                "people_found": 0,
                "projects_found": 0,
                "organizations_found": 0,
                "documents_found": 0
            },
            "key_insights": [],
            "search_method": "comprehensive_vector_search",
            "coverage": "all_entity_types"
        }